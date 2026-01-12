---
**[Pattern] Databases Standards Reference Guide**
*Ensure consistency, scalability, and maintainability in database design through standardized conventions, schemas, and practices.*

---

---

### **1. Overview**
This guide outlines the **Databases Standards** pattern, which establishes uniform conventions for database design, schema structure, data integrity, and query practices. By enforcing standards, teams avoid fragmented schemas, reduce refactoring costs, and improve query performance. Key focus areas include:
- **Naming conventions** for tables, columns, and keys.
- **Schema design principles** (e.g., normalization, partitioning).
- **Data type consistency** and validation rules.
- **Query standards** (e.g., parameterized queries, indexing).
- **Documentation and versioning** for schema changes.

This pattern is critical for multi-developer environments, microservices, or teams migrating legacy systems.

---
### **2. Schema Reference**
The following tables define the **core schema standards** for relational databases (e.g., PostgreSQL, MySQL). Adjust for NoSQL if applicable.

#### **2.1 Table Naming Conventions**
| Requirement                | Rule                                                                 | Example               |
|----------------------------|----------------------------------------------------------------------|-----------------------|
| **Format**                 | `lowercase_with_underscores`                                        | `customer_orders`      |
| **Table Purpose**          | Use plural nouns for entities.                                      | `users` (not `user`)  |
| **Avoid Reserved Words**   | Append `_tbl` to reserved words (e.g., `order`).                     | `order_tbl`            |
| **Composite Keys**         | Append `_idx` to composite key tables (e.g., `user_project`).       | `user_project_idx`    |

---

#### **2.2 Column Naming Conventions**
| Requirement                | Rule                                                                 | Example                     |
|----------------------------|----------------------------------------------------------------------|-----------------------------|
| **Format**                 | `lowercase_with_underscores`                                        | `first_name`                |
| **Primary Key (PK)**       | `id` or `{entity}_id` (e.g., `user_id`).                            | `post_id`                   |
| **Foreign Keys (FK)**      | `{referenced_entity}_id` (e.g., `customer_id` in `orders`).        | `department_id`             |
| **Boolean Fields**         | Prefix with `is_` or `has_`.                                       | `is_active`, `has_permission`|
| **Timestamps**             | `created_at`, `updated_at`, `deleted_at` (use `TIMESTAMP` or `DATETIME`). | `created_at`               |
| **Descriptive Names**      | Avoid abbreviations unless standard (e.g., `email_address`).         | `contact_email`            |

---

#### **2.3 Data Types by Use Case**
| Data Type       | Use Case Examples                          | Example Column          |
|-----------------|--------------------------------------------|-------------------------|
| `VARCHAR(n)`    | Text with variable length (max 255 chars). | `user_name` (VARCHAR(50))|
| `TEXT`          | Long text (e.g., descriptions).            | `bio`                   |
| `INT`           | Small integers (e.g., IDs).                | `order_quantity`        |
| `BIGINT`        | Large integers (e.g., unique IDs).         | `user_id`               |
| `FLOAT/DOUBLE`  | Decimal numbers (e.g., prices).            | `unit_price`            |
| `BOOLEAN`       | Yes/no flags.                              | `is_premium`            |
| `DATE`          | Date-only fields.                          | `start_date`            |
| `TIMESTAMP`     | Date + time (with timezone if needed).     | `last_login`            |
| `ENUM`          | Fixed set of values (e.g., status).        | `status` (ENUM: 'active', 'inactive') |
| `JSONB`         | Semi-structured data (PostgreSQL).         | `metadata`              |
| `UUID`          | Unique identifiers (e.g., distributed systems). | `session_token`       |

---

