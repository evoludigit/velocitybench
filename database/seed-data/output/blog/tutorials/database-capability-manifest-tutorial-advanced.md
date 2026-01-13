```markdown
---
title: "Database Capability Manifest: Compiling Portable SQL Across Heterogeneous Backends"
date: 2023-11-15
tags: ["database", "sql", "backend design", "dbms", "portability"]
author: "Arianna Ferrante"
---

# Database Capability Manifest: Compiling Portable SQL Across Heterogeneous Backends

As backend engineers, we’ve all faced the headache of writing SQL that works in PostgreSQL but fails catastrophically in MySQL—only to remember your staging database uses SQL Server. The frustration isn’t just about syntax errors; it’s about wasted cycles rewriting queries, debugging `ERROR 1064 (42000)` at 3 AM, or worse, silent data corruption from misinterpreted functions.

In this post, we’ll explore a pattern called **Database Capability Manifest and Multi-Target Compilation**, which FraiseQL uses to handle SQL portability systematically. This approach compiles queries into database-specific SQL *before* execution, ensuring consistency across databases while gracefully handling their quirks. Let’s dive into why this matters, how it works, and how you can implement it in your own projects.

---

## The Problem: "Write Once, Run Anywhere" Doesn’t Apply to SQL

SQL isn’t just about syntax—it’s about the *features* each database supports. A query that works in Postgres might return different results (or even fail) in MySQL, SQLite, or SQL Server due to:

1. **Missing or Incompatible Functions**:
   - `FILTER` clauses (Postgres) → No equivalent in MySQL (only `CASE WHEN`).
   - `JSONB` functions (Postgres) → `JSON` functions (MySQL) or no JSON support (SQLite).
   - `STDDEV_POP` (SQL Server) → `STDDEV()` (Postgres) → `STDDEV()` (MySQL, but different behavior).

2. **Syntax Variances**:
   - `DATE_TRUNC('day', timestamp)` (Postgres) → `DATE_FORMAT(timestamp, '%Y-%m-%d')` (MySQL).
   - `PERCENTILE_CONT(0.95)` (Postgres) → No equivalent; requires manual calculation in MySQL.
   - `GIN indexes` (Postgres) → `SPATIAL indexes` (MySQL) or no index type aliasing (SQLite).

3. **Behavioral Differences**:
   - `GROUP_CONCAT` (MySQL) vs. no equivalent in Postgres (use `STRING_AGG`).
   - `strftime` (SQLite) vs. `DATE_FORMAT` (MySQL) vs. `TO_CHAR` (Oracle).
   - `DISTINCT ON` (Postgres) → No alternative in MySQL/SQLite.

These differences aren’t just annoying—they can lead to:
- **Data inconsistencies**: A query might return 5 rows in Postgres but 6 in MySQL due to `GROUP_CONCAT` vs. `STRING_AGG` behavior.
- **Runtime errors**: Using `JSONB` in MySQL throws an error unless wrapped in `JSON_EXTRACT`.
- **Performance degradation**: Falling back to inefficient workarounds (e.g., `CASE WHEN` for `FILTER`).

---

## The Solution: Capability Manifest + Multi-Target Compilation

To solve this, we need a **compile-time approach** that:
1. **Detects** which database features are available for a given target.
2. **Validates** that the query uses only compatible features.
3. **Transforms** the query into database-specific SQL with fallbacks.
4. **Generates** optimized queries for each backend.

This is what FraiseQL’s **Database Capability Manifest** pattern does. Here’s how it works:

### 1. **Capability Manifest: A JSON/YAML Configuration**
We define a manifest that lists all available operators, functions, and features per database. This acts as a "contract" for what each database supports. Example:

```json
// capability-manifest.json
{
  "databases": {
    "postgres": {
      "features": {
        "filter_clause": true,
        "jsonb_support": true,
        "stddev": { "function": "STDDEV", "population": "STDDEV_POP", "sample": "STDDEV_SAMP" },
        "percentiles": {
          "continuous": "PERCENTILE_CONT",
          "discrete": "PERCENTILE_DISC"
        }
      },
      "functions": {
        "date_trunc": {
          "syntax": "DATE_TRUNC(unit, timestamp)",
          "units": ["minute", "hour", "day", "month", "year"]
        },
        "strftime": false
      }
    },
    "mysql": {
      "features": {
        "filter_clause": false,
        "jsonb_support": false,
        "stddev": { "function": "STDDEV", "population": "STDDEV", "sample": "STD" },
        "percentiles": false
      },
      "functions": {
        "date_trunc": false,
        "date_format": true,
        "strftime": false
      }
    },
    "sqlite": {
      "features": {
        "filter_clause": false,
        "jsonb_support": false,
        "stddev": false,
        "percentiles": false
      },
      "functions": {
        "date_trunc": false,
        "date_format": false,
        "strftime": true
      }
    },
    "sqlserver": {
      "features": {
        "filter_clause": false,
        "jsonb_support": false,
        "stddev": { "function": "STDEV", "population": "STDEVP", "sample": "STDEVS" },
        "percentiles": false
      },
      "functions": {
        "date_trunc": false,
        "datepart": true,
        "strftime": false
      }
    }
  }
}
```

### 2. **Compile-Time Detection**
Before generating SQL, the compiler checks:
- Which database target the query is being compiled for.
- Whether all functions/operators in the query are supported.
- If not, it applies fallbacks or raises errors.

Example: If a query uses `FILTER`, the compiler checks the manifest and replaces it with `CASE WHEN` for MySQL/SQL Server.

### 3. **SQL Lowering: Generating Database-Specific SQL**
The compiler "lowers" high-level queries into database-specific SQL. For example:

#### Original Query (FraiseQL DSL):
```sql
-- fraiseql (pseudo-DSL)
SELECT user_id, AVG(rating) FILTER (WHERE rating >= 4) AS avg_rating
FROM reviews
GROUP BY user_id;
```

#### PostgreSQL Output:
```sql
SELECT
    user_id,
    AVG(rating) FILTER (WHERE rating >= 4) AS avg_rating
