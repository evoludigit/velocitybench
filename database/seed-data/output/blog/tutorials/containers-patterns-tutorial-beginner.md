```markdown
---
title: "Containers Pattern: Organizing Your Data Like a Pro"
date: "2023-11-15"
author: "Alex Wright"
description: "Learn the Containers Pattern for cleaner, more maintainable database and API design. Real-world examples, tradeoffs, and anti-patterns to avoid."
tags: ["database design", "API design", "backend patterns", "software architecture"]
---

# Containers Pattern: Organizing Your Data Like a Pro

**Thinking about database tables or API endpoints as "containers" for related data isn't just a metaphor—it's a practical approach to clean, scalable design.** Whether you're building a simple CRUD API or a complex microservice architecture, how you group data affects performance, maintainability, and even API design. This post dives into the **Containers Pattern**, a practical approach to organizing relational data and exposing it via APIs without falling into common pitfalls.

We'll explore:
- Real-world scenarios where this pattern shines (or doesn’t)
- Code examples in SQL and Python (FastAPI) for clarity
- Tradeoffs and when to steer clear of this approach
- Anti-patterns that’ll make your system a nightmare

By the end, you’ll understand how to use containers to structure data intuitively, while balancing performance and complexity.

---

## The Problem: When Data Gets Messy

Imagine you're building an e-commerce backend. Initially, you have:
- A **`users`** table with `id`, `name`, and `email`.
- A **`products`** table with `id`, `name`, `price`, and `category`.

As features grow, you add:
- **Orders**: `user_id`, `product_id`, `quantity`
- **User reviews**: `user_id`, `product_id`, `rating`
- **Shopping carts**: `user_id`, `product_id`, `added_at`

Now, your API endpoints look like this:
```python
# FastAPI example
@app.get("/users/{user_id}/orders")
def get_orders(user_id: int):
    return db.query("SELECT * FROM orders WHERE user_id = ?", (user_id,))

@app.get("/users/{user_id}/reviews")
def get_reviews(user_id: int):
    return db.query("SELECT * FROM reviews WHERE user_id = ?", (user_id,))
```

Everything works, but let’s fast-forward to change requests:
1. **"Add a wishlist feature!"** → Now you need a **`wishlists`** table, but:
   - Do you add `/wishlists` to every user endpoint? Not ideal.
2. **"We need to show product details in user orders!"** → You must join `orders` ↔ `products` in every query.
3. **"Mobile users need lightweight endpoints!"** → Your `/users/{id}` endpoint suddenly does 5+ joins.

The result? **Tight coupling** between data structures and API design. Every new feature bumps into the old design, forcing hacks like:
- **Over-fetching**: Sending too much data to clients.
- **Deep nesting**: Returning JSON with 7 levels of nested objects.
- **Ad-hoc joins**: Writing SQL queries that change with every feature.

This is where **Containers Pattern** helps. Instead of treating tables as standalone entities, we group them into "logical containers" and build APIs around those containers.

---

## The Solution: Containers Pattern Explained

The **Containers Pattern** is about **grouping related tables into logical units (containers)** and exposing them as cohesive API endpoints. The core idea:
> *"Treat containers as self-contained data units, not just collections of tables."*

### Key Principles:
1. **Single Responsibility** – Each container solves *one* business problem.
   - Example: The **"Order"** container handles orders, line items, and payments.
   - Not: A **"User"** container that also manages orders and wishlists.

2. **Clear API Boundaries** – Endpoints follow the container structure.
   - Good: `/orders/{order_id}/items`
   - Bad: `/users/{user_id}/products` (mixes user and product data)

3. **Data Consistency** – The container maintains invariants (e.g., order total = sum of item prices).
   - Achieved via **transactions** and **stored procedures**, not business logic in the app.

---

## Components of the Containers Pattern

Let’s design a clear **Order Container** to replace our messy example.

### 1. Database Schema (SQL)
We’ll group related tables into the **`orders`** container:
```sql
-- The container "root" (main table)
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    total DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Child tables (related but in the same container)
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
);

CREATE TABLE order_payments (
    id SERIAL PRIMARY KEY,
    order_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
);
```

### 2. API Endpoints (FastAPI)
We design endpoints around the container, not just individual tables:
```python
from fastapi import APIRouter
from pydantic import BaseModel

# Models for the Order container
class OrderItem(BaseModel):
    order_id: int
    product_id: int
    quantity: int
    price: float

class OrderPayment(BaseModel):
    order_id: int
    amount: float
    status: str

# Router for the Order container
order_router = APIRouter(prefix="/orders", tags=["orders"])

@order_router.get("/{order_id}/items")
def get_order_items(order_id: int):
    return db.fetchall("SELECT * FROM order_items WHERE order_id = ?", (order_id,))

@order_router.post("")
def create_order(order_data: dict):
    # Start transaction for container consistency
    with db.transaction():
        # Create order
        db.execute(
            "INSERT INTO orders (user_id, total) VALUES (?, ?)",
            (order_data["user_id"], order_data["total"])
        )
        order_id = db.lastrowid

        # Create items
        for item in order_data["items"]:
            db.execute(
                "INSERT INTO order_items VALUES (?, ?, ?, ?, ?)",
                (None, order_id, item["product_id"], item["quantity"], item["price"])
            )

        return {"order_id": order_id}
