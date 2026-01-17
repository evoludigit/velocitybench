# **[Pattern] Optimization Techniques Reference Guide**

---
### **Overview**
Optimization Techniques is a **pattern** for systematically improving performance, efficiency, or resource utilization in applications, databases, APIs, or infrastructure. This pattern provides structured approaches to minimize latency, reduce resource consumption, and enhance scalability, ensuring systems operate at peak efficiency. Techniques apply to **query optimization, indexing, caching, load balancing, and algorithmic improvements**, making them applicable across **web applications, microservices, and data processing pipelines**.

Optimization is not a one-time task—it involves iterative testing, monitoring, and refinement. This guide outlines key strategies, implementation details, and best practices for applying optimization patterns in real-world scenarios.

---

## **Key Concepts & Implementation Details**

### **1. Core Principles**
- **Measure Before Optimizing:** Profile performance bottlenecks (CPU, memory, I/O) using tools like **JMeter, New Relic, or database profilers**.
- **Follow the 80/20 Rule:** Focus on 20% of code/query that causes 80% of issues.
- **Avoid Premature Optimization:** Optimize only when empirical data confirms a bottleneck.
- **Balance Trade-offs:** Consider trade-offs between complexity, cost, and performance gains (e.g., RAM vs. disk caching).

### **2. Optimization Categories**
| **Category**          | **Description**                                                                 | **When to Apply**                          |
|-----------------------|---------------------------------------------------------------------------------|--------------------------------------------|
| **Query Optimization** | Reduce database/query execution time via indexing, joins, and query rewrites.   | High-query-load or slow SQL queries.       |
| **Caching**           | Store frequent/expensive computation results in memory or disk.                 | Repeated API calls or database reads.      |
| **Indexing**          | Speed up data retrieval by pre-structuring data for faster searches.           | Large tables with frequent `WHERE` clauses.|
| **Load Balancing**    | Distribute traffic across multiple servers to prevent overload.                 | High-traffic applications.                |
| **Algorithm Tuning**  | Optimize custom algorithms (e.g., sorting, searching, compression).            | Custom operations with high complexity.    |
| **Memory Management** | Minimize garbage collection overhead and reduce memory leaks.                   | Long-running processes or high-memory apps. |
| **Hardware/Infrastructure** | Upgrade or reconfigure servers, use SSDs, or leverage cloud auto-scaling. | Platform-level bottlenecks detected.      |

---

## **Schema Reference**

### **1. Query Optimization Schema**
Optimize SQL queries using this schema:

| **Technique**               | **Description**                                                                 | **Example**                                  |
|-----------------------------|---------------------------------------------------------------------------------|----------------------------------------------|
| **Index Selection**         | Use indexes on frequently filtered/sorted columns (e.g., `PRIMARY KEY`, `WHERE` clauses). | `CREATE INDEX idx_user_email ON users(email);` |
| **Query Rewriting**         | Convert `SELECT *` to explicit column selection; avoid `NOT IN` or `OR`.      | `SELECT id, name FROM users WHERE status = 'active';` |
| **Join Optimization**       | Prefer `INNER JOIN` over `OUTER JOIN`; limit tables joined.                     | `SELECT * FROM users u INNER JOIN orders o ON u.id = o.user_id;` |
| **Pagination**              | Use `LIMIT/OFFSET` or keyset pagination instead of fetching all records.       | `SELECT * FROM logs ORDER BY timestamp LIMIT 10 OFFSET 50;` |
| **Denormalization**         | Store redundant data to avoid expensive joins (tradeoff: insert/update overhead). | Normalized: `users(id, name), orders(user_id, ...)`<br>Denormalized: `users(id, name, recent_order)` |

---

### **2. Caching Schema**
Cache strategies with trade-offs:

| **Caching Level**       | **Storage**       | **Use Case**                          | **Invalidation Strategy**               |
|-------------------------|-------------------|---------------------------------------|-----------------------------------------|
| **Client-Side**         | Browser/Mobile    | Reduce repeated HTTP requests.         | Cache headers (`Cache-Control: max-age`).|
| **Application-Level**   | Memory (Redis)    | Store frequent computation results.    | Time-based or event-triggered.           |
| **Database-Level**      | Query Cache       | Cache SQL results.                     | TTL (Time-To-Live) or manual flush.     |
| **CDN**                 | Edge Locations    | Serve static assets globally.          | Automatic (based on file version).       |

**Example Cache Headers:**
```http
Cache-Control: public, max-age=3600  // Cache for 1 hour
ETag: "abc123"                        //Conditional GET requests
```

---

### **3. Indexing Schema**
Database indexing guidelines:

