---
# **[Pattern] Containers Configuration Reference Guide**

---

## **Overview**
The **Containers Configuration** pattern standardizes how application settings, dependencies, and run-time parameters are managed within containerized environments (e.g., Docker, Kubernetes). This ensures consistency, portability, and secure configuration across deployments. It leverages **environment variables, config maps/secrets, and runtime overrides** to decouple configurations from application code, adhering to the **12-factor app principles**. This guide covers core concepts, schema definitions, query patterns, and best practices for implementing and maintaining scalable containerized configurations.

---

## **Implementation Details**

### **Core Concepts**
1. **Immutable Configurations**
   - Containers should not modify their configuration or runtime files. Use config maps/secrets for static settings and volume mounts for writable data (e.g., logs, caches).

2. **Environment Variables**
   - Preferences for lightweight, dynamic configuration. Prefer `ENV` for environment-specific settings (dev, staging, prod) and secrets for sensitive data (e.g., `DB_PASSWORD`).

3. **Config Maps & Secrets**
   - **ConfigMaps**: Store non-sensitive key-value configurations (e.g., logging levels, feature flags).
   - **Secrets**: Encrypted storage for credentials, tokens, or certificates. Mount as files or pass as environment variables.

4. **Dependency Injection**
   - Use dependency injection (e.g., Kubernetes `initContainers`) to fetch configurations before startup.

5. **Binding Mechanisms**
   - Language-specific libraries (e.g., `os.getenv()`, `java.util.Properties`) parse configurations into application objects.

6. **Validation & Defaults**
   - Implement schemas (e.g., JSON, YAML) to validate configurations at runtime or startup.

---

## **Schema Reference**
The following table outlines the structure of a standard container configuration:

| **Field**               | **Type**               | **Description**                                                                                               | **Example**                          |
|-------------------------|------------------------|---------------------------------------------------------------------------------------------------------------|--------------------------------------|
| `metadata.name`         | String (Required)      | Unique identifier for the configuration object (e.g., `app-config prod`).                                    | `app-config-prod`                    |
| `metadata.namespace`    | String (Optional)      | Namespaced context (e.g., Kubernetes).                                                                      | `default`                            |
| `source`                | Object (Required)      | Configuration origin (e.g., ConfigMap, Secrets).                                                            | `{ envVars: { DB_URL: "postgres://..." } }` |
| `source.filePath`       | String (Optional)      | Path to a mounted config file (e.g., `/etc/app/config.yml`).                                               | `/etc/app/config`                    |
| `source.envVars`        | Object (Optional)      | Dynamic environment variables.                                                                             | `{ LOG_LEVEL: "debug", FEATURE: "true" }` |
| `secrets`               | List of Secrets (Optional) | References to Kubernetes Secrets or encrypted credentials.                                               | `[ { name: "db-secret", key: "password" } ]` |
| `defaultValues`         | Object (Optional)      | Fallback defaults if a setting is missing.                                                                   | `{ DB_TIMEOUT: "30" }`               |
| `validation.schema`     | Object (Optional)      | JSON Schema for runtime validation.                                                                        | `{ $ref: "#/definitions/featureFlags" }` |
| `annotations`           | Object (Optional)      | Arbitrary metadata (e.g., `team: "backend"`, `version: "1.2"`).                                           | `{ owner: "DevOps" }`                |

**Example YAML Config Map:**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config-prod
  namespace: default
data:
  LOG_LEVEL: debug
  DB_URL: "postgres://user:secret@db:5432/mydb"
---
apiVersion: v1
kind: Secret
metadata:
  name: db-secret
type: Opaque
data:
  password: base64-encoded-secret
```

---

## **Query Examples**
### **1. Fetching a Single Configuration Value**
**Goal**: Retrieve `LOG_LEVEL` from a ConfigMap.
**Command (Kubernetes):**
```bash
kubectl get configmap app-config-prod -o jsonpath='{.data.LOG_LEVEL}'
```
**Output**:
```
debug
```

### **2. Querying All Configurations for a Pod**
**Goal**: List all environment variables in a running pod.
**Command**:
```bash
kubectl exec -it <pod-name> -- env
```
**Expected Output**:
```
LOG_LEVEL=debug
DB_URL=postgres://...
FEATURE_X=true
```

### **3. Validating Configurations Against a Schema**
**Goal**: Check if a ConfigMap matches a JSON Schema.
**Tool**: Use a validator like [`jsonschema`](https://pypi.org/project/jsonschema/).
**Example Schema (JSON)**:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "LOG_LEVEL": { "type": "string", "enum": ["debug", "info", "warn"] },
    "DB_URL": { "type": "string", "format": "uri" }
  },
  "required": ["LOG_LEVEL"]
}
```
**Validation Script (Python)**:
```python
import jsonschema
from jsonschema import validate

config = {"LOG_LEVEL": "debug", "DB_URL": "postgres://..."}
schema = {...}  # Load schema above

try:
    validate(instance=config, schema=schema)
    print("✅ Valid configuration")
except jsonschema.exceptions.ValidationError as e:
    print(f"❌ Invalid: {e}")
```

