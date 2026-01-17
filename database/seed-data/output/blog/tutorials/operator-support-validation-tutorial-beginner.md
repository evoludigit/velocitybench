```markdown
# **Operator Support Validation: Ensuring Your API Queries Work Everywhere**

---

## **Introduction**

When building backend systems that interact with databases, you often need to translate application-level queries (from APIs, ORMs, or direct SQL) into database-compatible syntax. But what happens when a developer—or even your own application—uses an SQL operator that your database doesn’t support? Maybe you're using PostgreSQL but your queries accidentally contain `LIKE` with regex syntax, or you’re running a legacy app on MySQL that suddenly tries to use a window function.

This is where the **Operator Support Validation** pattern comes into play. This pattern ensures that only database-supported operators are used in your queries, preventing runtime errors and unexpected failures. It acts as a **pre-flight check** before your queries even hit the database, catching issues early in development or deployment.

In this guide, we’ll cover:
- The problem of unsupported operators in WHERE clauses
- How to validate operators against a database’s capabilities
- A practical implementation with code examples
- Common pitfalls to avoid
- When (and when *not*) to use this pattern

Let’s dive in.

---

## **The Problem: WHERE Clauses with Unsupported Operators**

Imagine your team is building an e-commerce API, and you’ve decided to use a PostgreSQL database for its rich text search capabilities. You’ve written a query like this to find products matching a search term:

```sql
SELECT * FROM products
WHERE name ~* 'laptop';
```

This uses PostgreSQL’s `~*` operator (case-insensitive regex search), which is perfect for PostgreSQL. But what happens if your deployment pipeline accidentally deploys this to MySQL?

MySQL doesn’t support `~*`, and the query will fail with an error like:
`ERROR 1064 (42000): You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near '~* 'laptop'' at line 1`

This is a **runtime error**, which means:
1. Your API returns a `500 Internal Server Error` (or worse, a misleading `400 Bad Request` if you’re not careful).
2. Users see broken functionality, and you’re left debugging why the query failed.
3. Your tests (if they exist) likely don’t catch this because they assume a specific database.

Even worse, if you’re using an ORM like Prisma or Django ORM, you might not even realize you’re generating unsupported syntax until it fails in production.

---

## **The Solution: Operator Support Validation**

The Operator Support Validation pattern solves this by:
1. **Defining a capability manifest** – A list of operators supported by each database (e.g., PostgreSQL, MySQL, SQLite).
2. **Analyzing queries** – Before executing them, parse the WHERE clauses and check each operator against the manifest.
3. **Failing fast** – If an unsupported operator is detected, throw an error early (before hitting the database).

This pattern is especially useful for:
- **Multi-database systems** (e.g., PostgreSQL in dev, MySQL in production).
- **ORM-generated queries** (where you can’t control the exact SQL).
- **Legacy codebases** with untested queries.

---

## **Components of the Solution**

To implement this pattern, you’ll need:

### 1. **A Capability Manifest**
A JSON/YAML file that maps databases to their supported operators. Example (`db_operators.json`):

```json
{
  "postgresql": {
    "standard": ["=", "!=", "<", ">", "<=", ">=", "LIKE", "ILIKE", "~", "~*"],
    "advanced": ["ILIKE", "~*", "array_contains", "jsonb_contains"]
  },
  "mysql": {
    "standard": ["=", "!=", "<", ">", "<=", ">=", "LIKE", "REGEXP"],
    "advanced": ["REGEXP", "LIKE BINARY"]
  },
  "sqlite": {
    "standard": ["=", "!=", "<", ">", "<=", ">=", "LIKE"],
    "advanced": ["GLOB", "REGEXP"]
  }
}
```

### 2. **A Query Parser**
A tool to extract operators from SQL queries. You can:
- Use a **SQL parser library** (e.g., `sqlparser` for Python or `pg_query` for PostgreSQL).
- Write a **regex-based parser** (simpler but less robust).
- Use the database’s **native parser** (e.g., PostgreSQL’s `pg_parse_query`).

### 3. **Validation Logic**
Compare extracted operators against the manifest for the target database.

### 4. **Error Handling**
Return a clear error (e.g., `BadRequest`) if an unsupported operator is found.

---

## **Code Examples**

Let’s implement this in **Node.js** using Express and a simple SQL parser. We’ll use the `sql-parser` library for parsing.

### Step 1: Install Dependencies
```bash
npm install express sql-parser @types/sql-parser
```

### Step 2: Define the Capability Manifest
Create `db-operators.js`:

```javascript
const dbOperators = {
  postgresql: {
    standard: ["=", "!=", "<", ">", "<=", ">=", "LIKE", "ILIKE", "~", "~*"],
    advanced: ["ILIKE", "~*", "array_contains", "jsonb_contains"]
  },
  mysql: {
    standard: ["=", "!=", "<", ">", "<=", ">=", "LIKE", "REGEXP"],
    advanced: ["REGEXP", "LIKE BINARY"]
  },
  sqlite: {
    standard: ["=", "!=", "<", ">", "<=", ">=", "LIKE"],
    advanced: ["GLOB", "REGEXP"]
  }
};

