# **[Pattern] Query Execution Timing Reference Guide**

---

## **Overview**
The **Query Execution Timing** pattern helps analyze and optimize database query performance by breaking down execution time into measurable components. This pattern is essential for identifying bottlenecks, tuning slow queries, and ensuring predictable response times in applications reliant on database operations.

By capturing timing metrics at critical execution stages (e.g., parsing, optimization, execution), developers can:
- **Pinpoint slow queries** (e.g., full table scans, inefficient joins).
- **Benchmark improvements** (e.g., indexing, query restructuring).
- **Set performance baselines** for new features.

This pattern is widely applicable to ORMs, raw SQL, and NoSQL databases, though implementation specifics vary by engine (e.g., PostgreSQL, MySQL, MongoDB).

---

## **Key Concepts**
| **Term**               | **Definition**                                                                 | **Example Metrics**                          |
|------------------------|-------------------------------------------------------------------------------|----------------------------------------------|
| **Parsing Time**       | Time spent validating SQL syntax and converting it to an execution plan.     | `parse_start`–`parse_end`                   |
| **Optimization Time**  | Time spent generating an efficient execution plan (e.g., choosing indexes).   | `optimization_start`–`optimization_end`     |
| **Execution Time**     | Time spent retrieving/fetching data (excluding I/O waits).                     | `execute_start`–`execute_end`               |
| **Total Query Time**   | Sum of parsing, optimization, and execution times.                            | `query_start`–`query_end`                   |
| **I/O Latency**        | Time spent waiting for disk/network I/O (excluded from default timing).      | `io_wait_start`–`io_wait_end` (if tracked)  |
| **WAL (Write-Ahead Log)** | Time spent recording changes before applying them (PostgreSQL-specific).     | `wal_start`–`wal_end`                      |

---

## **Implementation Details**

### **1. Capturing Timing Metrics**
Timing can be measured at different levels:

#### **A. Database-Level Timing**
Most databases provide built-in timing hooks:
- **PostgreSQL**:
  ```sql
  -- Enable logging detailed query timing (postgresql.conf)
  log_duration = on
  log_min_duration_statement = 100  -- Log queries >100ms
  ```
  Output:
  ```
  [2023-10-01 12:00:00] LOG:  duration: 456.789 ms  statement: SELECT * FROM users WHERE age > 30;
  ```

- **MySQL**:
  ```sql
  SET GLOBAL general_log = 'ON';  -- Log all queries
  SET GLOBAL slow_query_log = 'ON'; -- Log queries slower than `long_query_time`
  ```

- **SQL Server**:
  ```sql
  -- Enable query store (SSMS: Database Properties > Query Store)
  ALTER DATABASE YourDB SET QUERY_STORE = ON;
  ```
  View execution times via `sys.query_store_runtime_stats`.

#### **B. Application-Level Timing**
For fine-grained control, wrap queries in code:
```python
# Python (with asyncpg)
import asyncpg
import time

async def run_query(conn, query):
    start_time = time.time()
    async with conn.transaction():
        await conn.execute(query)
    end_time = time.time()
    print(f"Query took {end_time - start_time:.3f}s")
```

```java
// Java (with JDBC)
long start = System.nanoTime();
try (Connection conn = DriverManager.getConnection(URL)) {
    Statement stmt = conn.createStatement();
    stmt.executeQuery("SELECT * FROM orders");
}
long end = System.nanoTime();
System.out.printf("Query took %.3f ms%n", (end - start) / 1_000_000.0);
```

#### **C. ORM-Specific Timing**
- **SQLAlchemy** (Python):
  ```python
  from sqlalchemy import event
  @event.listens_for(Engine, "before_cursor_execute")
  def log_query_time(dbapi_connection, cursor, statement, parameters, context, executemany):
      context.start_time = time.time()
  @event.listens_for(Engine, "after_cursor_execute")
  def log_query_time(dbapi_connection, cursor, statement, parameters, context, executemany):
      print(f"Query took {time.time() - context.start_time:.3f}s")
  ```

