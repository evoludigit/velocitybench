**[Pattern] Efficiency Strategies – Reference Guide**

---

### **Overview**
The **Efficiency Strategies** pattern is a framework for optimizing performance, resource utilization, and scalability in software systems by identifying and mitigating inefficiencies. It applies across domains like database queries, computation, networking, and system design, offering structured techniques to reduce latency, memory overhead, and energy consumption. This guide outlines key strategies (e.g., caching, indexing, lazy loading) and provides implementation details, use cases, and anti-patterns to ensure sustainable optimization.

---

## **1. Key Concepts**
Efficiency Strategies revolve around **trade-offs** between development effort and performance gains. Core principles include:
- **Least-Affected Principle**: Optimize only the most critical bottlenecks.
- **Empirical Validation**: Measure baseline performance before and after changes.
- **Cost-Benefit Analysis**: Weigh trade-offs (e.g., trade memory for CPU speed).

---

## **2. Schema Reference**
| **Strategy**          | **Description**                                                                 | **Applicability**                          | **When to Apply**                                                                 |
|-----------------------|---------------------------------------------------------------------------------|--------------------------------------------|-----------------------------------------------------------------------------------|
| **Caching**           | Store frequently accessed data in faster storage layers (RAM, disk, CDN).       | Database, API responses, UI components     | High-read, low-write workloads                                                |
| **Indexing**          | Pre-organize data to speed up retrieval (e.g., B-trees, hash indexes).          | SQL databases, search engines              | Frequent queries on specific columns                                            |
| **Lazy Loading**      | Load data/resources on-demand rather than upfront.                              | Large datasets, UI rendering              | Reducing initial load time or startup latency                                   |
| **Batch Processing**  | Group operations (e.g., DB writes, API calls) to reduce overhead.               | Bulk data operations                       | High-throughput, low-latency requirements                                       |
| **Compression**       | Reduce data size (e.g., gzip, protocol buffers) to minimize I/O and bandwidth. | Network transfers, storage                 | Transmitting large payloads over networks                                       |
| **Parallelism**       | Execute tasks concurrently (multi-threading, distributed computing).             | CPU-intensive tasks, distributed systems   | Long-running, independent operations                                            |
| **Memoization**       | Cache results of expensive function calls.                                      | Repeated computations                      | Identical inputs produce identical outputs                                        |
| **Pagination**        | Split large datasets into smaller, manageable chunks.                          | API endpoints, dashboards                 | Displaying infinite scroll or large result sets                                  |
| **Offloading**        | Delegate work to specialized hardware (GPU, TPU) or external services.          | ML inference, analytics                    | Resource-intensive tasks outside primary workloads                               |

---

## **3. Implementation Details**

### **3.1. Caching**
- **Types**:
  - **Client-side**: Browser caches (e.g., Service Workers, `Cache-Control` headers).
  - **Server-side**: In-memory caches (Redis, Memcached) or database-level caching (PostgreSQL `pg_cache`).
  - **CDN Caching**: Edge caching for static assets (Cloudflare, Akamai).
- **Key Considerations**:
  - Cache invalidation: Use `ETag`/`Last-Modified` or time-based TTLs.
  - Cache wars: Avoid excessive cache misses by predicting access patterns.

**Example (Redis Cache in Node.js):**
```javascript
const redis = require('redis');
const client = redis.createClient();

async function getCachedData(key) {
  const cached = await client.get(key);
  if (cached) return JSON.parse(cached);
  const data = await fetchFromDB(key); // Expensive operation
  await client.set(key, JSON.stringify(data), 'EX', 3600); // Cache for 1 hour
  return data;
}
```

---

### **3.2. Indexing**
- **Database Indexes**:
  - Single-column: Accelerate `WHERE` clauses on `id`, `email`.
  - Composite: Optimize multi-column filters (e.g., `WHERE user_id AND status = 'active'`).
  - Full-text: Enable search (PostgreSQL `tsvector`, Elasticsearch).
- **Anti-patterns**:
  - Over-indexing slows write operations.
  - Indexing high-cardinality columns (e.g., `user_id` without constraints).

