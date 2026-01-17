# **[Pattern] Hybrid Conventions Reference Guide**

---
## **1. Overview**
The **Hybrid Conventions** pattern combines traditional **explicit configuration** (e.g., YAML, JSON, XML) with **implicit rules** (e.g., naming conventions, type inference, runtime defaults). This approach streamlines workflows by reducing repetitive declarations while maintaining flexibility for explicit overrides.

Common use cases:
- **Configuration-driven systems** (e.g., Kubernetes, Terraform)
- **API contract definitions** (OpenAPI/Swagger, GraphQL schemas)
- **Stateful applications** (e.g., React/Vue component props with defaults)
- **Infrastructure-as-Code (IaC)** (Terraform modules, Ansible playbooks)

Hybrid Conventions are particularly valuable when:
✔ Most configurations follow a predictable structure.
✔ Some configurations require explicit overrides.
✔ Reducing cognitive load for developers is a priority.

---

## **2. Key Concepts & Schema Reference**

### **Core Principles**
| Concept               | Description                                                                 |
|-----------------------|-----------------------------------------------------------------------------|
| **Explicit Overrides** | User-defined values take precedence over inferred defaults.                |
| **Implicit Inference** | System derives values from context (e.g., filenames, environment variables). |
| **Layered Priority**   | Configurations can be applied at multiple levels (e.g., global → local).   |
| **Merge Strategies**   | Conflicts between explicit and implicit values are resolved via rules (e.g., last-write-wins). |

---

### **Schema Reference**
Below is a **JSON-based schema** for a generic Hybrid Conventions system (adaptable to YAML/XML/TOML).

| Field               | Type       | Required | Description                                                                 | Example Values                     |
|---------------------|------------|----------|-----------------------------------------------------------------------------|-------------------------------------|
| `metadata`          | Object     | No       | Non-functional data (e.g., versioning, author).                             | `{"version": "v1", "author": "admin"}` |
| `defaults`          | Object     | Yes      | Implicit values applied unless overridden.                                  | `{ "timeout": 30, "retries": 3 }` |
| `explicit`          | Object     | No       | User-provided overrides.                                                    | `{ "timeout": 60 }`                |
| `rules`             | Array      | No       | Custom inference logic (e.g., environment-based defaults).                  | `[{ "env_var": "DB_HOST", "fallback": "localhost" }]` |
| `fallbacks`         | Array      | No       | Ordered chain of fallback sources (e.g., environment → file → system).       | `[{ "source": "env" }, { "source": "file" }]` |
| `merge`             | String     | No       | Conflict resolution strategy (`deep_merge`, `last_wins`, `custom`).         | `"deep_merge"`                      |

**Example Configuration:**
```json
{
  "metadata": { "version": "v1" },
  "defaults": {
    "timeout": 30,
    "retries": 3
  },
  "explicit": {
    "timeout": 60,
    "retries": 5
  },
  "rules": [
    { "env_var": "APP_ENV", "fallback": "dev" }
  ],
  "fallbacks": [
    { "source": "environment" },
    { "source": "config_file" }
  ],
  "merge": "deep_merge"
}
```

---

## **3. Implementation Details**

### **3.1. Supported Formats**
Hybrid Conventions work with multiple formats via **transpilers** or **adapters**:

| Format  | Use Case                          | Example Adapter Example                     |
|---------|-----------------------------------|---------------------------------------------|
| **JSON** | API configurations, services      | `json.loads(file.read())`                   |
| **YAML** | Kubernetes manifests, Terraform   | `yaml.safe_load(file.read())`               |
| **TOML** | CLI tool configs                  | `tomllib.loads(file.read())`                |
| **XML**  | Legacy systems (e.g., SOA)        | `xml.etree.ElementTree.parse(file)`        |

### **3.2. Fallback Resolution**
When explicit values are missing, the system resolves defaults using this **priority order**:

1. **Explicit overrides** (highest priority).
2. **Runtime rules** (e.g., environment variables, runtime APIs).
3. **Fallback sources** (config file → system defaults).
4. **Derived values** (e.g., `timeout` inferred from `retries`).

**Example Resolution:**
```python
def resolve_value(key, config):
    if key in config["explicit"]:
        return config["explicit"][key]
    elif any(rule["env_var"] == key for rule in config["rules"]):
        return os.getenv(key, rule["fallback"])
    else:
        return config["defaults"].get(key, fallback())
```

### **3.3. Merge Strategies**
| Strategy          | Behavior                                                                 | Use Case                          |
|-------------------|-----------------------------------------------------------------------------|-----------------------------------|
| `deep_merge`      | Recursively merges nested objects (deep).                                | Kubernetes manifests              |
| `last_wins`       | Later-defined values overwrite earlier ones.                               | User preferences                  |
| `custom`          | User-provided merge function.                                             | Complex conflict resolution       |

**Example (`deep_merge`):**
```python
from deepmerge import always_merger

merged = always_merger.merge(
    default={"a": 1},
    explicit={"a": 2, "b": {"c": 3}}
)
# Result: {"a": 2, "b": {"c": 3}}
```

---

## **4. Query Examples**

### **4.1. Retrieving Values**
```python
from hybrid_conventions import Config

config = Config.load("config.yaml")
print(config.get("timeout"))  # Output: 60 (explicit override)
print(config.get("retries"))  # Output: 5 (explicit)
print(config.get("app_env"))  # Output: "dev" (resolved from rule)
```

### **4.2. Writing to Config**
```python
# Override a value
config.explicit["timeout"] = 120
config.save()  # Persists to file
```

### **4.3. Validating Config**
```python
if not config.is_valid():
    raise ValueError(f"Invalid config: {config.errors}")
```

### **4.4. CLI Integration**
```bash
# Load from environment + file
hybrid-conv load --file config.json --env APP_ENV=prod
```

---

## **5. Related Patterns**

| Pattern                     | Relationship to Hybrid Conventions                          | When to Use Together                     |
|-----------------------------|-----------------------------------------------------------|------------------------------------------|
| **Feature Flags**           | Hybrid Conventions can manage feature flag configs.      | Dynamic feature toggling.                |
| **Dependency Injection**    | Implicit defaults can be injected as fallback beans.     | Microservices architectures.            |
| **Configuration as Code**   | Hybrid Conventions implement a subset of this pattern.    | Infrastructure-as-Code (IaC).            |
| **Schema Validation**       | Validate configs against inferred schemas.               | APIs, databases.                         |
| **Contextual Abstraction**  | Use Hybrid Conventions to infer context (e.g., `dev/stage`). | Multi-environment deployments.           |

---

## **6. Best Practices**

1. **Document Defaults Clearly**
   Use comments or metadata to explain implicit values:
   ```yaml
   defaults:
     timeout: 30  # Default: 30s (override with `timeout: 60`)
   ```

2. **Leverage Environment Variables for Secrets**
   Never hardcode sensitive data; use `env_var` rules:
   ```json
   { "rules": [{ "env_var": "DB_PASSWORD", "fallback": "" }] }
   ```

3. **Version Defaults**
   Include version metadata to handle breaking changes:
   ```yaml
   metadata:
     version: "2.0"  # Defaults changed in v2
   ```

4. **Optimize Fallback Order**
   Prioritize faster sources (e.g., runtime env vars > file I/O).

5. **Unit Test Resolutions**
   Mock `Config.resolve()` to verify fallback logic:
   ```python
   def test_resolve_fallback():
       assert config.resolve("missing_key") == "default_value"
   ```

---
**See Also:**
- [Explicit Configuration Pattern](link)
- [Implicit Configuration Pattern](link)