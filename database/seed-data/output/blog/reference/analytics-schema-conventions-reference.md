# **[Pattern] Analytics Schema Conventions and Best Practices Reference Guide**

---

## **1. Overview**
This guide outlines **FraiseQL’s analytics schema conventions** to ensure consistent, high-performance data modeling. By standardizing table naming, column types, indexing, and JSONB structure, this pattern enables:
- **Compiler introspection** (automated query optimization and validation).
- **Scalable indexing** (reducing query latency via GIN, B-tree, and BRIN indexes).
- **Maintainable dimensions** (JSONB for nested metadata) and **efficient filtering** (indexed columns).

Adherence to these conventions improves query performance, reduces manual tuning, and supports Fraise’s analytical capabilities.

---

## **2. Core Components**

### **2.1 Table Naming Prefixes**
**Purpose:** Distinguish between fact and aggregate tables for clarity and tooling support.
**Convention:**
| Prefix | Table Type       | Example                     |
|--------|------------------|-----------------------------|
| `tf_`  | Fact tables      | `tf_user_activity`          |
| `ta_`  | Aggregate tables | `ta_daily_user_metrics`     |

**Rules:**
- Use lowercase, underscores for readability.
- Avoid abbreviations (e.g., `users` → `user_activity`).

---

### **2.2 Column Type Rules**
**Purpose:** Separate measures (aggregated metrics) from dimensions (descriptive attributes) and filter columns (query predicates).

| Column Type     | Data Structure | Use Case                          | Index Type          |
|-----------------|----------------|-----------------------------------|---------------------|
| **Measures**    | SQL column     | Numeric metrics (`count`, `sum`)  | *No index by default*|
| **Dimensions**  | JSONB column   | Structured nested data (e.g., user profiles) | **GIN**       |
| **Filters**     | Indexed SQL    | Columns used in `WHERE` clauses   | **B-tree** (or BRIN for time-series) |

**Example:**
```sql
CREATE TABLE tf_user_sessions (
    session_id UUID PRIMARY KEY,  -- Filter column
    user_id BIGINT,               -- Filter column
    start_time TIMESTAMPTZ,        -- BRIN index for time-series
    metrics JSONB,                -- Dimensions (e.g., {"device": "mobile", "os": "iOS"})
    revenue DECIMAL(10, 2)         -- Measure
);
```

**Key Notes:**
- **Measures** are **not indexed** (optimized for aggregation).
- **Filters** must be indexed (default: B-tree; use BRIN for high-cardinality timestamp columns).
- **Dimensions** store all metadata in a single `JSONB` column (see Section 2.4).

---

### **2.3 Index Strategy**
**Purpose:** Optimize query performance with schema-aware indexes.

| Index Type | When to Use                          | Example                     |
|------------|---------------------------------------|-----------------------------|
| **GIN**    | JSONB dimensions (e.g., path queries) | `CREATE INDEX ON tf_user_sessions USING GIN (metrics);` |
| **B-tree** | Low-cardinality filters (e.g., `user_id`) | `CREATE INDEX ON tf_user_sessions (user_id);` |
| **BRIN**   | Time-series data (e.g., `start_time`) | `CREATE INDEX ON tf_user_sessions USING BRIN (start_time);` |

**Guidelines:**
- Avoid over-indexing; index only **high-frequency filter columns**.
- BRIN is ideal for **time-partitioned data** (e.g., daily aggregates).
- GIN supports **JSONB path operators** (e.g., `metrics->>'os'`).

---

### **2.4 JSONB Path Conventions**
**Purpose:** Standardize nested attribute access for consistency.

**Convention:**
- Use **dot notation** for paths (e.g., `user.address.city`).
- Flatten complex hierarchies (e.g., avoid `user.profile.settings`).
- Prefix arrays with `[]` (e.g., `orders[].price`).

**Example JSONB Structure:**
```json
{
  "user": {
    "id": 123,
    "email": "user@example.com",
    "preferences": {
      "theme": "dark",
      "notifications": true
    }
  },
  "session_stats": [
    {"action": "click", "timestamp": "2023-01-01T12:00:00Z"}
  ]
}
```

**Query Access Rules:**
- Use `->>` for scalar values (e.g., `metrics->>'user.email'`).
- Use `->` for JSON objects (e.g., `metrics->'user'`).
- For arrays, use `->>` with indexing (e.g., `metrics->>'session_stats'[0].action'`).

