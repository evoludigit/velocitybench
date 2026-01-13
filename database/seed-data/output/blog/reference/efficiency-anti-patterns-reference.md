# **[Pattern] Efficiency Anti-Patterns: Reference Guide**

---

## **Overview**
Efficiency anti-patterns are **suboptimal design or implementation choices** that degrade system performance, increase resource consumption, or introduce unnecessary complexity without providing proportional benefits. These patterns often emerge from misaligned priorities, lack of profiling, or premature optimization assumptions.

This guide categorizes common **efficiency anti-patterns**—such as **unnecessary polymorphism**, **data duplication**, or **global state misuse**—along with their **impact**, **symptoms**, and **refactoring strategies**. Understanding these pitfalls helps engineers avoid common pitfalls in performance-critical systems, from micro-services to high-frequency trading platforms.

---

## **Schema Reference**
Below is a structured breakdown of **Efficiency Anti-Patterns** (4 categories, 12 sub-patterns).

| **Category**           | **Anti-Pattern**                  | **Symptoms**                                                                 | **Trigger**                                                                 | **Refactoring Strategy**                                                                 |
|------------------------|-----------------------------------|------------------------------------------------------------------------------|------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------|
| **Data Access**        | **N+1 Query Problem**             | Sudden spikes in database load; repeated identical queries.                 | Lazy-loading collections without eager batching (e.g., ORMs like Hibernate). | Use **JOINs**, **pre-fetching**, or **graph traversal** (e.g., DTOs, `SELECT *`).           |
|                        | **Over-Fetching**                 | Unnecessary data transfer; high memory/bandwidth usage.                     | Loading entire objects despite only needing a few fields.                   | Use **projections** (e.g., `SELECT id, name`), **pagination**, or **graphQL**.             |
|                        | **Under-Fetching**                | Multiple round-trips; inefficient caching.                                  | Fetching minimal data, then fetching related records separately.             | **Batch queries** or **denormalize** strategically.                                      |
| **Algorithm**          | **Premature Optimization**        | Code becomes harder to maintain for marginal gains.                          | Optimizing before profiling (e.g., hand-coded loops instead of built-ins).  | Profile first (**JVM Profilers, Flame Graphs**), then **defer optimizations**.              |
|                        | **Inefficient Data Structures**   | High time/space complexity (e.g., `O(n²)` for small `n`).                    | Using `List` for binary search; `HashMap` for sorted data.                 | Replace with **optimized collections** (e.g., `TreeMap`, `Trie`, or **Bloom Filters**).  |
|                        | **Recursive Without Memoization** | Exponential time complexity (e.g., Fibonacci recalculation).               | Recursive solutions without caching (e.g., LRU caches).                     | Use **memoization** or **iterative DP** (e.g., `longestCommonSubsequence`).              |
| **Concurrency**        | **Busy-Waiting (Spinlocks)**      | CPU waste due to repeated checks (e.g., `while (!ready) {}`).               | Lack of proper synchronization primitives (e.g., `Semaphore`, `Condition`).   | Replace with **non-blocking algorithms** (e.g., CAS, `ConcurrentHashMap`).                |
|                        | **Thread Starvation**             | Deadlocks or unbounded queues due to poor concurrency control.             | Unlimited thread pools or lack of **work-stealing**.                          | Use **bounded pools** (e.g., `ExecutorService` with `ThreadPoolExecutor`) or **async I/O**. |
| **Memory**             | **Object Retention (Memory Leaks)**| Gradual memory growth; GC pauses.                                          | Unreleased resources (e.g., file handles, DB connections).                  | Implement **weak references**, **try-finally blocks**, and **profile with `VisuBin`.**  |
|                        | **Data Duplication**              | Inconsistent state; high storage overhead.                                  | Copying data between layers (e.g., DB ↔ Cache ↔ API).                      | **Denormalize selectively**, use **event sourcing**, or **materialized views**.             |
| **Global State**       | **Mutable Global Variables**      | Unpredictable behavior; hard-to-debug race conditions.                     | Shared state across threads/processes (e.g., `static` variables).           | Replace with **dependency injection**, **immutable data**, or **message passing**.       |
|                        | **Monolithic Transaction Blocks** | Long-running transactions; blocking resources.                            | Chaining operations in a single DB transaction.                             | **Decompose transactions**, use **sagas**, or **optimistic concurrency**.                 |
| **Network**            | **Uncompressed Payloads**         | High bandwidth usage; slow transfers.                                       | Sending raw JSON/XML without compression (e.g., `gzip`).                    | Use **compression** (`Brorotli`, `Snappy`) or **protocol buffers**.                      |
|                        | **Excessive Serialization**      | CPU overhead for stringification/parsing.                                  | Overusing `JSON.stringify()`/`eval()` in JS or `JSONSerializer` in Java.   | Use **efficient formats** (e.g., **MessagePack**, **Protocol Buffers**) or **caching**.    |

