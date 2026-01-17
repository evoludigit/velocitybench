# **[Pattern] Optimization Setup Reference Guide**
*An end-to-end guide to configuring and implementing optimization patterns in **<System/Tool Name>** for performance, efficiency, and scalability.*

---

## **1. Overview**
The **Optimization Setup** pattern streamlines the process of identifying, configuring, and applying optimizations across your system, application, or infrastructure. This pattern ensures that performance bottlenecks are systematically addressed while maintaining reliability, scalability, and observability.

Optimization Setup follows a structured approach:
- **Discovery:** Identify inefficient components (e.g., slow queries, underutilized resources).
- **Configuration:** Adjust settings, parameters, or annotations to enhance performance.
- **Validation:** Measure improvements and iterate as needed.
- **Automation:** (Optional) Integrate optimizations into CI/CD pipelines or monitoring workflows.

This guide covers best practices, schema references, and implementation steps to enable data-driven optimization across databases, caching layers, compute resources, and API endpoints.

---

## **2. Key Concepts**

### **2.1 Optimization Categories**
Optimizations are categorized by scope:
| **Category**          | **Description**                                                                 | **Example Use Cases**                          |
|-----------------------|---------------------------------------------------------------------------------|-----------------------------------------------|
| **Database**          | Query tuning, indexing, connection pooling                                      | Slow SQL queries, high-latency joins          |
| **Compute**           | CPU, memory, parallel processing, caching                                       | CPU-bound tasks, high-memory workloads        |
| **Network**           | Load balancing, CDN configurations, protocol optimization                         | High-traffic APIs, global latency reduction   |
| **Storage**           | File I/O, disk caching, compression                                             | Large dataset processing, frequent file reads |
| **Application Logic** | Algorithmic improvements, lazy loading, batch processing                        | Nested loops, repeated computations           |

### **2.2 Optimization Metrics**
Track these KPIs to validate improvements:
- **Latency:** Response time (e.g., p99, p50).
- **Throughput:** Requests/sec (RPS), transactions/minute.
- **Resource Utilization:** CPU%, memory, disk I/O.
- **Error Rates:** Failed requests, timeouts, retries.
- **Cost:** Operational expenses (e.g., cloud compute hours).

---
## **3. Schema Reference**
Below are the core schemas for defining and applying optimizations. Adjust field names to match your system’s API or configuration format.

### **3.1 Optimization Entity Schema**
Defines an optimization task with metadata and target components.

| **Field**               | **Type**       | **Description**                                                                 | **Example Value**                          |
|--------------------------|----------------|---------------------------------------------------------------------------------|--------------------------------------------|
| `id`                     | `string`       | Unique identifier for the optimization.                                        | `"opt_db-index-2024"`                      |
| `name`                   | `string`       | Human-readable name (e.g., "Add Index to `users` table").                      | `"users_table_idx"`                        |
| `category`              | `string`       | Category (e.g., `database`, `compute`, `network`).                              | `"database"`                                |
| `status`                | `enum`         | `draft`, `proposed`, `implemented`, `validated`, `deprecated`.                   | `"implemented"`                             |
| `priority`              | `integer`      | Severity level (1–5, where 1 = critical).                                        | `3`                                        |
| `component`             | `object`       | Target resource (e.g., database table, API endpoint).                           | `{ "type": "table", "name": "orders" }`    |
| `configuration`         | `object`       | Optimized settings (e.g., index definition, cache TTL).                         | `{ "index": { "columns": ["user_id", "date"] } }` |
| `baseline_metrics`      | `object`       | Pre-optimization performance data.                                              | `{ "latency": 500ms, "throughput": 100RPS }`|
| `target_metrics`        | `object`       | Post-optimization goals.                                                        | `{ "latency": "<200ms", "throughput": ">500RPS" }` |
| `validation_date`       | `datetime`     | When metrics were last validated.                                               | `"2024-05-15T14:30:00Z"`                  |
| `owner`                 | `string`       | Assigned team/engineer.                                                           | `"backend-team"`                           |
| `tags`                  | `array`        | Categorical labels (e.g., `["postgres", "high-traffic"]`).                     | `["cache", "query-optimization"]`          |

