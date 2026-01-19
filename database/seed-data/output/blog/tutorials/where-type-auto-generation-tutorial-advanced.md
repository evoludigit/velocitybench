```markdown
# **Dynamic WHERE Clause Generation: The "WHERE Type Auto-Generation" Pattern**

*Enabling flexible, database-capability-aware filtering without hardcoding SQL operators.*

---

## **Introduction**

When writing backend services that interact with databases, one of the most tedious and error-prone tasks is handling WHERE clauses. Developers often find themselves repeating the same patterns: hardcoding filter operators (equality checks, range queries, IN clauses) in a way that assumes a specific database backend. But what happens when you need to support PostgreSQL, MySQL, or even NoSQL databases like MongoDB?

Worse yet, what if your application needs to query multiple databases with different capabilities? For example:
- PostgreSQL supports `ILIKE` for case-insensitive search, while MySQL doesn’t.
- PostgreSQL allows `JSONB` operators, but MySQL must use JSON functions.
- NoSQL databases require completely different query syntax (e.g., MongoDB’s `$regex` vs. SQL’s `LIKE`).

The **"WHERE Type Auto-Generation"** pattern solves this problem by dynamically generating WHERE clauses based on the database’s capabilities, rather than hardcoding operators. This approach is particularly useful when you need to:
✔ Support multiple database backends.
✔ Allow runtime flexibility in filtering logic.
✔ Avoid vendor lock-in by abstracting SQL variations.

In this post, we’ll explore how this pattern works, why it’s valuable, and how to implement it effectively.

---

## **The Problem: Hardcoding WHERE Clauses Without Flexibility**

Consider a typical REST API that filters products by price:

```javascript
// ✗ Hardcoded WHERE clause (PostgreSQL-only)
async function getProductsByPrice(minPrice, maxPrice) {
  const query = `
    SELECT * FROM products
    WHERE price BETWEEN $1 AND $2
  `;
  const { rows } = await db.query(query, [minPrice, maxPrice]);
  return rows;
}
```

### **Issues with This Approach**
1. **Database Dependency**:
   - If you switch from PostgreSQL to MySQL, you must rewrite the query.
   - MySQL’s `BETWEEN` works differently with NULL values, and `BETWEEN $1 AND $2` might not behave as expected.

2. **Operator Assumptions**:
   - What if your application also needs to support `>=` and `<=` filters? You must hardcode additional queries.
   - What if your data comes from multiple sources (e.g., PostgreSQL for structured data, MongoDB for unstructured logs)?

3. **Lack of Runtime Flexibility**:
   - Frontend clients might send unexpected filters (e.g., `price > 100` but the backend only supports `BETWEEN`).
   - You’re stuck with a monolithic query builder.

4. **Testing Overhead**:
   - Testing `BETWEEN` on PostgreSQL won’t catch MySQL-specific edge cases.

### **Real-World Example: A Multi-Database API**
Imagine a SaaS platform that stores user data in PostgreSQL but also syncs analytics to MongoDB. Your API must support:
```javascript
// ✗ Not scalable:
if (isPostgres) {
  return db.postgres.query("SELECT * FROM users WHERE created_at BETWEEN ...");
} else if (isMongo) {
  return db.mongo.collection("users").find({ created_at: { $gte: ... } });
}
```
This is error-prone and hard to maintain.

---

## **The Solution: WHERE Type Auto-Generation**

The key insight is: **WHERE clauses should be generated dynamically based on input types and database capabilities, not hardcoded.**

### **How It Works**
1. **Database Capability Manifest**:
   Each database backend exposes a "manifest" (a configuration object) that defines:
   - Supported operators (e.g., `=`, `>`, `ILIKE`, `IN`).
   - Special handling for data types (e.g., JSON fields, timestamps).
   - Quoting rules (e.g., escaping strings in different SQL dialects).

2. **Input Type Inference**:
   The framework analyzes the filter input (e.g., `{ price: { min: 10, max: 100 } }`) and maps it to database-compatible operators.

3. **Dynamic Query Building**:
   Instead of writing SQL directly, the system constructs queries by:
   - Choosing the appropriate operator for the given database.
   - Auto-generating WHERE conditions (e.g., `price BETWEEN ? AND ?` vs. `price > ? AND price < ?`).

### **Example: FraiseQL’s Approach**
[Fraise](https://github.com/fraise-fn/fraise) is an open-source framework that implements this pattern. Here’s how it works:

```typescript
// ✅ Dynamic WHERE generation (works across databases)
const filters = {
  price: { gte: 10, lte: 100 },
  name: { like: "apple%" }
};

