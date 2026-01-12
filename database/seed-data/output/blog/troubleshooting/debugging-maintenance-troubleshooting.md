# **Debugging Maintenance: A Troubleshooting Guide**
*For Backend Engineers Handling Legacy & High-Traffic Systems*

---

## **1. Title & Overview**
**"Debugging Maintenance"** refers to the process of diagnosing, isolating, and fixing issues in **legacy systems, long-running services, or high-traffic applications** where direct debugging tools (like breakpoints) are impractical. This often involves **log analysis, performance profiling, and incremental testing** to identify bottlenecks without disrupting production.

This guide focuses on **practical, actionable steps** to quickly resolve symptoms in real-world backend systems.

---

## **2. Symptom Checklist**
Before diving in, rule out obvious issues:

✅ **High CPU/Memory Usage** (e.g., unexpected spikes)
✅ **Sluggish Performance** (e.g., API responses > 1s)
✅ **Error Spikes** (e.g., 5xx errors in logs)
✅ **Database Locking/Timeouts** (e.g., long-running queries)
✅ **Third-Party Service Failures** (e.g., external API timeouts)
✅ **Inconsistent Data** (e.g., race conditions in distributed systems)
✅ **False Positives in Monitoring** (e.g., alert fatigue)

**Action:** If symptoms match multiple items, prioritize **high-impact, low-effort fixes** first.

---

## **3. Common Issues & Fixes**
### **3.1 High Latency (APIs, Queries, or External Calls)**
**Symptoms:**
- Endpoint responses take **>500ms** unexpectedly.
- Logs show **"query timeout"** or **"external API delay"** errors.

**Root Causes:**
- Slow database queries (unoptimized `SELECT`, missing indexes, N+1 problem).
- Uncached dependency calls (e.g., external APIs without retries).
- Blocking I/O (e.g., file system ops, network delays).

**Quick Fixes:**

#### **A. Database-Side Optimizations**
**Problem:** N+1 query issue in a REST API.
```python
# BAD: Fetching users, then loading posts for each (N+1)
users = db.query("SELECT * FROM users")
posts = []
for user in users:
    posts.append(db.query(f"SELECT * FROM posts WHERE user_id={user.id}"))
```
**Fix:** Use **joins** or **batch loading**.
```python
# GOOD: Single query with JOIN
posts = db.query("SELECT u.*, p.* FROM users u LEFT JOIN posts p ON u.id = p.user_id")
```

#### **B. External API Retries & Timeouts**
**Problem:** External API fails intermittently.
```javascript
// BAD: No retries, hard timeout
axios.get('https://external-api.com/data')
  .then(res => { ... })
  .catch(err => { throw err }});
```
**Fix:** Add **exponential backoff**.
```javascript
// GOOD: Retry with delay
async function fetchWithRetry(url, retries = 3) {
  try {
    return await axios.get(url, { timeout: 5000 });
  } catch (err) {
    if (retries <= 0) throw err;
    await new Promise(res => setTimeout(res, 1000 * Math.pow(2, 3 - retries)));
    return fetchWithRetry(url, retries - 1);
  }
}
```

---

### **3.2 Memory Leaks (Memory Usage Keeps Rising)**
**Symptoms:**
- **`top`/`htop` shows skyrocketing memory in a long-running process.**
- **Garbage collector logs indicate high churn.**

**Root Causes:**
- **Unclosed connections** (DB, HTTP, file handles).
- **Caching objects indefinitely** (e.g., `Dict`/`Map` kept in memory).
- **Circular references** (e.g., Python’s `weakref` issues).

**Quick Fixes:**

#### **A. Check for Unclosed Connections**
**Problem:** Database connections leak in Node.js.
```javascript
// BAD: Forgot to close connection
const pool = new Pool({ connectionLimit: 10 });
pool.query(...).then(() => {}); // Connection never released!
```
**Fix:** Use **connection pooling properly**.
```javascript
// GOOD: Use async/await + `release` in `finally`
const client = await pool.connect();
try {
  await client.query("SELECT * FROM users");
} finally {
  client.release(); // Always release!
}
```

