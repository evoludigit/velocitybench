# **[Pattern] Performance Troubleshooting Reference Guide**

---

## **Overview**
Performance Troubleshooting is a structured **multi-step debugging pattern** designed to identify and resolve inefficiencies in applications, databases, infrastructure, or systems. This pattern provides a **methodical process** to measure, analyze, and optimize performance bottlenecks using tools, metrics, and best practices. It applies to **high-latency issues, resource starvation, or suboptimal configurations** in microservices, monoliths, cloud-native workloads, or legacy systems.

Key objectives:
- **Isolate** performance degradation to specific layers (e.g., CPU, memory, I/O, network).
- **Quantify** bottlenecks using metrics (e.g., response time, throughput, error rates).
- **Propose** remediation strategies (e.g., code tuning, hardware scaling, or architectural changes).
- **Validate** fixes with controlled experiments.

This guide covers **concepts, schematic workflows, common tools, and actionable steps** to apply the pattern effectively.

---

## **Key Concepts & Implementation Details**

### **1. Performance Bottleneck Layers**
Performance issues typically arise in one or more of these layers:

| **Layer**          | **Common Metrics**                          | **Tools/Techniques**                          | **Example Issues**                          |
|--------------------|--------------------------------------------|-----------------------------------------------|--------------------------------------------|
| **Application Code** | CPU%, Memory usage, GC pauses, Thread pool saturation | Profiler (YourKit, JProfiler), APM (New Relic, Datadog) | High GC overhead, inefficient loops, blocking I/O |
| **Database**        | Query execution time, lock contention, slow joins | EXPLAIN plans, slow query logs, APM DB monitoring | Unindexed queries, N+1 problem, connection leaks |
| **Network**         | Latency (RTT), Throughput, Packet loss      | `ping`, `traceroute`, Wireshark, Load testing (k6, JMeter) | High TCP retries, DNS resolution delays |
| **Storage (Disk)**  | I/O ops/sec, Latency (SSD vs HDD), Cache hit ratio | `iostat`, `vmstat`, `dstat`, CloudWatch Metrics | Full table scans, fragmented disks, slow storage backend |
| **Memory**          | Heap usage, Swapping, Leaks                | `top`, `free`, Heap dump analysis (Eclipse MAT) | OOM crashes, excessive string duplication |
| **Hardware**        | CPU cores, RAM, GPU utilization           | `htop`, `nmon`, Cloud provider metrics       | CPU throttling, insufficient vCPUs |
| **Load Balancer/Proxy** | Request rate, Error 5xx, Timeout rates     | ELB logs, Nginx/Apache metrics, APM            | LB starvation, misconfigured rate limiting |
| **Container/Orchestration** | Pod restarts, CPU throttling, evictions | Kubernetes metrics (Prometheus), cAdvisor | Noisy neighbor problem, insufficient limits |

---

### **2. Performance Troubleshooting Workflow**
Use this **step-by-step schema** to diagnose bottlenecks systematically:

#### **Schema Reference**
| **Step**       | **Action**                                                                 | **Output**                                                                 | **Tools/Queries**                                                                 |
|----------------|---------------------------------------------------------------------------|---------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| **1. Observe** | Collect baseline metrics (before/after changes).                          | Metrics dashboard (Prometheus, Grafana), APM traces.                     | `prometheus query`, `kubectl top pods`, `New Relic APM` dashboard.               |
| **2. Isolate** | Narrow down to a **suspect layer** (e.g., high CPU in DB or slow API calls). | Suspect components (e.g., `/api/v1/search` taking 2s avg).               | APM traces, distributed tracing (Jaeger, OpenTelemetry).                          |
| **3. Drill Down** | Dive deeper into the suspect layer (e.g., slow DB query).                  | Root cause (e.g., missing index on `products.category_id`).              | `EXPLAIN ANALYZE`, slow query logs, CPU profiling.                                |
| **4. Hypothesize** | Formulate **testable hypotheses** (e.g., "Query X is slow due to lack of index"). | Hypothesis statement + expected impact.                                  | Reproduce issue with synthetic load (Locust, k6).                                |
| **5. Validate** | Test changes in a **staging environment**.                                 | Before/after metrics comparison.                                           | A/B testing, canary deployments, feature flags.                                   |
| **6. Deploy**   | Apply fix to production with **rollout monitoring**.                      | Zero downtime, automated rollback if metrics degrade.                     | Feature flags, blue-green deployment.                                           |
| **7. Review**   | Document lessons learned + performance budget.                            | Runbook, SLOs, post-mortem template.                                        | Slack/Confluence notes, SRE playbooks.                                            |

