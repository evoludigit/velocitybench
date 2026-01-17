# **[Pattern] GitOps: Reference Guide**

---

## **Overview**
GitOps is a declarative approach to infrastructure and application delivery where **Git becomes the single source of truth (SSOT)** for desired state configurations. By treating infrastructure as code (IaC) and synchronizing Git repositories with production environments, GitOps ensures **auditability, reproducibility, and automated reconciliation**. Unlike traditional CI/CD pipelines, GitOps emphasizes **continuous delivery via Git-driven workflows**, where changes are proposed, reviewed, and merged into a central repository before being automatically applied to clusters or environments.

Key principles of GitOps include:
- **Declarative state management** (e.g., Kubernetes manifests, Terraform configs).
- **Automated sync** (via agents or operators) to reconcile declared vs. actual state.
- **Immutable infrastructure** (changes are only made via Git).
- **Observability** (Git provides a complete audit trail).
- **Security** (changes are reviewed, tested, and versioned before deployment).

This guide outlines implementation best practices, schema conventions, example queries (for Git-based workflows), and related patterns for adopting GitOps effectively.

---

## **Schema Reference**
Below is a structured schema for GitOps repositories, focusing on common components. Adjust fields based on your IaC tool (e.g., Kubernetes, Terraform, Ansible).

| **Category**          | **Field**               | **Description**                                                                 | **Example**                                                                 | **Required?** |
|-----------------------|-------------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------|---------------|
| **Repository Metadata** | `repo_name`             | Name of the GitOps repository (e.g., `prod-k8s-config`).                       | `cluster-prod-apps`                                                      | ✅            |
|                       | `description`           | Purpose of the repo (e.g., "Production Kubernetes manifests").                 | "Hosts declarative Kubernetes configs for the `frontend` service."          | ❌            |
|                       | `default_branch`        | Primary branch (e.g., `main`, `master`).                                       | `main`                                                                     | ✅            |
|                       | `git_provider`          | Git hosting service (GitHub, GitLab, Bitbucket).                              | `github`                                                                   | ✅            |
|                       | `sync_reconciliation`   | Tool/agent used for sync (e.g., ArgoCD, Flux, Kustomize).                     | `argo-cd`                                                                | ✅            |
| **Environment Config** | `environment`           | Target environment (dev, staging, prod).                                      | `production`                                                              | ✅            |
|                       | `namespace`             | Kubernetes namespace or cloud region.                                          | `ecommerce`                                                               | ❌            |
|                       | `tags`                  | Labels for categorization (e.g., `team=frontend`, `owner=devops`).           | `["team:frontend", "owner:devops"]`                                      | ❌            |
| **IaC Configuration** | `manifest_path`         | Directory containing IaC files (e.g., Kubernetes YAML, Terraform HCL).        | `infra/terraform/modules/network/`                                         | ✅            |
|                       | `overrides_file`        | Path to environment-specific overrides (e.g., `values.yaml` for Helm).         | `helm/values-prod.yaml`                                                   | ❌            |
|                       | `secrets_management`    | Method for secret storage (e.g., Kubernetes Secrets, HashiCorp Vault).       | `vault`                                                                   | ✅            |
| **Workflow**          | `pr_workflow`           | Branch protection rules (e.g., require PR reviews, automated linting).        | `{ "require_review": 2, "status_checks": ["lint-passed"] }`               | ❌            |
|                       | `sync_trigger`          | Event that triggers sync (e.g., `push`, `tag`, `schedule`).                    | `on: [push]`                                                              | ✅            |
|                       | `rollback_strategy`     | How to undo changes (e.g., Git revert, ArgoCD rollback).                      | `git_revert`                                                              | ❌            |
| **Audit Trail**       | `change_log`            | Path to changelog file (e.g., `CHANGELOG.md`).                                | `docs/CHANGELOG.md`                                                       | ❌            |
|                       | `drift_notification`    | Alerting for configuration drift (e.g., Slack, email).                          | `slack-channel: #gitops-alerts`                                           | ❌            |

---

## **Query Examples**
GitOps workflows involve interacting with Git repositories, sync tools, and IaC artifacts. Below are common query-like operations (pseudo-code or CLI examples).

---

