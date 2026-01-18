```markdown
---
title: "Storage-Projection Separation: How to Keep Your Database and APIs from Braiding Like Overcooked Spaghetti"
date: "2023-11-15"
author: "Alex Carter"
description: "Learn how the Storage-Projection Separation pattern decouples your database schema from API contracts—keeping your system flexible, maintainable, and resilient to change."
---

# Storage-Projection Separation: How to Keep Your Database and APIs from Braiding Like Overcooked Spaghetti

![Database tables and API projections side by side](https://images.unsplash.com/photo-1633356122822-e0e024d561b9?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1470&q=80)

You’ve been there. Your application starts small: a few tables, a simple API. Then something changes. Maybe a new business rule emerges. Maybe an analytics team demands a different view of the data. Or perhaps you accidentally introduce a bug when you modify a column, breaking both your database *and* your API.

This is the **storage API coupling problem**—when your database schema and API contract are glued together like overcooked spaghetti. And in the long run, that’s a recipe for headache.

In this post, I’ll introduce the **Storage-Projection Separation** pattern—a way to keep your database storage separate from the projections (like API responses or input schemas) that your application exposes. This pattern is the backbone of systems like FraiseDB, and it solves real-world problems you’ll face as your applications grow.

---

## The Problem: Why Your Database and APIs Are Likely Braided

### Coupling Leads to Fragility
Most applications start with the assumption that the database schema and the API contract are one and the same. Your `users` table has a `name` column, and your `/users` API endpoint returns a `name` field. Sounds reasonable, right?

But here’s what happens as your system scales:

1. **Business rules evolve**. The marketing team wants a "recommended_price" field in the API response, but that’s derived from the `base_price` in your database. You have to modify both the database and the API to accommodate this change.
2. **Access patterns change**. Your analytics team needs a flattened view of user orders, but your storage tables are normalized. You’re forced to either denormalize the database (hurting performance) or duplicate logic in your API (hurting maintainability).
3. **Breaking changes creep in**. You rename a column in the database to fix a typo, but the API schema hasn’t updated yet. Now your documentation is out of sync, and clients are hitting 500 errors.

This coupling forces every change—no matter how small—to ripple through both your database and your application logic. And as your team grows, the cost of coordinating these changes becomes prohibitive.

### The Consequences of Coupling
- **Slower iteration**: Every schema change requires coordination between DBAs, engineers, and product teams.
- **Higher risk**: A typo in a database migration can crash your entire API.
- **Limited flexibility**: You can’t easily experiment with new projections without touching production tables.
- **Technical debt**: Over time, your application becomes a tangled mess of workarounds to keep the database and API in sync.

---

## The Solution: Storage-Projection Separation

The Storage-Projection Separation pattern solves this problem by introducing a clear separation between:

1. **Storage tables** (`tb_*`)
   - Owned by the database team.
   - Focused on **durability, consistency, and efficiency**.
   - Evolve independently of the application logic.

2. **Projection views** (`v_*`)
   - Owned by the API/engineering team.
   - Focused on **business logic, access patterns, and API contracts**.
   - Can be modified without touching the storage layer.

### How It Works
In this pattern:
- **Storage tables** store the raw data (normalized or optimized for joins).
- **Projection views** are derived from storage tables (or other projections) and define the exact shape of API responses.
- The application queries **only the projections**, never the underlying tables. This ensures that the API contract doesn’t break when storage tables change.

This separation allows you to:
- Modify storage tables without affecting APIs (e.g., add index-only scans for performance).
- Change API responses without touching the database (e.g., add computed fields or flatten nested data).
- Experiment with new projections in development without risking production data.

---

## Components and Solutions

### 1. Storage Tables (`tb_*`)
These tables are the source of truth for your data. They are owned by the database team and focus on:
- **Normalization** (for performance and consistency).
- **Optimized queries** (e.g., partitioning, indexing).
- **Durability** (e.g., transactions, backups).

Example:
```sql
-- Storage table: Normalized, optimized for writes and joins.
CREATE TABLE tb_users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    -- Other columns...
);
```

### 2. Projection Views (`v_*`)
These views define the API contract. They are owned by the API/engineering team and focus on:
- **API responses** (e.g., flattened, filtered, or enriched data).
- **Business logic** (e.g., computed fields, aggregations).
- **Performance for reads** (e.g., materialized views, caching).

Example:
```sql
-- Projection view: Denormalized for the API, with computed fields.
CREATE VIEW v_user_profile AS
SELECT
    u.id,
    u.email,
    u.created_at,
    -- Computed field for recommended price.
    (u.base_price + (u.base_price * 0.2)) AS recommended_price,
    -- Join with orders for analytics.
    COUNT(o.id) AS total_orders
