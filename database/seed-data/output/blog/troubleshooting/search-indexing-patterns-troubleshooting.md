# **Debugging Search & Indexing Patterns (Elasticsearch): A Troubleshooting Guide**

Elasticsearch is a powerful, distributed search and analytics engine that powers full-text search, aggregations, and real-time analytics in modern applications. When misconfigured, poorly optimized, or under stress, Elasticsearch can lead to degraded performance, high latency, or even system failures. This guide provides a structured approach to diagnosing and resolving common Elasticsearch-related issues in search and indexing patterns.

---

## **1. Symptom Checklist**
Before diving into debugging, verify whether your Elasticsearch setup exhibits any of the following symptoms:

### **Performance-Related Issues**
- [ ] High CPU usage (especially in master nodes)
- [ ] Slow search queries (long latency, timeouts)
- [ ] Slow indexing (documents not appearing in search results quickly)
- [ ] Increased disk I/O or slow reads/writes
- [ ] High network traffic between nodes

### **Reliability & Stability Issues**
- [ ] Frequent cluster yellow/red states
- [ ] Unsharded or partially sharded indices
- [ ] Node failures (disconnections, crashes)
- [ ] High garbage collection (GC) pause times
- [ ] Memory pressure (OOM errors, disk-based swapping)

### **Scalability & Resource Issues**
- [ ] Cluster struggles with additional data growth
- [ ] Slow scaling-out (adding new nodes)
- [ ] Uneven shard distribution (some nodes overloaded)
- [ ] Hot threads (thread contention issues)

### **Indexing & Search Problems**
- [ ] Inconsistent search results (partial or missing data)
- [ ] Failed bulk indexing operations
- [ ] Corrupted or unindexed documents
- [ ] Mapping explosions (excessive field mappings slowing queries)

### **Integration & Configuration Issues**
- [ ] Connectivity problems with applications (timeouts, 429 errors)
- [ ] Misconfigured settings (e.g., `cluster.max_shards_per_node`, `index.number_of_replicas`)
- [ ] Improper security policies (authentication/authorization failures)

If multiple symptoms occur, start with **performance bottlenecks** before moving to **reliability and scalability** issues.

---

## **2. Common Issues and Fixes**

### **Issue 1: Slow Search Queries**
**Symptoms:**
- High query latency (e.g., 100ms → 5s)
- Timeout errors (`SearchPhaseExecutionException`)
- Large `query_context` in logs

**Root Causes:**
- **Missing optimizations**: No query caching, deep pagination (`from=10000`), or inefficient queries.
- **Overly complex queries**: Nested queries, `script_score`, or `function_score` without optimizations.
- **Poor mapping design**: Unanalyzed or deep-nested fields.
- **Insufficient replicas/shards**: No parallel processing.

**Fixes:**

#### **Optimize the Query**
- **Use `search_after` instead of `from` for deep pagination** (better performance):
  ```json
  // Bad (slow for deep pagination)
  GET /products/_search
  {
    "query": { "match_all": {} },
    "from": 10000,
    "size": 10
  }

  // Good (uses search_after for deep pagination)
  GET /products/_search
  {
    "size": 10,
    "query": {
      "range": {
        "@timestamp": {
          "gte": "now-1h"
        }
      }
    }
  }
  ```

- **Enable query caching** (for repetitive queries):
  ```json
  PUT /products/_settings
  {
    "index.query.default_field": "cached_query"
  }
  ```

- **Use `term` instead of `match` for exact matches** (faster):
  ```json
  // Slow (analyzes text)
  "match": { "title": "elasticsearch" }

  // Fast (exact match)
  "term": { "title.keyword": "elasticsearch" }
  ```

#### **Adjust Cluster Settings**
- Increase `indices.query.bool.max_clause_count` (default: 1024, may be too low):
  ```json
  PUT /_cluster/settings
  {
    "persistent": {
      "indices.query.bool.max_clause_count": 8192
    }
  }
  ```

- **Use `doc_values` for sorting/filtering** (faster than `_source`):
  ```json
  PUT /products
  {
    "mappings": {
      "properties": {
        "price": { "type": "double", "doc_values": true }
      }
    }
  }
  ```

---

### **Issue 2: Slow Indexing (Bulk API Failures)**
**Symptoms:**
- Bulk operations fail with `MapperParsingException` or timeouts.
- Indexing speed drops significantly under load.

**Root Causes:**
- **Large chunk sizes** (default 5MB for bulk requests).
- **Unoptimized mappings** (e.g., `text` fields without analyzers).
- **Disk I/O bottlenecks** (slow HDD/SSD).
- **Too many shards** (each shard consumes resources).

**Fixes:**

