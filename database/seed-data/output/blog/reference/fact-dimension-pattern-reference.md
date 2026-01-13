**[Pattern] FraiseQL Fact-Dimension Pattern Reference Guide**

---

### **1. Overview**
FraiseQL’s **Fact-Dimension Pattern** optimizes time-series and analytical workloads by separating **measures** (aggregatable metrics) into fast SQL columns and **dimensions** (flexible grouping attributes) into a **JSONB** column. This design enables **10–100x faster aggregations** via direct column access while maintaining schema flexibility via JSON. Denormalized **filter columns** (indexed foreign keys) accelerate `WHERE` clauses without requiring joins.

**Core Principles:**
- **No joins allowed** – All dimensional data must be denormalized at ETL time.
- **Measures in SQL columns** – Optimized for aggregation (e.g., `SUM`, `AVG`).
- **Dimensions in JSONB** – Supports arbitrary nested attributes and future extensibility.
- **Filter columns** – Fast lookups via indexed foreign keys (e.g., `user_id`, `event_type`).
- **Primary key** – A unique identifier (UUID or BIGSERIAL) for row referencing.

This pattern excels for event logs, sensor data, or any use case requiring low-latency aggregations with evolving schema needs.

---

### **2. Schema Reference**

#### **Fact Table Structure**
| Column Name       | Type         | Description                                                                                                                                                     | Indexing         | Notes                          |
|-------------------|--------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------|--------------------------------|
| `id`              | UUID/BIGSERIAL | Primary key for record identification.                                                                                                               | `PRIMARY KEY`    |                                  |
| `measure1`        | INT/BIGINT   | Numeric aggregation metric (e.g., count, quantity).                                                                                                       | `INDEX`          | Optimized for `SUM`, `AVG`, etc. |
| `measure2`        | DECIMAL      | Another numeric measure (e.g., price, revenue).                                                                                                           | `INDEX`          |                                  |
| `dimensions`      | JSONB         | Denormalized dimensions (e.g., `{"user_id": "abc123", "category": "electronics", "timestamp": "2024-01-01"}`).                                            |                  | Supports nested JSON structures. |
| `user_id`         | UUID/VARCHAR | Denormalized foreign key for fast filtering (e.g., `WHERE user_id = 'abc123'`).                                                                            | `INDEX`          | Required for common filters.    |
| `event_type`      | VARCHAR      | Categorical filter (e.g., `purchase`, `view`).                                                                                                           | `INDEX`          |                                  |
| `region`          | VARCHAR      | Geographic filter (e.g., `us-west`, `eu-central`).                                                                                                       | `INDEX`          |                                  |
| `_timestamp`      | TIMESTAMP    | Optional column for time-series partitioning (if not stored in `dimensions`).                                                                             | `INDEX`          | Alternate to `dimensions.timestamp`. |

**Example Schema (PostgreSQL):**
```sql
CREATE TABLE facts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    measure1 BIGINT NOT NULL,
    measure2 DECIMAL(10, 2) NOT NULL,
    dimensions JSONB NOT NULL,
    user_id UUID NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    region VARCHAR(50) NOT NULL,
    _timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_event_type (event_type),
    INDEX idx_region (region),
    INDEX idx_timestamp (_timestamp)
);
```

---

### **3. Query Examples**

#### **Aggregations on Measures**
Fast aggregations leverage SQL-optimized columns:
```sql
-- Sum of measure1 grouped by region
SELECT
    region,
    SUM(measure1) AS total_events
FROM facts
WHERE event_type = 'purchase'
GROUP BY region;

-- Average measure2 by user_id
SELECT
    user_id,
    AVG(measure2) AS avg_revenue
FROM facts
GROUP BY user_id;
```