---

### **3.2 Query Schema (for Database Optimizations)**
Defines SQL queries and their optimization strategies.

| **Field**               | **Type**       | **Description**                                                                 | **Example Value**                          |
|--------------------------|----------------|---------------------------------------------------------------------------------|--------------------------------------------|
| `query_text`            | `string`       | The raw SQL query (sanitized).                                                   | `"SELECT * FROM orders WHERE user_id = ?"`  |
| `execution_plan`        | `string`       | Generated plan (e.g., from `EXPLAIN ANALYZE`).                                   | *"Seq Scan on orders (cost=0.15..8.17)"*  |
| `optimization_strategy` | `enum`         | `index`, `partitioning`, `query_refactor`, `materialized_view`.                  | `"index"`                                  |
| `index_suggestion`      | `object`       | Proposed index definition.                                                       | `{ "columns": ["user_id", "date"], "type": "btree" }` |
| `partitioning_scheme`   | `object`       | Partitioning rules (e.g., by range or hash).                                    | `{ "by": "date", "range": ["2023-01-01", "2024-01-01"] }` |

---

### **3.3 Compute Optimization Schema**
Targets CPU, memory, or parallelism settings.

| **Field**               | **Type**       | **Description**                                                                 | **Example Value**                          |
|--------------------------|----------------|---------------------------------------------------------------------------------|--------------------------------------------|
| `resource_type`          | `enum`         | `cpu`, `memory`, `disk`, `network`.                                              | `"cpu"`                                    |
| `current_utilization`    | `object`       | Baseline metrics (e.g., CPU%: 90%, memory: 8GB).                                  | `{ "cpu": 95, "memory": "7.5GB" }`         |
| `target_utilization`     | `object`       | Optimized thresholds.                                                              | `{ "cpu": "<80", "memory": "<6GB" }`       |
| `action`                 | `string`       | Proposed fix (e.g., "Scale up", "Enable multi-threading").                         | `"Enable async processing"`                |
| `dependencies`           | `array`        | Linked optimizations (e.g., "Requires new index").                                | `["opt_db-index-2024"]`                   |

---
## **4. Implementation Steps**

### **4.1 Discovery Phase**
1. **Monitor Baselines:**
   - Use tools like **Prometheus**, **Datadog**, or **New Relic** to collect metrics.
   - Example query (PromQL):
     ```sql
     rate(http_requests_total[5m]) by (route)
     ```
   - Flag outliers (e.g., latency > 2σ from mean).

2. **Profile Bottlenecks:**
   - **Databases:** Run `EXPLAIN ANALYZE` on slow queries.
   - **Applications:** Use profiling tools (e.g., `pprof` for Go, `py-spy` for Python).
   - **Compute:** Check cloud provider metrics (e.g., AWS CloudWatch for CPU throttling).

3. **Categorize Findings:**
   - Tag issues by `category` (e.g., `database`, `compute`) and `severity`.

---
### **4.2 Configuration Phase**
#### **Database Optimizations**
- **Add Indexes:**
  ```sql
  CREATE INDEX idx_orders_user_date ON orders(user_id, date);
  ```
- **Query Refactoring:**
  - Replace `SELECT *` with explicit columns.
  - Use `LIMIT` for pagination.
  - Example:
    ```sql
    -- Before (slow)
    SELECT * FROM products WHERE category = 'electronics';

    -- After (optimized)
    SELECT id, name, price FROM products WHERE category = 'electronics' LIMIT 100;
    ```

- **Partitioning:**
  ```sql
  CREATE TABLE sales (
      id SERIAL,
      amount DECIMAL(10,2)
  ) PARTITION BY RANGE (amount);

  CREATE TABLE sales_p0 PARTITION OF sales FOR VALUES FROM (0) TO (1000);
  ```

