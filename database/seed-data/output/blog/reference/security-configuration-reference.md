# **[Pattern] Security Configuration Reference Guide**

---

## **Overview**
The **Security Configuration Pattern** ensures that application and infrastructure settings are hardened against common vulnerabilities and compliance requirements. This pattern enforces systematic security policies—such as encryption, authentication, access control, and audit logging—via configuration templates, secrets management, and automated validation. Implementing this pattern reduces attack surfaces, aligns with frameworks (e.g., CIS Benchmarks, NIST SP 800-53), and simplifies compliance audits. While suitable for cloud-native, on-premises, and hybrid environments, it requires coordination between DevOps, security teams, and developers to maintain consistency across systems.

---

## **Core Concepts**
| **Concept**               | **Description**                                                                                   | **Key Attributes**                                                                 |
|---------------------------|---------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Policy Enforcement**    | Automation of security settings via configurations (e.g., `security_group`, `IAM policies`).     | - Mandatory vs. recommended rules <br> - Enforcement scope (app, infrastructure)  |
| **Secrets Management**    | Secure storage and rotation of credentials (API keys, db passwords) using tools like Vault.         | - Encryption-at-rest <br> - Least-privilege access <br> - Audit trails             |
| **Compliance Baselines**   | Pre-defined security configurations mapped to standards (e.g., PCI DSS, GDPR).                   | - Versioned templates <br> - Automated drift detection                           |
| **Audit Trails**          | Logging and monitoring of configuration changes to detect tampering.                             | - Immutable logs <br> - Anomaly detection thresholds                              |
| **Multi-Tiered Access**   | Role-based access control (RBAC) for configurations (e.g., admin vs. developer read-only).         | - Just-In-Time (JIT) access <br> - Temporary credentials for CI/CD pipelines      |

---

## **Schema Reference**
Below are standardized configuration schemas for enforcing security policies across environments.

### **1. Security Group Configuration (Cloud Infrastructure)**
| **Field**               | **Type**   | **Description**                                                                                     | **Example Value**                     |
|-------------------------|------------|-----------------------------------------------------------------------------------------------------|----------------------------------------|
| `name`                  | String     | Name of the security group.                                                                          | `"web-server-sg"`                      |
| `description`           | String     | Purpose of the security group.                                                                        | `"Restricts traffic to HTTP/HTTPS only"` |
| `rules`                 | Array      | List of inbound/outbound rules (protocol, port, source IP).                                          | `[{port: 80, direction: "inbound"}]`  |
| `compliance_checks`     | Object     | Mapping to compliance controls (e.g., AWS CIS Benchmark 1.5).                                       | `{rule_id: "1.5.1", status: "pass"}`   |
| `tags`                  | Object     | Metadata for cost allocation or team ownership.                                                     | `{env: "prod", owner: "security-team"}`|

---

### **2. IAM Policy Template**
| **Field**               | **Type**   | **Description**                                                                                     | **Example Value**                     |
|-------------------------|------------|-----------------------------------------------------------------------------------------------------|----------------------------------------|
| `policy_name`           | String     | Human-readable name (e.g., `"read-only-database-roles"`).                                          | `"db-viewer-role"`                    |
| `statements`            | Array      | List of JSON-formatted permissions (Actions, Resources).                                            | `[{Effect: "Allow", Actions: ["s3:GetObject"]}]` |
| `principals`            | Array      | Roles/accounts granted access (e.g., `["arn:aws:iam::123456789012:role/app-deployer"]`).           | `[{type: "AWS", identifier: "app-role"}]`|
| `expiry`                | String     | ISO8601 timestamp for policy rotation.                                                              | `"2024-12-31T23:59:59Z"`              |

---
### **3. Secrets Vault Entry**
| **Field**               | **Type**   | **Description**                                                                                     | **Example Value**                     |
|-------------------------|------------|-----------------------------------------------------------------------------------------------------|----------------------------------------|
| `secret_id`             | String     | Unique identifier (e.g., `db-password-prod`).                                                      | `"api-key-1234"`                      |
| `value`                 | String     | Encrypted secret value (base64-encoded or hashed).                                                 | `"dGVzdGluZw=="`                       |
| `rotation_policy`       | Object     | Frequency and method for rotation (e.g., daily via automaton).                                       | `{interval: "D", max_versions: 5}`     |
| `access_policy`         | Object     | Granular permissions (e.g., `["deployment-pipeline" : "read"]`).                                      | `{users: ["alice"], roles: ["auditor"]}`|