### **1. Query Repository Structure**
**Use Case**: List all environments and their configurations in a GitOps repo.
**Tool**: Git CLI + `jq` (for JSON/YAML parsing)
```bash
# List all environment directories in the repo
git ls-tree -r --name-only HEAD | grep -E 'env-(dev|staging|prod)/'
```
**Tool**: ArgoCD CLI (for ArgoCD-managed repos)
```bash
argocd repo list --app=my-app --output=json | jq '.apps[].spec.source.path'
```

---

### **2. Check for Configuration Drift**
**Use Case**: Detect discrepancies between Git and cluster state.
**Tool**: ArgoCD Application Status
```bash
argocd app get my-app -o json | jq '.status.health.status'
# Output: "Healthy", "Progressing", or "Degraded"
```
**Tool**: Kubernetes `kubectl` (for manual checks)
```yaml
# Compare Git-managed manifests with live cluster
kubectl diff -R -n my-namespace git://<repo-url>/branch:path/to/manifests
```

---

### **3. Validate PR Changes**
**Use Case**: Check if a PR introduces breaking IaC changes.
**Tool**: Git Hook + Custom Script
```bash
#!/bin/bash
# Validate Helm values for drift
git diff --name-only HEAD~1 HEAD | grep -E '\.(yaml|yml)$' | xargs -I {} yamllint {}
```
**Tool**: ArgoCD `prune` (for Kubernetes)
```bash
# Run ArgoCD prune to detect deleted resources
argocd app sync my-app --prune --prune-mode "all"
```

---

### **4. Generate Sync Diff**
**Use Case**: Preview changes before syncing.
**Tool**: Flux (for Flux-managed repos)
```bash
flux reconcile source git my-git-source
flux get kustomizations --diff -n my-namespace
```
**Tool**: Kustomize Local Build
```bash
# Build and diff Kustomize manifests
kustomize build ./overlays/production | kubectl diff -f -
```

---

### **5. Rollback to Last Known Good State**
**Use Case**: Revert to a previous Git commit.
**Tool**: ArgoCD Rolling Rollback
```bash
argocd app rollback my-app --revision=123 --output=json
```
**Tool**: Git Revert + IaC Tool
```bash
# Revert a specific commit and reapply IaC
git revert HEAD~1
kubectl apply -k ./kustomize/overlays/production  # Reapply after revert
```

---

### **6. Query Secrets Management**
**Use Case**: Ensure secrets are not hardcoded in Git.
**Tool**: `grep` + `git status`
```bash
# Find secrets in non-tracked files
git diff --cached --name-only | grep -E 'password|api_key|token'
```
**Tool**: Vault + ArgoCD Integration
```yaml
# Example: Secrets injected via ArgoCD
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
type: Opaque
data:
  username: <base64-encoded-from-vault>
```

---

## **Implementation Best Practices**
### **1. Repository Organization**
- **Split by Environment**: Use subdirectories (e.g., `env-dev/`, `env-prod/`).
- **Avoid Mixing Apps/Environments**: Dedicate repos per service or environment.
- **Example Structure**:
  ```
  /gitops-repo/
  ├── env-dev/
  │   ├── k8s/               # Kubernetes manifests
  │   └── terraform/         # Infrastructure-as-Code
  ├── env-prod/
  └── docs/
      └── CHANGELOG.md
  ```

### **2. Tooling Selection**
| **Tool**       | **Use Case**                                  | **Pros**                                  | **Cons**                          |
|----------------|-----------------------------------------------|-------------------------------------------|-----------------------------------|
| **ArgoCD**     | Declarative GitOps for Kubernetes.            | Mature, supports CRDs, RBAC.               | Steeper learning curve.           |
| **Flux**       | GitOps for Kubernetes with GitOps-native tools. | Lightweight, integrates with CD tools.    | Less enterprise support.          |
| **Kustomize**  | Overlay-based customization of manifests.    | Simple, no new language to learn.         | Limited to Kubernetes.            |
| **Terraform**  | Multi-cloud IaC with GitOps.                  | Broad provider support.                   | State management complexity.       |
| **Crossplane** | GitOps for cloud providers (e.g., GCP, AWS).   | Declarative cloud provisioning.           | Niche use case.                   |

