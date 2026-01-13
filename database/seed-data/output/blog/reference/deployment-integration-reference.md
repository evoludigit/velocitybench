**[Pattern] Deployment Integration Reference Guide**

---

### **Overview**
The **Deployment Integration** pattern ensures seamless synchronization between infrastructure deployments (e.g., CI/CD pipelines, cloud provisioning tools) and application metadata (e.g., configuration, dependencies, and runtime environments). It bridges the gap between dynamic deployment lifecycle systems and static or semi-static application specifications, reducing misconfigurations, downtime, and manual errors.

This guide covers:
- Key principles and components of Deployment Integration.
- Schema definitions for defining deployment artifacts.
- Query examples for validating and querying deployment metadata.
- Best practices and related patterns for context.

---

### **Implementation Details**

#### **Core Principles**
1. **Metadata-Driven Deployments**:
   Deployments rely on structured metadata (e.g., Kubernetes manifests, Terraform configurations, or Helm charts) to define infrastructure, services, and dependencies.
2. **Decoupling**:
   Separate deployment artifacts (e.g., YAML/JSON) from execution logic (e.g., Kubernetes controllers, Ansible playbooks) to enable reuse and cross-platform compatibility.
3. **Idempotency**:
   Ensure deployments can be rerun without unintended side effects (e.g., using `--recursive` or `--keep-history` flags in tools like ArgoCD).
4. **Observability**:
   Track deployment status, rollback triggers, and resource drift via logging/monitoring tools (e.g., Prometheus, OpenTelemetry).

---

### **Schema Reference**
The following schemas define critical components of Deployment Integration:

#### **1. Deployment Artifact Schema**
A standardized format for deployment definitions, supporting multiple tools (e.g., Kubernetes, Terraform).

| Field               | Type          | Description                                                                 | Required | Example Value                          |
|---------------------|---------------|-----------------------------------------------------------------------------|----------|-----------------------------------------|
| `apiVersion`        | `string`      | Schema version (e.g., `"deploy.integration/v1"`).                            | Yes       | `"deploy.integration/v1"`              |
| `kind`              | `string`      | Resource type (e.g., `"KubernetesManifest"`, `"TerraformModule"`).        | Yes       | `"KubernetesManifest"`                  |
| `metadata`          | `object`      | Unique identifiers and labels for artifact management.                     | Yes       | `{ "name": "nginx-service", "labels": {"env": "prod"}}` |
| `spec`              | `object`      | Tool-specific configuration (e.g., Kubernetes YAML, Terraform HCL).        | Yes       | *See below*                             |
| `dependencies`      | `array[object]` | References to other artifacts (e.g., databases, secrets).                   | No        | `[{ "artifact": "db-secret", "type": "KubernetesSecret" }]` |
| `tags`              | `array[string]` | Categorization tags (e.g., `{"release": "v2.4", "owner": "team-x"}`).       | No        | `["release-v2.4", "critical"]`           |
| `version`           | `string`      | Semantic version of the artifact (e.g., `"1.3.0"`).                         | No        | `"1.3.0"`                               |

#### **2. KubernetesManifest Schema (Example)**
```json
{
  "apiVersion": "deploy.integration/v1",
  "kind": "KubernetesManifest",
  "metadata": {
    "name": "frontend-deployment",
    "labels": { "app": "web" }
  },
  "spec": {
    "yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata: {...}\nspec: {...}",
    "checksum": "sha256:abc123...",  // For drift detection
    "source": "git://repo/frontend.yaml"
  }
}
```

#### **3. DeploymentStatus Schema**
Tracks the lifecycle of a deployment artifact.

| Field          | Type     | Description                                                                 | Example Value          |
|----------------|----------|-----------------------------------------------------------------------------|------------------------|
| `status`       | `string` | Deployment phase (`pending`, `running`, `failed`, `completed`).               | `"running"`             |
| `timestamp`    | `string` | ISO8601 timestamp of the status change.                                      | `"2023-10-15T12:00:00Z"`|
| `resourceIds`  | `array[string]` | IDs of affected Kubernetes resources (e.g., pods, services).              | `["pod/nginx-123", "svc/web-456"]` |
| `rolloutId`    | `string` | Correlation ID for tracking rollbacks.                                      | `"rollout-789"`         |
| `error`        | `object` | Error details if deployment failed.                                          | `{ "code": "500", "msg": "Timeout" }` |

---

### **Query Examples**
Use these queries to interact with Deployment Integration metadata.

#### **1. List All Kubernetes Deployments**
```sql
SELECT
  metadata.name,
  spec.yaml,
  status.status,
  status.timestamp
FROM deployment_artifacts
WHERE kind = "KubernetesManifest"
  AND status.status = "running";
```

