# **[Pattern] Database Conventions Reference Guide**

---

## **Overview**
This guide establishes standardized conventions for database design, schema naming, query practices, and data integrity to ensure consistency, maintainability, and interoperability across systems. By adhering to these conventions, developers can reduce ambiguity, automate tooling, and improve collaboration. These guidelines cover **naming conventions for objects (tables, columns, indexes), data types, constraints, and query patterns**, as well as best practices for schema evolution and documentation.

---

## **1. Core Principles**
- **Consistency**: Uniformity in naming, structure, and behavior across all databases.
- **Clarity**: Descriptive yet concise identifiers to reflect purpose.
- **Scalability**: Flexible design supporting future growth without refactoring.
- **Interoperability**: Alignment with common industry standards (e.g., ANSI SQL, ORMs).
- **Security**: Enforcement of data integrity and minimal permissions.

---

## **2. Schema Reference**

### **2.1 Object Naming Conventions**
| **Object Type**  | **Naming Convention**                     | **Examples**                          | **Notes**                                                                 |
|------------------|------------------------------------------|----------------------------------------|---------------------------------------------------------------------------|
| **Tables**       | `LowerCamelCase` (plural nouns)          | `users`, `orders`, `product_categories` | Avoid abbreviations unless widely recognized (e.g., `user_profiles`).      |
| **Columns**      | `LowerCamelCase` (single nouns/verbs)    | `user_id`, `created_at`, `is_active`   | Use `is_*` for boolean flags; avoid leading/trailing underscores.          |
| **Indexes**      | `idx_<prefix>_<object>_<column>`        | `idx_user_email`, `idx_order_status`   | Prefix with `idx_` to distinguish from tables/columns.                    |
| **Views**        | `vw_<object>_<purpose>`                 | `vw_user_activity`, `vw_sales_summary` | Avoid generic names like `vw_temp`.                                       |
| **Foreign Keys** | Same as column names (e.g., `order_id`)  | N/A                                   | Use cascading deletes sparingly (prefer `ON DELETE SET NULL`).            |
| **Stored Procedures** | `sp_<verb>_<object>`          | `sp_create_user`, `sp_update_order`    | Avoid generic verbs like `sp_get`; favor `sp_list_*`, `sp_get_*`.        |
| **Functions**    | `fn_<verb>_<object>`                     | `fn_calculate_discount`, `fn_format_date` | Use for reusable logic (e.g., validation, transformations).              |

---

### **2.2 Data Types**
| **Purpose**          | **Recommended Type**       | **Alternatives**                     | **Notes**                                                                 |
|----------------------|---------------------------|--------------------------------------|---------------------------------------------------------------------------|
| **Primary Keys**     | `BIGINT` (auto-increment) | `UUID` (if distributed systems)      | Use `SERIAL` in PostgreSQL; avoid `INT` for large-scale apps.              |
| **Strings**          | `VARCHAR(255)`            | `TEXT` (unbounded), `CHAR` (fixed)   | Prefer `VARCHAR` for variable-length; use `TEXT` for long content (e.g., JSON). |
| **Dates/Times**      | `TIMESTAMP WITH TIME ZONE`| `DATE`, `TIMESTAMP`                  | Avoid `DATETIME` (non-standard); store in UTC.                           |
| **Booleans**         | `BOOLEAN`                 | `TINYINT(1)`                         | Map `1`/`0` to `true`/`false` in app code.                               |
| **JSON Data**        | `JSONB` (PostgreSQL)      | `JSON`, `VARCHAR` (serialized)       | Use `JSONB` for indexing; avoid storing large JSON in `VARCHAR`.         |
| **Enums**            | `ENUM` (PostgreSQL)       | `VARCHAR` with constraints           | Define enums at the database level for validation.                       |
| **Geospatial**       | `GEOGRAPHY` (PostGIS)     | `GEOMETRY`                           | Use `GEOGRAPHY` for distance calculations; `GEOMETRY` for shapes.         |

---