module.exports = dbOperators;
```

### Step 3: Build the Validator
Create `query-validator.js`:

```javascript
const sqlparser = require("sql-parser");
const dbOperators = require("./db-operators");

function isOperatorSupported(query, targetDb) {
  try {
    const parsed = sqlparser.parse(query);
    const operators = new Set();

    // Recursively extract operators from WHERE clauses
    function extractOperators(node) {
      if (node.type === "binary_expression") {
        operators.add(node.operator);
        // Recursively check left and right operands (e.g., for nested conditions)
        if (node.left.type === "binary_expression") extractOperators(node.left);
        if (node.right.type === "binary_expression") extractOperators(node.right);
      } else if (node.type === "where") {
        extractOperators(node.expression);
      }
    }

    // Start extraction from the root of the parsed query
    parsed.forEach(stmt => {
      if (stmt.type === "select" && stmt.where) {
        extractOperators(stmt.where);
      }
    });

    // Get the list of supported operators for the target DB
    const supportedOperators = new Set([
      ...dbOperators[targetDb].standard,
      ...dbOperators[targetDb].advanced
    ]);

    // Check for unsupported operators
    for (const op of operators) {
      if (!supportedOperators.has(op)) {
        return false;
      }
    }

    return true;
  } catch (err) {
    console.error("Error parsing query:", err);
    return false;
  }
}

module.exports = isOperatorSupported;
```

### Step 4: Use the Validator in an API Endpoint
Create `app.js`:

```javascript
const express = require("express");
const isOperatorSupported = require("./query-validator");

const app = express();
app.use(express.json());

// Example: Validate a query before executing it
app.post("/search", (req, res) => {
  const { query, db } = req.body;

  if (!isOperatorSupported(query, db)) {
    return res.status(400).json({
      error: "Unsupported operator detected. Check your query syntax for the target database."
    });
  }

  // If validation passes, proceed with the query (e.g., execute in DB)
  console.log(`Executing query on ${db}:`, query);
  res.json({ success: true, message: "Query is valid for the target database." });
});

