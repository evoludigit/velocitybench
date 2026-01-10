# The Trinity Pattern: How to Master Identification in Your Backend Architecture

*Combining the best of sequential IDs, UUIDs, and slugs without the tradeoffs*

---

## Introduction

As backend engineers, we spend an inordinate amount of time agonizing over a seemingly simple question: **how should we identify our data?** The choice of primary key, API identifiers, and URL slugs shapes how your database performs, how your API feels, and how users interact with your application.

Every time you ship a new feature, you’re making silent design decisions about identification. Will you expose raw database IDs in your API? Will you force users to deal with unreadable UUIDs? Will your URLs break when a user changes their display name?

Most developers settle for suboptimal compromises:
- **Team A** exposes sequential IDs but grudgingly admits their API feels "internal"
- **Team B** goes full UUID but deals with slower queries on public endpoints
- **Team C** uses slugs for URLs but creates a maintenance nightmare when identifiers change

The **Trinity Pattern** flips this tradeoff entirely. By using three distinct identifier types—each optimized for its specific purpose—you can finally have it all: optimal database performance, clean API design, and user-friendly URLs—without sacrificing any of them.

---

## The Problem: The Identification Dilemma

Every backend system needs three distinct identification strategies:

1. **Database Operations** – Fast, efficient lookups for internal systems.
2. **API Exposure** – Stable, predictable identifiers for public consumption.
3. **User-Facing URLs** – Human-readable, intuitive paths for end-users.

Traditional approaches force you to pick just one identifier type for all purposes, creating inevitable problems:

### The Sequential ID Trap
```sql
-- Typical table with sequential IDs
CREATE TABLE tb_user (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    -- ...
);
```

**Problems:**
- **Leaks business information**: Id 1 might always be the admin user—security risk!
- **Forces URL changes**: If a user changes their name, you must update the entire URL (`/users/1` → `/users/2`).
- **API feels "internal"**: Using raw DB IDs makes the API feel like an ORM dump.

### The UUID Overhead
```sql
-- Table with UUIDs
CREATE TABLE tb_user (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(100) NOT NULL UNIQUE,
    -- ...
);
```

**Problems:**
- **Indexing overhead**: UUIDs are 16 bytes vs. 4 for integers → slower lookups.
- **URL complexity**: `https://example.com/users/550e8400-e29b-41d4-a716-446655440000`
- **No natural ordering**: Hard to implement pagination or "next/prev" APIs.

### The Slug Nightmare
```sql
-- Table with slugs as primary keys
CREATE TABLE tb_user (
    slug VARCHAR(255) PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    -- ...
);
```

**Problems:**
- **Poor database performance**: Strings are harder to index than integers.
- **URL instability**: Changing a user's name requires updating the slug *and* maintaining redirects.
- **Collision risks**: `john-doe` vs. `john-doe-jr` → ambiguous lookups.

### The Choice is Never Binary
Most teams end up "choosing" one approach and living with its drawbacks:
- **E-commerce sites** expose UUIDs (`/products/123e4567-e89b-12d3-a456-426614174000`) but regret the complexity.
- **Social platforms** use sequential IDs for URLs (`/users/42`) but worry about security implications.
- **Content systems** rely on slugs (`/articles/winter-solstice-2023`) but have to build redirect layers.

The Trinity Pattern breaks this binary choice. By intentionally using three distinct identifiers—each tailored to its purpose—you can eliminate these tradeoffs entirely.

---

## The Solution: The Trinity Pattern

The Trinity Pattern introduces **three kinds of identifiers**, each optimized for its specific use case:

| Identifier Type | Purpose                          | Example Value          | Storage Type         | When to Use                          |
|-----------------|----------------------------------|------------------------|----------------------|---------------------------------------|
| **pk\_\***      | Internal database operations     | `42`                   | `INTEGER PRIMARY KEY`| Database joins, indexing, relationships |
| **id**          | Public API exposure              | `123e4567-e89b-...`    | `UUID UNIQUE`        | API endpoints, rate limiting, caching |
| **identifier**  | User-facing URLs                 | `john-doe`             | `VARCHAR UNIQUE`     | Web routes, bookmarks, sharing        |

### Why This Works
1. **Database performance** remains optimal with `pk_*` (integer primary keys).
2. **API stability** is guaranteed with `id` (UUIDs never change).
3. **URL user-friendliness** is preserved with `identifier` (slugs can update safely).