---
### **4. Compliance Baseline Template**
| **Field**               | **Type**   | **Description**                                                                                     | **Example Value**                     |
|-------------------------|------------|-----------------------------------------------------------------------------------------------------|----------------------------------------|
| `standard`              | String     | Framework (e.g., `PCI_DSS_3.2.1`, `NIST_800-53`).                                                   | `"PCI_DSS"`                           |
| `controls`              | Array      | List of control IDs and their status (`pass`, `fail`, `not-applicable`).                              | `[{id: "REQ3.1", status: "pass"}]`    |
| `automation_rules`      | Object     | Scripts/APIs to enforce controls (e.g., `aws_iam_policy_validator`).                                 | `{script: "/opt/security/validate.sh"}`|

---

## **Implementation Steps**
### **1. Define Security Policies**
- Use **existing frameworks** (e.g., CIS, NIST) as a baseline.
- Define **custom rules** for organizational requirements (e.g., disable SSH root login).
- **Example Policy:**
  ```yaml
  # security_group_policy.yml
  rules:
    - protocol: tcp
      port: 22
      direction: inbound
      source: ["192.168.1.0/24"]  # Restrict to internal IPs
      compliance: {rule_id: "CIS_1.2"}
  ```

---

### **2. Enforce via Infrastructure-as-Code (IaC)**
- **Terraform Example:**
  ```hcl
  resource "aws_security_group" "app_sg" {
    name_prefix = "app-tier-"
    ingress {
      from_port   = 8080
      to_port     = 8080
      protocol    = "tcp"
      cidr_blocks = ["10.0.0.0/16"]
    }
    tags = {compliance = "PCI_DSS_2.1"}
  }
  ```
- **Ansible Playbook Snippet:**
  ```yaml
  - name: Configure SSH security
    lineinfile:
      path: /etc/ssh/sshd_config
      regex: '^#?PermitRootLogin'
      line: 'PermitRootLogin prohibit-password'
      backup: true
  ```

---

### **3. Integrate Secrets Management**
- **HashiCorp Vault Example:**
  ```bash
  vault write secret/db/credentials \
    username=admin \
    password="$(generate_random_password)" \
    expiration="24h"
  ```
- **Kubernetes Secrets (Encrypted):**
  ```yaml
  apiVersion: v1
  kind: Secret
  metadata:
    annotations:
      vault.hashicorp.com/agent-inject: "true"
      vault.hashicorp.com/role: "db-reader"
  ```

---

### **4. Automate Compliance Checks**
- **Use Tools:**
  - **AWS Config Rules:** Enforce security group best practices.
  - **OpenSCAP (Red Hat):** Validate compliance against benchmarks.
  - **Prisma Cloud:** Continuous security validation for containers.
- **Example OpenSCAP Benchmark:**
  ```bash
  oscap xccdf eval --profile rhel-7-disa-stig --results /tmp/scans \
    /usr/share/xml/scap/ssg/content/ssg-rhel7-disa-stig-xccdf.xml \
    /tmp/
  ```

---

### **5. Monitor and Audit**
- **Logging:**
  - CloudTrail (AWS), Auditd (Linux), or ELK Stack for centralized logs.
- **Alerting:**
  ```json
  # CloudWatch Alarm Policy
  {
    "MetricFilter": {
      "MetricName": "security_group_change",
      "Dimensions": [{"Name": "Service", "Value": "security-group"}],
      "Statistic": "Count",
      "Period": 3600,
      "Threshold": 1
    }
  }
  ```
- **Drift Detection:**
  Tools like **Terraform Plan**, **Chef InSpec**, or **Kube-Bench** flag non-compliant resources.

---

## **Query Examples**
### **1. List Non-Compliant Security Groups (AWS CLI)**
```bash
aws configservice list-compliance-resources-by-config-rules \
  --resource-type AWS::EC2::SecurityGroup \
  --compliance-resource-types all \
  --filter-name rule-name --filter-values CIS_1.2
```

### **2. Check IAM Policy Permissions (AWS CLI)**
```bash
aws iam simulate-principal-policy \
  --policy-arn arn:aws:iam::123456789012:policy/db-reader \
  --action-names "s3:GetObject" "ec2:DescribeInstances" \
  --principal-arn arn:aws:iam::123456789012:user/app-dev
```

### **3. Retrieve Secrets Metadata (Vault CLI)**
```bash
vault list secret/data/db/credentials | jq '.data[] | {secret_id, created_time, ttl}'
```

### **4. Validate Compliance via OpenSCAP (XML Output)**
```bash
oscap xccdf eval --report /tmp/compliance-report.html \
  /usr/share/xml/scap/ssg/content/ssg-rhel7-disa-stig-xccdf.xml \
  /etc/
```

---

