---
# **[Pattern] Deployment Conventions – Reference Guide**

---

## **Overview**
The **Deployment Conventions** pattern standardizes naming, structure, and folder conventions for artifacts (e.g., applications, libraries, services) to ensure consistency, reproducibility, and tooling compatibility across deployments. By enforcing structured naming (e.g., `project-version-artifact-type`, `org/service-name`), teams avoid ambiguity in environments, reduce human error, and support automated CI/CD tooling. This guide outlines key conventions, schema templates, and implementation examples for integrations with CI/CD pipelines, cloud platforms, and infrastructure-as-code (IaC) tools.

---

## **Key Concepts**
Deployment Conventions address three primary dimensions:
1. **Naming**
   Structured identifiers for deployments, artifacts, and versions (e.g., `myapp-v2.3.0`, `frontend-prod`).
2. **Artifact Structure**
   Consistent packaging and directory layouts for source code, builds, and configuration files.
3. **Environment Tags**
   Standard labels (`dev`, `staging`, `prod`) to distinguish environments during deployments.

---

## **Schema Reference**

| **Category**               | **Field**               | **Format**                                      | **Example**                          | **Notes**                                                                                     |
|----------------------------|-------------------------|-------------------------------------------------|---------------------------------------|-----------------------------------------------------------------------------------------------|
| **Naming Conventions**     | `artifactName`          | `{project}-{component}-{type}`                  | `myapp-frontend-webapp`               | `project`: Core product name; `component`: Module (e.g., frontend, api); `type`: Service/role. |
|                            | `version`               | `MAJOR.MINOR.PATCH` or `{YYYYMMDD}`             | `v2.0.3`/`20240615`                  | Semantic versioning recommended for patch-heavy workflows.                                  |
|                            | `environmentSuffix`     | `-{env}` (dev/staging/prod)                     | `myapp-api-dev`                       | Optional; omit for monolithic deployments.                                                 |
|                            | `commitHash`            | Shortened commit hash                           | `-gha-abc1234`                        | For CI/CD-specific deployments (e.g., GitHub Actions).                                      |
| **Artifact Structure**     | `repoRoot`              | `/project/{project}-{component}`                | `/myapp/frontend`                     | Source code repository layout.                                                              |
|                            | `buildOutputDir`        | `dist/`, `build/`, or `{project}-{artifact}`     | `dist/myapp-webapp-v2.0.0`            | Standardized build output paths for consistency.                                             |
|                            | `configDir`             | `config/{env}` or `{project}-{component}/config` | `config/prod/myapp-api.yaml`          | Environment-specific configurations.                                                       |
|                            | `imageTag`              | `{repoName}:{version}-{env}` or `:latest`        | `myapp-frontend:v2.0.0-prod`          | Docker/Kubernetes deployment tags.                                                          |
| **Environment Tags**       | `envLabel`              | `{env}.{domain}` or `{org}/{env}/{service}`     | `prod.myservice.example.com`          | DNS/subdomain conventions.                                                                   |
|                            | `tagPrefix`             | `{org}-{env}`                                   | `myorg-prod`                          | CI/CD pipeline tags (e.g., `myorg-prod-20240615`).                                           |
| **Deployment Metadata**    | `releaseNotes`          | Markdown/JSON file                              | `RELEASE_NOTES.md`                    | Optional; links to changelog or commits.                                                    |
|                            | `deploymentId`          | UUID or `{env}-{timestamp}`                     | `prod-20240615-1430`                  | Unique identifier for rollback tracking.                                                     |

---

## **Implementation Details**

### **1. Artifact Naming Rules**
- **Semantic Versioning**: Use `MAJOR.MINOR.PATCH` for versioned artifacts (e.g., libraries, APIs). Example:
  ```
  myapp-backend-api:v1.2.0
  ```
- **Commit-Hash Suffixes**: Append a shortened commit hash for CI/CD-triggered deployments:
  ```
  myapp-frontend-gha-abc1234
  ```
- **Environment Suffixes**: Optional; omit for deployments to a single environment (e.g., `prod`).

### **2. Directory Structure**
Adopt a standardized layout for source repositories and build outputs:
```
myapp/
├── frontend/               # Component directory
│   ├── src/
│   ├── dist/               # Build output
│   │   └── myapp-frontend-v1.0.0/
│   ├── config/
│   │   ├── dev.yaml
│   │   └── prod.yaml
│   └── RELEASE_NOTES.md
└── .github/workflows/      # CI/CD pipelines
    └── deploy.yml
```

### **3. Docker/Kubernetes Tags**
- **Versioned Tags**: Use `{repo}:{version}-{env}` for traceability:
  ```yaml
  image: myapp-frontend:v1.0.0-prod
  ```
