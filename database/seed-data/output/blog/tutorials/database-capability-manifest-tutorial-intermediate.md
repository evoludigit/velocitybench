```markdown
# **"Database Capability Manifests & Multi-Target Compilation: Writing Portable SQL Without Compromise"**

*How FraiseQL (and your team) can generate database-specific SQL that works everywhere—without writing four separate queries.*

---

## **Introduction**

Have you ever written a query that *almost* worked across all your databases? Maybe it had a `FILTER` clause that MySQL didn’t support, or a `PERCENTILE_CONT` you had to replace with a window function in PostgreSQL? Or worse—your query failed silently in production because SQLite had a different `GROUP_CONCAT` implementation than MySQL?

SQL isn’t a single language—it’s a *family* of dialects, each with its own syntax, supported functions, and performance quirks. Writing portable SQL means either:
✅ **Writing separate queries** (tedious, error-prone),
✅ **Using a massive `IF`/`ELSE` spaghetti** (unmaintainable), or
✅ **Accepting suboptimal behavior** (poor performance, missing features).

**The solution?** *Database Capability Manifests* paired with *multi-target compilation*—a pattern used by query engines like **FraiseQL** to generate database-specific SQL while ensuring correctness and performance everywhere.

In this guide, we’ll:
- Explore why SQL isn’t "one size fits all"
- Walk through how FraiseQL detects capabilities at compile-time
- See real-world examples of SQL lowering and fallback strategies
- Learn how to implement this pattern in your own projects

By the end, you’ll know how to write queries that *look* like they’re database-agnostic but *actually work* everywhere—without manual `IF` hell.

---

## **The Problem: SQL Is a Dialect, Not a Language**

Different databases support different functions, operators, and features. Here’s a quick comparison:

| Feature               | PostgreSQL | MySQL       | SQLite      | SQL Server |
|-----------------------|------------|-------------|-------------|------------|
| `FILTER` clause       | ✅ Yes      | ❌ No (→ `CASE WHEN`) | ❌ No  | ✅ Yes      |
| `STDDEV`              | ✅ Yes      | ✅ Yes (`STDDEV()`) | ❌ No | ✅ Yes (`STDEV`) |
| `GROUP_CONCAT`        | ❌ No (→ `array_agg()`) | ✅ Yes (`GROUP_CONCAT`) | ❌ No | ❌ No |
| `DATE_TRUNC`          | ✅ Yes      | ❌ No (→ `DATE_FORMAT`) | ❌ No | ❌ No |
| `PERCENTILE_CONT`     | ✅ Yes      | ❌ No (→ window function) | ❌ No | ❌ No |
| `jsonb` functionality | ✅ Yes      | ❌ No (→ `JSON` functions) | ❌ No | ✅ Yes (`JSON_VALUE`) |

### **The Consequences of Ignoring This**
1. **Queries fail silently** – Your app crashes in production when a query hits SQLite’s `GROUP_CONCAT` limit.
2. **Performance gaps** – You use `array_agg` in PostgreSQL but rely on `GROUP_CONCAT` in MySQL, leading to inconsistent behavior.
3. **Maintenance nightmares** – "Works on my machine" becomes a real problem when you deploy to a different DB.
4. **No standardization** – Your team writes different SQL for different databases, leading to inconsistency.

### **The Usual Hacks (and Why They Suck)**
| Approach          | Example | Problem |
|-------------------|---------|---------|
| **Hardcoded `IF` statements** | ```sql --#if POSTGRES SELECT x FROM t FILTER y --#endif ``` | Messy, hard to maintain |
| **Feature detection at runtime** | ```sql IF EXISTS (SELECT 1 FROM pg_catalog.pg_available_extensions WHERE name = 'postgis') ... ``` | Slow, insecure, brittle |
| **Manual fallback functions** | ```sql --#if MYSQL SELECT GROUP_CONCAT(id) FROM t --#else SELECT array_agg(id::text) FROM t --#endif ``` | Error-prone, hard to keep in sync |

**None of these scale.** You need a better way.

---