**Example (SQL CREATE INDEX):**
```sql
-- Single-column index
CREATE INDEX idx_user_email ON users(email);

-- Composite index
CREATE INDEX idx_user_status ON users(user_id, status);
```

---

### **3.3. Lazy Loading**
- **Use Cases**:
  - Infinite scroll in UIs (load more data when user scrolls).
  - On-demand image/video decoding.
- **Implementation**:
  - **Proxy Objects**: Lazy-load properties of objects.
  - **Asynchronous Initialization**: Defer heavy setup until needed.

**Example (JavaScript Proxy Lazy Loading):**
```javascript
const lazyImage = new Proxy({}, {
  get(target, prop) {
    if (prop === 'src') return 'data:image.png'; // Default
    // Load actual data when accessed
    const imgData = fetchImageData(prop);
    target[prop] = imgData;
    return imgData;
  }
});
```

---

### **3.4. Batch Processing**
- **Database**:
  - Use `INSERT ... VALUES (a, b), (c, d)` instead of multiple `INSERT` statements.
  - Batch `UPDATE`/`DELETE` with transactions.
- **APIs**:
  - Aggregate multiple requests into one (e.g., Stripe’s `ListCustomers` batching).

**Example (SQL Batch Insert):**
```sql
INSERT INTO transactions (user_id, amount, timestamp)
VALUES
  ('123', 100, NOW()),
  ('123', 50, NOW()),
  ('456', 200, NOW());
```

---

### **3.5. Compression**
- **Protocols**:
  - HTTP: `gzip`/`brotli` for responses (via `Content-Encoding` header).
  - Databases: Columnar formats (Parquet, ORC) for analytics.
- **Libraries**:
  - Node.js: `zlib` (for gzip).
  - Python: `gzip` module.

**Example (HTTP Response Compression):**
```nginx
gzip on;
gzip_types text/plain text/css application/json;
```

---

### **3.6. Parallelism**
- **Multi-threading**: Use worker pools (e.g., Python `concurrent.futures`, Go `goroutines`).
- **Distributed**: MapReduce (Hadoop), microservices (Kubernetes Pods).

**Example (Python ThreadPoolExecutor):**
```python
from concurrent.futures import ThreadPoolExecutor

def process_data(task):
    return task * task  # Expensive computation

with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(process_data, [1, 2, 3, 4, 5]))
```

---

## **4. Query Examples**
### **4.1. Optimized Database Query (With Indexing)**
```sql
-- Bad: Full table scan
SELECT * FROM users WHERE email LIKE '%@gmail.com' ORDER BY signup_date;

-- Good: Use index on email AND add index on signup_date
CREATE INDEX idx_email ON users(email);
CREATE INDEX idx_signup ON users(signup_date);
SELECT * FROM users WHERE email LIKE '%@gmail.com' ORDER BY signup_date;
```

### **4.2. Caching API Response (Node.js with `express-cache`)**
```javascript
const express = require('express');
const cache = require('express-cache');

const app = express();
app.use(cache('5 min')); // Cache responses for 5 minutes

app.get('/products/:id', (req, res) => {
  // Simulate DB fetch
  res.json({ id: req.params.id, name: 'Widget' });
});
```

### **4.3. Lazy-Loading Images (HTML + JavaScript)**
```html
<div id="lazy-container">
  <img data-src="slow-image.jpg" class="lazy">
</div>

<script>
  document.querySelectorAll('.lazy').forEach(img => {
    img.src = img.dataset.src; // Trigger load on demand
  });
</script>
```

---

