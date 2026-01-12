# **Debugging MongoDB Database Patterns: A Troubleshooting Guide**
*For Backend Engineers Facing Performance, Reliability, and Scalability Issues*

---

## **1. Introduction**
MongoDB excels in flexibility and scalability, but improper schema design, indexing, or query patterns can lead to bottlenecks, data corruption, or poor performance. This guide helps diagnose and resolve common MongoDB issues using practical, actionable steps.

---

## **2. Symptom Checklist**
Use this checklist to identify root causes quickly:

| **Symptom**                     | **Likely Cause**                          | **Check** |
|----------------------------------|------------------------------------------|-----------|
| Slow reads/writes (>500ms)       | Missing indexes, large documents, unoptimized queries | `explain()` analysis, `db.currentOp()` |
| High CPU/memory usage           | Memory-mapped files (WiredTiger), full scans | `db.serverStatus().mem`, `mongostat` |
| Frequent timeouts                | Connection pool exhaustion, slow queries  | `db.serverStatus().connections` |
| Data corruption/replication lag | Insufficient oplog size, network issues  | `rs.printReplicationInfo()` |
| Inconsistent reads               | No read preference, stale sessions        | `db.currentOp().inprog` |
| High disk I/O                    | Unsharded collections, large indexes     | `db.collection.stats()` |
| Slow aggregations                | Lack of index inclusion, pipeline inefficiency | `$explain` in aggregation |
| High error rate (121, 18)       | Network issues, disk failures            | Error logs (`mongod.log`) |

---
**Action:** Once symptoms are identified, proceed to **Section 3** for fixes.

---

## **3. Common Issues & Fixes**

### **3.1 Performance Issues**
#### **Problem 1: Slow Queries Due to Missing Indexes**
- **Symptoms:** Full collection scans (`"stage": "IXSCAN"`), high CPU.
- **Diagnosis:**
  ```javascript
  db.orders.find({ customerId: "123" }).explain("executionStats");
  ```
  Check `totalDocsExamined` (should be low if indexed).

- **Fix:** Add a compound index for frequently queried fields:
  ```javascript
  db.orders.createIndex({ customerId: 1, status: 1 });
  ```

#### **Problem 2: Large Document Bloat**
- **Symptom:** Inserts update time (`$set`) on huge documents (e.g., >16MB).
- **Fix:** Break into subdocuments, use embedded vs. referenced data carefully:
  ```javascript
  // Bad: Nested arrays of objects
  { products: [{ id: 1, name: "A" }, { id: 2, name: "B" }] }

  // Better: Reference or split
  { productIds: [1, 2] }  // Reference via lookup
  ```

#### **Problem 3: Unoptimized Aggregation Pipelines**
- **Symptom:** High memory usage, slow `$lookup`/`$unwind`.
- **Fix:** Use **`$indexStats`** to validate pipeline steps:
  ```javascript
  db.orders.aggregate([
    { $match: { status: "completed" } },  // Filter early
    { $lookup: { from: "payments", localField: "_id", foreignField: "orderId", as: "payments" } }
  ], { explain: true });
  ```
  - **Optimize:** Add indexes on joined fields, limit `$unwind` output.

---

### **3.2 Reliability Issues**
#### **Problem 4: Replication Lag**
- **Symptom:** `rs.status().members` shows lagging secondary.
- **Diagnosis:**
  ```javascript
  rs.printReplicationInfo();
  ```
  - Check `optime` and `lastHeartbeat` delays.
- **Fix:** Increase oplog size or reduce write volume:
  ```javascript
  sh.enableOplog("cluster", { opLogSizeMB: 1024 });  // Upgrade if needed
  ```

#### **Problem 5: Connection Pool Exhaustion**
- **Symptom:** Timeout errors (121), high `connections` in `db.serverStatus()`.
- **Fix:** Adjust pool settings:
  ```javascript
  // Node.js Driver Example
  const client = new MongoClient(uri, {
    maxPoolSize: 50,    // Default: 100
    minPoolSize: 5,     // Reduce if over-provisioned
    waitQueueTimeoutMS: 10000  // Fail fast
  });
  ```