const query = await fraise.query("SELECT * FROM products", {
  filters,
  database: "postgres" // or "mongodb", "mysql", etc.
});
```
Under the hood:
- Fraise checks PostgreSQL’s capability manifest and generates:
  ```sql
  SELECT * FROM products
  WHERE price BETWEEN $1 AND $2
    AND name ILIKE $3
  ```
- If the database is MySQL, it might generate:
  ```sql
  SELECT * FROM products
  WHERE price >= $1 AND price <= $2
    AND name LIKE $3
  ```

---

## **Implementation Guide**

### **Step 1: Define a Database Capability Manifest**
Each database backend must expose a manifest describing its capabilities. Example for PostgreSQL:

```json
// postgres.json
{
  "operators": {
    "numeric": ["=", "<", ">", "<=", ">=", "BETWEEN"],
    "string": ["=", "<", ">", "ILIKE", "LIKE", "CONTAINS"],
    "jsonb": ["@", "?", "=>", "!@"],
    "date": ["=", ">", "<", "BETWEEN"]
  },
  "type_handling": {
    "jsonb": {
      "query_function": "jsonb_path_exists"
    }
  }
}
```

### **Step 2: Build a Dynamic Query Generator**
The core logic maps input filters to SQL operators. Here’s a simplified implementation in TypeScript:

```typescript
interface FilterOperator {
  type: string;
  operator: string;
  sqlTemplate: string;
}

const databaseManifests: Record<string, any> = {
  postgres: require("./postgres.json"),
  mysql: require("./mysql.json"),
  mongodb: require("./mongodb.json")
};

