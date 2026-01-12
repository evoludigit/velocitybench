# **[Pattern] Database Migration Patterns – Reference Guide**

---

## **1. Overview**
The **Database Migration Patterns** reference guide provides best practices, key concepts, and implementation details for migrating data between database schemas, versions, or systems while minimizing downtime, data loss, or corruption. Common migration scenarios include:
- Upgrading to a new database version.
- Refactoring schemas (e.g., altering tables, renaming columns).
- Consolidating multiple databases into one.
- Migrating from legacy systems to modern databases (e.g., SQL Server → PostgreSQL, Oracle → MySQL).

This guide covers **migration patterns**, **strategies**, **tools**, and **common pitfalls**, ensuring a structured approach to database evolution.

---

## **2. Schema Reference**
The following table outlines critical components of a **migration schema**:

| **Component**               | **Description**                                                                 | **Example**                                                                 |
|-----------------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Versioned Schema**        | A database schema tracked via version control (e.g., Git) to log changes.   | `schema_20231001_v1`, `schema_20231005_v2`                                  |
| **Migration Script**        | SQL or tool-specific script to apply a schema change (e.g., add column, drop table). | `ALTER TABLE users ADD COLUMN last_login TIMESTAMP NULL;`                 |
| **Data Migration Script**   | Logic to transform or transfer data between states (e.g., type conversion, filtering). | `UPDATE products SET price = price + (price * 0.10);` (for tax adjustment) |
| **Rollback Script**         | Undo a migration in case of failure (critical for production).                | `ALTER TABLE orders DROP COLUMN shipping_fee;`                             |
| **Downtime Window**         | Time allocated for migration (affects batch vs. live migration).               | 30-minute maintenance window                                                |
| **Transaction Isolation**   | Read consistency level during migration (e.g., `READ COMMITTED` vs. `SERIALIZABLE`). | `SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;`                       |
| **Validation Check**        | Post-migration checks to ensure data integrity (e.g., record counts, constraints). | ```sql SELECT COUNT(*) FROM users WHERE id IN (SELECT DISTINCT user_id FROM orders); ``` |
| **Migration Log**           | Audit trail of executed migrations (timestamp, user, success/failure).       | `migration_logs: [{"id":1, "timestamp":"2023-10-01T12:00:00", "status":"success"}]` |

---

## **3. Implementation Details**
### **3.1 Core Patterns**
#### **A. Versioned Schema Migrations**
- **Use Case**: Sequential schema updates (e.g., from `v1` to `v2`).
- **How It Works**:
  1. Store migration scripts in version control (e.g., `migrations/001_create_users_table.sql`).
  2. Apply scripts in order during deployment.
  3. Track applied migrations in a `schema_migrations` table.
- **Tools**:
  - **Flyway** (SQL-based, supports rollbacks).
  - **Liquibase** (XML/YAML/XML scripts, change logs).
  - **Alembic** (Python, for PostgreSQL/SQLAlchemy).

