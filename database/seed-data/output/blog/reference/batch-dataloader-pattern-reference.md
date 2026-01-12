---

# **[Pattern] Batch DataLoader Pattern**
*Optimizing GraphQL Query Efficiency with Batch Loading*

---

## **Overview**
The **Batch DataLoader Pattern** mitigates the **N+1 query problem** in GraphQL applications by batching multiple database operations into a single optimized query. Introduced in **FraiseQL**, this pattern leverages **deduplication, caching, and strategic execution ordering** to fetch related data efficiently. Unlike imperative `findAll()` calls, DataLoader ensures:
- **Reduced database round trips** (batching reduces overhead).
- **Automatic deduplication** (avoids fetching duplicate records).
- **Caching** (reuses results for repeated requests).
- **Parallel processing** (optimizes query execution order).

This pattern is ideal for **embedded systems, real-time analytics, or high-frequency GraphQL APIs** where performance is critical.

---

## **Key Concepts**
| **Term**               | **Description**                                                                                                                                                                                                 |
|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Batch Loading**      | Groups multiple `find()`/`load()` operations into a single database query.                                                                                                                                  |
| **Deduplication**      | Skips redundant requests for already-resolved keys (e.g., if `users[1]` and `users[1]` are requested twice, it fetches only once).                                             |
| **Cache**              | Stores resolved data (e.g., in-memory map) to avoid reprocessing.                                                                                                                                         |
| **Execution Order**    | Resolves dependencies in parallel where possible (e.g., parent-child relationships).                                                                                                                      |
| **Error Handling**     | Isolates failures in batch operations without breaking the entire query.                                                                                                                                     |
| **Primitive Loader**   | Handles basic batch operations (e.g., `loadMany()`, `loadManyParallel()`).                                                                                                                                    |
| **Composite Loader**   | Combines multiple loaders (e.g., for nested relationships).                                                                                                                                                 |

---

## **Schema Reference**
Below is the core **FraiseQL DataLoader schema** with key methods and their signatures.

| **Component**          | **Method**                     | **Description**                                                                                                                                                                                                 | **Parameters**                                                                 | **Returns**                                                                                     |
|------------------------|--------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| **PrimitiveLoader**    | `load(key)`                    | Resolves a single key (synchronous).                                                                                                                                                                   | `key: K` (e.g., `userId: UUID`)                                                      | `Promise<Optional<V>>` (resolved value or `null`).                                              |
|                        | `loadMany(keys)`               | Batches a list of keys for a single query.                                                                                                                                                            | `keys: K[]` (e.g., `[userId1, userId2]`)                                              | `Promise<Map<K, Optional<V>>>` (mapped results).                                             |
|                        | `loadManyParallel(keys)`       | Batches keys with parallel execution (for independent queries).                                                                                                                                    | `keys: K[]`                                                                         | `Promise<Map<K, Optional<V>>>` (parallel results).                                            |
| **BatchLoaderABI**     | `load(batchKeys)`              | Abstract method for custom batch implementations.                                                                                                                                                      | `batchKeys: K[][]` (grouped keys for optimization)                                        | `Promise<BatchValueResult<V>>` (deduplicated + cached results).                              |
| **CompositeLoader**    | `load(keys)`                   | Combines multiple loaders (e.g., `UserLoader` + `PostLoader`).                                                                                                                                          | `keys: O` (object with nested keys)                                                    | `Promise<O>` (resolved composite structure).                                                   |
| **DefaultLoader**      | `createDefaultLoader`          | Factory method to create a `BatchLoaderABI`-compliant loader.                                                                                                                                             | `loadFn: (keys: K[]) => Promise<V[]>` (custom batch logic)                             | `BatchLoader<K, V>` instance.                                                               |
| **Cache**              | `primitiveLoaderCache`         | In-memory cache for primitive loaders.                                                                                                                                                                | –                                                                                   | `Map<K, V>` (default: `LRUCache`).                                                           |

---

## **Query Examples**
### **1. Basic PrimitiveLoader (Single Key)**
```javascript
// Fetch a single user by ID (no batching)
const userLoader = new PrimitiveLoader<UUID, User>(userId => db.getUser(userId));
const user = await userLoader.load("123e4567-e89b-12d3-a456-426614174000");
```
**Output:**
```json
{ "id": "123e4567-e89b-12d3-a456-426614174000", "name": "Alice" }
```

---

### **2. Batched Loading (Multiple Keys)**
```javascript
// Fetch multiple users in one query
const userIds = ["123e4567-e89b-12d3-a456-426614174000", "456e789a-b12d-3456-90ab-cdef12345678"];
const batchResults = await userLoader.loadMany(userIds);
```
**Output:**
```json
{
  "123e4567-e89b-12d3-a456-426614174000": { "id": "...", "name": "Alice" },
  "456e789a-b12d-3456-90ab-cdef12345678": { "id": "...", "name": "Bob" }
}
```

---

### **3. Parallel Loading (Independent Queries)**
```javascript
// Fetch unrelated posts (parallel execution)
const postLoader = new PrimitiveLoader<PostId, Post>(postId => db.getPost(postId));
const posts = await postLoader.loadManyParallel(["post-1", "post-2", "post-3"]);
```
**Output:**
```json
{
  "post-1": { "id": "post-1", "title": "Hello" },
  "post-2": { "id": "post-2", "title": "World" }
}
```

---

