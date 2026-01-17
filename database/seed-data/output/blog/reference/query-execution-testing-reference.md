# **[Pattern] Query Execution Testing Reference Guide**

---
## **Overview**
The **Query Execution Testing** pattern ensures end-to-end validation of query performance, correctness, and edge-case handling by simulating real-world execution scenarios. Unlike unit tests, this pattern validates:
- Full data pipeline execution (ingestion → processing → output).
- Correctness under varied conditions (e.g., empty input, large datasets).
- Performance metrics (latency, resource usage, scaling).
- Compliance with business rules or validation logic embedded in queries.

This pattern is critical for systems relying on queries (SQL, NoSQL, graph, or OLAP) where correctness and efficiency directly impact business outcomes. Use it for:
- Database applications (e.g., analytics dashboards).
- Data transformation pipelines (e.g., ETL jobs).
- API-driven query execution (e.g., REST endpoints for analytical queries).

---

## **Schema Reference**

| **Component**          | **Description**                                                                                                                                                                                                 | **Key Attributes**                                                                                     |
|------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------|
| **Test Case**          | A logical unit of test execution, defining inputs, expected outputs, and validation rules.                                                                                                                 | `id` (UUID), `name` (string), `description` (string), `priority` (enum: `low/medium/high`).          |
| **Input Data**         | Simulated or real data fed into the query system. Can be static (CSV, JSON) or dynamic (API responses, DB snapshots).                                                                                     | `source` (string: `"static"|"dynamic"`), `file_path` (string), `api_endpoint` (string), `sample_size` (integer).        |
| **Query Definition**   | The query to be tested (e.g., SQL, Cypher, SPARK SQL). Includes parameters, schema references, and optional optimizations (e.g., indexes).                                                                   | `query` (string), `language` (string), `parameters` (JSON), `dependencies` (list of schema objects).    |
| **Execution Context**  | Environment variables affecting query execution (e.g., connection strings, timeout settings, parallelism).                                                                                                       | `database_url` (string), `timeout_ms` (integer), `max_concurrent_queries` (integer), `region` (string). |
| **Expected Output**    | The schema and sample data the query should return. Used for post-execution validation.                                                                                                                 | `schema` (JSON), `sample_data` (JSON), `validation_rules` (JSON).                                      |
| **Performance Metrics**| Key performance indicators to monitor during execution (e.g., execution time, memory usage, rows processed).                                                                                                   | `target_latency_ms` (integer), `max_memory_mb` (integer), `rows_processed` (integer).                  |
| **Test Result**        | Output of a test run, including pass/fail status, timestamps, and diagnostic data.                                                                                                                           | `status` (enum: `pass/fail/skipped`), `timestamp` (datetime), `duration_ms` (integer), `logs` (string).  |
| **Validation Rule**    | Custom assertions (e.g., "output sum > 0") or external validations (e.g., API call to external service).                                                                                                     | `type` (string: `"regex"|"json_schema"|"api"`), `expression` (string), `external_endpoint` (string).       |

---

## **Implementation Details**

### **1. Test Case Design**
A test case follows the **Given-When-Then** structure:
- **Given**: Input data and context (e.g., "a table with 100K rows").
- **When**: The query is executed under specified conditions.
- **Then**: Output is validated against expectations (e.g., "returns 10 rows matching criteria").

#### **Example Structure**:
```json
{
  "test_case": {
    "id": "uuid123",
    "name": "Aggregate Sales by Region",
    "priority": "high",
    "input_data": {
      "source": "static",
      "file_path": "data/sales.csv",
      "sample_size": 1000
    },
    "query": {
      "language": "sql",
      "query": "SELECT region, SUM(amount) FROM sales WHERE date > ? GROUP BY region",
      "parameters": ["2023-01-01"],
      "dependencies": ["sales(region, amount, date)"]
    },
    "execution_context": {
      "database_url": "postgres://user:pass@db.example.com:5432/analytics",
      "timeout_ms": 5000
    },
    "expected_output": {
      "schema": {"region": "string", "total_sales": "float"},
      "sample_data": [{"region": "North", "total_sales": 125000}],
      "validation_rules": [
        {"type": "regex", "expression": "total_sales:\\d+"}
      ]
    },
    "performance_metrics": {
      "target_latency_ms": 2000
    }
  }
}
```

---

### **2. Input Data Generation**
- **Static Inputs**: Define paths to pre-populated files (CSV, JSON) or use mock generators (e.g., Faker library).
- **Dynamic Inputs**: Fetch real-time data from APIs or databases (e.g., `curl` to a REST endpoint).
- **Edge Cases**:
  - Empty tables or null values.
  - Data with outliers (e.g., negative values in a `price` column).
  - Schema mismatches (e.g., missing required columns).

#### **Example: Dynamic Input via API**
```bash
# Fetch weather data from an API and store as JSON
curl -o weather_data.json "https://api.weather.example.com/data?city=NewYork"
```

---

### **3. Query Execution**
Execute queries in controlled environments (e.g., staging databases, Dockerized services). Key considerations:
- **Isolation**: Run tests in isolated databases or transactions to avoid side effects.
- **Retry Logic**: Handle transient failures (e.g., connection timeouts) with exponential backoff.
- **Parallelism**: Control concurrency to avoid resource contention (e.g., `max_concurrent_queries: 5`).

#### **Example: SQL Execution (Python)**
```python
import psycopg2
from psycopg2 import sql

def execute_query(test_case):
    conn = psycopg2.connect(test_case["execution_context"]["database_url"])
    cursor = conn.cursor()
    cursor.execute(
        sql.SQL(test_case["query"]["query"]),
        test_case["query"]["parameters"]
    )
    results = cursor.fetchall()
    conn.close()
    return results
```

