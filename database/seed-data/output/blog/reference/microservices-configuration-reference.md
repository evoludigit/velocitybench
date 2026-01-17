# **[Pattern] Microservices Configuration: Reference Guide**

---
## **Overview**
Microservices Configuration is a design pattern that ensures **decoupled, dynamic, and scalable configuration** for microservices. Unlike monolithic applications, microservices often require **environment-specific, versioned, and service-specific configurations** that must be:
- **Externally managed** (avoiding code changes for deployments).
- **Securely distributed** (sensitive data not hardcoded).
- **Easily updated** (zero-downtime reconfiguration).
- **Validated & versioned** (backward compatibility, rollback support).

This pattern defines a **centralized, API-driven configuration system** (e.g., ConfigMaps, Spring Cloud Config, Consul KV, or custom solutions) that services fetch at runtime. Best suited for **containerized, multi-team, and polyglot architectures**, it balances **control with flexibility** while ensuring consistency across deployments.

---
## **Key Concepts**
| **Term**               | **Definition**                                                                                                                                                                                                 | **Example**                                                                                     |
|-------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| **Configuration Source** | External store (DB, file system, API, key-value DB) where config data resides.                                                                                                                                          | Kubernetes ConfigMap, Spring Cloud Config Server, Consul KV, AWS Parameter Store.                |
| **Configuration Profile** | A logical grouping of config values (e.g., `dev`, `prod`, `staging`). Helps manage environment-specific settings.                                                                                           | `{"profile": "prod", "database": {"url": "prod-db.example.com"}}`                              |
| **Configuration Label**  | A tag or metadata field to further categorize configs (e.g., `service=order-service`, `team=finance`).                                                                                              | `{"label": "order-service","version": "v2"}`                                                   |
| **Configuration Sync**   | Mechanisms to propagate changes (polling, event-driven via Webhooks/PubSub, or long-polling).                                                                                                             | Consul’s watch API, Spring Cloud Bus for event-driven updates.                                   |
| **Configuration Validation** | Rules to ensure configs are syntactically correct before deployment (e.g., schema validation, minimum/maximum values).                                                                                 | JSON Schema validation, OpenAPI specs for API configs.                                           |
| **Configuration Rollback** | Ability to revert to a previous version of configs (often tied to CI/CD pipelines).                                                                                                                              | Kubernetes ConfigMap revisions, Git-based config versioning (e.g., GitOps with ArgoCD/Flux).    |
| **Secrets Management**   | Secure storage and rotation of sensitive data (passwords, API keys) using **separate systems** (e.g., HashiCorp Vault, AWS Secrets Manager).                                                            | `{"db_password": "[Vault:/secrets/db/prod]"}`.                                                  |
| **Local Overrides**      | Temporarily overriding configs for testing/dev without modifying the central store.                                                                                                                           | Environment variables (`--spring.config.activate.on-profile=local`).                          |
| **Dynamic Reload**       | Services hot-reload configs without restarting (e.g., via signal handlers or change streams).                                                                                                        | Spring `@RefreshScope`, Kubernetes liveness probes triggering reloads.                           |

---

## **Schema Reference**
Below is a **standardized schema** for microservices configuration. Implementations may vary slightly (e.g., Spring Cloud uses YAML/JSON, Kubernetes uses key-value pairs).