- **Entity Framework Core** (C#):
  ```csharp
  using System.Diagnostics;
  var stopwatch = Stopwatch.StartNew();
  await dbContext.Orders.ToListAsync();
  stopwatch.Stop();
  Console.WriteLine($"Query took {stopwatch.ElapsedMilliseconds}ms");
  ```

---

### **2. Breaking Down Execution Time**
Use database-specific tools to dissect query phases:

| **Tool/Driver**       | **Command/Query**                          | **Purpose**                                  |
|-----------------------|--------------------------------------------|---------------------------------------------|
| **PostgreSQL `EXPLAIN ANALYZE`** | `EXPLAIN ANALYZE SELECT ...;`             | Shows step-by-step timing (e.g., `Seq Scan`, `Index Scan`). |
| **MySQL `PROFILE`**   | `SET profiling = 1; SELECT ...; SHOW PROFILE;` | Returns `Query_ID`, `Duration`, and phases. |
| **SQL Server `SET STATISTICS TIME`** | Enable in code (`SqlCommand.StatisticsOption`). | Logs parsing, compilation, execution. |
| **MongoDB `explain()`** | `db.collection.find().explain("executionStats")` | Breaks down `executionTimeMillis`. |

**Example Output (PostgreSQL):**
```
QUERY PLAN
----------------------------------------------------------------------------------------
 Seq Scan on users  (cost=0.00..1000.00 rows=1000 width=40) (actual time=456.789..456.790)
   Filter: (age > 30)
   Rows Removed by Filter: 9000
 Planning Time: 0.123 ms
 Execution Time: 456.790 ms
```
- **`actual time`**: Total execution time (includes I/O).
- **`Planning Time`**: Optimization time.

---

### **3. Common Pitfalls**
- **Ignoring I/O Latency**:
  Default timing may exclude disk/network waits. Use `pg_stat_activity` (PostgreSQL) or `SHOW PROFILE` (MySQL) to isolate I/O.
  ```sql
  -- PostgreSQL: Check active queries with I/O
  SELECT pid, usename, query, state, query_start, now() - query_start as duration
  FROM pg_stat_activity WHERE state = 'active';
  ```

- **Sampling Bias**:
  Logging every query may slow down the system. Configure thresholds (e.g., log only queries >100ms).

- **ORM Overhead**:
  ORMs add parsing/serialization time. Compare raw SQL vs. ORM-generated queries:
  ```python
  # Raw SQL (faster):
  conn.execute("SELECT * FROM users WHERE age > 30")
  # ORM (slower):
  db.session.query(User).filter(User.age > 30).all()
  ```

---

## **Schema Reference**
| **Schema**               | **Description**                                                                 | **Example Columns**                          |
|--------------------------|-------------------------------------------------------------------------------|----------------------------------------------|
| **`query_times`**        | Stores timing metrics for historical analysis.                                 | `query_id` (UUID), `start_time`, `end_time`, `parse_time`, `optimize_time`, `execute_time`, `total_time`, `user`, `application` |
| **`execution_plans`**    | Correlates timing with query plans (for optimization).                          | `query_id`, `plan_text`, `stats_mode` ("EXPLAIN", "ANALYZE") |
| **`bottlenecks`**        | Flags queries exceeding thresholds (e.g., >500ms).                               | `query_id`, `threshold_violation`, `recommendation` |

**Sample Table Creation (PostgreSQL):**
```sql
CREATE TABLE query_times (
    query_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    parse_time_ms BIGINT,
    optimize_time_ms BIGINT,
    execute_time_ms BIGINT,
    total_time_ms BIGINT,
    user VARCHAR(50),
    application VARCHAR(50),
    query_text TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_query_times_total_time ON query_times (total_time_ms);
```

---

## **Query Examples**

### **1. Log Query Timing to a Table**
```sql
-- PostgreSQL function to log timing
CREATE OR REPLACE FUNCTION log_query_time()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO query_times (
        start_time, end_time, parse_time_ms, optimize_time_ms, execute_time_ms,
        total_time_ms, query_text, user, application
    ) VALUES (
        TG_TGARG.start_time, TG_TGARG.end_time,
        TG_TGARG.parse_time_ms, TG_TGARG.optimize_time_ms, TG_TGARG.execute_time_ms,
        TG_TGARG.total_time_ms, TG_TGARG.query_text, current_user, 'myapp'
    );
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Set up trigger (PostgreSQL)
CREATE TABLE query_logs (
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    parse_time_ms BIGINT,
    optimize_time_ms BIGINT,
    execute_time_ms BIGINT,
    total_time_ms BIGINT,
    query_text TEXT,
    user VARCHAR(50),
    application VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TRIGGER log_queries_after
AFTER STATEMENT ON query_logs
FOR EACH STATEMENT EXECUTE FUNCTION log_query_time();
```

### **2. Find Slow Queries**
```sql
-- PostgreSQL: Queries slower than 500ms in last 24h
SELECT *
FROM query_times
WHERE total_time_ms > 500
  AND start_time > NOW() - INTERVAL '24 hours'
ORDER BY total_time_ms DESC
LIMIT 10;
```

```sql
-- MySQL: Queries in slow query log
SELECT *
FROM mysql.slow_log
WHERE timer > 500
ORDER BY timer DESC
LIMIT 10;
```

### **3. Analyze Execution Plan Trends**
```sql
-- PostgreSQL: Queries using full table scans
SELECT query_text, COUNT(*)
FROM query_times qt
JOIN execution_plans ep ON qt.query_id = ep.query_id
WHERE ep.plan_text LIKE '%Seq Scan%'
GROUP BY query_text
ORDER BY COUNT(*) DESC;
```

---

## **Related Patterns**
1. **[Query Rewriting]** ([Pattern] Query Rewriting Reference Guide)
   - Optimize slow queries via indexing, partitioning, or SQL restructuring.
   - *Example*: Replace `SELECT *` with explicit columns to reduce I/O.

2. **[Caching Query Results]** ([Pattern] Cache-Aside Reference Guide)
   - Reduce repeated query execution for expensive operations.
   - *Example*: Cache frequent `SELECT * FROM products` for 1 hour.

3. **[Batch Processing]** ([Pattern] Micro-Batching Reference Guide)
   - Minimize round-trips to the database by grouping operations.
   - *Example*: Use `INSERT ... VALUES (1,2), (3,4)` instead of two separate `INSERT`s.

4. **[Connection Pooling]** ([Pattern] Connection Pooling Reference Guide)
   - Reuse database connections to avoid overhead.
   - *Example*: Configure `pgbouncer` (PostgreSQL) or `HikariCP` (Java).

5. **[Asynchronous Query Execution]** ([Pattern] Async Query Execution Reference Guide)
   - Offload query execution to background threads to improve UI responsiveness.
   - *Example*: Use `asyncpg` (Python) or `SqlAsyncConnection` (C#).

6. **[Distributed Tracing]** ([Pattern] Distributed Tracing Reference Guide)
   - Correlate query timing with application latency across microservices.
   - *Example*: Use OpenTelemetry to trace `SELECT user` → `render UI`.

---

## **Further Reading**
- [PostgreSQL Performance Tuning](https://www.postgresql.org/docs/current/using-explain.html)
- [MySQL Query Optimization](https://dev.mysql.com/doc/refman/8.0/en/query-optimization.html)
- [Database Performance Antipatterns](https://use-the-index-luke.com/) (Luke Baker)

---
**Last Updated:** [Insert Date]
**Version:** 1.0