```markdown
# **Availability Conventions: A Backend Developer’s Guide to Clean and Maintainable API Responses**

*How to design APIs that clients can trust—and debug—without constant hand-holding.*

---

## **Introduction: When Your API Becomes the World’s Most Confusing Documentation**

Imagine this: A user clicks "Submit Order," but instead of a simple success or failure, they get back a JSON blob with nested error objects, HTTP status codes, and what feels like a manual from a 1990s ERP system.

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Missing or invalid fields",
    "details": {
      "field_errors": [
        {
          "field": "shipping_address.city",
          "reason": "must match regex /^[a-z]+$/i"
        },
        {
          "field": "payment_method",
          "error_type": "validation",
          "additional_info": {
            "valid_methods": ["credit_card", "paypal", "bank_transfer"]
          }
        }
      ],
      "non_field_errors": [
        "Order total exceeds credit limit. Check your account."
      ]
    },
    "severity": "high",
    "suggested_action": "Review all fields and retry."
  }
}
```

Sound familiar? If your API responses are this complex, you’re likely missing something crucial: **availability conventions**. These are the unspoken rules that make your API responses predictable, debuggable, and client-friendly.

In this post, we’ll explore:
- Why inconsistent error responses make clients miserable (and how to avoid it).
- How real-world APIs (like GitHub, Stripe, and Shopify) handle availability.
- A practical framework for designing your own conventions.
- Common pitfalls and how to sidestep them.

---

## **The Problem: Chaos Without Availability Conventions**

When APIs lack consistent availability conventions, they become:
1. **Inconsistent** – Success responses might return different fields depending on the endpoint.
   ```json
   # API 1: Success response
   {"status": "completed", "id": "123"}

   # API 2: Success response
   {"data": {"order": {"id": "123", "amount": 99.99}}}
   ```
2. **Overly verbose** – Clients wade through noise to find the signal.
   ```json
   {
     "result": {
       "user": { "id": 1, "name": "Alice" },
       "status": "found"
     },
     "debug_info": {
       "query_time": 42,
       "database_version": "PostgreSQL 14.2"
     }
   }
   ```
3. **Undebuggable** – Errors lack structure, making it hard to automate fixes.
   ```json
   # Endpoint 1
   {"error": "Something went wrong."}

   # Endpoint 2
   {"status": 400, "message": "Invalid payload"}
   ```

4. **Hard to document** – Devs spend more time explaining *why* the response looks this way than *what* it means.

---

## **The Solution: Availability Conventions**

Availability conventions are **design patterns** for API responses that ensure:
- **Predictability**: Clients know exactly what to expect.
- **Debuggability**: Errors and warnings are structured and actionable.
- **Flexibility**: The schema can evolve without breaking clients.

A well-designed convention answers these questions for every response:
1. **What’s the status?** (Success, error, warning?)
2. **What’s the payload?** (Success data, error details, or partial success?)
3. **How should I handle this?** (Retry? Log it? Show a toast?)

---

## **Components of Availability Conventions**

### **1. Standardized Status Codes (Beyond HTTP Alone)**
HTTP status codes are great, but they’re limited. Add a **response status field** to clarify intent:

```json
{
  "status": "success",  // or "partial_success", "error", "warning"
  "data": { ... }
}
```

**Example APIs using this pattern:**
- **GitHub API**: Uses `status: "ok"` or `status: "error"` with details.
- **Stripe API**: Returns `object` (success) or `error` (failure) as the root key.

---

### **2. Error Structuring: The "Error Object" Pattern**
Errors should include:
- A **human-readable message** (for users/clients).
- A **technical code** (for automation).
- **Details** (fields with validation errors, missing data, etc.).

```json
{
  "status": "error",
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Invalid email or password.",
    "details": {
      "field_errors": {
        "email": ["Must be a valid email."],
        "password": ["Too short (minimum 8 characters)."]
      }
    }
  }
}
```

**Pro Tip:** Use **RFC 7807 Problem Details** for a standardized format:
```json
{
  "type": "https://api.example.com/errors/invalid-credentials",
  "title": "Unauthorized",
  "status": 401,
  "detail": "Invalid email or password.",
  "instance": "/login",
  "errors": {
    "email": ["Must be a valid email."]
  }
}
```

---

### **3. Success Responses: The "Data-Only" Approach**
Success responses should focus on **only the data**, not metadata:
```json
{
  "status": "success",
  "data": {
    "user": {
      "id": 123,
      "name": "Alice",
      "email": "alice@example.com",
      "created_at": "2023-01-01T00:00:00Z"
    }
  }
}
```

**When to include metadata?**
Only if it’s **essential** for the client (e.g., pagination links, API version).

---