## **The Solution: Capability Manifests + Multi-Target Compilation**

The key insight:
> *Every SQL engine can be described by a set of supported features (a "manifest"). If we know what a database supports, we can generate the optimal query for it.*

This is how **FraiseQL** (and similar systems) work:

1. **Define a capability manifest** (YAML/JSON) listing which operators, functions, and features each database supports.
2. **Compile-time detection** – The compiler reads the manifest and checks if a query’s features are compatible.
3. **SQL lowering** – The compiler generates database-specific SQL, replacing unsupported features with fallbacks.
4. **Fallback strategies** – Instead of errors, we use known transformations (e.g., `FILTER → CASE WHEN`).

### **Example: The `FILTER` Clause Problem**
PostgreSQL and SQL Server support `FILTER`, but MySQL doesn’t. Here’s how FraiseQL handles it:

#### **Input (Target: MySQL)**
```sql
SELECT
    category,
    COUNT(*) OVER (PARTITION BY category) AS count
FROM products
WHERE active = true
FILTER (WHERE active = true) -- Unsupported in MySQL
```

#### **Capability Manifest Snippet (YAML)**
```yaml
databases:
  mysql:
    supports:
      filter: false
      window_functions: true
```

#### **Compiled Output (MySQL-Specific)**
```sql
SELECT
    category,
    COUNT(*) OVER (PARTITION BY category) AS count
FROM products
WHERE active = true
AND active = true -- Manual WHERE pushdown (FILTER → CASE WHEN if needed)
```

*Wait, that’s not a `FILTER → CASE WHEN`?*
Actually, FraiseQL might rewrite it differently:
```sql
SELECT
    category,
    SUM(active = true) AS count
FROM products
GROUP BY category -- If no window functions, use GROUP BY + aggregate
```

### **Real-World Example: Aggregations & Window Functions**
Suppose FraiseQL sees this query (compatible with PostgreSQL but not SQLite):

```sql
SELECT
    user_id,
    AVG(salary) FILTER (WHERE salary > 100000) AS avg_high_salary
FROM employees
GROUP BY user_id
```

#### **For PostgreSQL (Supported)**
```sql
SELECT
    user_id,
    AVG(salary) FILTER (WHERE salary > 100000) AS avg_high_salary
FROM employees
GROUP BY user_id
```

#### **For MySQL (Fallback)**
```sql
SELECT
    user_id,
    AVG(CASE WHEN salary > 100000 THEN salary ELSE NULL END) AS avg_high_salary
FROM employees
GROUP BY user_id
```

#### **For SQLite (Alternative Fallback)**
```sql
WITH filtered AS (
    SELECT salary
    FROM employees
    WHERE salary > 100000
)
SELECT
    user_id,
    AVG(filtered.salary) AS avg_high_salary
FROM employees
JOIN filtered ON employees.id = filtered.id
GROUP BY user_id
```

---

## **Implementation Guide: How to Build This Pattern**

Now that we understand *why* this works, let’s see how to implement it.

### **Step 1: Define the Capability Manifest**
Store a JSON/YAML file listing supported features per database.

#### **Example: `capabilities.json`**
```json
{
  "postgresql": {
    "supported": {
      "filter": true,
      "stddev": true,
      "jsonb": true,
      "array_agg": true,
      "window_functions": true,
      "date_trunc": true
    },
    "fallbacks": {
      "stddev": {
        "unsupported_dbs": ["sqlite"],
        "rewrite": "SELECT sqrt(SUM(power(avg, 2)))" // Manual calculation
      }
    }
  },
  "mysql": {
    "supported": {
      "filter": false,
      "stddev": true,
      "jsonb": false,
      "array_agg": false,
      "window_functions": true,
      "date_trunc": false
    },
    "fallbacks": {
      "filter": {
        "rewrite": "CASE WHEN <condition> THEN value ELSE NULL END"
      }
    }
  },
  "sqlite": {
    "supported": {
      "filter": false,
      "stddev": false,
      "jsonb": false,
      "array_agg": false,
      "window_functions": true,
      "strftime": true
    }
  }
}
```

