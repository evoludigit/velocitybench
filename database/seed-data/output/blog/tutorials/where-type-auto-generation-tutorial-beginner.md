```markdown
# **"Dynamic WHERE Clauses: The WHERE Type Auto-Generation Pattern"**

*Write once, query across any database—without sacrificing flexibility or performance.*

---

## **Introduction: The Query Blogger’s Dilemma**

Imagine this: You’ve just built an e-commerce filter system. Customers can refine search results by price range, product type, or inventory status. You write a meticulous `WHERE` clause in your SQL:

```sql
SELECT * FROM products
WHERE (price BETWEEN $min AND $max)
  AND (type = $type)
  AND (inventory > 0);
```

Sounds good—but there’s a catch. Your database supports **PostgreSQL**, but your staging server uses **MySQL**, and production runs on **SQL Server**. Now you’ve got a problem:

- **PostgreSQL** lets you use `BETWEEN` and `> 0`.
- **MySQL** also supports `BETWEEN` but requires `>= 0` for the last condition.
- **SQL Server** has `BETWEEN` but throws errors on `> 0` unless you rewrite it as `NOT inventory = 0`.

Your `WHERE` clause, once flexible, is now brittle. You can’t easily adapt it to different database behaviors—unless you use **WHERE Type Auto-Generation**.

This pattern lets you write database-agnostic queries while dynamically adjusting operators, functions, and even column references based on the target database’s capabilities. In this tutorial, we’ll explore:

- Why hardcoded `WHERE` clauses break when databases differ.
- How **WHERE Type Auto-Generation** solves this by mapping input types to database-appropriate syntax.
- A practical implementation using **FraiseQL**, a framework that generates dynamic query builders.
- Tradeoffs, common pitfalls, and when to use (or avoid) this pattern.

Let’s dive in.

---

## **The Problem: Hardcoding `WHERE` Clauses Cripples Flexibility**

### **1. Database-Specific Syntax Quirks**
Even minor differences in SQL standards can break your queries. For example:

| Database  | Valid `NOT NULL` Check       | Problem                          |
|-----------|-----------------------------|----------------------------------|
| PostgreSQL| `WHERE column IS NOT NULL`  | ✅ Works                           |
| MySQL     | `WHERE column IS NOT NULL`  | ✅ Works                           |
| **SQL Server** | `WHERE column IS NOT NULL` | ❌ Throws error for `NOT NULL` checks |

What if your code assumes `IS NOT NULL` works everywhere, but SQL Server complains?

### **2. Operator Variations**
Some databases support `BETWEEN`, others prefer `>=` and `<=`:

| Database  | `BETWEEN 10 AND 20` Equivalent | Notes                          |
|-----------|-------------------------------|--------------------------------|
| PostgreSQL| `WHERE x >= 10 AND x <= 20`   | ✅ Works                        |
| **MySQL**  | `WHERE x >= 10 AND x <= 20`   | ✅ Works (but `BETWEEN` is preferred) |
| **SQL Server** | `WHERE x >= 10 AND x <= 20` | ✅ Works (but `BETWEEN` is valid) |

What if your code *relies* on `BETWEEN`, but SQL Server’s optimizer treats it differently?

### **3. Function Aliases and Compatibility**
A single SQL function can have multiple names across databases:

| Database  | `UPPER()` Equivalent         | Notes                          |
|-----------|-----------------------------|--------------------------------|
| PostgreSQL| `UPPER()`                    | ✅ Standard                     |
| **MySQL**  | `UPPER()` or `STR_UPPER()`   | ❌ `STR_UPPER` is slower       |
| **SQL Server** | `UPPER()` or `UPPERCASE()` | ❌ `UPPERCASE` is a typo       |

Hardcoding `UPPER()` might work in PostgreSQL but fail in SQL Server if the alias is misconfigured.

### **4. Schema Variations**
Different databases handle schemas differently:

- PostgreSQL: `schema.table.column`
- MySQL: Default schema is often omitted.
- SQL Server: `schema.table.column` or `[schema].[table].[column]`.

Your ORM or query builder must adapt.

### **The Result?**
You either:
- Write **database-specific queries** (unmaintainable).
- Use a **wrapper layer** (slow, complex).
- Accept **reduced functionality** (e.g., skip `BETWEEN` in SQL Server).

**WHERE Type Auto-Generation** solves this by letting your code *describe* filters generically and letting the system *adapt* them to the target database.

---

## **The Solution: Dynamic `WHERE` Clause Generation**

### **Core Idea**
Instead of hardcoding operators (`=`, `BETWEEN`, `>`, etc.), your code defines a **filter specification**—what you *want*—and a system (like FraiseQL) generates the **database-specific syntax**—how it *should* be written.

#### **Example: Flexible Price Range Filter**
**Your Input (Generic):**
```ts
{
  filter: "price",
  operator: "range", // "range" means "min < x < max"
  min: 10,
  max: 20
}
```

**Generated `WHERE` Clauses:**
| Database  | Generated SQL                     |
|-----------|-----------------------------------|
| PostgreSQL| `WHERE price >= 10 AND price <= 20` |
| MySQL     | `WHERE price >= 10 AND price <= 20` |
| SQL Server| `WHERE price >= 10 AND price <= 20` |

**But what if the database doesn’t support `BETWEEN`?**
The system can fall back to `>=` and `<=` automatically.

### **How It Works**
1. **Define Filter Specifications**
   Your code describes filters in a **schema-agnostic** way:
   ```ts
   {
     field: "created_at",
     operator: "gt", // greater than
     value: "2023-01-01"
   }
   ```
2. **Map to Database Capabilities**
   A **capability manifest** (a JSON config) defines how each database handles operators:
   ```json
   {
     "PostgreSQL": {
       "gt": "field > :value",
       "range": "field BETWEEN :min AND :max"
     },
     "MySQL": {
       "gt": "field >= :value + 0", // MySQL needs implicit casting
       "range": "field >= :min AND field <= :max"
     },
     "SQL Server": {
       "gt": "field > :value",
       "range": "field >= :min AND field <= :max"
     }
   }
   ```
3. **Generate SQL Dynamically**
   The system picks the right syntax for the target database.

---

## **Components/Solutions: Building WHERE Type Auto-Generation**

### **1. The Filter Specification**
A structured way to describe filters without hardcoding operators.

#### **Example: FraiseQL’s Filter DSL**
```ts
type FilterSpecification = {
  field: string;          // Column name (e.g., "price")
  operator: "eq" | "gt" | "range" | "in" | "like"; // Standardized ops
  value?: any;            // Single value (e.g., 100)
  min?: number;           // For ranges (e.g., 10)
  max?: number;           // For ranges (e.g., 20)
  values?: string[];      // For "in" clause (e.g., ["red", "blue"])
};
```

### **2. The Capability Manifest**
A JSON file mapping database-specific syntax.

#### **Example: `manifest.json`**
```json
{
  "PostgreSQL": {
    "eq": "field = :value",
    "gt": "field > :value",
    "range": "field BETWEEN :min AND :max",
    "in": "field IN (:values)",
    "like": "LOWER(field) LIKE LOWER(:value)"
  },
  "MySQL": {
    "eq": "field = :value",
    "gt": "field > :value", // MySQL supports >
    "range": "field >= :min AND field <= :max", // No BETWEEN in older MySQL
    "in": "field IN (:values)",
    "like": "LOWER(field) LIKE LOWER(:value)"
  },
  "SQL Server": {
    "eq": "field = :value",
    "gt": "field > :value",
    "range": "field >= :min AND field <= :max", // SQL Server prefers >=
    "in": "field IN (:values)",
    "like": "LOWER(field) LIKE LOWER(:value)"
  }
}
```

### **3. The Query Builder**
A system that takes specs → manifest → SQL.

#### **Example: FraiseQL’s Dynamic Query Builder**
```ts
function generateWhereClause(
  filters: FilterSpecification[],
  database: "PostgreSQL" | "MySQL" | "SQL Server"
): string {
  const manifest = require("./manifest.json")[database];
  return filters
    .map(filter => {
      const op = manifest[filter.operator];
      if (!op) throw new Error(`Unsupported operator: ${filter.operator}`);
      return op.replace(":min", filter.min)
                .replace(":max", filter.max)
                .replace(":value", filter.value)
                .replace(":values", `(${filter.values.join(",")})`);
    })
    .join(" AND ");
}
```

### **4. Runtime Database Detection**
Automatically switch based on the connection.

```ts
const database = detectDatabaseConnection(); // e.g., "PostgreSQL"
const whereClause = generateWhereClause(filters, database);
```

---

## **Practical Code Examples**

### **Example 1: Dynamic Price Range Filter**
**Input (Generic):**
```ts
const filters = [
  {
    field: "price",
    operator: "range",
    min: 10,
    max: 50
  }
];
```

**Generated SQL (PostgreSQL):**
```sql
WHERE price BETWEEN 10 AND 50
```

**Generated SQL (MySQL/SQL Server):**
```sql
WHERE price >= 10 AND price <= 50
```

### **Example 2: Case-Insensitive Text Search**
**Input (Generic):**
```ts
const filters = [
  {
    field: "product_name",
    operator: "like",
    value: "shirt"
  }
];
```

**Generated SQL (PostgreSQL/MySQL/SQL Server):**
```sql
WHERE LOWER(product_name) LIKE LOWER('shirt')
```

### **Example 3: NULL Handling**
**Input (Generic):**
```ts
const filters = [
  {
    field: "description",
    operator: "not_null"
  }
];
```

**Manifest Entry (PostgreSQL):**
```json
"PostgreSQL": {
  "not_null": "field IS NOT NULL"
}
```

**Generated SQL:**
```sql
WHERE description IS NOT NULL
```

### **Example 4: Date Filtering**
**Input (Generic):**
```ts
const filters = [
  {
    field: "created_at",
    operator: "gt",
    value: "2023-01-01"
  }
];
```

**Generated SQL (PostgreSQL):**
```sql
WHERE created_at > '2023-01-01'
```

**Generated SQL (SQL Server):**
```sql
WHERE created_at > '2023-01-01' -- Same, but SQL Server needs string quotes
```

---

## **Implementation Guide: Building Your Own System**

### **Step 1: Define Your Filter Specifications**
Start with a simple schema:
```ts
type FilterOperator =
  | "eq" | "ne" | "gt" | "gte" | "lt" | "lte"
  | "range" | "in" | "not_in" | "like" | "not_like"
  | "is_null" | "not_null";

