---
# **[Pattern] API Versioning Strategies Reference Guide**
*Ensure backward compatibility while evolving APIs with structured versioning.*

---

## **Overview**
API versioning enables gradual migration of clients to new API features or breaking changes by isolating incompatible updates into distinct versions. Without versioning, a single API change could break all connected clients. This pattern provides structured ways to:
- Signal version compatibility via **URLs, headers, or query parameters**.
- Deprecate older versions while allowing controlled deprecation periods.
- Avoid **backward-incompatible changes** in production without disruptions.

Use this pattern when:
✅ Your API undergoes frequent updates (e.g., bug fixes, feature additions).
✅ You must support legacy clients while introducing new functionality.
✅ You want to future-proof APIs against unexpected client incompatibilities.

Avoid versioning when:
❌ Your API is **immutable** (e.g., stateless, read-only).
❌ Clients **cannot be updated** (e.g., embedded systems with no maintenance).
❌ Your architecture **natively supports schema evolution** (e.g., GraphQL).

---

## **Schema Reference**
| **Strategy**       | **Format**                          | **Use Case**                                      | **Pros**                                      | **Cons**                                      |
|--------------------|-------------------------------------|--------------------------------------------------|-----------------------------------------------|-----------------------------------------------|
| **URL Versioning** | `/v1/resource`, `/v2/resource`      | Simple, widely understood                       | Easy to implement; works with caching        | Hard to change version without breaking URLs   |
| **Header Versioning** | `Accept: application/vnd.api+json;version=1` | Fine-grained control over version per request   | Flexible; supports media-type variants         | Requires client-side version handling        |
| **Query Param**    | `?version=1`                        | Works with non-versioned endpoints              | Simple to add; backward-compatible           | Visible in logs; may clutter URLs              |
| **Content Negotiation** | Media type (`/resource;version=1`) | Resource-centric versioning                     | Clean URLs; aligns with HTTP standards        | Limited browser support                       |
| **GraphQL Schema Evolution** | New fields with `deprecated` tag    | Schema-first APIs                                | No versioned endpoints; elegant deprecation   | No backward-compatible breaking changes     |

---

## **Implementation Details**
### **1. Choose a Versioning Strategy**
- **URL Versioning**: Best for **semantic clarity** (e.g., `/v2/users`). Use when versioning is **global** (applies to all endpoints).
  ```http
  GET /v1/users
  ```
- **Header Versioning**: Best for **fine-grained control** (e.g., `Accept: application/vnd.company.api.v1+json`). Use when you need to **mix versions** in a single request.
  ```http
  Accept: application/vnd.company.api.v1+json
  ```
- **Query Parameter**: Best for **backward-compatibility** (e.g., `?version=1`). Avoid overuse as it can clutter requests.
  ```http
  GET /users?version=1
  ```
- **Content Negotiation**: Best for **RESTful APIs** (e.g., `/users;version=1`). Use if your server supports **media-type variants**.
  ```http
  GET /users;version=1
  ```
- **GraphQL**: Use **schema evolution** (add `deprecated: true` to fields) instead of versioned endpoints.
  ```graphql
  type User @deprecated(reason: "Use v2") {
    id: ID!
    legacyField: String
  }
  ```

