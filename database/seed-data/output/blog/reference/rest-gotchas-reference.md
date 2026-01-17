# **[Pattern] REST "Gotchas" Reference Guide**

---

## **Overview**
REST (Representational State Transfer) is a widely adopted architectural style for designing networked APIs, but its simplicity can sometimes lead to subtle pitfalls—what we call **"REST Gotchas."** These are common issues that arise from misinterpreting HTTP semantics, resource design, or error handling, leading to inconsistent or inefficient APIs. This guide outlines critical "gotchas" to avoid, ensuring robust and maintainable API implementations.

Key focus areas include:
- **Resource Naming & URIs** (ambiguity, over/under-posting)
- **HTTP Methods & Semantics** (incorrect `PUT`/`PATCH` usage, idempotency)
- **Status Codes & Errors** (misusing 2xx/4xx/5xx, missing details)
- **Response Formats** (inconsistent payloads, versioning)
- **Performance Pitfalls** (over-fetching, inefficient pagination)

---

## **Schema Reference**

| **Gotcha Category**       | **Symptom**                                                                 | **Correct Approach**                                                                                                                                                                                                 | **Example Fix**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| **Resource Naming**       | URIs are too complex or inconsistent.                                       | Keep URIs hierarchical, use nouns, avoid query parameters in paths (RFC 6570).                                                                                                                                | ❌ `/users/get?filter=active` → ✅ `/users/active`                                                   |
| **HTTP Method Misuse**    | Using `GET` for side effects (e.g., password reset).                        | Use `POST` for non-idempotent actions, `GET` only for data retrieval.                                                                                                                                          | ❌ `GET /reset-password?token=abc` → ✅ `POST /reset-password` (with token in body)               |
| **Idempotency Violations**| Repeating `PUT`/`POST` produces different results.                         | Ensure `PUT`/`POST` are idempotent; use ETags for `PUT` consistency checks.                                                                                                                              | ❌ `PUT /users/1` (fails if user doesn’t exist) → ✅ `PUT /users/1` (creates if missing or updates) |
| **Over-Posting**          | Clients must know all fields to update.                                     | Use `PATCH` with partial updates and `application/merge-patch+json` (RFC 7396).                                                                                                                           | ❌ `PUT /users/1` (full body) → ✅ `PATCH /users/1` (`{"name": "Alice"}`)                          |
| **Under-Posting**         | Clients can’t infer required fields from the API.                           | Document required fields explicitly; use `required` in OpenAPI/Swagger.                                                                                                                                        | ❌ No docs → ✅ `{ "id": "string", "name": "string (required)" }`                                   |
| **Status Code Confusion** | Using `200 OK` for errors (e.g., "Resource not found").                    | Use `4xx` for client errors, `5xx` for server errors; include details in `4xx` responses.                                                                                                                   | ❌ `200 OK` + `{"error": "Not found"}` → ✅ `404 Not Found` + `{"detail": "..."}`                  |
| **Missing Headers**       | Lack of `ETag`, `Last-Modified`, or `Accept` support.                      | Leverage caching headers (`ETag`, `Cache-Control`) and media-type negotiation (`Accept`).                                                                                                                    | ❌ No `ETag` → ✅ `ETag: "xyz123"` (for conditional requests)                                       |
| **Versioning Mismanagement** | No clear versioning strategy (e.g., `/v1/users` vs. headers).         | Use URI-based or header-based versioning (`Accept: application/vnd.company.v1+json`).                                                                                                                        | ❌ `/users` → ✅ `/v1/users` or `Accept: vnd.company.v1+json`                                         |
| **Pagination Abuse**      | Poor pagination (e.g., `LIMIT/OFFSET` for large datasets).                 | Prefer cursor-based pagination or keyset pagination for scalability.                                                                                                                                          | ❌ `GET /users?limit=1000&offset=5000` → ✅ `GET /users?before=cursor`                           |
| **HATEOAS Violations**    | Links in responses are static or missing.                                  | Use HATEOAS to dynamically link related resources (e.g., `links: { "self", "next" }`).                                                                                                                     | ❌ Hardcoded links → ✅ `{ "links": { "next": "/users?page=2" } }`                                |
| **CORS Misconfiguration**  | `Access-Control-Allow-Origin` is too permissive or missing.               | Restrict origins to trusted domains; include headers (`Access-Control-Expose-Headers`).                                                                                                                      | ❌ `*` (open) → ✅ `Access-Control-Allow-Origin: https://client.com`                              |
| **Rate Limiting Oversight**| No rate-limiting or unclear headers (`X-RateLimit-*`).                     | Implement rate-limiting and expose limits in headers.                                                                                                                                                          | ❌ No limits → ✅ `X-RateLimit-Limit: 100`, `X-RateLimit-Remaining: 98`                          |
| **Schema Evolution**      | Breaking changes in response schemas without warnings.                     | Use backward-compatible changes (add fields, not remove); warn via `Deprecation` header.                                                                                                                | ❌ Remove `oldField` → ✅ Add `deprecated: true` and `Deprecation: oldField` header               |

