```markdown
---
title: "fn_* Stored Procedure Naming: A Practical Guide to Clarity in Database Design"
date: 2024-02-15
tags: ["database design", "sql patterns", "backend engineering", "stored procedures", "naming conventions"]
authors: ["Alex Chen"]
description: "Learn how the fn_* naming convention clarifies the distinction between stored procedures as functions vs. views, reducing ambiguity in database design."
---

# fn_* Stored Procedure Naming: A Practical Guide to Clarity in Database Design

Database design isn't just about schema layout—it's also about creating intentional patterns that reduce ambiguity for future developers (including your future self). One often-overlooked yet highly impactful convention is the `fn_*` prefix for stored procedure naming. This simple convention can transform an opaque database layer into a self-documenting one, making it easier to reason about transaction boundaries, side effects, and invariants.

In this post, we’ll dive into why the `fn_*` naming pattern matters, how it solves a common problem, and how to implement it effectively. You’ll see concrete examples and anti-patterns to avoid, equipping you with practical insights you can apply immediately to your projects.

---

## The Problem: Function vs. View Ambiguity

Stored procedures are a double-edged sword. On the one hand, they encapsulate business logic, improve security by centralizing permissions, and can optimize complex queries. On the other hand, they often blur the line between *what* the database does and *how* it does it.

Consider this all-too-common scenario:

```sql
-- db_schema/orders.sql
CREATE PROCEDURE GetOrderSummary(IN order_id INT)
BEGIN
    SELECT customer_name, order_date, total_amount
    FROM orders o
    JOIN customers c ON o.customer_id = c.id
    WHERE o.id = order_id;
END;

-- Another developer later adds this:
CREATE PROCEDURE CreateOrder(IN customer_id INT, IN items JSON)
BEGIN
    INSERT INTO orders (customer_id, status, created_at)
    VALUES (customer_id, 'pending', NOW());

    INSERT INTO order_items (order_id, product_id, quantity)
    SELECT order_id, item.product_id, item.quantity
    FROM orders o
    CROSS JOIN JSON_TABLE(items, '$[*]' COLUMNS(
        product_id INT PATH '$.id',
        quantity INT PATH '$.quantity'
    )) AS item
    WHERE o.customer_id = customer_id;
END;
```

What’s the problem here? Let’s refactor the names to see:

```sql
-- Renamed to reflect intent
CREATE PROCEDURE GetOrderSummary(IN order_id INT) /* READ-ONLY VIEW */
BEGIN
    SELECT customer_name, order_date, total_amount
    FROM orders o
    JOIN customers c ON o.customer_id = c.id
    WHERE o.id = order_id;
END;

CREATE PROCEDURE CreateOrder(IN customer_id INT, IN items JSON) /* MUTATION FUNCTION */
BEGIN
    INSERT INTO orders (customer_id, status, created_at)
    VALUES (customer_id, 'pending', NOW());

    INSERT INTO order_items (order_id, product_id, quantity)
    SELECT order_id, item.product_id, item.quantity
    FROM orders o
    CROSS JOIN JSON_TABLE(items, '$[*]' COLUMNS(
        product_id INT PATH '$.id',
        quantity INT PATH '$.quantity'
    )) AS item
    WHERE o.customer_id = customer_id;
