# **[Pattern] Reference Guide: Throughput Troubleshooting**

---

## **Overview**
This reference provides a structured approach to diagnosing and optimizing throughput bottlenecks in systems. Throughput refers to the rate at which a system processes requests, transactions, or data. Poor throughput can degrade performance, increase latency, and impact user experience. This pattern guides troubleshooting processes based on system architecture layers (e.g., application, database, network) and common failure points (e.g., resource contention, inefficient algorithms, or misconfigurations).

Key steps include:
- **Identifying** throughput constraints (e.g., CPU, I/O, memory).
- **Measuring** baseline and degraded performance metrics.
- **Analyzing** logs, traces, and diagnostic tools.
- **Iterating** through fixes (e.g., scaling, caching, or code optimization).
- **Validating** resolution effectiveness.

This guide assumes familiarity with basic system monitoring tools (e.g., Prometheus, New Relic) and logging frameworks (e.g., ELK, OpenTelemetry).

---

## **Schema Reference**
Below are key attributes and metrics for throughput troubleshooting, organized by system layer.

| **Category**          | **Attribute**               | **Description**                                                                 | **Tools/Metrics**                                                                 |
|-----------------------|-----------------------------|---------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **System Overview**   | Total Requests (RPS)        | Rate of requests processed per second.                                          | Prometheus (`requests_total`), APM tools.                                         |
|                       | Latency (P99/P95)           | 99th/95th percentile response times.                                            | APM tools (e.g., Datadog, New Relic), APM traces.                                 |
|                       | Error Rate                  | Percentage of failed requests.                                                   | Log aggregation (e.g., ELK, Splunk), APM tools.                                  |
| **Application Layer** | Concurrent Requests         | Number of active requests handled simultaneously.                              | Thread pools, async workers (e.g., Java `ThreadPoolExecutor`, Node.js `worker_threads`). |
|                       | Code Path Hotspots          | Slowest functions/methods in call stacks.                                       | Profilers (e.g., YourKit, JFR for Java), APM traces.                              |
|                       | Dependency Latency          | Time spent waiting for external calls (e.g., APIs, databases).                  | APM traces, database query logs.                                                  |
| **Database Layer**    | Query Execution Time        | Average/slowest query durations.                                                 | Database slow query logs (e.g., PostgreSQL `slow_query_log`), APM tools.         |
|                       | Index Utilization           | How effectively indexes are used in queries.                                    | Explain plans (e.g., `EXPLAIN ANALYZE`), database tools (e.g., pgMustard).        |
|                       | Connection Pool Size        | Active vs. max connections (contention risk).                                    | Database metrics (e.g., `pg_stat_activity` for PostgreSQL).                        |
| **Network Layer**     | Bandwidth Utilization       | Data transfer rates (in/out).                                                   | Network tools (`iftop`, `nload`), APM tools.                                      |
|                       | Packet Loss/Drops           | Network reliability metrics.                                                     | `ping`, `mtr`, `tcpdump`.                                                         |
|                       | Load Balancer Status        | Health checks, request distribution.                                             | Load balancer logs (e.g., Nginx, HAProxy), APM tools.                             |
| **Infrastructure**    | CPU/Memory Pressure         | Resource saturation (e.g., >90% CPU).                                            | OS metrics (`top`, `vmstat`), Prometheus (`node_exporter`).                       |
|                       | Disk I/O Latency            | Read/write delays (e.g., HDD vs. SSD).                                          | `iostat`, Prometheus (`node_disk_io_time`).                                       |
|                       | Container/VM Overhead       | Resource contention in orchestrated environments (e.g., Kubernetes).            | Kubernetes metrics (`kube-state-metrics`), Prometheus.                             |

---

## **Query Examples**
Below are SQL-like queries and command-line examples for diagnosing throughput issues. Replace placeholders (`<table>`) with actual schema/table names.

---

### **1. Database Query Hotspots**
**Problem:** Slow queries are degrading throughput.
**Tool:** PostgreSQL `pg_stat_statements`.

```sql
-- Top 10 slowest queries (by execution time)
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;

-- Queries with high CPU time (potential optimization candidates)
SELECT query, total_time, total_time - sum(exec_time) AS "wait_time"
FROM (
    SELECT query, total_time,
           SUM(exec_time) AS sum_exec_time,
           COUNT(*) AS calls
    FROM pg_stat_statements
    GROUP BY query
) stats
WHERE total_time > 1000  -- >1 second
ORDER BY total_time DESC;
```

