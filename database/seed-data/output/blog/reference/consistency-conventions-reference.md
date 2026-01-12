# **[Pattern] Consistency Conventions Reference Guide**

---

## **Overview**
The **Consistency Conventions** pattern ensures uniform behavior across a system, API, or application by defining and enforcing rules for naming, formatting, data structures, responses, and error handling. This pattern mitigates ambiguity, reduces cognitive load, and improves maintainability by standardizing expectations for developers and users.

Consistency conventions are particularly critical in distributed systems, microservices, and API-first architectures, where disparate teams or components interact. By implementing this pattern, you align system behavior with user expectations, reduce debugging time, and enable predictable automation (e.g., scripts, CI/CD pipelines).

---
## **Key Concepts**
Before implementation, understand these foundational principles:

| **Concept**               | **Description**                                                                                                                                                                                                 |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Semantic Uniformity**   | Consistent meanings for elements (e.g., HTTP status codes, field naming conventions).                                                                                                                             |
| **Syntactic Uniformity**  | Uniform formatting (e.g., JSON serialization, date/time formats, decimal precision).                                                                                                                         |
| **Behavioral Uniformity** | Identical handling of edge cases (e.g., null values, pagination).                                                                                                                                           |
| **Documentation Alignment** | All artifacts (API docs, code comments, examples) reflect the same conventions.                                                                                                                             |
| **Validation**           | Runtime enforcement of conventions (e.g., schema validation, linters).                                                                                                                                       |

---

## **Schema Reference**
Below are tables outlining key conventions across common domains.

### **1. HTTP API Conventions**
| **Category**         | **Convention**                                      | **Example/Notes**                                                                                                                                                     |
|----------------------|----------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Status Codes**     | Use standard HTTP status codes where possible.      | `200 OK` for success, `400 Bad Request` for client errors, `500 Internal Server Error` for server failures. Custom codes should be documented.                        |
| **Response Format**  | Always return JSON with a consistent `data` field.   | `{"status": "success", "data": {...}, "timestamp": "2024-05-20T12:00:00Z"}`                                                                                     |
| **Pagination**       | Use `offset`/`limit` or cursor-based pagination.   | `GET /api/users?limit=10&offset=20` (offset) or `GET /api/users?cursor=abc123` (cursor). Document which method is supported.                                             |
| **Error Responses**  | Include `error` object with `code`, `message`, and `details`. | `{"status": "error", "error": {"code": "VALIDATION_ERROR", "message": "Invalid field", "details": {"field": "email"}}`                                           |
| **Field Naming**     | Use `snake_case` for request/response fields.     | `user_name` instead of `userName`, except for legacy systems.                                                                                                       |
| **Content-Type**     | Default to `application/json`; specify for others.  | `Accept: application/json` in headers. For binary data, use `application/octet-stream`.                                                                              |

### **2. Data Structures**
| **Category**         | **Convention**                                      | **Example/Notes**                                                                                                                                                     |
|----------------------|----------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Nesting Depth**    | Limit JSON nesting to 3 levels.                    | Avoid deeply nested objects; flatten or use arrays where possible.                                                                                                      |
| **Boolean Values**   | Use `true`/`false` (not `1`/`0` or `"Y"`/`"N"`).   | `{"active": true}` instead of `{"active": "Y"}`.                                                                                                                       |
| **Date/Time**        | ISO 8601 format: `YYYY-MM-DDTHH:mm:ss.sssZ`.         | `2024-05-20T12:00:00.000Z` for timestamps. Localized formats are allowed but must be documented.                                                                     |
| **Decimal Precision**| Use 10 decimal places for monetary values.         | `999.9999999999` instead of `100` or `999.99`.                                                                                                                         |
| **Null Handling**    | Use `null` for absence of data; omit for optional fields. | `{"name": null}` for unknown, `{"name": undefined}` for omitted.                                                                                                       |
| **Arrays**           | Use `[]` for empty arrays; omit for optional arrays.| `{"tags": []}` instead of `{"tags": null}`.                                                                                                                             |

