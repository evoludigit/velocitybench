# **[Pattern] Trinity Pattern Reference Guide**
*Solving the record identification dilemma through three optimized identifiers*

The **Trinity Pattern** resolves the conflict between database efficiency, API design, and user-facing URL requirements by assigning three distinct identifier types to each record. This eliminates the need to compromise between:
- **Sequential integers** (fast internal operations)
- **Universally Unique Identifiers (UUIDs)** (public API exposure)
- **Slugs** (human-readable URLs)

By maintaining one identifier per use case, the Trinity Pattern ensures:
- **Database performance** via primary keys (e.g., `SERIAL`).
- **API consistency** with UUIDs (non-guessable, stateless).
- **User-friendly URLs** with slugs (e.g., `/profiles/john-doe`).

---

## **2. Schema Reference**
The following schema defines the Trinity Pattern for a `tb_user` table. Columns are categorized by identifier purpose and indexed for performance.

| Column            | Type         | Description                                                                 | Indexes                     |
|-------------------|--------------|-----------------------------------------------------------------------------|-----------------------------|
| **`pk_user`**     | `SERIAL`     | Auto-incremented primary key for internal database operations.               | `idx_user_pk` (implicit)     |
| **`id`**          | `UUID` (UNIQUE)| Public-facing UUID for API endpoints and JSON responses.                     | `idx_user_id`                |
| **`username`**    | `VARCHAR(100)` | Human-readable slug for URLs (e.g., `/users/john_doe`).                     | `idx_user_username`          |
| **`email`**       | `VARCHAR(255)`| Unique identifier for user accounts.                                        | *(No extra index; relies on UNIQUE constraint)* |
| **Data Columns**  |              | Standard user fields (e.g., `first_name`, `last_name`, `bio`).              | -                           |

**Additional Rules:**
- All three identifiers (`pk_user`, `id`, `username`) are unique but *not* related to each other (e.g., `id` is not derived from `pk_user`).
- UUIDs are generated at insert time (e.g., PostgreSQL’s `gen_random_uuid()`).

---

## **3. Query Examples**

### **3.1. Database Operations (Primary Key)**
Use `pk_user` for internal queries where performance is critical.

```sql
-- Insert with implicit PK generation
INSERT INTO tb_user (id, username, email, first_name, last_name)
VALUES (
    gen_random_uuid(),
    'john_doe',
    'john@example.com',
    'John',
    'Doe'
);
-- Returns: pk_user = 1, id = '123e4567-e89b-12d3-a456-426614174000', etc.

-- Retrieve by PK (fastest lookup)
SELECT * FROM tb_user WHERE pk_user = 1;
```

### **3.2. API Exposure (UUID)**
Expose `id` in API responses and use it for endpoint routing.

**API Endpoint:**
```
GET /api/users/{uuid}
```
**Query:**
```sql
-- Lookup by UUID (indexed for speed)
SELECT * FROM tb_user WHERE id = '123e4567-e89b-12d3-a456-426614174000';
```

### **3.3. User-Facing URLs (Slug)**
Use `username` for friendly URLs and routing.

**URL Example:**
```
GET /users/john_doe
```
**Query:**
```sql
-- Lookup by username (indexed)
SELECT * FROM tb_user WHERE username = 'john_doe';
```

### **3.4. Cross-Reference Queries**
Join or correlate identifiers as needed (e.g., updating a record via API UUID but fetching data via slug).

```sql
-- Update a user via UUID but fetch their PK for database operations
UPDATE tb_user
SET first_name = 'Jonathan'
WHERE id = '123e4567-e89b-12d3-a456-426614174000';

-- Fetch another record (e.g., related entity) by PK
SELECT * FROM tb_post WHERE user_pk = (SELECT pk_user FROM tb_user WHERE username = 'jane_smith');
```

---

## **4. Implementation Guidelines**

### **4.1. Database Layer**
- **Primary Key (`pk_user`):**
  - Use `SERIAL` or `BIGSERIAL` for autogeneration.
  - Optimize for joins and foreign key constraints.
- **UUID (`id`):**
  - Add a unique index (`idx_user_id`) to speed up API lookups.
  - Avoid generating UUIDs in application code (use database functions).
- **Slug (`username`):**
  - Enforce uniqueness with `UNIQUE` constraint.
  - Use a `CHECK` constraint for slug validation (e.g., no spaces, hyphens only):
    ```sql
    ALTER TABLE tb_user ADD CONSTRAINT chk_username_format
    CHECK (username ~ '^[a-z0-9_-]+$');
    ```

