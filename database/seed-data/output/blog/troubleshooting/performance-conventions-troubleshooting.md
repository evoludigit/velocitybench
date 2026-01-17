# **Debugging Performance Conventions: A Troubleshooting Guide**

## **Introduction**
Performance Conventions refer to consistent coding practices, architectural patterns, and optimization techniques that ensure predictable, scalable, and efficient system behavior. When these conventions are violated—either through misconfiguration, poor coding habits, or external factors—the system may exhibit performance degradation, resource exhaustion, or unpredictable slowdowns.

This guide provides a structured approach to diagnosing and resolving common performance-related issues tied to **Performance Conventions**.

---

## **1. Symptom Checklist**
Before diving into debugging, systematically verify these symptoms to identify potential performance bottlenecks:

### **A. High Latency or Slow Response Times**
- Endpoints respond sluggishly (e.g., >1s for a simple API call).
- Latency spikes intermittently or under load.
- **Tools to check:** APM (New Relic, Dynatrace), distributed tracing (OpenTelemetry, Jaeger), `curl`/`Postman` benchmarks.

### **B. Resource Exhaustion (CPU/Memory/Disk)**
- CPU usage spikes to 100% under load.
- Memory leaks detected (increasing heap usage over time).
- Disk I/O bottlenecks (high `iowait` or `disk latency` in `top`/`iostat`).
- **Tools to check:** `htop`, `iotop`, `vmstat`, Prometheus/Grafana, JVM GC logs.

### **C. Database-Related Slowdowns**
- Query execution times exceed thresholds (e.g., >500ms for a simple `SELECT`).
- Connection pool exhaustion (`Too many connections` errors).
- Slow JOIN operations or unoptimized queries.
- **Tools to check:** Database query logs, `EXPLAIN ANALYZE`, pgAdmin/Phantom for Postgres, MySQL `slow_query_log`.

### **D. External API/Dependency Timeouts**
- External service calls (3rd-party APIs, microservices) time out.
- Retry logic overwhelmed by cascading failures.
- **Tools to check:** Distributed tracing (Zipkin), API latency monitoring (Grafana, Datadog).

### **E. Cold Start Delays (Serverless/Faas)**
- Function/inference startup time >5s (unexpected for serverless).
- Initial request latency significantly higher than subsequent ones.
- **Tools to check:** Cloud provider metrics (AWS Lambda Insights, Azure Application Insights).

### **F. Caching Issues**
- Cache misses skyrocket under load.
- Stale data returned due to improper TTL or eviction policies.
- **Tools to check:** Redis/Memcached metrics (`keyspace hits`, `evictions`), cache hit Ratio metrics.

### **G. Concurrency & Thread Pool Starvation**
- Thread pool exhaustion (`RejectedExecutionException` in Java).
- Lock contention (`Blocked threads` in `jstack`).
- **Tools to check:** Thread dumps (`jstack <pid>`), `top -H -p <pid>`, APM thread profiling.

---

## **2. Common Issues and Fixes**

### **Issue 1: Inefficient Database Queries**
**Symptoms:**
- Slow `SELECT` queries with high execution time.
- Full table scans (`Full Table Scan` in `EXPLAIN ANALYZE`).
- Missing indexes on frequently queried columns.

**Root Causes:**
- Lack of proper indexing.
- N+1 query problem (e.g., fetching related data in multiple queries).
- ORM-generated unoptimized SQL.

**Fixes:**
#### **Solution 1: Add Missing Indexes**
**Bad Query:**
```sql
-- Slow due to no index on `email` and `status`
SELECT * FROM users WHERE email = 'user@example.com' AND status = 'active';
```
**Fix:**
```sql
-- Add composite index
CREATE INDEX idx_users_email_status ON users(email, status);
```
**Verify with:**
```sql
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'user@example.com' AND status = 'active';
```

#### **Solution 2: Optimize Joins**
**Bad Query (Cartesian Product):**
```sql
-- No JOIN condition, returns all combinations
SELECT * FROM orders, users WHERE users.id = orders.user_id; -- Missing WHERE clause
```
**Fix:**
```sql
-- Proper JOIN with indexed columns
SELECT o.*, u.name
FROM orders o
JOIN users u ON o.user_id = u.id; -- Ensure `user_id` is indexed
```

