# **[Pattern] Database Compatibility Testing Reference Guide**

---

## **Overview**
The **Database Compatibility Testing** pattern ensures that SQL queries, stored procedures, and database-specific features function correctly across multiple database systems or versions. This is critical for applications leveraging multi-database architectures (e.g., PostgreSQL, MySQL, SQL Server) or migrating between platforms. The pattern standardizes test frameworks, query abstractions, and environment setups to automate cross-database validation while accounting for syntax variations, performance quirks, and T-SQL, PL/pgSQL, or JavaScript (SQLite) incompatibilities. By identifying and addressing discrepancies early, this pattern minimizes production failures and reduces refactoring overhead.

---

## **Key Components**
| **Component**               | **Purpose**                                                                                     | **Implementation Notes**                                                                 |
|------------------------------|-------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------|
| **Test Environment**         | Replicates target databases (on-prem/cloud, versioned) for consistent testing.               | Use Docker, VMs, or managed services (e.g., AWS RDS, Azure SQL).                      |
| **Query Abstraction Layer**  | Normalizes SQL syntax (e.g., `LIMIT` → `TOP`, `OFFSET` → `FETCH NEXT`).                       | Leverage libraries like [Drizzle ORM](https://orm.drizzle.team/), [Knex.js](https://knexjs.org/), or custom adapters. |
| **Feature Flags**            | Toggles database-specific features (e.g., `CITEXT` vs. `VARCHAR` collation).                   | Store flags in config files or environment variables.                                   |
| **Test Suite**               | Validates CRUD operations, transactions, and edge cases.                                       | Use frameworks like [Pest](https://pestphp.com/) (PHP), [pytest](https://docs.pytest.org/) (Python), or [JUnit](https://junit.org/). |
| **Result Comparison**        | Detects discrepancies in output (e.g., `NULL` vs. `NULLABLE` handling).                         | Implement fuzzy comparisons (e.g., ignore whitespace, normalize timestamps).            |
| **Performance Benchmarking** | Compares query execution times across databases.                                               | Tools: [pgMustard](https://pgmustard.github.io/) (PostgreSQL), [sql-monitor](https://github.com/pganalyze/sql-monitor). |

---

## **Schema Reference**
Below are common database schema patterns and their incompatibilities.

| **Feature**               | **PostgreSQL**                          | **MySQL**                              | **SQL Server**                          | **Notes**                                  |
|---------------------------|-----------------------------------------|----------------------------------------|-----------------------------------------|--------------------------------------------|
| **String Collation**      | `VARCHAR` with `COLLATE "C"`             | `VARCHAR` + `CHARACTER SET utf8mb4`     | `VARCHAR(MAX)` + `COLLATE SQL_Latin1_General_CP1_CI_AS` | Use `TEXT` for binary-safe operations.    |
| **Date/Time Handling**    | `TIMESTAMP WITH TIME ZONE`              | `DATETIME` (UTC)                       | `DATETIMEOFFSET`                        | Avoid hardcoding time zones; use `UTILITY.DATETIMEFROMPARTS`. |
| **JSON Support**          | `JSONB` (indexable), `JSON` (serialized)| `JSON` (5.7+)                          | `NVARCHAR(MAX)` (via `OPENJSON`)        | PostgreSQL: Prefer `JSONB` for performance. |
| **Window Functions**      | `OVER(PARTITION BY x ORDER BY y)`        | Limited (e.g., `RANK()`)               | Full support (`ROWS BETWEEN`)           | MySQL <8.0: Use user variables or subqueries. |
| **CTEs (WITH Clause)**    | Supported (`RECURSIVE` for hierarchies) | Supported (no recursion)               | Supported (`WITH RECURSIVE`)            | MySQL <8.0: Use temporary tables.          |
| **Auto-Increment**        | `SERIAL` or `BIGSERIAL`                 | `AUTO_INCREMENT`                       | `IDENTITY(1,1)`                         | PostgreSQL: `SERIAL` is a shortcut for `INTEGER` + `DEFAULT nextval()`. |
| **Transactions**          | `BEGIN`, `COMMIT`, `ROLLBACK`           | Same                                   | Same + `TRY/CATCH`                      | SQL Server: Use `SET XACT_ABORT ON` for error propagation. |
| **Stored Procedures**     | `PL/pgSQL`                              | `MySQL Stored Procedure`               | `T-SQL`                                 | PL/pgSQL: Use `DO $$ ... $$` for dynamic SQL. |

---

## **Query Examples**
### **1. Cross-Database `LIMIT` Equivalents**
#### **PostgreSQL/MySQL:**
```sql
SELECT * FROM users LIMIT 10 OFFSET 5;
```
#### **SQL Server:**
```sql
SELECT * FROM users
ORDER BY id  -- Required for OFFSET/FETCH
OFFSET 5 ROWS FETCH NEXT 10 ROWS ONLY;
```
#### **Abstraction Layer (Pseudocode):**
```python
def limit_query(query: str, limit: int, offset: int = 0):
    if database == "postgres" or database == "mysql":
        return query + f" LIMIT {limit} OFFSET {offset}"
    elif database == "sqlserver":
        return f"{query} ORDER BY id OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY"
```

---

### **2. Dynamic Table Creation (Database-Specific)**
#### **PostgreSQL:**
```sql
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);
```
#### **MySQL:**
```sql
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);
```
#### **SQL Server:**
```sql
CREATE TABLE IF NOT EXISTS users (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(100) NOT NULL
);
```
#### **Abstraction Solution:**
Use a template engine (e.g., Jinja2) to generate schema DDL:
```jinja
CREATE TABLE IF NOT EXISTS users (
    id {{ database_auto_increment )),
    name VARCHAR(100) NOT NULL
);
```
- `{{ database_auto_increment }}` expands to:
  - PostgreSQL: `SERIAL`
  - MySQL: `INT AUTO_INCREMENT`
  - SQL Server: `INT IDENTITY(1,1)`

---

### **3. NULL Handling in Aggregations**
#### **PostgreSQL/MySQL (COUNT):**
```sql
SELECT COUNT(*) FROM orders;  -- Counts NULL rows
SELECT COUNT(id) FROM orders; -- Excludes NULL ids
```
#### **SQL Server:**
```sql
SELECT COUNT_BIG(*) FROM orders;  -- Use COUNT_BIG for large tables
SELECT COUNT(id) FROM orders;     -- Same as others
```
#### **Test Case:**
```python
# Verify COUNT NULL behavior
assert query("SELECT COUNT(*) FROM orders") == query("SELECT COUNT(id) FROM orders")
```

---

### **4. Batch Inserts**
#### **PostgreSQL (COPY):**
```sql
COPY users(id, name) FROM '/tmp/users.csv' WITH (FORMAT CSV);
```
#### **MySQL (LOAD DATA):**
```sql
LOAD DATA INFILE '/tmp/users.csv'
INTO TABLE users (id, name)
FIELDS TERMINATED BY ',';
```
#### **SQL Server (BULK INSERT):**
```sql
BULK INSERT users
FROM '/tmp/users.csv'
WITH (FIELDTERMINATOR = ',', ROWTERMINATOR = '\n');
```
#### **Abstraction Workaround:**
Use a multi-step process:
1. Write data to a temp table.
2. Use `INSERT INTO ... SELECT` across databases.

---

### **5. Stored Procedure Calls**
#### **PostgreSQL (PL/pgSQL):**
```sql
CREATE OR REPLACE FUNCTION get_user(id INT) RETURNS JSON AS $$
BEGIN
    RETURN TO_JSONB(SELECT * FROM users WHERE id = $1);
END;
$$ LANGUAGE plpgsql;

SELECT get_user(1);
```
#### **MySQL:**
```sql
DELIMITER //
CREATE PROCEDURE get_user(IN id INT)
BEGIN
    SELECT * FROM users WHERE id = id;
END //
DELIMITER ;

CALL get_user(1);
```
#### **SQL Server (T-SQL):**
```sql
CREATE PROCEDURE [dbo].[GetUser]
    @id INT
AS
BEGIN
    SELECT * FROM users WHERE id = @id;
END;

EXEC GetUser @id = 1;
```
#### **Test Automation:**
Mock procedure calls in tests using frameworks like [DBML](https://dbml.dev/) (Python) or [pgTAP](http://pgtap.org/) (PostgreSQL).

---

## **Implementation Steps**
### **1. Set Up Test Environments**
- **Docker Compose Example:**
  ```yaml
  version: '3'
  services:
    postgres:
      image: postgres:15
      environment:
        POSTGRES_PASSWORD: test
    mysql:
      image: mysql:8.0
      environment:
        MYSQL_ROOT_PASSWORD: test
  ```
- **Cloud Providers:**
  - AWS RDS: Create snapshots of baseline versions.
  - Azure: Use SQL Database Dev/Test environments.

### **2. Implement Query Abstraction**
- **Option A: ORM Layer**
  Use an ORM like Drizzle.js to abstract queries:
  ```javascript
  const user = await db.query.users.findFirst({
    where: eq(users.id, 1),
    limit: 10,
  });
  ```
- **Option B: Custom Wrapper**
  ```python
  def get_users(limit: int, offset: int):
      if db == "postgres":
          return f"SELECT * FROM users LIMIT {limit} OFFSET {offset}"
      elif db == "mysql":
          return f"SELECT * FROM users LIMIT {offset}, {limit}"
  ```

### **3. Write Test Cases**
- **Unit Tests (Python Example):**
  ```python
  def test_user_insertion():
      # Setup
      db = connect("postgres")
      db.query("TRUNCATE TABLE users")

      # Test
      db.query("INSERT INTO users VALUES (1, 'Alice')")
      result = db.query("SELECT name FROM users WHERE id = 1")
      assert result == ["Alice"]

      # Teardown
      db.query("TRUNCATE TABLE users")
  ```
- **Integration Tests:**
  Test end-to-end workflows (e.g., order processing) across 2+ databases.

### **4. Compare Results**
- **Tooling:**
  - [TestContainers](https://www.testcontainers.org/) (Java/Python): Spin up ephemeral DBs.
  - [SchemaSpy](http://schemaspy.org/): Compare schemas post-migration.
- **Diff Scripts:**
  ```bash
  # Compare query outputs
  mysql -u root -h localhost test -e "SELECT * FROM users" | grep -v "id" > mysql_output.txt
  psql -U postgres -h localhost -d test -c "SELECT * FROM users" | grep -v "id" > postgres_output.txt
  diff mysql_output.txt postgres_output.txt
  ```

### **5. Handle Incompatibilities**
| **Issue**                     | **Solution**                                                                 |
|-------------------------------|--------------------------------------------------------------------------------|
| Missing functions (e.g., `JSON_EXTRACT`) | Implement polyfills (e.g., regex in MySQL for JSON parsing).                  |
| No window functions (MySQL <8.0) | Use `USER VARIABLES` or temporary tables for ranking.                        |
| Case sensitivity in `LIKE`     | Normalize queries (e.g., `UPPER(column) LIKE UPPER('%term%')`).              |
| Transaction isolation levels   | Test with `READ COMMITTED` (SQL Server default) vs. `REPEATABLE READ` (PostgreSQL). |

---

## **Query Examples: Edge Cases**
### **1. Time Zone Handling**
#### **Problem:**
PostgreSQL’s `TIMESTAMP WITH TIME ZONE` vs. MySQL’s `DATETIME` (UTC).
#### **Test Query:**
```sql
-- PostgreSQL: Adjusts for time zones
SELECT NOW() AT TIME ZONE 'UTC';

-- MySQL: Returns UTC but no built-in conversion
SELECT CONVERT_TZ(NOW(), @@session.time_zone, 'UTC');
```
#### **Solution:**
Standardize on UTC in application code:
```python
from datetime import datetime, timezone

def to_utc(dt):
    if db == "mysql":
        return dt.astimezone(timezone.utc)
    return dt.replace(tzinfo=timezone.utc)
```

---

### **2. JSON Path Queries**
#### **PostgreSQL:**
```sql
SELECT jsonb_path_query_array(users.json_data, '$.address.city') FROM users;
```
#### **MySQL:**
```sql
SELECT JSON_EXTRACT(users.json_data, '$.address.city') FROM users;
```
#### **SQL Server:**
```sql
SELECT OPENJSON(users.json_data, '$.address') WITH (
    city NVARCHAR(100) AS '$.city'
) FROM users;
```
#### **Test Workaround:**
Use a common JSON library (e.g., [jsonschema](https://json-schema.org/)) for validation.

---

### **3. Full-Text Search**
#### **PostgreSQL:**
```sql
CREATE INDEX idx_users_search ON users USING GIN (to_tsvector('english', name));
SELECT * FROM users WHERE to_tsvector('english', name) @@ to_tsquery('alpha*');
```
#### **MySQL:**
```sql
ALTER TABLE users ADD FULLTEXT(name);
SELECT * FROM users WHERE MATCH(name) AGAINST('alpha*');
```
#### **SQL Server:**
```sql
CREATE FULLTEXT INDEX ON users(name);
SELECT * FROM users WHERE CONTAINS(name, 'alpha*');
```
#### **Implementation Note:**
Implement a unified API:
```python
def search_users(query: str):
    if db == "postgres":
        return f"to_tsvector('english', name) @@ to_tsquery('{query}')"
    elif db == "mysql":
        return f"MATCH(name) AGAINST('{query}')"
```

---

## **Related Patterns**
1. **[Feature Flags Pattern](https://martinfowler.com/articles/feature-toggles.html)**
   - Use feature flags to toggle database-specific behaviors (e.g., enable `JSONB` path queries only in PostgreSQL).
2. **[Schema Migration Pattern](https://martinfowler.com/eaaCatalog/schemaMigration.html)**
   - Synchronize schema changes across databases using tools like [Flyway](https://flywaydb.org/) or [Liquibase](https://www.liquibase.org/).
3. **[Database Sharding Pattern](https://martinfowler.com/eaaCatalog/databaseSharding.html)**
   - Complementary to compatibility testing; ensures queries work across shards.
4. **[Query Caching Pattern](https://martinfowler.com/eaaCatalog/cachingStrategy.html)**
   - Cache results to reduce cross-database query overhead.
5. **[Transaction Scripting vs. Domain Model Pattern](https://martinfowler.com/eaaCatalog/transactionScript.html)**
   - If using transaction scripts, parameterize queries to avoid hardcoding database syntax.

---

## **Anti-Patterns to Avoid**
| **Anti-Pattern**                          | **Risk**                                                                 | **Mitigation**                                                                 |
|--------------------------------------------|---------------------------------------------------------------------------|--------------------------------------------------------------------------------|
| **String Concatenation for Queries**       | SQL injection, syntax errors.                                             | Use prepared statements (e.g., `?` placeholders).                             |
| **Ignoring Schema Differences**            | Silent failures in production.                                             | Validate schema compatibility pre-deployment.                                  |
| **Hardcoding Database-Specific Logic**    | Violates DRY principle.                                                    | Abstract logic into configuration or middleware.                              |
| **Testing Only Happy Paths**               | Undetected edge cases (e.g., NULL handling).                               | Include negative test cases (e.g., `INSERT NULL WHERE NOT NULL`).               |
| **No Rollback Plan**                       | Orphaned test data corrupts environments.                                  | Use transactions or schema resets in tests.                                    |

---

## **Tools & Libraries**
| **Purpose**               | **Tools/Libraries**                                                                 |
|---------------------------|------------------------------------------------------------------------------------|
| **ORM/Query Abstraction** | [Drizzle ORM](https://orm.drizzle.team/), [Knex.js](https://knexjs.org/), [SQLAlchemy](https://www.sqlalchemy.org/) |
| **Testing Frameworks**    | [Pest](https://pestphp.com/), [pytest](https://docs.pytest.org/), [JUnit](https://junit.org/)              |
| **Schema Comparison**     | [SchemaSpy](http://schemaspy.org/), [SQLDelta](https://github.com/sql-delta/sql-delta)                   |
| **Dockerized DBs**        | [TestContainers](https://www.testcontainers.org/), [Docker Compose](https://docs.docker.com/compose/)     |
| **CI/CD Integration**     | [GitHub Actions](https://github.com/features/actions), [GitLab CI](https://docs.gitlab.com/ee/ci/)         |

---

## **Checklist for Implementation**
1. [ ] Define target databases and versions.
2. [ ] Set up test environments (Docker/VMs/cloud).
3. [ ] Choose a query abstraction strategy (ORM or custom wrapper).
4. [ ] Implement feature flags for database-specific logic.
5. [ ] Write unit tests for CRUD operations and edge cases.
6. [ ] Compare query outputs across databases (tools: `diff`, TestContainers).
7. [ ] Document known incompatibilities and workarounds.
8. [ ] Integrate testing into CI/CD pipeline.
9. [ ] Schedule periodic compatibility reviews (e.g., quarterly).

---
**References:**
- [Database Compatibility Guide (Drizzle)](https://orm.drizzle.team/docs/compatibility)
- [SQL Standard vs. Database Extensions](https://www.sqlite.org/lang_keywords.html)
- [PostgreSQL vs. MySQL Comparison](https://www.postgresql.org/docs/current/sql-statements.html)