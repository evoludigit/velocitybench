---
# **[Pattern] Migration Scripting Reference Guide**
*Automate, track, and manage database schema changes with reusable, version-controlled migration scripts.*

---

## **Overview**
The **Migration Scripting** pattern automates database schema updates by encapsulating changes in reusable, version-controlled **migration scripts** (e.g., SQL files or domain-specific scripts). This approach standardizes schema evolution, enables rollbacks, and ensures consistent deployments across environments (dev, staging, prod).

Key benefits:
- **Auditability**: Track every schema change via versioned scripts.
- **Idempotency**: Scripts can be rerun safely without unintended side effects.
- **Portability**: Works across databases (PostgreSQL, MySQL, MongoDB, etc.) with minimal adaptation.
- **Collaboration**: Team members contribute scripts to a shared repository (e.g., Git).

---
## **Key Concepts**
| Term               | Definition                                                                                                                                                                                                                     |
|--------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Migration Script** | A declarative file (e.g., `001_create_users_table.sql`) defining a single schema change (e.g., `CREATE TABLE`, `ALTER COLUMN`). Scripts are numbered for dependency resolution.                  |
| **Up Migration**    | Applies changes to evolve the database *forward* (e.g., adding a column).                                                                                                                                        |
| **Down Migration**  | Reverts changes to roll back *to a previous state* (critical for undone deployments).                                                                                                                               |
| **Seed Script**     | Populates initial data (e.g., `seed_admin_user.sql`)—distinct from schema migrations.                                                                                                                               |
| **Migration Engine**| A tool (e.g., Flyway, Liquibase, custom script runner) that executes scripts in order, handles errors, and tracks applied migrations (via metadata tables).                                                          |
| **Metadata Table**  | A database table (e.g., `schema_version`) storing applied migration IDs/timestamps to avoid redundant runs.                                                                                                          |
| **Batch Migration** | A set of related scripts (e.g., `2023-05-monolith_to_microservice`) grouped for logical deployments (e.g., a major refactor).                                                                                   |

---

## **Schema Reference**
### **1. Required Metadata Tables**
Each migration engine may use slightly different metadata schemas, but they typically include:

| Column          | Type          | Description                                                                                     |
|-----------------|---------------|-------------------------------------------------------------------------------------------------|
| `version`       | `VARCHAR`     | Migration script filename (e.g., `001_create_users.sql`).                                       |
| `installed_rank`| `INT`         | Order of execution (auto-incremented).                                                          |
| `installed_on`  | `TIMESTAMP`   | When the migration was applied.                                                                |
| `execution_time`| `INT`         | Duration of execution (ms).                                                                |
| `success`       | `BOOLEAN`     | Whether the migration succeeded.                                                              |
| `down_script`   | `VARCHAR`     | Corresponding down migration filename (if applicable).                                         |

**Example (Flyway-style):**
```sql
CREATE TABLE flyway_schema_history (
    installed_rank INT PRIMARY KEY,
    version VARCHAR(100) NOT NULL,
    description VARCHAR(200),
    type VARCHAR(20),
    script VARCHAR(1000),
    check_sum INT,
    installed_by VARCHAR(100),
    installed_on TIMESTAMP,
    execution_time INT,
    success BOOLEAN
);
```

---

### **2. Migration Script Naming Conventions**
| Prefix/Format       | Purpose                                                                                     |
|----------------------|---------------------------------------------------------------------------------------------|
| `001_` (leading zeros)| Ensures numerical ordering (e.g., `001_create_users.sql` runs before `002_add_index.sql`).    |
| `YYYYMMDD_`         | Timestamp-based (e.g., `20230515_add_email_validation.sql`).                               |
| `batch_name_`        | For logical groups (e.g., `2023-05-monolith_to_microservice_v1.sql`).                       |
| `_down.sql`          | Rollback counterpart (e.g., `001_create_users_down.sql`).                                  |

**Best Practice**:
- Limit script length to **1 logical change** (e.g., avoid combining `ALTER TABLE` + `CREATE INDEX` in one file).
- Use **semantic filenames** (e.g., `add_not_null_constraint_to_email.sql` > `update_table.sql`).

---

