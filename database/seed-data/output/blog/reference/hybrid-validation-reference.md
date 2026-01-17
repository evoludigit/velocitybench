# **[Pattern] Hybrid Validation Reference Guide**

---

## **Overview**
The **Hybrid Validation** pattern combines **client-side validation** (e.g., browser-side checks) with **server-side validation** to ensure **data consistency, security, and UX optimization**. It leverages fast, immediate feedback on the client to improve user experience while relying on the server to enforce strict rules, handle complex logic, and prevent malicious payloads. This pattern is ideal for web applications where **real-time feedback** is important but **strict compliance** is non-negotiable.

Hybrid validation **reduces server load** (by catching errors early) while maintaining **data integrity** (via server-side enforcement). It’s particularly useful for forms, API requests, and stateful workflows where both **UX** and **security** must align.

---

## **Key Concepts & Implementation Details**

### **1. Core Principles**
| Concept                     | Description                                                                                                                                                                                                 | Responsibility               |
|-----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------|
| **Client-Side Validation**  | Lightweight checks for **UX improvement** (e.g., real-time feedback, reducing round trips). Example: Regex for email format, required fields.                                                          | **Client (frontend)**        |
| **Server-Side Validation**  | Strict, **security-focused** checks (e.g., business logic, sanitization, authorization). Example: Database constraints, complex rules like "must be a registered user." | **Server (backend)**          |
| **Error Handling**          | Consistent error messages for both client and server failures, with server-side validation taking precedence.                                                                                            | Both                        |
| **Immutability**            | Client-side changes may be rejected by the server; clients must handle graceful fallbacks.                                                                                                                   | Client & Server              |
| **Performance Tradeoff**    | Client validation reduces server load but may introduce complexity (e.g., maintaining sync between rules).                                                                                                      | Architectural consideration  |

---

### **2. Schema Reference**
Below is a structured schema for defining hybrid validation rules in a **declarative format** (e.g., JSON Schema, OpenAPI, or custom config).

| Field               | Type     | Description                                                                                                                                                                                                 | Example Values                          |
|---------------------|----------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------|
| `clientRules`       | Object   | Rules enforced on the client for **UX optimization**. Must be a **subset** of server-side rules.                                                                                                       | `{ "required": ["email", "password"], "pattern": { "email": "/^.*@.*$/" } }` |
| `serverRules`       | Object   | **Strict** rules enforced on the server (e.g., database constraints, business logic). **Must override** client-side mismatches.                                                                      | `{ "unique": ["email"], "minLength": { "password": 12 } }` |
| `errorMessages`     | Object   | Custom error messages for failed validations (client + server). Server messages take precedence if duplicate keys exist.                                                                              | `{ "email": { "client": "Invalid format", "server": "Duplicate entry" } }` |
| `sanitization`      | Object   | Rules for **input sanitization** (e.g., trimming, escaping). Runs **before** validation.                                                                                                                  | `{ "trim": ["username"], "escapeHtml": ["description"] }` |
| `dependencies`      | Array    | Fields that **must satisfy** conditions for another field to validate. Example: `"passwordConfirm": ["password"]` (must match).                                                                         | `[{ "field": "age", "condition": { "field": "isAdult", "value": true } }]` |
| `asyncRules`        | Object   | Rules requiring **server-side async checks** (e.g., API calls, database queries). Client pre-fetches data if possible.                                                                                     | `{ "username": { "async": true, "call": "/check-availability" } }` |

---

### **3. Implementation Patterns**
#### **A. Form Submission Flow**
1. **Client Preflight**
   - Validate fields **before submission** (e.g., using `beforeSubmit` in libraries like **Formik** or **React Hook Form**).
   - Show errors **immediately** (e.g., inline feedback, tooltips).
   - Example (React Hook Form + zod):
     ```javascript
     const schema = z.object({
       email: z.string().email({ message: "Invalid email" }).min(1, "Required"),
       password: z.string().min(12, "Must be 12+ chars"),
     });
     const { register, handleSubmit, formState: { errors } } = useForm({ resolver: zodResolver(schema) });
     ```

2. **Submit Attempt**
   - Send payload to server **even if client passes validation** (server **always** validates).
   - **Do not rely solely on client-side validation** for security-critical data (e.g., credentials, payments).

3. **Server Response**
   - Return **specific error codes** (e.g., `400 Bad Request` with `validationErrors` payload).
   - Example response:
     ```json
     {
       "success": false,
       "errors": {
         "email": ["Must be unique"],
         "password": ["Must include a number"]
       }
     }
     ```

4. **Client Fallback**
   - Update UI with **server errors** if client validation passed (rare but necessary).
   - Example:
     ```javascript
     if (!response.ok) {
       const data = await response.json();
       setErrors(data.errors); // Override or merge with client errors
     }
     ```

#### **B. API Requests**
- **Preflight Validation**: Validate request body/params in the client before sending (e.g., using **Swagger/OpenAPI** or custom libraries).
- **Server-Side**: Always validate in the **route handler** (e.g., Express middleware, FastAPI).
  ```python
  # FastAPI example
  from fastapi import FastAPI, HTTPException
  from pydantic import BaseModel

  class UserCreate(BaseModel):
      email: str
      password: str = Field(..., min_length=12)

  app = FastAPI()
  @app.post("/users/")
  def create_user(user: UserCreate):
      if User.select().where(User.email == user.email).exists():
          raise HTTPException(400, {"error": "Email already exists"})
      return {"message": "User created"}
  ```

