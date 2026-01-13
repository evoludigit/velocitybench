# **Debugging Execution Plan Caching: A Troubleshooting Guide**

## **Introduction**
Execution Plan Caching is a pattern used to optimize performance in query engines, compilers, and caching systems by reusing pre-computed execution plans for recurring operations. When implemented correctly, it reduces redundant planning overhead, improves execution speed, and minimizes CPU waste. However, misconfigurations, cache invalidation issues, or improper plan storage can degrade performance.

This guide provides a structured approach to diagnosing and resolving common issues with **Execution Plan Caching**.

---

## **1. Symptom Checklist**
Before diving into deep debugging, verify whether Execution Plan Caching is the root cause. Check for the following symptoms:

| **Symptom** | **Possible Cause** | **Quick Check** |
|-------------|-------------------|----------------|
| **Variable execution time** (some requests are slow, others fast) | Cache misses due to incorrect invalidation | Monitor cache hit/miss ratios |
| **High CPU usage during query planning** | Plans are recomputed frequently | Check profiling data for `PlanCompiler` or `QueryOptimizer` metrics |
| **Unexpected slowdowns after schema changes** | Stale cached plans | Verify cache invalidation triggers |
| **Memory spikes due to cached plans** | Too many plans stored | Inspect memory usage of cache structures |
| **Different plans for identical queries** | Divergent parsing or optimization paths | Log and compare execution plans |

---

## **2. Common Issues & Fixes**

### **Issue 1: Cache Misses Due to Ineffective Invalidation**
**Symptoms:**
- Plans become stale after schema changes (e.g., table updates, column renames).
- Repeated planning occurs even for unchanged queries.

**Root Cause:**
- The cache does not invalidate plans on schema changes.
- Cache keys are not generated correctly (e.g., missing table metadata in the key).

**Fix:**
Ensure cache keys include **schema dependencies** (e.g., table schemas, function definitions). Example in a pseudocode query engine:

```python
def generate_cache_key(query: str, schema_hash: str) -> str:
    return f"{query}_{schema_hash}"  # Schema hash ensures invalidation

def on_schema_change(table_name: str):
    cache.invalidate(api=f"schema_{table_name}")  # Invalidate relevant plans
```

**Debugging Steps:**
1. **Log cache keys** for repeated queries.
2. **Compare schema hashes** before/after changes.
3. **Check invalidation triggers** (e.g., `ON_SCHEMA_CHANGE` hooks).

---

### **Issue 2: Cache Throttling Due to Too Many Plans**
**Symptoms:**
- Memory usage grows uncontrollably.
- Cache eviction strategy fails to free space.

**Root Cause:**
- A **LRU (Least Recently Used) cache** grows indefinitely.
- No **TTL (Time-To-Live)** is set, causing indefinite storage.

**Fix:**
- **Limit cache size** (e.g., `maxsize=1000` in Python’s `LRUCache`).
- **Set TTL** for plans (e.g., expire after 5 minutes of inactivity).

```python
# Example: LRU Cache with TTL (using `cachetools`)
from cachetools import TTLCache

plan_cache = TTLCache(maxsize=1000, ttl=300)  # 5-minute expiry
```

**Debugging Steps:**
1. **Profile memory usage** (`top`, `htop`, or `ps aux`).
2. **Monitor cache size** (e.g., `len(cache)` in Python).
3. **Check eviction policy** (is it working as expected?).

---

### **Issue 3: Plan Variation Due to Dynamic Query Interpretation**
**Symptoms:**
- Identical queries generate different execution plans.
- No clear caching benefit.

**Root Cause:**
- **Query rewriting** (e.g., CBO, predicate pushdown) modifies the plan.
- **Session-specific settings** (e.g., `SET` clauses) affect planning.

**Fix:**
- **Normalize queries** before caching (e.g., canonicalize `SELECT *` vs. explicit column lists).
- **Include session context** in cache keys.

```sql
-- Example: Normalize queries before caching
IF query =~ '^SELECT .* FROM table WHERE .*$'
    THEN store_normalized_version(query)  -- Store without session settings
```

**Debugging Steps:**
1. **Log raw vs. normalized queries**.
2. **Check for session-specific optimizations** (e.g., `EXPLAIN ANALYZE` differences).
3. **Compare `EXPLAIN` output** for identical queries.

---

### **Issue 4: Race Conditions in Concurrent Plan Reuse**
**Symptoms:**
- **Segfaults** or **corrupted plans** under high concurrency.
- **Plan inconsistency** (e.g., one thread overrides another’s cached plan).

**Root Cause:**
- **Unsynchronized cache access** in multi-threaded environments.
- **Dirty reads** of partially written plans.