#### **2.4 Constraints and Indexes**
| Requirement                | Implementation Rules                                                                 | Example SQL                     |
|----------------------------|---------------------------------------------------------------------------------------|---------------------------------|
| **Primary Key**            | Always define a single-column or composite key.                                      | `PRIMARY KEY (id)`              |
| **Not Null**               | Mark required fields with `NOT NULL`.                                                | `email VARCHAR(255) NOT NULL`   |
| **Unique Constraints**     | Use `UNIQUE` for values like emails.                                                | `UNIQUE (email)`                |
| **Foreign Keys**           | Enforce referential integrity with `ON DELETE CASCADE` or `ON UPDATE SET NULL`.     | `FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE` |
| **Indexes**                | Create indexes on:
   - Columns in `WHERE`, `JOIN`, or `ORDER BY` clauses.
   - Foreign keys for faster joins.
   - High-cardinality columns.                                                                 | `CREATE INDEX idx_user_email ON users(email);` |
| **Partitioning**           | Partition large tables (e.g., by date or range) to improve query performance.       | See [Partitioning Guide](#partitioning) |

---

#### **2.5 Default Values and Not Null**
| Field Type       | Default Value          | Example                          |
|------------------|------------------------|----------------------------------|
| `BOOLEAN`        | `FALSE`                | `is_active BOOLEAN DEFAULT FALSE` |
| `DATE/TIMESTAMP` | `CURRENT_TIMESTAMP`    | `created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP` |
| `VARCHAR`        | Empty string (`''`)    | `notes VARCHAR(500) DEFAULT ''`   |
| **Not Null**     | Use for core identifiers (e.g., `id`, `email`).                                | `email VARCHAR(255) NOT NULL`   |

---

---
### **3. Query Examples**
#### **3.1 Standardized Query Patterns**
**3.1.1 Parameterized Queries (Security)**
*Avoid SQL injection by using parameters.*
```sql
-- ✅ Safe (parameterized)
PREPARE safe_query AS
SELECT * FROM users WHERE email = $1;
EXECUTE safe_query('user@example.com');

-- ❌ Unsafe (string concatenation)
SELECT * FROM users WHERE email = 'user@example.com'; -- Vulnerable to injection
```

**3.1.2 Join Best Practices**
*Use explicit joins and limit columns for performance.*
```sql
-- ✅ Optimal join (selective columns, explicit JOIN)
SELECT u.id, u.email, o.order_date
FROM users u
INNER JOIN orders o ON u.id = o.user_id
WHERE o.status = 'completed';
```

**3.1.3 Pagination**
*Always paginate results to avoid performance issues.*
```sql
-- ✅ Paginated query (offset + limit)
SELECT * FROM products
ORDER BY name
LIMIT 10 OFFSET 20; -- Page 2, 10 items
```

**3.1.4 Batch Operations**
*Use transactions for multiple writes to maintain consistency.*
```sql
-- ✅ Transaction for batch updates
BEGIN;
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;
COMMIT;
```

**3.1.5 Full-Text Search**
*Leverage database-level full-text indexing for text searches.*
```sql
-- ✅ Full-text search (PostgreSQL example)
CREATE INDEX idx_article_search ON articles USING gin(to_tsvector('english', content));
SELECT * FROM articles WHERE to_tsvector('english', content) @@ to_tsquery('search term');
```

---

#### **3.2 Common Anti-Patterns**
| **Anti-Pattern**               | **Problem**                                  | **Fix**                                  |
|---------------------------------|----------------------------------------------|------------------------------------------|
| `SELECT *`                      | Fetches unnecessary data, slows queries.     | Explicitly list columns.                 |
| Hardcoded values in queries     | Security risks and inflexibility.            | Use parameters.                         |
| No indexes on join/filter columns | Slows down queries.                          | Add indexes.                             |
| ORM-generated inefficient SQL   | Poorly optimized queries.                    | Review raw SQL or use query analyzers.   |
| Ignoring transactions           | Risk of partial updates or races.            | Wrap related operations in transactions. |

---
### **4. Implementation Steps**
#### **4.1 Schema Design Workflow**
1. **Define Entities**: Document all tables and their relationships.
2. **Apply Conventions**: Use naming standards (Section 2.1–2.2).
3. **Choose Data Types**: Align with Section 2.3.
4. **Add Constraints**: Enforce `NOT NULL`, `UNIQUE`, and `FK` rules.
5. **Index Strategically**: Index high-traffic columns (Section 2.4).
6. **Test Performance**: Validate queries with `EXPLAIN ANALYZE`.

#### **4.2 Enforcement Tools**
- **Linters**:
  - [SQLFluff](https://www.sqlfluff.com/) (auto-formats and enforces standards).
  - [dbt (data build tool)](https://www.getdbt.com/) for schema validation.
- **CI/CD Checks**:
  Integrate schema validation into pipelines (e.g., fail builds on naming violations).
- **Documentation**:
  Maintain an up-to-date [ER diagram](https://www.lucidchart.com/pages/er-diagram) or [DBDoc](https://dbdiagram.io/).

#### **4.3 Schema Migration**
- **Version Control**:
  Use tools like:
  - [Flyway](https://flywaydb.org/) (SQL migrations).
  - [Alembic](https://alembic.sqlalchemy.org/) (Python/SQLAlchemy).
- **Backup Before Migrations**: Always test in a staging environment.
- **Downtime Plan**: Schedule migrations during low-traffic periods.

---
### **5. Query Optimization Checklist**
Before deploying a query:
1. **Explain It**: Run `EXPLAIN ANALYZE` to check execution plan.
2. **Check Indexes**: Ensure filters/joins use indexes.
3. **Avoid `SELECT *`**: Fetch only needed columns.
4. **Limit N+1 Queries**: Use joins or subqueries.
5. **Batch Writes**: Group transactions to reduce round trips.
6. **Use Appropriate Data Types**: Avoid `VARCHAR` for large integers.

---
### **6. Related Patterns**
| Pattern                     | Description                                                                 | When to Use                          |
|-----------------------------|-----------------------------------------------------------------------------|--------------------------------------|
| **[Entity-Attribute-Value (EAV)](https://martinfowler.com/eaaCatalog/)** | Flexible schema for dynamic attributes.                                 | Systems with highly variable metadata. |
| **[Sharding](https://martinfowler.com/eaaCatalog/)** | Horizontal database partitioning.                                         | Scaling read/write operations.       |
| **[CQRS](https://martinfowler.com/bliki/CQRS.html)** | Separate read/write models.                                                | High-performance OLTP systems.       |
| **[Snowflake Schema](https://en.wikipedia.org/wiki/Snowflake_schema)** | Normalized schema with many intermediate tables.                          | Data warehousing.                     |
| **[Event Sourcing](https://martinfowler.com/eaaCatalog/eventSourcing.html)** | Store state changes as events.                                             | Audit trails or complex audit logs.   |
| **[Full-Text Search Optimization](https://www.postgresql.org/docs/current/textsearch.html)** | Enhance text search performance.                                          | Content-rich applications.           |

---
### **7. Troubleshooting**
| **Issue**                          | **Root Cause**                          | **Solution**                          |
|------------------------------------|-----------------------------------------|---------------------------------------|
| Slow queries                       | Missing indexes or inefficient joins.   | Add indexes; review `EXPLAIN ANALYZE`. |
| Schema drift                       | Uncontrolled migrations.               | Enforce schema versioning.            |
| Data duplication                  | Lack of constraints or business rules.  | Add `UNIQUE` constraints.             |
| ORM performance bottlenecks        | N+1 queries or lazy loading.            | Batch queries or use `IN` clauses.    |
| Connection pool exhaustion         | Too many open connections.              | Optimize connection timeouts.         |

---
### **8. Further Reading**
- [SQL Standardization Checklist](https://www.percona.com/blog/2013/05/17/sql-standardization-checklist/)
- [Database Performance Tuning](https://use-the-index-luke.com/)
- [PostgreSQL Indexing Guide](https://use-the-index-luke.com/sql/postgres/unique)
- [MySQL Best Practices](https://dev.mysql.com/doc/refman/8.0/en/optimization.html)