#### **Optimize Bulk API**
- **Increase bulk request size** (if network allows):
  ```json
  POST /_bulk?refresh=wait_for
  {"index": {"_index": "logs", "_id": "1"}}
  {"message": "test", "timestamp": "2024-01-01"}

  # Increase size (e.g., 100MB)
  POST /_bulk?refresh=wait_for&size=100mb
  ```
- **Use multi-threaded clients** (e.g., `elasticsearch-bulk` in Python):
  ```python
  from elasticsearch_bulk import BulkIndexer

  bi = BulkIndexer(es, index="logs", chunk_size=1000)
  bi.add({"_id": 1, "message": "test"})
  bi.add({"_id": 2, "message": "another"})
  bi.index(raise_on_error=True)  # Parallel processing
  ```

#### **Optimize Mappings**
- **Use `keyword` for exact searches** (avoid `text` where possible):
  ```json
  PUT /products
  {
    "mappings": {
      "properties": {
        "id": { "type": "keyword" },  # Fast exact matches
        "description": { "type": "text" }  # Full-text search
      }
    }
  }
  ```

- **Avoid nested objects** (deep nesting slows querying):
  ```json
  # Bad (slows queries)
  "properties": {
    "metadata": {
      "nested": {
        "properties": {
          "tags": { "type": "keyword" }
        }
      }
    }
  }

  # Good (flatten if possible)
  "properties": {
    "tag1": { "type": "keyword" },
    "tag2": { "type": "keyword" }
  }
  ```

---

### **Issue 3: Cluster Health Issues (Yellow/Red States)**
**Symptoms:**
- Cluster in **YELLOW** (shards unassigned).
- **RED** state (primary shards missing).
- `unassigned_shards` in cluster health.

**Root Causes:**
- **Insufficient replicas** (`index.number_of_replicas=0`).
- **Node failures** (disk full, JVM crash).
- **Misconfigured shard allocation** (`cluster.routing.allocation.disk.threshold_enabled`).
- **Shard size too large** (single shard > disk capacity).

**Fixes:**

#### **Check Cluster Health**
```json
GET /_cluster/health?pretty
```
- If **YELLOW**:
  - Increase replicas:
    ```json
    PUT /products/_settings
    {
      "index.number_of_replicas": 1
    }
    ```
  - Force reallocation (if shards stuck):
    ```json
    POST /_cluster/reroute?retry_failed=true
    ```

- If **RED**:
  - Check lost primary shards:
    ```json
    GET /_cat/shards?v&h=index,shard,prirep,state,node
    ```
  - Restore from snapshot (if data was lost):
    ```json
    POST /_snapshot/my_backup/restore
    {
      "indices": "products",
      "include_global_state": true
    }
    ```

#### **Adjust Shard Allocation**
- **Set disk thresholds** (prevent low-disk nodes from accepting shards):
  ```json
  PUT /_cluster/settings
  {
    "persistent": {
      "cluster.routing.allocation.disk.threshold_enabled": true,
      "cluster.routing.allocation.disk.watermark.low": 85%,  // 85% disk usage
      "cluster.routing.allocation.disk.watermark.high": 90%,
      "cluster.routing.allocation.disk.watermark.flood_stage": 95%
    }
  }
  ```

- **Limit shards per node** (prevent overloading):
  ```json
  PUT /_cluster/settings
  {
    "persistent": {
      "cluster.routing.allocation.total_shards_per_node": 50
    }
  }
  ```

---

### **Issue 4: High Memory Pressure (OOM Errors)**
**Symptoms:**
- Java heap out of memory (`OutOfMemoryError`).
- High GC pause times (slow responses).
- Swapping to disk (extreme slowdown).

**Root Causes:**
- **JVM heap too small** (default 1GB in Elasticsearch).
- **Too many concurrent requests** (thread pool saturation).
- **Large indices with many fields** (increased index overhead).

**Fixes:**

#### **Tune JVM Heap Size**
- **Set `ES_JAVA_OPTS`** in `elasticsearch.yml`:
  ```yaml
  bootstrap.memory_lock: true
  ```
  Then update systemd/service config (Linux):
  ```bash
  sudo nano /etc/systemd/system/elasticsearch.service
  ```
  Add:
  ```ini
  Environment="ES_JAVA_OPTS=-Xms4g -Xmx4g -XX:+UseG1GC -XX:MaxGCPAUSEMillis=200"
  ```
  Restart Elasticsearch:
  ```bash
  sudo systemctl restart elasticsearch
  ```

#### **Optimize Thread Pools**
- **Adjust thread pools** (default `search` and `write` queues may be too small):
  ```json
  PUT /_cluster/settings
  {
    "persistent": {
      "thread_pool.search.size": 8,
      "thread_pool.write.size": 16,
      "thread_pool.bulk.queue_size": 500
    }
  }
  ```