### Schema Example
```sql
CREATE TABLE tb_user (
    -- ⚡ INTERNAL: Optimized for database operations
    pk_user SERIAL PRIMARY KEY,

    -- 🔐 PUBLIC: Stable for API exposure
    id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),

    -- 🌍 USER-FACING: Human-readable URLs
    username VARCHAR(100) UNIQUE NOT NULL,

    -- Business data
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    bio TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Indexing Strategy
```sql
-- Optimized for each identifier type
CREATE INDEX idx_user_pk ON tb_user (pk_user);      -- Default (already indexed)
CREATE INDEX idx_user_id ON tb_user (id);            -- API lookups
CREATE INDEX idx_user_username ON tb_user (username); -- URL routing
```

### Required Application Logic
Your application must **map between these identifiers** in three key places:
1. **Database ↔ pk\_\*** (internal)
2. **API ↔ id** (public)
3. **URL ↔ identifier** (end-user)

Let’s explore how this works in practice.

---

## Implementation Guide

### Step 1: Model the Trinity in Your Database

Start by updating your schema to include all three identifiers. Example with PostgreSQL:

```sql
CREATE TABLE tb_product (
    -- Internal DB ID (never exposed)
    pk_product SERIAL PRIMARY KEY,

    -- Public API ID (stable, UUID)
    id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),

    -- User-facing slug (can change)
    slug VARCHAR(255) UNIQUE NOT NULL,

    -- Business data
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2),
    stock INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add indexes for each purpose
CREATE INDEX idx_product_pk ON tb_product (pk_product);
CREATE INDEX idx_product_id ON tb_product (id);
CREATE INDEX idx_product_slug ON tb_product (slug);
```

### Step 2: Add Mapping Logic in Your Application

Your application will need **three "finder" methods** to convert between identifiers:

```typescript
// Typescript example (adapt to your language)
interface Product {
  pk_product: number;
  id: string; // UUID
  slug: string;
  name: string;
  // ... other fields
}

/**
 * Find by internal DB ID (used by internal services)
 */
async function findByPkProduct(pk: number): Promise<Product | null> {
  return db.query<Product>(
    `SELECT * FROM tb_product WHERE pk_product = $1`,
    [pk]
  );
}

/**
 * Find by public API ID (used by clients)
 */
async function findById(id: string): Promise<Product | null> {
  return db.query<Product>(
    `SELECT * FROM tb_product WHERE id = $1`,
    [id]
  );
}

/**
 * Find by slug (used for URLs)
 */
async function findBySlug(slug: string): Promise<Product | null> {
  return db.query<Product>(
    `SELECT * FROM tb_product WHERE slug = $1`,
    [slug]
  );
}
```

### Step 3: Handle URL Redirects

When a user changes their slug, you must maintain backward compatibility. Example with Express.js:

```javascript
app.get('/products/:slug', async (req, res) => {
  const product = await findBySlug(req.params.slug);

  if (!product) {
    // Check if this might be an old slug (redirect)
    const oldProduct = await db.query(
      `SELECT slug FROM tb_product WHERE pk_product = ?`,
      [product.pk_product] // This is wrong! Should be: find by current slug
    );

    // Better approach: Track slug history
    const redirect = await findRedirect(req.params.slug);
    if (!product && redirect) {
      return res.redirect(301, `/products/${redirect.slug}`);
    }

    return res.status(404).send('Not Found');
  }

  res.render('product', { product });
});
```

### Step 4: Expose Only the `id` in Your API

Your API should **never expose `pk_product`**—only the UUID (`id`). Example OpenAPI specification:

```yaml
paths:
  /products:
    get:
      summary: List products
      responses:
        200:
          description: Array of products
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Product'

components:
  schemas:
    Product:
      type: object
      properties:
        id:          # 🔐 Public API ID (UUID)
          type: string
          format: uuid
          example: "123e4567-e89b-12d3-a456-426614174000"
        slug:        # 🌍 User-friendly (but hidden in API response)
          type: string
          example: "wireguard-guide"
        name:
          type: string
