# **Debugging "View Naming Convention (v_*, tv_*, mv_*, av_*)" – A Troubleshooting Guide**

## **1. Introduction**
View naming conventions like `v_*`, `tv_*`, `mv_*`, and `av_*` are meant to improve code readability by categorizing views based on their purpose (e.g., virtual, temporary, materialized, aggregated). However, misapplications can lead to confusion about semantics, materialization status, and data consistency.

This guide helps diagnose and resolve common issues related to this pattern while ensuring clarity and maintainability.

---

## **2. Symptom Checklist**
Check for these signs that your view naming convention may be misused or misunderstood:

| **Symptom** | **Description** | **Impact** |
|-------------|----------------|------------|
| **Inconsistent prefixes** | Views use `v_` for both virtual and materialized views. | Ambiguity in data persistence. |
| **Missing documentation** | No comments explaining `tv_*` (temporary views) or `mv_*` (materialized). | Developers assume incorrect semantics. |
| **Performance misalignment** | `mv_*` views are rarely queried, but `v_*` views are slow. | Poor query optimization. |
| **Schema drift** | Views are modified without updating prefixes (e.g., `v_users` → `mv_users`). | Desync between naming and functionality. |
| **"Why does this run slow?"** | Developers query `v_*` views without knowing they’re not materialized. | Unoptimized queries. |
| **Overuse of `tv_*`** | Temporary views persist longer than intended. | Storage bloat, missed cleanup. |

If multiple symptoms appear, the naming convention is likely **misconfigured or misapplied**.

---

## **3. Common Issues & Fixes**

### **3.1 Issue: Ambiguous View Types (e.g., `v_*` for Everything)**
**Problem:** Developers use `v_*` for all views, losing clarity on materialization status.
**Example:**
```sql
-- What is this? Virtual or materialized?
CREATE VIEW v_users AS SELECT * FROM users;

-- What about this?
CREATE MATERIALIZED VIEW mv_orders AS SELECT * FROM orders;
```

**Solution:**
- **Enforce strict prefixes:**
  - `v_*` → **Virtual views** (recomputed on query).
  - `tv_*` → **Temporary views** (session-scoped, auto-cleaned).
  - `mv_*` → **Materialized views** (precomputed, refreshable).
  - `av_*` → **Aggregate views** (e.g., metrics, KPIs).

**Code Fix:**
```sql
-- Correct usage:
CREATE VIEW v_user_activity AS SELECT * FROM activity_logs;  -- Virtual (slow for large joins)
CREATE MATERIALIZED VIEW mv_daily_sales AS SELECT * FROM sales WHERE date = CURRENT_DATE;  -- Precomputed
```

---

### **3.2 Issue: Temporary Views (`tv_*`) Persisting Unintentionally**
**Problem:** Temporary views (e.g., for debugging) are left behind, consuming storage.
**Example:**
```sql
-- Accidentally created a permanent view instead of a temp session view:
CREATE OR REPLACE TEMPORARY VIEW tv_debug_data AS SELECT * FROM logs LIMIT 1000;
-- If `TEMPORARY` is missing, it persists!
```

**Solution:**
- **Always declare temporary views explicitly:**
  ```sql
  CREATE TEMPORARY VIEW tv_debug_logs AS
    SELECT id, timestamp, message
    FROM application_logs
    WHERE level = 'ERROR';
  ```
- **Use DBMS-specific temp view handling:**
  - **PostgreSQL:** `CREATE TEMP VIEW` (session-scoped).
  - **BigQuery:** `CREATE TEMP TABLE` (session-only).
  - **Snowflake:** `CREATE OR REPLACE TEMPORARY VIEW` (auto-cleaned on session end).

**Debugging:**
Check if unwanted views exist:
```sql
-- PostgreSQL
SELECT viewname FROM pg_views WHERE viewname LIKE 'tv_%';

-- Snowflake
SELECT name FROM information_schema.views WHERE table_name LIKE 'tv_%';
```

---

### **3.3 Issue: Materialized Views (`mv_*`) Not Updated**
**Problem:** `mv_*` views are stale because they weren’t refreshed.
**Example:**
```sql
-- Materialized view for daily sales, but it hasn’t been refreshed in weeks.
CREATE MATERIALIZED VIEW mv_sales_summary AS
  SELECT product_id, SUM(amount) FROM orders GROUP BY product_id;
```

**Solution:**
- **Implement a refresh policy:**
  ```sql
  -- PostgreSQL: Use `REFRESH MATERIALIZED VIEW`
  REFRESH MATERIALIZED VIEW mv_sales_summary;

  -- BigQuery: Use `bgcreate` + scheduled refreshes.
  ```
