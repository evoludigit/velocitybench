---
# **[Data Modeling] MongoDB Database Patterns Reference Guide**

---

## **Overview**
MongoDB’s schema-flexible NoSQL design enables diverse data modeling approaches, but improper patterns can lead to performance bottlenecks, read/write inefficiencies, or scaling issues. This guide documents **key MongoDB database patterns**—**denormalized collections, embedded documents, referenced documents, schema design principles, and index strategies**—to optimize queries, storage, and scalability. Best practices cover trade-offs between normalization vs. denormalization, document structure, relationship handling, and query optimization.

---

## **Core Patterns**

| **Pattern**               | **Use Case**                                                                 | **Pros**                                                                 | **Cons**                                                                 | **Best Practices**                                                                                     |
|---------------------------|------------------------------------------------------------------------------|--------------------------------------------------------------------------|--------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|
| **Embedded Documents**    | One-to-many relationships (e.g., `users` with `addresses` where addresses are rare/read frequently). | - Atomic queries <br> - Simpler joins <br> - Faster reads                | - Update anomalies <br> - Storage bloat <br> - Limited to small docs (<16MB)  | Embed *only* for high-cardinality, low-variability data (e.g., user profiles). Use `denormalize` aggressively. |
| **Referenced Documents**  | Many-to-many or complex relationships (e.g., `orders` referencing `products` and `customers`). | - Atomic updates <br> - No storage duplication <br> - Flexible schema   | - Requires joins (slow for large datasets) <br> - Risk of stale data   | Use for high-cardinality, frequently updated data (e.g., inventory). Normalize where *read consistency* is critical. |
| **Denormalized Collections** | Aggregating data to reduce query complexity (e.g., `orders` with pre-calculated totals). | - Faster reads <br> - Fewer joins                                      | - Higher write overhead <br> - Potential inconsistencies               | Denormalize *only* for read-heavy workloads. Use transactions for consistency.                          |
| **Sharded Keys**          | Horizontal scaling (distributing data across shards).                          | - Scales horizontally <br> - Handles large datasets                     | - Shard key design critical <br> - Complex queries may span shards     | Choose shard keys based on query patterns (e.g., `_id` for even distribution, `region` for locality).      |
| **Time-Series Collections** | Storing time-series data (e.g., IoT sensor readings).                         | - Optimized for time-based queries <br> - Built-in TTL for auto-expiry   | - Limited to time-series use cases                                    | Use `TimeSeriesCollection` for metrics (MongoDB 5.0+). Pre-aggregate data for performance.              |
| **Geospatial Indexes**    | Location-based queries (e.g., "find restaurants within 5km").                  | - Fast geospatial queries <br> - Supports 2D/2dsphere indexes            | - Increased storage overhead                                          | Use `2dsphere` for Earth coordinates. Index `location` field for frequent geospatial lookups.           |
| **Partial Indexes**       | Filtering documents during indexing (e.g., index only documents with `status: "active"`). | - Reduces index size <br> - Faster queries on filtered subsets          | - Limited to specific query patterns                                  | Use for high-cardinality fields (e.g., `user_status`, `order_status`).                                    |
| **Text Indexes**          | Full-text search (e.g., search within `product.description`).                  | - Flexible search <br> - Supports analytics                          | - Slower than exact-match queries                                     | Use `text` index for search-heavy workloads. Combine with `collation` for case-insensitive matching.    |

---

## **Schema Design Principles**

### **1. Denormalization Strategies**
- **Embed when reads > writes**: Example: Embed `user.addresses` if addresses are accessed frequently.
  ```javascript
  // ✅ Embedded (read-optimized)
  {
    _id: ObjectId("..."),
    name: "Alice",
    addresses: [
      { city: "NYC", type: "home" },
      { city: "SF", type: "work" }
    ]
  }
  ```
- **Reference when updates > reads**: Example: Reference `products` in `orders` if products change often.
  ```javascript
  // ✅ Referenced (write-optimized)
  {
    _id: ObjectId("..."),
    customer: ObjectId("user-123"),
    products: [ObjectId("prod-456"), ObjectId("prod-789")]
  }
  ```

### **2. Avoiding Data Duplication**
- **Use `populate()` for joins** (instead of in-app joins) to fetch referenced data efficiently:
  ```javascript
  // MongoDB Query (using populate)
  db.orders.find({})
    .populate({
      path: "customer",
      select: "name email"
    });
  ```
- **Materialized views**: Pre-compute aggregations (e.g., `user_stats`) in a separate collection.

### **3. Document Structure**
- **Flat is faster**: Limit nesting (e.g., avoid `user.profile.addresses[0].city`; flatten to `user.home_city`).
- **Avoid arrays of objects**: Replace with embedded docs if possible (e.g., `tags: ["A", "B"]` → `tags: [{ name: "A" }, { name: "B" }]`).

---

## **Query Optimization**