#### **Filtering with Denormalized Columns**
Denormalized columns (e.g., `user_id`, `event_type`) enable fast `WHERE` clauses:
```sql
-- Filter purchases from a specific user
SELECT * FROM facts
WHERE user_id = 'abc123' AND event_type = 'purchase';

-- Filter events by region and timestamp range
SELECT * FROM facts
WHERE region = 'us-west'
  AND _timestamp BETWEEN '2024-01-01' AND '2024-01-31';
```

#### **JSONB Dimension Queries**
Access nested dimensions with PostgreSQL’s JSON operators:
```sql
-- Extract and filter by nested dimension (e.g., user attributes)
SELECT
    user_id,
    dimensions->>'category' AS category,
    SUM(measure1) AS count
FROM facts
WHERE dimensions->>'category' = 'electronics'
GROUP BY user_id, category;

-- Query dynamic dimensions (e.g., add new fields without schema changes)
SELECT * FROM facts
WHERE dimensions->>'new_custom_field' = 'value';
```

#### **Time-Series Analytics**
Leverage `_timestamp` or `dimensions.timestamp` for temporal queries:
```sql
-- Rolling sum over 7 days
SELECT
    DATE_TRUNC('day', _timestamp) AS day,
    SUM(measure1) AS daily_events
FROM facts
WHERE _timestamp >= NOW() - INTERVAL '7 days'
GROUP BY day
ORDER BY day;

-- Query events with timestamp in dimensions
SELECT * FROM facts
WHERE dimensions->>'timestamp'::TIMESTAMP BETWEEN '2024-01-01' AND '2024-01-07';
```

#### **Combining Measures and Dimensions**
Combine SQL measures with JSONB dimensions for rich analytics:
```sql
-- Top 5 categories by revenue
SELECT
    dimensions->>'category' AS category,
    SUM(measure2) AS total_revenue
FROM facts
GROUP BY category
ORDER BY total_revenue DESC
LIMIT 5;
```

---

### **4. Implementation Best Practices**

#### **ETL Considerations**
- **Denormalize dimensions at load time** to avoid joins:
  ```python
  # Pseudocode for ETL (e.g., Python + SQLAlchemy)
  def transform_dimensions(row):
      return {
          'user_id': row['user']['id'],
          'category': row['product']['category'],
          'timestamp': row['event']['created_at']
      }
  ```
- **Avoid partial updates** to `dimensions` (use new rows or `ALTER TABLE` with caution).

#### **Schema Evolution**
- **Add new measures**: Append SQL columns (e.g., `measure3`).
- **Add new dimensions**: Extend the `JSONB` column (no migration needed).
- **Add new filter columns**: Add indexed columns (e.g., `device_type`).

#### **Indexing Strategy**
- **Index all filter columns** (`user_id`, `event_type`, `region`, `_timestamp`).
- **Avoid over-indexing** `dimensions` (use dedicated columns for common filters).
- **Partition by time** for large tables:
  ```sql
  CREATE TABLE facts (
      -- columns...
  ) PARTITION BY RANGE (_timestamp);
  ```

#### **Performance Tuning**
- **Use `EXPLAIN ANALYZE`** to verify query plans:
  ```sql
  EXPLAIN ANALYZE
  SELECT * FROM facts WHERE user_id = 'abc123';
  ```
- **Materialized views** for common aggregations:
  ```sql
  CREATE MATERIALIZED VIEW daily_sales AS
  SELECT
      DATE_TRUNC('day', _timestamp) AS day,
      SUM(measure2) AS revenue
  FROM facts
  GROUP BY day;
  ```

---

### **5. Query Patterns and Anti-Patterns**

#### **✅ Recommended Patterns**
| Scenario                     | Query Example                                                                 |
|------------------------------|-----------------------------------------------------------------------------|
| **Fast aggregations**        | `SELECT SUM(measure1), AVG(measure2) FROM facts WHERE region = 'us';`     |
| **Filtering by denormalized**| `SELECT * FROM facts WHERE user_id = 'abc123';`                              |
| **JSONB attribute queries**  | `SELECT * FROM facts WHERE dimensions->>'status' = 'active';`               |
| **Time-range queries**       | `SELECT * FROM facts WHERE _timestamp BETWEEN ...;`                          |

