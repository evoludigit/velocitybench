# **[Cloud Configuration] Reference Guide**

---
## **Overview**
The **Cloud Configuration** pattern ensures consistent, secure, and scalable application deployment by managing configuration data external to application code. This pattern decouples configuration from environments (dev/stage/prod) and supports dynamic updates without redeploying the application. Key benefits include:
- **Environment isolation**: Different settings per deployment context.
- **Security**: Sensitive data (API keys, passwords) stored separately.
- **Agility**: Configuration changes applied instantly via cloud services.
- **Auditability**: Centralized tracking of configuration versions and updates.

Cloud Configuration is widely used with **AWS Systems Manager Parameter Store**, **Azure Key Vault**, **Google Cloud Secret Manager**, or **HashiCorp Vault**. It aligns with **Infrastructure as Code (IaC)** principles, such as Terraform or AWS CDK, and integrates with CI/CD pipelines for seamless updates.

---

## **Key Concepts**

| **Concept**               | **Description**                                                                                                                                                                                                 | **Example**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Configuration Store**   | Centralized repository for key-value pairs or structured settings (e.g., JSON/XML). Supports hierarchical organization (e.g., `/app/settings/prod/database`).                          | AWS SSM Parameter Store, Azure Configurations, HashiCorp Vault                                 |
| **Encryption**            | Sensitive data encrypted at rest and in transit. Uses **AWS KMS**, **Azure Key Vault**, or **Google Cloud KMS**.                                                                                         | `database_password = "encrypted:123abc..."` in HashiCorp Vault                                  |
| **Secrets Rotation**      | Automated rotation of credentials (e.g., database passwords) using cloud-native tools.                                                                                                                       | AWS Secrets Manager auto-generates and rotates secrets every 30 days                            |
| **Dynamic Substitution**  | Application injects configuration at runtime via SDKs (e.g., `spring-cloud-config` for Java, `AWS SDK` for .NET).                                                                                          | `${APP_ENV:prod}` → resolves to `prod` at runtime                                                 |
| **Versioning**            | Track changes to configurations (e.g., compare `/app/v1` vs `/app/v2`). Supports rollback to previous versions.                                                                                            | Azure Configurations history shows who modified `/app/settings` and when                      |
| **IAM/Permissions**       | Fine-grained access control via policies (e.g., least-privilege access). Restrict read/write to specific roles.                                                                                            | IAM policy allowing only `dev-team` to read `/app/dev/*`                                         |
| **Synchronization**       | Sync configurations across environments (e.g., deploy `dev` changes to `stage`).                                                                                                                             | Terraform apply updates `/app/settings` in both AWS and GCP via remote state                    |

---

## **Schema Reference**
Below is a standardized schema for Cloud Configuration storage:

| **Field**               | **Type**      | **Description**                                                                                     | **Examples**                                                                                     |
|-------------------------|---------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Key**                 | String        | Unique identifier for the configuration (e.g., `DATABASE_URL`).                                      | `AWS_ACCESS_KEY_ID`, `/app/settings/db/host`                                                   |
| **Value**               | String        | Configuration value (plaintext for non-sensitive data, encrypted otherwise).                        | `"db.example.com:5432"`, `"encrypted:123abc..."`                                                |
| **Type**                | Enum          | `string`, `secureString` (encrypted), `json`, or `binary`.                                           | `secureString` for passwords                                                                   |
| **Path**                | String        | Hierarchical location (e.g., `/prod/apps/webserver`).                                                | `/db/config`, `/api/keys/google`                                                                |
| **Description**         | String        | Human-readable purpose (e.g., "Primary DB connection string").                                      | `"Used by the backend service to connect to PostgreSQL."                                       |
| **Tags**                | List[String]  | Categorization for filtering (e.g., `env:prod`, `team:backend`).                                   | `["database", "prod"]`                                                                         |
| **Last Updated**        | Timestamp     | When the value was modified (ISO 8601 format).                                                     | `2024-05-20T14:30:00Z`                                                                        |
| **Version**             | String        | Semantic version (e.g., `1.2.0`) or auto-generated ID for rollback.                                 | `v20240520`, `abc123-xyz456`                                                                    |
| **Expires At**          | Timestamp     | Time-to-live for ephemeral secrets (e.g., OAuth tokens).                                            | `2024-05-21T14:30:00Z` (auto-rotates afterward)                                                |
| **Encryption Key**      | String        | KMS/Key Vault ARN or alias used for encryption (if applicable).                                      | `arn:aws:kms:us-east-1:123456789012:key/abcd1234`                                              |
| **Metadata**            | Object        | Custom attributes (e.g., `createdBy: "Alice"`).                                                     | `{ "source": "terraform", "owner": "devops@company.com" }                                     |

