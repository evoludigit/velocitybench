# **[Pattern] CouchDB Database Patterns: Reference Guide**

---

## **Overview**
CouchDB is a NoSQL, document-oriented database optimized for scalability, distributed operation, and fault tolerance. Unlike relational databases, CouchDB stores data as **JSON-like documents** with flexible schemas, enabling rapid application development and agile data modeling. This guide covers key **CouchDB database patterns**, including **denormalization strategies, document design, indexing, and replication**, along with implementation details, best practices, and common pitfalls. Whether you're building a real-time collaboration tool, a content management system, or a distributed analytics platform, these patterns help structure data efficiently for performance, consistency, and maintainability.

---

## **Key Concepts & Schema Reference**

| **Concept**               | **Description**                                                                                                                                                                                                 | **Example**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Document-Oriented**     | Data is stored as semi-structured JSON documents with unique `_id` and `_rev` fields. Documents can vary in schema.                                                                                     | `{ "_id": "user_123", "name": "Alice", "roles": ["admin"], "created_at": "2023-01-01" }`    |
| **Denormalization**       | Redundant data is intentionally duplicated for faster reads (trade-off with write overhead). CouchDB excels at this due to its document model.                                                                 | Storing `user_id` in `orders` documents instead of joining tables.                             |
| **Atomic Updates**        | `_rev` (revision) ensures conflict-free updates. Each write generates a new `_rev`. Conflicts are resolved manually or via `update` handlers.                                                                 | `{ "_rev": "2-abc123", "value": 42 }` → Next update: `{ "_rev": "3-def456", ... }`          |
| **Views (Map-Reduce)**    | Precomputed indexes (via `map` functions) for efficient querying. Supports `startkey`, `limit`, `group` clauses. Views are stored locally and replicated across nodes.                                     | `function(doc) { if(doc.type === "order") emit(doc.user_id, doc.total); }`                    |
| **Mango Queries**         | Native JSON query syntax for complex filtering, sorting, and projection. Faster for ad-hoc queries than views.                                                                                             | `{ "selector": { "status": "completed", "date": { "$gte": "2023-01-01" } } }`              |
| **Attachments**           | Binary data (images, files) stored as attachments to documents. Useful for media-heavy apps.                                                                                                                   | Document `_attachments`: `{ "profile_picture": { "content_type": "image/jpeg", "data": "..." } }` |
| **Replication**           | Built-in **peer-to-peer (CouchDB-CouchDB)** or **HTTP (CouchDB-Non-CouchDB)** replication for syncing distributed databases.                                                                                | `replicator` design doc for bidirectional sync: `{ "_id": "_replicator", ... }`               |
| **Security**              | Role-based access control (RBAC) via `_users` and `_roles` databases. Each document can define `_security` for granular permissions.                                                                          | `{ "design": "docs", "views": { "private": { "map": "...", "access": "private" } } }`       |
| **Full-Text Search**      | Use the `couchdb-lucene` or `esquery` plugin for advanced search capabilities.                                                                                                                               | `esquery` for Elasticsearch-like queries (e.g., `match: { content: "quick brown fox" }`).     |
| **Multi-Tenancy**         | Isolate tenants via **database-per-tenant** or **document-sharding** (e.g., `_tenant_id` prefix in `_id`).                                                                                                   | `{ "_id": "tenant_abc_order_123", "tenant": "abc", ... }`                                      |

---

## **Implementation Details**

### **1. Document Design Best Practices**
- **Keep documents "fat" for queries**: Denormalize to avoid expensive joins. Example:
  ```json
  // Instead of:
  { "_id": "user_123", "orders": ["order_1", "order_2"] }

  // Use:
  { "_id": "user_123", "name": "Alice", "orders": [
      { "order_id": "order_1", "total": 99.99, "items": [...] },
      { "order_id": "order_2", "total": 149.99, "items": [...] }
    ] }
  ```
