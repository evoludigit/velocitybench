# **[Pattern] REST Configuration Reference Guide**

---

## **1. Overview**
The **REST Configuration Pattern** defines a standardized way to expose and manage system-wide configurations via RESTful endpoints. It enables dynamic runtime adjustments, decouples configuration from application code, and supports multi-environment deployments. This pattern ensures configurations are versioned, secured, and validated before application use, promoting consistency across microservices, cloud applications, or hybrid architectures.

Key use cases include:
- **Dynamic feature toggles** (e.g., enabling/deactivating promotions).
- **Environment-specific overrides** (e.g., staging vs. production DB URLs).
- **Third-party integrations** (e.g., API keys for payment gateways).
- **A/B testing parameters** (e.g., experiment weights).

---

## **2. Schema Reference**

| Field          | Type       | Required | Description                                                                 | Example Value                     |
|----------------|------------|----------|-----------------------------------------------------------------------------|------------------------------------|
| `id`           | String     | Yes      | Unique identifier for the configuration entry.                              | `"app.max-retries"`               |
| `name`         | String     | Yes      | Human-readable name of the configuration.                                    | `"Max Retries for API Calls"`     |
| `value`        | String     | Yes      | The configuration value (stringified for all types).                        | `"5"` / `"true"` / `"[1, 2, 3]"` |
| `type`         | Enum       | Yes      | Data type of the value: `string`, `number`, `boolean`, `json`, or `enum`.    | `"number"`                        |
| `description`  | String     | No       | Additional context or usage notes.                                          | `"Max retries for HTTP calls."`   |
| `default`      | String     | No       | Fallback value if `value` is empty/unset.                                   | `"3"`                             |
| `environment`  | String     | No       | Target environment (e.g., `"prod"`, `"dev"`). Overrides global settings.    | `"prod"`                          |
| `metadata`     | Object     | No       | Extended attributes (e.g., `source: "dashboard"`, `lastUpdated: "2024-01-01"`). | `{"source": "dashboard"}`         |
| `schema`       | Object     | No       | Validation rules (e.g., `min`, `max`, `enum`).                              | `{"min": 0, "max": 10}`           |

---

## **3. Implementation Details**

### **3.1 Key Concepts**
1. **Configuration Store**:
   - Stores all configurations in a **key-value** format (e.g., Redis, database table, or distributed config service like Consul).
   - Supports **versioning** to track changes (e.g., `v1` vs. `v2`).

2. **Validation Layer**:
   - Enforces schema rules (e.g., reject non-numeric values for `type: number`).
   - Uses **JSON Schema** for definitions (example below).

3. **Change Propagation**:
   - **Event-driven updates**: Notify dependent services via **webhooks** or **message queues** (e.g., Kafka).
   - **Polling**: Services query configurations at startup/intervals (less efficient but simple).

4. **Security**:
   - **RBAC**: Role-based access control (e.g., `config:read`, `config:write`).
   - **Encryption**: Sensitive values (e.g., `type: secret`) are encrypted before storage.

---