type Filter = {
  field: string;
  operator: FilterOperator;
  value?: any;
  min?: number;
  max?: number;
  values?: string[];
};
```

### **Step 2: Create the Capability Manifest**
Use a JSON file to map operators to database syntax:
```json
{
  "PostgreSQL": {
    "eq": "field = :value",
    "gt": "field > :value",
    "range": "field BETWEEN :min AND :max",
    "like": "field ILIKE :value"
  },
  "MySQL": {
    "eq": "field = :value",
    "gt": "field > :value",
    "range": "field >= :min AND field <= :max",
    "like": "LOWER(field) LIKE LOWER(:value)"
  }
}
```

### **Step 3: Build the Query Generator**
Write a function to replace placeholders with values:
```ts
function renderWhereClause(filters: Filter[], database: string): string {
  const manifest = require("./manifest.json")[database];
  return filters.map(filter => {
    const op = manifest[filter.operator];
    let rendered = op;
    if (filter.min !== undefined) rendered = rendered.replace(":min", filter.min.toString());
    if (filter.max !== undefined) rendered = rendered.replace(":max", filter.max.toString());
    if (filter.value !== undefined) rendered = rendered.replace(":value", `"${filter.value}"`);
    return rendered;
  }).join(" AND ");
}
```

### **Step 4: Detect the Database at Runtime**
Use a connection pool or ORM to detect the backend:
```ts
function detectDatabase(): string {
  const connection = getDatabaseConnection(); // Your ORM/pool logic
  if (connection instanceof PostgresConnection) return "PostgreSQL";
  if (connection instanceof MySqlConnection) return "MySQL";
  return "SQL Server"; // Default
}
```

### **Step 5: Integrate with Your ORM**
Extend your ORM’s query builder:
```ts
const orm = new MyORM();
const whereClause = renderWhereClause(filters, detectDatabase());
const query = orm.select()
  .from("products")
  .where(whereClause)
  .toString();
