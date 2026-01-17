# **[Pattern] Fraisier: CQRS Architecture for Deployment State Management**
*Reference Guide*

---

## **1. Overview**
Fraisier is a **CQRS (Command Query Responsibility Segregation)**-based architecture for **efficient deployment state management**. It decouples **write operations** (recorded in `tb_*` transactional tables) from **read operations** (optimized via `v_*` read views).

This pattern ensures:
✅ **Atomic writes** for deployment events (deployments, webhooks, status changes).
✅ **High-performance reads** for historical queries and aggregated statistics.
✅ **Separation of concerns** between transactional logs and analytics-ready data.

Fraisier leverages the same **three-layer view architecture** as FraiseQL, applied to deployment orchestration.

---

## **2. Key Concepts**
| **Concept**       | **Description**                                                                                     | **Purpose**                                                                                     |
|-------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Write Tables**  | `tb_deployments`, `tb_webhooks`, `tb_status_changes` (transactional)                              | Record immutable facts in a single-source-of-truth (SSOT) format.                            |
| **Read Views**    | `v_deployment_history`, `v_current_status`, `v_stats` (optimized for queries)                     | Pre-computed and indexed for fast, complex analytics.                                          |
| **Synchronization** | Scheduled or event-driven updates to views from write tables.                                       | Ensures views reflect the latest state without blocking write operations.                       |
| **Event Sourcing** (Optional) | Append-only logs of deployment events (stored in `tb_events`).                                      | Enables time-travel debugging and replayability.                                               |

---

## **3. Schema Reference**

### **3.1 Write Tables (Transactional)**
| Table Name          | Key Fields          | Description                                                                                     | Example Data                                                                                     |
|---------------------|---------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| `tb_deployments`    | `id` (PK), `app_id`, `commit_hash`, `status`, `created_at` | Records deployment initiation and final status.                                                | `{ "id": "d123", "app_id": "webapp", "commit_hash": "abc123", "status": "COMPLETED", ... }` |
| `tb_webhooks`       | `id` (PK), `deployment_id`, `url`, `payload`, `status`, `attempts` | Logs webhook attempts for external callbacks.                                                  | `{ "id": "wh456", "deployment_id": "d123", "url": "https://api.example.com/webhook", ... }`   |
| `tb_status_changes` | `id` (PK), `deployment_id`, `old_status`, `new_status`, `changed_at` | Tracks every status transition in deployment lifecycle.                                        | `{ "id": "sc789", "deployment_id": "d123", "old_status": "PENDING", "new_status": "RUNNING", ... }` |

**Constraints:**
- All tables use **UUIDs** for `id` fields.
- `created_at`/`changed_at` are **timestamp with timezone** (`timestamptz`).
- `status` follows a **closed set** of enum values (e.g., `PENDING`, `RUNNING`, `FAILED`, `COMPLETED`).

---

### **3.2 Read Views (Optimized Queries)**
| View Name               | Purpose                                                                                     | Key Fields                                                                                     | Indexes                                                                                          |
|-------------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| `v_deployment_history`  | Full audit trail of deployments (joins `tb_deployments`, `tb_status_changes`).              | `deployment_id`, `app_id`, `commit_hash`, `status`, `created_at`, `changed_at`                | `app_id`, `(deployment_id, status)` (for time-series queries)                                |
| `v_current_status`      | Snapshot of live deployment statuses (materialized view).                                   | `app_id`, `commit_hash`, `status`, `last_updated_at`                                          | `app_id`, `(app_id, status)`                                                                   |
| `v_stats`               | Aggregated metrics (e.g., success rate, failure trends).                                    | `app_id`, `time_window` (daily/weekly), `success_count`, `failure_count`, `deployment_count` | `time_window`, `(app_id, time_window)`                                                          |

**Example View Definition (`v_deployment_history`):**
```sql
CREATE VIEW v_deployment_history AS
SELECT
    d.id AS deployment_id,
    d.app_id,
    d.commit_hash,
    d.status AS final_status,
    d.created_at,
    sc.changed_at,
    sc.new_status
FROM tb_deployments d
LEFT JOIN tb_status_changes sc ON d.id = sc.deployment_id
ORDER BY deployment_id, changed_at;
```

---

