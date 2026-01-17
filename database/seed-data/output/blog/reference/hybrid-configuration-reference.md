---
# **[Pattern] Hybrid Configuration Reference Guide**

---

## **Overview**
The **Hybrid Configuration** pattern combines centralized configuration management with decentralized overrides, enabling fine-grained control over application settings across environments (e.g., development, staging, production). This pattern leverages a **primary configuration source** (e.g., environment variables, config files, or cloud-secrets manager) augmented by **secondary overrides** (e.g., local files, in-memory overrides, or runtime flags). Hybrid configurations are ideal for:
- **Security-sensitive applications** where sensitive values (e.g., API keys) are vaulted centrally.
- **Multi-tenant systems** requiring tenant-specific overrides.
- **CI/CD pipelines** needing consistent baselines with per-deployment tweaks.
- **Microservices** where independent teams manage partial configurations.

Hybrid configurations reduce "switchboard" complexity in monolithic configs while maintaining auditability. They typically implement **fallback chains**, where missing values trigger cascaded lookups (e.g., config file → environment variable → default).

---

## **Key Concepts**
| **Term**                     | **Description**                                                                                     | **Example Use Cases**                                                                 |
|------------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| **Primary Source**           | Centralized config repository (e.g., AWS SSM, Kubernetes ConfigMaps, `.env` files).                | Storing non-sensitive configs like logging levels or timeouts.                        |
| **Secondary Override**       | Local or runtime modifications (e.g., `local.properties`, command-line args).                       | Overriding `DB_HOST` for testing with `db.host=localhost`.                          |
| **Fallback Chain**           | Logic to resolve missing values by checking sources in a defined order (e.g., overrides → vault → defaults). | Resolving `FEATURE_FLAG` if absent: `env_var → file → hardcoded fallback`.          |
| **Dynamic Override**         | Runtime adjustments (e.g., via API calls or gRPC flags) for dynamic environments.                   | Toggling a feature flag without redeploying.                                         |
| **Validation Layer**         | Ensures configurations are syntactically correct and meet constraints (e.g., schema validation).   | Enforcing `PORT` values between `8080` and `9000`.                                   |
| **Secrets Management**       | Isolation of sensitive values (e.g., `DB_PASSWORD`) from primary configs via rotation/encryption.   | Using HashiCorp Vault or Azure Key Vault for credentials.                           |

---

## **Schema Reference**
The following table outlines a **Hybrid Configuration Schema** for a sample microservice (`app.conf`, `overrides.conf`, and environment variables).

| **Field Name**               | **Type**      | **Source Priority**       | **Description**                                                                       | **Example Value**               | **Constraints**                     |
|------------------------------|---------------|---------------------------|---------------------------------------------------------------------------------------|---------------------------------|-------------------------------------|
| `app.name`                   | String        | Primary (file)            | Identifier for the application.                                                        | `user-service`                   | Regex: `[a-z0-9\-]+`               |
| `db.host`                    | String        | Fallback (env → file)      | Database host address. Overridden by `DB_HOST` environment variable.                   | `db.example.com`                | Must match `^[\w\-\.]+$`            |
| `db.port`                    | Integer       | Secondary (file)          | Database port (default in schema). Overridden by `DB_PORT` or runtime flags.          | `5432`                          | Range: `1–65535`                   |
| `feature.flags`              | Object        | Dynamic (runtime)         | Key-value flags for A/B testing. Modified via API or flags (e.g., `--flag=foo`).     | `{ "new_ui": true }`           | Values: `true`/`false`             |
| `logging.level`              | Enum          | Primary (file)            | Log verbosity (defaults to `INFO`). Overriden by `LOG_LEVEL`.                           | `DEBUG`                         | Values: `TRACE\|DEBUG\|INFO\|...`  |
| `sensitive.api.key`          | String        | Secrets Manager (Vault)   | API key for external service (never in file; fetched at runtime).                       | *(masked)*                      | Must be base64-encoded.           |
| `retries.max`                | Integer       | Secondary (env)           | Max retries for HTTP calls. Overridden by `MAX_RETRIES`.                                | `3`                             | ≥ `0`                              |

---

## **Implementation Details**

### **1. Fallback Chain Resolution**
Hybrid configurations resolve values in a **user-defined order**. Example chains:
- **Default:** `overrides.conf → primary.conf → environment variables → defaults`
- **Secrets-Priority:** `Vault → overrides.conf → config file`

**Implementation (Pseudocode):**
```python
def resolve_config(key):
    sources = [
        lambda: load_overrides(),        # 1. Local overrides
        lambda: load_primary_config(),    # 2. Central config
        lambda: os.getenv(key),           # 3. Env vars
        lambda: get_default(key)          # 4. Hardcoded
    ]
    for source in sources:
        value = source()
        if value is not None:
            return value
    raise ConfigError(f"Missing key: {key}")
```

### **2. Source Integration**
| **Source**               | **Implementation Notes**                                                                                     | **Tools/Libraries**                          |
|--------------------------|---------------------------------------------------------------------------------------------------------------|-----------------------------------------------|
| **Config Files**         | Use YAML/JSON (e.g., `config.yaml`) with fallback defaults. Supports includes (e.g., `@include secrets.json`). | `pydantic`, `viper`, `HOCON`                 |
| **Environment Variables**| Prefix keys with `APP_` (e.g., `APP_DB_HOST`). Override underscores with dots (e.g., `DB_HOST` → `db.host`).   | `python-dotenv`, `dotenv`                    |
| **Secrets Manager**      | Fetch secrets at startup (e.g., AWS SSM, HashiCorp Vault). Cache tokens to avoid per-request calls.            | `boto3`, `vault-sdk`                         |
| **Runtime Flags**        | Accept CLI args or flags (e.g., `--debug=true`). Parse with standard libraries like `argparse`.               | `argparse`, `pika` (for flags)                |
| **Dynamic APIs**         | Fetch overrides via HTTP (e.g., `/config/overrides`). Cache responses for performance.                      | `requests`, `aiohttp`                        |

