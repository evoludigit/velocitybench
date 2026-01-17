```markdown
---
title: "Cleaner DB Code: The fn_* Naming Convention Pattern"
date: 2023-11-15
author: Alex Petrov
tags: ["database design", "performance", "back-end architecture", "SQL patterns", "API design"]
description: "How the `fn_*` naming convention pattern revolutionizes database function clarity, reduces ambiguity, and aligns database interactions with your application's domain. A practical guide for backend engineers."
---

# **Cleaner DB Code: The `fn_*` Naming Convention Pattern**

In backend systems, databases often become tangled webs of undocumented functions and procedures—hidden gems buried under cryptic names like `proc_um_012` or `get_user_data_sp`. These unstructured artifacts make code harder to maintain, debug, and collaborate on. It’s no wonder that database operations frequently become bottlenecks or sources of bugs.

As a senior backend engineer who’s refactored countless legacy systems, I’ve seen how naming conventions can be a silent ally (or enemy) in maintainability. Enter the **`fn_*` naming convention pattern**, a simple yet powerful approach adopted by platforms like **FraiseQL** to enforce consistency, self-documenting code, and clearer mutation mapping.

In this post, we’ll dive into why this pattern works, how to implement it, and how it can transform your database interactions from chaotic to crisp.

---

## **The Problem: Unclear Function Purpose and Inconsistent Naming**

Before exploring solutions, let’s look at why this problem exists in the first place:

### 1. **Lack of Domain Alignment**
Many database functions don’t reflect the application’s business logic. For example:
```sql
-- What does this even do?
CREATE PROCEDURE `sp_generate_report`(...);
```
Is this generating a report for users, employees, or something else? The name gives no context.

### 2. **Mutation Ambiguity**
When you have procedures that both fetch *and* modify data (e.g., `get_or_create_user`), the intent is unclear. Is this a query? A mutation? Both?

### 3. **No Standardized Structure**
Without a convention, different developers invent their own naming schemes:
- `fn_create_blog_comment`
- `create_comment`
- `sp_new_comment`
- `new_comment()`
This inconsistency makes the codebase harder to navigate.

### 4. **Challenges in Debugging and Maintenance**
When functions are named vaguely, debugging becomes a guessing game. Teams spend more time figuring out *what* a function does rather than *how* it works.

### 5. **Breaking API Contracts**
If your database functions aren’t aligned with your API endpoints, you risk inconsistencies—e.g., `/users/{id}` expects `GET`, but the DB requires `fn_fetch_user_by_id`. This creates friction between layers.

---

## **The Solution: The `fn_*` Naming Convention**

The `fn_*` pattern solves these problems by enforcing **three key principles**:
1. **Prefix Standardization** – Every function starts with `fn_` (or `proc_`/`sp_` if your DB requires it).
2. **Action-Entity Verbs** – Functions follow `fn_{action}_{entity}` (e.g., `fn_create_user`, `fn_delete_order`).
3. **Explicit Intent** – The name clearly states **what** the function does and **where** it operates.

### **Why It Works**
- **Self-documenting**: No need for comments explaining what a function does.
- **Consistency**: Every team member writes in the same style.
- **Mutation Clarity**: `fn_*` implies *operations*, while `get_*` implies *queries*.
- **Scalability**: Easy to audit and refactor.

---

## **Components of the `fn_*` Pattern**

### 1. **The `fn_` Prefix**
The prefix signals that this is a **database function or stored procedure**, not a utility or application logic.
*Exception*: Some databases (like SQL Server) may require `sp_` or `proc_`, but `fn_*` remains a best practice for clarity.

### 2. **Action-Entity Structure**
The body of the name follows `{action}_{entity}`:
| Action      | Example Entity | Full Function Name      |
|-------------|----------------|-------------------------|
| `create`    | `user`         | `fn_create_user`        |
| `update`    | `post`         | `fn_update_post`        |
| `delete`    | `order`        | `fn_delete_order`       |
| `fetch`     | `comment`      | `fn_fetch_comment_by_id`|
| `list`      | `product`      | `fn_list_products`      |

### 3. **Handling Complex Actions**
For multi-step operations (e.g., transferring funds), use a **descriptive verb**:
```sql
-- Instead of:
fn_transfer_money_between_accounts