### **2.3 Constraints**
| **Constraint Type**  | **Syntax Example**                     | **Use Case**                          | **Notes**                                                                 |
|----------------------|---------------------------------------|----------------------------------------|---------------------------------------------------------------------------|
| **Primary Key**      | `PRIMARY KEY (id)`                    | Unique identifier for a table.        | Composite keys: `PRIMARY KEY (user_id, team_id)`.                        |
| **Foreign Key**      | `FOREIGN KEY (order_id) REFERENCES orders(id)` | Enforce referential integrity. | Use `ON DELETE CASCADE` sparingly; default to `SET NULL` or `NO ACTION`. |
| **Unique**           | `UNIQUE (email)`                      | Ensure column values are distinct.    | Avoid overusing; use for critical fields like emails.                     |
| **Not Null**         | `NOT NULL`                            | Require non-null values.              | Combine with defaults (e.g., `DEFAULT CURRENT_TIMESTAMP`).              |
| **Default**          | `DEFAULT 'active'`                    | Set default values.                   | Use for non-critical optional fields.                                   |
| **Check**            | `CHECK (age >= 18)`                   | Validate data ranges/patterns.        | Prefer server-side checks over client-side validation.                   |
| **Exclusion**        | `EXCLUDE USING gist` (PostgreSQL)     | Complex constraints (e.g., time slots). | For advanced use cases (e.g., overlapping intervals).                     |

---

### **2.4 Partitioning**
| **Strategy**         | **Use Case**                          | **Implementation Notes**                              |
|----------------------|----------------------------------------|-------------------------------------------------------|
| **Range Partitioning** | Time-series data (e.g., `orders` by `order_date`) | Example: `PARTITION BY RANGE (YEAR(order_date))`.    |
| **List Partitioning** | Fixed categories (e.g., `user_type` in `['admin', 'user']`) | Example: `PARTITION BY LIST (user_type)`.           |
| **Hash Partitioning** | Evenly distribute data (e.g., `logs` by `hash(id)`) | Example: `PARTITION BY HASH (id)`.                   |

**Tools**: Use `pg_partman` (PostgreSQL) or `Azure SQL Partitioning` for automation.

---

## **3. Query Examples**

### **3.1 CRUD Operations**
#### **Insert with Defaults**
```sql
INSERT INTO users (username, email)
VALUES ('jdoe', 'john@example.com')
-- `created_at` and `updated_at` use DEFAULT values.
```

#### **Update with Partial Data**
```sql
UPDATE products
SET price = price * 1.1, is_active = false
WHERE id = 42 AND stock_quantity > 0;
```

#### **Select with Joins**
```sql
SELECT
    u.id,
    u.username,
    o.order_date,
    o.total_amount
FROM users u
JOIN orders o ON u.id = o.user_id
WHERE u.is_active = true
ORDER BY o.order_date DESC
LIMIT 100;
```

#### **Delete with Caution**
```sql
DELETE FROM order_items
WHERE order_id IN (
    SELECT id FROM orders
    WHERE status = 'cancelled' AND created_at < '2023-01-01'
)
-- Use a subquery to avoid mass deletions.
```

---

### **3.2 Advanced Patterns**
#### **Pagination**
```sql
-- PostgreSQL (offset/fetch)
SELECT * FROM posts
ORDER BY created_at DESC
OFFSET 100 LIMIT 20;

-- Keyset pagination (recommended for large datasets)
SELECT * FROM posts
WHERE id < '12345' OR id IS NULL
ORDER BY id DESC
LIMIT 20;
```

#### **Batch Processing**
```sql
-- Update all inactive users older than 6 months
UPDATE users
SET is_active = false
WHERE last_login < CURRENT_DATE - INTERVAL '6 months'
AND is_active = true;
```

#### **Common Table Expressions (CTEs)**
```sql
WITH high_value_orders AS (
    SELECT user_id, SUM(amount) as total_spent
    FROM orders
    WHERE status = 'completed'
    GROUP BY user_id
    HAVING total_spent > 1000
)
UPDATE users u
SET loyalty_tier = 'vip'
FROM high_value_orders hvo
WHERE u.id = hvo.user_id;
```

#### **Full-Text Search**
```sql
-- PostgreSQL (using tsvector/tsquery)
SELECT *
FROM articles
WHERE to_tsvector('english', title || ' ' || content) @@ to_tsquery('search_text');
```

