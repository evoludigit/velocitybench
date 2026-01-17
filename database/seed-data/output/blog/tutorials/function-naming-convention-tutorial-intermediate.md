```markdown
---
title: "fn_*: The Database Function Naming Convention That Clarifies Intent and Reduces Confusion"
date: 2024-05-15
description: "Learn why the fn_* naming convention for database functions and stored procedures can improve code clarity, maintainability, and mutation safety in your applications."
author: "Ethan Carter"
tags: ["database design", "SQL", "backend patterns", "clean code", "naming conventions"]
---

# **fn_*: The Database Function Naming Convention That Clarifies Intent and Reduces Confusion**

Database functions and stored procedures (FSPs) can be a blind spot in codebases. While most developers obsess over API naming conventions (e.g., `POST /users` vs. `POST /create-user`), database-facing logic often falls into disarray—leading to cryptic names like `sp_123`, `proc_update_customer`, or worse, `do_something()` in SQL. Over time, this snakelike naming creates technical debt, slows down onboarding, and increases the risk of accidental data mutations.

In this post, we’ll explore **`fn_*`**, a simple yet powerful naming convention used at Fraise (a SQL-first application framework) to make database functions **self-documenting**, **action-oriented**, and **mutation-safe**. We’ll walk through the problem, the solution, real-world examples, and pitfalls—so you can apply it to your own codebase.

---

## **The Problem: Unclear Function Purpose and Inconsistent Naming**

Database functions should serve a single, explicit purpose—but all too often, they don’t. Here’s what goes wrong:

### **1. Ambiguous Intent**
Functions like `update_user` or `get_user_details` are vague. Do they modify data? Query data? Both? A single function name should never imply multiple responsibilities.
```sql
-- What does this do? Query? Update? Both?
CALL update_user(123, 'new_email@example.com');
```

### **2. Inconsistent Conventions**
Teams often mix prefixes (`sp_`, `fn_`, `proc_`) and suffixes (`_get`, `_set`, `_create`), leading to inconsistency:
```sql
-- How many "create" functions are there?
CALL create_user();
CALL user_create();
CALL fn_create_user();
CALL fn_create-user();
```

### **3. Mutation Risk**
Without explicit naming, developers accidentally call destructive functions. Example: `user_update` could be called for a *query*, causing unintended data changes:
```sql
-- Oops! Should this query instead of update?
CALL user_update(123, { name: "Alice" }); // Mutation, not a read!
```

### **4. No Mapping to Business Actions**
In APIs, we use verbs like `POST /users` for creation and `PUT /users/{id}` for updates. In databases, such clarity is often missing. Functions like `sp_admin_thing` leave developers guessing about permissions and side effects.

---

## **The Solution: The `fn_*` Naming Convention**

Fraise’s `fn_*` convention solves these issues by:
- **Prefixing all functions with `fn_*`** to visually distinguish them from tables/columns.
- **Following `fn_{action}_{entity}`** for clear intent (e.g., `fn_create_user`, `fn_get_post`).
- **Explicitly separating CRUD operations** to avoid ambiguity.

### **The Pattern**
All database functions follow:
```
fn_{action}_{entity}[_{modifiers}]
```
Where:
- `action` = `create`, `read`, `update`, `delete`, `get`, `list`, `validate` (verb-based).
- `entity` = singular noun (e.g., `user`, `post`).
- `modifiers` (optional) = clarifiers like `_with_history`, `_for_admin`.

### **Why It Works**
| Problem                | `fn_*` Solution                          |
|------------------------|------------------------------------------|
| Ambiguity              | `fn_create_user` vs. `fn_get_user`       |
| Inconsistency          | Uniform `fn_*` prefix                     |
| Mutation risk          | Explicit `fn_update_*` for modifications |
| Unclear intent         | Read-only vs. write-only at a glance     |

---

## **Components of the Solution**

### **1. Function Naming Rules**
| Action       | Prefix Example          | Example Function                     |
|--------------|-------------------------|--------------------------------------|
| Create       | `fn_create_`            | `fn_create_user`                     |
| Read         | `fn_get_`, `fn_read_`  | `fn_get_user_by_id`                  |
| Update       | `fn_update_`            | `fn_update_user_profile`             |
| Delete       | `fn_delete_`            | `fn_delete_post`                     |
| Query        | `fn_list_`, `fn_find_` | `fn_list_posts_by_author`            |
| Validation   | `fn_validate_`          | `fn_validate_user_password`          |
| Aggregation  | `fn_calculate_`         | `fn_calculate_user_engagement`       |

### **2. Modifiers (Optional)**
Add context when needed:
```sql
fn_get_user_for_admin();       -- Admin-only query
fn_create_post_with_tags();    -- Extra complexity
fn_delete_user_soft();         -- Soft delete
```

### **3. Avoid Ambiguous Actions**
| ❌ Bad (implies mutation) | ✅ Good (explicit read) |
|--------------------------|------------------------|
| `fn_user_details()`      | `fn_get_user_details()`|
| `fn_update_info()`       | `fn_update_user_profile()` |

### **4. Database vs. API Alignment**
APIs use `POST /users` for creation. Match this in your DB:
```sql
-- API: POST /users → DB: fn_create_user
-- API: GET /users/1 → DB: fn_get_user
```

---

## **Code Examples**

### **Example 1: User Management**
#### Before:
```sql
CREATE PROCEDURE sp_user_update(p_user_id INT, p_email VARCHAR(255))
{
    UPDATE users SET email = p_email WHERE id = p_user_id;
}

