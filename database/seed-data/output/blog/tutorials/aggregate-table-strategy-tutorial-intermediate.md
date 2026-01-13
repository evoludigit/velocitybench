```markdown
# **Aggregate Tables (ta_*) for Pre-Computed Rollups: Faster Queries at a Cost**

*Trade storage for speed: How to build dashboards that load in milliseconds, not minutes.*

---

## **Introduction**

Imagine you’re running a high-traffic analytics platform with billions of records in your fact table. Every time a user refreshes a dashboard, your database takes **5-10 seconds** to compute a simple `GROUP BY`. Meanwhile, your team spends **hours** each day re-running the same aggregations for reports.

This is the **billions-of-rows problem**—where raw performance just won’t cut it. The solution? **Pre-compute everything you can, query the pre-computed data instead.**

Enter **Aggregate Tables**—a database design pattern where we store pre-aggregated results in separate tables (often prefixed with `ta_*`) at different time granularities. These tables mirror the structure of your fact tables but contain only pre-calculated rollups (sums, counts, averages) for faster queries.

Think of it like this:

| **Raw Fact Table** | **Aggregate Tables** |
|--------------------|----------------------|
| 100 million rows   | 365 daily aggregates |
| Slow queries (5-10s)| Instant results (<100ms) |
| High write load    | Optimized reads      |

Aggregate tables are **not a silver bullet**, but when used correctly, they can give you **100x–1,000x faster queries** while reducing peak database load. In this post, we’ll explore:
- **Why** raw fact tables are slow for analytics
- **How** pre-computed aggregations solve the problem
- **How to implement** them with code examples
- **Tradeoffs** (storage vs. speed)
- **Common mistakes** to avoid

---

## **The Problem: Why Raw Fact Tables Are Slow**

### **1. Billions of Rows ≠ Fast Aggregations**
Let’s assume you have a `sales` fact table with **10 million transactions per day** (1B rows/year). Running a `GROUP BY` query like this:

```sql
SELECT
  product_category,
  EXTRACT(MONTH FROM sale_date) AS month,
  SUM(revenue) AS monthly_revenue
FROM sales
GROUP BY product_category, month;
```

...on a raw fact table can take **5–10 seconds**—even with indexing. Why?

- **Full table scans** are needed for `GROUP BY` on billions of rows.
- **Database engines** (PostgreSQL, BigQuery, etc.) can’t optimize away the computational cost of aggregating live data.
- **Peak load** spikes during business hours when everyone refreshes dashboards.

### **2. Daily Reports = Daily Computation Overhead**
Most analytics teams run **pre-aggregation jobs** (ETL) to generate reports. But what if the same aggregations are needed **100 times a day** (by dashboards, mobile apps, and ad-hoc queries)?

- **Wasted compute resources** re-running the same math.
- **Delayed insights** due to slow queries.
- **Scalability issues**—raw fact tables can’t handle real-time dashboards.

### **3. The Database Becomes a Bottleneck**
Fact tables are designed for **OLTP (transactional) workloads**, not **OLAP (analytics)**.
- **Write-heavy**: Inserts/updates are fast, but reads on large datasets are slow.
- **No indexing for aggregations**: Even with `GROUP BY` optimizations, raw data requires more work.
- **Peak load during business hours**: Your database slows down when most users are online.

### **4. Real-World Example: The E-commerce Dashboard**
Consider an e-commerce platform with:
- **1M orders/day** (365M/year)
- A dashboard showing **daily revenue by product category**

A raw fact table query would look like:

```sql
SELECT
  category,
  TO_CHAR(order_date, 'YYYY-MM-DD') AS day,
  SUM(total_revenue) AS daily_revenue
