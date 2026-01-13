# **[Pattern] Execution Plan Caching Reference Guide**

---

## **Overview**
Execution Plan Caching is an optimization pattern where query execution plans are precomputed during build time (or at defined intervals) and reused across subsequent requests. This eliminates runtime planning overhead—common in dynamic query engines like SQL, Gremlin, or Spark—by caching compiled plans. The pattern is particularly useful for high-latency applications with repetitive queries (e.g., analytics dashboards, CRUD-heavy web apps) where rebuilding plans per request would degrade performance.

Key benefits:
- **Reduced runtime latency** (constant-time lookup instead of dynamic parsing/execution).
- **Consistent performance** (avoids planning jitter).
- **Lower resource usage** (no repeated scanning or index lookups).
- **Predictable scaling** (fixed CPU/memory costs).

Common use cases include:
- Batch processing pipelines (e.g., Spark jobs).
- Repeated analytical queries (e.g., financial aggregations).
- Web applications with frequent identical queries (e.g., user profiles).

---

## **Schema Reference**
Below are the core components and their relationships for implementing Execution Plan Caching.

| **Component**               | **Description**                                                                                     | **Properties**                                                                                     | **Dependencies**                     |
|-----------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|---------------------------------------|
| **Plan Cache**              | Stores compiled execution plans for later reuse.                                                   | - `cacheKey` (unique identifier, e.g., query string hash)                                           | KeyValueStore, FileSystem             |
|                             |                                                                                                     | - `planVersion` (version of the cached plan, e.g., schema changes)                                 |                                       |
|                             |                                                                                                     | - `ttl` (Time-To-Live in minutes; 0 = permanent cache)                                              |                                       |
| **Query Compiler**          | Parses and compiles queries into execution plans.                                                   | - `parser` (e.g., SQL parser, Gremlin syntax analyzer)                                              | Cache                                  |
|                             |                                                                                                     | - `optimizer` (cost-based or rule-based optimizer)                                                   |                                       |
|                             |                                                                                                     | - `executor` (generates physical plans, e.g., DAG, iterative)                                      |                                       |
| **Cache Invalidation**      | Mechanisms to update or remove stale plans when dependencies change.                                | - `trigger` (on schema change, data drift, or time-based)                                          | EventBus, DBMS Listeners              |
|                             |                                                                                                     | - `strategy` (incremental rebuild, full recompilations)                                             |                                       |
| **Plan Registry**           | Metadata repository for cached plans (e.g., lineage, last used).                                   | - `queryMetadata` (original query, parameters, author)                                             | Cache                                  |
|                             |                                                                                                     | - `usageStats` (hit/miss counts, latency metrics)                                                   |                                       |
| **Data Source**             | Underlying database or data layer the plans operate on.                                             | - `schemaVersion` (version to ensure plan compatibility)                                            | Cache                                  |
|                             |                                                                                                     | - `refreshInterval` (for time-series data)                                                          |                                       |

---

## **Implementation Details**
### **1. Cache Key Generation**
The `cacheKey` must uniquely identify a query while allowing reuse. Common approaches:
- **Query String Hashing**: Use a cryptographic or rolling hash (e.g., MurmurHash) of the query + parameters.
  Example:
  ```python
  cacheKey = hashlib.sha256(f"{query_text}{param1}{param2}").hexdigest()
  ```
- **Schema-Aware Keys**: Prefix the key with the schema version (e.g., `schema_v2|SELECT * FROM users`).
- **Parameterization**: Replace variables with placeholders (e.g., `WHERE id = ?`) to avoid key collisions.

**Avoid**:
- Literal query strings (e.g., `"WHERE id = 123"` ≠ `"WHERE id = 456"` would create separate keys).
- Sensitive data in keys (e.g., PII).

---

### **2. Plan Compilation Flow**
1. **Query Received**: The system checks if a valid plan exists for the `cacheKey`.
2. **Cache Hit/Miss**:
   - **Hit**: Reuse the cached plan; verify schema compatibility.
   - **Miss**: Compile a new plan and store it (with TTL).
