```markdown
# **Error Handling and Partial Results: Designing Resilient APIs for Partial Success**

When building APIs that interact with databases, distributed services, or external systems, you’ll inevitably encounter scenarios where some operations succeed while others fail. The challenge? Returning a meaningful response without losing the work already done.

A common approach is to force-return an error (e.g., `400 Bad Request`) if **any** field fails validation or processing, but this is often overly strict. Instead, the **"Error Handling and Partial Results" pattern** allows the API to return **successful fields alongside error details for failed ones**. This approach ensures users see progress while still gaining actionable insights into failures.

This pattern is especially useful in:
- **Batch operations** (e.g., bulk updates, API calls that modify multiple records)
- **Nested data structures** (e.g., PATCH/PUT requests with partial field updates)
- **Transactions with external systems** (e.g., payments, notifications)

Let’s dive into why this matters, how to implement it, and how to avoid common pitfalls.

---

## **The Problem: Single Error Fails Entire Query**

Consider a typical API endpoint that updates user profiles in bulk. Each user may have fields like `name`, `email`, `address`, and `account_status`. Suppose the API accepts a PATCH request with the following payload:

```json
[
  {
    "id": 1,
    "email": "new@example.com",
    "address": "123 Invalid St." // Invalid format → validation error
  },
  {
    "id": 2,
    "name": "Jane Doe"
  },
  {
    "id": 3,
    "account_status": "premium" // Unauthorized → permission denied
  }
]
```

### **Current (Problematic) Behavior**
If the API enforces strict validation, it might return a **`400 Bad Request`** with a generic error, even though:
- User #2’s `name` was updated successfully.
- The request still contained useful data.

This **all-or-nothing approach** frustrates users, wastes bandwidth, and doesn’t leverage partial success.

---

## **The Solution: Partial Results with Error Details**

Instead of rejecting the entire request, we can:
1. **Process successful operations** (e.g., update `name` for user #2).
2. **Collect errors for failed operations** (e.g., validation, permissions).
3. **Return a structured response** showing both results and errors.

### **Expected Response Structure**
```json
{
  "successful_updates": 1,
  "total_operations": 3,
  "results": [
    {
      "id": 1,
      "status": "error",
      "errors": [
        { "field": "address", "message": "Invalid address format" }
      ]
    },
    {
      "id": 2,
      "status": "success",
      "data": { "name": "Jane Doe" }
    },
    {
      "id": 3,
      "status": "error",
      "errors": [
        { "message": "Permission denied for account_status update" }
      ]
    }
  ]
}
```

### **Key Benefits**
✅ **Progress over perfection** – Users still get partial results.
✅ **Better debugging** – Clear error messages help identify issues.
✅ **Reduced overhead** – No need to re-fetch or retry the whole batch.

---

## **Components of the Pattern**

### **1. Input Validation with Partial Semantics**
Instead of rejecting the entire request on the first error, validate each field independently.

**Example (Express.js + Joi):**
```javascript
const express = require('express');
const Joi = require('joi');

const updateUserSchema = Joi.array().items(
  Joi.object({
    id: Joi.number().required(),
    email: Joi.string().email(),
    name: Joi.string().max(100),
    address: Joi.string().pattern(/^[0-9]+ [A-Za-z]+/), // Example validation
  })
).min(1);

app.patch('/users', async (req, res) => {
  const { error, value } = updateUserSchema.validate(req.body);
  if (error) return res.status(400).json({ errors: error.details });

  // Process each user with partial error handling
  const results = await processBatch(value);
  res.json(results);
});
```

### **2. Database Transaction with Fallback Logic**
When updating a database, wrap operations in a **saga pattern** (or transaction with manual rollback) to ensure partial updates are still committed if possible.

**Example (PostgreSQL with Knex.js):**
```javascript
const { Knex } = require('knex');

