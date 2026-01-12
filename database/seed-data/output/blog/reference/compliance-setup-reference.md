---
**[Pattern] Reference Guide: Compliance Setup**
*Ensure system alignment with regulatory frameworks, industry standards, and organizational policies.*

---

## **1. Overview**
The **Compliance Setup** pattern centralizes configuration and automation for monitoring, reporting, and enforcing compliance requirements. It streamlines adherence to external regulations (e.g., GDPR, HIPAA) and internal controls by:
- **Standardizing compliance checks** across systems via policy definitions.
- **Automating evidence collection** (logs, audits, metadata) for audits or incidents.
- **Integrating with remediation workflows** (e.g., trigger fixes via CI/CD pipelines).
- **Scaling compliance** from single systems to multi-cloud/multi-domain environments.

This pattern applies to:
- **Security teams** enforcing access controls or data protection policies.
- **DevOps/SRE teams** embedding compliance steps into CI/CD.
- **Compliance officers** managing regulatory change logs.

---

## **2. Schema Reference**
All compliance configurations follow a **domain-specific schema** stored in a centralized repository (e.g., YAML, Terraform, or a compliance-as-code tool like OpenCompliance). The schema enforces a modular structure with:

| **Field**               | **Type**       | **Description**                                                                                     | **Example Value**                          |
|-------------------------|---------------|-----------------------------------------------------------------------------------------------------|--------------------------------------------|
| **`metadata`**          | Object        | Metadata for the compliance rule (e.g., owner, version).                                             | `{"owner": "security-team", "version": "1.0"}`|
| **`name`**              | String        | Unique identifier for the rule (e.g., `gdpr-ds-access`).                                              | `gdpr-ds-access`                           |
| **`description`**       | String        | Human-readable purpose of the rule.                                                                 | `"Audit user access to GDPR-protected data."`|
| **`scope`**             | Array[String] | Systems/services targeted (e.g., `["database", "kubernetes"]`).                                      | `["database", "kubernetes"]`                |
| **`regulations`**       | Array[String] | Compliance frameworks the rule addresses (e.g., `["GDPR", "HIPAA"]`).                                | `["GDPR", "HIPAA"]`                        |
| **`checks`**            | Array[Object] | Defines how to validate compliance.                                                                     | See [Check Schema](#check-schema) below    |
| **`remediation`**       | Object        | Steps to resolve violations (e.g., `automate: true`).                                                 | `{ "automate": true, "tool": "vault-policy" }`|
| **`severity`**          | String        | Impact level (e.g., `high`, `critical`).                                                               | `high`                                     |
| **`last-updated`**      | ISO8601       | Timestamp of the last configuration review.                                                          | `"2024-01-15T10:30:00Z"`                  |

---

### **Check Schema**
Each `check` object defines a validation rule:

| **Field**               | **Type**       | **Description**                                                                                     | **Example**                          |
|-------------------------|---------------|-----------------------------------------------------------------------------------------------------|--------------------------------------|
| **`type`**              | String        | Rule type (e.g., `regex`, `api`, `file-monitor`).                                                   | `"regex"`                            |
| **`criteria`**          | String/Object | Rule-specific logic. For `regex`, use a pattern. For `api`, specify endpoint.                     | `{"regex": "^[A-Za-z0-9]{8,}$"}`       |
| **`target`**            | String        | System/resource to scan (e.g., `env:prod/secret:db-password`).                                         | `{"env": "prod", "secret": "db-password"}` |
| **`frequency`**         | String        | How often to run (e.g., `daily`, `on-change`).                                                       | `daily`                              |
| **`tools`**             | Array[String] | Tools to use (e.g., `["lyft/okteto", "prometheus"]`).                                                 | `["lyft/okteto", "prometheus"]`      |

**Example Check:**
```yaml
checks:
  - type: "regex"
    criteria: ^[A-Za-z0-9]{8,}$
    target: {"env": "prod", "secret": "db-password"}
    tools: ["lyft/okteto"]
```

---

## **3. Implementation Details**
### **3.1. Core Components**
1. **Compliance Repository**
   - Store rule definitions (e.g., Git repo, HashiCorp Vault, or a dedicated compliance DB).
   - Tags rules by `scope`, `regulations`, and `severity`.

2. **Compliance Engine**
   - Parasails rule evaluation (e.g., using **Open Policy Agent** or a custom script).
   - Integrates with:
     - **Data sources**: APIs, file systems, databases (e.g., via Prometheus or Grafana).
     - **Remediation tools**: Vault, Kubernetes admission controllers, or CI/CD plugins.

3. **Audit Logs**
   - Log all compliance events (e.g., violations, fixes) to a centralized system (e.g., Splunk, Datadog).
   - Retain logs per regulatory retention policies (e.g., GDPR’s 7-year requirement).

4. **Alerting**
   - Trigger alerts (e.g., Slack, PagerDuty) for critical violations.
   - Escalate based on `severity` (e.g., `critical` → PagerDuty; `high` → Slack).

---

### **3.2. Example Workflow**
1. **Configure Rule**:
   Add a rule to the compliance repo to enforce **password complexity** (e.g., `gdpr-password-complexity`):
   ```yaml
   checks:
     - type: "regex"
       criteria: ^(?=.*[A-Z])(?=.*[a-z])(?=.*\d).{8,}$
       target: {"env": "prod", "secret": "*-password"}
       frequency: "daily"
   ```

2. **Execute Check**:
   - The compliance engine scans secrets (e.g., Kubernetes secrets) using **lyft/okteto**.
   - Violations trigger alerts if passwords fail the regex.

3. **Remediate**:
   - Automated: Replace weak passwords via **HashiCorp Vault** triggered by OPA.
   - Manual: Notify security teams via Slack for non-automated fixes.

---

## **4. Query Examples**
### **4.1. Querying Violations (CLI)**
Use a tool like `kubectl` or `jq` to filter violations from the compliance engine’s logs:
```bash
# List all high-severity violations in the "database" scope
kubectl get compliance-violations -o json | jq '
  .items[] |
  select(.metadata.labels.scope == "database" and .metadata.labels.severity == "high")
'
```

### **4.2. Updating a Rule (Terraform)**
Modify a rule’s `criteria` via Terraform:
```hcl
resource "compliance_rule" "gpg_encryption" {
  name        = "gdpr-gpg-encryption"
  description = "Ensure all DB backups are GPG-encrypted."
  checks {
    type    = "file-monitor"
    criteria = { "file_path": "/backups/*.sql", "pattern": "-----BEGIN PGP MESSAGE-----" }
    target   = { "env": "prod", "service": "database" }
  }
}
```

### **4.3. Automated Remediation (CI/CD)**
Add a compliance step to a GitHub Actions workflow:
```yaml
- name: Run compliance check
  uses: actions/github-script@v6
  with:
    script: |
      const response = await fetch('https://compliance-api.example.com/checks');
      const violations = await response.json();
      if (violations.some(v => v.severity === 'critical')) {
        core.error('Critical violations found!');
        process.exit(1);
      }
```

---

## **5. Related Patterns**
1. **[Policy as Code](https://example.com/policy-as-code)**
   - Use **OPA** or **Terraform** to enforce compliance rules declaratively.

2. **[Zero Trust Architecture](https://example.com/zero-trust)**
   - Combine with **Compliance Setup** to validate micro-segmentation policies.

3. **[Chaos Engineering](https://example.com/chaos)**
   - Trigger compliance checks during **chaos experiments** to ensure resilience.

4. **[Security Mesh](https://example.com/security-mesh)**
   - Integrate compliance checks into a **control plane** alongside observability tools.

5. **[Compliance-as-Code Tools](https://example.com/compliance-tools)**
   - Libraries like:
     - **OpenCompliance** (for GDPR/HIPAA).
     - **CIS Benchmarks** (for system hardening).
     - **NIST CSF** (for risk management).

---
## **6. Best Practices**
- **Modularity**: Design rules to reuse components (e.g., share `checks` or `tools` across scopes).
- **Immutability**: Store rule definitions in immutable version control (e.g., Git).
- **Testing**: Run compliance checks in **staging environments** before production.
- **Documentation**: Link each rule to its regulatory source (e.g., [GDPR Art. 5](https://gdpr.eu/art-5-gdpr/)).
- **Automation**: Prioritize automated remediation for `critical`/`high` violations.

---
**Feedback**: Suggest additions or clarifications to [GitHub Issues](https://github.com/your-repo/issues).