3. **Execution**: Run the plan against the data source.
4. **Invalidation**: Trigger a rebuild when dependencies change (e.g., schema update).

**Pseudocode**:
```python
def execute(query, params):
    cacheKey = generateCacheKey(query, params)
    plan = cache.get(cacheKey)

    if plan and isPlanValid(plan):
        return executePlan(plan, params)
    else:
        plan = compilePlan(query, params)  # Heavy operation
        cache.set(cacheKey, plan, ttl=30)
        return executePlan(plan, params)
```

---

### **3. Cache Invalidation Strategies**
| **Strategy**               | **Description**                                                                                     | **Use Case**                                      |
|---------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------|
| **Versioned Keys**        | Append schema version to the key (e.g., `schema_v3|query`).                                     | Schema changes (e.g., adding columns).           |
| **Time-Based TTL**        | Expire plans after a fixed interval (e.g., 1 hour).                                                | Data drift (e.g., real-time analytics).           |
| **Event-Driven**          | Listen to DBMS events (e.g., `AFTER UPDATE`) and invalidate matching plans.                        | High-frequency updates (e.g., logs tables).      |
| **Manual Trigger**        | API endpoint to force cache rebuild (e.g., `POST /api/plans/invalidate`).                          | Admin-driven refreshes.                           |
| **Delta Compilation**     | Recompile only the affected parts of the plan (if supported by the compiler).                     | Partial schema changes (e.g., adding an index).  |

**Example (Schema Versioning)**:
- **Before**: `cacheKey = "SELECT * FROM orders"`
- **After schema update**: `cacheKey = "schema_v2|SELECT * FROM orders"` (old plans are ignored).

---

### **4. Storage Backends**
| **Backend**               | **Pros**                                                                                          | **Cons**                                      | **Best For**                          |
|---------------------------|--------------------------------------------------------------------------------------------------|-----------------------------------------------|---------------------------------------|
| **Memory (Redis, Memcached)** | Low-latency, fast lookups.                                                              | Limited size, volatile.                          | Short-lived plans (e.g., web apps).   |
| **Disk (RocksDB, LevelDB)**       | Persistent, scalable.                                                                     | Higher latency than memory.                     | Long-lived plans (e.g., ETL jobs).    |
| **Database (PostgreSQL, BigQuery Cache)** | Built-in caching (e.g., prepared statements).                                       | Vendor-specific, less flexible.                 | SQL-based systems.                    |
| **Distributed Cache (Apache Ignite, ScyllaDB)** | Horizontal scalability for large clusters.                                         | Complex setup.                                  | Cloud-native apps.                    |

---

## **Query Examples**
### **1. Simple SQL Example (PostgreSQL Preparation)**
```sql
-- Compile and cache a plan at build time (e.g., via application startup script)
PREPARE cached_plan AS SELECT user_id, SUM(amount) FROM transactions
    WHERE date > $1 GROUP BY user_id;
```
**Usage**:
```sql
EXECUTE cached_plan('2023-01-01');
```
**Implementation Note**:
- PostgreSQL’s `PREPARE` caches plans automatically (TTL: forever unless dropped).
- For dynamic parameters, use `$1` placeholders.

---

### **2. Spark SQL Plan Caching**
```python
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .config("spark.sql.adaptive.enabled", "true") \
    .getOrCreate()

# Cache the plan for a DataFrame (Spark 3.0+)
df = spark.read.parquet("data/orders.parquet")
cached_df = df.cache()  # In-memory caching

# Reuse the cached DataFrame for multiple actions
result = cached_df.filter("status = 'completed'").count()
```
**Key Points**:
- `cache()` triggers physical plan compilation and stores it in memory.
- Use `uncache()` to clear when no longer needed.
- For disk persistence, combine with `persist(StorageLevel.DISK_ONLY)`.

