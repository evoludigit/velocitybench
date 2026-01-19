```markdown
---
title: "View Refresh Strategies: Keeping Your Materialized Views Fresh (Without Breaking Your App)"
date: 2024-02-15
tags: ["database design", "ETL", "performance", "postgres", "materialized views"]
---

# **View Refresh Strategies: Keeping Your Materialized Views Fresh (Without Breaking Your App)**

![Materialized Views Lifecycle](https://miro.medium.com/v2/resize:fit:1400/1*vq3QJX5ZqZ0XJtYbT7JZLw.png)

Materialized views are a powerful tool for performance optimization—they pre-compute query results so you can run complex aggregations or join-heavy queries in milliseconds instead of seconds or minutes. But here’s the catch: **like any pre-computed data, they eventually become stale**.

If your materialized view is based on a table that’s frequently updated, you need a strategy to refresh it—without causing downtime, performance bottlenecks, or inconsistent data.

In this post, we’ll explore three common **view refresh strategies**:
1. **Full refresh** (the predictable but resource-heavy approach)
2. **Incremental refresh** (the efficient but complex approach)
3. **Continuous refresh** (the real-time but challenging approach)

We’ll discuss tradeoffs, implementation details, and—most importantly—how to choose the right strategy for your use case.

---

## **The Problem: Stale Materialized Views**

Imagine this scenario:
- You have a `sales_summary` materialized view that aggregates daily sales data.
- Your frontend dashboard relies on this view to display real-time metrics.
- But when you refresh the view *only once per day*, your dashboard shows yesterday’s sales *all day today*.

This isn’t just annoying—it can lead to **bad business decisions**. Stale data undermines trust in your analytics, causes race conditions in financial systems, and can even violate compliance requirements.

Worse, if your materialized view is refreshes **too frequently**, you might:
- **Overload your database** with constant write-heavy refresh operations.
- **Block locks** on underlying tables, causing timeouts.
- **Waste resources** refreshing data that hasn’t changed.

So how do you balance **freshness** and **performance**?

---

## **The Solution: Three View Refresh Strategies**

The choice of refresh strategy depends on:
- **How often your data changes** (high-frequency vs. batch updates).
- **Your tolerance for stale data** (real-time vs. near-real-time).
- **Your database’s capacity** (can it handle heavy refresh loads?).

Let’s dive into each approach.

---

### **1. Full Refresh: A Clean Slate Every Time**

#### **What it does**
A full refresh **drops and recreates** the materialized view from scratch, re-running the entire query.

```sql
-- Example: Creating a materialized view
CREATE MATERIALIZED VIEW sales_summary AS
SELECT
    date_trunc('day', order_date) AS day,
    product_id,
    SUM(amount) AS total_sales
FROM orders
GROUP BY 1, 2;
```

```sql
-- Example: Full refresh
REFRESH MATERIALIZED VIEW sales_summary;
```

#### **Pros**
- **Simple to implement** (just one command).
- **Guarantees consistency** (no partial updates).
- **Works well for large but infrequently changing datasets**.

#### **Cons**
- **Expensive for large tables** (scans entire source tables).
- **Can lock tables during refresh** (impacting other queries).
- **Not ideal for high-frequency updates** (e.g., real-time analytics).

#### **When to use**
- **Batch processing scenarios** (e.g., daily/weekly summaries).
- **Infrequent updates** (e.g., nightly ETL jobs).
- **Small datasets** (where full scans are acceptable).

---

### **2. Incremental Refresh: Only Update What Changed**

#### **What it does**
Instead of re-running the entire query, an **incremental refresh** only updates rows affected by recent changes.

#### **How it works (PostgreSQL Example)**
PostgreSQL doesn’t natively support incremental refreshes, but you can **simulate** it with triggers or `INSERT/UPDATE` logic.

```sql
-- Step 1: Create a temporary table to track changes
CREATE TABLE order_changes AS
SELECT
    order_id,
    product_id,
    amount,
    order_date
FROM orders
WHERE order_date >= (CURRENT_DATE - INTERVAL '7 days')
  AND status = 'completed';

-- Step 2: Update the materialized view incrementally
INSERT INTO sales_summary (day, product_id, total_sales)
SELECT
    date_trunc('day', oc.order_date) AS day,
    oc.product_id,
    SUM(oc.amount) AS total_sales