```

### 3. Business Logic
Keep logic *within the container* (e.g., validate order totals):
```python
@order_router.post("/{order_id}/payments")
def process_payment(order_id: int, payment_data: dict):
    # Fetch current order total for validation
    order = db.fetchone("SELECT total FROM orders WHERE id = ?", (order_id,))
    if order["total"] != payment_data["amount"]:
        raise HTTPException(status_code=400, detail="Amount mismatch")

    with db.transaction():
        db.execute(
            "INSERT INTO order_payments VALUES (?, ?, ?)",
            (None, order_id, payment_data["amount"], "completed")
        )
        db.execute(
            "UPDATE orders SET status = 'paid' WHERE id = ?",
            (order_id,)
        )
    return {"message": "Payment processed"}
```

---

## Implementation Guide

### Step 1: Identify “Containers”
Ask yourself:
- What is the *business domain*? (e.g., Orders, Users, Inventory)
- Which tables are *indivisible*? (e.g., orders + order_items)
- What *invariants* must be enforced? (e.g., total = sum(items))

| Container   | Tables                | Example API Endpoint         |
|-------------|----------------------|------------------------------|
| Orders      | orders, order_items, payments | `/orders/{id}/items`          |
| Products    | products, inventory  | `/products/{id}/stock`       |
| Users       | users, wishlists     | `/users/{id}/wishlists`      |

### Step 2: Design the Schema
- **Root table**: The "parent" of the container. (e.g., `orders` is the root for order container).
- **Child tables**: Use foreign keys with `ON DELETE CASCADE` for integrity.
- **Avoid "flat" tables**: Tables like `user_products` should only exist if they represent a *unique* business concept.

### Step 3: Enforce Consistency
- Use **database constraints** (e.g., `CHECK` for total validation).
- **Atomic operations**: Wrap container changes in transactions.
- **Stored procedures** for complex logic (e.g., updating inventory + orders).

### Step 4: API Design
- **Prefix endpoints**: `/orders/{id}/items` (avoid mixing unrelated resources).
- **Hierarchical data**: Return nested JSON (e.g., orders with items included).
```json
// Example response for /orders/1
{
  "id": 1,
  "items": [
    {"product_id": 101, "quantity": 2},
    {"product_id": 102, "quantity": 1}
  ]
}
```

---

## Common Mistakes to Avoid

### ❌ **Overusing Containers**
**Problem**: Creating too many containers (e.g., a `User` container and a `UserOrders` container). This violates the single-responsibility principle.

**Fix**: Group tables only if they’re *indivisible* (e.g., orders and items are inseparable, but users and wishlists could be separate).

### ❌ **Deep Nesting in APIs**
**Problem**: Returning overly nested JSON:
```json
{
  "user": {
    "id": 1,
    "name": "Alice",
    "orders": [
      {
        "items": [
          {"product": {...}} // Too many levels!
        ]
      }
    ]
  }
}
```
**Fix**: Use **projection** (e.g., `/users/{id}` only returns user data; `/orders/{id}` returns order data).

### ❌ **Ignoring Performance**
**Problem**: Joining every table for a single container (e.g., fetching `user`, `orders`, `products` in one query).
**Fix**:
- Use **read models** (e.g., a `user_orders` view).
- **Lazy load** child data (e.g., only fetch items when requested).

### ❌ **Not Enforcing Transactions**
**Problem**: Partial updates (e.g., creating an order, but failing to add items).
**Fix**: Always wrap container operations in transactions.

---

## Key Takeaways

- **Containers = Business Domains**: Group tables by *what they solve*, not just *how they relate*.
- **APIs Follow Containers**: Design endpoints around containers, not tables.
- **Atomicity Matters**: Use transactions to keep containers consistent.
- **Avoid Overfitting**: Don’t create containers for every possible query (e.g., a `UserOrdersProducts` container).
- **Tradeoff**: Containers improve design but may add complexity for simple cases. Use them *when it matters*.

---

## When to Use Containers Pattern

✅ **Good Fit**:
- Complex domains where data integrity is critical (e.g., financial systems, e-commerce).
- APIs with many related tables (e.g., orders + items + payments).

❌ **Avoid When**:
- Your data is *flat* (e.g., a blog with `posts` and `comments` only).
- Containers add unnecessary complexity (e.g., a small app with 2 tables).

---

## Conclusion

The Containers Pattern isn’t about forcing every system into monolithic schemas—it’s about **intentional design**. By treating related tables as cohesive units, you:
- Reduce accidental coupling between features.
- Enforce business logic in the database (where it belongs).
- Design APIs that match real-world interactions.

**Start small**: Apply this pattern to one container (e.g., orders) and refactor incrementally. You’ll quickly see how much cleaner your database and API become.

---
**Further Reading**:
- [Database Perils of Not Using Transactions](https://www.cockroachlabs.com/blog/databases-perils-of-not-using-transactions/)
- [RESTful API Design Best Practices](https://restfulapi.net/)
- [FastAPI: Building APIs with Python](https://fastapi.tiangolo.com/)

**Try it yourself**: Grab a simple database schema and redesign it using containers. I’d love to see your examples!
```