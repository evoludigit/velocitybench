# **[Pattern] Database Introspection Strategy – Reference Guide**

---

## **Overview**
The **Database Introspection Strategy** pattern automates schema validation by dynamically inspecting the target database to discover and verify database objects (tables, views, columns, procedures, etc.) referenced in application schemas or mappings. This ensures that schema bindings (e.g., in ORMs, query builders, or migrations) reference valid, existing database objects, reducing runtime errors and enhancing maintainability.

Unlike static schema files (e.g., YAML/SQL scripts) that require manual updates, this pattern bridges the gap between code-generated schemas (e.g., from ORMs) and the actual database state. It is particularly useful in:
- **Mixed environments** (e.g., legacy databases + ORM-generated models).
- **CI/CD pipelines**, where schema changes must pass validation before deployment.
- **Multi-tenant applications**, where schema validation must account for tenant-specific objects.

---

## **Key Concepts**

| **Term**               | **Definition**                                                                 | **Example**                          |
|------------------------|-------------------------------------------------------------------------------|--------------------------------------|
| **Introspection Agent** | A runtime component (e.g., a library or service) that queries the database metadata. | JDBC Metadata API, SQLAlchemy `inspect()`, or a custom script. |
| **Schema Binding**     | A reference in code (e.g., `SELECT * FROM users`) or a configuration (e.g., `orm.models.User`) that links to a database object. | `@Table(name="users")` in an ORM. |
| **Validation Rule**    | A predicate that checks if a schema binding is valid (e.g., table exists, column is non-null). | "Table 'orders' must exist and have a 'user_id' column." |
| **Fallback Strategy**  | A rule for handling discrepancies (e.g., create missing objects, skip, or fail fast). | "Create missing tables but log warnings." |

---

## **Schema Reference**
The pattern relies on **database object metadata** (extracted via introspection) and **schema binding definitions** (user-provided or auto-generated). Below are the core tables/objects involved:

### **1. Database Metadata (Introspected)**
*(Generated dynamically by the introspection agent)*

| **Field**            | **Type**       | **Description**                                                                 | **Example Query**                                                                 |
|----------------------|----------------|---------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| `object_name`        | `VARCHAR`      | Name of the database object (table, view, procedure).                          | `SELECT table_name FROM information_schema.tables;`                              |
| `object_type`        | `ENUM`         | Type (e.g., `TABLE`, `VIEW`, `PROCEDURE`).                                      | `object_type = 'TABLE'`                                                         |
| `schema_name`        | `VARCHAR`      | Schema/namespace (if applicable).                                               | `public` (PostgreSQL), `dbo` (SQL Server).                                      |
| `created_at`         | `TIMESTAMP`    | When the object was created/last modified.                                     | `ALTER TABLE users ADD COLUMN last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP;` |
| `is_temporary`       | `BOOLEAN`      | Flag for temp objects (e.g., `#temp_table#`).                                 | `SELECT is_temporary FROM sys.tables;` (SQL Server)                             |
| `references`         | `JSON`/`ARRAY` | Foreign key dependencies (if tracked).                                          | `{"table": "orders", "column": "user_id"}`                                       |

---
### **2. Schema Binding Definitions**
*(User-provided or auto-generated, e.g., from ORM models)*

| **Field**            | **Type**       | **Description**                                                                 | **Example**                                                                       |
|----------------------|----------------|---------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| `binding_key`        | `VARCHAR`      | Unique identifier for the binding (e.g., `orm.model.User`).                     | `"users"` (table name), `"get_user_by_id"`.                                       |
| `binding_type`       | `ENUM`         | Type of binding (`TABLE`, `COLUMN`, `PROCEDURE`, `VIEW`).                       | `binding_type = 'TABLE'`                                                         |
| `target_object`      | `VARCHAR`      | Name of the referenced database object.                                         | `"users"` (must match `object_name`).                                            |
| `validation_rules`   | `JSON`         | Custom rules (e.g., `{"not_null": ["email"], "max_length": {"name": 100}}`).    | `{"foreign_keys": ["{table: 'orders', column: 'user_id'}"}]`                      |
| `fallback_action`    | `ENUM`         | Behavior on mismatch (`CREATE`, `SKIP`, `FAIL`, `WARNING`).                   | `fallback_action = 'CREATE'` (if table is missing).                               |
| `last_validated`     | `TIMESTAMP`    | When the binding was last validated against the database.                      | `2023-10-01 14:30:00 UTC`.                                                      |