---
### **2. Versioning Semantics**
- **Major.Minor.Patch**: Follow [SemVer](https://semver.org/) for version numbering (e.g., `v1.0.0`, `v2.1.0`).
  - **Major**: Breaking changes.
  - **Minor**: Backward-compatible additions.
  - **Patch**: Bug fixes without breaking changes.

- **Deprecation Policy**:
  - Announce deprecation **6+ months** before removal.
  - Provide **migration guides** for clients.
  - Use **header warnings** (e.g., `Deprecation-Warning: v1 will be removed in v3`).

---
### **3. Backend Implementation**
#### **Example: URL Versioning (Node.js/Express)**
```javascript
const express = require('express');
const app = express();

// Extract version from URL (e.g., /v1/users)
app.use((req, res, next) => {
  const versionMatch = req.path.match(/^\/v(\d+)/);
  if (versionMatch) {
    req.version = versionMatch[1];
  }
  next();
});

app.get('/v1/users', (req, res) => {
  // API v1 logic
});

app.get('/v2/users', (req, res) => {
  // API v2 logic (drop deprecated fields)
});
```

#### **Example: Header Versioning (Python/Flask)**
```python
from flask import Flask, request

app = Flask(__name__)

@app.route('/users')
def get_users():
    version = request.headers.get('Accept', '').split(';')[0]
    if 'version=2' in version:
        return {"data": get_v2_users()}
    else:
        return {"data": get_v1_users()}
```

---
### **4. Client-Side Considerations**
- **Automatic Versioning**: Clients should **default to the latest stable version** (e.g., `v1`).
- **Version Detection**: Use **feature flags** or **fallback mechanisms** for unsupported versions.
- **Logging**: Log version usage to monitor adoption (e.g., `"v1": 80%, "v2": 20%"`).

---
## **Query Examples**
### **1. URL Versioning**
```http
# Fetch users in v1
GET /v1/users
Host: api.example.com

# Fetch users in v2
GET /v2/users
Host: api.example.com
```
**Response (v1):**
```json
{
  "users": [
    {"id": 1, "name": "Alice", "legacy_field": "old"}
  ]
}
```

**Response (v2):**
```json
{
  "users": [
    {"id": 1, "name": "Alice", "new_field": "updated"}
  ]
}
```

---
### **2. Header Versioning**
```http
# Request v1 content
GET /users
Host: api.example.com
Accept: application/vnd.company.api.v1+json
```

**Response:**
```json
{
  "users": [{"id": 1, "name": "Alice", "legacy_field": "old"}]
}
```

```http
# Request v2 content
GET /users
Host: api.example.com
Accept: application/vnd.company.api.v2+json
```

**Response:**
```json
{
  "users": [{"id": 1, "name": "Alice", "new_field": "updated"}]
}
```

---
### **3. Query Parameter Versioning**
```http
# Force v1 response
GET /users?version=1
Host: api.example.com
```

**Response:**
```json
{
  "users": [{"id": 1, "name": "Alice", "legacy_field": "old"}]
}
```

```http
# Default to latest (v2)
GET /users
Host: api.example.com
```

**Response:**
```json
{
  "users": [{"id": 1, "name": "Alice", "new_field": "updated"}]
}
```

---
### **4. GraphQL Schema Evolution**
```graphql
# Query with deprecated field
query {
  user(id: 1) {
    id
    name
    legacyField  # Deprecated in v2
  }
}
```
**Response:**
```json
{
  "user": {
    "id": "1",
    "name": "Alice",
    "legacyField": "old"
  }
}
```

**Deprecated Warning in Schema:**
```graphql
type User {
  id: ID!
  name: String!
  legacyField: String @deprecated(reason: "Use updatedField instead")
  updatedField: String
}
```

---

## **Best Practices**
1. **Document All Versions**: Publish a **versioning guide** (e.g., `/docs/versioning`).
2. **Deprecate Gradually**: Use **deprecation headers** and **easter-egg warnings** (e.g., `Warning: v1 will be removed in 6 months`).
3. **Validate Versions**: Reject **unsupported versions** with a clear error (e.g., `406 Not Acceptable`).
4. **Monitor Adoption**: Track version usage to plan deprecations (e.g., Prometheus + Grafana).
5. **Avoid Version Proliferation**: Limit versions to **3 active at a time** (e.g., `v1`, `v2`, `v3`).

---
## **Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                          |
|---------------------------|---------------------------------------------------------------------------------|------------------------------------------|
| **[Backward Compatibility](...)** | Ensure new changes don’t break existing clients.                           | Always apply when versioning.            |
| **[Rate Limiting](...)**  | Control API usage per version/clients.                                       | High-traffic APIs with version skew.     |
| **[Feature Flags](...)**  | Gradually roll out changes without versioning.                               | A/B testing new features.                |
| **[API Gateway](...)**    | Route requests to versioned backends.                                        | Microservices with multiple versions.    |
| **[Deprecation Headers](...)** | Warn clients about upcoming deprecations.                         | Before removing a version.               |
| **[GraphQL Federation](...)** | Compose APIs without versioning (schema-first).                         | GraphQL-based architectures.             |

---
## **Common Pitfalls & Mitigations**
| **Pitfall**                          | **Mitigation**                                      |
|---------------------------------------|----------------------------------------------------|
| **Version Proliferation**             | Sunset old versions after 6+ months of inactivity.  |
| **Client Ignores Versioning**         | Use **content negotiation** or **406 errors**.      |
| **Breaking Changes in "Stable" Versions** | Enforce **SemVer**; avoid major changes in minor versions. |
| **No Deprecation Plan**               | Announce deprecations **6+ months in advance**.     |
| **URL Versioning in RESTful APIs**    | Prefer **headers** or **content negotiation**.      |

---
## **Further Reading**
- [IETF RFC 7231 (HTTP Semantics)](https://tools.ietf.org/html/rfc7231)
- [Semantic Versioning (SemVer)](https://semver.org/)
- [REST API Design Rule of Least Surprise](https://www.vinaysahni.com/best-practices-for-a-pragmatic-restful-api)
- [GraphQL Schema Evolution Guide](https://graphql.org/learn/schema/#schema-first)