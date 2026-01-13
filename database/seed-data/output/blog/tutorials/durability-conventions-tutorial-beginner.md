```markdown
---
title: "Durability Conventions: Ensuring Your Data Stays Safe in Unpredictable Worlds"
date: 2023-10-15
author: "Alex Carter"
tags: ["backend", "database", "durability", "pattern", "best-practice"]
slug: "durability-conventions-pattern"
---

# Durability Conventions: Ensuring Your Data Stays Safe in Unpredictable Worlds

![Database durability illustration](https://via.placeholder.com/1200x400?text=Database+Durability+Illustration)

---

## Introduction

Every backend engineer has faced the terrifying moment when a system crash, network interruption, or human error threatens to erase hours—or *years*—of data. In today’s web applications, from social media platforms to financial services, **data loss is unacceptable**.

The **"Durability Conventions"** pattern helps you design systems where data persists reliably despite failures, crashes, or unexpected interruptions. Unlike traditional "durability = ACID transactions" or "use a reliable database," this pattern focuses on *how your code interacts with storage* to ensure data *stays where it belongs*.

In this guide, we’ll explore why durability matters, how to implement it with real-world examples, and common pitfalls to avoid. Let’s start by understanding the problem.

---

## The Problem: Why Data Vanishes Like Digital Smoke

Imagine this scenario:

- **A user uploads an 80MB video** to your app using a built-in "Save" button.
- The upload completes, and the UI shows a success message.
- But then, **a network outage occurs**—or the server crashes—before the data reaches the database.
- When the user reloads the page, the video is *gone*.

Or consider:

- A **banking app** processes a withdrawal.
- The transaction appears successful in the UI, but due to a race condition, the database update fails.
- The user’s account is debited, but the record *disappears* from the system.

These scenarios aren’t hypothetical. They happen every day, often because teams overlook small but critical **durability conventions**—rules your code must follow to ensure data isn’t lost.

### The Hidden Risks Without Durability Conventions

1. **Network Interruptions** – If your app saves data to a remote database but doesn’t handle retries or timeouts, a blip in connectivity can mean lost data.
2. **Race Conditions** – Concurrent users or processes can overwrite each other’s changes if not properly synchronized.
3. **Incomplete Transactions** – Even with ACID databases, poorly written code can leave transactions in a "half-committed" state.
4. **Human Errors** – Developers might forget to commit changes or assume "close the connection" means data is safely stored.
5. **Hardware Failures** – Disk corruption, memory leaks, or OS crashes can delete data in transit.

Without explicit durability guarantees, **your application’s reliability is an accident waiting to happen**.

---

## The Solution: Durability Conventions

Durability conventions are **explicit rules** your code must follow to ensure data is safely persisted, even in the face of failures. Unlike high-level abstractions (like ORMs or frameworks), these conventions are about **how your code interacts with the storage layer**.

### Core Idea: **Assume Nothing Persists Until You Confirm It Does**

The guiding principle is this:
> *"Your database is a black box. Never trust that data has been saved unless you explicitly verify it."*

This means:

✅ **Validate writes** – Only consider a write successful after confirming it reached the database.
✅ **Handle retries** – Reattempt failed writes with backoff to avoid data loss.
✅ **Use transactions wisely** – Group related operations in a single transaction when possible.
✅ **Decouple persistence from UI feedback** – Don’t assume the UI reflects the actual state of the database.

---

## Components of Durability Conventions

Durability conventions can be broken down into three key components:

| Component          | Purpose                                                                 |
|--------------------|-------------------------------------------------------------------------|
| **Atomic Writes**  | Ensure each write operation is either fully completed or never happened.|
| **Idempotency**    | Guarantee the same operation can be retried safely without side effects.|
| **Persistence Checks** | Verify data is safely stored before proceeding.                      |

Let’s explore each with code examples.

---

## 1. Atomic Writes: The "All or Nothing" Rule

An **atomic write** means your code treats a single database operation (e.g., `INSERT`, `UPDATE`) as a single unit. No partial saves are allowed.

### Example: Safe Product Inventory Update

```python
# ❌ BAD: Non-atomic write (race condition risk)
def update_inventory(product_id, quantity):
    current_stock = get_product_stock(product_id)  # Not in a transaction
    new_stock = current_stock - quantity
    update_product_stock(product_id, new_stock)    # What if this fails?
    return True
