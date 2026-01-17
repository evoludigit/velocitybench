# **[Pattern] REST Profiling Reference Guide**

---
## **Overview**
REST Profiling is a design pattern that enhances RESTful APIs by allowing clients to dynamically customize endpoint behavior through lightweight, extensible metadata called **profiles**. This pattern enables granular control over resource representations, query parameters, and response formatting without altering the core API schema. Profiles are typically defined as small, self-contained JSON/YAML payloads that clients attach during requests, enabling features such as:
- **Filtering & Selecting Fields** (e.g., `projection` or `fields` parameters)
- **Sorting & Pagination** (e.g., `sort`, `limit`, `offset`)
- **Condition-Based Responses** (e.g., `if-match`, `if-none-match`)
- **Extension Mechanisms** (e.g., custom metadata for third-party integrations)

Profiles are particularly useful in microservices architectures where multiple clients (e.g., mobile apps, dashboards, IoT devices) consume the same API but require different response formats or access levels. This pattern adheres to REST principles while improving flexibility and reducing over-fetching or under-fetching of data.

---

## **Key Concepts**
### **1. Profile Definition**
A *profile* is a structured metadata object sent in the request body or headers to modify API behavior. Profiles are **idempotent** (same profile yields consistent results) and **versioned** to support backward compatibility.

#### **Core Components of a Profile:**
| Component          | Purpose                                                                 | Example Value                     |
|--------------------|-------------------------------------------------------------------------|-----------------------------------|
| `@type`            | Specifies profile version/specification (e.g., `http://example.com/profiles/v1`). | `"@type": "http://example.com/profiles/v1/fields"` |
| `fields`           | Selects specific resource fields to include/exclude.                     | `"fields": ["id", "name"]`        |
| `sort`             | Defines sorting criteria (asc/desc).                                   | `"sort": [{"field": "createdAt", "order": "desc"}]` |
| `limit`/`offset`   | Controls pagination (deprecated in favor of `page`).                   | `"limit": 10, "offset": 20`       |
| `page`             | Pagination via page size/number.                                        | `"page": {"size": 10, "number": 2}| |
| `if-match`         | Conditional request (e.g., ETag comparison).                           | `"if-match": "W/\"abc123\""`      |
| `extensions`       | Vendor-specific metadata (e.g., analytics IDs).                        | `"extensions": {"analytics": "xyz"}| |

---

### **2. Profile Delivery Mechanisms**
Profiles can be attached via:
- **Request Body (POST/PUT):** Ideal for complex profiles.
  ```http
  POST /api/orders HTTP/1.1
  Content-Type: application/json

  {
    "@type": "http://example.com/profiles/v1/fields",
    "fields": ["orderId", "customer.name"]
  }
  ```
- **Query Parameters:** For simple cases (e.g., `fields=name,email`).
  ```http
  GET /api/users?fields=name,email
  ```
- **Headers:** Custom headers (e.g., `X-Profile: "..."`).

---

