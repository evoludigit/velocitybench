```markdown
# **Operator Support Validation: Ensuring Your Database Queries Play by the Rules**

You’ve spent months building a robust API layer to abstract database queries from your application services. Your team is proud of the flexible query builder that lets clients craft complex WHERE clauses. But then—**disaster strikes**. A client fires off a request with a seemingly innocent filter, and your application crashes with a database error:

> *"Unrecognized operator 'BETWEEN' for type 'jsonb'."*

This isn’t just a bug—it’s a **dependencies mismatch**. The API layer supports the operator, but the underlying database engine doesn’t. Welcome to the **Operator Support Validation** problem.

In this post, we’ll explore how to prevent this issue by explicitly validating WHERE clause operators against the database’s supported capabilities. This pattern—**Operator Support Validation**—is a critical but often overlooked part of building resilient, production-grade database APIs. We’ll cover:
- Why this problem exists and how it manifests in real-world systems.
- A scalable solution using a **capability manifest** to enforce database compatibility.
- Practical implementations in Golang, with tradeoffs, anti-patterns, and performance considerations.

---

## **The Problem: Why Your WHERE Clauses Might Break**

Let’s start with the **why**.

### **1. Database Diversity Ignites Fragility**
Modern applications often rely on multiple database backends:
- PostgreSQL with custom extensions (e.g., JSONB functions).
- MySQL with specialized string functions (e.g., `SUBSTRING_INDEX`).
- MongoDB with its own aggregation pipeline operators.

A query builder written for one database (e.g., PostgreSQL) won’t necessarily work on another. For example:
```sql
-- Works in PostgreSQL
WHERE jsonb_column @> '{"key": "value"}'  -- JSONB operator
```

```sql
-- Fails in MySQL (no JSONB support)
WHERE json_column -> '$.key' = 'value'    -- MySQL JSON function
```

### **2. Feature Creep in the API Layer**
Over time, query builders accumulate operators to support edge cases:
- `BETWEEN` for date ranges.
- `ILIKE` (case-insensitive LIKE) for full-text search.
- Custom user-defined functions (UDFs) for domain-specific logic.

But not all databases support these operators uniformly. A PostgreSQL operator might fail in SQLite, or a MongoDB `$elemMatch` expression might break in Elasticsearch.

### **3. Silent Failures in Development**
In local or staging environments, developers might use a specific database (e.g., PostgreSQL) and miss testing against others. Production deployments often reveal these gaps when the wrong database is used.

### **4. Security Implications**
A malicious query could exploit unsupported operators to:
- Execute arbitrary code via SQL injection (e.g., `1=1; DROP TABLE users`).
- Leverage database-specific syntax to bypass authorization (e.g., `EXEC sp_helpusers` in SQL Server).

---

## **The Solution: Operator Support Validation**

The **Operator Support Validation** pattern ensures that:
1. Your query builder **only generates operators supported by the target database**.
2. The database schema **explicitly declares supported operators** (via a capability manifest).
3. The runtime **validates operators before compilation/execution**.

This approach turns a runtime error into a compile-time check, making failures predictable and easier to debug.

### **Key Components of the Solution**
1. **Capability Manifest**: A configuration file or runtime-definition listing which operators are supported by each database.
2. **Operator Whitelist**: During query parsing, the builder checks if an operator exists in the manifest for the target database.
3. **Fallback Behavior**: For unsupported operators, the system can either:
   - Reject the query (fail fast).
   - Provide a custom fallback (e.g., convert `BETWEEN` to `>= AND <=` if not natively supported).
   - Delegate to a different database (e.g., route to a PostgreSQL read replica if SQLite lacks JSON support).

---

## **Implementation Guide: Golang Example**

Let’s build a proof-of-concept using Golang, focusing on a **where clause validator** for a PostgreSQL-like query builder.

### **Step 1: Define the Capability Manifest**
First, we’ll create a struct to represent database capabilities. This could be loaded from a config file or database metadata.

```go
package validator

import (
	"database/sql/driver"
	"errors"
	"fmt"
)