| **Field**               | **Type**       | **Description**                                                                                                                                                                                                 | **Example Value**                                                                                     |
|-------------------------|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| `metadata`              | Object         | Metadata about the configuration (id, version, labels, createdAt).                                                                                                                                               | `{"id": "db-config-v1", "version": "1.0", "labels": {"team": "backend"}}`                          |
| `profile`               | String[]       | Deployment environment(s) this config applies to.                                                                                                                                                          | `["dev", "staging"]`                                                                                  |
| `service`               | String         | Name of the microservice consuming this config.                                                                                                                                                            | `"payment-service"`                                                                                  |
| `source`                | String         | Where the config originates (e.g., `git`, `vault`, `database`).                                                                                                                                             | `"git://config-repo/main/db-configs"`                                                              |
| `data`                  | Object/Array   | Key-value pairs or nested structures defining the config.                                                                                                                                                     | `{"database": {"url": "postgres://user:pass@host:5432/db", "poolSize": 10}, "logging": { ... }}` |
| `secrets`               | Object[]       | References to secrets (never store plaintext).                                                                                                                                                               | `[{"key": "DB_PASSWORD", "path": "vault/secrets/db/password"}]`                                    |
| `dependencies`          | String[]       | Other configs this config depends on (for ordering/validation).                                                                                                                                                 | `["db-common-v1", "feature-flags-v2"]`                                                              |
| `validationSchema`      | String/Object  | Link to a schema (JSON Schema, OpenAPI) or embedded rules.                                                                                                                                                   | `"#/schemas/db-config.json"` or `{"poolSize": {"min": 1, "max": 50}}`                                     |
| `lastUpdated`           | Timestamp      | When the config was last modified.                                                                                                                                                                            | `"2023-10-15T14:30:00Z"`                                                                             |
| `deprecated`            | Boolean        | Flag indicating if this config is obsolete.                                                                                                                                                                      | `false`                                                                                               |
| `fallback`              | Object         | Default values if a key is missing.                                                                                                                                                                           | `{"timeout": {"default": 30000}}`                                                                     |

---
### **Example Config (JSON)**
```json
{
  "metadata": {
    "id": "order-service-v1",
    "version": "1.0",
    "labels": {"service": "order-service", "team": "commerce"}
  },
  "profile": ["prod", "staging"],
  "data": {
    "service": {
      "timeout": 5000,
      "retryPolicy": { "maxAttempts": 3, "backoffFactor": 2 }
    },
    "database": {
      "url": "postgres://user:{{secrets.DB_PASSWORD}}@db.example.com:5432/orders",
      "poolSize": 20
    }
  },
  "secrets": [
    {"key": "DB_PASSWORD", "provider": "vault", "path": "/secrets/db/password"}
  ],
  "dependencies": ["feature-flags-v2"],
  "validationSchema": "https://config-schemas.example.com/order-service-v1.json",
  "lastUpdated": "2023-10-15T14:30:00Z"
}
```

---
## **Implementation Patterns**
### **1. Centralized Configuration Server**
Use a **dedicated service** (e.g., Spring Cloud Config, HashiCorp Consul, or a custom REST API) to host configs. Microservices **poll or subscribe** to changes.

**Pros:**
- Single source of truth.
- Easy to audit and version.

**Cons:**
- Polling can introduce latency.
- Scalability challenges with high-volume configs.

**Example (Spring Cloud Config):**
```yaml
# application.yml
spring:
  cloud:
    config:
      uri: http://config-server:8888
      profile: prod
      label: main
```

---
### **2. GitOps-Based Configuration**
Store configs in a **Git repository** (e.g., GitHub, GitLab) and sync them to runtime using tools like **ArgoCD, Flux, or Spinnaker**.

**Pros:**
- Version control and rollback.
- Immutable history.

**Cons:**
- Latency in applying changes.
- Requires GitOps tooling.

**Example (GitOps Workflow):**
1. Commit config to repo.
2. ArgoCD detects change and syncs to Kubernetes ConfigMaps.
3. Services reload configs via Kubernetes watch.

---
### **3. Distributed Key-Value Store**
Use a **lightweight KV store** (e.g., Consul, etcd, DynamoDB) for **low-latency, high-available** configs.

**Pros:**
- Fast reads/writes.
- Built-in health checks.

**Cons:**
- No native versioning (unless extended).
- Eventual consistency risks.

**Example (Consul KV):**
```bash
# Write config
curl -X PUT -d '{"timeout":5000}' http://consul:8500/v1/kv/services/order-service/prod

# Read config
curl http://consul:8500/v1/kv/services/order-service/prod?keys
```

---
### **4. API-Based Configuration**
Expose configs via a **REST/gRPC API** (e.g., using Envoy, Nginx, or a custom service).

**Pros:**
- Fine-grained access control.
- Supports dynamic queries (e.g., `GET /configs?service=payment&profile=prod`).

**Cons:**
- Adds network overhead.
- Requires API reliability.

