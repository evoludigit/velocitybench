---
# **[Pattern] Trinity Pattern – Unified Record Identification**
*Optimizing Database Efficiency, API Exposure, and User-Facing URLs*

---

## **Overview**
The **Trinity Pattern** resolves the classic backend dilemma of choosing between **sequential IDs**, **UUIDs**, or **slugs** for record identification. By integrating **three identifier types**—a **primary key (PK)**, a **UUID**, and a **slug**—the pattern ensures:
- **Database efficiency** via **auto-incrementing integers** (PK).
- **Scalability** in **REST/gRPC APIs** with **UUIDs** (collision resistance, no size limits).
- **User-friendly URLs** using **slugs** (e.g., `/users/jane-doe`).

This avoids trade-offs like poor URL readability or inefficient joins while maintaining performance.

---

## **Schema Reference**
Below is the **core table structure** and **indexing strategy** for applying the Trinity Pattern. Columns marked with `*` are optional but recommended for consistency.

| **Column**       | **Type**       | **Constraints**                     | **Purpose**                          |
|------------------|----------------|-------------------------------------|--------------------------------------|
| `pk_<table>`     | `SERIAL`       | `PRIMARY KEY`                       | Internal DB operations (fast, indexed) |
| `id`             | `UUID`         | `UNIQUE NOT NULL DEFAULT gen_random_uuid()` | Public API exposure (collision-proof) |
| `<identifier>`*  | `VARCHAR(N)`   | `UNIQUE NOT NULL`                   | User-facing URLs (e.g., `username`)   |
| `<data_columns>` | Varies         | Varies                              | Application-specific fields          |

### **Index Strategy**
| **Index**               | **Purpose**                          |
|-------------------------|--------------------------------------|
| `PRIMARY KEY` (`pk_*`)  | Optimizes `JOIN`s, `WHERE` clauses.  |
| `UNIQUE` (`id`)         | Accelerates API lookups (e.g., `/api/users/{uuid}`). |
| `UNIQUE` (`<identifier>`) | Enables fast URL routing (e.g., `/users/jane-doe`). |

**Example (User Table):**
```sql
CREATE TABLE tb_user (
    pk_user SERIAL PRIMARY KEY,
    id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    -- Other fields...
);

-- Explicit indexes (already covered by PRIMARY KEY/UNIQUE)
CREATE INDEX idx_user_slug ON tb_user (username);
```

---

## **Query Examples**
### **1. Internal Database Operations (Using `pk_*`)**
Optimized for speed and join performance:
```sql
-- Fetch a user by auto-incremented ID (fastest path)
SELECT * FROM tb_user WHERE pk_user = 123;

-- Join with another table (PK-based join is efficient)
SELECT u.username, o.order_id
FROM tb_user u
JOIN tb_orders o ON u.pk_user = o.pk_user;
```

### **2. Public API Exposure (Using `id` UUID)**
Expose UUIDs in API endpoints (e.g., `/api/users/{uuid}`):
```sql
-- Lookup a user via UUID (unique constraint ensures O(1) lookup)
SELECT * FROM tb_user WHERE id = 'a1b2c3d4-e5f6-7890-abc1-234567890abc';

-- Update via UUID (common in REST APIs)
UPDATE tb_user SET email = 'new@example.com' WHERE id = 'a1b2c3d4-e5f6-7890-abc1-234567890abc';
```

### **3. User-Facing URLs (Using Slugs)**
Generate SEO-friendly URLs (e.g., `/users/jane-doe`):
```sql
-- Fetch a user by slug (common for web routing)
SELECT * FROM tb_user WHERE username = 'jane-doe';

-- Redirect slugs to UUIDs (optional middleware step)
-- Example: `/users/jane-doe` → `/api/users/{uuid_of_jane-doe}`
```

### **4. Hybrid Queries (Combining Identifiers)**
Use **all three identifiers** in complex queries:
```sql
-- Find users matching slug *or* UUID (e.g., admin dashboard)
SELECT u.*
FROM tb_user u
WHERE u.username = 'admin'
   OR u.id = 'a1b2c3d4-e5f6-7890-abc1-234567890abc';

-- Batch operations (e.g., bulk updates via UUIDs)
UPDATE tb_user
SET is_active = FALSE
WHERE id IN (
    'a1b2c3d4-e5f6-7890-abc1-234567890abc',
    'b2c3d4e5-f678-90ab-c123-4567890abcdef'
);
```

---

## **Implementation Guidelines**
### **Column Naming Conventions**
| **Identifier Type** | **Column Prefix** | **Example**       | **Use Case**               |
|--------------------|-------------------|--------------------|----------------------------|
| Primary Key        | `pk_`             | `pk_user`          | Internal DB operations     |
| UUID               | `id`              | `id`               | API endpoints (`/api/users/{id}`) |
| Slug               | `<table>_slug`*   | `username`         | User-facing URLs (`/users/{slug}`) |

*—Optional: Use `<table>_slug` if the column isn’t the primary identifier (e.g., `product_slug` for `/products/running-shoes`).*

