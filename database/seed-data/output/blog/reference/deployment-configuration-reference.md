**[Pattern] Deployment Configuration Reference Guide**

---

### **Overview**
The **Deployment Configuration** pattern defines a structured way to manage runtime settings, environment-specific parameters, and version-specific configurations for applications, microservices, or infrastructure. Unlike hardcoded values or version control file changes, this pattern centralizes configuration management, enabling dynamic updates, security, and backward/forward compatibility across environments (e.g., Dev, Staging, Production).

Key benefits:
- **Decoupling**: Isolates configuration from code, simplifying deployments and rollbacks.
- **Scalability**: Supports dynamic updates without redeployment (e.g., feature flags, A/B testing).
- **Security**: Encrypts sensitive data (e.g., API keys) and restricts access via RBAC.
- **Versioning**: Tracks configuration changes alongside application versions.

This guide covers schema design, implementation, query best practices, and integrations with related patterns.

---

### **Schema Reference**
The Deployment Configuration pattern typically uses a **nested, hierarchical schema** to organize configurations by:
- **Environment** (e.g., `dev`, `prod`)
- **Service/Application** (e.g., `auth-service`, `payment-gateway`)
- **Configuration Group** (e.g., `database`, `logging`, `feature-flags`)
- **Key-Value Pairs** (e.g., `host: "db.example.com"`, `max-retries: 5`).

Below is a standardized schema format (adaptable to JSON, YAML, or databases):

| **Field**               | **Type**          | **Description**                                                                 | **Examples**                                                                 |
|-------------------------|-------------------|---------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **environment**         | String (Required) | Target deployment environment.                                                  | `["dev", "staging", "prod"]`                                                |
| **service**             | String (Required) | Name of the service/application.                                                 | `"user-service"`                                                           |
| **configGroup**         | String (Required) | Category of configurations (e.g., `database`, `scaling`).                        | `["database", "logging", "feature-flags"]`                                   |
| **key**                 | String (Required) | Unique identifier for the configuration key.                                     | `"host"`, `"timeout_sec"`                                                   |
| **value**               | String/Number     | The configuration value (can be serialized).                                    | `"postgres.example.com"`, `30`                                             |
| **defaultValue**        | String/Number     | Fallback value if the key is missing.                                            | `defaultValue: "localhost"`                                                 |
| **isSensitive**         | Boolean           | Marks keys requiring encryption (e.g., secrets).                                | `isSensitive: true`                                                         |
| **version**             | String            | Deployment version tied to this configuration.                                   | `"v1.2.3"`, `"main-20240501"`                                               |
| **createdAt**           | Timestamp         | When the configuration was added/updated.                                       | `2024-05-10T12:00:00Z`                                                     |
| **lastModifiedAt**      | Timestamp         | Last update timestamp.                                                           | `2024-05-15T09:30:00Z`                                                     |
| **metadata**            | Object            | Extended attributes (e.g., `description`, `tags`).                               | `{ "description": "Primary DB host" }`                                        |

---
**Example JSON Structure**:
```json
{
  "environment": "prod",
  "service": "user-service",
  "configGroup": "database",
  "key": "host",
  "value": "prod-db.example.com",
  "defaultValue": "dev-db.example.com",
  "isSensitive": false,
  "version": "v2.1.0",
  "createdAt": "2024-05-10T12:00:00Z",
  "lastModifiedAt": "2024-05-20T15:45:00Z"
}
```

---

### **Implementation Details**
#### **1. Storage Backends**
Choose a backend based on scalability, security, and query needs:
- **Databases**:
  - **PostgreSQL/MySQL**: Use JSON/JSONB columns for nested data (e.g., `configurations configGroup JSONB`).
  - **Redis**: Fast key-value store for runtime configurations (ideal for caching).
- **Configuration Management Tools**:
  - **Vault (HashiCorp)**: Secure secrets management with dynamic secrets.
  - **Consul**: Service mesh integration for dynamic configs.
  - **AWS Systems Manager (SSM)**: Parameter store for cloud-native deployments.