#### **Solution 3: Use Query Batching (N+1 Problem)**
**Bad (N+1 Queries):**
```python
# Generates 100+ queries for each user's orders
users = db.get_all_users()
for user in users:
    user.orders = db.get_orders_by_user(user.id)
```
**Fix (Batch Fetching):**
```python
# Single query per entity
users = db.get_all_users(batch_size=1000)
user_ids = [u.id for u in users]
orders = db.get_orders_by_users(user_ids)  # Returns nested data
```

---

### **Issue 2: Memory Leaks**
**Symptoms:**
- Gradual increase in heap/memory usage over time.
- `OutOfMemoryError` in JVM or `Segmentation Fault` in C++.
- Unreleased database connections or file handles.

**Root Causes:**
- Unclosed resources (DB connections, files, sockets).
- Caching layer not evicting stale data.
- Accumulation of large objects (e.g., unbounded lists in memory).

**Fixes:**
#### **Solution 1: Ensure Resource Cleanup**
**Bad (Resource Leak):**
```java
// Database connection not closed
public void processUser(User user) {
    Connection conn = dataSource.getConnection();
    Statement stmt = conn.createStatement();
    // ... (logic) ...
    // Missing: stmt.close(); conn.close();
}
```
**Fix (Use Try-With-Resources):**
```java
// Auto-closes resources
public void processUser(User user) throws SQLException {
    try (Connection conn = dataSource.getConnection();
         Statement stmt = conn.createStatement()) {
        // Logic here
    } // Resources auto-closed
}
```

#### **Solution 2: Implement Cache Eviction**
**Bad (Unbounded Cache):**
```python
# Guaranteed memory leak
cache = {}
for item in infinite_stream():
    cache[item.id] = item
```
**Fix (Size-Bounded Cache):**
```python
# Using LRUCache (Python) or Guava Cache (Java)
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_expensive_data(key):
    return fetch_from_db(key)
```

**Tools:**
- **Java:** VisualVM, Eclipse MAT (Memory Analyzer Tool).
- **Node.js:** `clinic.js`, `heapdump`.
- **Go:** `pprof` built-in profiler.

---

### **Issue 3: Thread Pool Starvation**
**Symptoms:**
- `RejectedExecutionException` (Java).
- High `BLOCKED` threads in `jstack`.
- CPU spiking when throttling occurs.

**Root Causes:**
- Fixed-size thread pool too small for load.
- Infinite blocking operations (e.g., deadlocks, hung I/O).
- Unbounded task queues.

**Fixes:**
#### **Solution 1: Right-Size Thread Pool**
**Bad (Too Small Pool):**
```java
// Only 2 threads for high-load system
ExecutorService pool = Executors.newFixedThreadPool(2);
```
**Fix (Dynamic Sizing):**
```java
// Use cached thread pool or dynamic scaling
ExecutorService pool = Executors.newCachedThreadPool();
// OR (for bounded concurrency)
ExecutorService pool = Executors.newFixedThreadPool(Runtime.getRuntime().availableProcessors() * 4);
```

#### **Solution 2: Avoid Blocking in Worker Threads**
**Bad (Blocking Calls):**
```java
// Deadlock risk if `slowOperation()` blocks forever
pool.execute(() -> {
    slowOperation(); // No timeout or cancellation
});
```
**Fix (Async with Timeout):**
```java
// Use CompletableFuture with timeout
CompletableFuture.supplyAsync(() ->
    slowOperation(), executor)
    .exceptionally(ex -> handleError(ex))
    .orTimeout(5, TimeUnit.SECONDS); // Timeout after 5s
```

**Tools:**
- **Java:** `jstack -l <pid>`, APM thread profiling.
- **Go:** `pprof net` for goroutine leaks.

---

### **Issue 4: Inefficient Caching Strategies**
**Symptoms:**
- Cache hit ratio < 50% (wasted reads).
- Stale data served due to incorrect TTL.
- Cache stampede effect under load.

**Root Causes:**
- TTL too short/long.
- No cache invalidation.
- Missing cache partitioning (e.g., global cache for multi-tenant apps).

