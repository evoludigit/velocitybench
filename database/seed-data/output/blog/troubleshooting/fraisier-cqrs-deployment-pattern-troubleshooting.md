# **Debugging Fraisier (CQRS for Deployment State Management): A Troubleshooting Guide**

## **Introduction**
Fraisier implements a **CQRS (Command Query Responsibility Segregation) pattern** for tracking deployment states by separating **write-heavy** (`tb_*`) and **read-optimized** (`v_*`) schemas. This design ensures scalability by offloading analytics workloads from transactional tables.

However, misconfigurations in indexing, query design, or event sourcing can degrade performance. This guide covers common issues, diagnostic steps, and fixes to resolve bottlenecks.

---

## **1. Symptom Checklist**
Before diving into fixes, verify which symptoms apply to your system:

| **Symptom** | **Description** | **Severity** |
|-------------|----------------|-------------|
| **Slow deployment history queries** | `SELECT * FROM v_deployment_history WHERE env='prod'` takes >1s | High |
| **High CPU on analytics tables** | `v_*` tables under heavy scan operations in monitoring | Medium |
| **Lock contention on write tables** | Long-running `INSERT`/`UPDATE` on `tb_deployment_logs` | High |
| **Inconsistent reports** | Stats differ between API calls and direct DB queries | Medium |
| **Frequent timeouts** | Event processing (e.g., `deployment_state_change`) fails | Critical |
| **Large transaction logs** | `pg_stat_activity` shows long-lived transactions on `tb_*` tables | High |

---

## **2. Common Issues & Fixes**

### **Issue 1: Slow Deployment History Queries**
**Root Cause:** Missing indexes on `v_deployment_history` or inefficient query patterns.

#### **Debugging Steps:**
1. **Check the query plan:**
   ```sql
   EXPLAIN ANALYZE
   SELECT * FROM v_deployment_history
   WHERE env = 'prod' ORDER BY timestamp DESC LIMIT 10000;
   ```
   - Look for `Seq Scan` on large tables (indicator of missing indexes).
   - High `cost` in the plan suggests suboptimal execution.

2. **Verify indexing:**
   ```sql
   SELECT * FROM pg_stat_user_indexes
   WHERE tablename = 'v_deployment_history';
   ```
   - Ensure composite indexes exist for `env` + `timestamp`.

#### **Fix:**
Add missing index:
```sql
CREATE INDEX idx_v_deployment_history_env_timestamp ON v_deployment_history (env, timestamp DESC);
```

---

### **Issue 2: Complex Joins for Statistics**
**Root Cause:** Statistics queries requiring multiple joins on `v_*` tables perform poorly due to lack of materialized views or optimizations.

#### **Debugging Steps:**
1. **Analyze the query:**
   ```sql
   EXPLAIN ANALYZE
   SELECT d.env, COUNT(*) as success_count, AVG(t.duration)
   FROM v_deployment_history d
   JOIN v_deployment_stats s ON d.id = s.deployment_id
   WHERE d.timestamp > NOW() - INTERVAL '7 days'
   GROUP BY d.env;
   ```
   - Check for nested loops (`Nested Loop`) or hash joins (`Hash Join`).

2. **Optimize with materialized views:**
   ```sql
   CREATE MATERIALIZED VIEW mv_7day_deployment_stats AS
   SELECT env, COUNT(*) as success_count, AVG(duration)
   FROM v_deployment_history
   WHERE timestamp > NOW() - INTERVAL '7 days'
   GROUP BY env;
   ```
   - Refresh periodically with `REFRESH MATERIALIZED VIEW mv_7day_deployment_stats;`

---

### **Issue 3: Denormalized Schema (Write Conflicts)**
**Root Cause:** Redundant columns in `v_*` tables cause update conflicts when syncing with `tb_*` tables.

#### **Debugging Steps:**
1. **Check for concurrent writes:**
   ```sql
   SELECT * FROM pg_stat_activity
   WHERE query LIKE '%INSERT INTO tb_deployment_logs%';
   ```
   - High contention suggests race conditions.

2. **Verify event sourcing consistency:**
   - Ensure `tb_deployment_logs` emits events (`deployment_started`, `deployment_completed`) to a message queue.
   - Validate that `v_deployment_history` is updated via event listeners.

#### **Fix:**
- **Option 1: Use CDC (Change Data Capture)**
  ```python
  # Example: Debezium-based CDC listener (Kafka/Postgres)
  def handle_deployment_event(event):
      if event['type'] == 'insert':
          update_materialized_view(event['payload'])
  ```