### **3.2 Example JSON Schema for Validation**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "app.timeout": {
      "type": "number",
      "minimum": 0,
      "maximum": 30,
      "default": 10
    },
    "features.enable-logging": {
      "type": "boolean",
      "enum": [true, false]
    },
    "notifications.threshold": {
      "type": "array",
      "items": { "type": "number" },
      "minItems": 1,
      "maxItems": 5
    }
  },
  "required": ["app.timeout"]
}
```

---

### **3.3 Integration with Services**
- **Service Startup**:
  Fetch configurations during initialization (e.g., `GET /configs?service=order-service`).
  Example response:
  ```json
  {
    "configs": [
      { "id": "order.timeout", "value": "15", "type": "number" },
      { "id": "order.enabled", "value": "true", "type": "boolean" }
    ]
  }
  ```

- **Runtime Updates**:
  Trigger updates via `PATCH /configs/{id}`:
  ```json
  PATCH /configs/app.max-retries
  {
    "value": "7",
    "type": "number"
  }
  ```

---

## **4. API Endpoints**

| Method | Endpoint                     | Description                                                                 | Query Parameters               |
|--------|------------------------------|-----------------------------------------------------------------------------|---------------------------------|
| `GET`  | `/configs`                   | List all configurations (paginated).                                        | `type=string&limit=10`          |
| `GET`  | `/configs/{id}`              | Retrieve a single configuration.                                            | —                               |
| `POST` | `/configs`                   | Create a new configuration (requires validation).                          | —                               |
| `PATCH`| `/configs/{id}`              | Update an existing configuration (partial updates allowed).                | —                               |
| `DELETE`| `/configs/{id}`              | Delete a configuration (use with caution).                                  | —                               |
| `GET`  | `/configs/validate`          | Validate a configuration payload against the schema.                      | `payload={"id":"x","value":"10"}`|

---

## **5. Query Examples**

### **5.1 List All String-Type Configs**
```bash
GET /configs?type=string
```

Response:
```json
{
  "configs": [
    { "id": "app.version", "value": "1.2.0", "type": "string" },
    { "id": "user.timezone", "value": "America/New_York", "type": "string" }
  ]
}
```

---

### **5.2 Update a Configuration**
```bash
PATCH /configs/app.max-retries
{
  "value": "8",
  "type": "number",
  "metadata": { "changedBy": "admin-123" }
}
```

Response:
```json
{
  "id": "app.max-retries",
  "value": "8",
  "lastUpdated": "2024-01-15T09:30:00Z"
}
```

---

### **5.3 Validate a Configuration**
```bash
POST /configs/validate
{
  "payload": {
    "id": "order.threshold",
    "value": "50",
    "type": "number"
  }
}
```

Response (valid):
```json
{ "valid": true }
```

Response (invalid):
```json
{
  "valid": false,
  "errors": [
    { "field": "value", "message": "Must be <= 30" }
  ]
}
```

---

## **6. Related Patterns**

| Pattern                     | Description                                                                 | When to Use                          |
|-----------------------------|-----------------------------------------------------------------------------|--------------------------------------|
| **Config-as-Code**          | Store configurations in version control (e.g., Git).                         | Infrastructure-as-code (IaC) workflows. |
| **Feature Flags**           | Toggle features dynamically (subset of REST Config for boolean toggles).    | A/B testing or phased rollouts.      |
| **Service Mesh Config**     | Inject configurations via Istio/Linkerd sidecars.                           | Kubernetes-native deployments.       |
| **Environment Variables**   | Traditional approach (hardcoded in deployment).                             | Legacy monoliths or static setups.   |
| **Event-Driven Config**     | Push updates via events (e.g., Kafka topics) instead of polling.           | High-frequency updates (e.g., trading systems). |

---

## **7. Best Practices**
1. **Namespace Configurations**:
   Use prefixes (e.g., `service-a.`, `service-b.`) to avoid collisions.

2. **Immutable Writes**:
   Treat `PATCH` as immutable—append new versions instead of overwriting.

3. **Circuit Breakers**:
   Cache configurations locally with TTL to reduce network calls during outages.

4. **Audit Logging**:
   Log all changes (who, when, why) for compliance.

5. **Fallbacks**:
   Use `default` values gracefully (e.g., `default: "3"` for retries).

6. **Testing**:
   - Unit tests: Validate schema parsing.
   - Integration tests: Simulate API calls to the config service.

---
**Example Test Case (Python/Pytest):**
```python
def test_config_validation():
    payload = {"id": "invalid.number", "value": "abc", "type": "number"}
    response = client.post("/configs/validate", json={"payload": payload})
    assert response.json()["valid"] is False
    assert "Must be a number" in response.json()["errors"][0]["message"]
```

---
**See Also**:
- [REST API Design Best Practices](https://swagger.io/resources/articles/api-design/)
- [JSON Schema Reference](https://json-schema.org/understanding-json-schema/)