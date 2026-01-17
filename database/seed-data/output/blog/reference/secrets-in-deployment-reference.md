---
# **[Pattern] Secrets in Deployment Reference Guide**

---

## **1. Overview**
The **Secrets in Deployment** pattern addresses the secure handling, storage, and retrieval of sensitive credentials (e.g., API keys, database passwords, encryption keys) during CI/CD pipelines, application deployments, and runtime execution. Poorly managed secrets risk exposure via configuration files, version control, or misconfigured cloud environments. This pattern ensures compliance with security best practices by enforcing encryption, access controls, and auditability—while minimizing manual secret handling.

Key principles include:
- **Never hardcode** secrets in source code or immutable artifacts.
- Use **temporary, short-lived credentials** where possible (e.g., ephemeral tokens).
- Implement **least-privilege access** and **role-based permissions** for secrets.
- Automate secret injection using **secure vaults** (e.g., AWS Secrets Manager, HashiCorp Vault, Azure Key Vault).
- Rotate secrets **regularly** and monitor for anomalies.

This guide covers implementation techniques, schema design, example workflows, and integration with related patterns.

---

## **2. Schema Reference**
The following tables define the core components of the Secrets in Deployment pattern, including roles, inputs, and outputs.

### **2.1 Core Schema: Secrets Management Workflow**
| **Component**       | **Description**                                                                                     | **Required Fields**                                                                 |
|---------------------|-----------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| **Secrets Vault**   | Centralized service for storing and managing secrets.                                            | `vault_name`, `secret_backend` (e.g., `kv`, `database`)                            |
| **Secret Path**     | Hierarchical namespace within the vault for categorizing secrets.                                 | `namespace` (e.g., `prod/app1`), `key`                                              |
| **Secret Template** | Structured definition of secrets (e.g., YAML or JSON) used for dynamic injection.               | `template_version`, `placeholder` (e.g., `{{.DB_PASSWORD}}`), `secret_type`        |
| **Deployer Role**   | Identity or service account with permissions to access secrets.                                  | `role_name`, `vault_access_policy`, `secret_lease_ttl` (secs)                     |
| **Secret Injection Policy** | Rules for when and how secrets are injected (e.g., post-build, pre-deploy).             | `trigger` (e.g., "on_push", "manual"), `scope` (e.g., "pod", "function")           |
| **Audit Trail**     | Log of secret access and usage for compliance.                                                    | `timestamp`, `secrets_accessed`, `user_agent`, `action` (e.g., "read", "revoke") |

---

### **2.2 Example Vault Configuration (AWS Secrets Manager)**
| **Field**          | **Description**                                                                                     | **Example Value**                          |
|--------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------|
| `secret_name`      | Unique identifier for the secret.                                                                | `prod/db_password_2024`                    |
| `secret_string`    | Base64-encoded sensitive data.                                                                     | `dGVzdA==` (binary-encoded "test")        |
| `arn`              | ARN for access control policies.                                                                  | `arn:aws:secretsmanager:us-east-1:123456789:secret:prod/db_password_2024` |
| `rotation_lambda`  | ARN of a Lambda function for automatic rotation.                                                | `arn:aws:lambda:us-east-1:123456789:function:rotate_db_password` |
| `description`      | Human-readable purpose of the secret.                                                             | "PostgreSQL admin password for prod app"  |

---

### **2.3 Secret Injection Schema (Kubernetes Manifest)**
| **Field**          | **Description**                                                                                     | **Example**                              |
|--------------------|-----------------------------------------------------------------------------------------------------|------------------------------------------|
| `spec.template.spec.env` | Secrets mounted as environment variables to containers.                                              | `name: DB_PASSWORD, valueFrom: {secretKeyRef: {name: db-secret, key: password}}` |
| `volumes`          | Secrets mounted as files in a pod's filesystem.                                                     | `name: secrets-volume, secret: {secretName: app-keystore}` |
| `serviceAccountName` | Role-based access control (RBAC) binding for Kubernetes secrets.                                  | `app-secret-reader`                     |
| `annotations`      | Metadata for audit/labeling (e.g., `secrets.knative.dev/inject=true`).                          | `{"secrets.knative.dev/inject": "true"}` |

---

## **3. Implementation Details
### **3.1 Secrets Injection Strategies**
| **Strategy**               | **Use Case**                                                                                     | **Tools/Examples**                                                                 |
|----------------------------|-------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| **Vault Agent Sidecar**    | Inject secrets dynamically into running containers.                                              | HashiCorp Vault Agent (Kubernetes sidecar)                                        |
| **Immutable Secrets**      | Embed secrets in deployment artifacts (e.g., Helm charts) with encryption at rest.              | Kubernetes Secrets + Sealed Secrets (Bitnami)                                    |
| **Runtime Token Exchange** | Fetch short-lived tokens (e.g., OAuth) during deployment.                                        | AWS STS, Azure Managed Identity, OIDC tokens                                    |
| **CI/CD Pipeline Injection** | Inject secrets during build/deploy (e.g., Jenkins, GitHub Actions).                           | GitHub Secrets (Actions), CircleCI ENV vars                                      |