**Example Flyway Migration File (`V1__Create_Users.sql`)**:
```sql
--+ Flyway SQL
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

#### **B. Zero-Downtime Migration**
- **Use Case**: Avoiding downtime during production schema changes.
- **How It Works**:
  1. **Add-Column Migration**:
     - Start with a nullable column, update data, then alter the column to `NOT NULL`.
     ```sql
     -- Step 1: Add nullable column
     ALTER TABLE orders ADD COLUMN shipping_fee DECIMAL(10,2) NULL;

     -- Step 2: Update existing records
     UPDATE orders SET shipping_fee = 0.00 WHERE shipping_fee IS NULL;

     -- Step 3: Make column non-nullable
     ALTER TABLE orders ALTER COLUMN shipping_fee SET NOT NULL;
     ```
  2. **Read/Write Splitting**:
     - Redirect new reads to the new schema while writes continue on the old schema.
     - Use database replication or application routing.

---

#### **C. Data Transformation Migrations**
- **Use Case**: Converting data formats (e.g., `TEXT` → `JSONB` in PostgreSQL).
- **How It Works**:
  1. **Batch Processing**: Use tools like `pg_dump` (PostgreSQL) or `mysqldump` to extract, transform, and reinsert data.
     ```sql
     -- Convert legacy format to JSON
     UPDATE products SET description = to_jsonb(description_legacy);
     ```
  2. **ETL Pipelines**: Use Apache NiFi, Airflow, or custom scripts for complex transformations.
  3. **Schema-Agnostic Functions**: Write reusable functions to handle transformations (e.g., Python `pandas` or SQL `CASE` statements).

---

#### **D. Schema Inference (Reverse Engineering)**
- **Use Case**: Generating migration scripts from an existing database.
- **How It Works**:
  1. **Extract Schema**: Use tools to generate SQL scripts from a live database.
     - **MySQL**: `mysqldump -d database_name > schema.sql`
     - **PostgreSQL**: `pg_dump -s -d database_name > schema.sql`
     - **Liquibase**: `liquibase diff --referenceUrl=postgres://user:pass@host/db`
  2. **Differencing**: Compare schemas between environments (e.g., dev vs. prod) to identify changes.

---

#### **E. Rollback Strategies**
- **Automated Rollbacks**:
  - Store rollback scripts alongside migrations (e.g., `V1__Create_Users_rollback.sql`).
  - Example:
    ```sql
    DROP TABLE IF EXISTS users;
    ```
- **Backup Before Migration**:
  - Always take a backup (e.g., `pg_dumpall` for PostgreSQL) before applying migrations.
- **Feature Flags**:
  - Deploy the new schema but hide it from users until fully validated.

---

### **3.2 Common Pitfalls & Mitigations**
| **Pitfall**                          | **Mitigation**                                                                 |
|---------------------------------------|--------------------------------------------------------------------------------|
| **Data Corruption**                   | Use transactions (`BEGIN`/`COMMIT`) and validate post-migration.              |
| **Downtime in Production**            | Schedule migrations during low-traffic periods or use zero-downtime patterns. |
| **Lock Contention**                   | Apply changes during off-peak hours or use `ONLINE` operations (e.g., MySQL `ALTER TABLE`). |
| **Incompatible Schema Changes**       | Test migrations in staging with production-like data.                          |
| **Missing Rollback Plan**             | Always define a rollback script and test it.                                    |
| **Concurrency Issues**                | Use `SELECT FOR UPDATE` or database-specific locking mechanisms.               |

---

## **4. Query Examples**
### **4.1 Basic Schema Migration**
**Add a Column with Default Value**:
```sql
-- MySQL
ALTER TABLE products ADD COLUMN discount_rate DECIMAL(5,2) DEFAULT 0.00;

-- PostgreSQL
ALTER TABLE products ADD COLUMN discount_rate DECIMAL(5,2) DEFAULT '0.00'::DECIMAL;
```

**Rename a Column**:
```sql
-- SQL Server
EXEC sp_rename 'users.username', 'user_id', 'COLUMN';
```

**Drop a Table Safely**:
```sql
-- First, verify no dependent objects exist
SELECT * FROM information_schema.table_dependencies
WHERE table_name = 'temp_data';

-- Then drop
DROP TABLE IF EXISTS temp_data;
```

---

### **4.2 Data Migration**
**Update Records in Batch**:
```sql
-- PostgreSQL: Update with a time-based condition
UPDATE accounts
SET last_login = NOW()
WHERE last_login < CURRENT_DATE - INTERVAL '1 year';
```

**Convert Data Type**:
```sql
-- MySQL: Convert ENUM to VARCHAR
UPDATE users
SET role = CAST(role AS CHAR(20))
WHERE role IS NOT NULL;
```