## **Error Handling and Troubleshooting**
| **Issue**                          | **Root Cause**                          | **Solution**                                                                                     |
|-------------------------------------|----------------------------------------|--------------------------------------------------------------------------------------------------|
| **Configuration Drift**             | Manual changes override IaC.           | Enable **Terraform State Locks** or **GitOps** (ArgoCD/Flux) for immutable configs.            |
| **Secret Leak**                     | Hardcoded credentials in logs.         | Use **environment variables** or **KMS-sealed secrets** with rotation policies.                 |
| **False Positives in Compliance**   | Overly strict baselines.              | Adjust thresholds (e.g., relax `CIS_1.3` for staging environments).                             |
| **Permission Denied Errors**        | Incorrect IAM Roles.                   | Use **AWS IAM Access Analyzer** or **Chef InSpec** to validate policies before deployment.        |
| **Audit Logs Corruption**           | Disk failure or improper retention.    | Configure **S3 + Glacier** for immutable logs (AWS) or **PurgeView** (GCP).                    |

---

## **Related Patterns**
1. **Zero Trust Architecture**
   - Complements security configuration by enforcing **least-privilege access** across perimeters.
   - *Use together with:* **Identity Federation Pattern**, **Microsegmentation Pattern**.

2. **Secrets Management**
   - Handles dynamic secrets but relies on **Security Configuration** for static policies (e.g., TLS cert rotation).

3. **Infrastructure as Code (IaC)**
   - Provides the **template mechanism** for enforcing security configurations via Terraform, CloudFormation, or Pulumi.

4. **Compliance Automation**
   - Extends **Security Configuration** with **real-time validation** (e.g., **AWS Config Rules**, **Open Policy Agent**).

5. **Runtime Security**
   - Monitors **runtime behavior** (e.g., falcon sensor, Aqua Security) while **Security Configuration** focuses on static settings.

---
## **Tools and Libraries**
| **Category**               | **Tools**                                                                                     | **Purpose**                                                                                     |
|----------------------------|-----------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| **IaC Enforcement**        | Terraform, Pulumi, AWS CDK                                                                      | Deploy hardened configurations via code.                                                        |
| **Secrets Management**     | HashiCorp Vault, AWS Secrets Manager, Azure Key Vault                                       | Store and rotate secrets securely.                                                               |
| **Compliance Scanning**    | OpenSCAP, Prisma Cloud, AWS Config, Chef InSpec                                               | Validate against benchmarks (CIS, NIST).                                                        |
| **Audit Logging**          | AWS CloudTrail, Google Cloud Audit Log, Splunk                                                  | Centralized logging for compliance trails.                                                       |
| **Policy-as-Code**         | OPA/Gatekeeper, Kyverno (Kubernetes), AWS IAM Policy Generator                                  | Enforce policies declaratively.                                                                |

---
## **Best Practices**
1. **Principle of Least Privilege:** Grant minimal access (e.g., **IAM roles** instead of shared keys).
2. **Immutable Infrastructure:** Use IaC to prevent manual drift (e.g., **Terraform + State Locks**).
3. **Automate Rotation:** Enable password/key rotation for secrets (e.g., **Vault Auto-Unseal**).
4. **Context-Aware Policies:** Apply different baselines per environment (e.g., stricter for `prod`).
5. **Regular Audits:** Schedule **compliance scans** (weekly/quarterly) and remediate failures.
6. **Documentation:** Maintain a **policy registry** (e.g., GitHub wiki) for team knowledge sharing.
7. **Incident Response:** Integrate **Security Configuration** with **SIEM** (e.g., Splunk) for anomaly detection.

---
## **Anti-Patterns to Avoid**
- **Manual Configuration:** Avoid ad-hoc changes (e.g., SSH keys set via `puttygen` instead of Vault).
- **Over-Permissive Policies:** Don’t use `*` in IAM rules (e.g., `s3:*` → `s3:GetObject` only).
- **Ignoring Drift:** Let non-compliant resources accumulate without remediation.
- **Hardcoding Secrets:** Never commit credentials to version control (use **`gitignore` + secrets manager**).
- **Silent Failures:** Ensure **audit logs** capture all configuration changes, even failures.

---
## **Example Workflow: Deploying a Compliance-Ready App**
1. **Define:** Write a **Terraform template** with security group rules (CIS-compliant).
2. **Secure:** Store DB credentials in **Vault** with 7-day rotation.
3. **Deploy:** Use **ArgoCD** to sync IaC state with Kubernetes (immutable).
4. **Validate:** Run **OpenSCAP** to scan for CIS benchmarks before promotion to `prod`.
5. **Monitor:** Set up **CloudWatch Alarms** for unauthorized security group changes.

---
## **Further Reading**
- [AWS Security Best Practices](https://docs.aws.amazon.com/wellarchitected/latest/security-pill/security-best-practices.html)
- [CIS Benchmarks](https://www.cisecurity.org/benchmarks/)
- [NIST SP 800-53](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final)
- [OPA/Gatekeeper Policy Samples](https://github.com/open-policy-agent/gatekeeper-library)

---
**Last Updated:** [MM/YYYY]
**Maintainer:** [Team/Contact]