#### **Compute Optimizations**
- **Enable Caching:**
  - **Redis:** Set `TTL` (e.g., `EXPIRE cache_key 3600`).
  - **CDN:** Configure cache headers (`Cache-Control: public, max-age=300`).
- **Parallel Processing:**
  - Use **async tasks** (e.g., Celery, RabbitMQ) for long-running jobs.
  - Example (Python `concurrent.futures`):
    ```python
    from concurrent.futures import ThreadPoolExecutor

    def process_data(data):
        # Heavy computation
        pass

    with ThreadPoolExecutor(max_workers=4) as executor:
        executor.map(process_data, data_chunk)
    ```

#### **Network Optimizations**
- **Load Balancing:**
  - Configure **Nginx** or **AWS ALB** to distribute traffic.
  - Example Nginx upstream block:
    ```nginx
    upstream backend {
        server api1:8080;
        server api2:8080;
    }
    ```
- **Protocol Tuning:**
  - Use **HTTP/2** or **gRPC** for lower latency.
  - Compress responses (`Accept-Encoding: gzip`).

---
### **4.3 Validation Phase**
1. **Compare Metrics:**
   - Pre- vs. post-optimization (e.g., latency dropped from 500ms → 150ms).
   - Example validation query:
     ```sql
     SELECT
         query_text,
         AVG(execution_time) as avg_latency,
         COUNT(*) as requests
     FROM query_performance
     WHERE query_text LIKE '%orders%'
     GROUP BY query_text;
     ```

2. **Load Testing:**
   - Simulate traffic with **Locust** or **JMeter**.
   - Example Locust script:
     ```python
     from locust import HttpUser, task

     class DBUser(HttpUser):
         @task
         def fetch_orders(self):
             self.client.get("/orders?user_id=123")
     ```
   - Run with:
     ```bash
     locust -f locustfile.py --host=https://api.example.com
     ```

3. **A/B Testing:**
   - Route a percentage of traffic to the optimized endpoint (e.g., via **Feature Flags**).

---
### **4.4 Automation (Optional)**
Integrate optimizations into workflows:
- **CI/CD Pipelines:**
  - Run performance tests in GitHub Actions:
    ```yaml
    - name: Run Load Test
      run: locust -f load_tests.py --host=https://staging.example.com --headless -u 100 -r 10
    ```
- **Monitoring Alerts:**
  - Set up alerts in **Slack/PagerDuty** when metrics degrade (e.g., latency > 500ms).
  - Example Prometheus alert:
    ```yaml
    - alert: HighLatency
      expr: rate(http_request_duration_seconds{quantile="0.99"}[5m]) > 0.5
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "High p99 latency on {{ $labels.route }}"
    ```

---
## **5. Query Examples**
### **5.1 Database Optimization Queries**
**Find Slow Queries:**
```sql
SELECT
    query,
    avg_exec_time,
    calls,
    rows_processed
FROM pg_stat_statements
ORDER BY avg_exec_time DESC
LIMIT 10;
```

**Check Missing Indexes (PostgreSQL):**
```sql
SELECT
    schemaname || '.' || relname AS table,
    indexrelname AS missing_index,
    seq_scan,
    idx_scan,
    idx_tup_read
FROM (
    SELECT
        n.nspname AS schemaname,
        c.relname AS table,
        i.relname AS missing_index,
        idx_scan,
        seq_scan,
        idx_tup_read
    FROM pg_class c
    JOIN pg_namespace n ON c.relnamespace = n.oid
    LEFT JOIN pg_index i ON i.indrelid = c.oid
    WHERE
        c.relkind = 'r'
        AND n.nspname NOT IN ('pg_catalog', 'information_schema')
        AND idx_scan < seq_scan * 0.1  -- Heuristic for missing indexes
) AS x
ORDER BY seq_scan - idx_scan DESC
LIMIT 10;
```