**Fixes:**
#### **Solution 1: Optimize Cache TTL**
**Bad (Too Short/Long TTL):**
```python
# TTL too short: High read-to-write ratio
cache = Cache(TTL=1)  # Expires every second
```
**Fix (TTL Based on Access Pattern):**
```python
# Dynamic TTL or probabilistic cache
cache = Cache(TTL=300)  # Longer for read-heavy data
```
**Solution 2: Use Cache Stampede Protection**
**Bad (Miss Stampede):**
```python
# All threads race to fetch from DB when cache misses
def get_data(key):
    if key not in cache:
        data = fetch_from_db(key)
        cache[key] = data  # Race condition
    return cache[key]
```
**Fix (Lazy Loading + Locking):**
```python
# Using `functools.lru_cache` or Redis Lua script
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_data(key):
    return fetch_from_db(key)  # Thread-safe via decorators
```

**Tools:**
- **Redis:** `INFO stats` (evictions, hits/misses), `redis-cli --stat`.
- **APM:** Track cache hit ratio metrics.

---

### **Issue 5: External API Timeouts & Retries**
**Symptoms:**
- HTTP 5xx errors from downstream services.
- Retry logic causing cascading failures.
- Timeout errors (`Connection Timeout`, `Read Timeout`).

**Root Causes:**
- No retry logic for transient failures.
- Fixed retry delay (exponential backoff not implemented).
- Unbounded retries (loop forever).

**Fixes:**
#### **Solution 1: Implement Exponential Backoff**
**Bad (Fixed Retry Delay):**
```python
# Always retry after 1s (inefficient under load)
def call_api(url):
    for _ in range(3):
        try:
            response = requests.get(url)
            return response
        except requests.exceptions.RequestException:
            time.sleep(1)  # Fixed delay
```
**Fix (Exponential Backoff):**
```python
import time
import random

def call_api(url, max_retries=3):
    delay = 1
    for _ in range(max_retries):
        try:
            return requests.get(url)
        except requests.exceptions.RequestException as e:
            time.sleep(delay)
            delay *= 2  # Exponential backoff
    raise Exception(f"Failed after {max_retries} retries")
```

#### **Solution 2: Circuit Breaker Pattern**
**Bad (No Fallback):**
```python
# Crashes the app if API fails
def process_order(order):
    api_response = call_external_api(order)
    save_to_db(api_response)
```
**Fix (Circuit Breaker):**
```python
from pybreaker import CircuitBreaker

breaker = CircuitBreaker(fail_max=5, reset_timeout=60)

@breaker
def process_order(order):
    api_response = call_external_api(order)
    save_to_db(api_response)
```

**Tools:**
- **Retry Libraries:** `resilience4j`, `retry`, `tenacity`.
- **APM:** Distributed tracing to track API call latency.

---

## **3. Debugging Tools and Techniques**
### **A. Profiling & Performance Monitoring**
| **Tool**               | **Use Case**                          | **Command/Example**                  |
|-------------------------|---------------------------------------|---------------------------------------|
| **JVM Profiling**       | Java heap/method profiling            | `jprofiler`, `VisualVM`, `Async Profiler` |
| **Go Profiler**         | Goroutine/CPU memory profiling        | `go tool pprof http://localhost:6060/debug/pprof/profile` |
| **Node.js Profiling**   | CPU flame graphs                      | `node --inspect --expose-gc` + Chrome DevTools |
| **Linux Tools**         | System-level bottlenecks              | `top`, `htop`, `iotop`, `strace`, `perf` |
| **Database Profiling**  | Slow queries                          | `EXPLAIN ANALYZE`, `slow_query_log` |
| **APM Tools**           | Distributed tracing, latency analysis | New Relic, Datadog, Dynatrace |

### **B. Logging & Tracing**
- **Structured Logging:** Use `JSON` logs with correlation IDs.
  ```json
  {"timestamp":"2024-02-20T12:00:00Z", "level":"ERROR", "trace_id":"abc123", "message":"DB query timeout"}
  ```
- **Distributed Tracing:** Tools like OpenTelemetry, Jaeger, or Zipkin to track requests across services.

### **C. Load Testing**
- **Tools:**
  - **Locust**, **JMeter**, **k6** (for synthetic load).
  - **Chaos Engineering:** Gremlin, Chaos Monkey (to test resilience).