FROM order_changes oc
GROUP BY 1, 2
ON CONFLICT (day, product_id)
DO UPDATE SET total_sales = EXCLUDED.total_sales;
```

#### **Pros**
- **Efficient for large tables** (only processes recent changes).
- **Reduces lock contention** (no full table scans).
- **Better for high-frequency updates**.

#### **Cons**
- **More complex to implement** (requires tracking deltas).
- **Harder to debug** (edge cases in partial updates).
- **Still may miss some changes** if not implemented carefully.

#### **When to use**
- **High-update scenarios** (e.g., real-time stock prices).
- **Large datasets where full refreshes are impractical**.
- **When you can tolerate slight stale data** (e.g., analytics dashboards).

---

### **3. Continuous Refresh: Real-Time (But Complex)**

#### **What it does**
Continuous refreshes **update the materialized view in real-time** as source data changes.

#### **How it works (PostgreSQL with Triggers)**
```sql
-- Step 1: Create a function to update the MV on INSERT/UPDATE
CREATE OR REPLACE FUNCTION update_sales_summary()
RETURNS TRIGGER AS $$
BEGIN
    -- Delete old record if needed (if your MV uses UNIQUE constraints)
    DELETE FROM sales_summary
    WHERE day = (SELECT date_trunc('day', NEW.order_date))
      AND product_id = NEW.product_id;

    -- Insert/Update the new aggregate
    INSERT INTO sales_summary (day, product_id, total_sales)
    VALUES (
        date_trunc('day', NEW.order_date),
        NEW.product_id,
        NEW.amount
    )
    ON CONFLICT (day, product_id)
    DO UPDATE SET total_sales = EXCLUDED.total_sales;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Step 2: Attach a trigger to the source table
CREATE TRIGGER trg_update_sales_summary
AFTER INSERT OR UPDATE ON orders
FOR EACH ROW EXECUTE FUNCTION update_sales_summary();
```

#### **Pros**
- **Always up-to-date** (no stale data).
- **Ideal for critical real-time systems** (e.g., banking, IoT).

#### **Cons**
- **High overhead** (each row update triggers a refresh).
- **Risk of lock contention** (if not optimized).
- **Complex to maintain** (edge cases, performance tuning).

#### **When to use**
- **Real-time financial systems** (e.g., balance tracking).
- **Low-latency IoT/telemetry dashboards**.
- **When correctness > performance** (and your DB can handle it).

---

## **Implementation Guide: Choosing the Right Strategy**

| **Strategy**       | **Best For**                          | **Database Overhead** | **Consistency Guarantee** | **Implementation Complexity** |
|--------------------|---------------------------------------|-----------------------|---------------------------|--------------------------------|
| **Full Refresh**   | Batch processing, small datasets      | High                  | High                      | Low                            |
| **Incremental**    | High-frequency updates, large data    | Medium                | Medium                    | High                           |
| **Continuous**     | Real-time critical systems            | Very High             | High                      | Very High                      |

### **Step-by-Step Implementation**

#### **1. Start with Full Refresh (Simplest Case)**
```sql
-- Create MV with a simple query
CREATE MATERIALIZED VIEW user_activity AS
SELECT
    user_id,
    COUNT(*) AS activity_count,
    MAX(last_active_at) AS last_activity
FROM user_sessions
GROUP BY user_id;

-- Refresh manually (or schedule with cron)
REFRESH MATERIALIZED VIEW user_activity;
```

#### **2. Move to Incremental (For Medium Loads)**
```sql
-- Track only new/updated sessions in the last hour
CREATE MATERIALIZED VIEW incremental_user_activity AS
SELECT
    user_id,
    COUNT(*) AS activity_count,
    MAX(last_active_at) AS last_activity
FROM user_sessions
WHERE last_active_at >= (NOW() - INTERVAL '1 hour')
GROUP BY user_id;

-- Merge results with the main MV
CREATE OR REPLACE MATERIALIZED VIEW user_activity AS
WITH new_activity AS (
    SELECT
        ua.user_id,
        COUNT(*) AS activity_count,
        MAX(ua.last_activity) AS last_activity
    FROM incremental_user_activity ua
    GROUP BY ua.user_id
)
SELECT
    COALESCE(main.user_id, new.user_id) AS user_id,
    COALESCE(main.activity_count, 0) + COALESCE(new.activity_count, 0) AS activity_count,
    COALESCE(new.last_activity, main.last_activity) AS last_activity
