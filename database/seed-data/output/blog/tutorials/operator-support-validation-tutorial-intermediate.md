```markdown
# **Operator Support Validation: Ensuring Query Portability Across Databases**

You’ve spent months meticulously designing a data API that scales from PostgreSQL to MySQL to Snowflake. Your team is proud—until a customer deploys your app and realizes that a critical query using `ILIKE` (PostgreSQL’s case-insensitive LIKE) fails in Snowflake, which only supports `LIKE` with `ILIKE` emulation via `LOWER()`.

Sound familiar? This is the **Operator Support Validation** problem—where your application’s query logic assumes database capabilities that don’t exist elsewhere. Best-case scenario? A runtime error. Worst case? Data inconsistencies or degraded performance.

In this post, we’ll explore how to use the **Operator Support Validation** pattern to detect unsupported operators early, in the schema design phase, before they make it to production. We’ll walk through a practical implementation in Go using SQL parsing and database capabilities manifests, discuss tradeoffs, and share lessons from real-world deployments.

---

## **The Problem: WHERE Clause Assumptions in Production**

Modern applications often target multiple database systems (Polyglot Persistence) to meet cost, performance, or compliance requirements. A common pattern is to abstract platform-specific details behind an ORM or query builder. However, this abstraction often fails when the underlying SQL syntax varies **wide** across engines.

### **Example: `ILIKE` in PostgreSQL vs. Snowflake**
| PostgreSQL | Snowflake |
|------------|-----------|
| `WHERE name ILIKE 'j%'` (case-insensitive LIKE) | ❌ Fails with `ILIKE` error |
| ✅ Works with `LOWER()` emulation: `WHERE LOWER(name) LIKE 'j%'` | ✅ Works natively with `ILIKE` |

This is just the tip of the iceberg. Other common issues include:

- **`BETWEEN` vs. `>= AND <=`**: Some databases optimize `BETWEEN`, while others don’t.
- **`LIMIT`/`OFFSET` vs. `FETCH`/`ROWNUM`**: Pagination syntax differs by engine.
- **`JOIN` predicates**: PostgreSQL allows cross-joins with `ON`, while MySQL may require `WHERE` clauses.
- **Window functions**: Snowflake and BigQuery support `OVER()`, but SQLite does not.

### **Real-World Impact**
- **Crashes**: A query with unsupported syntax fails at runtime, not during development.
- **Workarounds**: Your team adds `if` statements to rewrite queries based on the DBMS, bloating the codebase.
- **Performance pitfalls**: Unsupported operators force inefficient rewrites (e.g., `LOWER()` on indexed columns).
- **Migration pain**: Adding a new database to your stack means auditing **all** queries for compatibility.

---

## **The Solution: Operator Support Validation**

Before your query builder generates SQL, we need to:
1. **Parse the WHERE clause** to identify operators.
2. **Check a manifest of supported operators** for the target database.
3. **Fail fast** if unsupported operators are found.

This shifts validation from runtime errors to compile-time checks, ensuring only portable queries reach production.

### **Key Components**
| Component | Responsibility |
|-----------|----------------|
| **Query Parser** | Extracts operators (e.g., `ILIKE`, `BETWEEN`) from SQL. |
| **Capabilities Manifest** | Maps operators to supported databases (e.g., `ILIKE` → PostgreSQL, Snowflake). |
| **Validation Engine** | Cross-checks operators against the manifest. |
| **Query Rewriter (Optional)** | Automatically rewrites unsupported operators (e.g., `ILIKE` → `LOWER()`). |

---

## **Implementation Guide**

Let’s implement this pattern in Go using https://github.com/dolthub/go-dolthub/tree/master/sqlparser and a mock capabilities list.

### **Step 1: Define Database Capabilities**
First, create a manifest of supported operators per database. We’ll use a JSON schema for flexibility.

```yaml
# capabilities.yml
databases:
  postgres:
    operators:
      - name: ILIKE
      - name: BETWEEN
      - name: FULL
      - name: CONFIG
  mysql:
    operators:
      - name: LIKE
      - name: BETWEEN
      - name: BETWEEN (explicit range)
  snowflake:
    operators:
      - name: ILIKE  # via LOWER() emulation
      - name: FULL
      - name: CONFIG
```

### **Step 2: Parse SQL and Extract Operators**
Use a SQL parser like `go-dolthub/sqlparser` to extract operators.

```go
package main

import (
	"log"
	"strings"

	"github.com/dolthub/go-dolthub/tree/sqlparser"
)

func extractOperators(sql string) ([]string, error) {
	stmt, err := sqlparser.Parse(sql)
	if err != nil {
		return nil, err
	}

	// Simplistic: look for keywords like ILIKE, BETWEEN, etc.
	var operators []string
	switch stmt := stmt.(type) {
	case *sqlparser.Select:
		// Check WHERE clause
		if stmt.Where != nil {
			whereExpr := sqlparser.String(stmt.Where)
			operators = append(operators, extractWhereOperators(whereExpr)...)
		}
		// Add more stmt types as needed (JOINs, HAVING, etc.)
	default:
		return nil, nil // ignore non-Select statements for this example
	}
	return operators, nil
}