END;
```

Now, the intention is clearer—but **why the difference in naming isn’t obvious is the real issue**. Both procedures accept input parameters and return results, but:

1. **`GetOrderSummary`** *reads* data and *does not modify* it.
2. **`CreateOrder`** *writes* data, triggers side effects, and has transactional invariants.

Without clear naming, future developers (or even you in a few months) might:
- Assume `CreateOrder` is a read-only query and pass it a precomputed order to "retrieve."
- Overlook transactional guarantees when calling `CreateOrder` in an application.
- Mix up the parameters or return types in API contracts.

This ambiguity is the core problem: **stored procedures act like both functions (pure transformations) and views (materialized queries), but their naming doesn’t reflect this distinction.**

---

## The Solution: The `fn_*` Naming Pattern

The `fn_*` convention comes from functional programming principles and database theory. It explicitly marks stored procedures that behave like functions (mathematical transformations) rather than views (materialized queries). Here’s how it works:

1. **`fn_*` = Function**: The procedure performs a computation with no hidden side effects. Its output depends purely on its inputs.
   - Example: `fn_calculate_discounted_price`
   - Characteristics: Deterministic, no writes, no transactional assumptions.

2. **No prefix** = View-like procedure: The procedure reads data but may have implicit assumptions (e.g., transactional guarantees, materialized results).
   - Example: `GetCustomerOrders` (implies read-only, but may still have complex logic).
   - Characteristics: May have side effects, depends on state, or is optimized for materialization.

### Why `fn_*` Works
- **Self-documenting**: The prefix communicates intent without comments.
- **Consistent**: You can audit your database for all functions vs. procedural logic.
- **Interoperable**: Makes it easier to integrate with pure functions (e.g., in API contracts or testing).

---

## Implementation Guide

### Step 1: Separate Functionality by Behavior
Divide stored procedures into two categories:

1. **Functions (`fn_*`)**:
   - Pure transformations (e.g., `fn_format_address`, `fn_calculate_tax`).
   - Read-only queries where output depends only on input.
   - Logic that can be safely externalized (e.g., to application code or a microservice).

2. **Non-functions (procedural logic)**:
   - Procedures that modify data or have transactional guarantees.
   - Materialized queries (e.g., `GetRecentOrders`).
   - Complex workflows (e.g., `ProcessPayment` with multiple tables).

### Step 2: Rename Existing Procedures
Start with a migration plan. For example:

```diff
- CREATE PROCEDURE OrderSummary(IN order_id INT) /* Ambiguous */
+ DROP PROCEDURE IF EXISTS OrderSummary;
+ CREATE PROCEDURE fn_order_summary(IN order_id INT) /* Pure function */
```

### Step 3: Apply to New Code
Enforce `fn_*` for new functions in code reviews. Tools like [Dbeaver](https://dbeaver.io/) or [pgAdmin](https://www.pgadmin.org/) can highlight naming patterns.

### Step 4: Document Assumptions
Even with `fn_*`, document non-obvious behavior for non-functions:

```sql
-- Mark this as a side-effectful procedure
CREATE PROCEDURE UpdateOrderStatus(IN order_id INT, IN new_status VARCHAR(50))
BEGIN
    UPDATE orders SET status = new_status WHERE id = order_id;
    -- Side effect: Triggers event_publishing
    CALL fn_publish_order_status_event(order_id, new_status);
END;
```

---

## Practical Code Examples

### Example 1: Functional vs. Non-functional Order Procedures

#### Non-functional: Workflow Logic
```sql
-- Procedural logic with side effects
CREATE PROCEDURE CreateOrder(
    IN customer_id INT,
    IN items JSON,
    OUT order_id INT
) BEGIN
    START TRANSACTION;
    INSERT INTO orders (customer_id, status, created_at)
    VALUES (customer_id, 'pending', NOW())
    RETURNING id INTO order_id;

    INSERT INTO order_items (order_id, product_id, quantity)
    SELECT order_id, item.product_id, item.quantity
    FROM JSON_TABLE(items, '$[*]' COLUMNS(
        product_id INT PATH '$.id',
        quantity INT PATH '$.quantity'
    )) AS item;

    -- Side effect: Update customer's last_order_date
    UPDATE customers SET last_order_date = NOW() WHERE id = customer_id;

    CALL fn_publish_order_event(order_id, 'created');
    COMMIT;
END;
```

#### Functional: Pure Transformation
```sql
-- Pure function: No side effects, input-only
CREATE FUNCTION fn_calculate_order_total(
    IN order_id INT
) RETURNS DECIMAL(10, 2) DETERMINISTIC
AS $$
    SELECT COALESCE(SUM(oi.quantity * p.price), 0)
    FROM order_items oi
    JOIN products p ON oi.product_id = p.id
    WHERE oi.order_id = order_id;
