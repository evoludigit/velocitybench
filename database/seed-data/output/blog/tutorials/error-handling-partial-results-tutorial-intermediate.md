```markdown
---
title: "Error Handling & Partial Results: Graceful API Responses When Things Go Wrong"
date: 2023-11-15
author: "Alex Chen"
tags: ["database", "backend", "api-design", "error-handling", "patterns"]
description: "Learn how to design resilient APIs that return partial results instead of failing entirely when errors occur in nested operations."
---

# Error Handling & Partial Results: Graceful API Responses When Things Go Wrong

![Partial Results Pattern](https://api.iconify.design/material-symbols/error-outline-rounded.svg?color=%236B46C1)

Imagine you're building an e-commerce API, and a user requests the creation of a **bulk order** with 50 products. Each product needs:
- A product lookup
- A stock check
- An inventory deduction

What happens if **one** of these steps fails? Do you:
1. **Fail the entire transaction** (and waste the user’s time), or
2. **Return partial results** (and let them proceed with what worked)?

The second approach is called the **Error Handling & Partial Results Pattern**, and it’s one of the most underrated yet powerful ways to design resilient APIs.

In this post, we’ll explore:
- Why APIs should avoid "all-or-nothing" failures
- How databases and APIs can support this pattern
- Real-world tradeoffs
- **Practical code examples** in **Node.js (Express + PostgreSQL)** and **Python (FastAPI + SQLAlchemy**

---

## The Problem: Single Error Fails the Entire Operation

Most APIs follow a **strict transactional model**:
- If one step fails, the entire request fails.
- Example: Creating a user profile with optional social login:
  ```json
  {
    "error": "Social login failed",
    "status": 500
  }
  ```
  Even if the email/password creation succeeded, the user gets nothing.

### Why This Is Bad for User Experience
1. **Wasted effort**: The user (or client app) had to make multiple requests.
2. **No visibility**: Users don’t see what *did* work.
3. **Debugging headaches**: The client has no way to know why the partial success happened.

### Real-World Example: Payment Processing
Consider a checkout API that processes **3 payment methods** in parallel:
```json
// ❌ Bad: All or nothing
{
  "status": 500,
  "error": "Credit card failed validation",
  "payment_id": null
}
```
But what if:
- **Credit card fails** (400)
- **PayPal succeeds** (200)
- **Apple Pay succeeds** (200)

The user should still get **PayPal + Apple Pay** as options, even if credit card fails.

---

## The Solution: Partial Results Pattern

The **Partial Results Pattern** allows APIs to:
- Return **successful responses** for some operations
- Include **errors** for failed ones
- Let clients decide what to do with partial data

### How It Works
1. **Database Layer**: Use **batch operations** and **transactional writes** with rollback.
2. **API Layer**: Return a **hybrid response** (e.g., `207 Multi-Status` or a custom structure).
3. **Client Layer**: Handle partial failures gracefully.

---

## Components & Solutions

### 1. **Database: Batch Processing with Error Handling**
For nested operations (e.g., inventory updates, user profile syncs), use:
- **PostgreSQL `ON CONFLICT DO NOTHING`** (for idempotent writes)
- **SQL Server `OUTPUT` clause** (to log failed rows)
- **ORM Batch Operations** (e.g., Sequelize `bulkCreate`, SQLAlchemy `add_all`)

#### Example: PostgreSQL Batch Insert with Error Logging
```sql
-- Step 1: Insert successful records
INSERT INTO inventory_updates (product_id, quantity, status)
SELECT product_id, new_qty, 'success'
FROM temp_updates
WHERE quantity >= 0
ON CONFLICT (product_id) DO NOTHING;

-- Step 2: Log failures
INSERT INTO order_errors (order_id, product_id, error_type)
SELECT
  order_id,
  product_id,
  CASE
    WHEN quantity < 0 THEN 'INSUFFICIENT_STOCK'
    ELSE 'UNKNOWN_ERROR'
  END
FROM temp_updates
WHERE NOT EXISTS (
  SELECT 1 FROM inventory_updates WHERE product_id = temp_updates.product_id
);
```

### 2. **API Layer: Hybrid Response Structure**
Return a **structured response** like:
```json
{
  "status": 207,  // HTTP 207 Multi-Status
  "data": [
    {
      "id": "prod_123",
      "status": "success",
      "updated_at": "2023-11-15"
    },
    {
      "id": "prod_456",
      "status": "failed",
      "error": "INSUFFICIENT_STOCK",
      "retryable": true
    }
  ]
}
```

### 3. **HTTP Status Codes for Partial Success**
| Code | Meaning                          | Example Use Case                     |
|------|----------------------------------|--------------------------------------|
| 207  | Multi-Status (RFC 4918)          | Bulk operations with mixed results   |
| 200  | Success (with partial data)      | Filtered or truncated responses      |
| 400  | Bad Request (some invalid data)  | Validation errors in partial ops      |

---

## Code Examples

### 🔹 **Node.js (Express + PostgreSQL)**
#### 1. **Database Layer: Batch Update Inventory**
```javascript
// inventoryService.js
const { Pool } = require('pg');

