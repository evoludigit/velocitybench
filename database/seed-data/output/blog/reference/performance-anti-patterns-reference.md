# **[Pattern] Performance Anti-Patterns: Reference Guide**

---

## **Overview**
Performance Anti-Patterns are suboptimal techniques, designs, or architectural decisions that degrade application responsiveness, efficiency, or scalability—often in ways that are difficult to detect or diagnose. Unlike performance best practices, anti-patterns perpetuate inefficiencies by encouraging inefficient data access, excessive computation, or poor resource allocation. Recognizing these patterns helps developers avoid costly pitfalls in systems design, database tuning, and application logic.

This guide categorizes common anti-patterns by domain (e.g., database, caching, concurrency) and provides actionable solutions to mitigate their impact. Each example includes structural causes, failure symptoms, and refactoring strategies.

---

## **Classification Schema**
Below is a structured table of Performance Anti-Patterns, organized by **category**, **description**, **symptoms**, and **mitigation**.

| **Category**       | **Anti-Pattern Name**               | **Description**                                                                 | **Symptoms**                                                                 | **Mitigation**                                                                                     |
|--------------------|-------------------------------------|---------------------------------------------------------------------------------|-----------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Database**       | **N+1 Query Problem**               | Fetching related data in loops instead of batching queries.                          | High query count, slow response times under load.                          | Use **joins**, **EAGER loading** (ORM), or **subqueries**.                                      |
|                    | **SELECT *** / **Over-Fetching**    | Retrieving unnecessary columns or rows to satisfy current needs.                  | Excessive data transfer, slower parsing, wasted storage.                    | Limit columns (`SELECT id, name`) or use **pagination**.                                         |
|                    | **No Indexing on Hot Keys**         | Missing indexes on frequently queried columns (e.g., foreign keys).              | Full table scans, degraded query performance with scale.                     | Add indexes on **high-cardinality** columns and foreign keys.                                    |
|                    | **Long-Running Transactions**       | Transactions holding locks or open cursors for extended periods.                | Stalled queries, deadlocks, reduced concurrency.                          | Optimize transactions (avoid `SELECT FOR UPDATE`), use **timeouts**, or **shrink transactions**. |
| **Caching**        | **Lazy Loading Without Warming**    | Caching data only when accessed, leading to cold-start delays.                     | Sporadic latency spikes.                                                    | Pre-warm caches (e.g., preload during startup).                                                 |
|                    | **Cache Stampede**                  | Many requests trigger cache misses simultaneously when a stale key expires.      | Thundering herd problem, degraded performance.                            | Use **cache warming** or **stale-while-revalidate**.                                             |
|                    | **Over-Caching**                    | Storing data in cache for prolonged periods, increasing memory pressure.         | Cache evictions, OOM errors.                                                 | Set **TTL policies**, use **LRU eviction**, or **cache sharding**.                              |
| **Concurrency**    | **Thread Starvation**               | Insufficient thread pools causing contention or delays.                           | Slow response times, CPU underutilization.                                  | Scale thread pools dynamically (e.g., **work-stealing** pools).                                  |
|                    | **Race Conditions**                 | Uncontrolled concurrent access to shared resources.                              | Inconsistent data, crashes, or race conditions.                            | Use **locks**, **atomics**, or **immutable data structures**.                                        |
|                    | **Blocking Calls in Loops**         | Synchronous I/O blocking threads in CPU-bound loops.                              | High latency, thread starvation.                                            | Use **asynchronous I/O** (e.g., `async/await`, **completion stages**).                          |
| **Algorithms**     | **Linear Search in Large Datasets** | Scanning entire collections for a value (O(n)).                                  | Poor performance for large `n`.                                              | Pre-sort data or use **hash maps** (O(1) lookup).                                                |
|                    | **Deep Recursion**                  | Recursive functions without tail-call optimization.                              | Stack overflow for large inputs.                                             | Refactor to **iterative loops** or **tail recursion**.                                           |
|                    | **Inefficient Sorting**             | Using O(n²) algorithms (e.g., bubble sort) on large datasets.                    | Sorting times scale quadratically.                                           | Use **Timsort** (Python), **QuickSort** (Java), or **parallel sorts**.                          |
| **Memory**         | **Memory Leaks**                    | Unreleased objects (e.g., unclosed DB connections, unused closures).             | Gradual degradation, OOM errors.                                              | Use **garbage collection tuning**, **manual cleanup** (e.g., `try-finally`), or **weak references**. |
|                    | **Premature Object Creation**       | Instantiating objects unnecessarily (e.g., heavy objects in loops).              | Increased memory usage, GC overhead.                                         | Reuse objects (e.g., **object pools**), or **lazy initialization**.                              |
| **Network**        | **Large Payloads**                  | Sending excessive data over the wire (e.g., unserialized objects).               | High bandwidth usage, slower deserialization.                              | **Compress data**, use **protobuf/gRPC**, or **serialization optimizations**.                     |
|                    | **Connection Pool Exhaustion**      | Exhausting DB/network connection pools under load.                               | Connection refused errors, degraded throughput.                              | Configure **pool sizing** (e.g., HikariCP), use **connection reuse**.                            |
| **Parallelism**    | **False Sharing**                   | Concurrent threads modifying adjacent memory locations, causing cache misses.     | Poor CPU cache locality, reduced throughput.                                | Align data structures (e.g., **padding**, **thread-local storage**).                              |
|                    | **Over-Partitioning**               | Splitting work into too many tiny tasks, increasing coordination overhead.        | High scheduling cost, reduced efficiency.                                    | Batch tasks or **adjust partition granularity**.                                                 |