FROM reviews
GROUP BY user_id;
```

#### MySQL Output:
```sql
SELECT
    user_id,
    SUM(CASE WHEN rating >= 4 THEN rating ELSE NULL END) / COUNT(CASE WHEN rating >= 4 THEN 1 END) AS avg_rating
FROM reviews
GROUP BY user_id;
```

#### SQLite Output (fallback):
```sql
SELECT
    user_id,
    SUM(CASE WHEN rating >= 4 THEN rating ELSE NULL END) / NULLIF(SUM(CASE WHEN rating >= 4 THEN 1 END), 0) AS avg_rating
FROM reviews
GROUP BY user_id;
```

### 4. **Fallback Strategies**
The compiler includes rules for common fallbacks:
| **Feature**          | **Postgres**       | **MySQL/SQL Server**          | **SQLite**                     |
|----------------------|--------------------|--------------------------------|--------------------------------|
| `FILTER`             | `WHERE` in aggregate | `CASE WHEN`                    | `CASE WHEN` (with `NULLIF` for division) |
| `PERCENTILE_CONT(0.9)` | `PERCENTILE_CONT`   | Manual calculation (percentile formula) | Manual calculation          |
| `JSONB` functions    | `->`, `->>`       | `JSON_EXTRACT`, `->`          | No JSON support (fallback to string parsing) |
| `DATE_TRUNC`         | `DATE_TRUNC`       | `DATE_FORMAT`                   | `strftime`                      |

---

## Implementation Guide

### Step 1: Define Your Capability Manifest
Start by documenting all the features your application uses across databases. Example:

```yaml
# capability-manifest.yaml
databases:
  postgres:
    features:
      filter_clause: true
      jsonb: true
      stddev: true
      percentiles: true
    functions:
      date_trunc:
        syntax: "DATE_TRUNC(unit, timestamp)"
        units: ["minute", "hour", "day", "month", "year"]
      strftime: false
  mysql:
    features:
      filter_clause: false
      jsonb: false
      stddev: true
      percentiles: false
    functions:
      date_trunc: false
      date_format: true
      strftime: false
  sqlite:
    features:
      filter_clause: false
      jsonb: false
      stddev: false
      percentiles: false
    functions:
      date_trunc: false
      date_format: false
      strftime: true