FROM orders
GROUP BY category, day
ORDER BY day DESC;
```

If this runs **30 times/day** across 100 dashboards, your database is doing:
**100 operations × 5 seconds = 8.3 hours of wasted compute per day.**

---

## **The Solution: Pre-Computed Aggregations**

### **Core Idea**
Instead of aggregating every time a query runs, we:
1. **Pre-compute aggregations** in batch (e.g., hourly, daily, monthly).
2. **Store them in separate tables** (`ta_orders_daily`, `ta_orders_hourly`).
3. **Route queries intelligently**—use pre-aggregated data when possible.

### **How It Works**
| **Granularity** | **Table Name**       | **Use Case**                          |
|-----------------|----------------------|---------------------------------------|
| Hourly          | `ta_orders_hourly`   | Real-time dashboards                  |
| Daily           | `ta_orders_daily`    | Daily reports                        |
| Monthly         | `ta_orders_monthly`  | Executive dashboards                 |

Each aggregate table has:
- **Same dimensions** as the fact table (e.g., `category`, `date`).
- **Pre-computed measures** (`SUM(revenue)`, `MAX quantity`, etc.).
- **JSONB fields** for flexible querying (more on this later).

### **Example Schema**
#### **Fact Table (`orders`)**
```sql
CREATE TABLE orders (
  order_id SERIAL PRIMARY KEY,
  user_id INT,
  product_id INT,
  category VARCHAR(50),
  order_date TIMESTAMP,
  total_revenue DECIMAL(18, 2),
  quantity INT
);
```

#### **Daily Aggregate Table (`ta_orders_daily`)**
```sql
CREATE TABLE ta_orders_daily (
  category VARCHAR(50) NOT NULL,
  date DATE NOT NULL,
  total_revenue DECIMAL(18, 2) NOT NULL,
  avg_quantity DECIMAL(5, 2),
  order_count INT NOT NULL,
  metadata JSONB,  -- Flexible extra fields
  PRIMARY KEY (category, date)
);
```

### **Querying the Aggregate Table**
Now, instead of scanning 1B rows, we query **only 365 rows**:

```sql
-- Fast query (uses pre-aggregated data)
SELECT
  category,
  date AS day,
  total_revenue AS daily_revenue
FROM ta_orders_daily
WHERE date >= NOW() - INTERVAL '30 days'
ORDER BY date DESC;
```

This runs in **<100ms** instead of 5–10 seconds.

---

## **Implementation Guide**

### **Step 1: Design Your Aggregate Tables**
Each aggregate table should:
1. **Match the fact table’s dimensions** (e.g., `category`, `date`).
2. **Store pre-computed measures** (`SUM`, `AVG`, `COUNT`).
3. **Include a `metadata` JSONB field** for flexibility (e.g., `{"source": "sales", "updated_at": "2024-05-20"}`).

**Example Schema for Multiple Granularities**
```sql
-- Hourly aggregates (for real-time dashboards)
CREATE TABLE ta_orders_hourly (
  category VARCHAR(50) NOT NULL,
  hour TIMESTAMP NOT NULL,
  total_revenue DECIMAL(18, 2) NOT NULL,
  order_count INT NOT NULL,
  metadata JSONB,
  PRIMARY KEY (category, hour)
);

-- Daily aggregates (for reports)
CREATE TABLE ta_orders_daily (
  category VARCHAR(50) NOT NULL,
  date DATE NOT NULL,
  total_revenue DECIMAL(18, 2) NOT NULL,
  avg_quantity DECIMAL(5, 2),
  order_count INT NOT NULL,
  metadata JSONB,
  PRIMARY KEY (category, date)
);

-- Monthly aggregates (for executive dashboards)
CREATE TABLE ta_orders_monthly (
  category VARCHAR(50) NOT NULL,
  month DATE NOT NULL,  -- YYYY-MM-01 format
  total_revenue DECIMAL(18, 2) NOT NULL,
  order_count INT NOT NULL,
  metadata JSONB,
  PRIMARY KEY (category, month)
);
```

---

### **Step 2: Build the ETL Pipeline**
We need a **batch job** to update aggregates. Here’s a PostgreSQL example using `pg_cron` (or Airflow, dbt, etc.):

#### **Daily Update Script (`update_aggregates_daily.sql`)**
```sql
DO $$
DECLARE
  today DATE := CURRENT_DATE;
  yesterday DATE := today - INTERVAL '1 day';
