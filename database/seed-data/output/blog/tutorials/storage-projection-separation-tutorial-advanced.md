```markdown
# **Storage-Projection Separation: Decoupling Your Database Schema from Your API Contracts**

*How FraiseQL lets you evolve your data model independently from your API while serving multiple business views*

---

## **Introduction**

In modern backend systems, the gap between your database schema and your API contracts is often a source of technical debt. As your application grows, you might start exposing storage tables directly in your API—only to later discover that these raw tables don’t align with your business logic. Maybe a single API caller needs a denormalized view of your data, while another requires an entirely different projection. Or perhaps your database schema evolves faster than your API contracts can keep up.

This is where the **Storage-Projection Separation** pattern comes in. Popularized by systems like **FraiseQL**, this pattern explicitly separates normalized storage tables (owned by DBAs and data engineers) from denormalized projections (owned by API designers). By doing so, you enable:
- **Independent schema evolution** – Your database can change without breaking APIs (or vice versa).
- **Multiple API shapes** – A single dataset can serve different business views.
- **Performance optimization** – Projections can be precomputed for common queries.

This isn’t just an academic idea—it’s a battle-tested approach used at scale in systems like **Airbnb’s API layer** and **Shopify’s data pipelines**. In this guide, we’ll explore:
1. **The problem** with exposing storage tables directly.
2. **How FraiseQL solves it** with a clean separation.
3. **Practical implementations** (PostgreSQL, SQL Server, and application-layer examples).
4. **Common pitfalls** and how to avoid them.

Let’s dive in.

---

## **The Problem: Coupling Storage and API**

When your API exposes raw database tables, you’re effectively **hardcoding your business logic into your data model**. Here’s why this is problematic:

### **1. APIs Become Brittle**
If your database schema changes (e.g., adding a column or refactoring a table), your API contracts may break, even if the underlying data semantics remain the same.

**Example:**
```sql
-- Old schema (exposed in API)
CREATE TABLE user_profiles (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50),
    email VARCHAR(100),
    last_login TIMESTAMP
);
```

Now, a business requirement arises to **split `user_profiles` into two tables** (`users` and `profile_data`) for better normalization:

```sql
-- New schema (incompatible with old API)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50),
    email VARCHAR(100)
);

