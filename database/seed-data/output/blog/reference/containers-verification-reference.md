# **[Pattern] Containers Verification – Reference Guide**

## **Overview**
The **Containers Verification** pattern ensures that containerized applications (e.g., Docker, Kubernetes) meet security, compliance, and operational requirements before deployment. It includes static and dynamic analysis techniques—such as image scanning, runtime monitoring, and policy enforcement—to detect vulnerabilities, misconfigurations, and compliance violations. This pattern integrates with CI/CD pipelines, orchestration platforms, and security tools to automate verification workflows, reducing false positives and ensuring secure container deployments.

Key use cases include:
- **Pre-deployment scanning** (e.g., detecting CVEs in base images)
- **Runtime enforcement** (e.g., restricting privilege escalation)
- **Compliance validation** (e.g., adherence to CIS Docker Benchmark)
- **Image integrity checks** (e.g., verifying container images against known threats)

---

## **Implementation Details**

### **1. Key Concepts**
| **Term**               | **Definition**                                                                                     | **Example**                                                                                     |
|------------------------|---------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Static Analysis**    | Scanning container images for vulnerabilities, misconfigurations, or policy violations *without* execution. | Using `Trivy` or `Anchore` to scan for unpatched OS packages in a Docker image.                 |
| **Dynamic Analysis**   | Monitoring running containers for runtime anomalies (e.g., exposed ports, unauthorized processes). | Using `Falco` or `Aqua Security` to detect suspicious API calls in a Kubernetes pod.            |
| **Image Signing**      | Cryptographically verifying the integrity and authenticity of container images.                  | Using `Cosign` or `Notary` to validate images signed by trusted entities.                       |
| **Policy-as-Code**     | Defining security rules (e.g., "No root access," "Minimal base image") via tools like Open Policy Agent (OPA). | Enforcing a rule via `OPA` that blocks images with `USER: root` in their `Dockerfile`.       |
| **Secrets Management** | Protecting sensitive data (API keys, passwords) stored in containers or environments.             | Using `Vault` or `Sealed Secrets` to encrypt secrets before embedding them in container configs. |
| **Runtime Enforcement**| Enforcing security controls during container execution (e.g., SELinux, AppArmor).               | Dropping unnecessary Linux capabilities via `cap-drop` in a container runtime.                  |

---

### **2. Schema Reference**
The following tables outline the core components and their attributes for containers verification.

#### **A. Static Analysis Scan Profile**
| **Field**            | **Type**   | **Description**                                                                                     | **Example Value**                          |
|----------------------|------------|-----------------------------------------------------------------------------------------------------|--------------------------------------------|
| `tool`               | `string`   | Name of the static analysis tool (e.g., Trivy, Clair, Snyk).                                       | `"Trivy"`                                  |
| `scan_type`          | `enum`     | Type of scan (`vulnerability`, `policy`, `compliance`).                                            | `"vulnerability"`                          |
| `image_regex`        | `string`   | Regex pattern to match targeted images (e.g., `nginx:*`).                                           | `^nginx:[0-9]+\.[0-9]+$`                   |
| `severity_threshold` | `string`   | Minimum severity level to trigger alerts (`critical`, `high`, `medium`, `low`).                     | `"high"`                                   |
| `policy_rules`       | `array`    | List of policy rules to enforce (e.g., `no-root`, `non-root-user`).                                | `[{"rule": "no-root", "severity": "critical"}]` |
| `exclude_layers`     | `array`    | Layer paths to exclude from scanning (e.g., `/tmp`).                                               | `["/tmp/"]`                                |

#### **B. Dynamic Analysis Rule**
| **Field**            | **Type**   | **Description**                                                                                     | **Example Value**                          |
|----------------------|------------|-----------------------------------------------------------------------------------------------------|--------------------------------------------|
| `event`              | `string`   | Trigger event (e.g., `container_start`, `file_modified`).                                           | `"container_start"`                         |
| `pattern`            | `string`   | Regex or condition to match (e.g., `execve.*/bin/sh`).                                             | `execve.*/bin/sh`                          |
| `action`             | `string`   | Response action (`alert`, `terminate`, `audit`).                                                    | `"terminate"`                              |
| `severity`           | `string`   | Severity level (`critical`, `high`, `medium`, `low`).                                               | `"critical"`                               |
| `tool`               | `string`   | Dynamic analysis tool (e.g., `Falco`, `Aqua`).                                                      | `"Falco"`                                  |