- **Automate refreshes** via:
  - **Cron jobs** (e.g., `cron` in Linux, Cloud Scheduler in GCP).
  - **DB triggers** (e.g., PostgreSQL `pg_cron`).
  - **ORM hooks** (e.g., Django signals, Python `schedule` library).

**Debugging:**
Verify last refresh time:
```sql
-- PostgreSQL
SELECT m.relkind, relname, pg_last_autovacuum(oid)
FROM pg_class m
JOIN pg_namespace n ON n.oid = m.relnamespace
WHERE n.nspname = 'public' AND m.relname LIKE 'mv_%';
```

---

### **3.4 Issue: Schema Changes Break Views**
**Problem:** A table’s schema change (e.g., column dropped) breaks dependent views.
**Example:**
```sql
-- Original table:
ALTER TABLE users ADD COLUMN is_active BOOLEAN;

-- Old view fails:
SELECT * FROM v_user_stats;  -- Error: "column is_active does not exist"
```

**Solution:**
- **Use schema validation tools:**
  - **Great Expectations** (for data profiling).
  - **Schematics** (schema migration monitoring).
- **Document dependencies:**
  ```sql
  -- Add a comment in the view:
  CREATE VIEW v_user_stats AS
    SELECT user_id, COUNT(*) as order_count
    FROM orders
    GROUP BY user_id
    /* DEPENDS_ON: users(user_id), orders(user_id) */
  ;
  ```

**Debugging:**
Check for broken dependencies:
```sql
-- PostgreSQL: Query inheritance constraints.
SELECT conname, conrelid::regclass AS table_name
FROM pg_constraint
WHERE conrelid IN (SELECT oid FROM pg_class WHERE relkind = 'v');
```

---

### **3.5 Issue: Performance Misalignment (Slow `v_*` vs. Fast `mv_*`)**
**Problem:** Developers query `v_*` views expecting materialized performance.
**Example:**
```sql
-- This runs slowly because it’s a virtual view:
SELECT * FROM v_all_orders;

-- But this is fast (materialized):
SELECT * FROM mv_important_orders;
```

**Solution:**
- **Add metadata comments:**
  ```sql
  CREATE VIEW v_all_orders AS SELECT * FROM orders
  /* WARNING: THIS IS A VIRTUAL VIEW (NOT MATERIALIZED!) */;
  ```
- **Use materialized views for high-frequency queries:**
  ```sql
  -- Example: Materialize only the top 100 high-value orders.
  CREATE MATERIALIZED VIEW mv_high_value_orders AS
    SELECT * FROM orders
    WHERE customer_id IN (SELECT customer_id FROM customers WHERE tier = 'premium')
    LIMIT 100;
  ```

**Debugging:**
Profile query performance:
```sql
-- PostgreSQL: Use EXPLAIN ANALYZE
EXPLAIN ANALYZE SELECT * FROM v_all_orders WHERE order_date > '2023-01-01';
```

---

## **4. Debugging Tools & Techniques**

### **4.1 Query View Dependencies**
**Tool:** `pg_query_tools` (PostgreSQL) or `INFORMATION_SCHEMA` (standard SQL).
**Command:**
```sql
-- PostgreSQL: Find tables referenced by a view.
SELECT depname AS dependency
FROM pg_depend
WHERE objid IN (
  SELECT oid FROM pg_class WHERE relname = 'v_orders'
);
```

### **4.2 Check for Orphaned Views**
**Tool:** Database-specific metadata queries.
**Example (PostgreSQL):**
```sql
-- Find unused views (no queries in last 30 days).
SELECT schemaname, v.relname
FROM pg_stat_user_views v
JOIN pg_class c ON v.relname = c.relname
WHERE last_query IS NULL AND schemaname NOT IN ('pg_catalog', 'information_schema');
```

### **4.3 Validate Prefix Consistency**
**Tool:** Custom scripts or CI checks.
**Example (Python):**
```python
import psycopg2

conn = psycopg2.connect("dbname=my_db")
cursor = conn.cursor()

cursor.execute("SELECT table_name FROM information_schema.views WHERE table_name LIKE 'v_%'")
views = cursor.fetchall()

for view in views:
    if view[0].startswith('mv_') or view[0].startswith('tv_'):
        print(f"ERROR: View {view[0]} has inconsistent prefix!")
```

### **4.4 Use ORM Annotations (Django, SQLAlchemy)**
**Example (Django):**
```python
# models.py
class UserActivityView(View):
    name = 'v_user_activity'  # Explicitly mark as virtual
    query = "SELECT * FROM activity_logs"
```
**OR:**
```python
# SQLAlchemy (via extensions like `sqlalchemy-utils`)
@metadata.reflectable_table(
    name="v_user_stats",
    view=True,  # Mark as virtual view
    columns={
        "user_id": Column(Integer),
        "total_orders": Column(Integer)
    }
)
```

