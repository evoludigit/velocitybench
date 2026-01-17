**[Pattern] Performance Techniques – Reference Guide**

---

### **1. Overview**
Optimizing application performance is critical for scalability, user experience, and cost efficiency. This reference guide outlines proven **Performance Techniques**—a pattern for improving runtime efficiency through coding best practices, resource management, and architectural optimizations. The pattern applies to backend services, databases, caching layers, and client-side applications. By adopting these techniques, developers can reduce latency, minimize resource consumption, and handle higher loads without sacrificing maintainability.

Key focus areas include:
- **Algorithm optimization** (reducing time/space complexity).
- **Efficient data fetching** (query tuning, pagination, denormalization).
- **Resource allocation** (memory/CPU throttling, lazy loading).
- **Caching strategies** (in-memory, CDN, query caching).
- **Asynchronous processing** (non-blocking I/O, event-driven architectures).

This guide assumes familiarity with basic software engineering principles (e.g., Big-O notation, REST/gRPC design).

---

### **2. Schema Reference**

| **Category**          | **Technique**                  | **Description**                                                                 | **Applicable To**               | **Trade-offs**                          | **Example Metrics**          |
|-----------------------|--------------------------------|---------------------------------------------------------------------------------|----------------------------------|-----------------------------------------|-------------------------------|
| **Algorithm Design**  | **Memoization**               | Cache results of expensive function calls to avoid recomputation.              | Pure functions, recursive logic  | Memory overhead                       | 50% reduction in call duration |
|                       | **Asymptotic Optimization**    | Replace O(n²) algorithms with O(n log n) or O(n) solutions (e.g., sorting).     | Loop-heavy operations            | Implementation complexity             | 10x faster for large datasets   |
|                       | **Spatial Data Structures**    | Use hash maps, tries, or bloom filters for O(1) lookups instead of linear scans. | Key-value searches               | Higher memory usage                    | 90% faster for exact matches   |
| **Data Access**       | **Query Optimization**         | Indexing, query refactoring, and avoiding `SELECT *`.                          | SQL/NoSQL databases              | Storage requirements for indexes       | 3x faster query response      |
|                       | **Pagination**                 | Fetch data in chunks (e.g., `LIMIT`/`OFFSET`) instead of loading all records.    | Large datasets                   | Additional round trips for deep pages  | 80% reduced initial load time   |
|                       | **Denormalization**            | Reduce joins by storing redundant data (trade-off for write consistency).     | Read-heavy workloads             | Increased write complexity           | 60% fewer joins in queries       |
| **Caching**           | **Multi-Level Caching**        | Tiered caches (e.g., CPU cache → RAM → Disk → Database).                        | High-throughput systems          | Cache invalidation complexity        | 99% hit rate for hot data      |
|                       | **CDN Caching**                | Serve static assets (images, JS/CSS) via geographically distributed edge nodes. | Web/mobile applications          | Stale data if not invalidated properly | 70% reduced latency for users    |
|                       | **Object/Query Caching**       | Cache entire database query results or serialized objects.                      | Repeated identical queries       | Cache pollution if patterns change    | 5x faster repeated queries      |
| **Asynchronous Work** | **Non-Blocking I/O**           | Use async/await or event loops to handle concurrent requests without threads.    | I/O-bound applications           | Callback hell complexity               | 4x higher request throughput    |
|                       | **Batch Processing**           | Group small operations into fewer, larger requests (e.g., bulk inserts).      | Batch jobs                        | Higher memory usage temporarily       | 30% faster for 10K+ operations   |
|                       | **Background Jobs**            | Offload long-running tasks (e.g., reporting) to queues (Kafka, SQS).           | Event-driven architectures        | Eventual consistency requirements      | 95% reduced main-thread load     |
| **Memory/CPU**        | **Lazy Loading**               | Load data on-demand rather than upfront (e.g., `lazy` properties in OOP).       | Large objects/graphs              | Higher cognitive load for developers   | 60% less memory pressure        |
|                       | **Garbage Collection Tuning**  | Adjust heap sizes or use generational GC for long-running apps.                  | JVM/.NET applications             | Risk of OOM errors if misconfigured    | 20% reduced GC pauses           |
|                       | **Algorithm Parallelization**  | Split work across cores (e.g., `std::async` in C++).                            | CPU-bound tasks                   | Overhead for small tasks              | 5x speedup for 8-core parallelization |

---

### **3. Query Examples**

#### **3.1 Database Optimization**
**Problem:** Slow `SELECT` due to full table scans.
**Before:**
```sql
-- Bad: Scans 1M rows unnecessarily
SELECT * FROM users WHERE status = 'active';
```
**After:**
```sql
-- Good: Uses index on `status` column
CREATE INDEX idx_users_status ON users(status);
SELECT user_id, email FROM users WHERE status = 'active' LIMIT 1000;
```

