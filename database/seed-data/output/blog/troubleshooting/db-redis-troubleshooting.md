# **Debugging Redis Database Patterns: A Troubleshooting Guide**

---

## **Introduction**
Redis is a high-performance in-memory data store widely used for caching, session management, rate limiting, and real-time analytics. While Redis is efficient, improper configuration, misused patterns, or operational oversights can lead to **performance degradation, reliability issues, or scalability bottlenecks**.

This guide helps backend engineers quickly diagnose and resolve common Redis-related problems using battle-tested techniques.

---

## **Symptom Checklist**
Before diving into fixes, confirm which symptoms are present:

✅ **Performance Issues**
- Slow response times (e.g., >100ms latency)
- High CPU or memory usage in Redis
- Evictions (`expired`, `evicted`) in Redis logs
- High `BGSAVE` or `BGREWRITEAOF` delays

✅ **Reliability Problems**
- Connection drops (`ERROR: Connection reset by peer`)
- Persistence failures (`AOF rewrite failed`, `RDB save error`)
- Memory exhaustion (`maxmemory policy` triggering evictions)
- Disk I/O spikes (if persistence is enabled)

✅ **Scalability Challenges**
- High `pub/sub` or `cluster` shard contention
- Overloaded master nodes in Redis Cluster
- Slow replication lag in replica nodes
- Client-side bottlenecks (e.g., bulk gets failing)

---

## **Common Issues & Fixes**

### **1. High Latency (Slow Operations)**
**Symptom:** Commands like `GET`, `SET`, or `HGETALL` take >100ms.

#### **Root Causes & Fixes**
| Cause | Diagnosis | Fix |
|--------|----------|------|
| **Redis memory fragmentation** | Run `MEMORY DOCTOR` or `MEMORY USAGE <key>` | Enable `lazyfree-lazy-expire` + `lazyfree-lazy-eviction` (Redis 6+). |
| **Overloaded master node** | Check `db1:keys` (master) vs. `db1:keys` (replica) | Use **Redis Cluster** or **read-only replicas** for reads. |
| **NX/NPSP commands** | High `INCR`/`INCRBY` failures | Avoid `NX`/`CHECK` flags in hot keys; use Lua scripts for atomicity. |
| **Slow Lua scripts** | High `LUASCRPT` latency | Optimize scripts with `__KEYS[]` and `__VALUES[]`. |
| **Client-side batching** | Large `MGET`/`LPUSH` calls | Split into smaller batches (<100 keys). |

**Code Fix Example: Reduce Lua Script Latency**
```lua
-- Bad: Scans all keys → slow
local total = 0
for i = 1, 10000 do
    local val = redis.call('GET', 'key:' .. i)
    if val then total = total + 1 end
end
return total

-- Good: Use `__KEYS` (if keys are known)
return redis.call('HGETALL', KEYS[1])
```

---

### **2. Memory Overuse & Evictions**
**Symptom:** Redis logs show `maxmemory policy hit`, and evictions (`expired`, `evicted`) spike.

#### **Root Causes & Fixes**
| Cause | Diagnosis | Fix |
|--------|----------|------|
| **No maxmemory policy set** | `redis-cli INFO memory | grep "maxmemory"` → `0` | Set `maxmemory 4gb` + `maxmemory-policy volatile-lru`. |
| **Hot keys with large values** | `MEMORY USAGE <large_key>` → hundreds of MB | Compress values (`zlib` in Lua) or split into smaller DBs. |
| **Unused objects (e.g., expired keys)** | `OBJECT ENCODING <key>` → `blob`/`ziplist` | Force rehash with `MEMORY RESET_STATS` + `CONFIG REWRITE`. |
| **Replicas not evicting** | Replica has same keys as master | Use `maxmemory-reserve 100mb` to allow reps to evict first. |

**Code Fix Example: Configure Memory Policy**
```ini
# redis.conf
maxmemory 4gb
maxmemory-policy volatile-lru  # Evict least recently used keys first
maxmemory-reserve 500mb        # Reserve space for replicas
```

---

### **3. Persistence Failures (RDB/AOF)**
**Symptom:** `RDB Snapshot Failed` or `AOF Rewrite Stuck`.

#### **Root Causes & Fixes**
| Cause | Diagnosis | Fix |
|--------|----------|------|
| **Disk I/O bottleneck** | `dstat -d` shows high disk usage | Disable AOF or reduce sync frequency (`appendfsync everysec`). |
| **Large RDB dump** | `BGSAVE` takes >10s | Use `save ""` (no cron) and `auto-aof-rewrite-percentage 10`. |
| **Inode limit reached** | `df -i` shows full `/` | Increase inodes (`ulimit -n 65535`) or move RDB to SSD. |
| **AOF append errors** | `AOF rewrite fails` | Use `appendonly yes` + `dir /fast-ssd/`.

**Code Fix Example: Optimize AOF**
```ini
# redis.conf
appendfsync everysec       # Balance durability/speed
auto-aof-rewrite-percentage 10  # Rewrite if AOF grows >10%
auto-aof-rewrite-min-size 64mb  # Only rewrite if AOF >64MB
```

