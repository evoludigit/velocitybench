```markdown
# **"fn_* Prepending": The Simple (But Effective) Stored Procedure Naming Pattern**

*Why clear patterns matter for maintainable database code—and how this tiny convention saves you from endless confusion*

---

## **Introduction: When "What Am I Looking At" Isn’t Just a Curiosity**

As backend engineers, we spend a disproportionate amount of time navigating and maintaining code we didn’t write. Stored procedures—those self-contained snippets of SQL logic—are no exception. Whether in PostgreSQL, SQL Server, or Oracle, they can become a tangled mess of procedures, functions, and views, especially in legacy systems.

The problem? **Ambiguity.** Without explicit conventions, it’s unclear whether a procedure is:
- A **read-only query** (view-like)
- A **pure function** (deterministic, no side effects)
- A **mutation action** (writes to the database)
- A **hybrid** (complex logic with state)

This ambiguity isn’t just an annoyance—it leads to:
✅ **Debugging nightmares** ("Is this `update_order` a function or a stored proc?")
✅ **Misleading documentation** (code comments that don’t match behavior)
✅ **Team friction** (junior devs hesitant to modify "mysterious" stored logic)

Enter the **"fn_*" pattern**: a lightweight but powerful naming convention that forces clarity. It’s not revolutionary, but it’s *effective*—the kind of small discipline that compounds over time.

---

## **The Problem: Function vs. View Ambiguity**

Let’s set the stage with a real-world example. Suppose you’re working with an e-commerce platform, and you find this in your database:

```sql
CREATE PROCEDURE update_user_cart(user_id INT, product_id INT)
BEGIN
  UPDATE cart_items
  SET quantity = quantity + 1
  WHERE user_id = user_id AND product_id = product_id;
END;
```

**The question:** Is this a view? A function? A stored procedure?

### **1. "It’s a Procedure" (But What Kind?)**
Stored procedures are conceptually simple: reusable blocks of SQL logic. But in practice, they blur into three categories:
- **Views** (purely read, no side effects)
- **Functions** (deterministic, return data)
- **Actions** (modify data, trigger side effects)

The example above *looks* like a procedure, but its intent is ambiguous. Does it:
- **Return** the updated cart?
- **Modify** the cart silently?
- **Do both**?

### **2. The "Descriptive Naming" Trap**
Some teams try to solve this with naming like:
```sql
CREATE PROCEDURE get_user_orders(user_id INT) -- Returns orders (view-like)
CREATE PROCEDURE place_user_order(user_id INT, product_id INT) -- Modifies DB (action)
```
This works *if* everyone agrees on the convention. But when a junior dev later adds:
```sql
CREATE PROCEDURE validate_user_order(user_id INT, product_id INT)
```
…it’s unclear whether this is:
- A **pure function** (returns a boolean)
- An **action** (also updates an `orders` table)

### **3. Documentation Gaps**
Most databases don’t natively support procedure metadata—no built-in way to tag them as "read-only" or "modifies state." As a result:
- Comments become the authoritative source (but they’re rarely updated).
- Tests are sparse (hard to mock stored procedures).
- Refactoring is risky (what if the procedure secretly writes to DB?).

---
## **The Solution: fn_* Prepending for Clarity**

The **"fn_*" pattern** was inspired by functional programming concepts (e.g., `fn` for functions in Elixir or Haskell) and applied to stored procedures. It’s a simple rule:
> **Any stored procedure that implements a pure function or read-only query should start with `fn_`.**

### **Why It Works**
1. **Explicit over implicit**: Forces developers to declare intent upfront.
2. **Separates concerns**: `fn_*` = pure logic; non-`fn_*` = state-changing actions.
3. **Scalable**: Easy to adopt in existing repos (no breaking changes).
4. **Self-documenting**: No need for comments like `// Returns cart items`.

---

## **Components/Solutions**

### **1. The Naming Rules**
| Prefix  | Meaning                          | Example                          |
|---------|-----------------------------------|----------------------------------|
| `fn_`   | Pure function or read-only query | `fn_get_user_orders()`            |
| `(no prefix)` | Action (modifies data) | `create_order()`, `update_cart()` |
| `util_` | Helper procedural logic (rare)   | `util_generate_token()`          |
| `trigger_` | Event handler (e.g., `ON DELETE`) | `trigger_delete_old_inventory()` |

