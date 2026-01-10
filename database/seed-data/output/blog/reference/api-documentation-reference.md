# **[Pattern] Writing Effective API Documentation: A Reference Guide**

---

## **1. Overview**
API documentation is the bridge between developers and the functionality an API provides. High-quality reference documentation ensures clarity, reduces onboarding friction, and minimizes errors by explicitly defining expected inputs, outputs, and behaviors. This guide outlines best practices for structuring, formatting, and presenting API documentation to maximize comprehension and usability.

---

## **2. Core Principles of API Documentation**

### **2.1 Be Scannable & Searchable**
Developers often skim documentation—prioritize clarity over verbosity:
- Use **short paragraphs** and **bullet points** for key details.
- Include a **table of contents (TOC)** for easy navigation.
- Use **headings (H2, H3)** to demarcate sections logically.
- Avoid walls of text; break up information with visual cues like **code blocks, icons, or callouts**.

### **2.2 Follow Standardized Formats**
Consistency reduces cognitive load. Adopt a **schema-based approach**:
- Use **REST conventions** (e.g., `GET /users/{id}`) or **OpenAPI/Swagger** for consistency.
- Label endpoints with **HTTP method, path, and summary**.
- Use **JSON/YAML schemas** for request/response bodies.

### **2.3 Document Everything**
Leave no ambiguity:
- **Endpoints**: Paths, methods (GET/POST/PUT/DELETE), and descriptions.
- **Parameters**: Query, path, and header parameters (include **types, required status, and examples**).
- **Responses**: HTTP status codes, success/failure payloads, and error examples.
- **Authentication**: Required tokens, scopes, and rate limits.
- **Examples**: Real-world request/response pairs.

### **2.4 Use Clear Language & Examples**
- Avoid jargon; explain terms if necessary.
- Provide **live examples** (e.g., `curl`, `Postman` snippets).
- Use **codelike formatting** for code blocks and **monospace font** in documentation.

### **2.5 Stay Updated & Versioned**
- Document **API versioning** (e.g., `/v1/users`).
- Mark **deprecated** methods with clear migration paths.
- Update documentation **before** API changes go live.

---

## **3. Schema Reference (Table Format)**

| **Component**       | **Description**                                                                 | **Example**                                                                 |
|---------------------|-------------------------------------------------------------------------------|---------------------------------------------------------------------------|
| **Endpoint**        | HTTP method + path (e.g., `GET /products?page=1`).                             | `GET /api/v1/users/{id}`                                                   |
| **Method**          | HTTP verb (GET, POST, etc.).                                                   | `POST`                                                                     |
| **Parameters**      | Input variables (path, query, headers).                                        | `query: "search_term"` (string, optional)                                 |
| **Auth Required**   | Required authentication (e.g., `Bearer Token`).                               | `Authorization: Bearer <token>`                                           |
| **Response (200)**  | Successful payload structure.                                                  | `{ "id": 123, "name": "Example" }`                                        |
| **Response (404)**  | Error payload format.                                                         | `{ "error": "Not Found", "code": 404 }`                                   |
| **Rate Limits**     | Request limits (e.g., 1000 reqs/min).                                          | "Limit: 1000 requests/minute"                                              |
| **Examples**        | Real-world request/response pairs.                                             | `curl -X GET "https://api.example.com/users/1" -H "Authorization: Bearer..."`|

---

## **4. Query Examples**

### **4.1 Successful Request**
**Endpoint**: `GET /api/v1/users/{id}`
**Method**: GET
**Headers**:
- `Authorization: Bearer abc123`
- `Accept: application/json`

**Query**:
```json
curl -X GET "https://api.example.com/api/v1/users/123"
```

**Response (200 OK)**:
```json
{
  "id": 123,
  "name": "Alice",
  "email": "alice@example.com",
  "created_at": "2023-01-15T10:00:00Z"
}
```

---

### **4.2 Failed Request (Invalid Token)**
**Endpoint**: `GET /api/v1/users/{id}`
**Method**: GET
**Headers**:
- `Authorization: Bearer invalid_token`

**Query**:
```json
curl -X GET "https://api.example.com/api/v1/users/123"
```

**Response (401 Unauthorized)**:
```json
{
  "error": "Invalid token",
  "code": 401,
  "message": "Authentication failed"
}
```

---

### **4.3 Paginated Search**
**Endpoint**: `GET /api/v1/products`
**Method**: GET
**Query Params**:
- `page=2` (numeric, required)
- `limit=10` (numeric, optional, default=10)

**Query**:
```json
curl -X GET "https://api.example.com/api/v1/products?page=2&limit=5"
```

**Response (200 OK)**:
```json
{
  "meta": {
    "page": 2,
    "limit": 5,
    "total": 42
  },
  "data": [
    {
      "id": 101,
      "name": "Product 101"
    },
    ...
  ]
}
```

---

## **5. Common Pitfalls & Fixes**
| **Pitfall**               | **Solution**                                                                 |
|---------------------------|-----------------------------------------------------------------------------|
| Missing **error examples** | Always include error payloads and HTTP status codes.                        |
| Unclear **parameter types** | Specify types (e.g., `string`, `number`, `boolean`) and validate examples.  |
| No **versioning**         | Use paths like `/v1/users` and document breaking changes.                   |
| **Outdated docs**         | Automate updates or flag deprecated endpoints in documentation.             |
| **Hidden auth**           | Explicitly state auth requirements (e.g., `Bearer Token`).                   |

---

## **6. Tools & Automation**
- **Static Documentation**: Markdown (GitHub Docs), Docusaurus, Sphinx.
- **Dynamic Documentation**: Swagger/OpenAPI (generated from code).
- **Testing**: Use tools like Postman or Insomnia to validate examples.
- **CI/CD**: Auto-generate docs from code (e.g., OpenAPI + Swagger UI).

---

## **7. Related Patterns**
- **[API Versioning](...)**: How to manage backward compatibility.
- **[Rate Limiting](...)**: Best practices for API throttling.
- **[Authentication Patterns](...)**: OAuth2, API keys, JWT.
- **[Error Handling](...)**: Standardized error responses.

---
**Last Updated**: [Date]
**Version**: [X.Y]

---
**Feedback**: [Link to feedback form] | **License**: [MIT/CC-BY-SA] | **Contributors**: [List]

---
**Key Takeaway**: Good API docs are **scannable, consistent, and example-rich**—prioritize clarity over completeness. Update docs **before** API changes to avoid confusion.