---

### **3.3 Scalability Issues**
#### **Problem 6: Unscaled Collections**
- **Symptom:** Single node handling >10M writes/sec.
- **Fix:** Shard based on query patterns:
  ```javascript
  sh.enableSharding("db", { shardKey: "customerId" });
  sh.shardCollection("db.orders", { "customerId": 1 } );
  ```
  - **Rule:** Shard on high-cardinality fields used in ranges (`IN` queries).

#### **Problem 7: Hot Partitions**
- **Symptom:** One partition handles 90% of writes.
- **Diagnosis:**
  ```javascript
  db.orders.aggregate([ { $group: { _id: "$customerId", count: { $sum: 1 } } } ]);
  ```
- **Fix:** Reshard or use **time-based sharding**:
  ```javascript
  // Example: Add hash component
  sh.shardCollection("db.orders", { _id: 1, region: 1, $natural: 1 });
  ```

---

## **4. Debugging Tools & Techniques**
### **4.1 Profiling Queries**
- Enable slow query log (4.4+):
  ```javascript
  db.setProfilingLevel(2, { slowms: 100 });  // Log queries >100ms
  ```
- Query the `system.profile` collection:
  ```javascript
  db.system.profile.find().sort({ millis: -1 }).limit(5);
  ```

### **4.2 Monitoring**
- **`mongostat`**: Real-time metrics (latency, ops).
  ```bash
  mongostat -h localhost -p 27017 --metrics always
  ```
- **MongoDB Atlas/Grafana**: Visual dashboards for cluster health.

### **4.3 Log Analysis**
- Key log entries to watch:
  - `{ "level": "S", "msg": "slowWrite" }` (inserts >100ms).
  - `{ "msg": "connection dropped" }` (network issues).

---

## **5. Prevention Strategies**
### **5.1 Schema Design**
- **Embed or Reference?**
  - **Rule:** Embed if data is frequently accessed together (e.g., user + name).
  - **Reference** if data is large or rarely accessed (e.g., product catalogs).

- **Indexing Strategy:**
  - Create indexes for **query, sort, aggregation** predicates.
  - Avoid over-indexing (each index requires ~50% extra storage).

### **5.2 Query Optimization**
- **Avoid `find()` with Projection + `$lookup`:**
  ```javascript
  // Bad: Two network hops
  db.orders.find({ status: "completed" }, { _id: 1 });
  db.payments.find({ orderId: "$_id" });

  // Better: Join in one query
  db.orders.aggregate([
    { $match: { status: "completed" } },
    { $lookup: { from: "payments", localField: "_id", foreignField: "orderId" } }
  ]);
  ```

### **5.3 Replication & Backups**
- **Oplog Size:** Target 10-20% of database size.
- **Backup Strategy:** Use `mongodump` + `mms` (MongoDB Atlas) for automated backups.

### **5.4 Scaling**
- **Sharding:** Start with **2x shards** per collection to avoid hotspots.
- **Read Preference:** Use `secondaryPreferred` for write-heavy apps.

---
## **6. Checklist for Quick Resolution**
| **Step** | **Action** | **Tool** |
|----------|------------|----------|
| 1        | Check `explain()` for slow queries | `db.collection.find().explain()` |
| 2        | Verify indexes | `db.orders.getIndexes()` |
| 3        | Monitor replication lag | `rs.printReplicationInfo()` |
| 4        | Optimize aggregations | `$explain` in pipeline |
| 5        | Reshard if hot partitions | `sh.enableSharding()` |

---
**Final Note:** For persistent issues, review MongoDB’s [Performance Notes](https://www.mongodb.com/docs/manual/core/query-performance/) and use **MongoDB Enterprise** for advanced diagnostics.