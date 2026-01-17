# **[Pattern] Serverless Configuration: Reference Guide**

---

## **Overview**
The **Serverless Configuration** pattern provides a centralized, dynamic, and scalable way to manage settings, secrets, and environment-specific parameters for serverless applications. Unlike traditional configuration files (e.g., JSON/YAML), this pattern leverages infrastructure-as-code (IaC) tools like AWS Systems Manager (SSM), AWS Secrets Manager, or Terraform to:
- Store configurations securely in cloud-native repositories.
- Apply environment-specific overrides (e.g., `dev`, `staging`, `prod`).
- Dynamically inject configurations at runtime without redeploying functions or containers.
- Integrate with CI/CD pipelines for seamless validation and rollback.

This guide covers core concepts, schema standards, query methods, and integration patterns for implementing Serverless Configuration effectively.

---

## **Key Concepts**

| **Term**               | **Definition**                                                                 | **Use Case Example**                                                                 |
|-------------------------|-------------------------------------------------------------------------------|-------------------------------------------------------------------------------------|
| **Configuration Source** | Where settings are stored (e.g., SSM Parameter Store, Secrets Manager, DynamoDB). | Store API keys in AWS Secrets Manager; environment variables in GitHub Actions.     |
| **Environment Profile**  | Logical grouping of settings (e.g., `dev`, `qa`, `prod`) with fallbacks.       | Override `DB_HOST` for `prod` but inherit `DEFAULT_TIMEOUT` from `dev`.           |
| **Parameter Hierarchy** | Nested key-value pairs (e.g., `/app/settings/db/host`) for modularity.         | Separate database settings from feature flags.                                      |
| **Dynamic Reference**   | Runtime substitution of configuration values (e.g., `${SSM:/app/timeout}`).    | Use SSM parameters in Lambda environment variables or Kubernetes configs.          |
| **Encryption at Rest**  | Encrypted storage (e.g., KMS keys for SSM) to protect sensitive data.        | Store API credentials encrypted by AWS KMS.                                          |
| **Versioning**          | Track changes to configurations (e.g., SSM parameter versioning, Terraform state). | Roll back to a previous `DATABASE_URL` if a deploy fails.                           |

---

## **Schema Reference**

### **1. Core Schema (JSON/YAML Format)**
Configurations follow a hierarchical structure with **mandatory** (denoted `*`) and **optional** fields.

| **Path**                     | **Type**       | **Description**                                                                 | **Example Value**                          | **Example Usage**                          |
|------------------------------|----------------|---------------------------------------------------------------------------------|-------------------------------------------|--------------------------------------------|
| `/app/*`                     | Object         | Root namespace for all configurations.                                           | `{}`                                       | Group all app settings under `/app`.      |
| `/app/environment*`          | String         | Current environment (`dev`, `staging`, `prod`).                                | `"prod"`                                   | Used for conditional logic.                |
| `/app/settings/*`            | Object         | Top-level settings (e.g., timeouts, retries).                                  | `{ "timeout": 30 }`                        | `app/settings/timeout`.                     |
| `/app/secrets/*`             | Object         | **Encrypted** sensitive data (e.g., passwords, tokens).                        | `{ "db_password": "{encrypted}" }`          | Reference via secrets manager.              |
| `/app/features/*`            | Boolean/String | Feature flags (e.g., `new_ui_enabled`).                                         | `"true"`                                   | Enable/disable features dynamically.       |
| `/app/fallback/*`            | Any            | Default values if a parameter is missing.                                        | `{ "max_retries": 3 }`                   | Override in environment-specific configs.  |
| `/app/version`               | String         | Semantic version of the config schema.                                          | `"1.2.0"`                                  | Validate compatibility during runtime.      |

---

### **2. Environment-Specific Overrides**
Override settings per environment using a suffix (e.g., `/app/settings/db/dev`).

| **Path**                     | **Type**       | **Description**                                                                 | **Example**                                  |
|------------------------------|----------------|---------------------------------------------------------------------------------|----------------------------------------------|
| `/app/settings/db*`          | Object         | Database configurations.                                                         | `{ "host": "db.example.com", "port": 5432 }`  |
| `/app/settings/db/dev`       | Object         | Overrides for `dev` environment.                                                 | `{ "host": "dev-db.example.com" }`           |
| `/app/secrets/api_key/prod*` | String         | Environment-specific secrets (stored encrypted).                                | `"{encrypted}"` (decrypted at runtime)       |

**Rule**: Lower-priority keys override higher-priority ones (e.g., `dev` > `app`).

---

### **3. Secrets Management Schema**
For sensitive data (e.g., API keys), use a dedicated schema with metadata.

