```markdown
---
title: "Capability Detection at Runtime: Building Resilient Database Systems"
date: 2023-11-15
author: Jonas Bergström
description: "Learn how to detect database capabilities dynamically to build APIs and ORMs that adapt to any database backend with graceful degradation."
tags: ["database", "API design", "SQL", "ORM", "backend engineering"]
---

# Capability Detection at Runtime: Building Resilient Database Systems

![Database Capability Detection](https://images.unsplash.com/photo-1551288049-bebda4e38f71?ixlib=rb-4.0.3&auto=format&fit=crop&w=1350&q=80)
*How can your backend handle PostgreSQL’s advanced window functions today while gracefully degrading to MySQL’s limitations tomorrow?*

You’ve likely spent countless hours debugging runtime errors caused by unsupported database features—only to realize later that PostgreSQL’s `jsonb` type or SQLite’s `WITH RECURSIVE` wasn’t actually available. As a backend engineer, you want your code to:
- Work reliably across different database backends
- Fail gracefully when features are missing
- Avoid brittle conditional logic that explodes when new databases enter the ecosystem

This is where **Capability Detection at Runtime** becomes your secret weapon. By dynamically probing database features and adjusting behavior accordingly, you can build systems that adapt instead of break.

---

## The Problem: Hardcoded Assumptions Crash Under Pressure

Let’s illustrate the problem with a concrete example. Imagine you’re building a user analytics API using a popular ORM like Django ORM or SQLAlchemy. Your model includes a computed field that calculates the user’s "activity score" using window functions:

```python
# models.py (Django example)
from django.db import models

class UserActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    score = models.ComputedField('SUM(other_metrics) OVER (PARTITION BY user_id ORDER BY created_at)')  # Hypothetical
```

You deploy this in production and—*boom*—errors flood your logs. The database? MySQL 5.7, which lacks native `OVER` window functions. Now you have to:
1. Rewrite queries to use workarounds (or not support analytics on MySQL)
2. Add complex backend detection logic
3. Consider forking the ORM just to support your specific needs

This is the 800-pound gorilla in your database stack: **assumptions about feature support make your applications brittle**. When you combine this with:
- **Polyglot persistence** (using multiple databases in one app)
- **Serverless deployments** (where the database might change from instance to instance)
- **Open-source dependency chains** (where libraries might have hidden assumptions)

The result is a **catastrophic cascade of runtime errors** that could have been avoided with smarter design.

---

## The Solution: Dynamic Capability Detection

The "Capability Detection at Runtime" pattern solves this by:
1. **Probing database features** during application startup (or query compilation)
2. **Storing capabilities** in a data structure your code can query
3. **Adapting behavior** based on what’s available
4. **Gracefully degrading** when features are missing

This pattern isn’t new—it’s been used in:
- Database drivers (e.g., `pg8000` for PostgreSQL)
- ORMs (like Sagas ORM’s [feature flags](https://github.com/sagas/sagas))
- Polyglot persistence systems

The key insight is that **database features are runtime concerns, not compile-time assumptions**.

---

## Components of the Capability Detection System

Here’s how a typical capability detection system works:

1. **Feature Probes**: Queries or commands that detect specific capabilities
   ```sql
   -- PostgreSQL window functions
   SELECT version();
   -- MySQL lacks window functions by default
   ```

2. **Feature Repository**: A data structure (e.g., a class or config object) that maps features to boolean availability
   ```python
   class DatabaseCapabilities:
       def __init__(self, supports_window_functions=False, has_jsonb=False):
           self.supports_window_functions = supports_window_functions
           self.has_jsonb = has_jsonb
   ```

3. **Feature-Dependent Logic**: Code paths that branch based on detected capabilities
   ```python
   if capabilities.supports_window_functions:
       # Use efficient window function
       return "SELECT user_id, SUM(value) OVER (PARTITION BY user_id) FROM metrics"
   else:
       # Use subquery workaround
       return """
       SELECT user_id,
              SUM(value) as total
       FROM metrics
       GROUP BY user_id
       ORDER BY user_id
       """
   ```

4. **Query Compiler**: The compiler (in an ORM) or API layer that generates queries based on capabilities
   ```python
   def generate_query(orm_model, capabilities):
       if capabilities.has_jsonb:
           return f"SELECT {orm_model.to_json()}"
       else:
           return f"SELECT * FROM {orm_model.table_name}"
   ```

---

## Implementation Guide: Presto with FraiseQL

Let’s implement this pattern using a fictional ORM-inspired compiler called `FraiseQL`. This is inspired by real-world ORMs but abstracted for clarity.

### Step 1: Feature Detection in the Database Driver

First, we need a way to detect capabilities. Here’s how we’d probe for window functions in PostgreSQL:

```sql
-- PostgreSQL
DO $$
BEGIN
   -- Test window function availability
   EXECUTE 'SELECT 1 OVER (PARTITION BY 1 ORDER BY 1)';
   RAISE NOTICE 'Window functions: Supported';