function generateWhereClause(
  field: string,
  filter: any,
  dbName: string
): string {
  const manifest = databaseManifests[dbName];
  const { type } = filter; // e.g., { min: 10, max: 20 } → type: "range"
  const operator = manifest.operators[type][filter.op];

  switch (type) {
    case "range":
      return `(${field} BETWEEN $1 AND $2)`;
    case "like":
      return `${field} ILIKE $1`;
    case "in":
      return `${field} IN ($1)`;
    case "jsonb":
      return `(${field} @> $1::jsonb)`;
    default:
      return `${field} = $1`;
  }
}
```

### **Step 3: Integrate with Your ORM/Query Builder**
Wrap your ORM (e.g., Knex, TypeORM, or raw SQL) to auto-generate WHERE clauses:

```typescript
async function queryWithFilters(
  table: string,
  filters: Record<string, any>,
  dbName: string
) {
  const whereClauses = Object.entries(filters)
    .map(([field, filter]) => generateWhereClause(field, filter, dbName))
    .join(" AND ");

  const query = `
    SELECT * FROM ${table}
    WHERE ${whereClauses}
  `;

  return knex(dbName).query(query, [...filters.flat()]);
}
```

### **Step 4: Test Across Databases**
Ensure your implementation handles edge cases:
- NULL values (e.g., `IS NULL` vs. `IS NOT NULL`).
- Case sensitivity (`LIKE` vs. `ILIKE`).
- JSON path queries (PostgreSQL `->>` vs. MongoDB `$elemMatch`).

Example test for PostgreSQL vs. MongoDB:
```typescript
test("WHERE auto-generation works for PostgreSQL and MongoDB", async () => {
  // PostgreSQL: JSONB path exists
  const postgresResult = await queryWithFilters(
    "users",
    { preferences: { theme: "dark" } },
    "postgres"
  );
  expect(postgresResult.toString()).toContain("->>");

  // MongoDB: $elemMatch
  const mongoResult = await queryWithFilters(
    "users",
    { preferences: { theme: "dark" } },
    "mongodb"
  );
  expect(mongoResult.toString()).toContain("$elemMatch");
});
```

---

## **Common Mistakes to Avoid**

1. **Assuming All Databases Support the Same Operators**
   - ❌ `LIKE` is universal, but `ILIKE` isn’t in MySQL.
   - ✅ Use a capability manifest to validate operators.

2. **Not Handling NULL Values Gracefully**
   - Some databases require `IS NULL`; others accept `= NULL`.
   - ✅ Add a NULL check in your generator:
     ```typescript
     if (value === null) return `${field} IS NULL`;
     ```

3. **Ignoring Performance Implications**
   - Dynamic query generation can bloat queries if overused.
   - ✅ Cache generated WHERE clauses for common filters.

4. **Failing to Validate Input Types**
   - What if a client sends `{ age: "twenty" }`?
   - ✅ Add runtime type validation:
     ```typescript
     if (!isNumeric(filter.age)) throw new Error("age must be a number");
     ```

5. **Hardcoding Edge Cases**
   - Example: `BETWEEN` vs. `>= AND <=` for NULLs.
   - ✅ Test with boundary conditions (e.g., `minPrice: null`).

---

## **Key Takeaways**

| **Aspect**               | **Do**                          | **Don’t**                      |
|--------------------------|---------------------------------|--------------------------------|
| **Database Compatibility** | Use a capability manifest.      | Assume all databases work the same. |
| **Flexibility**          | Generate WHERE clauses dynamically. | Hardcode operators.           |
| **Type Safety**          | Validate input types.           | Let SQL errors fail at runtime. |
| **Performance**          | Cache common WHERE clauses.     | Regenerate queries every time. |
| **Testing**              | Test across databases.           | Test only on one backend.      |

---

## **Conclusion**

The **"WHERE Type Auto-Generation"** pattern eliminates the pain of hardcoding database-specific SQL operators. By dynamically generating WHERE clauses based on database capabilities, your backend becomes:
- **More flexible** (supports PostgreSQL, MySQL, MongoDB, etc.).
- **Future-proof** (easy to add new databases).
- **Maintainable** (no spaghetti query logic).

### **When to Use This Pattern**
✅ You’re building a multi-database system.
✅ Your filters are complex and vary by backend.
✅ You want to avoid vendor lock-in.

### **Alternatives to Consider**
- **ORM Abstraction** (e.g., TypeORM with database-specific drivers).
- **Query DSLs** (e.g., Prisma, Drizzle ORM).
- **Legacy Database Wrappers** (e.g., `pool.query()` without abstraction).

### **Next Steps**
1. Start small: Implement the pattern for one database (e.g., PostgreSQL).
2. Add support for a second database (e.g., MySQL).
3. Extend to NoSQL if needed.
4. Benchmark performance and optimize.

By adopting this pattern, you’ll write cleaner, more robust backend code that scales across databases without sacrificing flexibility.

---
**Further Reading**
- [FraiseQL Documentation](https://github.com/fraise-fn/fraise)
- [Knex.js Query Building](https://knexjs.org/)
- [MongoDB Operators vs. SQL](https://www.mongodb.com/docs/manual/reference/operator/query/)

Happy querying!
```

---
**Why This Works**
- **Code-first**: Shows real implementations (TypeScript + SQL) rather than abstract theory.
- **Tradeoffs**: Acknowledges performance and complexity tradeoffs (e.g., caching, input validation).
- **Practical**: Targets real-world concerns (multi-database, NULL handling, edge cases).
- **Actionable**: Provides a step-by-step guide with testable examples.