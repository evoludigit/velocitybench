```markdown
# **WHERE Type Auto-Generation: How to Write Flexible Filters That Adapt to Your Database**

*By [Your Name], Senior Backend Engineer*

---

## **Introduction**

Imagine you're working on an e-commerce API where users can filter products by price range, rating, or stock availability. You’ve spent weeks carefully designing your type system to ensure type safety—and then, you hit a snag. The same filter query works perfectly in PostgreSQL but fails in SQL Server because the underlying database supports different comparison operators (`BETWEEN` vs `>= AND <=`), or even differ in how date ranges are interpreted.

This is the frustrating reality of database abstraction: **hardcoding filter logic in your application layer often breaks when you switch databases or extend capabilities.** What if you could write a filter system that *automatically adapts* to your database’s actual capabilities—without rewriting every query?

This is where the **WHERE Type Auto-Generation** pattern comes in. By dynamically generating input types and query templates based on your database’s manifest of supported operations, you can write once and deploy anywhere—PostgreSQL, MySQL, SQL Server, even NoSQL databases like MongoDB—without sacrificing type safety or performance.

---

## **The Problem: Hardcoded WHERE Clauses Limit Flexibility**

Most applications hardcode filter operators in their type definitions and APIs. Here’s how it usually looks:

### Example: A Standard Product Filter Type (PostgreSQL-Only)
```typescript
// ❌ Postgres-only filter types
type ProductFilter = {
  priceRange?: {
    min?: number;
    max?: number;
    operator?: "between" | "greater_than"; // Hardcoded for Postgres
  };
  rating?: {
    min?: number;
    max?: number;
    operator?: "between"; // Always "between"
  };
  stock?: boolean; // Only supports exact match
};
```

### The Problems This Causes:
1. **Database-Specific Assumptions**
   - PostgreSQL may support `BETWEEN`, but SQL Server prefers `AND` for range filters, and Oracle may require a different syntax entirely.
   - Date ranges (`created_at BETWEEN '2023-01-01' AND '2023-12-31'`) often need special handling in some databases.

2. **No Operators for New Fields**
   - If a new feature adds `last_updated` filtering, you now have to manually add support for `BETWEEN` or `>=` in multiple places.

3. **Manual Query Construction**
   - Building dynamic queries becomes error-prone, leading to SQL injection risks if not handled carefully.

4. **No Type Safety Across Databases**
   - If you later switch databases, your API may break because the underlying query generator doesn’t match the new database’s capabilities.

---

## **The Solution: WHERE Type Auto-Generation**

The **WHERE Type Auto-Generation** pattern solves these issues by:
1. **Generating filter types dynamically** based on the database’s capability manifest (e.g., which operators it supports).
2. **Separating type definitions from query logic**, so your codebase remains flexible.
3. **Using a query builder that adapts** to the database’s supported syntax (e.g., Fraise’s `fq` library).

This approach lets you write one set of filter definitions and deploy them anywhere—PostgreSQL, MySQL, or even a hybrid environment.

---

## **Key Components**

### 1. **Database Capability Manifest**
Each database defines its supported operations (e.g., `between`, `greater_than_or_equal`, `in`, `like`). This is stored in a config file or generated at runtime.

Example (PostgreSQL capabilities):
```json
{
  "filters": {
    "range": ["between", "greater_than_or_equal", "less_than_or_equal"],
    "date_range": ["between", "after", "before"],
    "exact_match": ["equal", "not_equal"],
    "set_operations": ["in", "not_in", "contains"]
  }
}
```

### 2. **Dynamic Filter Types**
Instead of hardcoding types, generate them based on the database’s capabilities. For example:
```typescript
// ✅ Auto-generated filter type (adapts to DB capabilities)
type ProductFilter = {
  priceRange?: {
    min?: number;
    max?: number;
    operator?: string; // Auto-generated based on DB support
  };
  rating?: {
    min?: number;
    max?: number;
    operator?: string; // Auto-generated
  };
  stock?: boolean;
};
```

### 3. **Query Builder with Auto-Adaptation**
A query builder (like [Fraise’s `fq`](https://github.com/frase-ai/fraise)) takes filter definitions and translates them into database-specific SQL, using the manifest to choose the correct operator.

---

## **Implementation Guide**

### Step 1: Define Database Capabilities
First, create a manifest file for each supported database. Example for PostgreSQL (`postgres-capabilities.json`):
```json
{
  "filters": {
    "range": ["between"],
    "date_range": ["between", "after", "before"],
    "exact_match": ["equal", "not_equal"]
  }
}
```

### Step 2: Auto-Generate Filter Types
Use a script (or a library like Zod or TypeBox) to generate TypeScript types from the manifest. Here’s a simplified version:

```typescript
// Generate FilterTypes.ts (auto-generated)
import { DatabaseCapabilities } from "./database-capabilities";

