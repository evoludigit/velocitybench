# **[Pattern] Performance Gotchas: Reference Guide**

---

## **Overview**
Performance Gotchas are **anti-patterns, edge cases, and suboptimal practices** that degrade system performance, often subtly and unpredictably. They can arise from misconceptions about algorithmic efficiency, inefficient data structures, I/O bottlenecks, concurrency pitfalls, or platform-specific quirks. This guide identifies common gotchas across programming paradigms (imperative, functional, OOP), frameworks, and hardware layers, with actionable fixes to maintain or improve system scalability.

---

## **1. Schema Reference: Performance Gotchas by Category**
*(Sorted by severity, not exhaustive.)*

| **Category**          | **Gotcha**                          | **Root Cause**                          | **Impact**                          | **Mitigation Strategy**                                                                 |
|-----------------------|--------------------------------------|-----------------------------------------|-------------------------------------|----------------------------------------------------------------------------------------|
| **Algorithm**         | **Brute-force search**               | O(n) or O(n²) for tasks solvable in O(log n) or better | Slow for large datasets | Use binary search, hash maps, or mathematical optimizations.                          |
|                       | **Nested loops**                     | O(n²) or higher for linearizable tasks  | Quadratic scaling                     | Refactor into O(n) with memoization, parallelization, or greedy algorithms.           |
| **Data Structures**   | **Linked lists for random access**   | O(1) cache misses vs. O(1) array access | Poor locality, high latency          | Prefer arrays/vectors or hash tables for frequent access.                               |
|                       | **Unbounded collections**            | Memory bloat, GC overhead               | OOM crashes or high latency          | Use bounded queues (e.g., `LinkedBlockingQueue`), streaming, or pagination.            |
| **Memory**            | **Premature optimization**           | Optimizing microbenchmarks only         | Unnecessary complexity                | Profile first; optimize hot paths *after* measuring.                                   |
|                       | **Object allocation thrashing**      | Allocating small objects frequently      | High GC pressure                      | Use object pools, flyweights, or primitive types where possible.                      |
| **Concurrency**       | **Lock contention**                  | Fine-grained locking in hot paths       | Deadlocks or serialization           | Coarse-grained locking, lock stripping, or lock-free structures (e.g., CAS).           |
|                       | **Thread-per-request model**         | Over-provisioning threads               | High context-switching overhead       | Use thread pools, async I/O, or event loops.                                           |
| **I/O**               | **Synchronous blocking I/O**         | Threads blocked on disk/network         | Latency spikes, resource starvation  | Use async I/O (e.g., `async/await`, epoll, `select`), or non-blocking APIs.             |
|                       | **Small, frequent file writes**      | High OS call overhead                   | 10x+ performance degradation          | Buffer writes or use memory-mapped files.                                               |
| **Networking**        | **Uncompressed payloads**            | Large binary/text transfer              | Bandwidth and latency overhead       | Use compression (gzip, Protocol Buffers), chunking, or edge caching.                   |
|                       | **Chatty RPCs**                      | Thousands of small RPCs per request     | Protocol overhead                     | Batch requests, use gRPC’s streaming, or reduce granularity.                           |
| **Caching**           | **Cache thrashing**                  | Frequent cache misses due to invalidation | High memory bandwidth usage           | Increase cache size, use LRU/MFU policies, or reduce write frequency.                  |
|                       | **Stale cache reads**                | No consistency guarantees               | Inconsistent data                     | Implement cache invalidation (TTL, write-through) or eventual consistency.             |
| **Database**          | **SELECT * queries**                 | Full table scans                         | Slow queries, high I/O               | Fetch only required columns; add indexes or partition tables.                         |
|                       | **N+1 query problem**                | Lazy-loaded relations                   | Multiplicative latency               | Use eager loading, batch joins, or DTOs.                                                |
| **Hardware**          | **False sharing**                    | Shared cache lines between threads      | Cache line ping-pong                  | Pad structs or use atomics with fine-grained boundaries.                                |
|                       | **Global variables**                 | Race conditions or cache pollution      | Unpredictable performance            | Replace with thread-local storage or immutable data.                                   |
| **Language-Specific** | **Dynamic typing**                   | Runtime type checks                      | JIT overhead                          | Use static types (e.g., TypeScript, Rust) or type annotations.                         |
|                       | **Garbage collection pauses**        | STW (Stop-The-World) pauses              | Unpredictable latency                 | Tune GC (e.g., G1GC, ZGC), reduce allocations, or use manual memory management.        |
| **Framework Gotchas** | **Mutable state in closures**        | Captured references in async tasks       | Memory leaks or stale data            | Use `let` bindings, weak references, or immutable data.                                |
|                       | **Third-party SDK bloat**            | Heavy libraries (e.g., React DOM)       | Bundle size, startup time             | Tree-shake unused code, audit dependencies, or use lightweight alternatives.           |

---

## **2. Query Examples: Common Gotchas and Fixes**