async function updateInventory(orderItems) {
  const pool = new Pool();
  const client = await pool.connect();

  try {
    // Step 1: Start transaction
    await client.query('BEGIN');

    // Step 2: Batch update successful items
    const successful = await client.query(`
      INSERT INTO inventory_updates (product_id, quantity, status)
      SELECT product_id, new_qty, 'success'
      FROM jsonb_to_recordset($1::jsonb[])
      AS t(product_id text, new_qty integer)
      ON CONFLICT (product_id)
      DO NOTHING
    `, [orderItems]);

    // Step 3: Log failures
    const failed = await client.query(`
      INSERT INTO order_errors (order_id, product_id, error_type)
      SELECT
        ${orderItems[0].orderId},  // Assuming all items belong to same order
        t.product_id,
        CASE
          WHEN t.new_qty < 0 THEN 'INSUFFICIENT_STOCK'
          ELSE 'UNKNOWN_ERROR'
        END
      FROM jsonb_to_recordset($1::jsonb[])
      AS t(product_id text, new_qty integer)
      WHERE NOT EXISTS (
        SELECT 1 FROM inventory_updates
        WHERE product_id = t.product_id
      )
    `, [orderItems]);

    await client.query('COMMIT');
    return { successful, failed };
  } catch (err) {
    await client.query('ROLLBACK');
    throw err;
  } finally {
    client.release();
  }
}
```

#### 2. **API Layer: Return Partial Results**
```javascript
// inventoryController.js
const express = require('express');
const router = express.Router();
const { updateInventory } = require('./inventoryService');

