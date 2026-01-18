# **[Pattern] Caching Troubleshooting Reference Guide**

## **Overview**
Caching is a critical performance optimization technique that stores frequently accessed or computationally expensive data in a fast-access layer (e.g., memory) to reduce latency and backend load. However, misconfigurations, inconsistent invalidation, or improper cache design can degrade scalability and introduce bugs. This guide provides a structured approach to diagnosing and resolving common caching issues.

Key topics covered:
- **Common caching pitfalls** and their symptoms
- **Schema-driven troubleshooting** using metadata and infrastructure logs
- **Query patterns** for identifying cache hits/misses, stale data, and bottlenecks
- **Integration with related patterns** (e.g., Circuit Breaker, Retry)

---

## **Implementation Details**

### **Key Concepts**
1. **Cache Hit/Miss Ratio**
   - **Hit**: Data retrieved from cache (low latency).
   - **Miss**: Data fetched from the primary store (higher latency).
   - *Ideal ratio*: >90% hits for optimal caching.

2. **Cache Invalidation Strategies**
   - **Time-based (TTL)**: Automatically expire entries after X seconds.
   - **Event-based**: Invalidate on writebacks (e.g., `CACHE_INVALIDATE(user:123)`).
   - **Lazy loading**: Populate cache only on first access.

3. **Cache Layers**
   - **Client-side Cache**: Browser/LocalStorage (e.g., React Query).
   - **Server-side Cache**: In-memory (Redis, Memcached) or CDN.
   - **Distributed Cache**: Multi-node synchronization (e.g., Redis Cluster).

4. **Cache Stampede**
   - Multiple requests hit the cache simultaneously after invalidation, overwhelming the backend.
   - *Mitigation*: Use **locking** (e.g., `REDIS_LOCK`) or **random backoff**.

5. **Cache Thundering**
   - A single request triggers a massive cache refill, causing spikes.

---

## **Schema Reference**
Below is a standardized schema for caching diagnostics, supported by tools like **Prometheus Metrics**, **ELK Stack**, or custom logging.

| **Field**               | **Type**   | **Description**                                                                 | **Example Values**                     |
|-------------------------|------------|---------------------------------------------------------------------------------|----------------------------------------|
| `cache_cluster`         | String     | Name of the caching tier (e.g., `redis-primary`, `client-side`).                 | `redis-cache-tier-1`                   |
| `operation`             | String     | Type of caching action (e.g., `GET`, `SET`, `INVALIDATE`).                       | `GET:userProfile_123`                  |
| `status`                | String     | Success/failure flag (`SUCCESS`, `MISS`, `STALE`, `ERROR`).                     | `MISS`                                 |
| `latency_ms`            | Double     | Time taken for cache operation.                                                 | `42.3`                                 |
| `backend_latency_ms`    | Double     | Fallback latency if cache missed.                                               | `1200.5`                               |
| `hit_count`             | Integer    | Incremented on cache hits.                                                      | `42`                                   |
| `miss_count`            | Integer    | Incremented on cache misses.                                                    | `5`                                    |
| `invalidations`         | Integer    | Number of invalidation events triggered.                                       | `3`                                    |
| `throttled_requests`    | Integer    | Count of requests blocked due to cache stampede.                               | `0`                                    |
| `cache_key`             | String     | Unique identifier for the cached item.                                           | `user_123_profile`                     |
| `timestamp`             | ISO8601    | When the event occurred.                                                        | `2024-05-20T12:34:56.123Z`            |
| `metadata`              | JSON       | Additional context (e.g., `source=API_GATEWAY`, `version=v2`).                   | `{"source":"mobile-app"}`              |

---

## **Query Examples**
### **1. Identify Cache Misses**
**Problem**: High backend load suggests excessive misses.
**Query (Prometheus)**:
```sql
sum(rate(cache_miss_total[5m])) by (cache_cluster)
```
**Expected Output**:
| `cache_cluster`       | `rate`  |
|-----------------------|---------|
| `redis-primary`       | 15.3    |
| `client-side`         | 0.1     |

