# **[Pattern] Schema Migration Strategy Reference Guide**

---

## **Overview**
The **Schema Migration Strategy** pattern ensures backward compatibility and safe evolution of database schemas across application versions. By systematically managing schema changes, this pattern minimizes downtime, prevents data corruption, and accommodates incremental updates without breaking existing functionality. It’s particularly critical in distributed systems, microservices, or applications with versioned data persistence (e.g., PostgreSQL, MongoDB, or custom databases). The pattern balances automation (e.g., migrations) with manual oversight (e.g., cutover windows) and supports **zero-downtime** operations where possible.

---

## **Key Concepts and Implementation Details**

### **1. Core Principles**
- **Backward Compatibility**: New versions of the application must read data written by older versions.
- **Forward Compatibility**: Older versions must write data that newer versions can interpret (if possible).
- **Atomic Migrations**: Schema changes are applied in transactions to avoid partial updates.
- **Idempotency**: Migrations should be repeatable without adverse effects (e.g., adding a NOT NULL column twice).
- **Versioning**: Track schema state with a `schema_version` table or metadata field.

### **2. Migration Strategies**
| Strategy               | Use Case                                  | Pros                                  | Cons                                  |
|------------------------|------------------------------------------|---------------------------------------|---------------------------------------|
| **Migration Scripts**  | One-time schema changes (e.g., adding a column). | Simple, deterministic.               | Manual execution risk; no rollback.   |
| **Zero-Downtime**      | Critical services (e.g., read replicas). | High availability.                    | Complex; requires dual-write/read paths. |
| **Feature Flags**      | Gradual rollout (e.g., optional columns). | Low risk; canary testing.             | Adds application complexity.          |
| **Schema Aliasing**    | Legacy data access.                      | Preserves old queries.                | Storage overhead.                     |
| **Deprecation**        | Sunsetting old fields.                    | Clean separation.                     | Requires coordination.                |

### **3. Migration Lifecycle**
1. **Design**: Plan changes with impact analysis (e.g., ALTER TABLE vs. CREATE TABLE AS).
2. **Test**: Validate in staging with:
   - **Schema validation tools** (e.g., Flyway, Liquibase).
   - **Integration tests** for backward/forward compatibility.
3. **Deploy**: Use CI/CD pipelines to automate migrations (e.g., Git hooks).
4. **Monitor**: Log migration failures and rollback if needed.
5. **Cutover**: For zero-downtime, promote to production during low-traffic periods.

### **4. Zero-Downtime Techniques**
- **Dual-Write**: Write to both old and new schemas until cutover (e.g., using triggers or application logic).
- **Shadow Schema**: Serve new data via a parallel schema; switch traffic gradually.
- **Read Replicas**: Migrate replicas first, then promote.

### **5. Handling Data Schema Evolution**
| Evolution Type       | Example                          | Strategy                          |
|---------------------|----------------------------------|-----------------------------------|
| **Column Addition** | Add `last_updated_at` timestamp. | Use `ALTER TABLE ADD COLUMN`.     |
| **Column Removal**  | Drop deprecated `legacy_id`.     | **Avoid** (use aliases instead).  |
| **Column Type Change** | Change `VARCHAR(255)` to `TEXT`. | Use a temporary column during cutover. |
| **Table Renaming**  | Rename `users` to `customers`.   | Redirect writes/reads via app logic. |
| **Partitioning**    | Split large tables.              | Batch migrations during off-peak.  |

---

## **Schema Reference**
Below is a reference for a `schema_version` table to track migrations (adaptable to your DBMS).

| Field            | Type         | Description                                                                 | Example                     |
|------------------|--------------|-----------------------------------------------------------------------------|-----------------------------|
| `id`             | `BIGSERIAL`  | Unique migration ID.                                                        | `1`                         |
| `version`        | `VARCHAR(50)`| Semantic version (e.g., `1.2.3`).                                           | `"2.1.0"`                   |
| `description`    | `TEXT`       | Migration purpose (e.g., "Add `status` column").                           | `"Add support for soft deletes."` |
| `sql`            | `TEXT`       | Migration script (or reference URL).                                        | `"ALTER TABLE users ADD COLUMN status VARCHAR(20);"` |
| `applied_at`     | `TIMESTAMP`  | When the migration ran.                                                     | `"2023-10-01 14:30:00"`    |
| `applied_by`     | `VARCHAR(50)`| User/process that executed it.                                               | `"migration-bot"`           |

