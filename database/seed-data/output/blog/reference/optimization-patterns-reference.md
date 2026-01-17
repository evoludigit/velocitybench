# **[Optimization Pattern] Reference Guide**

## **Overview**
Optimization Patterns provide structured approaches to improving performance, efficiency, and scalability in software systems, APIs, and database operations. These patterns address common bottlenecks by leveraging architectural best practices, algorithmic optimizations, caching strategies, and resource management techniques. When applied effectively, they reduce latency, minimize overhead, and enhance overall system responsiveness—critical for high-traffic applications, real-time processing, or resource-constrained environments.

Key use cases for Optimization Patterns include:
- **API & Microservices:** Reducing request-processing time, minimizing 3xx/4xx/5xx errors, and optimizing payloads.
- **Database Operations:** Limiting query execution time, reducing I/O operations, and optimizing indexing.
- **Frontend Performance:** Minimizing render-blocking resources, lazy-loading assets, and improving page-load speeds.
- **Backend Processing:** Efficiently managing CPU, memory, and network usage via load balancing, caching, and parallel processing.
- **Data Processing Pipelines:** Optimizing batch jobs, stream processing, and data transformations to meet SLAs (Service-Level Agreements).

This guide covers core optimization patterns, their implementation details, schema references, and practical examples using SQL, REST, and application-level optimizations.

---

## **Schema Reference**
Below are common pattern categories with their key components.

| **Pattern Category**       | **Key Components**                                                                 | **Interaction**                                                                 |
|----------------------------|------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Caching**                | Cache expiry (`TTL`), cache keys, cache invalidation strategies, cache schemas    | Reduce repeated computations by storing results of expensive operations.         |
| **Pagination**             | `limit`/`offset` (SQL), `cursor-based pagination`, `key-based pagination`        | Fetch subsets of data to improve query performance and reduce payload size.     |
| **Query Optimization**     | Indexes (`B-tree`, `hash`), query rewrites, `SELECT` optimization, `JOIN` strategies | Minimize full-table scans and leverage database optimizations.                  |
| **Parallel Processing**    | Task partitioning, `map-reduce`, `worker pools`                                    | Distribute workloads across multiple threads/cores for faster execution.         |
| **Load Balancing**         | Round-robin, least connections, `consistent hashing`                              | Distribute traffic evenly to prevent single points of failure.                   |
| **Lazy Loading**           | On-demand resource loading (images, scripts, data)                                | Improve perceived performance by deferring non-critical loads.                 |
| **Compression**            | `gzip`, `Broti`, `Zstandard` for payloads                                         | Reduce network transfer size and bandwidth usage.                              |
| **Connection Pooling**     | Reusable DB/API connections, timeouts, max connections                            | Reuse connections to avoid overhead of establishing new ones repeatedly.        |
| **Asynchronous Processing**| Background jobs, `event-driven` processing, `async/await`                          | Handle long-running tasks without blocking user requests.                       |
| **Data Sharding**          | Partitioning data by key (e.g., `user_id`, `date`)                                 | Improve read/write performance by distributing data across nodes.               |

---

## **Implementation Details**

### **1. Caching Patterns**
**Purpose:** Store frequently accessed data in memory to reduce latency and database/API load.

#### **Key Strategies:**
- **Time-to-Live (TTL):** Set expiry times for cached items (e.g., `expires_in: 3600`).
- **Cache Invalidation:** Update cache when underlying data changes (e.g., `DELETE` triggers cache purge).
- **Cache Stampede Protection:** Use mutex locks or probabilistic early expiry to prevent multiple requests from recreating expired cache simultaneously.

#### **Schema Example (Redis):**
```json
{
  "cache_key": "user:123:profile",
  "value": {
    "name": "Alice",
    "email": "alice@example.com",
    "last_updated": "2023-10-01T12:00:00Z"
  },
  "ttl_seconds": 3600,
  "metadata": {
    "version": "v1",
    "source": "database"
  }
}
```

#### **Query Example (SQL with Caching):**
```sql
-- Check cache first (pseudo-code)
SELECT * FROM cache WHERE key = 'user:123'
IF NOT FOUND:
  -- Fallback to database
  SELECT * FROM users WHERE id = 123
  -- Store result in cache
  INSERT INTO cache (key, value, ttl) VALUES ('user:123', ..., 3600)
```

---

### **2. Pagination Patterns**
**Purpose:** Fetch data in smaller chunks to avoid overwhelming clients or databases.

#### **Key Strategies:**
- **Offset-Limit (SQL):** Simple but inefficient for large datasets.
  ```sql
  SELECT * FROM products LIMIT 10 OFFSET 20;
  ```
- **Cursor-Based Pagination:** Use a unique identifier (e.g., `last_seen_id`) to fetch next batch.
  ```sql
  SELECT * FROM orders WHERE id > '12345' ORDER BY id LIMIT 10;
  ```
- **Key-Based Pagination:** Use a sorted column (e.g., `created_at`) for temporal data.

#### **API Example (REST):**
```http
GET /api/products?page=2&per_page=10
GET /api/orders?last_id=12345
```