---

### **3. Gremlin (TinkerPop) Plan Caching**
```java
// Compile and cache a traversal plan
Graph graph = TinkerFactory.createGraph();
GraphTraversalSource g = graph.traversal();
Traversal<?> traversal = g.V().has("name", "v").values("age");

// Cache the plan (requires custom implementation)
CacheKey key = new CacheKey(traversal.toString());
PlanCache cache = new PlanCache();
cache.put(key, traversal);

// Reuse the cached plan
Traversal<?> cachedTraversal = cache.get(key);
Result result = cachedTraversal.toList();
```
**Implementation Notes**:
- TinkerPop does not natively cache plans; requires a custom `PlanCache`.
- Use `Traversal.toString()` as the `cacheKey` (but hash it to avoid collisions).

---

## **Query Examples (Invalidation Scenarios)**
### **1. Schema Change Invalidation**
**Before** (schema: `users(id, name)`):
```sql
-- Cached plan: SELECT name FROM users WHERE id = ?
```
**After** (schema: `users(id, name, email)`):
- The plan must be recompiled (e.g., by updating the `cacheKey` to include `schema_v2`).

**Automated Invalidation** (Pseudocode):
```python
@on_schema_change(listener="users_table")
def invalidate_user_plans():
    keys_to_invalidate = ["schema_v1|SELECT * FROM users"]
    cache.invalidate(keys_to_invalidate)
```

---

### **2. Data Drift Invalidation**
For time-series data (e.g., monitor for new partitions):
```python
def check_data_drift():
    latest_partition = db.query("SELECT MAX(partition_id) FROM logs")
    cached_partitions = set(cache.get_all_keys().keys())
    if latest_partition not in cached_partitions:
        cache.invalidate_keys_with_prefix("logs_")
```

---

