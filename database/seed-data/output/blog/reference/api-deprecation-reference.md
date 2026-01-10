# **[Pattern] API Deprecation & Sunset Policies Reference Guide**

---

## **Overview**
APIs are subject to change as technology evolves, business requirements shift, or technical debt accumulates. The **API Deprecation & Sunset Policies** pattern ensures a controlled, client-friendly transition by:
- **Deprecating** endpoints or features before removal to allow gradual adoption of alternatives.
- Providing **clear timelines** to prevent last-minute disruptions.
- Offering **migration guidance** (e.g., updated SDKs, documentation, or example code).
- Enforcing **sunset deadlines**, after which the API is permanently removed.

This pattern minimizes client downtime and maintains API stability by balancing backward compatibility with forward progress.

---

## **Core Concepts**
### **1. Deprecation Phases**
| Phase | Description | Client Expectation |
|-------|-------------|--------------------|
| **Announcement** | Endpoint marked as deprecated in API docs and metadata (e.g., `X-API-Deprecated: true` header). | Clients should audit usage; no functional changes. |
| **Deprecation Warning** | Deprecated endpoint still works but returns warnings (e.g., HTTP `426 Upgrade` or custom header). | Clients must migrate but can still use the endpoint. |
| **Sunset (Deprecation Enforced)** | Endpoint is disabled for new requests; existing requests may fail or require migration. | Clients must migrate to an alternative. |
| **Permanent Removal** | Endpoint is deleted from the API contract. | Clients using the deprecated endpoint will encounter errors. |

---
### **2. Deprecation Signals**
To signal deprecation to clients, use:
| Signal Type | Example Implementation | Purpose |
|-------------|-------------------------|---------|
| **HTTP Headers** | `X-API-Deprecated: "true; migration-path=/v2/users; sunset=2025-06-01"` | Machine-readable warning in responses. |
| **API Documentation** | Marked with a `Deprecated` tag in OpenAPI/Swagger specs. | Human-readable context for developers. |
| **Response Warnings** | JSON payload with `warnings` array: `{ "deprecated": { "endpoint": "/v1/users", "migration": "/v2/users" } }`. | Inline guidance in API responses. |
| **SDK Changes** | Deprecated methods/parameters in client libraries are flagged or removed. | Smooth migration for SDK users. |

---
### **3. Sunset Deadlines**
- **Public Commitment**: Announce sunset dates *at least 6 months* in advance (12 months for high-impact APIs).
- **Grace Periods**: Allow a short buffer (e.g., 1–2 weeks) after sunset for exceptions (e.g., legacy integrations).
- **Communication Channels**:
  - API changelogs (e.g., `/docs/changelog`).
  - Email updates to registered clients.
  - Deprecation notices in API responses (e.g., `Deprecation-Warning` header).

---
### **4. Migration Support**
Provide clear migration paths:
- **Direct Replacements**: Map deprecated endpoints to new ones (e.g., `/v1/users → /v2/users`).
- **Deprecation Roadmaps**: Publish a timeline of affected endpoints [here](link).
- **Example Code**: Offer snippets for transitioning requests (e.g., cURL, Python).
- **Deprecation Status Page**: Track live deprecation state (e.g., `/api/status/deprecated`).

---

## **Schema Reference**
### **1. Deprecation Metadata (HTTP Headers)**
| Header | Description | Example Value |
|--------|-------------|---------------|
| `X-API-Deprecated` | Flags deprecated endpoints. | `true; migration-path=/v2/users; sunset=2025-06-01; reason=performance` |
| `Deprecation-Warning` | Human-readable warning. | `This endpoint will sunset on 2025-06-01. Use /v2/users instead.` |
| `Retry-After` | For rate-limited deprecated endpoints. | `2025-06-01T00:00:00Z` |

---
### **2. Response Body (Deprecation Warning)**
```json
{
  "status": "success",
  "data": { "users": [...] },
  "warnings": [
    {
      "code": "DEPRECATED_ENDPOINT",
      "path": "/v1/users",
      "migration": "/v2/users",
      "sunset": "2025-06-01",
      "message": "This endpoint will be removed. Update your requests."
    }
  ]
}
```

---
### **3. OpenAPI/Swagger Deprecation Tag**
```yaml
paths:
  /v1/users:
    get:
      tags: [Deprecated]
      deprecated: true
      description: "Deprecated on 2023-12-01. Use /v2/users instead."
      parameters:
        - $ref: '#/components/parameters/DeprecationWarning'
```

---

## **Query Examples**
### **1. Fetching Deprecated Endpoint (with Warning)**
```http
GET /v1/users HTTP/1.1
Host: api.example.com

HTTP/1.1 200 OK
X-API-Deprecated: true; migration-path=/v2/users; sunset=2025-06-01
Deprecation-Warning: This endpoint will sunset on 2025-06-01. Use /v2/users.

{
  "data": [...],
  "warnings": [{"code": "DEPRECATED_ENDPOINT", ...}]
}
```

---
### **2. Checking Deprecation Status (Proactive Check)**
```http
GET /api/status/deprecated HTTP/1.1
Host: api.example.com

HTTP/1.1 200 OK
Content-Type: application/json

{
  "endpoints": [
    {
      "path": "/v1/users",
      "status": "deprecated",
      "sunset": "2025-06-01",
      "migration": "/v2/users",
      "severity": "high"
    }
  ]
}
```