#### **Use Index Lifecycle Management (ILM)**
- **Auto-rotate old indices** to reduce memory pressure:
  ```json
  PUT _ilm/policy/logstash-policy
  {
    "policy": {
      "phases": {
        "hot": {
          "actions": { "rollover": { "max_size": "50gb", "max_age": "30d" } }
        },
        "delete": { "min_age": "90d", "action": "delete" }
      }
    }
  }
  ```

---

## **3. Debugging Tools and Techniques**

### **A. Elasticsearch REST API for Diagnostics**
| **Endpoint** | **Purpose** |
|-------------|------------|
| `GET /_cluster/health?pretty` | Check cluster status (green/yellow/red) |
| `GET /_cat/allocation?v` | See shard allocation issues |
| `GET /_cat/shards?v` | Check shard states (STARTED, INITIALIZING) |
| `GET /_nodes/stats?pretty` | Node-level metrics (CPU, memory, disk) |
| `GET /_nodes/hot_threads?pretty` | Identify thread contention |
| `GET /_cluster/settings?include_defaults=true` | View all cluster settings |
| `GET /_nodes?filter_path=*.os,*.jvm,*.process` | JVM heap/disk usage |

**Example: Check Disk Usage**
```bash
GET /_cat/allocation?v&h=shard,node,store,disk.avail
```

### **B. Performance Analysis Tools**
- **Elasticsearch Slow Logs** (enable in `elasticsearch.yml`):
  ```yaml
  index.search.slowlog.threshold.query.warn: 10s
  index.search.slowlog.threshold.query.info: 5s
  ```
- **APM Integration** (for distributed tracing):
  ```yaml
  xpack.apm.enabled: true
  ```
- **Visualize with Kibana** (Discover, Dev Tools, APM).

### **C. Third-Party Tools**
- **Elasticsearch-Curator** (cleanup old indices):
  ```bash
  docker run -it --rm lmc-eu/elasticsearch-curator:6.8.0 \
    --host http://localhost:9200 \
    --config /etc/curator/config.yml
  ```
- **Grafana + Elasticsearch Plugin** (monitoring dashboards).
- **Prometheus + cAdvisor** (containerized metrics).

---

## **4. Prevention Strategies**

### **A. Indexing Best Practices**
1. **Use the Bulk API** (never single-document inserts).
2. **Avoid `text` fields for exact searches** (use `keyword`).
3. **Limit shard size** (target 10-50GB per shard).
4. **Use ILM for auto-indexing** (prevent manual cleanup).

### **B. Query Optimization**
1. **Avoid `match_all` in production** (use explicit filters).
2. **Use `doc_values` for sorting/filtering**.
3. **Limit `_source` fields** (only fetch needed data):
   ```json
   GET /products/_search
   {
     "_source": ["id", "title"],
     "query": { "match_all": {} }
   }
   ```

### **C. Cluster Configuration**
1. **Set proper JVM heap** (`-Xms` = `-Xmx` for fixed heap).
2. **Enable node resource limits** (prevent rogue nodes):
   ```json
   PUT /_cluster/settings
   {
     "persistent": {
       "cluster.routing.allocation.node_concurrent_recoveries": 2,
       "indices.breaker.total.limit": "70%"
     }
   }
   ```
3. **Use managed services** (AWS OpenSearch, Elastic Cloud) for large-scale deployments.

### **D. Regular Maintenance**
1. **Monitor shard counts** (avoid too many small shards).
2. **Test failover** (simulate node failures).
3. **Backup indices** (snapshots at least daily):
   ```json
   PUT /_snapshot/my_backup
   {
     "type": "fs",
     "settings": { "location": "/backups" }
   }
   POST /_snapshot/my_backup/snapshot_1?wait_for_completion=true
   ```

---

## **5. Quick Resolution Checklist**
| **Issue** | **Immediate Fix** | **Long-Term Fix** |
|-----------|-------------------|-------------------|
| Slow searches | Enable query caching, use `search_after` | Optimize mappings, reduce shard count |
| Bulk indexing fails | Increase bulk size, check mappings | Use multi-threaded bulk, optimize docs |
| Cluster YELLOW | Increase replicas, force reallocation | Set disk thresholds, monitor node health |
| OOM errors | Reduce heap size, increase GC timeout | Tune JVM, optimize thread pools |
| High latency | Check slow logs, increase thread pools | Use APM, optimize queries |

---

## **Final Notes**
- **Start with logs** (`/var/log/elasticsearch/` or Kibana Stack Monitoring).
- **Isolate the problem** (CPU, disk, network, or query).
- **Test changes incrementally** (avoid breaking production).
- **Use snapshots** before making major config changes.

By following this guide, you should be able to diagnose and resolve most Elasticsearch-related issues efficiently. For persistent problems, consider consulting [Elasticsearch’s official documentation](https://www.elastic.co/guide/) or the [Elastic Stack Community](https://discuss.elastic.co/).