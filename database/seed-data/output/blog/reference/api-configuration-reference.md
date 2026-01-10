# **[Pattern] API Configuration Reference Guide**

---

## **Overview**
The **API Configuration** pattern defines structured, centralized mechanisms for managing API behavior, endpoints, and runtime parameters. This pattern ensures APIs are configurable without requiring code changes, enabling dynamic adjustments for environments (dev/stage/prod), feature flags, or adaptive behavior. Key use cases include **environment-specific settings**, **rate limiting**, **authentication policies**, **timeout configurations**, and **payload validation rules**, reducing hard-coded dependencies and improving maintainability.

API Configuration decouples application logic from infrastructure, enabling teams to enforce policies (e.g., GDPR compliance) or tweak performance (e.g., caching) via externalized configurations. It is critical in microservices architectures where APIs may interact with multiple services, each requiring tailored rules.

---

## **Implementation Details**

### **Key Concepts**
1. **Configuration Sources**
   - *Static*: Application-specific JSON/YAML files (e.g., `api-config.yaml`).
   - *Dynamic*: Externalized via:
     - Environment variables (e.g., `DATABASE_TIMEOUT=30s`).
     - Registry services (e.g., Consul, HashiCorp Vault).
     - API Gateway configurations (e.g., Kong, Apigee).
     - Cloud-managed services (e.g., AWS Parameter Store, Azure App Configuration).

2. **Configuration Types**
   - **Runtime**: Adjustable without redeployment (e.g., throttling limits).
   - **Schema Validation**: Rules for input/output payloads (e.g., OpenAPI/Swagger specs).
   - **Service-Specific**: Endpoint URLs, authentication tokens, or SDK configurations.

3. **Versioning**
   - Schema versioning (e.g., `config-v1.json`) to avoid breaking changes.
   - Backward compatibility: Deprecate old keys while supporting legacy clients.

4. **Reloading Mechanisms**
   - Polling-based (e.g., refresh every 5 minutes).
   - Event-driven (e.g., Kubernetes ConfigMaps on watch).

5. **Security**
   - Encrypt sensitive data (e.g., TLS for cloud storage).
   - Least-privilege access (e.g., IAM roles for API keys).

6. **Fallbacks**
   - Default values for missing configurations.
   - Graceful degradation if external sources fail.

---

## **Schema Reference**

| **Field**               | **Type**       | **Description**                                                                 | **Example**                          | **Required** |
|-------------------------|----------------|---------------------------------------------------------------------------------|--------------------------------------|--------------|
| `version`               | String         | Schema version (e.g., `v1.2.0`).                                                  | `"v1"`                               | Yes          |
| `base_url`              | String         | Root API endpoint URL.                                                          | `"https://api.example.com/v1"`        | Yes          |
| `endpoints`             | Object[]       | List of configured endpoints.                                                    | `{...}` (see below)                  | Yes          |
| `authentication`        | Object         | Authentication rules (e.g., JWT, API keys).                                     | `{ "type": "bearer", "timeout": 60 }` | No           |
| `rate_limits`           | Object[]       | Rate-limiting policies per endpoint.                                             | `[{ "path": "/users", "limit": 100 }]`| No           |
| `timeouts`              | Object         | Request/response timeouts (ms).                                                 | `{ "connect": 5000, "read": 10000 }` | No           |
| `payload_validation`    | Boolean/Object | Enable OpenAPI schema validation or custom rules.                               | `true` or `{ "schema": "openapi.json" }`| No           |
| `logging`               | Object         | Logging configuration (e.g., level, format).                                   | `{ "level": "info", "format": "json" }`| No           |
| `fallback_settings`     | Object         | Defaults for missing configurations.                                             | `{ "timeout": 30000 }`               | No           |