### **4. Partial Success: The "Errors-With-Some-Data" Pattern**
Some endpoints succeed partially (e.g., creating a user but failing to set an address). Include both **data** and **errors**:

```json
{
  "status": "partial_success",
  "data": {
    "user": {
      "id": 456,
      "name": "Bob",
      "email": null  // Error: Couldn't set email due to validation.
    }
  },
  "errors": {
    "address": [
      { "field": "zipcode", "message": "Invalid format." }
    ]
  }
}
```

---

### **5. Retryable vs. Non-Retryable Errors**
Add a **retryable** flag to help clients automate retries:
```json
{
  "status": "error",
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests.",
    "retryable": true,
    "retry_after": 300  // 5 minutes in seconds
  }
}
```

---

### **6. Warning Responses**
Not all issues are errors. **Warnings** are non-critical but worth acknowledging:
```json
{
  "status": "warning",
  "warnings": [
    {
      "code": "DEPRECATION",
      "message": "Field 'old_field' is deprecated. Use 'new_field' instead."
    }
  ],
  "data": { ... }
}
```

---

## **Code Examples: Implementing Availability Conventions**

### **Example 1: Success Response (REST API)**
```python
# FastAPI (Python) example
from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.post("/users/", response_model=dict)
async def create_user(user: dict):
    # Simulate successful creation
    user_id = 123
    return {
        "status": "success",
        "data": {
            "user": {
                "id": user_id,
                "name": user["name"],
                "email": user["email"]
            }
        }
    }
```

---

### **Example 2: Error Response (with RFC 7807)**
```python
# FastAPI with Problem Details
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class ErrorDetails(BaseModel):
    type: str
    title: str
    status: int
    detail: str
    errors: dict = {}

@app.post("/login/")
async def login(email: str, password: str):
    if not email:
        raise HTTPException(
            status_code=400,
            detail=ErrorDetails(
                type="https://api.example.com/errors/missing-field",
                title="Invalid input",
                status=400,
                detail="Email is required.",
                errors={"email": ["This field is required."]}
            ).dict()
        )
    return {"status": "success", "data": {"user": {"id": 1}}}
```

---

### **Example 3: Partial Success (Node.js/Express)**
```javascript
// Express.js example
const express = require('express');
const app = express();

app.post('/orders/', express.json(), (req, res) => {
    const { items, shipping_address } = req.body;

    const createdOrder = {
        id: 'ord_123',
        items: items.map(item => ({ name: item.name, quantity: item.quantity })),
        shipping_address: {}  // Simulate partial failure
    };

    const errors = [];
    if (!shipping_address?.zipcode) {
        errors.push({
            field: 'shipping_address.zipcode',
            message: 'Zipcode is required.'
        });
    }

    if (errors.length > 0) {
        return res.status(207).json({
            status: 'partial_success',
            data: { order: createdOrder },
            errors
        });
    }

    res.json({ status: 'success', data: { order: createdOrder } });
});
```

---

### **Example 4: Client-Side Validation (Frontend)**
```javascript
// Fetch API with error handling
const handleResponse = async (response) => {
    if (response.status === 200) {
        const data = await response.json();
        if (data.status === 'success') {
            console.log("Success:", data.data);
        } else if (data.status === 'error') {
            throw new Error(data.error.message);
        } else if (data.status === 'warning') {
            console.warn("Warning:", data.warnings);
        }
    } else {
        const errorData = await response.json();
        throw new Error(`API error: ${errorData.error?.message ?? 'Unknown error'}`);
    }
};

// Usage
fetch('/api/users/', { method: 'POST', body: JSON.stringify({ name: '' }) })
    .then(handleResponse)
    .catch(err => console.error("Failed:", err.message));
```

---

## **Implementation Guide: Rollout Your Conventions**

### **Step 1: Define Your Standards**
Start with a **design document** answering:
- What’s the root key for status? (`"status"`, `"meta"`, or no key?)
- How will errors be structured? (Flat object vs. nested?)
- Should partial success be a separate status code?

**Example Standards Table:**
| Scenario          | Root Key       | Structure Example                          |
|-------------------|----------------|-------------------------------------------|
| Success           | `status`       | `{ status: "success", data: {...} }`      |
| Error             | `error`        | `{ status: "error", error: {...} }`       |
| Partial Success   | `status`       | `{ status: "partial_success", data: {...}, errors: [...] }` |

---

### **Step 2: Update Existing APIs Gradually**
1. **Add conventions to new endpoints** first.
2. **Deprecate old responses** with warnings (e.g., HTTP 426 for new clients only).
3. **Use feature flags** to enable conventions incrementally.

