---
# **[Pattern] Secrets Management Best Practices – Reference Guide**
*Version 1.2*
*Last Updated: [Date]*

---

## **1. Overview**
Secrets Management Best Practices ensures sensitive data (e.g., API keys, credentials, tokens) is securely stored, accessed, and rotated without hardcoding or exposing them in plaintext. This pattern reduces risks of data breaches, unauthorized access, and compliance violations by centralizing secrets in encrypted storage, automating injection at runtime, and enforcing rotation policies.

**Core Principles:**
- **Never hardcode** secrets in source code, logs, or version control.
- Use **least-privilege access** to restrict who can view/rotate secrets.
- **Encrypt secrets** at rest and in transit.
- **Rotate secrets** periodically with minimal downtime.
- **Audit access** to detect suspicious activities.

---

## **2. Schema Reference**
Below is a structured breakdown of components and their attributes.

| **Component**               | **Attributes**                                                                 | **Scope**               | **Example Values**                     |
|-----------------------------|-------------------------------------------------------------------------------|-------------------------|----------------------------------------|
| **Secrets Manager**         |                                                                               | Infrastructure          | AWS Secrets Manager, HashiCorp Vault, Azure Key Vault |
| Attribute                  | Value                                                                         |                         |                                        |
| Storage Encryption         | On (AES-256) or Off                                                         | Required                | `true`/`false`                        |
| Access Control             | IAM policies, RBAC, or ABAC                                                  | Required                | `Read: S3:GetObject, Write: S3:PutObject` |
| Secret TTL                 | Time before secrets expire (hours/days)                                      | Optional                | `P1D` (1 day)                          |
| Versioning                 | Track secret revisions for rollback                                          | Optional                | `v1`, `v2`                             |
| **Environment Variables**  |                                                                               | Runtime                  |                                      |
| Injection Method           | Direct assignment, config files, or CI/CD pipeline                           | Required                | `--env-file=secrets.env`               |
| Masking (Runtime)          | Hide secrets when logging (e.g., `DB_PASS=****`)                             | Optional                | `true`                                 |
| **Secret Rotation**        |                                                                               | Process/Tooling          |                                      |
| Rotation Frequency         | Daily, weekly, or on event (e.g., key compromise)                             | Required                | `P7D` (weekly)                        |
| Migration Window           | Downtime for updating services (e.g., 5-minute window)                       | Optional                | `PT30M`                                |
| Audit Logs                 | Track who rotated secrets and when                                           | Required                | `User: alice@example.com, Timestamp: 2024-05-01` |

---

## **3. Implementation Details**

### **3.1 Secrets Manager**
**Purpose:** Centralized, encrypted storage for secrets with strict access controls.

#### **Key Features:**
- **Encryption:** Secrets encrypted at rest (e.g., AWS KMS, HashiCorp Vault’s Transit engine).
- **Access Policies:** Use **IAM roles** (AWS), **RBAC** (Vault), or **ABAC** (Azure) to restrict access.
- **Secrets Versioning:** Maintain multiple versions for rollback (e.g., `v1` → `v2`).
- **Integration:** Sync with CI/CD (Jenkins, GitHub Actions) or orchestration tools (Kubernetes Secrets).

#### **Example Workflow (HashiCorp Vault):**
```plaintext
1. Store secret:
   $ vault kv put secret/db/credentials password="s3cr3t" username="admin"
2. Retrieve secret (with token):
   $ vault kv get secret/db/credentials
```

---

### **3.2 Environment Variables**
**Purpose:** Inject secrets securely at runtime without hardcoding.

#### **Implementation Methods:**
| **Method**               | **Use Case**                          | **Example Command**                          |
|--------------------------|---------------------------------------|---------------------------------------------|
| **Direct Assignment**    | Local development                     | `export DB_PASSWORD="s3cr3t"`               |
| **Config Files**         | Production deployments                | `--env-file=production.env`                 |
| **CI/CD Pipelines**      | Secure variable injection             | `secrets: DB_PASSWORD: "${{ secrets.DB_PASSWORD }}"` (GitHub Actions) |
| **Kubernetes Secrets**   | Containerized environments            | `kubectl create secret generic db-secret --from-literal=password=s3cr3t` |

#### **Best Practices:**
- **Mask secrets** in logs/outputs (e.g., `DB_PASSWORD=****`).
- **Use vaults** (e.g., AWS Parameter Store) for dynamic secrets.
- **Validate injection** in tests (e.g., `assert db_password is not None`).

---

### **3.3 Secret Rotation**
**Purpose:** Automate secret replacement to limit exposure windows.

#### **Rotation Strategies:**
| **Strategy**              | **When to Use**                          | **Tools**                                |
|---------------------------|------------------------------------------|------------------------------------------|
| **Time-Based**            | Fixed intervals (e.g., monthly)          | AWS Secrets Manager, Vault Auto-Rotation |
| **Event-Based**           | On breach detection or key expiry       | AWS Lambda triggers, Vault Policies      |
| **Usage-Based**           | After N accesses (e.g., 100 requests)    | Custom scripts + monitoring (Prometheus) |

