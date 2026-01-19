# **[Pattern] Trinity Pattern Reference Guide**
*Flexible Entity Identification in FraiseQL*

---

## **Overview**
The **Trinity Pattern** is a schema design pattern used in FraiseQL to define entities with **three distinct but complementary identifiers**:
1. **Primary Key (pk_*)** – A high-performance, auto-generated integer for internal operations (e.g., fast joins, indexing).
2. **UUID (id)** – A globally unique, human-readable string for external references and API endpoints.
3. **Human-Readable Identifier (identifier)** – A short, stable slug (e.g., `abc-123`) for user-friendly interactions.

This approach balances **performance**, **uniqueness**, and **usability** while minimizing collisions and manual ID management.

---

## **Schema Reference**
Below is the standard schema structure for entities adopting the Trinity Pattern in FraiseQL.

| Field Name      | Type         | Description                                                                                     | Constraints                | Example Value          |
|-----------------|--------------|-------------------------------------------------------------------------------------------------|-----------------------------|------------------------|
| `pk_*`          | `BIGINT`     | Auto-incremented primary key for internal database operations.                                  | `PRIMARY KEY`, `AUTO_INCREMENT` | `1234567890`            |
| `id`            | `UUID`       | Globally unique identifier (UUIDv4) for external references.                                     | `UNIQUE`, `GENERATED ALWAYS` | `7a5f6d1e-9c3b-4f2a-8d7e-123456789abc` |
| `identifier`    | `VARCHAR(255)`| Human-readable slug for user-facing URLs and displays.                                           | `UNIQUE`, `NOT NULL`        | `user-profile-abc123`  |
| `created_at`    | `TIMESTAMPTZ`| Timestamp of record creation (optional but recommended).                                         | -                           | `2024-05-20T14:30:00Z` |
| `updated_at`    | `TIMESTAMPTZ`| Timestamp of last modification (optional but recommended).                                       | -                           | `2024-05-21T09:15:00Z` |

**Notes:**
- Replace `pk_*` with the appropriate table name (e.g., `pk_users` for a `users` table).
- The `id` column auto-generates on insertion via `GENERATED ALWAYS`.
- The `identifier` should be **stable** (e.g., derived from `name.to_slug()`) and **immutable** after creation.

---

## **Query Examples**
### **1. Inserting a Record**
```sql
INSERT INTO users (
    pk_users,
    id,
    identifier,
    name,
    email
) VALUES (
    DEFAULT,  -- Auto-incremented
    gen_random_uuid(),  -- Auto-generated UUID
    'user-account-789', -- Manually set or derived from `name`
    'Alice Johnson',
    'alice@example.com'
);
```
**Alternative (auto-generate identifier from `name`):**
```sql
INSERT INTO users (
    pk_users,
    id,
    identifier,
    name,
    email
) VALUES (
    DEFAULT,
    gen_random_uuid(),
    to_slug(name),  -- FraiseQL function to generate slugs
    'Alice Johnson',
    'alice@example.com'
);
```

---

### **2. Retrieving a Record by Identifier (User-Friendly Lookup)**
```sql
SELECT * FROM users
WHERE identifier = 'user-account-789';
```

---

### **3. Retrieving a Record by UUID (API-Friendly Lookup)**
```sql
SELECT * FROM users
WHERE id = '7a5f6d1e-9c3b-4f2a-8d7e-123456789abc';
```

---

### **4. Retrieving a Record by Primary Key (Performance-Optimized)**
```sql
SELECT * FROM users
WHERE pk_users = 1234567890;
```

---

### **5. Updating a Record (Preserving UUID and Identifier)**
```sql
UPDATE users
SET
    name = 'Alice Smith',
    email = 'alice.smith@example.com',
    updated_at = NOW()
WHERE pk_users = 1234567890;
```
**Note:** The `id` and `identifier` remain unchanged unless explicitly updated (rarely recommended).

---

### **6. Joining Tables with Trinity Pattern**
```sql
SELECT
    u.pk_users,
    u.identifier,
    u.name,
    p.pk_posts,
    p.id,
    p.title
FROM users u
JOIN posts p ON u.pk_users = p.pk_users;  -- Join on primary key for speed
```
**Alternative (join on UUID for flexibility):**
```sql
SELECT
    u.id AS user_id,
    u.identifier,
    p.id AS post_id,
    p.title
FROM users u
JOIN posts p ON u.id = p.user_id;  -- Join on UUID if relationships are UUID-based
```

