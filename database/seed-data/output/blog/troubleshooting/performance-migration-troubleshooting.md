# **Debugging Performance Migration: A Troubleshooting Guide**

## **Introduction**
The **Performance Migration** pattern is used to gradually optimize performance by migrating critical operations from slow to faster components (e.g., moving database queries to a cache, shifting heavy computations to a microservice, or optimizing synchronous calls to asynchronous ones). While this approach improves scalability and responsiveness, misconfigurations, race conditions, or improper rollout strategies can introduce performance degradation, errors, or cascading failures.

This guide provides a structured approach to diagnosing and resolving issues when implementing Performance Migration.

---

## **1. Symptom Checklist**
Before diving into fixes, identify which symptoms match your problem:

| **Symptom** | **Likely Cause** |
|-------------|----------------|
| **Increased latency** after migration | Slow fallback mechanism, caching layer misconfiguration, or throttling issues |
| **Timeouts or 5xx errors** | Insufficient retries, deadlocks, or improper circuit breakers |
| **Degraded throughput** | Resource contention (CPU, memory, I/O) in the new system |
| **Unexpected spikes in database load** | Cache bypasses, stale invalidation policies, or missing query optimizations |
| **Inconsistent results** | Race conditions between old and new components |
| **High memory usage** | Leaky cache (e.g., Redis, Memcached) or unoptimized data structures |
| **Failed health checks** | Misconfigured readiness probes or missing graceful degradation |

If multiple symptoms appear, prioritize based on **impact** (e.g., errors > latency > memory).

---

## **2. Common Issues and Fixes**

### **Issue 1: Slow Fallback Mechanism (Latency Spikes)**
**Symptom:** After migrating a feature, requests fall back to the old system but are significantly slower.

**Root Cause:**
- The fallback path (e.g., direct DB query instead of cached response) is unoptimized.
- Throttling is disabled, causing overload on the legacy system.

**Debugging Steps:**
1. **Verify Fallback Path:**
   ```sql
   -- Check query performance in the legacy DB
   EXPLAIN ANALYZE SELECT * FROM users WHERE id = 123;
   ```
   - If the query is slow, consider denormalizing data or adding indexes.

2. **Enable Throttling (if applicable):**
   ```java
   // Example: Rate-limiting fallback requests
   public String getUser(int id) {
       RateLimiter rateLimiter = RateLimiter.create(10.0); // 10 requests/sec
       if (!rateLimiter.tryAcquire()) {
           throw new TooManyRequestsException("Throttled fallback");
       }
       return databaseService.getUser(id); // Slow DB call
   }
   ```

3. **Logging & Monitoring:**
   ```bash
   # Check fallback request rates (Prometheus/Grafana)
   sum(rate(http_requests_total{path=~"/api/user.*"}[5m]))
   ```
   - If > 80% of requests hit the fallback, the migration isn’t ready.

---

### **Issue 2: Cache Invalidation Too Aggressive/Too Lenient**
**Symptom:** Either stale data or excessive cache misses.

**Root Cause:**
- **Too aggressive:** Cache evicts valid data too soon (e.g., `TTL=1s` for a rarely changing dataset).
- **Too lenient:** Cache never invalidates (e.g., `TTL=infinity`), leading to stale reads.

**Debugging Steps:**
1. **Check Cache Hit/Miss Ratio:**
   ```bash
   # Redis CLI
   INFO stats | grep "keyspace_hits"
   ```
   - If hits < 70%, the cache is too small or invalidation is broken.

2. **Fix Invalidations:**
   ```python
   # Example: Proper cache invalidation on write
   def update_user(user_id, data):
       db.update(user_id, data)  # Write to DB
       cache.delete(f"user:{user_id}")  # Invalidate cache
       cache.set(f"user:{user_id}", data, expire=3600)  # Set new entry
   ```

3. **Use Cache-Aside with Stale-While-Revalidate:**
   ```java
   // Spring Cache + @CacheEvict with condition
   @Cacheable(value = "users", key = "#id")
   public User getUser(int id) {
       return userRepository.findById(id);
   }

   @CacheEvict(value = "users", key = "#id", beforeInvocation = true)
   public void updateUser(User user) {
       // Update DB first, then evict cache
   }
   ```