### **4. Overriding Configurations via CLI**
**Goal**: Temporarily override a ConfigMap value for debugging.
**Command**:
```bash
kubectl set env deployment/my-app LOG_LEVEL=debug --overwrite
```

---

## **Best Practices**
1. **Use Secrets for Sensitive Data**
   - Avoid hardcoding credentials. Store them in Kubernetes Secrets or managed secrets (e.g., HashiCorp Vault).

2. **Immutable ConfigMaps**
   - Never update ConfigMaps directly in production. Use rolling deployments to spin up new pods with updated configs.

3. **Layered Configuration**
   - Combine defaults (`defaultValues`), overrides (e.g., `--env`), and secrets to create a "config hierarchy."

4. **Monitor Config Changes**
   - Log configuration changes (e.g., using Kubernetes `Event` resources) for auditing.

5. **Idempotency**
   - Design config queries to be idempotent (e.g., avoid race conditions when fetching secrets).

6. **Document Dependencies**
   - Clearly document required ConfigMaps/Secrets for each container (e.g., in `README.md`).

---

## **Related Patterns**
1. **[Service Discovery](https://referenceguide.dev/service-discovery)**
   - Complements Containers Configuration by dynamically resolving dependencies (e.g., service URLs) at runtime.

2. **[Health Checks](https://referenceguide.dev/health-checks)**
   - Ensures containers are ready before accepting traffic, often triggered by configuration readiness checks.

3. **[Canary Deployments](https://referenceguide.dev/canary-deployments)**
   - Gradually rolls out configurations to a subset of users, reducing impact during config changes.

4. **[Feature Flags](https://referenceguide.dev/feature-flags)**
   - Dynamically enables/disables features via configuration, decoupling code changes from deployments.

5. **[Observability with Prometheus](https://referenceguide.dev/prometheus-integration)**
   - Exposes container configurations as metrics (e.g., `config_version`) for monitoring.

---
## **Troubleshooting**
| **Issue**                     | **Diagnostic Command**                                  | **Solution**                                                                 |
|-------------------------------|--------------------------------------------------------|------------------------------------------------------------------------------|
| ConfigMap not applied          | `kubectl describe pod <pod>`                          | Verify `ConfigMap` references in pod spec.                                     |
| Missing environment variable   | `kubectl get env <pod>`                                 | Check for typos or missing `envFrom`/`env` in YAML.                        |
| Secret not decrypted           | `kubectl get secret db-secret -o yaml`                  | Ensure `type: Opaque` and correct `data` encoding.                            |
| Validation failure             | `kubectl logs <pod> | grep "schema"`   | Update schema or config to match required fields.                           |
| Config drift                   | `kubectl diff configmap app-config-prod --local`     | Use GitOps (e.g., ArgoCD) to sync configs with source control.               |

---
## **Schema Tools**
| **Tool**               | **Purpose**                                                                 |
|------------------------|-----------------------------------------------------------------------------|
| [Kubernetes ConfigMap](https://kubernetes.io/docs/concepts/configuration/configmap/) | Manage non-sensitive configurations.                                        |
| [Kubernetes Secret](https://kubernetes.io/docs/concepts/configuration/secret/) | Store sensitive data securely.                                             |
| [Envoy Proxy](https://www.envoyproxy.io/) | Dynamic runtime configuration for service meshes.                          |
| [Consul](https://www.consul.io/)       | Distributed configuration store with health checks.                       |
| [Jsonnet](https://jsonnet.org/)         | Templating language for declarative configurations.                         |

---
## **Example Workflow**
1. **Define Config** (YAML):
   ```yaml
   # configmaps/app-config.yaml
   apiVersion: v1
   kind: ConfigMap
   metadata:
     name: app-config
   data:
     API_KEY: "123abc"
     FEATURE_Y: "false"
   ---
   # secrets/db-secret.yaml
   apiVersion: v1
   kind: Secret
   metadata:
     name: db-secret
   data:
     password: cGFzc3dvcmQxMjNwYXNzd29yZA==
   ```

2. **Deploy**:
   ```bash
   kubectl apply -f configmaps/
   kubectl apply -f secrets/
   ```

3. **Consume in Pod**:
   ```yaml
   # deployment.yaml
   containers:
     - name: app
       image: my-app:latest
       envFrom:
         - configMapRef: { name: app-config }
       env:
         - name: DB_PASSWORD
           valueFrom:
             secretKeyRef: { name: db-secret, key: password }
   ```

4. **Verify**:
   ```bash
   kubectl exec -it my-pod -- env | grep API_KEY
   ```

---
## **Key Takeaways**
- **Separation of Concerns**: Use ConfigMaps for static data, Secrets for sensitive data, and environment variables for dynamic overrides.
- **Validation**: Enforce schema compliance to avoid runtime errors.
- **Immutability**: Treat configs as ephemeral; rebuild containers if configs change.
- **Integration**: Combine with service discovery and feature flags for advanced use cases.

For further reading, refer to the [Kubernetes Configuration Management](https://kubernetes.io/docs/concepts/configuration/) documentation.