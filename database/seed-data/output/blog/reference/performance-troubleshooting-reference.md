# **[Pattern] Performance Troubleshooting – Reference Guide**

---

## **1. Overview**
Performance troubleshooting is a structured approach to identifying, diagnosing, and resolving bottlenecks in application, system, or infrastructure performance. This pattern provides a systematic methodology to:
- **Measure** baseline and real-time performance metrics.
- **Isolate** root causes (e.g., CPU overload, I/O saturation, latency spikes).
- **Optimize** configurations, code, or dependencies.
- **Validate** fixes using repeatable testing.

Unlike reactive debugging, performance troubleshooting focuses on **proactive analysis**, leveraging logging, monitoring, and profiling tools. It applies across domains: web apps, databases, microservices, and cloud workloads.

---

## **2. Key Concepts & Implementation Details**

### **2.1. Performance Metrics**
| **Category**       | **Metrics**                          | **Tools** Example                     | **Target Threshold**                     |
|--------------------|--------------------------------------|---------------------------------------|------------------------------------------|
| **System**         | CPU %, Memory Usage, Disk I/O       | `top`, `vmstat`, `iostat`            | CPU < 80%, Mem < 90%, Disk I/O < 1000 ops/s |
| **Network**        | Latency (P99), Throughput, Packets/sec | `ping`, `netdata`, `Wireshark`       | Latency < 200ms, Throughput > 90% baseline |
| **Application**    | Response Time (P99), Error Rate     | APM (AppDynamics, New Relic), APM     | P99 RT < 500ms, Error Rate < 1%          |
| **Database**       | Query Execution Time, Lock Contention | `EXPLAIN ANALYZE`, `pg_stat`, `Slow Query Log` | Avg QRT < 100ms, Lock Waits < 0.5%      |

**Note:** Thresholds depend on SLAs (e.g., 99th percentile latency for user-facing apps).

---

### **2.2. Troubleshooting Workflow**

#### **Phase 1: Observation & Hypothesis**
1. **Symptoms**: Describe observed issues (e.g., "API responses slow at 3 PM").
2. **Data Collection**:
   - **Logs**: Filter for errors/warnings (e.g., `grep "ERROR" /var/log/app.log | tail -n 50`).
   - **Metrics**: Correlate with tooling (e.g., Prometheus + Grafana).
   - **Profiling**: Use CPU/memory profilers (e.g., `pprof`, Java Flight Recorder).
3. **Hypotheses**: Propose root causes (e.g., "High GC pauses due to memory leaks").

#### **Phase 2: Isolation**
- **Eliminate Noise**: Rule out external factors (e.g., spikes in CDN traffic).
- **Reproduce**: Simulate conditions (e.g., load test with `locust` or `k6`).
- **Isolate Components**: Check dependencies (e.g., database queries, external APIs).

**Example Isolation Steps**:
```bash
# Check DB query performance
EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = 123;

# Monitor network latency to a backend
tcpdump -i eth0 host backend-api -c 100 | wc -l
```

#### **Phase 3: Optimization**
- **System-Level**:
  - Tune OS settings (e.g., `vm.swappiness=10` in `/etc/sysctl.conf`).
  - Optimize storage (e.g., SSDs for I/O-bound workloads).
- **Application-Level**:
  - Code refactoring (e.g., avoid N+1 queries).
  - Caching (Redis, CDN).
- **Infrastructure-Level**:
  - Scale horizontally (add replicas) or vertically (upgrade nodes).

#### **Phase 4: Validation**
- **Baseline Comparison**: Compare metrics before/after fixes.
- **A/B Testing**: Deploy changes to a subset of users.
- **Automated Alerts**: Set up alerts for regression detection (e.g., Prometheus alerts).

---

## **3. Schema Reference**

### **3.1. Performance Incident Template**
| **Field**               | **Type**      | **Description**                                                                 | **Example**                          |
|-------------------------|---------------|---------------------------------------------------------------------------------|--------------------------------------|
| `incident_id`           | String        | Unique identifier for the issue.                                                | `PERF-2023-045`                     |
| `timestamp`             | Datetime      | When the issue was reported/observed.                                           | `2023-10-15T14:30:00Z`              |
| `component`             | String        | Affected system (e.g., `backend-service`, `database`).                          | `payment-service`                    |
| `severity`              | Enum          | Critical/High/Medium/Low.                                                      | `High`                               |
| `metrics_affected`      | Array         | Affected metrics (from Schema 2.1).                                            | `["latency_p99", "cpu_usage"]`       |
| `root_cause`            | String        | Hypothesis or confirmed cause.                                                  | `Blocking queries due to missing index`|
| `resolution`            | String        | Steps taken to fix (e.g., "Added index on `user_id`").                          | `"Enabled Redis caching for orders API"`|
| `validation_method`     | String        | How fix was verified (e.g., "Load test with 10K RPS").                           | `" Compared P99 latency pre/post-fix"`|
| `status`                | String        | `Open`, `In Progress`, `Resolved`, `Closed`.                                  | `Resolved`                           |
| `affected_users`        | Integer       | Number of end users impacted.                                                   | `5000`                               |

---

