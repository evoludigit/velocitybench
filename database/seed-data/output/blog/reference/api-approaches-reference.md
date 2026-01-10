# **[Pattern] Api Approaches Reference Guide**

---

## **Title (H2)**
### **API Approaches Pattern: Choosing the Right Approach for Your API Design**

---

## **Overview**
The **API Approaches** design pattern defines how clients interact with an API, influencing scalability, maintainability, and user experience. This pattern outlines three primary approaches—**XML-RPC/JSON-RPC, REST (Representational State Transfer), and GraphQL**—each suited for different use cases. By understanding their trade-offs, developers can select an approach that aligns with system requirements (e.g., flexibility vs. performance). This guide provides technical details, implementation considerations, and best practices to help you choose and implement the right API approach.

---

## **Implementation Details**
### **1. Key Concepts**
| **Concept**         | **Description**                                                                                                                                                                                                 |
|----------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Statelessness**   | REST enforces statelessness (no server-side session storage), while JSON-RPC and GraphQL may retain session context.                                                                                     |
| **Resource Modeling** | REST organizes data as resources (e.g., `/users/{id}`), while JSON-RPC/GraphQL treats APIs as procedure calls or schema-driven queries.                                                                 |
| **Caching**         | REST leverages HTTP caching headers; JSON-RPC/GraphQL require custom implementation.                                                                                                                     |
| **Data Fetching**   | REST uses fixed endpoints; GraphQL allows dynamic query shaping; JSON-RPC supports ad-hoc requests.                                                                                                     |
| **Versioning**      | REST versions via URLs (`/v2/users`), JSON-RPC/GraphQL often use schema updates.                                                                                                                          |

---

### **2. Approach Breakdown**

#### **A. REST (Representational State Transfer)**
**Best for:** Scalable systems, caching-heavy applications, or when strict statelessness is required.

- **Core Principles:**
  - Uses HTTP methods (`GET`, `POST`, `PUT`, `DELETE`) to define operations.
  - Data is accessed via resources (e.g., `/products`).
  - Supports caching, versioning, and stateless interactions.

- **Pros/Cons:**
  | **Pros**                          | **Cons**                          |
  |-----------------------------------|-----------------------------------|
  - Caching-friendly                  | Over-fetching (unnecessary data)  |
  - Standardized (HTTP protocols)     | Under-fetching (manual pagination) |
  | Works well with CDNs              | Complex for nested queries        |

- **Implementation:**
  - Use **Hypermedia APIs** (e.g., HATEOAS) for dynamic navigation.
  - Leverage **OpenAPI/Swagger** for documentation.

---

#### **B. JSON-RPC (Remote Procedure Call)**
**Best for:** Legacy systems, internal tools, or when RPC-style requests are preferred.

- **Core Principles:**
  - Direct function calls over HTTP/JSON (e.g., `{ "method": "getUser", "params": { "id": 1 } }`).
  - Minimal structure; no resource modeling.

- **Pros/Cons:**
  | **Pros**                          | **Cons**                          |
  |-----------------------------------|-----------------------------------|
  - Simple for ad-hoc queries         | No built-in caching               |
  | Low boilerplate                   | Session-dependent (statefulness)  |
  | Supports binary data              | Less discoverable than REST       |

- **Implementation:**
  - Libraries: [`json-rpc`](https://www.npmjs.com/package/json-rpc) (Node.js), [`pyjsonrpc`](https://pypi.org/project/PyJsonRPC/).
  - Ensure **idempotency** for safety.

---

#### **C. GraphQL**
**Best for:** Flexible data retrieval, frontend-heavy apps, or microservices.

- **Core Principles:**
  - Single endpoint (`/graphql`) with customizable queries (e.g., `{ user(id: 1) { name, email } }`).
  - Uses a schema (SDL) to define data shapes.

- **Pros/Cons:**
  | **Pros**                          | **Cons**                          |
  |-----------------------------------|-----------------------------------|
  - Precise data fetching             | Steep learning curve              |
  - Real-time updates (subscriptions) | Performance overhead (N+1 queries) |
  | Unified API surface               | Less SEO-friendly than REST       |

- **Implementation:**
  - Schema Design: Use **Apollo Server** or **Hasura**.
  - Optimize with **batch queries** and **data loader**.

---

## **Schema Reference**
Compare core attributes of each approach in a scannable table:

| **Attribute**       | **REST**                          | **JSON-RPC**                      | **GraphQL**                      |
|---------------------|-----------------------------------|-----------------------------------|-----------------------------------|
| **Request Format**  | URL + HTTP method                | JSON payload                      | Query string                     |
| **Response Format** | JSON/XML (resource-based)        | JSON (RPC response)               | JSON (schema-mapped)             |
| **Versioning**      | URL paths (`/v1/users`)           | Schema updates                    | Schema updates                    |
| **Caching**         | HTTP headers (`Cache-Control`)    | None (custom)                     | Query-based (client-side)         |
| **Discovery**       | Endpoints via docs/swagger        | Limited (no standard discovery)   | Schema (SDL)                     |
| **Performance**     | Fast (cached)                     | Moderate (serial requests)        | Variable (query complexity)       |

---

## **Query Examples**

### **1. REST Example**
**Request:**
```http
GET /api/v1/users/42 HTTP/1.1
Accept: application/json
```

**Response:**
```json
{
  "id": 42,
  "name": "Alice",
  "email": "alice@example.com"
}
```

---

### **2. JSON-RPC Example**
**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "getUser",
  "params": { "id": 42 },
  "id": 1
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": { "name": "Alice", "email": "alice@example.com" },
  "id": 1
}
```

---

### **3. GraphQL Example**
**Request:**
```graphql
query {
  user(id: "42") {
    name
    email
    posts(count: true)
  }
}
```

**Response:**
```json
{
  "data": {
    "user": {
      "name": "Alice",
      "email": "alice@example.com",
      "posts": { "count": 5 }
    }
  }
}
```

---

## **Best Practices**
1. **REST:**
   - Use **resource naming** (plural nouns, `/users`).
   - Document with **OpenAPI/Swagger**.
   - Implement **HATEOAS** for dynamic links.

2. **JSON-RPC:**
   - Add **error handling** (e.g., `-32601: Invalid Request`).
   - Avoid deep nesting for performance.

3. **GraphQL:**
   - Limit **query depth** (N+1 issues).
   - Use **persisted queries** to prevent injection.
   - Optimize with **fragments** for reuse.

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------|
| **Pagination**            | Handle large datasets with `?page=1&limit=10` (REST) or cursor-based (GraphQL).                     |
| **OAuth 2.0**             | Secure APIs with token-based authentication.                                                       |
| **Event-Driven APIs**     | Use WebSockets or Server-Sent Events (SSE) for real-time updates.                                   |
| **Microservices**         | REST/GraphQL for service-to-service communication; JSON-RPC for legacy integration.                |
| **API Gateways**          | Route requests (e.g., Kong, Apigee) for load balancing, rate-limiting, and request transformation. |

---

## **Conclusion**
Choosing an **API approach** depends on your system’s needs:
- **REST** for scalability and caching.
- **JSON-RPC** for simplicity and legacy systems.
- **GraphQL** for flexible, frontend-driven data fetching.

Evaluate trade-offs (performance, complexity, discoverability) and align with your architecture’s goals. For hybrid systems, consider **REST for public APIs + GraphQL for internal tools**.

---
**Further Reading:**
- [REST API Design Best Practices](https://restfulapi.net/)
- [GraphQL Fundamentals](https://graphql.org/learn/)
- [JSON-RPC Spec](https://www.jsonrpc.org/specification)