# **[Pattern] Database Migration Strategies – Reference Guide**

---
## **1. Overview**
Database migrations are controlled, version-tracked modifications to a database schema that enable safe **schema evolution** (adding, modifying, or removing tables/columns) without downtime or data loss. When executed poorly, migrations can cause:
- **Downtime** during deployments
- **Data corruption** due to race conditions
- **Failed rollbacks** or orphaned migrations

This reference guide covers **proven strategies**—including **expand-contract**, **online schema changes (OSC)**, and **blue-green deployments**—to apply migrations safely in production. Best practices include **atomic transactions**, **idempotency**, and **rollback planning**.

---

## **2. Core Concepts & Implementation**

### **2.1 Key Principles**
| **Principle**               | **Description**                                                                 | **Example**                                                                 |
|-----------------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Atomicity**               | Migrations must succeed fully or not at all.                                  | Wrap changes in a transaction.                                             |
| **Idempotency**             | Repeating a migration should have no side effects.                            | Use `IF NOT EXISTS` for table creation.                                     |
| **Version Control**         | Migrations are tracked in Git (e.g., `migrations/20240101_add_index.sql`).   | `git tag v1.2.3` → Apply `migrations/v1.2.3/` to sync.                      |
| **Rollback Planning**       | Every migration must define a reversal step.                                 | Add `rollback.sql` or `reverse()` logic.                                   |
| **State Tracking**          | Avoid reprocessing migrations (use a `schema_migrations` table).              | Track applied versions in a DBMS-specific table.                           |

---

### **2.2 Migration Lifecycle**
1. **Author**: Write migration files in a structured format (see **Schema Reference**).
2. **Test**: Validate migrations on a staging environment with real data.
3. **Apply**: Run migrations via a **Migration Runner** (e.g., Flyway, Liquibase, Django’s `makemigrations`).
4. **Monitor**: Log success/failure and alert on failures.
5. **Rollback**: Execute reverse migrations if needed.

---
## **3. Schema Reference**

### **3.1 Migration File Structure**
Each migration follows this template (SQL example):
```sql
-- migrations/20240101_add_users_table.sql
BEGIN TRANSACTION;

-- Up migration (create table)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
) COMMENT 'User accounts';

INSERT INTO schema_migrations (version, applied_at, migration_file)
VALUES ('20240101_add_users_table', NOW(), 'migrations/20240101_add_users_table.sql');

COMMIT;

-- migrations/reverse_20240101_add_users_table.sql
BEGIN TRANSACTION;

DROP TABLE users;

DELETE FROM schema_migrations WHERE version = '20240101_add_users_table';

COMMIT;
```

---

### **3.2 Core Tables (Example)**
| Table Name          | Description                                                                 | Columns                                                                     |
|---------------------|-----------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| `schema_migrations` | Tracks applied migrations to prevent reprocessing.                         | `version` (VARCHAR), `applied_at` (TIMESTAMP), `migration_file` (VARCHAR) |
| `database_lock`     | Ensures only one migration process runs at a time (optional).              | `lock_id` (INT), `locked_at` (TIMESTAMP)                                   |

---
## **4. Query Examples**

### **4.1 Apply a Migration (PostgreSQL)**
```sql
-- Using a script (simplified)
DO $$
DECLARE
    migration_file RECORD;
BEGIN
    -- Fetch next unapplied migration
    FOR migration_file IN
        SELECT name FROM pg_catalog.pg_class
        WHERE relnamespace = 'migrations_schema'::regnamespace
        AND relkind = 'r'
        ORDER BY name ASC LOOP
        -- Execute migration logic
        EXECUTE migration_file.name;
        -- Mark as applied
        INSERT INTO schema_migrations (version, applied_at, migration_file)
        VALUES (migration_file.name, NOW(), migration_file.name);
    END LOOP;
END $$;
```

### **4.2 Expand-Contract Pattern (Example)**
**Step 1: Expand (Add New Column)**
```sql
ALTER TABLE users ADD COLUMN email VARCHAR(255);
-- Add default value for existing rows (nullable)
UPDATE users SET email = NULL WHERE email IS NULL;
```

**Step 2: Contract (Drop Old Column)**
```sql
ALTER TABLE users DROP COLUMN old_email;
```

**Step 3: Rollback (Reverse Contract)**
```sql
ALTER TABLE users ADD COLUMN old_email VARCHAR(255) GENERATED ALWAYS AS (email) STORED;
```

---
## **5. Migration Strategies**

### **5.1 Expand-Contract Pattern**
**Use Case**: Making breaking changes (e.g., renaming a column) without downtime.
**Steps**:
1. **Expand**: Add the new column/field.
2. **Migrate Data**: Populate the new column from the old one.
3. **Contract**: Drop the old column/field.
4. **Rollback**: Restore the old column with data.

