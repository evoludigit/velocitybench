```markdown
# **Capability Detection Runtime: Building Databases That Adapt to What They Can Do**

*How a clever query compiler uses runtime feature probing to handle incompatibilities—and why this pattern matters for your own database or query layer.*

---

## Introduction

Imagine writing a query that works perfectly in PostgreSQL version 15—but crashes in MySQL 8.0, or requires a radical rewrite when you switch from a traditional SQL database to ClickHouse. Hidden incompatibilities between database features, versions, and extensions can silently break your application. Worse, many databases provide *enough* functionality to make you believe everything will work… until it doesn’t.

This is the "hardcoded assumption" problem—a common pitfall in database and query-layer design. Traditionally, applications rely on fixed assumptions about what their database supports, leading to brittle code that either fails spectacularly or silently downgrades performance. **The Capability Detection Runtime (CDR) pattern** flips this on its head: instead of assuming features exist, the query compiler *probes* the database at runtime to dynamically tailor its behavior.

Developed in tools like **FraiseQL** (a query compilation framework), CDR is a pragmatic way to handle feature gaps gracefully—without rewriting your entire query layer for every database. In this post, we’ll explore how CDR works, why it’s valuable, and how you can adapt it for your own projects.

---

## The Problem: Hardcoded Assumptions About Database Features

Let’s start with a concrete example. Suppose you’re writing a query layer that supports **window functions** with `PARTITION BY` and `ORDER BY`. Your code looks something like this:

```sql
-- Works in most modern databases, but what if they don’t?
SELECT
    user_id,
    order_id,
    SUM(amount) OVER (PARTITION BY user_id ORDER BY order_date) AS running_total