**SQL Example (PostgreSQL):**
```sql
CREATE TABLE schema_migrations (
    id SERIAL PRIMARY KEY,
    version VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    sql TEXT,
    applied_at TIMESTAMP DEFAULT NOW(),
    applied_by VARCHAR(50)
);
```

---

## **Query Examples**

### **1. List Applied Migrations**
```sql
-- PostgreSQL
SELECT * FROM schema_migrations ORDER BY applied_at DESC;
```

### **2. Check Unapplied Migrations**
```sql
-- Compare against a list of expected versions (e.g., from config)
SELECT version FROM schema_migrations
WHERE version NOT IN ('1.2.0', '2.1.0');
```

### **3. Rollback to a Specific Version**
```sql
-- Reverse migrations (e.g., drop a column)
BEGIN;
  -- Execute reverse SQL (stored in a `rollback_sql` column if available)
  ALTER TABLE users DROP COLUMN IF EXISTS status;
  DELETE FROM schema_migrations WHERE version = '2.1.0';
COMMIT;
```

### **4. Zero-Downtime Migration (Add Column)**
```sql
-- Step 1: Add a temporary column
ALTER TABLE users ADD COLUMN status_temp VARCHAR(20);

-- Step 2: Dual-write logic in application (e.g., fill `status_temp` before writing)
-- Example app code (pseudo):
for user in db.users.select():
    user.status_temp = "active"
    db.users.update(user)

-- Step 3: Drop old column, rename temp column
ALTER TABLE users DROP COLUMN IF EXISTS status;
ALTER TABLE users RENAME COLUMN status_temp TO status;
```

---

## **Related Patterns**

| Pattern                     | Purpose                                                                 | Integration Notes                                                                 |
|-----------------------------|-------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| **CQRS**                    | Separate read/write schemas.                                            | Schema migrations can target read models independently.                          |
| **Event Sourcing**          | Audit schema changes via domain events.                                 | Log schema versions as events for replayable migrations.                          |
| **Database Sharding**       | Distribute schema changes across shards.                               | Coordinate migrations across all shards (e.g., using consensus protocols).      |
| **Schema Aliasing**         | Maintain backward compatibility.                                        | Combine with migrations to phase out old schemas.                               |
| **Feature Toggles**         | Gradually enable new schema features.                                  | Use toggles to control writes to new schema fields.                              |
| **Blue-Green Deployment**   | Swap schemas with zero downtime.                                       | Requires dual databases with identical schemas.                                 |

---

## **Best Practices**
1. **Automate Testing**: Use tools like [Flyway](https://flywaydb.org/) or [Liquibase](https://www.liquibase.org/) to validate migrations.
2. **Small Batches**: Prefer 1–2 schema changes per migration to simplify rollbacks.
3. **Document Risks**: Note potential data loss (e.g., dropping columns) in migration descriptions.
4. **Monitor Performance**: ALTER operations can lock tables; schedule during low traffic.
5. **Rollback Plan**: Always define a rollback strategy (e.g., `DROP TABLE ... IF EXISTS`).
6. **Audit Logs**: Track migrations with timestamps and responsible users for accountability.

---
## **Anti-Patterns**
- **Big Bang Migrations**: Avoid massive schema changes with no rollback path.
- **Ignoring Backward Compatibility**: New versions must read old data without errors.
- **Hardcoded Schema Assumptions**: Use ORMs/DTOs to abstract schema details.
- **Unversioned Migrations**: Manual `ALTER` commands without tracking risk data loss.

---
**See Also**:
- [Database Change Management](https://martinfowler.com/articles/database-change-management.html) (Martin Fowler)
- [PostgreSQL: Schema Migration Best Practices](https://www.postgresql.org/docs/current/sql-altertable.html#SQL-ALTERTABLE-ALTER-COLUMN)