func extractWhereOperators(expr string) []string {
	// Lowercase and split by spaces to catch keywords
	// This is a naive approach; real-world tools use AST traversal.
	words := strings.Split(strings.ToLower(expr), " ")
	operators := make([]string, 0)
	for _, word := range words {
		if isOperator(word) {
			operators = append(operators, word)
		}
	}
	return operators
}

func isOperator(word string) bool {
	// Replace with a real operator lookup
	operatorKeywords := map[string]bool{
		"like":   true,
		"ilike":  true,
		"between": true,
		"full":   true,
		"config": true,
	}
	return operatorKeywords[word]
}
```

### **Step 3: Validate Against Capabilities**
Read the capabilities manifest and validate operators.

```go
type Capabilities struct {
	Databases map[string][]string `yaml:"databases"`
}

func (c *Capabilities) IsOperatorSupported(dbName, operator string) bool {
	operators, exists := c.Databases[dbName]
	if !exists {
		return false
	}
	for _, op := range operators {
		if op == operator {
			return true
		}
	}
	return false
}
```

### **Step 4: Run Validation**
Putting it all together:

```go
func validateQuery(sql, dbName string, capabilities *Capabilities) error {
	operators, err := extractOperators(sql)
	if err != nil {
		return err
	}

	for _, op := range operators {
		if !capabilities.IsOperatorSupported(dbName, op) {
			return fmt.Errorf("unsupported operator '%s' in '%s' for database '%s'", op, sql, dbName)
		}
	}
	return nil
}
```

### **Step 5: (Optional) Query Rewriter**
If supported, rewrite unsupported operators to safe alternatives.

```go
func rewriteQuery(sql, dbName string, capabilities *Capabilities) (string, error) {
	// Simplified: replace ILIKE in non-PostgreSQL with LOWER()
	if !capabilities.IsOperatorSupported(dbName, "ILIKE") {
		return strings.ReplaceAll(sql, "ILIKE", "LOWER() LIKE"), nil
	}
	return sql, nil
}
```

---

## **Common Mistakes to Avoid**

1. **Over-reliance on ORMs**:
   ORMs like SQLAlchemy or Entity Framework abstract queries, but they often don’t validate supported syntax. Always check raw SQL before generation.

2. **Hardcoding workarounds**:
   Don’t bury rewrites like `ILIKE` → `LOWER()` deep in query logic. Use a central validator.

3. **Ignoring edge cases**:
   Some databases support an operator in specific contexts (e.g., `FULL` in Snowflake but not in `EXISTS`). Your manifest should note these.

4. **Assuming schema-equals-capabilities**:
   A database might support `ILIKE` in some columns but not others (e.g., full-text search requires `tsvector`). Validate per-column if needed.

5. **Skipping CI integration**:
   Add this validation to your query testing pipeline. A CI failure on a PR is better than a production down.

---

## **Key Takeaways**

✅ **Validate early**: Catch unsupported operators during schema design, not runtime.
✅ **Use a capabilities manifest**: Centralize supported operators for all databases.
✅ **Parse SQL precisely**: Avoid regex; traverse the AST for accuracy.
✅ **Rewrite if needed**: Automate transformations for portable queries.
✅ **Integrate with CI**: Require validation in your pull requests.
✅ **Document tradeoffs**:
   - **Pros**: Prevents runtime errors, reduces DB-specific code.
   - **Cons**: Adds complexity to query generation; false positives if your manifest is outdated.

---

## **Conclusion**

Operator Support Validation ensures your queries are portable across databases, saving time and preventing production outages. By parsing SQL clauses and cross-checking them against a capabilities manifest, you move unsupported operators from the gray area of "it works in my dev environment" to the realm of "this is a compile-time error."

For teams using PostgreSQL, Snowflake, or MySQL, this pattern is a no-brainer. For alternate systems (e.g., SQLite, ClickHouse), an initial audit might expose 10+ unsupported operators. Fixing them early is cheaper than fixing them in production.

As always, consider the tradeoffs: This pattern adds overhead to query generation, but the cost of runtime errors is far higher. Use it strategically, and your applications will be more resilient than ever.

---

## **Further Reading**
- [SQL Standard vs. Database Operator Support](https://www.postgresql.org/docs/current/sql-keywords-appendix.html)
- [Dolthub SQL Parser](https://github.com/dolthub/go-dolthub/tree/master/sqlparser)
- [Snowflake SQL Differences](https://docs.snowflake.com/en/user-guide/sql-reference-syntax-differences)
- [Citus Query Validation](https://www.citusdata.com/blog/2021/06/22/query-validation-for-distributed-systems/) (similar concept for distributed queries)

---
**What’s your experience with operator compatibility? Have you encountered a database where common patterns failed? Share in the comments!**
```