```

### Step 2: Build a Compiler Pipeline
Your compiler should:
1. Parse the input query (FraiseQL DSL, SQL, or another abstraction).
2. Validate it against the manifest for the target database.
3. Transform it into database-specific SQL.

#### Example Compiler Pseudocode (Python-like):
```python
def compile_query(query, target_db):
    # Step 1: Parse the query into an AST
    ast = parse_query(query)

    # Step 2: Check compatibility with the target DB
    manifest = load_capability_manifest()
    for node in ast.nodes:
        if node.op == "FILTER" and not manifest[target_db]["features"]["filter_clause"]:
            raise UnsupportedFeatureError("FILTER not supported in MySQL")

    # Step 3: Lower to database-specific SQL
    db_sql = lower_ast(ast, target_db)

    return db_sql
```

### Step 3: Implement SQL Lowering Rules
Create rules for common transformations. Here’s a snippet for `FILTER`:

```python
def lower_filter(node, target_db):
    if target_db == "postgres":
        return f"FILTER ({node.condition})"
    else:
        # MySQL/SQL Server: Replace FILTER with CASE WHEN
        return f"CASE WHEN {node.condition} THEN {node.column} ELSE NULL END"
```

### Step 4: Handle Edge Cases
- **Null Handling**: SQLite’s `NULLIF` is crucial for avoiding division by zero in fallbacks.
- **Aggregate Functions**: Replace `GROUP_CONCAT` (MySQL) with `STRING_AGG` (Postgres).
- **Date Functions**: Map `DATE_TRUNC` to `DATE_FORMAT` or `strftime` where needed.

---

## Common Mistakes to Avoid

1. **Assuming "SQL" is Universal**:
   - Not all databases support `LIMIT-OFFSET` (SQLite uses `OFFSET-LIMIT`).
   - `ORDER BY RAND()` works in Postgres but may not be deterministic in other DBs.

2. **Ignoring Performance Fallbacks**:
   - Replacing `FILTER` with `CASE WHEN` can be 10x slower for large datasets.
   - Always benchmark fallbacks (e.g., `PERCENTILE_DISC` vs. manual calculation).

3. **Overlooking NULL Handling**:
   - SQLite treats `NULL` in aggregates differently than Postgres/MySQL.
   - Example: `AVG(NULL) = NULL` (Postgres) vs. `AVG(NULL) = NULL` (MySQL) vs. `AVG(NULL) = 0` (SQLite in some versions).

4. **Hardcoding Database-Specific Code**:
   - Never let SQL strings intermingle with your logic. Use a compiler to enforce separation.

5. **Not Validating at Compile Time**:
   - Catch errors early with static checks. For example:
     ```python
     if not manifest[target_db]["features"]["jsonb"]:
         raise Error("JSONB functions not supported in MySQL")
     ```

---

## Key Takeaways

- **Database portability requires intentional design**: Writing SQL without considering the target database leads to technical debt.
- **Compile-time validation is critical**: Catch compatibility issues before runtime.
- **Fallbacks are necessary but costly**: Optimize fallbacks (e.g., avoid `CASE WHEN` for large datasets).
- **Automate SQL generation**: Use a compiler to enforce consistency and reduce manual rewrites.
- **Document your manifest**: Keep it up-to-date as you add new features.

---

## Conclusion

The Database Capability Manifest pattern is a powerful way to handle SQL portability without sacrificing performance or correctness. By decoupling your queries from specific database quirks and compiling them at build time, you ensure that your application runs consistently across Postgres, MySQL, SQLite, and SQL Server.

This approach is especially valuable in:
- Microservices where each service might use a different database.
- Serverless architectures where database choice varies by region.
- Open-source libraries where users might deploy on any backend.

Start small—define a manifest for your most critical queries, then gradually expand it. Over time, you’ll build a robust system where "write once, run anywhere" becomes a reality for your SQL.

---
**Further Reading**:
- [FraiseQL’s SQL Compiler](https://github.com/fraise-lang/fraiseql)
- [SQLite vs. PostgreSQL: A Feature Comparison](https://www.sqlite.org/lang.html)
- [MySQL vs. PostgreSQL: Aggregate Functions](https://dev.mysql.com/doc/refman/8.0/en/group-by-functions.html)
```