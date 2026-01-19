# **Debugging "tb_* Table Naming Prefix" Pattern: A Troubleshooting Guide**
*For Backend Engineers Identifying & Fixing Naming Consistency Issues*

---

## **Introduction**
The **`tb_*` table naming prefix** pattern aims to standardize database table naming for better readability, consistency, and maintenance. However, if misapplied, it can lead to confusion—especially in large systems with multiple schemas, legacy databases, or hybrid (SQL + NoSQL) setups.

This guide helps you **diagnose issues, apply fixes, and prevent regression** in `tb_*` table naming conventions.

---

## **1. Symptom Checklist**
Before diving into fixes, verify if the issue aligns with these common symptoms:

### **✅ Visual & Structural Issues**
- [ ] Tables with `tb_` prefix appear alongside views (e.g., `tb_users`, `vw_users`) but lack clear differentiation in tooling (e.g., PostgreSQL `psql`, MySQL Workbench).
- [ ] Some tables lack the `tb_` prefix (e.g., `users`, `products`), causing inconsistency in naming.
- [ ] Schema exploration (e.g., `information_schema.tables`) reveals mixed `tb_*` and non-named tables.
- [ ] ORM/DBAL (e.g., Doctrine, SQLAlchemy) struggles to auto-map tables with inconsistent prefixes.

### **✅ Functionality & Maintenance Issues**
- [ ] SQL queries fail due to ambiguous table names (e.g., `JOIN tb_users ON users.id`).
- [ ] Backups/restores trigger errors if scripts assume all tables follow `tb_*` (or vice versa).
- [ ] CI/CD pipelines (e.g., schema migrations) fail due to naming inconsistencies.
- [ ] Developers misuse the prefix (e.g., `temporary_tb_logs` instead of `tb_temp_logs`).

### **✅ Tooling & Automation Issues**
- [ ] Database schema generators (e.g., ERD tools) misinterpret `tb_` as a special marker (e.g., temporary tables).
- [ ] Monitoring tools (e.g., Prometheus + SQL exporters) misconfigure due to naming conflicts.
- [ ] CI/CD scripts (e.g., Flyway, Liquibase) skip/break on tables with inconsistent prefixes.

---
## **2. Common Issues & Fixes**
### **Issue 1: "tb_*" Tables Mixed with Views or Non-Prefixed Tables**
**Symptoms:**
- `SELECT * FROM tb_users WHERE id = 1;` works, but `SELECT * FROM users;` fails.
- Schema dumps include `tb_users` and `users` in the same schema.

**Root Cause:**
- Incomplete migration (e.g., old views without `tb_` prefix).
- ORM auto-generation conflicts with manual schema changes.

**Fixes:**
#### **Option A: Standardize All Tables Under `tb_*` (Recommended)**
```sql
-- Rename non-prefixed tables (PostgreSQL example)
ALTER TABLE users RENAME TO tb_users;
ALTER VIEW users_view RENAME TO vw_users;  -- If views exist, keep them as-is
```
**Tools:**
- **Flyway SQL Migrations** (for applied changes):
  ```sql
  -- flyway_v2__003_add_tb_prefix.sql
  RenameTable("users", "tb_users");
  ```
- **Doctrine Schema Tool** (PHP):
  ```php
  $schemaManager->getDatabasePlatform()->renameTable(
      $connection,
      'users',
      'tb_users'
  );
  ```

#### **Option B: Keep Legacy Tables (If Breaking Changes Aren’t Possible)**
Add a **configuration file** (e.g., `db_config.json`) to map old names:
```json
{
  "legacy": {
    "users": "tb_users",
    "products": "tb_products"
  }
}
```
**Usage in Application Code:**
```python
# Python Example (SQLAlchemy)
from sqlalchemy import inspect

table_map = {"users": "tb_users"}
model = inspect(engine).get_table("users")
real_table = table_map.get(model.name, model.name)
query = session.query(real_table)  # Forces corrected table name
```

---

### **Issue 2: ORM Doesn’t Respect `tb_*` Prefix**
**Symptoms:**
- ORM auto-generates `users` table instead of `tb_users`.
- Doctrine/SQLAlchemy fails to find mapped tables.

**Root Cause:**
- ORM configuration (e.g., `mapping_types`) lacks prefix awareness.
- Schema auto-generation overrides manual naming.

**Fixes:**
#### **Doctrine (PHP)**
Update `orm.yaml`:
```yaml
doctrine:
    orm:
        mappings:
            App\Entity:
                type: attribute
                dir: "%kernel.project_dir%/src/Entity"
                is_bundle: false
                prefix: "App\Entity"  # No prefix for classes, but ensure Entity names match `tb_*` tables
        ddl_algorithm: update  # Force schema updates
```
**Table Name Override in Entity:**
```php
use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity(repositoryClass: UserRepository::class)]
#[ORM\Table(name: "tb_users")]
class User { ... }
```