FROM tb_users u
LEFT JOIN tb_orders o ON u.id = o.user_id
GROUP BY u.id;
```

### 3. Application Layer
The application queries **only the projection views**. This ensures that:
- The API contract is stable, even if storage tables change.
- Business logic (e.g., computed fields) is encapsulated in the view.

Example in Go (using `database/sql`):
```go
// Fetch user profile via the projection view.
func GetUserProfile(db *sql.DB, userID int) (*UserProfile, error) {
    var profile UserProfile
    query := "SELECT id, email, recommended_price, total_orders FROM v_user_profile WHERE id = $1"
    err := db.QueryRow(query, userID).Scan(
        &profile.ID,
        &profile.Email,
        &profile.RecommendedPrice,
        &profile.TotalOrders,
    )
    if err != nil {
        return nil, fmt.Errorf("query failed: %v", err)
    }
    return &profile, nil
}
```

### 4. Materialized Views (Optional)
For high-performance projections, you can use **materialized views** (or tables with incremental refreshes) to pre-compute expensive calculations.

Example with PostgreSQL:
```sql
-- Materialized view: Pre-compute expensive aggregations.
CREATE MATERIALIZED VIEW mv_user_analytics AS
SELECT
    u.id,
    u.email,
    COUNT(o.id) AS total_orders,
    AVG(o.amount) AS avg_order_value
FROM tb_users u
LEFT JOIN tb_orders o ON u.id = o.user_id
GROUP BY u.id;
```

Refresh it periodically:
```sql
REFRESH MATERIALIZED VIEW mv_user_analytics;
```

---

## Implementation Guide: Step by Step

### Step 1: Start with Storage Tables
Begin by designing your storage tables as if they were a standalone data warehouse. Focus on:
- Normalization (3NF or otherwise).
- Indexes for write-heavy operations.
- Partitioning for large tables.

Example:
```sql
-- Storage table for orders, partitioned by date.
CREATE TABLE tb_orders (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES tb_users(id),
    order_date TIMESTAMP WITH TIME ZONE NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(50) NOT NULL
) PARTITION BY RANGE (order_date);
```

### Step 2: Define Projection Views
Create views that match your API responses. These can include:
- Flattened data (e.g., denormalizing foreign keys).
- Computed fields (e.g., business rules like discounts).
- Aggregations (e.g., counts, averages).

Example:
```sql
-- Projection view for the `/orders` API endpoint.
CREATE VIEW v_order_summary AS
SELECT
    o.id,
    u.email AS user_email,
    o.order_date,
    o.amount,
    -- Computed field: tax included.
    o.amount * 1.1 AS total_amount,
    -- Status translated to human-readable.
    CASE o.status
        WHEN 'pending' THEN 'Not Processed'
        WHEN 'completed' THEN 'Processed'
        ELSE 'Unknown'
    END AS status_description
FROM tb_orders o
JOIN tb_users u ON o.user_id = u.id;
```

### Step 3: Query Projections in Your Application
Always query the projection views, never the storage tables. This ensures that your API contract stays stable.

Example in Python (using `psycopg2`):
```python
import psycopg2

def get_orders_for_user(db_conn, user_id):
    with db_conn.cursor() as cur:
        cur.execute("""
            SELECT id, order_date, amount, status_description
            FROM v_order_summary
            WHERE user_id = %s
            ORDER BY order_date DESC
        """, (user_id,))
        orders = cur.fetchall()
    return orders