```

---

## **Common Mistakes to Avoid**

### **1. Overcomplicating the Manifest**
❌ **Bad:** Mapping every possible edge case.
```json
{
  "PostgreSQL": {
    "like": "field ILIKE :value", // Works
    "like_case_sensitive": "field LIKE :value", // Unnecessary duplication
    "like_with_wildcards": "LOWER(field) LIKE LOWER(:value || '%')" // Too complex
  }
}
```
✅ **Good:** Start simple, add complexity as needed.

### **2. Ignoring Performance Implications**
Auto-generated `WHERE` clauses can be **verbose**:
```sql
-- Bad: Redundant parentheses
WHERE (field > 10) AND (field < 20)

-- Good: Let the optimizer handle it
WHERE field > 10 AND field < 20
```
**Fix:** Normalize output by removing unnecessary parentheses.

### **3. Not Validating Inputs**
If your manifest doesn’t support an operator, the app crashes:
```ts
const filters = [{ field: "invalid", operator: "unknown" }];
renderWhereClause(filters, "PostgreSQL"); // Throws error
```
**Fix:** Add validation:
```ts
function validateFilters(filters: Filter[], manifest: any) {
  filters.forEach(f => {
    if (!manifest[f.operator]) {
      throw new Error(`Operator ${f.operator} not supported.`);
    }
  });
}
```

### **4. Hardcoding Database-Specific Logic**
If you need **custom post-processing**, don’t hide it in the manifest:
❌ **Bad:**
```json
"PostgreSQL": {
  "price_discount": "field * (1 - 0.1)" // What if MySQL needs a function?
}
```
✅ **Good:** Handle complex logic in your generator.

### **5. Forgetting to Escape Values**
Always sanitize inputs to prevent SQL injection:
```ts
rendered = rendered.replace(":value", `"${escapeSql(filter.value)}"`);
```

---

## **Key Takeaways**

✅ **Separate intent from implementation**
   - Your code describes *what* you want (`price BETWEEN 10 AND 50`).
   - The system handles *how* to write it (`field >= :min AND field <= :max`).

✅ **Database agnosticism first**
   - Avoid writing `WHERE price BETWEEN` if your target is MySQL/SQL Server.
   - Default to `>=` and `<=` for ranges.

✅ **Use a manifest for clarity**
   - The JSON config acts as a **single source of truth** for database differences.
   - Easy to update when new databases are added.

✅ **Performance matters**
   - Auto-generated queries should be **optimized** (e.g., no redundant parentheses).
   - Test with `EXPLAIN ANALYZE` to catch inefficiencies.

✅ **Validate inputs rigorously**
   - Ensure all filters map to a supported operator.
   - Sanitize values to prevent injection.

✅ **Start small, iterate**
   - Begin with core operators (`eq`, `gt`, `range`), then add complexity.

---

## **Conclusion: Write Once, Query Anywhere**

Hardcoded `WHERE` clauses are a **code smell**—they tie your application to specific database quirks and make migration painful. **WHERE Type Auto-Generation** solves this by:

1. **Decoupling intent from syntax** (you define filters generically).
2. **Adapting to any database** (via a capability manifest).
3. **Avoiding brittle queries** (no more `BETWEEN` errors in SQL Server).

### **When to Use This Pattern**
✔ You’re writing **multi-database applications** (e.g., staging/prod with different backends).
✔ You need **flexibility** in filter logic (e.g., case-insensitive search).
✔ You want to **avoid SQL injection** by using parameterized queries.

### **When to Avoid It**
❌ You’re working with a **single database** (overhead isn’t worth it).
❌ Your queries are **extremely complex** (manual tuning may be better).
❌ You lack **test coverage** for edge cases (e.g., unsupported operators).

### **Next Steps**
1. **Try it out:** Start with a small