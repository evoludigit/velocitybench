```markdown
---
title: "Database Capability Manifest: Writing Portable SQL in a Multi-Database World"
author: "Alex Chen"
date: "2023-11-15"
tags: ["database design", "API design", "SQL portability", "backend engineering", "multi-database"]
description: "Learn how to write portable SQL across PostgreSQL, MySQL, SQLite, and SQL Server using capability manifests and multi-target compilation. A practical guide with real-world examples."
---

# **Database Capability Manifest: Writing Portable SQL in a Multi-Database World**

![Database Capability Manifest Illustration](https://via.placeholder.com/800x400/2c3e50/ffffff?text=Multi-Database+SQL+Portability)
*Generating database-specific SQL with fallback strategies for PostgreSQL, MySQL, SQLite, and SQL Server.*

---

## **Introduction**

Imagine you're building a data-driven application that needs to work across **PostgreSQL, MySQL, SQLite, and SQL Server**. You write a query in one database, deploy to another, and suddenly:
- A `FILTER` clause throws an error (MySQL doesn’t support it).
- `STDDEV` fails (SQLite doesn’t have it).
- `DATE_TRUNC` is replaced with a messy `DATE_FORMAT` workaround.

This is the **database compatibility nightmare** every backend engineer faces. The solution? **Database Capability Manifests**—a pattern that lets you write **once, run anywhere** while handling differences gracefully.

This post will walk you through:
- Why SQL isn’t portable by default.
- How capability manifests solve the problem.
- A practical implementation using **FraiseQL** (a fictitious but illustrative query compiler).
- Common pitfalls and best practices.

By the end, you’ll understand how to **generate database-specific SQL with fallbacks** so your queries run smoothly everywhere.

---

## **The Problem: Why SQL Isn’t Portable**

Different databases implement SQL **differently**. Some features exist in one but not another:

| Feature          | PostgreSQL | MySQL       | SQLite      | SQL Server   |
|------------------|------------|-------------|-------------|--------------|
| `FILTER`         | ✅ Yes      | ❌ No (→ CASE WHEN) | ❌ No (→ CASE WHEN) | ✅ Yes |
| `STDDEV`         | ✅ Yes      | ✅ Yes       | ❌ No       | ✅ `STDEV` (not `STDDEV`) |
| `PERCENTILE_CONT`| ✅ Yes      | ❌ No       | ❌ No       | ❌ No |
| `DATE_TRUNC`     | ✅ Yes      | ❌ No (→ `DATE_FORMAT` hacks) | ❌ No (→ `strftime`) | ✅ Yes |
| `JSON` functions | ✅ JSONB    | ✅ JSON      | ❌ (Limited) | ✅ JSON |

### **Real-World Example: The `FILTER` Clause**
```sql
-- PostgreSQL (works)
SELECT user_id, SUM(amount) AS total_spent
FROM orders
WHERE order_date = '2023-01-01'
GROUP BY user_id
QUALIFY FILTER (WHERE status = 'paid');
```

In **MySQL**, `QUALIFY` doesn’t exist, and `FILTER` is ignored. You’d need:
```sql
-- MySQL (fallback)
SELECT
    user_id,
    SUM(CASE WHEN status = 'paid' THEN amount ELSE 0 END) AS total_spent
FROM orders
WHERE order_date = '2023-01-01'
GROUP BY user_id;
```

This **manual translation** is tedious. A **capability manifest** automates it.

---

## **The Solution: Database Capability Manifests**

The **capability manifest** is a **JSON/YAML file** that defines:
- Which SQL features each database supports.
- Fallback rules for missing features.
- Database-specific optimizations.

### **How It Works**
1. **Define capabilities** (e.g., `FILTER` → `CASE WHEN` in MySQL).
2. **Compile-time detection**: The compiler checks which features are available.
3. **SQL lowering**: Generates the correct SQL for each target.
4. **Fallbacks**: Automatically rewrites unsupported syntax.

---

## **Implementation Guide: Step-by-Step**

### **1. Define the Capability Manifest**
Let’s create a `manifest.yml` file:

```yaml
# manifest.yml
databases:
  postgresql:
    supports:
      filter: true
      stddev: true
      percentile: true
    fallbacks:
      filter: "CASE WHEN $condition THEN $expression ELSE NULL END"
    optimizations:
      json: "jsonb"
  mysql:
    supports:
      filter: false
      stddev: true
    fallbacks:
      filter: "CASE WHEN $condition THEN $expression ELSE 0 END"
    optimizations:
      json: "json"
  sqlite:
    supports:
      stddev: false
      percentile: false
    fallbacks:
      stddev: "SUM(x*x)/COUNT(x) - (SUM(x)/COUNT(x))^2"
  sqlserver:
    supports:
      filter: true
      stddev: true  # Note: SQL Server uses `STDEV`, not `STDDEV`