#### **3.2 Pagination**
**Problem:** Loading all 100K records at once.
**Before:**
```sql
-- Bad: No pagination
SELECT * FROM orders;
```
**After (Cursor-Based):**
```sql
-- Good: Uses `LIMIT`/`OFFSET` or cursor pagination (e.g., PostgreSQL)
SELECT * FROM orders
WHERE created_at > '2023-01-01'
ORDER BY created_at
LIMIT 100 OFFSET 500;
```
**Cursor-Based Alternative (PostgreSQL):**
```sql
SELECT * FROM orders
WHERE created_at > '2023-01-01'
ORDER BY created_at
FOR JSON PATH '$.created_at' -- Emits a cursor token
LIMIT 100;
```

#### **3.3 Caching Strategy**
**Problem:** Repeated expensive calculations.
**Before (Python):**
```python
# Bad: Recalculates every request
def compute_stats(data):
    return sum(x for x in data if x > 0)
```
**After (With `functools.lru_cache`):**
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def compute_stats(data):
    return sum(x for x in data if x > 0)
```
**For Database Queries (Redis):**
```bash
# Cache a query result for 5 minutes
SET cache:users:100:stats "{\"total\":1000,\"active\":800}"
EXPIRE cache:users:100:stats 300
```

#### **3.4 Asynchronous Processing**
**Problem:** Blocking HTTP endpoints.
**Before (Synchronous):**
```python
# Bad: Blocks thread for 5 seconds
def process_order(order):
    # Simulate slow operation
    time.sleep(5)
    return {"status": "processed"}
```
**After (Async/Await):**
```python
# Good: Non-blocking
async def process_order(order):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, slow_operation, order)
    return {"status": "processed"}
```

---

### **4. Implementation Checklist**
Follow this order to apply techniques systematically:
1. **Profile First:** Use tools like:
   - **Backend:** `pprof` (Go), `asyncio` profiler (Python), `VisualVM` (Java).
   - **Frontend:** Chrome DevTools (Performance tab), Lighthouse.
   - **Database:** `EXPLAIN ANALYZE`, `slowlog` (MySQL).
2. **Optimize Hot Paths:** Focus on 80% of code used 20% of the time.
3. **Cache Aggressively:** Start with in-memory caching (e.g., `memcached`), then add CDN/database-level caching.
4. **Review Queries:** Audit for:
   - Unindexed columns in `WHERE`/`JOIN` clauses.
   - `SELECT *` statements.
   - Nested loops in joins.
5. **Asynchronize I/O:** Replace synchronous calls with async frameworks (e.g., `FastAPI`, `Node.js`).
6. **Monitor:** Track metrics like:
   - Latency percentiles (P99 < 1s for API responses).
   - Cache hit rates (>90% ideal).
   - CPU/memory trends (avoid spikes).

---

### **5. Related Patterns**
| **Pattern**               | **Connection to Performance Techniques**                                                                 | **When to Use**                                  |
|---------------------------|--------------------------------------------------------------------------------------------------------|--------------------------------------------------|
| **CQRS**                  | Separates read (optimized for speed) and write (optimized for consistency) paths.                      | High write/read disparity workloads.            |
| **Event Sourcing**        | Replaces direct DB writes with append-only event logs, enabling efficient reprocessing.               | Audit logs, time-series data.                     |
| **Circuit Breaker**       | Prevents cascading failures by limiting calls to slow services, improving resilience.                | Microservices with unreliable dependencies.      |
| **Bulkhead Pattern**      | Isolates resource usage (e.g., threads) to prevent one request from starving others.                  | High-concurrency applications.                  |
| **Rate Limiting**         | Throttles requests to avoid overloading backend systems.                                               | APIs exposed to untrusted clients.               |
| **Sharding**              | Distributes data across nodes to parallelize reads/writes.                                            | Global-scale applications.                       |

---

### **6. Anti-Patterns to Avoid**
- **Premature Optimization:** Profile before optimizing (e.g., don’t `SELECT *` just because).
- **Cache Stampede:** Many requests hit a cache miss simultaneously (mitigate with [warm-up patterns](https://martinfowler.com/bliki/CacheStampede.html)).
- **Over-Caching:** Cache too much data, increasing memory pressure and invalidation overhead.
- **Blocking Operations:** Sleeping in threads (e.g., `time.sleep`) instead of async I/O.
- **Ignoring Edge Cases:** Optimizing for average case but failing catastrophically at P99 traffic spikes.

---
**Further Reading:**
- [Database Design for Performance](https://use-the-index-luke.com/)
- [High Performance Python](https://www.oreilly.com/library/view/high-performance-python/9781491942363/)
- [CDN Strategies](https://cloud.google.com/cdn/docs) (Google Cloud)