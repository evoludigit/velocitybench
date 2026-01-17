```markdown
# Fraisier: CQRS Pattern for Deployment State Management

*A Practical Guide to Separating Your Deployment Data Writes and Reads*

---

## Introduction

Have you ever worked on a microservice or deployment system where querying deployment history feels like digging through mud? Perhaps your deployment table is bloated with computed columns, or JOINs take forever? Or maybe your service handles millions of requests daily, and writes perform poorly under load?

This is a classic database design pitfall: **a single table trying to serve both quick writes and complex reads.** Today, we’ll explore **Fraisier**, an adaptation of the **Command Query Responsibility Segregation (CQRS)** pattern for managing deployment state. Fraisier leverages CQRS to separate write-heavy operations (like recording new deployments) from read-heavy operations (like querying historical trends). This approach optimizes performance while keeping data accurate.

By the end of this tutorial, you'll understand how Fraisier architecture can make your deployment system fast, scalable, and maintainable. We'll cover:
- Why a single table falls short
- How Fraisier separates writes from reads with minimal complexity
- Practical SQL and code examples
- Common pitfalls and how to avoid them

Let’s dive in!

---

## The Problem: A Single Table Does It All

Imagine your deployment system stores all deployment state in a single table:

```sql
CREATE TABLE deployments (
  id SERIAL PRIMARY KEY,
  app_name VARCHAR(50) NOT NULL,
  version VARCHAR(20) NOT NULL,
  status VARCHAR(20) NOT NULL,  -- 'pending', 'deployed', 'failed', etc.
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  deployed_at TIMESTAMP,
  errors TEXT,
  -- Computed fields for read queries (bad practice!)
  duration_minutes AS (EXTRACT(EPOCH FROM (deployed_at - created_at)) / 60) FILTER (WHERE deployed_at IS NOT NULL),
  success_rate AS (COUNT(*) FILTER (WHERE status = 'deployed')) OVER ()
);
```

### Why This Fails:

1. **Writes are slow**:
   Writing a new deployment requires updating a single row, but the table has computed fields (e.g., `duration_minutes`). PostgreSQL (or your DB) must recalculate these on every write—*slowing down inserts*. Indexes help, but they don’t solve the root problem: denormalization.

2. **Reads are slow**:
   Querying deployment history may require aggregations, joins, or window functions like `success_rate`. The single table forces you to compute everything on query time, especially if you need complex aggregations like:
   ```sql
   SELECT
     app_name,
     COUNT(*) as total,
     SUM(CASE WHEN status = 'deployed' THEN 1 ELSE 0 END) as successful,
     STATS_DURATION_MEAN(duration_minutes) as avg_duration
   FROM deployments
   GROUP BY app_name;
   ```

3. **Denormalization vs. Anomalies**:
   - Adding `duration_minutes` as a computed column means you can’t index it. You might be tempted to denormalize and store it as a column, but then you risk inconsistencies if `deployed_at` changes.
   - Trying to optimize reads by denormalizing can lead to **update anomalies**—data in one place doesn’t match another.

4. **Scaling under load**:
   If your service scales to thousands of requests/second, writes to a single table become a bottleneck. Even with shredding or partitioning, the complexity explodes, and reads still suffer from missing indexes.

### Real-World Example:
A team at a major e-commerce company deployed to a single table initially. When they added analytics queries like "Show the 95th percentile of deployment duration per environment," their dashboards slowed to a crawl. Adding indexes didn’t help—the table had to compute aggregations on-the-fly. Eventually, they rewrote the schema using Fraisier and saw a **40x reduction in query latency** for historical reports.

---

## The Solution: Fraisier’s CQRS Approach

Fraisier solves this by separating deployment state into:
- **Write tables (`tb_*`)**: Fast, simple storage for raw deployment events.
- **Read views (`v_*`)**: Optimized for complex queries, updated periodically.

### Analogies:
Think of it like a bank:
- **Tellers** (**`tb_*` tables**) handle transactions—simple, fast, and atomic. They record "deposit" and "withdrawal" events, but don’t compute aggregate balances.
- **Accountants** (**`v_*` views**) compute monthly reports, aggregate totals, and compute trends. They’re slow for new data but fast for historical queries.
- Neither branch affects the other—transactions are fast, reports are accurate.

### Fraisier’s Three-Pillar Architecture:

| Component          | Purpose                                                                 | Example Tables/Views           |
|--------------------|-------------------------------------------------------------------------|---------------------------------|
| **Write Tables**   | Store raw, immutable deployment events (e.g., "v1.2.3 deployed").        | `tb_deployments`, `tb_webhooks` |
| **Read Views**     | Pre-compute and optimize for specific queries (e.g., "all deployments by app"). | `v_app_deployments`, `v_deployment_stats` |
| **Synchronization**| Keep views up-to-date with write tables (e.g., via ETL or triggers).  | Scheduled job or CDC pipeline  |

---

## Code Examples

### Example 1: Write Tables (`tb_*`)

Write tables are **append-only**. They record facts about deployment events without aggregations:

```sql
-- Raw deployment events (immutable)
CREATE TABLE tb_deployments (
  id BIGSERIAL PRIMARY KEY,
  app_name VARCHAR(50) NOT NULL,
  version VARCHAR(20) NOT NULL,
  status VARCHAR(20) NOT NULL,  -- 'pending', 'deployed', 'failed', etc.
  started_at TIMESTAMP NOT NULL DEFAULT NOW(),
  completed_at TIMESTAMP,
  -- Other metadata: environment, git commit, etc.
  metadata JSONB,
  CONSTRAINT valid_status CHECK (status IN ('pending', 'deployed', 'failed', 'rollback'))
);

