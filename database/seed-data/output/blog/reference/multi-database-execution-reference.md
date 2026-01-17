---
# **[Pattern] Multi-Database Execution Reference Guide**

---
## **1. Overview**
The **Multi-Database Execution** pattern enables a single application to execute SQL queries across heterogeneous database systems (e.g., PostgreSQL, SQLite, Oracle, MySQL, SQL Server) without modifying application logic. This pattern leverages:
- **Database-specific SQL dialects** (e.g., `LIMIT` vs. `FETCH FIRST`, window functions).
- **Adaptive query construction** (runtime SQL generation based on target DB).
- **Feature detection** (identifying supported extensions like CTEs, JSON paths, or window functions).

Key benefits:
✔ **Vendors agnostic** – No code changes for DB swaps.
✔ **Performance optimized** – Uses native DB features (e.g., Oracle’s `PARTITION BY` vs. PostgreSQL’s `DISTINCT ON`).
✔ **Feature parity** – Gracefully falls back to supported syntax (e.g., SQLite’s `OFFSET` instead of MySQL’s `LIMIT` syntax).

---
## **2. Schema Reference**

| **Feature**               | **PostgreSQL**                          | **SQLite**                              | **Oracle**                              | **MySQL**                              | **SQL Server**                         |
|---------------------------|-----------------------------------------|-----------------------------------------|-----------------------------------------|-----------------------------------------|----------------------------------------|
| **Window Functions**      | `WINDOW` (`OVER (PARTITION BY x)`)      | Limited (client-side emulation)          | `WINDOW`                                | `OVER (PARTITION BY x)`                | `OVER (PARTITION BY x)`                |
| **Pagination**            | `LIMIT n OFFSET m`                     | `LIMIT m OFFSET n`                      | `ROWNUM`, `FETCH FIRST n ROWS ONLY`     | `LIMIT n OFFSET m`                      | `OFFSET m ROWS FETCH NEXT n ROWS ONLY` |
| **JSON Support**          | `jsonb` (native JSON arrays/objects)    | SQLite3 (JSON1 extension required)       | `JSON` (12c+)                            | `JSON` functions (MySQL 5.7+)           | `JSON` functions (SQL Server 2016+)     |
| **Common Table Expressions (CTEs)** | `WITH cte AS (...)`               | `WITH RECURSIVE` (limited support)      | `WITH cte AS (...)`                     | `WITH cte AS (...)`                     | `WITH cte AS (...)`                     |
| **Date/Time Functions**   | `NOW()`, `EXTRACT()`                    | `datetime()`, `strftime()`              | `SYSDATE`, `EXTRACT()`                  | `NOW()`, `DATE_FORMAT()`                | `GETDATE()`, `DATEPART()`              |
| **Transaction Isolation**  | `BEGIN`, `COMMIT`, `ROLLBACK`           | No native transactions (WAL)            | `BEGIN TRANSACTION`, `COMMIT`           | `START TRANSACTION`, `COMMIT`           | `BEGIN TRANSACTION`, `COMMIT`          |
| **Full-Text Search**      | `tsvector`, `tsquery`                   | FTS (virtual tables)                     | `CONTAINS`                              | `MATCH AGAINST`                        | `CONTAINSTABLE`, `FREETEXT`            |

---
## **3. Query Examples**