#### **Example (AWS Secrets Manager):**
1. **Enable rotation** in the AWS Console:
   - Select a rotation lambda (e.g., RDS, DocDB).
   - Set `rotation_lambda_arn`.
2. **Trigger rotation:**
   ```bash
   aws secretsmanager update-secret --secret-id "db/credentials" --rotation-lambda-arn "arn:aws:lambda:us-east-1:123456789012:function:rotate-db-secret"
   ```

#### **Downtime Mitigation:**
- **Blue-green deployments:** Route traffic to new secrets gradually.
- **Short-lived tokens:** Use OAuth2 refresh tokens (e.g., 4-hour expiry).

---

## **4. Query Examples**
### **4.1 Querying Secrets (CLI)**
**HashiCorp Vault:**
```bash
# List all secrets in a path
vault kv list secret/db/
# Output:
  db/credentials
  db/backup_keys

# Get a specific secret
vault kv get secret/db/credentials
```

**AWS CLI:**
```bash
# Retrieve a secret
aws secretsmanager get-secret-value --secret-id "db/credentials" --query SecretString --output text
# Output:
{"username":"admin","password":"s3cr3t"}
```

---

### **4.2 Rotating Secrets (CI/CD)**
**GitHub Actions Example:**
```yaml
jobs:
  rotate-secret:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Rotate DB password
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_KEY }}
        run: |
          NEW_PASSWORD=$(openssl rand -base64 32)
          aws secretsmanager update-secret --secret-id "db/credentials" \
            --secret-string "{\"password\": \"$NEW_PASSWORD\"}"
```

---

### **4.3 Auditing Access**
**AWS CloudTrail Example:**
```bash
# Query CloudTrail for secret access
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue="GetSecretValue" \
  --max-results 10
# Output:
  {
    "EventName": "GetSecretValue",
    "UserIdentity": {
      "Type": "IAMUser",
      "UserName": "alice@example.com"
    },
    "EventTime": "2024-05-01T12:00:00Z"
  }
```

---

## **5. Related Patterns**
| **Pattern**                          | **Description**                                                                 | **When to Use**                          |
|--------------------------------------|---------------------------------------------------------------------------------|------------------------------------------|
| **Infrastructure as Code (IaC)**     | Define secrets managers via Terraform/CloudFormation.                            | Provisioning secure environments.        |
| **Zero Trust Networking**            | Assume breach; enforce least-privilege access to secrets.                       | High-security environments.              |
| **Audit Logging**                    | Log all secret access for compliance (e.g., GDPR, HIPAA).                      | Regulated industries.                    |
| **Service Mesh (e.g., Istio)**       | Inject secrets dynamically into microservices using mTLS.                       | Kubernetes-based architectures.          |
| **Key Rotation for Encryption**      | Rotate encryption keys (e.g., RSA) separately from credentials.                 | Long-term data protection.               |

---

## **6. Common Pitfalls & Mitigations**
| **Pitfall**                          | **Mitigation**                                                                 |
|--------------------------------------|-------------------------------------------------------------------------------|
| Hardcoding secrets in code.          | Use `envsubst` or templating (e.g., Helm) to inject secrets at deploy time.   |
| Over-permissive IAM roles.           | Apply the principle of least privilege; use AWS IAM Access Analyzer.          |
| No rotation policy.                  | Configure rotation via the secrets manager (e.g., Vault’s `path="secret/*"`).  |
| Secrets leaked in logs.              | Use masking (e.g., `log-secrets=false` in Vault) or tools like `splunk mask`.  |
| Manual rotation errors.              | Automate with CI/CD (e.g., GitHub Actions) or serverless functions (AWS Lambda). |

---

## **7. Tools & Providers**
| **Tool/Provider**               | **Features**                                                                   | **Cost**                | **Best For**                     |
|----------------------------------|-------------------------------------------------------------------------------|-------------------------|----------------------------------|
| **AWS Secrets Manager**          | Auto-rotation, IAM integration, CloudTrail logging.                           | Pay-per-use (~$0.40/month) | AWS-native workloads.             |
| **HashiCorp Vault**              | Dynamic secrets, ABAC, multi-cloud support.                                   | Enterprise-only         | Hybrid/cloud environments.        |
| **Azure Key Vault**              | RBAC, managed identities, Certificate Manager.                                | Included in Azure plan  | Microsoft ecosystem.              |
| **Google Secret Manager**        | Serverless, IAM-based access, audit logs.                                     | Pay-per-use (~$0.02/secret) | GCP workloads.                   |
| **HashiCorp Boundary**           | Remote secret access with SSH/gRPC.                                            | Open-source             | On-prem or air-gapped environments. |

---

## **8. References**
1. [AWS Secrets Manager Documentation](https://docs.aws.amazon.com/secretsmanager/)
2. [HashiCorp Vault Secrets Management](https://www.vaultproject.io/docs/secrets/)
3. [NIST SP 800-63B: Digital Identity Guidelines](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-63B.html)
4. [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)