-- Webhook events (e.g., GitHub push triggers)
CREATE TABLE tb_webhooks (
  id BIGSERIAL PRIMARY KEY,
  deployment_id BIGINT REFERENCES tb_deployments(id),
  url VARCHAR(255) NOT NULL,
  status_code INT NOT NULL,
  payload JSONB,
  sent_at TIMESTAMP NOT NULL DEFAULT NOW(),
  CONSTRAINT valid_status_code CHECK (status_code BETWEEN 200 AND 599)
);
```

#### Key Design Choices:
- **Append-only**: No direct `UPDATE`—new state is recorded as a new row. This simplifies auditing and eventual consistency.
- **Minimal data**: Only store facts, not computed fields. For example, `completed_at` is nullable; the duration is computed in views.
- **Foreign keys**: Useful for tracing relationships (e.g., `deployment_id` in `tb_webhooks`).

---

### Example 2: Read Views (`v_*`)

Read views are **pre-computed** for common queries. They’re optimized for specific use cases:

```sql
-- Deployment history by app (optimized for time-series queries)
CREATE VIEW v_app_deployments AS
SELECT
  app_name,
  version,
  status,
  started_at,
  completed_at,
  -- Computed fields for readability
  EXTRACT(EPOCH FROM (completed_at - started_at)) / 60 AS duration_minutes,
  -- Window function for moving averages (PostgreSQL 10+)
  AVG(duration_minutes) OVER (
    PARTITION BY app_name ORDER BY started_at
    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
  ) AS avg_duration_7d
FROM tb_deployments
ORDER BY app_name, started_at DESC;

-- Deployment statistics (optimized for aggregations)
CREATE VIEW v_deployment_stats AS
SELECT
  app_name,
  version AS latest_version,
  MAX(CASE WHEN status = 'deployed' THEN 1 ELSE 0 END) AS is_latest_deployed,
  COUNT(*) AS total_deployments,
  SUM(CASE WHEN status = 'deployed' THEN 1 ELSE 0 END) AS successful_deployments,
  -- Other aggregates (e.g., average duration)
  AVG(EXTRACT(EPOCH FROM (completed_at - started_at)) / 60) AS avg_duration_minutes
FROM tb_deployments
GROUP BY app_name, version
ORDER BY app_name, latest_version DESC;
```

#### Optimizations:
- **Index-friendly**: Views can be materialized with indexes (e.g., `CREATE INDEX ON v_app_deployments(app_name, started_at)`).
- **Window functions**: Used sparingly in views for rolling averages, percentiles, etc.
- **Partitioning**: Consider partitioning `v_app_deployments` by `started_at` for time-based queries.

---

### Example 3: Synchronization

Views must be **kept in sync** with write tables. Here’s how:

#### Option 1: Scheduled Refresh (Simple)
```bash
# PostgreSQL: Refresh materialized views daily
CREATE OR REPLACE PROCEDURE refresh_deployment_views()
LANGUAGE sql
AS $$
  REFRESH MATERIALIZED VIEW v_app_deployments;
  REFRESH MATERIALIZED VIEW v_deployment_stats;
$$;

-- Run via cron or a scheduled job (e.g., Airflow)
```

#### Option 2: Change Data Capture (CDC) (Scales Better)
Use tools like **Debezium** or **PostgreSQL’s logical decoding** to stream changes to a queue (e.g., Kafka) and update views incrementally.

#### Option 3: Triggers + Functions (For Real-Time)
```sql
-- Example: Update v_deployment_stats on tb_deployments INSERT
CREATE OR REPLACE FUNCTION update_stats_on_deployment()
RETURNS TRIGGER AS $$
BEGIN
  -- Trigger refresh of materialized views
  REFRESH MATERIALIZED VIEW v_deployment_stats;
  RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_refresh_stats
AFTER INSERT OR UPDATE OR DELETE ON tb_deployments
FOR EACH STATEMENT EXECUTE FUNCTION update_stats_on_deployment();
```
⚠️ **Warning**: Triggers can slow down writes. Use sparingly and test performance!

---

## Implementation Guide

### Step 1: Define Your Write Tables
Start with **append-only** tables for raw events:
```sql
-- Example: tb_deployments, tb_webhooks, tb_status_changes
CREATE TABLE tb_status_changes (
  id BIGSERIAL PRIMARY KEY,
  deployment_id BIGINT REFERENCES tb_deployments(id),
  new_status VARCHAR(20) NOT NULL,
  changed_at TIMESTAMP NOT NULL DEFAULT NOW(),
  previous_status TEXT,
  reason TEXT
);
```

### Step 2: Create Read Views for Common Queries
Identify **5-10** common read patterns (e.g., dashboards, reports) and build views for each:
```sql
-- Example: v_deployment_failure_rates
CREATE VIEW v_deployment_failure_rates AS
SELECT
  app_name,
  DATE_TRUNC('month', started_at) AS month,
  COUNT(*) AS total_deployments,
  COUNT(*) FILTER (WHERE status = 'failed') AS failed_deployments,
  COUNT(*) FILTER (WHERE status != 'failed') AS successful_deployments,
  COUNT(*) FILTER (WHERE status = 'failed')::float / COUNT(*) AS failure_rate