### **Indexing Strategies**
| **Index Type**       | **Use Case**                          | **Example**                                  |
|----------------------|---------------------------------------|---------------------------------------------|
| **Single Field**     | Equality/range queries.               | `db.users.createIndex({ email: 1 })`        |
| **Compound Index**   | Multi-field queries (order matters).  | `db.orders.createIndex({ customer: 1, date: -1 })` |
| **TTL Index**        | Auto-expiry for time-series data.     | `db.logs.createIndex({ timestamp: 1 }, { expireAfterSeconds: 300 })` |
| **Text Index**       | Full-text search.                     | `db.products.createIndex({ description: "text" })` |
| **2dsphere Index**   | Geospatial queries.                   | `db.locations.createIndex({ location: "2dsphere" })` |

### **Performance Anti-Patterns**
- **❌ Scans**: Avoid `find()` without an index.
  ```javascript
  // Slow: No index on `status`
  db.orders.find({ status: "shipped" });
  ```
- **❌ Deeply nested queries**: Limit array traversal (e.g., `$elemMatch` on arrays).
- **❌ Over-fragmented shards**: Use balanced shard keys (e.g., hash-based for uniform distribution).

---

## **Common Pitfalls & Solutions**

| **Pitfall**                          | **Solution**                                                                 |
|---------------------------------------|------------------------------------------------------------------------------|
| **Update anomalies** (e.g., partial updates in embedded docs). | Use atomic operators (`$set`, `$push`) or transactions.                        |
| **Over-normalization** (joins for everything).                  | Denormalize aggressively for read-heavy apps; use references for write-heavy. |
| **Shard key skew** (uneven data distribution).                  | Analyze query patterns; use compound shard keys (e.g., `country:region`).      |
| **Storage bloat** (duplicate data).                               | Use `denormalize` judiciously; consider materialized views.                   |
| **Index cardinality issues** (low-selectivity indexes).          | Drop unused indexes; prefer high-cardinality fields (e.g., `email` over `gender`). |

---

## **Query Examples**

### **1. Embedded Documents (Read-Optimized)**
**Collection**: `users`
```javascript
// Query: Find users in "NYC"
db.users.find({
  "addresses.city": "NYC"
});
```
**Result**:
```json
{
  "_id": ObjectId("..."),
  "name": "Alice",
  "addresses": [
    { "city": "NYC", "type": "home" }
  ]
}
```

### **2. Referenced Documents (Write-Optimized)**
**Collections**: `orders`, `products`
```javascript
// Query: Find orders with product ID "prod-123"
db.orders.find({
  "products": ObjectId("prod-123")
}).populate("products");
```
**Result**:
```json
{
  "_id": ObjectId("..."),
  "products": [
    {
      "_id": ObjectId("prod-123"),
      "name": "Laptop"
    }
  ]
}
```

### **3. Aggregation Pipeline (Denormalized)**
**Collection**: `sales`
```javascript
// Pre-aggregate daily sales by product
db.sales.aggregate([
  { $match: { date: { $gte: ISODate("2023-01-01") } } },
  { $group: {
      _id: "$product_id",
      total: { $sum: "$amount" }
  }},
  { $lookup: {
      from: "products",
      localField: "_id",
      foreignField: "_id",
      as: "product"
  }}
]);
```

### **4. Geospatial Query**
**Collection**: `restaurants`
```javascript
// Find restaurants within 5km of coordinate (40.7128, -74.0060)
db.restaurants.find({
  location: {
    $near: {
      $geometry: { type: "Point", coordinates: [-74.0060, 40.7128] },
      $maxDistance: 5000 // meters
    }
  }
});
```

### **5. Text Search**
**Collection**: `articles`
```javascript
// Search for "mongodb" in title/body
db.articles.find({
  $text: { $search: "mongodb" }
});
```

---

## **Related Patterns**
1. **Data Partitioning**:
   - [Sharding](#sharded-keys) for horizontal scaling.
   - [Time-Series Collections](#time-series-collections) for event data.
2. **Query Patterns**:
   - [Projection](https://www.mongodb.com/docs/manual/tutorial/project-fields-in-query-results/) to fetch only needed fields.
   - [Aggregation Framework](https://www.mongodb.com/docs/manual/aggregation/) for complex analytics.
3. **Schema Evolution**:
   - [Schema Validation](https://www.mongodb.com/docs/manual/core/schema-validation/) to enforce structure.
   - [Multi-Document ACID Transactions](https://www.mongodb.com/docs/manual/core/transactions/) for consistency.
4. **Performance**:
   - [Index Design](https://www.mongodb.com/docs/manual/core/indexes/) for query optimization.
   - [Read/Write Concerns](https://www.mongodb.com/docs/manual/core/read-write-concern/) for consistency guarantees.

---

## **Further Reading**
- [MongoDB Official Documentation](https://www.mongodb.com/docs/)
- [MongoDB University Courses](https://university.mongodb.com/)
- [Atlas Performance Guidelines](https://www.mongodb.com/docs/atlas/performance/)