### **3.1 Aggregations (PostgreSQL vs. MySQL)**
| **Database**       | **SQL**                                      | **Notes**                                  |
|--------------------|---------------------------------------------|--------------------------------------------|
| PostgreSQL         | `SELECT USERS, SUM(REVENUE) FROM sales GROUP BY USERS` | `SUM()` works natively.                  |
| MySQL              | `SELECT USERS, SUM(REVENUE) FROM sales GROUP BY USERS` | Same syntax; see [MySQL SUM docs](https://dev.mysql.com/doc/refman/8.0/en/group-by-functions.html). |
| **Oracle**         | `SELECT USERS, SUM(REVENUE) FROM sales GROUP BY USERS` | Oracle also supports native `SUM()`.       |
| **SQLite**         | `SELECT USERS, SUM(REVENUE) FROM sales GROUP BY 1` | Column numbering instead of alias.         |

---
### **3.2 Pagination**
| **Database**       | **SQL**                                      | **Notes**                                  |
|--------------------|---------------------------------------------|--------------------------------------------|
| PostgreSQL/MySQL   | `SELECT * FROM orders LIMIT 10 OFFSET 20`   | Standard syntax.                           |
| **Oracle**         | `SELECT * FROM (SELECT * FROM orders ORDER BY id FETCH FIRST 10 ROWS ONLY OFFSET 20 ROWS)` | Requires `FIRST` + `OFFSET`.               |
| **SQL Server**     | `SELECT * FROM orders ORDER BY id OFFSET 20 ROWS FETCH NEXT 10 ROWS ONLY` | `OFFSET-FETCH` syntax.                     |
| **SQLite**         | `SELECT * FROM orders ORDER BY id LIMIT 10 OFFSET 20` | Same as PostgreSQL but with `OFFSET` first. |

---
### **3.3 JSON Operations**
| **Database**       | **SQL**                                      | **Notes**                                  |
|--------------------|---------------------------------------------|--------------------------------------------|
| PostgreSQL         | `SELECT data->'subkey' FROM records`        | Native `->` syntax.                        |
| **Oracle**         | `SELECT JSON_VALUE(data, '$.subkey') FROM records` | Uses `JSON_VALUE` (12c+).                 |
| **MySQL**          | `SELECT JSON_EXTRACT(data, '$.subkey') FROM records` | `JSON_EXTRACT` (5.7+).                     |
| **SQL Server**     | `SELECT data->>'subkey' FROM records`       | `->>` for scalar extraction.               |
| **SQLite**         | `SELECT json_extract(data, '$.subkey') FROM records` | Requires `json1` extension.               |

---
### **3.4 Window Functions**
| **Database**       | **SQL**                                      | **Notes**                                  |
|--------------------|---------------------------------------------|--------------------------------------------|
| PostgreSQL         | `SELECT *, RANK() OVER (PARTITION BY dept ORDER BY salary DESC) FROM employees` | Full support.  |
| **Oracle**         | `SELECT *, RANK() OVER (PARTITION BY dept ORDER BY salary DESC) FROM employees` | Same syntax.                          |
| **MySQL (8.0+)**   | `SELECT *, RANK() OVER (PARTITION BY dept ORDER BY salary DESC) FROM employees` | Introduced in MySQL 8.0.                   |
| **SQL Server**     | `SELECT *, RANK() OVER (PARTITION BY dept ORDER BY salary DESC) FROM employees` | Standard.                                 |
| **SQLite**         | *No native support*                          | Use `GROUP_CONCAT` + subqueries.          |

---
### **3.5 Transactions**
| **Database**       | **SQL**                                      | **Notes**                                  |
|--------------------|---------------------------------------------|--------------------------------------------|
| PostgreSQL         | `BEGIN; INSERT INTO users (...) VALUES (...); COMMIT;` | Standard.                                 |
| **MySQL**          | `START TRANSACTION; INSERT INTO users (...) VALUES (...); COMMIT;` | `START TRANSACTION` vs. `BEGIN`.          |
| **Oracle**         | `BEGIN TRANSACTION; INSERT INTO users (...) VALUES (...); COMMIT;` | `BEGIN TRANSACTION` (not `BEGIN`).          |
| **SQL Server**     | `BEGIN TRANSACTION; INSERT INTO users (...) VALUES (...); COMMIT;` | Same as Oracle.                           |
| **SQLite**         | *Auto-commit by default*                    | Use `BEGIN TRANSACTION` + `COMMIT`.       |

---
## **4. Implementation Patterns**

### **4.1 Dynamic SQL Generation**
```python
# Pseudocode: Generate DB-specific SQL
def build_query(db_type, params):
    if db_type == "POSTGRESQL":
        return f"SELECT * FROM users LIMIT {params['limit']} OFFSET {params['offset']}"
    elif db_type == "ORACLE":
        return (
            f"SELECT * FROM ("
            f"  SELECT * FROM users "
            f"  ORDER BY id "
            f"  FETCH FIRST {params['limit']} ROWS ONLY OFFSET {params['offset']} ROWS)"
        )
    # ... add other DB cases
```

### **4.2 Feature Detection**
```python
# Check if a DB supports JSON functions
def has_json_support(db_connection):
    try:
        # Test a known JSON function
        cursor = db_connection.cursor()
        cursor.execute("SELECT JSON_OBJECT('a', 1) AS test")
        return True
    except Exception:
        return False
```

### **4.3 Fallback Strategy**
```python
def top_n_users(db_type, limit):
    if db_type in ("POSTGRESQL", "MYSQL"):
        return f"SELECT * FROM users ORDER BY signup_date DESC LIMIT {limit}"
    elif db_type == "SQLITE":
        return f"SELECT * FROM users ORDER BY signup_date DESC LIMIT {limit}"
    else:  # Oracle/SQL Server
        return f"SELECT * FROM users ORDER BY signup_date DESC FETCH FIRST {limit} ROWS ONLY"
```

---
## **5. Related Patterns**
| **Pattern**                     | **Description**                                                                 | **Use Case**                          |
|---------------------------------|---------------------------------------------------------------------------------|---------------------------------------|
| **[Database Abstraction Layer](https://martinfowler.com/eaaCatalog/databaseAbstractionLayer.html)** | Abstracts DB-specific code into a unified API.                               | Legacy system refactoring.              |
| **Repository Pattern**          | Encapsulates data access logic (e.g., `UserRepository`).                      | Large-scale apps with complex ORM.    |
| **Schema Regression Testing**   | Validates SQL compatibility across databases.                                 | CI/CD pipelines.                      |
| **Connection Pooling**          | Reuses DB connections for performance.                                      | High-traffic apps.                     |

---
## **6. Best Practices**
1. **Centralize SQL Templates**
   Store DB-specific SQL fragments in config files or a DSL to avoid hardcoding.

2. **Use ORMs with Caution**
   ORMs (e.g., SQLAlchemy) may not support all features. Prefer raw SQL for edge cases.

3. **Test with Real Databases**
   Critical queries should be tested in target environments (e.g., Dockerized DBs).

4. **Leverage DB-Specific Optimizations**
   Example: Use PostgreSQL’s `EXPLAIN ANALYZE` vs. MySQL’s `EXPLAIN`.

5. **Handle Quirks Early**
   - SQLite’s `LIMIT` syntax differs from others.
   - Oracle’s `ROWNUM` vs. other pagination methods.

---
## **7. Common Pitfalls**
| **Pitfall**                          | **Solution**                                                                 |
|--------------------------------------|-----------------------------------------------------------------------------|
| **Syntax Errors**                    | Use a validation layer (e.g., `sqlparse`).                                 |
| **Missing Features**                 | Implement fallbacks (e.g., emulate window functions with subqueries).        |
| **Performance Differences**           | Profile queries per DB; adjust `LIMIT`/`OFFSET` for SQLite.                 |
| **Transaction Isolation Mismatches**  | Test `READ COMMITTED` vs. `SERIALIZABLE` behavior in each DB.                |

---
## **8. Tools & Libraries**
| **Tool**                          | **Purpose**                                                                 |
|-----------------------------------|-----------------------------------------------------------------------------|
| **PyGreSQL** / **sqlalchemy**     | Python DB abstraction layers.                                               |
| **DBeaver**                       | Cross-DB SQL editor with syntax highlighting.                              |
| **SQLFluff**                      | Linter/formatter for SQL (multi-DB support).                                |
| **Testcontainers**                | Spin up Dockerized DBs for testing.                                        |

---
## **9. Further Reading**
- [Fowler’s Database Abstraction Layer](https://martinfowler.com/eaaCatalog/databaseAbstractionLayer.html)
- [PostgreSQL vs. MySQL: Key Differences](https://www.postgresql.org/about/qa/)
- [SQLite3 JSON1 Extension](https://sqlite.org/json1.html)
- [Oracle FETCH FIRST Syntax](https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/FETCH-FIRST.html)