### **4.2. Application Layer**
- **API Contracts:**
  - Return `id` in all API responses (e.g., `200 OK: { "id": "123e4567...", "username": "john_doe"}`).
  - Use UUIDs in endpoint paths (e.g., `/api/users/123e4567...`).
- **URL Routing:**
  - Map slugs to controller actions (e.g., `users_controller.show(:username)`).
  - Redirect invalid slugs to a `404` or `410`.
- **User Input Handling:**
  - Sanitize slugs (e.g., convert `John Doe` → `john_doe`).
  - Generate UUIDs server-side (never trust client-generated UUIDs).

### **4.3. Migration Strategy**
- **Existing Databases:**
  - Add `id` and `username` as new columns (backfill UUIDs with `gen_random_uuid()`).
  - Update application logic to resolve cross-identifier lookups:
    ```sql
    -- Example: Add a generated UUID to existing records
    UPDATE tb_user SET id = gen_random_uuid();
    CREATE INDEX idx_user_id ON tb_user (id);
    ```
- **New Projects:**
  - Design the Trinity Pattern from the outset to avoid refactoring.

---

## **5. Query Performance Considerations**
| Operation               | Identifier Used | Complexity | Notes                                  |
|-------------------------|-----------------|------------|----------------------------------------|
| Insert                  | `pk_user`       | O(1)       | Auto-incremented.                      |
| Read (internal)         | `pk_user`       | O(log n)   | Fastest lookup.                        |
| Read (API)              | `id`            | O(log n)   | UUID index speeds up lookups.          |
| Read (URL)              | `username`      | O(log n)   | Slug index ensures quick routing.      |
| Update/Delete           | Any             | O(log n)   | Use the identifier most relevant to the context. |

**Avoid Anti-Patterns:**
- ❌ **Deriving `id` from `pk_user`**: Breaks UUID randomness.
- ❌ **Using `pk_user` in URLs**: Unfriendly and guessable.
- ❌ **Ignoring indexes**: Always index `id` and `username`.

---

## **6. Related Patterns**
| Pattern               | Purpose                                                      | When to Use                          |
|-----------------------|-------------------------------------------------------------|--------------------------------------|
| **[UUIDs for APIs](https://www.uuid.dev/)** | Standard for public-facing IDs.                             | When exposing records via REST/gRPC. |
| **[Slug-Based Routing](https://www.alexkohler.net/blog/url-friendly-id-generators/)** | Human-readable URLs.                                        | Frontend or SEO-sensitive apps.      |
| **[Composite Keys](https://use-the-index-luke.com/sql/composite-and-covered-indexes)** | Multi-column uniqueness.                                    | When one identifier isn’t sufficient. |
| **[Immutable IDs](https://martinfowler.com/articles/immutable-model.html)** | Preventing optimistic concurrency conflicts.                | High-concurrency systems.            |

---

## **7. Example Workflow**
1. **User Signup:**
   - Database assigns:
     - `pk_user = 1` (internal)
     - `id = "123e4567-e89b-12d3-a456-426614174000"` (API)
     - `username = "john_doe"` (URL)
   - Application returns:
     ```json
     {
       "id": "123e4567-e89b-12d3-a456-426614174000",
       "username": "john_doe",
       "email": "john@example.com"
     }
     ```
2. **API Read:**
   - Client fetches `/api/users/123e4567-e89b-12d3-a456-426614174000`.
   - Database looks up by `id`.
3. **User Profile:**
   - Client accesses `/users/john_doe`.
   - Application fetches data via `username`.

---

## **8. Trade-offs**
| Benefit                          | Cost                                | Mitigation                          |
|----------------------------------|-------------------------------------|-------------------------------------|
| Fast database operations         | UUIDs increase storage by ~16 bytes | Use `BIGUUID` if needed.            |
| Non-guessable API IDs            | Slightly longer URLs                | Slugs remain concise (e.g., `5 chars`). |
| Human-readable URLs              | Requires slug generation logic      | Use libraries (e.g., `slugify` in Node.js). |

---

## **9. Tools & Libraries**
- **Database:**
  - PostgreSQL: `gen_random_uuid()`.
  - MySQL: `UUID()` or `SHA2()` for UUIDs.
- **Application:**
  - **Node.js**: `uuid` package, `slugify` for slugs.
  - **Python**: `uuid` module, `inflect` for slugs.
  - **Ruby**: `uuid` gem, `slugged` gem.
- **ORM:**
  - Django: Use `UUIDField` + custom slug handling.
  - Laravel: `Str::slug()` for slugs, `uuid()` for IDs.

---
**Last Updated:** [Insert Date]
**Author:** [Your Name]