### **UUID Generation**
- **PostgreSQL**: Use `gen_random_uuid()` (built-in).
- **MySQL**: Use `UUID()` (MySQL 8.0+) or a custom function.
- **Application Layer**: Generate UUIDs in code (e.g., `uuid4()` in Python’s `uuid` module).

### **Slug Generation**
- **Rules**:
  - Convert to **lowercase**.
  - Replace spaces/hyphens with `-`.
  - Remove special characters (e.g., `O` → `0`, `Ä` → `A`).
- **Tools**:
  - **PostgreSQL**: Use `regexp_replace(username, '[^a-z0-9-]', '-', 'g')`.
  - **Application Code**: Libraries like `slugify` (JavaScript) or `python-slugify`.

### **Migration Strategy**
1. **Add `id` and `slug` columns** to an existing table:
   ```sql
   ALTER TABLE tb_user ADD COLUMN id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid();
   ALTER TABLE tb_user ADD COLUMN username VARCHAR(100) UNIQUE NOT NULL;
   ```
2. **Backfill slugs** for existing records:
   ```sql
   UPDATE tb_user SET username = slugify(email) WHERE username IS NULL;
   ```
3. **Update application code** to use the new identifiers.

---

## **Performance Considerations**
| **Identifier Type** | **Pros**                                  | **Cons**                                  | **Best For**               |
|--------------------|-------------------------------------------|-------------------------------------------|----------------------------|
| **`pk_*` (SERIAL)** | Fastest joins, smallest size (4 bytes).   | Not user-friendly, requires sequential allocation. | Internal DB logic.         |
| **UUID**           | Collision-resistant, size-agnostic.       | Slightly slower than integers in some DBs. | API endpoints.             |
| **Slug**           | Human-readable, SEO-friendly.             | Requires regex handling, not DB-optimized. | Web URLs.                  |

- **Indexing**: Always index `UNIQUE` columns (`id`, `slug`).
- **Database Choice**:
  - **PostgreSQL**: UUIDs perform nearly as well as integers.
  - **MySQL/MariaDB**: UUIDs are slower; consider `BINARY(16)` for compatibility.
- **Caching**: Cache slug-ID mappings (e.g., Redis) if URL routing is a bottleneck.

---

## **Edge Cases & Solutions**
| **Scenario**               | **Solution**                                  |
|----------------------------|-----------------------------------------------|
| **Slug collisions**        | Enforce `UNIQUE` + append timestamps (e.g., `jane-doe-2023`). |
| **UUID generation race**    | Use database-generated UUIDs (avoid app-level conflicts). |
| **PK overflow** (rare)     | Switch to `BIGSERIAL` or monitoring-based scaling. |
| **Slug updates**           | Disallow updates; use soft deletes or redirects. |

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                          |
|---------------------------|-------------------------------------------------------------------------------|-------------------------------------------|
| **[Snowflake ID](https://link-to-pattern)** | Distributed ID generation (e.g., Twitter).                                | High-scale microservices.                |
| **[Composite Keys](https://link-to-pattern)** | Multi-column primary keys (e.g., `(user_id, post_id)`).                  | Denormalized data models.                |
| **[ETAGs for API Caching](https://link-to-pattern)** | Versioning APIs with UUIDs/ETAGs.                                        | Read-heavy APIs.                         |
| **[URL Shortening](https://link-to-pattern)** | Map slugs to UUIDs for analytics.                                          | Analytics dashboards.                     |

---

## **Anti-Patterns to Avoid**
1. **Using UUIDs for everything**:
   - Slower joins, larger storage overhead.
2. **Relying on auto-incremented IDs for URLs**:
   - `/users/123` is less user-friendly than `/users/jane-doe`.
3. **Dynamic slugs without uniqueness**:
   - Duplicate slugs break URL routing.
4. **Ignoring indexing**:
   - Always index `UNIQUE` columns (`id`, `slug`).

---
## **Example: Full Table Definition**
```sql
-- Trinity Pattern: Comprehensive Example
CREATE TABLE tb_product (
    pk_product SERIAL PRIMARY KEY,
    id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    slug VARCHAR(200) UNIQUE NOT NULL,  -- e.g., "running-shoes-nike"
    name VARCHAR(255) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    stock_quantity INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_product_slug ON tb_product (slug);       -- URL routing
CREATE INDEX idx_product_id ON tb_product (id);           -- API lookups

-- Triggers (optional: auto-update timestamps)
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_product_update_timestamp
BEFORE UPDATE ON tb_product
FOR EACH ROW EXECUTE FUNCTION update_timestamp();
```

---
## **Summary of Trade-offs**
| **Identifier** | **Database Efficiency** | **API Efficiency** | **URL Friendly** | **Storage Overhead** |
|----------------|-------------------------|--------------------|------------------|----------------------|
| `pk_*`         | ✅ Best                  | ❌ Worst            | ❌ No             | ✅ Low (4 bytes)      |
| UUID           | ⚠️ Good (PostgreSQL)    | ✅ Best             | ❌ No             | ⚠️ Medium (16 bytes) |
| Slug           | ❌ Worst                 | ⚠️ Good (caching)   | ✅ Best           | ✅ Low (variable)     |

**Trinity Pattern** = **✅✅✅** (Balanced solution).