app.listen(3000, () => {
  console.log("Server running on http://localhost:3000");
});
```

### Step 5: Test It Out
**Test Case 1: Valid Query (PostgreSQL)**
```bash
curl -X POST http://localhost:3000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT * FROM products WHERE name ~* \'laptop\';", "db": "postgresql"}'
```
**Response:**
```json
{ "success": true, "message": "Query is valid for the target database." }
```

**Test Case 2: Invalid Query (MySQL)**
```bash
curl -X POST http://localhost:3000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT * FROM products WHERE name ~* \'laptop\';", "db": "mysql"}'
```
**Response:**
```json
{
  "error": "Unsupported operator detected. Check your query syntax for the target database."
}
```

---

## **Implementation Guide**

### When to Use This Pattern
1. **Multi-database deployments** (e.g., PostgreSQL in dev, MySQL in production).
2. **Shared databases** (e.g., your team uses PostgreSQL locally but the production DB is MySQL).
3. **ORM-generated queries** where you can’t predict the exact SQL.
4. **Legacy systems** with untested queries.

### When to Avoid This Pattern
1. **Single-database systems** (if you know the DB and it’s consistent).
2. **Performance-critical paths** (parsing SQL adds overhead).
3. **Simple CRUD apps** where queries are trivial.

### Steps to Implement
1. **Define your capability manifest** (start with standard operators).
2. **Choose a SQL parser** (e.g., `sql-parser` for Node.js, `psycopg2` for PostgreSQL).
3. **Integrate validation** into your query execution flow (before hitting the DB).
4. **Handle errors gracefully** (return `400 Bad Request` for invalid queries).
5. **Test thoroughly** (validate queries for all supported databases).

### Tools to Consider
| Tool/Library       | Language      | Purpose                          |
|--------------------|---------------|----------------------------------|
| `sql-parser`       | Node.js       | Parse SQL queries                |
| `pg_query`         | PostgreSQL    | Parse PostgreSQL queries         |
| `mysqlclient`      | Python        | MySQL query parsing              |
| `sqlparse`         | Python        | Lightweight SQL parsing          |
| `prisma`           | Node.js       | ORM with query validation        |

---

## **Common Mistakes to Avoid**

1. **Overly Complex Parsing**
   - Don’t try to parse *every* SQL construct (e.g., CTEs, window functions). Focus on `WHERE` clauses first.
   - Start with a simple regex for basic operators and expand later.

2. **False Positives**
   - Some operators are context-dependent (e.g., `LIKE` is supported in MySQL, but `ILIKE` isn’t). Handle case-insensitive variants carefully.
   - Example: `LIKE` is standard, but `ILIKE` is only in PostgreSQL.

3. **Ignoring Database Dialects**
   - MySQL and PostgreSQL both support `LIKE`, but `REGEXP` works differently:
     - MySQL: `REGEXP 'pattern'`
     - PostgreSQL: `~ 'pattern'`
   - Your manifest should reflect these differences.

4. **Not Testing Edge Cases**
   - Test queries with:
     - Nested conditions (`WHERE (a > 1 AND b < 10)`).
     - Multiple operators (`WHERE name LIKE '%lap%' AND price > 100`).
     - Unsupported functions (e.g., PostgreSQL’s `array_contains`).

5. **Assuming ORMs Are Safe**
   - ORMs like Prisma or Django ORM can generate unsupported SQL if misconfigured. Validate even ORM-generated queries.

---

## **Key Takeaways**

✅ **Prevent runtime errors** by validating operators before executing queries.
✅ **Support multi-database systems** with a capability manifest.
✅ **Use SQL parsers** to extract operators from queries (e.g., `sql-parser` for Node.js).
✅ **Fail fast** with clear error messages (e.g., `400 Bad Request`).
✅ **Start simple** (validate basic operators first) and expand later.

❌ **Don’t overcomplicate parsing** – focus on `WHERE` clauses initially.
❌ **Don’t ignore dialect differences** (e.g., MySQL `REGEXP` vs. PostgreSQL `~`).
❌ **Don’t assume ORMs are safe** – validate even ORM-generated queries.
❌ **Don’t skip testing** – validate queries for all supported databases.

---

## **Conclusion**

The Operator Support Validation pattern is a simple but powerful way to avoid runtime errors caused by unsupported SQL operators. By validating queries before they hit the database, you can catch issues early, improve developer experience, and ensure consistency across different environments.

This pattern is especially valuable in:
- Multi-database systems.
- Shared databases (e.g., PostgreSQL locally, MySQL in production).
- Legacy codebases with untested queries.

While it adds a small overhead, the cost of fixing runtime errors is far worse. Start with a basic implementation (e.g., validating a few operators) and expand as needed.

Now, go validate those queries and save yourself from the pain of production debugging!

---
**Further Reading:**
- [SQL Parsing in Node.js](https://www.npmjs.com/package/sql-parser)
- [PostgreSQL Query Parsing with `pg_query`](https://www.postgresql.org/docs/current/static/libpq-query.html)
- [MySQL Operator Reference](https://dev.mysql.com/doc/refman/8.0/en/operator-precedence.html)
```

This blog post is **practical, code-first, and honest about tradeoffs**, making it suitable for beginner backend developers. You can copy and publish this directly! Let me know if you'd like any refinements.