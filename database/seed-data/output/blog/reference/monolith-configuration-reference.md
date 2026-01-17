# **[Pattern] Monolith Configuration Reference Guide**

---

## **Overview**
The **Monolith Configuration** pattern consolidates all application settings into a central, structured configuration file or repository, simplifying management, deployment, and version control. Unlike distributed configurations (e.g., multiple `json`, `yaml`, or environment-specific files), this pattern centralizes settings into a single source of truth—typically a **root-level configuration file** (e.g., `app.yaml`, `config.json`) or a **database-backed registry**—to ensure consistency across environments (development, staging, production).

This pattern is ideal for:
- **Large applications** with diverse feature sets requiring unified control.
- **Serverless/microservices** where runtime flexibility is needed.
- **Infrastructure-as-Code (IaC)** deployments needing standardized configurations.
- **Compliance-heavy** applications requiring audit trails for changes.

**Key Principles**:
✔ **Single Source of Truth**: One file/repo for all configurations.
✔ **Environment Agnostic**: Override values per environment via variables (e.g., `config.DEV.yaml`).
✔ **Extensible**: Modular sub-configurations (e.g., `db.yaml`, `logging.yaml`).
✔ **Version-Controlled**: Track changes in Git/LFS with rollback capabilities.

---

## **Schema Reference**
Below is the recommended schema structure for a **monolithic configuration file** (e.g., YAML/JSON). Fields are categorized for clarity.

| **Category**       | **Field**               | **Type**       | **Description**                                                                 | **Example Value**                          | **Validation**                     |
|--------------------|-------------------------|----------------|---------------------------------------------------------------------------------|--------------------------------------------|------------------------------------|
| **Core Settings**  | `app.name`              | String         | Application identifier.                                                          | `"MyApp:V1.2.0"`                           | Regex: `^[A-Za-z0-9_\-]+$`         |
|                    | `app.env`               | Enum           | Environment: `dev`, `staging`, `prod`.                                           | `"prod"`                                   | Enum: `[dev, staging, prod]`        |
|                    | `app.timezone`          | String         | System timezone (e.g., `UTC`, `America/New_York`).                               | `"UTC"`                                    | RFC 3339 compliant                  |
| **Database**       | `db.host`               | String         | Primary DB server address.                                                        | `"db.example.com:5432"`                   | IP/Port validation                  |
|                    | `db.username`           | String         | DB credentials.                                                                   | `"admin"`                                  | No empty strings                    |
|                    | `db.password`           | String (secret)| Encrypted in production; use vaults/secrets managers.                           | `$$ENC[...]` (encrypted)                  | PasswordPolicy (e.g., 8+ chars)     |
|                    | `db.tls.enabled`        | Boolean        | Enable TLS for DB connections.                                                    | `true`                                     | `true`/`false`                      |
| **APIs & Services**| `services.thirdparty`   | Object         | Third-party service URLs/keys.                                                    | `{ "stripe": { "key": "sk_test_123" } }`   | URL/Key validation                  |
|                    | `services.caching`      | String         | Cache backend (Redis/Memorystore).                                              | `"redis://cache.example.com:6379"`        | Redis URL format                    |
| **Logging**        | `logging.level`         | String         | Log verbosity: `debug`, `info`, `warn`, `error`.                               | `"info"`                                   | Enum: `[debug, info, warn, error]`  |
|                    | `logging.destination`   | String         | Output target: `stdout`, `file`, `syslog`.                                       | `"file:/var/log/app.log"`                  | File path validation                |
| **Security**       | `security.jwt.secret`   | String (secret)| JWT signing key.                                                                   | `$$ENC[...]`                               | 32+ chars                           |
|                    | `security.roles`        | Array          | Permitted roles (e.g., `{"admin": true, "user": false}`).                        | `[ "admin", "auditor" ]`                   | Role whitelist                      |
| **Modules**        | `modules.feature_flags` | Object         | Enable/disable features dynamically.                                             | `{ "beta": true, "analytics": false }`    | Boolean keys/values                 |
| **Overrides**      | `overrides.env.[key]`   | Dynamic        | Environment-specific overrides (e.g., `overrides.dev.db.host`).                   | `{ "db.host": "dev-db.example.com" }`     | N/A (runtime resolution)            |

