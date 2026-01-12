```markdown
---
title: "Availability Validation: Ensuring Your API Serves Valid Data Before Processing"
date: 2023-11-05
author: "Alex Chen"
tags: ["database design", "backend engineering", "API design", "software patterns"]
description: "Learn how to validate data availability before processing requests to prevent common pitfalls like race conditions, inconsistent states, and wasted resources. Practical examples in SQL, Python, and Java."
---

# **Availability Validation: Ensuring Your API Serves Valid Data Before Processing**

When building APIs and database-backed applications, you want to confidently process requests—right? But what happens when user A places an order for the last available item, and user B also checks availability *just before* A finishes the transaction? Suddenly, your system serves inconsistent data, leading to frustration, wasted resources, or even financial losses.

This is where **availability validation** comes in. The pattern ensures that data (e.g., inventory, seats, credits) is available *at the exact moment* of processing, not just when it was checked. It’s a critical safeguard against race conditions, stale data, and costly errors.

In this guide, we’ll explore:
- Why availability validation matters (and the pain points it solves)
- How to implement it in databases and APIs
- Practical code examples in SQL, Python, and Java
- Common mistakes to avoid

By the end, you’ll have actionable strategies to make your systems more reliable.

---

## **The Problem: When Availability Validation Fails**

Imagine an e-commerce platform where users can book limited-edition products. Without proper checks, two users might:
1. Check inventory → both see `quantity = 1`.
2. Place orders → both "win" the last item, leading to over-sales.

This is a classic **race condition**. Worse, if your system processes requests asynchronously (e.g., via Kafka or Celery), the problem worsens:
- User A checks inventory, sees `quantity = 10`.
- User B checks, also sees `quantity = 10`.
- User A’s order reduces inventory to `9` *before* B’s request is processed.
- User B’s order succeeds with `quantity = 9`, leaving negative stock.

### **Real-World Consequences**
- **Lost Revenue**: Over-selling leads to refunds and damaged credibility.
- **Technical Debt**: Fixing race conditions often requires complex refactoring.
- **Poor UX**: Users face errors like "Sorry, this item is out of stock" after adding to cart.

Without validation, your system is essentially a **black box**—users trust it, but the backend fails silently.

---

## **The Solution: Availability Validation Patterns**

Availability validation ensures that:
1. Data is read *consistently* across transactions.
2. Updates are atomic (no partial modifications).
3. External checks (e.g., cache, microservices) are validated again.

Here are three key approaches:

### **1. Pessimistic Locking (Database-Level)**
Hold a lock on the data during validation to prevent concurrent changes.
*Best for*: Low-latency systems where correctness > performance.

### **2. Optimistic Locking (Version-Based)**
Use a "version" column to detect conflicts. If a row’s version changes between read and write, reject the update.
*Best for*: Read-heavy systems with infrequent conflicts.

### **3. Pre-Checks (Application-Level)**
Validate availability *before* processing (e.g., in a separate transaction).
*Best for*: High-contention scenarios (e.g., inventory systems).

---

## **Implementation Guide**

Let’s explore each pattern with code examples.

---

### **1. Pessimistic Locking in PostgreSQL**
Lock a row during validation to block other transactions.

#### **SQL Example**
```sql
-- Start a transaction with a table-level lock
BEGIN TRANSACTION;

-- Lock the inventory row for SELECT + UPDATE
SELECT * FROM inventory
WHERE product_id = 123
FOR UPDATE;

-- Check availability
IF quantity >= desired_quantity THEN
    -- Update inventory
    UPDATE inventory
    SET quantity = quantity - desired_quantity
    WHERE product_id = 123;

    COMMIT;
    RETURN "Success";
ELSE
    ROLLBACK;
    RETURN "Out of stock";
END IF;
```

#### **Python (Using `psycopg2`)**
```python
import psycopg2

def book_product(product_id, quantity):
    conn = psycopg2.connect("dbname=inventory")
    try:
        with conn.cursor() as cursor:
            # Lock the row
            cursor.execute(
                "SELECT * FROM inventory WHERE product_id = %s FOR UPDATE",
                (product_id,)
            )
            inventory = cursor.fetchone()

            if inventory["quantity"] >= quantity:
                # Update after locking
                cursor.execute(
                    "UPDATE inventory SET quantity = quantity - %s WHERE product_id = %s",
                    (quantity, product_id)
                )
                conn.commit()
                return {"status": "success"}
            else:
                conn.rollback()
                return {"status": "out_of_stock"}
    finally:
        conn.close()