---

### **4. High Replication Lag**
**Symptom:** Replica lags behind master by >1 sec.

#### **Root Causes & Fixes**
| Cause | Diagnosis | Fix |
|--------|----------|------|
| **Slow network** | `ping -c 10 redis-replica` → high latency | Colocate Redis instances or use VPC peering. |
| **Replica busy with commands** | `redis-cli --r <ip> | grep "used_memory" | diff` | Offload reads to replicas. |
| **High traffic on master** | `redis-cli INFO commands | grep "cmdstat_get"` → high count | Use **Redis Cluster** or **read replicas**. |

**Fix: Force Replica Replica Sync**
```sh
# On master:
REPLICATE
SAVE  # Force RDB snapshot
```

**Optimize Replication**
```ini
# redis.conf
repl-backlog-size 1gb      # Buffer for >1s lag
repl-diskless-sync no      # Avoid slow disk syncs
repl-timeout 300           # Wait longer for replicas to catch up
```

---

### **5. Cluster Failures**
**Symptom:** Slower writes, `CLUSTER FAILOVER` hangs.

#### **Root Causes & Fixes**
| Cause | Diagnosis | Fix |
|--------|----------|------|
| **Cross-slot keys** | `CLUSTER CHECK` → `cross-slot` errors | Use `CLUSTER KEYSLOT <key>` to migrate keys. |
| **Slave overload** | `CLUSTER INFO | grep "slave-repl-offset"` → lagging | Add more replicas or use **Redis Stack** (Active Replication). |
| **Node evictions** | `CLUSTER NODES` → `fail?` marked nodes | Run `CLUSTER RESET` (careful!) or repair with `redis-trib`. |

**Fix: Resolve Cross-Slot Issues**
```sh
# Identify problematic keys:
redis-cli --cluster check mycluster.conf

# Migrate keys (example):
CLUSTER REPLICATE <source-node> <target-node>
CLUSTER MOVE <key> <slot>  # Force rehash
```

---

## **Debugging Tools & Techniques**
### **1. Built-in Redis Commands**
| Command | Purpose |
|---------|---------|
| `INFO memory` | Check memory fragmentation. |
| `MEMORY DOCTOR` | Detect memory leaks. |
| `CLUSTER CHECK` | Validate cluster health. |
| `REPLICAOF` + `SYNC` | Check replication lag. |
| `LUASCRPT DEBUG` | Profile Lua scripts. |

**Example: Diagnose Memory Issues**
```sh
redis-cli --stat
redis-cli INFO stats | grep "used_memory"
redis-cli MEMORY DOCTOR
```

### **2. External Tools**
- **Redis CLI** (`redis-cli --bigkeys`) → Detect large keys.
- **RedisInsight** → Visualize cluster topology.
- **Prometheus + Grafana** → Monitor latency/memory.
- **Redis Enterprise** → Enterprise-grade debugging.

### **3. Log Analysis**
- Enable **debug logs** (`loglevel debug`) in `redis.conf`.
- Check `redis-server.log` for:
  - `BGSAVE failed` → Disk issues.
  - `Connection reset` → Client timeouts.

---

## **Prevention Strategies**
### **1. Best Practices**
- **Use Redis Cluster** for >10k keys (avoid hotspots).
- **Enable RDB + AOF** (not just AOF) for durability.
- **Offload writes** to replicas (read-only).
- **Compress large values** (`zlib` in Lua scripts).
- **Limit script complexity** (avoid `KEYS *` in Lua).

### **2. Monitoring Baselines**
| Metric | Healthy Threshold |
|--------|------------------|
| `used_memory_rss` | <80% of RAM |
| `replication_backlog_active` | <1GB |
| `slowlog_len` | <1000 commands |
| `keyspace_hits` | >90% of `keyspace_misses` |

### **3. Alert Rules**
- **Redis Exporter + Alertmanager**:
  - Alert if `mem_fragmentation_ratio > 3`.
  - Alert if `repl_backlog_active > 500mb`.
  - Alert if `slowlog` > 100 entries.

---

## **Summary Checklist**
| **Symptom** | **Quick Fixes** |
|-------------|----------------|
| High latency | Check `MEMORY DOCTOR`, use replicas, optimize Lua. |
| Memory evictions | Adjust `maxmemory-policy`, compress keys. |
| Persistence fails | Reduce `BGSAVE` frequency, enable SSDs. |
| Replication lag | Increase `repl-backlog-size`, offload writes. |
| Cluster issues | Fix cross-slot keys, add more replicas. |

---

**Final Tip:** Always validate fixes with `redis-cli --stat` and monitor with Prometheus/Grafana. Redis performance is 90% configuration—small tweaks can yield massive improvements.

---
**Troubleshooting Deep Dive:** If issues persist, use `redis-debug-all` or contact Redis support with:
- `INFO commandstats`
- `INFO memory`
- `CLUSTER INFO` (if clustered)