-- Use:
fn_transfer_funds_from_to
```

### 4. **Query vs. Mutation Split**
- **Queries (reads)**: Prefix with `fn_get_` or `fn_list_`.
- **Mutations (writes)**: Prefix with `fn_create_`, `fn_update_`, `fn_delete_`.

---
## **Code Examples**

### **Example 1: Create a User**
**Problematic (vague):**
```sql
CREATE PROCEDURE `user_creation`(...);
-- What if we need a `user_update` next? Naming clashes.
```

**Solution (`fn_*`):**
```sql
CREATE FUNCTION fn_create_user(
    p_username VARCHAR(50),
    p_email VARCHAR(100),
    p_password_hash VARCHAR(255)
) RETURNS INT
BEGIN
    -- Logic to insert user
    RETURN LAST_INSERT_ID();
END;
```
**Why this works**:
- Clear intent (`create_user`).
- Returns an ID (OK for mutations).
- Easy to extend (e.g., `fn_update_user_password`).

---

### **Example 2: Fetch a User by ID**
**Problematic (ambiguous):**
```sql
CREATE PROCEDURE `get_user`(...);
-- Could this *also* create a user?
```

**Solution (`fn_*`):**
```sql
CREATE FUNCTION fn_get_user_by_id(
    p_user_id INT
) RETURNS JSON
BEGIN
    SELECT JSON_OBJECT(
        'id', u.id,
        'username', u.username,
        'email', u.email
    ) FROM users u WHERE u.id = p_user_id;
END;
```
**Why this works**:
- `get_` signals a query.
- Returns JSON (good for APIs).
- No side effects.

---

### **Example 3: Delete an Order with Validation**
**Problematic (inconsistent):**
```sql
DROP PROCEDURE IF EXISTS delete_order;
CREATE PROCEDURE delete_order(p_order_id INT) { ... };
-- Later: DROP PROCEDURE IF EXISTS cancel_order;
```

**Solution (`fn_*`):**
```sql
CREATE FUNCTION fn_delete_order(
    p_order_id INT,
    p_user_id INT
) RETURNS BOOLEAN
BEGIN
    DECLARE order_found INT;

    -- Validation: Order must belong to the user
    SELECT COUNT(*) INTO order_found
    FROM orders
    WHERE id = p_order_id AND user_id = p_user_id;

    IF order_found = 0 THEN
        RETURN FALSE; -- Forbidden
    END IF;

    DELETE FROM orders WHERE id = p_order_id;
    RETURN TRUE;
END;
```
**Why this works**:
- `fn_delete_order` is explicit.
- Includes validation logic (a common mutation use case).
- Returns `BOOLEAN` for success/failure.

---

### **Example 4: Complex Action (Transfer Funds)**
**Problematic (too verbose):**
```sql
CREATE PROCEDURE fn_transfer_money_between_two_accounts(...);
```

**Solution (`fn_*` with descriptive action):**
```sql
CREATE FUNCTION fn_transfer_funds_from_to(
    p_from_account_id INT,
    p_to_account_id INT,
    p_amount DECIMAL(10, 2)
) RETURNS BOOLEAN
BEGIN
    -- Logic to debit `from_account` and credit `to_account`
    -- with transactions and validation
    RETURN TRUE;
END;
```
**Why this works**:
- Clear, action-oriented name.
- Parameters are self-explanatory.

---

## **Implementation Guide**

### **Step 1: Audit Existing Functions**
Before adopting `fn_*`, migrate existing functions:
1. List all stored procedures/functions.
2. Rename them using the `fn_{action}_{entity}` pattern.
3. Document changes in a migration guide.

**Example Migration:**
```sql
-- Old:
ALTER PROCEDURE sp_get_users_by_email TO `fn_list_users_by_email`;

-- New:
ALTER PROCEDURE sp_get_users_by_email TO `fn_get_users_by_email`;
```

### **Step 2: Enforce the Convention in Code**
Use **linters** or **code reviews** to catch violations:
- **Database Linter**: Check for functions without `fn_` prefix.
- **PR Guidelines**: Require `fn_*` in all new DB changes.

### **Step 3: Update Application Code**
If your app interacts with these functions:
```python
# Old (ambiguous):
db.execute("sp_generate_report")