$$;
```

---

### Example 2: Avoiding Common Pitfalls

#### ❌ Anti-pattern: Unsafe Side Effects in "Functions"
```sql
-- ❌ WRONG: Looks like a function but modifies data!
CREATE FUNCTION fn_apply_discount(
    IN order_id INT,
    IN discount_percent DECIMAL(3, 2)
) RETURNS VOID /* Lies about being a function */
AS $$
    UPDATE orders SET total_amount = total_amount *
        (1 - discount_percent/100) WHERE id = order_id;
$$;
```
**Problem**: The `fn_` prefix misleads callers into treating this as a pure function.

#### ✅ Fix: Explicitly Label Side Effects
```sql
CREATE PROCEDURE ApplyDiscount(
    IN order_id INT,
    IN discount_percent DECIMAL(3, 2)
)
BEGIN
    UPDATE orders SET total_amount = total_amount *
        (1 - discount_percent/100) WHERE id = order_id;

    -- Document the side effect
    CALL fn_audit_order_modification(order_id, 'DISCOUNT_APPLIED');
END;
```

---

### Example 3: Integrating with APIs
Use `fn_*` functions to create clean, predictable API endpoints:

```sql
-- API: Get order total (pure function)
CREATE PROCEDURE GetOrderTotal(IN order_id INT)
BEGIN
    SELECT fn_calculate_order_total(order_id) AS total;
END;
```

vs.

```sql
-- API: Create order (procedural)
CREATE PROCEDURE CreateOrder(IN customer_id INT, IN items JSON)
BEGIN
    CALL CreateOrderTransactional(customer_id, items);
END;
```

---

## Common Mistakes to Avoid

1. **Overusing `fn_*`**:
   - Don’t prefix every procedure. Reserve `fn_*` for pure functions only.
   - Example: `fn_get_orders` is misleading if it’s actually a materialized query.

2. **Ignoring Procedural Logic**:
   - Assume all unmarked procedures are functions. Document side effects explicitly.

3. **Mixing Concerns in Functions**:
   - A function like `fn_validate_email_and_update_profile` is no longer pure (it modifies data).

4. **Assuming Deterministic Behavior**:
   - Even functions can fail if inputs change. Document edge cases:
     ```sql
     CREATE FUNCTION fn_create_user_email_check(
         IN email VARCHAR(255)
     ) RETURNS BOOLEAN
     DETERMINISTIC
     COMMENT 'Returns TRUE if email is available for registration.'
     AS $$
         SELECT COUNT(*) = 0 FROM users WHERE email = $1;
     $$;
     ```

5. **Not Updating Applications**:
   - Renaming procedures breaks code. Plan migrations carefully and update app contracts (e.g., gRPC, GraphQL).

---

## Key Takeaways

- **`fn_*` is for functions only**: Pure transformations with no side effects.
- **No prefix is for procedural logic**: Workflows, materialized queries, or state changes.
- **Clarity > Consistency**: If renaming breaks existing contracts, prioritize communication over perfection.
- **Complement with documentation**: Even with `fn_*`, document invariants (e.g., "This function returns NULL for invalid orders").
- **Tooling matters**: Use IDEs or database tools to enforce naming conventions.

---

## Conclusion

The `fn_*` naming pattern is a small but powerful way to reduce cognitive load in your database layer. By explicitly distinguishing between functions and procedural logic, you:

1. Reduce bugs caused by misinterpreted procedure behavior.
2. Make it easier to reason about transaction boundaries.
3. Enable safer refactoring (e.g., externalizing functions to application code).

Start with a few critical functions (e.g., `fn_calculate_discount`, `fn_format_address`) and iterate. Over time, your database will become more predictable—and your team’s confidence in it will grow.

As with all conventions, this pattern isn’t a silver bullet. Use it judiciously, pair it with clear documentation, and stay mindful of tradeoffs. But in the right context, `fn_*` is a simple, effective way to write cleaner database code.

---
```