- **Version Control (Git)**:
  - Store non-sensitive configs in `.env` files or directories (e.g., `/config/dev`).
  - Use **Git LFS** for large binaries (e.g., SSL certificates).

#### **2. Access Patterns**
Configurations are accessed via:
- **Environment Variables**: Inject at runtime (e.g., `DB_HOST=${CONFIG_PROD_USER_SERVICE_DATABASE_HOST}`).
- **API Clients**: Fetch via REST/gRPC (e.g., `GET /configs?service=user-service&key=host`).
- **Language SDKs**: Libraries like `config` (Node.js), `python-dotenv`, or `spring-cloud-config` (Java).

#### **3. Versioning Strategies**
- **Immutable Configs**: Append new versions (e.g., `v1.0`, `v2.0`) and use `version` field to select.
- **Backward Compatibility**: Define `defaultValue` for new keys or deprecate old ones with `deprecatedSince`.
- **Canary Deployments**: Gradually roll out configs to a subset of instances.

#### **4. Security**
- **Encryption**: Use **AWS KMS**, **Vault**, or **AWS Secrets Manager** for `isSensitive` keys.
- **Access Control**:
  - **RBAC**: Role-based permissions (e.g., `devops:read-write`, `app-team:read-only`).
  - **Least Privilege**: Limit access to specific `service`/`configGroup` combinations.
- **Audit Logs**: Track changes via `lastModifiedAt` and `createdBy` fields.

#### **5. Migration**
- **Tooling**:
  - **Flyway/Liquibase**: Database schema migrations.
  - **Terraform/Pulumi**: Infrastructure-as-code for config backends.
- **Example Migration**:
  ```sql
  -- Add 'isSensitive' column to existing configs table
  ALTER TABLE configurations ADD COLUMN is_sensitive BOOLEAN DEFAULT false;
  ```

---

### **Query Examples**
#### **1. Fetch Configs by Service and Environment**
**Use Case**: Retrieve all database configs for the `user-service` in production.
**Query (PostgreSQL)**:
```sql
SELECT * FROM configurations
WHERE service = 'user-service'
  AND environment = 'prod'
  AND configGroup = 'database';
```
**Output**:
```json
[
  { "key": "host", "value": "prod-db.example.com" },
  { "key": "port", "value": "5432" }
]
```

#### **2. Dynamic Query with Default Fallback**
**Use Case**: Get `DB_HOST` with a fallback if missing.
**SQL**:
```sql
SELECT COALESCE(
    (SELECT value FROM configurations
     WHERE service = 'user-service' AND key = 'host' AND environment = 'prod'),
    'dev-db.example.com'
) AS db_host;
```
**Output**: `"prod-db.example.com"` (or fallback if config is missing).

#### **3. Filter by Version**
**Use Case**: Deploy `v1.2.0` configs for a service.
**SQL**:
```sql
SELECT * FROM configurations
WHERE service = 'payment-gateway'
  AND version = 'v1.2.0';
```

#### **4. List Sensitive Keys**
**Use Case**: Audit secrets in the `auth-service`.
**SQL**:
```sql
SELECT key, value FROM configurations
WHERE isSensitive = true
  AND service = 'auth-service';
```

#### **5. Time-Based Queries**
**Use Case**: Find configs modified in the last 7 days.
**SQL**:
```sql
SELECT * FROM configurations
WHERE lastModifiedAt >= NOW() - INTERVAL '7 days';
```

---
**API Endpoint Examples** (REST):
| **Endpoint**                          | **Method** | **Description**                                      | **Example Request**                          |
|---------------------------------------|------------|------------------------------------------------------|-----------------------------------------------|
| `/configs?service={service}&env={env}`| `GET`      | Fetch configs by service and environment.             | `/configs?service=user-service&env=prod`      |
| `/configs/{key}`                      | `GET`      | Get a single key-value pair.                          | `/configs/DB_HOST`                           |
| `/secrets`                            | `GET`      | List sensitive keys (authenticated).                 | `GET /secrets?service=auth-service`          |
| `/configs/version/{version}`          | `GET`      | Retrieve configs for a specific version.              | `/configs/version/v1.2.0`                    |
| `/configs`                            | `POST`     | Add/update a config (admin-only).                    | `POST /configs` with JSON payload           |

