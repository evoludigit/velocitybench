# **Debugging Performance Standards: A Troubleshooting Guide**

## **Introduction**
The **Performance Standards** pattern ensures that your system meets expected speed, latency, throughput, and resource usage benchmarks. This pattern helps identify bottlenecks, optimize critical paths, and maintain predictable performance under load.

If your system consistently fails to meet SLAs (Service Level Agreements) or exhibits degraded performance, this guide will help you diagnose and resolve common issues efficiently.

---

## **1. Symptom Checklist**
Before diving into debugging, assess the following symptoms to narrow down potential causes:

| **Symptom**                     | **Possible Cause**                          | **Verification Step** |
|---------------------------------|--------------------------------------------|-----------------------|
| Slow response times (e.g., >1s for API calls) | Database queries, I/O bottlenecks, or inefficient algorithms | Check latency metrics (e.g., Prometheus, APM tools) |
| High CPU/memory usage under load | Unoptimized code, memory leaks, or inefficient caching | Monitor via `htop`, `netdata`, or cloud provider metrics |
| Database lock contention        | Long-running transactions, missing indexes, or poor query design | Check `EXPLAIN ANALYZE`, slow query logs |
| API Gateway timeouts            | Backend service latency or connection pooling issues | Test with `curl`/`Postman` and check gateway logs |
| Caching misses (high evictions) | Over-partitioned cache or incorrect TTL settings | Review Redis/Memcached eviction logs |
| High network latency            | Underpowered load balancers, DNS issues, or slow endpoints | Use `ping`, `traceroute`, or `curl -v` |
| Database replication lag        | Unbalanced read/write workload or slow replication | Check `SHOW SLAVE STATUS` (MySQL), `pg_stat_replication` (PostgreSQL) |
| Spikes in garbage collection pauses | Java/Python heap allocations, or excessive object creation | Use `jstat`, `gc logs`, or Python profiler |

If multiple symptoms appear, prioritize the most critical (e.g., database slowness before high CPU).

---

## **2. Common Issues & Fixes**

### **2.1 Database Performance Bottlenecks**
#### **Issue: Slow Queries Due to Missing Indexes**
**Symptom:**
High query execution time (e.g., `FULL TABLE SCAN` in PostgreSQL logs).

**Fix:**
- **Add proper indexes** (e.g., for `WHERE`, `JOIN`, and `ORDER BY` clauses).
- **Optimize queries** by avoiding `SELECT *` and using `LIMIT`.

**Example (PostgreSQL):**
```sql
-- Before (slow)
SELECT * FROM users WHERE email LIKE '%@gmail.com';

-- After (indexed)
CREATE INDEX idx_users_email ON users (email);
SELECT * FROM users WHERE email LIKE 'gmail.com'; -- Uses index
```

**Debugging Steps:**
1. Run `EXPLAIN ANALYZE` to identify scans.
2. Use `pg_stat_statements` (PostgreSQL) or `perf_schema` (MySQL) to find slow queries.

---

#### **Issue: N+1 Query Problem (ORMs)**
**Symptom:**
High database load due to inefficient ORM queries (e.g., ActiveRecord, Django ORM).

**Fix:**
- **Use `includes` (ActiveRecord) or `prefetch_related` (Django) to reduce round trips.**

**Example (Django):**
```python
# Before (3 queries: 1 for Team + 2 for members)
team = Team.objects.get(id=1)
members = team.members.all()  # N+1 if accessed later

# After (1 query)
team = Team.objects.prefetch_related('members').get(id=1)
```

**Debugging Steps:**
1. Check SQL logs for repeated identical queries.
2. Use ORM tracing tools (e.g., Django Debug Toolbar, Rails Bulk).

---

### **2.2 API Gateway & Load Balancer Issues**
#### **Issue: Timeouts Due to Unoptimized Backend**
**Symptom:**
API Gateway returns `504 Gateway Timeout`.

**Fix:**
- **Increase timeout settings** in the gateway (e.g., AWS ALB/NGINX).
- **Optimize backend response times** (see database fixes above).

**Example (AWS ALB Timeout Config):**
```yaml
# ALB settings (AWS CLI or Console)
aws elbv2 modify-load-balancer-attributes \
  --load-balancer-arn Arn \
  --attributes Key=idle_timeout.timeout_seconds,Value=60
```