---

## **Query Examples and Fixes**

### **1. Database Anti-Patterns**
#### **Problem: N+1 Query Problem**
**Bad:**
```sql
-- Fetch users (1 query)
SELECT * FROM users WHERE active = true;

-- Then loop and fetch orders per user (N queries)
foreach user:
    SELECT * FROM orders WHERE user_id = ?;
```
**Symptoms:** Slow queries under load, high CPU usage.
**Fix:** Use **joins** or **EAGER loading**:
```sql
SELECT u.*, o.* FROM users u LEFT JOIN orders o ON u.id = o.user_id WHERE u.active = true;
```
**Alternative (ORM):**
```python
# Django (EAGER loading)
User.objects.select_related('orders').filter(active=True)
```

#### **Problem: Over-Fetching**
**Bad:**
```sql
SELECT * FROM products WHERE category = 'electronics';
```
**Symptoms:** Unnecessary data transfer, slower processing.
**Fix:** Explicitly fetch required columns:
```sql
SELECT id, name, price FROM products WHERE category = 'electronics';
```

### **2. Caching Anti-Patterns**
#### **Problem: Cache Stampede**
**Bad:** No defense against cache misses when a key expires.
**Symptoms:** Spikes in DB load when a popular cache hits TTL.
**Fix:** Implement **stale-while-revalidate**:
```python
@lru_cache(maxsize=128)
def get_user_data(user_id):
    data = cache.get(f"user_{user_id}")
    if data is None:
        data = fetch_from_db(user_id)
        cache.set(f"user_{user_id}", data, timeout=60)
    return data
```

### **3. Concurrency Anti-Patterns**
#### **Problem: Thread Starvation**
**Bad:** Fixed thread pool with insufficient capacity.
**Symptoms:** Queueing delays, slow task processing.
**Fix:** Dynamic scaling (e.g., Java’s `ForkJoinPool`):
```java
ExecutorService pool = Executors.newWorkStealingPool();
```

#### **Problem: Blocking Calls**
**Bad:** Synchronous HTTP calls in a loop.
**Symptoms:** Threads blocked, poor scalability.
**Fix:** Use async I/O (Node.js example):
```javascript
const fetch = require('node-fetch');

async function processUsers() {
    const users = await fetch('/users');
    const promises = users.map(user =>
        fetch(`/user/${user.id}`).then(res => res.json())
    );
    await Promise.all(promises); // Non-blocking
}
```

### **4. Algorithm Anti-Patterns**
#### **Problem: Linear Search**
**Bad:**
```python
def find_user(users, name):
    for user in users:  # O(n)
        if user['name'] == name:
            return user
    return None
```
**Fix:** Use a hash map (O(1)):
```python
user_map = {user['name']: user for user in users}
def find_user(name):
    return user_map.get(name)
```

