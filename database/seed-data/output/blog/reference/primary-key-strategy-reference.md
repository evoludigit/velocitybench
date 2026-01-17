# **[Pattern] Primary Key Strategy (`pk_*`) Reference Guide**

---

## **Overview**
The **Primary Key Strategy (`pk_*`)** is a FraiseQL design pattern that ensures efficient internal data indexing while maintaining a clean external API. This pattern leverages **SERIAL INTEGER surrogate keys** (auto-incrementing numbers) as internal identifiers (`pk_*`) for optimal B-tree performance in FraiseQL’s storage engine. Simultaneously, it exposes **UUIDs** as external identifiers (`id`) for consistency with distributed systems and **human-readable identifiers** (`slug`, `url`) for web-friendly URLs.

This approach follows the **Trinity Pattern**, where:
- **Internal storage** uses `pk_*` for speed (B-tree optimized).
- **External APIs** use UUIDs for consistency and portability.
- **URLs** use slugs or custom identifiers for readability.

---

## **Schema Reference**

| Field Name  | Type          | Description                                                                 | Example Value          |
|-------------|---------------|-----------------------------------------------------------------------------|------------------------|
| **`pk_*`**  | `SERIAL INTEGER` | Internal surrogate key for B-tree indexing (auto-incremented).              | `pk_user=123`, `pk_order=456` |
| **`id`**    | `UUID`        | External identifier (portable, globally unique).                          | `id='550e8400-e29b-41d4-a716-446655440000'` |
| **`slug`**  | `TEXT`        | Human-readable URL-friendly identifier.                                     | `slug='user-profile'`  |
| **`url`**   | `TEXT`        | Custom URL path (if applicable).                                            | `url='/dashboard'`     |
| **`created_at`** | `TIMESTAMP`   | Record creation timestamp (optional but recommended).                      | `created_at='2023-10-01T00:00:00Z'` |
| **`updated_at`** | `TIMESTAMP`   | Last update timestamp (for audit purposes).                               | `updated_at='2023-10-02T12:00:00Z'` |

**Key Rules:**
1. **`pk_*` is reserved internally**—do not exposed in APIs unless absolutely necessary.
2. **`id` is the external identifier**—used in API responses and client applications.
3. **`slug`/`url` are optional** but recommended for web-facing resources.
4. **UUIDs must be generated client-side** (e.g., via FraiseQL’s `uuidos` or `uuid4` functions) before insertion.

---

## **Query Examples**

### **1. Inserting a Record**
```sql
-- Insert with auto-generated pk_* and UUID
INSERT INTO users (id, pk_user, name, email)
VALUES (
    uuidos(),  -- Generates a random UUID (client-side)
    nextval('pk_user_seq'),  -- Auto-incremented surrogate key
    'Alice Smith',
    'alice@example.com'
);
```

**Output:**
| `pk_user` | `id`                          | `name`       | `email`               |
|-----------|-------------------------------|--------------|-----------------------|
| 123       | `550e8400-e29b-41d4-a716-446655440000` | Alice Smith  | alice@example.com     |

---

### **2. Retrieving Records by External ID (UUID)**
```sql
-- Fetch a user by their UUID (external API ID)
SELECT pk_user, id, name, email
FROM users
WHERE id = '550e8400-e29b-41d4-a716-446655440000';
```

**Output:**
| `pk_user` | `id`                          | `name`       | `email`               |
|-----------|-------------------------------|--------------|-----------------------|
| 123       | `550e8400-e29b-41d4-a716-446655440000` | Alice Smith  | alice@example.com     |

---

### **3. Retrieving Records by Surrogate Key (Internal)**
```sql
-- Fetch a user by their internal pk_* (admin-only)
SELECT pk_user, id, name, email
FROM users
WHERE pk_user = 123;
```

**Output:**
| `pk_user` | `id`                          | `name`       | `email`               |
|-----------|-------------------------------|--------------|-----------------------|
| 123       | `550e8400-e29b-41d4-a716-446655440000` | Alice Smith  | alice@example.com     |

---

### **4. Joining Tables with `pk_*` and UUIDs**
```sql
-- Join orders to users (using UUIDs for external consistency)
SELECT
    o.pk_order,
    o.id,
    u.pk_user,
    u.name,
    o.amount,
    o.created_at
FROM orders o
JOIN users u ON o.user_id = u.id;  -- Join via UUID
```