---

### **3.3 Error Handling**
#### **Transaction Rollback on Error**
```sql
BEGIN;
INSERT INTO accounts (user_id, balance)
VALUES (1, -100);
-- If this fails (e.g., negative balance), the transaction rolls back.
COMMIT;
```

#### **Handling Duplicates**
```sql
-- Upsert (PostgreSQL)
INSERT INTO users (id, username)
VALUES (42, 'new_user')
ON CONFLICT (id) DO UPDATE
SET username = EXCLUDED.username;

-- MySQL (INSERT ... ON DUPLICATE KEY UPDATE)
INSERT INTO users (id, username)
VALUES (42, 'new_user')
ON DUPLICATE KEY UPDATE username = VALUES(username);
```

---

## **4. Schema Evolution**
### **4.1 Migration Strategies**
| **Approach**         | **Use Case**                          | **Example**                                  |
|----------------------|----------------------------------------|---------------------------------------------|
| **Alter Column**     | Add/change column types.              | `ALTER TABLE users ADD COLUMN phone VARCHAR(20)`. |
| **Add Column**       | Backward-compatible changes.          | Add `is_premium: BOOLEAN DEFAULT false`.     |
| **Add Table**        | New entity with no breaking changes.   | `CREATE TABLE user_preferences (...)`.       |
| **Refactor Schema**  | Redesign without downtime.            | Use tools like `Flyway` or `Alembic`.        |

**Best Practices**:
- Use **migrations** (e.g., Flyway, Liquibase) for version control.
- **Test migrations** in a staging environment.
- **Document breaking changes** in release notes.

---

### **4.2 Backward Compatibility**
- **Add-only changes**: New columns, tables, or indexes.
- **Optional columns**: Use `DEFAULT` values or nullable fields.
- **Deprecation**: Mark obsolete columns with `DISABLE` (if supported) or add `is_deprecated` flags.

---

## **5. Related Patterns**
- **[Idempotency Pattern]**: Ensure safe retryable operations (e.g., `IF NOT EXISTS` in inserts).
- **[Schema as Code]**: Manage database schemas via version control (e.g., `schema-migrations` folder).
- **[Read Replicas]**: Offload read queries for scalability.
- **[Database Sharding]**: Split data horizontally by range/hash (e.g., `users_1`, `users_2`).
- **[Event Sourcing]**: Store state changes as immutable events (e.g., with `event_history` table).
- **[Materialized Views]**: Pre-computed aggregations (e.g., `vw_daily_sales`).

---

## **6. Tools and Libraries**
| **Category**         | **Tools**                                  | **Notes**                                  |
|----------------------|--------------------------------------------|--------------------------------------------|
| **ORM**              | SQLAlchemy, Django ORM, Entity Framework   | Align with conventions (e.g., `snake_case` for columns). |
| **Migration Tools**  | Flyway, Liquibase, Alembic                 | Automate schema changes.                   |
| **Monitoring**       | Datadog, New Relic, pgAudit               | Track schema/query performance.            |
| **Backup**           | pg_dump (PostgreSQL), mysqldump (MySQL)   | Schedule automated backups.                |
| **Query Analysis**   | pgBadger, SQL Server Profiler             | Optimize slow queries.                     |

---

## **7. Anti-Patterns to Avoid**
- **Schema-less Databases**: Avoid NoSQL for relational data without justification.
- **Over-Partitioning**: Too many partitions increase overhead.
- **Cascading ON DELETE**: Can silently delete related data; prefer `SET NULL`.
- **Hardcoded Values**: Avoid `WHERE status = 1`; use `ENUM` or `VARCHAR` with constraints.
- **Unbounded `TEXT` Columns**: Can bloat storage; limit or use compression.
- **Ignoring Indexes**: Missing indexes on `JOIN`/`WHERE` columns degrade performance.
- **Global Transactions**: Long-running transactions block other operations.

---
**Last Updated**: [Insert Date]
**Maintainers**: [Insert Team/Individual]

---
**Scannable Keywords**: Naming conventions, CRUD, constraints, migrations, CTEs, pagination, partitioning, idempotency, ORM, Flyway, anti-patterns.