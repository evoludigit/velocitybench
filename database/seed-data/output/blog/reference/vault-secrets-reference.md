---
**[Pattern] Vault Secrets Integration Patterns – Reference Guide**
*Version 1.2 | © 2024*

---

### **1. Overview**
Vault Secrets Integration Patterns define standardized ways to securely fetch, rotate, and use secrets (e.g., API keys, DB credentials, certificates) from **HashiCorp Vault** within applications, workflows, or CI/CD pipelines. This guide covers **implementation strategies**, **Vault SDK/API interactions**, and **integration pitfalls** for dynamic secrets management. Best suited for:
- Microservices with short-lived credentials.
- Cloud-native apps (Kubernetes, serverless).
- Hybrid environments (on-prem + cloud).

---

### **2. Schema Reference**
| **Component**               | **Description**                                                                 | **Vault API/Integration**                     | **Notes**                          |
|-----------------------------|---------------------------------------------------------------------------------|-----------------------------------------------|-------------------------------------|
| **Auth Methods**            | How to authenticate with Vault before accessing secrets.                          | `auth/approle`, `auth/kubernetes`, `auth/azure` | Prefer least-privilege roles.      |
| **Secret Paths**            | Standardized paths to store secrets (e.g., `kv/v2/data/DB/CREDENTIALS`).         | `kv/v2/` (KV v2), `transit/` (encryption).    | Use namespaces for scope separation.|
| **Lease Duration**          | Time (TTL) a secret is valid before renewal.                                    | `lease` parameter in `read`/`write` calls.    | Default: 1h; adjust per use case.  |
| **Dynamic Secrets**         | Short-lived secrets (e.g., DB connections) with auto-rotation.                    | `generate` (DB secrets engine), `transit`.     | Requires dedicated secrets engine.  |
| **Policy Enforcement**      | Vault policies to restrict access to secrets.                                    | JSON policies (e.g., `path "/kv/data/db/*" { capabilities = ["read"] }`). | Test policies with `vault policy write`. |
| **Integration SDKs**        | Official SDKs for Vault integration (e.g., Python, Go).                          | [HashiCorp Vault SDKs](https://developer.hashicorp.com/vault). | Prefer SDKs over raw HTTP calls.    |
| **Monitoring**              | Logs/auditing for secret access events.                                          | Vault audit logs, OpenTelemetry integration.    | Enable `file`/`syslog` audit backend. |

---

### **3. Query Examples**

#### **3.1. Fetching a Static Secret (KV v2)**
**Scenario**: Retrieve an app configuration secret from KV v2.
**Command**:
```bash
curl --request GET \
     --header "X-Vault-Token: <TOKEN>" \
     https://vault.example.com/v1/kv/data/config/app
```
**SDK (Python)**:
```python
import hvac
client = hvac.Client(url='https://vault.example.com')
secret = client.secrets.kv.v2.read_secret_version(path='config/app')
print(secret.data['data']['password'])
```

#### **3.2. Generating a Dynamic Database Credential**
**Scenario**: Request a short-lived DB password with auto-rotation.
**Command**:
```bash
curl --request POST \
     --header "X-Vault-Token: <TOKEN>" \
     https://vault.example.com/v1/db/creds/myapp/user1 \
     --data '{"ttl": "1h"}'
```
**SDK (Go)**:
```go
import vault "github.com/hashicorp/vault-api"
config := vault.DefaultConfig()
config.Address = "https://vault.example.com"
client, err := vault.New(config)
cred, _ := client.Logical().Read("db/creds/myapp/user1")
fmt.Println(cred.Data["password"])
```

#### **3.3. Encrypting Secrets with Transit Engine**
**Scenario**: Encrypt sensitive data in transit.
**Command**:
```bash
curl --request PUT \
     --header "X-Vault-Token: <TOKEN>" \
     --data '{"plaintext": "sensitive_value"}' \
     https://vault.example.com/v1/transit/encrypt/plain \
     --data-urlencode 'key_name=my_key'
```

#### **3.4. Renewing a Lease**
**Scenario**: Extend a secret’s TTL.
**Command**:
```bash
curl --request POST \
     --header "X-Vault-Token: <TOKEN>" \
     --data '{"lease_id": "<LEASE_ID>"}' \
     https://vault.example.com/v1/auth/approle/renew-self
```

---
### **4. Implementation Patterns**

#### **4.1. Dynamic Credential Rotation**
**Use Case**: Auto-rotate DB credentials for microservices.
**Steps**:
1. **Configure Database Secrets Engine**:
   ```bash
   vault secrets enable database
   vault write database/config/myapp \
     plugin_name=postgresql-database-plugin \
     allowed_roles="myapp-reader" \
     connection_url="postgres://user@example.com:5432/db"
   ```
2. **Define a Role**:
   ```bash
   vault write database/roles/myapp-reader \
     db_name=myapp \
     creation_statements="..." \
     default_ttl=1h
   ```
3. **Request Credentials**:
   ```bash
   vault read database/creds/myapp/user1
   ```

#### **4.2. Service Mesh Integration (Istio/Linkerd)**
**Use Case**: Inject secrets into service mesh sidecars.
**Steps**:
1. **Mount KV Secrets in Sidecar**:
   ```yaml
   # Istio VirtualService extension
   extensions:
     - name: "vault-secrets"
       vault:
         path: "kv/data/app/secrets"
         refresh_interval: "30s"
   ```
2. **Use Envoy Filter** to expose secrets as env vars:
   ```bash
   export VAULT_ADDR="https://vault.example.com"
   export VAULT_TOKEN="..."
   ```

#### **4.3. CI/CD Pipeline Secrets**
**Use Case**: Securely pass secrets to GitHub Actions/GitLab CI.
**Steps**:
1. **Store Secrets in KV**:
   ```bash
   vault kv put ci/github-actions \
     GH_TOKEN=ghp_abc123 \
     DB_PASS=secret123
   ```
2. **Fetch in CI**:
   ```yaml
   # GitHub Actions
   steps:
     - name: Fetch secrets
       run: |
         SECRET=$(curl -s -H "X-Vault-Token: $VAULT_TOKEN" \
           https://vault.example.com/v1/kv/data/ci/github-actions/data/DB_PASS)
   ```

---
### **5. Best Practices**
| **Best Practice**               | **Implementation**                                                                 |
|----------------------------------|------------------------------------------------------------------------------------|
| **Avoid Hardcoding Tokens**      | Use **approle authentication** or **Kubernetes auth** in Kubernetes.               |
| **Minimize TTLs**                | Set TTLs to the **minimum required** (e.g., 5m for API keys).                     |
| **Use Namespaces**               | Organize secrets by **environment** (e.g., `dev/`, `prod/`).                       |
| **Encrypt Secrets in Transit**  | Enable **TLS** (`vault server -dev -listener="https"`).                            |
| **Audit Access**                 | Enable **file/audit logs** and monitor for anomalies (e.g., brute-force attempts). |
| **Automate Rotation**            | Use **Vault’s `db` or `transit` engines** for auto-rotation.                      |
| **Leverage SDKs**                | Use **official SDKs** (e.g., `hvac` for Python) instead of raw HTTP calls.         |

---

### **6. Common Pitfalls & Mitigations**
| **Pitfall**                          | **Root Cause**                          | **Mitigation**                                                                 |
|---------------------------------------|-----------------------------------------|---------------------------------------------------------------------------------|
| Secrets Leaked in Logs               | Overly permissive policies.              | Use **dynamic credentials** + strict policies (`capability = ["read"]`).         |
| Long-Lived Secrets                   | Default TTLs too long.                   | Set **custom TTLs** (e.g., 1h) and enable renewal.                                |
| Auth Token Exhaustion                | Token not rotated.                       | Use **approle+short-lived tokens** or **Kubernetes auth**.                       |
| Unintended Policy Leaks              | Policy written incorrectly.              | **Test policies** (`vault policy read -format=json`) before applying.             |
| Secrets Engine Not Configured        | Missing `database`/`transit` setup.     | Enable engines **before** creating secrets (`vault secrets enable database`).     |

---

### **7. Related Patterns**
- **[Pattern] Zero-Trust Networking** – Combine Vault with **mutual TLS** or **SPIFFE**.
- **[Pattern] Policy as Code** – Use **Terraform Providers** or **Open Policy Agent (OPA)** for Vault policies.
- **[Pattern] CI/CD Secrets Management** – Integrate Vault with **ArgoCD**, **Flux**, or **Spinnaker**.
- **[Pattern] Certificate Management** – Use Vault’s **PKI Engine** for TLS cert auto-rotation.
- **[Pattern] Hybrid Cloud Secrets** – Sync Vault secrets across **AWS/GCP/Azure** via **Consul Connect**.

---
### **8. References**
- [Vault KV Secrets Engine Docs](https://developer.hashicorp.com/vault/docs/secrets/kv)
- [Database Secrets Engine](https://developer.hashicorp.com/vault/docs/secrets/dynamic/db)
- [Vault SDKs](https://developer.hashicorp.com/vault/docs/platform/sdks)
- [Istio-Vault Integration](https://istio.io/latest/docs/tasks/security/vault-integration/)