---

### **Issue 3: Race Conditions Between Old & New Systems**
**Symptom:** Inconsistent data due to concurrent reads/writes.

**Root Cause:**
- Partial migration (e.g., some services still use the old API while others use the new one).
- Lack of distributed locks.

**Debugging Steps:**
1. **Check for Concurrent Modifications:**
   ```sql
   -- Find conflicting transactions
   SELECT * FROM pg_locks WHERE relation ~ 'users' ORDER BY locktype;
   ```

2. **Implement Distributed Locking:**
   ```java
   // Using Redis for optimistic concurrency
   public boolean updateUser(User user) {
       String lockKey = "user_lock:" + user.getId();
       Boolean locked = redisson.getLock(lockKey).tryLock(0, 5, TimeUnit.SECONDS);
       try {
           if (locked) {
               // Safe to update
               userRepository.save(user);
           } else {
               throw new OptimisticLockException("Conflict detected");
           }
       } finally {
           locked.ifPresent(lock -> lock.unlock());
       }
   }
   ```

3. **Use Saga Pattern for Distributed Transactions:**
   ```mermaid
   sequenceDiagram
     Participant A as Service A
     Participant B as Service B
     A->>B: Send update request
     B->>B: Execute locally (optimistic lock)
     B-->>A: Acknowledge
     Note over A,B: If conflict, retry or fallback
   ```

---

### **Issue 4: Resource Exhaustion (CPU/Memory)**
**Symptom:** High CPU/memory usage in the migrated service.

**Root Cause:**
- Unoptimized algorithms (e.g., O(n²) loop in a hot path).
- Memory leaks (e.g., unclosed connections).
- Too many concurrent requests (no backpressure).

**Debugging Steps:**
1. **Profile CPU Usage:**
   ```bash
   # Flame graph analysis (Linux)
   perf record -g -- python app.py
   flamegraph.pl perf.data > cpu.flame.svg
   ```
   - Look for hot methods (e.g., `sort()`, `join()`).

2. **Fix Memory Leaks:**
   ```python
   # Example: Close DB connections
   def get_user(user_id):
       conn = database.connect()
       try:
           cursor = conn.cursor()
           cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
           return cursor.fetchone()
       finally:
           cursor.close()  # Ensure cleanup
   ```

3. **Implement Backpressure:**
   ```go
   // Go: Use semaphores to limit concurrency
   var sem = make(chan struct{}, 20) // Max 20 concurrent requests
   func handleRequest(w http.ResponseWriter, r *http.Request) {
       sem <- struct{}{} // Wait for slot
       defer func() { <-sem }() // Release slot
       // Process request
   }
   ```

---

### **Issue 5: Database Overload (Cache Bypass)**
**Symptom:** DB query load increases after migration.

**Root Cause:**
- Cache is too small (high miss rate).
- Missing `SELECT FOR UPDATE` locks causing contention.
- No query optimization (e.g., missing indexes).

**Debugging Steps:**
1. **Check DB Query Plans:**
   ```sql
   EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = 42;
   ```
   - If using `Seq Scan` instead of `Index Scan`, add an index:
     ```sql
     CREATE INDEX idx_orders_user_id ON orders(user_id);
     ```

2. **Enable Slow Query Log:**
   ```ini
   # my.cnf (MySQL)
   slow_query_log = 1
   slow_query_log_file = /var/log/mysql/slow.log
   long_query_time = 1
   ```
   - Review `slow.log` for expensive queries.

3. **Use Read Replicas for Reads:**
   ```yaml
   # Django settings.py
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': 'primary',
           'USER': 'admin',
       },
       'replica': {  # For read-heavy queries
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': 'replica',
           'USER': 'ro_user',
           'OPTIONS': {'READ_ONLY': True},
       }
   }
   ```

---

