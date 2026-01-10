# **[Pattern] API Migration Reference Guide**

---
## **1. Overview**
The **API Migration** pattern ensures seamless transition from an older API version to a newer one while minimizing downtime, client disruption, and data loss. This pattern is critical for maintaining backward compatibility during cloud services migrations, microservices updates, or when introducing breaking changes. Key strategies include **parallel operation**, **phased rollouts**, **versioning**, and **deprecation management**.

The pattern supports gradual adoption of new APIs without forcing clients to update immediately. It leverages strategies like:
- **Dual-write**: Writing to both old and new APIs temporarily.
- **Feature flags**: Conditionally routing requests to legacy or updated endpoints.
- **Canary deployments**: Slowly shifting traffic to the new API.
- **Rate limiting**: Preventing overload on the deprecated API.

By following this pattern, teams can mitigate risks associated with abrupt API changes, ensuring a controlled migration path for both internal systems and third-party integrations.

---

## **2. Schema Reference**

| **Component**               | **Description**                                                                                     | **Example Values/Notes**                                                                 |
|-----------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| **Migration Strategy**      | Defines how APIs coexist during transition.                                                         | `Parallel`, `Staggered`, `Big Bang` (avoid), `Phased`                                   |
| **Versioning**              | Version identifiers for APIs (e.g., URL paths, headers).                                           | `/v1/endpoint`, `/v2/endpoint`; Header: `X-API-Version: v2`                              |
| **Deprecation Policy**      | Rules for announcing and removing old endpoints.                                                    | **Deprecation Period:** 6 months before removal; **Notification:** 3-month heads-up     |
| **Dual-Write Mechanism**    | Logic to sync writes across old and new APIs.                                                        | Trigger on `POST /v1/users` → Write to `/v1/users` **and** `/v2/users`                   |
| **Request/Response Mapping**| Rules to transform payloads between old and new schemas.                                           | Legacy → New: Replace `oldField` with `newField`; Add `compatibilityMode: true` header. |
| **Rate Limiting**           | Controls traffic to deprecated endpoints.                                                           | Legacy API limit: 1000 requests/minute; New API: Unrestricted                            |
| **Feature Flags**           | Client-side flags to route requests to new APIs (e.g., via config or header).                      | `X-Feature-Flag: enableV2`; Client checks config before sending.                           |
| **Monitoring Metrics**      | Key metrics to track migration health.                                                              | **Success Rate:** % of requests resolved via new API; **Error Rate:** Legacy API failures. |
| **Rollback Plan**           | Steps to revert to the old API if issues arise.                                                      | Documented DB rollback SQL; Manual override flag for critical systems.                    |
| **Testing Strategy**        | Validation approach for parallel API operation.                                                      | **Unit Tests:** Mock both v1 and v2 endpoints; **Integration Tests:** Simulate live traffic.|
| **Cutover Timeline**        | Schedule for enabling/disabling APIs.                                                               | **Phase 1:** Legacy API read-only; **Phase 2:** Write-only; **Phase 3:** Deprecation.       |

---

## **3. Query Examples**

### **3.1 Enabling Parallel Operation**
**Scenario:** Gradually shift writes from `/v1/users` to `/v2/users` while maintaining read compatibility.

#### **Dual-Write Implementation (Backend Logic)**
```python
@app.route("/v1/users", methods=["POST"])
def create_user_v1(request):
    data = request.json
    # Transform legacy payload to new schema
    new_data = {
        "name": data["full_name"],  # Legacy → New field mapping
        "email": data["contact_email"],
        "legacy_fields": data  # Preserve legacy data for backward compatibility
    }
    # Write to new API (async if possible)
    create_user_v2(new_data)
    # Write to legacy API (synchronous)
    return write_to_legacy_api(data)
```

