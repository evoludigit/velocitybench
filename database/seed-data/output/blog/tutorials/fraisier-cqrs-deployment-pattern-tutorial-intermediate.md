```markdown
# **Fraisier: CQRS for Deployment State Management (A Practical Guide)**

*How to split writes and reads in deployment orchestration for better performance and scalability*

---

## **Introduction**

Deployments are the lifeblood of modern software—fast, reliable, and transparent. But as deployments grow in complexity (multi-environment, canary releases, blue-green rollbacks), so do the challenges:

- **Write-heavy systems** struggle under the load of logging every change (new deployments, status updates, webhooks).
- **Read-heavy systems** choke when querying historical data or aggregating metrics across environments.
- **Denormalization** (joining hundreds of rows per deployment) slows down queries, forcing costly optimizations.

Enter **Fraisier**: a CQRS (Command Query Responsibility Segregation) pattern tailored for deployment state management. Inspired by FraiseQL’s three-layer view architecture, Fraisier splits deployment data into **write tables** (fast mutations) and **read views** (optimized queries), keeping them in sync via a background process.

This pattern isn’t theoretical—it’s battle-tested in systems handling thousands of deployments per minute. In this post, we’ll explore:
✅ Why traditional deployment tables fail under scale
✅ How Fraisier separates writes (tb_*) and reads (v_*) for performance
✅ Practical SQL implementations for PostgreSQL/Mysql
✅ Common pitfalls and how to avoid them

Let’s dive in.

---

## **The Problem: Why Single-Table Deployments Fail**

Most deployment systems start simple: a single `deployments` table with columns like:
- `id`, `environment`, `version`, `status`, `created_at`, `webhook_url`

But as deployments multiply, this design hits walls:

### **1. Write Performance**
Every deployment triggers:
- An INSERT/UPDATE (fast)
- Webhook calls (slow, external)
- Status transitions (e.g., PENDING → RUNNING → DONE)

All this happens in a single transaction. As concurrency rises, locks and retries cause latency spikes.

### **2. Read Performance**
To answer questions like:
- *"List all failed deployments in `prod` this month"*
- *"Show deployment rollback history for artifact `v2.1.0`"*
- *"Calculate SLA compliance across environments"*

You need:
- JOINs across related tables (e.g., `deployments`, `webhooks`, `status_changes`)
- Aggregations (e.g., `COUNT`, `AVG` over time)
- Denormalized columns (e.g., `latest_version`) to avoid repeated queries

A single table forces compromises:
- **Denormalize for reads** → Higher write complexity (e.g., triggers to update `latest_version`).
- **Normalize for writes** → Slow queries with 5+ JOINs.

### **3. Data Bloat**
A deployment may have:
- 1 `deployment` row
- 10 `status_change` rows
- 5 `webhook` rows
- 3 `artifact` rows

Querying all this in a single table leads to:
```sql
SELECT * FROM deployments
JOIN status_changes ON deployments.id = status_changes.deployment_id
JOIN webhooks ON deployments.id = webhooks.deployment_id
WHERE environment = 'prod' AND status = 'FAILED';
```
*(This is a simplified example—real-world queries are worse.)*

### **The Fraisier Solution**
Fraisier tackles these issues by:
1. **Separating writes** (tb_* tables) for fast mutations.
2. **Separating reads** (v_* views) for optimized queries.
3. **Synchronizing** them via a background process (e.g., `update_views_job`).

This mirrors FraiseQL’s three-layer architecture but focuses on deployment orchestration.

---

## **The Solution: Fraisier CQRS for Deployments**

Fraisier splits deployment data into two layers:

| Layer       | Purpose                          | Example Tables/Views       | Query Focus               |
|-------------|----------------------------------|----------------------------|---------------------------|
| **Write**   | Record deployment *facts*        | `tb_deployments`, `tb_status`, `tb_webhooks` | Fast mutations (INSERT/UPDATE) |
| **Read**    | Optimize for *queries*           | `v_deployment_history`, `v_environment_status`, `v_webhook_aggregates` | JOINs, aggregations, denormalized data |

### **Key Principles**
1. **Append-only writes**: Write tables (`tb_*`) only support `INSERT` (or `UPSERT` for immutable IDs).
2. **Materialized reads**: Read views (`v_*`) are updated via triggers or background jobs.
3. **No direct updates**: Read views are *never* updated directly—they’re rebuilt from writes.
4. **Eventual consistency**: Views lag behind writes by milliseconds (e.g., via `ON INSERT/UPDATE` triggers).

---

## **Implementation Guide: SQL Examples**

### **Step 1: Define Write Tables (tb_*)**
These tables log *what happened* in chronological order.

#### **1. Core Deployment Table**
```sql
CREATE TABLE tb_deployments (
  id BIGSERIAL PRIMARY KEY,
  environment VARCHAR(64) NOT NULL,
  artifact_name VARCHAR(128) NOT NULL,
  version VARCHAR(64) NOT NULL,
  requested_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  user_id BIGINT REFERENCES users(id),
  metadata JSONB
);
```

#### **2. Status Changes (Event Sourcing)**
```sql
CREATE TABLE tb_status_changes (
  id BIGSERIAL PRIMARY KEY,
  deployment_id BIGINT REFERENCES tb_deployments(id),
  status VARCHAR(32) NOT NULL,  -- PENDING, RUNNING, FAILED, DONE
  changed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  details JSONB,
  UNIQUE (deployment_id, status)  -- One status per deployment
);
```

#### **3. Webhook Results**
```sql
CREATE TABLE tb_webhooks (
  id BIGSERIAL PRIMARY KEY,
  deployment_id BIGINT REFERENCES tb_deployments(id),
  url TEXT NOT NULL,
  status_code INT,
  response_time_ms INT,
  payload JSONB,
  sent_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

### **Step 2: Create Read Views (v_*)**
These views join write tables and denormalize for common queries.

#### **1. Deployment History (All Status Transitions)**
```sql
CREATE VIEW v_deployment_history AS
SELECT
  d.id,
  d.environment,
  d.artifact_name,
  d.version,
  d.requested_at,
  d.user_id,
  s.status,
  s.changed_at,
  s.details,
  ROW_NUMBER() OVER (PARTITION BY d.id ORDER BY s.changed_at) AS status_rank
FROM tb_deployments d
LEFT JOIN tb_status_changes s ON d.id = s.deployment_id;
```

#### **2. Environment Status (Current State)**
```sql
CREATE OR REPLACE VIEW v_environment_status AS
SELECT
  environment,
  MAX(CASE WHEN status = 'DONE' THEN id END) AS latest_done_id,
  MAX(CASE WHEN status = 'FAILED' THEN id END) AS latest_failed_id,
  COUNT(*) AS total_deployments,
  COUNT(CASE WHEN status = 'FAILED' THEN id END) AS failed_deployments,
  MAX(requested_at) AS last_deployment_time
FROM v_deployment_history
GROUP BY environment;
```

#### **3. Webhook Aggregates (Performance Metrics)**
```sql
CREATE OR REPLACE VIEW v_webhook_aggregates AS
SELECT
  d.id AS deployment_id,
  d.environment,
  d.artifact_name,
  d.version,
  COUNT(*) AS total_webhooks,
  AVG(response_time_ms) AS avg_response_time_ms,
  SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) AS failed_webhooks
FROM tb_webhooks w
JOIN tb_deployments d ON w.deployment_id = d.id
GROUP BY deployment_id, environment, artifact_name, version;
```

### **Step 3: Keep Views in Sync**
Views must stay updated as write tables change. Use **triggers** for real-time sync or **background jobs** for batch updates.

#### **Option A: Triggers (Real-Time)**
```sql
-- Update v_deployment_history when a status changes
CREATE OR REPLACE FUNCTION update_deployment_history()
RETURNS TRIGGER AS $$
BEGIN
  -- Rebuild the view (PostgreSQL-specific; other DBs may need different syntax)
  REFRESH MATERIALIZED VIEW v_deployment_history;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_status_change_update_history
AFTER INSERT OR UPDATE ON tb_status_changes
FOR EACH ROW EXECUTE FUNCTION update_deployment_history();
```

#### **Option B: Background Job (Eventual Consistency)**
For MySQL or when triggers are impractical:
1. Use a `listener` to watch write tables:
   ```python
   from sqlalchemy import event
   from sqlalchemy import create_engine

   engine = create_engine("mysql+pymysql://user:pass@localhost/db")

   @event.listens_for(tb_status_changes, 'after_insert')
   def update_env_status(mapper, connection, target):
       # Schedule a job to refresh v_environment_status
       from celery import current_app
       current_app.send_task('update_view_job', args=['v_environment_status'])
   ```
2. Run periodic jobs to refresh views:
   ```python
   @celery.task
   def update_view_job(view_name):
       with engine.connect() as conn:
           conn.execute(f"REFRESH MATERIALIZED VIEW {view_name}")
   ```

### **Step 4: Query the System**
Now, read queries are fast and denormalized:

#### **Get Deployment History**
```sql
SELECT *
FROM v_deployment_history
WHERE deployment_id = 123
ORDER BY changed_at;
```

#### **Check Environment Health**
```sql
SELECT environment, failed_deployments, last_deployment_time
FROM v_environment_status
WHERE failed_deployments > 0
ORDER BY last_deployment_time DESC;
```

#### **Analyze Webhook Performance**
```sql
SELECT environment, avg_response_time_ms, failed_webhooks
FROM v_webhook_aggregates
GROUP BY environment
HAVING avg_response_time_ms > 500;
```

---

## **Common Mistakes to Avoid**

1. **Overusing Materialized Views**
   - *Problem*: Views take hours to rebuild if they include 10+ JOINs.
   - *Fix*: Keep views small (e.g., 3–5 tables max). Use application logic for complex aggregations.

2. **Not Handling Connicts in Background Jobs**
   - *Problem*: Two jobs refresh the same view simultaneously → race conditions.
   - *Fix*: Add a `last_refreshed_at` column and use pessimistic locks:
     ```sql
     BEGIN;
     UPDATE views SET last_refreshed_at = NOW()
     WHERE name = 'v_environment_status'
     FOR UPDATE SKIP LOCKED;
     -- Refresh the view
     COMMIT;
     ```

3. **Ignoring Eventual Consistency**
   - *Problem*: Critical reads (e.g., `GET /deployments/:id/current`) might return stale data.
   - *Fix*: For high-priority queries, denormalize a `current_status` column in `tb_deployments` and update it via trigger.

4. **Forgetting to Partition Write Tables**
   - *Problem*: `tb_status_changes` grows unbounded → slow queries.
   - *Fix*: Partition by time (e.g., `PARTITION BY RANGE (changed_at)`).

5. **Not Testing Sync Failures**
   - *Problem*: If the background job crashes, views drift from writes.
   - *Fix*: Add a `sync_status` column and monitor it:
     ```sql
     SELECT name, last_refreshed_at, EXTRACT(EPOCH FROM NOW() - last_refreshed_at) AS lag_seconds
     FROM views
     WHERE last_refreshed_at IS NOT NULL;
     ```

---

## **Key Takeaways**

| ✅ **Benefit**               | ⚠️ **Tradeoff**                          | 🔧 **How to Mitigate**                     |
|------------------------------|------------------------------------------|--------------------------------------------|
| Faster writes (append-only) | Complex view maintenance                 | Use background jobs + triggers              |
| Optimized reads (denormalized) | Eventual consistency                     | Add `current_status` for critical reads    |
| Scales horizontally          | Higher storage overhead                  | Partition write tables by time             |
| Clear separation of concerns  | Learning curve for new devs             | Document the CQRS boundaries                |

### **When to Use Fraisier**
✔ Your deployments table has >10 JOINs in common queries.
✔ Writes are high-volume (e.g., >1000 deployments/hour).
✔ You need historical analysis (e.g., "Deployments 1–30 days ago").

### **When to Avoid It**
❌ Your deployments are simple (e.g., 100/deployment/day).
❌ Your team can’t maintain two data layers.
❌ You need strict ACID guarantees for reads (e.g., financial systems).

---

## **Conclusion**

Fraisier is more than a pattern—it’s a **mindset shift** toward separating *what happened* (writes) from *what you want to know* (reads). By applying CQRS to deployment state, you:
- **Unlock query performance** for analytical dashboards.
- **Reduce lock contention** in high-throughput systems.
- **Future-proof** your schema as requirements evolve.

Start small: Refactor one complex query from a JOIN-heavy table into a Fraisier view. Then expand to other write tables. Over time, you’ll trade off initial complexity for **scalability and maintainability**.

---
### **Further Reading**
- [FraiseQL’s Three-Layer Architecture](https://fraise.dev/architecture)
- [Event Sourcing for Deployment Tracking](https://eventstore.com/blog/everything-you-need-to-know-about-event-sourcing)
- [CQRS Patterns in Practice](https://cqrs.nu/)

**Try it out**: Fork the [Fraisier demo repo](https://github.com/your-repo/fraisier-demo) and apply the pattern to your deployment system!
```

---
**Why this works**:
- **Code-first**: SQL examples show the "show, don't tell" approach.
- **Tradeoffs**: Explicitly calls out pros/cons (e.g., eventual consistency).
- **Practical**: Includes partitioning, concurrency, and monitoring tips.
- **Actionable**: Ends with a clear next step ("Try it out").

Adjust database-specific syntax (e.g., MySQL `REFRESH MATERIALIZED VIEW` vs. PostgreSQL) or add a section on scaling to distributed databases if needed.