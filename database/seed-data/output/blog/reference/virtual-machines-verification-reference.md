# **[Pattern] Virtual Machines Verification Reference Guide**

---

## **1. Overview**
The **Virtual Machines (VM) Verification** pattern ensures the integrity, authenticity, and correct operation of virtualized workloads within a cloud or on-premises infrastructure. This pattern validates VM configurations, runtime states, and security posture by comparing expected attributes (e.g., OS version, firewall rules, installed patches) against predefined compliance or operational baselines. It is critical for **security audits, disaster recovery testing, and infrastructure-as-code (IaC) validation**.

Use cases include:
- **Regulatory compliance** (e.g., PCI-DSS, HIPAA) – Verifying VMs meet security controls.
- **Operational hygiene** – Detecting misconfigurations before incidents escalate.
- **Golden Image validation** – Ensuring consistent deployments across environments.
- **Security hardening** – Enforcing baseline configurations (e.g., disabling unnecessary services).

Key benefits:
✔ **Automated validation** – Reduces manual checks via scripting/integration.
✔ **Remediation guidance** – Flags deviations with corrective actions (e.g., patching).
✔ **Audit trails** – Logs changes for compliance reporting.

---

## **2. Key Concepts**
| **Term**               | **Definition**                                                                                     | **Example**                                                                                     |
|------------------------|---------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **VM Profile**         | A set of expected attributes (e.g., OS, services, firewall rules) for a VM type (e.g., "web-server"). | `{ "os": "Ubuntu 22.04", "services": ["nginx", "sshd"], "firewall": "allow_http" }`            |
| **Verification Rule**  | A condition to validate (e.g., "OS must be patched," "No unused users").                           | `"rule": "os_patch_level >= ' critical '"`                                                      |
| **Compliance Policy**  | A collection of rules tied to a standard (e.g., CIS Benchmark).                                  | `policy: "CIS_Linux_1.14"` with 10+ rules for hardening.                                          |
| **Verification Agent** | A lightweight tool (e.g., Ansible, Terraform, or custom script) that queries VMs.                | SSH-based script checking `/etc/passwd` for root accounts.                                      |
| **Remediation Action**  | Steps to fix a failed check (e.g., reboot, install patch).                                        | `action: "apt update && apt upgrade -y"`                                                        |
| **Audit Log**          | Immutable record of verification runs, including timestamps, results, and remediation attempts.   | `{"vm_id": "vm-123", "rule": "sshd_disabled_root_login", "status": "failed", "timestamp": ...}` |

---

## **3. Schema Reference**
Below is the canonical structure for defining VM verification profiles and rules. Implementations may use YAML, JSON, or a database schema.

### **3.1. VM Profile Schema**
```yaml
# Example: Profile for a "secure-web-server" VM
---
name: secure-web-server
description: "Compliant Ubuntu 22.04 web server with hardened SSH."
os:
  distro: ubuntu
  version: "22.04"
  patch_level: "critical"  # Requires no critical vulnerabilities (CVE-2023-...)
services:
  required: ["nginx", "sshd"]
  forbidden: ["telnet", "ftp"]
firewall:
  rules:
    - action: allow
      port: 80
      protocol: tcp
    - action: deny
      port: 22
      protocol: icmp
users:
  admin_users:
    - username: admin
      password_policy: "complex"  # Min 12 chars, no reuse
  root_login: disabled
```

---

### **3.2. Verification Rule Schema**
| **Field**          | **Type**       | **Required** | **Description**                                                                                     | **Examples**                                                                                       |
|--------------------|----------------|--------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| `rule_id`          | `string`       | Yes          | Unique identifier for the rule (e.g., "CIS-2.2").                                                  | `"CIS-OS-001"`                                                                                     |
| `description`      | `string`       | Yes          | Human-readable rule purpose.                                                                         | `"Ensure SSH root login is disabled."`                                                              |
| `severity`         | `enum`         | Yes          | Criticality level: `low`, `medium`, `high`, `critical`.                                            | `"high"`                                                                                        |
| `check_type`       | `string`       | Yes          | Method of validation (e.g., `file_contents`, `service_running`, `cve_scan`).                      | `"file_contents"` (checks `/etc/ssh/sshd_config` for `PermitRootLogin`)                            |
| `path`             | `string`       | Conditional  | File path or API endpoint to inspect.                                                              | `"/etc/ssh/sshd_config"`                                                                           |
| `query`            | `string`/`json`| Conditional  | Regex, grep, or JSONPath query to extract data (e.g., `grep "PermitRootLogin"`).                  | `"!PermitRootLogin.*yes"` (negative match for disabled root login)                                  |
| `expected_value`   | `string`/`bool`| Conditional  | Target value (e.g., `true`, `"22"`).                                                              | `"false"` (root login should be off)                                                               |
| `remediation`      | `string`       | Conditional  | Command or script to fix the issue.                                                               | `"sed -i '/PermitRootLogin/s/yes/no/' /etc/ssh/sshd_config; systemctl restart sshd"`               |
| `tool_requirement`  | `string`       | Optional     | Agent/tool needed (e.g., `ansible`, `osquery`).                                                  | `"ansible"`                                                                                       |
| `policy_link`      | `string`       | Optional     | Reference to compliance standard (e.g., "CIS Benchmark v8").                                      | `"CIS_Linux_Benchmark_v8"`                                                                      |

**Example Rule (YAML):**
```yaml
rule_id: CIS-2.2
description: "Disable root SSH login."
severity: high
check_type: file_contents
path: "/etc/ssh/sshd_config"
query: "!PermitRootLogin.*yes"
remediation: >
  sed -i '/PermitRootLogin/s/yes/no/' {{ path }} &&
  systemctl restart sshd
tool_requirement: ansible
policy_link: "CIS_Linux_Benchmark_v8"
```