---

### **3.2 Best Practices**
- **Encryption**:
  - Encrypt secrets in transit (TLS) and at rest (AES-256).
  - Use **cloud provider key management** (e.g., AWS KMS, Azure Key Vault) for master keys.
- **Access Control**:
  - Enforce **principle of least privilege**: Grant access only to necessary roles/services.
  - Use **attribute-based access control (ABAC)** for dynamic policies (e.g., time-based access).
- **Rotation**:
  - Rotate **credential-based secrets** (e.g., passwords) every 90 days.
  - Use **automated rotation** (e.g., AWS Secrets Manager) for critical secrets.
- **Audit & Compliance**:
  - Log all secret access with **immutable audit trails** (e.g., AWS CloudTrail).
  - Integrate with **SIEM tools** (e.g., Splunk, Datadog) for anomaly detection.

---

## **4. Query Examples**
### **4.1 Querying Secrets from a Vault (AWS CLI)**
Retrieve a secret from AWS Secrets Manager:
```bash
aws secretsmanager get-secret-value \
    --secret-id prod/db_password_2024 \
    --query SecretString \
    --output text
```

### **4.2 Dynamically Injecting Secrets into Kubernetes (Helm)**
Edit a Helm chart to reference secrets:
```yaml
# values.yaml
app:
  db:
    password: {{ .Values.secrets.db_password }}
```
Deploy with secrets override:
```bash
helm upgrade --install my-app ./charts \
    --set secrets.db_password=$(aws secretsmanager get-secret-value --secret-id prod/db_password_2024 --query SecretString --output text)
```

### **4.3 Rotating a Secret (HashiCorp Vault)**
Rotate a dynamic database password:
```bash
vault write database/rotate/password/postgres \
    username=app_user \
    password=app_password
```

### **4.4 Checking Secret Access Logs (AWS CloudTrail)**
Filter for secret access events:
```bash
aws cloudtrail lookup-events \
    --lookup-attributes AttributeKey=EventName,AttributeValue=GetSecretValue
```

---

## **5. Error Handling & Troubleshooting**
| **Issue**                          | **Root Cause**                                                                 | **Solution**                                                                       |
|-------------------------------------|---------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Permission Denied**               | Incorrect IAM role or RBAC binding.                                          | Verify `vault_policies` in AWS/Vault or Kubernetes `RoleBinding` rules.           |
| **Secret Not Found**                | Incorrect `secret_id` or namespace.                                           | Use `aws secretsmanager list-secrets` or `vault secrets list`.                     |
| **Rotation Failure**                | Lambda function or external service timeout.                                  | Increase `rotation_lambda` timeout or check CloudWatch Logs.                      |
| **Secret Leak in Git**              | Accidental commit of secrets.                                                 | Use `.gitignore` for `*.env` files. Scan repos with `git-secrets` or Snyk.       |
| **Immutable Secrets Expired**      | Secret injected via `SealedSecrets` but not updated post-deploy.              | Recreate sealed secrets or use dynamic injection (Vault Agent).                    |

---

## **6. Related Patterns**
| **Pattern**                          | **Description**                                                                                     | **When to Use**                                                                     |
|--------------------------------------|-----------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| **[Configuration as Code](https://example.com/config-as-code)** | Centralize app configuration in version-controlled files (e.g., YAML/JSON).                     | When secrets are part of a larger config (e.g., app settings + credentials).        |
| **[Blue/Green Deployment](https://example.com/blue-green)**    | Zero-downtime deployments using duplicate environments.                                              | To safely test secrets in staging before promotion.                                |
| **[Canary Releases](https://example.com/canary)**             | Gradually roll out secrets to a subset of traffic.                                                 | For A/B testing secrets (e.g., new API keys).                                      |
| **[Infrastructure as Code (IaC)](https://example.com/iac)**   | Define secrets in IaC templates (e.g., Terraform, Pulumi).                                         | To enforce consistency across environments.                                       |
| **[Observability for Secrets](https://example.com/observability)** | Monitor secret usage and failures via logs/metrics.                                              | To detect and respond to unauthorized access or leaks.                           |

---

## **7. References**
- **AWS**: [Secrets Manager Best Practices](https://docs.aws.amazon.com/secretsmanager/latest/userguide/best-practices.html)
- **HashiCorp**: [Vault Dynamic Secrets](https://www.vaultproject.io/docs/secrets/dynamic)
- **Kubernetes**: [Secrets Documentation](https://kubernetes.io/docs/concepts/configuration/secret/)
- **OWASP**: [Top 10 Secrets Management](https://owasp.org/www-project-top-ten/2021/A02_2021-Cryptographic_Failures.html)