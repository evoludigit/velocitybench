# **Debugging CockroachDB Database Patterns: A Troubleshooting Guide**

## **Introduction**
CockroachDB is a distributed, scalable SQL database designed for high availability, strong consistency, and linearizable transactions. While its architecture provides resilience, misconfigurations, improper patterns, or operational overhead can lead to **performance bottlenecks, reliability issues, and scalability challenges**.

This guide provides a **practical, actionable approach** to diagnose and resolve common CockroachDB problems, focusing on best practices and quick fixes.

---

## **1. Symptom Checklist**
Before diving into troubleshooting, identify which symptoms align with your issue:

| **Symptom Category**       | **Possible Indicators** |
|----------------------------|-------------------------|
| **Performance Issues**     | Slow queries, high latency, CPU/memory pressure, frequent timeouts |
| **Reliability Problems**   | Unstable nodes, split-brain risks, transaction retries, frequent restarts |
| **Scalability Challenges**  | Bottlenecked nodes, high disk I/O, slow horizontal scaling, improper sharding |
| **Connectivity Issues**    | Connection timeouts, network partitions, DNS resolution failures |
| **Transaction Problems**   | Deadlocks, repeated retries, inconsistent reads, long-running transactions |
| **Storage & Disk Issues**  | High disk utilization, slow disk I/O, frequent compaction delays |

**Quick Check:**
- Are errors appearing in logs (`cockroach debug sql`)?
- Is there a spike in **RPC latency** (`cockroach sql --execute="select * from pg_stat_rpc_in_progress;"`)?
- Are nodes **stuck in a state** (`cockroach node status`)?
- Are transactions **blocking** (`cockroach debug sql --transaction-timeout=10s`)?

---

## **2. Common Issues & Fixes**

### **Issue 1: Slow Queries & High Latency**
**Symptoms:**
- Queries taking **seconds instead of milliseconds**.
- High `pg_stat_statements` or `cockroach sql --show-plan` reveals inefficient plans.
- Nodes under heavy CPU load (`top`, `cockroach version --status`).

**Root Causes:**
- Missing indexes (`EXPLAIN ANALYZE` shows full table scans).
- Poorly written queries (N+1 selects, complex joins).
- Lack of read replicas (for read-heavy workloads).
- Insufficient hardware (CPU, memory, or disk).

**Fixes:**

#### **A. Optimize Queries**
```sql
-- Check if an index exists (e.g., for a frequent WHERE clause)
SELECT * FROM pg_indexes WHERE tablename = 'users';

-- Create a missing index
CREATE INDEX idx_user_email ON users(email);

-- Use EXPLAIN to analyze query performance
EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = 123;
```
**Best Practice:**
- Avoid `SELECT *`—fetch only required columns.
- Use `LIMIT` and `OFFSET` cautiously (use pagination instead).
- Denormalize where appropriate (but keep data consistent with triggers).

#### **B. Enable Read Replicas**
```sh
# Scale read capacity by adding replicas
cockroach start --insecure --advertise-addr=node2:26257 --join=node1:26257
```
**Verify:**
```sql
SELECT node_id, role FROM crdb_internal.node_status;
```
**Best Practice:**
- Use `--replicas=3` for production to avoid single points of failure.

#### **C. Increase Hardware Resources**
- **CPU:** Ensure each node has enough cores (CockroachDB is CPU-bound).
- **Memory:** Allocate at least **8GB per node** (adjust `cockroach database --max-sql-memory`).
- **Disk:** Use **SSDs** for high-throughput workloads.

---

### **Issue 2: Reliability Problems (Node Failures, Splits)**
**Symptoms:**
- Nodes **crash frequently** without clear logs.
- **Split-brain** detected (`cockroach node status` shows inconsistent states).
- **Raft log corruption** (`cockroach debug raft`).

**Root Causes:**
- **Improper cluster configuration** (e.g., `--max-peers` too low).
- **Network partitions** (nodes can’t communicate).
- **Storage corruption** (bad disk or misconfigured `cockroach storage`).
- **Resource starvation** (OOM kills).

**Fixes:**