// SupportedOperator represents a database operator with its supported data types.
type SupportedOperator struct {
	Name     string
	DataTypes []string // e.g., "int4", "text", "jsonb"
}

// DatabaseCapabilities describes the supported operators for a specific DB.
type DatabaseCapabilities struct {
	Name           string
	WhereOperators []SupportedOperator
	JoinOperators  []SupportedOperator
	// ... other clauses
}

// CapabilityManifest holds capabilities for all supported databases.
type CapabilityManifest struct {
	Databases map[string]DatabaseCapabilities
}
```

Example manifest for PostgreSQL:
```go
// NewPostgresManifest returns a manifest for PostgreSQL.
func NewPostgresManifest() CapabilityManifest {
	return CapabilityManifest{
		Databases: map[string]DatabaseCapabilities{
			"postgres": {
				Name: "PostgreSQL",
				WhereOperators: []SupportedOperator{
					{Name: "=", DataTypes: {"int4", "text", "jsonb"}},
					{Name: ">", DataTypes: {"int4", "numeric"}},
					{Name: "<", DataTypes: {"int4", "numeric"}},
					{Name: "BETWEEN", DataTypes: {"int4", "timestamp"}},
					{Name: "@>", DataTypes: {"jsonb"}}, // JSONB operator
				},
			},
		},
	}
}
```

---

### **Step 2: Parse and Validate the WHERE Clause**
Next, we’ll write a parser/validator that checks clauses against the manifest. For simplicity, we’ll use a recursive descent parser for WHERE conditions (in a real system, you’d use a proper library like `go-ast` or `antlr`).

```go
package validator

import (
	"errors"
	"fmt"
	"strings"
)

// WhereCondition represents a parsed WHERE clause.
type WhereCondition struct {
	Left     interface{} // Column name or expression
	Operator string
	Right    interface{} // Value or expression
}

// ParseWhere parses a raw WHERE clause into a structured form.
func ParseWhere(whereClause string) (*WhereCondition, error) {
	// Simplified parser (real-world: use a proper parser generator)
	parts := strings.Fields(whereClause)
	if len(parts) < 3 {
		return nil, errors.New("invalid WHERE clause")
	}

	return &WhereCondition{
		Left:     parts[0],
		Operator: parts[1],
		Right:    strings.Join(parts[2:], " "),
	}, nil
}

// ValidateWhere checks if an operator is supported by the database.
func (vc *WhereCondition) Validate(dbName, columnType string, manifest CapabilityManifest) error {
	caps, ok := manifest.Databases[dbName]
	if !ok {
		return fmt.Errorf("unsupported database: %s", dbName)
	}

	// Check if the operator is in the manifest.
	for _, op := range caps.WhereOperators {
		if op.Name == vc.Operator {
			// Check if the operator supports the column type.
			for _, supportedType := range op.DataTypes {
				if supportedType == columnType {
					return nil
				}
			}
			return fmt.Errorf("operator '%s' not supported for type '%s'", vc.Operator, columnType)
		}
	}

	return fmt.Errorf("operator '%s' is not supported by %s", vc.Operator, dbName)
}
```

---

### **Step 3: Integrate with a Query Builder**
Now, modify a query builder (e.g., `sqlx`) to validate clauses before execution.

```go
package main

import (
	"fmt"
	"log"
	"operator-validator/validator"
)

