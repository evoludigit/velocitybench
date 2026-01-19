# **[Anti-Pattern] Throughput Anti-Patterns Reference Guide**
*Unintentional bottlenecks that degrade system scalability and performance*

---

## **Overview**
Throughput anti-patterns are common design or implementation flaws that prevent a system from handling requests efficiently, even under light to moderate load. These issues often stem from inefficient resource utilization (CPU, memory, I/O, or network), poor concurrency handling, or suboptimal algorithm choices. While individual anti-patterns may appear minor, their cumulative effect can cripple scalability, leading to degraded user experience, increased latency, or even system failures under load.

This guide categorizes key throughput anti-patterns, their root causes, and mitigation strategies. It covers **process-level, data access, concurrency, and architectural anti-patterns**, with actionable solutions to optimize performance.

---

## **Schema Reference**
| **Category**               | **Anti-Pattern**               | **Description**                                                                                     | **Impact**                                                                                     | **Root Cause**                                                                                     |
|----------------------------|----------------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| **Process-Level**          | **Blocking I/O**                | Synchronous calls (e.g., file/network ops) without asynchronous or non-blocking alternatives.       | High CPU contention; threads blocked waiting on I/O.                                           | Lack of async programming models or improper use of synchronous APIs.                             |
|                            | **Global Locks**                | Single locking mechanism (e.g., `synchronized` blocks) protecting all shared resources.             | Throttled concurrency; scalability limited by lock contention.                                 | Over-reliance on coarse-grained locks or lack of lock granularity.                                |
|                            | **Unbounded Resources**         | Memory-heavy data structures (e.g., in-memory caches, unsized collections) growing indefinitely.    | OOM (Out-of-Memory) errors; garbage collection pauses.                                        | Ignoring resource limits or assuming infinite memory.                                           |
| **Data Access**            | **N+1 Query Problem**           | Fetching related data via multiple round-trips (e.g., joining tables in application code).          | Database overload; increased latency.                                                          | Lack of batching or eager-loading strategies.                                                     |
|                            | **Sequential Scans**            | Scanning entire databases/tables without indexes or filters.                                         | Slow read operations; high CPU/memory usage.                                                   | Poor indexing strategy or unoptimized queries.                                                   |
|                            | **Write-Heavy Workloads**        | Excessive small writes (e.g., frequent updates to shared tables) without batching.               | Database performance degradation (e.g., InnoDB buffer pool misses).                           | Transactional workloads without batching or caching.                                             |
| **Concurrency**            | **Thread Starvation**           | Fixed thread pool size insufficient for concurrent tasks.                                           | High latency; thread context-switching overhead.                                              | Static thread pool sizing or ignoring workload spikes.                                            |
|                            | **Race Conditions**             | Shared state modified without proper synchronization (e.g., `double-checked locking`).             | Inconsistent data; crashes or silent failures.                                                 | Unsafe concurrent access patterns.                                                              |
|                            | **Deadlocks**                   | Circular dependencies between locks (e.g., `Lock A` → `Lock B` → `Lock A`).                          | System hangs; unpredictable failures.                                                          | Poor lock acquisition order or nested locking.                                                   |
| **Architectural**          | **Tight Coupling**              | Components dependent on monolithic services (e.g., all business logic in a single microservice).   | Scalability bottlenecks; single point of failure.                                              | Lack of modular decomposition or service boundaries.                                            |
|                            | **Over-Fetching**               | Retrieving unnecessary data (e.g., entire records instead of fields).                               | Higher network bandwidth; slower processing.                                                  | Poor API design or inefficient data serialization.                                              |
|                            | **Poor Caching Strategy**       | Cache invalidation not tied to data changes (e.g., stale reads).                                   | Increased load on backend systems.                                                             | Lack of cache coherence mechanisms (e.g., TTL, write-through).                                  |

---

## **Query Examples: Anti-Patterns and Fixes**
### **1. Blocking I/O → Asynchronous I/O**
**Anti-Pattern (Python):**
```python
# Synchronous HTTP request (blocks thread)
response = requests.get("https://api.example.com/data")
```

**Fix:**
```python
# Async HTTP request (non-blocking)
import aiohttp
async def fetch_data():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.example.com/data") as response:
            return await response.text()
```

**Key Takeaway:**
Use async libraries (e.g., `asyncio`, `aiohttp`) or non-blocking I/O (e.g., `epoll`, `kqueue`) for I/O-bound tasks.

---

### **2. Global Locks → Fine-Grained Locks**
**Anti-Pattern (Java):**
```java
// Coarse-grained lock (blocks entire system)
private static final Object lock = new Object();
public void updateSharedState() {
    synchronized (lock) { ... } // Locks everything
}
```

**Fix:**
```java
// Per-object locks (scalable)
private final Object stateLock = new Object();
public void updateState() {
    synchronized (stateLock) { ... } // Locks only the state
}
```

**Key Takeaway:**
Replace global locks with locks scoped to the smallest possible unit of access.

---
### **3. N+1 Query Problem → Eager Loading**
**Anti-Pattern (SQL):**
```sql
-- Individual queries per row
SELECT * FROM users WHERE id = 1;
SELECT * FROM orders WHERE user_id = 1;
SELECT * FROM orders WHERE user_id = 2;
```

