# **[Pattern] API Pagination Patterns – Reference Guide**

---

## **Overview**
Pagination improves API efficiency by splitting large datasets into smaller, manageable chunks rather than returning all results in a single response. Without pagination, a single endpoint (e.g., fetching all users) could return thousands or millions of records, overwhelming clients and causing performance degradation, latency, or service outages.

Three primary pagination strategies exist, each balancing trade-offs between simplicity, performance, and consistency:
- **Offset-based pagination** (e.g., `?page=2&limit=10`) uses fixed numeric offsets, which is intuitive but inefficient for large datasets due to slow scans or updates when the offset grows.
- **Cursor-based pagination** (e.g., `?cursor=abc123`) leverages opaque tokens to track position, avoiding repeated full scans but requiring consistent sorting across tables or database clusters.
- **Keyset pagination** (e.g., `?after=123&before=456`) uses ordered column values (e.g., IDs) to fetch records in a range, ideal for streams but requiring strict ordering guarantees.

This guide covers implementation details, schema designs, and examples for each approach, including query patterns for REST, GraphQL (Relay Connections), and database-agnostic implementations.

---

## **Schema Reference**
Below are key schema components for pagination patterns. All examples assume a `User` model with an `id` (primary key) and `name` fields.

| **Component**               | **Description**                                                                 | **Example**                          |
|-----------------------------|---------------------------------------------------------------------------------|--------------------------------------|
| **Offset-based**            | `limit` and `offset` parameters define result range.                           | `{ limit: 10, offset: 0 }`           |
| **Cursor-based**            | `cursor` and `limit` use opaque tokens to track position (e.g., encoded offsets). | `{ cursor: "abc123", limit: 10 }`    |
| **Keyset-based**            | `after`/`before` use ordered values (e.g., IDs) to fetch ranges.               | `{ after: 100, before: 200 }`        |
| **Relay Connection** (GraphQL) | Fields like `edges`, `pageInfo`, and `cursor` for incremental loading.          | `{ edges: [...], pageInfo: { hasNextPage: true } }` |

---

## **Implementation Patterns**

### **1. Offset-Based Pagination**
**Best for:** Simple use cases where data volume is low or consistent.

#### **Schema Design**
- **Query Parameters:**
  - `limit` (int): Number of items per page (recommended: ≤ 100).
  - `offset` (int): Starting index for the page (0-based).

- **Example Response:**
  ```json
  {
    "data": [
      { "id": 1, "name": "Alice" },
      { "id": 2, "name": "Bob" }
    ],
    "metadata": {
      "total": 100,
      "limit": 2,
      "offset": 0
    }
  }
  ```

#### **Database Query (SQL Example)**
```sql
-- Offset-based pagination in SQL (inefficient for large offsets)
SELECT * FROM users
ORDER BY id
LIMIT 2 OFFSET 0;
```

#### **Code Example (REST Endpoint)**
```javascript
// Pseudocode: Node.js/Express
router.get("/users", (req, res) => {
  const { limit = 10, offset = 0 } = req.query;
  const users = await db.query(
    "SELECT * FROM users ORDER BY id LIMIT ? OFFSET ?",
    [limit, offset]
  );
  res.json({ data: users, metadata: { limit, offset, total: await db.count() } });
});
```

#### **Pros/Cons**
✅ **Simple to implement and understand.**
❌ **Performance degrades with large offsets** (e.g., `OFFSET 1000000` requires a full scan).
❌ **No consistent cursor for incremental loads** (e.g., real-time updates).

---

### **2. Cursor-Based Pagination**
**Best for:** High-volume APIs where offsets are inefficient (e.g., social media feeds).

#### **Schema Design**
- **Cursor Format:** Typically encoded as a Base64/URL-safe string of:
  - Database cursor (e.g., MySQL `cursor()` function).
  - Client-generated tokens (e.g., `last_seen_id`).
- **Query Parameters:**
  - `cursor` (string): Unique token for the next page (e.g., `after:abc123`).
  - `limit` (int): Items per page.

- **Example Response:**
  ```json
  {
    "data": [
      { "id": 3, "name": "Charlie" }
    ],
    "metadata": {
      "next_cursor": "def456",
      "total": 100,
      "limit": 1
    }
  }
  ```