**Example Deprecation Warning:**
```json
{
  "status": "warning",
  "warnings": [
    {
      "code": "RESPONSE_FORMAT_CHANGE",
      "message": "This response format will be deprecated in 6 months. Use the new format with 'status' field."
    }
  ],
  "legacy_response": {...}  // Old format for backward compatibility
}
```

---

### **Step 3: Document Everything**
- **API docs**: Show examples of success/error/partial responses.
- **Client libraries**: Update SDKs to handle conventions automatically.
- **Internal wiki**: Explain why you chose your conventions.

**Example API Doc Snippet:**
```markdown
# POST /orders/
Creates a new order.

**Success Response:**
```json
{
  "status": "success",
  "data": {
    "order": {
      "id": "ord_456",
      "items": [...],
      "status": "pending"
    }
  }
}
```

**Error Response (Invalid Payment):**
```json
{
  "status": "error",
  "error": {
    "code": "PAYMENT_FAILED",
    "message": "Payment processing failed.",
    "retryable": true,
    "retry_after": 60
  }
}
```

---

### **Step 4: Enforce via Validation**
Use tools to catch violations:
- **OpenAPI/Swagger**: Define response schemas.
- **Postman/Newman**: Automated tests for response consistency.
- **Linters**: Regex checks for error formats in logs.

**Example OpenAPI Response Definition:**
```yaml
responses:
  200:
    description: Success
    content:
      application/json:
        schema:
          type: object
          properties:
            status:
              type: string
              enum: ["success"]
            data:
              type: object
  400:
    description: Bad Request
    content:
      application/json:
        schema:
          type: object
          properties:
            status:
              type: string
              enum: ["error"]
            error:
              $ref: '#/components/schemas/ErrorObject'
```

---

## **Common Mistakes to Avoid**

### **1. Overcomplicating Success Responses**
**Bad:**
```json
{
  "status": "success",
  "meta": {
    "request_id": "req_123",
    "duration_ms": 42,
    "database_version": "PostgreSQL 14.2"
  },
  "data": { ... }
}
```
**Why?** Metadata bloat clutters responses. Only include what clients **need**.

---

### **2. Inconsistent Error Codes**
**Bad:**
```json
// Error 1
{"error": "Invalid email."}

// Error 2
{"status": 400, "message": "Missing field 'name'."}
```
**Fix:** Stick to one error structure (e.g., always include `code`, `message`, and `details`).

---

### **3. Ignoring Partial Success**
**Bad:** Treat partial failures as all-or-nothing.
**Fix:** Let clients handle partial data gracefully:
```json
// Good: Partial success with errors
{
  "status": "partial_success",
  "data": { "user": { "id": 1 } },
  "errors": [ { "field": "address", "message": "Invalid city." } ]
}
```

---

### **4. Not Documenting Conventions**
**Bad:** Assume clients know how to parse responses.
**Fix:** Document **why** you chose your structure (e.g., "We use `retry_after` in seconds for consistency with AWS").

---

### **5. Changing Conventions Without Warning**
**Bad:** Sudden format shifts break clients.
**Fix:** Use **deprecation headers** or **versioned endpoints** (e.g., `/v1/users`, `/v2/users`).

---

## **Key Takeaways**

✅ **Predictability > Verbosity**: Clients should know what to expect upfront.
✅ **Standardize Errors**: Use a consistent structure (e.g., `code`, `message`, `details`).
✅ **Handle Partial Success**: Not all failures are total failures.
✅ **Document Everything**: Conventions are useless if no one knows they exist.
✅ **Iterate Gradually**: Roll out changes carefully to avoid breaking clients.
✅ **Leverage RFC 7807**: For a battle-tested error format.

---

## **Conclusion: Your API Should Be Intuitive, Not Puzzling**

Availability conventions turn your API from a "black box" into a **reliable partner**. By following patterns like standardized status fields, structured errors, and partial success handling, you:
- Reduce client-side debugging headaches.
- Make your API easier to document.
- Future-proof against changes.

Start small—pick one endpoint, define a convention, and iterate. Over time, your entire API will become **cleaner, more maintainable, and delightfully predictable**.

Now go forth and design APIs that clients will **love**, not tolerate.

---
**Further Reading:**
- [RFC 7807: Problem Details for HTTP APIs](https://tools.ietf.org/html/rfc7807)
- [GitHub API Error Handling](https://docs.github.com/en/rest/overview/api-responses#error-response-structure)
- [Stripe API Reference](https://stripe.com/docs/api)
```

---
**Why This Works:**
- **Code-first**: Examples in Python, Node.js, and OpenAPI show real-world application.
- **Tradeoffs upfront**: Discusses balancing standardization with flexibility.
- **Actionable**: Step-by-step implementation guide avoids theory.
- **Beginner-friendly**: Avoids jargon (e.g., "RFC 7807" is explained in context).