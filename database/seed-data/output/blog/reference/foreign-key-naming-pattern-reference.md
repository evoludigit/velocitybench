# **[Pattern] Foreign Key Naming Convention (fk_*) Reference Guide**

---

## **Overview**
This pattern mandates a standardized naming convention (`fk_*_id`) for foreign key columns in FraiseQL schemas, ensuring consistency, performance, and semantic clarity. Foreign keys always reference surrogate key columns (prefixed with `pk_*` as `INTEGER`) rather than UUIDs, improving indexing for JOIN operations while maintaining explicit relationship semantics.

Unlike UUID-based references (e.g., `user_id`), this convention enforces:
- **Explicit naming**: `fk_user_id` always denotes a mandatory link to the `user` table’s primary key.
- **Optimized JOINs**: Using `INTEGER` surrogates minimizes overhead in relational joins.
- **Schematic consistency**: Avoids ambiguity by standardizing all foreign keys under a predictable pattern.

---

## **Schema Reference**

| **Field**         | **Type**  | **Description**                                                                 | **Example**                     |
|-------------------|-----------|---------------------------------------------------------------------------------|---------------------------------|
| **Foreign Key Name** | `VARCHAR` | Always follows `fk_[table_name]_id` (e.g., `fk_user_id`)                          | `fk_customer_id`                |
| **Foreign Column**   | `INTEGER` | References the target table’s `pk_id` column (surrogate key, auto-incremented). | `fk_user_id` → `user.pk_id`     |
| **Target Table**     | `TABLE`   | The referenced entity (e.g., `users`, `products`).                                   | `fk_user_id` → `users.pk_id`    |
| **Nullable?**       | `BOOLEAN` | `NOT NULL` unless explicitly documented as optional (e.g., `fk_address_id`).      | `fk_user_id NOT NULL`           |
| **Indexing**         | `INDEX`   | All `fk_*` columns are indexed by default for JOIN performance.                   | `CREATE INDEX idx_fk_user_id ON orders(fk_user_id);` |

**Key Rules:**
1. **Prefix**: `fk_` for all foreign keys.
2. **Suffix**: `_id` to denote the referenced table’s primary key.
3. **Target**: Only bind to `pk_*` columns (e.g., `user.pk_id`), not UUIDs or natural keys.
4. **Data Type**: Strictly `INTEGER` (auto-incremented surrogate keys).

---

## **Example Schema**

```sql
-- Users table (primary key surrogate)
CREATE TABLE users (
    pk_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    username   VARCHAR(50) UNIQUE NOT NULL,
    email      VARCHAR(100) UNIQUE NOT NULL
);

-- Orders table (foreign key referencing users.pk_id)
CREATE TABLE orders (
    pk_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    fk_user_id   INTEGER NOT NULL,  -- Foreign key to users.pk_id
    order_date   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10, 2),
    FOREIGN KEY (fk_user_id) REFERENCES users(pk_id) ON DELETE CASCADE
);

-- Products table (optional foreign key)
CREATE TABLE products (
    pk_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    name         VARCHAR(100) NOT NULL,
    fk_category_id INTEGER,  -- Optional FK (nullable)
    price        DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (fk_category_id) REFERENCES categories(pk_id) ON DELETE SET NULL
);
```

---

## **Query Examples**

### **1. Basic JOIN with Foreign Keys**
```sql
-- Retrieve all orders for a user (using fk_user_id)
SELECT
    u.username,
    o.order_date,
    o.total_amount
FROM
    users u
JOIN
    orders o ON u.pk_id = o.fk_user_id
WHERE
    u.username = 'john_doe';
```
**Performance Note**: The `ON u.pk_id = o.fk_user_id` clause leverages the indexed `fk_user_id` for fast JOIN resolution.

---

### **2. Inserting with Foreign Key Constraints**
```sql
-- Add an order referencing an existing user
INSERT INTO orders (fk_user_id, total_amount)
VALUES (
    -- Validate: fk_user_id must match users.pk_id
    (SELECT pk_id FROM users WHERE username = 'john_doe'),
    99.99
);
```
**Validation Rule**: The query ensures the referenced `users.pk_id` exists (enforced by `NOT NULL` + `FOREIGN KEY` constraints).