---

### **Related Patterns**
1. **Feature Toggle**
   - **Relation**: Deployment Configuration can store feature flags (e.g., `configGroup: "feature-flags"`, `key: "enable_new_ui"`).
   - **Integration**: Use `value` as a boolean (e.g., `true/false`) and query with:
     ```sql
     SELECT value FROM configurations
     WHERE key = 'enable_new_ui' AND environment = 'prod';
     ```

2. **Canary Deployment**
   - **Relation**: Gradually roll out configs to a subset of instances (e.g., `metadata: { "canary": true }`).
   - **Integration**:
     - Store rollout percentage in `value` (e.g., `5%`).
     - Query with:
       ```sql
       SELECT * FROM configurations
       WHERE service = 'payment-service'
         AND metadata->>'canary' = 'true';
       ```

3. **Infrastructure as Code (IaC)**
   - **Relation**: Use Terraform/CloudFormation to provision config backends (e.g., RDS, Vault).
   - **Example**:
     ```hcl
     # Terraform: Create a Secrets Manager parameter
     resource "aws_ssm_parameter" "db_password" {
       name  = "/prod/user-service/database/password"
       type  = "SecureString"
       value = var.db_password
     }
     ```

4. **Observability**
   - **Relation**: Log/config changes for auditing (e.g., `lastModifiedBy` field).
   - **Integration**: Forward to tools like **Datadog** or **Loki**:
     ```json
     {
       "event": "config_updated",
       "service": "user-service",
       "key": "timeout_sec",
       "old_value": "30",
       "new_value": "60",
       "timestamp": "2024-05-20T15:45:00Z"
     }
     ```

5. **Circuit Breaker**
   - **Relation**: Store circuit breaker thresholds (e.g., `configGroup: "resilience"`, `key: "max_failures"`).
   - **Query**:
     ```sql
     SELECT value FROM configurations
     WHERE configGroup = 'resilience'
       AND key = 'max_failures'
       AND service = 'payment-service';
     ```

---

### **Best Practices**
1. **Idempotency**: Design configs to be re-deployed without side effects.
2. **Validation**: Use tools like **JSON Schema** or **OpenAPI** to validate configs at runtime.
3. **Monitoring**: Alert on config drift (e.g., `lastModifiedAt` gaps) or access anomalies.
4. **Documentation**: Maintain a **CHANGELOG** for config updates (e.g., `/docs/config-changelog.md`).
5. **Testing**:
   - Unit tests for config loading (e.g., mock `environments` in tests).
   - Integration tests for dynamic updates (e.g., `curl /configs`).

---
### **Troubleshooting**
| **Issue**                     | **Diagnosis**                          | **Solution**                                      |
|-------------------------------|----------------------------------------|---------------------------------------------------|
| Config missing at runtime     | Invalid `defaultValue` or missing key. | Check `defaultValue` or verify the key exists.    |
| Permission denied             | RBAC misconfiguration.                 | Grant read/write roles to the caller.             |
| Slow queries                  | Missing indexes on `service`, `env`.   | Add indexes: `CREATE INDEX idx_service_env ON configs(service, environment)`. |
| Stale configs                 | Caching layer outdated.                | Invalidate cache on `lastModifiedAt` changes.     |

---
### **Example Workflow**
1. **Dev**: Developer pushes a config update to Git:
   ```yaml
   # config/dev/user-service/database/host: prod-db.example.com
   ```
2. **CI/CD**: Pipeline validates and deploys changes to Vault:
   ```bash
   vault kv put secret/user-service/database host=prod-db.example.com
   ```
3. **Runtime**: Application queries Vault:
   ```go
   // Pseudocode
   host, _ := vault.Get("secret/user-service/database", "host")
   ```
4. **Monitoring**: Alert if `host` changes without approval (via audit logs).