#### **C. Real-Time Input (e.g., Search Bars, Autocomplete)**
- **Debounce client validation** (e.g., validate after user pauses typing).
- **Server-side validation** runs only for **submitted queries** (e.g., after pressing "Search").
- Example (React + useDebounce):
  ```javascript
  const [query, setQuery] = useState("");
  const debouncedQuery = useDebounce(query, 300);

  useEffect(() => {
    if (debouncedQuery) {
      validateClientSide(debouncedQuery); // Lightweight checks
    }
  }, [debouncedQuery]);
  ```

---

### **4. Query Examples**
#### **Client-Side Validation (JavaScript)**
```javascript
// Validate email format before submission
const validateEmail = (email) => {
  const clientRule = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return clientRule.test(email) ? { valid: true } : { valid: false, message: "Invalid email" };
};

// Example usage
const email = "test@example.com";
const result = validateEmail(email);
console.log(result); // { valid: true }
```

#### **Server-Side Validation (Node.js + Express)**
```javascript
const { body, validationResult } = require("express-validator");

app.post("/users",
  body("email").isEmail().normalizeEmail(),
  body("password").isLength({ min: 12 }),
  (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }
    // Proceed if valid
    res.send({ success: true });
  }
);
```

#### **Async Validation (Database Check)**
```sql
-- Example: Check if email exists in the database (server-side)
SELECT COUNT(*) FROM users WHERE email = 'test@example.com';
```
**Backend (Python Flask):**
```python
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import BadRequest

db = SQLAlchemy()
email_exists = db.session.query(db.session.query(db.exists().where(User.email == new_user.email)).scalar())
if email_exists:
    raise BadRequest("Email already registered")
```

---

### **5. Error Handling Best Practices**
| Scenario                     | Client Action                          | Server Action                          | User Feedback                     |
|------------------------------|----------------------------------------|----------------------------------------|-----------------------------------|
| **Client fails**             | Show error immediately.                | Ignore (client handled).              | Inline tooltip/error message.      |
| **Server fails**             | Clear client errors.                   | Return detailed errors.               | Override client display with server message. |
| **Async dependency fails**   | Disable submit button while loading.   | Return `429 Too Many Requests` if rate-limited. | Spinner + timeout message.       |
| **Sanitization fails**       | Strip invalid chars (client-side).    | Reject entirely (server-side).        | Warn user: "Invalid characters removed." |

---

### **6. Tools & Libraries**
| Category               | Tools/Libraries                                                                                     |
|------------------------|---------------------------------------------------------------------------------------------------|
| **Frontend Validation** | React Hook Form, Formik, zod, yup, AJV (JSON Schema)                                              |
| **Backend Validation**  | Express-validator (Node), FastAPI (Python), Django forms, Pydantic (Python), Spring Validation (Java) |
| **Schema Definition**   | OpenAPI (Swagger), JSON Schema, GraphQL Schema                                                   |
| **Async Validation**    | Axios interceptors, custom hooks, debouncing libraries (e.g., `lodash.debounce`)                 |

---

## **Related Patterns**
1. **[Client-Side Only Validation]**
   - *Use when*: UX is priority, data is non-sensitive (e.g., form styling), or server validation is trivial.
   - *Avoid when*: Security-critical data (e.g., passwords, payments) or complex business rules.

2. **[Server-Side Only Validation]**
   - *Use when*: Strict security requirements (e.g., financial systems) or validation logic is too complex for the client.
   - *Avoid when*: Real-time feedback is critical (e.g., search bars, live collaboration tools).

3. **[Optimistic UI + Validation]**
   - Assume validation passes, then **roll back** on server failure (e.g., Redux-Optimistic, React Query’s `mutateAsync`).
   - *Pair with*: Hybrid validation for **immediate UX** while maintaining server integrity.

4. **[EAFP (Easier to Ask for Forgiveness than Permission)]**
   - Validate only when failing (e.g., try database insertion, catch errors). Use sparingly in forms.
   - *Contrast with*: Hybrid validation’s **preemptive** approach.

5. **[Idempotent Requests]**
   - For APIs: Use idempotency keys to prevent duplicate submissions (e.g., Stripe’s `idempotency-key`).
   - *Works well with*: Hybrid validation to ensure **retries** are handled gracefully.

---

## **Anti-Patterns to Avoid**
| Anti-Pattern                          | Problem                                                                 | Solution                          |
|---------------------------------------|--------------------------------------------------------------------------|-----------------------------------|
| **Relying solely on client validation** | Bypassed by disabled scripts, tampered data, or malicious payloads.    | Always validate on the server.    |
| **Overloading client with complex rules** | Slows UI, increases bundle size.                                      | Offload complex logic to server. |
| **Ignoring server errors on client**  | Users submit invalid data repeatedly.                                   | Show server errors prominently.  |
| **Caching client validation state**   | Stale data (e.g., form resets, browser refreshes).                      | Re-validate on every submit.     |
| **Mixing validation layers poorly**   | Conflicting rules (e.g., client allows short passwords, server rejects). | Ensure `clientRules` ⊆ `serverRules`. |

---

## **When to Use Hybrid Validation**
✅ **Forms** (registration, login, surveys)
✅ **APIs** (CRUD operations, search queries)
✅ **Real-time apps** (chat, live edits, autocomplete)
✅ **Stateful workflows** (multi-step processes like checkout)

❌ **Avoid for**:
- Highly dynamic rules (use server-side only).
- Low-stakes UIs (e.g., non-critical admin panels).
- Extensively connected clients (e.g., offline-first apps with inconsistent network).