```markdown
# **Capability Manifest Design: Explicitly Define Database Features for Smarter Query Processing**

As backend developers, we often grapple with API and database interactions that feel like fishing in the dark—we know there should be a way to do something, but mapping out all the possible combinations of features, constraints, and capabilities can be tedious. Imagine building a SQL query optimizer that doesn’t know what functions or operators your database supports. Or designing an ORM that tries to map every object to a table without knowing which extensions are available.

The **Capability Manifest Design** pattern addresses these challenges by explicitly declaring what features a database or system supports—enabling smarter APIs, optimized query compilers, and more agile application design. This approach is particularly powerful in systems like **FraiseQL**, where the database engine needs to compile queries dynamically based on available features.

This tutorial will walk you through the problems this pattern solves, how it works, and how you can implement it in your own projects. By the end, you’ll understand when to use this pattern, how to model database capabilities, and how it can simplify complex system interactions.

---

## **The Problem: Hardcoded Database Feature Support Matrix**

Most systems with backend/database interactions rely on implicit assumptions about supported features. For example:
- **APIs** may assume a database supports JSON functions, but what if it doesn’t?
- **Query compilers** may include `WITH RECURSIVE` clauses in their templates, but some databases (like older MySQL versions) don’t support them.
- **ORMs** may generate `JOIN` queries but fail silently when the database lacks specific join types.

### **Real-World Pain Points**
Here’s how these assumptions often lead to problems:

1. **Silent Failures**
   A query optimizer might include `ARRAY_AGG` and fail with a runtime error (`ERROR: function array_agg does not exist`).

2. **Overqualified Queries**
   APIs may generate overly complex queries that work in some databases but are inefficient or unsupported in others.

3. **Debugging Nightmares**
   A system that doesn’t explicitly track supported features makes it difficult to debug why a query fails—was it a syntax error, or did the database lack the required capability?

4. **Vendor Lock-in**
   If a system hardcodes features for a specific database (e.g., PostgreSQL-only functions), it becomes harder to migrate to other databases.

---

## **The Solution: Capability Manifests**

The **Capability Manifest** pattern explicitly declares what features a database or system supports. This is done through a structured way of documenting:
- **Operators** (`+`, `=`, `LIKE`, `IN`)
- **Functions** (`SUM()`, `GROUP_CONCAT()`, `ARRAY_AGG()`)
- **Extensions** (`postgis`, `pg_trgm`)
- **Query Features** (`WITH RECURSIVE`, `Common Table Expressions`, `JSON operations`)

By defining these capabilities upfront, the system can:
✔ **Compensate dynamically** when a feature is missing.
✔ **Optimize queries** based on available features.
✔ **Fail early** with clear error messages instead of runtime crashes.
✔ **Support multiple database backends** without hardcoding.

---

## **Components of the Capability Manifest**

A capability manifest typically includes:

1. **Capabilities Metadata**
   - A structured schema describing what features are supported (e.g., JSON, YAML, or a database table).

2. **Feature Kits**
   - Groups of related capabilities (e.g., "JSON Functions," "Window Functions").

3. **Compiler/Query Planner Integration**
   - Uses the manifest to decide how to compile or rewrite queries.

4. **API Layer Adaptation**
   - If writing an ORM or API layer, use the manifest to generate compatible queries.

---

## **Code Examples: Implementing a Capability Manifest**

### **Example 1: JSON Manifest for FraiseQL (Conceptual)**
FraiseQL declares supported features in a structured way. Here’s how a capability manifest might look:

```json
{
  "database": "postgresql",
  "version": "15",
  "capabilities": {
    " Operators": {
      "supports": ["=", "+", "->", "->>", "JSON_EXTRACT_PATH_TEXT"]
    },
    "Functions": {
      "aggregates": ["SUM", "COUNT", "AVG", "ARRAY_AGG"],
      "window": ["LEAD", "LAG", "RANK", "DENSE_RANK"],
      "json": ["JSON_EXTRACT_PATH_TEXT", "JSONB_SET"]
    },
    "Extensions": ["postgis", "pg_trgm"],
    "QueryFeatures": {
      "CTEs": true,
      "RecursiveCTEs": true,
      "JSONOperations": true
    }
  }
}
```

This manifest would help FraiseQL’s query compiler decide whether it can use `ARRAY_AGG` or whether it needs to rewrite a query to work without it.

---

### **Example 2: Database Table-Based Capabilities**
Instead of a JSON file, you could store capabilities in a database table:

```sql
CREATE TABLE database_capabilities (
  database_name VARCHAR(50) PRIMARY KEY,
  is_operator_supported BOOLEAN,
  is_function_supported BOOLEAN,
  supported_operators JSONB,
  supported_functions JSONB,
  has_recursive_ctes BOOLEAN,
  extensions JSONB
);
```

**Insert Example:**
```sql
INSERT INTO database_capabilities (
  database_name,
  is_operator_supported,
  supported_operators,
  supported_functions,
  has_recursive_ctes,
  extensions
) VALUES (
  'postgresql',
  TRUE,
  '{"operators": ["=", "+", "->"], "operators.json": ["JSONB_EXTRACT_PATH"]}',
  '{"aggregates": ["SUM", "ARRAY_AGG"], "window": ["LEAD"]}',
  TRUE,
  '["postgis", "pg_trgm"]'
);
```

---

### **Example 3: Runtime Query Adapter (API Layer)**
If you’re building an API layer that needs to adapt to different database capabilities, you could use the manifest to generate compatible queries:

```go
package main

