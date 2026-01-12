# **Debugging Cassandra Database Patterns: A Troubleshooting Guide**

Cassandra is a distributed NoSQL database known for its high scalability, fault tolerance, and linearizable consistency. However, improper data modeling, query patterns, or cluster misconfigurations can lead to performance bottlenecks, reliability issues, and scalability challenges. This guide provides a structured approach to diagnosing and resolving common Cassandra problems.

---

## **1. Symptom Checklist**

Before diving into fixes, identify which symptoms align with your issue:

### **Performance Issues**
- [ ] Slow read/write operations
- [ ] High CPU, network, or disk I/O utilization
- [ ] Timeouts (`ReadTimeoutException`, `WriteTimeoutException`)
- [ ] Long `nodetool tpstats` or `nodetool cfstats` response times
- [ ] High `read_latency` or `write_latency` in `nodetool tpstats`

### **Reliability Problems**
- [ ] Frequent `UnavailableException` (read/write timeouts)
- [ ] Cassandra node crashes or hangs
- [ ] Data loss or corruption (e.g., `InsufficientReplicasException`)
- [ ] High `dropped messages` or `pending flushes` in `nodetool tpstats`
- [ ] GC-related issues (high pause times in `jstat -gc`)

### **Scalability Challenges**
- [ ] Cluster unable to handle increased load
- [ ] Co-processor (triggers) or secondary indexes causing bottlenecks
- [ ] Imbalanced data distribution (hotspots)
- [ ] Too many `coordinate_completion_time` spikes in `nodetool tablehistograms`
- [ ] High `sstable count` growth leading to compaction overload

---

## **2. Common Issues and Fixes**

### **Issue 1: Poor Query Performance (Slow Reads/Writes)**
#### **Symptoms:**
- High `read_latency` or `write_latency` in `nodetool tpstats`.
- Queries taking seconds instead of milliseconds.
- Large `coordinate_completion_time` spikes in `nodetool tablehistograms`.

#### **Root Causes:**
- **Inefficient data model** (e.g., using `SELECT *` instead of query-specific columns).
- **Missing secondary indexes** (causing full table scans).
- **Large partitions** (exceeding memory limits).
- **Unoptimized compaction strategy** (e.g., `SizeTieredCompactionStrategy (STCS)` on high-write tables).

#### **Fixes:**

##### **A. Optimize Data Modeling**
**Bad:**
```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY,
    name TEXT,
    email TEXT,
    posts TEXT[],  -- Large array causing partition bloat
    last_login TIMESTAMP
);
```
**Good:**
```sql
-- Time-series data (partition by time)
CREATE TABLE user_sessions (
    user_id UUID,
    session_date DATE,
    sessions LIST<TEXT>,  -- Limited size per partition
    PRIMARY KEY ((user_id), session_date)
) WITH CLUSTERING ORDER BY (session_date DESC);

-- Avoid large collections (use separate tables if needed)
```

##### **B. Use Partition Keys Effectively**
- Distribute data evenly:
  ```sql
  -- Bad: Single partition
  CREATE TABLE orders (
      user_id UUID,
      order_id UUID,
      PRIMARY KEY (user_id, order_id)
  );

  -- Good: Bucket by time or hash
  CREATE TABLE orders (
      user_id UUID,
      order_year INT,
      order_id UUID,
      PRIMARY KEY ((user_id, order_year), order_id)
  );
  ```
- Use `BUCKET` or `TOKEN`-aware partitioning.

##### **C. Avoid Full Table Scans**
- **Bad:** Using secondary indexes on high-cardinality columns.
  ```sql
  CREATE TABLE events (
      event_id UUID,
      user_id UUID,
      event_type TEXT,
      PRIMARY KEY (event_id)
  );
  CREATE INDEX ON events(user_id);  -- Full scan on large table
  ```
- **Good:** Denormalize or use dedicated tables.
  ```sql
  CREATE TABLE user_events (
      user_id UUID,
      event_id UUID,
      event_type TEXT,
      PRIMARY KEY ((user_id), event_id)
  );
  ```

##### **D. Tune Compaction Strategy**
- For high-write tables, use `LeveledCompactionStrategy (LCS)`:
  ```sql
  ALTER TABLE high_write_table WITH compaction = {
      'class': 'LeveledCompactionStrategy'
  };
  ```
- For read-heavy tables, `STCS` may suffice.

##### **E. Increase Read/Write Capacity**
- Adjust `memtable_allocation_type` and `memtable_heap_space_in_mb`:
  ```json
  memtable_allocation_type: offheap_objects
  memtable_heap_space_in_mb: 256
  ```