FROM (
    SELECT * FROM user_activity
) main
FULL OUTER JOIN new_activity new ON main.user_id = new.user_id;
```

#### **3. For Real-Time (Advanced)**
```sql
-- Use PostgreSQL's LISTEN/NOTIFY or database triggers
CREATE OR REPLACE FUNCTION refresh_mv_on_change()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM REFRESH MATERIALIZED VIEW user_activity;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Attach to session inserts
CREATE TRIGGER trg_refresh_after_insert
AFTER INSERT ON user_sessions
FOR EACH ROW EXECUTE FUNCTION refresh_mv_on_change();
```

---

## **Common Mistakes to Avoid**

1. **Assuming Full Refresh is Always "Safe"**
   - ❌ Running a full refresh during peak hours **locks tables**, causing timeouts.
   - ✅ Schedule full refreshes **off-peak** (e.g., midnight).

2. **Ignoring Dependency Ordering**
   - If `sales_summary` depends on `customer_data`, refreshing `sales_summary` **before** `customer_data` causes consistency issues.
   - ✅ Use **dependency graphs** (e.g., `pg_depend` in PostgreSQL) to enforce correct refresh order.

3. **Overcomplicating Incremental Refresh**
   - ❌ Trying to track **every possible delta** leads to bugs.
   - ✅ Start with **time-based slices** (e.g., "only refresh last 24 hours").

4. **Not Testing Failure Scenarios**
   - What happens if the refresh **fails halfway**?
   - ✅ Use **transaction rollbacks** and **fallback mechanisms**.

5. **Forgetting About Storage Growth**
   - Materialized views **never auto-prune** old data.
   - ✅ Add **TTL policies** (e.g., drop rows older than 30 days).

---

## **Key Takeaways**

✅ **Full Refresh** → Best for **simple, batch-heavy** workloads.
✅ **Incremental Refresh** → Best for **large datasets with frequent updates**.
✅ **Continuous Refresh** → Only for **real-time critical systems** (if database can handle it).

🚨 **Tradeoffs Matter:**
- **Freshness vs. Performance** – More frequent refreshes = more overhead.
- **Complexity vs. Correctness** – Incremental refreshes avoid full scans but require careful implementation.

🔧 **Best Practices:**
1. **Start simple** (full refresh), then optimize.
2. **Schedule refreshes** (cron, Airflow, or database-native tools).
3. **Monitor lock contention** (use `pg_stat_activity`).
4. **Test failure scenarios** (what if the refresh crashes?).
5. **Consider partitioned materialized views** (for huge datasets).

---

## **Conclusion: Pick Your Approach Wisely**

Materialized views are **incredibly powerful**, but their value depends on **how fresh the data is**. The right refresh strategy balances **performance, consistency, and complexity**.

- **For most applications**, **incremental refresh** (with time-based slices) is a **sweet spot**—it’s efficient, scalable, and avoids full-table scans.
- **For critical real-time systems**, **continuous refresh** (with triggers) ensures **zero stale data**, but at a **high cost**.
- **For simplicity**, **full refresh** works well **if updates are infrequent**.

**Next Steps:**
1. Experiment with **PostgreSQL’s `REFRESH MATERIALIZED VIEW`** in a test database.
2. Try **partitioning your MV** for large datasets.
3. Explore **ETL tools** (e.g., dbt, Airflow) that handle refresh logic for you.

---
**What’s your go-to refresh strategy? Have you run into gotchas with stale materialized views? Share your experiences in the comments!**
```

---
### **Why This Works for Beginners**
- **Code-first approach**: Shows `CREATE`, `INSERT`, and `REFRESH` examples immediately.
- **Real-world tradeoffs**: Explicitly calls out "when to use" each method (not just "here’s how").
- **Common mistakes**: Practical warnings (e.g., "don’t run full refreshes during peak hours").
- **Actionable next steps**: Ends with clear "pick your approach" guidance.

This balances **theory** (why strategies exist) with **practicality** (how to pick the right one).