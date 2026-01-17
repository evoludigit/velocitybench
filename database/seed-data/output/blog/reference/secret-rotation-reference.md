# **[Pattern] Secrets Rotation Reference Guide**

---

## **Overview**
Secrets rotation is a security best practice to mitigate risks from credential exposure. This pattern standardizes how credentials (e.g., API keys, database passwords, encryption keys) are periodically refreshed or automatically rotated. The process minimizes long-term exposure risks while ensuring uninterrupted service access.

Key benefits:
- **Reduced Risk**: Limits impact of credential leaks.
- **Automation**: Reduces manual intervention and human error.
- **Compliance**: Aligns with security standards (e.g., PCI DSS, NIST).
- **Process Control**: Provides auditability and traceability.

This guide covers implementation strategies, configuration options, and integration considerations for automated and manual rotation.

---

## **1. Key Concepts**

### **Core Components**
| **Term**               | **Definition**                                                                                     |
|-------------------------|---------------------------------------------------------------------------------------------------|
| **Secrets**             | Credentials, tokens, or keys used to access systems (e.g., passwords, API keys).                  |
| **Rotation Policy**     | Rules defining how often secrets are rotated (e.g., daily, monthly).                              |
| **Credential Store**    | Secure vaults (e.g., AWS Secrets Manager, HashiCorp Vault) where secrets are stored.              |
| **Rotation Agent**      | System/service responsible for rotating secrets (e.g., CI/CD pipelines, custom scripts).          |
| **Service Account**     | Non-human identities used by apps to interact with systems.                                        |
| **Audit Log**           | Record of rotation events for compliance and troubleshooting.                                     |

### **Types of Rotation**
| **Type**               | **Description**                                                                                  |
|-------------------------|--------------------------------------------------------------------------------------------------|
| **Automated Rotation**  | Scheduled or event-triggered (e.g., after a password breach).                                   |
| **Manual Rotation**     | Admin-initiated (less common; risk of human error).                                              |
| **Time-Based**          | Secrets expire after a set duration (e.g., 90 days).                                             |
| **Usage-Based**         | Secrets rotate after a defined number of uses (e.g., after 1,000 API calls).                    |
| **On-Breach**           | Secrets rotate immediately if exposed (e.g., via a breach detection system).                      |

---

## **2. Schema Reference**

### **Rotation Policy Schema**
```json
{
  "rotation_policy": {
    "type": "object",
    "properties": {
      "id": { "type": "string", "description": "Unique identifier for the policy." },
      "secrets": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "name": { "type": "string", "description": "Secret name (e.g., 'db_password')." },
            "type": { "type": "string", "enum": ["password", "api_key", "ssh_key"], "description": "Secret type." },
            "rotation_strategy": {
              "type": "object",
              "properties": {
                "interval": { "type": "integer", "description": "Rotation interval in hours (e.g., 720 for 30 days)." },
                "max_uses": { "type": "integer", "description": "Max uses before rotation (optional)." },
                "on_breach": { "type": "boolean", "description": "Enable immediate rotation on exposure." }
              }
            },
            "vault_ref": {
              "type": "object",
              "properties": {
                "provider": { "type": "string", "enum": ["aws", "vault", "azure"], "description": "Vault provider." },
                "path": { "type": "string", "description": "Path to the secret in the vault (e.g., 'dev/db/password')." }
              }
            }
          }
        }
      },
      "audit_settings": {
        "type": "object",
        "properties": {
          "enabled": { "type": "boolean", "description": "Enable audit logging." },
          "log_retention_days": { "type": "integer", "description": "Days to retain logs." }
        }
      }
    },
    "required": ["secrets"]
  }
}
```

---

## **3. Implementation Patterns**

### **A. Automated Rotation with a Secret Manager**
**Use Case**: Periodic rotation of database credentials via AWS Secrets Manager.

#### **Steps**:
1. **Store Secrets**: Upload credentials to AWS Secrets Manager.
2. **Define Rotation Lambda**: Create a Lambda function triggered by CloudWatch Events.
3. **Rotate Secrets**: Lambda fetches the current secret, generates a new one, updates the secret, and injects it into the target service (e.g., RDS).
4. **Audit Logs**: Log rotation events to CloudTrail.

#### **Example Workflow**:
```
[CloudWatch Event] → Trigger Lambda → Fetch Old Secret → Generate New Secret → Update Secret → Update RDS → Log Event
```

#### **Tools**:
- **AWS**: Secrets Manager + Lambda
- **Azure**: Azure Key Vault + Logic Apps
- **Open Source**: HashiCorp Vault + Automated CLI scripts

---

### **B. On-Demand Rotation with CI/CD**
**Use Case**: Rotate secrets during deployment in a CI/CD pipeline.

#### **Steps**:
1. **Trigger Rotation**: On pipeline start (e.g., GitHub Actions), fetch the latest secret from the vault.
2. **Dynamic Injection**: Pass the secret as an environment variable to the deployed service.
3. **Short-Lived Credentials**: Use temporary tokens (e.g., AWS STS, Kubernetes Service Accounts).