### **3. Naming Conventions**
| **Category**         | **Rule**                                           | **Example**                                                                                                                                                     |
|----------------------|----------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Endpoints**        | Use plural nouns for resource collections.         | `GET /api/users` instead of `GET /api/user`.                                                                                                                          |
| **Query Parameters** | Use `camelCase` for query params.                 | `?userId=123` instead of `?user_id=123`.                                                                                                                         |
| **Headers**          | Use `PascalCase` for custom headers.               | `X-Correlation-ID` instead of `x-correlation-id`.                                                                                                                   |
| **Environment Variables** | Use `UPPER_SNAKE_CASE`.       | `DB_HOST` instead of `dbHost`.                                                                                                                                       |
| **Variables**        | Use `camelCase` for local variables.               | `const userName = req.body.name;`                                                                                                                                  |
| **Constants**        | Use `UPPER_SNAKE_CASE`.                             | `const MAX_RETRIES = 3;`                                                                                                                                              |
| **Functions**        | Use `pascalCase` for function names.               | `function getUserDetails()` instead of `get_user_details()`.                                                                                                      |

### **4. Error Handling**
| **Category**         | **Convention**                                      | **Example**                                                                                                                                                     |
|----------------------|----------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Error Codes**      | Prefix with `ERR_` for internal use.              | `ERR_VALIDATION_FAILED`                                                                                                                                    |
| **Custom Errors**    | Extend base error classes (e.g., `CustomError`).   | `throw new CustomError("Invalid credentials", { code: "AUTH_001" });`                                                                                          |
| **Stack Traces**     | Omit sensitive data (e.g., passwords) in logs.      | Use environment variables or masking.                                                                                                                            |
| **Retryable Errors** | Include `retryAfter` in `429` responses.           | `{"status": "error", "error": {"code": "TOO_MANY_REQUESTS", "retryAfter": 30}}`                                                                                 |

### **5. Logging**
| **Category**         | **Convention**                                      | **Example**                                                                                                                                                     |
|----------------------|----------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Format**           | Use JSON for logs.                                  | `{"level": "INFO", "message": "User logged in", "userId": "123", "timestamp": "2024-05-20T12:00:00Z"}`                                                        |
| **Severity Levels**  | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `FATAL`.       | Avoid custom levels unless necessary.                                                                                                                          |
| **Sensitive Data**   | Never log PII (e.g., passwords, tokens).           | Use redaction or avoid logging entirely.                                                                                                                       |
| **Structured Fields**| Include `context` for operation details.         | `"context": {"endpoint": "/api/users", "method": "POST"}`                                                                                                       |

---

## **Implementation Details**
### **1. Tooling and Validation**
Enforce conventions at compile-time, runtime, and CI/CD stages:

| **Tool/Tech**        | **Purpose**                                                                 | **Example/Integration**                                                                                                                                 |
|----------------------|-----------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------|
| **JSON Schema**      | Validate request/response structures.                                      | Use OpenAPI/Swagger or JSON Schema Validator.                                                                                                           |
| **ESLint**          | Enforce code naming conventions.                                           | `.eslintrc.json`: `{ "rules": { "camelcase": "error" } }`                                                                                             |
| **Prettier**        | Auto-format code to match style guides.                                     | Integrate with VS Code or Git hooks.                                                                                                                   |
| **Husky + lint-staged** | Run linters on staged files.         | Skip linting for test files: `"*.test.js": null` in `.lintstagedrc`.                                                                                       |
| **API Gateway**     | Enforce request/response conventions.                                      | AWS API Gateway, Kong, or Apigee with request/response validation policies.                                                                             |
| **CI/CD Pipelines** | Fail builds on convention violations.                                      | GitHub Actions: `if [ "$(npm run lint)" != "success" ]; then exit 1; fi`                                                                            |

### **2. Documentation**
Keep documentation aligned with conventions:

| **Artifact**         | **Guideline**                                                                 |
|----------------------|------------------------------------------------------------------------------|
| **API Docs**         | Include examples for all endpoints.                                         |
| **Code Comments**    | Document why conventions are used (e.g., `"snake_case for DB compatibility"`). |
| **READMEs**          | List all conventions in a "Glossary" or "Conventions" section.               |
| **Changelogs**       | Highlight breaking changes to conventions.                                   |

### **3. Example Workflow**
1. **Design Phase**: Define conventions in a `CONVENTIONS.md` file.
2. **Development**: Use linters/formatting tools (e.g., ESLint, Prettier) locally.
3. **Testing**: Validate API responses with `Postman` or `Newman` against schemas.
4. **Deployment**: Enforce validation in the API gateway or gateway patterns.
5. **Monitoring**: Log violations (e.g., inconsistent date formats) in observability tools.

---

## **Query Examples**
### **Example 1: Paginated API Response**
--- **Request**
```http
GET /api/posts?limit=10&offset=0
Headers: Accept: application/json
```

--- **Expected Response**
```json
{
  "status": "success",
  "data": {
    "posts": [
      { "id": 1, "title": "Consistency Matters" },
      { "id": 2, "title": "API Best Practices" }
    ],
    "total": 100,
    "limit": 10,
    "offset": 0
  },
  "timestamp": "2024-05-20T12:00:00Z"
}
```
**Note**: `total` and `offset`/`limit` are always included.

---

### **Example 2: Error Handling**
--- **Request**
```http
POST /api/users
Headers: Content-Type: application/json
Body: { "email": "invalid" }
```

--- **Expected Response**
```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email format",
    "details": { "field": "email", "expected": "user@example.com" }
  },
  "timestamp": "2024-05-20T12:00:00Z"
}
```

---

### **Example 3: Date-Time Consistency**
--- **Request**
```http
GET /api/events?start=2024-05-20T00:00:00Z
```

--- **Expected Response Field**
```json
"event": {
  "id": 1,
  "timestamp": "2024-05-20T14:30:00.000Z"  // ISO 8601
}
```
**Note**: Clients should parse using `new Date("2024-05-20T14:30:00.000Z")`.

---

## **Related Patterns**
| **Pattern**               | **Relation to Consistency Conventions**                                                                                                                                                     |
|---------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **[API Gateway Pattern]** | Centralizes validation and enforces consistency across services.                                                                                                                          |
| **[Schema Registry]**     | Stores and validates data schemas (e.g., Avro, Protobuf) for consistency.                                                                                                             |
| **[Client-Side Validation]** | Ensures consistency before requests reach the server.                                                                                                                                 |
| **[Circuit Breaker]**     | Prevents cascading failures that could break consistency expectations.                                                                                                                 |
| **[OpenAPI/Swagger]**     | Documents conventions explicitly for tools and users.                                                                                                                                     |
| **[Feature Flags]**       | Gradually roll out changes while maintaining consistency in behavior.                                                                                                                 |
| **[Idempotency Keys]**    | Ensures repeated requests produce consistent results.                                                                                                                                   |

---

## **Anti-Patterns**
1. **Inconsistent Retries**: Allowing clients to retry on any error without clear guidance (use `retryAfter` for throttling).
2. **Over-Nesting**: Deeply nested JSON objects that violate the 3-level limit.
3. **Un documented Variations**: Custom headers or endpoints that deviate from conventions without explanation.
4. **Lazy Validation**: Skipping validation in "local" or "dev" environments.
5. **Ignoring Breaking Changes**: Changing conventions without deprecation warnings.

---
## **Further Reading**
- [RESTful API Design Best Practices](https://restfulapi.net/)
- [JSON Schema Specification](https://json-schema.org/)
- [OpenAPI Specification](https://spec.openapis.org/oas/v3.1.0)
- [Google’s Style Guide for JavaScript](https://google.github.io/styleguide/jsguide.html)

---
**Last Updated**: [Insert Date]
**Version**: [1.0.0]