func main() {
	// Load capabilities for PostgreSQL.
	manifest := validator.NewPostgresManifest()

	// Simulate a query with a potentially unsupported operator.
	whereClause := "age > 30" // Valid
	unsafeClause := "json_data @> '{\"key\":\"value\"}'" // Invalid for SQLite

	// Parse and validate.
	cond, err := validator.ParseWhere(whereClause)
	if err != nil {
		log.Fatalf("Failed to parse: %v", err)
	}
	if err := cond.Validate("postgres", "int4", manifest); err != nil {
		log.Fatalf("Validation failed: %v", err)
	}
	fmt.Println("✅ Valid query:", whereClause)

	// Test the unsafe clause.
	unsafeCond, err := validator.ParseWhere(unsafeClause)
	if err != nil {
		log.Fatalf("Failed to parse: %v", err)
	}
	if err := unsafeCond.Validate("sqlite", "json", manifest); err != nil {
		log.Fatalf("❌ %v", err) // Output: "operator '@>' is not supported by sqlite"
	}
}
```

---

### **Step 4: Extending for Complex Cases**
In a real system, you’d need to handle:
- **Composite conditions** (`WHERE (age > 30 AND status = 'active')`).
- **Subqueries** (e.g., `WHERE id IN (SELECT user_id FROM sessions)`).
- **Custom functions** (e.g., `WHERE extract(year FROM created_at) = 2023`).
- **Dynamic type inference** (e.g., guessing `jsonb` vs `text` for a column).

Here’s how you might extend the validator for composite conditions:

```go
// CompositeWhereCondition handles AND/OR clauses.
type CompositeWhereCondition struct {
	Left     *WhereCondition
	Operator string // "AND" or "OR"
	Right    *WhereCondition
}

func (cwc *CompositeWhereCondition) Validate(dbName, colType string, manifest CapabilityManifest) error {
	// Validate left child.
	if err := cwc.Left.Validate(dbName, colType, manifest); err != nil {
		return err
	}

	// Validate right child.
	if err := cwc.Right.Validate(dbName, colType, manifest); err != nil {
		return err
	}

	return nil
}
```

---

## **Common Mistakes to Avoid**

1. **Hardcoding Database-Specific Logic in the Manifest**
   Avoid writing database-specific logic in the manifest itself. Instead, use a lightweight schema (e.g., `jsonb`) to define capabilities dynamically.

2. **Overly Permissive Whitelists**
   Don’t include every possible operator from every database. Focus on the ones your application actually uses.

3. **Ignoring Performance Tradeoffs**
   Operator validation adds overhead. Profile your query paths to ensure this check doesn’t become a bottleneck.

4. **Assuming Schema = Capabilities**
   A column may exist in the schema but not support certain operators. Always validate both existence and operability.

5. **Silently Falling Back to Unsupported Operators**
   A better approach is to fail fast with a clear error message (e.g., `"Operator 'BETWEEN' not supported for SQLite"`).

---

## **Key Takeaways**
- **Problem**: Database operator mismatches cause runtime failures, breaking client expectations.
- **Solution**: Use a **capability manifest** to validate operators before query execution.
- **Implementation**:
  - Parse WHERE clauses into structured conditions.
  - Check operators against a predefined manifest for the target database.
  - Fail fast with clear error messages.
- **Tradeoffs**:
  - Adds validation overhead (but negligible compared to query execution).
  - Requires maintaining the manifest (but reduces runtime bugs).
- **Extensions**:
  - Support nested conditions, subqueries, and dynamic typing.
  - Integrate with ORMs like GORM or sqlx for seamless validation.

---

## **Conclusion: Defend Your API Against Database Inconsistencies**
The **Operator Support Validation** pattern is a small but powerful tool in your backend engineer’s toolkit. By validating operators upfront, you:
- Prevent cryptic runtime errors.
- Ensure consistency across database backends.
- Harden your system against malicious or malformed queries.

Start with a minimal implementation for your most critical queries, then expand as needed. Remember: **the goal isn’t to restrict operators, but to ensure they work reliably where you need them.**

Next steps:
- Integrate this with a query profiler to track operator usage.
- Combine with **schema migration validation** for even tighter control.
- Explore **runtime capability detection** (e.g., querying `information_schema` for supported operators).

Happy validating!
```

---
**P.S.** For a production-ready implementation, consider using tools like:
- [OpenTelemetry](https://opentelemetry.io/) to trace operator validation decisions.
- [Sqlparser](https://github.com/volatiletech/sqlparser) for robust SQL parsing.
- [SQL Mesh](https://sqlmesh.com/) for multi-database query compatibility.

Would you like a deeper dive into any specific part (e.g., handling joins or custom functions)?