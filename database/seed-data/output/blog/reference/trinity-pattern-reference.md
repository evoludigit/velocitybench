# **[Pattern] Trinity Pattern Reference Guide**

---

## **Overview**
The **Trinity Pattern** resolves the common backend challenge of selecting optimal identifiers for **database operations**, **API exposure**, and **user-facing URLs** by leveraging three distinct identifier types in a single schema.

Instead of forcing a single choice (e.g., UUIDs for APIs or slugs for URLs), the Trinity Pattern **combines**:
- **`pk_*` (SERIAL INTEGER)**: Optimized for **database performance** (fast lookups, joins, and indexing).
- **`id` (UUID)**: Suitable for **public APIs** (collision-resistant, globally unique).
- **`username` (VARCHAR/SLUG)**: Designed for **human-readable URLs** (e.g., `/users/john-doe`).

This approach eliminates trade-offs, ensuring each identifier type serves its purpose without redundancy.

---

## **Schema Reference**

| **Field**       | **Type**       | **Constraints**                     | **Purpose**                          | **Indexes**                     |
|-----------------|---------------|------------------------------------|--------------------------------------|----------------------------------|
| `pk_user`       | `SERIAL`      | `PRIMARY KEY`                      | Internal DB operations (fast indexing) | `IDX_USER_PK` (auto-created)   |
| `id`            | `UUID`        | `UNIQUE NOT NULL DEFAULT gen_random_uuid()` | Public API exposure (collision-proof) | `IDX_USER_ID` (`id`)            |
| `username`      | `VARCHAR(100)`| `UNIQUE NOT NULL`                  | User-facing URLs (e.g., `/users/john-doe`) | `IDX_USER_USERNAME` (`username`) |
| `email`         | `VARCHAR(255)`| `UNIQUE NOT NULL`                  | User identification (validation)     | (auto-created from `UNIQUE`)    |
| `first_name`    | `VARCHAR(100)`|                                    | User display name                     |                                  |
| `last_name`     | `VARCHAR(100)`|                                    | User display name                     |                                  |
| `bio`           | `TEXT`        |                                    | User profile content                  |                                  |
| `is_active`     | `BOOLEAN`     | `DEFAULT true`                     | Account status (e.g., soft deletes)  |                                  |
| `created_at`    | `TIMESTAMPTZ` | `DEFAULT NOW()`                    | Record creation timestamp             |                                  |
| `updated_at`    | `TIMESTAMPTZ` | `DEFAULT NOW()`                    | Last update timestamp                 |                                  |

---

## **Key Design Principles**

### **1. Separation of Concerns**
| **Identifier** | **Use Case**                          | **Why?**                                                                 |
|----------------|---------------------------------------|-------------------------------------------------------------------------|
| `pk_user`      | Internal DB operations (inserts, joins, pagination) | Auto-incremented integers are fastest for relational queries.          |
| `id`           | API responses (e.g., `/api/users/123`) | UUIDs prevent ID leaks and collisions across services.                   |
| `username`     | URLs (e.g., `/users/john-doe`)        | Readable, memorable, and SEO-friendly.                                   |

### **2. Data Model Example**
```sql
-- Example schema for a "Post" table
CREATE TABLE tb_post (
    pk_post      SERIAL PRIMARY KEY,
    id           UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    slug         VARCHAR(255) UNIQUE NOT NULL,  -- e.g., "how-to-learn-postgresql"
    title        VARCHAR(255) NOT NULL,
    content      TEXT NOT NULL,
    author_id    INTEGER REFERENCES tb_user(pk_user),  -- Uses pk_* for joins
    created_at   TIMESTAMPTZ DEFAULT NOW()
);
```

### **3. Indexing Strategy**
Ensure indexes match query patterns:
```sql
-- Database-specific UUID generation (PostgreSQL example)
ALTER TABLE tb_user ADD COLUMN id UUID DEFAULT gen_random_uuid();

-- Alternative (MySQL)
ALTER TABLE tb_user ADD COLUMN id CHAR(36) NOT NULL DEFAULT (UUID());
```

---

## **Query Examples**

### **1. Database Operations (Using `pk_*`)**
```sql
-- Insert (uses auto-incremented `pk_user`)
INSERT INTO tb_user (email, first_name, last_name)
VALUES ('user@example.com', 'John', 'Doe')
RETURNING pk_user, id, username;

-- Select with JOIN (optimized for `pk_user`)
SELECT u.pk_user, u.username, p.title
FROM tb_user u
JOIN tb_post p ON u.pk_user = p.author_id
WHERE u.pk_user = 42;
```

### **2. API Responses (Using `id`)**
```sql
-- Fetch user by UUID for API response
SELECT id, username, email, first_name, last_name
FROM tb_user
WHERE id = '123e4567-e89b-12d3-a456-426614174000';
```

### **3. URL Routing (Using `username`)**
```sql
-- Fetch user by slug/username for frontend routing
SELECT pk_user, id, email
FROM tb_user
WHERE username = 'john-doe';

-- Frontend URL: https://example.com/users/john-doe
```