```

### Step 4: Handle Updates and Deletes
If your projections need to support writes (e.g., `CREATE`, `UPDATE`, `DELETE`), you have a few options:
1. **CTEs (Common Table Expressions)**: Use `WITH` clauses to handle inserts/updates.
2. **Application-side logic**: Let the app handle changes and refresh the projection.
3. **Triggers**: Automate updates to the projection when storage tables change.

Example with a CTE for inserts:
```sql
-- Insert into the projection via a CTE.
INSERT INTO v_user_profile (id, email, recommended_price)
WITH new_user AS (
    INSERT INTO tb_users (email) VALUES ('new@example.com') RETURNING id, email
)
SELECT id, email, (email_price + (email_price * 0.2)) AS recommended_price
FROM new_user;
```

### Step 5: Optimize Projections
- Use **indexes** on projection views for frequently queried fields.
- Cache projections with **Redis** or **PostgreSQL’s TTL indexes**.
- Consider **materialized views** for expensive aggregations.

Example with an index:
```sql
CREATE INDEX idx_v_order_summary_user_id ON v_order_summary(user_id);
```

---

## Common Mistakes to Avoid

### ❌ Mistake 1: Querying Storage Tables Directly
**Why it’s bad**: If your application ever queries `tb_users` instead of `v_user_profile`, a change to the storage table (e.g., adding a column) could break the API response.

**Fix**: Always query projections. Use SQL linting tools to enforce this rule.

### ❌ Mistake 2: Overloading Projections
**Why it’s bad**: If a single projection view is used by multiple APIs with different requirements, you’ll end up with a "Swiss Army knife" view that’s hard to maintain.

**Fix**: Break down projections into smaller, focused views. For example:
- `v_user_public` for public-facing APIs.
- `v_user_admin` for admin dashboards.

### ❌ Mistake 3: Ignoring Performance
**Why it’s bad**: Projections can become slow if they join too many tables or compute expensive aggregations. This defeats the purpose of separation!

**Fix**:
- Use **materialized views** for read-heavy projections.
- Cache projections in memory (e.g., Redis) or pre-compute them.
- Monitor query performance and optimize as needed.

### ❌ Mistake 4: Not Updating Projections
**Why it’s bad**: If projections aren’t refreshed when storage tables change (e.g., new orders), your API will return stale data.

**Fix**:
- For simple projections, refresh them periodically.
- For critical projections, use triggers or application-side refresh logic.

### ❌ Mistake 5: Treating Projections as Storage
**Why it’s bad**: Projections are not a substitute for storage tables. They should never contain data that isn’t in the source tables.

**Fix**: Keep projections in sync with storage. If you need to store additional data, add it to the storage tables.

---

## Key Takeaways

- **Separate concerns**: Storage tables (`tb_*`) handle raw data; projections (`v_*`) handle API contracts.
- **API stability**: Projections ensure your API contract doesn’t break when storage tables change.
- **Flexibility**: You can experiment with new projections without affecting production data.
- **Performance**: Projections can be optimized independently of storage tables (e.g., materialized views).
- **Ownership**: Storage tables are owned by DBAs; projections are owned by engineers/designers.

### When to Use This Pattern
✅ Your database and API are growing out of sync.
✅ You need to expose multiple shapes of the same data (e.g., public vs. admin APIs).
✅ Business rules require computed fields or aggregations.
✅ You want to avoid "coupling hell" as your system scales.

### When to Avoid This Pattern
❌ Your application is tiny and simple.
❌ You don’t have a database team to own storage tables.
❌ Your projections are trivial (e.g., 1:1 with storage tables).

---

## Conclusion: Build for Tomorrow, Not Just Today

The Storage-Projection Separation pattern is a simple but powerful way to keep your database and API from becoming a tangled mess. By decoupling storage from projections, you:
- Reduce coupling between components.
- Enable independent evolution of data and APIs.
- Improve performance and flexibility.

Start small: identify one API endpoint where your storage and projection are braided, and refactor it using this pattern. Over time, you’ll build a system that’s easier to maintain, more resilient to change, and (most importantly) less prone to breaking under the weight of your own growth.

As your team grows and your data needs evolve, this separation will save you countless hours of coordination and debugging. And in the backend world, that’s time well spent.

---
```