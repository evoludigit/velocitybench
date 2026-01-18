```markdown
---
title: "The Six-Phase Compilation Process: Building Robust Query Compilers Like a Pro"
date: 2023-11-15
tags: ["database patterns", "query compilation", "backend engineering", "performance optimization"]
---

# The Six-Phase Compilation Process: Building Robust Query Compilers Like a Pro

## Introduction

As backend developers, we often find ourselves wrestling with query compilation—whether in ORMs, data access layers, or custom query builders. Compiling queries from raw input (like JSON or string literals) into optimized database operations isn't trivial. Without a structured approach, you risk writing brittle code that’s hard to maintain, inefficient, or even incorrect. This is where the **Six-Phase Compilation Process** pattern comes into play—a battle-tested approach used in projects like Prisma, SQLx, and even some ORMs in Go and Rust.

This pattern breaks down the compilation process into six clear phases, each with its own purpose and responsibilities. By following these phases, you can build compilers that are:
- **Correct**: Catch errors early (e.g., type mismatches, invalid operators).
- **Optimized**: Apply query optimizations (e.g., index hints, join ordering).
- **Maintainable**: Decouple concerns into modular phases.
- **Extensible**: Easily add support for new features (e.g., new database backends).

In this tutorial, we’ll walk through the six phases, explore real-world examples, and show you how to implement this pattern in your own projects—whether you’re building a database ORM, a query builder, or even a custom DSL for your API.

---

## The Problem: Ad-Hoc Compilation Without Clear Phases

Before diving into the solution, let’s examine why ad-hoc compilation often goes wrong. Here’s a common scenario:

You start with a simple query builder like this:

```rust
// Pseudocode: A naive query builder
fn build_query(input: String) -> String {
    let mut query = "SELECT * FROM users".to_string();
    if input.contains("name") {
        query += " WHERE name = 'Alice'";
    }
    query
}
```

This approach quickly becomes unmanageable as requirements grow. Here’s why:

1. **No Type Safety**: The `input` string could contain anything (e.g., `name = 123` or `age > 'high'`), leading to SQL injection or runtime errors.
2. **No Validation**: A query like `SELECT * FROM users WHERE name = NULL` might slip through without checking for invalid values.
3. **No Optimization**: The query is generated in one pass, so you can’t reorder joins, apply index hints, or simplify expressions.
4. **Brittle Extensibility**: Adding a new database backend (e.g., switching from PostgreSQL to MySQL) requires rewriting the entire logic.

Without phases, every change risks breaking existing functionality. The Six-Phase Compilation Process addresses this by isolating each concern into a distinct step.

---

## The Solution: Six Phases of Compilation

The Six-Phase Compilation Process is inspired by compilers (like LLVM or Rustc) and adapted for database query compilation. The phases are:

1. **Parse Input**: Convert raw input (e.g., JSON, strings) into an **abstract syntax tree (AST)**.
2. **Bind Types**: Attach database-specific types (e.g., `INT`, `TEXT`) to the AST.
3. **Generate Filter Types**: Convert filters (e.g., `WHERE name = 'Alice'`) into a standardized format.
4. **Validate**: Check for errors (e.g., invalid columns, type mismatches).
5. **Optimize**: Apply optimizations (e.g., join reordering, constant folding).
6. **Emit Artifacts**: Output the final query (SQL) and other artifacts (e.g., prepared statements).

Let’s explore each phase with practical examples.

---

## Components/Solutions: Implementing the Six Phases

### 1. Parse Input: From Raw Data to AST
The first phase converts raw input into an AST. For example, if your input is a JSON object like:
```json
{
  "select": ["name", "email"],
  "from": "users",
  "where": {
    "name": "Alice",
    "age": { "gt": 30 }
  }
}
```
The AST might look like this (in pseudocode):
```rust
struct Query {
    columns: Vec<String>,
    from: String,
    where_clause: WhereClause,
}

struct WhereClause {
    conditions: Vec<Condition>,
}