#### **SQLAlchemy (Python)**
Configure table name in model:
```python
from sqlalchemy import Table, MetaData

metadata = MetaData()

users = Table(
    'tb_users',  # Explicit name
    metadata,
    Column('id', Integer, primary_key=True)
)
```
**For Dynamic Models (e.g., EAV):**
```python
def get_table_name(model_class):
    return f"tb_{model_class.__name__.lower()}"
```

---

### **Issue 3: Schema Migrations Fail Due to Prefix Mismatch**
**Symptoms:**
- Flyway/Liquibase complains about "unknown table `users`" during migration.
- Rollbacks break due to naming conflicts.

**Root Cause:**
- Migrations assume all tables follow `tb_*` or none do.
- CI/CD pipelines skip table renames in new deployments.

**Fixes:**
#### **Flyway SQL Migrations**
Ensure all migrations use `tb_*`:
```sql
-- Correct: Uses tb_ prefix
CREATE TABLE tb_orders (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES tb_users(id)
);
```
**For Legacy Tables (if needed):**
```sql
-- temporary workaround (avoid if possible)
CREATE VIEW tb_legacy_users AS SELECT * FROM users;
```

#### **Liquibase XML**
```xml
<changeSet id="rename-users-table" author="dev">
    <renameTable oldName="users" newName="tb_users"/>
</changeSet>
```

---
### **Issue 4: Monitoring/Logging Tools Misinterpret `tb_*`**
**Symptoms:**
- Prometheus SQL exporter fails to query `tb_users` but works for `users`.
- ELK stack indexes logs with incorrect table names.

**Root Cause:**
- Hardcoded queries in monitoring tools don’t account for prefixes.
- Database backups include both `tb_*` and non-prefixed tables.

**Fixes:**
#### **Update Monitoring Queries**
**Example: Prometheus SQL Exporter Config (`prometheus.yml`)**
```yaml
scrape_configs:
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:9090']
        relabel_configs:
          - source_labels: [__address__]
            regex: 'postgres:9090'
            replacement: 'postgres:5432'
            target_label: 'instance'
        metrics_path: '/query'
        params:
          query: |
            SELECT * FROM tb_users;
```
**For Dynamic Table Discovery:**
```sql
-- Generates consistent queries (PostgreSQL)
SELECT 'tb_' || table_name AS tb_table_name
FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
```

#### **Backup Scripts**
Modify `pg_dump` calls:
```bash
# Correct: Explicitly target tb_* tables
pg_dump -h localhost -U postgres -d mydb --schema-only --if-exists \
  --table=tb_users --table=tb_orders > schema_dump.sql
```

---

## **3. Debugging Tools & Techniques**
### **A. Schema Inspection Tools**
| Tool          | Command/Query                          | Purpose                          |
|---------------|----------------------------------------|----------------------------------|
| **PostgreSQL** | `SELECT * FROM information_schema.tables` | List all tables (filter by `tb_*` prefix) |
| **MySQL**      | `SHOW TABLES WHERE ` LIKE 'tb_%'`;`    | Find `tb_*` tables                |
| **SQLAlchemy** | `inspect(engine).get_table_names()`    | Get all tables (check for `tb_*`) |
| **Doctrine CLI** | `php bin/console doctrine:schema:validate` | Check mapping consistency |

**Example Debugging Workflow:**
1. **List inconsistent tables:**
   ```sql
   -- PostgreSQL
   SELECT table_name, table_type
   FROM information_schema.tables
   WHERE table_schema = 'public'
   ORDER BY table_name;
   ```
2. **Compare with expected `tb_*` pattern:**
   ```bash
   # Script to flag missing/malformed prefixes
   grep -v "^tb_" <(psql -Atc "SELECT table_name FROM information_schema.tables") > missing_tables.txt
   ```

---

### **B. CI/CD Pipeline Checks**
Add a **pre-deploy hook** to validate table naming:
**GitHub Actions Example:**
```yaml
- name: Check table naming consistency
  run: |
    TABLES=$(psql -Atc "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    if [[ ! $TABLES =~ ^tb_[a-z_]+$ ]]; then
      echo "Error: Table names must start with 'tb_'"
      exit 1
    fi
```

---