### **3. Validation**
Validate configurations **before runtime** to fail fast:
- **Schema Validation:** Use tools like [`pydantic`](https://pydantic-docs.helpmanual.io/) or [`json-schema`](https://json-schema.org/) to enforce types/constraints.
- **Environment-Specific Checks:** Flag invalid combinations (e.g., `LOG_LEVEL=TRACE` in production).

**Example (Pydantic):**
```python
from pydantic import BaseModel, Field, validator

class Config(BaseModel):
    db_host: str = Field(..., regex=r"^[\w\-\.]+$")
    retries_max: int = Field(..., ge=0)

    @validator("db_port")
    def port_valid(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError("Port out of range")
        return v
```

### **4. Secrets Management**
- **Never embed secrets** in config files or version control.
- **Rotation:** Use short-lived tokens (e.g., AWS temporary credentials).
- **Tools:**
  - **AWS:** [`AWS Systems Manager Parameter Store`](https://aws.amazon.com/systems-manager/parameter-store/)
  - **Cloud:** [`Azure Key Vault`](https://azure.microsoft.com/en-us/products/key-vault/)
  - **Open Source:** [`HashiCorp Vault`](https://www.vaultproject.io/)

---

## **Query Examples**
### **1. Load Hybrid Config (Python)**
```python
from hybrid_config import HybridConfig

config = HybridConfig(
    sources=[
        ("overrides", "~/config/overrides.yaml"),
        ("primary", "config.yaml"),
        ("env", {}),  # Uses os.environ
    ],
    secrets_provider=VaultClient()
)

db_host = config.resolve("db.host")  # Resolves from overrides → primary → env → default
```

### **2. CLI Overrides**
```bash
# Override db.host via CLI (priority > overrides file)
python app.py --db.host=localhost
```

### **3. Dynamic API Fetch**
```python
# Fetch feature flags dynamically
flags = requests.get("https://config-service/flags").json()
config.update_override("feature.flags", flags)
```

### **4. Fallback Chain Debugging**
```python
print(config.resolve("non.existent"))  # Raises ConfigError with fallback chain
# Output: "Key 'non.existent' not found. Checked: overrides.yaml > config.yaml > env > defaults"
```

---

## **Related Patterns**
| **Pattern**               | **Relationship**                                                                                     | **When to Use Together**                                                                 |
|---------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| **Feature Flags**         | Hybrid configs often manage feature flags dynamically via runtime overrides.                         | When you need to toggle features without redeploying.                                  |
| **Configuration As Code** | Centralized configs (e.g., Terraform for IAC) align with hybrid patterns for infrastructure.         | For DevOps teams managing both app and cloud configs.                                   |
| **Circuit Breaker**       | Configures retry policies (e.g., `retries.max`) in hybrid configs.                                  | When handling fault-tolerant microservices.                                             |
| **Secret Rotation**       | Integrates with secrets managers for periodic token refresh.                                        | For high-security applications (e.g., financial services).                              |
| **Environment Variables** | Fallback source in hybrid configs; often used for runtime overrides.                                | Simplifying local development overrides.                                                 |

---

## **Best Practices**
1. **Immutable Primary Sources:**
   - Treat central configs (e.g., Kubernetes ConfigMaps) as read-only. Use GitOps for changes.

2. **Minimize Fallback Chains:**
   - Limit sources to **3–4** (e.g., overrides → primary → secrets → defaults) to avoid ambiguity.

3. **Document Overrides:**
   - Include a `README` in override files (e.g., `overrides.example.yaml`) explaining how to customize.

4. **Monitor Config Changes:**
   - Log config resolves (e.g., `INFO: Resolved 'db.host' from overrides`) for debugging.

5. **Test Locally:**
   - Use tools like [`configmapgen`](https://github.com/GoogleCloudPlatform/configmapgen) to mock environments.

6. **Avoid Hardcoding:**
   - Never hardcode secrets or environment-specific values (e.g., `DB_PASSWORD` in code).

---

## **Anti-Patterns**
| **Anti-Pattern**               | **Why It’s Bad**                                                                                     | **Fix**                                                                                 |
|---------------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| **No Fallback Chain**           | Missing values crash apps unpredictably.                                                            | Implement a clear fallback order (e.g., overrides → defaults).                          |
| **Secrets in Config Files**     | Exposes credentials to version control or logs.                                                     | Use secrets managers or short-lived tokens.                                            |
| **Overusing Runtime Overrides** | Makes configs hard to debug or version.                                                              | Limit dynamic overrides to truly volatile settings (e.g., feature flags).                |
| **Circular Dependencies**       | Config files include each other indefinitely.                                                        | Use `require`/`include` carefully with validation.                                      |
| **Ignoring Validation**         | Invalid configs (e.g., wrong port) slip to production.                                               | Validate at load time with tools like Pydantic.                                          |

---
**See Also:**
- [12-Factor App Config](https://12factor.net/config) (foundational principles)
- [Kubernetes ConfigMaps](https://kubernetes.io/docs/tasks/configure-pod-container/configure-pod-configmap/) (for containerized apps)
- [AWS Systems Manager](https://aws.amazon.com/systems-manager/) (for cloud-based secrets)