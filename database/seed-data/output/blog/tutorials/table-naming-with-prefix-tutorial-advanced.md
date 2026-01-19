```markdown
# **`tb_*` Prefix Convention: A Simple but Powerful Database Naming Pattern**

*By [Your Name]*

---

## **Introduction**

Database naming is one of those seemingly trivial details that often gets overlooked—until it causes confusion in a 10,000-line schema or a multi-team project. When tables, views, and CTEs (Common Table Expressions) share similar names, or when developers mislabel temporary vs. permanent objects, the consequences can be costly: wasted debugging time, accidental data corruption, or worse—misleading production issues that slip through the cracks.

In this post, we’ll explore the **`tb_*` prefix convention**, a simple yet effective practice for distinguishing database tables from other objects. This pattern isn’t about reinventing the wheel—it’s about consistency, clarity, and reducing cognitive load for developers working across different layers of an application.

By the end, you’ll understand:
- Why table names should be unambiguous
- How the `tb_*` prefix solves key naming challenges
- Real-world implementation tradeoffs
- Common pitfalls to avoid

Let’s dive in.

---

## **The Problem: Ambiguous Database Objects**

A well-designed database is organized, predictable, and maintainable. However, real-world databases often suffer from ambiguity in naming, leading to issues like:

### **1. Confusing Tables with Views and CTEs**
In complex systems, developers frequently create:
- **Permanent tables** (e.g., `users`, `orders`)
- **Materialized views** (e.g., `user_stats`, `sales_summary`)
- **Temporary CTEs** (e.g., `temp_orders`, `customer_segmentation`)

Without a clear naming convention, these objects can blend together. For example:
- A developer might query `SELECT * FROM orders;`, only to realize they’re hitting a **view** instead of the actual database table.
- Another might drop a **temporary table** by accident, thinking it’s a legacy table.

### **2. Unclear Ownership of Tables**
In large systems, teams or services often manage their own tables. Without explicit naming, it’s hard to tell:
- Which tables belong to the **auth service** vs. the **billing service**?
- Which are **schema migrations** vs. **legacy tables**?

### **3. Risk of Accidental Data Loss**
Dropping a table with the wrong name (e.g., `orders` vs. `temp_orders`) can’t be undone. A clear prefix reduces the risk of miscommunication.

### **4. Migration and CI/CD Complexity**
When running schema migrations, tools often target all objects in a database. If tables and views share similar names, developers might:
- Accidentally run `ALTER TABLE` on a view.
- Fail to include temporary tables in backup queries.

---

## **The Solution: The `tb_*` Prefix Convention**

The **`tb_*` prefix** is a lightweight but powerful way to:
✅ **Explicitly mark tables** (vs. views, CTEs, or temporary objects).
✅ **Improve schema readability** by grouping related objects.
✅ **Reduce accidental errors** in `DROP`, `ALTER`, or `INSERT` operations.

### **How It Works**
- **All permanent tables** start with `tb_`.
  Example: `tb_users`, `tb_orders`, `tb_payment_methods`
- **Views and CTEs** use alternative prefixes (e.g., `vw_`, `cte_`)
- **Temporary tables** (session-specific) may use `temp_` or `#` (SQL Server).

### **Why `tb_*` Instead of `user_*` or `order_*`?**
Some teams use schema prefixes (e.g., `auth_users`, `billing_orders`), but this can lead to:
- **Long, hard-to-read names** (`auth_tb_legacy_users`).
- **Schema name collisions** if services share the same database.

`tb_*` is **flat and universal**, working across any schema or team.

---

## **Code Examples: Applying the `tb_*` Pattern**

### **Example 1: Basic Table Creation**
```sql
-- ✅ Correct: Tables use tb_ prefix
CREATE TABLE tb_users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ❌ Avoid: No prefix—ambiguous with views/CTEs
CREATE TABLE users_backup (
    ...
);
```

### **Example 2: Differentiating Tables from Views**
```sql
-- ✅ Tables
CREATE TABLE tb_customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100)
);

-- ✅ Views (typically vw_)
CREATE VIEW vw_active_customers AS
SELECT * FROM tb_customers WHERE is_active = true;

-- Querying explicitly avoids confusion
SELECT * FROM tb_customers;  -- Actual table
SELECT * FROM vw_active_customers;  -- Precomputed view
```

### **Example 3: Schema Migrations with Resilience**
When writing migrations, be explicit:
```sql
-- Safe migration: Only targets tb_* tables
ALTER TABLE tb_users ADD COLUMN last_login TIMESTAMP;

-- ❌ Risky: Might hit views or CTEs
ALTER TABLE users ADD COLUMN ...;  -- Could fail or corrupt data
```