### **3. Server-Side Processing**
Servers must:
1. **Validate Profiles:** Reject malformed or unsupported profiles (HTTP 400).
2. **Apply Profiles:** Transform responses dynamically (e.g., filter fields via a middleware like [JSONata](https://www.jsonata.org/)).
3. **Log Profiles:** Track usage for monitoring/analytics.
4. **Cache Profiles:** Optimize performance for repeated requests.

**Example Middleware Flow:**
```
Request → Profile Validator → Field Filter → Paginator → Response
```

---

### **4. Profile Versioning**
To avoid breaking changes:
- Use **URIs** in `@type` (e.g., `v1`, `v2`).
- Document deprecated profiles with `deprecated: true`.
- Provide **migration paths** (e.g., deprecate `limit/offset` in favor of `page`).

---

## **Schema Reference**
Below is a reference table for common profile schemas. Custom schemas can extend these using `extensions`.

| Schema Type               | Description                                                                 | Required Fields               | Example Payload                          |
|---------------------------|-----------------------------------------------------------------------------|-------------------------------|------------------------------------------|
| **Fields Profile**        | Selects/includes specific resource fields.                                  | `@type`, `fields`             | `{"@type": "fields", "fields": ["id", "name"]}` |
| **Sort Profile**          | Defines sorting criteria.                                                   | `@type`, `sort`               | `{"@type": "sort", "sort": [{"field": "date", "order": "asc"}]}` |
| **Pagination Profile**    | Manages pagination (deprecated in favor of `page`).                         | `@type`, `limit`, `offset`    | `{"@type": "pagination", "limit": 10, "offset": 50}` |
| **Page Profile**          | Modern pagination (replaces `limit/offset`).                                | `@type`, `page.size`, `page.number` | `{"@type": "page", "page": {"size": 10, "number": 3}}` |
| **Conditional Profile**   | Conditional requests (e.g., ETag).                                        | `@type`, `if-match`           | `{"@type": "conditional", "if-match": "W/\"etag\""}` |
| **Extension Profile**     | Vendor-specific metadata (e.g., analytics).                                 | `@type`, `extensions`         | `{"@type": "extensions", "extensions": {"analytics": "track123"}}` |

---

## **Query Examples**
### **1. Basic Field Selection**
**Request:**
```http
POST /api/users HTTP/1.1
Content-Type: application/json

{
  "@type": "http://example.com/profiles/v1/fields",
  "fields": ["id", "email", "createdAt"]
}
```
**Response:**
```json
{
  "id": 123,
  "email": "user@example.com",
  "createdAt": "2023-01-01"
}
```

### **2. Sorting + Pagination**
**Request:**
```http
POST /api/products HTTP/1.1
Content-Type: application/json

{
  "@type": "http://example.com/profiles/v1/page",
  "page": {
    "size": 5,
    "number": 2
  },
  "sort": [
    {"field": "price", "order": "desc"}
  ]
}
```
**Response:**
```json
{
  "items": [
    {"id": 1, "price": 99.99},
    {"id": 2, "price": 89.99}
  ],
  "page": {"size": 5, "number": 2, "total": 100}
}
```

### **3. Conditional Request (ETag)**
**Request:**
```http
POST /api/orders HTTP/1.1
Content-Type: application/json

{
  "@type": "http://example.com/profiles/v1/conditional",
  "if-match": "W/\"etag-value\""
}
```
**Response (200 if ETag matches):**
```json
{
  "orderId": "abc123",
  "status": "shipped"
}
```

### **4. Extension for Analytics**
**Request:**
```http
POST /api/events HTTP/1.1
Content-Type: application/json

{
  "@type": "http://example.com/profiles/v1/extensions",
  "extensions": {
    "analytics": {
      "campaignId": "spring2024",
      "userAgent": "MobileApp/1.0"
    }
  }
}
```

---

## **Implementation Considerations**
### **1. Server-Side Libraries**
- **Node.js:** Use [`express-profile`](https://www.npmjs.com/package/express-profile) or custom middleware.
- **Java (Spring):** Implement a [`Filter`](https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/web/filter/Filter.html) or [`WebFilter`](https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/web/server/WebFilter.html).
- **Python (FastAPI):** Use [`Pydantic`](https://fastapi.tiangolo.com/tutorial/body-items/) for profile validation.
- **Go:** Use [`gorilla/mux`](https://github.com/gorilla/mux) for middleware.

### **2. Client Libraries**
- **JavaScript:** `fetch` with `body: JSON.stringify(profile)`.
- **Python:** `requests.post(url, json=profile)`.
- **Mobile (iOS/Android):** Use `JSON` serialization in HTTP body.

### **3. Security**
- **Input Validation:** Reject profiles with unexpected fields (e.g., SQL injection via `fields`).
- **Rate Limiting:** Profile processing should be throttled to prevent abuse.
- **Authentication:** Profile metadata should not override access controls.

### **4. Testing**
- **Unit Tests:** Validate profile parsing/serialization.
- **Integration Tests:** Test endpoints with different profiles.
- **Load Testing:** Ensure scalability under high profile usage.

---

## **Related Patterns**
| Pattern               | Description                                                                 | When to Use                          |
|-----------------------|-----------------------------------------------------------------------------|---------------------------------------|
| **HATEOAS**           | Dynamically links resources in responses.                                   | When clients need self-discovery.     |
| **Filtering**         | Standard query parameters (`?fields=name`).                                 | Simple field selection.               |
| **GraphQL**           | Single endpoint for complex queries.                                        | When clients need ad-hoc data.        |
| **OpenAPI (Swagger)** | Standardizes API documentation.                                            | Documentation-driven development.    |
| **Pagination**        | Standardized `limit/offset` or `page`.                                      | Large datasets.                       |
| **Event Sourcing**    | Stores state changes as events.                                             | Audit trails or replayability.        |

---

## **Common Pitfalls & Solutions**
| Pitfall                          | Solution                                                                 |
|-----------------------------------|---------------------------------------------------------------------------|
| **Overly Complex Profiles**       | Limit nesting depth (e.g., max 3 levels).                                |
| **Server Overhead**               | Cache profile results for repeated requests.                              |
| **Versioning Chaos**              | Use semantic versioning (e.g., `v1`, `v2`) and deprecation warnings.      |
| **Missing Documentation**         | Auto-generate OpenAPI docs from profile schemas.                          |
| **Client Confusion**              | Provide examples in API docs and SDKs.                                   |

---
## **Further Reading**
1. [IETF Draft: REST API Profiles](https://datatracker.ietf.org/doc/draft-ietf-restapiregistry-profiles/)
2. [JSONata for Dynamic Data Transformation](https://www.jsonata.org/)
3. [Spring Boot Profile Filters](https://spring.io/guides/gs/accessing-data-rest/)
4. [FastAPI Custom Body Parsing](https://fastapi.tiangolo.com/tutorial/body-items/)