**Example API Request (gRPC):**
```proto
service ConfigService {
  rpc GetConfig (GetConfigRequest) returns (ConfigResponse) {}
}

message GetConfigRequest {
  string service = 1;
  repeated string profiles = 2;
}

message ConfigResponse {
  map<string, string> data = 1;
  string etag = 2; // For versioning
}
```

---
### **5. Environment Variables + Local Overrides**
Use **environment variables** for dynamic overrides (e.g., Docker/Kubernetes secrets, `.env` files).

**Pros:**
- Simple for local/dev.
- Works with most runtimes.

**Cons:**
- Not scalable for complex configs.
- Risk of secrets leakage.

**Example (Docker + Kubernetes):**
```yaml
# Kubernetes Secret (base64 encoded)
apiVersion: v1
kind: Secret
metadata:
  name: order-service-secrets
type: Opaque
data:
  DB_PASSWORD: base64-encoded-password
```
**Deployment Override:**
```yaml
env:
- name: DATABASE_URL
  value: "postgres://user:$(DB_PASSWORD)@db.example.com:5432/orders"
```

---
## **Query Examples**
### **1. Fetching Config via REST (Spring Cloud Config)**
```bash
curl http://config-server:8888/order-service/prod
```
**Response:**
```json
{
  "name": "order-service",
  "profiles": ["prod"],
  "label": "main",
  "propertySources": [
    {
      "name": "https://github.com/org/config-repo/main/order-service.yml",
      "source": {
        "service": { "timeout": 5000 },
        "database": { "url": "postgres://user:PASSWORD@db.example.com:5432/orders" }
      }
    }
  ]
}
```

### **2. Consul KV Query**
```bash
# Get all configs for a service
curl http://consul:8500/v1/kv/services/order-service/?keys
```
**Response:**
```json
[
  { "Key": "services/order-service/prod", "Value": "eyJ0b2tlbiI6NTAwfQ==" },
  { "Key": "services/order-service/dev", "Value": "eyJ0b2tlbiI6NTAwLjAwfQ==" }
]
```

### **3. gRPC Config Fetch**
```bash
# Client-side call (using grpcurl)
grpcurl -plaintext localhost:50051 ConfigService.GetConfig '{"service": "payment-service", "profiles": ["prod"]}'
```
**Response:**
```json
{
  "data": {
    "service": { "timeout": 3000 },
    "paymentGateway": { "url": "https://api.gateway.example.com" }
  },
  "etag": "abc123"
}
```

### **4. Kubernetes ConfigMap Query**
```bash
kubectl get configmap order-service-config -o jsonpath='{.data}'
```
**Response:**
```json
{
  "application.yml": "service:\n  timeout: 5000\ndatabase:\n  url: postgres://user:$(DB_PASSWORD)@db.example.com:5432/orders"
}
```

---
## **Validation & Best Practices**
### **1. Schema Validation**
- Use **JSON Schema** or **OpenAPI** to validate configs.
- Example schema for a database config:
  ```json
  {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
      "database": {
        "type": "object",
        "properties": {
          "url": { "type": "string", "format": "uri" },
          "poolSize": { "type": "integer", "minimum": 1, "maximum": 100 }
        },
        "required": ["url"]
      }
    }
  }
  ```

### **2. Secret Management**
- **Never store secrets in configs.** Use **separate systems** (Vault, AWS Secrets Manager).
- Example with Vault:
  ```yaml
  database:
    url: "postgres://user:${VAULT_DB_PASSWORD}@db.example.com:5432/orders"
  ```
  **Vault Token Mount:**
  ```bash
  export VAULT_DB_PASSWORD=$(vault read secret/data/db/password)
  ```

### **3. Dynamic Reload Strategies**
- **Spring Boot:** Use `@RefreshScope` + `@RefreshScope` beans.
- **Kubernetes:** Use liveness probes to trigger reloads:
  ```yaml
  livenessProbe:
    httpGet:
      path: /actuator/health/refresh
      port: 8080
  ```
- **Custom:** Implement a **change stream listener** (e.g., Consul watch, Kafka consumer).

