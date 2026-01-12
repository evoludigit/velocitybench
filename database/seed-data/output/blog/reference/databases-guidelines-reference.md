---
# **[Pattern] Database Guidelines Reference Guide**

---

## **1. Overview**
This reference guide outlines best practices and implementation details for adhering to **Databases Guidelines** in system design, data modeling, and database operations. The pattern ensures **consistency, scalability, maintainability, and performance** across database schemas, queries, and integrations. It categorizes rules into **naming conventions, schema design, query optimization, security, and backup policies** while providing actionable examples and exceptions where applicable.

Key benefits include:
- **Reduced technical debt** through standardized practices.
- **Faster debugging** via predictable schema structures.
- **Enhanced security** with role-based access controls and data validation.
- **Improved query performance** with indexing strategies and denormalization guidelines.
- **Scalability** via schema partitioning and cloud-ready design principles.

This guide assumes familiarity with **SQL-based databases** (e.g., PostgreSQL, MySQL, SQL Server) or **NoSQL alternatives** (e.g., MongoDB, Cassandra).

---

## **2. Schema Reference**

### **2.1 Core Naming Conventions**
| Category               | Rule                                                                                     | Example                                                                 | Notes                                                                                     |
|------------------------|-----------------------------------------------------------------------------------------|--------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| **Tables**             | Use **snake_case** for table names; avoid plurals unless clarifying collections.       | `user_accounts` (not `users`)                                              | Exceptions: Legacy systems or ER diagrams may use singular/plural conventions.           |
| **Columns**            | **snake_case**, descriptive, and **verb-noun** structure (e.g., `created_at`).          | `user_email`, `order_status_id`                                            | Avoid abbreviations (e.g., use `full_name` instead of `fn`).                             |
| **Primary Keys**       | Auto-incremental integers (`id`) unless domain-specific (e.g., `user_id`).              | `id INT AUTO_INCREMENT PRIMARY KEY`                                        | Composite keys (e.g., `user_id + order_id`) should be prefixed (e.g., `user_order_id`). |
| **Foreign Keys**       | End with `_id`; add `_fk` suffix if manually defined (avoid implicit FKs).               | `order_user_id` (FK to `user_accounts(id)`)                               | Use `ON DELETE CASCADE` for relationships with clear lifecycles (e.g., `order → line_items`). |
| **Enums**              | Use **PascalCase** for enum values; store as `VARCHAR` or `SMALLINT` (if limited).     | `ENUM('PENDING', 'SHIPPED', 'DELIVERED')`                                  | For large enums, consider a lookup table (`status_type`).                                |
| **Indexes**            | Prefix with `idx_`; avoid over-indexing (limit to <3–5 columns per index).              | `CREATE INDEX idx_user_email ON user_accounts(email);`                    | Composite indexes should follow query patterns (most selective columns first).           |
| **Timestamps**         | Use `created_at` and `updated_at`; avoid `timestamp` for business logic.               | `created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` | For timezones, store in UTC and convert client-side.                                      |
| **Booleans**           | Use `IS_TRUE`/`IS_FALSE` or `active/inactive` for clarity over `1/0`.                  | `is_active BOOLEAN DEFAULT FALSE`                                           | Avoid `bit` type; use `BOOLEAN` for readability.                                        |
| **JSON/NoSQL Fields**  | Use `JSONB` (PostgreSQL) or similar for semi-structured data; document schema.         | `metadata JSONB`                                                           | Example: `{"preferences": {"theme": "dark"}}`                                            |
| **Audit Logs**         | Include `changed_at`, `changed_by` (user_id), and `old_value`/`new_value` (if needed).  | Table: `audit_logs(id, table_name, record_id, action, changed_at, user_id)` | For sensitive data, hash `old_value` before storage.                                     |

---

### **2.2 Schema Design Principles**
#### **Normalization vs. Denormalization**
| Rule                          | When to Apply                                                                 | Example                                                                 |
|-------------------------------|------------------------------------------------------------------------------|--------------------------------------------------------------------------|
| **3NF (Third Normal Form)**   | Default for relational databases; reduce redundancy.                         | Avoid repeating `user_name` in `orders`; use a FK to `users(id)`.         |
| **Denormalization**           | Performance-critical read-heavy systems (e.g., analytics, reporting).         | Store `user_name` in `orders` if joins are expensive.                     |
| **Partial Denormalization**   | Store computed fields (e.g., `full_name = concat(first_name, last_name)`).   | Use `generated always as` (PostgreSQL) or triggers.                      |
| **Schema Partitioning**       | Distribute large tables by ranges (e.g., `date`, `user_id`).                | `PARTITION BY RANGE (YEAR(created_at))`                                  |