struct Condition {
    field: String,
    op: Operator, // e.g., Eq, Gt
    value: Value, // e.g., String("Alice"), Int(30)
}
```

#### Code Example (Rust)
Here’s a minimal parser using `serde_json` and a custom AST:
```rust
use serde_json::{Value, from_value};
use std::collections::HashMap;

#[derive(Debug)]
struct Query {
    columns: Vec<String>,
    from: String,
    where_clause: Option<WhereClause>,
}

#[derive(Debug)]
struct WhereClause {
    conditions: Vec<Condition>,
}

#[derive(Debug)]
enum Condition {
    Eq { field: String, value: String },
    Gt { field: String, value: i32 },
    // Add other operators as needed
}

fn parse_input(raw: &str) -> Result<Query, String> {
    let data: Value = from_value(raw.to_string()).map_err(|e| e.to_string())?;
    let mut columns = Vec::new();
    let from = data["from"].as_str().ok_or("Missing 'from' field")?.to_string();

    if let Some(columns_json) = data["select"].as_array() {
        columns = columns_json.iter()
            .filter_map(|v| v.as_str().map(|s| s.to_string()))
            .collect();
    }

    let where_clause = if let Some(where_json) = data["where"].as_object() {
        let mut conditions = Vec::new();
        for (field, value) in where_json {
            if let Value::String(s) = value {
                conditions.push(Condition::Eq { field: field.clone(), value: s.clone() });
            } else if let (Some(num), _) = (value.as_i64(), field == "age") {
                conditions.push(Condition::Gt { field: field.clone(), value: num as i32 });
            }
        }
        Some(WhereClause { conditions })
    } else {
        None
    };

    Ok(Query { columns, from, where_clause })
}
```

---

### 2. Bind Types: Attach Database-Specific Types
After parsing, the AST contains generic types (e.g., `Value`). This phase resolves them to database-specific types (e.g., `PostgresType::Text`, `PostgresType::Integer`).

#### Code Example
```rust
#[derive(Debug)]
enum PostgresType {
    Text,
    Integer,
    Timestamp,
}

fn bind_types(ast: &Query, db_config: &str) -> Result<BoundQuery, String> {
    // In a real implementation, you'd resolve types based on the database schema.
    // For simplicity, assume a mapping like this:
    let type_map = HashMap::from([
        ("name", PostgresType::Text),
        ("age", PostgresType::Integer),
    ]);

    let bound_conditions = ast.where_clause.as_ref().map(|wc| {
        WhereClause {
            conditions: wc.conditions.iter()
                .map(|cond| {
                    let type_ = type_map.get(&cond.field).ok_or_else(|| {
                        format!("Unknown field '{}'", cond.field)
                    })?;
                    match type_ {
                        PostgresType::Text => match cond {
                            Condition::Eq { value, .. } => Ok(BoundCondition::EqText { field: cond.field.clone(), value: value.clone() }),
                            _ => Err(format!("Invalid operator for text field")),
                        },
                        PostgresType::Integer => match cond {
                            Condition::Gt { value, .. } => Ok(BoundCondition::GtInt { field: cond.field.clone(), value: *value }),
                            _ => Err(format!("Invalid operator for integer field")),
                        },
                    }
                })
                .collect::<Result<_, _>>()?
        }
    });

    Ok(BoundQuery {
        columns: ast.columns.clone(),
        from: ast.from.clone(),
        where_clause: bound_conditions,
    })
}

#[derive(Debug)]
struct BoundQuery {
    columns: Vec<String>,
    from: String,
    where_clause: Option<BoundWhereClause>,
}

#[derive(Debug)]
struct BoundWhereClause {
    conditions: Vec<BoundCondition>,
}

#[derive(Debug)]
enum BoundCondition {
    EqText { field: String, value: String },
    GtInt { field: String, value: i32 },
}
```

---

### 3. Generate Filter Types: Standardize Filters
This phase converts conditions into a **standardized filter format** (e.g., a tree structure) to prepare for validation and optimization. For example:
```rust
#[derive(Debug)]
struct Filter {
    field: String,
    op: FilterOp,
    value: FilterValue,
}