### **Endpoints Schema**
| **Field**       | **Type**       | **Description**                                                                 | **Example**                          | **Required** |
|-----------------|----------------|-------------------------------------------------------------------------------|--------------------------------------|--------------|
| `path`          | String         | API path (e.g., `/users`).                                                    | `"/v2/users"`                        | Yes          |
| `method`        | String         | HTTP method (e.g., `GET`, `POST`).                                             | `"GET"`                              | Yes          |
| `auth_required` | Boolean        | Require authentication.                                                        | `true`                               | No           |
| `timeout`       | Integer        | Endpoint-specific timeout (ms).                                                | `8000`                               | No           |
| `retry_policy`  | Object         | Retry rules (e.g., maxAttempts, delay).                                       | `{ "maxAttempts": 3, "delay": 1000 }`| No           |
| `custom_headers`| Object         | Headers to inject (e.g., `Accept: application/json`).                           | `{ "X-API-Key": "${env.API_KEY}" }`  | No           |

---

## **Query Examples**

### **1. Static Configuration (JSON)**
`api-config.json`:
```json
{
  "version": "v1",
  "base_url": "https://api.example.com",
  "endpoints": [
    {
      "path": "/health",
      "method": "GET",
      "timeout": 2000
    }
  ],
  "authentication": {
    "type": "api_key",
    "header": "X-API-Key"
  }
}
```
**Usage**:
Load in your application:
```javascript
const config = require('./api-config.json');
console.log(config.base_url); // "https://api.example.com"
```

---

### **2. Dynamic Configuration (Environment Variables)**
Set in `.env`:
```env
API_BASE_URL=https://api.example.com
RATE_LIMIT_USERS=100
```
**Usage (Python)**:
```python
import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    api_base_url: str
    rate_limit_users: int

config = Settings()
print(config.api_base_url)  # "https://api.example.com"
```

---

### **3. Schema Validation (OpenAPI)**
`validation-schema.json`:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "userId": { "type": "string", "pattern": "^[a-f0-9]{24}$" }
  },
  "required": ["userId"]
}
```
**Application Integration**:
Validate requests:
```typescript
import Ajv from 'ajv';
import schema from './validation-schema.json';

const ajv = new Ajv();
const validate = ajv.compile(schema);

if (!validate({ userId: "invalid" })) {
  throw new Error("Invalid payload");
}
```

---

### **4. Cloud-Based Configuration (AWS Parameter Store)**
**AWS CLI**:
```bash
aws ssm put-parameter --name "/api/config/base_url" --value "https://api.example.com" --type "SecureString"
```
**Application Fetch (Node.js)**:
```javascript
const { SSMClient, GetParameterCommand } = require("@aws-sdk/client-ssm");

const client = new SSMClient({ region: "us-east-1" });
const command = new GetParameterCommand({
  Name: "/api/config/base_url",
  WithDecryption: true,
});

const response = await client.send(command);
console.log(response.Parameter.Value); // "https://api.example.com"
```

---

## **Related Patterns**
1. **API Gateway**
   - Use gateways (e.g., Kong, Apigee) to manage configurations centrally via plugins (e.g., rate limiting, JWT validation).

2. **OpenAPI/Swagger**
   - Define schemas in OpenAPI specs to validate payloads dynamically. Integrate with tools like Swagger Editors for visual configuration.

3. **Feature Flags**
   - Combine with API Configuration to toggle endpoints/behaviors (e.g., `enabled: false` for beta features).

4. **Circuit Breaker**
   - Configure fallback paths (e.g., `fallback_endpoint: "/fallback/users"`) for degraded service states.

5. **Service Mesh (Istio, Linkerd)**
   - Apply configurations via sidecars (e.g., retries, timeouts) without code changes.

6. **Config Maps (Kubernetes)**
   - Deploy configurations as Kubernetes ConfigMaps for containerized APIs, syncing with environment-specific values.

7. **Canary Releases**
   - Use configurations to route traffic to canary versions (e.g., `traffic_percentage: 10`).

---
**Note**: For production, validate configurations on startup and log changes via tools like [Sentry](https://sentry.io/) or [Datadog](https://www.datadoghq.com/). Use circuit breakers (e.g., [Hystrix](https://github.com/Netflix/Hystrix)) to handle misconfigurations gracefully.