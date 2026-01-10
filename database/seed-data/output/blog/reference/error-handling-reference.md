---

# **[Pattern] Reference Guide: API Error Handling Best Practices**

---

## **1. Overview**
API error handling ensures robust, maintainable, and user-friendly communication between clients and services. Following standardized practices improves debugging, reduces ambiguity, and prevents security risks like information leakage. This guide outlines best practices for designing consistent error responses, selecting appropriate HTTP status codes, providing actionable error details, and implementing consistent tracing via correlation IDs. Best practices vary slightly between API styles (REST, GraphQL, gRPC), but core principles remain applicable.

**Key Goals:**
- **Consistency** – Uniform structure and formatting for errors across all endpoints.
- **Actionability** – Clear, developer-friendly messages guiding recovery.
- **Security** – Avoid exposing sensitive details (e.g., stack traces) to clients.
- **Observability** – Enable debugging with trace correlation.
- **Compatibility** – Align with industry norms (e.g., [OpenAPI](https://swagger.io/specification/), [JSON:API](https://jsonapi.org/)) where applicable.

---

## **2. Schema Reference**
### **Standardized Error Response Structure**
All errors should adhere to the following schema. Differences arise in how errors are grouped (e.g., REST vs. GraphQL) but should maintain these fields where applicable.

| Field                | Type       | Description                                                                                                                                                                                                 | Required | Notes                                                                                                                                                                                                 |
|----------------------|------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **status**           | Integer    | HTTP status code (e.g., `400`, `404`, `500`).                                                                                                                                                              | Yes       | Must match the HTTP status code in the response header.                                                                                                                                                     |
| **error**            | String     | Human-readable, concise error title (e.g., `InvalidRequest`, `ResourceNotFound`).                                                                                                                      | Yes       | Should be consistent across similar errors. Use [HTTP status codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status) as a basis.                                                                    |
| **message**          | String     | Detailed explanation of the error, actionable where possible.                                                                                                                                        | Yes       | Avoid generic messages. Include specifics like missing fields or invalid values.                                                                                                                         |
| **code**             | String     | Optional machine-readable identifier for the error (e.g., `VALIDATION_FAILED`).                                                                                                                        | No        | Useful for client-side error handling logic. Align with business-specific error codes if applicable.                                                                                                  |
| **details**          | Object     | Nested structure for granular error context.                                                                                                                                                     | No        | Include validation errors, field-specific issues, or metadata as needed.                                                                                                                               |
| **correlationId**    | String     | Unique identifier for tracing the request across services.                                                                                                                                             | Yes       | Generated server-side; should be propagated in client requests for debugging.                                                                                                                             |
| **timestamp**        | ISO 8601   | When the error occurred (e.g., `2024-05-20T14:30:00Z`).                                                                                                                                                   | Yes       | Helps correlate logs and debugging sessions.                                                                                                                                                         |
| **links**            | Object     | Optional resources for resolving the error (e.g., API docs, support forums).                                                                                                                              | No        | Example: `{ "documentation": "https://example.com/docs/errors/400" }`.                                                                                                                                   |

---

### **Example Error Response (JSON)**
```json
{
  "status": 422,
  "error": "Unprocessable Entity",
  "message": "Validation failed for field 'email': must be a valid email address.",
  "code": "INVALID_EMAIL",
  "details": {
    "field": "email",
    "constraint": "Valid email required"
  },
  "correlationId": "abc123-xyz456",
  "timestamp": "2024-05-20T14:30:00Z"
}
```

---

## **3. HTTP Status Codes**
Use appropriate HTTP status codes to convey the nature of the error. Below are common use cases:

| Status Code | Description                                                                 | Example Scenario                                                                                     |
|-------------|-----------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| **400 Bad Request**      | Client-side error (e.g., malformed request).                              | Missing required field, invalid JSON syntax.                                                      |
| **401 Unauthorized**     | Authentication failed.                                                      | Invalid API key, expired token.                                                                        |
| **403 Forbidden**        | Authorization failed (user lacks permissions).                             | User doesn’t have access to the requested resource.                                               |
| **404 Not Found**        | Resource does not exist.                                                    | Non-existent endpoint or ID.                                                                        |
| **405 Method Not Allowed** | HTTP method not supported for the endpoint.                                | `PUT` request sent to an endpoint that only supports `POST`.                                        |
| **409 Conflict**         | Request conflicts with server state (e.g., duplicate data).                 | Attempting to create a user with an existing email.                                              |
| **422 Unprocessable Entity** | Valid request but semantically invalid (e.g., validation error).         | Invalid data format (e.g., wrong password strength).                                               |
| **429 Too Many Requests** | Rate limiting exceeded.                                                    | Client hitting API rate limits.                                                                  |
| **500 Internal Server Error** | Server-side error (avoid exposing stack traces).                       | Database connection failure, unhandled exception.                                                 |
| **503 Service Unavailable** | Temporary server downtime.                                              | Scheduled maintenance.                                                                             |

---

## **4. Implementation by API Style**
### **4.1 REST API**
- **Error Grouping**: Errors are returned in the **response body** (not HTML pages).
- **Field-Specific Validation**: Use the `details` object to list validation errors. Example:
  ```json
  {
    "status": 422,
    "error": "Unprocessable Entity",
    "message": "Validation errors found.",
    "details": [
      { "field": "name", "message": "Length must be between 3 and 50 characters." },
      { "field": "age", "message": "Must be a positive number." }
    ]
  }
  ```
- **Headers**: Include `X-Correlation-ID` for tracing:
  ```http
  X-Correlation-ID: abc123-xyz456
  ```
- **Pagination**: If errors occur in paginated responses, return them for all failed items (e.g., in GraphQL-like structures).

---

### **4.2 GraphQL API**
- **Error Grouping**: GraphQL errors are returned in the **top-level `errors` array**:
  ```json
  {
    "data": null,
    "errors": [
      {
        "message": "Field 'email' must be a valid email address.",
        "extensions": {
          "code": "INVALID_EMAIL",
          "path": ["user", "email"],
          "correlationId": "abc123-xyz456"
        }
      }
    ]
  }
  ```
- **Field-Level Errors**: Use `extensions` to include machine-readable details (e.g., `path` for the invalid field).
- **Correlation ID**: Pass via headers or GraphQL variables:
  ```graphql
  query CreateUser($input: UserInput!) {
    createUser(input: $input) {
      user {
        id
      }
      errors {
        message
        path
      }
    }
  }
  ```

---

### **4.3 gRPC**
- **Error Grouping**: Use gRPC’s built-in status codes with custom error details in the `details` field:
  ```protobuf
  syntax = "proto3";
  message ValidationError {
    string field = 1;
    string message = 2;
  }
  service UserService {
    rpc CreateUser (UserInput) returns (UserOutput) {
      option (grpc.status = { code = INVALID_ARGUMENT });
    }
  }
  ```
- **HTTP-Style Errors**: Embed JSON errors in the `details` field:
  ```json
  {
    "@type": "type.googleapis.com/google.rpc.BadRequest",
    "fieldViolations": [
      { "field": "email", "description": "Invalid email address." }
    ]
  }
  ```

---

## **5. Best Practices**
### **5.1 Error Messages**
- **Be Specific**: Avoid generic messages like "Something went wrong." Instead:
  - Good: `"Invalid API key. Please verify your credentials."`
  - Bad: `"Authentication failed."`
- **Avoid Client-Side Logic Guessing**: Don’t rely on error codes alone; include clear messages.
- **Localization**: Support multiple languages where applicable (e.g., via `Accept-Language` header).

---

### **5.2 Security**
- **Never Expose Stack Traces**: Return generic `500` errors for server issues; log details internally.
- **Sanitize Data**: Avoid leaking sensitive info (e.g., passwords, internal IDs) in error messages.
- **Rate Limiting**: Combine `429` responses with `Retry-After` headers:
  ```http
  Retry-After: 30
  ```

---

### **5.3 Observability**
- **Correlation IDs**: Generate a unique ID for each request and include it in:
  - Response headers (`X-Correlation-ID`).
  - Logs (e.g., `correlationId=abc123-xyz456`).
  - Client requests (propagate via headers or cookies if needed).
- **Logging**: Log errors with:
  - Correlation ID.
  - HTTP method/endpoint.
  - User/Client IP (if applicable).
  - Stack trace (for server errors, stored separately).

---

### **5.4 Validation**
- **Preemptive Validation**: Validate input on the client *and* server. Return validation errors early (e.g., `400` for malformed data, `422` for semantic errors).
- **Example Validation Errors**:
  ```json
  {
    "status": 422,
    "error": "Invalid Request",
    "message": "Validation failed.",
    "details": [
      { "field": "age", "constraint": "Minimum 18 years required." },
      { "field": "password", "constraint": "Must be at least 8 characters." }
    ]
  }
  ```

---

### **5.5 Testing**
- **Mock Errors**: Test error responses in integration tests (e.g., using Postman/Newman or tools like [Pytest](https://docs.pytest.org/)).
- **Edge Cases**:
  - Invalid queries (e.g., SQL injection attempts).
  - Rate-limiting scenarios.
  - Authentication failures.

---

## **6. Query Examples**
### **6.1 REST: Successful Request**
```http
GET /users/123 HTTP/1.1
Host: api.example.com
Accept: application/json

HTTP/1.1 200 OK
Content-Type: application/json
X-Correlation-ID: def456-ghi789

{
  "id": "123",
  "name": "Alice"
}
```

---

### **6.2 REST: Validation Error**
```http
POST /users HTTP/1.1
Host: api.example.com
Content-Type: application/json

{
  "name": "Bob",
  "age": "thirty" // Invalid (should be number)
}

HTTP/1.1 422 Unprocessable Entity
Content-Type: application/json
X-Correlation-ID: abc123-xyz456

{
  "status": 422,
  "error": "Unprocessable Entity",
  "message": "Validation failed for field 'age'.",
  "details": {
    "field": "age",
    "constraint": "Must be a number."
  }
}
```

---

### **6.3 GraphQL: Field-Level Error**
```graphql
query CreateUser($input: UserInput!) {
  createUser(input: $input) {
    user {
      id
    }
    errors {
      message
      path
    }
  }
}
```

**Request Headers:**
```
Content-Type: application/json
X-Correlation-ID: def456-ghi789
```

**Response:**
```json
{
  "data": null,
  "errors": [
    {
      "message": "Field 'email' must be a valid email address.",
      "extensions": {
        "code": "INVALID_EMAIL",
        "path": ["input", "email"],
        "correlationId": "def456-ghi789"
      }
    }
  ]
}
```

---

### **6.4 gRPC: Custom Error**
**Request (`CreateUser`):**
```protobuf
{
  "name": "Charlie",
  "age": "invalid" // Invalid (should be number)
}
```

**Response:**
```json
{
  "code": 3, // INVALID_ARGUMENT
  "message": "Validation failed",
  "details": [
    {
      "@type": "type.googleapis.com/google.rpc.BadRequest",
      "fieldViolations": [
        { "field": "age", "description": "Must be a number." }
      ]
    }
  ]
}
```

---

## **7. Related Patterns**
1. **[Pattern] API Versioning](https://example.com/pattern-versioning)**
   - Align error formats across API versions to avoid breaking changes.
2. **[Pattern] Authentication & Authorization](https://example.com/pattern-auth)**
   - Handle `401`/`403` errors consistently with auth systems.
3. **[Pattern] Rate Limiting](https://example.com/pattern-rate-limiting)**
   - Use `429` errors with `Retry-After` headers for throttling.
4. **[Pattern] OpenAPI/Swagger Documentation](https://example.com/pattern-openapi)**
   - Document errors in your spec to help clients implement proper error handling.
5. **[Pattern] Logging & Distributed Tracing](https://example.com/pattern-tracing)**
   - Use correlation IDs to trace errors across microservices.

---

## **8. Further Reading**
- [HTTP Status Codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)
- [JSON:API Error Handling](https://jsonapi.org/format/#errors)
- [OpenAPI Error Schemas](https://swagger.io/specification/2-0/#error-object)
- [gRPC Status Codes](https://grpc.io/docs/guides/error/)

---
**Last Updated:** [Insert Date]
**Version:** [1.0]