#[derive(Debug)]
enum FilterOp {
    Eq,
    Gt,
    Lt,
    // etc.
}

#[derive(Debug)]
enum FilterValue {
    Text(String),
    Int(i32),
    Bool(bool),
}
```

#### Code Example
```rust
fn generate_filters(bound_query: &BoundQuery) -> Result<QueryWithFilters, String> {
    let filters = bound_query.where_clause.as_ref().map(|wc| {
        wc.conditions.iter()
            .map(|cond| {
                let filter_value = match cond {
                    BoundCondition::EqText { value, .. } => FilterValue::Text(value.clone()),
                    BoundCondition::GtInt { value, .. } => FilterValue::Int(*value),
                };
                Ok(Filter {
                    field: cond.field.clone(),
                    op: match cond {
                        BoundCondition::EqText { .. } => FilterOp::Eq,
                        BoundCondition::GtInt { .. } => FilterOp::Gt,
                    },
                    value: filter_value,
                })
            })
            .collect::<Result<_, _>>()?
    });

    Ok(QueryWithFilters {
        columns: bound_query.columns.clone(),
        from: bound_query.from.clone(),
        filters,
    })
}

#[derive(Debug)]
struct QueryWithFilters {
    columns: Vec<String>,
    from: String,
    filters: Option<Vec<Filter>>,
}
```

---

### 4. Validate: Catch Errors Early
This phase validates the query for correctness. For example:
- Ensure all fields exist in the schema.
- Check type compatibility (e.g., comparing a `Text` to an `Integer`).
- Reject invalid operators (e.g., `LIKE` on a numeric field).

#### Code Example
```rust
fn validate(query: &QueryWithFilters, schema: &HashMap<String, PostgresType>) -> Result<ValidatedQuery, String> {
    if let Some(filters) = &query.filters {
        for filter in filters {
            // Check if the field exists in the schema
            if !schema.contains_key(&filter.field) {
                return Err(format!("Field '{}' not found in schema", filter.field));
            }

            // Check type compatibility
            let expected_type = schema[&filter.field];
            match (&filter.op, &filter.value) {
                (FilterOp::Eq, FilterValue::Text(_)) if expected_type == &PostgresType::Text => {},
                (FilterOp::Gt, FilterValue::Int(_)) if expected_type == &PostgresType::Integer => {},
                _ => return Err(format!("Invalid filter: op={:?}, value={:?} for field '{}'", filter.op, filter.value, filter.field)),
            }
        }
    }
    Ok(ValidatedQuery { query: query.clone() })
}

#[derive(Debug)]
struct ValidatedQuery {
    query: QueryWithFilters,
}
```

---

### 5. Optimize: Apply Query Optimizations
This phase applies optimizations like:
- **Join Reordering**: Reorder joins to minimize the number of rows processed (e.g., start with the smallest table).
- **Constant Folding**: Simplify expressions (e.g., `age > 30 AND age < 40` → `age > 30 AND age < 40`).
- **Index Hints**: Suggest indices to the database if they improve performance.

#### Code Example (Simplified)
```rust
fn optimize(validated_query: ValidatedQuery) -> OptimizedQuery {
    // Example: Add index hints if the query is simple
    let mut optimized_query = validated_query.query;
    if validated_query.query.filters.as_ref().map_or(false, |fs| fs.len() == 1) {
        // Assume the first filter can use an index
        optimized_query.index_hint = Some("idx_users_name".to_string());
    }
    OptimizedQuery { query: optimized_query }
}

#[derive(Debug)]
struct OptimizedQuery {
    query: QueryWithFilters,
    index_hint: Option<String>,
}
```

---

### 6. Emit Artifacts: Generate SQL and Other Outputs
Finally, emit the optimized query as SQL and other artifacts (e.g., prepared statements).

#### Code Example
```rust
fn emit(optimized_query: OptimizedQuery) -> String {
    let mut sql = format!("SELECT {} FROM {}", optimized_query.query.columns.join(", "), optimized_query.query.from);

    if let Some(filters) = &optimized_query.query.filters {
        sql.push_str(" WHERE ");
        sql.push_str(&filters[0].field);
        sql.push_str(" ");
        match (&filters[0].op, &filters[0].value) {
            (FilterOp::Eq, FilterValue::Text(v)) => sql.push_str(&format!("= '{}'", v)),
            (FilterOp::Gt, FilterValue::Int(v)) => sql.push_str(&format!("> {}", v)),
            // Add other cases...
        }
    }

    if let Some(hint) = optimized_query.index_hint {
        sql.push_str(&format!(" WITH (INDEX({}))", hint));
    }

    sql
}