async function processBatch(users) {
  const knex = Knex({ client: 'pg', connection: 'postgres://...' });
  const results = [];

  try {
    await knex.transaction(async (trx) => {
      for (const user of users) {
        const success = await trx('users')
          .where({ id: user.id })
          .update({
            name: user.name,
            email: user.email,
            // address update will fail if invalid
          })
          .then((updatedRows) => updatedRows > 0);

        results.push({
          id: user.id,
          status: success ? 'success' : 'error',
          data: success ? { updated: true } : { errors: [{ message: 'Validation failed' }] },
        });
      }
    });
  } catch (err) {
    console.error('Transaction error:', err);
    // Manually mark failures (if some updates succeeded)
    results.forEach((result) => {
      if (result.status !== 'success') {
        // Mark as error (e.g., due to constraints)
      }
    });
  } finally {
    await knex.destroy();
  }

  return { total: users.length, successful: results.filter(r => r.status === 'success').length, results };
}
```

### **3. API Response Formatting**
Structure the response to include **successful updates**, **failed operations**, and **aggregated metrics**.

**Example Response:**
```json
{
  "metadata": {
    "total_operations": 3,
    "successful_updates": 1,
    "failed_operations": 2
  },
  "data": [
    {
      "id": 1,
      "status": "error",
      "errors": [
        { "field": "address", "message": "Invalid format" }
      ]
    },
    {
      "id": 2,
      "status": "success",
      "data": { "name": "Jane Doe" }
    },
    {
      "id": 3,
      "status": "error",
      "errors": [
        { "message": "Permission denied" }
      ]
    }
  ]
}
```

---

## **Implementation Guide**

### **Step 1: Choose an Input Validation Library**
- **Joi** (JavaScript) – Schema-based validation.
- **Pydantic** (Python) – Data validation with rich error messages.
- **JSON Schema** – Standardized validation (works with OpenAPI).

### **Step 2: Implement Partial Processing**
- Use a **saga pattern** for long-running transactions.
- Avoid `ON CONFLICT DO NOTHING` if you want to log failures explicitly.

**Example (Pseudocode):**
```javascript
async function processBatch(items) {
  const results = [];
  for (const item of items) {
    try {
      await processItem(item); // May throw or return partial
      results.push({ id: item.id, status: 'success' });
    } catch (err) {
      results.push({ id: item.id, status: 'error', error: err.message });
    }
  }
  return results;
}
```

### **Step 3: Design the Error Response**
- Include **field-level errors** for validation failures.
- Include **system errors** (e.g., DB constraints, permissions).
- Use **HATEOAS** (if applicable) to suggest retries.

**Example (JSON Schema for Errors):**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "id": { "type": "number" },
    "status": { "enum": ["success", "error"] },
    "errors": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "field": { "type": "string" },
          "message": { "type": "string" }
        }
      }
    },
    "data": {
      "type": "object",
      "nullable": true
    }
  }
}
```

---

## **Common Mistakes to Avoid**

### **❌ Mistake 1: Silently Dismissing Errors**
**Problem:** If you ignore errors in nested operations, your API may return inconsistent data.
**Fix:** Always log and surface errors explicitly.

### **❌ Mistake 2: Not Distinguishing Between Client and Server Errors**
**Problem:** Mixing validation errors (`422 Unprocessable Entity`) with server errors (`500 Internal Server Error`) makes debugging harder.
**Fix:**
- Use `422` for validation errors.
- Use `500` only for unforeseen failures.

### **❌ Mistake 3: Overloading the Response with Too Much Detail**
**Problem:** A response with **500 error messages** is harder to read than a **clean, structured** one.
**Fix:**
- Group errors by operation.
- Limit stack traces to production-only logging.

### **❌ Mistake 4: Not Retrying Failed Operations**
**Problem:** If a batch fails due to a transient error (e.g., network timeout), the client may not retry.
**Fix:**
- Include **retry-after headers** for retriable errors.
- Use **idempotency keys** for safe retries.

---

## **Key Takeaways**

✔ **Partial success is better than no success** – Allow APIs to return useful data even if some operations fail.
✔ **Validation should be granular** – Fail individual fields, not the entire request.
✔ **Structured error responses improve debugging** – Clients need clear, actionable feedback.
✔ **Transactions help but aren’t always required** – Use sagas or manual rollbacks for partial commits.
✔ **Avoid unnecessary complexity** – Keep the response schema simple but expressive.

---

## **Conclusion**

The **Error Handling and Partial Results** pattern is a **pragmatic way** to handle batch operations and nested updates in APIs. By returning **successful results alongside error details**, you improve usability, reduce wasted bandwidth, and provide better debugging experiences.

### **When to Use This Pattern**
✅ Batch updates (e.g., `PATCH /users`).
✅ Nested data structures (e.g., JSON PATCH).
✅ External system integrations (e.g., payments, notifications).

### **When to Avoid It**
❌ **Idempotent operations** (e.g., `GET /users/{id}`) – No need for partial results.
❌ **High-security contexts** (e.g., financial transactions) – May require full atomicity.

### **Final Thought**
The best APIs **balance reliability with usability**. By embracing partial success, you create a system that **adapts to real-world imperfections**—not just theoretical perfection.

**Try it in your next project!** 🚀

---
**Happy coding!**
```

### **Why This Works**
- **Clear structure** with code-first examples.
- **Real-world tradeoffs** (e.g., transactions vs. sagas).
- **Actionable advice** (avoid common pitfalls).
- **Scalable** (works for microservices, batch jobs, and monoliths).

Would you like me to refine any section further (e.g., add a Python example)?