- Increase `concurrent_reads`/`concurrent_writes` (if underutilized):
  ```json
  concurrent_reads: 32
  concurrent_writes: 32
  ```

---

### **Issue 2: High Latency & Timeouts**
#### **Symptoms:**
- `ReadTimeoutException` or `WriteTimeoutException`.
- High `pending` operations in `nodetool tpstats`.
- Slower than expected `nodetool proxyhistograms`.

#### **Root Causes:**
- **Network issues** (high latency between nodes).
- **Disk I/O bottlenecks** (SSDs vs. HDDs).
- **Overloaded nodes** (CPU/memory pressure).
- **Replication factor mismatch** (e.g., `RF=3` but only 2 replicas available).

#### **Fixes:**

##### **A. Check Network Latency**
```bash
# Test network between nodes
ping <node_ip>
mtr <node_ip>
```
- If latency > 10ms, consider:
  - Increasing `endpoint_snitch` to a network-aware type (e.g., `GossipingPropertyFileSnitch`).
  - Using a **cross-DC replication** strategy if nodes are geographically distant.

##### **B. Optimize Disk I/O**
- Use **SSDs** for `commitlog` and `data` directories.
- Increase `commitlog_sync` (tradeoff between durability and performance):
  ```json
  commitlog_sync: periodic  # Default: 'batch' (higher durability)
  commitlog_sync_period_in_ms: 10000
  ```
- Monitor disk usage (`nodetool cfstats`):
  ```bash
  nodetool cfhistograms events_table
  ```

##### **C. Scale Vertically or Horizontally**
- **Vertical scaling:** Increase node resources (CPU, RAM, disks).
- **Horizontal scaling:** Add more nodes (adjust `num_tokens` for better load distribution).

##### **D. Adjust Replication Factor**
- If `RF=3` but only 2 nodes are available, increase `RF` or ensure nodes are healthy:
  ```bash
  nodetool ring
  nodetool status  # Check alive/down nodes
  ```

---

### **Issue 3: Data Loss or Corruption**
#### **Symptoms:**
- `InsufficientReplicasException`.
- Data missing after node failure.
- High `dropped messages` in `nodetool tpstats`.

#### **Root Causes:**
- **Improper `replication_factor`** (e.g., `RF=1` in a multi-node cluster).
- **Disk failures** (unrecovered or corrupted SSTables).
- **Network partitions** (nodes unable to replicate).
- **Incorrect `hinted handoff` settings**.

#### **Fixes:**

##### **A. Verify Replication Settings**
```sql
-- Ensure proper RF and replication strategy
CREATE TABLE critical_data (
    id UUID PRIMARY KEY
) WITH replication = {
    'class': 'NetworkTopologyStrategy',
    'datacenter1': 3
};
```
- Check replication status:
  ```bash
  nodetool tablehistograms critical_data
  ```

##### **B. Recovery from Hinted Handoff Failures**
- Flush hints if they accumulate:
  ```bash
  nodetool flushhints
  ```
- Enable **`hinted_handoff_enabled`** and tune timeouts:
  ```json
  hinted_handoff_enabled: true
  hinted_handoff_throttle_in_kb: 1024
  ```

##### **Avoid `RF=1`** in production—always use at least `RF=2` or `RF=3`.

##### **C. Check for Corrupted SSTables**
- Run `nodetool repairs`:
  ```bash
  nodetool repair  # Full repair (slow but thorough)
  ```
- For partial repairs (faster, but less safe):
  ```bash
  nodetool repair -pr
  ```

---

### **Issue 4: Compaction & Storage Overhead**
#### **Symptoms:**
- High `sstable count` (e.g., > 1000).
- Slow compactions (`nodetool compactionstats` shows long runs).
- Disk space filling up rapidly.

#### **Root Causes:**
- **Improper compaction strategy** (e.g., `STCS` on a high-write table).
- **Large partitions** (compaction becomes expensive).
- **Missing `gc_grace_seconds` tuning** (stale tombstones).

#### **Fixes:**

##### **A. Choose the Right Compaction Strategy**
| Strategy | Use Case | Pros | Cons |
|----------|----------|------|------|
| **STCS** | Read-heavy, low-write workloads | Simple, good for large partitions | High storage overhead |
| **LCS** | Write-heavy, high-performance | Low latency, predictable reads | High CPU usage during compactions |
| **TWCS** | Time-series data | Good for TTL-based data | Requires careful tuning |

**Example (LCS for high-write tables):**
```sql
ALTER TABLE high_write_table WITH compaction = {
    'class': 'LeveledCompactionStrategy'
};
```