#### **Database Implementation (MySQL)**
```sql
-- Generate a cursor for the last fetched row
SELECT cursor() INTO @current_cursor FROM users ORDER BY id DESC LIMIT 1;

-- Use the cursor in the next query
SELECT * FROM users
WHERE cursor() > @current_cursor
ORDER BY id
LIMIT 1;
```

#### **Code Example (REST Endpoint)**
```javascript
router.get("/users", (req, res) => {
  const { cursor, limit = 10 } = req.query;
  let query = "SELECT * FROM users ORDER BY id ASC LIMIT ?";
  const params = [limit];

  if (cursor) {
    // Decode cursor (e.g., Base64) and use in WHERE clause
    const lastId = decodeCursor(cursor);
    query += ` WHERE id > ?`;
    params.push(lastId);
  }

  const users = await db.query(query, params);
  res.json({
    data: users,
    next_cursor: generateCursor(users[users.length - 1].id)
  });
});
```

#### **Pros/Cons**
✅ **Efficient for large datasets** (avoids full scans).
✅ **Supports incremental updates** (e.g., real-time feeds).
❌ **Cursor management complexity** (encoding/decoding).
❌ **Requires consistent sorting** across database shards.

---

### **3. Keyset Pagination**
**Best for:** Ordered data (e.g., timestamps, IDs) where cursor-based tokens are impractical.

#### **Schema Design**
- **Query Parameters:**
  - `after` (value): Fetch records **after** this value (e.g., `after=100`).
  - `before` (value): Fetch records **before** this value (e.g., `before=200`).
  - `limit` (int): Items per page.

- **Example Response:**
  ```json
  {
    "data": [
      { "id": 101, "name": "Dave" },
      { "id": 102, "name": "Eve" }
    ],
    "metadata": {
      "has_next_page": true,
      "after": 102
    }
  }
  ```

#### **Database Query (SQL)**
```sql
-- Fetch records after a given ID
SELECT * FROM users
WHERE id > 100
ORDER BY id
LIMIT 10;
```

#### **Code Example (REST Endpoint)**
```javascript
router.get("/users", (req, res) => {
  const { after, before, limit = 10 } = req.query;
  let query = "SELECT * FROM users ORDER BY id ASC LIMIT ?";
  const params = [limit];

  if (after) {
    query += ` WHERE id > ?`;
    params.push(parseInt(after));
  }
  if (before) {
    query += ` WHERE id < ?`;
    params.push(parseInt(before));
  }

  const users = await db.query(query, params);
  const hasNextPage = users.length === limit;
  res.json({
    data: users,
    metadata: {
      hasNextPage,
      after: hasNextPage ? users[users.length - 1].id : null
    }
  });
});
```

#### **Pros/Cons**
✅ **Simple and efficient** for ordered data (e.g., timestamps, IDs).
✅ **No cursor encoding/decoding needed**.
❌ **Requires strict ordering** (e.g., primary key or unique column).
❌ **Cannot paginate arbitrarily** (e.g., no random access).

---

### **4. GraphQL Relay Connection Spec**
**Best for:** GraphQL APIs needing incremental loading (e.g., React with Apollo).

#### **Schema Design**
- **Fields:**
  - `edges`: Array of `{ cursor, node }` objects.
  - `pageInfo`: `{ hasNextPage, hasPreviousPage, startCursor, endCursor }`.
  - `totalCount` (optional): Total records.

- **Example Query:**
  ```graphql
  query {
    users(first: 10, after: "YXJyYXljb25uZWN0aW9uOjE=") {
      edges {
        cursor
        node {
          id
          name
        }
      }
      pageInfo {
        hasNextPage
        endCursor
      }
    }
  }
  ```

#### **Resolver Code Example (Node.js)**
```javascript
const resolvers = {
  Query: {
    users: async (_, { first, after }, { db }) => {
      const args = { limit: first };
      if (after) {
        args.after = after; // Decoded cursor or ID
      }
      const users = await db.paginate("users", args);
      return {
        edges: users.map(u => ({ cursor: generateCursor(u.id), node: u })),
        pageInfo: {
          hasNextPage: users.length === first,
          endCursor: generateCursor(users[users.length - 1].id)
        }
      };
    }
  }
};
```