**Tool:** MySQL `performance_schema`.

```sql
-- Slow queries exceeding 1 second
SELECT
    event_name,
    count_star AS "count",
    SUM(timer_wait / 1000000000) AS "wait_time_sec"
FROM performance_schema.events_statements_summary_by_digest
WHERE timer_wait > 1000000000  -- >1 second
GROUP BY event_name
ORDER BY wait_time_sec DESC;
```

---

### **2. Application-Level Latency**
**Problem:** High latency in application layers.
**Tool:** APM Traces (e.g., New Relic).

```sql
-- Top 5 slowest transactions (New Relic SQL)
FROM Transaction
WHERE duration > 1000  -- >1 second
ORDER BY duration DESC
LIMIT 5;
```

**Tool:** Prometheus Metrics.

```promql
# Latency percentiles (P99)
histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))
```

**Command Line (Go PProf):**
```bash
# Generate a CPU profile during peak load
go tool pprof http://localhost:6060/debug/pprof/profile
# Analyze hotspots
top -seconds 2  # Top 2 seconds of CPU time
```

---

### **3. Network Bottlenecks**
**Problem:** High packet loss or bandwidth saturation.
**Tool:** `iftop` (real-time bandwidth monitoring).

```bash
sudo iftop -i eth0 -n  # Monitor interface `eth0`
```

**Tool:** `netstat` (connection states).

```bash
# List active TCP connections (potential bottlenecks)
netstat -tan | awk '{print $5}' | cut -d: -f1 | sort | uniq -c | sort -nr
```

**Tool:** `mtr` (network latency + packet loss).

```bash
mtr --report google.com  # Test latency to a target
```

---

### **4. Resource Contention**
**Problem:** CPU/memory saturation.
**Tool:** `top` (real-time process monitoring).

```bash
# Sort by CPU usage
top -o %CPU
```

**Tool:** `vmstat` (system-wide metrics).

```bash
# Check CPU, memory, and I/O (every 2s, 5 iterations)
vmstat 2 5
```

**Tool:`iostat` (disk I/O).

```bash
# Monitor disk utilization
iostat -x 1  # Update every 1 second for 1 minute
```

---

### **5. Kubernetes-Specific Issues**
**Problem:** Pods or nodes under resource pressure.
**Tool:** `kubectl top`.

```bash
# Check pod resource usage
kubectl top pods --all-namespaces

# Check node resource allocation
kubectl top nodes
```

**Tool:** Prometheus + Grafana Dashboard.
Query for pod CPU throttling:
```promql
kube_pod_container_resource_limits{resource="cpu", namespace="<namespace>"}
```

---

## **Step-by-Step Troubleshooting Workflow**
Use this iterative process to diagnose throughput issues:

### **Step 1: Baseline Measurement**
- **Collect metrics** for normal operation (e.g., RPS, latency, error rates).
- **Define SLOs** (e.g., 95th percentile latency < 500ms).
- **Tools:** Prometheus, APM, or custom logging.

### **Step 2: Identify Degradation**
- Compare metrics during degradation vs. baseline.
- Look for spikes in:
  - Latency (e.g., P99 > 2x baseline).
  - Error rates (e.g., >1% failures).
  - Resource usage (e.g., CPU > 80%).

### **Step 3: Layered Analysis**
| **Layer**       | **Questions to Ask**                                                                 | **Tools**                                  |
|------------------|------------------------------------------------------------------------------------|--------------------------------------------|
| Application      | Are there unoptimized loops or external calls?                                     | Profilers, APM traces                      |
| Database         | Are queries inefficient or missing indexes?                                         | `EXPLAIN ANALYZE`, slow query logs          |
| Network          | Is bandwidth saturated or latency high?                                             | `iftop`, `mtr`, load balancer logs          |
| Infrastructure   | Are CPU/memory/disk under pressure?                                                  | `top`, `vmstat`, `iostat`                   |
| Orchestration    | Are pods over-subscribed or throttled?                                              | `kubectl top`, Prometheus                   |

### **Step 4: Hypothesis Testing**
- **Example Hypothesis:** *"Database queries are slow due to missing indexes."*
  - **Test:** Add missing indexes and re-run queries.
  - **Validate:** Check if `total_time` in `pg_stat_statements` decreases.

- **Example Hypothesis:** *"Application threads are starved due to high concurrency."*
  - **Test:** Increase thread pool size or use async I/O.
  - **Validate:** Monitor `ThreadPoolExecutor` metrics (Java) or worker queue lengths.

