```markdown
---
title: "Input Validation & Sanitization: Secure Your APIs Like a Pro"
date: 2023-10-15
author: "Jane Doe"
tags: ["backend", "security", "database", "api-design"]
---

# Input Validation & Sanitization: Secure Your APIs Like a Pro

As backend developers, we spend most of our time building robust APIs and database schemas. But if you haven’t stopped to think about input validation and sanitization, you might be leaving your applications exposed to malicious actors. A single oversight in input handling can lead to catastrophic breaches—think SQL injection, XSS attacks, or malicious payloads that corrupt your database.

Roughly **70% of database security incidents** stem from poor input validation (according to OWASP). That’s not just theory; it’s a real risk in production systems. Even experienced developers often make subtle mistakes—like trusting client input blindly or misapplying sanitization—that can turn a simple function into an attack vector. The good news? This pattern is straightforward to implement correctly once you understand the key principles.

In this guide, we’ll cover:
- Why inputs are the first line of defense in security
- How to validate and sanitize inputs for different use cases (REST APIs, forms, database queries)
- Practical code examples in Python and JavaScript
- Common pitfalls and how to avoid them
- Tradeoffs between validation libraries and manual checks

Let’s dive in.

---

## The Problem: Why Input Validation & Sanitization Matters

Imagine this scenario:
A customer submits a review on your e-commerce platform. They include a star rating of `5` and some text like:
“This product is amazing! 😊✨ My favorite purchase—#BestBuyEver.”

Now, imagine the same user sends:
```sql
"DELETE FROM products WHERE id = 1; --"
```
as their review text.

Without proper input handling, your backend might:
1. **Directly pass this to your database**, accidentally deleting your entire product table.
2. **Inject malicious scripts** into your HTML if the review is displayed on a webpage, leading to XSS attacks.
3. **Crash your application** if the input violates type or format expectations (e.g., a negative age in a user profile).

This isn’t hypothetical. In 2021, a misconfigured API on a major retail site exposed customer data because the team didn’t sanitize URL parameters. The incident led to a 4-month breach affecting millions.

The core issue is that **all user input is untrusted**. Even if you “know” your users, an attacker might impersonate them or exploit your system. Your code must validate and sanitize inputs before processing them.

---

## The Solution: A Layered Approach

The best practice is to **validate early, sanitize later**. Here’s how we’ll break it down:

1. **Validation**: Ensure inputs meet expected criteria (e.g., required fields, data types, ranges).
2. **Sanitization**: Strip or encode dangerous characters to prevent injection attacks.
3. **Defense in Depth**: Apply security measures at multiple layers (client, server, database).

---

## Components & Solutions

### 1. Validation: Rules for Inputs
Validation checks whether inputs conform to expected formats. For example:
- A password must be at least 8 characters long.
- An email must match the regex `^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$`.
- A user’s age must be between 13 and 120.

#### Validation Libraries
Libraries like `pydantic` (Python) or `Zod` (JavaScript) automate much of this work. Here’s how they compare:

| Library       | Language   | Strengths                          | Weaknesses                  |
|---------------|------------|------------------------------------|-----------------------------|
| `pydantic`    | Python     | Intuitive schema validation        | Heavy for simple projects    |
| `Zod`         | JavaScript | Lightweight, TypeScript integration | Requires manual setup        |
| `express-validator` | Node.js | Integrates with Express            | Verbose for complex rules    |

#### Example: Validating a User Signup Form
Using `Pydantic` (Python):
```python
from pydantic import BaseModel, EmailStr, validator

class UserSignup(BaseModel):
    username: str
    email: EmailStr
    age: int = 18
    password: str

    @validator("age")
    def age_must_be_reasonable(cls, v):
        if v < 13 or v > 120:
            raise ValueError("Age must be between 13 and 120")
        return v

# Usage:
user_data = {"username": "alice", "email": "alice@example.com", "age": "25", "password": "secure123"}
user = UserSignup(**user_data)
```

Using `Zod` (JavaScript):
```javascript
import { z } from "zod";

const userSchema = z.object({
  username: z.string().min(3).max(20),
  email: z.string().email(),
  age: z.number().int().min(13).max(120),
  password: z.string().min(8),
});

const userData = {
  username: "alice",
  email: "alice@example.com",
  age: 25,
  password: "secure123",
};

try {
  const validatedUser = userSchema.parse(userData);
  console.log("Valid user:", validatedUser);
} catch (error) {
  console.error("Invalid data:", error.errors);
}
```

### 2. Sanitization: Cleaning Inputs
Sanitization removes or encodes dangerous characters. For example:
- **SQL Injection**: Replace `'` with `''` or use parameterized queries.
- **XSS**: Escape HTML or use `text/html` content type with proper headers.
- **LDAP Injection**: Encode special characters in directory queries.

#### Example: Sanitizing User Input for SQL Queries (Python)
❌ **Unsafe**:
```python
user_input = "admin'; DROP TABLE users;--"
query = f"SELECT * FROM users WHERE username = '{user_input}'"
# Exploitable!
```

✅ **Safe**:
```python
import sqlite3

user_input = "admin'; DROP TABLE users;--"
query = "SELECT * FROM users WHERE username = ?"
conn = sqlite3.connect("database.db")
cursor = conn.cursor()
cursor.execute(query, (user_input,))  # Parameterized query
```

#### Example: Sanitizing HTML Input (JavaScript)
```javascript
const userInput = '<script>alert("hacked")</script>';

// Option 1: Escape HTML (DOMPurify is a robust library)
import DOMPurify from "dompurify";
const cleanedInput = DOMPurify.sanitize(userInput);

// Option 2: Simple text-only encoding (less secure)
const escapedInput = userInput.replace(/</g, "&lt;").replace(/>/g, "&gt;");
```