---

## **Query Examples**

### **1. Correct vs. Incorrect Resource URIs**
| **Incorrect**               | **Correct**                     | **Explanation**                                                                                     |
|------------------------------|----------------------------------|-----------------------------------------------------------------------------------------------------|
| `/products/categories/1/items`| `/products/1/items`              | Avoid nesting resources; categories should be a separate endpoint.                                  |
| `/api/v2/users`              | `/users` (with `Accept` versioning)| Prefer URI-based versioning only if necessary; otherwise use headers.                              |

---

### **2. HTTP Method Usage**
| **Scenario**                  | **Incorrect**               | **Correct**                     | **Why**                                                                                         |
|-------------------------------|------------------------------|----------------------------------|-------------------------------------------------------------------------------------------------|
| **Update Partial Data**       | `PUT /users/1` (full payload) | `PATCH /users/1` (`{ "name": "Bob" }`) | `PATCH` allows partial updates; `PUT` should replace the entire resource.                  |
| **Create Resource**           | `POST /users` (with `id` in body) | `POST /users` (no `id`)         | `POST` should not include the `id`; servers generate IDs.                                      |
| **Delete Non-Existent Resource** | `DELETE /users/999` (returns 404) | `DELETE /users/999` (returns 204) | `404` suggests the resource exists but was not found; `204` confirms deletion.             |

---

### **3. Status Codes**
| **Scenario**                  | **Incorrect**               | **Correct**                     | **Details**                                                                                     |
|-------------------------------|------------------------------|----------------------------------|-------------------------------------------------------------------------------------------------|
| **Resource Not Found**        | `200 OK` + `{"error": "Not found"}` | `404 Not Found` + `{ "detail": "User not found" }` | `404` is semantically correct; details help clients handle errors.                          |
| **Conflict (e.g., duplicate email)** | `400 Bad Request` | `409 Conflict` + `{ "code": "duplicate_email" }` | `409` indicates a logical conflict, not a client error.                                   |
| **Server Error (Database Down)** | `500 Internal Server Error` (no details) | `500 Internal Server Error` + `{ "message": "Database unavailable" }` | Include machine-readable errors (e.g., `error.code`).                                       |

---

### **4. Pagination (Bad vs. Good)**
| **Bad Practice**               | **Good Practice**                     | **Reason**                                                                                     |
|----------------------------------|-----------------------------------------|-------------------------------------------------------------------------------------------------|
| `GET /users?limit=1000&offset=5000` | `GET /users?before=cursor`             | `LIMIT/OFFSET` is inefficient for large datasets; cursor-based pagination scales better.     |
| No `next` link in response      | `{ "links": { "next": "/users?cursor=abc" } }` | HATEOAS helps clients navigate pagination dynamically.                                      |

---

### **5. Versioning**
| **Bad Versioning**            | **Good Versioning**                | **Explanation**                                                                               |
|---------------------------------|-------------------------------------|-----------------------------------------------------------------------------------------------|
| `/users` (no versioning)       | `/v1/users`                         | Explicit versioning prevents breaking changes.                                               |
| Only URI versioning (`/v1`)     | URI + header versioning (`Accept: vnd.api.v1+json`) | Hybrid approach allows future flexibility.                                                 |

---

### **6. Error Responses**
| **Bad Error Response**         | **Good Error Response**             | **Improvements**                                                                             |
|----------------------------------|---------------------------------------|-----------------------------------------------------------------------------------------------|
| `400 { "message": "Invalid input" }` | `400 { "errors": [{ "field": "email", "message": "Invalid format" }] }` | Structured errors help clients validate input.                                            |
| No `error.code`                  | `{ "code": "invalid_email", "message": "..." }` | Machine-readable codes enable automated handling.                                          |

---

## **Related Patterns**
To address REST gotchas effectively, combine this pattern with:
1. **[API Versioning](https://www.codacy.com/blog/api-versioning-strategies/)**
   - Structured versioning (URI, headers, or response media types) to avoid breaking changes.
2. **[HATEOAS (Hypermedia as the Engine of Application State)](https://www.martinfowler.com/articles/richardsonMaturityModel.html)**
   - Dynamically link resources in responses to reduce client-side coupling.
3. **[Idempotency Keys](https://tools.ietf.org/html/rfc7252#section-7.2)**
   - Use `Idempotency-Key` headers for `POST`/`PUT` to ensure retries succeed.
4. **[OpenAPI/Swagger](https://swagger.io/specification/)**
   - Document schemas, examples, and error responses upfront to prevent ambiguity.
5. **[Caching Strategies](https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching)**
   - Leverage `ETag`, `Cache-Control`, and `Last-Modified` to optimize performance.

---
**Key Takeaway**: REST gotchas often stem from misapplying HTTP standards or ignoring edge cases. By adhering to these guidelines—**clear URIs, proper HTTP methods, semantic status codes, and client-friendly errors**—you can design APIs that are consistent, scalable, and maintainable. Always validate API behavior with tools like **Postman**, **Swagger UI**, or **cURL** to catch gotchas early.