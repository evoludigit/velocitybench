**[Pattern] Virtual-Machines Validation Reference Guide**

---
### **1. Overview**
The **Virtual-Machines Validation** pattern ensures that virtual machine (VM) deployments meet predefined requirements for security, performance, compliance, and operational integrity. This pattern validates VM configurations—including hardcoded credentials, firewall rules, guest OS integrity, and resource allocations—using automated scans during provisioning, runtime, or scheduled cycles.

Key use cases:
- **Security Compliance**: Enforce policies like CIS benchmarks or PCI-DSS.
- **Runtime Anomaly Detection**: Flag unauthorized changes (e.g., software installations, modified firewall rules).
- **Performance Validation**: Evaluate CPU/memory utilization vs. SLAs.
- **Image Asset Management**: Verify VM templates before deployment.

---

### **2. Schema Reference**
Below are the primary entities and their attributes in JSON schema format:

#### **Core Entities**
| **Entity**               | **Attributes**                                                                                     | **Type**       | **Required** | **Description**                                                                 |
|--------------------------|---------------------------------------------------------------------------------------------------|----------------|--------------|---------------------------------------------------------------------------------|
| `ValidationPolicy`       | `id`                          | `string`       | Yes           | Unique identifier for the policy.                                               |
|                          | `name`                        | `string`       | Yes           | Human-readable policy name.                                                      |
|                          | `description`                 | `string`       | No            | Policy purpose/intent.                                                           |
|                          | `targetOs`                    | `string[]`     | No            | Operating systems (e.g., `["Windows_Server_2019", "Ubuntu_20.04"]`).              |
|                          | `appliesTo`                   | `enum`         | Yes           | Scope: `VM_PROVISION` (pre-deploy), `VM_RUNTIME` (continuous), `VM_IMAGE` (template). |
|                          | `rules`                       | `Rule[]`       | Yes           | Array of validation rules (see `Rule` schema).                                  |
|                          | `schedule`                    | `Schedule`     | No            | Cron-like schedule for runtime policies (e.g., `"0 3 * * *"`).                      |
|                          | `severityLevel`               | `enum`         | No            | Default severity for policy violations (`INFO`, `WARNING`, `CRITICAL`).          |

---
| **Entity**               | **Attributes**                                                                                     | **Type**       | **Required** | **Description**                                                                 |
|--------------------------|---------------------------------------------------------------------------------------------------|----------------|--------------|---------------------------------------------------------------------------------|
| `Rule`                   | `id`                          | `string`       | Yes           | Unique rule identifier (e.g., `disable_rdp`).                               |
|                          | `name`                        | `string`       | Yes           | Human-readable rule name.                                                      |
|                          | `severity`                    | `enum`         | Yes           | Severity level (`INFO`, `WARNING`, `CRITICAL`).                                |
|                          | `description`                 | `string`       | No            | Rule intent/impact.                                                              |
|                          | `type`                        | `string`       | Yes           | Rule type: `SECURITY`, `PERFORMANCE`, `CONFIG`, `IMAGE`.                      |
|                          | `check`                       | `object`       | Yes           | Rule-specific validation logic (see below).                                     |
|                          | `remediation`                 | `Remediation`  | No            | Instructions to fix violations (e.g., `patch_os`).                            |

---
#### **Rule Types and Checks**
Rules are categorized by `type` with nested `check` attributes:

| **Rule Type**   | **Check Attributes**                          | **Description**                                                                                     |
|-----------------|-----------------------------------------------|-----------------------------------------------------------------------------------------------------|
| `SECURITY`      | `credentials`                                | Detect hardcoded secrets (passwords, keys) in VM files (e.g., `C:\users\admin\password.txt`).     |
|                 | `firewallRules`                              | Validate allowed ports (e.g., enforce only `80/443`).                                                 |
|                 | `antivirus`                                  | Ensure antivirus is installed and enabled.                                                          |
|                 | `accountLockout`                             | Verify password policies (e.g., max attempts: `3`).                                                  |
| `PERFORMANCE`   | `cpuUtilization`                             | Compare VM CPU usage against SLAs (e.g., `< 70%`).                                                     |
|                 | `diskLatency`                                | Check disk I/O latency thresholds (e.g., `< 100ms`).                                                   |
| `CONFIG`        | `guestTools`                                 | Ensure VMware Tools/OpenVMTools are installed.                                                       |
|                 | `timeSync`                                   | Validate NTP service is active.                                                                     |
| `IMAGE`         | `os版本`                                    | Verify OS version matches baseline (e.g., `Ubuntu_20.04.5`).                                         |
|                 | `patches`                                    | Check for missing critical patches (e.g., `CVE-2023-1234`).                                         |