---

## **Query Examples**
### **1. Database Bottleneck Analysis**
**Problem:** Slow `SELECT * FROM orders WHERE customer_id = ?` (avg 1.2s).

#### **Step 1: Check Query Plan**
```sql
-- PostgreSQL
EXPLAIN ANALYZE SELECT * FROM orders WHERE customer_id = 12345;
```
**Expected Output:**
```
Seq Scan on orders  (cost=0.15..8.17 rows=1 width=80) (actual time=1234.56..1234.56 rows=1 loops=1)
```
**→** Full table scan → **Add index:**
```sql
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
```

#### **Step 2: Verify Fix**
```sql
EXPLAIN ANALYZE SELECT * FROM orders WHERE customer_id = 12345;
```
**Expected Output:**
```
Index Scan using idx_orders_customer_id on orders  (cost=0.15..8.17 rows=1 width=80) (actual time=0.50..0.50 rows=1 loops=1)
```

---

### **2. Application-Level CPU Profiling**
**Problem:** High CPU usage in a Java application (90% utilization).

#### **Step 1: Use JStack to Identify Threads**
```bash
jstack <pid> | grep "native"  # Look for blocked threads
```
#### **Step 2: Profile with YourKit**
1. Attach YourKit profiler to the process.
2. Run a load test (`ab -n 1000 -c 50 http://localhost/api`).
3. Analyze **CPU profiles** for slow methods.

**Example Output:**
```
Method Name               | Time (%) | Calls
--------------------------|----------|-------
com.example.service.OrderService.findById | 60%     | 500
```
**→** Optimize `OrderService.findById` (e.g., cache results).

---

### **3. Network Latency Investigation**
**Problem:** High latency for `/api/users` (avg 800ms).

#### **Step 1: Use `traceroute`**
```bash
traceroute api.example.com
```
**Expected Output:**
```
1  * * *
2  api.example.com (10.0.0.1)  400ms
```
**→** Latency spike at step 2 → Investigate **CDN/LB** or **DNS propagation**.

#### **Step 2: Use `curl -v` for HTTP Inspection**
```bash
curl -v -o /dev/null http://api.example.com/users
```
**Look for:**
- `> GET /users HTTP/1.1` → `HTTP/1.1 200 OK` (total time)
- Slowest hop (e.g., 500ms DNS, 300ms TLS).

#### **Step 3: Load Test with k6**
```javascript
// script.js
import http from 'k6/http';

export default function () {
  http.get('http://api.example.com/users');
}
```
Run with:
```bash
k6 run --vus 100 --duration 30s script.js
```
**Expected Output:**
```
Duration: 30s
Requests: 3000
Avg RTT: 850ms (should reduce to <500ms after fix)
```

---

### **4. Memory Leak Detection**
**Problem:** Java app crashes with `OutOfMemoryError` after 48h.

#### **Step 1: Generate Heap Dump**
```bash
jmap -dump:format=b,file=heap.hprof <pid>
```
#### **Step 2: Analyze with Eclipse MAT**
1. Open `heap.hprof` in **Eclipse MAT**.
2. Navigate to **Dominator Tree** → Large objects (e.g., `"java.util.ArrayList"`).
3. **Suspicious Patterns:**
   - Unclosed streams (e.g., `java.io.FileInputStream`).
   - Cached data not invalidated (e.g., `ConcurrentHashMap` growth).

**Fix Example:**
```java
// Before (leak)
public class Cache {
  private static Map<String, User> cache = new HashMap<>();
}

// After (fixed)
public class Cache {
  private static Map<String, User> cache = new WeakHashMap<>();
}
```

---