#### **Table Relationships**
| Relationship Type | Implementation Guidelines                          | Example SQL                                                                 |
|--------------------|----------------------------------------------------|-----------------------------------------------------------------------------|
| **One-to-One**     | Use FK + `UNIQUE` constraint; avoid redundant tables. | `ALTER TABLE user_accounts ADD CONSTRAINT unique_email UNIQUE(email);`    |
| **One-to-Many**    | FK in child table; ensure `ON DELETE CASCADE` if appropriate.              | `orders(user_id INT, user_id INT REFERENCES user_accounts(id) ON DELETE CASCADE)` |
| **Many-to-Many**   | Junction table with composite PKs; add metadata if needed.                 | `order_items(order_id, product_id, quantity, PRIMARY KEY (order_id, product_id))` |
| **Self-Referential** | Use `parent_id` + `id` for hierarchical data (e.g., categories).      | `categories(id, name, parent_id INT REFERENCES categories(id))`            |

---

## **3. Query Examples**

### **3.1 Basic CRUD Operations**
#### **Create**
```sql
-- Insert with defaults
INSERT INTO user_accounts (email, password_hash, created_at)
VALUES ('user@example.com', '$argon2id...', DEFAULT);

-- Upsert (PostgreSQL)
INSERT INTO user_preferences (user_id, theme, NOTIFY_EMAIL)
VALUES (123, 'dark', TRUE)
ON CONFLICT (user_id) DO UPDATE SET theme = EXCLUDED.theme;
```

#### **Read**
```sql
-- Indexed lookup
SELECT id, email, created_at
FROM user_accounts
WHERE email = 'user@example.com'
LIMIT 1;

-- Join with pagination
SELECT u.id, o.order_date, p.product_name
FROM orders o
JOIN users u ON o.user_id = u.id
JOIN products p ON o.product_id = p.id
WHERE o.status = 'PENDING'
ORDER BY o.order_date DESC
LIMIT 10 OFFSET 20;
```

#### **Update**
```sql
-- Batch update with WHERE
UPDATE products
SET price = price * 1.1  -- 10% price hike
WHERE category_id IN (1, 2, 3);

-- Soft delete (status flag)
UPDATE orders
SET status = 'CANCELLED'
WHERE status = 'PENDING'
AND cancelled_by = 'sys_admin';
```

#### **Delete**
```sql
-- Hard delete with cascade
DELETE FROM order_items WHERE order_id = 456;

-- Soft delete (recommended for audit)
UPDATE orders
SET status = 'ARCHIVED'
WHERE order_id = 456;
```

---

### **3.2 Advanced Queries**
#### **Aggregate Functions**
```sql
-- Group by with HAVING
SELECT category_id, COUNT(*) as orders_count
FROM orders
WHERE order_date BETWEEN '2023-01-01' AND '2023-12-31'
GROUP BY category_id
HAVING COUNT(*) > 50;

-- Window functions (PostgreSQL)
SELECT
    user_id,
    order_date,
    SUM(amount) OVER (PARTITION BY user_id) as lifetime_spend,
    RANK() OVER (ORDER BY order_date DESC) as order_rank
FROM order_items;
```

#### **Subqueries and CTEs**
```sql
-- Common Table Expression (CTE)
WITH popular_products AS (
    SELECT product_id, COUNT(*) as sales
    FROM order_items
    GROUP BY product_id
    ORDER BY sales DESC
    LIMIT 10
)
SELECT p.product_name, pp.sales
FROM products p
JOIN popular_products pp ON p.id = pp.product_id;
```

#### **Optimized Joins**
```sql
-- Avoid SELECT *
SELECT u.id, u.email, o.order_date, oi.quantity, p.price
FROM users u
INNER JOIN orders o ON u.id = o.user_id
INNER JOIN order_items oi ON o.id = oi.order_id
INNER JOIN products p ON oi.product_id = p.id
WHERE o.order_date > '2023-01-01'
-- Use explicit join conditions for clarity
-- Avoid implicit joins (no join table specified);
```