FROM orders;
```

Seems simple, right? But what if your database:
- Is PostgreSQL, but lacks a critical extension?
- Is MySQL, which only supports `PARTITION BY` without `ORDER BY` in window functions?
- Is SQLite, where window functions are an experimental feature requiring special handling?
- Is an older version of PostgreSQL where `ORDER BY` in window functions is buggy?

Without runtime checks, your code might:
- **Crash spectacularly** with an unhandled error.
- **Return incorrect results** due to misinterpreted syntax.
- **Silently degrade performance** by falling back to inefficient alternatives.

This is the core challenge of database abstraction: you need to write code that works **without knowing the exact capabilities** of the underlying system.

---

## The Solution: Runtime Capability Detection

The **Capability Detection Runtime (CDR)** pattern addresses this by:
1. **Probing** the database at runtime to determine available features (e.g., supported SQL syntax, extensions, operator versions).
2. **Adapting** the query compilation process based on those findings.
3. **Providing graceful fallbacks** when features are missing (e.g., rewriting a window function into a subquery when `ORDER BY` in windows isn’t supported).

### How It Works (High-Level)

1. **Feature Probing**: The compiler sends lightweight queries to detect capabilities.
   ```sql
   -- Example: Check if the database supports window functions with ORDER BY
   SELECT EXISTS (
       SELECT 1 FROM information_schema.views
       WHERE view_name = 'pg_version' AND view_definition LIKE '%window%'
   );
   ```

2. **Dynamic Compilation**: The compiled query is adjusted based on the response.
   - If `ORDER BY` in windows is supported, use the optimized syntax.
   - If not, rewrite as a correlated subquery.

3. **Fallback Logic**: When a feature is unavailable, the compiler selects the least costly alternative.

---

## Components of the Capability Detection Runtime

Let’s break down the key pieces of CDR:

### 1. The Prober
A module that queries the database for metadata about its capabilities. Examples:
- **SQL Version**: Check `SELECT version();` to infer supported syntax.
- **Extension Support**: Query `information_schema.extensions` (PostgreSQL) or `SHOW PLUGINS` (MySQL).
- **Operator Support**: Test if a function or operator exists (e.g., `SELECT EXISTS (SELECT 1 FROM pg_operator WHERE oprname = '&&')`).

### 2. The Compiler Adapter
Modifies the abstract syntax tree (AST) of queries based on detected capabilities. For example:
- If window functions are unsupported, replace `OVER (PARTITION BY ...)` with a self-join or CTE.

### 3. Fallback Strategies
A library of alternative query formulations for unsupported features. Examples:
| Feature          | Supported Syntax               | Fallback                          |
|------------------|--------------------------------|-----------------------------------|
| Window Functions | `OVER (PARTITION BY ...)`      | Correlated subqueries             |
| JSON Path       | `jsonb_path_query`             | String manipulation               |
| Window Aggregates| `SUM() OVER (...)`             | Ranking function with subqueries   |

### 4. Performance Monitor
Tracks which fallbacks are used and suggests optimizations (e.g., "This database lacks window functions; consider upgrading").

---

## Code Examples: Implementing CDR in Practice

Let’s dive into practical examples. We’ll simulate CDR in a hypothetical query compiler.

### Example 1: Probing for Window Function Support

```python
def probe_window_functions(conn):
    """Detects if the database supports window functions with ORDER BY."""
    # Test query: Check if ORDER BY works in window clauses
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                (SELECT EXISTS (
                    SELECT 1 FROM pg_namespace n
                    JOIN pg_operator o ON o.oprnamespace = n.oid
                    WHERE n.nspname = 'pg_catalog' AND o.oprname = '~'
                )) AS has_window_support;
        """)
        supports_order_by_in_windows = cursor.fetchone()[0]
        return supports_order_by_in_windows
    except Exception as e:
        # Assume unsupported if query fails
        return False
```

### Example 2: Dynamic Query Rewriting

```python
def compile_query_ast(ast, supports_order_by_in_windows):
    """Rewrites AST based on capabilities."""
    if ast.type == "WindowFunction":
        if supports_order_by_in_windows:
            # Original optimized window function
            return ast
        else:
            # Fallback: Convert window function to correlated subquery
            return rewrite_to_subquery(ast)
```

### Example 3: Fallback Implementation (Subquery for Window Functions)

```sql
-- Original window function (PostgreSQL 15+)
SELECT
    user_id,
    order_id,
    SUM(amount) OVER (PARTITION BY user_id ORDER BY order_date) AS running_total
FROM orders;

-- Fallback for databases without ORDER BY in windows (e.g., MySQL)
SELECT
    o1.user_id,
    o1.order_id,
    o2.running_total
FROM (
    SELECT user_id, order_id, amount
    FROM orders
    ORDER BY user_id, order_date
) o1
JOIN (
    SELECT
        user_id,
        SUM(amount) AS running_total,
        ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY order_date) AS rn
    FROM orders
    GROUP BY user_id
) o2 ON o1.user_id = o2.user_id AND o1.rn = o2.rn;
```

### Example 4: Extension Support Probing

```sql
-- Check if PostgreSQL’s "intarray" extension is installed
SELECT
    CASE
        WHEN EXISTS (
            SELECT 1 FROM pg_extension
            WHERE extname = 'intarray'
        ) THEN true
        ELSE false
    END AS has_intarray_extension;
```

### Example 5: Operator Support Check

```python
def supports_range_operator(conn):
    """Checks if the database supports the '&&' range operator (e.g., PostgreSQL)."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM pg_operator
                WHERE oprname = '&&'
            ) AS supports_range;
        """)
        return cursor.fetchone()[0]
    except Exception:
        return False
```

---

## Implementation Guide: Building Your Own CDR System

If you’re designing a query layer or database abstraction, here’s how to integrate CDR:

### Step 1: Define Capabilities
List the features your application depends on. Examples:
- Window functions with `ORDER BY`
- JSON path queries (`jsonb_path_query`)
- CTEs (WITH clauses)
- Common Table Expressions (CTEs)
- User-Defined Functions (UDFs)

### Step 2: Create Probes for Each Feature
Write lightweight SQL queries to detect support. Example probes:

```sql
-- Does this database support CTEs?
SELECT EXISTS(
    SELECT 1 FROM pg_keywords
    WHERE keyword = 'WITH'
) AS supports_ctes;

-- Does it support the '||' string concatenation operator?
SELECT EXISTS(
    SELECT 1 FROM pg_operator
    WHERE oprname = '||'
) AS supports_concat_operator;
```

### Step 3: Build a Capability Registry
Store detected features in a structured way (e.g., a dictionary):

```python
capabilities = {
    "window_functions_order_by": False,
    "jsonb_path_query": True,
    "ctes": False,
    ...
}
```

### Step 4: Modify the Compiler
Adjust query compilation based on `capabilities`:

```python
def compile_query(ast, capabilities):
    if ast.type == "WindowFunction" and capabilities["window_functions_order_by"]:
        return ast
    elif capabilities["jsonb_path_query"]:
        return rewrite_to_jsonb_path(ast)
    else:
        return fallback_to_subqueries(ast)
```

### Step 5: Integrate Fallbacks
Implement rewriting strategies for unsupported features. Example for window functions:

```python
def fallback_window_function(ast, partition_by, order_by):
    """Rewrites window functions to correlated subqueries."""
    # Simplified: Replace OVER(PARTITION BY ...) with a self-join
    return rewrite_to_subquery(ast)
```

### Step 6: Log and Monitor Fallbacks
Track which fallbacks are used to identify gaps:

```python
fallback_stats = {
    "window_functions": 42,
    "jsonb_path": 10,
    ...
}
```

---

## Common Mistakes to Avoid

1. **Over-Probing**: Don’t query the database for every minor feature. Balance runtime overhead with accuracy.
   - *Bad*: Probe 50 different operators for every query.
   - *Good*: Probe once per session or connection.

2. **Ignoring Performance**: Fallbacks should be *correct*, but not *slow*.
   - Example: A window function fallback might introduce `N^2` complexity.

3. **Assuming All Databases Have Metadata**: Some databases (e.g., SQLite) lack rich `information_schema`. Use heuristics:
   ```python
   def guess_sqlite_version(conn):
       cursor = conn.cursor()
       cursor.execute("SELECT sqlite_version();")
       return float(cursor.fetchone()[0].split('.')[0])
   ```

4. **Not Testing Edge Cases**: Always validate fallbacks with real-world data.
   - Example: A window function fallback might fail if `order_date` is null.

5. **Hardcoding Fallbacks**: Don’t assume MySQL *always* uses subqueries for windows. Test on multiple versions.

---

## Key Takeaways

- **CDR reduces brittleness**: Instead of crashing on unsupported features, your queries adapt.
- **It’s not a silver bullet**: Fallbacks introduce complexity and potential performance hits. Use it where necessary.
- **Probes should be minimal**: Only detect what you *need* to know.
- **Monitor fallback usage**: Identify databases with critical gaps.
- **Prioritize correctness over optimization**: A correct fallback is better than a fast but broken query.

---

## Conclusion

The Capability Detection Runtime pattern is a pragmatic way to handle the "works on my machine" problem in database-driven applications. By probing for features *before* compiling queries, and adapting dynamically, you can build systems that:
- Work across databases without breaking.
- Provide graceful fallbacks when features are missing.
- Avoid costly refactoring when switching databases.

While CDR adds complexity, the tradeoff—avoiding silent failures and reducing database-specific hacks—is often worth it. For teams maintaining query layers that span multiple databases, CDR is a powerful tool in the toolbox.

**Next steps**:
- Integrate CDR into your query compiler or ORM.
- Start with a few critical features (e.g., window functions) before scaling.
- Benchmark fallbacks to ensure they don’t degrade performance excessively.

Happy probing!

---
**Further Reading**:
- [FraiseQL’s Capability Detection Docs](https://docs.fraise.dev/)
- [PostgreSQL’s `information_schema` Reference](https://www.postgresql.org/docs/current/infoschema.html)
- [Database Abstraction Patterns](https://martinfowler.com/eaaCatalog/databaseAbstraction.html)
```