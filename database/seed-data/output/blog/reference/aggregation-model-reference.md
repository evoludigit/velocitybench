---
**[Pattern] FraiseQL Aggregation Model Reference Guide**
*Version: v2.1*
*Last Updated: [Insert Date]*

---

### **1. Overview**
The **FraiseQL Aggregation Model** transforms GraphQL aggregate queries (e.g., `SUM`, `AVG`, `COUNT`) into **PostgreSQL-native SQL aggregations** with **server-side execution**. This pattern avoids client-side aggregation, leverages **JSONB denormalization** for flexible grouping, and supports **temporal bucketing** and **database-specific functions** (e.g., `PERCENTILE`, `STDDEV`).

Key principles:
- **No joins**: Dimensions must be pre-denormalized into JSONB (e.g., `{"dimension1": "value1", "dimension2": "value2"}`).
- **Efficient aggregation**: Uses PostgreSQL’s `GROUP BY` with JSONB extraction (e.g., `data->>'field'`) and `HAVING` filters for post-aggregation constraints.
- **Temporal support**: Standardizes time-series aggregation via `DATE_TRUNC` or `strftime`.

---

### **2. Schema Reference**
| **Component**               | **Description**                                                                 | **Example Syntax**                          | **Notes**                                  |
|-----------------------------|---------------------------------------------------------------------------------|--------------------------------------------|------------------------------------------|
| **Aggregate Functions**     | PostgreSQL-compatible aggregations                                              | `COUNT(*), SUM(revenue), AVG(price), ...` | Supports `STDDEV`, `VARIANCE`, `PERCENTILE`. |
| **JSONB Dimensions**        | Denormalized fields grouped via `GROUP BY`                                       | `GROUP BY data->>'country', data->>'category'` | Requires JSONB column in source schema.   |
| **HAVING Clause**           | Filters aggregated results (e.g., post-`SUM` checks)                            | `HAVING SUM(revenue) > 10000`               | Equivalent to GraphQL’s `filter` in aggregates. |
| **Temporal Bucketing**      | Time-series grouping using PostgreSQL functions                                 | `DATE_TRUNC('month', event_time)`, `strftime('%Y', created_at)` | Use `DATE_TRUNC` for standard intervals.   |
| **Window Functions**        | Additional analytics (e.g., `LAG`, `OVER()`)                                     | `SUM(revenue) OVER(PARTITION BY user_id ORDER BY date)` | Requires `WINDOW` clause in SQL.          |

---

### **3. Query Examples**
#### **Basic Aggregation (COUNT/SUM)**
**GraphQL Query:**
```graphql
{
  events(aggregate: {
    groupBy: ["country", "category"]
    sum: { revenue: true }
    count: { orders: true }
  }) {
    groups {
      country
      category
      revenue_sum
      order_count
    }
  }
}
```
**Compiled SQL:**
```sql
SELECT
  data->>'country' AS country,
  data->>'category' AS category,
  SUM(revenue) AS revenue_sum,
  COUNT(*) AS order_count
FROM events
WHERE data->>'status' = 'completed'
GROUP BY data->>'country', data->>'category';
```

#### **With HAVING Filter**
**GraphQL Query:**
```graphql
{
  revenue(aggregate: {
    groupBy: ["country"]
    sum: { revenue: true }
    having: { revenue_sum: { gt: 10000 } }
  }) {
    groups {
      country
      revenue_sum
    }
  }
}
```
**Compiled SQL:**
```sql
SELECT
  data->>'country' AS country,
  SUM(revenue) AS revenue_sum
FROM transactions
GROUP BY data->>'country'
HAVING SUM(revenue) > 10000;
```