**Pros**:
- Zero downtime.
- Testable in staging.

**Cons**:
- Requires double storage temporarily.
- Complex for large datasets.

---
### **5.2 Online Schema Changes (OSC)**
**Use Case**: Large tables where downtime is unacceptable (e.g., e-commerce databases).
**Tools**:
- **PostgreSQL**: `pg_repack`, `pg_partman`
- **MySQL**: `ALTER TABLE ... ALGORITHM=INPLACE`
- **ORM Tools**: Django’s `schema editor`, Rails’ `ActiveRecord::SchemaMigration`

**Example (PostgreSQL OSC)**:
```sql
-- Add column without locking the table
ALTER TABLE orders ADD COLUMN shipping_address TEXT;
-- Trigger a vacuum to reindex
VACUUM (VERBOSE, ANALYZE) orders;
```

**Pros**:
- Minimal downtime.
- Works for large tables.

**Cons**:
- Requires careful planning.
- May need tooling support.

---
### **5.3 Blue-Green Deployment**
**Use Case**: Zero-downtime schema changes for high-traffic systems.
**Steps**:
1. Deploy a **green database** with the new schema.
2. Route **new traffic** to the green DB while keeping old traffic on **blue**.
3. Once verified, switch traffic to green and discard blue.
4. Rollback: Traffic reverts to blue if issues arise.

**Tools**:
- **Database Replication**: PostgreSQL streaming replication, MySQL binlog.
- **Proxy Routers**: NGINX, HAProxy for traffic switching.

**Pros**:
- No downtime.
- Easy rollback.

**Cons**:
- Double storage overhead.
- Complex setup.

---
## **6. Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                                  |
|---------------------------|-------------------------------------------------------------------------------|--------------------------------------------------|
| **Feature Flags**         | Gradually roll out schema changes to users.                                     | Canary releases.                                 |
| **Database Sharding**     | Split data across servers to parallelize migrations.                          | Horizontal scalability.                         |
| **Event Sourcing**        | Use event logs (e.g., Kafka) to rebuild state after migrations.              | Audit trails, complex rollbacks.                |
| **Schema-as-Code**        | Define schemas in code (e.g., Prisma, Entity Framework) instead of SQL.     | Microservices, IaC.                             |

---
## **7. Anti-Patterns to Avoid**
| **Anti-Pattern**          | **Problem**                                                                 | **Fix**                                      |
|---------------------------|-----------------------------------------------------------------------------|-----------------------------------------------|
| **Direct `ALTER TABLE`**  | Locks the table during changes (downtime).                                  | Use OSC or expand-contract.                  |
| **No Rollback Plan**      | Broken migrations brick the database.                                      | Always include `reverse.sql`.                |
| **Migrations in Production** | Manual SQL risks data loss.                                               | Automate via CI/CD (e.g., GitHub Actions).   |
| **Skipping Version Control** | Untracked migrations lead to divergence between environments.          | Commit migrations to Git with tags.         |

---
## **8. Tools & Libraries**
| **Tool**                  | **Database**  | **Key Features**                              | **Link**                                    |
|---------------------------|--------------|-----------------------------------------------|---------------------------------------------|
| **Flyway**                | All          | Simple SQL-based migrations, rollbacks.        | [flyway.io](https://flyway.io)              |
| **Liquibase**             | All          | XML/YAML/JSON migrations, change sets.        | [liquibase.org](https://liquibase.org)       |
| **Django Migrations**     | PostgreSQL   | Pythonic schema migrations.                   | [docs.djangoproject.com](https://docs.djangoproject.com) |
| **Prisma Migrations**     | PostgreSQL   | Type-safe migrations for Prisma ORM.          | [prisma.io](https://prisma.io)              |
| **AWS Database Migration**| All          | Cloud-managed migrations (RDS → Aurora).      | [aws.amazon.com/dms](https://aws.amazon.com/dms) |

---
## **9. Best Practices Checklist**
1. [ ] **Test migrations** in a staging environment identical to production.
2. [ ] **Use transactions** to ensure atomicity.
3. [ ] **Document rollbacks** for each migration.
4. [ ] **Monitor migration jobs** (e.g., Prometheus alerts).
5. [ ] **Freeze production schema** during critical deployments.
6. [ ] **Back up the database** before applying migrations.
7. [ ] **Limit migration duration** (e.g., 5-minute timeouts).
8. [ ] **Automate testing** (e.g., integration tests for migrations).

---
## **10. Further Reading**
- [PostgreSQL Online Schema Changes](https://wiki.postgresql.org/wiki/Online_schema_change)
- [Flyway Docs: Expand-Contract Pattern](https://flywaydb.org/documentation/patterns/expandcontract/)
- [Database Migration Anti-Patterns (InfoQ)](https://www.infoq.com/articles/database-migration-anti-patterns/)