### **C. Database-Specific Tricks**
| Database   | Command to List `tb_*` Tables                          |
|------------|-------------------------------------------------------|
| **PostgreSQL** | `SELECT * FROM information_schema.tables WHERE table_name LIKE 'tb_%';` |
| **MySQL**      | `SHOW TABLES LIKE 'tb_%';`                            |
| **SQL Server** | `SELECT name FROM sys.tables WHERE name LIKE 'tb_%';` |

**Fixing Malformed Prefixes:**
```sql
-- Rename all tables with malformed prefixes (MySQL)
SELECT CONCAT('ALTER TABLE ', table_name, ' RENAME TO tb_', table_name, ';')
FROM information_schema.tables
WHERE table_name NOT LIKE 'tb_%';
```

---

## **4. Prevention Strategies**
### **A. Enforce Naming in Code**
**1. ORM Table Naming Conventions**
- **Doctrine:** Use `@ORM\Table(name: "tb_...")` on entities.
- **SQLAlchemy:** Set `metadata.bind = engine` and explicitly define table names.

**2. Database Schema Generators**
- Configure tools like **Flyway** or **Liquibase** to **always** use `tb_*` prefixes.
- Example Flyway template:
  ```sql
  CREATE TABLE tb_{{ tableName }}
  ```

### **B. Automated Validation**
**1. Database Schema Linter**
Create a script to scan schemas for violations:
```bash
#!/bin/bash
# db_schema_linter.sh
TABLES=$(psql -Atc "SELECT table_name FROM information_schema.tables")
for table in $TABLES; do
  if [[ ! $table =~ ^tb_ ]]; then
    echo "Error: Table '$table' does not follow tb_* prefix."
    exit 1
  fi
done
```
**Integrate into CI:**
```yaml
- uses: actions/checkout@v2
- run: ./db_schema_linter.sh
```

**2. CI/CD Gates**
- **Pre-Merge Checks:** Run the linter on PRs.
- **Post-Deploy Validation:** Use database connections to verify naming.

### **C. Documentation & Team Alignment**
1. **Update Database Docs**
   - Add a **naming conventions** section in your `CONTRIBUTING.md`.
   - Example:
     > **Table Naming:** All tables must use the `tb_` prefix (e.g., `tb_users`). Views should use `vw_`.

2. **Code Reviews**
   - Enforce naming via Git hooks (e.g., **Husky + lint-staged**).
   - Example `.husky/pre-commit` script:
     ```bash
     # Check SQL files for tb_ prefix
     grep -E 'CREATE TABLE[^tb_]' *.sql && echo "Error: Table must use tb_ prefix" && exit 1
     ```

3. **Migration Guardrails**
   - **Never** allow `CREATE TABLE users`—redirect to a migration template.
   - Example Flyway template:
     ```sql
     -- DO NOT EDIT (use tb_ prefix)
     CREATE TABLE tb_{{ tableName }} (
         id SERIAL PRIMARY KEY,
         ${columns}
     );
     ```

---

## **5. Advanced: Handling Hybrid Systems**
If your system mixes `tb_*` (SQL) and non-prefixed (NoSQL/legacy) tables:

### **A. Layered Abstraction**
Use a **repository pattern** to abstract table names:
```python
# Python Example
class UserRepository:
    def __init__(self, db_session, table_prefix="tb_"):
        self.table_name = f"{table_prefix}users"

    def get(self, user_id):
        return db_session.query(self.table_name).filter_by(id=user_id).one()
```

### **B. Dual Schema Strategy**
- **SQL Schema:** All `tb_*` tables.
- **NoSQL/Legacy:** Keep as-is (e.g., `users` in MongoDB).

**Application Logic:**
```python
if database_type == "sql":
    query = session.query("tb_users")  # Use prefix
else:  # NoSQL
    query = mongo.db.users.find_one({"id": user_id})
```

---

## **6. Summary Checklist for Fixes**
| Issue                          | Quick Fix                          | Prevention Tool                     |
|--------------------------------|------------------------------------|-------------------------------------|
| Mixed `tb_*` and non-prefixed    | Rename tables (`ALTER TABLE`)       | CI schema linter                     |
| ORM misconfiguration            | Explicit table names in entities    | Doctrine/SQLAlchemy configs         |
| Migration failures             | Standardize migrations (`tb_*`)     | Flyway/Liquibase templates           |
| Monitoring misqueries           | Update exporter configs             | Dynamic query generators             |
| Team non-compliance             | Git hooks + code reviews            | Husky + lint-staged                  |

---

## **7. Final Notes**
- **Start small:** Fix one schema at a time (e.g., `public` first).
- **Back up first:** Always snapshot schemas before bulk renames.
- **Communicate:** Notify the team of changes to avoid confusion.

By following this guide, you’ll **standardize table naming**, reduce bugs, and future-proof your database schema. 🚀