---

## **Query Examples**
### **1. Introspecting Database Objects**
#### **PostgreSQL**
```sql
-- List all tables in the current schema
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_type = 'BASE TABLE';
```
#### **MySQL**
```sql
-- Get columns for a specific table
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'users'
AND table_schema = 'app_db';
```
#### **SQL Server**
```sql
-- Check for foreign key constraints
SELECT
    f.name AS foreign_key,
    OBJECT_NAME(f.parent_object_id) AS parent_table,
    COL_NAME(fc.parent_object_id, fc.parent_column_id) AS parent_column,
    OBJECT_NAME(f.referenced_object_id) AS referenced_table,
    COL_NAME(fc.referenced_object_id, fc.referenced_column_id) AS referenced_column
FROM sys.foreign_keys f
INNER JOIN sys.foreign_key_columns fc ON f.object_id = fc.constraint_object_id
WHERE f.name LIKE '%users%';
```

---
### **2. Validating Schema Bindings**
#### **Pseudocode (Introspection Agent Logic)**
```python
def validate_bindings(database_config, binding_definitions):
    # Step 1: Fetch metadata
    metadata = introspect_database(database_config)

    # Step 2: Check each binding
    for binding in binding_definitions:
        expected_object = binding["target_object"]
        object_type = binding["binding_type"]

        # Look up in metadata
        matching_object = next(
            (obj for obj in metadata
             if obj["object_name"] == expected_object
             and obj["object_type"] == object_type),
            None
        )

        # Step 3: Apply validation rules
        if not matching_object:
            handle_fallback(binding["fallback_action"], binding)
        else:
            validate_rules(matching_object, binding["validation_rules"])

# Example rule: Ensure 'email' is NOT NULL in 'users' table
def validate_rules(object_metadata, rules):
    if "not_null" in rules:
        for column in rules["not_null"]:
            if object_metadata["columns"][column]["is_nullable"] == "YES":
                raise ValidationError(f"Column '{column}' must not be nullable.")
```