| **Field**               | **Type**       | **Description**                                                                 | **Example**                          |
|-------------------------|----------------|---------------------------------------------------------------------------------|--------------------------------------|
| `arn`                   | String*        | AWS ARN of the secret (for Secrets Manager).                                     | `"arn:aws:secretsmanager:us-east-1:123456789012:secret:app-db-password"` |
| `last_updated`          | String (ISO8601)| Timestamp of the last update.                                                     | `"2023-10-15T12:00:00Z"`              |
| `expiry_date`           | String         | Scheduled expiry (optional).                                                      | `"2024-01-15"`                        |
| `description`           | String         | Purpose of the secret.                                                            | `"Database password forProductionDB"`  |
| `value`                 | String*        | Encrypted value (decrypted by application).                                      | `{encrypted: "AQIC..."}`              |

---
## **Implementation Details**

### **1. Storage Choices**
| **Service**               | **Best For**                          | **Pros**                                  | **Cons**                              |
|---------------------------|----------------------------------------|-------------------------------------------|---------------------------------------|
| **AWS SSM Parameter Store** | Non-sensitive config (e.g., timeouts). | Native Lambda integration, low cost.      | No built-in versioning for strings.   |
| **AWS Secrets Manager**   | Sensitive data (e.g., passwords).     | Automatic rotation, KMS encryption.       | Higher cost than SSM.                 |
| **Terraform Remote State** | CI/CD pipeline configs.                | Version-controlled, multi-environment.    | Requires Terraform setup.             |
| **DynamoDB**              | High-frequency updates (e.g., A/B tests). | Atomic updates, low-latency reads.        | Overkill for static configs.          |
| **HashiCorp Vault**       | Enterprise secrets management.        | Fine-grained access control.              | Complex setup.                       |

---
### **2. Runtime Injection Methods**
Inject configurations into serverless functions (e.g., AWS Lambda) via:

#### **A. Environment Variables**
```ini
# AWS Lambda example (Terraform)
resource "aws_lambda_function" "example" {
  environment {
    variables = {
      DB_HOST     = data.aws_ssm_parameter.db_host.value
      API_KEY     = aws_secretsmanager_secret_version.api_key_secret.value
    }
  }
}
```

#### **B. Lambda Layers**
- Bundle configurations in a Layer shared across functions.
- Example: Store `/opt/config/settings.json` with dynamic paths.

#### **C. API Gateway + Lambda Proxy**
- Fetch configs at request time (e.g., from DynamoDB).
- Useful for A/B testing or user-specific overrides.

#### **D. Custom Runtimes (e.g., Node.js)**
```javascript
// Example using AWS SDK to fetch SSM parameters
const { SSMClient, GetParameterCommand } = require("@aws-sdk/client-ssm");

const client = new SSMClient({ region: "us-east-1" });
const config = (await client.send(
  new GetParameterCommand({
    Name: "/app/settings/timeout",
    WithDecryption: true,
  })
)).Parameter.Value;
```

---
### **3. Validation & Testing**
- **Schema Validation**: Use OpenAPI or JSON Schema to enforce structure.
  ```yaml
  # Example OpenAPI schema snippet
  definitions:
    Config:
      type: object
      properties:
        timeout:
          type: integer
          minimum: 1
  ```
- **Unit Tests**: Mock SSM/DynamoDB responses.
  ```python
  # Python (using boto3-mock)
  from moto import mock_ssm
  import boto3

  @mock_ssm
  def test_db_config():
      ssm = boto3.client("ssm")
      ssm.put_parameter(Name="/app/settings/db/host", Value="test-host", Type="String")
      assert ssm.get_parameter(Name="/app/settings/db/host")["Value"] == "test-host"
  ```
- **CI/CD Gates**: Block deployments if configs are invalid (e.g., missing `ENVIRONMENT`).

---

## **Query Examples**

### **1. Fetching from AWS SSM**
```bash
# AWS CLI: Get a single parameter
aws ssm get-parameter --name "/app/settings/timeout" --with-decryption

# AWS CLI: Get all under a path (e.g., /app/settings)
aws ssm get-parameters-by-path --path "/app/settings/"
```

### **2. Fetching from Secrets Manager**
```bash
# Get a secret version
aws secretsmanager get-secret-value --secret-id "app/db-password" --version-stage "AWSCURRENT"

# List all secrets (filter by name)
aws secretsmanager list-secrets --query "SecretList[?contains(Name, ':password')]"
```

### **3. Terraform Example (Dynamic SSM Fetch)**
```hcl
# Fetch SSM parameter and use in Lambda
data "aws_ssm_parameter" "db_url" {
  name = "/app/settings/db/url"
}

resource "aws_lambda_function" "app" {
  environment {
    variables = {
      DB_URL = data.aws_ssm_parameter.db_url.value
    }
  }
}
```