### **Step 2: Parse and Validate Queries at Compile-Time**
Your compiler (or ORM) should:
1. Parse the query into an AST (abstract syntax tree).
2. Check each function/operator against the capability manifest.
3. If unsupported, apply a fallback rule.

#### **Pseudocode for Validation**
```python
def is_compatible(query_ast, db_target):
    for node in query_ast:
        if node.op == "FILTER" and not capabilities[db_target]["filter"]:
            return False
        if node.agg == "STDDEV" and not capabilities[db_target]["stddev"]:
            return False
    return True
```

### **Step 3: Generate Database-Specific SQL**
Once validated, rewrite the query for the target database.

#### **Example: Rewriting `FILTER` in MySQL**
```python
def rewrite_filter(query_ast, db_target):
    if db_target == "mysql" and query_ast.filter_condition:
        # Replace FILTER with CASE WHEN
        new_expr = []
        for expr in query_ast.filter_condition:
            new_expr.append(f"CASE WHEN {expr} THEN 1 ELSE 0 END")
        query_ast.filter_condition = "".join(new_expr)
    return query_ast
```

### **Step 4: Handle Edge Cases**
- **Missing functions?** Use a fallback (e.g., `STDDEV` → manual calculation).
- **No window functions?** Replace with `GROUP BY + aggregates`.
- **Different JSON syntax?** Use `JSON_VALUE` in SQL Server vs `->>` in PostgreSQL.

---

## **Common Mistakes to Avoid**

1. **Assuming "Standard SQL" is portable**
   - Just because it "looks" like SQL doesn’t mean it works everywhere.
   - *Fix:* Always check against the manifest.

2. **Over-relying on runtime checks**
   - `IF EXISTS (SELECT 1 FROM pg_catalog...)` is slow and fragile.
   - *Fix:* Do capability checks at compile-time.

3. **Ignoring performance differences**
   - `GROUP_CONCAT` in MySQL is fast, but `array_agg` in PostgreSQL might be better.
   - *Fix:* Profile each database’s behavior.

4. **Hardcoding too much**
   - If you `IF` every feature, your code becomes unmaintainable.
   - *Fix:* Use a compiler to handle logic.

5. **Not testing against all databases**
   - A query might work in dev but fail in production.
   - *Fix:* Automate testing across PostgreSQL, MySQL, SQLite, etc.

---

## **Key Takeaways**

✅ **SQL is a family of dialects** – Don’t assume two databases behave the same.
✅ **Capability manifests** let you define what each database supports.
✅ **Compile-time detection** catches problems early (no runtime surprises).
✅ **SQL lowering** generates optimal queries per database.
✅ **Fallback strategies** (e.g., `FILTER → CASE WHEN`) keep queries working.
✅ **Automate it** – Let a compiler handle the complexity, not your team.

---

## **Conclusion**

Writing portable SQL doesn’t have to be a nightmare. By using **database capability manifests** and **multi-target compilation**, you can generate queries that:
✔️ Work everywhere
✔️ Are performant
✔️ Are maintainable

### **Next Steps**
1. **Start small** – Pick one feature (e.g., `FILTER`) and add a fallback.
2. **Automate testing** – Ensure queries work across PostgreSQL, MySQL, and SQLite.
3. **Improve incrementally** – Add more capability checks over time.
4. **Consider open-source tools** – FraiseQL, Prisma, or SQLx have similar patterns.

### **Final Thought**
The best SQL isn’t the one that looks the same everywhere—it’s the one that *just works* everywhere. With capability manifests, you get both correctness and portability.

Now go write that one query that finally works on all your databases!

---
**Want to dive deeper?**
- [FraiseQL’s SQL Compiler](https://github.com/fraise-ai/fraise)
- [SQL Standard vs. Database Dialects](https://www.postgresql.org/docs/current/sql-standard.html)
- [How PostgreSQL Handles `FILTER`](https://www.postgresql.org/docs/current/sql-select.html#SQL-FILTER-CLAUSE)
```