---
### **3. Generated SQL for Fallback Actions**
#### **CREATE Missing Table**
```sql
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
#### **ALTER Table to Add Missing Column**
```sql
ALTER TABLE orders
ADD COLUMN user_id INTEGER REFERENCES users(id) NOT NULL;
```

---

## **Implementation Strategies**
| **Strategy**               | **Use Case**                                  | **Pros**                                  | **Cons**                                  |
|----------------------------|-----------------------------------------------|-------------------------------------------|-------------------------------------------|
| **Pre-deployment Check**   | Block deployments with invalid schemas.      | Prevents runtime errors.                  | Slow for large schemas.                   |
| **Lazy Validation**        | Validate only when a binding is used.        | Faster, better for dynamic apps.         | May fail during production traffic.      |
| **Hybrid (Pre + Lazy)**    | Validate critical bindings pre-deployment, lazy for others. | Balances safety and performance.          | Complex to implement.                     |
| **Event-Based**            | Trigger validation on schema changes (e.g., via DB triggers). | Real-time consistency.                  | Requires DB hooks; vendor-specific.       |

---

## **Related Patterns**
1. **[Schema Registry Pattern](https://example.com/schema-registry)**
   - Centralizes schema definitions for consistency across services.
   - *Complementary*: Use introspection to validate against a registered schema.

2. **[Database Migration Pattern](https://example.com/migration-pattern)**
   - Defines a structured way to evolve schemas over time.
   - *Related*: Introspection can detect drift between current and intended schemas.

3. **[ORM-Ware Pattern](https://example.com/orm-ware)**
   - Abstracts ORM-specific code to reduce vendor lock-in.
   - *Related*: Introspection helps generate portable bindings.

4. **[Canary Schema Deployment](https://example.com/canary-deployment)**
   - Gradually rolls out schema changes to a subset of users.
   - *Related*: Introspection validates the canary schema before full rollout.

5. **[Event Sourcing with Schema Validation](https://example.com/event-sourcing)**
   - Validates event payload schemas against the database schema.
   - *Related*: Introspection ensures event data matches referenced tables.

---
## **Best Practices**
1. **Cache Metadata**: Avoid repeated introspection by caching metadata (e.g., for 5 minutes).
2. **Idempotency**: Design fallback actions (e.g., `CREATE TABLE IF NOT EXISTS`) to be idempotent.
3. **Performance**: Limit introspection to critical objects or use sampling for large databases.
4. **Logging**: Track validation results (e.g., `failed_bindings: [{"table": "legacy.users", "reason": "missing_pk"}]`).
5. **Vendor Abstraction**: Use a library (e.g., [JOOQ](https://www.jooq.org/), [DBI](https://github.com/dbi/dbi)) to handle vendor-specific metadata queries.

---
## **Example Workflow**
1. **Developer** defines a binding:
   ```python
   # ORM model (binding definition)
   class User(db.Model):
       __tablename__ = "users"
       id = db.Column(db.Integer, primary_key=True)
       email = db.Column(db.String(255), nullable=False)
   ```
2. **Introspection Agent** runs:
   - Queries PostgreSQL for `users` table.
   - Validates:
     - Table exists.
     - `email` column is not nullable.
     - Primary key `id` exists.
3. **Fallback Action**:
   - If `users` table is missing, it’s created with defaults.
   - If `email` is nullable, a warning is logged (or deployment fails).

---
## **Anti-Patterns to Avoid**
- **Over-introspection**: Querying metadata during every query or transaction (performance bottleneck).
- **Ignoring Fallbacks**: Using `SKIP` for critical objects (e.g., `SKIP` a required foreign key).
- **Static Validation Only**: Relying solely on compile-time checks (database schemas can change).
- **Vendor Lock-In**: Hardcoding vendor-specific queries (e.g., hardcoding `information_schema` paths).

---
## **Tools & Libraries**
| **Tool/Library**          | **Language/DB**       | **Key Features**                                  |
|---------------------------|-----------------------|---------------------------------------------------|
| [JOOQ](https://www.jooq.org/) | Java, Multi-DB         | Type-safe SQL with metadata introspection.        |
| [DBI](https://github.com/dbi/dbi) | Rust                 | Cross-DB metadata queries.                       |
| [SQLAlchemy Inspector](https://docs.sqlalchemy.org/en/14/core/metadata.html#sqlalchemy.schema.inspector) | Python      | Inspect DB schemas in Python.                    |
| [Liquibase](https://www.liquibase.org/) | Multi-Lang          | Schema validation + migration support.            |
| [Flyway](https://flywaydb.org/) | Multi-DB              | Schema validation as part of migrations.          |

---
## **Troubleshooting**
| **Issue**                          | **Cause**                          | **Solution**                                  |
|-------------------------------------|------------------------------------|-----------------------------------------------|
| Introspection fails on large DBs.   | Metadata queries are slow.         | Use `LIMIT` or sample tables.                 |
| Fallback creates incorrect objects. | Missing constraints in fallback SQL. | Use parameterized fallback templates.         |
| False positives in validation.     | Metadata is stale.                 | Invalidate cache on schema changes.            |
| ORM-generated bindings mismatch.    | ORM schema drifts from DB.         | Run introspection after each migration.        |