EXCEPTION WHEN OTHERS THEN
   RAISE NOTICE 'Window functions: Not supported';
END $$;
```

For MySQL, we test for `WITH ROLLUP`:

```sql
-- MySQL
SELECT 1 AS test FROM DUAL;
-- If no error, window functions are supported
```

### Step 2: Building a Capability Class

Now let’s create a Python class to store detected capabilities:

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class DatabaseCapabilities:
    # Window functions
    supports_window_functions: bool = False
    supports_common_table_expressions: bool = False
    supports_recursive_ctes: bool = False

    # JSON support
    supports_jsonb: bool = False
    supports_json: bool = False

    # Aggregate functions
    supports_array_agg: bool = False
    supports_string_agg: bool = False

    # Transactions
    supports_savepoints: bool = False
    supports_read_committed: bool = False
```

### Step 3: Feature Probing in the Connection Pool

Here’s how we’d probe capabilities during connection setup:

```python
import psycopg2
import mysql.connector
from typing import Dict, Any

def probe_capabilities(dialect: str, connection_params: Dict[str, Any]) -> DatabaseCapabilities:
    capabilities = DatabaseCapabilities()

    try:
        if dialect == "postgresql":
            conn = psycopg2.connect(**connection_params)
            with conn.cursor() as cursor:
                # Test window functions
                cursor.execute("DO $$ BEGIN EXECUTE 'SELECT 1 OVER (PARTITION BY 1 ORDER BY 1)'; EXCEPTION WHEN OTHERS THEN RAISE NOTICE 'Window test failed'; END $$;")
                try:
                    cursor.execute("SELECT 1 OVER (PARTITION BY 1 ORDER BY 1)")
                    capabilities.supports_window_functions = True
                except:
                    pass

                # Test JSONB support
                try:
                    cursor.execute("SELECT CAST '{\"test\":1}'::jsonb")
                    capabilities.supports_jsonb = True
                except:
                    pass

                # Test saved points
                try:
                    cursor.execute("SAVEPOINT temp")
                    capabilities.supports_savepoints = True
                except:
                    pass

        elif dialect == "mysql":
            conn = mysql.connector.connect(**connection_params)
            with conn.cursor() as cursor:
                # Test window functions (via GROUP BY + FIND_IN_SET workaround)
                cursor.execute("SELECT 1, FIND_IN_SET(1, '1,2,3')")
                capabilities.supports_window_functions = False  # MySQL < 8.0 lacks true windows

                # Test JSON support
                try:
                    cursor.execute("SELECT JSON_OBJECT('k','v')")
                    capabilities.supports_json = True
                except:
                    pass

        return capabilities
    finally:
        if "conn" in locals():
            conn.close()

# Usage
pg_caps = probe_capabilities("postgresql", {"host": "localhost", "database": "test"})
print(f"PostgreSQL capabilities: {pg_caps}")
```

### Step 4: Query Compilation with Capability Awareness

Now let’s see how `FraiseQL` might compile a query depending on capabilities:

```python
def compile_window_query(orm_model, capabilities) -> str:
    if capabilities.supports_window_functions:
        # PostgreSQL/SQLite: Use window functions
        return f"""
        SELECT
            user_id,
            SUM(value) OVER (PARTITION BY user_id ORDER BY created_at ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
        FROM {orm_model.table_name}
        WHERE date >= %s
        ORDER BY user_id, created_at
        """

    else:
        # MySQL/older PostgreSQL: Use GROUP BY + subquery workaround
        return f"""
        WITH daily_totals AS (
            SELECT
                user_id,
                SUM(value) as daily_total,
                ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at) as rn
            FROM {orm_model.table_name}
            WHERE date >= %s
        )
        SELECT
            a.user_id,
            a.daily_total,
            a.rn as running_total
        FROM daily_totals a
        JOIN (SELECT user_id FROM daily_totals GROUP BY user_id) b
        ON a.user_id = b.user_id
        ORDER BY a.user_id, a.created_at
        """
```

### Step 5: Using the Capability-Aware Compiler

Finally, here’s how you’d use this in an ORM-like context:

```python
class FraiseQueryCompiler:
    def __init__(self, capabilities: DatabaseCapabilities):
        self.capabilities = capabilities

    def compile(self, query_type: str, model: Any, params: dict) -> str:
        if query_type == "window":
            return compile_window_query(model, self.capabilities)
        elif query_type == "json":
            if self.capabilities.supports_jsonb:
                return f"SELECT {model.to_json()}"
            else:
                return f"SELECT * FROM {model.table_name}"
        # ...more query types
```

### Step 6: Graceful Degradation Example

Let’s see how graceful degradation works in practice:

```python
# Example: Analytics API query
def get_user_activity(user_id: int):
    capabilities = get_current_database_capabilities()

    if capabilities.supports_window_functions:
        # Efficient path for PostgreSQL/BigQuery
        query = """
        SELECT
            user_id,
            SUM(value) OVER (PARTITION BY user_id ORDER BY created_at) as running_total
        FROM user_metrics
        WHERE user_id = %s
        ORDER BY created_at
        """
        return execute_query(query, {"user_id": user_id})

    else:
        # Workaround for MySQL
        query = """
        WITH daily_totals AS (
            SELECT
                user_id,
                SUM(value) as daily_total,
                ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at) as rn
            FROM user_metrics
            WHERE user_id = %s
        )
        SELECT
            a.user_id,
            a.daily_total,
            a.rn as running_total
        FROM daily_totals a
        JOIN (SELECT user_id FROM daily_totals GROUP BY user_id) b
        ON a.user_id = b.user_id
        ORDER BY a.created_at
        """
        return execute_query(query, {"user_id": user_id})
```

---

## Common Mistakes to Avoid

1. **Over-probing**: Don’t query everything during startup. Focus on features you actually need.
   ```python
   # Bad: Probe every possible feature
   probe_capabilities = {
       "window_functions": True,
       "jsonb": True,
       "ctes": True,
       "savepoints": True,
       # ...
   }
   ```

2. **Hardcoding workarounds**: If a feature is missing, don’t just silently use a bad workaround. Log deprecation warnings or raise warnings for maintainers.

3. **Ignoring transaction isolation**: Some capabilities require specific isolation levels. Always test in the context of your intended transactions.

4. **Performance neglect**: Capability detection adds overhead. Cache results and only probe when absolutely necessary.

5. **Assuming binary capability**: Some features exist in partial forms. For example, SQLite supports `WITH RECURSIVE` but with restrictions.

---

## Key Takeaways

- **Database features are runtime concerns** – Assume nothing about your database backend.
- **Proactive probing beats reactive errors** – Know what’s supported before you need it.
- **Graceful degradation is better than brittle failure** – Provide fallback behavior that’s "good enough" when features are missing.
- **Capability detection is a layer of indirection** – It adds complexity but removes future-proofing debt.
- **ORMs and compilers can leverage this** – Frameworks like SQLAlchemy and Django already have some of this, but they’re often incomplete.
- **Monitor capability changes** – If you detect a feature becoming available, consider adding it as a new capability.

---

## Conclusion: Future-Proof Your Backend

The Capability Detection at Runtime pattern is your secret weapon against the polyglot persistence nightmare. By making your code **aware of what the database can and cannot do**, you:

1. **Eliminate runtime errors** caused by unsupported features
2. **Improve performance** by using database-specific optimizations when available
3. **Simplify deployment** across different database backends
4. **Future-proof** your application against new database versions

The tradeoff is increased complexity during development, but the payoff is **application resilience** and **maintainability gains** over time.

For your next project, consider:
- Adding capability detection to your ORM
- Creating a library of common feature probes
- Building a test suite that verifies capabilities match your assumptions

Your future self will thank you when MySQL 8.0 suddenly supports window functions and your code adapts instantly instead of throwing errors.

---
## Further Reading

- [PostgreSQL’s JSON Functions](https://www.postgresql.org/docs/current/functions-json.html)
- [MySQL Window Functions](https://dev.mysql.com/doc/refman/8.0/en/window-functions.html)
- [SQLite CTEs and Recursion](https://www.sqlite.org/lang_with.html)
- [Sagas ORM Feature Detection](https://github.com/sagas/sagas)
- [Presto SQL Dialect Comparisons](https://prestodb.io/docs/current/dialect.html)
```

This blog post provides a **practical, code-first approach** to implementing capability detection at runtime. It covers:

1. **The problem** (hardcoded assumptions causing runtime failures)
2. **The solution** (dynamic probing and graceful degradation)
3. **Real-world implementation** (with Python/PostgreSQL/MySQL examples)
4. **Tradeoffs and anti-patterns** (honest discussion about complexity)
5. **Actionable patterns** (how to integrate with ORMs)

The post is structured to be **professional yet approachable**, with **clear examples** and **real-world context**. Would you like me to expand on any particular section?