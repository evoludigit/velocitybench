**[Pattern] Function Naming Convention (fn_*) – Reference Guide**

---

### **Overview**
FraiseQL enforces a strict **`fn_*` prefix** naming convention for database functions and stored procedures to ensure consistency, readability, and explicit intent. Functions follow the pattern **`fn_{action}_{entity}`** (e.g., `fn_create_user`, `fn_delete_order`), where:
- **`fn_`** denotes a persistence operation (versus a utility or scalar function).
- **`{action}`** describes the operation (e.g., `create`, `update`, `validate`).
- **`{entity}`** references the database table or domain object (e.g., `user`, `post`).

This pattern supports:
✔ **Semantic clarity** – Matches intent (e.g., `fn_publish_article` signals mutation).
✔ **Mutation tracking** – Prefix distinguishes CRUD operations from read-only queries.
✔ **Automation support** – Easily parseable by build tools for migration scripts or ORMs.

---

### **Schema Reference**
The convention applies to all stored functions/procedures. Below are key components:

| Component       | Description                                                                 | Example                          |
|-----------------|-----------------------------------------------------------------------------|----------------------------------|
| **Prefix**      | Required `fn_` to identify persistence logic.                                 | `fn_`                            |
| **Action**      | Verb describing the DB operation (case-preserved; plural if applicable).    | `create`/`update`/`validate`     |
| **Entity**      | Noun mapping to a database table or entity (PascalCase for complex types).   | `user`/`post_comment`            |
| **Parameters**  | Inline with SQL (e.g., `IN`, `OUT`) or documented in a schema definition. | `fn_update_user(IN id INT)`       |
| **Return Type** | Explicit for scalar functions; implicit (no return) for procedures.           | `fn_get_user_count() RETURNS INT`|

**Reserved Actions**:
- `get`/`select` – Read-only queries (use if no mutation occurs).
- `create`/`insert` – Add records (avoid `new`).
- `update`/`modify` – Confirm table updates, not application logic.
- `delete`/`remove` – Hard deletion (use `fn_soft_delete` for soft deletes).
- `validate`/`check` – Logic-heavy functions (e.g., `fn_validate_email`).

**Restrictions**:
- No hyphens or underscores in `{action}` or `{entity}` (use camelCase only).
- Avoid generic names like `fn_save` or `fn_process`—be specific.
- Prefer `fn_update_*` over `fn_save_*` for mutative functions.

---

### **Query Examples**
#### **1. Standard CRUD Operations**
```sql
-- Create
CREATE FUNCTION fn_create_user(
    IN email VARCHAR(255),
    IN password_hash VARCHAR(255)
) RETURNS INT
BEGIN
    INSERT INTO users (email, password_hash) VALUES (email, password_hash);
    RETURN LAST_INSERT_ID();
END;

-- Update
CALL fn_update_post(1, 'New title', 'Revised content');

-- Delete
CALL fn_delete_order(101);
```

#### **2. Read-Only Queries**
```sql
-- Note: Prefix with `fn_get` to indicate no mutation
SELECT * FROM fn_get_user_by_id(1);
```

#### **3. Complex Actions**
```sql
-- Composite actions (e.g., transfer funds)
CREATE PROCEDURE fn_transfer_funds(
    IN from_account INT,
    IN to_account INT,
    IN amount DECIMAL(10,2)
) BEGIN
    -- Atomic transaction logic
END;

-- Validation function
SELECT * FROM fn_validate_user_credentials('user@example.com', 'password123');
```

#### **4. Edge Cases**
```sql
-- Soft delete
CREATE PROCEDURE fn_soft_delete_post(IN id INT)
BEGIN
    UPDATE posts SET is_deleted = TRUE WHERE id = id;
END;

-- Batch operations (avoid if possible; use explicit CRUD)
CREATE FUNCTION fn_mass_update_users(
    IN batch_data JSON
) RETURNS TABLE(...);
```

---

### **Implementation Rules**
1. **Consistency**:
   - Use `fn_` for all functions/procedures tied to persistence.
   - Omit `fn_` for utility functions (e.g., `hash_password()`, `generate_id()`).

2. **Action Verb Selection**:
   - Prefer **atomic actions** (e.g., `fn_create_*` over `fn_register_user`).
   - Avoid ambiguous verbs like `fn_change`—specify the field/property (e.g., `fn_update_status`).

3. **Entity Naming**:
   - Align with table names (e.g., `fn_create_user` for `users` table).
   - Use singular nouns for CRUD unless the plural noun is idiomatic (e.g., `fn_update_posts`).

4. **Parameters**:
   - Document parameter direction (`IN`, `OUT`) in SQL comments or via a separate schema file.

5. **Return Types**:
   - Scalar functions return a value (e.g., `RETURNS INT`).
   - Procedures return nothing but may use `OUT` parameters for results.

---

### **Related Patterns**
| Pattern                | Description                                                                 |
|------------------------|-----------------------------------------------------------------------------|
| **[Table Naming](...)** | Follows `snake_case` for tables (e.g., `user_profiles`).                  |
| **[Query Naming](...)**| Uses `q_*` prefix for complex queries (e.g., `q_get_active_subscribers`).  |
| **[Idempotency](...)** | Design functions to be repeatable (e.g., `fn_create_user` with checks).      |
| **[Error Handling](...)**| Use `fn_*` to return error codes or throw exceptions (e.g., `DUPLICATE_ENTRY`).|

---
### **Anti-Examples**
| **❌ Poor Convention**       | **✅ Corrected**                     | **Why?**                                  |
|-----------------------------|------------------------------------|-------------------------------------------|
| `fn_save_user`             | `fn_create_user`                   | "Save" is ambiguous; prefer `create`.     |
| `fn_update_user_data`      | `fn_update_user_name(..., name)`   | Overly generic; specify the field.       |
| `fn_process_order`         | `fn_create_order`/`fn_cancel_order`| Too vague; use explicit actions.          |
| `fn_getAllUsers`           | `fn_get_users()`                   | Use `get_*` for singular/plural clarity.  |

---
### **Tools & Automation**
- **Build Scripts**: Parse `fn_*` functions to generate OpenAPI/Swagger docs.
- **ORM Integration**: Map `fn_create_user` to an application method like `userService.create()`.
- **Migration Tools**: Tag `fn_*` functions as "persistence" to auto-generate tests.

---
### **When to Break the Rules**
- **Legacy Code**: Use `fn_legacy_update_users` to mark exceptions.
- **Domain Logic**: Move pure business logic to application code (e.g., `validate_password()`).
- **ORM Overrides**: If using an ORM, prefix functions with `fn_orm_` (e.g., `fn_orm_save_user`).

---
**Version**: 1.0.0
**Last Updated**: [Date]
**Owner**: Database Design Team