## **3. Debugging Tools & Techniques**
| **Tool** | **Purpose** | **Command/Usage** |
|----------|------------|-------------------|
| **Prometheus + Grafana** | Metrics (latency, error rates, cache hits) | `http_request_duration_seconds:histogram{quantile="0.95"}` |
| **Redis Insight** | Cache analysis (memory, evictions) | `redis-cli --stat` |
| **JVM Flight Recorder** | Java heap/metrospace analysis | `jcmd <pid> JFR.start duration=60s filename=prof.jfr` |
| **k6** | Load testing new vs. old endpoints | `k6 run --vus 100 -d 30m script.js` |
| **Traceroute/ping** | Network latency issues | `traceroute api.example.com` |
| **PostgreSQL pgBadger** | Query optimization | `pgbadger /var/log/postgresql/postgresql.log` |
| **Chaos Engineering (Gremlin)** | Test resilience under load | Simulate node failures |

**Key Metrics to Monitor:**
- **Cache:** Hit ratio, eviction rate, memory usage.
- **Database:** QPS, lock contention, slow queries.
- **Application:** Error rates, latency percentiles (P99), throughput.
- **System:** CPU/memory usage, GC pauses (Java).

---

## **4. Prevention Strategies**
To avoid Performance Migration pitfalls in the future:

### **Pre-Migration Checklist**
✅ **Benchmark Both Systems:**
   ```bash
   # Compare old vs. new endpoint latency
   ab -n 1000 -c 50 http://old-api/users/1
   ab -n 1000 -c 50 http://new-api/users/1
   ```
   - Ensure new system handles **at least** the same load.

✅ **Feature Toggle Rollout:**
   ```java
   // Gradual rollout with feature flags
   @Configuration
   public class PerformanceMigrationConfig {
       @Bean
       public UserService userService(FeatureFlagService flagService) {
           if (flagService.isEnabled("PERFORMANCE_MIGRATION")) {
               return new NewUserService(); // Optimized
           } else {
               return new LegacyUserService(); // Fallback
           }
       }
   }
   ```

✅ **Canary Testing:**
   - Route **5% of traffic** to the new system first.
   - Monitor errors and latency spikes.

✅ **Automated Rollback Plan:**
   - Use **circuit breakers** (e.g., Hystrix, Resilience4j) to fallback gracefully.
   - Example:
     ```java
     @CircuitBreaker(name = "userService", fallbackMethod = "fallbackGetUser")
     public User getUser(int id) {
         return newUserService.getUser(id);
     }
     ```

### **Post-Migration Best Practices**
🔹 **Monitor Cache Invalidation:**
   - Use **TTL + stale reads** (e.g., Redis `GET` + `INCR` for versioning).
   - Example:
     ```python
     cache.set("user:1", data, px=3600)  # 1-hour TTL
     ```

🔹 **Optimize Database Queries:**
   - Avoid `SELECT *`; use **projections**.
   - Example:
     ```sql
     -- Bad
     SELECT * FROM users WHERE id = 1;

     -- Good
     SELECT id, name, email FROM users WHERE id = 1;
     ```

🔹 **Implement Dead Letter Queues (DLQ):**
   - For async tasks that fail repeatedly.
   ```java
   // Spring Kafka DLQ
   @KafkaListener(topics = "user-events", groupId = "migration-group")
   public void listenGroup(ListenerContainerFactory<KafkaListenerContainer<?, ?>> factory) {
       factory.setErrorHandler(new DeadLetterPublishingRecoverer(new TopicPartitions("user-events-dlq")));
   }
   ```

🔹 **Document Rollback Steps:**
   - Keep a **runbook** for reverting changes (e.g., switch back to legacy DB).

---

## **5. Conclusion**
Performance Migration is a powerful optimization technique, but it introduces complexity. The key to troubleshooting is:
1. **Isolate symptoms** (latency? errors? resource leaks?).
2. **Use metrics** (Prometheus, Redis Insight) to diagnose root causes.
3. **Test incrementally** (canary deployments, feature flags).
4. **Prevent regressions** with benchmarks, circuit breakers, and automated rollbacks.

**Final Checklist Before Going Live:**
- [ ] Cache hit ratio > 70% under production load.
- [ ] Database queries optimized (`EXPLAIN ANALYZE` validated).
- [ ] Fallback mechanism throttled to avoid overload.
- [ ] Monitoring alerts for cache misses, errors, and latency spikes.
- [ ] Rollback plan tested (e.g., disable feature flag).

By following this guide, you can **diagnose, fix, and prevent** Performance Migration issues quickly. 🚀