**Migration Validation Query**:
```sql
-- Verify record counts match between old and new schemas
SELECT
    COUNT(*) AS user_count_old,
    (SELECT COUNT(*) FROM users_new) AS user_count_new
FROM users_legacy;
```

---

### **4.3 Zero-Downtime Example**
**Add a Column to a Large Table Without Locking**:
```sql
-- MySQL: Use ONLINE ALTER
ALTER TABLE orders ADD COLUMN shipping_fee DECIMAL(10,2) NULL ONLINE;

-- PostgreSQL: Use pg_repack (requires extension)
CREATE EXTENSION pg_repack;
SELECT pg_repack_table('orders', 'shipping_fee');
```

---

## **5. Related Patterns**
| **Pattern**                     | **Description**                                                                 | **When to Use**                                  |
|---------------------------------|-------------------------------------------------------------------------------|--------------------------------------------------|
| **[CQRS](https://martinfowler.com/bliki/CQRS.html)** | Separate read and write models for scalability.                              | High-read-load systems with complex queries.     |
| **[Event Sourcing](https://martinfowler.com/eaaT/evolving.html)** | Store state changes as a sequence of events.                                  | Audit trails, time-travel debugging.              |
| **[Schema Evolution](https://www.postgresql.org/docs/current/sql-altertable.html)** | Gradually modify schemas without downtime.                                   | Large, frequently updated databases.              |
| **[Database Sharding](https://aws.amazon.com/sharding/)** | Split data across multiple instances for horizontal scaling.                  | Auto-scaling apps with global users.             |
| **[Materialized Views](https://www.postgresql.org/docs/current/materialized-views.html)** | Pre-compute and store query results for performance.                        | Analytics-heavy workloads.                       |
| **[Blue-Green Deployment](https://martinfowler.com/bliki/BlueGreenDeployment.html)** | Switch traffic between identical environments.                              | Feature rollouts with zero downtime.             |

---

## **6. Tools & Libraries**
| **Tool/Library**       | **Database**       | **Key Features**                                                                 |
|------------------------|--------------------|---------------------------------------------------------------------------------|
| **Flyway**             | Multi-database     | SQL-based migrations, rollbacks, version tracking.                               |
| **Liquibase**          | Multi-database     | Change logs (XML/YAML/JSON), diff comparison.                                   |
| **Alembic**            | PostgreSQL/MySQL    | Python-based migrations for SQLAlchemy.                                          |
| **pgAdmin**            | PostgreSQL         | GUI for schema changes (supports migrations).                                   |
| **MySQL Workbench**    | MySQL              | Visual schema editing and migration tools.                                       |
| **AWS Database Migration Service (DMS)** | Multi-database | Near-real-time CDC (Change Data Capture) for large migrations.                  |
| **Debezium**           | Kafka-based        | Real-time data streaming for CDC.                                                 |
| **Hibernate Envers**   | JPA-compatible     | Audit table versions for schema changes.                                          |

---

## **7. Best Practices**
1. **Test in Staging**: Always validate migrations on a production-like environment.
2. **Small, Atomic Changes**: Prefer incremental migrations (e.g., add column > update > alter).
3. **Automate Rollbacks**: Include rollback scripts in your CI/CD pipeline.
4. **Monitor Performance**: Use `EXPLAIN ANALYZE` to optimize migration queries.
5. **Document Changes**: Maintain a `CHANGELOG.md` for schema updates.
6. **Limit Transaction Size**: Break large migrations into smaller transactions to avoid locks.
7. **Use Schema Migrations Over Direct Edits**: Avoid manual `ALTER TABLE` in production.

---
**References**:
- [Flyway Documentation](https://flywaydb.org/documentation/)
- [Liquibase Best Practices](https://docs.liquibase.com/liquibase/continuous-integration.html)
- [PostgreSQL Online DDL](https://www.postgresql.org/docs/current/ddl-ddl.html)
- [Database Migration Service (AWS)](https://aws.amazon.com/dms/)