---
#### **Remediation Example (`Remediation`)**
| **Attribute**  | **Type**       | **Description**                                                                                     |
|----------------|----------------|-----------------------------------------------------------------------------------------------------|
| `action`       | `string`       | Remediation step (e.g., `install_package`, `restart_service`).                                       |
| `command`      | `string`       | Shell command to execute (e.g., `apt-get update && apt-get install -y rkhunter`).                   |
| `requires`     | `string[]`     | Preconditions (e.g., `["root_access"]`).                                                           |
| `notes`        | `string`       | User-facing instructions or warnings.                                                               |

---

### **3. Query Examples**
#### **List All Validation Policies**
```sql
GET /api/v1/validation-policies
Headers:
  Authorization: Bearer <token>
Response:
[
  {
    "id": "policy-123",
    "name": "CIS-Benchmark-Level-2",
    "appliesTo": "VM_RUNTIME",
    "rules": [
      {"id": "disable_rdp", "severity": "CRITICAL"},
      {"id": "enable_firewall", "severity": "WARNING"}
    ]
  }
]
```

#### **Validate a Single VM**
```bash
curl -X POST "https://<control-plane>/validate-vm" \
  -H "Content-Type: application/json" \
  -d '{
    "vmId": "vm-xyz",
    "policyId": "policy-123"
  }'
```
**Response (Partial):**
```json
{
  "vmId": "vm-xyz",
  "violations": [
    {
      "ruleId": "disable_rdp",
      "message": "RDP port (3389) is open. Remediate by disabling it in Windows Firewall.",
      "severity": "CRITICAL"
    }
  ],
  "status": "PARTIALLY_COMPLIANT"
}
```

#### **Schedule a Batch Validation**
```bash
curl -X POST "https://<control-plane>/schedule-batch" \
  -H "Content-Type: application/json" \
  -d '{
    "policyId": "policy-456",
    "vmIds": ["vm-abc", "vm-def"],
    "schedule": "0 2 * * *"
  }'
```

---

### **4. Implementation Patterns**
#### **A. Pre-Provision Validation (Image Validation)**
- **Trigger**: During VM template creation.
- **Tools**:
  - **Custom Scripts**: Use `ovaInspect` (OpenStack) or cloud-init hooks to validate templates.
  - **SCAP Tools**: Use `openscap` to check CIS benchmarks against golden images.
  - **Concurrency**: Distribute scans via a workload orchestrator (e.g., Kubernetes `Job`).
- **Example Workflow**:
  1. Upload templates to registry.
  2. Run `openscap evaluate --profile /usr/share/xml/scap/ssg-content/ssg-fedora19-ds.xml --results /output`.
  3. Flag templates with `CRITICAL` violations.

#### **B. Runtime Validation**
- **Trigger**: Continuous (e.g., every 6 hours) or event-driven (e.g., VM power-on).
- **Tools**:
  - **Agent-Based**: Deploy lightweight agents (e.g., `vmtoolsd` hooks for Windows/Linux).
  - **Agentless**: Use VMware Tools API or `libguestfs` for live VM inspection.
  - **Cloud Providers**:
    - **AWS**: Use AWS Systems Manager Automation to run compliance checks.
    - **GCP**: Leverage Compute Engine’s *Health API* + custom scripts.
- **Example Agent Command (Python)**:
  ```python
  import requests
  # Fetch VM metadata and validate against policy
  vm_data = requests.get("http://localhost/metadata/vmware/toolbox/cmdline").json()
  if "rdp_port" in vm_data and vm_data["rdp_port"] == "open":
      reports.violation("RDP exposed", severity="CRITICAL")
  ```

