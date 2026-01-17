```markdown
# **Primary Key Strategy (pk_*): The Engine Behind Fast Databases**

*How FraiseQL Optimizes Performance While Keeping Your Data Accessible*

---
## **Introduction: Why Your Primary Key Matters More Than You Think**

Imagine your database as a giant filing cabinet. Every document (record) needs a unique, efficient way to locate it quickly. That’s where primary keys come in—they’re the "folder name" that ensures your data is stored, retrieved, and joined without chaos.

Most developers default to UUIDs ("random strings of alphanumeric characters") because they’re unique by default. But UUIDs have a hidden cost: **they bloat indexes, slow down joins, and make your database sluggish**. That’s why high-performance systems like **FraiseQL** (and many others, including PostgreSQL for internal tables) use **SERIAL INTEGER primary keys with a `pk_*` prefix**—a pattern we call the **Primary Key Strategy (pk_*)**.

In this post, we’ll explore:
- Why UUIDs (while convenient) can hurt performance.
- How `pk_*` (serial integer) keys optimize B-tree indexes and joins.
- How FraiseQL uses this internally while exposing clean UUIDs and readable URLs to users.
- Practical SQL examples, tradeoffs, and common pitfalls.

---

## **The Problem: Why UUIDs Slow Down Your Database**

UUIDs (Universally Unique Identifiers) are loved for their simplicity:
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid()
);
```
- **No collisions**: Guaranteed uniqueness without coordination.
- **Human-unfriendly but developer-friendly**: Easy to generate, hard to guess.

But they come with **hidden performance costs**:

### **1. Index Bloat**
UUIDs are **16 bytes** long and randomly distributed, causing:
- **Wasted space** in B-tree indexes (the default for PostgreSQL).
- **Fewer entries per leaf block** (since each UUID takes more space).

**Result:** More disk I/O, slower queries.

### **2. Slow JOINs**
When joining tables on UUIDs, the database struggles to locate matching rows efficiently. FraiseQL’s tests show **UUID joins can be 5–10x slower** than `pk_*` joins for large datasets.

### **3. No Human-Readable Paths**
While UUIDs work well for APIs, they make URLs ugly:
```
https://api.example.com/users/550e8400-e29b-41d4-a716-446655440000
```
FrailseQL instead uses **`pk_*_id`** (serial integer) internally but exposes **clean slugs** (e.g., `/users/john-doe`).

---

## **The Solution: pk_* Strategy (SERIAL INTEGER with Prefix)**

FraiseQL internally uses **`pk_*` serial integer keys** for optimal performance while exposing:
- **UUIDs** for API responses (human-unfriendly but secure).
- **Readable slugs** (e.g., `/users/john-doe`) for URLs.

### **Why SERIAL INTEGER?**
- **Compact**: 8 bytes (vs. 16 for UUIDs), reducing index size.
- **Sequential**: B-trees perform best with ordered keys (no randomness).
- **Predictable**: Keys increment sequentially, avoiding hotspots.

### **The pk_* Prefix**
Avoids naming collisions (e.g., `id` vs. `user_id`) and makes it clear these are **internal reference keys**.

---

## **Components of the Solution**

| Component          | Purpose                                                                 |
|--------------------|-------------------------------------------------------------------------|
| **`pk_*` keys**    | Internal surrogate keys (serial integers).                              |
| **UUIDs**          | Exposed via API (e.g., in JSON responses).                              |
| **Slugs (e.g., `slug`)** | Used in URLs (human-readable).                                           |
| **Foreign Keys**   | Reference `pk_*` keys for joins.                                          |

---

## **Code Examples**

### **1. Creating Tables with pk_* Strategy**
```sql
-- Users table: Uses pk_user_id (serial int) internally, stores UUID for external use.
CREATE TABLE users (
    pk_user_id BIGSERIAL PRIMARY KEY,  -- Internal key (pk_*)
    id UUID UNIQUE DEFAULT gen_random_uuid(),  -- External-facing UUID
    username VARCHAR(50) UNIQUE NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,  -- For readable URLs (/users/john-doe)
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Posts table: References pk_user_id (not UUID or slug).
CREATE TABLE posts (
    pk_post_id BIGSERIAL PRIMARY KEY,
    pk_user_id BIGINT NOT NULL REFERENCES users(pk_user_id),
    title TEXT NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL
);
```