## **Query Examples**
### **1. Checking Applied Migrations**
**Flyway:**
```bash
# List applied migrations
SELECT * FROM flyway_schema_history ORDER BY installed_rank;
```

**PostgreSQL (Custom Metadata):**
```sql
SELECT version, installed_on FROM schema_versions ORDER BY rank;
```

### **2. Creating a Down Migration**
**SQL (for `001_create_users.sql`):**
```sql
-- Up migration (included in 001_create_users.sql)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

-- Down migration (in 001_create_users_down.sql)
DROP TABLE IF EXISTS users;
```

**Liquibase XML (for a batch):**
```xml
<changeSet id="drop-users-table" author="dev">
    <dropTable tableName="users"/>
</changeSet>
```

### **3. Batch Migration (Liquibase):**
```xml
<changeSet id="microservice-refactor-v1" author="dev">
    <comment>Refactor database for microservices</comment>
    <sqlFile
        path="sql/2023-05-monolith_to_microservice_v1.sql"
        relativeToChangelogFile="true"
        splitStatements="true"/>
</changeSet>
```

### **4. Custom Migration Engine (Python Example)**
```python
import sqlite3
from pathlib import Path

def apply_migrations(db_path: str, migration_dir: str = "migrations"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Initialize metadata table if missing
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS migration_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE,
            executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Process scripts in order
    for script_path in sorted(Path(migration_dir).glob("*.sql")):
        if not script_path.stem.endswith("_down"):
            try:
                with open(script_path) as f:
                    cursor.executescript(f.read())
                cursor.execute(
                    "INSERT INTO migration_history (filename) VALUES (?)",
                    (script_path.name,)
                )
                conn.commit()
                print(f"Applied: {script_path.name}")
            except Exception as e:
                conn.rollback()
                print(f"Failed {script_path.name}: {e}")
    conn.close()
```

---

## **Implementation Steps**
### **1. Set Up the Environment**
- **Metadata Table**: Create a table to track applied migrations (see *Schema Reference*).
- **Migration Directory**: Organize scripts in a folder (e.g., `/migrations` or `/db/migrations`).
- **Migration Engine**: Choose one:
  - **Flyway** (Java-focused, SQL-first)
    ```bash
    # Download Flyway CLI
    curl -sL https://repo1.maven.org/maven2/org/flywaydb/flyway-commandline/9.20.1/flyway-commandline-9.20.1-linux-x64.tar.gz | tar xz
    # Run migrations
    ./flyway -url=jdbc:postgresql://localhost:5432/mydb -user=user -password=pw migrate
    ```
  - **Liquibase** (XML/YAML/JSON support)
    ```bash
    # Install Liquibase
    brew install liquibase
    # Run changesets
    liquibase --url=jdbc:postgresql://localhost:5432/mydb \
              --username=user --password=pw \
              --changeLogFile=db/changelog/db.changelog-master.yml update
    ```
  - **Custom Script**: Write a standalone tool (e.g., Python/Node.js) to parse and execute scripts.

### **2. Write a Migration Script**
**Example (PostgreSQL):**
```sql
-- 002_add_index_to_users.sql
CREATE INDEX idx_users_name ON users(name);
```

**Example (MongoDB with Migrate):**
```javascript
// 003_add_last_login_mongo.js
db.users.updateMany(
    {},
    { $set: { last_login: new Date() } }
);
```

### **3. Apply Migrations**
```bash
# Using Flyway
flyway migrate

# Using custom tool
python migrate.py
```

### **4. Rollback (Critical!)**
```bash
# Flyway rollback (undo last migration)
flyway rollback

# Custom tool (execute down scripts)
python migrate.py --rollback
```

### **5. Seed Data (Separate from Migrations)**
Use scripts prefixed with `seed_` (e.g., `seed_admin_user.sql`):
```sql
-- seed_admin_user.sql
INSERT INTO users (id, name, is_admin)
VALUES (1, 'Admin User', true);
```
Run seeds **only after all migrations** apply.

---