### **2. When to Use fn_* vs. No Prefix**
| Behavior          | Naming Convention | Example                          |
|-------------------|-------------------|----------------------------------|
| **Returns data**  | `fn_*`            | `fn_get_product_recommendations()` |
| **Modifies data** | No prefix         | `update_order_status()`           |
| **Computes value**| `fn_*`            | `fn_calculate_discount()`         |
| **Side effects**  | No prefix         | `send_notification()`             |

### **3. Edge Cases**
- **Functions that loop**: Still `fn_*` if deterministic (e.g., `fn_generate_fibonacci_sequence()`).
- **Functions with `INOUT` params**: Only use `fn_*` if they *don’t* modify DB state.
- **Stored functions vs. procedures**: Works for both (PostgreSQL/Latin-1 conventions).

---
## **Code Examples**

### **Example 1: Pure Function (fn_*)**
```sql
-- Returns a user's total order value (read-only)
CREATE OR REPLACE FUNCTION fn_calculate_user_spend(user_id INT) RETURNS DECIMAL AS $$
DECLARE
  total DECIMAL;
BEGIN
  SELECT COALESCE(SUM(amount), 0) INTO total
  FROM orders
  WHERE user_id = user_id;

  RETURN total;
END;
$$ LANGUAGE plpgsql;

-- Usage: SELECT fn_calculate_user_spend(123);
```

### **Example 2: Action (No Prefix)**
```sql
-- Modifies the database (no fn_ prefix)
CREATE PROCEDURE refund_order(order_id INT)
BEGIN
  UPDATE orders SET status = 'refunded' WHERE order_id = order_id;
  INSERT INTO refund_history (order_id, amount) VALUES (order_id, (SELECT total FROM orders WHERE order_id = order_id));
END;
```

### **Example 3: Hybrid (Bad!)**
```sql
-- ❌ Ambiguous: Does this return data? Modify DB?
CREATE PROCEDURE process_order(order_id INT)
BEGIN
  -- Returns order details...
  SELECT * FROM orders WHERE order_id = order_id;

  -- ...and updates status
  UPDATE orders SET status = 'processed' WHERE order_id = order_id;
END;
```
**Fix:** Split into two procedures:
```sql
-- Pure function
CREATE FUNCTION fn_get_order(order_id INT) RETURNS orders AS $$
BEGIN
  RETURN QUERY SELECT * FROM orders WHERE order_id = order_id;
END;
$$;

-- Action
CREATE PROCEDURE mark_order_processed(order_id INT) AS $$
BEGIN
  UPDATE orders SET status = 'processed' WHERE order_id = order_id;
END;
$$;
```

### **Example 4: Trigger vs. fn_* (Contrast)**
```sql
-- Event handler (uses trigger_ prefix)
CREATE TRIGGER trigger_delete_old_inventory
BEFORE DELETE ON inventory FOR EACH ROW
BEGIN
  IF NEW.stock_date < CURRENT_DATE - INTERVAL '1 year' THEN
    INSERT INTO historical_stock (product_id, quantity) VALUES (NEW.id, NEW.quantity);
  END IF;
END;
```

---

## **Implementation Guide**

### **Step 1: Audit Existing Procedures**
Run a query to find all stored procedures:
```sql
-- PostgreSQL
SELECT proname, prosrc
FROM pg_proc
WHERE pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public');

-- SQL Server
SELECT name, definition
FROM sys.sql_modules
WHERE object_id IN (
  SELECT object_id
  FROM sys.objects
  WHERE type = 'P' OR type = 'FN'
);
```
**Action:** Flag ambiguous procedures (e.g., `update_*` without clear intent).

### **Step 2: Enforce the Rule in Code Reviews**
Add a check in your review tool (e.g., PR comment template):
> ⚠️ **Stored Procedure Naming Check**
> - Does this procedure start with `fn_*` if it’s read-only?
> - Does it modify data without the `fn_*` prefix?