### **3.2. Query Performance Report Schema**
| **Field**               | **Type**      | **Description**                                                                 |
|-------------------------|---------------|---------------------------------------------------------------------------------|
| `query_id`              | String        | Unique query identifier (e.g., transaction ID).                                |
| `sql`                   | String        | Raw SQL query.                                                                  |
| `execution_time_ms`     | Float         | Time taken (milliseconds).                                                       |
| `rows_processed`        | Integer       | Number of rows fetched.                                                          |
| `lock_contention`       | Float         | % of time spent waiting for locks.                                              |
| `cache_hit_ratio`       | Float         | % of queries served from cache.                                                 |
| `database_version`      | String        | DBMS version (e.g., `PostgreSQL 15.3`).                                         |
| `environment`           | String        | `dev`, `staging`, `prod`.                                                       |

---
## **4. Query Examples**

### **4.1. Database Query Analysis**
**Problem**: Slow `SELECT * FROM users WHERE email = ?`.
**Tools**: PostgreSQL `EXPLAIN ANALYZE`.

```sql
-- Check query plan
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'user@example.com';

-- Sample output (identify bottlenecks like sequential scans)
QUERY PLAN
-------------------------------------------------------
Seq Scan on users  (cost=0.00..1.04 rows=1 width=72) (actual time=0.015..0.015 rows=1 loops=1)
  Filter: (email = 'user@example.com'::text)
  Rows Removed by Filter: 10000
```
**Fix**: Add a composite index:
```sql
CREATE INDEX idx_users_email ON users(email);
```

---

### **4.2. Network Latency Diagnosis**
**Problem**: High latency to `api.external.com`.
**Tools**: `mtr` (matrix ping) or `ping + tcpdump`.

```bash
# Install mtr
sudo apt install mtr

# Trace route + latency
mtr api.external.com

# Check packet loss/delay
api.external.com     100.0%  |    --  1.2 ms    0.8 ms    1.1 ms
                         0.0%  |    --  2.5 ms    2.3 ms    2.4 ms
```
**Fix**: Escalate to network team if TTL hops > 15 or packet loss > 1%.

---

### **4.3. CPU Profiling (Python Example)**
**Problem**: Slow Python script (`app.py`).
**Tools**: `cProfile`.

```python
# Run with profiling
python -m cProfile -s cumulative app.py
```
**Output**:
```
         1200 function calls in 4.234 seconds

   Ordered by: cumulative time

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
        1    0.000    0.000    4.234    4.234 app.py:5(main)
        1    0.000    0.000    4.234    4.234 app.py:10(_process_data)
   1200    0.000    0.000    4.233    0.003 {built-in method builtins.range}
```
**Fix**: Optimize `_process_data` (e.g., use `pandas` for vectorized operations).

---

## **5. Related Patterns**
| **Pattern**                     | **Description**                                                                 | **When to Use**                                  |
|----------------------------------|---------------------------------------------------------------------------------|---------------------------------------------------|
| **[Observability](Pattern)**     | Centralized logging, metrics, and tracing for visibility.                       | When you need real-time monitoring.                |
| **[Load Testing](Pattern)**      | Simulate production traffic to find bottlenecks.                                | Before deployments or under heavy load.           |
| **[Caching](Pattern)**           | Reduce database/API latency with in-memory stores.                              | For read-heavy or repetitive queries.              |
| **[Auto-Scaling](Pattern)**      | Dynamically adjust resources based on demand.                                   | For unpredictable workloads.                     |
| **[Database Indexing](Pattern)** | Optimize query performance with indexes.                                       | When SQL queries are slow due to full table scans. |

---

## **6. Best Practices**
1. **Instrument Early**: Add metrics/logging from development.
2. **Define SLIs/SLOs**: Set clear performance targets (e.g., "99% of requests < 300ms").
3. **Automate Alerts**: Use tools like Prometheus + Alertmanager for proactive detection.
4. **Profile Regularly**: Run performance tests post-deployment (e.g., "Smoke Tests" with synthetic traffic).
5. **Document Fixes**: Update runbooks with reproducibility steps (e.g., "Fix: Added index `idx_user_email`").
6. **Isolate Environments**: Ensure staging mirrors production (e.g., same DB version, OS).

---
## **7. Tools Cheat Sheet**
| **Category**       | **Tool**               | **Use Case**                                  | **Example Command**                     |
|--------------------|------------------------|-----------------------------------------------|------------------------------------------|
| **Logging**        | ELK Stack (Elasticsearch, Logstash, Kibana) | Centralized log analysis.                    | `logstash input { stdin { codec => plain { charset => "UTF-8" } } }` |
| **Metrics**        | Prometheus + Grafana   | Time-series monitoring.                       | `prometheus --web.listen-address=:9090`   |
| **APM**            | New Relic / Datadog    | Application performance monitoring.          | `datadog-agent service`                  |
| **Profiling**      | `pprof` (Go), JFR (Java)| CPU/memory profiling.                         | `pprof http://localhost:6060/debug/pprof` |
| **Database**       | `pgBadger` (PostgreSQL)| Query analysis/reports.                        | `pgbadger logfile.sql.gz > report.html`  |
| **Load Testing**   | Locust / k6            | Simulate traffic.                             | `locust -f locustfile.py`               |

---
## **8. Common Pitfalls**
- **Ignoring the 99th Percentile**: Focusing only on averages can hide outliers.
- **Over-Optimizing Prematurely**: Profile before refactoring (e.g., don’t optimize a rarely used function).
- **Silos**: Isolate teams (e.g., frontend vs. backend) can delay fixes.
- **False Positives**: Correlate metrics with business impact (e.g., "High CPU" but no user impact).

---
**Appendix**: Glossary of terms like **P99 Latency**, **Throughput**, **GC Pause**, **Blocking Query**.