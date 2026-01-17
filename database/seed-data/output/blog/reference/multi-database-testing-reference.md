# **[Pattern] Multi-Database Testing Reference Guide**

---
## **Overview**
The **Multi-Database Testing** pattern ensures that application logic and integrations work consistently across diverse database systems (e.g., SQL Server, PostgreSQL, MySQL, MongoDB). This pattern mitigates risks from vendor lock-in and guarantees compatibility when deploying in heterogeneous environments. It involves:
- **Database-agnostic queries** (e.g., using ANSI SQL where possible).
- **Abstraction layers** (e.g., ORMs, query builders, or dynamic SQL generators).
- **Test coverage** for schema differences, transaction isolation, and query performance.
- **Continuous validation** via automated CI/CD pipelines.

This guide covers implementation strategies, schema considerations, and query examples for common database families.

---

## **Key Concepts**
### **1. Database Agnosticism**
- Avoid proprietary features (e.g., SQL Server’s `TOP`, Oracle’s `ROWNUM`).
- Use **standard SQL** (e.g., `JOIN`, `WHERE`, `GROUP BY`) or platform-specific profiles.
- Example: Replace `LIMIT` (PostgreSQL/MySQL) with `FETCH FIRST` (SQL Server) via dynamic wrappers.

### **2. Abstraction Layers**
| **Layer**          | **Purpose**                                                                 | **Implement Via**                          |
|---------------------|-----------------------------------------------------------------------------|--------------------------------------------|
| **ORM**            | Map objects to tables, handle dialect-specific syntax.                       | Entity Framework (C#), Hibernate (Java), Django ORM (Python) |
| **Query Builder**  | Construct queries dynamically for multiple dialects.                        | Dapper (C#), TypeORM (TypeScript), raw SQL templates |
| **Middleware**     | Wrap database calls; support fallbacks or migrations.                       | Custom interceptors, database proxy tools |

### **3. Schema Compatibility**
- **Standardize schema naming**: Use snake_case or camelCase consistently.
- **Normalize common fields**: E.g., `created_at` instead of `create_date`/`created_on`.
- **Handle schema differences**:
  - Primary keys (auto-increment vs. UUID).
  - Case sensitivity (e.g., MySQL is case-insensitive by default for `utf8mb4`, PostgreSQL is not).
  - JSON vs. separate tables (NoSQL vs. relational).

### **4. Transaction Isolation**
| **Database**       | **Default Isolation** | **Notes**                                  |
|--------------------|-----------------------|--------------------------------------------|
| PostgreSQL         | Read Committed        | Supports `SERIALIZABLE` for strict ACID.   |
| SQL Server         | Read Committed        | Uses `Snapshot Isolation` for long transactions. |
| MongoDB            | Read Committed        | No native transactions; use multi-document ACID modes. |

**Recommendation**: Test with `READ UNCOMMITTED` and `REPEATABLE READ` to detect inconsistencies.

---

## **Schema Reference**
Compare core schema elements across databases. Below are common patterns:

| **Feature**               | **PostgreSQL**               | **SQL Server**               | **MySQL**                  | **MongoDB**               |
|---------------------------|-----------------------------|------------------------------|----------------------------|----------------------------|
| **Primary Key**           | `SERIAL` (auto-increment)   | `IDENTITY(1,1)`              | `AUTO_INCREMENT`           | `_id` (ObjectId)          |
| **Case Sensitivity**      | `name VARCHAR(255)` (case-sensitive) | `name NVARCHAR(255)` (case-sensitive) | `name VARCHAR(255)` (default case-insensitive) | `name: string` (case-sensitive) |
| **JSON Support**          | `jsonb` column               | `NVARCHAR(MAX)` + JSON functions | `JSON` column              | Native document storage    |
| **Indexes**               | `CREATE INDEX idx_name ON table(name)` | `CREATE INDEX idx_name ON table(name)` | `ALTER TABLE add INDEX idx_name(name)` | `{ "name": 1 }` (collection-level) |
| **Date/Time Precision**   | `TIMESTAMP WITH TIME ZONE`   | `DATETIMEOFFSET`             | `DATETIME(6)`              | `ISODate`                 |

---
**Best Practice**: Use a **schema registry** (e.g., Flyway, Liquibase) to manage migrations across databases.

---

## **Query Examples**
### **1. Database-Agnostic Joins**
| **Problem**               | **PostgreSQL/SQL Server**               | **MongoDB (Aggregation)**         |
|---------------------------|----------------------------------------|----------------------------------|
| Join `users` and `orders` | `SELECT u.name, o.total FROM users u JOIN orders o ON u.id = o.user_id;` | `{ $lookup: { from: "orders", localField: "_id", foreignField: "user_id", as: "user_orders" } }` |

**Solution**: Use a query builder like **Dapper** or **TypeORM** to generate the correct syntax:
```csharp
// Dapper (C#)
var query = "SELECT u.name, o.total FROM users u JOIN orders o ON u.id = o.user_id";
var results = connection.Query<dynamic>(query);
```

### **2. Handling NULLs and Defaults**
| **Database**       | **Default NULL Behavior** | **Example Query**                          |
|--------------------|---------------------------|--------------------------------------------|
| PostgreSQL         | `NULL` accepted           | `WHERE created_at IS NULL OR created_at > '2023-01-01'` |
| SQL Server         | `NULL` accepted           | `WHERE ISNULL(created_at, '1900-01-01') > '2023-01-01'` |
| MySQL              | `NULL` accepted           | `WHERE IFNULL(created_at, '1970-01-01') > '2023-01-01'` |

**Solution**: Use **parameterized queries** to avoid SQL injection:
```python
# SQLAlchemy (Python)
query = "SELECT * FROM users WHERE created_at IS NULL OR created_at > :date"
result = session.execute(query, {"date": "2023-01-01"})
```

### **3. Dynamic SQL for Dialect Support**
**Pattern**: Generate SQL strings conditioned on the database type.
```javascript
// TypeORM (TypeScript)
const query = entityManager.createQueryBuilder()
  .select("u.name")
  .from(User, "u")
  .where("u.active = :active", { active: true })
  .andWhere(dialect === 'mysql' ? "u.created_at > NOW() - INTERVAL 7 DAY" : "u.created_at > DATEADD(day, -7, GETDATE())");
```

### **4. Transaction Testing**
Test with **savepoints** or **distributed transactions** (if supported):
```sql
-- PostgreSQL (START + COMMIT)
BEGIN;
  INSERT INTO users VALUES (1, 'Alice');
  COMMIT;

-- SQL Server (TRY-CATCH)
BEGIN TRY
  INSERT INTO users VALUES (2, 'Bob');
  COMMIT TRANSACTION;
END TRY
BEGIN CATCH
  ROLLBACK TRANSACTION;
END CATCH;
```

**MongoDB Alternative**:
```javascript
// MongoDB (Session API)
const session = db.getMongo().startSession();
session.startTransaction();
try {
  db.users.insertOne({ name: "Alice" }, { session });
  session.commitTransaction();
} catch (e) {
  session.abortTransaction();
}
```

---

## **Testing Strategies**
### **1. Unit Tests for Queries**
Use **mock databases** (e.g., `MockDbUnit` for JUnit, `pytest` with `SQLAlchemy`).
```python
# Pytest example
def test_join_query():
    conn = create_mock_connection()
    result = conn.execute("SELECT * FROM users JOIN orders ON users.id = orders.user_id")
    assert len(result) == 2
```

### **2. Integration Tests**
- **Test Environment**: Deploy to a staging DB with multiple engines (e.g., RDS for PostgreSQL + Azure SQL).
- **CI/CD**: Run tests in parallel across databases using **GitHub Actions** or **GitLab CI**:
  ```yaml
  # GitHub Actions example
  jobs:
    test-postgres:
      runs-on: ubuntu-latest
      services:
        postgres:
          image: postgres:13
  ```

### **3. Schema Validation**
- **Tools**:
  - **SQL: `pg_diff`** (PostgreSQL → PostgreSQL)
  - **JSON Schema**: Validate NoSQL documents against a schema registry.
- **Automate**: Use **SchemaSpy** to generate docs and detect drift.

---

## **Performance Considerations**
| **Database**       | **Optimization Tips**                          |
|--------------------|-----------------------------------------------|
| PostgreSQL         | Use `EXPLAIN ANALYZE` to identify bottlenecks. |
| SQL Server         | Enable `INDEX` stats updates (`AUTO_UPDATE_STATISTICS`). |
| MongoDB            | Shard large collections; use `TTL indexes`.   |

**Best Practice**: Benchmark queries across databases using **JMeter** or **k6**.

---

## **Related Patterns**
1. **[Database Sharding]** – Partition data across multiple DB instances for scalability.
2. **[Feature Flags]** – Roll out database changes gradually (e.g., toggle query behavior).
3. **[Canary Testing]** – Deploy to a subset of users with a new DB version.
4. **[Schema Migration]** – Use tools like **Flyway** or **Alembic** to sync schemas.
5. **[Event Sourcing]** – Decouple database writes from application logic for testing.

---
## **Anti-Patterns to Avoid**
- ❌ **Hardcoding database-specific syntax** (e.g., `SELECT TOP 10` without checks).
- ❌ **Ignoring case sensitivity** (e.g., assuming `name = 'Alice'` works everywhere).
- ❌ **Assuming ACID behaves identically** (e.g., MongoDB lacks native multi-document transactions).
- ❌ **No rollback testing** for failed migrations.

---
## **Tools & Libraries**
| **Category**               | **Tools**                                      |
|----------------------------|------------------------------------------------|
| **ORM/Query Builders**     | Entity Framework, Hibernate, TypeORM, SQLAlchemy |
| **Schema Migration**       | Flyway, Liquibase, Alembic                     |
| **Testing**                | Jest, pytest, JUnit, MockDbUnit                 |
| **CI/CD Integration**      | GitHub Actions, GitLab CI, CircleCI             |
| **Database Monitoring**    | Datadog, New Relic, pgAdmin                     |

---
### **Further Reading**
- [ORM vs. Query Builder: When to Use Each](https://dev.to/awwwards/orm-vs-query-builder-which-one-to-use-4f7l)
- [PostgreSQL vs. SQL Server: Feature Comparison](https://www.cdata.com/drivers/postgresql-vs-sql-server/)
- [MongoDB Transactions: A Primer](https://www.mongodb.com/basics/mongodb-transactions)