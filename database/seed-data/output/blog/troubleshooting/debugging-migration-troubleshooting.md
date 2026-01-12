---
# **Debugging Database Migration: A Troubleshooting Guide**

## **Introduction**
Database migrations are a critical part of application development, enabling schema changes, refactoring, and updates. However, migrations can introduce downtime, data corruption, or performance issues. This guide provides a **structured, actionable approach** to diagnosing and fixing common migration-related issues in applications like Rails, Django, or custom SQL-based systems.

---

## **1. Symptom Checklist**
Before diving into fixes, confirm the issue using this checklist:

### **General Symptoms**
✅ **Deployment fails** – Migration rolls back automatically or crashes.
✅ **Application crashes** – Internal Server Error (500) with
   - `ActiveRecord::StatementInvalid` (PostgreSQL)
   - `MySQL Error 1054` (undefined column)
   - `SQLite::ConstraintException`
✅ **Slow performance** – Migrations take abnormally long (>5-10x baseline).
✅ **Data inconsistencies** – Records missing, corrupted, or duplicated.
✅ **Locking issues** – Long-running transactions block other queries.
✅ **Rollback failures** – Migration reverts correctly, but system state is unstable.
✅ **Error logs** – Check:
   - `RAILS_ENV=production rails log/tail production.log` (Rails)
   - `journalctl -u your_app` (Linux)
   - Database logs (`/var/log/mysql/error.log`, `pg_log`)

### **Migration-Specific Checks**
✅ **Migration stack trace** – Look for:
   - `SQL syntax errors` (e.g., missing semicolons in SQL)
   - `Constraint violations` (e.g., `FOREIGN KEY`, `NOT NULL`)
   - `Transaction errors` (e.g., deadlocks, timeouts)
✅ **Schema drift** – Does the new schema match the application’s expectations?
✅ **Partial executions** – Is the migration stuck halfway? (Check `migrations` table.)
✅ **Race conditions** – Are migrations running concurrently on multiple servers?

---

## **2. Common Issues and Fixes**

### **A. Migration Fails on Deployment**
#### **Issue 1: SQL Syntax Error**
**Symptoms:**
- Error: `PG::SyntaxError`, `MySQL Error 1064`
- Migration halves or fails mid-execution.

**Debugging Steps:**
1. **Isolate the failing migration** – Run migrations sequentially:
   ```bash
   rails db:migrate:status  # See which migration failed
   rails db:migrate VERSION=20230101000000
   ```
2. **Check the migration file** – Look for:
   ```ruby
   # Bad: Missing semicolon
   def up
     create_table :users do |t|
       t.string :name
       t.timestamps
   end  # ❌ Missing `end` or parentheses
   ```

**Fix:**
   ```ruby
   def up
     execute <<-SQL
       CREATE TABLE users (
         id SERIAL PRIMARY KEY,
         name VARCHAR(255) NOT NULL
       );
     SQL
   end
   ```

**Tools:**
   - Use `psql` to test raw SQL:
     ```bash
     psql -U postgres -d db_production <<< "SELECT * FROM your_table;"
     ```

---

#### **Issue 2: Foreign Key Constraint Violation**
**Symptoms:**
- Error: `PG::ForeignKeyViolation` or `MySQL Error 1052`
- Application fails to create/insert records referencing missing parent IDs.

**Debugging Steps:**
1. **Check dependencies** – Ensure parent tables exist:
   ```bash
   rails db:migrate:migrate --trace  # Show exact failing line
   ```
2. **Order matters** – Run migrations in correct sequence.

**Fix:**
   - **Option 1:** Disable FK temporarily (if safe):
     ```ruby
     def up
       execute "SET CONSTRAINTS ALL DEFERRED"
       create_table :posts do |t|
         t.references :user, null: false
       end
       execute "SET CONSTRAINTS ALL IMMEDIATE"
     end
     ```
   - **Option 2:** Use `change_table` to add FK *after* data exists.

---

#### **Issue 3: Large Table Creates Locks**
**Symptoms:**
- Migration hangs for minutes/hours.
- Other queries timeout.

**Debugging Steps:**
1. **Check locks** in PostgreSQL:
   ```sql
   SELECT * FROM pg_locks WHERE relation = 'your_table';
   ```
2. **Kill long-running transactions**:
   ```sql
   SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'your_db';
   ```

**Fix:**
   - **For large tables**, consider:
     - Adding indexes in smaller chunks.
     - Using `pg_cron` to run migrations during off-peak hours.
     - Splitting the migration into multiple files.

---

### **B. Data Issues After Migration**
#### **Issue 4: Missing or Corrupted Data**
**Symptoms:**
- Records vanish after migration.
- Application queries return `NULL` for non-nullable fields.

**Debugging Steps:**
1. **Compare schemas** pre- and post-migration:
   ```bash
   rails schema:dump:current  # Compare with old schema
   ```
2. **Check rollback logs** – Does reverting fix the issue?

**Fix:**
   - **If data was lost:**
     - Restore from backup.
     - Use `rails db:rollback` + manual fixes.
   - **If schema changed improperly:**
     ```ruby
     # Ensure referential integrity
     def change
       add_index :posts, :user_id, if_not_exists: true
     end
     ```

---

#### **Issue 5: Race Conditions in Multi-Environments**
**Symptoms:**
- Migration succeeds on staging but fails on production.
- "Table already exists" error.