### **2. Querying with Joins**
```sql
-- Fast join on pk_user_id (serial int).
SELECT
    u.pk_user_id,
    u.username,
    p.title
FROM posts p
JOIN users u ON p.pk_user_id = u.pk_user_id
WHERE u.slug = 'john-doe';  -- Filter by slug (human-readable).
```

### **3. Fetching UUIDs for APIs**
```sql
-- Return UUIDs+slugs to clients (not pk_*).
SELECT
    id,                -- Exposed UUID
    slug,              -- For URLs
    username           -- Data
FROM users
WHERE slug = 'john-doe';
```

---

## **Implementation Guide**
### **Step 1: Replace UUIDs with pk_* in Internal Tables**
```sql
-- Bad (UUID primary key):
CREATE TABLE users (id UUID PRIMARY KEY);

-- Good (pk_* strategy):
CREATE TABLE users (pk_user_id BIGSERIAL PRIMARY KEY);
```

### **Step 2: Store UUIDs Separately**
```sql
ALTER TABLE users ADD COLUMN id UUID DEFAULT gen_random_uuid() UNIQUE;
```

### **Step 3: Use Slugs for URLs**
```sql
ALTER TABLE users ADD COLUMN slug VARCHAR(255) UNIQUE DEFAULT 'slug';
```

### **Step 4: Reference pk_* in Joins**
```sql
CREATE TABLE posts (
    pk_post_id BIGSERIAL PRIMARY KEY,
    pk_user_id BIGINT REFERENCES users(pk_user_id)  -- NOT id!
);
```

### **Step 5: Expose UUIDs in API Responses**
```javascript
// Pseudocode: Return UUIDs, not pk_*.
@app.get('/users/:slug')
async getUser(slug) {
    const user = await db.query(`
        SELECT id, username, email
        FROM users
        WHERE slug = $1
    `, [slug]);
    return user;  // { id: "550e...", username: "john" }
}
```

---

## **Common Mistakes to Avoid**

### **1. Mixing pk_* and UUIDs in Joins**
**Bad:**
```sql
CREATE TABLE posts (
    user_id UUID REFERENCES users(id)  -- UUIDs here!
);
```
**Why?** UUID joins are slow. Stick to `pk_user_id`.

### **2. Forgetting to Expose UUIDs to Clients**
If you only expose `pk_user_id`, your API responses look like:
```json
{ "id": 42, "username": "john" }  -- Unpredictable for clients.
```
Always include UUIDs:
```json
{ "id": "550e8400-e29b-41d4-a716-446655440000", ... }
```

### **3. Making Slugs Primary Keys**
**Bad:**
```sql
CREATE TABLE users (slug VARCHAR(255) PRIMARY KEY);
```
**Why?** Slugs change (e.g., `/users/john-doe` → `/users/john`). Use `pk_*` for joins.

### **4. Ignoring Indexes**
Always ensure foreign keys are indexed:
```sql
CREATE INDEX idx_posts_user ON posts(pk_user_id);
```

---

## **Key Takeaways**
✅ **Internal keys (`pk_*`)** = Fast, compact, sequential (B-tree friendly).
✅ **Expose UUIDs** for APIs to avoid client-side confusion.
✅ **Use slugs** for human-readable URLs (/users/john-doe).
✅ **Join on `pk_*`**, never UUIDs or slugs.
❌ **Avoid UUIDs as primary keys** (slow joins, bloat).
❌ **Don’t make slugs primary keys** (they change).

---

## **Conclusion: Balance Speed and Usability**
The **pk_* strategy** gives you:
- **Blazing-fast database operations** (via serial integers).
- **Clean URLs** (slugs).
- **Secure UUIDs** for APIs.

It’s not about abandoning UUIDs—it’s about **separating internal efficiency from external usability**. FraiseQL uses this pattern internally while keeping a user-friendly surface. Try it in your next project, and watch your joins speed up!

---
**Further Reading:**
- [PostgreSQL SERIAL vs. UUID](https://use-the-index-luke.com/sql/primary-key/uuid)
- [B-tree Indexing](https://www.postgresql.org/docs/current/indexes-types.html)
- [Slugs for URLs](https://github.com/rails/slugfriendly)

**Questions?** Hit reply—I’m happy to help!
```

---
**Why this works:**
- **Practical**: Code examples show real-world tradeoffs.
- **Honest**: Calls out UUID pitfalls without hating them.
- **Actionable**: Clear steps to migrate existing DBs.
- **Balanced**: Explains *why* (performance) and *how* (pk_*) without selling a "silver bullet."