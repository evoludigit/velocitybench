```markdown
# **Writing Self-Documenting Database Code: The `fn_*` Function Naming Convention**

## **Introduction**

Imagine this scenario: You’re on-call at 3 AM, your phone buzzes with a critical alert, and you need to fix a production issue fast. You open the database, scroll through function names like `sp1`, `update_user_data`, `proc_add_to_cart`, and `get_all_orders_v2`—each with slightly different parameters and behavior. It’s a chaotic mess.

**How can you make database functions and stored procedures easier to debug, maintain, and collaborate on?** The answer lies in **consistent, intentional naming conventions**—especially for your database functions.

In this post, we’ll explore the **`fn_*` (Function Naming Convention)** pattern—a practical approach used by systems like FraiseQL to structure database functions in a way that improves readability, reduces bugs, and speeds up debugging. We’ll cover:

- Why unclear naming hurts your team
- How `fn_*` solves these problems with real-world examples
- A step-by-step guide to implementing it
- Common pitfalls and best practices

Let’s dive in.

---

## **The Problem: Unclear Function Purpose & Inconsistent Naming**

Database functions and stored procedures are often treated like a black box—written quickly, deployed, and forgotten. This leads to a few common pain points:

### **1. Functions with Vague or Misleading Names**
Example:
❌ `update_user_info()`
Does this update email, password, or both? Does it require admin privileges? The name tells you nothing.

### **2. Inconsistent Naming Across the Codebase**
Example:
```sql
-- Where do these two do the same thing?
CREATE PROCEDURE insert_new_user (name VARCHAR, age INT);
CREATE FUNCTION add_user (username VARCHAR, email VARCHAR);
```
You now have to dig into the implementation to understand the differences.

### **3. Harder Debugging & On-Call Stress**
When something breaks at 3 AM, you don’t want to spend 15 minutes guessing what `fn_retrieve_orders_v3` does—especially if it’s been modified a dozen times.

### **4. Mutation Confusion**
Functions like `fn_get_user_by_id` sound safe, but if someone later modifies them to **write** data, a developer could accidentally trigger unintended side effects.

### **5. No Clear Action-Entity Mapping**
A function like `fn_sync_data()` could mean:
- Syncing user data with a third-party API
- Updating database triggers
- Sending a notification
Without context, it’s ambiguous.

---
## **The Solution: The `fn_*` Naming Convention**

The `fn_*` convention is a **pattern for naming database functions and stored procedures** that solves these problems by enforcing:

1. **A clear prefix (`fn_`)** to distinguish them from other objects.
2. **Explicit action + entity structure** (`fn_{action}_{entity}`) to describe intent.
3. **Consistency** across the entire database.

### **The Rule**
Use the following format for **all** database functions and stored procedures:
```
fn_{action}_{entity}[_{modifier}]
```
- **`fn_`**: Prepends all functions (avoids naming collisions with tables/views).
- **`{action}`**: A **verb** describing what the function does (e.g., `create`, `update`, `delete`, `get`, `list`).
- **`{entity}`**: The **table or domain object** being acted upon (e.g., `user`, `post`, `order`).
- **`{modifier}` (optional)**: Additional context like `soft`, `hard`, or `auto` (e.g., `fn_soft_delete_post`).

### **Why This Works**
| Problem                  | Solution with `fn_*`                          |
|--------------------------|-----------------------------------------------|
| Vague names              | `fn_create_user` vs. `fn_get_user_data`       |
| Inconsistent naming      | Uniform pattern for all functions             |
| Mutation confusion       | `fn_get_user` (read-only) vs. `fn_update_user` |
| Debugging difficulties   | Clear intent in function names                 |

---

## **Code Examples: Before & After**

### **Example 1: User Management Functions**
#### ❌ **Before (Chaotic)**
```sql
-- What does this do?
CREATE PROCEDURE modify_user_data (user_id INT, new_data JSON);

-- Could this update or delete?
CREATE FUNCTION user_action (id INT, action VARCHAR);

-- Does this return all or paginated results?
SELECT * FROM get_users();
```

#### ✅ **After (Clear & Consistent)**
```sql
-- Create a new user
CREATE FUNCTION fn_create_user (
    name VARCHAR,
    email VARCHAR,
    password_hash VARCHAR
) RETURNS INT;

-- Fetch a single user
CREATE FUNCTION fn_get_user_by_id (user_id INT) RETURNS JSON;

-- Update user profile (soft update = no delete)
CREATE FUNCTION fn_soft_update_user_profile (
    user_id INT,
    name VARCHAR,
    bio TEXT
) RETURNS BOOLEAN;

-- Bulk delete inactive users
CREATE FUNCTION fn_hard_delete_inactive_users (days_inactive INT) RETURNS INT;
```

### **Example 2: Order Processing**
#### ❌ **Before**
```sql
-- Why is this called `order_update`? Does it delete or modify?
UPDATE order_items (status = 'shipped');

-- What’s the difference between this and `get_orders`?
SELECT * FROM fetch_order_history();
```

#### ✅ **After**
```sql
-- Mark an order as shipped
CREATE FUNCTION fn_update_order_status (
    order_id INT,
    status VARCHAR
) RETURNS BOOLEAN;

-- Get order history (read-only)
CREATE FUNCTION fn_get_order_history (order_id INT) RETURNS JSON;

-- Cancel an order (explicit intent)
CREATE FUNCTION fn_cancel_order (order_id INT) RETURNS BOOLEAN;