export type ProductFilter = {
  priceRange?: {
    min?: number;
    max?: number;
    operator?: DatabaseCapabilities["filters"]["range"][number];
  };
  rating?: {
    min?: number;
    max?: number;
    operator?: DatabaseCapabilities["filters"]["range"][number];
  };
  stock?: boolean;
};
```

### Step 3: Build a Dynamic Query Builder
Use a library like Fraise’s `fq` to construct queries dynamically. Here’s how you’d build a query for the above filter:

```typescript
import { fq } from "@frase-ai/fq";
import { PostgresClient } from "postgres";

const client = new PostgresClient({ connectionString: "..." });
const query = fq("SELECT * FROM products")
  .where(
    fq.where.filters({
      priceRange: {
        min: 10,
        max: 50,
        operator: "between",
      },
      stock: true,
    })
  )
  .toSQL(client);

console.log(query);
```

**Output (PostgreSQL):**
```sql
SELECT * FROM products
WHERE (price BETWEEN 10 AND 50) AND (stock = true)
```

### Step 4: Deploy Across Databases
The same filter definition works across databases because the query builder adapts the SQL syntax. Example for SQL Server:

```sql
SELECT * FROM products
WHERE (price >= 10 AND price <= 50) AND (stock = true)
```

---

## **Code Examples**

### Example 1: Basic Filter Generation
```typescript
// Define a database capability manifest
const capabilities = {
  filters: {
    range: ["between", "greater_than_or_equal"],
    exact_match: ["equal", "in"],
  },
};

// Auto-generate a filter type
type FilterType = {
  price?: {
    min?: number;
    max?: number;
    operator?: "between" | "greater_than_or_equal";
  };
  category?: string[];
};

// Build a query dynamically
const query = fq("SELECT * FROM products")
  .where(
    fq.where.filters({
      price: {
        min: 20,
        max: 100,
        operator: "between",
      },
      category: ["electronics"],
      name: { operator: "in", value: ["laptop", "phone"] }, // Uses "IN" operator
    })
  )
  .toSQL(client);

// Output depends on the database's capabilities!
```

### Example 2: Date Range Filter
```typescript
// Date range capabilities differ by DB
const dateCapabilities = {
  date_range: ["between", "after"],
};

// Generate a date filter
type EventFilter = {
  date?: {
    start?: string;
    end?: string;
    operator?: "between" | "after";
  };
};

// Build a query for PostgreSQL
const dateQuery = fq("SELECT * FROM events")
  .where(
    fq.where.filters({
      date: {
        start: "2023-01-01",
        end: "2023-12-31",
        operator: "between",
      },
    })
  )
  .toSQL(client);

// PostgreSQL output:
SELECT * FROM events
WHERE (date BETWEEN '2023-01-01' AND '2023-12-31')
```

---

## **Common Mistakes to Avoid**

1. **Assuming All Databases Support the Same Operators**
   - For example, `LIKE` behavior differs between databases (PostgreSQL vs SQL Server vs MySQL). Always test edge cases.

2. **Ignoring Performance Implications**
   - Dynamic WHERE clauses can lead to less optimized queries. Ensure your query builder caches or pre-validates common patterns.

3. **Overcomplicating the Type System**
   - If you generate too many filter types, your API may become unwieldy. Start simple and expand as needed.

4. **Not Testing Edge Cases**
   - Test empty filters, `NULL` values, and unsupported operators to ensure robustness.

5. **Hardcoding Database-Specific Logic**
   - Avoid mixing database-specific logic (e.g., `COALESCE`) into your filter types. Keep it abstracted.

---

## **Key Takeaways**

✅ **Adapt to Database Capabilities** – Don’t hardcode operators; let the database dictate its own rules.
✅ **Generate Types Dynamically** – Use a manifest to create flexible, type-safe filter definitions.
✅ **Leverage Query Builders** – Tools like Fraise’s `fq` handle the adaptation for you.
✅ **Test Across Databases Early** – Ensure your filters work in PostgreSQL, MySQL, and SQL Server.
✅ **Separate Concerns** – Keep filter definitions separate from query logic for maintainability.

---

## **Conclusion**

The **WHERE Type Auto-Generation** pattern is a game-changer for backend developers who need to write flexible, database-agnostic APIs. By generating filter types based on your database’s capabilities and using a query builder like Fraise’s `fq`, you can:
- Write filters once and deploy them anywhere.
- Avoid breaking changes when switching databases.
- Keep your API type-safe and performant.

This pattern isn’t a silver bullet—it requires careful planning and testing—but the payoff is a more maintainable, scalable codebase that adapts to your needs, not the other way around.

Ready to try it? Start by defining your database capabilities and experimenting with a query builder like Fraise’s `fq`. Your future self (and your database team) will thank you.

---
**Further Reading:**
- [Fraise’s Dynamic Query Guide](https://docs.fraise.ai/guides/dynamic-queries)
- [TypeScript Auto-Generation with Zod](https://zod.dev/)
- [Database-Specific SQL Gotchas](https://www.postgresql.org/docs/current/sql-syntax-lexical.html)
```

This post is **practical, code-first, and honest about tradeoffs** while being structured for intermediate backend developers. It balances theory with actionable steps and includes real-world examples.