import (
	"fmt"
	"encoding/json"
)

// CapabilityManifest defines the supported features of a database
type CapabilityManifest struct {
	Database string      `json:"database"`
	Version  string      `json:"version"`
	Capabilities struct {
		Operators struct {
			Supports []string `json:"supports"`
		} `json:"operators"`
		Functions struct {
			JSON []string `json:"json"`
		} `json:"functions"`
	} `json:"capabilities"`
}

func (cm *CapabilityManifest) CanUseJSONFunction(funcName string) bool {
	for _, fn := range cm.Capabilities.Functions.JSON {
		if fn == funcName {
			return true
		}
	}
	return false
}

// GenerateQuery adapts queries based on the manifest
func GenerateQuery(manifest *CapabilityManifest, query string) string {
	if manifest.Database == "postgresql" {
		if !manifest.CanUseJSONFunction("JSONB_SET") {
			// Fallback for older versions
			return rewriteToLegacyFormat(query)
		}
		return query // Safe to use
	}
	// Handle other databases
	return query
}

func main() {
	manifest := &CapabilityManifest{
		Database: "postgresql",
		Version: "15",
		Capabilities: struct {
			Operators struct {
				Supports []string `json:"supports"`
			} `json:"operators"`
			Functions struct {
				JSON []string `json:"json"`
			} `json:"functions"`
		}{
			Operators: struct{ Supports []string }{
				Supports: []string{"=", "+", "->"},
			},
			Functions: struct {
				JSON []string `json:"json"`
			}{
				JSON: []string{"JSONB_SET", "JSONB_EXTRACT_PATH_TEXT"},
			},
		},
	}

	query := `SELECT JSONB_SET(data->'config', '{engine}', 'postgres') FROM users;`
	modifiedQuery := GenerateQuery(manifest, query)
	fmt.Println("Generated Query:", modifiedQuery)
}
```

This illustrates how a manifest can help an API layer dynamically adapt queries to the database’s capabilities.

---

## **Implementation Guide: How to Add Capability Manifests to Your Project**

### **Step 1: Define Your Capabilities**
Start by documenting the features your system needs to track. Ask:
- Which operators/functions does my query planner need?
- Which database extensions matter?
- Are there query features I avoid if not supported?

### **Step 2: Choose a Representation**
Decide how to store the manifest:
- **JSON/YAML file**: Good for small, fixed databases.
- **Database table**: Best for dynamic environments.
- **Language struct**: Ideal for compiler integration.

### **Step 3: Load the Manifest at Runtime**
Load the manifest when your system initializes:
```go
// Pseudocode for loading from JSON
var manifest CapabilityManifest
file, _ := os.Open("capabilities.json")
defer file.Close()
json.NewDecoder(file).Decode(&manifest)
```

### **Step 4: Integrate with Query Processing**
Use the manifest to:
- Rewrite queries if a feature is missing.
- Skip certain optimizations.
- Fail early with helpful errors.

### **Step 5: Test Edge Cases**
Ensure your system handles:
- Missing capabilities gracefully.
- Unsupported queries without crashing.
- Mixed environments (e.g., PostgreSQL and MySQL).

---

## **Common Mistakes to Avoid**

### **1. Overcomplicating the Manifest**
A manifest should be simple and maintainable. Avoid listing every single operator—group related features (e.g., "JSON functions" instead of "JSONB_EXTRACT_PATH_TEXT," "JSONB_SET," etc.).

### **2. Not Updating the Manifest**
If you add a new feature, the manifest must be updated. Otherwise, your system will silently fail.

### **3. Over-Reliance on the Manifest**
The manifest is a guide, not a silver bullet. Always test queries across databases.

### **4. Ignoring Performance Implications**
If your manifest is stored in a database table, ensure it doesn’t slow down query compilation.

### **5. Forgetting to Handle Missing Capabilities**
A manifest without a fallback is useless. Always plan for the case where a feature isn’t available.

---

## **Key Takeaways**

- **Capability Manifests** make database interactions explicit.
- They enable **smarter query processing** by knowing available features.
- They **reduce silent failures** by checking capabilities early.
- They promote **multi-database compatibility** by documenting differences.
- **Tradeoffs**: Requires upfront effort, but pays off in long-term maintainability.

---

## **Conclusion**

The **Capability Manifest Design** pattern is a powerful way to handle the complexity of database interactions. By explicitly declaring what features your system supports, you avoid silent failures, optimize queries, and make your application more adaptable.

If you’re building a query compiler, ORM, or database abstraction layer, consider adopting this pattern. Start small—document the capabilities you need—and gradually expand as your project grows. The result will be a system that’s more reliable, flexible, and easier to debug.

Now go ahead and give it a try! Your future self (and your users) will thank you.

---
**Further Reading:**
- [FraiseQL Documentation](https://fraise.dev/) (Example of capability-driven compilation)
- [PostgreSQL Operator Reference](https://www.postgresql.org/docs/current/functions-operators.html) (For inspiration on manifest entries)
```