## **Related Patterns**
| **Pattern**                     | **Purpose**                                                                 | **When to Use**                                                                 |
|----------------------------------|-----------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **[Observability]**               | Design systems for **metrics, logs, traces**.                               | When building **new services** or migrating to cloud.                           |
| **[Load Testing]**                | Simulate traffic to **validate performance under load**.                    | Before **production deployments** or major feature releases.                     |
| **[Caching Strategies]**          | Reduce database/API calls with **in-memory caching**.                       | When **slow queries** or **high read loads** are identified.                     |
| **[Asynchronous Processing]**     | Offload work to **message queues (Kafka, SQS)**.                          | When **long-running tasks** block HTTP responses.                                |
| **[Auto-Scaling]**                | Dynamically adjust **compute resources** based on load.                    | For **spiky workloads** (e.g., e-commerce during Black Friday).                  |
| **[Database Sharding]**           | Split **database load** across multiple instances.                          | When **single DB becomes a bottleneck** (e.g., >10k RPS).                       |
| **[Retry & Circuit Breakers]**    | Handle **failure gracefully** with retries and fallback.                    | For **external API dependencies** with high failure rates.                      |

---

## **Best Practices**
1. **Start with Metrics:**
   - Use **Prometheus/Grafana** for real-time dashboards.
   - Set **SLOs (Service Level Objectives)** (e.g., "95% of API calls <500ms").

2. **Reproduce Issues Locally:**
   - Use **Docker Compose** to mimic production environments.
   - Example:
     ```yaml
     # docker-compose.yml
     services:
       db:
         image: postgres
         environment:
           POSTGRES_PASSWORD: example
       app:
         image: my-app
         depends_on: [db]
         environment:
           DB_URL: jdbc:postgresql://db:5432/mydb
     ```

3. **Isolate Changes:**
   - Test fixes in **staging first** (use **feature flags**).
   - Example (Java):
     ```java
     if (System.getenv("FEATURE_TURBO_MODE") != null) {
       // Optimized code path
     } else {
       // Original code path
     }
     ```

4. **Document Everything:**
   - Keep a **runbook** for recurring issues (e.g., "How to fix slow login API").
   - Example template:
     ```
     [Issue] High latency in /login (2023-10-01)
     - Root Cause: Missing index on `users.email`.
     - Fix: Run `CREATE INDEX idx_users_email ON users(email)`.
     - Impact: Reduced latency from 800ms → 50ms.
     ```

5. **Automate Alerting:**
   - Set up **alerts** for:
     - `http_request_duration > 1s` (Prometheus alert rule).
     - `db.query_time > 2s` (CloudWatch alarm).
   - Example Prometheus rule:
     ```yaml
     - alert: HighApiLatency
       expr: histogram_quantile(0.95, sum(rate(http_request_duration_bucket[5m])) by (le, route)) > 1000
       for: 5m
       labels:
         severity: warning
       annotations:
         summary: "High latency on {{ $labels.route }}" (95th percentile {{ $value }}ms)
     ```

6. **Plan for Scale Early:**
   - **Database:** Use **read replicas** for read-heavy workloads.
   - **App:** Implement **circuit breakers** (e.g., Resilience4j).
   - **Storage:** Move to **SSDs** or **distributed storage** (e.g., S3, Ceph).

---

## **Common Pitfalls**
| **Pitfall**                          | **Solution**                                                                 |
|---------------------------------------|------------------------------------------------------------------------------|
| **Blindly optimizing without data**   | Always **measure first** (use profiling tools).                             |
| **Ignoring the "tail" (99th percentile)** | Focus on **P99 latency**, not just averages.                               |
| **Over-tuning for edge cases**       | Balance **performance** with **code readability**.                          |
| **Not testing in production-like env** | Use **staging with identical infra** (e.g., same DB version, OS).          |
| **Rolling back too late**             | Implement **canary releases** and **automated rollback** on metric degradation. |
| **Forgetting cold starts**            | Pre-warm caches or use **serverless optimizations** (e.g., Provisioned Concurrency). |

---
## **Further Reading**
- **Books:**
  - *Site Reliability Engineering* (Google SRE Book) – [Link](https://sre.google/sre-book/)
  - *Production-Ready Microservices* – Chris Richardson
- **Tools:**
  - [Prometheus Documentation](https://prometheus.io/docs/introduction/overview/)
  - [OpenTelemetry Guide](https://opentelemetry.io/docs/)
  - [Kubernetes Performance Tuning](https://kubernetes.io/docs/tasks/debug-application-cluster/debugging-performance/)
- **Talks:**
  - [How Google Scales to 10^8 QPS](https://www.youtube.com/watch?v=wFIka9XQnwU) (Google I/O 2016)

---
**End of Guide.** For feedback or contributions, open an issue in the [documentation repo](LINK).