## **Best Practices**
| Guideline                          | Reason                                                                                     |
|------------------------------------|-------------------------------------------------------------------------------------------|
| **Idempotent Scripts**             | Scripts should succeed when rerun (e.g., use `IF NOT EXISTS` for tables).                 |
| **Unit Test Migrations**           | Validate scripts with tools like [SQLFluff](https://www.sqlfluff.com/) or custom tests.   |
| **Small, Atomic Changes**          | 1 script = 1 logical change (e.g., don’t combine `ALTER TABLE` + `CREATE INDEX`).        |
| **Document Dependencies**          | Use comments in scripts to explain pre/post-requisites.                                    |
| **Test Rollbacks**                 | Verify down migrations work in staging before prod.                                        |
| **Exclude in Git**                 | Never commit raw data (seeds) or sensitive scripts (use `.gitignore`).                    |
| **Environment Params**             | Use placeholders (`${DB_NAME}`) and environment variables for config.                     |
| **Backup Before Migrations**       | Critical for production; use tools like `pg_dump` or `mysqldump`.                        |
| **Monitor Execution Time**         | Long-running migrations may block services; log durations.                                |

---

## **Common Pitfalls & Solutions**
| Pitfall                          | Solution                                                                                     |
|----------------------------------|---------------------------------------------------------------------------------------------|
| **Orphaned Migrations**          | Always check `SELECT COUNT(*) FROM migration_history` before running scripts.            |
| **Race Conditions**              | Use database locks during migrations (e.g., Flyway’s `--out-of-order` flag).               |
| **Down Migrations Fail**         | Test rollbacks in staging; ensure scripts are reversible (e.g., don’t `DROP TABLE` if data is needed). |
| **Migration Order Issues**       | Use strict numerical prefixes or timestamp-based names.                                      |
| **Cross-Database Portability**   | Write scripts in a subset of SQL (PostgreSQL/MySQL common syntax) or use tools like [DbSchema](https://www.dbschema.com/). |

---

## **Related Patterns**
| Pattern                     | Description                                                                                     | When to Use                                                                                     |
|-----------------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Feature Flags**           | Gradually roll out schema changes to users while testing.                                       | Large-scale deployments where unscheduled downtime is risky.                                    |
| **Database-as-a-Service (DBaaS)** | Offload migrations to managed services (e.g., AWS RDS, Supabase).                              | Reduces operational overhead for non-critical projects.                                         |
| **Schema Versioning**       | Treat schema changes like code versions (e.g., semantic versioning: `v1.2.0`).                  | Projects with frequent breaking changes (e.g., microservices).                                  |
| **Event Sourcing**          | Store schema history as an audit log of events (alternative to metadata tables).               | Systems requiring immutable audit trails (e.g., finance).                                       |
| **Canary Deployments**      | Test migrations on a subset of traffic before full rollout.                                    | Production environments where downtime is unacceptable.                                        |
| **Schema Migrations + ORM**  | Use tools like Django’s `makemigrations` or Prisma to auto-generate migration scripts.         | Projects already using an ORM where manual SQL feels tedious.                                   |

---

## **Tools & Libraries**
| Tool/Library          | Language/DB   | Key Features                                                                                     |
|-----------------------|---------------|-------------------------------------------------------------------------------------------------|
| **Flyway**            | Java/SQL      | SQL-first, supports rollbacks, plugins for many DBs.                                             |
| **Liquibase**         | Multi-language| YAML/XML/JSON support, change sets, rollback testing.                                            |
| **Alembic**           | Python        | SQLAlchemy integration, transactional migrations.                                                 |
| **Migrate**           | Node.js       | MongoDB/PostgreSQL/SQLite, promises-based API.                                                    |
| **DbMig**             | Java          | Lightweight, supports down migrations.                                                          |
| **Laravel Migrations**| PHP           | Artisan CLI, rollbacks, and batch migrations.                                                    |
| **Custom Scripts**    | Any           | Full control; use for niche databases (e.g., DynamoDB).                                        |

---
## **Further Reading**
- [Flyway Documentation](https://flywaydb.org/documentation/)
- [Liquibase ChangeLog Format](https://www.liquibase.org/documentation/changelog-reference.html)
- ["Database Migrations with Node.js" (Migrate)](https://www.npmjs.com/package/migrate)
- ["Idempotent Migrations" (PostgreSQL)](https://www.citusdata.com/blog/2021/05/18/idempotent-migrations-postgresql/)
- ["Schema Evolution at Scale" (Google)](https://engineering.fb.com/2019/04/22/data-engineering/schema-evolution-at-facebook/)