---

### **File Structure Example (YAML)**
```yaml
# config/app.yaml
app:
  name: "MyApp"
  env: "prod"
  timezone: "UTC"

db:
  host: "prod-db.example.com"
  username: "$DB_USER"
  password: "$$ENC[...]"
  tls:
    enabled: true

services:
  stripe:
    key: "$STRIPE_API_KEY"

logging:
  level: "info"
  destination: "file:/var/log/app.log"

# Environment-specific overrides (e.g., config/app.DEV.yaml)
overrides:
  dev:
    db:
      host: "dev-db.example.com"
```

---

## **Query Examples**
Monolith configs are **static at compile-time** but **dynamic at runtime**. Use these methods to access values:

### **1. File-Based Access (YAML/JSON)**
```python
import yaml
import os

# Load config
with open("config/app.yaml") as f:
    config = yaml.safe_load(f)

# Access values
db_host = config["db"]["host"]
env = config["app"]["env"]

# Environment overrides
env_suffix = f"_{config['app']['env']}" if config["app"]["env"] != "prod" else ""
overrides = yaml.safe_load(open(f"config/app{env_suffix}.yaml")) or {}
db_host = overrides.get("db", {}).get("host", db_host)
```

### **2. Environment Variable Overrides**
For secrets or dynamic values, use environment variables:
```bash
# Deploy with overrides
DB_PASSWORD=$(vault read secret/db/password) \
  export DB_PASSWORD \
  ./app --config=config/app.yaml
```

### **3. Database-Backed Configs (PostgreSQL Example)**
```sql
-- Schema
CREATE TABLE app_config (
  key TEXT PRIMARY KEY,
  value JSONB NOT NULL,
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Query
SELECT value FROM app_config WHERE key = 'db.host';
```

### **4. Runtime Injection (Serverless)**
```javascript
// AWS Lambda (Node.js)
const config = {
  ...require("./config/app.json"),
  ...process.env // Override with env vars
};

exports.handler = async (event) => {
  const dbHost = config.db.host || process.env.DB_HOST;
  // ...
};
```

---

## **Implementation Details**
### **1. Schema Design**
- **Hierarchy**: Use nested objects for logical grouping (e.g., `db`, `services`).
- **Secrets Management**:
  - Avoid hardcoding: Use **vaults** (HashiCorp Vault), **KMS**, or **environment variables**.
  - Example:
    ```yaml
    db:
      password: "$(vault read db/creds/password)"
    ```