**Fix:**
- **Use thread-safe caching** (e.g., `ConcurrentHashMap` in Java, `threading.Lock` in Python).
- **Atomic updates** for plan storage.

```java
// Java example: Thread-safe cache with atomic updates
Map<String, ExecutionPlan> planCache = new ConcurrentHashMap<>();

ExecutionPlan getPlan(String queryKey) {
    return planCache.computeIfAbsent(queryKey, k -> compilePlan(k));
}
```

**Debugging Steps:**
1. **Enable thread dumps** (`jstack` in Java, `gdb` for C++).
2. **Check for `deadlocks` or `race conditions`**.
3. **Log plan access timestamps** for concurrency conflicts.

---

## **3. Debugging Tools & Techniques**

### **A. Profiling & Metrics**
| **Tool** | **Purpose** | **Example Command** |
|----------|------------|---------------------|
| **CPU Profiler** (`perf`, `vtune`) | Identify planning bottlenecks | `perf record -g ./query_engine` |
| **Latency Tracing** (`pprof`, `trace`) | Measure cache hit/miss times | `go tool pprof http://localhost:6060/debug/pprof/profile` |
| **Cache Statistics** (`Redis INFO`, `Memcached stats`) | Check hit/miss ratios | `redis-cli INFO stats` |
| **Logging Execution Plans** | Compare cached vs. fresh plans | `LOG_DEBUG("Plan for '{query}': {json.dumps(plan)}")` |

### **B. Key Debugging Commands**
1. **Check cache hit/miss ratio:**
   ```bash
   # Redis example
   redis-cli --stat
   ```
2. **Compare execution plans:**
   ```sql
   -- Log plans before/after cache hit
   SET LOG_PLANS_TO_FILE ON;
   EXPLAIN ANALYZE SELECT * FROM users WHERE id = 1;
   ```
3. **Monitor memory growth:**
   ```bash
   watch -n 1 "free -h && ps aux | grep cache"
   ```

### **C. Debugging Workflow**
1. **Reproduce the issue** (e.g., run under load while monitoring).
2. **Capture logs** (enable DEBUG/TRACE logging).
3. **Compare cached vs. fresh plans** (are they identical?).
4. **Check cache invalidation** (does it trigger on schema changes?).
5. **Test concurrency** (simulate high-load scenarios).

---

## **4. Prevention Strategies**

### **A. Best Practices for Execution Plan Caching**
✅ **Always include schema metadata in cache keys.**
✅ **Set a reasonable TTL** (e.g., 5-30 minutes).
✅ **Use a bounded cache** (e.g., `LRU` or `SizeTTL`).
✅ **Invalidate cache on schema changes** (trigger via DB events).
✅ **Normalize queries** before caching (e.g., sort columns, remove aliases).

### **B. Anti-Patterns to Avoid**
❌ **Caching plans indefinitely** → Memory leaks.
❌ **Ignoring concurrency** → Race conditions.
❌ **Not invalidating cache** → Stale plans.
❌ **Over-caching dynamic queries** → High memory usage.

### **C. Automated Monitoring**
- **Alert on high cache miss ratios** (e.g., >90% misses).
- **Monitor memory growth** (set thresholds for cache eviction).
- **Log plan divergence** (compare cached vs. fresh plans).

---
## **5. Example Debugging Session**
### **Scenario:**
"Our query performance degraded after a database schema change, but the cache should have invalidated stale plans."

### **Steps:**
1. **Check logs** → Found repeated planning for the same query.
2. **Log cache keys** → Discovered cache key didn’t include schema hash.
3. **Update cache key generation**:
   ```python
   def get_cache_key(query, schema_hash):
       return hashlib.md5(f"{query}_{schema_hash}".encode()).hexdigest()
   ```
4. **Verify invalidation** → Added `ON_SCHEMA_CHANGE` hook to clear plans.
5. **Monitor post-fix** → Cache hit ratio improved from 20% → 90%.

---
## **Conclusion**
Execution Plan Caching is powerful but requires careful tuning. Common pitfalls include:
- **Incorrect cache keys** → Stale plans.
- **No invalidation** → Performance degradation.
- **Concurrency issues** → Plan corruption.
- **Unbounded cache growth** → Memory problems.

**Quick Fixes:**
| **Issue** | **Immediate Action** |
|-----------|----------------------|
| High planning overhead | Add schema hash to cache key |
| Memory bloat | Set `maxsize` and `TTL` |
| Plan inconsistency | Normalize queries before caching |
| Race conditions | Use thread-safe cache structures |

By following this guide, you can quickly diagnose and resolve Execution Plan Caching issues, ensuring optimal query performance. 🚀