### **3. Security**
- **Secrets**: Use **Vault, Kubernetes Secrets, or external secret managers**.
- **RBAC**: Restrict Git access via **SAML/OIDC** (e.g., GitHub Teams).
- **Audit Logs**: Enable Git provider audits (e.g., GitHub Audit Logs).

### **4. Observability**
- **Sync Status**: Monitor sync tools (e.g., ArgoCD UI, Prometheus metrics).
- **Drift Alerts**: Set up alerts for unmanaged resources (e.g., `kubectl get --dry-run=client ...`).
- **Change Tracking**: Use `git blame` or tools like **GitHub Code Scanning**.

### **5. Deployment Strategies**
| **Strategy**       | **Description**                                                                 | **GitOps Fit**                          |
|--------------------|-------------------------------------------------------------------------------|-----------------------------------------|
| **Blue-Green**     | Deploy to a parallel environment, switch traffic.                             | Sync `env-prod` + `env-prod-old`.       |
| **Canary**         | Gradually roll out to a subset of users.                                       | Use Argo Rollouts or Flux CD.           |
| **Feature Flags**  | Toggle features at runtime (e.g., Istio).                                    | Sync with environment-specific configs. |

---

## **Related Patterns**
GitOps integrates with or extends these complementary patterns:

1. **[Declarative Configuration as Code]**
   - *Relatedness*: GitOps relies on IaC (e.g., Kubernetes YAML, Terraform) to define the desired state.
   - *Synergy*: Ensure IaC is **idempotent** and **version-controlled**.

2. **[Immutable Infrastructure]**
   - *Relatedness*: GitOps enforces immutability by treating environments as read-only outside Git.
   - *Synergy*: Combine with **containerized infrastructure** (e.g., Kubernetes nodes).

3. **[Progressive Delivery]**
   - *Relatedness*: GitOps tools like Argo Rollouts enable canary deployments.
   - *Synergy*: Use **Git tags** to correlate deployments with traffic shifts.

4. **[Secret Management]**
   - *Relatedness*: Secrets must be externalized (e.g., Vault, HashiCorp Secrets Engine).
   - *Synergy*: Integrate secret rotation with GitOps syncs (e.g., Flux with Vault).

5. **[Infrastructure as Code (IaC)]**
   - *Relatedness*: GitOps manages the *delivery* of IaC, not the *creation*.
   - *Synergy*: Use tools like **Terragrunt** or **Kustomize** for environment-specific IaC.

6. **[Chaos Engineering]**
   - *Relatedness*: GitOps can validate resilience by **reverting to a stable branch** post-failure.
   - *Synergy*: Pair with **GitOps + Istio** for canary chaos testing.

7. **[Policy as Code]**
   - *Relatedness*: Enforce policies (e.g., "no delete operations") via GitOps sync tools.
   - *Synergy*: Use **OPA/Gatekeeper** or **Kyverno** to validate manifests before sync.

---

## **Troubleshooting**
| **Issue**               | **Diagnosis**                          | **Solution**                                                                 |
|-------------------------|----------------------------------------|-----------------------------------------------------------------------------|
| **Sync Stuck**          | Check ArgoCD/Flux logs.                | `kubectl logs -n argocd argocd-server`; restart controller.                |
| **Drift Detected**      | Run `argocd app sync --diff`.          | Manually apply Git changes or investigate orphaned resources.             |
| **PR Blocked**          | Review GitHub/GitLab branch protection.| Approve PR or update `pr_workflow` schema rules.                           |
| **Secrets Leaked**      | Audit `git status` for secret files.   | Rotate secrets, audit tooling access.                                       |
| **Slow Syncs**          | Large manifests or network latency.   | Optimize manifests (e.g., Kustomize overlays); use Git LFS for binaries.   |

---

## **Further Reading**
- **[GitOps Handbook](https://www.gitops.tech/handbook/)**: Official GitOps documentation.
- **[Argo Workflows](https://argo-workflows.readthedocs.io/)**: For GitOps + CI/CD pipelines.
- **[Flux CD Docs](https://fluxcd.io/flux/)**: Flux-specific GitOps implementation.
- **[Kubernetes GitOps Guide](https://kubernetes.io/blog/2020/02/07/gitops-tools-for-kubernetes/)**: Kubernetes-native tools.