---
### **3. Migrating to New Endpoint**
```http
GET /v2/users HTTP/1.1
Host: api.example.com

HTTP/1.1 200 OK
Content-Type: application/json

{
  "data": [...],
  "warnings": []
}
```

---

## **Implementation Steps**
### **1. Announce Deprecation**
- Update OpenAPI/Swagger specs with `deprecated: true`.
- Add `X-API-Deprecated` header to responses.
- Publish a changelog entry (e.g., [/docs/changelog#deprecated](link)).

### **2. Enforce Deprecation Warning**
- Modify backend to return warnings in responses.
- Log deprecation warnings for monitoring.

### **3. Set Sunset Deadline**
- Calculate a fair deadline (e.g., 6–12 months post-announcement).
- Notify clients via email/Slack channels.

### **4. Enforce Sunset**
- Disable endpoint for new requests (return `426 Upgrade` or custom error).
- Allow existing requests to complete (with warnings).

### **5. Remove Permanently**
- Delete endpoint from API contract.
- Redirect old requests to 404 or migration path.

---

## **Error Handling**
| Scenario | HTTP Status | Response Example |
|----------|-------------|------------------|
| **Deprecated Endpoint Accessed Post-Sunset** | `426 Upgrade` or `404` | `{ "error": "DEPRECATED", "migration": "/v2/users" }` |
| **Legacy Request During Grace Period** | `200` (with warning) | Includes `Deprecation-Warning` header. |
| **Client Ignores Sunset** | `404` (permanent removal) | No migration path offered. |

---

## **Related Patterns**
1. **[API Versioning]**
   - Complementary pattern for managing concurrent API versions alongside deprecations.
   - *Link*: [API Versioning Reference Guide](#).

2. **[Rate Limiting & Throttling]**
   - Useful for managing degraded access to deprecated endpoints before removal.
   - *Link*: [Rate Limiting Patterns](#).

3. **[Change Data Capture (CDC)]**
   - Helps clients sync data from deprecated to new endpoints during migration.
   - *Link*: [CDC for APIs](#).

4. **[Deprecation Notification Webhooks]**
   - Automatically notify clients when an endpoint they use is deprecated.
   - *Link*: [Event-Driven API Patterns](#).

5. **[Backward Compatibility Guidelines]**
   - Ensures deprecated endpoints maintain stability until migration is complete.
   - *Link*: [Backward Compatibility Reference](#).

---
## **Best Practices**
1. **Communicate Early**: Announce deprecations *before* implementation if possible.
2. **Provide Alternatives**: Always map deprecated endpoints to replacements.
3. **Monitor Usage**: Track usage of deprecated endpoints to gauge readiness.
4. **Support Legacy Clients**: Offer a grace period for clients unable to migrate.
5. **Document Everything**: Include deprecation notes in API docs, SDKs, and changelogs.
6. **Test Migrations**: Validate new endpoints handle deprecated requests gracefully.
7. **Avoid "Zombie" APIs**: Remove deprecated endpoints *completely* after sunset to prevent technical debt.

---
## **Anti-Patterns**
❌ **Silent Removal**: Dropping endpoints without warning causes client failures.
❌ **No Migration Path**: Leaving clients stranded with no alternative.
❌ **Overly Long Deprecation Periods**: Encourages procrastination and technical debt.
❌ **Breaking Changes in Deprecated Endpoints**: Invalidates client assumptions mid-deprecation.
❌ **Ignoring Client Feedback**: Not addressing migration challenges from users.

---
## **Tools & Libraries**
| Tool | Purpose |
|------|---------|
| **OpenAPI/Swagger** | Annotate deprecated endpoints in API specs. |
| **Spring Boot (Java)** | `@Deprecated` annotations + custom filters for headers. |
| **Express (Node.js)** | Middleware to inject `Deprecation-Warning` headers. |
| **Postman/Newman** | Test deprecated endpoint responses. |
| **Datadog/New Relic** | Monitor usage of deprecated endpoints. |
| **GitHub/GitLab** | Track deprecation-related PRs/issues. |

---
## **Example Workflow**
1. **2023-06-01**: Announce `/v1/users` will deprecate on **2025-06-01** (via changelog and headers).
   ```http
   GET /v1/users
   X-API-Deprecated: true; migration-path=/v2/users; sunset=2025-06-01
   ```
2. **2024-12-01**: Deprecated endpoint returns warnings:
   ```json
   { "warnings": [{"code": "DEPRECATED_ENDPOINT", ...}] }
   ```
3. **2025-06-01 (Sunset)**: New requests return `426 Upgrade`.
   ```http
   GET /v1/users
   HTTP/1.1 426 Upgrade
   Retry-After: 2025-07-01
   ```
4. **2025-07-01**: Endpoint removed entirely (404).

---
## **Further Reading**
- [IETF RFC 7231 (HTTP Semantics)](https://datatracker.ietf.org/doc/html/rfc7231) (for `426 Upgrade` status).
- [Google’s Deprecation Policy](https://developers.google.com/analytics/devguides/collection/protocol/v1/deprecations).
- [AWS API Deprecation Process](https://aws.amazon.com/developer/api/).
- [Microsoft’s Deprecation Guidelines](https://learn.microsoft.com/en-us/azure/architecture/guide/technology-choices/api-deprecation).