CREATE TABLE profile_data (
    user_id INT REFERENCES users(id),
    last_login TIMESTAMP
);
```

Suddenly, your API that previously returned `user_profiles` now fails because the structure has changed. Worse yet, you might need to **deprecate old APIs** while maintaining backward compatibility, leading to duplicate code.

### **2. Poor Performance for Complex Queries**
Modern applications often need **denormalized, filtered, or aggregated data**—things that aren’t naturally represented in a normalized storage schema. Querying this directly from the database forces inefficient `JOIN` hell or application-layer transformations.

**Example: A "User with Orders" API**
```sql
-- Raw query (inefficient for APIs)
SELECT u.id, u.username, o.order_id, o.amount
FROM users u
JOIN orders o ON u.id = o.user_id
WHERE o.status = 'completed';
```
This often leads to:
- **N+1 queries** (if the API fetches users and orders separately).
- **Large payloads** (if the API returns all columns, even if the client only needs a few).
- **Application-side filtering**, which defeats database optimizations.

### **3. Single Source of Truth Strain**
When DBAs and API designers work in silos, you end up with:
- **Duplicate data** (e.g., storing a `user_full_name` in both the database and the API cache).
- **Inconsistent projections** (e.g., an API returning `user.name` while the database stores `user.first_name || ' ' || user.last_name`).
- **Hard-to-debug synchronization issues** (e.g., a cache miss causing the API to fetch stale data).

---
## **The Solution: Storage-Projection Separation**

The core idea is to **decouple storage from presentation**:
- **Storage tables (`tb_*`)** – Owned by DBAs, optimized for **ACID compliance, normalization, and long-term data integrity**.
- **Projection views (`v_*`)** – Owned by API designers, optimized for **specific business queries, performance, and API contracts**.

This separation allows:
✅ **Independent evolution** – Change the database without breaking APIs (or vice versa).
✅ **Performance optimizations** – Precompute common aggregations or denormalize for fast reads.
✅ **Multiple API shapes** – Serve different clients with different data structures from the same source.

### **FraiseQL’s Approach**
FraiseQL (a SQL-based data virtualization layer) implements this pattern by:
1. **Abstracting storage tables** behind a unified schema.
2. **Allowing projections to reference other projections** (like a graph of views).
3. **Supporting incremental refreshes** (e.g., only updating changed rows).

Let’s see how this looks in practice.

---

## **Code Examples: Implementing Storage-Projection Separation**

### **1. Storage Layer (PostgreSQL Example)**
First, define normalized storage tables (owned by DBAs):

```sql
-- tb_users: Storage table (DBA-owned)
CREATE TABLE tb_users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- tb_orders: Storage table (DBA-owned)
CREATE TABLE tb_orders (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES tb_users(id),
    amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### **2. Projection Layer (API-Owned Views)**
Now, define **denormalized, optimized views** for different API needs:

#### **Projection 1: "User Profile" (Simple API)**
```sql
-- v_user_profile: Projection for user profile API
CREATE OR REPLACE VIEW v_user_profile AS
SELECT
    tu.id,
    tu.username,
    tu.email,
    -- Derived field (denormalized for API)
    tu.username || '@example.com' AS user_email_domain,
    -- Filter out deleted users
    CASE WHEN tu.deleted_at IS NULL THEN tu.created_at ELSE NULL END AS active_since
FROM
    tb_users tu
WHERE
    tu.deleted_at IS NULL;
```

#### **Projection 2: "User with Order Stats" (Analytics API)**
```sql
-- v_user_order_stats: Projection for analytics dashboard
CREATE OR REPLACE VIEW v_user_order_stats AS
SELECT
    tu.id,
    tu.username,
    COUNT(to.id) FILTER (WHERE to.status = 'completed') AS completed_orders,
    SUM(to.amount) FILTER (WHERE to.status = 'completed') AS total_spent,
    MAX(to.created_at) AS last_order_date
FROM
    tb_users tu
LEFT JOIN
    tb_orders to ON tu.id = to.user_id
GROUP BY
    tu.id, tu.username;
```

#### **Projection 3: "Public User List" (Frontend API)**
```sql
-- v_public_user_list: Projection for frontend (no sensitive data)
CREATE OR REPLACE VIEW v_public_user_list AS
SELECT
    tu.id,
    tu.username,
    -- Mask email for public view
    CONCAT(SUBSTRING(tu.email FROM 1 FOR 3), '****') AS masked_email
FROM
    tb_users tu
WHERE
    tu.deleted_at IS NULL;
```

### **3. Querying Projections via API**
Your application can now query these views directly, without exposing `tb_users` or `tb_orders`:

```sql
-- Example: Fetch user profile (via API)
SELECT * FROM v_user_profile WHERE username = 'alice';
```

```json
// API Response
{
  "id": 1,
  "username": "alice",
  "email": "alice@example.com",
  "user_email_domain": "alice@example.com",
  "active_since": "2023-01-15T10:00:00Z"
}
```

### **4. Application-Layer Projection (Alternative)**
If your database doesn’t support views (e.g., MongoDB), you can implement projections in your application code:

#### **Python (FastAPI Example)**
```python
from pydantic import BaseModel
from typing import List
from fastapi import FastAPI

app = FastAPI()

# Storage model (DBA-owned)
class UserStorage(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

# Projection model (API-owned)
class UserProfile(BaseModel):
    id: int
    username: str
    user_email_domain: str
    active_since: datetime | None

@app.get("/users/{username}", response_model=UserProfile)
async def get_user_profile(username: str):
    # Query storage (DBA-owned)
    user = await db.get_user_by_username(username)

    if not user:
        raise HTTPException(404, "User not found")

    # Apply projection logic (API-owned)
    return UserProfile(
        id=user.id,
        username=user.username,
        user_email_domain=f"{user.username}@example.com",
        active_since=user.created_at if user.deleted_at is None else None
    )
```

---

## **Implementation Guide**

### **Step 1: Define Storage Tables (DBA Ownership)**
- Use **normalized schemas** (3NF or higher).
- Include **soft-delete flags** (`deleted_at`) for flexibility.
- Add **indexes** for common queries (DBAs know best here).

### **Step 2: Design Projections (API Ownership)**
For each API contract:
1. **Identify the denormalized fields** your API needs.
2. **Write a view** that filters, aggregates, or transforms the data.
3. **Test edge cases** (e.g., `NULL` handling, empty results).

**Example: Handling NULLs in Projections**
```sql
-- Safe projection with COALESCE
CREATE OR REPLACE VIEW v_user_stats AS
SELECT
    tu.id,
    tu.username,
    COALESCE(SUM(to.amount), 0) AS lifetime_spent
FROM
    tb_users tu
LEFT JOIN
    tb_orders to ON tu.id = to.user_id
GROUP BY
    tu.id, tu.username;
```

### **Step 3: Version Your Projections**
Use **database versions** or **feature flags** to manage schema changes:

```sql
-- Adding a new projection version
CREATE OR REPLACE VIEW v_user_orders_v2 AS
SELECT
    tu.id,
    tu.username,
    to.order_id,
    to.amount,
    to.status,
    -- New field for tracking promotions
    to.promo_code
FROM
    tb_users tu
JOIN
    tb_orders to ON tu.id = to.user_id;
```

### **Step 4: Cache Projections (Optional)**
For high-traffic APIs, cache projections:
- **Database-level**: Use `REFRESH MATERIALIZED VIEW CONCURRENTLY` (PostgreSQL).
- **Application-level**: Cache results with Redis or CDN.

**PostgreSQL MATERIALIZED VIEW Example**
```sql
CREATE MATERIALIZED VIEW mv_daily_user_stats AS
SELECT
    DATE(created_at) AS day,
    COUNT(DISTINCT user_id) AS active_users
FROM
    tb_user_activity_logs
GROUP BY
    DATE(created_at);

-- Refresh periodically
REFRESH MATERIALIZED VIEW mv_daily_user_stats;
```

---

## **Common Mistakes to Avoid**

### **❌ Mistake 1: Overloading Projections with Business Logic**
**Problem**:
Putting complex business rules (e.g., "discounts for first-time buyers") in SQL views makes them hard to maintain.

**Fix**:
- Keep views **purely data transformations**.
- Move business logic to **application code** or **separate microservices**.

### **❌ Mistake 2: Not Updating Projections When Storage Changes**
**Problem**:
If you modify `tb_users` but forget to update `v_user_profile`, your API returns incorrect data.

**Fix**:
- **Document dependencies** between storage and projections.
- Use **schema migration tools** (e.g., Flyway, Alembic) to alert when related views need updates.

### **❌ Mistake 3: Creating Too Many Projections**
**Problem**:
Every API getting its own view leads to:
- **Duplicate code** (similar views with minor differences).
- **Hard-to-maintain schema** (e.g., 50 `v_user_*` views).

**Fix**:
- **Share common projections** (e.g., `v_core_user_data`).
- **Use view inheritance** (PostgreSQL `WITH RECURSIVE` or app-layer composition).

### **❌ Mistake 4: Ignoring Performance**
**Problem**:
Writing views like `SELECT * FROM tb_users JOIN tb_orders` without optimization kills query performance.

**Fix**:
- **Pre-filter** in the view (e.g., `WHERE status = 'active'`).
- **Leverage indexes** (e.g., `CREATE INDEX ON tb_orders(user_id, status)`).
- **Materialize** frequently accessed projections.

### **❌ Mistake 5: Not Testing Projection Updates**
**Problem**:
Changing a storage table might break a projection without you realizing it.

**Fix**:
- **Write integration tests** for projections.
- Use **schema diff tools** (e.g., `pg_dump` diffs) to catch breaking changes.

---

## **Key Takeaways**

| **Aspect**               | **Storage Layer (DBA)**                          | **Projection Layer (API)**                      |
|--------------------------|------------------------------------------------|------------------------------------------------|
| **Ownership**            | DBAs, data engineers                           | API designers, frontend teams                 |
| **Schema Style**         | Normalized (3NF, ACID)                         | Denormalized, optimized for queries           |
| **Performance Goal**     | Durability, consistency                        | Fast reads, minimal payloads                  |
| **Evolution Speed**      | Slow (schema migrations)                       | Fast (API contract changes)                   |
| **Example Tables**       | `tb_users`, `tb_orders`                        | `v_user_profile`, `v_user_order_stats`         |

### **When to Use Storage-Projection Separation**
✔ You have **multiple APIs** consuming the same data.
✔ Your **database schema evolves frequently**.
✔ You need **denormalized or aggregated data** for APIs.
✔ You want to **avoid exposing raw tables** to clients.

### **When to Avoid It**
❌ Your system is **small and simple** (overhead not worth it).
❌ You **rarely query the same data in multiple ways**.
❌ Your database is **read-heavy with no write conflicts**.

---

## **Conclusion**

The **Storage-Projection Separation** pattern is a powerful way to decouple your database schema from your API contracts. By maintaining two distinct layers—one for storage and one for presentation—you gain:
- **Flexibility** to evolve either layer independently.
- **Performance** through optimized projections.
- **Clarity** in ownership (DBAs vs. API teams).

### **Next Steps**
1. **Experiment with views** in your next feature.
2. **Audit your APIs** to find raw table exposures.
3. **Start small**—pick one projection to denormalize first.

Tools like **FraiseQL**, **SQLMesh**, and **RisingWave** make this pattern easier to implement at scale. If you’re working with a complex data layer, consider investing time here—it’ll save you headaches down the road.

**Have you used this pattern before? What challenges did you face? Share your thoughts in the comments!**

---
```