#### **Database Implementation (PostgreSQL JSONB)**
```sql
-- Example for cursor-based pagination in PostgreSQL
WITH paginated AS (
  SELECT *,
    row_number() OVER (ORDER BY id) AS row_num
  FROM users
  WHERE id > to_number(split_part(cast('YXJyYXljb25uZWN0aW9uOjE='::bytea, ':', 'b'), 2))
  LIMIT 10
)
SELECT * FROM paginated;
```

#### **Pros/Cons**
✅ **Standardized for GraphQL** (works with Relay, Apollo).
✅ **Supports incremental loading** (e.g., React `useLazyLoadQuery`).
❌ **Overhead for REST clients**.
❌ **Cursor complexity** (must handle encoding/decoding).

---

## **Query Examples**

### **Offset-Based**
**Request:**
```
GET /users?limit=5&offset=10
```
**Response:**
```json
{
  "data": [
    { "id": 11, "name": "Charlie" },
    { "id": 12, "name": "Dave" }
  ],
  "metadata": {
    "total": 100,
    "limit": 5,
    "offset": 10
  }
}
```

### **Cursor-Based**
**Request:**
```
GET /users?limit=5&cursor=abc123
```
**Response:**
```json
{
  "data": [
    { "id": 13, "name": "Eve" }
  ],
  "metadata": {
    "next_cursor": "def456",
    "total": 100
  }
}
```

### **Keyset-Based**
**Request:**
```
GET /users?limit=5&after=10
```
**Response:**
```json
{
  "data": [
    { "id": 11, "name": "Charlie" }
  ],
  "metadata": {
    "has_next_page": true,
    "after": 12
  }
}
```

### **GraphQL Relay**
**Query:**
```graphql
query {
  users(first: 5, after: "YXJyYXljb25uZWN0aW9uOjE=") {
    edges {
      cursor
      node { id }
    }
    pageInfo { endCursor }
  }
}
```
**Response:**
```json
{
  "data": {
    "users": {
      "edges": [
        { "cursor": "abc123", "node": { "id": "11" } }
      ],
      "pageInfo": { "endCursor": "def456" }
    }
  }
}
```

---

## **Related Patterns**
1. **[API Versioning](#)**:
   Pagination logic may evolve; document versioning in API contracts (e.g., `Accept: application/vnd.api.v1+json`).

2. **[Rate Limiting](#)**:
   Combine pagination with rate limiting (e.g., `X-RateLimit-Limit` headers) to prevent abuse.

3. **[Caching](#)**:
   Cache paginated results with conditional headers (`ETag`, `Last-Modified`) or Redis keys (e.g., `users_page_1`).

4. **[Search + Pagination](#)**:
   For search APIs, paginate filtered results (e.g., `/search?q=foo&page=2`).

5. **[Webhooks for Updates](#)**:
   Use cursor-based pagination alongside real-time updates (e.g., "since cursor" for change feeds).

6. **[GraphQL DataLoader](#)**:
   Batch paginated queries to reduce N+1 issues (e.g., fetching `User` posts with pagination).

---

## **Best Practices**
1. **Default Limits**:
   Enforce reasonable defaults (e.g., `limit: 100`) to avoid overwhelming clients.

2. **Total Counts**:
   Include `total` or `totalCount` metadata for UI progress bars (but avoid full scans for `total`).

3. **Error Handling**:
   Handle invalid cursors/IDs gracefully (e.g., `400 Bad Request` with `missing_after_cursor`).

4. **Database Indexes**:
   Ensure paginated columns (`id`, `created_at`) are indexed.

5. **Pagination Tokens**:
   For cursor-based keyset, use **primary keys** or **unique columns** to avoid duplicates.

6. **Client-Side State**:
   Store `after`/`cursor` locally (e.g., Redux, URL hash) for seamless navigation.

7. **Performance Monitoring**:
   Log pagination query times (e.g., `offset_scan_time`, `cursor_scan_time`) for optimization.

---
**See Also:**
- [REST API Design Best Practices](#)
- [GraphQL Performance Guide](#)
- [Database Indexing for Pagination](#)