-- Auto-cancel expired orders
CREATE FUNCTION fn_auto_cancel_expired_orders (expiry_days INT) RETURNS INT;
```

### **Example 3: Modifiers (Optional but Useful)**
```sql
-- Soft vs. hard delete
CREATE FUNCTION fn_soft_delete_post (post_id INT) RETURNS BOOLEAN;
CREATE FUNCTION fn_hard_delete_post (post_id INT) RETURNS BOOLEAN;

-- Auto vs. manual processing
CREATE FUNCTION fn_auto_generate_report (date_range DATE) RETURNS JSON;
CREATE FUNCTION fn_manual_generate_report (template_id INT) RETURNS JSON;
```

---

## **Implementation Guide: How to Adopt `fn_*`**

### **Step 1: Audit Existing Functions**
Before refactoring, list all existing functions and name them using `fn_{action}_{entity}`:
```sql
-- Bad: vague, inconsistent
SELECT * FROM get_all_users();
UPDATE customer_account SET status = 'active';

-- Good: clear and consistent
CREATE FUNCTION fn_get_all_users() RETURNS JSON;  -- Note: 'list' might be better
CREATE FUNCTION fn_activate_customer (customer_id INT) RETURNS BOOLEAN;
```

### **Step 2: Define Your Action Verbs**
Pick a **small set of standard actions** for your team. Example:
| Action       | Example Function                     |
|--------------|--------------------------------------|
| Create       | `fn_create_user`                     |
| Read         | `fn_get_post`, `fn_list_comments`     |
| Update       | `fn_update_profile`, `fn_soft_update` |
| Delete       | `fn_hard_delete`, `fn_soft_delete`    |
| Sync         | `fn_sync_user_data`                  |
| Validate     | `fn_validate_payment`                |

### **Step 3: Enforce the Convention**
- **Add to your database documentation** (e.g., in a `README.md`).
- **Use CI/CD checks** to reject PRs with non-compliant function names.
- **Train your team** in code reviews.

### **Step 4: Handle Edge Cases**
| Scenario                     | Solution                                  |
|------------------------------|-------------------------------------------|
| Functions that do multiple things | Split into smaller functions (e.g., `fn_send_notification` vs. `fn_log_event`). |
| Legacy functions              | Rename incrementally (e.g., `sp_update_user` → `fn_update_user`). |
| Event handlers                | Use `fn_on_{event}_trigger` (e.g., `fn_on_order_created_trigger`). |

---

## **Common Mistakes to Avoid**

### **1. Overcomplicating the Modifier**
❌ `fn_super_duper_update_user_with_cache_refresh` → Too verbose.

✅ Stick to 1-2 modifiers max: `fn_refresh_user_cache`, `fn_hard_delete_post`.

### **2. Inconsistent Action Verbs**
❌ Mix `get`, `fetch`, `retrieve`, `select` for read operations.
✅ Use **one verb per action type** (e.g., always `fn_get` for single items).

### **3. Ignoring Read-Only vs. Mutable Functions**
❌ `fn_get_user_data` that secretly modifies data.
✅ **Read-only**: `fn_get_user_by_id`
✅ **Mutable**: `fn_update_user_profile`

### **4. Not Documenting Exceptions**
If you *must* break the rule (e.g., legacy code), **document why**.
```sql
-- NOTE: This is a legacy function. Avoid in new code.
CREATE FUNCTION legacy_user_login (email VARCHAR) RETURNS INT;
```

### **5. Forgetting to Update API Layer**
If you rename a function, **update all application code** that calls it.
```python
# Old (bad)
db.execute("update_user_data")

# New (good)
db.execute("fn_update_user_profile")
```

---

## **Key Takeaways**

✅ **Self-documenting code**: Function names now describe their purpose clearly.
✅ **Reduced debugging time**: No more guessing what `fn_retrieve_orders_v3` does.
✅ **Consistency**: Every function follows the same pattern, making the DB easier to navigate.
✅ **Mutation safety**: `fn_get_*` implies read-only; `fn_update_*` implies write.
✅ **Easier collaboration**: New devs can jump in without deep context.

⚠️ **Tradeoffs to consider**:
- **Refactoring effort**: Renaming existing functions takes time.
- **Tooling overhead**: Some databases (e.g., PostgreSQL) don’t enforce naming, so discipline is key.
- **Over-engineering risk**: Don’t apply this to every trivial function.

---

## **Conclusion**

The `fn_*` naming convention isn’t about reinventing the wheel—it’s about **intentionality**. By structuring your database functions with a clear pattern, you:

1. **Make your code easier to understand** (for yourself and your team).
2. **Reduce debugging time** in emergencies.
3. **Future-proof your database** against inconsistent changes.

### **Next Steps**
1. Start small: Pick one table (e.g., `users`) and rename 3-5 functions.
2. Share the pattern with your team and get feedback.
3. Gradually expand to the entire codebase.

**Try it out—your future self (and your on-call colleagues) will thank you.**

---
### **Further Reading**
- [FraiseQL’s Database Design Principles](https://fraise.com/docs/database-design)
- [Why Naming Matters in Software (Martin Fowler)](https://martinfowler.com/articles/naming.html)
- [Database Function Naming Best Practices (Dev.to)](https://dev.to/yourarticlehere)

---
**What’s your experience with database function naming? Have you used a similar pattern? Share your thoughts in the comments!**
```