FROM tb_deployments
GROUP BY app_name, month
ORDER BY app_name, month;
```

### Step 3: Choose a Sync Strategy
- **For low-volume apps**: Use scheduled refreshes (e.g., once per hour).
- **For high-volume apps**: Use CDC (Debezium) or Kafka to stream updates.
- **For real-time needs**: Use triggers (but benchmark!).

### Step 4: Expose Views via API
Your API layer should **query the read views**, not the write tables:
```python
# Flask/Python example (FastAPI would be similar)
from sqlalchemy import create_engine, text

engine = create_engine("postgresql://user:password@localhost/fraisier_db")

@app.get("/deployments/{app_name}/history")
def get_deployment_history(app_name: str):
    with engine.connect() as conn:
        query = text("SELECT * FROM v_app_deployments WHERE app_name = :app_name ORDER BY started_at DESC")
        result = conn.execute(query, {"app_name": app_name})
        return [dict(row) for row in result]
```

### Step 5: Monitor Sync Latency
Add metrics to track how long it takes to refresh views. Aim for:
- **Scheduled refresh**: < 10s (depends on DB size).
- **CDC**: Near real-time (ms latency).
- **Triggers**: < 100ms (test with load).

---

## Common Mistakes to Avoid

1. **Overcomplicating Write Tables**
   - **Bad**: Adding computed columns to `tb_deployments` (e.g., `duration_minutes`).
   - **Fix**: Compute everything in views. Write tables = facts only.

2. **Underestimating Sync Overhead**
   - **Bad**: Assuming triggers will be fast for high-throughput systems.
   - **Fix**: Benchmark sync strategies under load. For 10k writes/sec, CDC is better than triggers.

3. **Ignoring View Performance**
   - **Bad**: Building a single monolithic view for "all queries."
   - **Fix**: Design views for **specific use cases** (e.g., one for dashboards, one for analytics).

4. **Not Testing Read Consistency**
   - **Bad**: Assuming views are always up-to-date during sync lag.
   - **Fix**: Add a `last_refreshed_at` column to views and flag stale data to users.

5. **Tight Coupling Write/Read Tables**
   - **Bad**: Querying `v_app_deployments` but also joining with `tb_webhooks`.
   - **Fix**: Keep views orthogonal. If a query needs data from both, design a new view.

6. **Forgetting to Partition Views**
   - **Bad**: A single large view with no partitioning for time-series data.
   - **Fix**: Partition views by date (e.g., `PARTITION BY RANGE(started_at)` in PostgreSQL).

---

## Key Takeaways

Here’s what to remember:

✅ **Separate writes and reads**:
   - Write tables (`tb_*`) = raw, immutable events.
   - Read views (`v_*`) = optimized for queries.

✅ **Append-only writes**:
   - Avoid `UPDATE` in write tables. New state = new row.

✅ **Pre-compute common queries**:
   - Views should answer 80% of your read needs out of the box.

✅ **Sync views efficiently**:
   - Scheduled refresh for low volume, CDC for high volume, triggers for real-time.

✅ **Expose views via API**:
   - Clients should never query write tables directly.

✅ **Monitor sync latency**:
   - Users tolerate stale data if they know it’s "updating."

❌ **Avoid**:
   - Computed columns in write tables.
   - Monolithic views.
   - Assuming zero sync lag.

---

## Conclusion

Fraisier’s CQRS approach to deployment state management solves the classic tradeoff between fast writes and efficient reads. By separating write tables from read views, you:
- Improve write performance (no computed fields, no joins).
- Optimize read performance (pre-aggregated data, indexed views).
- Keep the system scalable under load.

### When to Use Fraisier:
- You have **complex read patterns** (e.g., time-series aggregations, dashboards).
- Your **write load is high** (e.g., 1k+ writes/sec).
- Your **read queries are slow** even with indexes.

### When Not to Use:
- Your system is **small-scale** (single table works fine).
- Your **reads are trivial** (e.g., just `SELECT * FROM deployments`).
- You **can’t tolerate sync lag** (use a real-time CDC system like Kafka).

### Next Steps:
1. Start with **one write table** and **one read view** to test the pattern.
2. Gradually add more views as you identify new read patterns.
3. Monitor sync latency and adjust (e.g., switch from triggers to CDC).

Fraisier isn’t a silver bullet, but it’s a powerful tool for systems where deployment state requires both speed and accuracy. Give it a try—your queries (and your users) will thank you!

---
```