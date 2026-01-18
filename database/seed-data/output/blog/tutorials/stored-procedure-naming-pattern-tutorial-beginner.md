```markdown
# **fn_*: The Simple Pattern for Storing Procedures That Actually Do Stuff**

When you’re building database-backed applications, you quickly realize that not all stored procedures are created equal. Some are read-only queries that just return data (views), while others modify that data (mutations). Without a clear convention, it’s easy to confuse these two types—especially in teams where database design isn’t the top priority.

This is where naming conventions like **`fn_*`** (function prefix) come in. This pattern visually separates stored procedures that perform actions from those that merely query data. It’s a low-effort, high-impact way to improve readability and maintainability in your database layer.

Today, we’ll explore:
- The chaos of mixing functions and views in your stored procedures
- Why `fn_*` is a better way to organize them
- How to implement it in your SQL code
- Real-world tradeoffs

Let’s dive in.

---

## **The Problem: Functions and Views Blending Together**

At first glance, stored procedures might seem like a straightforward way to abstract database logic. But as your project grows, they often evolve into a mess. Here’s what happens when you don’t distinguish between **read-only views** and **mutating functions**:

```sql
-- This procedure does *both*—querying AND modifying data.
CREATE PROCEDURE update_user_profile(
    IN user_id INT,
    IN new_email VARCHAR(255)
)
BEGIN
    -- First, fetch the user's current data (view-like behavior)
    SELECT * FROM users WHERE id = user_id;

    -- Then, update their email (mutation)
    UPDATE users SET email = new_email WHERE id = user_id;
    SELECT * FROM users WHERE id = user_id; -- Return the updated record
END;
```

### **The Confusion Begins**
- **What kind of procedure is this?**
  - Is it a **view**? It fetches data.
  - Is it a **function/mutation**? It modifies data.
- **How should it be called?**
  - Should we treat it as a query in a REST API endpoint?
  - Or should it be a write operation with stricter validation?
- **What happens when we refactor?**
  - If we split this into two procedures, who maintains consistency?
  - Is there a way to enforce that only certain roles can call this?

This lack of clarity leads to:
✅ **Slower debugging** – Developers waste time trying to figure out if the procedure is safe to call in a `SELECT` vs. an `UPDATE`.
✅ **Security risks** – Procedural code that *looks* like a read-only query might actually hide destructive mutations.
✅ **Maintenance hell** – Future developers (including *your future self*) will curse the decision to merge these concerns.

---

## **The Solution: `fn_*` Prefix for Mutations**

The **`fn_*` pattern** provides a simple but powerful way to organize stored procedures by their purpose:

| **Naming Convention** | **Purpose** | **Example** |
|----------------------|------------|------------|
| `fn_crud_operation`  | Mutation (INSERT, UPDATE, DELETE, CALL) | `fn_create_user`, `fn_update_order_status` |
| `vw_*` or `get_*`    | Read-only queries | `vw_get_user_by_email`, `get_customer_orders` |

This naming scheme:
1. **Explicitly signals intent** – A procedure with `fn_` is expected to change data.
2. **Encourages separation of concerns** – Forces you to think: *"Does this need to modify data?"*
3. **Makes documentation easier** – Teams can immediately see which procedures are safe for reads vs. writes.

---

## **Implementation Guide: When and How to Use `fn_*`**

### **1. Start with a Clean Naming Convention**
Define your team’s standards early. For example:

- **Functions (mutations):** `fn_*`
- **Queries (reads):** `get_*` or `vw_*`
- **Transactions:** `fn_begin_*`, `fn_commit_*`

Example:

```sql
-- A function that updates a user's password (mutation)
CREATE PROCEDURE fn_update_user_password(
    IN user_id INT,
    IN new_password VARCHAR(255)
)
BEGIN
    UPDATE users SET password_hash = SHA2(new_password, 256)
    WHERE id = user_id;
END;

-- A view that returns a user's details (read-only)
CREATE PROCEDURE vw_get_user_details(
    IN user_id INT
)
BEGIN
    SELECT * FROM users WHERE id = user_id;
END;
```

### **2. Follow RESTful API Design**
If your backend follows REST conventions, your stored procedures should align with those patterns.

| **HTTP Method** | **Stored Procedure Naming** | **Purpose** |
|----------------|-----------------------------|------------|
| `POST`         | `fn_create_*`               | Create new records |
| `PUT`/`PATCH`  | `fn_update_*`               | Modify existing records |
| `DELETE`       | `fn_delete_*`               | Remove records |
| `GET`          | `vw_get_*`, `get_*`         | Fetch data |

Example API endpoint mapping:

```sql
-- API: POST /users -> Calls fn_create_user
CREATE PROCEDURE fn_create_user(
    IN name VARCHAR(100),
    IN email VARCHAR(255),
    IN password_hash VARCHAR(256)
)
BEGIN
    INSERT INTO users (name, email, password_hash)
    VALUES (name, email, password_hash);
    -- Return the ID of the new user
    SELECT LAST_INSERT_ID() AS user_id;
END;

-- API: GET /users/{id} -> Calls get_user_by_id
CREATE PROCEDURE get_user_by_id(
    IN user_id INT
)
BEGIN
    SELECT * FROM users WHERE id = user_id;
END;
```

### **3. Enforce Consistency with Code Reviews**
- **Require `fn_*` for mutations** in pull requests.
- **Reject queries that mix SELECT + updates** without a clear function name.

---

## **Code Examples: `fn_*` in Action**

### **Example 1: Mutation (`fn_*`)**
```sql
-- A function to create a new order (mutation)
CREATE PROCEDURE fn_create_order(
    IN user_id INT,
    IN product_id INT,
    IN quantity INT
)
BEGIN
    -- Validate quantity
    IF quantity <= 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Quantity must be positive';
    END IF;

    -- Insert the order
    INSERT INTO orders (user_id, product_id, quantity, created_at)
    VALUES (user_id, product_id, quantity, NOW());

    -- Return the new order ID
    SELECT LAST_INSERT_ID() AS order_id;