---

## **Implementation Examples**

### **1. AWS Systems Manager Parameter Store**
#### **Create a Parameter (CLI)**
```bash
aws ssm put-parameter \
  --name "/app/settings/db/host" \
  --value "db.example.com" \
  --type SecureString \
  --key-id "alias/aws/ssm" \
  --overwrite
```
#### **Retrieve a Parameter (Code Example in Python)**
```python
import boto3

ssm = boto3.client('ssm')
response = ssm.get_parameter(
    Name='/app/settings/db/host',
    WithDecryption=True  # For SecureString
)
host = response['Parameter']['Value']
print(f"Database host: {host}")
```

#### **Terraform Declaration**
```hcl
resource "aws_ssm_parameter" "db_host" {
  name    = "/app/settings/db/host"
  type    = "SecureString"
  value   = "db.example.com"
  key_id  = "alias/aws/ssm"
}
```

---

### **2. Azure Key Vault**
#### **Set a Secret (Azure CLI)**
```bash
az keyvault secret set \
  --vault-name MyKeyVault \
  --name DatabasePassword \
  --value "s3cr3tP@ss" \
  --enabled true
```
#### **Access in Application (C#)**
```csharp
using Azure.Identity;
using Azure.Security.KeyVault.Secrets;

var client = new SecretClient(
    new Uri("https://MyKeyVault.vault.azure.net"),
    new DefaultAzureCredential());

KeyVaultSecret secret = await client.GetSecretAsync("DatabasePassword");
Console.WriteLine($"Password: {secret.Value}");
```

#### **Terraform Declaration**
```hcl
resource "azurerm_key_vault_secret" "db_password" {
  name         = "DatabasePassword"
  value        = "s3cr3tP@ss"
  key_vault_id = azurerm_key_vault.example.id
}
```

---

### **3. Google Cloud Secret Manager**
#### **Create a Secret (gcloud CLI)**
```bash
gcloud secrets create DB_PASSWORD \
  --replication-policy="automatic" \
  --data-file=./db_password.txt
```
#### **Fetch a Secret (Node.js)**
```javascript
const { SecretManagerServiceClient } = require('@google-cloud/secret-manager');

const client = new SecretManagerServiceClient();
const [version] = await client.accessSecretVersion({
  name: 'projects/my-project/secrets/DB_PASSWORD/versions/latest',
});

const dbPassword = version.payload.data.toString();
console.log(dbPassword);
```

#### **Terraform Declaration**
```hcl
resource "google_secret_manager_secret" "db_password" {
  secret_id = "DB_PASSWORD"
  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "db_password_version" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = "s3cr3tP@ss"
}
```

---

## **Query Examples**
### **1. List All Configuration Keys (AWS)**
```bash
aws ssm get-parameters-by-path \
  --path "/app/settings/" \
  --recursive
```

### **2. Filter by Tags (Azure)**
```bash
az keyvault secret list \
  --vault-name MyKeyVault \
  --query "[?tags.env == 'prod']"
```

### **3. Dynamic Substitution in Spring Boot**
**`application.yml`:**
```yaml
spring:
  cloud:
    config:
      uri: http://localhost:8888
      name: app-config
      profile: ${SPRING_PROFILES_ACTIVE:prod}

database:
  url: ${DATABASE_URL:jdbc:postgresql://${DB_HOST:localhost}:5432/mydb}
```

**Environment Variable:**
```bash
export DATABASE_URL="jdbc:postgresql://db.example.com:5432/mydb"
```
Spring Cloud Config replaces `${DATABASE_URL}` with the environment variable.

---

## **Best Practices**
1. **Namespace Configuration Keys**
   Use hierarchical paths (e.g., `/env/stage/app/service`) to avoid collisions.