#### **Transactions**
```sql
BEGIN TRANSACTION;
-- Transfer funds between accounts (atomic)
UPDATE accounts
SET balance = balance - 100
WHERE id = 123 AND balance >= 100;

UPDATE accounts
SET balance = balance + 100
WHERE id = 456;

-- Commit or rollback
COMMIT;
-- ROLLBACK;  -- Use if an error occurs
```

---

## **4. Security Guidelines**
| Rule                          | Implementation                                                                 | Example                                                                 |
|-------------------------------|-------------------------------------------------------------------------------|--------------------------------------------------------------------------|
| **Input Validation**          | Sanitize all inputs (e.g., reject SQL keywords in user input).               | Use prepared statements (see below).                                     |
| **Prepared Statements**       | Always use parameterized queries to prevent SQL injection.                   | ```sql -- Python (psycopg2)<br>cursor.execute("SELECT * FROM users WHERE email = %s", (user_email,))``` |
| **Least Privilege**           | Grant minimal permissions (e.g., `SELECT` only for read-only roles).          | ```sql<br>GRANT SELECT ON orders TO analytics_role;<br>GRANT INSERT, DELETE ON orders TO admin_role;``` |
| **Column-Level Security**    | Restrict access to sensitive columns (e.g., `password_hash`).                | ```sql<br>ALTER TABLE user_accounts ALTER COLUMN password_hash SET NOT NULL;<br>CREATE POLICY sensitive_data_policy ON user_accounts USING (role_id IN (SELECT id FROM roles WHERE access_level > 1));``` |
| **Data Masking**              | Mask PII (e.g., obfuscate email for non-admins).                             | ```sql<br>CREATE VIEW public.user_profile_masked AS<br>SELECT id, email || '***', created_at FROM user_accounts;``` |
| **Encryption**                | Encrypt sensitive fields (e.g., `credit_card_number` with AES).               | ```sql<br>ALTER TABLE payments ADD COLUMN credit_card_number TEXT ENCRYPTED WITH AES_USING_KEYGEN_FUNCTION('pgp_sym_keygen', 'password');``` |
| **Audit Logging**             | Log all DDL/DML changes to a separate `audit_logs` table.                    | Use triggers or database extensions (e.g., PostgreSQL’s `pgAudit`).       |
| **Backup Policies**           | Schedule automated backups; test restores periodically.                      | ```bash<br>pg_dump -U postgres mydb > /backups/mydb_$(date +%F).sql<br># Schedule with cron: 0 2 * * * /usr/bin/pg_dump ...``` |

---

## **5. Performance Optimization**
| Technique                | Implementation                                                                 | When to Use                                                                 |
|--------------------------|-------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **Indexing**             | Add indexes for frequently queried columns (especially `WHERE`, `JOIN`, `ORDER BY`). | Avoid over-indexing (each index adds write overhead).                       |
| **Covering Indexes**     | Include all columns needed for a query in the index.                          | Example: `CREATE INDEX idx_user_online ON user_accounts(user_id, status, last_seen);` |
| **Partitioning**         | Split large tables by time/range (e.g., `orders` by `YEAR(order_date)`).     | Reduces scan size for time-bound queries.                                   |
| **Denormalization**      | Duplicate data to avoid expensive joins (e.g., store `user_name` in `orders`). | Trades storage for read speed (apply cautiously).                          |
| **Materialized Views**   | Pre-compute expensive aggregations (refresh periodically).                   | PostgreSQL: `CREATE MATERIALIZED VIEW mv_sales_by_category AS ...;`          |
| **Connection Pooling**   | Use pools (e.g., PgBouncer, connection strings) to reuse DB connections.    | Reduces overhead for high-traffic apps.                                    |
| **Batch Operations**     | Use `INSERT ... SELECT` or `UPDATE ... FROM` instead of loops.                | Faster than row-by-row inserts in application code.                          |
| **Query Caching**         | Cache frequent queries (e.g., Redis for read-heavy apps).                   | Example: Cache `SELECT * FROM products WHERE id = X` for 5 minutes.        |
| **Read Replicas**        | Offload read queries to replicas (not production DB).                        | Scales reads but not writes.                                                |

---