### **Step 3: Update Documentation**
Annotate your DB schema (e.g., in a `README.md`):
```markdown
# Stored Procedure Naming Conventions
| Prefix | Purpose                          |
|--------|----------------------------------|
| fn_    | Pure functions or queries       |
| (none) | Actions (modifies DB state)      |
```
### **Step 4: Tooling (Optional)**
For PostgreSQL, extend `pg_catalog` with views:
```sql
CREATE OR REPLACE VIEW v_procedure_metadata AS
SELECT
  proname,
  CASE
    WHEN proname LIKE 'fn_%' THEN 'function'
    ELSE 'action'
  END AS procedure_type
FROM pg_proc
WHERE pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public');
```

---

## **Common Mistakes to Avoid**

### **1. Overusing fn_* for Actions**
❌ Wrong:
```sql
CREATE FUNCTION fn_update_user_cart(user_id INT, product_id INT) -- Modifies DB!
BEGIN
  UPDATE cart_items SET quantity = quantity + 1 WHERE ...;
END;
```
**Fix:** Use no prefix for actions.

### **2. Ignoring Hybrid Procedures**
❌ Wrong:
```sql
CREATE PROCEDURE fn_get_and_update_order(order_id INT) -- Does both!
BEGIN
  SELECT * FROM orders WHERE ...; -- Returns data
  UPDATE orders SET status = 'seen' WHERE ...; -- Modifies DB
END;
```
**Fix:** Split into separate procedures.

### **3. Misusing fn_ for Stateful Logic**
❌ Wrong:
```sql
CREATE FUNCTION fn_generate_invoice(user_id INT) -- "Pure" but writes to DB!
RETURNS INT AS $$
DECLARE
  invoice_id INT;
BEGIN
  INSERT INTO invoices (user_id, amount) VALUES (user_id, 100) RETURNING id INTO invoice_id;
  RETURN invoice_id;
END;
$$;
```
**Fix:** Use no prefix (it’s an action).

### **4. Forgetting to Update Comments**
❌ Wrong:
```sql
-- ❌ Comment doesn’t match behavior
CREATE FUNCTION fn_get_user_data(user_id INT) RETURNS JSON
-- Returns updated user data (but actually modifies it!)
```
**Fix:** Keep comments aligned with code.

---

## **Key Takeaways**

✅ **Clarity > Creativity**: The `fn_*` prefix isn’t about being clever—it’s about reducing cognitive load.
✅ **Consistency Wins**: Enforce the rule across the team (code reviews, tooling).
✅ **Split Ambiguous Logic**: If a procedure does both read/write, split it.
✅ **Document Clearly**: Update DB docs to reflect the convention.
✅ **Tooling Helps**: Use queries/views to audit procedure types.

---

## **Conclusion: Small Patterns, Big Impact**

The `fn_*` naming pattern might seem trivial, but its value lies in **preventing ambiguity before it becomes a bug**. In a team of 5 people, it’s a minor discussion. In a team of 500? It saves hours of debugging.

Adopt it not because it’s perfect, but because it’s **practical and scalable**. Start with a migration plan, enforce it in reviews, and watch how much easier stored procedures become to maintain.

**Final Challenge**: Audit your database today. How many stored procedures could benefit from `fn_*`? Even one clear naming convention makes the difference between a codebase that’s *manageable* and one that’s a *black box*.

---
**Further Reading**
- [PostgreSQL Stored Procedures Docs](https://www.postgresql.org/docs/current/plpgsql.html)
- [SQL Server Functions vs. Procedures](https://learn.microsoft.com/en-us/sql/relational-databases/stored-procedures/stored-procedure-functions)
- [Clean Code: Naming Conventions](https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350882)

---
```markdown
---
**Author**: [Your Name]
**Post Date**: [YYYY-MM-DD]
**Tags**: #databases #sql #backend #namingconventions #storedprocedures

**Why This Matters**: Ambiguous database code isn’t just a developer annoyance—it’s a technical debt that compounds. Small patterns like `fn_*` may seem insignificant, but they’re the difference between a system that’s *understood* and one that’s *feared*.
```

---
**P.S.** Want to take this further? Pair this with **parameterized naming** (e.g., `fn_calculate_discount_for_user()` instead of `fn_calculate_discount()`) for even more clarity. The goal is **zero ambiguity**.