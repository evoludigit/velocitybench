**[Pattern] API Validation Reference Guide**
*Ensure data quality, consistency, and security in API interactions with structured validation rules.*

---

### **1. Overview**
API Validation enforces constraints on request/response data to maintain integrity across services. This pattern standardizes validation logic—applied at the API layer—to reject malformed inputs early, minimize downstream errors, and improve developer experience. Validation rules can include format checks (e.g., emails), required fields, type consistency, and custom business logic (e.g., "quantity > 0"). The pattern supports validation for:
- **Request Bodies** (POST/PUT)
- **Query Parameters** (GET)
- **Path Parameters** (DELETE/PUT)
- **Headers**
- **Responses** (e.g., error codes, metadata)

Unlike client-side validation (which only catches issues for the user), server-side validation ensures data reliability when processed. Implementations often pair with **OpenAPI/Swagger** for schema documentation or **JSON Schema** for declarative rules.

---
### **2. Schema Reference**
Use the following schemas to define validation rules. Tools like **FastAPI (Python), Express.js (Node.js)**, or **Spring Boot (Java)** integrate these natively.

| **Component**       | **Field**               | **Type**          | **Description**                                                                                     | **Example**                          |
|---------------------|-------------------------|-------------------|-----------------------------------------------------------------------------------------------------|--------------------------------------|
| **Request Body**    | `required`              | Boolean           | Mandatory fields.                                                                                   | `"required": true`                   |
|                     | `type`                  | String            | Data type: `string`, `number`, `integer`, `array`, `object`, `boolean`.                             | `"type": "string"`                   |
|                     | `format`                | String            | Standard formats: `email`, `date-time`, `uuid`, `ipv4`.                                              | `"format": "email"`                  |
|                     | `minimum`, `maximum`    | Number            | Numeric bounds.                                                                                     | `"minimum": 1`                       |
|                     | `enum`                  | Array             | Allowed values.                                                                                     | `"enum": ["active", "inactive"]`     |
|                     | `pattern`               | Regex             | Regex validation (e.g., passwords).                                                                 | `"pattern": "^[A-Za-z0-9]+$"`         |
| **Query/Path**      | `minLength`, `maxLength`| Number            | String length constraints.                                                                          | `"minLength": 3`                     |
|                     | `items` (for arrays)    | Schema            | Validate array elements recursively.                                                                  | `"items": { "type": "string" }`      |
| **Response**        | `statusCode`            | Integer           | Expected HTTP status (e.g., `400` for validation errors).                                           | `"statusCode": 400`                  |
|                     | `errorMessage`          | String            | Custom error messages for clients.                                                                  | `"errorMessage": "Invalid credentials"`|

**Example Schema (JSON):**
```json
{
  "type": "object",
  "properties": {
    "username": {
      "type": "string",
      "minLength": 3,
      "pattern": "^[a-zA-Z0-9_]+$"
    },
    "age": {
      "type": "integer",
      "minimum": 18,
      "maximum": 120
    },
    "roles": {
      "type": "array",
      "items": { "enum": ["admin", "user"] }
    }
  },
  "required": ["username", "age"]
}
```

---
### **3. Query Examples**
#### **Valid Request**
**Endpoint:** `POST /users`
**Body:**
```json
{
  "username": "j.doe123",
  "age": 30,
  "roles": ["user"]
}
```
**Response (201 Created):**
```json
{
  "id": "xyz789",
  "message": "User created successfully"
}
```

