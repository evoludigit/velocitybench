# **[Pattern] Containers Validation – Reference Guide**

---

## **Overview**
The **Containers Validation** pattern ensures that containerized applications adhere to predefined compliance, security, and operational standards before deployment. It automates the validation of container images, manifests, and runtime configurations against best practices, regulatory requirements, and organizational policies.

This pattern is critical for:
- **Security**: Detecting vulnerabilities, misconfigurations, or non-compliant dependencies in containers.
- **Operational Reliability**: Enforcing consistent runtime environments across development, staging, and production.
- **Compliance**: Validating adherence to standards (e.g., **CIS Benchmarks**, **OWASP Top 10**, **PCI-DSS**).
- **Efficiency**: Reducing manual audits and speeding up CI/CD pipelines by integrating validation early.

---

## **1. Key Concepts**
### **1.1 Validation Scope**
Containers Validation covers multiple artifacts, including:
- **Container Images**: Base images, layers, and installed packages.
- **Container Manifests**: `Dockerfile`, `docker-compose.yml`, Kubernetes manifests (`podspec`, `deployment`).
- **Runtime Configurations**: Secrets, environment variables, ports, and volumes.
- **Dependency Trees**: Package managers (`apt`, `yum`, `npm`, `pip`) and languages (e.g., Go, Java).

### **1.2 Validation Types**
| **Type**               | **Description**                                                                 | **Targets**                          |
|------------------------|---------------------------------------------------------------------------------|--------------------------------------|
| **Security Scanning**  | Detects vulnerabilities, CVEs, or weak credentials.                             | Images, layers, dependencies.        |
| **Policy Enforcement** | Checks for compliance with organizational policies (e.g., no root access).    | `Dockerfile`, manifests.             |
| **Runtime Checks**     | Validates container behavior at runtime (e.g., resource limits, health checks). | Pods, deployments, services.         |
| **Image Integrity**    | Ensures image authenticity via signatures (e.g., **Cosign**, **Notary**).       | Signed images.                       |
| **Context Awareness**  | Validates against multi-cloud or hybrid environments (e.g., EKS vs. GKE).      | Kubernetes manifests.                |

### **1.3 Validation Workflow**
A typical validation pipeline follows these stages:
1. **Pull Request/Commit Hook**: Scan changes to container artifacts in version control (e.g., GitHub Actions).
2. **CI Pipeline**: Validate images during build (e.g., Trivy, Clair).
3. **Pre-Deployment Gate**: Block non-compliant manifests in staging/production.
4. **Runtime Monitoring**: Continuously audit running containers (e.g., Falco, Aqua Security).
5. **Reporting**: Generate pass/fail results with remediation guidance.

---

## **2. Schema Reference**
Below are the core schema definitions for containers validation, structured for integration with tools like **Open Policy Agent (OPA)**, **Kyverno**, or custom scripting.

### **2.1 Container Image Validation Schema**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ContainerImageValidation",
  "type": "object",
  "properties": {
    "image": {
      "type": "string",
      "description": "Fully qualified image name (e.g., 'nginx:latest')."
    },
    "baseImage": {
      "type": "string",
      "description": "Base image used in the build (e.g., 'ubuntu:22.04')."
    },
    "layers": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "packageManager": {
            "type": "string",
            "enum": ["apt", "yum", "npm", "pip", "apk"]
          },
          "packages": {
            "type": "array",
            "items": { "type": "string" }
          },
          "vulnerabilities": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "cve": { "type": "string" },
                "severity": { "type": "string", "enum": ["critical", "high", "medium", "low"] }
              }
            }
          }
        }
      }
    },
    "security": {
      "type": "object",
      "properties": {
        "user": {
          "type": "object",
          "properties": {
            "uid": { "type": "integer", "minimum": 1000 },
            "nonRoot": { "type": "boolean" }
          }
        },
        "capabilities": {
          "type": "array",
          "items": { "type": "string" }
        },
        "secrets": {
          "type": "boolean",
          "description": "Whether secrets are properly managed (e.g., Kubernetes Secrets)."
        }
      }
    },
    "compliance": {
      "type": "object",
      "properties": {
        "benchmarks": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "benchmark": { "type": "string" }, // e.g., "CIS-Docker-Benchmark"
              "score": { "type": "number" },
              "passed": { "type": "boolean" }
            }
          }
        }
      }
    }
  },
  "required": ["image", "baseImage", "layers", "security"]
}
```

---
### **2.2 Kubernetes Manifest Validation Schema**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "KubernetesManifestValidation",
  "type": "object",
  "properties": {
    "kind": { "type": "string", "enum": ["Pod", "Deployment", "StatefulSet", "Job"] },
    "securityContext": {
      "type": "object",
      "properties": {
        "runAsNonRoot": { "type": "boolean" },
        "readOnlyRootFilesystem": { "type": "boolean" },
        "allowPrivilegeEscalation": { "type": "boolean" }
      }
    },
    "resources": {
      "type": "object",
      "properties": {
        "limits": {
          "type": "object",
          "properties": {
            "cpu": { "type": "string" },
            "memory": { "type": "string" }
          }
        },
        "requests": {
          "type": "object",
          "properties": {
            "cpu": { "type": "string" },
            "memory": { "type": "string" }
          }
        }
      }
    },
    "podSecurity": {
      "type": "object",
      "properties": {
        "selinux": { "type": "string" },
        "runAsUser": { "type": "integer" },
        "seccompProfile": { "type": "string" }
      }
    },
    "allowedServiceAccounts": {
      "type": "array",
      "items": { "type": "string" }
    }
  },
  "required": ["kind", "securityContext"]
}
```