#### **C. Image Signing Policy**
| **Field**            | **Type**   | **Description**                                                                                     | **Example Value**                          |
|----------------------|------------|-----------------------------------------------------------------------------------------------------|--------------------------------------------|
| `signing_method`     | `string`   | Method (e.g., `cosign`, `notary`).                                                                   | `"cosign"`                                 |
| `trusted_keys`       | `array`    | Public keys of trusted signers (base64-encoded).                                                     | `[{"key": "-----BEGIN PUBLIC KEY-----..."}]` |
| `image_digest`       | `string`   | Expected digest of the signed image.                                                                 | `"sha256:abc123..."`                       |
| `expiry`             | `datetime` | Expiration date for the signature.                                                                  | `"2024-12-31T23:59:59Z"`                   |

---

## **Query Examples**

### **1. Static Analysis Query (Trivy)**
**Use Case:** Scan a Docker image for vulnerabilities with severity `high` or `critical`.
```bash
# Scan a locally built image
docker build -t my-app:latest .
trivy image --severity HIGH,CRITICAL my-app:latest

# Integrate with CI/CD (GitHub Actions example)
- name: Run Trivy scan
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: 'my-registry/my-app:latest'
    severity: 'CRITICAL,HIGH'
```

**Output Example:**
```json
[
  {
    "Vulnerability": {
      "Severity": "HIGH",
      "ID": "CVE-2023-1234",
      "Description": "OpenSSL memory leak",
      "FixedVersion": "3.0.2"
    },
    "Target": "my-app:latest"
  }
]
```

---

### **2. Dynamic Analysis Query (Falco)**
**Use Case:** Detect containers executing `/bin/sh` with elevated privileges.
```yaml
# falco_rules.yml
- rule: SuspiciousShellExec
  desc: Detect containers executing /bin/sh with elevated capabilities
  condition: |
    evt.type=execve and
    evt.execve.arg[0]=/bin/sh and
    container.info.image != "nginx:latest"
  output: "Process /bin/sh executed with elevated permissions in container %container.name"
  priority: WARNING
  tags: [privilege_escalation]
```
**Trigger Falco:**
```bash
falco --rule-file=falco_rules.yml -k
```

**Output Example (JSON):**
```json
{
  "output": "Process /bin/sh executed with elevated permissions in container my-app",
  "priority": "WARNING",
  "rule": "SuspiciousShellExec",
  "output_fields": {
    "container.name": "my-app",
    "container.id": "123abc..."
  }
}
```

---

### **3. Image Signing Verification (Cosign)**
**Use Case:** Verify a container image signed by a trusted key.
```bash
# Sign an image (run once by the signer)
cosign sign --key cosign.key my-registry/my-app:latest

# Verify the signature (run during deployment)
cosign verify --key cosign.pub my-registry/my-app:latest
```
**Output:**
```
Verification successful
```

---

### **4. Policy-As-Code Query (OPA Rego)**
**Use Case:** Enforce that containers do not run as `root`.
```rego
package k8s

default allow = false

allow {
  input.request.object.metadata.name == "my-pod"
  input.request.object.spec.containers[_].securityContext.runAsUser != 0
}

# Deny if root is used
deny {
  input.request.object.spec.containers[_].securityContext.runAsUser == 0
}
```
**Integrate with Kubernetes Admission Controller:**
```yaml
# admission_controller_config.yaml
apiVersion: apiregistration.k8s.io/v1
kind: APIService
spec:
  service: "v1alpha2.openshift.io"
  group: "security.openshift.io"
  groupPriorityMinimum: 1000
  versionPriority: 15
  version: "v1alpha2"
```

---

## **Related Patterns**
1. **[Image Optimization]** – Minimize container image sizes by leveraging multi-stage builds and distroless images.
2. **[Runtime Security]** – Use tools like `gVisor` or `Kata Containers` to isolate container workloads.
3. **[Secrets Management]** – Rotate and encrypt secrets using `Vault` or `Sealed Secrets`.
4. **[Compliance Automation]** – Integrate with tools like `OpenSCAP` or `CIS Benchmarks` for automated compliance checks.
5. **[Zero-Trust Networking]** – Restrict pod-to-pod communication with `NetworkPolicies` in Kubernetes.
6. **[Immutable Infrastructure]** – Use ephemeral containers to reduce attack surfaces.

---
## **Further Reading**
- [Trivy Documentation](https://aquasecurity.github.io/trivy/v0.43/docs/)
- [Falco Ruleset Examples](https://falco.org/docs/rules/)
- [Cosign Image Signing](https://github.com/sigstore/cosign)
- [OPA Policy-as-Code](https://www.openpolicyagent.org/docs/latest/)
- [CIS Docker Benchmark](https://www.cisecurity.org/benchmark/docker/)