---
### **5.2 Compute Optimization Queries**
**AWS CloudWatch: CPU Throttling Alerts:**
```json
{
  "MetricName": "CPUUtilization",
  "Namespace": "AWS/EC2",
  "Dimensions": [
    { "Name": "InstanceId", "Value": "i-1234567890abcdef0" }
  ],
  "Statistic": "Average",
  "Period": 300,
  "Unit": "Percent",
  "ComparisonOperator": "GreaterThanThreshold",
  "Threshold": 90,
  "EvaluationPeriods": 2,
  "DatapointsToAlarm": 1,
  "AlarmDescription": "High CPU utilization detected."
}
```

---
## **6. Error Handling & Rollback**
| **Scenario**               | **Action**                                                                 |
|-----------------------------|----------------------------------------------------------------------------|
| Post-optimization degradation | Revert changes (e.g., remove index, downgrade cache TTL).                   |
| False positives (e.g., noisy metrics) | Add sampling or adjust thresholds.                                         |
| Dependency conflicts         | Isolate optimizations (e.g., test in staging first).                       |
| Failed load tests            | Investigate bottlenecks (e.g., database connections, external API calls).   |

---
## **7. Related Patterns**
| **Pattern**                  | **Description**                                                                 | **When to Use**                                  |
|-------------------------------|---------------------------------------------------------------------------------|--------------------------------------------------|
| **[Observability](pattern_observability)** | Centralized logging, metrics, and tracing for debugging optimizations.        | After implementation to validate changes.       |
| **[Caching Strategy](pattern_caching)**   | Design patterns for cache layers (e.g., Redis, CDN).                          | For reducing database/network load.              |
| **[Auto-Scaling](pattern_autoscaling)** | Dynamically adjust resources based on load.                                   | For compute/network optimizations.              |
| **[Query Rewriting](pattern_rewriting)** | Transform queries for performance (e.g., join elimination).                   | When SQL queries are inefficient.                |
| **[Feature Flags](pattern_feature_flags)** | Gradually roll out optimizations to a subset of users.                       | For safe A/B testing of changes.                 |

---
## **8. Best Practices**
1. **Start Small:**
   - Optimize one bottleneck at a time to avoid cascade failures.
2. **Document Changes:**
   - Track optimizations in the schema (e.g., `optimization.entity` table).
3. **Set Baselines:**
   - Always measure pre- and post-optimization metrics.
4. **Monitor Long-Term:**
   - Revisit optimizations every 3–6 months (e.g., due to schema changes).
5. **Automate Where Possible:**
   - Use tools like **Terraform** for infrastructure optimizations or **Flyway** for DB migrations.
6. **Consider trade-offs:**
   - Example: Adding an index improves query speed but increases write latency.

---
## **9. Tools & Integrations**
| **Category**       | **Tools**                                                                 |
|--------------------|--------------------------------------------------------------------------|
| **Database**       | pgAdmin, MySQL Workbench, Datadog DBI, CloudWatch RDS Insights             |
| **Compute**        | Prometheus + Grafana, kubectl (Kubernetes), AWS Cost Explorer             |
| **Network**        | Wireshark, NGINX Access Logs, Cloudflare Analytics                        |
| **Application**    | OpenTelemetry, Jaeger, Sentry                                            |
| **Automation**     | GitHub Actions, Jenkins, Terraform, Ansible                               |

---
## **10. Example Workflow**
1. **Discover:** Identify slow `SELECT * FROM orders` queries in `EXPLAIN ANALYZE`.
2. **Configure:** Add index `idx_orders_user_id` and refactor query to `SELECT id, amount`.
3. **Validate:** Run load test with Locust; confirm latency drops from 400ms → 120ms.
4. **Automate:** Add index via CI/CD (e.g., Flyway migration) and set up Prometheus alert.
5. **Document:** Log optimization in `optimization.entity` with status `validated`.