**Debugging Steps:**
1. **Check migration status** on all servers:
   ```bash
   rails db:migrate:status  # Compare across environments
   ```
2. **Lock migrations** during deployment (Rails):
   ```ruby
   config.database_configuration = YAML.load(File.read("#{Rails.root}/config/database.yml"))
   config.active_record.migrations_lock = true
   ```

**Fix:**
   - **Option 1:** Use `db:migrate:abort_if_pending`.
   - **Option 2:** Deploy migrations in a transaction (PostgreSQL):
     ```ruby
     def up
       ActiveRecord::Base.transaction do
         # Migration logic
       end
     end
     ```

---

## **3. Debugging Tools and Techniques**
### **A. Database-Specific Tools**
| Database  | Tool/Command                          | Use Case                                  |
|-----------|---------------------------------------|-------------------------------------------|
| PostgreSQL| `EXPLAIN ANALYZE SELECT * FROM table;` | Analyze slow queries.                      |
| PostgreSQL| `pgAdmin` / `psql \df`                | View indexes and constraints.              |
| MySQL      | `SHOW CREATE TABLE your_table;`       | Compare schema versions.                  |
| SQLite     | `.schema` in SQLite CLI               | Inspect raw SQL schema.                   |
| All        | `dbdiff` (RubyGem)                    | Compare schemas between environments.      |

### **B. Logging and Monitoring**
- **Rails:**
  ```ruby
  # Enable full migration logs
  config.active_record.migration_logging = :debug
  ```
- **Prometheus + Grafana** – Track migration duration.
- **New Relic / Datadog** – Alert on long-running migrations.

### **C. Testing Strategies**
1. **Unit tests for migrations** (RSpec Example):
   ```ruby
   require 'rails_helper'

   RSpec.describe "MigrationTest", type: :model do
     it "creates indexes correctly" do
       expect { create_table :posts }.to change {
         ActiveRecord::Schema.check_constraints(:posts)
       }.from(false).to(true)
     end
   end
   ```
2. **Use `rails db:migrate:redo` in staging** to test edge cases.
3. **Mock external dependencies** (e.g., Kafka, Redis) during migration tests.

---

## **4. Prevention Strategies**
### **A. Before Writing Migrations**
✔ **Write migrations last** – Schema changes should align with feature development.
✔ **Use `change_table` instead of `add_column`/`remove_column`** where possible.
✔ **Add `down` methods** – Even if trivial, they save time later:
   ```ruby
   def down
     remove_column :posts, :views_count
   end
   ```

### **B. During Development**
✔ **Test migrations locally** – Use `rails db:migrate:reset` to simulate production.
✔ **Use `db:schema:dump`** to validate schema consistency.
✔ **Run migrations in production-like environments** (e.g., Dockerized test DB).

### **C. During Deployment**
✔ **Deploy migrations incrementally** – Avoid "big bang" migrations.
✔ **Use blue-green deployment** – Route traffic to a staging DB first.
✔ **Monitor migration progress** – Add a health check endpoint:
   ```ruby
   # config/routes.rb
   get '/migration_status', to: 'migrations#status'
   ```
   ```ruby
   # app/controllers/migrations_controller.rb
   def status
     @pending = ActiveRecord::Migrator.pending_migrations
     render json: { pending: @pending }
   end
   ```

### **D. Post-Migration**
✔ **Document schema changes** – Add to `CHANGELOG.md`.
✔ **Set up alerts** for failed migrations (e.g., Slack/PagerDuty hooks).
✔ **Revisit migrations** after 24 hours – Some issues appear under load.

---

## **5. Advanced Debugging: Deadlocks and Timeouts**
### **Symptom:**
Migrations hang with no error, but other queries block.

### **Debugging Steps:**
1. **Check for deadlocks** (PostgreSQL):
   ```sql
   SELECT * FROM pg_locks WHERE relation = 'your_table';
   ```
2. **Increase `lock_timeout`** in `database.yml`:
   ```yaml
   production:
     adapter: postgresql
     lock_timeout: 30000  # 30s
   ```
3. **Use `pg_repack` for stuck transactions** (PostgreSQL):
   ```bash
   pg_repack -d your_db -t your_table
   ```

### **Fix:**
   - **Split large migrations** into smaller transactions.
   - **Use `execute` instead of `create_table`** for complex operations:
     ```ruby
     def up
       execute <<-SQL
         ALTER TABLE users ADD COLUMN bio TEXT;
       SQL
     end
     ```

---

## **6. Migration Anti-Patterns**
❌ **Schema changes in production without testing.**
❌ **Running migrations on large tables without indexes.**
❌ **Assuming `down` methods work correctly.**
❌ **Using `change_column` on non-nullable columns without data migration.**
❌ **Ignoring foreign key constraints.**

---

## **7. Final Checklist Before Production**
1. [ ] All migrations are tested in staging.
2. [ ] Rollback plan is documented.
3. [ ] Monitoring is set up for migration duration.
4. [ ] Database backups exist before migration.
5. [ ] No race conditions are anticipated.
6. [ ] `down` methods are verified.

---
**Key Takeaway:**
Migrations are **not rocket science**, but they require discipline. **Test incrementally, log aggressively, and automate rollbacks.** Use this guide as a checklist—spend 80% of your time on prevention and 20% on fixes.

**Happy debugging!** 🚀