**Action**: Review TTL settings or query patterns.

---

### **2. Detect Stale Data**
**Problem**: Users see outdated cache entries.
**Query (ELK Kibana)**:
```json
// Count "GET" operations with timestamp older than TTL
GET cache_operations
| stats count by (cache_key, operation)
| where operation == "GET" AND @timestamp < (currentTime() - 300s)
```
**Throttle Rule**: If `count > 10`, investigate **invalidations** or **TTL misconfigurations**.

---

### **3. Analyze Cache Stampede**
**Problem**: Sudden spikes in `backend_latency` after invalidation.
**Query (Grafana)**:
```sql
histogram_quantile(0.95, sum(rate(backend_latency_bucket[1m])) by (le))
```
**Action**: Implement **locking** (e.g., Redis `SETNX`) or **rate limiting**.

---

### **4. Correlate with Related Patterns**
**Problem**: Circuit Breaker trips alongside cache issues.
**Query (Log Correlation)**:
```sql
// Look for cache misses + Circuit Breaker opens
GET logs
| filter (status == "MISS" AND circuit_state == "OPEN")
| sort @timestamp desc
```

---

## **Troubleshooting Workflow**
### **Step 1: Verify Cache Hit Ratio**
```sql
sum(cache_hit_count) / (sum(cache_hit_count) + sum(cache_miss_count))
```
- **<80%**: Investigate query patterns or TTL.

### **Step 2: Check for Thundering**
```sql
max(backend_latency_ms) over last 5m
```
- **Spikes**: Enable **cache pre-warming** (e.g., `WRITE_THROUGH`).

### **Step 3: Validate Invalidation**
```sql
sum(invalidations) by (cache_key) | sort -desc
```
- **Zero invalidations**: Confirm event-driven triggers (e.g., database triggers).

### **Step 4: Audit Cache Keys**
```sql
cache_keys
| where length(cache_key) > 256  // Oversized keys
```
- **Long keys**: Optimize serialization (e.g., use `HashIDs`).

---

## **Related Patterns**
| **Pattern Name**               | **Relationship**                                                                 | **When to Use**                          |
|---------------------------------|---------------------------------------------------------------------------------|------------------------------------------|
| **Circuit Breaker**             | Cache misses may trigger circuit opens; use Prometheus correlation.               | High-latency services                     |
| **Retry with Backoff**         | Cache refills should retry transient failures (e.g., Redis downtime).           | Distributed systems                      |
| **Bulkheads**                  | Isolate cache-heavy operations from others using thread pools.                    | Microservices                           |
| **Bulkhead Isolation**         | Cache tier may need dedicated resources to prevent contention.                  | High-throughput APIs                   |
| **Rate Limiting**              | Throttle cache stampedes (e.g., Redis Rate Limiter).                           | Sudden traffic spikes                    |

---

## **Best Practices**
1. **Monitor**:
   - Track `hit/miss` ratios, `latency`, and `invalidations` proactively.
   - Use tools: Prometheus, Datadog, or custom metrics.

2. **Design**:
   - Avoid **over-caching** (increase complexity with minimal gains).
   - Use **layered cache** (e.g., Redis + client-side).

3. **Validate**:
   - Test invalidation workflows (e.g., `CACHE_INVALIDATE(user:1)`).
   - Simulate cache misses to verify fallbacks.

4. **Document**:
   - Maintain a **cache schema** (keys, TTLs, dependencies).
   - Example:
     ```json
     {
       "cache_key": "product_1001",
       "ttl": 300,
       "dependencies": ["inventory", "reviews"],
       "invalidation_trigger": "on_write"
     }
     ```

5. **Tooling**:
   - **Redis**: Use `INFO` command.
   - **Client-side**: Debugger (e.g., Chrome DevTools for React Query).

---
**Note**: Always correlate logs with application trace IDs for context. For distributed systems, use **distributed tracing** (e.g., Jaeger).