##### **B. Limit Partition Size**
- Enforce **TTL** for time-series data:
  ```sql
  CREATE TABLE logs (
      log_id UUID,
      timestamp TIMESTAMP,
      data TEXT,
      PRIMARY KEY (log_id, timestamp)
  ) WITH default_time_to_live = 86400;  // 1 day
  ```
- Use **batching** to avoid single large writes.

##### **C. Adjust `gc_grace_seconds`**
- Reduce tombstone overhead:
  ```sql
  ALTER TABLE data_table WITH gc_grace_seconds = 300;  // Default: 10800 (3 hours)
  ```

##### **D. Trigger Manual Compaction**
```bash
nodetool compact  # Force immediate compaction (use cautiously)
```

---

## **3. Debugging Tools and Techniques**

### **A. Monitoring & Diagnostics**
| Tool | Purpose | Example Command |
|------|---------|-----------------|
| `nodetool` | Cluster health, stats, repairs | `nodetool status`, `nodetool tpstats` |
| `cqlsh` | Query execution tracing | `TRACING ON; SELECT * FROM table;` |
| `jstack` | Thread dump analysis | `jstack <pid> > thread_dump.txt` |
| `jstat` | GC monitoring | `jstat -gc <pid> 1000` |
| Prometheus + Grafana | Long-term metrics | `cassandra_exceptions_total` |
| `sstabletools` | SSTable inspection | `sstabletools info -p data/data.db/table` |

### **B. Key Commands**
| Command | Purpose |
|---------|---------|
| `nodetool tpstats` | Thread pool statistics (pending ops) |
| `nodetool cfstats` | Per-table statistics (read/write latencies) |
| `nodetool tablehistograms` | Query performance distribution |
| `nodetool proxyhistograms` | Client query latency |
| `nodetool netstats` | Network I/O and RPC latency |
| `nodetool compactionstats` | Compaction progress |

### **C. Log Analysis**
- Check `system.log` for:
  - `CompactionFailureException`
  - `ReadTimeoutException` (network issues)
  - `OutOfMemoryError` (heap exhaustion)
- Use `grep` for key errors:
  ```bash
  grep "Timeout" /var/log/cassandra/system.log
  grep "OOM" /var/log/cassandra/system.log
  ```

---

## **4. Prevention Strategies**

### **A. Data Modeling Best Practices**
✅ **Do:**
- Design tables for **query patterns**, not data relationships.
- Use **partition keys** to distribute data evenly.
- Avoid `SELECT *`—fetch only needed columns.
- Use **TTL** for expiring data.

❌ **Don’t:**
- Store large binary blobs (use external storage like S3).
- Use secondary indexes on high-cardinality columns.
- Create overly nested tables (denormalize when necessary).

### **B. Cluster Configuration**
✅ **Do:**
- Use **SSDs** for `commitlog` and `data` directories.
- Monitor `memtable` and `compaction` stats regularly.
- Adjust `RF` based on availability needs (`RF=3` for DC-aware, `RF=2` for single DC).

❌ **Don’t:**
- Set `commitlog_sync=periodic` in high-durability scenarios.
- Use `SimpleStrategy` in multi-node clusters (always use `NetworkTopologyStrategy`).
- Ignore `nodetool repair`—run it regularly.

### **C. Performance Tuning**
✅ **Do:**
- Enable **JVM GC tuning** (`G1GC` recommended).
- Limit `max_heap_size` to **32GB** (Cassandra scales better with multiple nodes).
- Use **connection pooling** (e.g., `cassandra-driver` pool settings).

❌ **Don’t:**
- Run out of disk space (`datanode` failures).
- Allow `sstable` count to exceed **1000** (trigger manual compaction).
- Ignore **warmup queries** (pre-load SSTable caches).

### **D. High Availability & Disaster Recovery**
✅ **Do:**
- Enable **hinted handoff** and **read repair**.
- Use **snapshot retention** (`snapshot_before_compactions: true`).
- Test **failover scenarios** (kill nodes randomly).

❌ **Don’t:**
- Rely solely on backups (Cassandra is append-only, so backups are slow).
- Use `RF=1` in production.
- Ignore **disk failures** (always have hot spares).

---

## **Final Checklist for Quick Resolution**
1. **Is the issue performance-related?** → Check `nodetool tpstats`, `cfstats`, and query execution.
2. **Is it reliability-related?** → Verify replication, hints, and node health.
3. **Is it scalability-related?** → Review data distribution, partitions, and compaction.
4. **Monitor logs** (`system.log`, GC stats).
5. **Adjust configuration** (compaction, replication, JVM settings).
6. **Test fixes** in a staging environment before production.

By following this structured approach, you can quickly identify and resolve Cassandra issues while preventing future problems. 🚀