---

### **7. Soft Deletion (Optional)**
```sql
-- Mark as deleted (logical deletion)
UPDATE users
SET is_deleted = true, deleted_at = NOW()
WHERE pk_users = 1234567890;

-- Query active records
SELECT * FROM users
WHERE is_deleted = false;
```

---

## **Best Practices**
1. **Auto-Generate UUIDs and PKs**
   - Never manually set `id` or `pk_*` unless absolutely necessary.
   - Use `gen_random_uuid()` for UUIDs and `DEFAULT` for auto-incremented keys.

2. **Derive Identifiers Automatically**
   - Use FraiseQL’s `to_slug()` function to generate `identifier` from `name` or other fields:
     ```sql
     identifier = to_slug(concat(name, '-', to_char(pk_users, '000000')));
     ```

3. **Avoid Updates to `id` or `identifier`**
   - Changing these after insertion breaks referential integrity in linked tables.

4. **Indexing**
   - Ensure `pk_*`, `id`, and `identifier` are indexed for fast lookups:
     ```sql
     CREATE INDEX idx_users_pk ON users(pk_users);
     CREATE INDEX idx_users_id ON users(id);
     CREATE INDEX idx_users_identifier ON users(identifier);
     ```

5. **Use UUIDs for External APIs**
   - Return UUIDs (`id`) in API responses for flexibility, but expose `identifier` in URLs for users:
     ```
     GET /api/v1/users/{identifier}/posts
     ```

---

## **Edge Cases and Considerations**
### **1. Identifier Collisions**
- If two records generate the same `identifier` (e.g., from `to_slug()`), add a suffix like `_1`, `_2`:
  ```sql
  identifier = to_slug(name) || '_' || (SELECT COUNT(*) FROM users WHERE identifier LIKE to_slug(name) || '_%');
  ```

### **2. UUID Collisions**
- Probability is negligible (1 in 2^122), but FraiseQL’s `gen_random_uuid()` is cryptographically secure.

### **3. Performance**
- For **high-throughput** systems, prefer `pk_*` for joins. Use UUIDs (`id`) only when necessary (e.g., distributed systems).

### **4. Migrations**
- When updating an existing table to the Trinity Pattern, ensure backward compatibility:
  ```sql
  ALTER TABLE legacy_users ADD COLUMN id UUID GENERATED ALWAYS AS (gen_random_uuid());
  ALTER TABLE legacy_users ADD COLUMN identifier VARCHAR(255) NOT NULL;
  ```

---

## **Related Patterns**
1. **[Snowflake ID Pattern]**
   - Use for distributed systems requiring sortable, timestamp-embedded IDs (e.g., `pk_*` can be Snowflake IDs).

2. **[Soft Delete Pattern]**
   - Complements Trinity Pattern by adding `is_deleted` and `deleted_at` columns for logical deletion.

3. **[Event Sourcing Pattern]**
   - Use UUIDs (`id`) as immutable event identifiers in event logs.

4. **[Slug Generation Pattern]**
   - Extend with custom slug rules (e.g., hyphenated vs. underscore-separated identifiers).

5. **[Composite Keys Pattern]**
   - Combine with Trinity Pattern for tables requiring multi-column uniqueness (e.g., `UNIQUE(id, external_service_id)`).

---

## **When to Use (and Avoid) the Trinity Pattern**
### **Use It When:**
- You need **fast internal lookups** (`pk_*`).
- Records must be **globally unique** (`id`).
- User-facing URLs or displays need **readable identifiers**.

### **Avoid It When:**
- The entity is **small-scale** (primary key alone suffices).
- UUIDs introduce **unnecessary complexity** (e.g., embedded systems).
- The `identifier` is **frequently updated** (risk of breaking links).

---
**Example Use Cases:**
✅ User profiles (APIs, web apps)
✅ Blog posts (URL slugs)
✅ Distributed systems (UUIDs for cross-service refs)
❌ Internal configs (primary key only)
❌ Time-series data (auto-incremented timestamps)