- **Validation**: Use tools like:
  - **YAML**: [YAML Schema](https://github.com/FISCO-BCBC/YAMLSchema) or [jsonschema](https://json-schema.org/).
  - **Runtime**: Libraries such as [pydantic](https://pydantic-docs.helpmanual.io/) (Python) or [Zod](https://github.com/colinhacks/zod) (JavaScript).

### **2. Versioning**
- **File Naming**:
  - `config/v1/app.yaml` (semantic versioning).
- **Backward Compatibility**:
  - Add new fields; avoid removing deprecated ones (use `deprecated: true`).
  - Example:
    ```yaml
    deprecated:
      api.version: "v1"  # Warn users to migrate to `api.v2.enabled`
    ```

### **3. Deployment Strategies**
| **Strategy**          | **Use Case**                          | **Implementation**                          |
|-----------------------|---------------------------------------|---------------------------------------------|
| **File-Based**        | Static configs (dev/staging).         | Deploy `config/app.PROD.yaml` via CI/CD.   |
| **Database Sync**     | Dynamic configs (prod).               | Sync config table on deploy (e.g., Flyway). |
| **Secret Manager**    | Sensitive data.                       | Inject secrets at runtime (e.g., AWS SSM).  |
| **GitOps**            | IaC + config as code.                 | Use ArgoCD/Kustomize to reconcile configs.  |

### **4. Performance Considerations**
- **File Size**: Keep under **500KB** (compress if needed with `gzip`).
- **Caching**: Load configs once at startup (e.g., Python’s `lru_cache`).
- **Reloading**: For dynamic changes, use a **config watcher** (e.g., [config-reloader](https://github.com/kelseyhightower/config-reloader)).

---

## **Query Examples (Expanded)**
### **Example 1: Feature Flag Toggle**
```yaml
# config/app.yaml
modules:
  feature_flags:
    analytics: false
    dark_mode: true
```

**Code Access (Go):**
```go
type Config struct {
    Modules struct {
        FeatureFlags map[string]bool `json:"feature_flags"`
    } `json:"modules"`
}

func main() {
    cfg := loadConfig()
    if cfg.Modules.FeatureFlags["dark_mode"] {
        // Enable dark mode logic
    }
}
```

### **Example 2: Environment-Specific DB**
```yaml
# config/app.DEV.yaml
overrides:
  dev:
    db:
      host: "dev-db.example.com"
      port: 5433
```

**Code Override (Python):**
```python
import yaml
from os import getenv

config = yaml.safe_load(open("config/app.yaml"))
env = config["app"]["env"]

# Load overrides if they exist
overrides = yaml.safe_load(open(f"config/app.{env}.yaml")) or {}
db_config = {**config["db"], **overrides.get("db", {})}

# Use overridden values
db_host = db_config["host"]
```

### **Example 3: Secrets Rotation**
```bash
# Rotate DB password via Vault
vault write secret/db/password password="new_password_123"

# App accesses the latest value
export DB_PASSWORD=$(vault read secret/db/password)
```

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                          |
|---------------------------|-------------------------------------------------------------------------------|------------------------------------------|
| **[Environment Variables](https://12factor.net/config)** | Dynamic runtime overrides for configs/secrets.                              | When some values must vary per runtime instance (e.g., containers). |
| **[Feature Toggles](https://martinfowler.com/articles/feature-toggles.html)** | Enable/disable features without redeploying.                               | For A/B testing or beta features.        |
| **[Configuration as Code](https://www.terraform.io/)** | Manage configs via IaC tools (Terraform, Pulumi).                          | When configs are tied to infrastructure. |
| **[Secrets Management](https://www.vaultproject.io/)** | Secure storage and rotation of secrets.                                    | For production deployments.             |
| **[Modular Config](https://docs.microsoft.com/en-us/azure/architecture/patterns/modular-configuration)** | Split configs into smaller files (e.g., `auth.yaml`, `cache.yaml`).        | For large apps needing loose coupling.   |
| **[Canary Releases](https://martinfowler.com/bliki/CanaryRelease.html)** | Gradually roll out config changes.                                          | For zero-downtime updates.               |

---

## **Best Practices**
1. **Idempotency**: Ensure config reloads don’t cause race conditions.
2. **Audit Logging**: Log config changes with timestamps (useful for compliance).
3. **Default Values**: Provide fallbacks for optional fields.
   ```yaml
   db:
     timeout: 10  # Default: 10s
   ```
4. **Validation**: Reject invalid configs early (e.g., validation hooks in code).
5. **Documentation**: Include a `README.md` with:
   - Example configs.
   - Change process (e.g., PR reviews for config updates).
   - Ownership (who manages secrets?).

---
## **Anti-Patterns**
❌ **Hardcoding Sensitive Data**: Never commit passwords to Git.
❌ **Monolithic Overrides**: Avoid `config/app.ALL_ENVIRONMENTS.yaml`.
❌ **No Versioning**: Mixing config versions causes inconsistencies.
❌ **Ignoring Validation**: Unvalidated configs lead to runtime errors.

---
## **Tools & Libraries**
| **Language** | **Tool**                          | **Description**                          |
|--------------|-----------------------------------|------------------------------------------|
| Python       | Pydantic                          | Data validation and settings management.  |
| JavaScript   | Zod                                | Type-safe config parsing.                 |
| Go           | `viper`                           | Config file + environment variable support. |
| Java         | Spring Cloud Config               | Centralized config server.                |
| Infrastructure | Terraform/Ansible               | Config as IaC.                           |