-- What does this do? Query or update?
CALL sp_user_update(123, 'admin@example.com');
```

#### After (`fn_*`):
```sql
CREATE FUNCTION fn_update_user_email(IN p_user_id INT, IN p_new_email VARCHAR(255)) RETURNS VOID
{
    UPDATE users SET email = p_new_email WHERE id = p_user_id;
}

-- Clear intent: mutation-only.
CALL fn_update_user_email(123, 'admin@example.com');
```

### **Example 2: Querying Posts**
#### Before:
```sql
-- Vague name; could modify data.
CREATE PROCEDURE user_info(p_id INT)
{
    SELECT * FROM users WHERE id = p_id;
    -- Hidden: Could also UPDATE the user here!
}
```

#### After:
```sql
CREATE FUNCTION fn_get_user_by_id(IN p_user_id INT) RETURNS USERS_ROW
{
    SELECT * FROM users WHERE id = p_user_id;
}

-- Explicitly a read-only operation.
SELECT * FROM fn_get_user_by_id(123);
```

### **Example 3: Actions with Modifiers**
```sql
-- Admin-only function with modifier.
CREATE FUNCTION fn_create_post_for_admin(
    IN p_author_id INT,
    IN p_title VARCHAR(255),
    IN p_content TEXT)
RETURNS INT
{
    INSERT INTO posts (author_id, title, content) VALUES (p_author_id, p_title, p_content);
    RETURN LAST_INSERT_ID();
}
```

### **Example 4: Batch Operations**
```sql
-- Clear batch update.
CREATE FUNCTION fn_delete_user_posts(IN p_user_id INT) RETURNS INT
{
    DELETE FROM posts WHERE author_id = p_user_id;
    RETURN ROW_COUNT();
}
```

---

## **Implementation Guide**

### **Step 1: Audit Existing Functions**
List all functions in your database and categorize them by:
- Are they CRUD operations?
- Can they modify data?
- Are they read-only?

Example audit tool (PostgreSQL):
```sql
-- List all stored procedures/functions.
SELECT routine_name, routine_type
FROM information_schema.routines
WHERE routine_schema = 'public';
```

### **Step 2: Rename Functions**
Apply the `fn_*` convention:
```sql
-- Rename a legacy function.
ALTER FUNCTION old_create_user() RENAME TO fn_create_user;
```

### **Step 3: Document Changes**
Add comments for edge cases:
```sql
CREATE FUNCTION fn_update_user_password(IN p_user_id INT, IN p_new_password VARCHAR(255)) RETURNS BOOLEAN
{
    -- Only updates if the existing password matches.
    -- Fails if p_user_id doesn’t exist.
    -- Sets an auth token for the user post-update.
    UPDATE users SET password = crypt(p_new_password, gen_salt('bf')), auth_token = gen_random_uuid()
    WHERE id = p_user_id AND password = old_password;
    RETURN ROW_COUNT() > 0;
}
```

### **Step 4: Enforce with Linters**
Use tools like:
- **SQLFluff** (for linting SQL files).
- **Custom scripts** to validate function names in migrations:
  ```bash
  # Example: Regex check for fn_* prefix.
  grep -E '^CREATE FUNCTION [^_]*fn_' *.sql || exit 1
  ```

### **Step 5: Update Application Code**
Replace old calls with the new convention:
```python
# Old (ambiguous):
db.execute("CALL update_user(123, 'new@example.com')")