| **Index Type**       | **Description**                                                                 | **Best For**                          |
|----------------------|---------------------------------------------------------------------------------|---------------------------------------|
| **B-Tree**           | Balanced tree; default for most databases.                                    | Equality and range queries (`=`, `>`, `<`). |
| **Hash**             | Fast lookups for exact matches (no range queries).                              | Key-value stores (e.g., Redis).       |
| **Full-Text**        | Optimized for text search (e.g., `LIKE '%term%'`).                              | Search applications.                  |
| **Composite**        | Index on multiple columns (order matters).                                     | Queries filtering on multiple columns. |
| **Covering Index**   | Index includes all columns needed for a query (avoids table lookup).           | `SELECT id, name FROM users WHERE status = 'active';` |

**When *Not* to Index:**
- Small tables (<10K rows).
- Columns with low selectivity (e.g., `gender` with only `M/F` values).
- Frequently updated columns (indexes slow down `INSERT/UPDATE`).

---

## **Query Examples**

### **1. Optimized vs. Unoptimized SQL**
**Unoptimized (Slow):**
```sql
SELECT * FROM products
WHERE category = 'Electronics'
AND (price > 100 OR discount > 0.1)
ORDER BY name;
```
**Issues:** Wildcard (`%`) in `LIKE`, no index hints, inefficient `OR`.

**Optimized:**
```sql
-- Add composite index: CREATE INDEX idx_products_cat_price ON products(category, price);
SELECT id, name, price
FROM products
WHERE category = 'Electronics' AND price > 100  -- Filter first, then OR
ORDER BY name LIMIT 100;
```

---

### **2. Caching Example (Redis)**
**Scenario:** Cache API responses for `/users/{id}` endpoint.

**Implementation:**
```python
# Set cache (TTL = 1 hour)
redis.setex(f"user:{user_id}", 3600, user_data)

# Get cached data
user_data = redis.get(f"user:{user_id}")
if user_data:
    return json.loads(user_data)  # Return cached
else:
    # Fallback to database
    user_data = db.query_user(user_id)
    redis.setex(f"user:{user_id}", 3600, user_data)
    return user_data
```

---

### **3. Load Balancing Example (Nginx)**
**Scenario:** Distribute traffic across 3 backend servers.

**Nginx Config:**
```nginx
upstream backend {
    least_conn;  # Balance by least connections
    server 192.168.1.1:3000;
    server 192.168.1.2:3000;
    server 192.168.1.3:3000 backup;  # Only used if others fail
}

server {
    listen 80;
    location / {
        proxy_pass http://backend;
    }
}
```

---

## **Algorithm Optimization Examples**
### **1. Sorting: Quickselect vs. Full Sort**
**Problem:** Find the 5th largest salary in a list.

**Unoptimized (Full Sort):**
```python
salaries = [100, 50, 200, 150, 80]
salaries.sort()  # O(n log n)
return salaries[-5]  # O(1)
```
**Optimized (Quickselect):**
```python
def quickselect(arr, k):
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x > pivot]
    right = [x for x in arr if x < pivot]
    if k <= len(left):
        return quickselect(left, k)
    elif k > len(left) + 1:
        return quickselect(right, k - len(left) - 1)
    else:
        return pivot  # Found the kth largest

quickselect(salaries, 5)  # O(n) average case
```

---

## **Monitoring & Validation**
| **Tool**               | **Purpose**                                      | **Example Command/Metric**               |
|------------------------|--------------------------------------------------|-------------------------------------------|
| **SQL Profiler**       | Analyze slow queries.                            | `EXPLAIN ANALYZE SELECT * FROM users;`   |
| **APM Tools**          | Track application performance (e.g., New Relic). | Latency percentiles (P95, P99).          |
| **Load Testers**       | Simulate traffic (e.g., JMeter, Locust).        | Throughput (requests/sec), error rate.   |
| **Cache Hit Ratio**    | Measure cache effectiveness.                     | `redis-cli --stat | grep "keyspace_hits"`                   |

---

## **Related Patterns**
1. **[Data Pipeline Optimization]**
   - Complementary: Focuses on ETL processes, batch jobs, and streaming optimizations.

2. **[Micro-Optimization]**
   - Dives deeper into low-level tweaks (e.g., bytecode optimization, JIT compilation).

3. **[Circuit Breaker]**
   - Prevents cascading failures by limiting requests to degraded services during optimization.

4. **[Fault Tolerance]**
   - Ensures systems remain resilient during optimization-induced instability.

5. **[Observability]**
   - Provides telemetry needed to validate optimization efficacy (logs, metrics, traces).

---
## **Anti-Patterns to Avoid**
- **Over-Indexing:** Too many indexes slow down `INSERT/UPDATE`.
- **Ignoring Data Skew:** Uneven data distribution can break hash-based optimizations.
- **Static Optimization:** Systems evolve; re-evaluate optimizations quarterly.
- **Silent Assumptions:** Always validate optimizations with real-world data.

---
## **Further Reading**
- **[Database Internals]** (Armando Fox) – Covers indexing and query execution.
- **[High Performance Web Sites]** (Steve Souders) – Frontend optimization strategies.
- **[Designing Data-Intensive Applications]** (Martin Kleppmann) – Scalability and partitioning.