BEGIN
  -- Update daily aggregates for yesterday
  INSERT INTO ta_orders_daily (
    category,
    date,
    total_revenue,
    avg_quantity,
    order_count,
    metadata
  )
  SELECT
    o.category,
    DATE(o.order_date) AS date,
    SUM(o.total_revenue) AS total_revenue,
    AVG(o.quantity) AS avg_quantity,
    COUNT(*) AS order_count,
    JSONB_BUILD_OBJECT(
      'source', 'sales',
      'updated_at', NOW()
    ) AS metadata
  FROM orders o
  WHERE DATE(o.order_date) = yesterday
  GROUP BY o.category, date;

  -- Update monthly aggregates if needed (e.g., first of the month)
  IF EXTRACT(DAY FROM today) = 1 THEN
    INSERT INTO ta_orders_monthly (...)
    SELECT ...
    FROM ta_orders_daily
    WHERE date BETWEEN (EXTRACT(YEAR FROM today) || '-' || EXTRACT(MONTH FROM today) || '-01')
                 AND (today - INTERVAL '1 day');
  END IF;
END $$;
```

#### **Scheduling the Job**
Run this daily via:
- **PostgreSQL `pg_cron`**:
  ```sql
  INSERT INTO cron.schedule (name, command, up_next, crontab)
  VALUES ('update_daily_aggregates', 'SELECT pg_cron.run_task(''update_aggregates_daily'');', NOW(), '0 3 * * *');
  ```
- **Airflow/Dagster**: Schedule a daily DAG.
- **Cloud Scheduler**: Trigger a Cloud Function.

---
### **Step 3: Implement a Query Router**
Not all queries should hit aggregate tables. We need a **smart query planner** that:
1. **Checks against the latest data** (e.g., "Is this query about today’s sales?").
2. **Falls back to raw data** when needed (e.g., real-time updates).

#### **Example Query Router Logic**
```python
def get_data(query_params):
    # Example: Querying sales for the last 7 days
    date_filter = f"WHERE date >= NOW() - INTERVAL '7 days'"

    # Check if we can use pre-aggregated data
    if query_params.get('time_granularity') == 'daily':
        return get_from_aggregate_table('ta_orders_daily', date_filter)
    elif query_params.get('time_granularity') == 'hourly':
        return get_from_aggregate_table('ta_orders_hourly', date_filter)
    else:
        # Fall back to raw data for real-time updates
        return get_from_fact_table('orders', date_filter)
```

#### **When to Use Raw Data**
- **Real-time updates** (e.g., live order tracking).
- **Ad-hoc queries** not covered by aggregates.
- **Edge cases** (e.g., "Show me all orders from 3 months ago").

---

### **Step 4: Optimize for Incremental Updates**
Recalculating **all aggregates daily** is inefficient. Instead:
1. **Track the last updated date** in the `metadata` field.
2. **Only update new periods** (e.g., last 7 days).

**Optimized Update Script**
```sql
DO $$
DECLARE
  yesterday DATE := CURRENT_DATE - INTERVAL '1 day';
  last_updated TIMESTAMP;
BEGIN
  -- Get the last updated date for this category (from metadata)
  SELECT metadata->>'last_updated' INTO last_updated
  FROM ta_orders_daily
  WHERE category = 'Electronics'
  LIMIT 1;

  -- Only insert new data if not already present
  IF NOT EXISTS (
    SELECT 1 FROM ta_orders_daily
    WHERE category = 'Electronics' AND date = yesterday
  ) THEN
    INSERT INTO ta_orders_daily (...)
    SELECT ...
    FROM orders
    WHERE DATE(order_date) = yesterday AND category = 'Electronics'
    GROUP BY category, date;
  END IF;
END $$;
```

---

### **Step 5: Handle Time-Zone & Edge Cases**
- **Use `TIMESTAMP WITH TIME ZONE`** if dealing with global data.
- **Handle partial days** (e.g., "What was yesterday’s revenue?").
- **Backfill missing data** if the ETL fails.

**Example: Backfilling Missing Days**
```sql
DO $$
DECLARE
  start_date DATE := '2024-01-01';
  end_date DATE := CURRENT_DATE - INTERVAL '1 day';