- **Example (Locust):**
  ```python
  from locust import HttpUser, task

  class DbUser(HttpUser):
      @task
      def hit_endpoint(self):
          self.client.get("/slow-endpoint?force-slow=true")
  ```

### **D. Database-Specific Tools**
| **Database** | **Tool**                     | **Command**                          |
|--------------|------------------------------|---------------------------------------|
| PostgreSQL   | `pgbadger`, `pg_stat_statements` | `pgbadger -f logfile.log`            |
| MySQL        | `pt-query-digest`, `MySQL Workbench` | `pt-query-digest slow.log` |
| MongoDB      | `mongotop`, `explain()`      | `db.collection.explain("executionStats")` |

---

## **4. Prevention Strategies**
### **A. Coding Conventions**
1. **Database:**
   - Always use `EXPLAIN ANALYZE` before optimizing queries.
   - Avoid `SELECT *`; fetch only required columns.
   - Use connection pooling (HikariCP, PgBouncer).

2. **Caching:**
   - Follow **Cache-Aside** (Lazy Loading) or **Write-Through** patterns.
   - Set appropriate TTL (e.g., shorter for volatile data).
   - Use **cache sharding** for multi-tenant apps.

3. **Concurrency:**
   - Prefer **asynchronous I/O** (e.g., `asyncio` in Python, `CompletableFuture` in Java).
   - Limit thread pools (`Executors.newFixedThreadPool(N)`).
   - Avoid holding locks for too long.

4. **Error Handling:**
   - Implement **circuit breakers** (Resilience4j, Hystrix).
   - Use **exponential backoff** for retries.
   - Log failures with context (e.g., `trace_id`).

### **B. Observability Best Practices**
1. **Metrics:**
   - Track `response_time`, `error_rate`, `cache_hit_ratio`.
   - Use **percentiles** (P99) to detect outliers.

2. **Logging:**
   - Correlate logs with `trace_id` for end-to-end debugging.
   - Avoid logging sensitive data.

3. **Alerting:**
   - Set up alerts for:
     - High error rates (>1%).
     - Latency spikes (>3σ from baseline).
     - Resource exhaustion (CPU > 90%, memory > 80%).

### **C. Automated Testing & CI/CD**
1. **Performance Tests:**
   - Include load tests in CI (e.g., `k6` in GitHub Actions).
   - Reject PRs that degrade P99 latency by >10%.

2. **Static Analysis:**
   - Linters for inefficient code (e.g., `eslint-plugin-performance` for JS).
   - Database schema validators (e.g., `sqlfluff`).

3. **Chaos Testing:**
   - Periodically kill random pods (Kubernetes) or database instances to test resilience.

### **D. Architectural Considerations**
1. **Microservices:**
   - Decouple services with **async messaging** (Kafka, RabbitMQ).
   - Use **gRPC** for internal service communication (lower latency than REST).

2. **Database:**
   - Shard read-heavy tables.
   - Use **read replicas** for analytics queries.

3. **Caching:**
   - Tiered caching (Redis → Memcached → SSD).
   - **Edge caching** (Cloudflare, Fastly) for static content.

---

## **5. Quick Checklist for Immediate Debugging**
When a performance issue arises, follow this **5-step checklist**:

1. **Reproduce:** Can you reproduce the issue? (Load test, stress test.)
2. **Isolate:** Is it CPU, memory, disk, or network-bound?
3. **Profile:** Use `top`, `heapdump`, or APM to identify bottlenecks.
4. **Fix:** Apply the most likely fix (e.g., add index, resize thread pool).
5. **Validate:** Measure before/after (e.g., `curl -o /dev/null -w "%{time_total}\n"`).

---

## **Conclusion**
Performance Conventions are not just guidelines—they’re **contracts** between developers and the system’s reliability. When issues arise:
- **Systematically rule out symptoms** (latency, memory, DB, etc.).
- **Use the right tools** (profilers, APM, distributed tracing).
- **Apply fixes incrementally** and validate with metrics.
- **Prevent recurrence** with observability, testing, and architectural best practices.

By following this guide, you’ll quickly diagnose and resolve performance issues while ensuring your system remains scalable and efficient.