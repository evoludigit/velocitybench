# **[Pattern] GitLab CI Integration Patterns: Reference Guide**

---

## **Overview**
GitLab CI/CD integrates seamlessly with GitLab and external tools via **CI/CD pipelines**, **triggers**, **webhooks**, **APIs**, and **custom integrations**. This pattern defines reusable integration approaches—such as **pipeline orchestration**, **parallel testing**, **artifact management**, and **cross-service synchronization**—to streamline workflows. It covers **implementation details** (e.g., `.gitlab-ci.yml` configurations, API calls, and job dependencies), **best practices** (e.g., caching strategies, role-based access control), and common pitfalls (e.g., flaky tests, rate limits, or over-optimized pipelines). This guide assumes familiarity with **GitLab CI/CD basics**, including jobs, stages, and artifacts.

---

## **Schema Reference**

Below is a structured table of key components and their properties for common GitLab CI integration patterns.

| **Component**               | **Purpose**                                                                                     | **Key Properties**                                                                                     | **Example Values**                                                                                     |
|-----------------------------|-------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| **Pipeline Type**           | Defines how jobs are triggered.                                                                 | Type (Manual, Scheduled, Pipeline, Trigger, Auto DevOps)                                            | `scheduled`, `pipeline`                                                                             |
| **Job**                     | Represents a single task in a pipeline.                                                          | `name`, `stage`, `script`, `rules`, `artifacts`, `dependencies`, `cache`, `timeout`, `tags`            | `name: "build"`, `stage: "test"`, `script: ["npm install"]`                                         |
| **Trigger Source**          | How jobs are triggered (e.g., branch push, merge request, API).                                  | Source (Push, Webhook, API, Manual)                                                                   | `rules: - if: '$CI_PIPELINE_SOURCE == "push"'`                                                       |
| **Artifact**                | Intermediate or final output shared between jobs.                                                | `paths`, `expire_in`, `when`, `unpack: true`                                                         | `paths: ["dist/"], expire_in: 1 week`                                                              |
| **Cache**                   | Speeds up pipelines by storing dependencies.                                                      | `paths`, `key`, `policy`, `when`                                                                      | `cache: { key: "$CI_COMMIT_REF_SLUG", paths: ["node_modules/"] }`                                   |
| **Parallelization**         | Runs jobs concurrently to optimize execution.                                                    | `parallel: N`, `matrix` (strategy)                                                                    | `parallel: 4`, `matrix: ["os: [linux, windows]"]`                                                  |
| **Webhook**                 | External system triggers GitLab CI via HTTP.                                                     | `secret`, `url`, `event`                                                                              | `url: "https://api.example.com/webhook", event: "push"`                                              |
| **Auto DevOps**             | Automates testing, security scanning, and deployment.                                             | `use_auto_devops: true`, `auto_devops_type`                                                          | `auto_devops_type: merge_request`                                                                   |
| **Deploy Key**              | Secure SSH access for deployments.                                                               | `host`, `username`, `private_key`                                                                     | `host: "deploy.example.com", private_key: "$DEPLOY_SSH_KEY"`                                         |
| **API Integration**         | Uses GitLab’s REST API to fetch/config data dynamically.                                          | `endpoint`, `auth` (token/bearer)                                                                    | `GET /api/v4/projects/$CI_PROJECT_ID/merge_requests`                                               |
| **Environment**             | Manages deployment stages (e.g., staging, production).                                           | `name`, `on_stop`, `deploy_stop_job`                                                                 | `environment: [name: "staging", url: "https://staging.example.com"]`                                |
| **Custom Scripts**          | Extends CI with shell/Python scripts for complex logic.                                          | `script: ["python validate.py", "run_tests.sh"]`                                                     | `script: ["docker build . && docker push myrepo/image:latest"]`                                     |

---

## **Implementation Details by Pattern**

### **1. Pipeline Orchestration**
Use **job dependencies**, **stages**, and **conditions** to control workflows.

#### **Example: Sequential & Parallel Jobs**
```yaml
stages:
  - build
  - test
  - deploy

build_job:
  stage: build
  script: ["docker build -t myapp ."]
  artifacts:
    paths:
      - dist/

test_job:
  stage: test
  script: ["npm test"]
  needs: ["build_job"]  # Dependency

deploy_job:
  stage: deploy
  script: ["docker push myapp"]
  environment:
    name: production
    url: "https://example.com"
  only:
    - main  # Runs only on `main` branch
```

#### **Key Considerations**
- **`needs`** replaces `artifacts:after_script` in newer GitLab versions.
- **`only/except`** filters jobs by branch/tag.
- **`rules`** (more powerful than `only/except`) supports complex conditions:
  ```yaml
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
    - when: manual  # Manual approval
  ```

---

### **2. Parallel Testing with Matrix Strategy**
Run tests on multiple OS/version combinations simultaneously.

#### **Example: Matrix-Powered Tests**
```yaml
test_job:
  stage: test
  script: ["npm test"]
  parallel: 4  # 4 parallel jobs
  tags:
    - docker
  matrix:
    - OS: [ubuntu, windows]
      NODE_VERSION: [14, 16]
```

#### **Best Practices**
- Limit matrix size to avoid rate limits.
- Use `allow_failure: true` for non-critical tests.
- Cache dependencies (`node_modules`) to reduce rebuilds.

---

