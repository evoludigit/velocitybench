---

# **[Pattern] REST Validation Reference Guide**

---

## **Overview**
The **REST Validation Pattern** standardizes how data is validated upon submission, ensuring request consistency, security, and correct API behavior. This pattern defines schema-based validation for request/response payloads, path parameters, query parameters, and headers, enforcing constraints before processing. By validating early and returning structured error responses, APIs improve reliability, developer experience, and debugging efficiency.

Key benefits include:
- **Predictable error handling**: Clients receive consistent, machine-readable validation errors.
- **Reduced server load**: Invalid payloads are rejected before processing.
- **Documentation via schema**: APIs self-describe constraints (e.g., OpenAPI/Swagger).
- **Security**: Prevents malformed or malicious input (e.g., SQL injection, buffer overflows).

---

## **Schema Reference**

Validation schemas are defined using **JSON Schema** (or equivalent formats like XML Schema, YAML). Below are common schema structures for REST endpoints.

### **1. Request Payload Validation**
| Field          | Type       | Description                                                                 | Example Constraints                                                                 |
|----------------|------------|-----------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| `title`        | `string`   | A human-readable identifier for the schema.                               | `"type": "string", "minLength": 3, "maxLength": 64`                                |
| `description`  | `string`   | Detailed schema explanation.                                                | `"format": "html"`                                                                  |
| `required`     | `array`    | Fields mandatory for validation.                                            | `["username", "email"]`                                                             |
| `properties`   | `object`   | Nested field definitions.                                                   | `{ "username": { "type": "string", "pattern": "^[a-zA-Z0-9_]+$" } }`               |
| `additionalProperties` | `boolean` | Allows/unrestricts extra fields.                                          | `"additionalProperties": false`                                                     |
| `enum`         | `array`    | Validates against a predefined list.                                        | `"enum": ["admin", "user", "guest"]`                                               |
| `items`        | `object`   | Defines array/item constraints.                                             | `{ "items": { "type": "number", "minimum": 0 } }`                                    |
| `oneOf`/`anyOf`| `array`    | Validates against *exactly one* (`oneOf`) or *any* (`anyOf`) schema.        | `{ "oneOf": [{ "type": "string" }, { "type": "integer" }] }`                         |
| `format`       | `string`   | Enforces data formats (e.g., `date-time`, `email`).                       | `"format": "date-time"`                                                              |
| `const`        | `any`      | Validates against a literal value.                                          | `"const": 42`                                                                     |
| `default`      | `any`      | Provides a fallback value.                                                  | `"default": "default@example.com"`                                                  |

---
### **2. Query Parameter Validation**
Query parameters are validated using query schema objects (e.g., in OpenAPI):
```json
{
  "parameters": [
    {
      "name": "limit",
      "in": "query",
      "schema": {
        "type": "integer",
        "minimum": 1,
        "maximum": 100,
        "default": 10
      },
      "required": false
    }
  ]
}
```

---
### **3. Path Parameter Validation**
Path parameters enforce route constraints (e.g., `/users/{userId}`):
```json
{
  "parameters": [
    {
      "name": "userId",
      "in": "path",
      "schema": {
        "type": "string",
        "pattern": "^[a-zA-Z0-9]{8,32}$"
      },
      "required": true
    }
  ]
}
```

---
### **4. Header Validation**
Headers validate security/auth constraints (e.g., `Authorization`):
```json
{
  "headers": {
    "Authorization": {
      "schema": {
        "type": "string",
        "pattern": "^Bearer [a-zA-Z0-9._-]+$",
        "example": "Bearer xyz123"
      },
      "required": true
    }
  }
}
```

---
### **5. Response Validation**
Responses define expected structure (e.g., success/error codes):
```json
{
  "responses": {
    "200": {
      "description": "Success",
      "content": {
        "application/json": {
          "schema": {
            "type": "object",
            "properties": {
              "data": { "type": "array", "items": { "$ref": "#/components/schemas/User" } }
            }
          }
        }
      }
    },
    "400": {
      "description": "Validation Error",
      "content": {
        "application/json": {
          "schema": {
            "type": "object",
            "properties": {
              "errors": {
                "type": "array",
                "items": { "type": "string" }
              }
            }
          }
        }
      }
    }
  }
}
```

---

## **Implementation Details**