END;
```

**How it’s called from an API (e.g., FastAPI):**
```python
# FastAPI endpoint
@app.post("/orders")
def create_order(user_id: int, product_id: int, quantity: int):
    cursor = db.execute("fn_create_order(?, ?, ?)", (user_id, product_id, quantity))
    return {"order_id": cursor.fetchone()["order_id"]}
```

---

### **Example 2: Read-Only Query (`vw_*` or `get_*`)**
```sql
-- A view to fetch user orders (read-only)
CREATE PROCEDURE vw_get_user_orders(
    IN user_id INT
)
BEGIN
    SELECT
        o.id,
        o.product_id,
        o.quantity,
        p.name AS product_name
    FROM orders o
    JOIN products p ON o.product_id = p.id
    WHERE o.user_id = user_id;
END;
```

**How it’s called from an API:**
```python
# FastAPI endpoint
@app.get("/users/{user_id}/orders")
def get_user_orders(user_id: int):
    cursor = db.execute("vw_get_user_orders(?)", (user_id,))
    return [dict(row) for row in cursor.fetchall()]
```

---

## **Common Mistakes to Avoid**

### **1. Overusing `fn_*` for Everything**
Don’t prefix **every** stored procedure with `fn_`. It should only be used for **explicit mutations**.

❌ **Bad:**
```sql
CREATE PROCEDURE fn_get_user_by_email(IN email VARCHAR(255)) -- Mutation? No!
```

✅ **Good:**
```sql
CREATE PROCEDURE get_user_by_email(IN email VARCHAR(255)) -- Read-only
```

### **2. Not Enforcing Separation of Concerns**
Avoid procedures that do **both** reads and writes.

❌ **Bad:**
```sql
CREATE PROCEDURE fn_check_and_update_balance(IN user_id INT, IN amount DECIMAL(10,2))
BEGIN
    SELECT balance FROM accounts WHERE id = user_id; -- Read
    UPDATE accounts SET balance = balance - amount WHERE id = user_id; -- Write
END;
```

✅ **Good:**
```sql
-- Separate read and write
CREATE PROCEDURE get_account_balance(IN user_id INT) -- Read
BEGIN
    SELECT balance FROM accounts WHERE id = user_id;
END;

CREATE PROCEDURE fn_withdraw_money(IN user_id INT, IN amount DECIMAL(10,2)) -- Write
BEGIN
    UPDATE accounts SET balance = balance - amount WHERE id = user_id;
END;
```

### **3. Ignoring Transaction Safety**
If your `fn_*` procedure fails mid-execution, ensure it **rolls back** changes.

❌ **Unsafe:**
```sql
CREATE PROCEDURE fn_transfer_funds(IN from_id INT, IN to_id INT, IN amount DECIMAL(10,2))
BEGIN
    -- Deduct from 'from' account (but what if the update fails?)
    UPDATE accounts SET balance = balance - amount WHERE id = from_id;

    -- Add to 'to' account (but what if this fails?)
    UPDATE accounts SET balance = balance + amount WHERE id = to_id;
END;
```

✅ **Safe (with transaction):**
```sql
CREATE PROCEDURE fn_transfer_funds(IN from_id INT, IN to_id INT, IN amount DECIMAL(10,2))
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
        ROLLBACK;

    START TRANSACTION;

    -- Deduct from 'from' account
    UPDATE accounts SET balance = balance - amount WHERE id = from_id;

    -- Add to 'to' account
    UPDATE accounts SET balance = balance + amount WHERE id = to_id;

    COMMIT;
END;
```

---

## **Key Takeaways**

✔ **Use `fn_*` for mutations only** – It signals intent and improves readability.
✔ **Keep reads separate** – Use `vw_*` or `get_*` for queries.
✔ **Avoid hybrid procedures** – Don’t mix reads and writes in one procedure.
✔ **Enforce transactions** – Always use `START TRANSACTION` for safe mutations.
✔ **Align with REST APIs** – Design procedures to match HTTP methods.
✔ **Document your convention** – Make sure the whole team follows it.

---

## **Conclusion: Small Change, Big Impact**

The `fn_*` naming convention might seem like a tiny detail, but it’s one of those **small wins** that compound over time. By explicitly separating read-only queries from mutating functions, you:

- **Reduce confusion** – No more guessing whether a procedure changes data.
- **Improve security** – Prevents accidental writes in read-only contexts.
- **Make refactoring safer** – Splitting or merging procedures becomes easier.

Start applying this pattern today—even in small projects. The consistency you build now will save you hours of debugging later.

**Try it out:**
1. Pick one of your projects with unclear stored procedures.
2. Rename `fn_*` for mutations and `get_*`/`vw_*` for queries.
3. Review your API calls to ensure they align.

Your future self (and your teammates) will thank you.

---
**Further Reading:**
- [RESTful API Design Best Practices](https://restfulapi.net/)
- [Database Transactions in MySQL](https://dev.mysql.com/doc/refman/8.0/en/commit.html)
- [Stored Procedure Anti-Patterns](https://blog.sqlauthority.com/2009/03/23/sql-server-stored-procedure-antipatterns/)
```

---
**Why This Works:**
- **Clear structure** – From problem to solution with practical examples.
- **Hands-on approach** – Code snippets make it easy to trial the pattern.
- **Honest about tradeoffs** – Covers edge cases like transactions.
- **Encourages adoption** – Ends with actionable steps.