2. **Encrypt Sensitive Data**
   Default to `SecureString` or `secureString` for passwords/API keys.
3. **Least Privilege Access**
   Restrict IAM roles to only required parameters (e.g., `ssm:GetParameters` for `prod/db/*`).
4. **Automate Rotation**
   Enable cloud-native rotation (e.g., AWS Secrets Manager for RDS credentials).
5. **Audit Logs**
   Enable cloud provider logs (e.g., AWS CloudTrail, Azure Monitor) for parameter changes.
6. **Backup Critical Configs**
   Versioned backups (e.g., Azure Configurations export) prevent accidental loss.
7. **Use Infrastructure as Code**
   Declare configurations in Terraform/CDK to ensure consistency across environments.

---

## **Related Patterns**
1. **[Configuration as Code](https://example.com/config-as-code)**
   Treat configurations as version-controlled files (e.g., YAML/JSON templates) synced to cloud stores.
2. **[Feature Flags](https://example.com/feature-flags)**
   Use cloud config to toggle features dynamically (e.g., `FEATURE_NEW_DASHBOARD=true`).
3. **[Canary Deployments](https://example.com/canary-deploys)**
   Deploy configurations per traffic split (e.g., `50%` of users get `/app/v2/settings`).
4. **[Multi-Region Configuration Sync](https://example.com/multi-region-config)**
   Sync configurations across regions using cloud services (e.g., AWS Global Accelerator + SSM).
5. **[Observability for Configs](https://example.com/config-observability)**
   Monitor config changes in real-time with tools like Datadog or Prometheus alerts.

---
## **Troubleshooting**
| **Issue**                     | **Diagnosis**                                                                 | **Solution**                                                                                     |
|-------------------------------|---------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| **Parameter not found**       | Key mismatch or incorrect path (e.g., `/app/settings` vs `/settings/app`).     | Verify path hierarchy; use `get-parameters-by-path` (AWS) or `list` (Azure).                  |
| **Permission denied**         | IAM role lacks `ssm:GetParameters` or `keyvault/secrets/get` permissions.      | Grant least-privilege access; test with `sts:AssumeRole`.                                       |
| **Decryption failure**        | Missing KMS key or incorrect key ID.                                           | Check `EncryptionKey` in schema; validate KMS alias ARN.                                         |
| **Stale configurations**      | Application caching old values.                                                  | Implement short TTL for config cache (e.g., 5 minutes) or force refresh.                        |
| **Versioning conflicts**      | Two teams updated the same path simultaneously.                                | Use optimistic locks or enforce branching (e.g., `/dev/app/v1`, `/prod/app/v1`).                 |

---
## **Tools & Integrations**
| **Tool/Service**               | **Purpose**                                                                 | **Integration**                                                                                     |
|---------------------------------|-----------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| **AWS Systems Manager**         | Parameter store + session manager.                                          | Integrates with EC2, ECS, Lambda via IAM roles.                                                   |
| **Azure Key Vault**             | Secrets management + certificate rotation.                                   | Works with App Service, Kubernetes via Managed Identity.                                           |
| **Google Cloud Secret Manager** | Secure secrets with access controls.                                        | Used by GKE, Cloud Run, and App Engine.                                                             |
| **HashiCorp Vault**             | Enterprise-grade secrets + dynamic secrets.                                    | Syncs with AWS, Azure, or self-managed clusters via CLI/API.                                       |
| **Spring Cloud Config**         | Java/Kotlin apps with centralized config.                                   | Plugins for AWS SSM, Azure, and custom stores.                                                     |
| **Terraform**                   | IaC for configurations.                                                      | Data sources for AWS SSM, Azure Key Vault, and GCP Secret Manager.                                  |
| **Pulumi**                      | Config-as-code with cloud-native SDKs.                                      | Supports AWS SSM, Azure Configurations, and Kubernetes Secrets.                                    |

---
## **Further Reading**
- [AWS SSM Parameter Store Documentation](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html)
- [Azure Key Vault Best Practices](https://docs.microsoft.com/en-us/azure/key-vault/general/best-practices)
- [Google Cloud Secret Manager IAM](https://cloud.google.com/secret-manager/docs/access-control)
- [12-Factor App Config](https://12factor.net/config) – Best practices for cloud-native apps.