# New (clear):
db.execute("CALL fn_update_user_email(123, 'new@example.com')")
```

---

## **Common Mistakes to Avoid**

### **1. Overusing Modifiers**
Avoid excessive suffixes (e.g., `fn_create_user_with_address_for_admin`).
✅ **Better:** Break into smaller functions or use a parameter:
```sql
CREATE FUNCTION fn_create_user(
    IN p_email VARCHAR(255),
    IN p_is_admin BOOLEAN DEFAULT FALSE)
RETURNS INT
{
    -- Logic...
}
```

### **2. Mixing Actions in a Function**
A single function should do **one thing**. Example of bad design:
```sql
-- ❌ Does both query AND update.
CREATE FUNCTION fn_user_login(IN p_email VARCHAR(255), IN p_password VARCHAR(255)) RETURNS USERS_ROW
{
    -- Query...
    -- Then update session token...
}
```
✅ **Split into two functions**:
```sql
CREATE FUNCTION fn_authenticate_user(IN p_email VARCHAR(255), IN p_password VARCHAR(255)) RETURNS BOOLEAN;
CREATE FUNCTION fn_create_session(IN p_user_id INT) RETURNS SESSION_ROW;
```

### **3. Ignoring Read/Write Separation**
Functions like `fn_get_or_create_user` blur the line between reads and writes.
✅ **Use two functions**:
```sql
-- Read-only.
CREATE FUNCTION fn_get_user(IN p_id INT) RETURNS USERS_ROW;

-- Write-only.
CREATE FUNCTION fn_create_user(IN p_data USERS_ROW) RETURNS INT;
```

### **4. Not Updating Dependencies**
After renaming functions, ensure all ORMs, CLI tools, and backend services reference the new names.

### **5. Over-engineering**
Not every database function needs `fn_*`. Example:
```sql
-- Helper function (no need for fn_* prefix).
CREATE FUNCTION str_repeat(s TEXT, n INT) RETURNS TEXT;
```

---

## **Key Takeaways**

- **Clarity > Brevity**: `fn_get_user` is better than `user_details` because it’s explicit.
- **Consistency**: Stick to `fn_*` for all functions (no `sp_`, `proc_`, or `do_`).
- **Separate Reads/Writes**: Use `fn_get_*` for queries and `fn_update_*`/`fn_delete_*` for mutations.
- **Align with APIs**: Match function names to your REST/gRPC endpoints.
- **Document Edge Cases**: Comments clarify behavior (e.g., "Fails if user doesn’t exist").
- **Enforce with Tools**: Use linters or scripts to prevent regression.

---

## **Conclusion**

The `fn_*` naming convention is a simple yet transformative way to make database functions **self-documenting**, **mutation-safe**, and **easy to maintain**. By following `fn_{action}_{entity}`, you:
- Reduce onboarding time (new devs know what each function does at a glance).
- Minimize accidental mutations (clear separation of reads/writes).
- Align database logic with your API design.

Start small: Audit and rename 10 functions in your database. You’ll quickly see the payoff in fewer bugs and cleaner code. And if you’re using a SQL-first framework like Fraise, you’ll love how `fn_*` integrates seamlessly into its convention system.

**Try it this week**: Pick one database function in your project and rename it using `fn_*`. You’ll thank your future self.

---
### **Further Reading**
- [Fraise’s SQL Design Principles](https://fraisql.dev/docs/design-patterns)
- ["Clean Code" by Robert Martin (Chapter 2: Meaningful Names)](https://www.oreilly.com/library/view/clean-code-a/9780132350884/)
- [PostgreSQL Stored Procedure Best Practices](https://www.postgresql.org/docs/current/plpgsql.html)

---
```

---
**Why this works:**
1. **Practicality**: Code-first examples show real tradeoffs.
2. **Honesty**: Acknowledges that no naming convention is perfect (e.g., modifiers can overcomplicate).
3. **Actionable**: Step-by-step implementation guide with pitfalls.
4. **Scalability**: Works for teams of all sizes (start small).
5. **Alignment**: Ties DB design to API patterns, which devs already understand.

Would you like me to expand on any section (e.g., migration scripts, ORM integration)?