**Debugging Steps:**
1. **Check backend latency** with `curl -v http://backend-service`.
2. **Enable detailed logging** in the gateway (e.g., AWS Access Logs).

---

### **2.3 Caching Issues**
#### **Issue: High Cache Miss Rate**
**Symptom:**
Cache evictions (e.g., Redis `evicted_keys`) or unexpectedly slow responses.

**Fix:**
- **Adjust cache TTL** (time-to-live) based on data volatility.
- **Partition cache keys effectively** (e.g., by user session or region).

**Example (Redis with Smart TTL):**
```bash
# Set TTL based on access frequency
SET user:123 data ... PX 3600  # Expires in 1 hour
```

**Debugging Steps:**
1. Check Redis stats:
   ```bash
   redis-cli INFO stats | grep evicted_keys
   ```
2. Monitor cache hit/miss ratio (e.g., via `redis-stats-exporter`).

---

### **2.4 Memory Leaks (Java/Python)**
#### **Issue: Uncontrolled Memory Growth**
**Symptom:**
`OOM Killer` logs (Linux) or `MemoryError` (Python).

**Fix:**
- **Find and fix memory leaks** (e.g., unclosed database connections, caches).
- **Optimize data structures** (e.g., use `slots` in Python classes).

**Example (Python Memory Leak Fix):**
```python
# Before (memory leak)
class Cache:
    def __init__(self):
        self.data = {}  # Grows indefinitely

# After (bounded cache)
import functools
class BoundedCache:
    def __init__(self, max_size=1000):
        self.data = {}
        self.max_size = max_size

    def set(self, key, value):
        if len(self.data) >= self.max_size:
            self.data.pop(next(iter(self.data)))
        self.data[key] = value
```

**Debugging Steps:**
1. **Use memory profilers**:
   - Python: `tracemalloc`, `memory_profiler`
   - Java: VisualVM, YourKit
2. Check for `java.lang.OutOfMemoryError` or `Segmentation Fault` logs.

---

### **2.5 Network Latency Issues**
#### **Issue: High Round-Trip Time (RTT)**
**Symptom:**
API calls take >500ms due to network delays.

**Fix:**
- **Optimize DNS resolution** (use Cloudflare DNS).
- **Use CDN for static assets**.
- **Reduce payload size** (compress responses).

**Example (Ngix Gzip Compression):**
```nginx
gzip on;
gzip_types text/plain text/css application/json;
```

**Debugging Steps:**
1. Use `mtr` or `tracepath` to check network hops:
   ```bash
   mtr google.com
   ```
2. Test TCP connection time:
   ```bash
   telnet backend-service 8080
   ```

---

## **3. Debugging Tools & Techniques**

### **3.1 Performance Monitoring Tools**
| **Tool**               | **Purpose**                          | **Example Use Case**                     |
|------------------------|--------------------------------------|------------------------------------------|
| **Prometheus + Grafana** | Metrics collection & visualization    | Track HTTP request latency over time     |
| **New Relic/Datadog**   | APM (Application Performance Monitoring) | Identify slow database queries          |
| **Redis Insight**      | Redis performance analysis            | Check cache hit ratio                   |
| **Blackfire**          | PHP profiler                         | Find slow PHP functions                  |
| **JVM Flight Recorder** | Java low-overhead profiling         | Analyze garbage collection pauses        |

**Example Prometheus Query (Latency):**
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

---

### **3.2 Profiling Techniques**
- **CPU Profiling** (e.g., `perf`, `pprof`):
  ```bash
  go tool pprof http://localhost:6060/debug/pprof/profile
  ```
- **Database Profiler** (Slow Query Log):
  ```sql
  -- Enable MySQL slow query log
  SET GLOBAL slow_query_log = 'ON';
  SET GLOBAL long_query_time = 1;  -- Log queries >1s
  ```
- **Logging & Structured Tracing**:
  - Use `structured logging` (JSON) with `OpenTelemetry`.
  - Example (Python + OpenTelemetry):
    ```python
    from opentelemetry import trace
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("db_query"):
        cursor.execute("SELECT * FROM users")
    ```

---

### **3.3 Load Testing**
- **Simulate production traffic** using:
  - **Locust** (Python-based)
  - **k6** (JavaScript-based)
  - **JMeter** (Enterprise-grade)

