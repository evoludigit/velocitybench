# **[Pattern] View Refresh Strategies Reference Guide**

---

## **Overview**
FraiseQL’s **View Refresh Strategies** pattern enables efficient, low-overhead updates to materialized views (MVs) with flexibility to balance accuracy, performance, and consistency. Users can choose from **full refresh**, **incremental refresh**, or **continuous refresh** modes, each optimized for different use cases. These strategies support:
- **Configurable schedules** (manual, cron-based, or event-triggered)
- **Concurrent refreshes** to minimize downtime
- **Dependency resolution** for cascading refreshes (e.g., refresh View A before View B if A is a dependency)
- **Auto-throttling** to prevent resource contention

This guide covers implementation details, schema references, query examples, and related patterns.

---

## **Key Concepts**

| **Term**               | **Description**                                                                 |
|-------------------------|---------------------------------------------------------------------------------|
| **Materialized View (MV)** | A cached, precomputed query result stored in FraiseQL for faster reads.         |
| **Refresh Strategy**    | Defines *how* and *when* an MV is updated (e.g., full, incremental, continuous). |
| **Refresh Schedule**    | Defines *when* refreshes occur (e.g., `@ every 1 hour`, `@ on demand`).         |
| **Concurrent Refresh**  | Allows parallel refreshes for zero-downtime updates (configurable concurrency).|
| **Dependency Graph**    | Automatically resolves refresh order for cascading dependencies (e.g., `VIEW_B` depends on `VIEW_A`). |

---

## **Schema Reference**

### **1. Create a Materialized View**
```sql
CREATE MATERIALIZED VIEW [IF NOT EXISTS] view_name
    [WITH (refresh_strategy = strategy, refresh_interval = 'X', ...)]
    AS query;
```

| **Field**               | **Type**       | **Description**                                                                                     |
|--------------------------|----------------|-----------------------------------------------------------------------------------------------------|
| `view_name`              | String         | Name of the materialized view.                                                                     |
| `IF NOT EXISTS`          | Boolean        | Prevents error if the view already exists.                                                           |
| `refresh_strategy`       | Enum           | `full`, `incremental`, or `continuous` (default: `full`).                                           |
| `refresh_interval`       | Time/Event     | Schedule (e.g., `'every 1 hour'`, `'@ hourly'`, `'@ on demand'`).                                   |
| `concurrency`            | Integer        | Number of parallel refreshes allowed (default: `1`).                                               |
| `dependency_order`       | Boolean        | Enforces automatic dependency resolution (default: `true`).                                         |

---

### **2. Update Refresh Strategy**
```sql
ALTER MATERIALIZED VIEW view_name
    SET (refresh_strategy = 'new_strategy', refresh_interval = 'new_interval');
```

| **Field**               | **Type**       | **Description**                                                                                     |
|--------------------------|----------------|-----------------------------------------------------------------------------------------------------|
| `refresh_strategy`       | Enum           | Update to `full`, `incremental`, or `continuous`.                                                  |
| `refresh_interval`       | Time/Event     | Change schedule (e.g., `'every 2 hours'`, `'@ daily'`).                                           |

---

### **3. Refresh Manually**
```sql
REFRESH MATERIALIZED VIEW [CASCADE | WITH CONCURRENCY N]
    [view_name [, view_name2, ...]];
```
| **Argument**            | **Description**                                                                                     |
|-------------------------|-----------------------------------------------------------------------------------------------------|
| `CASCADE`               | Refreshes views and their dependencies automatically.                                               |
| `WITH CONCURRENCY N`     | Allows `N` parallel refreshes (default: `1`).                                                      |
| `view_name`             | Comma-separated list of views to refresh.                                                           |

---

## **Query Examples**

### **1. Create a View with Full Refresh (Cron-Based)**
```sql
-- Refresh every 6 hours
CREATE MATERIALIZED VIEW sales_summary
    WITH (refresh_strategy = 'full', refresh_interval = 'every 6 hours')
    AS SELECT product_id, SUM(revenue) FROM transactions GROUP BY product_id;
```