---

## **3. Query Examples**
Below are examples of validation queries using **Open Policy Agent (OPA)** and **Kyverno** formats.

### **3.1 OPA Policy Example: Block Non-NonRoot Containers**
```rego
package k8s.security

# Block pods running as root
default allow = true

# Input: Kubernetes pod spec
pod {
    spec {
        securityContext {
            runAsUser: 0 # Root user
        }
    }
} {
    allow = false
    msg = "Pod must not run as root user"
}
```

---
### **3.2 Kyverno Policy Example: Enforce CIS Benchmark Compliance**
```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: enforce-cis-benchmark
spec:
  validationFailureAction: enforce
  rules:
  - name: check-cis-score
    match:
      any:
      - resources:
          kinds:
          - Pod
    validate:
      message: "Pod does not meet CIS benchmark score of 90%"
      pattern:
        metadata:
          annotations:
            cis-score: ["<90"]
```

---
### **3.3 CLI Tool Example: Using `trivy` to Scan Container Images**
```bash
# Scan an image for vulnerabilities
trivy image --severity CRITICAL,HIGH nginx:latest

# Export vulnerabilities to JSON
trivy image --format json nginx:latest > vulnerabilities.json
```

---
### **3.4 GitHub Action Example: Validate Dockerfile Linting**
```yaml
name: Dockerfile Lint
on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Hadolint
        uses: hadolint/hadolint-action@v2.1.0
        with:
          dockerfile: "Dockerfile"
          config: ".hadolint.yaml"
```

---

## **4. Implementation Tools**
| **Tool**               | **Purpose**                                                                 | **Integration**                          |
|------------------------|-----------------------------------------------------------------------------|------------------------------------------|
| **Trivy**              | Security scanning for containers/vulnerabilities.                           | CLI, CI/CD (GitHub Actions, Jenkins).   |
| **Clair**              | Static analysis of container images.                                        | Docker Registry plugins.                |
| **Open Policy Agent (OPA)** | Policy enforcement for containers/K8s.                                    | K8s admission controllers.               |
| **Kyverno**            | Policy engine for Kubernetes resources.                                    | Built into K8s admission webhooks.       |
| **Falco**              | Runtime security monitoring for containers.                                | DaemonSet in K8s clusters.               |
| **Hadolint**           | Lint Dockerfiles for best practices.                                       | CLI, CI pipelines.                       |
| **Cosign**             | Verify container image signatures.                                         | Docker Registry, CI/CD.                  |
| **Anchore Engine**     | Image scanning and compliance validation.                                  | REST API, Kubernetes operator.           |

---

## **5. Query Examples (Advanced)**
### **5.1 Query: "Find all pods with elevated privileges"**
**OPA Query:**
```rego
package k8s

# Output: List of pods running with privileged=true
pods_with_privileges {
    pods := input.pods
    pod := pods[_]
    pod.spec.securityContext.privileged == true
} output := { "name": pod.metadata.name, "namespace": pod.metadata.namespace }
```

---
### **5.2 Query: "Validate no containers use deprecated base images"**
**Kyverno Policy:**
```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: block-deprecated-base-images
spec:
  validationFailureAction: enforce
  rules:
  - name: check-base-image
    match:
      any:
      - resources:
          kinds:
          - Pod
    validate:
      message: "Container uses deprecated base image"
      pattern:
        spec:
          containers:
            - image: "ubuntu:14.04"  # Example deprecated image
```

---
### **5.3 Query: "Export compliance report for an image"**
**Using `trivy` + `jq`:**
```bash
trivy image --format json nginx:latest | jq '
  .Results[] |
  {Image: .Image,
   Vulnerabilities: (map(select(.Severity == "HIGH")) |
                     {count: length, examples: (.[] | {CVE: .Vulnerability.ID, Title: .Vulnerability.Title})})
  }'
```

---