**Fix (Batched Query or JOIN):**
```sql
-- Single query with JOIN
SELECT u.*, o.*
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE u.id IN (1, 2);
```

**Key Takeaway:**
Use `JOIN`, `batch fetching`, or ORM eager-loading (e.g., `include` in Django) to reduce round-trips.

---
### **4. Thread Starvation → Dynamic Thread Pool**
**Anti-Pattern (Java):**
```java
// Fixed-size pool (inflexible)
ExecutorService pool = Executors.newFixedThreadPool(10);
```

**Fix:**
```java
// Dynamic pool (scales with load)
ExecutorService pool = Executors.newCachedThreadPool();
```

**Key Takeaway:**
Use `newCachedThreadPool` (Java) or `ThreadPoolExecutor` with adaptive sizing for variable workloads.

---
### **5. Over-Fetching → Projection**
**Anti-Pattern (API Response):**
```json
// Returns entire user object
{
  "id": 1,
  "name": "Alice",
  "email": "alice@example.com",
  "address": { ... },  // Unnecessary for this use case
  "orders": [ ... ]
}
```

**Fix:**
```json
// Returns only required fields
{
  "id": 1,
  "name": "Alice",
  "email": "alice@example.com"
}
```

**Key Takeaway:**
Design APIs to return only the data consumers need (e.g., GraphQL queries, field projection).

---

## **Related Patterns**
To mitigate throughput anti-patterns, leverage these complementary patterns:

| **Pattern**                  | **Description**                                                                                     | **When to Use**                                                                                     |
|------------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| **[Event-Driven Architecture](https://microservices.io/patterns/data/event-driven-architecture.html)** | Decouple components via events (e.g., Kafka, RabbitMQ) to avoid synchronous bottlenecks.          | High-volume asynchronous workflows (e.g., order processing).                                       |
| **[CQRS (Command Query Responsibility Segregation)](https://cqrs.files.wordpress.com/2010/11/cqrs_documents.pdf)** | Separate read and write models to optimize each path.                                               | Systems with distinct read/write patterns (e.g., analytics + transactions).                          |
| **[Bulkheading](https://martinfowler.com/bliki/BulkheadPattern.html)** | Isolate failure domains (e.g., thread pools per service) to contain cascading failures.           | Microservices with independent scalability needs.                                                   |
| **[Rate Limiting](https://github.com/uber/ratelimit)** | Control request volume to prevent overload (e.g., token bucket algorithm).                          | APIs exposed to untrusted clients (e.g., public endpoints).                                        |
| **[Caching Strategies (Cache-Aside, Write-Through)](https://martinfowler.com/eaaCatalog/cacheAside.html)** | Store frequently accessed data in memory to reduce backend load.                                   | Read-heavy workloads with consistent data.                                                         |
| **[Connection Pooling](https://www.baeldung.com/java-connection-pooling)** | Reuse database/network connections to reduce overhead.                                              | High-concurrency applications (e.g., web servers).                                                 |
| **[Pagination](https://use-the-index-luke.com/sql/limit-offset)** | Fetch data in chunks (e.g., `LIMIT 10 OFFSET 20`) to avoid memory overload.                        | Large datasets requiring incremental processing.                                                   |

---

## **Mitigation Checklist**
1. **Profile First**: Use tools like **JVM Profilers (Async Profiler)**, **APM (New Relic, Datadog)**, or **database slow queries logs** to identify bottlenecks.
2. **Concurrency**:
   - Replace global locks with fine-grained locks or `ConcurrentHashMap` (Java).
   - Use thread pools with dynamic sizing (e.g., `newCachedThreadPool`).
3. **Data Access**:
   - Optimize queries with indexes, JOINs, or batch operations.
   - Implement read replicas for scaling reads.
4. **Async I/O**:
   - Adopt async libraries (e.g., `asyncio`, `vert.x`, `Project Reactor`).
   - Avoid blocking calls in high-concurrency paths.
5. **Architecture**:
   - Decompose monolithic services into microservices.
   - Use event sourcing/CQRS for complex workflows.
6. **Monitoring**:
   - Track **throughput metrics** (e.g., requests/sec, error rates).
   - Set up **alerts for anomalies** (e.g., sudden latency spikes).

---
## **Key Takeaways**
- Throughput anti-patterns often emerge from **over-simplification** (e.g., global locks, synchronous I/O) or **ignorance of resource constraints** (e.g., unbounded memory).
- **Concurrency** and **data access** are the top culprits; address them with **asynchronous design**, **efficient queries**, and **proper synchronization**.
- **Architectural patterns** (CQRS, event-driven) can prevent anti-patterns before they occur.
- **Always profile** under realistic load to validate fixes. Theoretical optimizations don’t replace empirical data.

---
**Further Reading**:
- [Martin Fowler’s *Refactoring to Pattern*](https://martinfowler.com/articles/refactoring-to-patterns.html)
- *High Performance MySQL* (Baron Schwartz) – Data access anti-patterns.
- *Java Concurrency in Practice* (Brian Goetz) – Threading anti-patterns.