- **Use `_id` prefixes** for namespacing (e.g., `user_`, `order_`, `event_`).
- **Avoid circular references**: Replace references with `_id` fields (e.g., `user_id: "user_123"` instead of embedding a full user object).

### **2. Indexing Strategies**
| **Strategy**          | **Use Case**                                  | **Implementation**                                                                 |
|-----------------------|-----------------------------------------------|------------------------------------------------------------------------------------|
| **Views (Map-Reduce)** | Predefined aggregations (e.g., user orders)    | Define in `design/doc` (e.g., `_design/orders/views/by_user`).                     |
| **Mango Queries**     | Ad-hoc filtering/sorting                      | Use `POST /db/_find` with JSON query syntax.                                        |
| **Global Change**     | Track all document changes                     | Enable `_global_changes` feed for real-time updates.                                |
| **Compound Indexes**  | Multi-field queries                           | Design views with composite keys (e.g., `emit([doc.user_id, doc.date])`).        |

### **3. Denormalization Trade-offs**
| **Pros**                          | **Cons**                                                                 |
|-----------------------------------|--------------------------------------------------------------------------|
| Faster reads (no joins)            | Higher storage/bandwidth usage.                                           |
| Simpler queries                   | Write conflicts if not managed carefully (use `update` handlers).          |
| Scales horizontally                | Requires careful design to avoid "document explosion."                     |

### **4. Conflict Resolution**
- **Last-Write-Wins (LWW)**: Enable with `_rev` comparisons (default).
- **Custom Handling**: Use `_update` handlers to merge conflicts:
  ```javascript
  function(doc, req) {
    if (doc.conflicts && doc.conflicts.length) {
      // Resolve conflicts (e.g., take max revision or merge fields).
      doc.resolved_value = Math.max(...doc.conflicts.map(c => c.rev));
    }
    return doc;
  }
  ```

### **5. Replication Considerations**
- **Bidirectional Sync**: Use `replicator` design doc:
  ```json
  {
    "_id": "_replicator",
    "source": "http://source_db:5984/db",
    "target": "http://target_db:5984/db",
    "create_target": true,
    "continuous": true
  }
  ```
