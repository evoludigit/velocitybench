# **[Pattern] Performance Optimization – Reference Guide**

---

## **Overview**
Performance Optimization is a design pattern focused on improving system efficiency by reducing latency, minimizing resource usage, and enhancing scalability. This pattern applies across **database queries, caching, code optimization, and infrastructure tuning** to ensure applications respond quickly under load while maintaining reliability. Key strategies include **indexing, query restructuring, lazy loading, and caching mechanisms**, all tailored to specific use cases (e.g., read-heavy vs. write-heavy workloads). By applying these techniques systematically, developers can achieve **substantial speed gains (e.g., 10x–100x reduction in query time)** without compromising correctness or maintainability.

---

## **1. Key Concepts**
| **Concept**               | **Description**                                                                 | **When to Use**                                                                 |
|---------------------------|---------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Caching**               | Stores frequently accessed data in memory (e.g., Redis, Memcached) to avoid repeated computations or database hits. | High-read, low-write scenarios; repetitive queries or expensive computations. |
| **Indexing**              | Optimizes database queries by creating structures (B-tree, hash) for faster lookups. | High-volume search or filtering operations.                                  |
| **Query Optimization**    | Restructures SQL/NoSQL queries to reduce execution time (e.g., avoiding `SELECT *`, using `JOIN` sparingly). | Slow-performing or complex queries.                                            |
| **Pagination**            | Limits data fetched per request (e.g., `LIMIT/OFFSET`, cursor-based pagination). | Large datasets where full retrieval is impractical.                           |
| **Lazy Loading**          | Loads data only when needed (e.g., deferred joins, graph traversal).           | Applications with sparse access patterns.                                     |
| **Connection Pooling**    | Reuses database connections to reduce overhead.                                | High-concurrency applications.                                                 |
| **Asynchronous Processing** | Offloads tasks to background workers (e.g., queues like RabbitMQ, Celery).    | Long-running or CPU-intensive tasks.                                           |
| **Compression**           | Reduces data size for transfer/storage (e.g., gzip, Protocol Buffers).         | Bandwidth-constrained or storage-limited environments.                         |
| **Load Balancing**        | Distributes traffic across multiple servers to prevent bottlenecks.            | High-traffic applications with horizontal scalability.                        |
| **Gzip Compression**      | Compresses response payloads to minimize network transfer.                     | Web APIs or static content delivery.                                           |

---

## **2. Schema Reference**
Below are structural optimizations for common systems. Adjust based on your database (e.g., PostgreSQL, MongoDB).

### **2.1 Database Schema Optimizations**
| **Optimization**          | **PostgreSQL Example**                                                                 | **MongoDB Example**                                                                 |
|---------------------------|---------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Indexing**              | `CREATE INDEX idx_user_email ON users(email);`                                         | `db.users.createIndex({ email: 1 })`                                                 |
| **Partial Indexing**      | `CREATE INDEX idx_active_users ON users(status) WHERE status = 'active';`              | `db.users.createIndex({ status: 1 }, { partialFilterExpression: { status: "active" } })` |
| **Covering Index**        | `CREATE INDEX idx_name_age ON users(name, age);` (avoids table lookup for `WHERE`).   | `db.users.createIndex({ name: 1, age: 1 })` (for `SELECT name, age`).               |
| **Composite Index**       | `CREATE INDEX idx_name_dept ON users(last_name, department);`                        | `db.users.createIndex({ last_name: 1, department: 1 })`                           |
| **Full-Text Search**      | `CREATE EXTENSION pg_trgm; CREATE INDEX idx_search ON articles USING gin(trgm_ops);`  | `db.articles.createIndex({ content: "text" })`                                     |

---

### **2.2 Application-Level Optimizations**
| **Optimization**          | **Implementation**                                                                                     | **Tools/Technologies**                                                                 |
|---------------------------|-------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------|
| **Redis Caching**         | Store query results with a TTL (e.g., `SET user:123:profile { ... } EX 300`; fetch from Redis first). | Redis, Memcached                                                                       |
| **CDN Caching**           | Cache static assets (images, JS/CSS) at the edge (e.g., Cloudflare, Fastly).                          | Cloudflare Worker, AWS CloudFront                                                      |
| **Query Batch Processing**| Combine multiple small queries into one (e.g., `BulkWrite` in MongoDB).                               | MongoDB Bulk Operations, PostgreSQL `COPY`                                              |
| **Connection Pooling**    | Limit active connections (e.g., `pgbouncer` for PostgreSQL).                                           | PgBouncer, HikariCP (Java), `pooling=True` (Python `psycopg2`)                         |
| **Compression**           | Enable gzip for HTTP responses (`Content-Encoding: gzip`).                                             | Nginx, Apache, Express.js (middleware)                                                 |
| **Lazy Loading**          | Use `SELECT * FROM users WHERE id = ?` + separate queries for related data (e.g., orders).         | Database joins (avoid `N+1`), DTOs (Data Transfer Objects)                             |
| **Asynchronous Tasks**    | Offload heavy tasks (e.g., image resizing) to a queue (e.g., Celery).                                | RabbitMQ, AWS SQS, Celery                                                               |

---

## **3. Query Optimization Examples**
### **3.1 PostgreSQL**
**Before (Slow):**
```sql
SELECT u.*, o.*
FROM users u
JOIN orders o ON u.id = o.user_id
WHERE u.status = 'active'
ORDER BY o.created_at DESC;
```
**After (Optimized):**
```sql
-- Add composite index: CREATE INDEX idx_user_status_orders ON users(id, status) WHERE status = 'active';
-- Fetch only needed columns:
SELECT u.id, u.name, o.order_id, o.amount
FROM users u
JOIN orders o ON u.id = o.user_id
WHERE u.status = 'active'
ORDER BY o.created_at DESC
LIMIT 100;
```