### **3. Artifact & Cache Management**
Optimize storage and speed.

#### **Example: Artifact + Cache**
```yaml
cache:
  key: "${CI_JOB_NAME}"
  paths:
    - node_modules/
    - .next/cache

build_job:
  artifacts:
    paths:
      - dist/
    expire_in: 1 week
```

#### **Common Pitfalls**
- **Cache bloat**: Exclude unnecessary files (e.g., `node_modules` if using `npm ci`).
- **Artifact size limits**: GitLab caps artifacts at **5 GB** (adjust `expire_in`).
- **Cross-job caching**: Use `paths: ["$CI_PROJECT_DIR/**/*"]` cautiously.

---

### **4. Webhook Triggers**
External systems (e.g., Slack, Jenkins) can trigger GitLab CI.

#### **Example: Webhook Setup**
```yaml
trigger_job:
  stage: deploy
  trigger:
    include: deploy.yml
    strategy: depend
  rules:
    - if: '$CI_PIPELINE_SOURCE == "web"'
```

#### **Setup Steps**
1. **Generate a webhook secret** in GitLab (`Settings > Webhooks`).
2. **Configure the trigger**:
   ```bash
   curl --request POST \
     --url "https://gitlab.example.com/api/v4/projects/$PROJECT_ID/trigger/pipeline" \
     --header "PRIVATE-TOKEN: $SECRET_TOKEN" \
     --form "ref=main"
   ```

---

### **5. Auto DevOps Integration**
Leverage GitLab’s built-in automation.

#### **Example: Auto DevOps for MRs**
```yaml
use_auto_devops: true
auto_devops_type: merge_request
```

#### **Key Features**
- **Security scanning** (SAST, DAST).
- **Auto-remediation** for failed pipelines.
- **Deployment approvals** for protected branches.

---

### **6. API-Driven Integrations**
Fetch/config data dynamically via GitLab’s REST API.

#### **Example: Fetch Merge Requests**
```yaml
fetch_mrs:
  script:
    - |
      MRs=$(curl --header "PRIVATE-TOKEN: $CI_JOB_TOKEN" \
        "https://gitlab.example.com/api/v4/projects/$CI_PROJECT_ID/merge_requests")
      echo "$MRs" > mrs.json
```

#### **Best Practices**
- Use `$CI_JOB_TOKEN` for authentication (scoped access).
- Cache API responses to avoid rate limits.
- Rate limits: **60 requests/minute** (authenticated).

---

## **Query Examples**

### **1. List All Pipelines for a Project**
```bash
curl --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "https://gitlab.example.com/api/v4/projects/$PROJECT_ID/pipelines"
```

### **2. Get Pipeline Artifacts**
```bash
curl --header "PRIVATE-TOKEN: $CI_JOB_TOKEN" \
  --output artifacts.zip \
  "https://gitlab.example.com/api/v4/projects/$PROJECT_ID/jobs/$JOB_ID/artifacts"
```

### **3. Trigger a Pipeline via Webhook**
```bash
curl --request POST \
  --url "https://gitlab.example.com/api/v4/projects/$PROJECT_ID/trigger/pipeline" \
  --header "PRIVATE-TOKEN: $WEBHOOK_SECRET" \
  --form "ref=feature-branch"
```

---

## **Common Pitfalls & Mitigations**

| **Pitfall**                          | **Solution**                                                                                     |
|---------------------------------------|-------------------------------------------------------------------------------------------------|
| **Flaky tests**                       | Use `retry: 2` and isolate tests in separate jobs.                                              |
| **Pipeline timeout**                  | Increase `timeout` (max: **10 hours**) or split into smaller jobs.                             |
| **Over-parallelization**              | Limit `parallel` jobs to avoid resource contention.                                            |
| **Uncontrolled branching**           | Use `rules` or `only/except` to restrict pipeline triggers.                                     |
| **Large artifacts**                  | Compress artifacts or use `when: on_failure` to avoid bloating successful runs.                  |
| **API rate limits**                  | Cache responses or use `retry` with exponential backoff.                                         |
| **Secret exposure**                   | Use **variables with masks** (e.g., `****`) and restrict `$CI_JOB_TOKEN` scope.                   |

---

## **Related Patterns**

1. **[Deployment Strategies](https://docs.gitlab.com/ee/ci/deployment_strategies/)**
   - Compare **rolling**, **blue-green**, and **canary** deployments in GitLab CI.

2. **[Infrastructure as Code (IaC)](https://docs.gitlab.com/ee/user/infrastructure/terraform_integration.html)**
   - Automate cloud provisioning (Terraform, Ansible) in CI pipelines.

3. **[Security Scanning](https://docs.gitlab.com/ee/user/application_security/scanning/index.html)**
   - Integrate **SAST**, **DAST**, and **container scanning** into pipelines.

4. **[GitLab CI for CI/CD Tools](https://docs.gitlab.com/ee/ci/integration/gitlab_ci_cd_tools.html)**
   - Extend GitLab CI with **Jenkins**, **ArgoCD**, or **Kubernetes**.

5. **[Monitoring & Observability](https://docs.gitlab.com/ee/ci/monitoring/index.html)**
   - Track pipeline performance with **GitLab’s CI Analytics** or **Prometheus**.

---
**Last Updated:** [Version]
**Feedback:** [GitLab Community Forum Link]