**Output:**
| `pk_order` | `id`                          | `pk_user` | `name`       | `amount` | `created_at`          |
|------------|-------------------------------|-----------|--------------|----------|-----------------------|
| 456        | `1a2b3c4d-5e6f-7g8h-9i0j-1k2l3m4n5o6p` | 123       | Alice Smith  | 99.99    | `2023-10-03T10:00:00Z` |

---

### **5. Generating Slugs for URLs**
```sql
-- Create a slug from a name (for web URLs)
UPDATE users
SET slug = to_slug(name)
WHERE pk_user = 123;
```

**Output (after update):**
| `pk_user` | `id`                          | `name`       | `email`               | `slug`          |
|-----------|-------------------------------|--------------|-----------------------|-----------------|
| 123       | `550e8400-e29b-41d4-a716-446655440000` | Alice Smith  | alice@example.com     | `alice-smith`   |

---

### **6. Deleting by Surrogate Key (Caution)**
```sql
-- Delete a record by internal pk_* (use sparingly)
DELETE FROM users
WHERE pk_user = 123;
```

**Warning:**
- Deletions by `pk_*` should be avoided in production unless absolutely necessary (e.g., admin actions).
- Prefer soft deletes (`is_deleted` flag) for external-facing systems.

---

## **Best Practices**
1. **Never expose `pk_*` in APIs**—use `id` (UUID) instead.
2. **Generate UUIDs client-side** before insertion to avoid collisions.
3. **Use `nextval('pk_*_seq')` for surrogate keys**—FraiseQL auto-manages sequences.
4. **Add indexes on `id`, `slug`, and foreign keys** for performance:
   ```sql
   CREATE INDEX idx_users_id ON users(id);
   CREATE INDEX idx_users_slug ON users(slug);
   ```
5. **For read-heavy tables**, ensure `pk_*` is the PRIMARY KEY and indexed.
6. **For write-heavy tables**, consider adding a `version` column for optimistic concurrency control:
   ```sql
   ALTER TABLE users ADD COLUMN version INTEGER DEFAULT 0;
   ```

---

## **Performance Considerations**
| Key          | Performance Impact                          | When to Use                          |
|--------------|--------------------------------------------|--------------------------------------|
| **`pk_*` (SERIAL INTEGER)** | ✅ **Fastest for internal B-tree lookups** | Primary key, joins, indexes.         |
| **`id` (UUID)**      | ⚠️ Slightly slower than integers (but negligible in practice) | External APIs, distributed systems. |
| **`slug`/`url`**    | ⚠️ May require additional indexing         | Web URLs, human-readable paths.     |

---

## **Related Patterns**
1. **[Trinity Pattern]** – Combines `pk_*`, UUIDs, and slugs for a unified strategy.
2. **[Soft Delete Pattern]** – Use an `is_deleted` flag instead of hard deletes.
3. **[Optimistic Concurrency Control]** – Add a `version` column to handle conflicts.
4. **[Composite Keys]** – Use rare, but useful for multi-column uniqueness.
5. **[Denormalization for Read Performance]** – Materialized views or cached slugs.

---

## **Troubleshooting**
| Issue                          | Solution                                  |
|--------------------------------|-------------------------------------------|
| **UUID collisions**           | Ensure UUIDs are generated client-side.   |
| **Slow UUID lookups**         | Add an index on the `id` column.          |
| **Surrogate key exposure**     | Validate API responses—don’t return `pk_*`. |
| **Slug generation failures**   | Use `to_slug()` function or a custom ETL. |

---

## **Migration Guide**
### **From Plain UUIDs to `pk_*` + UUID**
1. **Add `pk_*` column**:
   ```sql
   ALTER TABLE users ADD COLUMN pk_user SERIAL PRIMARY KEY;
   ```
2. **Update existing records** (or use triggers):
   ```sql
   UPDATE users SET pk_user = nextval('pk_user_seq');
   ```
3. **Update foreign keys** to reference `pk_*` internally:
   ```sql
   ALTER TABLE orders ADD COLUMN user_pk_ INT REFERENCES users(pk_user);
   ```
4. **Deprecate old `id` if not needed** (or keep for backward compatibility).

### **From Surrogate Keys Only to Trinity Pattern**
1. **Add `id` (UUID) column**:
   ```sql
   ALTER TABLE users ADD COLUMN id UUID NOT NULL DEFAULT uuidos();
   ```
2. **Add `slug` column** (optional):
   ```sql
   ALTER TABLE users ADD COLUMN slug TEXT;
   ```
3. **Update API responses** to return `id` instead of `pk_*`.

---