---

### **3. Deleting with Cascade**
```sql
-- Delete a user and all their orders (cascade deletion)
DELETE FROM users
WHERE pk_id = (
    SELECT pk_id FROM users WHERE username = 'john_doe'
);
```
**Behavior**: The `ON DELETE CASCADE` clause automatically removes related orders via the `fk_user_id` reference.

---

### **4. Updating Foreign Key Values**
```sql
-- Update a user’s data (no direct fk_user_id update needed)
UPDATE users
SET email = 'new_email@example.com'
WHERE pk_id = 42;
```
**Key Point**: Foreign keys are updated implicitly via the referenced table’s `pk_id`.

---

## **Query Patterns for Foreign Keys**

| **Use Case**               | **Query Template**                                                                 | **Notes**                                  |
|----------------------------|-----------------------------------------------------------------------------------|--------------------------------------------|
| **One-to-Many JOIN**       | `SELECT * FROM parent JOIN child ON parent.pk_id = child.fk_parent_id`            | Standard for hierarchical data.            |
| **Subquery with FK**       | `WHERE fk_user_id IN (SELECT pk_id FROM users WHERE ...)`                          | Efficient for filtering.                   |
| **Self-Referential FK**    | `FOREIGN KEY (fk_parent_id) REFERENCES users(pk_id)`                            | Used for hierarchies (e.g., `employees.fk_manager_id`). |
| **NULL Check**             | `WHERE fk_category_id IS NULL`                                                    | For optional relationships.                |

---

## **Related Patterns**

1. **Surrogate Key Pattern (pk_*)**
   - *Connection*: Foreign keys (`fk_*`) **only** reference surrogate keys (`pk_*`), ensuring normalization and index efficiency.
   - *Reference*: [Surrogate Key Pattern](link-to-docs).

2. **Composite Key Naming**
   - *Connection*: If using composite keys, foreign keys should follow `fk_[table1]_[table2]_id` (e.g., `fk_order_item_id`).
   - *Reference*: [Composite Key Pattern](link-to-docs).

3. **UUID Anti-Pattern**
   - *Avoid*: Never use UUIDs as foreign keys. This pattern enforces `INTEGER` references for JOIN performance.

4. **Indexing Strategy**
   - *Connection*: All `fk_*` columns are indexed by default. Explicit indexes may be added for high-cardinality tables.
   - *Reference*: [Indexing Best Practices](link-to-docs).

5. **Data Migration**
   - *Connection*: When updating schemas, foreign key columns **must** align with `pk_*` columns. Use transactions for atomic changes.
   - *Tooling*: Leverage FraiseQL’s migration scripts to auto-generate `fk_*` constraints.

---

## **Best Practices**

1. **Consistency**:
   - Enforce `fk_*` prefix **everywhere** in your schema. Tools like schema validators can catch violations.

2. **Validation**:
   - Add schema checks (e.g., in CI/CD) to ensure foreign keys only reference `pk_*` columns.

3. **Documentation**:
   - Annotate nullable foreign keys (e.g., `fk_address_id` may be `NULL` for users without addresses).

4. **Performance**:
   - Prefer `INTEGER` over UUIDs for foreign keys to reduce JOIN overhead (~70% faster on most databases).

5. **Error Handling**:
   - Use `ON DELETE CASCADE/SET NULL` judiciously to avoid unintended data loss.

---
**Example Schema Validator (Pseudocode):**
```python
def validate_foreign_keys(schema):
    for table in schema:
        for column in table.columns:
            if column.name.startswith('fk_'):
                assert column.references.pk_table == 'pk_', "FK must reference pk_* column"
                assert column.data_type == 'INTEGER', "FK must be INTEGER"
```

---
**Final Note**: This pattern balances **semantic clarity** (explicit `fk_*` naming) with **performance** (optimized `INTEGER` JOINs). Deviations should be documented and justified.