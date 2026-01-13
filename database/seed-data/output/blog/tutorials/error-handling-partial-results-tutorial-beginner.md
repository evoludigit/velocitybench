```markdown
# **Error Handling & Partial Results: Building Resilient APIs That Never Crash**

When building APIs, one of the biggest frustrations is seeing a **500 error** every time a user enters invalid data—or worse, a partial update that silently fails. What if we could **gracefully handle errors while still delivering useful data**?

This is where the **Partial Results Pattern** shines. Instead of failing an entire request on a single error, APIs return **partial success**—showing what worked while highlighting where things went wrong.

Let’s break down **why this matters**, **how it works**, and **how to implement it** in code.

---

## **The Problem: Single Error Fails the Entire Request**

Imagine a user updating their **User Profile** with three fields:
- `name` (valid)
- `email` (valid)
- `age` (invalid, e.g., `"twenty"` instead of a number)

A traditional API would either:
1. **Fail entirely** (HTTP 400/500, no updates applied).
2. **Silently ignore errors** (update `name` and `email` but hide the `age` failure).

Both approaches are **bad user experience**:
- **No feedback** → Users don’t know what went wrong.
- **Unpredictable state** → Database inconsistency.

```json
// Traditional API (all-or-nothing)
{
  "success": false,
  "error": "age must be a number",
  "updatedFields": []
}
```

**This approach is rigid and frustrating.**

---

## **The Solution: Partial Results Pattern**

Instead of rejecting the **entire request**, we:
1. **Process all valid fields** (e.g., update `name` and `email`).
2. **Return errors only for invalid fields** (e.g., `age` is invalid).
3. **Let the client decide** how to handle partial success.

```json
// Partial Results Response
{
  "success": true,
  "updatedFields": ["name", "email"],
  "errors": [
    { "field": "age", "message": "age must be a number" }
  ]
}
```

This approach:
✅ **Keeps the API alive** (no 500 errors).
✅ **Provides actionable feedback** (users know what failed).
✅ **Maintains data consistency** (no partial updates).

---

## **How It Works: Components of the Pattern**

### **1. API Contract (Response Structure)**
The API should return:
- **Valid updates** (what worked).
- **Errors** (what failed).
- **Status** (`success: true` indicates partial success).

### **2. Backend Processing Logic**
- **Batch processing** (handle multiple fields in one request).
- **Error isolation** (fail only the problematic fields).
- **Transaction rollback** (if needed, revert changes if critical).

### **3. Client-Side Handling**
- **Show partial success** (e.g., "Updated successfully, but fix your age").
- **Retry failed fields** (allow users to fix errors before submitting again).

---

## **Implementation Guide: Code Examples**

We’ll implement this in **Node.js + Express + PostgreSQL**, but the pattern applies to any backend (Python, Java, Go, etc.).

### **Step 1: Define the API Endpoint**
```javascript
const express = require('express');
const router = express.Router();
const { Pool } = require('pg');

// Connect to PostgreSQL
const pool = new Pool({ connectionString: 'postgres://user:pass@localhost/db' });

router.put('/user-profile', async (req, res) => {
  const { name, email, age } = req.body;

  try {
    // 1. Validate input (basic client-side check)
    if (!validateInput(name, email, age)) {
      return res.status(400).json({ success: false, errors: validationErrors });
    }

    // 2. Process valid fields
    const results = await pool.query(`
      UPDATE users
      SET name = $1, email = $2
      WHERE id = $3 RETURNING *;
    `, [name, email, req.userId]);

    // 3. Check for age validation (server-side)
    if (age && isNaN(age)) {
      return res.json({
        success: true,
        updatedFields: ['name', 'email'],
        errors: [{ field: 'age', message: 'age must be a number' }]
      });
    }

    // 4. If all valid, return full success
    res.json({ success: true, message: 'Profile updated successfully' });

  } catch (error) {
    console.error(error);
    res.status(500).json({ success: false, error: 'Internal server error' });
  }
});