```

This code is vulnerable to race conditions. If another process updates the stock between `get_product_stock` and `update_product_stock`, the result could be incorrect.

### Solution: Use Transactions

```python
# ✅ GOOD: Atomic write with a transaction
def update_inventory(product_id, quantity):
    with db.session.begin():  # Start a transaction
        current_stock = db.query("SELECT stock FROM products WHERE id = :id", {"id": product_id}).scalar()
        if current_stock < quantity:
            raise ValueError("Insufficient stock")
        new_stock = current_stock - quantity
        db.execute("UPDATE products SET stock = :stock WHERE id = :id", {"stock": new_stock, "id": product_id})
    return True  # Only returns if the transaction succeeds
```

Key takeaways:
- **Wrap database operations in a transaction** when related changes must succeed together.
- **Avoid reading data outside transactions** if it might be modified elsewhere.
- **Use database-level locks** (like `SELECT FOR UPDATE`) if needed.

---

## 2. Idempotency: "Retry Safe" Operations

An **idempotent** operation is one that can be retried without causing unintended side effects.

### Why It Matters

Imagine a user submits an order, but the API call fails due to a network error. If the system retries the same request, it should **not** create duplicate orders.

```python
# ❌ NON-IDEMPOTENT: Could create duplicate orders on retry
@api.route("/orders", methods=["POST"])
def create_order():
    order = request.json
    # No check for existing order → retry could duplicate
    db.execute("INSERT INTO orders (...) VALUES (...)")
    return {"status": "created"}
```

### Solution: Add Idempotency Keys

```python
# ✅ IDEMPOTENT: Uses a unique key to prevent duplicates
import uuid

@api.route("/orders", methods=["POST"])
def create_order():
    order = request.json
    idempotency_key = request.headers.get("Idempotency-Key") or str(uuid.uuid4())

    # Check if order already exists for this key
    if db.query("SELECT COUNT(*) FROM orders WHERE idempotency_key = :key", {"key": idempotency_key}).scalar() > 0:
        return {"status": "already_processed"}, 200

    # Insert the new order
    db.execute(
        "INSERT INTO orders (idempotency_key, user_id, items) VALUES (:key, :user_id, :items)",
        {"key": idempotency_key, "user_id": order["user_id"], "items": order["items"]}
    )
    return {"status": "created"}, 201
```

Key takeaways:
- **Add an `Idempotency-Key` header** to HTTP requests for retry safety.
- **Store the key in the database** alongside the operation.
- **Reject duplicate requests** with the same key.
- **Use this for all external-facing APIs**, especially payment processing.

---

## 3. Persistence Checks: "Don’t Trust; Verify"

The "don’t trust" principle means **never assume** data is saved until you’ve verified it.

### Example: File Uploads

```python
# ❌ BAD: Assumes file save works
def upload_file(file):
    filepath = f"/uploads/{file.filename}"
    file.save(filepath)
    return {"status": "uploaded"}
```

This fails if:
- The disk is full.
- The filesystem is corrupted.
- The server crashes mid-write.

### Solution: Verify After Write

```python
# ✅ GOOD: Confirms file metadata before returning
import os

def upload_file(file):
    filepath = f"/uploads/{file.filename}"
    try:
        with open(filepath, "wb") as f:
            f.write(file.read())
        # Verify file exists and has correct size
        if not os.path.exists(filepath) or os.path.getsize(filepath) != file.size:
            raise IOError("File write failed")
        return {"status": "uploaded", "path": filepath}
    except Exception as e:
        raise e  # Let the caller handle the error