## **5. Anti-Patterns & Pitfalls**
| **Anti-pattern**          | **Risk**                                                                 | **Mitigation**                                                                 |
|---------------------------|--------------------------------------------------------------------------|--------------------------------------------------------------------------------|
| **Premature Optimization** | Over-engineering before identifying bottlenecks.                         | Profile first (e.g., `EXPLAIN ANALYZE` in SQL).                                |
| **Cache Stampede**        | Thousands of requests hit DB when cache expires simultaneously.           | Use probabilistic caching (e.g., `redis-cluster` with `WATCH` or **cache warming**). |
| **Over-Indexing**         | Bloats writes and increases storage.                                      | Drop unused indexes; monitor with `pg_stat_user_indexes`.                     |
| **Blocking I/O**          | Synchronous operations halt the event loop (e.g., `fs.readFileSync`).    | Use async I/O (`fs.readFile`) or non-blocking APIs.                            |
| **Ignoring Edge Cases**   | Optimizations fail under stress (e.g., memory limits, high concurrency). | Test with tools like **JMeter**, **Locust**, or **k6**.                       |

---

## **6. Related Patterns**
| **Pattern**               | **Connection to Efficiency Strategies**                                  | **When to Combine**                                                                 |
|---------------------------|----------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **CQRS**                  | Separates read/write paths for optimized queries (e.g., materialized views).| Use CQRS + caching for high-read workloads.                                         |
| **Event Sourcing**        | Enables batch processing and replayable optimizations.                   | Combine with lazy loading for large event logs.                                   |
| **Bulkhead Pattern**      | Isolates failures to prevent cascading slowdowns.                        | Pair with parallelism to distribute load across isolated pools.                     |
| **Observer Pattern**      | Efficiently notifies subscribers (e.g., caching invalidation).           | Use with memoization to avoid redundant computations.                                |
| **Micro-batching**        | Reduces network overhead by grouping small requests.                     | Apply to APIs with high latency due to frequent tiny calls.                         |
| **Lazy Evaluation**       | Defers computation until needed (common in functional languages).          | Implement in UI frameworks (e.g., React’s `useEffect` with dependencies).           |

---

## **7. Tools & Libraries**
| **Category**            | **Tools/Libraries**                                                                 | **Use Case**                                                                       |
|-------------------------|------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Caching**             | Redis, Memcached, Varnish, `express-cache` (Node.js)                             | In-memory caching for API responses.                                               |
| **Indexing**            | PostgreSQL (GIN, GiST), MongoDB (TTL indexes), Elasticsearch                     | Accelerate search and filtering.                                                   |
| **Lazy Loading**        | Proxy objects (JavaScript), `LazyList` (Android), `lazy-loading` (Python `functools`) | Defer resource-heavy operations.                                                    |
| **Parallelism**         | `ThreadPoolExecutor` (Python), `goroutines` (Go), `asyncio` (Python)             | Distribute CPU-bound tasks.                                                        |
| **Compression**         | `gzip` (HTTP), `zstd` (storage), Protocol Buffers (serialization)                | Reduce payload size for network/storage.                                           |
| **Monitoring**          | Prometheus, Datadog, `EXPLAIN ANALYZE` (SQL), Chrome DevTools                  | Identify bottlenecks before optimizing.                                           |

---

## **8. Best Practices**
1. **Measure Before Optimizing**: Use tools like:
   - **Databases**: `EXPLAIN ANALYZE`, `pg_stat_activity`.
   - **Network**: Wireshark, `curl -v`.
   - **CPU**: `top`, `htop`, `perf`.
2. **Start Small**: Optimize one bottleneck at a time.
3. **Document Trade-offs**: Note why a strategy was chosen (e.g., "Redis cache added to reduce DB load by 60%").
4. **Monitor Post-Optimization**: Ensure no regressions (e.g., new latency spikes).
5. **Consider the Full Stack**: Optimize the slowest layer (e.g., a slow DB query will outpace a fast frontend).

---
**Example Workflow**:
1. **Profile**: Identify `SELECT * FROM orders` as a bottleneck.
2. **Optimize**:
   - Add index on `order_id`.
   - Replace `SELECT *` with explicit columns.
3. **Cache**: Use Redis for frequent `GET /orders/{id}` calls.
4. **Validate**: Confirm 90% reduction in query time.

---
**See Also**:
- [Database Optimization Guide](https://www.postgresql.org/docs/current/using-9-5.html)
- [High-Performance Web Sites (YSlow)](https://developer.yahoo.com/performance/rules.html)