### **4. Hybrid Queries (Combining Identifiers)**
```sql
-- Find users by partial `username` (e.g., search bar)
SELECT pk_user, username, email
FROM tb_user
WHERE username ILIKE '%john%'
ORDER BY updated_at DESC;

-- Update via `id` (API) but fetch by `pk_*` (DB)
UPDATE tb_user
SET email = 'new@example.com'
WHERE id = '123e4567-e89b-12d3-a456-426614174000';
```

---

## **Best Practices**

### **1. Generation Rules**
| **Identifier** | **Generation Method**                          | **Notes**                                      |
|----------------|-----------------------------------------------|------------------------------------------------|
| `pk_user`      | Auto-increment (`SERIAL`)                     | No intervention needed.                        |
| `id`           | `gen_random_uuid()` (PostgreSQL) or `UUID()` (MySQL) | Ensures global uniqueness.                     |
| `username`     | User input + slugify (e.g., `john-doe` → `john-doe`) | Validate uniqueness before saving.             |

### **2. Validation**
```sql
-- Ensure `username` is unique and slug-friendly
INSERT INTO tb_user (username, email)
VALUES ('  john-doe  ', 'user@example.com')
ON CONFLICT (username) DO NOTHING
RETURNING username;

-- Alternative: Pre-slugify before insert
UPDATE tb_user
SET username = slugify(username)
WHERE username LIKE '% %';  -- Trim spaces and hyphenate
```

### **3. Migration Considerations**
- **Add identifiers incrementally**:
  ```sql
  -- Step 1: Add UUID (if not already present)
  ALTER TABLE tb_user ADD COLUMN id UUID DEFAULT gen_random_uuid();

  -- Step 2: Add slug (backfill if needed)
  UPDATE tb_user SET username = slugify(concat(first_name, '-', last_name));
  ALTER TABLE tb_user ADD CONSTRAINT unique_username UNIQUE (username);
  ```
- **Backward compatibility**: Maintain old identifiers during transition.

---

## **Related Patterns**

| **Pattern**               | **Connection to Trinity Pattern**                                                                 | **When to Use**                                  |
|---------------------------|------------------------------------------------------------------------------------------------|--------------------------------------------------|
| **[Snowflake ID](https://link-to-snowflake)** | Uses `pk_*` (integer) but with distributed ID generation.                                      | High-scale systems needing ordered IDs.          |
| **[UUIDv7](https://link-to-uuidv7)**          | Replaces `id` (UUID) with time-sorted UUIDs for temporal queries.                               | Time-based sorting in APIs.                     |
| **[DTO Pattern](https://link-to-dto)**        | Complements Trinity by exposing only `id` in API responses (not `pk_*`).                          | Clean API contracts.                             |
| **[Resource Naming](https://link-to-naming)** | Extends `username` to canonical resource names (e.g., `/articles/how-to-code`).               | SEO and discoverability.                         |
| **[CQRS](https://link-to-cqrs)**              | `pk_*` optimizes write-heavy commands; `id`/`username` powers read-side queries.              | Complex event-sourced systems.                  |

---

## **Common Pitfalls & Mitigations**

| **Issue**                          | **Solution**                                                                 |
|------------------------------------|-----------------------------------------------------------------------------|
| **UUID storage bloat**             | Use `CHAR(36)` (MySQL) or `VARCHAR(36)` (PostgreSQL) instead of `BINARY(16)`. |
| **Slug collisions**                | Add a suffix (e.g., `post-1`, `post-2`) for near-duplicates.              |
| **API ID leaks**                   | Use `id` in responses but never expose `pk_*` directly.                     |
| **Performance on `username` LIKE** | Add a **GIN index** if using full-text search (PostgreSQL).                 |
| **Migration downtime**             | Batch-add identifiers during off-peak hours.                               |

---

## **Example Application Flow**

1. **Frontend**:
   - User navigates to `/users/john-doe` → fetches `username`.
   - API responds with `id` (e.g., `123e4567-e89b-12d3-a456-426614174000`).

2. **Backend**:
   - **Routing**: Resolves `/users/{slug}` to `WHERE username = slug`.
   - **Database**: Uses `pk_user` for joins (e.g., `user_posts` table).
   - **API**: Returns `id` in responses (not `pk_user`).

3. **Database**:
   - All internal ops (inserts, updates) use `pk_user`.
   - UUIDs (`id`) are ignored in joins but used for external references.

---

## **Alternatives Considered**
| **Approach**               | **Pros**                          | **Cons**                                      | **Fits Trinity?** |
|----------------------------|-----------------------------------|-----------------------------------------------|-------------------|
| **Single UUID for all**    | Globally unique                   | Slow for joins, bloated storage              | ❌ No             |
| **Single Slug for all**    | Human-readable                   | Collisions, not API-friendly                 | ❌ No             |
| **Hybrid (e.g., Slug + UUID)** | Flexible                         | Redundancy, inconsistent queries             | ⚠️ Partial        |

---
The Trinity Pattern avoids these trade-offs by **specializing each identifier**.