### **Example 4: CI/CD Pipeline Considerations**
In deployment scripts, filter operations by prefix:
```bash
# Only run ALTER on tables (not views)
psql -c "SELECT 'ALTER TABLE ' || tablename || ' ADD COLUMN ...'
         FROM information_schema.tables
         WHERE table_name LIKE 'tb_%';"
```

### **Example 5: Temporary vs. Permanent Tables**
```sql
-- Temporary (session-specific)
CREATE TEMP TABLE temp_session_data AS
SELECT * FROM tb_users WHERE is_active = true;

-- Permanent (with tb_ prefix)
CREATE TABLE tb_user_stats AS
SELECT * FROM tb_users;
```

---

## **Implementation Guide**

### **Step 1: Document the Convention**
Add the prefix rule to your **database design docs** or **coding styleguide**. Example:
```
Database Naming Rules:
- Tables: Prefix with `tb_` (e.g., `tb_users`, `tb_order_items`).
- Views: Prefix with `vw_` (e.g., `vw_sales_summary`).
- CTEs: Prefix with `cte_` (e.g., `WITH cte_high_value_customers AS`).
- Temporary tables: Use `temp_` or SQL-specific syntax (e.g., `#temp`).
```

### **Step 2: Enforce in Schema Migrations**
Use tools like:
- **Liquibase/Flyway**: Add validation to reject non-`tb_*` table names.
- **Database constraints**: Reject invalid names at creation time.

Example with Flyway:
```xml
<sql>
CREATE TABLE tb_users (...);
-- Reject this:
-- CREATE TABLE users (...);  <!-- Fails validation -->
</sql>
```

### **Step 3: Educate Teams**
- Run **code reviews** to catch violations.
- Use **linters** (e.g., SQLLint for psql) to enforce consistency.
- Add the rule to **onboarding docs** for new developers.

### **Step 4: Retrofit Existing Databases (If Needed)**
If working with legacy systems:
1. Identify all tables missing `tb_`.
2. Create a **migration script** to rename them (carefully!):
   ```sql
   ALTER TABLE users RENAME TO tb_users;
   ALTER TABLE user_backup RENAME TO tb_user_backup;
   ```
3. Update all queries, backups, and migrations.

⚠️ **Warning**: Test thoroughly before renaming in production!

---

## **Common Mistakes to Avoid**

### **1. Overcomplicating the Prefix**
❌ Avoid:
```sql
auth_tb_users  -- Too many prefixes
service_b_tb_users  -- Hard to read
```

✅ Stick to `tb_` (or `user_`/`order_` if your team prefers).

### **2. Ignoring Views and CTEs**
Many teams only prefix tables but forget:
- **Views** (`vw_`)
- **CTEs** (documented in code comments)
- **Materialized views** (`mv_`)

### **3. Not Updating All Queries**
If you rename `orders` → `tb_orders`, **every query** must change:
```sql
-- Old (risks hitting views)
SELECT * FROM orders;

-- New (explicit)
SELECT * FROM tb_orders;
```

### **4. Allowing Exceptions**
Some teams add `tb_` to **only some tables** (e.g., `tb_users` but not `tb_logs`). This defeats the purpose! **Be consistent.**

### **5. Forgetting Temporary Tables**
Temporary tables (e.g., `#temp`) should **not** use `tb_`. They’re session-specific and short-lived.

---

## **Key Takeaways**

✔ **Explicit > Implicit**: The `tb_*` prefix makes tables instantly recognizable.
✔ **Reduces Ambiguity**: Avoids `orders` (table?) vs. `orders` (view?).
✔ **Improves Safety**: Fewer accidental `DROP` or `ALTER` accidents.
✔ **Works Everywhere**: Flat prefix avoids schema collisions.
✔ **Easy to Enforce**: Simple regex or linter rules can validate compliance.

🚨 **Tradeoffs**:
- **No magic**: Requires discipline to maintain.
- **No performance impact**: Just a naming convention.
- **Migration effort**: Retrofitting old DBs takes time.

---

## **Conclusion**

The `tb_*` prefix is a **low-hanging fruit** in database design—simple, scalable, and yet often overlooked. By adopting this convention, teams can:
- Reduce debugging time by making tables unambiguous.
- Improve migration safety with explicit object names.
- Onboard developers faster with clear, consistent schemas.

Like any naming pattern, it works best when **documented, enforced, and consistently applied**. Start small—add it to your next table—and gradually phase it into existing systems. Over time, you’ll see the benefits in fewer "Why did this break?" moments and more time focused on building features, not fixing naming-related fires.

**What’s your team’s database naming convention?** Share your experiences in the comments—I’d love to hear how you handle this!

---
*Thanks for reading! If you found this useful, consider sharing or subscribing for more backend patterns.*
```