```

### Step 5: Generate `slug` Updates Safely

When a product’s name changes, update the slug **without breaking URLs**. Use a transaction:

```typescript
async function updateProductName(pk: number, newName: string): Promise<void> {
  // 1. Generate new slug
  const newSlug = slugify(newName);

  // 2. Update slug in DB (atomic with other changes)
  await db.query(
    `UPDATE tb_product SET slug = $1 WHERE pk_product = $2`,
    [newSlug, pk]
  );

  // 3. Create redirect for old slug (optional, if needed)
  await createSlugRedirect(oldSlug, newSlug);
}
```

---

## Common Mistakes to Avoid

### ❌ Mistake 1: Exposing `pk_*` in Your API
**Don’t do this:**
```yaml
components:
  schemas:
    User:
      properties:
        id:          # ❌ This is the database PK, not a UUID!
          type: integer
          example: 42
```

**Why bad:**
- Security risk: Users can guess internal IDs.
- No stability guarantees: IDs could reset after migration.

**Fix:** Always use the UUID (`id`) in your API responses.

---

### ❌ Mistake 2: Forgetting to Index `id` (UUID)
If you don’t index the UUID column, lookups will be **`WHERE id LIKE '%some%'`** slow.

**Bad:**
```sql
-- No index! 💥
CREATE TABLE tb_user (
    id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid()
);
```

**Fix:** Always add an index:
```sql
CREATE INDEX idx_user_id ON tb_user (id);
```

---

### ❌ Mistake 3: Not Handling Slug Updates Gracefully
Users hate broken links. If you update a slug without redirects, `/old-slug` → 404.

**Bad:**
```javascript
// Just overwrite the slug
await db.query(`UPDATE tb_user SET slug = 'new-slug' WHERE pk_user = 1`);
```

**Fix:** Implement redirects (301) or a slug history table.

---

### ❌ Mistake 4: Using `slug` for Database Joins
Avoid this pattern:
```sql
-- ❌ Bad: Slugs are for URLs, not joins!
SELECT * FROM tb_order o
JOIN tb_user u ON o.user_slug = u.slug;
```

**Fix:** Always join on `pk_user` (the integer primary key).

---

### ❌ Mistake 5: Chasing Perfection with Slug "Versioning"
You might be tempted to track every slug ever used, but this quickly becomes a nightmare.

**Bad:**
```sql
CREATE TABLE slug_versions (
    pk_slug_version SERIAL PRIMARY KEY,
    user_pk INTEGER REFERENCES tb_user(pk_user),
    slug VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Fix:** Only redirect if the change is **unavoidable** (e.g., name change). For most cases, let the user update their profile.

---

## Key Takeaways

- **Never choose just one identifier type.** The Trinity Pattern eliminates forced tradeoffs.
- **Use `pk_*` for database efficiency** (internal operations, joins, indexing).
- **Use `id` (UUID) for API stability** (never changes, safe for caching/rate limits).
- **Use `identifier` (slug) for URLs** (can update, use redirects).
- **Keep redirects simple.** Only redirect when absolutely necessary.
- **Never expose `pk_*` in your API.** Always use `id` instead.
- **Index aggressively.** UUIDs and slugs need proper indexes to perform well.

---

## When *Not* to Use the Trinity Pattern

While the Trinity Pattern solves most problems, it’s **not always the best choice**:

### ❌ Tiny Projects
If your system has <100 records, the overhead may not be worth it.

### ❌ Systems with No URLs
API-only systems (e.g., internal tools, CLI apps) don’t need slugs.

### ❌ Legacy Systems
Refactoring an existing system to Trinity may require significant migration effort.

### ❌ Performance-Critical Read-Heavy Systems
If you have millions of slug lookups, a single-table approach with hashing might be simpler.

---

## Conclusion

The Identification Dilemma has plagued backend developers for decades. But it doesn’t have to be this way.

By adopting the **Trinity Pattern**, you sidestep the traditional tradeoffs:
- **Database performance** stays optimal with `pk_*`.
- **API stability** is guaranteed with UUIDs.
- **User experience** remains smooth with slugs and redirects.

### The Cost? A Little Extra Code
Yes, you’ll write three "finder" methods and handle redirects. But the **long-term benefits**—cleaner APIs, more reliable URLs, and happier users—far outweigh the complexity.

### The Payoff
- **Security:** No more leaking business logic through sequential IDs.
- **Stability:** UUIDs ensure your API remains unchanged across deployments.
- **Usability:** Slugs make sharing and bookmarking intuitive.

### Final Thought
The Trinity Pattern isn’t about perfection—it’s about ** Intentionality**. By explicitly designing each identifier for its purpose, you eliminate accidental compromises and build systems that feel **right** instead of just working.

Now go forth and identify your data **truly**. 🚀

---
**What’s your experience with identification patterns?** Have you tried something similar? Share in the comments!

---