#### **Invalid Request (Missing Field)**
**Endpoint:** `POST /users`
**Body:**
```json
{
  "age": 30  // "username" is missing
}
```
**Response (400 Bad Request):**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Missing required field: username"
  }
}
```

#### **Custom Error Handling**
**Endpoint:** `POST /orders`
**Body:**
```json
{
  "items": [
    { "product": "laptop", "quantity": -1 } // Negative quantity
  ]
}
```
**Response (400 Bad Request):**
```json
{
  "error": {
    "code": "INVALID_QUANTITY",
    "message": "Quantity must be ≥ 1"
  }
}
```

---
### **4. Implementation Details**
#### **Key Concepts**
1. **Validation Placement**:
   - **API Gateway**: Centralized validation for all services (scalable but adds latency).
   - **Service Layer**: Validate per-service (granular but requires redundancy).
   - **Client-Side**: Catch errors early (UX benefit) but not reliable (bypassed).

2. **Validation Strategies**:
   - **Declarative (Schema-Driven)**: Define rules in OpenAPI/JSON Schema (e.g., FastAPI’s `Pydantic`).
     ```python
     from fastapi import FastAPI
     from pydantic import BaseModel

     class Item(BaseModel):
         name: str
         price: float

     app = FastAPI()
     @app.post("/items")
     async def create_item(item: Item):
         return item
     ```
   - **Programmatic**: Custom logic (e.g., Python’s `marshal` or Node.js middleware).
     ```javascript
     // Express.js middleware
     app.use((req, res, next) => {
       if (!req.body.email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) {
         return res.status(400).json({ error: "Invalid email" });
       }
       next();
     });
     ```
   - **Hybrid**: Combine schema + custom checks (e.g., validate format *and* business rules).

3. **Error Handling**:
   - Return **consistent error formats** (e.g., JSON with `error.code` and `error.message`).
   - Use **HTTP status codes**:
     - `400 Bad Request`: Invalid input.
     - `422 Unprocessable Entity`: Semantic errors (e.g., "price < cost").
   - Log validation failures for analytics (e.g., "Invalid email domain: `spam.com`").

4. **Performance**:
   - **Early Validation**: Check required fields before parsing complex schemas.
   - **Caching**: Cache validation schemas if unused for >1 hour (e.g., Redis).
   - **Async Support**: Use non-blocking validation (e.g., `async/await` in Node.js).

5. **Security**:
   - **Input Sanitization**: Strip or escape dangerous characters (e.g., SQL injection).
   - **Rate Limiting**: Validate + rate-limit to prevent brute-force attacks.
   - **API Keys**: Validate auth headers alongside payloads.

---

#### **Common Pitfalls**
| **Pitfall**               | **Solution**                                                                 |
|---------------------------|-----------------------------------------------------------------------------|
| Overly complex schemas    | Split into smaller schemas (e.g., `User`, `Address`).                       |
| Silent failures           | Always return `400` for invalid inputs; avoid `200` with partial success.   |
| Validation drift          | Sync schema definitions across teams (e.g., GitHub sync for OpenAPI files).|
| No response validation    | Validate responses for errors/metadata (e.g., check `status: "active"`).    |

---

### **5. Query Examples (Advanced)**
#### **Nested Validation**
**Schema:**
```json
{
  "type": "object",
  "properties": {
    "order": {
      "type": "object",
      "properties": {
        "items": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "id": { "type": "string", "format": "uuid" },
              "price": { "type": "number", "minimum": 0 }
            },
            "required": ["id", "price"]
          }
        }
      },
      "required": ["items"]
    }
  }
}
```
**Valid Request:**
```json
{
  "order": {
    "items": [
      { "id": "550e8400-e29b-41d4-a716-446655440000", "price": 9.99 }
    ]
  }
}
```

#### **Conditional Validation**
**Use Case**: Discounts only apply to orders >$100.
**Implementation (Node.js):**
```javascript
if (order.total > 100 && !order.discount) {
  return res.status(400).json({ error: "Discount required for large orders" });
}
```

#### **Dynamic Validation**
**Use Case**: Validate fields based on `type` (e.g., `user` vs. `admin`).
**Schema (JSON Schema Draft 7):**
```json
{
  "type": "object",
  "properties": {
    "type": { "enum": ["user", "admin"] },
    "adminOnly": {
      "type": ["string", "null"],
      "if": { "properties": { "type": { "const": "admin" } } },
      "then": { "type": "string" }
    }
  }
}
```

---
### **6. Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                          |
|---------------------------|-------------------------------------------------------------------------------|------------------------------------------|
| **[Request/Response]**    | Standardize API contracts for consistency.                                    | Define schemas before validation.        |
| **[Authentication]**      | Secure API access with tokens/keys.                                           | Validate auth *and* payloads together.   |
| **[Rate Limiting]**       | Control API usage to prevent abuse.                                            | Pair with validation for security.      |
| **[Idempotency Keys]**    | Ensure safe retries for duplicate requests.                                   | Use with validation for order processing. |
| **[CORS]**                | Restrict cross-origin requests for security.                                  | Validate origins + payloads.             |
| **[OpenAPI/Swagger]**     | Document APIs with interactive validation.                                    | Publish schemas for client teams.        |

---
### **7. Tools/Libraries**
| **Tool**               | **Language/Framework** | **Key Features**                                  |
|------------------------|------------------------|--------------------------------------------------|
| **FastAPI (Pydantic)** | Python                 | Auto-validation, OpenAPI docs, async support.    |
| **Express Validator**  | Node.js                | Middleware for query/body/path validation.       |
| **Spring Boot Validator** | Java     | `@Valid` annotations, Bean Validation API.      |
| **Apache APISIX**      | Lua/Proxy              | Gateway-level schema validation.                 |
| **JSON Schema Validator** | Cross-platform | CLI/tool for validating JSON against schemas. |

---
### **8. Best Practices**
1. **Document Clearly**: Include examples in OpenAPI docs (e.g., `examples` field in OpenAPI 3.x).
2. **Version Schemas**: Use semantic versioning (e.g., `v1.0.0`) for backward compatibility.
3. **Test Thoroughly**:
   - Unit tests for validation logic (e.g., Jest for Node.js).
   - Integration tests with mock APIs (e.g., Postman/Newman).
4. **Monitor Failures**: Track validation errors in logs/APM tools (e.g., Datadog).
5. **Client Libraries**: Generate SDKs with built-in validation (e.g., `swagger-codegen`).

---
### **9. Example Workflow**
1. **Client** sends:
   ```json
   { "email": "invalid", "age": "thirty" }
   ```
2. **API Gateway/Service** validates:
   - `email` fails `format: email`.
   - `age` fails `type: integer`.
3. **Response**:
   ```json
   {
     "errors": [
       { "path": "email", "message": "Invalid email format" },
       { "path": "age", "message": "Must be an integer" }
     ]
   }
   ```
   **Status**: `400 Bad Request`

---
### **10. References**
- [FastAPI Documentation](https://fastapi.tiangolo.com/tutorial/body-validation/)
- [JSON Schema Specification](https://json-schema.org/)
- [OpenAPI Specification](https://spec.openapis.org/oas/v3.1.0)
- [Express Validator](https://express-validator.github.io/docs/)