### **4. Dynamic Reference in Kubernetes (Helm)**
```yaml
# values.yaml
db:
  host: {{ tpl $.Values.app.configs.db.host . }}
  port: {{ .Values.app.configs.db.port | default "5432" }}

# Use Helm’s `--set` with external configs
helm install my-app ./chart \
  --set app.configs.db.host="$SSM_DB_HOST"
```

---

## **Related Patterns**

| **Pattern**                     | **Description**                                                                 | **When to Use**                                      |
|----------------------------------|---------------------------------------------------------------------------------|------------------------------------------------------|
| **Feature Flags**                | Toggle features dynamically (e.g., `feature/new_ui` in configs).               | Gradual rollouts, experiments.                      |
| **Canary Releases**              | Route traffic based on config flags (e.g., `traffic_percentage: 10`).          | Blue-green deployments.                              |
| **Infrastructure as Code (IaC)** | Define configs alongside infrastructure (e.g., Terraform modules).           | Consistency across environments.                    |
| **Observability-Driven Config**  | Log/config correlation (e.g., `logs: {level: "DEBUG"}`).                       | Debugging distributed systems.                      |
| **Multi-Tenant Isolation**       | Scope configs per tenant (e.g., `/tenants/123/settings`).                    | SaaS applications.                                   |
| **Secret Rotation**              | Automate secret updates (e.g., AWS Secrets Manager rotation lambdas).          | Reducing credential exposure.                      |

---

## **Best Practices**

1. **Least Privilege**:
   - Grant Lambda functions only the SSM/Secrets Manager permissions they need.
   ```json
   # IAM Policy Example
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": ["ssm:GetParameter"],
         "Resource": "arn:aws:ssm:us-east-1:123456789012:parameter/app/settings/*"
       }
     ]
   }
   ```

2. **Avoid Hardcoding**:
   - Never commit secrets or env-specific configs to version control.

3. **Use Fallbacks**:
   - Define defaults in `/app/fallback` to avoid runtime errors for missing keys.

4. **Audit Trails**:
   - Enable cloud trail logging for SSM/Secrets Manager to track changes.

5. **CI/CD Integration**:
   - Validate configs in pipelines (e.g., Terraform `validate` or custom scripts).

6. **Document Schema**:
   - Maintain a `CONFIG_SCHEMA.md` file with all paths and examples.

---
## **Troubleshooting**

| **Issue**                          | **Cause**                                  | **Solution**                                                                 |
|-------------------------------------|--------------------------------------------|------------------------------------------------------------------------------|
| **Missing Parameter Error**         | Key not found in SSM/DynamoDB.             | Check the path; use fallback values.                                         |
| **Permission Denied**               | IAM role lacks `ssm:GetParameter` access.   | Attach the correct policy to the Lambda execution role.                      |
| **Caching Stale Configs**           | Lambda reuses old environment variables.   | Use AWS Lambda Layers or fetch configs at runtime.                           |
| **Secrets Not Decrypted**           | Missing `WithDecryption: true` in SDK call. | Ensure the AWS SDK/KMS policy allows decryption.                             |
| **High Latency on Config Fetch**    | SSM/DynamoDB throttled.                   | Increase concurrency limits or cache locally (e.g., Redis).                 |

---
## **Example Workflow (AWS Lambda + SSM)**

1. **Store Config**:
   ```bash
   aws ssm put-parameter --name "/app/settings/api/timeout" --value "30" --type "String"
   ```

2. **Lambda Function (`index.js`)**:
   ```javascript
   const { SSMClient, GetParameterCommand } = require("@aws-sdk/client-ssm");

   exports.handler = async (event) => {
     const client = new SSMClient({ region: process.env.AWS_REGION });
     const timeout = await client.send(
       new GetParameterCommand({ Name: "/app/settings/api/timeout", WithDecryption: true })
     ).Parameter.Value;

     return { statusCode: 200, body: `API timeout set to ${timeout}s` };
   };
   ```

3. **IAM Role Policy**:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": ["ssm:GetParameter"],
         "Resource": "arn:aws:ssm:us-east-1:123456789012:parameter/app/settings/api/*"
       }
     ]
   }
   ```

---
## **Conclusion**
The **Serverless Configuration** pattern enables scalable, secure, and dynamic settings management for serverless apps. By leveraging cloud-native services like SSM, Secrets Manager, or DynamoDB, you can:
- Eliminate hardcoded configurations.
- Support multi-environment deployments with minimal overhead.
- Inject secrets and settings without redeploying functions.

**Next Steps**:
1. Start with SSM for non-sensitive configs.
2. Use Secrets Manager for credentials and rotate them automatically.
3. Integrate CI/CD pipelines to validate configs before deployment.
4. Monitor for stale or missing parameters.