// Example output:
// SELECT name, email FROM users WHERE name = 'Alice' WITH (INDEX(idx_users_name))
```

---

## Implementation Guide: Putting It All Together

Here’s how you’d chain the phases together in a real-world implementation:

### Step 1: Define the Input and AST
Start with a clear input format (e.g., JSON) and define your AST.

### Step 2: Implement the Parser
Write a parser for your input format (e.g., using `serde_json` in Rust or `JSON.parse()` in JavaScript).

### Step 3: Bind Types
Resolve types from your database schema. This may involve querying the database metadata (e.g., `information_schema.columns` in PostgreSQL).

### Step 4: Generate Filters
Convert bound conditions into a standardized filter format.

### Step 5: Validate
Check for errors and reject invalid queries early.

### Step 6: Optimize
Apply optimizations based on your database’s capabilities.

### Step 7: Emit Artifacts
Generate SQL and other outputs (e.g., prepared statements for performance).

---

## Common Mistakes to Avoid

1. **Skipping Phases for "Simplicity"**:
   - Skipping validation or optimization might feel faster, but it leads to brittle code and performance issues.
   - *Fix*: Always include all phases, even if some are no-ops for simple cases.

2. **Tight Coupling Between Phases**:
   - Mixing logic across phases (e.g., validating while parsing) makes the code harder to test and extend.
   - *Fix*: Keep each phase independent and pass data explicitly between them.

3. **Ignoring Error Handling**:
   - Poor error messages make debugging frustrating. Provide clear, actionable errors.
   - *Fix*: Use detailed error types (e.g., `CompilationError::TypeMismatch`) and include context in messages.

4. **Over-Optimizing Too Early**:
   - Optimization is only useful if the query will run often. Premature optimization can make the code harder to understand.
   - *Fix*: Start with correctness, then add optimizations as needed.

5. **Not Testing Edge Cases**:
   - Test invalid inputs (e.g., `NULL` values, malformed filters) and ensure they’re caught during validation.
   - *Fix*: Write property tests for your compiler.

---

## Key Takeaways

- **The Six-Phase Compilation Process** provides a structured way to build robust query compilers.
- **Phases are modular**: Each phase has a single responsibility, making the code easier to maintain and extend.
- **Validation and optimization are critical**: They catch errors early and improve performance.
- **Start simple, then optimize**: Begin with a working implementation, then iterate on optimizations.
- **Error handling matters**: Clear errors improve developer experience and reduce debugging time.

---

## Conclusion

Building a query compiler from scratch is challenging, but the Six-Phase Compilation Process gives you a proven structure to follow. By breaking the problem into parsing, type binding, filtering, validation, optimization, and emission, you can create compilers that are correct, performant, and maintainable.

Start with a minimal implementation, iterate, and don’t forget to test! Whether you’re building an ORM, a query builder, or a custom DSL, this pattern will help you avoid common pitfalls and deliver a robust solution.

---
**Further Reading**:
- [Prisma’s Query Compiler](https://www.prisma.io/docs/concepts/components/prisma-client/querying#the-query-compiler)
- [SQLx’s Query Building](https://github.com/launchbadge/sqlx)
- [Rust’s AST Patterns](https://rust-lang.github.io/rust-clippy/rustc_ast/ast/)

**Try It Yourself**:
1. Implement the Six-Phase Compilation Process in your favorite language.
2. Start with a simple query builder and expand it with features like joins, aggregations, and subqueries.
3. Benchmark your compiler before and after optimizations to see the impact!

Happy compiling!
```