#### **B. Limit Object Retention**
**Problem:** Python script caches too much in memory.
```python
# BAD: Global cache grows indefinitely
cache = {}

def get_user(user_id):
    if user_id not in cache:
        cache[user_id] = fetch_user_from_db(user_id)
    return cache[user_id]
```
**Fix:** **TTL-based cache** (e.g., `cachetools`).
```python
from cachetools import TTLCache

cache = TTLCache(maxsize=1000, ttl=300)  # 5-minute expiry

def get_user(user_id):
    return cache.get(user_id, fetch_user_from_db(user_id))
```

---

### **3.3 Database Lock Contention**
**Symptoms:**
- **Long-running transactions** block queries.
- **`LOCK TABLE` warnings** in logs.
- **Deadlocks** (e.g., `ERROR 1205 (HY000): Lock wait timeout` in MySQL).

**Root Causes:**
- **Long transactions** (not using `BEGIN/COMMIT` properly).
- **No transaction isolation** (dirty reads).
- **Excessive `SELECT FOR UPDATE` locks**.

**Quick Fixes:**

#### **A. Shorten Transaction Time**
**Problem:** A slow transaction holds a lock for 10 seconds.
```sql
-- BAD: No transaction bounds
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE logs SET amount = amount + 100 WHERE id = 1;
```
**Fix:** **Commit early** or use **sagas**.
```sql
-- GOOD: Atomic block with explicit commit
START TRANSACTION;
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE logs SET amount = amount + 100 WHERE id = 1;
COMMIT;
```

#### **B. Avoid `SELECT FOR UPDATE` Where Possible**
**Problem:** Locking rows unnecessarily.
```sql
-- BAD: Blocks other writes
SELECT * FROM orders WHERE user_id = 1 FOR UPDATE;
```
**Fix:** **Use optimistic locking** (version column).
```sql
-- GOOD: Check version first
UPDATE orders SET version = version + 1, status = 'paid'
WHERE user_id = 1 AND version = expected_version;
```

---

### **3.4 External Dependency Failures**
**Symptoms:**
- **Third-party API returns 5xx errors.**
- **Microservice dependencies time out.**

**Root Causes:**
- **No circuit breaker** (cascading failures).
- **No retry logic** (failing silently).
- **Hardcoded dependencies** (no fallback).

**Quick Fixes:**

#### **A. Implement Circuit Breaker (Resilience4j/Python `tenacity`)**
**Problem:** External API crashes the app.
```python
# BAD: No fallback, no retries
def call_external_api():
    response = requests.get("https://external-api.com/data")
    return response.json()
```
**Fix:** **Resilience4j (Java) or `tenacity` (Python).**
```python
# GOOD: Circuit breaker with fallback
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def call_external_api():
    response = requests.get("https://external-api.com/data")
    response.raise_for_status()
    return response.json()
```

#### **B. Use Stubs for Testing**
**Problem:** External API is slow/unreliable in tests.
**Fix:** **Mock with `unittest.mock` (Python) or `msw` (JavaScript).**
```javascript
// GOOD: Mock API in tests (MSW)
import { setupServer } from 'msw/node';
import { rest } from 'msw';

const server = setupServer(
  rest.get('https://external-api.com/data', (req, res, ctx) => {
    return res(ctx.json({ mock: 'data' }));
  })
);

beforeAll(() => server.listen());
afterAll(() => server.close());
```

---