- **Filtering Replication**: Use `_replication_filter` to sync only specific documents.
- **Sync Gateway**: For mobile/offline apps, use [PouchDB](https://pouchdb.com/) + CouchDB sync.

---

## **Query Examples**

### **1. Basic View Query**
**Design Doc:**
```json
{
  "_id": "_design/orders",
  "views": {
    "by_user": {
      "map": "function(doc) { if (doc.type === 'order') emit(doc.user_id, doc); }"
    }
  }
}
```
**Query:**
```bash
GET /db/_design/orders/_view/by_user?key="user_123"
```
**Response:**
```json
{
  "rows": [
    { "key": "user_123", "value": { "order_id": "order_1", ... } }
  ]
}
```

### **2. Mango Query (JSON)**
```bash
POST /db/_find
{
  "selector": {
    "status": "completed",
    "date": { "$gte": "2023-01-01" },
    "items": { "$elemMatch": { "price": { "$gt": 50 } } }
  },
  "fields": ["order_id", "total"]
}
```

### **3. Full-Text Search (with `esquery` plugin)**
```bash
POST /db/_esquery
{
  "query": {
    "match": { "description": "wireless headphones" }
  }
}
```

### **4. Global Change Feed (Real-Time Updates)**
```bash
GET /db/_changes?feed=continuous&since=now
```
**Response (WebSocket-like stream):**
```json
{ "id": "doc_123", "seq": 1234, "changes": [{ "rev": "456-abc" }] }
```

### **5. Attachment Handling**
**Upload:**
```bash
PUT /db/doc_123?rev=3-abc123&attachment=photo.jpg
```
**Download:**
```bash
GET /db/doc_123/photo.jpg
```

---

## **Best Practices**

1. **Schema Flexibility**: Leverage CouchDB’s schema-less nature, but document evolving schemas in a `schema/versions` document.
2. **Pagination**: Use `skip`/`limit` in views or `_all_docs?limit=100&startkey="A"`.
3. **Batch Operations**: Use `bulk_docs` for multiple writes (reduces overhead):
   ```bash
   POST /db/_bulk_docs
   {
     "docs": [
       { "_id": "doc1", "value": 1 },
       { "_id": "doc2", "value": 2 }
     ]
   }
   ```
4. **Monitoring**: Use `_stats` and `_active_tasks` endpoints to track performance:
   ```bash
   GET /db/_stats
   ```
5. **Backup**: Regularly replicate to a secondary node or use `couchdb-backup` tool.

---

## **Common Pitfalls & Solutions**

| **Pitfall**                          | **Solution**                                                                 |
|---------------------------------------|--------------------------------------------------------------------------------|
| **Over-normalization**               | Denormalize aggressively for read-heavy workloads.                            |
| **View Staleness**                    | Use `_local_docs` or `_replicator` to sync views across nodes.               |
| **Memory Bloat**                      | Limit view memory usage with `reduce=true` (for aggregations only).          |
| **Attachment Limits**                 | Compress large attachments (e.g., use base64 or external storage).           |
| **Conflicts in Replication**          | Implement `update` handlers or use `async_replication` with conflict resolution. |
| **No Transactions**                   | Simulate ACID with `update` handlers or external systems (e.g., Kafka).     |

---

## **Related Patterns**

1. **Event Sourcing**
   - Store historical state changes as immutable documents. Useful for auditing and time-travel debugging.
   - *Example*: `{ "_id": "user_123_events", "events": [{ "type": "login", "timestamp": "2023-01-01" }] }`

2. **Sharding by Time**
   - Split documents by date (e.g., `logs_2023-01`) for easier archiving and scaling.
   - *Tool*: Use `couchdb-shards` or custom `_id` prefixes.

3. **CAP Trade-offs**
   - CouchDB prioritizes **Availability + Partition Tolerance (AP)**. For strong consistency, use single-node setups or external coordination (e.g., ZooKeeper).

4. **Mobile Offline-First**
   - Pair CouchDB with [PouchDB](https://pouchdb.com/) for offline sync and conflict resolution.
   - *Example*: `pouchdb.sync(local_db, remote_couchdb_url)`.

5. **Multi-Document Transactions**
   - Use `update` handlers with HTTP `207 Multi-Status` to simulate atomicity across documents.

6. **Data Lake Integration**
   - Export CouchDB documents to S3/HDFS for analytics using tools like [CouchDB to Spark](https://github.com/apache/couchdb-spark).

---

## **Tools & Extensions**
| **Tool**               | **Purpose**                                                                 |
|------------------------|-----------------------------------------------------------------------------|
| [Fauxton](https://fauxton.io/) | Web-based admin interface for CouchDB.                                     |
| [BigCouch](https://github.com/cloudant/bigcouch) | Distributed CouchDB for horizontal scaling.                                |
| [CouchDB HTTP API](https://docs.couchdb.org/en/stable/api/intro.html) | RESTful CRUD operations.                                                  |
| [CouchDB Plugins](https://docs.couchdb.org/en/stable/plugins/) | Extend functionality (e.g., `couchdb-lucene`, `esquery`).                 |
| [DDP (Meteor)](https://www.meteor.com/ddp) | Real-time bidirectional sync for web apps.                                |
| [CouchDB CLI](https://docs.couchdb.org/en/stable/cli.html) | `couchjs` and `couchadmin` for scripting.                                  |

---
## **Further Reading**
- [CouchDB Official Docs](https://docs.couchdb.org/)
- ["CouchDB: The Definitive Guide"](https://www.oreilly.com/library/view/couchdb-the-definitive/9781449303096/) (O’Reilly)
- [Designing Data-Intensive Applications](https://dataintensive.net/) (Chapters on NoSQL)
- [PouchDB Docs](https://pouchdb.com/) (Offline-first patterns)