**Example Locust Test (Python):**
```python
from locust import HttpUser, task, between

class DatabaseUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def query_users(self):
        self.client.get("/api/users")
```

**Expected Outcomes:**
- Identify **thresholds** (e.g., "System degrades at 1000 RPS").
- Find **bottlenecks** (e.g., database under load).

---

## **4. Prevention Strategies**

### **4.1 Design-Time Best Practices**
1. **Set Performance SLAs Early**
   - Define acceptable thresholds for latency, throughput, and error rates.
2. **Use Caching Aggressively**
   - Cache **read-heavy** data (e.g., user profiles, product listings).
3. **Optimize Database Schema**
   - Avoid `TEXT` fields for search; use `TSVECTOR` (PostgreSQL) instead.
   - Normalize where possible, denormalize for read-heavy workloads.
4. **Implement Circuit Breakers**
   - Use **Hystrix** (Java) or **Resilience4j** (Java/Kotlin) to fail fast.

### **4.2 Code-Level Optimizations**
- **Avoid Blocking Calls**
  - Use **asynchronous I/O** (e.g., `async/await` in Python, `CompletableFuture` in Java).
- **Batch Database Operations**
  - Replace `INSERT` loops with `INSERT ... VALUES (val1), (val2), ...`.
- **Lazy Load Data**
  - Load only necessary fields (e.g., Django’s `only()` or `exclude()`).

**Example (Batch Insert):**
```python
# Before (slow)
for user in users:
    db.insert_user(user)

# After (fast)
db.insert_users(users)  # Single batch insert
```

### **4.3 Observability & Alerting**
- **Monitor Key Metrics**:
  - **Latency Percentiles** (P99, P95)
  - **Error Rates** (5xx responses)
  - **Throughput** (RPS)
- **Set Up Alerts**:
  - Example (Prometheus Alert):
    ```yaml
    - alert: HighLatency
      expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
      for: 1m
      labels:
        severity: warning
      annotations:
        summary: "High latency detected"
    ```

### **4.4 Regular Maintenance**
- **Database Maintenance**:
  - Run `ANALYZE` (PostgreSQL) and `OPTIMIZE TABLE` (MySQL) periodically.
  - Archive old logs/data.
- **Cache Warm-Up**:
  - Pre-load cache before traffic spikes (e.g., during nightly jobs).
- **Upgrade Infrastructure**:
  - Right-size CPU/memory (e.g., move from `t2.medium` → `m5.large` if bottlenecked on CPU).

---

## **5. Step-by-Step Debugging Workflow**
1. **Reproduce the Issue**
   - Check logs, metrics, and traces under load.
2. **Isolate the Component**
   - Is it the database? API? Caching layer?
3. **Narrow Down the Bottleneck**
   - Use `traceroute`, `EXPLAIN ANALYZE`, or APM tools.
4. **Apply Fixes**
   - Optimize code, database, or infrastructure.
5. **Validate with Load Testing**
   - Confirm the fix resolves the issue (e.g., latency drops).
6. **Monitor Post-Fix**
   - Set up alerts to detect regressions.

---

## **6. Example Debugging Scenario**
**Symptom:** "API `/users` is slow under 1000 RPS."

### **Debugging Steps:**
1. **Check Metrics (Prometheus):**
   - `/users` latency spikes at ~900 RPS.
   - Database `SELECT * FROM users` takes **800ms** (vs. 50ms idle).
2. **Run `EXPLAIN ANALYZE`:**
   ```sql
   EXPLAIN ANALYZE SELECT * FROM users WHERE status = 'active';
   ```
   - Shows a **sequential scan** (no index).
3. **Add Index:**
   ```sql
   CREATE INDEX idx_users_status ON users(status);
   ```
4. **Test with Locust:**
   - Latency drops to **150ms** at 1000 RPS.
5. **Deploy Fix + Set Up Alert:**
   - Add Prometheus alert for latency > 300ms.

---

## **7. Final Checklist Before Production**
✅ **Test under load** ( Locust/k6 )
✅ **Profile critical paths** ( pprof, Blackfire )
✅ **Set up monitoring & alerts**
✅ **Document performance SLAs**
✅ **Have a rollback plan**

---
By following this guide, you can systematically diagnose and resolve performance issues while preventing future bottlenecks. **Start with monitoring, then optimize, then automate.**