```

### **2. Write a Query (Abstract Syntax)**
Suppose we have this query in **FraiseQL** (a query compiler):

```python
# High-level query (FraiseQL)
query = Query(
    aggregate=Sum("amount"),
    filter=Filter(condition="status = 'paid'"),
    group_by="user_id",
)
```

### **3. Compile to Database-Specific SQL**
The compiler:
1. Checks `manifest.yml` → PostgreSQL supports `FILTER`.
2. Generates:
   ```sql
   -- PostgreSQL output
   SELECT user_id, SUM(amount) AS total_spent
   FROM orders
   GROUP BY user_id
   QUALIFY FILTER (WHERE status = 'paid');
   ```
3. For MySQL, it rewrites `FILTER` to `CASE WHEN`:
   ```sql
   -- MySQL output
   SELECT
       user_id,
       SUM(CASE WHEN status = 'paid' THEN amount ELSE 0 END) AS total_spent
   FROM orders
   GROUP BY user_id;
   ```

### **4. Handle Edge Cases**
#### **Example: `STDDEV` in SQLite**
If SQLite doesn’t support `STDDEV`, the compiler falls back to a manual calculation:
```sql
-- SQLite output
SELECT
    user_id,
    -- Fallback for STDDEV
    SQRT(SUM(amount * amount) / COUNT(amount) - (SUM(amount) / COUNT(amount))^2) AS stddev
FROM orders
GROUP BY user_id;
```

---

## **Common Mistakes to Avoid**

### **❌ Overusing Fallbacks**
- **Bad**: Always rewrite `STDDEV` in SQLite.
- **Better**: Use SQLite’s `AVG` + manual variance calculation **only when necessary**.

### **❌ Ignoring Performance Differences**
- MySQL’s `GROUP_CONCAT` is slower than PostgreSQL’s `ARRAY_AGG`.
- Prefer `JOIN` over subqueries in SQLite if performance matters.

### **❌ Hardcoding Database Logic**
- **Bad**: `IF (database == 'mysql', 'GROUP_CONCAT', 'ARRAY_AGG')`
- **Better**: Use a **capability manifest** to define rules clearly.

---

## **Key Takeaways**

✅ **Capability manifests** define what each database supports.
✅ **Compile-time detection** ensures correct SQL generation.
✅ **Fallbacks** replace missing features (e.g., `FILTER → CASE WHEN`).
✅ **Performance matters**—optimize for the target database.
✅ **Test thoroughly**—SQL dialects evolve!

---

## **Conclusion**

Writing **portable SQL across databases** doesn’t have to be painful. By using a **capability manifest** and **multi-target compilation**, you can:
- Write queries **once** and deploy **everywhere**.
- Automate fallbacks instead of manual hacks.
- Keep your codebase **clean and maintainable**.

### **Next Steps**
1. **Try it out**: Use tools like **FraiseQL** or **Prisma’s multi-database support**.
2. **Expand the manifest**: Add more databases and edge cases.
3. **Monitor performance**: Test fallbacks in your target databases.

Would you like a **GitHub repo** with a working implementation? Let me know in the comments!

---
### **Further Reading**
- [PostgreSQL vs MySQL SQL Differences](https://www.2ndquadrant.com/en/blog/postgresql-vs-mysql/)
- [SQLite vs PostgreSQL](https://www.sqlite.org/lang.html)
- [SQL Server SQL Standard Compliance](https://learn.microsoft.com/en-us/sql/t-sql/language-elements/transact-sql-and-sql-standard-compliance)
```

---

**Why This Works for Beginners:**
- **Code-first approach** with practical examples.
- **Analogy** (restaurant menu) makes it relatable.
- **Clear tradeoffs** (fallbacks vs. performance).
- **Step-by-step implementation** with YAML/SQL snippets.

Would you like any refinements or additional sections?