## **6. Related Patterns**
| **Pattern**                     | **Description**                                                                 | **Connection to Containers Validation**                                                                 |
|----------------------------------|-------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| **Image Signing**                | Secures container images with cryptographic signatures to prevent tampering.  | Validated alongside **Containers Validation** to ensure provenance.                                     |
| **Admission Control**           | Enforces policies at K8s pod admission time.                                  | Works with **Containers Validation** to block non-compliant manifests before runtime.                 |
| **Runtime Security**             | Monitors running containers for anomalies (e.g., Falco).                     | Complements **Containers Validation** by detecting post-deployment issues not caught in static scans.  |
| **Zero Trust Networking**        | Restricts container-to-container communication.                              | Ensures validated containers only communicate with authorized services.                                  |
| **Secrets Management**           | Securely stores and rotates secrets for containers.                          | **Containers Validation** can enforce secrets management policies (e.g., no plaintext secrets).       |
| **Canary Deployments**           | Gradually rolls out container updates with validation gates.                | Validates canary containers separately before full deployment.                                          |
| **Policy as Code**               | Defines security policies in code (e.g., OPA, Kyverno).                       | Core to **Containers Validation** for automated enforcement.                                           |

---

## **7. Best Practices**
1. **Early Validation**:
   - Integrate validation into **CI/CD pipelines** (pre-build, pre-deploy stages).
   - Use **pre-commit hooks** (e.g., Hadolint for Dockerfiles) to catch issues early.

2. **Multi-Tool Approach**:
   - Combine **static scanning** (Trivy, Clair) with **dynamic analysis** (Falco).
   - Use **OPA/Kyverno** for policy enforcement at runtime.

3. **Compliance-Driven Validation**:
   - Map validation rules to standards (e.g., **CIS Docker Benchmark**, **NIST SP 800-190**).
   - Automate **compliance reporting** for audits.

4. **Image Integrity**:
   - Sign all container images with **Cosign** or **Notary**.
   - Implement **image immutability** (e.g., no `--pull` flag in Kubernetes).

5. **Performance Optimization**:
   - Cache scan results to avoid redundant checks.
   - Use **parallel scanning** for multiple layers/images.

6. **Feedback Loops**:
   - Provide **detailed remediation guidance** in validation reports.
   - Integrate with **SLI/SLO dashboards** to track compliance trends.

7. **Multi-Environment Synchronization**:
   - Ensure **staging/production parity** by validating manifests across environments.

---

## **8. Example Workflow: Validating a Kubernetes Deployment**
### **Step 1: Validate Dockerfile**
```bash
hadolint Dockerfile --success-exit-code  # Exit with non-zero on errors
```

### **Step 2: Scan Image for Vulnerabilities**
```bash
trivy image --exit-code 1 nginx:latest
```

### **Step 3: Enforce Policies with Kyverno**
Apply a Kyverno policy to block non-compliant pods:
```bash
kubectl apply -f kyverno-policy.yaml
```

### **Step 4: Deploy with Admission Control**
Use **OPA Gatekeeper** to validate the deployment:
```bash
kubectl apply -f gatekeeper-policy.yaml
kubectl apply -f deployment.yaml  # Blocked if non-compliant
```

### **Step 5: Monitor Runtime (Optional)**
Deploy **Falco** to detect anomalous behavior:
```bash
kubectl apply -f falco.yaml
```

---
## **9. Troubleshooting**
| **Issue**                          | **Cause**                                      | **Solution**                                                                 |
|-------------------------------------|------------------------------------------------|------------------------------------------------------------------------------|
| Validation fails on `Dockerfile`    | Syntax errors or deprecated commands.          | Use `hadolint` for linting; update to compliant syntax.                     |
| High-severity CVEs detected        | Outdated base image or packages.               | Update base image or patch vulnerable packages (e.g., `apt-get update`).    |
| Kyverno Block                       | Policy mismatch (e.g., `privileged: true`).    | Adjust pod spec or modify Kyverno policy.                                    |
| OPA Rego errors                     | Incorrect query logic.                         | Test policies with `opa test` or debug with `opa eval`.                     |
| Falco Alerts                        | Unexpected container behavior.                 | Review Falco rules or container logs.                                         |
| Slow scan times                     | Large image or many layers.                    | Use `--scanners vuln,cves` to limit scans; parallelize scans.                |

---

## **10. Further Reading**
- [CIS Docker Benchmark](https://www.cisecurity.org/benchmark/docker/)
- [OWASP Container Security Guide](https://owasp.org/www-project-container-security-guide/)
- [Trivy Documentation](https://aquasecurity.github.io/trivy/latest/)
- [Kyverno Policy Language](https://kyverno.io/docs/policy-language/)
- [Open Policy Agent (OPA) Rego](https://www.openpolicyagent.org/docs/latest/policy-language/)

---
**Last Updated:** [Insert Date]
**Version:** 1.2