### **4. CompositeLoader (Nested Relationships)**
```javascript
// Fetch users + their posts in one batch
const userLoader = new PrimitiveLoader<UUID, User>(...);
const postLoader = new PrimitiveLoader<PostId, Post>(...);
const compositeLoader = new CompositeLoader({
  userLoader,
  postLoader: (user: User) => user.postIds.map(id => ({ postId: id })),
});

const user = await compositeLoader.load({ userId: "123e4567-e89b-12d3-a456-426614174000" });
```
**Output:**
```json
{
  "user": { "id": "123e4567-e89b-12d3-a456-426614174000", "name": "Alice" },
  "posts": [
    { "id": "post-1", "title": "Hello" },
    { "id": "post-2", "title": "World" }
  ]
}
```

---

### **5. Custom BatchLoader Implementation**
```javascript
// Define a custom batch loader for optimized SQL queries
const customLoader = DataLoader.createBatchLoader<UUID, User>(
  async (userIds) => {
    const [users] = await db.query(`
      SELECT * FROM users WHERE id IN (?)
    `, [userIds]);
    return userIds.map(id => users.find(u => u.id === id));
  }
);
const users = await customLoader.loadMany(["1", "2", "3"]);
```

---

## **Advanced Considerations**
### **1. Error Handling**
DataLoader isolates failures per batch:
```javascript
try {
  const results = await userLoader.loadMany(["valid-id", "invalid-id"]);
  console.log("Success:", results);
} catch (error) {
  console.error("Batch failed:", error);
  // Only invalid-id is missing; others are cached.
}
```

### **2. Cache Strategies**
- **TTL (Time-to-Live):** Set cache expiration for dynamic data.
  ```javascript
  const loader = new PrimitiveLoader<UUID, User>(...);
  loader.setCacheTTL(60); // Cache for 60 seconds.
  ```
- **Manual Eviction:** Clear cache when data changes.
  ```javascript
  await loader.clear("123e4567-e89b-12d3-a456-426614174000");
  ```

### **3. Batch Size Limits**
Configure max batch size to avoid overwhelming the database:
```javascript
const loader = new PrimitiveLoader<UUID, User>(
  ...,
  { batchSize: 1000 } // Max 1000 keys per batch
);
```

### **4. Dependency Injection**
Use dependency injection for testability:
```javascript
// In a service:
class UserService {
  constructor(private userLoader: PrimitiveLoader<UUID, User>) {}
  async getUser(id: UUID) {
    return await this.userLoader.load(id);
  }
}
```

---

## **Performance Benchmarks**
| **Scenario**               | **Without DataLoader** | **With DataLoader** | **Improvement** |
|----------------------------|------------------------|---------------------|-----------------|
| 10 users (10 queries)      | 10 DB round trips      | 1 DB round trip      | **90% reduction** |
| 100 users (100 queries)    | 100 DB round trips     | 1 DB round trip      | **99% reduction** |
| Nested relationships       | 15 queries             | 3 queries           | **80% reduction** |

---

## **Related Patterns**
1. **[GraphQL N+1 Problem](https://www.apollographql.com/docs/devtools/graphql-playground/#n1)**
   - *Problem:* Excessive database queries due to naive resolver implementations.
   - *Solution:* DataLoader batches queries to resolve this.

2. **[Cursor-based Pagination](https://www.apollographql.com/docs/react/data/pagination/)**
   - *Use Case:* Combine with DataLoader for efficient paginated queries.
   - *Example:*
     ```javascript
     const posts = await postLoader.loadMany(
       paginationCursor.map(cursor => ({ cursor }))
     );
     ```

3. **[Data Skipping & Streams](https://spec.graphql.org/October2021/#sec-DataSkippingAndStreams)**
   - *Use Case:* Skip unnecessary fields in batches using `DataLoader` + `Data Skipping`.
   - *Example:*
     ```javascript
     const userLoader = new PrimitiveLoader<UUID, User>(...);
     const user = await userLoader.load("123e4567-e89b-12d3-a456-426614174000");
     // Skip posts if not needed:
     const { posts, ...rest } = user;
     ```

4. **[Connection-based Loaders](https://github.com/graphql/dataloader#connection-based-loading)**
   - *Use Case:* Optimize for large datasets with connections (e.g., `edges` in GraphQL).
   - *Example:*
     ```javascript
     const connectionLoader = new DataLoader(
       async ({ cursor, first }) => await db.getConnection(cursor, first)
     );
     ```

5. **[Eventual Consistency Patterns](https://martinfowler.com/eaaCatalog/eventualConsistency.html)**
   - *Use Case:* Combine with DataLoader for background synchronization (e.g., caches that update asynchronously).

---

## **When to Avoid DataLoader**
- **Read-Only APIs:** If data never changes, simple caching may suffice.
- **Small Datasets:** Overhead of batching may not justify gains (e.g., <10 queries).
- **Non-Deterministic Queries:** If results depend on runtime state (e.g., user-specific filters), batching may not help.

---

## **FraiseQL-Specific Optimizations**
| **Feature**               | **Implementation**                                                                 |
|---------------------------|------------------------------------------------------------------------------------|
| **Automatic Dedupe**      | Uses `Map`-based caching to eliminate duplicate keys.                              |
| **Parallel Batch Fetch**  | Leverages `fetchAllParallel` for independent queries.                              |
| **SQL Generator**         | Optimizes `IN` clauses for large batches (e.g., splits into chunks for PostgreSQL).|
| **TypeScript Support**    | Strongly typed keys/values (e.g., `PrimitiveLoader<UUID, User>`).                  |

---
**Key Takeaway:** The **Batch DataLoader Pattern** is a **must-use** for GraphQL APIs targeting performance-critical embedded systems, where minimizing database load is non-negotiable. Pair it with **composite loaders** for nested data and **connection-based loading** for large datasets.