### **Key Concepts**
1. **Schema Enforcement**:
   - Use tools like [JSON Schema Validator](https://json-schema.org/), [Joi](https://joi.dev/), or [Zod](https://github.com/colinhacks/zod) to validate payloads.
   - Embed schemas in API documentation (e.g., OpenAPI/Swagger).

2. **Error Handling**:
   - Return **standardized error responses** (e.g., HTTP 400 for invalid requests):
     ```json
     {
       "errors": [
         {
           "field": "email",
           "message": "Must be a valid email",
           "code": "invalid_email"
         }
       ]
     }
     ```
   - Include **error codes** for programmatic handling.

3. **Server-Side Validation**:
   - Validate **before** business logic executes (e.g., in middleware).
   - Example (Node.js with Express + Joi):
     ```javascript
     const express = require('express');
     const Joi = require('joi');

     const schema = Joi.object({
       username: Joi.string().alphanum().min(3).max(30).required(),
       email: Joi.string().email().required()
     });

     app.post('/register', (req, res, next) => {
       const { error } = schema.validate(req.body);
       if (error) return res.status(400).json({ errors: error.details });
       next();
     });
     ```

4. **Client-Side Validation**:
   - Preemptively validate using libraries like [Yup](https://github.com/jquense/yup) (JavaScript) or [Pydantic](https://pydantic-docs.helpmanual.io/) (Python).
   - Example (React + Yup):
     ```javascript
     const schema = Yup.object().shape({
       username: Yup.string().required().min(3),
       email: Yup.string().email().required()
     });

     Yup.reach(req.body, 'email').validate().catch(err => {
       setError(err.message);
     });
     ```

5. **Validation Tools**:
   - **Backend**: FastAPI (Pydantic), Django REST Framework, Express (Joi/Zod).
   - **Frontend**: React Hook Form, Formik + Yup.
   - **Standalone**: [Ajv](https://ajv.js.org/) (JSON Schema validator).

---

## **Query Examples**

### **1. Valid Request**
**Endpoint**: `POST /users`
**Request**:
```json
{
  "username": "jdoe",
  "email": "john@example.com",
  "age": 30
}
```
**Schema**:
```json
{
  "type": "object",
  "properties": {
    "username": { "type": "string", "minLength": 3 },
    "email": { "type": "string", "format": "email" },
    "age": { "type": "integer", "minimum": 18, "maximum": 120 }
  },
  "required": ["username", "email"]
}
```
**Response** (201 Created):
```json
{
  "id": "123",
  "username": "jdoe",
  "email": "john@example.com"
}
```

---

### **2. Invalid Request (Missing Field)**
**Request**:
```json
{
  "email": "invalid"
}
```
**Response** (400 Bad Request):
```json
{
  "errors": [
    {
      "field": "username",
      "message": "Username is required",
      "code": "missing_field"
    }
  ]
}
```

---

### **3. Invalid Query Parameter**
**Endpoint**: `GET /users?limit=150`
**Schema**:
```json
{
  "parameters": [
    {
      "name": "limit",
      "schema": {
        "type": "integer",
        "minimum": 1,
        "maximum": 100
      }
    }
  ]
}
```
**Response** (400 Bad Request):
```json
{
  "errors": [
    {
      "field": "limit",
      "message": "Limit must be between 1 and 100",
      "code": "invalid_limit"
    }
  ]
}
```

---

### **4. Path Parameter Validation**
**Endpoint**: `GET /users/abc`
**Schema**:
```json
{
  "parameters": [
    {
      "name": "userId",
      "in": "path",
      "schema": {
        "type": "string",
        "pattern": "^[a-z0-9]{8,32}$"
      }
    }
  ]
}
```
**Response** (400 Bad Request):
```json
{
  "errors": [
    {
      "field": "userId",
      "message": "User ID must be 8+ alphanumeric characters",
      "code": "invalid_user_id"
    }
  ]
}
```

---

## **Related Patterns**

1. **[API Versioning]**
   - Pair validation schemas with versioned endpoints (e.g., `/v1/users`).
   - *Why*: Ensures backward compatibility when schemas evolve.

2. **[Rate Limiting]**
   - Combine with validation to reject malformed requests from rate-limited clients.
   - *Why*: Prevents abuse of validation endpoints.

3. **[OpenAPI/Swagger]**
   - Document schemas in OpenAPI specs for auto-generated clients/tools.
   - *Why*: Reduces manual error handling in SDKs.

4. **[Idempotency Keys]**
   - Use validation to ensure idempotent requests (e.g., deduplicate payments).
   - *Why*: Guarantees consistent responses for retryable operations.

5. **[CORS & Security Headers]**
   - Validate `Origin` headers and enforce security constraints (e.g., `Content-Security-Policy`).
   - *Why*: Mitigates CSRF and injection attacks.

6. **[Pagination]**
   - Validate `limit`, `offset`, and `sort` query parameters for pagination.
   - *Why*: Prevents performance issues (e.g., `limit=1000000`).

7. **[Field-Level Authorization]**
   - Validate access rights before exposing fields (e.g., hide `salary` for non-admin users).
   - *Why*: Enforces least-privilege principles.

8. **[Schema Registry]**
   - Centralize schemas (e.g., using [Confluent Schema Registry](https://developer.confluent.io/)).
   - *Why*: Simplifies versioning and cross-team consistency.

---

## **Best Practices**
- **Idempotency**: Design validation to handle retries safely (e.g., use `idempotency-key` headers).
- **Performance**: Cache validation schemas where possible (e.g., in-memory).
- **Localization**: Include translated error messages for global APIs.
- **Deprecation**: Use `deprecated: true` in schemas to flag upcoming changes.
- **Testing**: Unit-test validation edges (e.g., empty strings, edge-case numbers).