#### **❌ Anti-Patterns**
| Scenario                     | Avoid                                                                       |
|------------------------------|---------------------------------------------------------------------------|
| **Joins**                    | Never join to a separate `dimensions` table – denormalize at ETL time.    |
| **Complex JSONB parsing**    | Avoid deep recursion in `json_path_ops` for performance.                   |
| **Dynamic SQL for filters**  | Prefer indexed columns over `WHERE dimensions ?& '{"key": "value"}'`.     |
| **Partial updates**          | Use new rows instead of modifying `dimensions` mid-stream.                 |

---

### **6. Related Patterns**
| Pattern                          | Use Case                                                                 | When to Combine With Fact-Dimension         |
|----------------------------------|------------------------------------------------------------------------|---------------------------------------------|
| **Time-Series Partitioning**     | Large datasets needing temporal slices.                                | Partition `facts` by `_timestamp` for faster scans. |
| **Materialized Views**          | Pre-computed aggregations (e.g., daily metrics).                       | Create views over `facts` for slow-changing dimensions. |
| **Denormalized Foreign Keys**   | Fast lookups without joins (e.g., `user_id`, `product_id`).              | Add to `facts` alongside `dimensions`.       |
| **JSONB Indexes**                | Accelerate queries on nested JSON attributes.                          | Use `GIN` or `GiST` indexes on `dimensions`.   |
| **Incremental ETL**             | Streaming data pipelines (e.g., Kafka → PostgreSQL).                   | Denormalize dimensions in real-time sinks.   |

---

### **7. Example: ETL Pipeline (FraiseQL + Python)**
```python
from fraise import Table, Column, SQLAlchemyEngine
from datetime import datetime

# Define the fact table
facts = Table(
    name="facts",
    columns=[
        Column(name="id", type_="UUID", primary_key=True),
        Column(name="measure1", type_="INT"),
        Column(name="measure2", type_="DECIMAL(10, 2)"),
        Column(name="dimensions", type_="JSONB"),
        Column(name="user_id", type_="UUID", indexed=True),
        Column(name="event_type", type_="VARCHAR(50)", indexed=True),
        Column(name="_timestamp", type_="TIMESTAMP", indexed=True),
    ],
    engine=SQLAlchemyEngine("postgresql://user:pass@localhost/db")
)

# Transform raw data
def transform_event(event):
    return {
        "id": uuid.uuid4(),
        "measure1": 1,  # Example: count
        "measure2": event["price"],
        "dimensions": {
            "user_id": event["user"]["id"],
            "category": event["product"]["category"],
            "timestamp": event["created_at"].isoformat()
        },
        "user_id": event["user"]["id"],
        "event_type": event["type"],
        "_timestamp": datetime.fromisoformat(event["created_at"])
    }

# Write to FraiseQL
for event in raw_events:
    record = transform_event(event)
    facts.insert(**record).execute()
```

---
### **8. Troubleshooting**
| Issue                          | Diagnosis                          | Solution                                  |
|--------------------------------|-------------------------------------|-------------------------------------------|
| **Slow aggregations**          | Missing indexes on measure columns | Add `INDEX` to frequently aggregated columns. |
| **JSONB query performance**    | Deep nesting or unindexed queries  | Use `GIN` index on `dimensions`.          |
| **ETL failures**               | Schema mismatch                     | Validate `dimensions` structure in ETL.   |
| **High storage usage**         | Large JSONB payloads                | Compress or normalize repeated dimensions. |

---
### **9. References**
- [PostgreSQL JSONB Documentation](https://www.postgresql.org/docs/current/datatype-json.html)
- [FraiseQL Performance Guide](https://fraise.com/docs/performance)
- [Denormalization for Analytics](https://www.percona.com/blog/denormalization-for-analytics)