## **6. Backup and Recovery**
| Action               | Implementation                                                                 | Frequency                                                                 |
|----------------------|-------------------------------------------------------------------------------|----------------------------------------------------------------------------|
| **Full Backups**     | Dump entire database (logical or physical).                                 | Daily (or hourly for critical data).                                      |
| **Logical Backup**   | Use `pg_dump` (PostgreSQL), `mysqldump` (MySQL), or equivalent.              | ```bash<br>pg_dump -U postgres -Fc mydb > /backups/mydb_full_$(date +%F).dump``` |
| **Physical Backup**  | OS-level snapshots (e.g., `pg_basebackup` for PostgreSQL).                    | Weekly (for large databases).                                              |
| **Transaction Logs**  | Back up WAL (Write-Ahead Log) segments for point-in-time recovery (PITR).    | ```bash<br>pg_basebackup -D /backup_dir -Ft -P -R -Xs -C -v -z -S mydb``` |
| **Point-in-Time Recovery (PITR)** | Restore full backup + apply logs up to desired timestamp.               | Use `pg_restore` or `pg_standby` (PostgreSQL).                            |
| **Test Restores**    | Verify backups restore successfully (e.g., spin up a test DB).             | Monthly or after major schema changes.                                   |
| **Retention Policy** | Delete old backups after 30 days (adjust for compliance).                   | ```bash<br>find /backups -type f -mtime +30 -delete```                      |
| **Disaster Recovery** | Maintain offsite/off-cloud backups (e.g., cloud storage or tape).          | Automate with tools like `AWS Backup` or `Backblaze`.                     |

---

## **7. Related Patterns**
| Pattern                          | Description                                                                                     | When to Combine                                                                 |
|----------------------------------|-------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **[Event Sourcing]**             | Append-only log of state changes; useful for auditing and replayability.                     | Pair with databases for materialized views of state (e.g., `user_profile`).      |
| **[CQRS]**                       | Separate read (query) and write (command) models; denormalize for read paths.                 | Use when read queries are complex or read/write patterns diverge.               |
| **[Schema Migration]**           | Version-controlled schema changes (e.g., Flyway, Alembic).                                   | Automate schema updates for team collaboration.                                  |
| **[Database Sharding]**           | Split data horizontally by key (e.g., `user_id % 10`).                                       | Scale read/write throughput for large user bases.                                |
| **[Connection Pooling]**         | Manage DB connections efficiently (e.g., PgBouncer, HikariCP).                               | Reduce connection overhead in high-traffic apps.                                |
| **[Query Optimization]**         | Analyze slow queries (`EXPLAIN ANALYZE`) and refine indexes/queries.                          | Ongoing maintenance for performance-critical systems.                           |
| **[Data Masking]**               | Protect PII in non-production environments.                                                 | Required for compliance (e.g., GDPR) in test/staging databases.               |
| **[Read Replicas]**              | Scale reads by distributing to replicas.                                                     | Offload reporting/analytics from primary DB.                                  |
| **[Partial Indexes]**            | Index subsets of data (e.g., `WHERE status = 'ACTIVE'`).                                     | Improve performance for filtered queries.                                      |
| **[JSON/NoSQL Hybrid]**          | Use relational DB for structured data + NoSQL for unstructured (e.g., MongoDB subdocuments). | When schema flexibility is needed alongside relational integrity.              |

---

## **8. Anti-Patterns to Avoid**
| Anti-Pattern               | Problem                                                                                     | Solution                                                                         |
|----------------------------|---------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **Schema-less Design**     | No conventions lead to inconsistent naming/structure.                                      | Enforce naming rules and review PRs.                                          |
| **Over-Indexing**          | Too many indexes slow down writes.                                                          | Limit to columns used in `WHERE`, `JOIN`, or `ORDER BY`.                       |
| **Implicit Transactions**  | Uncommitted transactions can cause locks/conflicts.                                       | Explicitly `BEGIN`/`COMMIT`/`ROLLBACK`.                                       |
| **Dynamic SQL**            | SQL injection risk with string concatenation.                                             | Use prepared statements (parameterized queries).                             |
| **Ignoring Indexes**       | Forgetting to update indexes after schema changes.                                        | Document index updates in migration scripts.                                  |
| **No Backup Testing**      | Unreliable backups go unnoticed until disaster strikes.                                   | Schedule regular restore tests.                                               |
| **Hardcoding Credentials** | Secrets in code or configs risk exposure.                                                  | Use environment variables or secret managers (e.g., AWS Secrets Manager).     |
| **Unbounded Transactions** | Long-running transactions block resources.                                                | Keep