function validateInput(name, email, age) {
  // Basic validation (expand as needed)
  if (!name || !email) return false;
  // ... more checks
}
```

### **Step 2: Handle Partial Updates with Transactions**
If multiple updates fail, use a **transaction** to ensure consistency:

```javascript
router.put('/multi-field-update', async (req, res) => {
  const { address, phone, bio } = req.body;

  try {
    await pool.query('BEGIN');

    // Try updating each field (fail independently)
    const addressResult = await pool.query(`
      UPDATE users SET address = $1 WHERE id = $2
    `, [address, req.userId]);

    const phoneResult = await pool.query(`
      UPDATE users SET phone = $1 WHERE id = $2
    `, [phone, req.userId]);

    // Collect errors (e.g., if phone is invalid)
    const errors = [];
    if (phone && !isValidPhone(phone)) {
      errors.push({ field: 'phone', message: 'Invalid phone number' });
    }

    // Commit or rollback
    if (errors.length === 0) {
      await pool.query('COMMIT');
      res.json({ success: true });
    } else {
      await pool.query('ROLLBACK');
      res.json({
        success: true,
        updatedFields: ['address'],
        errors
      });
    }

  } catch (error) {
    await pool.query('ROLLBACK');
    res.status(500).json({ success: false, error: 'Update failed' });
  }
});
```

### **Step 3: Client-Side Display (React Example)**
```jsx
function handleProfileUpdate(updatedFields, errors) {
  if (!updatedFields.length && errors.length) {
    return alert("Please fix the following errors:");
  }

  const successMsg = `Updated: ${updatedFields.join(', ')}`;
  const errorList = errors.map(e => `- ${e.field}: ${e.message}`).join('\n');

  alert(`${successMsg}\n\nErrors:\n${errorList}`);
}
```

---

## **Common Mistakes to Avoid**

### **1. Treating Partial Success as Full Success**
❌ **Bad:** Return `success: true` even if some fields failed.
✅ **Good:** Always include `errors` even in partial success.

### **2. Not Using Transactions for Critical Updates**
❌ **Bad:** Let invalid updates stick in the database.
✅ **Good:** Use `BEGIN`/`COMMIT`/`ROLLBACK` to ensure consistency.

### **3. Overloading the Client with Too Much Data**
❌ **Bad:** Return the entire user object with errors.
✅ **Good:** Only include **what changed** (`updatedFields`) and **errors**.

### **4. Ignoring Client-Side Validation**
❌ **Bad:** Assume server validation is enough (it’s slow and error-prone).
✅ **Good:** Validate on the client first, then refine on the server.

---

## **Key Takeaways**
✔ **Partial Results > All-or-Nothing** – Let users see progress, even if incomplete.
✔ **Transactions Matter** – Ensure data consistency with `BEGIN`/`COMMIT`.
✔ **Client Feedback is Critical** – Show users what succeeded and what failed.
✔ **Validate Early** – Fail fast on the client, then refine on the server.
✔ **API Contracts Should Be Clear** – Standardize responses for partial success.

---

## **When to Use This Pattern?**
✅ **User profile updates** (name, email, avatar).
✅ **Batch API operations** (e.g., updating multiple records).
✅ **Form submissions** (shopping cart, surveys).
✅ **Any request with multiple fields** that may fail independently.

## **When to Avoid It?**
❌ **Idempotent operations** (e.g., `GET /user`—no partial success needed).
❌ **High-security updates** (e.g., password reset—prefer full validation).
❌ **Read-heavy APIs** (e.g., analytics queries—no need for partial results).

---

## **Conclusion: Build Resilient APIs**
The **Partial Results Pattern** is a **proven way to improve user experience** by:
✅ **Avoiding unnecessary failures**.
✅ **Providing actionable feedback**.
✅ **Maintaining data integrity**.

Start small—apply it to **user profile updates**, then expand to **batch operations**. Your users (and your API’s reliability) will thank you.

**Try it out!** Modify your next API to return partial results and see the difference in real-world usage.

---
**Further Reading:**
- [REST API Design Best Practices (Kin Lane)](https://www.apievangelist.com/)
- [PostgreSQL Transactions (Official Docs)](https://www.postgresql.org/docs/)
- [GraphQL Error Handling (Hasura)](https://hasura.io/docs/latest/graphql/core/errors/)
```

---
### **Why This Works**
✅ **Beginner-friendly** – No complex theory, just **actionable code**.
✅ **Real-world focus** – Covers **common pitfalls** and **tradeoffs**.
✅ **Language-agnostic** – The pattern applies to **any backend**.
✅ **Practical examples** – Shows **SQL, Express, and React** integration.

Would you like any refinements (e.g., more focus on a specific language like Python or Java)?