---

### **4. Output Validation**
Validate outputs against:
- **Structural Checks**: Ensure columns/types match the expected schema.
- **Data Checks**: Use SQL assertions (e.g., `COUNT(*) = 10`) or regex patterns.
- **Custom Logic**: Invoke external services (e.g., call a fraud-detection API on query results).

#### **Example: SQL Assertion**
```sql
-- Verify total sales sum matches expected value
SELECT
    SUM(amount) AS total_sales
FROM sales
WHERE date > '2023-01-01';

-- Expected: total_sales == 1250000
```

#### **Example: Regex Validation**
```python
import re

def validate_output(results):
    for row in results:
        assert re.match(r"total_sales:\d+", str(row)), "Output format invalid"
```

---

### **5. Performance Testing**
Measure:
- **Latency**: End-to-end execution time (including I/O).
- **Resource Usage**: CPU/memory via tools like `perf` (Linux) or Prometheus.
- **Scalability**: Test under load (e.g., 100 concurrent queries).

#### **Example: Load Testing with Locust**
```python
# locustfile.py
from locust import HttpUser, task

class QueryUser(HttpUser):
    @task
    def run_analytics_query(self):
        self.client.post("/api/query", json={"query": "SELECT * FROM users"})
```

---

### **6. Test Result Reporting**
Store results in a structured format (e.g., JSON, database table) with:
- **Status**: `pass`/`fail`/`skipped`.
- **Timestamps**: Start/end time, duration.
- **Diagnostics**: Logs, SQL execution plans, or snapshots of input/output.

#### **Example Output**:
```json
{
  "test_result": {
    "test_case_id": "uuid123",
    "status": "pass",
    "timestamp": "2023-10-01T12:00:00Z",
    "duration_ms": 1500,
    "logs": "Executed query in 1.5s. Rows returned: 50",
    "metrics": {
      "latency_percentage": 95,
      "rows_processed": 50
    }
  }
}
```

---

## **Query Examples**

### **1. Simple Aggregation (SQL)**
**Test Case**: Verify `SUM(amount)` across a sales table.
**Query**:
```sql
SELECT
    SUM(amount) AS total_amount
FROM sales
WHERE date > ?;
```
**Validation**:
- Expected: `total_amount > 0`.
- Schema: `{"total_amount": "float"}`.

---

### **2. Joined Query (NoSQL)**
**Test Case**: Validate a MongoDB aggregation pipeline.
**Query**:
```json
[
  { "$match": { "status": "active" } },
  { "$group": { "_id": "$region", "count": { "$sum": 1 } } }
]
```
**Validation**:
- Sample output: `[{"_id": "North", "count": 150}]`.
- Use `$expr` assertions in MongoDB tests.

---

### **3. Parameterized Query (Edge Case)**
**Test Case**: Handle null parameters.
**Query**:
```sql
SELECT
    user_id,
    COALESCE(bonus, 0) AS bonus_amount
FROM users
WHERE department = ?;
```
**Input**:
```json
{ "parameters": [null], "sample_user": {"department": "Engineering"} }
```
**Validation**:
- All `bonus_amount` fields should be `0` if parameter is `null`.

---

### **4. Graph Query (Cypher)**
**Test Case**: Verify shortest path in a graph database.
**Query**:
```cypher
MATCH p = shortestPath(
    (a:Person)-[*1..3]-(b:Person)
    WHERE a.name = $start AND b.name = $end
)
RETURN p;
```
**Input**:
```json
{ "parameters": { "start": "Alice", "end": "Bob" } }
```
**Validation**:
- Path length should be `≤ 3` edges.
- Node count in path should match expected relationships.

---

## **Related Patterns**

| **Pattern**               | **Purpose**                                                                                     | **When to Use**                                                                                     |
|---------------------------|-------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| **Schema Testing**        | Validate data models (schema, constraints, relationships) before query execution.               | When schema changes frequently or need to ensure backward compatibility.                           |
| **Data Generation**       | Automatically generate test datasets (synthetic or derived from real data).                    | For large-scale or distributed systems requiring realistic inputs.                                |
| **Performance Benchmarking** | Compare query performance across different indices, databases, or hardware.                  | Optimizing query plans or evaluating database upgrades.                                             |
| **Chaos Testing**         | Introduce failures (e.g., network partitions, disk failures) to test query resilience.        | For critical systems where high availability is required.                                           |
| **Rolling Backtesting**   | Test queries on historical data to validate predictive models or time-series analysis.       | Financial forecasting, fraud detection, or trend analysis systems.                                |
| **API Contract Testing**  | Validate query endpoints (e.g., REST/gRPC) for correctness and schema compliance.              | For serverless or microservices querying external databases.                                        |

---

## **Best Practices**
1. **Modularize Tests**: Isolate queries to avoid brittle tests (e.g., one test shouldn’t rely on another’s data).
2. **Use Mocks for External Dependencies**: Replace slow APIs/database calls with mocks during unit testing.
3. **Parameterize Tests**: Avoid hardcoding values (e.g., dates, IDs) to improve reusability.
4. **Automate Cleanup**: Reset test databases or tables after execution to avoid pollution.
5. **Log Everything**: Capture SQL execution plans, input/output samples, and system metrics for debugging.
6. **Prioritize**: Categorize tests by risk (e.g., `high` for critical business queries).
7. **Integrate with CI/CD**: Run query tests in pipelines to catch regressions early.