### **4. Circuit Breakers for Config Fetch**
- Fail gracefully if the config server is unavailable.
- Example (Resilience4j):
  ```java
  @CircuitBreaker(name = "configService", fallbackMethod = "fallbackConfig")
  public Config fetchConfig() { ... }
  ```

### **5. Backward Compatibility**
- **Version configs** (e.g., `v1`, `v2`).
- **Deprecate configs** with `deprecated: true` and `fallback` values.
- Example:
  ```json
  {
    "metadata": { "id": "payment-service-v2", "deprecated": true },
    "fallback": { "timeout": 3000 }  // Default if v2 config is missing
  }
  ```

---
## **Related Patterns**
| **Pattern**                     | **Description**                                                                                                                                                                                                 | **When to Use**                                                                                     |
|----------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| **[API Gateway Pattern]**        | Centralized routing and configuration for microservices (e.g., Kong, Apigee).                                                                                                                                     | When you need unified config for API endpoints, rate limiting, and auth.                           |
| **[Feature Flags Pattern]**     | Toggle features dynamically via config (e.g., LaunchDarkly, Unleash).                                                                                                                                         | For A/B testing, canary deployments, or gradual feature rollouts.                                    |
| **[Circuit Breaker Pattern]**    | Resilience against config service failures (e.g., Resilience4j, Hystrix).                                                                                                                                       | When config fetching is critical and downtime must be minimized.                                     |
| **[Service Discovery Pattern]**  | Dynamically resolve service endpoints (e.g., Consul, Eureka).                                                                                                                                                  | When services need to discover each other’s configs (e.g., database URLs).                            |
| **[GitOps Pattern]**             | Sync infrastructure as code (IaC) from Git (e.g., ArgoCD, Flux).                                                                                                                                                | For immutable, auditable config deployments.                                                         |
| **[Saga Pattern]**               | Manage distributed transactions using configs (e.g., orchestrate via config steps).                                                                                                                             | For long-running workflows where configs define step-by-step actions.                                |
| **[Multi-Tenant Pattern]**       | Configure tenants dynamically (e.g., per-customer configs).                                                                                                                                                   | When offering SaaS with customizable per-tenant settings.                                             |

---
## **Anti-Patterns & Pitfalls**
| **Anti-Pattern**               | **Risk**                                                                                                                                                                                                 | **Mitigation**                                                                                     |
|---------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| **Hardcoded Configs**           | Losing flexibility; cannot change without deployments.                                                                                                                                                     | Use external config stores.                                                                        |
| **No Versioning**               | Breaking changes without warning.                                                                                                                                                                      | Tag configs with versions (e.g., `v1`, `v2`).                                                      |
| **Centralized Single Point of Failure** | Config server outage halts all services.                                                                                                                                                            | Use **multi-region config servers** or **local fallbacks**.                                         |
| **No Secrets Management**       | Plaintext secrets in configs (security risk).                                                                                                                                                            | Use **Vault, AWS Secrets Manager, or Kubernetes Secrets**.                                         |
| **Polling with Fixed Intervals** | High latency if configs change frequently.                                                                                                                                                             | Use **event-driven updates** (Webhooks, Kafka, Consul watch).                                     |
| **Overusing Local Overrides**   | Config drift between environments.                                                                                                                                                                    | Enforce **GitOps or immutable configs** for prod/staging.                                          |
| **Ignoring Validation**         | Invalid configs slip into production.                                                                                                                                                                   | Implement **schema validation** at runtime (e.g., JSON Schema).                                    |

---
## **Tools & Libraries**
| **Category**               | **Tools/Libraries**                                                                                                                                                                                                 | **Best For**                                                                                     |
|----------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| **Config Servers**         | Spring Cloud Config, HashiCorp Consul, etcd, AWS Systems Manager Parameter Store, Azure Key Vault.                                                                                                  | Centralized config management.                                                                     |
| **GitOps**                 | ArgoCD, Flux, Spinnaker, Jenkins X.                                                                                                                                                                      | Immutable config deployments from Git.                                                             |
| **Secrets Management**     | HashiCorp Vault, AWS Secrets Manager, Azure Key Vault, AWS Parameter Store (Secure Strings).                                                                                                         | Secure credential storage.                                                                        |
| **Validation**             | JSON Schema, Open