#### **Client-Side Feature Flag**
Clients check a config flag (e.g., environment variable or header) to decide which API to call:
```javascript
// Client-side logic to route requests
if (process.env.USE_API_V2 || request.headers["X-Feature-Flag"] === "enableV2") {
    await fetch("/v2/users", { method: "POST", body: newData });
} else {
    await fetch("/v1/users", { method: "POST", body: legacyData });
}
```

---

### **3.2 Deprecation and Cutover**
**Scenario:** Transition from read-only legacy API to full removal.

#### **Step 1: Announce Deprecation (Header Response)**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "data": { ... },
  "deprecation": {
    "status": "deprecated",
    "replacement": "/v2/endpoint",
    "deprecation_date": "2024-06-01",
    "action_required": true
  }
}
```

#### **Step 2: Enforce Read-Only (During Cutover)**
```python
@app.route("/v1/users/<id>", methods=["PUT"])
def update_user_v1_readonly(request):
    if current_date > DEPRECATION_DATE:
        raise PermissionError("PUT/DELETE operations disabled for v1")
    # Allow GET/HEAD only
    return get_user_v1(id)
```

#### **Step 3: Full Removal**
After monitoring, disable the legacy endpoint:
```nginx
# In nginx config (or equivalent proxy)
location /v1/users {
    return 410 Gone;
    error_page 410 =200 /legacy_error.html;
}
```

---

### **3.3 Canary Deployment (Traffic Shifting)**
**Scenario:** Gradually route 10% of traffic to the new API before full cutover.

#### **Backend Routing Logic**
```python
# Use a probabilistic or weighted approach
if random.random() < 0.1:  # 10% chance to use v2
    return call_v2_endpoint(request)
else:
    return call_v1_endpoint(request)
```

#### **Client-Side Canary Testing**
Clients may implement canary testing by routing a subset of requests to the new API:
```bash
# Example: Using curl with probabilistic routing
if [ $((RANDOM % 10)) -lt 1 ]; then
    curl -X POST -H "X-Feature-Flag: enableV2" /v2/users
else
    curl -X POST /v1/users
fi
```

---

## **4. Implementation Steps**

### **Step 1: Plan the Migration**
- **Audit Dependents:** Identify clients (internal/external) using the legacy API.
- **Define Cutover Phases:** Align with business cycles (e.g., off-peak hours).
- **Set Deprecation Timeline:** Follow [Semantic Versioning](https://semver.org/) guidelines (e.g., `v1` → `v2`).

### **Step 2: Implement Parallel Operation**
- **Add Versioning:** Use URL paths, headers, or query params (e.g., `?version=v2`).
- **Dual-Write Logic:** Ensure data consistency between APIs during the transition.
- **Transform Payloads:** Map legacy schemas to the new format (e.g., flatten nested objects).

### **Step 3: Monitor and Validate**
- **Track Usage:** Monitor API calls to legacy vs. new endpoints.
- **Error Tracking:** Alert on failures in the legacy API (e.g., 5xx errors).
- **Load Testing:** Simulate peak traffic to ensure no bottlenecks.

### **Step 4: Deprecate and Cutover**
- **Announce Deprecation:** Provide clear documentation and ETA for removal.
- **Enforce Read-Only:** Disable writes after a grace period.
- **Monitor Rollback Readiness:** Ensure backout plans are viable.

### **Step 5: Full Removal**
- **Disable Legacy Endpoints:** Update proxies/gateways (e.g., NGINX, API Gateway).
- **Update Documentation:** Remove references to the deprecated API.
- **Archive Legacy Data:** If needed, preserve historical data for compliance.

---

## **5. Query Examples (Full Workflow)**

### **Example 1: Legacy to New API Migration (CRUD)**
**Legacy API (`/v1/orders`):**
```http
POST /v1/orders
{
  "order_id": "ORD-123",
  "customer": {
    "id": 42,
    "name": "John Doe"
  },
  "items": [
    { "product": "Laptop", "quantity": 1 }
  ]
}
```

**New API (`/v2/orders`):**
```http
POST /v2/orders
{
  "order_id": "ORD-123",
  "customer_id": 42,
  "customer_name": "John Doe",
  "items": [
    { "sku": "LP-001", "quantity": 1 }
  ],
  "is_legacy": true  # Flag for transformation
}
```

**Dual-Write Backend Code:**
```python
def create_order_v1_to_v2(request):
    legacy_data = request.json
    # Transform to new schema
    new_data = {
        "order_id": legacy_data["order_id"],
        "customer_id": legacy_data["customer"]["id"],
        "customer_name": legacy_data["customer"]["name"],
        "items": [
            {
                "sku": item["product"].lower().replace(" ", "-"),  # Legacy → SKU mapping
                "quantity": item["quantity"]
            }
            for item in legacy_data["items"]
        ]
    }
    # Write to new API
    create_order_v2(new_data)
    # Write to legacy API (for backward compatibility)
    return write_to_legacy_api(legacy_data)