#### **C. Remediation Automation**
- **Self-Healing**:
  - Use **Ansible** or **Terraform** to auto-apply fixes (e.g., disable RDP if flagged).
  - Example Ansible Playbook:
    ```yaml
    - name: Disable RDP
      win_firewall_rule:
        name: "Allow-RDP"
        state: disabled
        action: Block
    ```
- **Human Review Workflow**:
  - Escalate `CRITICAL` violations to a ticketing system (e.g., Jira) for manual approval.

---

### **5. Related Patterns**
| **Pattern Name**               | **Relationship**                          | **When to Use**                                                                                     |
|---------------------------------|------------------------------------------|------------------------------------------------------------------------------------------------------|
| **Configuration-as-Code (CfC)** | Input for validation policies.          | Define VM configs in Terraform/Ansible before validation.                                             |
| **Secret Management**           | Detects hardcoded secrets in VMs.        | Combine with HashiCorp Vault’s policy enforcement to block credential leaks.                        |
| **Change Data Capture (CDC)**   | Tracks VM config drifts.                 | Use CDC (e.g., Debezium) to monitor VM state changes after validation.                               |
| **Policy-as-Code (PaC)**        | Defines validation rules declaratively.  | Store policies in Git (e.g., Open Policy Agent) and sync with validator agents.                   |
| **Chaos Engineering**           | Stress-tests VM resilience post-validation. | Run chaos experiments (e.g., kill VMs) after compliance passes to verify recovery.                   |

---
### **6. Troubleshooting**
| **Issue**                          | **Diagnosis**                                                                 | **Solution**                                                                                     |
|-------------------------------------|-------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| **Validation Fails on Older Images** | Rule checks target newer OS versions.                                           | Update `targetOs` in policy or add version-specific overrides.                                     |
| **High Remediation Failure Rate**  | Remediation steps fail due to permissions/dependencies.                        | Test remediation commands manually in a staging VM.                                               |
| **Agent Overload**                  | Too many VMs trigger validation simultaneously.                                | Implement rate limiting (e.g., queue workflows in Celery).                                       |
| **False Positives**                 | Rule is too strict (e.g., blocks legitimate software).                          | Refine `check` logic or add exceptions (e.g., whitelist approved software).                       |

---
### **7. Best Practices**
1. **Phased Rollout**:
   - Start with `INFO`-level rules to avoid overwhelming teams, then escalate to `WARNING`/`CRITICAL`.
2. **Automated Remediation**:
   - Limit auto-fixes to non-disruptive actions (e.g., patching) and flag critical changes for review.
3. **Audit Logging**:
   - Log all validation events (e.g., "Policy `policy-123` ran on VM `vm-xyz` at 2023-10-01T12:00:00Z").
4. **Vendor-Specific Optimizations**:
   - Leverage provider APIs (e.g., AWS Inspector, Azure Security Center) for built-in validation.
5. **Cost Control**:
   - For cloud environments, use spot instances for validation scans to reduce costs.

---
### **8. Example Policy JSON**
```json
{
  "id": "compliance-policy-v1",
  "name": "Multi-Cloud Security Baseline",
  "description": "Enforces CIS Level 2 for Windows/Linux across Azure/GCP/AWS.",
  "targetOs": ["Windows_Server_2022", "Ubuntu_22.04"],
  "appliesTo": "VM_RUNTIME",
  "schedule": "0 2,14 * * *",  // Daily at 2 AM and 2 PM UTC
  "severityLevel": "WARNING",
  "rules": [
    {
      "id": "disable-ssh-root",
      "name": "Disable root SSH access",
      "severity": "CRITICAL",
      "type": "SECURITY",
      "check": {
        "osType": "Linux",
        "command": "grep '^PermitRootLogin' /etc/ssh/sshd_config",
        "expectedOutput": "no"
      },
      "remediation": {
        "action": "edit_config",
        "command": "sed -i 's/PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config",
        "requires": ["ssh_access"]
      }
    },
    {
      "id": "enable-defender",
      "name": "Windows Defender must be enabled",
      "severity": "WARNING",
      "type": "SECURITY",
      "check": {
        "osType": "Windows",
        "registryPath": "HKLM:\\SOFTWARE\\Microsoft\\Windows Defender\\Real-Time Protection",
        "key": "DisableRealtimeMonitoring",
        "expectedValue": "0"
      }
    }
  ]
}
```