#### **2. Find Artifacts Dependent on a Database Secret**
```sql
SELECT
  metadata.name,
  spec.source
FROM deployment_artifacts
WHERE dependencies.artifact = "db-secret";
```

#### **3. Check for Drift (Mismatched Checksum)**
```sql
SELECT
  metadata.name,
  spec.checksum,
  status.status
FROM deployment_artifacts
WHERE spec.checksum != (
  SELECT checksum FROM live_resources WHERE resource_id = metadata.name
);
```

#### **4. Rollback a Failed Deployment**
```sql
UPDATE deployment_artifacts
SET status.status = 'pending-rollback',
    status.timestamp = NOW()
WHERE metadata.name = 'frontend-deployment'
  AND status.status = 'failed';
```

---

### **Best Practices**
1. **Version Control**:
   Store deployment artifacts in a versioned repository (e.g., Git) to track changes.
2. **Immutable Deployments**:
   Treat artifacts as immutable; update via new versions rather than editing in place.
3. **Resource Tagging**:
   Use consistent labels (e.g., `env`, `team`) for cross-tool querying.
4. **Drift Detection**:
   Automate checks for runtime vs. artifact differences (e.g., using `kubectl diff` or Terraform `plan`).
5. **Rollback Testing**:
   Simulate rollbacks in staging to validate recovery procedures.

---
### **Related Patterns**
| Pattern                          | Description                                                                 | Use Case                                                                 |
|----------------------------------|-----------------------------------------------------------------------------|---------------------------------------------------------------------------|
| **[Infrastructure as Code (IaC)](#)** | Automates infrastructure provisioning via code (e.g., Terraform, Pulumi). | Declare cloud environments declaratively.                                |
| **[Configuration Management](#)** | Syncs application configurations across environments (e.g., Ansible, Chef). | Manage settings like logs or monitoring endpoints.                       |
| **[Canary Deployments](#)**     | Gradually rolls out changes to a subset of users.                           | Reduce risk in production releases.                                       |
| **[GitOps](#)**                  | Uses Git as the single source of truth for deployments.                     | Audit trails and collaborative workflows with CI/CD.                      |
| **[Policy as Code](#)**          | Enforces compliance rules (e.g., OPA/Gatekeeper) during deployments.        | Block non-compliant artifacts before execution.                           |

---
### **Tools & Libraries**
| Tool/Library          | Purpose                                                                 |
|-----------------------|-------------------------------------------------------------------------|
| **ArgoCD**            | GitOps-based deployment synchronization for Kubernetes.                   |
| **Flux**              | Continuous delivery for Kubernetes using Git repositories.               |
| **Terragrunt**        | Composes and manages multi-module Terraform deployments.                |
| **OpenPolicyAgent**   | Enforces policies (e.g., require TLS in Kubernetes ingresses).           |
| **Crossplane**        | Extends Kubernetes to manage multi-cloud infrastructure.                 |

---
### **Troubleshooting**
| Issue                          | Diagnosis                                                                 | Resolution                                                                 |
|--------------------------------|-----------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Deployment Stuck in `Pending`** | Check resource quotas or missing RBAC permissions.                        | Verify `kubectl get events` or audit logs in ArgoCD.                        |
| **Configuration Drift**       | Runtime resource settings differ from artifact specs.                      | Run `kubectl diff` or compare artifacts with live state via CLI.           |
| **Rollback Fails**             | Target version is incompatible with current state.                          | Test rollback in staging first; ensure backward compatibility.               |
| **Slow Deployment Updates**    | Artifact polling frequency is low (e.g., ArgoCD `syncInterval`).            | Adjust sync frequency or use webhooks for event-driven updates.             |

---
### **Example Workflow**
1. **Define Artifact**:
   ```bash
   cat > nginx-deploy.json <<EOF
   {
     "apiVersion": "deploy.integration/v1",
     "kind": "KubernetesManifest",
     "metadata": { "name": "nginx" },
     "spec": { "yaml": "...", "checksum": "sha256:..." }
   }
   EOF
   ```
2. **Sync with Kubernetes**:
   ```bash
   kubectl apply -f nginx-deploy.json
   ```
3. **Monitor Status**:
   ```bash
   kubectl get deployment nginx -w
   ```
4. **Rollback if Needed**:
   ```bash
   kubectl rollout undo deployment/nginx --to-revision=2
   ```

---
**See Also**:
- [Kubernetes Manifest Spec](https://kubernetes.io/docs/concepts/configuration/overview/)
- [Terraform Module Registry](https://registry.terraform.io/)
- [GitOps Handbook](https://www.gitops.tech/)