```

**Tradeoffs**:
✅ **Simple** to implement.
❌ **Blocks other transactions** (low concurrency).

---

### **2. Optimistic Locking (PostgreSQL + Python)**
Use a `version` column to detect conflicts.

#### **SQL Table Setup**
```sql
CREATE TABLE inventory (
    id SERIAL PRIMARY KEY,
    product_id INT,
    quantity INT,
    version INT DEFAULT 0  -- Optimistic lock version
);
```

#### **Python Example**
```python
def book_product(product_id, quantity, expected_version):
    conn = psycopg2.connect("dbname=inventory")
    try:
        with conn.cursor() as cursor:
            # Check availability and version
            cursor.execute(
                """
                SELECT quantity, version FROM inventory
                WHERE product_id = %s AND version = %s
                FOR UPDATE
                """,
                (product_id, expected_version)
            )
            row = cursor.fetchone()

            if not row:
                return {"status": "failed", "error": "Version conflict"}

            if row["quantity"] >= quantity:
                # Update with new version
                cursor.execute(
                    """
                    UPDATE inventory
                    SET quantity = quantity - %s, version = version + 1
                    WHERE product_id = %s AND version = %s
                    RETURNING version
                    """,
                    (quantity, product_id, row["version"])
                )
                conn.commit()
                return {"status": "success", "new_version": cursor.fetchone()[0]}
            else:
                conn.rollback()
                return {"status": "out_of_stock"}
    finally:
        conn.close()
```

**Tradeoffs**:
✅ **High concurrency** (no locks during read).
❌ **Requires retries** if version conflicts occur.

---

### **3. Pre-Checks (Two-Phase Validation)**
First, validate availability in a separate transaction. Then, proceed only if unchanged.

#### **Python Example**
```python
from contextlib import contextmanager
import psycopg2

@contextmanager
def transaction(conn):
    cur = conn.cursor()
    try:
        yield cur
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e

def book_product(product_id, quantity):
    conn = psycopg2.connect("dbname=inventory")

    # Phase 1: Check availability
    with transaction(conn) as cur:
        cur.execute("SELECT quantity FROM inventory WHERE product_id = %s", (product_id,))
        available = cur.fetchone()[0]

        if available < quantity:
            return {"status": "out_of_stock"}

        # Phase 2: Reserve with lock
        cur.execute(
            "SELECT * FROM inventory WHERE product_id = %s FOR UPDATE",
            (product_id,)
        )
        inventory = cur.fetchone()

        if inventory["quantity"] >= quantity:
            cur.execute(
                "UPDATE inventory SET quantity = quantity - %s WHERE product_id = %s",
                (quantity, product_id)
            )
            return {"status": "success"}
    finally:
        conn.close()
```

**Tradeoffs**:
✅ **Balances performance and correctness**.
❌ **More complex** (two round-trips to DB).

---

## **Common Mistakes to Avoid**

1. **Assuming "SELECT FOR UPDATE" is enough**
   - Forgetting to check `quantity` *after* locking can lead to race conditions.

2. **Using optimistic locking without retries**
   - If a version conflict occurs, your app should retry or notify the user.

3. **Overusing pessimistic locking**
   - Can degrade performance in high-traffic systems.

4. **Ignoring async validation**
   - If using caching or microservices, revalidate data *before* processing.

5. **Not handling partial failures**
   - Example: If inventory is updated but payment fails, roll back both.

---

## **Key Takeaways**

- **Availability validation prevents over-selling and data corruption**.
- **Three main approaches**:
  - Pessimistic locking (simple but blocking).
  - Optimistic locking (scalable but requires retries).
  - Pre-checks (hybrid approach for complex workflows).
- **Always validate *after* locking** (don’t assume the lock is enough).
- **Test edge cases** (e.g., concurrent requests, network failures).

---

## **Conclusion**

Availability validation is a small but critical part of building reliable systems. Whether you’re managing inventory, seat reservations, or credits, proper checks ensure users get what they expect—every time.

### **Next Steps**
1. Start with **optimistic locking** for high-traffic systems.
2. For sensitive data (e.g., banking), use **pessimistic locks** or **two-phase validation**.
3. Monitor conflicts and adjust (e.g., retry logic, fallback mechanisms).

Now go build something that *always* works!

---
**Have you encountered race conditions in your apps? Share your stories in the comments!**
```