- **Option 2: Batch updates**
  ```sql
  CREATE OR REPLACE FUNCTION sync_deployment_stats()
  RETURNS VOID AS $$
  BEGIN
      -- Batch load from tb_* to v_*
      INSERT INTO v_deployment_history
      SELECT * FROM tb_deployment_logs WHERE timestamp > last_sync;
  END;
  $$ LANGUAGE plpgsql;
  ```

---

### **Issue 4: Update Conflicts in Statistics**
**Root Cause:** Real-time sync between `tb_*` and `v_*` causes deadlocks.

#### **Debugging Steps:**
1. **Check deadlocks:**
   ```sql
   SELECT * FROM pg_locks WHERE mode = 'ExclusiveLock';
   ```
   - Look for blocked transactions holding locks on `v_*` tables.

2. **Analyze lock contention:**
   ```sql
   SELECT * FROM pg_stat_database
   WHERE datname = 'your_db' AND n_deadlocks > 0;
   ```

#### **Fix:**
- **Use optimistic concurrency control:**
  ```sql
  UPDATE v_deployment_history
  SET success_rate = :new_rate
  WHERE id = :id AND success_rate = :current_rate;
  ```
- **Partition large tables:**
  ```sql
  CREATE TABLE v_deployment_history (
      id SERIAL,
      env TEXT,
      timestamp TIMESTAMPTZ,
      success_rate NUMERIC,
      PRIMARY KEY (env, timestamp)
  ) PARTITION BY RANGE (timestamp);
  ```

---

## **3. Debugging Tools & Techniques**
### **A. Database-Level Tools**
| Tool | Purpose |
|------|---------|
| `EXPLAIN ANALYZE` | Identify slow queries and missing indexes. |
| `pg_stat_statements` | Track top resource-consuming queries. |
| `pgBadger` | Log analysis for slow query patterns. |
| `Redis (Cache)** | Cache frequently accessed `v_*` read models. |

### **B. Application-Level Debugging**
1. **Enable query logging (PostgreSQL):**
   ```conf
   logging_collector = on
   log_statement = 'all'
   log_min_duration_statement = 500ms
   ```
2. **Use APM tools (Datadog, New Relic):**
   - Track deployment event latencies.
3. **Validate event ordering:**
   - Log event IDs and timestamps before processing.

### **C. Distributed Tracing**
- If using Kafka/RabbitMQ, enable **tracing headers**:
  ```python
  # Example: Structured logging
  logger.debug(f"Processing event {event.id} (queue: {queue_name})")
  ```
- Use OpenTelemetry to trace end-to-end latency.

---

## **4. Prevention Strategies**
### **A. Schema Design**
- **Keep `tb_*` tables normalized** (write-optimized).
- **Denormalize `v_*` tables** for read performance (accept eventual consistency if needed).
- **Use columnar storage** (e.g., ClickHouse, BigQuery) for analytics.

### **B. Indexing Strategy**
- **Composite indexes** for common query patterns:
  ```sql
  CREATE INDEX idx_v_deployment_history_env_date ON v_deployment_history (env, date_trunc('day', timestamp));
  ```
- **Partial indexes** for filtering:
  ```sql
  CREATE INDEX idx_v_deployment_history_success ON v_deployment_history (success_flag) WHERE success_flag IS TRUE;
  ```

### **C. Event Sourcing Best Practices**
- **Batch events** to reduce database load:
  ```python
  # Example: Kafka producer with batching
  producer.flush(max_messages=100)
  ```
- **Use idempotent event processing** to avoid duplicates.

### **D. Monitoring & Alerts**
- **Set up alerts** for:
  - High latency in `v_*` queries.
  - Deadlocks in `tb_*` tables.
  - Backlog in event processing queues.
- **Example Prometheus alert:**
  ```yaml
  - alert: SlowDeploymentQuery
    expr: pg_stat_statements.query > 1000 AND pg_stat_statements.mean_time > 1000ms
    for: 5m
    labels:
      severity: warning
  ```

---

## **Conclusion**
Fraisier’s CQRS pattern excels at separating write and read workloads but requires careful tuning to avoid bottlenecks. Focus on:
1. **Indexing** (`v_*` tables) for fast reads.
2. **Event sourcing consistency** to sync `tb_*` ↔ `v_*`.
3. **Monitoring** to detect lock contention early.
4. **Caching** for high-frequency reads.

By following this guide, you can quickly diagnose and resolve performance issues while maintaining scalability.

---
**Further Reading:**
- [CQRS Patterns in Practice](https://martinfowler.com/articles/201701/event-consistency.html)
- [PostgreSQL Performance Tuning](https://www.postgresql.org/docs/current/performance-tuning.html)