BEGIN
  FOR day IN SELECT generate_series(start_date, end_date, INTERVAL '1 day')::date AS day
  LOOP
    IF NOT EXISTS (
      SELECT 1 FROM ta_orders_daily WHERE date = day
    ) THEN
      INSERT INTO ta_orders_daily (...)
      SELECT ...
      FROM orders
      WHERE DATE(order_date) = day
      GROUP BY category, day;
    END IF;
  END LOOP;
END $$;
```

---

## **Common Mistakes to Avoid**

### **1. Over-Aggregating (Too Many Granularities)**
- **Bad**: Creating hourly, daily, weekly, **and monthly** aggregates for everything.
- **Solution**: Start with **one granularity** (e.g., daily), then add more as needed.

### **2. Not Tracking Metadata**
- **Bad**: Losing track of when aggregates were last updated.
- **Solution**: Always store `metadata` with `updated_at` timestamps.

### **3. Ignoring Data Drift**
- **Problem**: Fact tables change (e.g., new columns, schema updates).
- **Solution**: **Version your aggregates** or rebuild them periodically.

### **4. Not Handling Partial Periods**
- **Problem**: "Yesterday’s revenue" might span multiple days in some time zones.
- **Solution**: Use `DATE_TRUNC` and `DATE_TRUNC + INTERVAL '1 day' - INTERVAL '1 ms'` for full-day coverage.

### **5. Forgetting to Test Edge Cases**
- **What if the ETL fails?** (Use backfills.)
- **What if a query needs raw data?** (Fallback logic.)
- **What if storage costs explode?** (Monitor and archive old aggregates.)

---

## **Key Takeaways**

✅ **Speed up queries by 100x–1,000x** with pre-aggregated data.
✅ **Reduce database load** during peak hours.
✅ **Trade storage for speed**—aggregate tables use more space but save compute.
✅ **Use JSONB for flexibility**—store extra metadata without schema changes.
✅ **Incremental updates** are key—only recalculate what’s needed.
✅ **Not a silver bullet**—fall back to raw data when necessary.

⚠️ **Tradeoffs to consider**:
- **Storage cost** (aggregate tables grow with time).
- **ETL complexity** (pipelines must be reliable).
- **Data freshness** (pre-aggregated data isn’t real-time).

---

## **Conclusion**

Aggregate tables (`ta_*`) are a **powerful pattern for analytics-heavy applications**, especially when dealing with **billions of rows**. By pre-computing common aggregations, you:
- **Eliminate slow `GROUP BY` queries**.
- **Reduce peak database load**.
- **Enable real-time dashboards** without overloading your database.

### **When to Use This Pattern**
✔ You have **large fact tables** (>10M rows).
✔ You run **repeated aggregations** (dashboards, reports).
✔ Your **queries are slow** (5+ seconds).

### **When to Avoid It**
✖ Your data is **highly variable** (e.g., clickstream with millions of unique events).
✖ You need **real-time updates** (use materialized views instead).
✖ Your team **can’t maintain ETL pipelines**.

### **Next Steps**
1. **Start small**: Add one aggregate table (e.g., daily revenue by category).
2. **Monitor performance**: Compare query times before/after.
3. **Scale gradually**: Add more granularities as needed.
4. **Automate everything**: Use Airflow, dbt, or a scheduling tool.

---
**Further Reading**
- [PostgreSQL Materialized Views](https://www.postgresql.org/docs/current/materialized-views.html) (alternative to aggregate tables).
- [BigQuery BI Engine](https://cloud.google.com/bigquery/docs/reference/rest/v2/biEngine) (for serverless aggregation).
- [dbt Aggregations](https://docs.getdbt.com/docs/build/aggregations) (modern ETL with pre-computation).

---
**Have you used aggregate tables in production? What were your biggest challenges?** Share your thoughts in the comments! 🚀
```

---
This blog post is **practical, code-heavy, and honest about tradeoffs**—perfect for intermediate backend engineers who want to optimize their analytics workloads.