#### **Example (GitHub Actions)**:
```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Fetch Secret
        run: |
          SECRET=$(aws secretsmanager get-secret-value --secret-id "prod/db/password" --query SecretString --output text)
          echo "DB_PASSWORD=$SECRET" >> $GITHUB_ENV
      - name: Deploy
        run: |
          export DB_PASSWORD=${{ env.DB_PASSWORD }}
          ./deploy.sh
```

---

### **C. Event-Driven Rotation**
**Use Case**: Rotate secrets immediately after a breach detection.

#### **Steps**:
1. **Monitor for Breaches**: Use tools like AWS GuardDuty or Splunk.
2. **Trigger Rotation**: Send an event to a secrets manager to rotate exposed secrets.
3. **Notify Teams**: Alert security teams via Slack/email.

#### **Example (AWS CloudTrail + Lambda)**:
```python
# Lambda function triggered by CloudTrail
import boto3

def lambda_handler(event, context):
    if "breach_detected" in event:
        client = boto3.client("secretsmanager")
        client.rotate_secret(SecretId="exposed_secret")
        # Send Slack alert
        send_slack_alert("Secret breach detected! Rotation triggered.")
```

---

## **4. Query Examples**

### **Query 1: List All Secrets Under a Policy**
```sql
SELECT name, type, rotation_strategy.interval
FROM secrets_rotation.policies
WHERE policy_id = "prod_db_rotation";
```

### **Query 2: Find Secrets Expired Before a Date**
```sql
SELECT name
FROM secrets_rotation.secrets
WHERE last_rotation < '2023-10-01'
  AND type = 'password';
```

### **Query 3: Audit Logs for Failed Rotations**
```sql
SELECT *
FROM secrets_rotation.audit_logs
WHERE status = 'FAILED'
ORDER BY timestamp DESC
LIMIT 10;
```

---

## **5. Best Practices**

1. **Automate Where Possible**:
   - Use tools like AWS Secrets Manager or HashiCorp Vault to avoid manual errors.
   - Integrate rotation with CI/CD pipelines for deployment consistency.

2. **Short-Term Credentials**:
   - Use temporary tokens (e.g., AWS STS, Kubernetes Service Accounts) for high-risk services.

3. **Monitor and Alert**:
   - Set up alerts for failed rotations (e.g., via Prometheus or Datadog).
   - Log all rotation events for audit trails.

4. **Secret Least Privilege**:
   - Grant minimal permissions to rotation agents (e.g., only "rotate" access).

5. **Backward Compatibility**:
   - Ensure old secrets remain valid until fully replaced (avoid service downtime).

6. **Testing**:
   - Run rotation tests in staging before deploying to production.
   - Validate that services can handle temporary failures during rotation.

---

## **6. Error Handling and Troubleshooting**

| **Issue**                     | **Cause**                                  | **Solution**                                                                 |
|--------------------------------|--------------------------------------------|-----------------------------------------------------------------------------|
| Rotation fails                 | Missing IAM permissions                    | Verify rotation agent has `secretsmanager:RotateSecret` permissions.        |
| Service misconfiguration       | Incorrect secret injection into service    | Check environment variables and config files.                               |
| Audit logs missing            | Logging disabled                          | Enable audit settings in the rotation policy.                              |
| Service downtime               | Old secret still in use                    | Use short-lived credentials or graceful degradation.                        |
| Breach not detected            | Alerting system misconfigured              | Test breach detection workflow with mock events.                           |

---

## **7. Related Patterns**
1. **[Credential Storage Best Practices]**
   - Guidance on securely storing secrets (e.g., encrypted vaults, restricted access).

2. **[Token Revocation]**
   - Strategies for revoking compromised tokens (e.g., OAuth revocation).

3. **[Secrets Scanning]**
   - Tools to detect secrets in code/commits (e.g., GitHub CodeQL, Snyk).

4. **[Just-In-Time Access]**
   - Granting temporary access to secrets (e.g., via AWS IAM roles).

5. **[Key Management for Encryption]**
   - Managing encryption keys alongside secrets (e.g., AWS KMS).

---

## **8. Example Architecture**
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│             │    │             │    │             │    │             │
│   Service   │───▶│ Secrets    │───▶│  Rotation   │───▶│  Audit      │
│   (App)     │    │  Vault     │    │  Lambda    │    │  Logs       │
│             │    │             │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       ↑               ↓               ↑               ↓
       │               │               │               │
┌─────┴─────┐ ┌─────┴─────┐ ┌─────┴─────┐ ┌─────┴─────┐
│ CloudWatch│ │  IAM      │ │   CloudTrail│ │  Slack   │
│ (Scheduling)│ │  Permissions│ │ (Event   │ │ (Alerts) │
└─────────────┘ └─────────────┘ │   Logs)  │ └─────────────┘
                               └─────────────┘
```

---
**References**:
- AWS Secrets Manager [Documentation](https://docs.aws.amazon.com/secretsmanager/)
- HashiCorp Vault [Rotation Docs](https://www.vaultproject.io/docs/secrets/rotation)
- NIST SP 800-63B [Digital Identity Guidelines](https://csrc.nist.gov/publications/detail/sp/800-63b/final)