---

## **Query Examples**
### **1. Detecting the N+1 Problem (SQL/ORM)**
**Bad:**
```python
# Hibernate/Ktor example: Each user fetches their comments separately
for user in User.find_all():
    print(user.comments)  # Generates N+1 queries!
```
**Fix:**
```python
# Pre-fetch comments in a single query
users = db.session.execute("""
    SELECT u.*, c.*
    FROM users u
    LEFT JOIN comments c ON u.id = c.user_id
""").fetchall()
```

**Symptom Detection:**
```sql
-- Check slow queries in PostgreSQL
SELECT query, count(*) as calls
FROM pg_stat_statements
WHERE query LIKE '%select%comments%'
ORDER BY calls DESC;
```

---

### **2. Premature Optimization (Python Example)**
**Bad:**
```python
# Manual list sorting (ignoring built-in TimSort)
def sort_naive(arr):
    for i in range(len(arr)):
        for j in range(i+1, len(arr)):
            if arr[j] < arr[i]:
                arr[i], arr[j] = arr[j], arr[i]
    return arr
```
**Fix (after profiling):**
```python
# Use Python’s built-in TimSort (O(n log n))
arr = [5, 2, 9, 1]  # Actual data shows this is slower than sorted(arr)
```

**Profiling Workflow:**
```bash
# Use Python’s cProfile
python -m cProfile -s cumulative script.py
```

---

### **3. Thread Starvation (Java Example)**
**Bad:**
```java
// Unbounded thread pool leads to OOM
ExecutorService executor = Executors.newCachedThreadPool();
for (int i = 0; i < 1_000_000; i++) {
    executor.submit(() -> { /* ... */ });
}
```
**Fix:**
```java
// Bounded pool with queue limit
ExecutorService executor = new ThreadPoolExecutor(
    5, 10, 60, TimeUnit.SECONDS,
    new LinkedBlockingQueue<>(1000)  // Rejects after 1000 tasks
);
```

**Diagnosis:**
```bash
# Check thread dumps for blocked threads
jstack <pid> | grep "Deadlock"
```

---

## **Refactoring Checklist**
1. **Profile First**:
   - Use tools like **JVM Profiler (Async Profiler)**, **Perf (Linux)**, or **Chrome DevTools**.
   - Identify **hotspots** (e.g., 90% CPU in a single method).

2. **Optimize Selectively**:
   - Focus on **top 20% of functions** contributing to 80% of latency (Pareto Principle).

3. **Avoid Cognitive Load**:
   - Trade off **readability** for performance only when **measured**.
   - Example: Replace a **regex** with a **trie** if profiling shows it’s a bottleneck.

4. **Leverage Abstractions**:
   - Use **standard libraries** (e.g., `SortedSet` over manual sorting).
   - Prefer **concurrency primitives** (e.g., `ConcurrentHashMap`) over custom locks.

5. **Document Trade-offs**:
   - Add comments explaining **why** an anti-pattern was avoided (e.g., "Avoided `ArrayList` for `int[]` due to cache locality").

---

## **Related Patterns**
| **Pattern**                     | **When to Use**                                                                 | **Avoid When**                                                                 |
|----------------------------------|---------------------------------------------------------------------------------|--------------------------------------------------------------------------------|
| **[Lazy Initialization]**        | Deferring expensive setup (e.g., DB connections).                              | In **hot paths** where overhead outweighs benefits.                            |
| **[Caching Strategies]**         | Reducing redundant computations (e.g., `Cache-Aside`).                         | When **cache invalidation** becomes complex.                                  |
| **[Microservices Decomposition]**| Splitting monoliths for scalability.                                           | When **inter-service latency** exceeds in-memory speed.                        |
| **[Immutable Data]**             | Thread-safe shared state (e.g., `final` in Java).                             | When **mutability** is required for performance (e.g., sorting in-place).       |
| **[Event-Driven Architecture]**  | Decoupling components via events.                                               | In **high-throughput** systems where **event serialization** becomes costly.   |

---
**Note:** Efficiency anti-patterns are **context-dependent**. Always validate assumptions with **real metrics** (e.g., latency, throughput). For further reading, see:
- *"Structure and Interpretation of Computer Programs"* (SICP) – Algorithm analysis.
- *"Designing Data-Intensive Applications"* – Distributed system trade-offs.