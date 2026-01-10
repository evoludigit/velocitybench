---
# **[Pattern] Input Validation Patterns – Reference Guide**

---

## **1. Overview**
Input validation is a **critical security and reliability measure** that ensures data integrity by verifying user input, API payloads, file uploads, and other external inputs against predefined rules before processing. This pattern mitigates risks such as **SQL injection, XSS, data corruption, and application crashes** by enforcing constraints on:
- **Format** (e.g., email, date, JSON structure)
- **Type** (e.g., integer, string, boolean)
- **Length** (e.g., max 255 chars)
- **Allowed values** (e.g., predefined lists, regex patterns)

Validation should occur at **every system boundary** (API endpoints, database connections, CLI inputs) to prevent malicious or malformed data from reaching core logic or storage.

---

## **2. Core Principles**
Adopt these guidelines for robust input validation:

| Principle               | Description                                                                 |
|-------------------------|-----------------------------------------------------------------------------|
| **Fail Fast**           | Reject invalid input immediately with a clear error; never proceed silently. |
| **Defensive Coding**    | Assume all input is malicious; validate before parsing or processing.       |
| **Least Privilege**     | Validate at the lowest possible level (e.g., API gateway before middleware). |
| **Explicit > Implicit** | Define strict rules (e.g., `required: true`) rather than relying on defaults. |
| **Context-Aware**       | Rules vary by use case (e.g., a "username" vs. a "credit card" field).     |
| **Idempotency**         | Revalidate on repeated requests to handle race conditions.                  |
| **Logging**             | Log validation failures (without sensitive data) for debugging.              |

---

## **3. Schema Reference**
Use this table to define validation rules for common data types. Customize based on your system’s needs.

| Field          | Type       | Rules                                                                                     | Example Values          | Rejected Values       | Default Value |
|----------------|------------|------------------------------------------------------------------------------------------|-------------------------|-----------------------|---------------|
| **Username**   | String     | `length: 3-20`, `pattern: ^[a-zA-Z0-9_]+$`, `required: true`                           | `john_doe`, `user123`   | `John Doe`, `user@`    | `null`        |
| **Email**      | String     | `format: email`, `length: max 254`, `required: true`                                   | `user@example.com`      | `user@example`       | `null`        |
| **Age**        | Integer    | `min: 18`, `max: 120`                                                                   | `25`                    | `-5`, `abc`           | `null`        |
| **Password**   | String     | `length: 8-64`, `pattern: at least 1 special char`, `required: true`                     | `Pass123!`              | `pass`, `123456`      | `null`        |
| **UUID**       | String     | `format: uuid` (e.g., `^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$`)           | `550e8400-e29b-41d4-a716-446655440000` | `invalid-uuid`        | `null`        |
| **File Upload** | Binary     | `max_size: 5MB`, `allowed_extensions: [jpg, png, pdf]`, `required: true`               | `image.jpg`             | `script.py`, `file.exe` | `null`        |
| **API Key**    | String     | `length: 32-128`, `required: true` (check against a whitelist)                       | `abc123...` (valid)     | `short`, `malicious`  | `null`        |
| **Date**       | ISO String | `format: YYYY-MM-DD`, `min: 2020-01-01`                                                 | `2023-10-05`            | `05/10/2023`, `invalid` | `null`       |

---

## **4. Implementation Patterns**
### **4.1 Validation Libraries**
Leverage existing libraries to reduce boilerplate:

| Language/Tool          | Library/Framework                     | Key Features                                                                 |
|------------------------|---------------------------------------|------------------------------------------------------------------------------|
| **JavaScript**         | [Joi](https://joi.dev/), [Zod](https://github.com/colinhacks/zod)          | Schema validation, type inference, custom errors.                           |
| **Python**             | [Pydantic](https://pydantic-docs.helpmanual.io/), [Marshmallow](https://marshmallow.readthedocs.io/) | Data parsing, ORM-friendly, async support.                                  |
| **Java**               | [Bean Validation (JSR 380)](https://beanvalidation.org/), [Apache Commons Validator] | Integrates with frameworks like Spring; supports annotations.               |
| **Go**                 | [Govalidator](https://github.com/go-playground/validator), [structvalidate]  | Minimalist, custom validators, easy integration.                           |
| **C#**                 | [FluentValidation](https://fluentvalidation.net/), Data Annotations         | Rule chaining, dynamic validation, ASP.NET Core integration.               |
| **Ruby**               | [Dry-Validation](https://dry-rb.org/gems/dry-validation/), ActiveModel::Validations | Pure Ruby, composable rules.                                                |
| **PHP**                | [Symfony Validator](https://symfony.com/doc/current/validation.html), [Respect/Validation] | Framework-agnostic, supports complex rules.                                |

**Example (Joi in Node.js):**
```javascript
const Joi = require('joi');

const schema = Joi.object({
  email: Joi.string().email().required(),
  age: Joi.number().integer().min(18).max(120),
});

const { error } = schema.validate({ email: "test", age: "thirty" });
if (error) throw new Error(error.details[0].message); // "age must be a number"
```

---

### **4.2 Custom Validation Rules**
Extend libraries or write custom validators for domain-specific logic:

| Rule Type               | Example Use Case                          | Implementation Snippet (Pseudocode)                          |
|-------------------------|-------------------------------------------|---------------------------------------------------------------|
| **Whitelist/Blacklist** | Allow only specific countries/cities     | `if (city not in ['New York', 'London']) { reject() }`       |
| **Rate Limiting**       | Limit API calls to 100/hour per user     | `if (requests[user] > 100) { throw RateLimitExceeded() }`    |
| **IP Whitelisting**     | Restrict access to corporate IPs         | `if (request.ip not in allowed_ips) { reject() }`             |
| **File Hash Validation**| Ensure uploaded files haven’t been tampered with | `if (sha256(file) !== expected_hash) { reject() }`          |
| **Captcha Verification**| Prevent bot submissions                  | `if (!verify_captcha(token)) { reject() }`                   |

---

### **4.3 Validation by Layer**
Apply validation at multiple system layers for defense in depth:

| Layer               | Validation Example                                                                 | Tools/Techniques                                  |
|---------------------|------------------------------------------------------------------------------------|---------------------------------------------------|
| **API Gateway**     | Validate request headers (e.g., `X-API-Key`).                                     | Envoy, Kong, AWS API Gateway                      |
| **Application**     | Validate query/route parameters and request body.                                  | Framework-specific validators (e.g., FastAPI, Django REST). |
| **Database**        | Enforce constraints (e.g., `CHECK (age BETWEEN 18 AND 120)` in SQL).              | Raw SQL, ORM constraints.                         |
| **ORM/Repository**  | Validate entity models before database insertion.                                 | Pydantic (Python), Hibernate Validators (Java).   |
| **CLI/Script**      | Validate command-line arguments.                                                  | `argparse` (Python), Got (Go), `yargs` (Node).    |

---

### **4.4 Handling Edge Cases**
Anticipate and handle invalid inputs gracefully:

| Scenario                     | Recommended Approach                                                                 |
|------------------------------|--------------------------------------------------------------------------------------|
| **Empty Input**              | Return `400 Bad Request` with `{"error": "Field is required"}`.                     |
| **Too Long Input**           | Truncate or reject with `{"error": "Max length exceeded (255 chars)"}`.               |
| **Malformed JSON/XML**       | Return `400 Bad Request` with `{"error": "Invalid format"}` (no processing).          |
| **Rate Limiting Hit**        | Return `429 Too Many Requests` with `Retry-After` header.                            |
| **Database-Level Rejection** | Log the error but return a generic user-friendly message (e.g., "Invalid credentials"). |

---

## **5. Query Examples**
### **5.1 REST API Validation**
**Request:**
```http
POST /users
Content-Type: application/json

{
  "email": "invalid-email",
  "age": "twenty"
}
```
**Response (400 Bad Request):**
```json
{
  "errors": {
    "email": ["must be a valid email"],
    "age": ["must be a number", "must be between 18 and 120"]
  }
}
```

---

### **5.2 SQL Query Validation**
**Invalid Query (SQL Injection Attempt):**
```sql
-- User input: "DELETE FROM users WHERE id = "
SELECT * FROM users WHERE id = "1; DROP TABLE users; --"
```
**Defensive Approach:**
1. Use **prepared statements**:
   ```python
   # Python (SQLAlchemy)
   result = db.session.execute(text("SELECT * FROM users WHERE id = :id"), {"id": user_id})
   ```
2. **OR** enforce input constraints in the schema:
   ```sql
   ALTER TABLE users ADD CONSTRAINT valid_age CHECK (age BETWEEN 18 AND 120);
   ```

---

### **5.3 File Upload Validation**
**Allowed:** `profile.jpg` (200KB, JPEG)
**Rejected:** `malicious.php` (3MB)
Use middleware (e.g., [Express Multer](https://github.com/expressjs/multer) in Node.js) or ORM-level checks:
```javascript
const multer = require('multer');
const storage = multer.diskStorage({
  filename: (req, file, cb) => cb(null, `${Date.now()}-${file.originalname}`),
  fileFilter: (req, file, cb) => {
    if (!file.originalname.match(/\.(jpg|png)$/)) {
      return cb(new Error("Only JPG/PNG allowed"), false);
    }
    cb(null, true);
  }
});
```

---

## **6. Testing Validation**
Validate your validation logic with:
- **Unit Tests**: Test edge cases (e.g., `null`, empty string, max length).
- **Integration Tests**: Simulate API requests with invalid payloads.
- **Fuzz Testing**: Use tools like [AFL++](https://labs.dinamica.net/publications/af-faster/) or [Honggfuzz](https://github.com/google/honggfuzz) to find edge cases.
- **Static Analysis**: Linters (e.g., ESLint plugins for Joi/Zod) or tools like [Semgrep](https://semgrep.dev/).

**Example (Jest Test for Joi):**
```javascript
const { expect } = require('@jest/globals');
const Joi = require('joi');

test('validates email format', () => {
  const schema = Joi.string().email();
  expect(schema.validate("test@example.com").error).toBeNull();
  expect(schema.validate("invalid").error).toBeDefined();
});
```

---

## **7. Performance Considerations**
- **Avoid Over-Validation**: Validate only what’s necessary (e.g., skip password strength checks for read-only endpoints).
- **Caching**: Cache validation results for repeated requests (e.g., whitelisted IPs).
- **Concurrency**: Use async validators (e.g., `async-validator` in Node.js) to avoid blocking threads.
- **Benchmark**: Profile critical paths (e.g., API endpoints) to ensure validation doesn’t become a bottleneck.

---

## **8. Related Patterns**
| Pattern                           | Description                                                                 | When to Use                                      |
|-----------------------------------|-----------------------------------------------------------------------------|--------------------------------------------------|
| **[Authentication & Authorization](https://reflectoring.io/authentication-authorization/)** | Verify user identity and permissions.                         | After input validation to enforce access controls. |
| **[Rate Limiting](https://www.nginx.com/blog/rate-limiting-nginx/)** | Throttle requests to prevent abuse.                               | When combined with input validation for API security. |
| **[Circuit Breaker](https://microservices.io/patterns/resilience/circuit-breaker.html)** | Fail fast and recover gracefully from invalid data streams. | If validation fails repeatedly (e.g., corrupt API responses). |
| **[Idempotency Keys](https://docs.aws.amazon.com/amazons3/latest/userguide/idempotency.html)** | Ensure duplicate requests are handled safely.               | For retryable operations with validated inputs.   |
| **[Data Sanitization](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)** | Strip or encode malicious scripts (e.g., XSS).             | After validation to sanitize allowed inputs.      |
| **[Schema Registry](https://confluent.io/hub/confluentinc/kafka-schema-registry)** | Centralize validation rules for event-driven systems.       | For microservices exchanging schemas (e.g., Avro). |

---

## **9. Common Pitfalls**
| Pitfall                                | Risk                                                                 | Mitigation Strategy                                  |
|----------------------------------------|----------------------------------------------------------------------|------------------------------------------------------|
| **Trusting Client-Side Validation**    | Clients can bypass frontend checks.                                | Always validate on the server.                      |
| **Overly Complex Rules**               | Validation becomes a performance bottleneck.                        | Simplify rules; use libraries for common patterns.    |
| **Ignoring Null/Empty Inputs**         | NPEs (NullPointerExceptions) or inconsistent behavior.              | Explicitly handle `null`, `undefined`, and empty strings. |
| **Hardcoding Values**                  | Rules become hard to update.                                        | Externalize rules (e.g., config files, databases).   |
| **Validation Bypass in Errors**        | Exposing internal details (e.g., database column names).           | Return generic error messages to users.              |
| **Race Conditions**                    | Concurrent requests may bypass validation.                          | Use atomic checks (e.g., database transactions).     |

---

## **10. Further Reading**
- [OWASP Input Validation Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html)
- [Microsoft Secure Coding Guidelines: Input Validation](https://learn.microsoft.com/en-us/security/engineering/securesdk/input-validation)
- [12-Factor App: Validation as a Service](https://12factor.net/config) (externalize rules)
- [Postel’s Law](https://en.wikipedia.org/wiki/Robustness_principle) ("Be liberal in what you accept").