#### **A. Check Node States**
```sh
cockroach node status
```
**Expected:**
- **UP** (healthy)
- **DOWN** (temporary failure)
- **DOWN (SUSPICIOUS)** (potential corruption)

**Fix:**
- **For DOWN nodes:**
  ```sh
  cockroach restart node_key
  ```
- **For SUSPICIOUS nodes:**
  ```sh
  cockroach debug remove-node --force node_key
  ```
  (Backup data first!)

#### **B. Verify Raft Log Health**
```sh
cockroach debug raft --show-logs
```
**If logs are corrupted:**
```sh
cockroach debug remove-node --force node_key
cockroach start --insecure --join=primary-node ...
```

#### **C. Configure Proper Networking**
```sh
# Ensure `--listen-addr` and `--advertise-addr` match network topology
cockroach start --listen-addr=0.0.0.0:26257 --advertise-addr=node1.example.com:26257 --join=node2.example.com:26257
```
**Best Practice:**
- Use **VPC peering** or **VPN** for cloud deployments.
- Avoid public IPs unless necessary.

---

### **Issue 3: Scalability Bottlenecks**
**Symptoms:**
- **High disk I/O** (`iostat -x 1` shows 100% disk usage).
- **Slow horizontal scaling** (adding nodes doesn’t improve performance).
- **Hotspots** (frequent timeouts on specific tables).

**Root Causes:**
- **Improper sharding** (hot keys overwhelming a node).
- **Missing distributed index** (for multi-region deployments).
- **Small `storage.block.size`** (default 64MB may be too small for large tables).

**Fixes:**

#### **A. Check Table Distribution**
```sql
-- Find tables with uneven distribution
SELECT table_name, COUNT(*) FROM crdb_internal.node_table_stats
GROUP BY table_name HAVING COUNT(*) > 1000;
```
**Fix:**
- **Add a distributed index** (if data is accessed across regions):
  ```sql
  ALTER TABLE users ADD DISTRIBUTED BY SHARDING KEY (region_id);
  ```
- **Use `CLUSTER BY` for hot keys**:
  ```sql
  CREATE TABLE orders (id UUID PRIMARY KEY, user_id UUID, CLUSTER BY (user_id));
  ```

#### **B. Adjust Storage Block Size**
```sh
cockroach database --block-size=256MB  # For large datasets
```
**Verify:**
```sql
SELECT * FROM crdb_internal.storage_stats;
```

#### **C. Use Read/Write Separation**
```sh
# Dedicate nodes for read-heavy workloads
cockroach start --insecure --advertise-addr=read-node:26257 --join=primary-cluster ...
```
**Best Practice:**
- **Avoid mixing read/write workloads** if possible.

---

### **Issue 4: Transaction Problems**
**Symptoms:**
- **Long-running transactions** (`pg_stat_activity` shows frozen transactions).
- **Deadlocks** (repeated retries).
- **Inconsistent reads** (due to `REPEATABLE READ` isolation).

**Root Causes:**
- **Missing transaction timeouts**:
  ```sql
  SET SELECT_FOR_UPDATE SKIP LOCKED; -- For long-running scans
  ```
- **Heavy locking** (many `SELECT FOR UPDATE` queries).
- **Unoptimized transactions** (e.g., large batch inserts).

**Fixes:**

#### **A. Set Transaction Timeouts**
```sql
SET max_transaction_duration = '10s'; -- Enforce short transactions
```
**Apply globally:**
```sh
cockroach sql --exec="SET max_transaction_duration = '10s';"
```

#### **B. Optimize Locking Strategies**
```sql
-- Use advisory locks for high-contention scenarios
SELECT pg_advisory_xact_lock(42);
```

#### **C. Use Batch Inserts Efficiently**
```sql
-- Batch inserts reduce overhead
BEGIN;
INSERT INTO users (name, email) VALUES ('A', 'a@test.com'), ('B', 'b@test.com');
COMMIT;
```
**Avoid:**
```sql
-- Anti-pattern: Many single-row inserts
INSERT INTO users VALUES ('A', 'a@test.com');
INSERT INTO users VALUES ('B', 'b@test.com');
```