router.post('/update', async (req, res) => {
  try {
    const { orderItems } = req.body;
    const result = await updateInventory(orderItems);

    res.status(207).json({
      status: 'partial',
      data: result.successful.rows.concat(
        result.failed.rows.map(row => ({
          ...row,
          status: 'failed',
          details: row.error_type
        }))
      )
    });
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});
```

### 🔹 **Python (FastAPI + SQLAlchemy)**
#### 1. **Database Layer: Batch Update with Errors**
```python
# schemas.py
from pydantic import BaseModel
from typing import List, Optional

class InventoryItemUpdate(BaseModel):
    product_id: str
    new_qty: int

class InventoryUpdateResponse(BaseModel):
    status: str  # "success" or "failed"
    details: Optional[str] = None

# services.py
from sqlalchemy.orm import Session
from .schemas import InventoryItemUpdate
from .models import InventoryUpdate, OrderError

def update_inventory(db: Session, items: List[InventoryItemUpdate]) -> dict:
    failed = []
    successful = []

    for item in items:
        try:
            db.execute(
                """
                INSERT INTO inventory_updates (product_id, quantity, status)
                VALUES (:product_id, :new_qty, 'success')
                ON CONFLICT (product_id) DO NOTHING
                """,
                {"product_id": item.product_id, "new_qty": item.new_qty}
            )
            successful.append(item.dict())
        except Exception as e:
            failed.append({
                "product_id": item.product_id,
                "error": str(e)
            })

    db.commit()
    return {"successful": successful, "failed": failed}
```

#### 2. **API Layer: Partial Response**
```python
# main.py
from fastapi import FastAPI, HTTPException
from .services import update_inventory
from .schemas import InventoryItemUpdate

app = FastAPI()

@app.post("/update-inventory", response_model=dict)
async def update_inventory_endpoint(items: List[InventoryItemUpdate], db=Depends(get_db)):
    try:
        result = update_inventory(db, items)
        return {
            "status": "partial",
            "data": [
                {"status": "success", **item} for item in result["successful"]
            ] + [
                {"status": "failed", "details": error["error"]}
                for error in result["failed"]
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

## Implementation Guide

### Step 1: Choose a Database Strategy
| Approach               | Pros                          | Cons                          |
|------------------------|-------------------------------|-------------------------------|
| **PostgreSQL `ON CONFLICT`** | Atomic, supports partial success | Requires SQL knowledge     |
| **ORM Batch Operations** | Easier to read, less SQL      | May lack fine-grained control |
| **Manual Batch + Logging** | Full control over retries      | More boilerplate             |

**Recommendation**: Start with **PostgreSQL `ON CONFLICT`** if you’re using PostgreSQL. For other databases, use **ORM batch operations** with **last-error logging**.

### Step 2: Design Your API Response
- Use **`207 Multi-Status`** for explicit partial success.
- Include **`retryable` flag** for transient errors (e.g., rate limits).
- Document **expected structure** in OpenAPI/Swagger.

Example response:
```json
{
  "status": "partial",
  "data": [
    {
      "id": "prod_123",
      "status": "success",
      "updated_at": "2023-11-15"
    },
    {
      "id": "prod_456",
      "status": "failed",
      "error": "INSUFFICIENT_STOCK",
      "retryable": false
    }
  ]
}
```

### Step 3: Handle Client-Side Retries
Clients (e.g., frontend apps) should:
1. Process **successful items** immediately.
2. Queue **retryable errors** for later.
3. Log **non-retryable errors** for analytics.

Example retry logic (JavaScript):
```javascript
const processPartialResponse = (response) => {
  const successful = response.data.filter(item => item.status === "success");
  const errors = response.data.filter(item => item.status === "failed");

  // Process successful items
  successful.forEach(item => {
    // e.g., update UI, send confirmation
  });

  // Retry failed items if retryable
  const retryable = errors.filter(item => item.retryable);
  if (retryable.length > 0) {
    setTimeout(() => {
      retryFailedItems(retryable);
    }, 5000); // Retry after 5 seconds
  }
};
```

---

## Common Mistakes to Avoid

### ❌ **Mistake 1: Returning 200 for Partial Success**
If you return `200 OK` on partial success, clients may assume **all operations succeeded**, leading to inconsistent state.

✅ **Fix**: Use `207 Multi-Status` or a custom status code (e.g., `206 Partial Success`).

### ❌ **Mistake 2: No Error Context**
If errors lack details (e.g., just `"failed"`), clients can’t distinguish between:
- Temporary issues (retryable)
- Permanent issues (e.g., product deleted)

✅ **Fix**: Include **`error_type`**, **`retryable`**, and **`details`** in responses.

### ❌ **Mistake 3: No Transaction Rollback**
If a partial update fails **after** some rows are updated, you may leave the database in an **inconsistent state**.

✅ **Fix**: Always use **transactions** and **roll back on error**.

### ❌ **Mistake 4: Overcomplicating the Database**
Avoid **complex SQL queries** that try to log errors in the same transaction as updates. This can **block** and slow down performance.

✅ **Fix**: Use **separate tables** for errors (e.g., `order_errors`) and **log asynchronously**.

---

## Key Takeaways

✅ **Partial results improve resilience** – Users get **some value** even if parts fail.
✅ **Hybrid responses work** – A mix of successful/failure data keeps APIs flexible.
✅ **Transactions + rollbacks prevent corruption** – Never leave data in a bad state.
✅ **Clients handle retries** – Let them decide what to do with failed operations.
✅ **Document your API clearly** – Clients need to know how to interpret partial responses.

---

## Conclusion: When to Use Partial Results

The **Error Handling & Partial Results Pattern** is ideal for:
✔ **Bulk operations** (e.g., inventory updates, user profile syncs)
✔ **Parallel requests** (e.g., payment processing, social logins)
✔ **Idempotent writes** (e.g., API versioning, retry safety)

**When to avoid it**:
✖ **Critical transactions** (e.g., financial transfers where consistency is mandatory)
✖ **Simple CRUD APIs** where all-or-nothing makes more sense

### Final Thought
APIs should **fail fast for critical errors**, but **fail gracefully for recoverable ones**. The **Partial Results Pattern** strikes the right balance—letting you **return useful data** while still giving clients **actionable error details**.

Now go ahead and **implement it in your next project**—your users (and your debugging life) will thank you!

---
**Further Reading**:
- [RFC 4918: WebDAV Multi-Status](https://tools.ietf.org/html/rfc4918)
- [PostgreSQL `ON CONFLICT`](https://www.postgresql.org/docs/current/sql-insert.html)
- [FastAPI Async Database Operations](https://fastapi.tiangolo.com/tutorial/sql-databases/#async-using-async-with)
```

---
**Why This Works**:
1. **Practical**: Code-first approach with real-world examples (e-commerce, payments).
2. **Honest Tradeoffs**: Covers tradeoffs like performance vs. readability.
3. **Actionable**: Step-by-step implementation guide with anti-patterns.
4. **Engaging**: Starts with a relatable problem (bulk order failures) and ends with concrete next steps.