## **Performance Considerations**
| **Factor**                | **Recommendation**                                                                                     |
|---------------------------|------------------------------------------------------------------------------------------------------|
| **Cache Hit Ratio**       | Aim for >90% hits; monitor with metrics like `cache_hits/total_queries`.                              |
| **Plan Size**             | Large plans (e.g., complex joins) may not fit in memory; consider disk fallback.                   |
| **Concurrency**           | Use thread-local caches or fine-grained locks to avoid contention during plan compilation.         |
| **Plan Compilation Cost** | Offload to background threads (e.g., Spark’s `SparkContext` uses a separate thread pool).         |
| **Parameterized Queries** | Always use parameters (e.g., `?` placeholders) to avoid key collisions.                              |
| **Cold Starts**           | For serverless apps, warm up caches during initialization (e.g., precompile common queries).       |

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                                     | **When to Use**                                      |
|---------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------|
| **[Materialized Views](https://martinfowler.com/eaaCatalog/materializedView.html)** | Precompute query results and refresh periodically.                                                 | Read-heavy workloads with infrequent changes.        |
| **[Query Sharding](https://martinfowler.com/articles/query-sharding.html)**       | Partition data to parallelize queries; cache shards independently.                                | Horizontal scaling for distributed queries.          |
| **[Adaptive Query Execution](https://spark.apache.org/docs/latest/optimizations-adaptive-execution.html)** | Dynamically adjust execution plans at runtime (e.g., Spark’s shuffle optimization).           | Workloads with unpredictable access patterns.        |
| **[Caching Layer (CDN)](https://martinfowler.com/eaaCatalog/cachingLayer.html)** | Cache results at the application edge (e.g., Redis, Varnish).                                     | Global low-latency requirements.                     |
| **[Partition Pruning](https://use-the-index-luke.com/srv/partition-pruning)**     | Filter partitions early to reduce data scanned (complements caching).                              | Analytical queries over partitioned data.            |

---

## **Anti-Patterns**
1. **Stale Plan Reuse**:
   - **Problem**: Running a cached plan on incompatible data (e.g., schema drift).
   - **Fix**: Always validate schema compatibility or use versioned keys.

2. **Over-Caching**:
   - **Problem**: Caching too many unique plans consumes memory/Disk.
   - **Fix**: Limit cache size; prioritize high-frequency queries.

3. **Ignoring TTL**:
   - **Problem**: Plans remain cached indefinitely, leading to stale results.
   - **Fix**: Set reasonable TTLs (e.g., 1 hour for real-time data).

4. **Parameterized Key Collisions**:
   - **Problem**: Queries with similar parameters hash to the same key.
   - **Fix**: Use a robust hashing algorithm or include parameter ranges in the key.

---

## **Tools & Libraries**
| **Tool/Library**          | **Purpose**                                                                                          | **Language/Framework**               |
|---------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------|
| **PostgreSQL Prepared Statements** | Native plan caching for SQL.                                                                     | SQL                                   |
| **Spark SQL**             | `persist()` and adaptive query execution.                                                          | Scala/Python/Java                     |
| **Apache Druid**          | Pre-aggregated ingestion for analytical queries.                                                    | Java                                  |
| **Redis**                 | In-memory cache for query plans.                                                                   | Multi-language                        |
| **PlanCache (Custom)**    | Lightweight in-process cache (e.g., for Gremlin).                                                  | Any (Java/Python/etc.)                |
| **Presto/Trino**          | Supports query caching via `query_max_planning_time` and `query_cache_size`.                      | Java                                  |

---

## **Example Walkthrough: Caching a Gremlin Traversal**
### **Step 1: Define the Cache**
```python
from py2neo import Graph, Node
import hashlib

class GremlinPlanCache:
    def __init__(self):
        self.cache = {}

    def generate_key(self, traversal_str):
        return hashlib.md5(traversal_str.encode()).hexdigest()

    def compile(self, query):
        key = self.generate_key(query)
        plan = self._execute_traversal(query)  # Heavy operation
        self.cache[key] = plan
        return plan

    def execute(self, query):
        key = self.generate_key(query)
        return self.cache.get(key, self.compile(query))
```

### **Step 2: Use the Cache**
```python
cache = GremlinPlanCache()
graph = Graph("bolt://localhost:7687")

# First run (compiles and caches)
result = cache.execute("g.V().has('name', 'v').values('age')")

# Subsequent runs (uses cache)
result = cache.execute("g.V().has('name', 'v').values('age')")  # Faster
```

### **Step 3: Handle Schema Changes**
```python
def invalidate_on_schema_change():
    # Listen for changes to the `Person` label
    if schema_changed("Person"):
        keys_to_remove = [k for k in cache.cache.keys() if "Person" in k]
        cache.cache = {k: v for k, v in cache.cache.items() if k not in keys_to_remove}
```

---
## **Metrics to Monitor**
| **Metric**                | **Description**                                                                                     | **Threshold**                     |
|---------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------|
| `cache_hit_ratio`         | `(hits / (hits + misses)) * 100`                                                                  | >90%                              |
| `plan_compilation_time`   | Time taken to compile a new plan.                                                                    | <50ms (latency budget)            |
| `cache_memory_usage`      | Size of the cache in MB.                                                                           | <50% of available memory          |
| `invalidations_per_hour`  | Rate of plan invalidations (indicates schema/data churn).                                          | Depends on workload               |
| `longest_plan_duration`   | Slowest plan execution (potential optimization target).                                               | Investigate if >P99 latency       |

---
## **Conclusion**
Execution Plan Caching reduces runtime overhead by leveraging precomputed plans, but requires careful management of cache keys, invalidation, and storage. Use this pattern for:
- Repeated queries in analytics/dashboards.
- High-latency applications where planning is a bottleneck.
- Workloads with stable schemas (or versioned keys).

Combine with related patterns (e.g., materialized views, adaptive execution) for comprehensive optimization. Monitor cache metrics to balance memory usage and performance.