#### **Temporal Aggregation (Monthly Revenue)**
**GraphQL Query:**
```graphql
{
  revenueByMonth(aggregate: {
    groupBy: ["DATE_TRUNC('month', event_time)"]  # Custom scalar
    sum: { revenue: true }
  }) {
    groups {
      month
      monthly_revenue
    }
  }
}
```
**Compiled SQL:**
```sql
SELECT
  DATE_TRUNC('month', event_time) AS month,
  SUM(revenue) AS monthly_revenue
FROM events
GROUP BY DATE_TRUNC('month', event_time);
```

#### **Advanced: PERCENTILE + Window Function**
**GraphQL Query:**
```graphql
{
  userSpend(
    aggregate: {
      groupBy: ["user_id"]
      percentiles: { revenue: { percentile: 0.9 } }  # 90th percentile
    }
  ) {
    groups {
      user_id
      revenue_90th
    }
  }
}
```
**Compiled SQL:**
```sql
SELECT
  user_id,
  PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY revenue) AS revenue_90th
FROM orders
GROUP BY user_id;
```

---

### **4. Implementation Details**
#### **JSONB Denormalization**
- **Requirement**: Source data must embed dimensions as JSONB (e.g., `JSONB` column in PostgreSQL).
- **Example Schema**:
  ```sql
  CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    revenue NUMERIC,
    data JSONB NOT NULL  -- {"country": "US", "category": "electronics"}
  );
  ```
- **Grouping**:
  ```sql
  GROUP BY data->>'country', data->>'category'
  ```

#### **Handling Missing Fields**
- Use `COALESCE(data->>'field', 'default')` to avoid `NULL` grouping issues.
- Example:
  ```sql
  GROUP BY COALESCE(data->>'country', 'unknown')
  ```

#### **Performance Considerations**
- **Indexing**: Create GIN indexes on JSONB columns for faster extraction:
  ```sql
  CREATE INDEX idx_events_data ON events USING GIN(data);
  ```
- **Partitioning**: For large datasets, partition by time or range:
  ```sql
  CREATE TABLE events (
    event_time TIMESTAMP NOT NULL,
    revenue NUMERIC
  ) PARTITION BY RANGE (event_time);
  ```

#### **Database Extensions**
- **PERCENTILE**: Requires PostgreSQL’s `percentile_cont` (built-in).
- **STDDEV/VARIANCE**: Standard SQL functions:
  ```sql
  STDDEV(revenue), VARIANCE(revenue)
  ```

---

### **5. Related Patterns**
| **Pattern**                | **Description**                                                                 | **Use Case**                          |
|----------------------------|---------------------------------------------------------------------------------|---------------------------------------|
| **FraiseQL Filtering**     | Client-server filtering with JSONB projections                                   | Reduce data transfer before aggregation. |
| **Time-Series Partitioning** | Optimize temporal queries with table partitioning                               | High-volume time-series data.        |
| **Materialized Views**     | Pre-compute aggregations for read-heavy workloads                                | Dashboards with static metrics.       |
| **GraphQL Scalars**        | Define custom scalars (e.g., `DATE_TRUNC`) for reusable SQL fragments          | Templatize complex time-series logic. |

---

### **6. Troubleshooting**
| **Issue**                  | **Cause**                              | **Solution**                          |
|----------------------------|----------------------------------------|---------------------------------------|
| `NULL` in grouping columns | Missing JSONB fields                   | Use `COALESCE` or validate data.      |
| Slow aggregation           | Missing indexes on JSONB columns       | Add GIN index: `CREATE INDEX ON table USING GIN(jsonb_column)`. |
| `HAVING` not working        | Aggregation misalignment with `GROUP BY` | Ensure all `HAVING` columns are in `GROUP BY`. |
| Unsupported function        | Database-specific syntax (e.g., MySQL `STDDEV`) | Use PostgreSQL-compatible functions.   |

---
**Notes**:
- All examples assume PostgreSQL. Adjust for other databases (e.g., MySQL’s `JSON_EXTRACT`).
- For nested JSONB, use `->>` or `->` with path notation (e.g., `data->>'nested.field'`).