---

## **3. Debugging Tools & Techniques**

| **Tool/Command** | **Purpose** | **Example Usage** |
|------------------|------------|------------------|
| `cockroach sql --show-plan` | Analyze query execution | `cockroach sql --show-plan "SELECT * FROM users WHERE email = 'x@y.com';"` |
| `cockroach debug sql` | Inspect active transactions | `cockroach debug sql --transaction-timeout=5s` |
| `cockroach node status` | Check node health | `cockroach node status --format=csv` |
| `cockroach status --show-routes` | Check routing distribution | `cockroach status --show-routes` |
| `cockroach sql --exec="SELECT * FROM crdb_internal.node_status;"` | Monitor node roles | `cockroach sql --exec="SELECT * FROM crdb_internal.node_status;"` |
| `cockroach sql --exec="SELECT * FROM pg_stat_statements ORDER BY total_time DESC;"` | Identify slow queries | `cockroach sql --exec="SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"` |
| `cockroach debug raft --show-logs` | Inspect Raft log issues | `cockroach debug raft --show-logs --node-id=1` |
| `cockroach debug remove-node --force` | Force node removal (last resort) | `cockroach debug remove-node --force node_key` |

**Advanced Debugging:**
- **Enable SQL tracing** (`cockroach database --sql-trace`).
- **Use `cockroach sql --insecure`** for direct debugging.
- **Check OS-level metrics** (`dmesg`, `journalctl`).

---

## **4. Prevention Strategies**

### **General Best Practices**
✅ **Use `cockroach init` for clean deployments** (avoid manual `cockroach start`).
✅ **Enable backups** (`cockroach backup create`).
✅ **Monitor with Prometheus + Grafana** (CockroachDB has built-in metrics).
✅ **Test failure scenarios** (kill nodes, simulate network splits).

### **Query Optimization**
✅ **Index strategically** (`EXPLAIN ANALYZE` everything).
✅ **Avoid `SELECT *`** (fetch only needed columns).
✅ **Use `LIMIT` + `OFFSET` carefully** (prefer cursor-based pagination).

### **Cluster Configuration**
✅ **Set `--max-peers=3` (minimum for production)**.
✅ **Use `--max-sql-memory=8GB` (adjust based on workload)**.
✅ **Enable `--store.incompatible-initialization` for upgrades**.

### **Automation & Alerts**
✅ **Set up alerts for:**
   - High disk I/O (`cockroach sql --exec="SELECT * FROM crdb_internal.storage_stats WHERE averageio > 1000";`)
   - Long-running transactions (`pg_stat_activity`)
   - Node failures (`cockroach node status`)

---

## **5. Final Checklist for Quick Resolution**
| **Step** | **Action** |
|----------|-----------|
| **1.** | Check `cockroach node status` for unhealthy nodes. |
| **2.** | Review slow queries (`pg_stat_statements`). |
| **3.** | Verify Raft log health (`cockroach debug raft`). |
| **4.** | Optimize queries (`EXPLAIN ANALYZE`). |
| **5.** | Scale reads if performance is bad (add replicas). |
| **6.** | Check disk I/O (`iostat -x 1`). |
| **7.** | Monitor transaction timeouts (`pg_stat_activity`). |
| **8.** | Enable backups (`cockroach backup test`). |

---

## **Conclusion**
CockroachDB is **highly resilient**, but misconfigurations and unoptimized patterns can lead to **performance degradation, reliability issues, and scalability bottlenecks**.

**Key Takeaways:**
- **Monitor actively** (metrics, logs, query plans).
- **Optimize queries** (indexes, batching, proper isolation).
- **Design for failure** (replicas, backups, network redundancy).
- **Use built-in tools** (`cockroach debug`, `pg_stat_*` views).

By following this guide, you should be able to **quickly diagnose and resolve** most CockroachDB issues while maintaining **high availability and performance**.

---
**Next Steps:**
- [CockroachDB Official Docs](https://www.cockroachlabs.com/docs/stable/)
- [CockroachDB Performance Guide](https://www.cockroachlabs.com/docs/stable/performance-tuning.html)