- **Latest Tag**: Avoid for production deployments; reserve for staging/testing.

### **4. CI/CD Integration**
- **Pipeline Tags**: Tag deployments with `{org}-{env}` (e.g., `myorg-prod-20240615`) for consistency:
  ```yaml
  # GitHub Actions example
  env:
    IMAGE_TAG: "myorg-prod-${{ github.sha }}"
  ```
- **Automatic Versioning**: Use tools like [`semantic-release`](https://github.com/semantic-release/semantic-release) to automate version tags based on commits.

### **5. Infrastructure-as-Code (IaC)**
- **Terraform/CloudFormation**: Reference artifacts via standardized names:
  ```hcl
  resource "aws_ecs_task_definition" "myapp" {
    family = "myapp-api-v1.2.0-prod"
    container_definitions = jsonencode([{
      image = "myapp-api:v1.2.0-prod"
    }])
  }
  ```

---

## **Query Examples**

### **1. Finding the Latest Deployment**
**Context**: Query the CI/CD system (e.g., GitHub API) for the most recent `prod` deployment of `myapp-api`.
**Request**:
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/repos/myorg/myapp/actions/runs?branch=main&env=prod&per_page=1"
```
**Response**:
```json
{
  "workflow_runs": [
    {
      "name": "Deploy myapp-api-prod",
      "conclusion": "success",
      "html_url": "https://github.com/myorg/myapp/actions/runs/123456",
      "artifacts": {
        "image_tag": "myapp-api:v1.0.0-prod"
      }
    }
  ]
}
```

### **2. Listing Environment-Specific Configs**
**Context**: Retrieve all `prod` configurations for `myapp-backend`.
**Command**:
```bash
# Bash glob pattern
find /config -name "*myapp-backend*" -path "*/prod/*"
```
**Output**:
```
/config/prod/myapp-backend/config.yaml
/config/prod/myapp-backend/secrets.env
```

### **3. Validating Docker Image Tags**
**Context**: Check if a tagged image exists in a registry.
**Request** (using `docker` CLI):
```bash
docker manifest inspect myorg/myapp-frontend:v1.0.0-prod
```
**Output** (success):
```json
{
  "schemaVersion": 2,
  "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
  "config": {
    "mediaType": "application/vnd.docker.container.image.v1+json",
    "size": 4253
  },
  "layers": [/* ... */]
}
```

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                                                                 |
|---------------------------|---------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **[Blueprint for Deployment]** | Defines reusable IaC templates for environments (e.g., Kubernetes clusters).    | When deploying complex multi-service architectures.                           |
| **[Configuration as Code]** | Manages environment-specific configs via version-controlled files.             | For teams using Terraform/Ansible with dynamic configurations.                 |
| **[Rollback Strategy]**    | Documents procedures for reverting to previous deployments.                    | Critical systems requiring high availability.                                 |
| **[Canary Releases]**      | Gradually rolls out changes to a subset of users.                               | High-traffic applications needing zero-downtime updates.                        |
| **[Service Mesh Conventions]** | Standardizes service-to-service communication (e.g., Istio, Linkerd).       | Microservices architectures with distributed tracing requirements.              |

---
## **Best Practices**
1. **Enforce with CI Gates**: Reject PRs/deployments with non-compliant naming (e.g., using `git-hooks` or CI linting).
2. **Document Exceptions**: Keep a `DEPLOYMENT_CONVENTIONS.md` file in the repo to explain deviations.
3. **Tooling Support**: Integrate with:
   - **CI/CD**: GitHub Actions, GitLab CI, Jenkins.
   - **Orchestration**: Kubernetes Helm charts, AWS CodeDeploy.
   - **Monitoring**: Prometheus labels for deployments (`job=myapp-api-v1.0.0-prod`).
4. **Audit Trails**: Use tools like [Argo Rollouts](https://argoproj.github.io/argo-rollouts/) to track canary deployments.

---
## **Troubleshooting**
| **Issue**                          | **Solution**                                                                 |
|-------------------------------------|------------------------------------------------------------------------------|
| Ambiguous artifact names            | Use `prefix-artifact-type` (e.g., `myapp-db-mysql`).                         |
| Missing environment suffixes        | Standardize on `-dev`, `-staging`, `-prod` for clarity.                      |
| Version conflicts in Docker         | Tag images with `{version}-{env}` to avoid overlap (e.g., `v1.0.0` vs `v1.0.0-prod`). |
| CI/CD pipeline failures             | Validate tags in the pipeline (e.g., regex checks for `v[0-9]+\.[0-9]+\.[0-9]+-prod`). |

---
**See also**:
- [CNCF Deployment Best Practices](https://github.com/cncf/deployment-patterns)
- [12-Factor App](https://12factor.net/) (for conventions on codebase structure).