---

### **3.3. Verification Report Schema**
```json
{
  "vm_id": "vm-abc123",
  "profile_name": "secure-web-server",
  "timestamp": "2024-02-20T14:30:00Z",
  "results": [
    {
      "rule_id": "CIS-2.2",
      "status": "passed",
      "message": "Root SSH login disabled as required."
    },
    {
      "rule_id": "CIS-3.1",
      "status": "failed",
      "message": "Critical CVEs detected in kernel (CVE-2023-1234).",
      "remediation": "apt update && apt upgrade -y",
      "details": {
        "cve": ["CVE-2023-1234", "CVE-2023-5678"]
      }
    }
  ],
  "overall_status": "partially_compliant",
  "last_remediated": "2024-02-19T10:15:00Z"
}
```

---

## **4. Query Examples**
### **4.1. Verify All VMs Against a Profile**
**Tool:** Terraform + Custom Provider
```hcl
data "verification_profile" "web_server" {
  name = "secure-web-server"
}

resource "verification_check" "vm_scan" {
  for_each = data.aws_instances.web_servers
  vm_id    = each.instance_id
  profile  = data.verification_profile.web_server.id
}
```
**Output:**
```json
{
  "vm-abc123": { "status": "passed" },
  "vm-def456": { "status": "partially_compliant", "failed_rules": ["CIS-3.1"] }
}
```

---

### **4.2. Filter VMs with Critical Failures (Python + Boto3)**
```python
import boto3
from botocore.exceptions import ClientError

def check_critical_failures():
    ec2 = boto3.client("ec2")
    violations = []
    for vm in ec2.describe_instances()["Reservations"]:
        vm_id = vm["Instances"][0]["InstanceId"]
        response = ec2.describe_tags(
            Filters=[{"Name": "key", "Values": ["verification-status"]}]
        )
        if response["Tags"][0]["Value"] == "critical_violations":
            violations.append(vm_id)
    return violations
```

---

### **4.3. CVE Scan Integration (OpenSCAP)**
```bash
# Run OpenSCAP on a VM (requires `oscap` CLI)
oscap xccdf eval --profile xccdf_org.ssgproject.content_standard benchmark \
    ubuntu-2204-lts.xccdf > scan_report.xml

# Parse results for failures
grep -A5 "<result id=" < scan_report.xml | grep "fail"
```

---

## **5. Implementation Tools**
| **Tool**               | **Purpose**                                                                                     | **Example Use Case**                                                                             |
|------------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Ansible**           | Run idempotent checks/fixes via playbooks.                                                     | Validate `/etc/hosts.allow` and block root SSH access.                                           |
| **Terraform**         | Embed verification as a module (e.g., `terraform validate`).                                     | Enforce profiles during IaC deployment.                                                          |
| **OpenSCAP**           | Benchmark VMs against CIS/NIST profiles.                                                         | Scan for PCI-DSS compliance before production deployment.                                        |
| **Osquery**            | Lightweight agent for real-time monitoring (e.g., detect unauthorized users).                    | Trigger alerts if `SELECT * FROM users` finds unexpected accounts.                              |
| **Custom Scripts**     | Flexible checks (e.g., AWS Systems Manager Run Command).                                        | Bash/Python scripts to validate AWS Security Groups.                                           |
| **Vulnerability Scanners** | Detect CVEs (e.g., Nessus, Qualys).                                                              | Automate patching via `apt-get update && apt-get upgrade`.                                       |

---

## **6. Common Pitfalls & Mitigations**
| **Pitfall**                          | **Mitigation**                                                                                     |
|--------------------------------------|---------------------------------------------------------------------------------------------------|
| **False positives** (e.g., legacy rules). | Use `--dry-run` flags; validate rules against a known-good VM.                                      |
| **Performance impact** on large fleets. | Batch checks; use lightweight tools like Osquery for agentless scans.                              |
| **Dynamic environments** (e.g., Kubernetes). | Store profiles in **GitOps** (e.g., ArgoCD) or **policy-as-code** (e.g., Kyverno).                |
| **Agent dependency risks**.           | Combine agent-based (e.g., Ansible) with agentless (e.g., AWS SSM) checks.                         |
| **Compliance drift**.                | Schedule **weekly full scans** and **continuous monitoring** (e.g., Falco for runtime anomalies). |

---

## **7. Related Patterns**
| **Pattern Name**               | **Description**                                                                                     | **Link to Documentation**                          |
|---------------------------------|---------------------------------------------------------------------------------------------------|-----------------------------------------------------|
| **Infrastructure as Code (IaC)** | Define VM profiles in Terraform/Pulumi to enforce consistency during deployment.                     | [IaC Reference Guide](#)                          |
| **Policy as Code**              | Enforce VM policies via tools like Open Policy Agent (OPA) or Kyverno (K8s).                      | [Policy as Code Pattern](#)                       |
| **Golden Image Management**     | Maintain immutable, verified VM templates for repeatable deployments.                               | [Golden Image Pattern](#)                         |
| **Runtime Security Monitoring**  | Detect anomalies during VM execution (e.g., Falco, Aqua Security).                                  | [Runtime Security Pattern](#)                     |
| **Compliance Automation**       | Use tools like Policy Center or CloudCheckr to map VMs to frameworks (e.g., ISO 27001).          | [Compliance Automation Guide](#)                   |

---
**Next Steps:**
- Start with **CIS benchmarks** for your OS (Ubuntu/CentOS/RHEL).
- Integrate verification into your **CI/CD pipeline** (e.g., Terraform `validate` step).
- Automate remediation with **Ansible Tower** or **AWS Systems Manager**.

---
**Feedback:** Report issues or suggest enhancements at **[GitHub Issue Tracker](#)**.