---

## **Mitigation Strategies by Category**

### **Database**
- **Profile Queries:** Use tools like `EXPLAIN ANALYZE` (PostgreSQL) or slow query logs.
- **Optimize Schema:** Denormalize, add computed columns, or partition tables.
- **Connection Pooling:** Configure pools (e.g., HikariCP) to handle concurrency.

### **Caching**
- **Tiered Caching:** Combine in-memory (Redis) + disk (Memcached) caches.
- **Cache Invalidation:** Use **write-through** or **event-based** invalidation.
- **Cache Sharding:** Distribute cache keys across nodes to reduce contention.

### **Concurrency**
- **Thread Pools:** Size pools dynamically (e.g., `ExecutionContext` in .NET).
- **Lock Granularity:** Use **fine-grained locks** (e.g., row-level in databases).
- **Non-Blocking Algorithms:** Prefer **CAS** (Compare-And-Swap) for shared state.

### **Memory**
- **Garbage Collection Tuning:** Adjust heap sizes (e.g., `-Xmx`, `-Xms` in JVM).
- **Object Pools:** Reuse heavy objects (e.g., `Socket` connections).
- **Weak References:** Use `WeakHashMap` (Java) or `__weakref__` (Python) for ephemeral data.

### **Network**
- **Compression:** Enable gzip/deflate for HTTP responses.
- **Protocol Buffers:** Replace JSON with protobuf for binary efficiency.
- **Connection Reuse:** Reuse HTTP/2 or WebSocket connections.

### **Parallelism**
- **Parallel Streams:** Use Java’s `parallelStream()` for CPU-bound tasks.
- **Lock-Free Data Structures:** Consider `AtomicInteger`, `ConcurrentHashMap`.
- **Bulk Operations:** Batch DB writes/reads to reduce coordination overhead.

---

## **Related Patterns**
To avoid anti-patterns, align with these complementary patterns:

1. **Database:**
   - **[Indexing Strategy Pattern](#)** – Design indexes for query patterns.
   - **[Read Replicas Pattern](#)** – Offload read-heavy workloads.
   - **[Connection Pooling Pattern](#)** – Manage DB connections efficiently.

2. **Caching:**
   - **[Cache-Aside Pattern](#)** – Lazy-load data with cache fallback.
   - **[Write-Through Pattern](#)** – Sync writes to cache and DB.
   - **[Cache Warming](#)** – Preload caches during low-traffic periods.

3. **Concurrency:**
   - **[Producer-Consumer Pattern](#)** – Decouple producers/consumers.
   - **[Actor Model](#)** – Isolate state with message-passing.
   - **[Thread-Local Storage](#)** – Avoid shared-state contention.

4. **Algorithm:**
   - **[Memoization Pattern](#)** – Cache expensive function results.
   - **[Divide-and-Conquer](#)** – Optimize recursive algorithms (e.g., merge sort).
   - **[Greedy Algorithms](#)** – For optimization problems (e.g., scheduling).

5. **Memory:**
   - **[Flyweight Pattern](#)** – Share objects to reduce memory.
   - **[Object Pool Pattern](#)** – Reuse costly objects.
   - **[Lazy Initialization](#)** – Delay resource-heavy creations.

6. **Network:**
   - **[Client-Side Pagination](#)** – Limit data transfer.
   - **[Compression Proxy](#)** – Offload compression to a reverse proxy.
   - **[CDN Offloading](#)** – Serve static assets from edge locations.

---

## **Key Takeaways**
- **Avoid Premature Optimization:** Profile before refactoring.
- **Design for Scale:** Assume growth; avoid monolithic anti-patterns.
- **Monitor Proactively:** Use APM tools (e.g., New Relic, Datadog) to catch anti-patterns early.
- **Document Assumptions:** Clarify trade-offs in code reviews (e.g., "This cache is intentionally short-lived").

By recognizing these anti-patterns and applying targeted fixes, you can significantly improve system performance, responsiveness, and scalability. Always prioritize **measurement**, **iteration**, and **collaboration** with DevOps teams to validate improvements.