### **Step 5: Iterate and Optimize**
- **Short-term fixes:**
  - Scale horizontally (add nodes/pods).
  - Cache frequent queries (e.g., Redis).
  - Optimize slow queries (e.g., denormalize data).
- **Long-term fixes:**
  - Refactor code (e.g., reduce blocking calls).
  - Right-size resources (e.g., adjust CPU/memory limits).
  - Implement auto-scaling (e.g., Kubernetes HPA).

### **Step 6: Validate Resolution**
- Re-run metrics to confirm improvements.
- Monitor for regression (e.g., new slow queries after caching).
- Document fixes and add alerts for similar conditions.

---

## **Related Patterns**
Consult these patterns for deeper context or complementary solutions:

1. ****[Latency Optimization]** *(Guide to reducing response times at each system layer.)*
   - Focus: Code-level optimizations, caching strategies, and database tuning.
   - **Use case:** When throughput is constrained by slow operations.

2. ****[Resource Scaling]** *(Horizontal vs. vertical scaling strategies.)*
   - Focus: Adding nodes, adjusting cloud auto-scaling, or optimizing resource allocation.
   - **Use case:** When baseline metrics show resource saturation (e.g., CPU > 90%).

3. ****[Circuit Breaker Pattern]** *(Prevent cascading failures during degraded throughput.)*
   - Focus: Implementing fallback mechanisms (e.g., Hystrix, Resilience4j).
   - **Use case:** When downstream services are unreliable, worsening throughput.

4. ****[Observability Stack]** *(Centralized logging, metrics, and tracing.)*
   - Focus: Tools like Prometheus, ELK, and OpenTelemetry for holistic monitoring.
   - **Use case:** When manual metric collection is infeasible at scale.

5. ****[Database Sharding]** *(Horizontal partitioning for high-write workloads.)*
   - Focus: Distributing database load across multiple instances.
   - **Use case:** When a single database cannot handle write-throughput.

6. ****[Rate Limiting]** *(Preventing overload during spikes in traffic.)*
   - Focus: Enforcing request quotas (e.g., Redis rate limiting).
   - **Use case:** When sudden traffic surges degrade performance.

---

## **Common Pitfalls**
- **Ignoring the 80/20 Rule:** 20% of queries or dependencies often cause 80% of latency. Focus on hotspots.
- **Over-Optimizing Prematurely:** Profile before assuming a bottleneck (e.g., don’t tune code until profiling shows it’s slow).
- **Neglecting External Dependencies:** Slow APIs or databases are often the culprits, not the application code.
- **Scaling Without Monitoring:** Adding resources without measuring impact can lead to waste or instability.
- **Silent Failures:** Implement health checks and alerts for degraded throughput (e.g., Prometheus alerts for P99 latency spikes).

---

## **Example Diagnoses**
### **Case 1: Sudden Spikes in Latency**
**Symptoms:**
- P99 latency jumps from 100ms to 1.2s.
- Database `pg_stat_statements` shows a new slow query:
  ```sql
  SELECT * FROM large_table WHERE created_at > NOW() - INTERVAL '1 hour';
  ```
**Root Cause:** Missing index on `created_at` + full table scan.
**Fix:** Add index:
```sql
CREATE INDEX idx_large_table_created_at ON large_table(created_at);
```

### **Case 2: CPU Throttling in Kubernetes**
**Symptoms:**
- Pod CPU usage at 100% for 5+ minutes.
- `kubectl top pod` shows `100m/1` (requested/limit CPU).
**Root Cause:** CPU limit too low for workload spike.
**Fix:** Adjust resource limits:
```yaml
# In deployment.yaml
resources:
  limits:
    cpu: "500m"  # Increased from 100m
```

---

## **Further Reading**
- **Books:**
  - *Site Reliability Engineering* (Google SRE) – Chapter on Performance.
  - *Production-Ready Microservices* (Chris Richardson) – Observability and scaling.
- **Tools:**
  - [Prometheus Documentation](https://prometheus.io/docs/introduction/overview/)
  - [New Relic APM](https://docs.newrelic.com/docs/apm/)
  - [PostgreSQL `pg_stat_statements`](https://www.postgresql.org/docs/current/pgstatstatements.html)
- **Talks:**
  - [How to Fix Slow Queries](https://www.youtube.com/watch?v=0oED9LYPHdo) (Citus Data).
  - [Distributed Tracing for Observability](https://www.youtube.com/watch?v=wA5W-6pXZ4o) (OpenTelemetry).