```

---

### **Example 2: Feature Flag Routing**
**Client Configuration:**
```ini
# .env file
USE_API_V2=true
```

**Client Code (JavaScript):**
```javascript
const apiEndpoint = process.env.USE_API_V2
    ? "/v2/users"
    : "/v1/users";

fetch(apiEndpoint, {
    method: "POST",
    headers: { "X-Feature-Flag": process.env.USE_API_V2 ? "enableV2" : "legacy" },
    body: JSON.stringify({ ... })
});
```

**Backend Handling:**
```python
@app.route("/users", methods=["POST"])
def handle_user_creation(request):
    if request.headers.get("X-Feature-Flag") === "enableV2":
        return create_user_v2(request.json)
    else:
        # Fallback to legacy
        return create_user_v1(request.json)
```

---

## **6. Common Pitfalls and Mitigations**

| **Pitfall**                          | **Mitigation Strategy**                                                                 |
|---------------------------------------|----------------------------------------------------------------------------------------|
| **Data Inconsency**                  | Use transactions or eventual consistency with idempotency keys.                        |
| **Client Non-Compliance**             | Provide clear migration guides; use feature flags to nudge adoption.                  |
| **Performance Overhead**              | Optimize dual-write with async operations or batching.                                 |
| **Undocumented Changes**              | Document all schema breaking changes in a changelog.                                    |
| **Rollback Failures**                 | Test rollback procedures in staging; use database snapshots for critical data.         |
| **Third-Party Dependencies**          | Notify partners of deprecation early; offer migration support.                         |

---

## **7. Related Patterns**

1. **API Versioning**
   - *When to use:* When introducing breaking changes without immediate client updates.
   - *Key Difference:* Focuses on **how** to manage versions (e.g., URLs, headers), while Migration addresses **when** to phase out old versions.

2. **Feature Toggles**
   - *When to use:* To gradually enable new API features without deploying new versions.
   - *Key Difference:* Toggles control **functionality**, while Migration controls **end-of-life**.

3. **Circuit Breaker**
   - *When to use:* To prevent legacy API overload during cutover.
   - *Key Difference:* Isolates failures; Migration manages the lifecycle of the API.

4. **Canary Analysis**
   - *When to use:* To safely test new APIs with a subset of traffic.
   - *Key Difference:* Focuses on **testing**, while Migration encompasses the full transition plan.

5. **Database Migration**
   - *When to use:* To sync schema changes between legacy and new APIs.
   - *Key Difference:* Handles **data model** changes; Migration handles **API contract** changes.

---
## **8. Further Reading**
- [REST API Versioning Best Practices](https://restfulapi.net/versioning/)
- [Feature Flags for API Migration](https://launchdarkly.com/blog/feature-flags-api-migration/)
- [Semantic Versioning 2.0.0](https://semver.org/)
- [Kindly API Documentation](https://kindlyapi.com/) (Example of phased API updates).