### **3.3 Synchronization Mechanism**
| Method               | Description                                                                                     | Trigger                                                                                          |
|----------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Scheduled Refresh** | Cron job updates views nightly (best for analytics-heavy loads).                               | `0 3 * * *` (UTC)                                                                             |
| **Event-Driven**     | PostgreSQL **triggers** or **listeners** update views on write table changes.                 | `ON tb_status_changes DO UPDATE v_current_status`                                             |
| **Change Data Capture (CDC)** | Debezium/Kafka stream processes `tb_*` writes to update `v_*`.                                | Requires Kafka Connect + PostgreSQL connector.                                                 |

**Example Trigger (Simplified):**
```sql
CREATE OR REPLACE FUNCTION update_current_status()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE v_current_status
    SET status = NEW.new_status,
        last_updated_at = NOW()
    WHERE app_id = NEW.app_id AND commit_hash = NEW.commit_hash;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_status
AFTER INSERT OR UPDATE ON tb_status_changes
FOR EACH ROW EXECUTE FUNCTION update_current_status();
```

---

## **4. Query Examples**

### **4.1 Write Operations (CQRS Commands)**
**Create a Deployment:**
```sql
INSERT INTO tb_deployments (
    id, app_id, commit_hash, status, created_at
) VALUES (
    gen_random_uuid(), 'webapp', 'abc123', 'PENDING', NOW()
);
```

**Log a Webhook Attempt:**
```sql
INSERT INTO tb_webhooks (
    id, deployment_id, url, payload, status, attempts
) VALUES (
    gen_random_uuid(), 'd123', 'https://api.example.com/webhook',
    '{"key": "value"}', 'PENDING', 0
);
```

**Update Deployment Status:**
```sql
INSERT INTO tb_status_changes (
    id, deployment_id, old_status, new_status, changed_at
) VALUES (
    gen_random_uuid(), 'd123', 'PENDING', 'RUNNING', NOW()
);
```

---

### **4.2 Read Operations (CQRS Queries)**
**Get Deployment Timeline:**
```sql
SELECT
    deployment_id,
    app_id,
    commit_hash,
    final_status,
    changed_at,
    new_status
FROM v_deployment_history
WHERE app_id = 'webapp'
ORDER BY deployment_id, changed_at DESC;
```

**Check Current Status:**
```sql
SELECT * FROM v_current_status
WHERE app_id = 'webapp' AND commit_hash = 'abc123';
```

**Generate Failure Rate Report:**
```sql
SELECT
    time_window::date AS day,
    failure_count,
    ROUND(failure_count * 100.0 / deployment_count, 2) AS failure_percentage
FROM v_stats
WHERE app_id = 'webapp'
AND time_window >= (CURRENT_DATE - INTERVAL '30 days')
ORDER BY day;
```

---

## **5. Related Patterns**
| Pattern               | Connection to Fraisier                                                                         | When to Use                                                                                     |
|-----------------------|-----------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Event Sourcing**    | `tb_events` can store raw deployment events (immutable log).                                | Need audit trails, replayability, or time-travel debugging.                                     |
| **Materialized Views**| `v_*` views are materialized for performance.                                               | Read-heavy workloads with complex aggregations.                                                |
| **Schema Evolution**  | Use **PostgreSQL’s JSONB** or **PolarsDB** for schema flexibility.                          | Experimental features or dynamic fields (e.g., custom metrics).                               |
| **Idempotency**       | Write tables enforce uniqueness via `(app_id, commit_hash)`.                               | Prevent duplicate deployments for the same commit.                                            |
| **Compensating Transactions** | Rollback via `tb_status_changes` (e.g., mark as `FAILED`).                                | Handle failed deployments gracefully.                                                          |

---

## **6. Best Practices**
1. **Partition Large Tables**
   - Add `(app_id)` partition key to `tb_deployments`/`tb_webhooks` for scalability.
   ```sql
   CREATE TABLE tb_deployments (
       -- columns --
   ) PARTITION BY LIST (app_id);
   ```

2. **Use Partial Indexes**
   - Optimize `v_deployment_history` queries with:
   ```sql
   CREATE INDEX idx_history_running ON v_deployment_history (deployment_id, status)
   WHERE status = 'RUNNING';
   ```

3. **Monitor Sync Lag**
   - Track view refresh time via `pg_stat_activity` or Prometheus metrics.

4. **Backup Views**
   - Include `v_*` in PostgreSQL logical replication for disaster recovery.

5. **Avoid Direct Writes to Views**
   - Always update via `tb_*` tables to maintain consistency.

---
**Final Note:** Fraisier balances **transactional integrity** (via `tb_*`) with **analytical efficiency** (via `v_*`), ideal for modern deployment pipelines. For further customization, extend with **Event Sourcing** or **PolarsDB** for time-series data.