---

### **3. Query Optimization**
**Purpose:** Reduce query execution time by leveraging indexes and efficient SQL patterns.

#### **Key Strategies:**
- **Index Selection:** Use `EXPLAIN` to analyze query plans.
  ```sql
  EXPLAIN SELECT * FROM users WHERE email = 'user@example.com';
  ```
- **Avoid `SELECT *`:** Fetch only required columns.
  ```sql
  SELECT id, name FROM users; -- Instead of SELECT *
  ```
- **Denormalize Judiciously:** Store aggregated data to avoid expensive `JOIN`s.

#### **Schema Example (Optimized Table):**
```sql
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_orders_user_id ON orders(user_id);
```

---

### **4. Parallel Processing**
**Purpose:** Speed up tasks by distributing workloads across multiple workers.

#### **Key Strategies:**
- **Task Partitioning:** Split data into chunks (e.g., process 1000 records per worker).
- **Worker Pools:** Use libraries like `asyncio` (Python), `ExecutorService` (Java), or Kubernetes pods.

#### **Example (Python):**
```python
from concurrent.futures import ThreadPoolExecutor

def process_chunk(chunk):
    # Process a chunk of data
    return sum(chunk)

with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(process_chunk, data_chunks))
```

---

### **5. Load Balancing**
**Purpose:** Distribute traffic to prevent overload on a single instance.

#### **Key Strategies:**
- **Round-Robin:** Rotate requests evenly across servers.
- **Least Connections:** Send requests to the server with the fewest active connections.
- **Consistent Hashing:** Map requests to servers based on a key (e.g., `user_id`).

#### **Schema Example (Load Balancer Config):**
```json
{
  "servers": [
    { "host": "db1.example.com", "weight": 2 },
    { "host": "db2.example.com", "weight": 1 }
  ],
  "strategy": "least_connections",
  "timeout_ms": 5000
}
```

---

## **Query Examples**

### **1. Optimized Database Query (SQL)**
**Before (Slow):**
```sql
SELECT * FROM large_table WHERE date_column BETWEEN '2023-01-01' AND '2023-12-31';
```
**After (Optimized):**
```sql
-- Add index
CREATE INDEX idx_large_table_date ON large_table(date_column);

-- Use parameterized query
SELECT id, processed_data FROM large_table
WHERE date_column BETWEEN ? AND ?
LIMIT 1000;
```

### **2. Caching with API Requests**
**Before (Repeated DB Calls):**
```http
GET /api/users/123
GET /api/users/123
GET /api/users/123
```
**After (Cached Response):**
```http
-- First request (cache miss)
GET /api/users/123
Response: { "data": { ... }, "cache-hit": false }

-- Subsequent requests (cache hit)
GET /api/users/123
Response: { "data": { ... }, "cache-hit": true }
```

### **3. Lazy Loading in Frontend**
**Before (Block UI):**
```html
<script src="analytics.js"></script>
<link rel="stylesheet" href="styles.css">
<img src="large-image.jpg">
```
**After (Lazy Load):**
```html
<!-- Load scripts asynchronously -->
<script src="analytics.js" defer></script>
<!-- Dynamically load images -->
<img src="large-image.jpg" loading="lazy">
```

---

## **Related Patterns**
| **Pattern**                     | **Description**                                                                 | **When to Use**                                  |
|----------------------------------|---------------------------------------------------------------------------------|--------------------------------------------------|
| **[Reactive Programming]**       | Handle data streams asynchronously with event-driven architectures.            | Real-time systems (e.g., chat apps, IoT).        |
| **[Rate Limiting]**              | Throttle requests to prevent abuse or resource exhaustion.                     | Public APIs, microservices with high traffic.   |
| **[Microservices Decomposition]**| Break monolithic apps into smaller, independent services.                     | Scaling large applications.                     |
| **[Event Sourcing]**             | Store state changes as a sequence of events instead of snapshots.              | Audit trails, complex business logic.            |
| **[CDN Caching]**                | Distribute static assets globally to reduce latency.                          | High-traffic websites, media-rich applications.   |
| **[Database Sharding]**          | Split data across multiple servers for horizontal scaling.                     | Very large datasets (e.g., social media platforms).|

---

## **Best Practices**
1. **Measure Before Optimizing:** Use profiling tools (e.g., `EXPLAIN` in SQL, browser DevTools) to identify bottlenecks.
2. **Profile Guiltlessly:** Avoid premature optimization; focus on actual performance issues.
3. **Tradeoffs:** Balance readability, maintainability, and performance (e.g., caching adds complexity).
4. **Monitor:** Use APM (Application Performance Monitoring) tools to track optimization effectiveness.
5. **Test Edge Cases:** Ensure optimizations don’t break error handling or edge cases (e.g., cache storms).

---
**See Also:**
- [Database Optimization Patterns (DZone)](https://dzone.com/articles/database-optimization-patterns)
- [High-Performance Websites (Google Developers)](https://developers.google.com/web/fundamentals/performance)
- [12-Factor App (Heroku)](https://12factor.net/) (For scalable, optimized app architectures).