```

Key takeaways:
- **Check file metadata** (size, permissions) after writing.
- **Use database `INSERT` + `SELECT` pattern** to confirm writes.
- **Log persistence failures** for debugging.

---

## Implementation Guide: Durability Conventions in Practice

### Step 1: Define Durability Rules for Your Team

Start by documenting **explicit durability requirements** for your app. Example:

| Operation          | Durability Rule                                                                 |
|--------------------|---------------------------------------------------------------------------------|
| User data          | Always persist in a transaction.                                               |
| File uploads       | Verify disk write before returning success.                                     |
| Payment processing | Use idempotency keys to prevent duplicates.                                   |
| API calls          | Retry failed writes with exponential backoff.                                  |

### Step 2: Instrument Your Code for Persistence Checks

- **For databases**: Use `SELECT ... RETURNING` (PostgreSQL) or `ON CONFLICT` to confirm writes.
- **For files**: Check file properties post-write.
- **For messages**: Ensure message queues confirm delivery.

```python
# Example: PostgreSQL INSERT with RETURNING
def add_user(username, email):
    with db.session.begin():
        new_user = db.execute(
            "INSERT INTO users (username, email) VALUES (:username, :email) RETURNING id",
            {"username": username, "email": email}
        )
        return new_user.fetchone()["id"]
```

### Step 3: Handle Failures Gracefully

- **Retry failed writes** with exponential backoff:
  ```python
  def retry_on_failure(fn, max_retries=3):
      def wrapper(*args, **kwargs):
          last_error = None
          for i in range(max_retries):
              try:
                  return fn(*args, **kwargs)
              except Exception as e:
                  last_error = e
                  time.sleep(2 ** i)  # Exponential backoff
          raise last_error
      return wrapper
  ```
- **Log persistence failures** for monitoring:
  ```python
  import logging
  logging.basicConfig(level=logging.ERROR)

  @retry_on_failure
  def save_user_data(user):
      try:
          db.execute("INSERT INTO user_data (...) VALUES (...)")
      except Exception as e:
          logging.error(f"Failed to save user {user.id}: {e}")
          raise
  ```

### Step 4: Test Durability Scenarios

Write tests to ensure your code handles failures:

```python
# Example: Test for database failure during transaction
def test_transaction_failure():
    with db.session.begin():
        db.execute("INSERT INTO users (...) VALUES (...)")
        # Simulate a crash by raising an exception
        raise RuntimeError("Simulated crash")
    assert False, "Transaction should have been rolled back"
```

---

## Common Mistakes to Avoid

1. **Assuming the UI Reflects Database State**
   - ❌ Show "Saved" to the user before confirming the database write.
   - ✅ Use **optimistic concurrency** (e.g., `version` fields) to handle conflicts.

2. **Ignoring Timeouts**
   - ❌ Let database queries hang indefinitely.
   - ✅ Set **reasonable timeouts** (e.g., 5 seconds for most queries).

3. **Not Handling Retry Logic Explicitly**
   - ❌ Rely on ORMs to "just work" after retries.
   - ✅ Implement **custom retry logic** with backoff.

4. **Overusing Transactions**
   - ❌ Wrapping *every* operation in a transaction.
   - ✅ Use transactions **only for related operations** (e.g., transfer funds).

5. **Forgetting to Close Connections**
   - ❌ Letting database connections leak.
   - ✅ Use **connection pooling** (e.g., `pgbouncer` for PostgreSQL).

---

## Key Takeaways

✔ **Durability isn’t free** – It requires explicit code patterns, not just "using a good database."
✔ **Atomic writes** prevent partial updates by grouping operations in transactions.
✔ **Idempotency** makes retries safe by avoiding duplicates.
✔ **Persistence checks** ensure data is actually saved before success is returned.
✔ **Test for failures** – Assume your app will crash, and design for recovery.
✔ **Document your rules** – Every team member must follow the same durability conventions.

---

## Conclusion: Build Systems That Last

Data loss is a silent killer of user trust. By adopting **durability conventions**, you’re not just adding safeguards—you’re building a system where users can rely on their data being **there tomorrow**, not "maybe."

Start small: Pick one operation (e.g., user signups) and apply these patterns. Then expand. Over time, your entire application will become **resilient to the unpredictable**.

Remember: **The most durable systems aren’t just built—they’re *guaranteed*.**

---

### Further Reading
- [PostgreSQL: Transactions and Isolation Levels](https://www.postgresql.org/docs/current/tutorial-transactions.html)
- [IdempotencyKeys: A Guide](https://idempotencykey.org/)
- [Circuit Breakers Pattern (for resilience)](https://microservices.io/patterns/resilience/circuit-breaker.html)
- [Database Design Patterns (Martin Fowler)](https://martinfowler.com/books/odp.html)

---
```