## **4. Debugging Tools & Techniques**
| **Tool/Technique**       | **Use Case**                          | **Example Command/Setup** |
|--------------------------|---------------------------------------|---------------------------|
| **`strace` (Linux)**     | Trace system calls (I/O, DB locks).   | `strace -p <PID>` |
| **`perf`/`pprof`**       | CPU profiling (hotspots).             | `perf record -g -e cycles ./app` |
| **`dtrace`**             | Kernel-level tracing (Java/Native).    | `sudo dtrace -n 'pid$target::start:* { printf("%s", copyinstr(arg0)); }'` |
| **Prometheus/Grafana**   | Metrics for latency, errors, rates.   | Query: `rate(http_requests_total[5m])` |
| **ELK Stack (Elasticsearch)** | Log aggregation & analysis. | Kibana DSL: `error: "timeout"` |
| **`gdb`/`pdb`**          | Debug core dumps (C/Python).          | `gdb ./app core dumpfile` |
| **`tcpdump`**            | Network packet inspection.             | `tcpdump -i eth0 port 3306` (MySQL) |
| **`turbostat` (Intel)**  | CPU throttling analysis.               | `turbostat --show Package0 --repeat 1` |
| **JVM Profilers**        | Java heap/dump analysis.               | `jcmd <PID> GC.heap_dump > heap.hprof` |

**Pro Tip:**
- **For latency issues**, use **`traceroute`** (network) + **`EXPLAIN ANALYZE`** (SQL).
- **For memory leaks**, compare **before/after snapshots** (e.g., `gcore` + `heapdump`).

---

## **5. Prevention Strategies**
### **5.1 Code-Level**
✔ **Benchmark critical paths** (e.g., `benchmarks` in Go, `@benchmark` in Java).
✔ **Use circuit breakers** (Resilience4j, Hystrix).
✔ **Implement retries with jitter** (avoid thundering herd).
✔ **Avoid global state** (prefer stateless handlers).

### **5.2 Infrastructure-Level**
✔ **Auto-scaling** (scale-out before memory leaks grow).
✔ **Read replicas** (offload query load).
✔ **Distributed tracing** (Jaeger, OpenTelemetry).
✔ **Chaos engineering** (test failure modes with Gremlin).

### **5.3 Monitoring & Alerts**
✔ **Set SLOs** (e.g., "API < 1s p99").
✔ **Alert on anomalies** (not just thresholds).
✔ **Log correlation IDs** (trace requests end-to-end).

**Example Alert (Prometheus):**
```yaml
- alert: HighLatency
  expr: histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) > 1
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "API latency >1s (instance={{ $labels.instance }})"
```

---

## **6. Quick Resolution Checklist**
| **Step**               | **Action**                                                                 |
|------------------------|---------------------------------------------------------------------------|
| **1. Isolate**         | Check if issue is prod vs. staging.                                        |
| **2. Reproduce**       | Trigger the symptom (e.g., `ab` for load, `curl` for API calls).          |
| **3. Profile**         | Use `perf`, `traceroute`, or `EXPLAIN ANALYZE`.                           |
| **4. Fix**             | Apply the smallest change (e.g., add index, retry logic).                |
| **5. Validate**        | Ensure fix doesn’t introduce new issues (A/B test if possible).            |
| **6. Prevent**         | Add monitoring, tests, or docs to avoid recurrence.                       |

---

## **Final Notes**
- **"Debugging Maintenance" is about** **inference** (not just code changes).
- **Start with logs** (`journalctl`, ELK) before diving into code.
- **Assume the simplest cause first** (e.g., cache miss → DB overload).
- **Document fixes**—future you (or team) will thank you.

**Example Workflow:**
1. **Symptom:** `5xx errors spike at 3 PM`.
2. **Check:** `kubectl logs <pod>` → External API timeouts.
3. **Fix:** Add retry logic + circuit breaker.
4. **Verify:** Roll out + monitor metrics.

---
**End of Guide.**
*For deeper dives, see:*
- [Google’s Site Reliability Engineering (SRE) Book](https://sre.google/sre-book/)
- [Kubernetes Debugging Guide](https://kubernetes.io/docs/tasks/debug/)
- [Chaos Engineering: How Netflix Stays Aloft](https://www.oreilly.com/library/view/chaos-engineering-how/9781491993268/)