### **2.1 Algorithm: The "QuickSort is Always Fast" Myth**
**Gotcha:** Assuming `O(n log n)` is always better than `O(n²)` without considering constants.
**Example (Python):**
```python
# ❌ Gotcha: Nested loops for "optimization" (O(n²))
def slow_duplicate_check(list1, list2):
    for x in list1:
        for y in list2:
            if x == y:
                return True
    return False

# ✅ Fix: Use a hash set (O(n))
def fast_duplicate_check(list1, list2):
    return any(x in set(list2) for x in list1)
```

---
### **2.2 Memory: Premature Optimization in Loops**
**Gotcha:** Micro-optimizing loop counters without profiling.
**Example (C):**
```c
// ❌ Gotcha: Unnecessary array bounds check
for (int i = 0; i < n; i++) {
    if (i >= ARRAY_SIZE) break;  // Redundant
    arr[i] = i * 2;
}

// ✅ Fix: Profile first; remove if benchmark shows no benefit
for (int i = 0; i < n; i++) arr[i] = i * 2;
```

---
### **2.3 Concurrency: Deadlock from Lock Ordering**
**Gotcha:** Acquiring locks in inconsistent order.
**Example (Java):**
```java
// ❌ Gotcha: Deadlock possible if Thread1 and Thread2 swap lock order
Lock lock1 = new ReentrantLock();
Lock lock2 = new ReentrantLock();

Thread1.run(() -> {
    lock1.lock();
    lock2.lock();  // Thread2 might hold lock2 first
    // ...
});

Thread2.run(() -> {
    lock2.lock();
    lock1.lock();  // Deadlock if Thread1 proceeds
    // ...
});

// ✅ Fix: Enforce global lock order
Lock[] locks = {lock1, lock2};
Arrays.sort(locks);
locks[0].lock();
locks[1].lock();
// ...
```

---
### **2.4 I/O: Blocking Network Calls in a Loop**
**Gotcha:** Synchronous HTTP calls in a loop.
**Example (Node.js):**
```javascript
// ❌ Gotcha: Blocks event loop (O(n) latency)
const data = [];
for (let i = 0; i < 1000; i++) {
    const res = await fetch(`http://api.example.com/${i}`); // Blocks each iteration
    data.push(res.json());
}

// ✅ Fix: Parallelize with limits
const results = await Promise.all(
    Array.from({ length: 1000 }, async (_, i) =>
        fetch(`http://api.example.com/${i}`).then(res => res.json())
    )
);
```

---
### **2.5 Database: The "SELECT * FROM users" Anti-Pattern**
**Gotcha:** Fetching entire rows when only a field is needed.
**Example (SQL):**
```sql
-- ❌ Gotcha: 100MB transfer for 1MB payload
SELECT * FROM orders WHERE user_id = 123;

-- ✅ Fix: Specify columns + limit
SELECT order_id, amount FROM orders WHERE user_id = 123 LIMIT 10;
```

---
### **2.6 Hardware: False Sharing in Multithreaded Arrays**
**Gotcha:** Threads sharing cache lines, causing contention.
**Example (C):**
```c
// ❌ Gotcha: Padded structs or arrays can still suffer false sharing
typedef struct {
    volatile int data;
    int padding[3]; // May not align to cache lines (64B)
} ThreadData;

// ✅ Fix: Use padding to separate cache lines
typedef struct {
    volatile int data;
    int __attribute__((aligned(64))) padding[15]; // Force 64B boundary
} ThreadData;
```

---

## **3. Mitigation Checklist**
1. **Profile First**: Use tools like `perf`, `VTune`, or `Chrome DevTools` to identify bottlenecks.
2. **Measure Constants**: `O(n log n)` vs. `O(2n)` may favor the latter for small `n`.
3. **Avoid Premature Abstractions**: Generic solutions (e.g., "use a queue") often introduce overhead.
4. **Design for Failure**: Assume threads/networks will fail; use retries, circuit breakers, or timeouts.
5. **Leverage Hardware**: Use SIMD, GPU compute, or hardware offloading (e.g., TPUs) for parallelizable tasks.
6. **Document Assumptions**: Note edge cases (e.g., "this cache invalidates on write").

---

## **4. Related Patterns**
- **[Optimized Data Structures](data-structures.md)**: Trade-offs between time/space complexity.
- **[Concurrency Control](concurrency.md)**: Patterns for thread-safe code (e.g., actors, immutable data).
- **[Microservices Optimization](microservices.md)**: Decoupling for scalability vs. latency trade-offs.
- **[Caching Strategies](caching.md)**: Cache invalidation, stale reads, and hit/miss ratios.
- **[Algorithm Selection](algorithms.md)**: Choosing between greedy, divide-and-conquer, or dynamic programming.

---
## **5. Further Reading**
- **Books**:
  - *High Performance JavaScript* (Nicholas Zakas) – I/O and JS gotchas.
  - *Programming Erlang* (Armstrong et al.) – Concurrency and functional gotchas.
- **Tools**:
  - [Heap Profiler](https://github.com/FPs/heap-profiler) (JavaScript heap analysis).
  - [Valgrind](https://valgrind.org/) (C/C++ memory leaks).
- **Papers**:
  - *"The Impact of False Sharing on CPU Performance"* (Cianciula et al.).

---
**Last Updated**: [Date]
**Contributors**: [List names]