**Pagination (Offset vs. Cursor):**
```sql
-- Offset (inefficient for large datasets)
SELECT * FROM posts OFFSET 1000 LIMIT 10;

-- Cursor (better for deep pagination)
SELECT * FROM posts WHERE id > '1000' ORDER BY id LIMIT 10;
```

---

### **3.2 MongoDB**
**Before (Slow):**
```javascript
// Fetch all users and their orders (N+1 problem)
db.users.find().forEach(user => {
  db.orders.find({ user_id: user._id });
});
```
**After (Optimized):**
```javascript
// Use $lookup for one-time join (avoids N+1):
db.users.aggregate([
  { $lookup: {
      from: "orders",
      localField: "_id",
      foreignField: "user_id",
      as: "orders"
    }
  },
  { $match: { status: "active" } },
  { $limit: 100 }
]);
```

**Text Search:**
```javascript
// Create index: db.posts.createIndex({ content: "text" });
db.posts.find({
  $text: { $search: '"performance optimization"' },
  $limit: 20
});
```

---

### **3.3 Caching Strategies**
**Redis (Key-Value Caching):**
```bash
# Cache query results for 5 minutes
SET user:123:profile '{"name": "Alice", "email": "alice@example.com"}' EX 300
```
**Cache-Aside Pattern (Pseudocode):**
```python
def get_user_profile(user_id):
    cache_key = f"user:{user_id}:profile"
    profile = cache.get(cache_key)
    if profile is None:
        profile = db.users.find_one({"id": user_id})
        cache.set(cache_key, profile, ex=300)  # Cache for 5 mins
    return profile
```

**Distributed Cache (Multi-Region):**
Use **Redis Cluster** or **Memcached** with sharding for horizontal scalability.

---

## **4. Benchmarking & Validation**
### **4.1 Tools for Measurement**
| **Tool**               | **Purpose**                                                                 |
|------------------------|-----------------------------------------------------------------------------|
| `EXPLAIN ANALYZE`      | PostgreSQL query performance analysis.                                       |
| MongoDB `explain()`    | Analyzes query execution plans.                                             |
| `ab` (ApacheBench)    | HTTP load testing (requests per second, response time).                     |
| `k6`                   | Advanced load testing with custom scripts.                                  |
| `New Relic`/`Datadog`  | APM (Application Performance Monitoring) for real-time metrics.              |

### **4.2 Example: Query Timeline**
```
Before Optimization:
- Query: 500ms (slow due to full table scan)
- Network: 200ms (serialized JSON response)

After Optimization:
- Cache hit: 1ms (Redis)
- Query: 5ms (indexed join)
- Network: 50ms (compressed response)
Total: ~10ms (98% improvement)
```

---

## **5. Trade-offs & Considerations**
| **Optimization**        | **Pros**                                  | **Cons**                                                                 |
|-------------------------|-------------------------------------------|-------------------------------------------------------------------------|
| **Indexing**            | Faster queries                           | Higher write overhead; storage cost.                                      |
| **Caching**             | Reduces database load                    | Stale data risk; cache invalidation needed.                              |
| **Lazy Loading**        | Memory efficiency                        | N+1 query problem if overused.                                           |
| **Asynchronous Tasks**  | Non-blocking UI                           | Complex error handling; eventual consistency.                            |
| **Compression**         | Lower bandwidth                          | CPU overhead for decompression.                                          |

---

## **6. Anti-Patterns to Avoid**
1. **Over-Indexing**: Adding indexes without measuring impact can slow down writes.
2. **Cache Stampede**: Thousands of requests hit the database when cache is empty.
   *Fix*: Use **cache warming** (pre-load data) or **locking** (e.g., Redis `SETNX`).
3. **Unbounded Pagination**: `OFFSET 1000000` scans millions of rows (use cursors instead).
4. **Ignoring Query Plans**: Blindly adding indexes without checking `EXPLAIN`.
5. **Over-Asynchronization**: Queueing every task can create cascading delays.

---

## **7. Related Patterns**
| **Pattern**                     | **Connection to Performance Optimization**                                                                 |
|----------------------------------|-----------------------------------------------------------------------------------------------------------|
| **[Repository Pattern]**         | Centralizes data access; apply caching/lazy loading here.                                                 |
| **[CQRS]**                       | Separates read/write models; optimize read paths with caching.                                            |
| **[Event Sourcing]**             | Enables efficient audit logs and replay; reduce load on primary DB.                                      |
| **[Microservices]**              | Isolate performance bottlenecks; optimize services independently.                                       |
| **[Circuit Breaker]**            | Prevents cascading failures in distributed systems (e.g., fallback to cache).                          |
| **[Bulkhead Pattern]**           | Limits resource contention; improves throughput under load.                                               |
| **[Rate Limiting]**              | Prevents abuse; optimizes system stability.                                                              |

---

## **8. Further Reading**
- **Books**:
  - *Database Performance Tuning* (Markus Winand)
  - *High Performance MySQL* (Baron Schwartz)
- **Articles**:
  - [PostgreSQL Indexing Guide](https://use-the-index-luke.com/)
  - [MongoDB Performance Best Practices](https://www.mongodb.com/docs/manual/)
- **Tools**:
  - [Redis Benchmarking](https://redis.io/topics/benchmarks)
  - [SQL Performance Explorer](https://github.com/sqlite/sqlite-browser) (for SQLite)

---
**Note**: Always validate optimizations with real-world data and load tests. Benchmark changes incrementally to isolate impacts.