### 3. Defense in Depth: Multiple Layers
Never rely on a single layer of security. Combine:
- **Client-side validation**: Improve UX with immediate feedback (but don’t trust it).
- **Server-side validation**: The only layer you *must* rely on.
- **Database-level safeguards**: Use stored procedures or schema constraints.
- **API gateways**: Tools like Kong or AWS API Gateway can block malicious traffic.

---

## Implementation Guide

### Step 1: Define Validation Rules
For each input field, ask:
- What’s the expected type? (string, number, boolean)
- Are there constraints? (e.g., minimum age, allowed characters)
- Should the input be required?

#### Example: API Endpoint for `/api/users` (Express.js)
```javascript
const express = require("express");
const { body, validationResult } = require("express-validator");

const router = express.Router();

router.post(
  "/users",
  [
    // Validate email format
    body("email").isEmail(),
    // Validate age is a number between 13 and 120
    body("age").isInt({ min: 13, max: 120 }),
    // Password must be at least 8 chars
    body("password").isLength({ min: 8 }),
  ],
  (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }
    // Proceed with sanitization and database operations
    res.status(201).json({ success: true });
  }
);
```

### Step 2: Sanitize Inputs Before Processing
Always sanitize inputs *before* using them in:
- SQL queries
- OS commands
- HTML rendering
- JSON/XML parsing

#### Example: Sanitizing for SQL (Python)
```python
import re

def sanitize_username(username):
    # Remove dangerous characters (SQL injection)
    sanitized = re.sub(r"[;'\-\-\\\x00-\x1f]", "", username)
    return sanitized

# Usage:
user_input = "admin'; DROP TABLE users;--"
safe_input = sanitize_username(user_input)  # Returns "admin"
```

### Step 3: Use Parameterized Queries Always
**Never** interpolate inputs into SQL or shell commands. Use:
- Python: `sqlite3`’s `?` placeholders or `psycopg2` for PostgreSQL.
- JavaScript: `pg` (PostgreSQL) or `mysql2/promise` for MySQL.

#### Example: Parameterized Query (Node.js)
```javascript
const { Pool } = require("pg");

const pool = new Pool();

async function getUser(userId) {
  const query = "SELECT * FROM users WHERE id = $1";
  const { rows } = await pool.query(query, [userId]);
  return rows[0];
}

// Safe even if userId is malicious
getUser("1; DROP TABLE users;--");
```

### Step 4: Handle Errors Gracefully
- Return **400 Bad Request** for invalid inputs.
- Log validation errors (without exposing sensitive data).
- Avoid error messages that leak system details.

#### Example: Graceful Error Handling (Python)
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ValidationError

app = FastAPI()

class CreateUser(BaseModel):
    username: str
    email: str
    age: int

@app.post("/users")
async def create_user(user: CreateUser):
    try:
        # Simulate database save
        return {"message": "User created", "user": user.dict()}
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

## Common Mistakes to Avoid

1. **Assuming Client Validation is Enough**
   - *Why it’s wrong*: Attackers can bypass client-side checks (e.g., with browser extensions).
   - *Fix*: Always validate server-side.

2. **Over-Sanitizing Inputs**
   - *Why it’s wrong*: Aggressively sanitizing can break valid inputs (e.g., stripping legitimate apostrophes).
   - *Fix*: Use targeted sanitization (e.g., escape only for SQL/HTML).

3. **Ignoring Edge Cases**
   - *Why it’s wrong*: Inputs like `\0`, `\x00`, or very long strings can crash your app.
   - *Fix*: Validate length constraints (e.g., `max_length: 100`).

4. **Using ORMs Carelessly**
   - *Why it’s wrong*: ORMs like Django ORM or Sequelize can still be exploited if you don’t use their parameterized queries.
   - *Fix*: Always use ORM methods for queries (e.g., `User.objects.filter(username=username)`).

5. **Logging Sensitive Inputs**
   - *Why it’s wrong*: Logs are often misconfigured and can leak passwords or PII.
   - *Fix*: Never log raw inputs. Log only sanitized or hashed versions.

6. **Not Updating Dependencies**
   - *Why it’s wrong*: Libraries like `pydantic` or `express-validator` may have security patches.
   - *Fix*: Use tools like `safety` (Python) or `npm audit` (Node.js) to check for vulnerabilities.

---

## Key Takeaways

- **All user input is untrusted**. Treat it as malicious until proven otherwise.
- **Validate early, sanitize later**. Use libraries like `Pydantic`, `Zod`, or `express-validator` for validation.
- **Never interpolate inputs into SQL or shell commands**. Always use parameterized queries.
- **Sanitize for context**. Escape HTML for web output, but not for database storage.
- **Defense in depth**: Combine client-side validation, server-side checks, and database constraints.
- **Avoid common pitfalls**: Don’t rely on client validation, over-sanitize, or ignore edge cases.
- **Keep dependencies updated**. Security patches are critical.

---

## Conclusion

Input validation and sanitization are non-negotiable for secure backend development. By following the patterns in this guide—validation rules, context-aware sanitization, and parameterized queries—you’ll significantly reduce your risk of injection attacks, data breaches, and application crashes.

Remember: Security is an ongoing process. Regularly audit your input handling, stay updated on OWASP’s Top 10, and treat every input as a potential threat. The effort is worth it—your users (and your peace of mind) will thank you.

Now go forth and build securely!
```

---
**Related Resources:**
- [OWASP Input Validation Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html)
- [Python `pydantic` Documentation](https://pydantic-docs.helpmanual.io/)
- [Zod Validation Guide](https://zod.dev/)