# New (clear):
result = db.execute("fn_get_sales_report_for_month", month="2023-11")
```

### **Step 4: Document Edge Cases**
Handle exceptions gracefully:
```sql
CREATE FUNCTION fn_update_user_email(
    p_user_id INT,
    p_new_email VARCHAR(100)
) RETURNS JSON
BEGIN
    -- Check if email is taken
    IF EXISTS (SELECT 1 FROM users WHERE email = p_new_email AND id != p_user_id) THEN
        RETURN JSON_OBJECT('error', 'Email already in use');
    END IF;

    UPDATE users SET email = p_new_email WHERE id = p_user_id;
    RETURN JSON_OBJECT('success', TRUE);
END;
```

### **Step 5: Consider ORM/Wrapper Layer**
If using an ORM (e.g., SQLAlchemy, Prisma, Dapper), wrap `fn_*` calls in a layer that maps them to domain logic:
```python
# Python example
class UserRepository:
    def create_user(self, username: str, email: str) -> int:
        return self.db.execute("fn_create_user", username=username, email=email)
```

---

## **Common Mistakes to Avoid**

### ❌ **1. Overloading Actions**
Avoid:
```sql
-- ❌ Bad: One function for both reads and writes
CREATE FUNCTION fn_user_actions(...) { ... };

-- ✅ Good: Separate `fn_get_user`, `fn_create_user`, `fn_update_user`
```

### ❌ **2. Overly Generic Names**
Avoid:
```sql
-- ❌ Ambiguous
fn_process_data(...);

-- ✅ Specific
fn_generate_invoice_for_order(...)
```

### ❌ **3. Ignoring Read-Write Separation**
Avoid mixing queries with mutations:
```sql
-- ❌ Bad: One function does both
CREATE FUNCTION fn_get_or_create_user(...) { ... };

-- ✅ Good: Separate `fn_get_user_by_email` and `fn_create_user`
```

### ❌ **4. Not Including Parameters Clearly**
Avoid cryptic parameters:
```sql
-- ❌ Bad
CREATE FUNCTION fn_x(p1 INT, p2 VARCHAR) { ... };

-- ✅ Good
CREATE FUNCTION fn_update_product_price(
    p_product_id INT,
    p_new_price DECIMAL(10, 2)
) { ... };
```

### ❌ **5. Forgetting to Handle Errors**
Always validate and return meaningful responses:
```sql
-- ❌ Bad: Silent failures
CREATE FUNCTION fn_delete_order(p_order_id INT) { DELETE FROM orders WHERE id = p_order_id; };

-- ✅ Good: Explicit feedback
CREATE FUNCTION fn_delete_order(p_order_id INT) RETURNS BOOLEAN
BEGIN
    IF NOT EXISTS (SELECT 1 FROM orders WHERE id = p_order_id) THEN
        RETURN FALSE; -- Not found
    END IF;
    DELETE FROM orders WHERE id = p_order_id;
    RETURN TRUE;
END;
```

---

## **Key Takeaways**

✅ **`fn_*` enforces consistency** across database functions, reducing cognitive load.
✅ **Action-entity structure (`fn_{action}_{entity}`)** makes functions self-documenting.
✅ **Separates queries (`fn_get_*`) from mutations (`fn_create_*`)** for clarity.
✅ **Easier debugging**—no more guessing what a function does.
✅ **Better API alignment**—functions map cleanly to your domain logic.
✅ **Scalable**—new functions follow the same pattern automatically.

---

## **Conclusion**

The `fn_*` naming convention isn’t just a stylistic choice—it’s a **maintainability upgrade** for your database layer. By standardizing how functions are named, you reduce ambiguity, improve collaboration, and make your codebase easier to reason about.

### **Next Steps**
1. **Start small**: Pick one table (e.g., `users`) and rename all its functions using `fn_`.
2. **Automate enforcement**: Use linters or CI checks to catch violations.
3. **Educate your team**: Hold a quick workshop on the pattern.
4. **Iterate**: Refactor as you go, but never roll back!

The goal isn’t perfection—it’s **progress**. Over time, this small change will make your database interactions **cleaner, faster to debug, and more aligned with your application’s logic**.

Happy coding!
```

---
**Author Bio**:
Alex Petrov is a senior backend engineer with 10+ years of experience optimizing database-driven systems. He’s worked on scaling APIs for fintech platforms and now advocates for cleaner code patterns through open-source contributions and technical writing. Follow his work on [LinkedIn](https://linkedin.com/in/alexpetrovdev) or [GitHub](https://github.com/alexpetrov).