# **[Pattern] Capability Detection Runtime Reference Guide**

---

## **Overview**
The **Capability Detection Runtime (CDR)** pattern enables dynamic database feature detection at compile-time, ensuring that FraiseQL adapts schema compilation and query execution to the capabilities of target databases. By querying system metadata, version numbers, and extension support, CDR determines which SQL dialects and operators are available, mitigating schema incompatibilities and enabling graceful fallbacks where needed.

This pattern is particularly valuable in multi-database environments where direct schema replication is impractical (e.g., PostgreSQL vs. SQLite). CDR balances performance (by minimizing redundant probing) with flexibility (by supporting feature-specific optimizations).

---

## **Key Concepts**

| **Term**                     | **Description**                                                                                                                                                                                                                                                                 |
|------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Feature Probe**            | A low-level query (e.g., `SHOW VERSION`, `SELECT pg_available_extensions()`) to check for supported SQL dialects, extensions, or operators.                                                                                                               |
| **Capability Profile**       | A runtime-assigned tag (e.g., `postgres-v15`, `mysql-8-0`) capturing detected features. Used to route compiled queries to matching databases.                                                                                             |
| **Graceful Degradation**     | Automatic rewriting of queries to use compatible alternatives (e.g., `LIMIT` → `FETCH FIRST` in SQLite) when advanced operators are unsupported.                                                                                               |
| **Probe Cache**              | Persistent storage (local or shared) to avoid redundant capability checks on repeated connections to the same database.                                                                                                                   |
| **Schema Adapter**           | Compiler pass that alters schema definitions based on detected capabilities (e.g., dropping `JSONB` functions for SQLite).                                                                                                               |

---

## **Schema Reference**
FraiseQL’s **Capability Detection Runtime** operates across three layered schemas:

| **Schema Layer**       | **Description**                                                                                     | **Key Tables**                                                                 |
|-------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Core**                | Universal abstractions (e.g., tables, columns) incompatible with any database.                    | `tables`, `columns`, `constraints`                                               |
| **Dialect-Specific**    | Database-specific extensions (e.g., PostgreSQL’s `jsonb`, MySQL’s `JSON` functions).                | `postgres_extensions`, `mysql_operators`                                         |
| **Capability-Dependent**| Conditionally compiled definitions based on runtime probes.                                           | `dynamic_operators`, `fallback_procedures`                                      |

**Example:**
```sql
-- Core schema (universal)
CREATE TABLE users (
    id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

-- Conditional schema (PostgreSQL only)
CREATE EXTENSION IF EXISTS "pg_trgm" ON SCHEMA postgres_dialect;
```

---

## **Query Examples**

### **1. Feature Probing**
Probes assess supported features via metadata queries:

```sql
-- PostgreSQL version check
SELECT version() AS postgres_version;
-- Output: "PostgreSQL 15.3 on x86_64-pc-linux-gnu"

-- MySQL JSON support
SELECT NULL AS mysql_json_support WHERE JSON_SUPPORT IS NOT NULL;
```

### **2. Capability-Driven Query Rewrite**
If a database lacks `LIMIT`, CDR rewrites:
```sql
-- Input (unsupported in SQLite)
SELECT * FROM users LIMIT 10;

-- Rewritten for SQLite (SQLite uses `FETCH FIRST`)
SELECT * FROM users FETCH FIRST 10 ROWS ONLY;
```

### **3. Schema Compiler Output**
Conditional schema generation (pseudo-code):
```sql
-- Compiler output for PostgreSQL
CREATE TABLE users (
    id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    bio TEXT CHECK (
        CASE WHEN pg_trgm_is_textsearchable(name) THEN true ELSE false END
    )
);

-- Compiler output for SQLite (fallback)
CREATE TABLE users (
    id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    bio TEXT -- No text search support
);
```

### **4. Dynamic Operator Resolution**
```sql
-- FraiseQL query (abstract syntax)
SELECT GREATEST(id, 100) FROM users;

-- Resolved to PostgreSQL:
SELECT GREATEST(id, 100) FROM users;

-- Resolved to MySQL (uses LEAST and COALESCE):
SELECT COALESCE(LEAST(NULLIF(100, GREATEST(id, 100)), id), id) FROM users;
```

---

## **Implementation Details**
### **1. Probe Handlers**
Customizable probe functions (example for JSON support):
```sql
-- MySQL JSON probe
CREATE FUNCTION has_mysql_json() RETURNS BOOLEAN LANGUAGE SQL
AS $$ SELECT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_SCHEMA = 'mysql' AND TABLE_NAME = 'func'
) $$;
```

### **2. Cache Management**
Probe results are cached with TTL (e.g., 1 hour):
```json
{
  "database": "postgres://host:5432",
  "capability_profile": "postgres-v15-wal",
  "ttl": 3600,
  "probes": {
    "jsonb_support": true,
    "pg_trgm": true
  }
}
```

### **3. Schema Adapter Logic**
Compiler passes (pseudo-implementation):
```python
def adaptor(schema, profile):
    if "sqlite" in profile:
        drop_extension(schema, "pg_trgm")
        replace_operator(schema, "LIMIT", "FETCH FIRST")
    return schema
```

---

## **Performance Considerations**
| **Aspect**               | **Optimization**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------|
| **Probe Overhead**        | Cache results per connection; batch probes where possible.                                           |
| **Query Rewriting**       | Precompile fallback patterns to minimize runtime changes.                                            |
| **Schema Compilation**    | Use incremental compilation: only regenerate affected schemas when capabilities change.              |

---

## **Related Patterns**

| **Pattern Name**               | **Relation to CDR**                                                                                     |
|---------------------------------|-------------------------------------------------------------------------------------------------------|
| **Multi-Database Schema**       | CDR enables this by dynamically adapting schemas per database.                                         |
| **Feature Flags**               | Similiar to CDR’s capability profiles but typically static; CDR is dynamic.                           |
| **Query Translation**           | CDR often feeds into this pattern by generating database-specific SQL.                                |
| **Adaptive Query Execution**    | CDR informs runtime optimizers about operator support (e.g., avoiding `ANALYZE` in SQLite).          |

---
## **Limitations & Workarounds**
| **Challenge**                     | **Workaround**                                                                                     |
|-----------------------------------|-----------------------------------------------------------------------------------------------------|
| **Slow probes**                   | Limit probes to critical features; cache aggressively.                                              |
| **Incomplete metadata**           | Combine system tables with runtime checks (e.g., `pg_isextensioninstalled()`).                    |
| **Unsupported dialects**          | Use a universal subset of SQL or fall back to generic queries.                                     |

---
## **Further Reading**
- *PostgreSQL Documentation*: [`pg_available_extensions()`](https://www.postgresql.org/docs/current/functions-info-schema.html)
- *SQLite Extensions*: [SQLite 3 Language Extensions](https://www.sqlite.org/lang_corefunc.html)
- *FraiseQL Compiler Design*: [Internal Docs → Adaptive Schema Compilation](https://fraise-lang.org/docs/compilers/adaptive)

---
**Last Updated:** [VERSION] | **Version:** [1.3.0]