---

## **5. Prevention Strategies**

### **5.1 Enforce Naming Rules via CI/CD**
- **GitHub Actions / GitLab CI:**
  ```yaml
  - name: Check view naming convention
    run: |
      if grep -E '^CREATE VIEW [^_][^v_]' *.sql; then
        echo "ERROR: View must start with v_*, mv_*, tv_*, or av_*"
        exit 1
      fi
  ```
- **Pre-commit hooks** (Python example):
  ```python
  # pre_commit.py
  import re

  def check_view_names(file):
      with open(file) as f:
          content = f.read()
      if re.search(r"CREATE VIEW [^vmt_]", content):
          print(f"ERROR: {file} has improper view prefix!")
          return False
      return True
  ```

### **5.2 Document View Purposes in Comments**
**Example:**
```sql
-- =============================================
-- v_customer_segmentation: Virtual view of customer segments.
--   - NOT MATERIALIZED (runs slowly on large datasets).
--   - Depends on: customers, order_history.
-- =============================================
CREATE VIEW v_customer_segmentation AS
  SELECT
    customer_id,
    CASE WHEN total_spend > 1000 THEN 'high_value'
         WHEN total_spend > 500 THEN 'medium'
         ELSE 'low' END AS segment
  FROM (
    SELECT customer_id, SUM(amount) as total_spend
    FROM orders
    GROUP BY customer_id
  ) AS spends
  JOIN customers USING (customer_id);
```

### **5.3 Use ORM/Query Builders for Consistency**
- **SQLAlchemy:**
  ```python
  # Automatically prefix views in models.
  class MaterializedView(Base):
      __table_args__ = {'view': True, 'prefix': 'mv_'}

      __table__ = db.Table(
          'mv_customer_stats',
          Column('customer_id', Integer),
          Column('avg_order_value', Float)
      )
  ```
- **Prisma (TypeScript):**
  ```typescript
  // In schema.prisma:
  model MaterializedView {
    id     Int    @id @default(autoincrement())
    name   String @map("mv_${name}")  // Auto-prefixed as mv_*
  }
  ```

### **5.4 Schedule Regular View Audits**
- **Monthly report:**
  ```sql
  -- Find views not queried in the last 30 days.
  SELECT schemaname, v.relname
  FROM pg_stat_user_views v
  WHERE last_query IS NULL
    AND schemaname NOT IN ('pg_catalog', 'information_schema');
  ```
- **Automate cleanup of unused `tv_*` views:**
  ```sql
  -- Drop temp views older than 7 days.
  DROP VIEW IF EXISTS tv_temp_data_20230701;
  ```

### **5.5 Train Teams on Naming Conventions**
- **Convention Cheat Sheet:**
  | Prefix | Type          | Use Case                          | Example                          |
  |--------|---------------|-----------------------------------|----------------------------------|
  | `v_`   | Virtual       | Ad-hoc queries, small datasets     | `v_user_sessions`                 |
  | `tv_`  | Temporary     | Debugging, session-scoped          | `tv_debug_logs`                   |
  | `mv_`  | Materialized  | Precomputed, high-frequency data   | `mv_daily_revenue`                |
  | `av_`  | Aggregate     | Metrics, KPIs                      | `av_monthly_growth`               |

---

## **6. Summary of Key Actions**
| **Issue**               | **Quick Fix**                          | **Long-Term Solution**               |
|-------------------------|----------------------------------------|--------------------------------------|
| Inconsistent prefixes   | Audit views with `LIKE 'v_%'` queries. | Enforce CI/CD checks.                |
| Stale materialized views| Run `REFRESH MATERIALIZED VIEW`.      | Schedule automated refreshes.        |
| Unused temp views       | Drop with `DROP VIEW IF EXISTS`.      | Add TTL or auto-cleanup logic.       |
| Performance confusion   | Add `/* WARNING */` comments.         | Materialize slow virtual views.      |
| Schema drift            | Check `pg_depend` for dependencies.   | Use schema migration tools.          |

---

## **7. Final Checklist for Resolution**
1. **Audit all views** for correct prefixes (`v_`, `mv_`, `tv_`, `av_`).
2. **Refresh materialized views** and set up automation.
3. **Drop orphaned `tv_*` views** and implement cleanup policies.
4. **Update documentation** with view purposes and dependencies.
5. **Enforce naming rules** via CI/CD or ORM constraints.
6. **Monitor query performance** and suggest materialization where needed.

By following this guide, you’ll resolve ambiguity in view semantics and ensure consistent, maintainable naming conventions.