---

## **3. Schema Reference**
Below is a reference table for common analytics table structures.

| **Table**          | **Description**                          | **Key Columns**                          | **Indexes**                                  |
|--------------------|------------------------------------------|-------------------------------------------|---------------------------------------------|
| `tf_user_activity` | Raw user interactions.                   | `user_id`, `event_time`, `metrics`        | `B-tree(user_id)`, `BRIN(event_time)`      |
| `ta_daily_users`   | Aggregated daily user counts.            | `date`, `user_id`, `total_sessions`       | `B-tree(date)`, `B-tree(user_id)`           |
| `tf_transactions`  | Financial transactions.                  | `tx_id`, `user_id`, `amount`, `status`    | `B-tree(user_id)`, `B-tree(status)`         |
| `ta_product_metrics`| Product-level analytics.                 | `product_id`, `period`, `revenue`         | `B-tree(product_id)`, `BRIN(period)`       |

**Example Fact Table:**
```sql
CREATE TABLE tf_user_activity (
    event_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,         -- Filter
    event_time TIMESTAMPTZ NOT NULL, -- BRIN index for time-series
    device TEXT,                     -- Dimension (stored in JSONB)
    metrics JSONB NOT NULL           -- { "duration": 120, "category": "social" }
);

-- Create indexes
CREATE INDEX idx_user_activity_user_id ON tf_user_activity (user_id);
CREATE INDEX idx_user_activity_event_time USING BRIN (event_time);
CREATE INDEX idx_user_activity_metrics USING GIN (metrics);
```

---

## **4. Query Examples**

### **4.1 Filtering with Indexed Columns**
```sql
-- B-tree index on user_id (fast lookup)
SELECT * FROM tf_user_activity
WHERE user_id = 1001 AND event_time > '2023-01-01';
```

### **4.2 Querying JSONB Dimensions**
```sql
-- GIN index enables path queries
SELECT
    user_id,
    metrics->>'device' AS device,
    metrics->>'category' AS category
FROM tf_user_activity
WHERE metrics @> '{"category": "social"}'::jsonb;
```

### **4.3 Aggregating Measures**
```sql
-- No index needed for aggregations
SELECT
    date_trunc('day', event_time) AS day,
    COUNT(*) AS session_count
FROM tf_user_activity
GROUP BY day;
```

### **4.4 Joining Fact/Aggregate Tables**
```sql
-- Reuse ta_daily_users (pre-aggregated)
SELECT
    u.user_id,
    du.date,
    du.total_sessions,
    ja.metrics->>'avg_duration' AS avg_duration
FROM ta_daily_users du
JOIN tf_user_activity ja ON du.user_id = ja.user_id
WHERE du.date = '2023-01-01';
```

---

## **5. Best Practices**
1. **Name Tables Descriptively**
   Avoid vague names like `table1`. Use `tf_order_items` or `ta_monthly_sales`.

2. **Minimize JSONB Depth**
   Flatten nested structures to 2–3 levels to simplify queries.

3. **Partition Time-Series Data**
   Use `BRIN` + table partitioning for large temporal datasets:
   ```sql
   CREATE TABLE tf_user_logs (
       event_id BIGSERIAL,
       event_time TIMESTAMPTZ,
       user_id BIGINT,
       data JSONB
   )
   PARTITION BY RANGE (event_time);
   ```

4. **Document Dimensions**
   Add a `dimensions_schema` column (JSONB) to define expected paths:
   ```json
   {
     "user": { "type": "object", "required": ["email", "preferences.theme"] },
     "metrics": { "type": "object", "required": ["duration"] }
   }
   ```

5. **Avoid Redundant Measures**
   Store only **aggregated values** in fact tables; compute derived metrics in queries.

---

## **6. Related Patterns**
- **[Partitioning for Time-Series Data](#)** – Optimize large temporal datasets.
- **[Materialized Views for Aggregates](#)** – Pre-compute common queries.
- **[Columnar Storage](#)** – Use for analytical workloads (e.g., TimescaleDB).
- **[Data Quality Validation](#)** – Enforce schema constraints via triggers.

---
**Last Updated:** [Version/Date]
**Feedback:** [Contact Link]