### **2. Create a View with Incremental Refresh (Time-Based)**
```sql
-- Incrementally refresh incremental rows since last refresh
CREATE MATERIALIZED VIEW daily_orders
    WITH (refresh_strategy = 'incremental', refresh_interval = 'daily')
    AS SELECT * FROM orders WHERE order_date >= last_refresh_time;
```

### **3. Create a View with Continuous Refresh (Event-Triggered)**
```sql
-- Refresh on new data insertion (triggers immediately)
CREATE MATERIALIZED VIEW active_users
    WITH (refresh_strategy = 'continuous', refresh_interval = '@ on insert')
    AS SELECT * FROM users WHERE last_active > NOW() - INTERVAL '7 days';
```

### **4. Configure Concurrent Refreshes**
```sql
-- Allow 3 parallel refreshes for cascading dependencies
ALTER MATERIALIZED VIEW reporting_dashboard
    SET (concurrency = 3);
```

### **5. Force a Manual Refresh with Concurrency**
```sql
-- Refresh 3 views in parallel
REFRESH MATERIALIZED VIEW WITH CONCURRENCY 3
    (sales_summary, daily_orders, active_users);
```

---

## **Advanced Usage**

### **1. Dependency-Based Refreshes**
```sql
-- Automatically refreshes `user_stats` if `users` changes
CREATE MATERIALIZED VIEW user_stats
    WITH (auto_dependency = true)
    AS SELECT user_id, COUNT(*) FROM orders GROUP BY user_id;
```

### **2. Hybrid Refresh Strategy (Manual + Scheduled)**
```sql
-- Default: manual refresh, but auto-refreshes every 4 hours
CREATE MATERIALIZED VIEW analytics
    WITH (refresh_strategy = 'full', refresh_interval = 'every 4 hours')
    AS SELECT * FROM raw_data;
-- Later:
REFRESH MATERIALIZED VIEW analytics; -- Override schedule
```

---

## **Performance Considerations**

| **Strategy**       | **Pros**                                      | **Cons**                                  | **Best For**                          |
|--------------------|-----------------------------------------------|------------------------------------------|---------------------------------------|
| **Full Refresh**   | Simple, accurate                              | High latency, high resource usage         | Low-frequency updates                |
| **Incremental**    | Low overhead, fast updates                    | Complex logic for tracking changes       | Time-series data                     |
| **Continuous**     | Real-time accuracy                            | High resource consumption                | Streaming/real-time analytics        |

---
## **Related Patterns**

1. **[Partitioned Materialized Views](link)**
   - Combines refresh strategies with horizontal partitioning for large datasets.

2. **[Caching Layers](link)**
   - Integrates with caching (e.g., Redis) for low-latency reads while MV refreshes run in background.

3. **[Query Optimization](link)**
   - Use `EXPLAIN` to analyze MV refresh costs and adjust strategies accordingly.

4. **[Event-Driven Refreshes](link)**
   - Trigger refreshes via Kafka, Pub/Sub, or database change data capture (CDC).

---
## **Troubleshooting**
| **Issue**               | **Solution**                                                                 |
|-------------------------|------------------------------------------------------------------------------|
| **Refresh pending**     | Use `SHOW MATERIALIZED VIEW STATUS` to check queue backlog.                   |
| **Dependency cycles**   | Disable `auto_dependency` or restructure views to avoid circular references.  |
| **High concurrency lag**| Reduce `concurrency` or split into smaller views.                           |
| **Incremental misses**  | Verify `refresh_interval` aligns with data change frequency.                  |

---
## **References**
- [FraiseQL Materialized Views Docs](https://doc.fraiseql.com/mvs)
- [Concurrency Controls](https://doc.fraiseql.com/refresh-concurrency)