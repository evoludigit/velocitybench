# **[Pattern] GitHub Actions Integration Patterns – Reference Guide**

---

## **Overview**
GitHub Actions enables automation and CI/CD workflows directly within GitHub repositories. This reference guide details core **integration patterns** for leveraging GitHub Actions effectively, including event-driven workflows, reusable components, caching strategies, and security best practices. Whether you're deploying infrastructure, testing code, or orchestrating multi-step pipelines, this guide provides concrete examples and implementation details to ensure robust integrations while avoiding common pitfalls.

---

## **Key Concepts & Implementation Details**
GitHub Actions integrates with repositories via:
1. **Events** (triggers)
2. **Jobs** (parallel or sequential tasks)
3. **Steps** (actions or shell commands)
4. **Actions** (reusable units of logic)
5. **Artifacts** (outputs between jobs)
6. **Environments** (deployment stages)

### **Core Patterns**
| Pattern | Description |
|---------|------------|
| **Event-Driven Workflows** | Run jobs in response to GitHub events (e.g., `push`, `pull_request`). |
| **Reusable Workflows** | Define workflows once and call them from multiple repositories. |
| **Matrix Strategies** | Run jobs with varying configurations (e.g., OS, Python versions). |
| **Artifact Caching** | Cache dependencies (e.g., Node.js modules, Docker layers) to reduce redundancy. |
| **Secrets & Environments** | Securely manage credentials and restrict job execution to specific environments. |
| **Self-Hosted Runners** | Control execution environments for legacy systems or specialized hardware. |
| **Matrix + Artifacts** | Combine matrix strategies with caching for efficient parallel builds. |
| **Cancellation Policies** | Cancel outdated workflow runs to save resources. |

---

## **Schema Reference**

### **1. Basic Workflow Structure**
```yaml
name: Example Workflow
on: [push]  # Trigger: event
jobs:
  test:
    runs-on: ubuntu-latest  # Runner OS
    steps:
      - uses: actions/checkout@v4  # Checkout repo
      - run: npm install && npm test  # Execute commands
```

| Field | Type | Description |
|-------|------|-------------|
| `name` | String | Workflow identifier. |
| `on` | Object | Event triggers (e.g., `push`, `pull_request`). |
| `jobs.{job_id}` | Object | A job definition. |
| `runs-on` | String | Runner OS (e.g., `ubuntu-latest`, `windows-latest`). |
| `steps` | Array | Sequential steps (actions or shell commands). |
| `needs` | Object | Dependency between jobs (optional). |

---

### **2. Reusable Workflow**
```yaml
name: Reusable Workflow
on:
  workflow_call:
    inputs:
      env:
        description: 'Environment to deploy'
        required: true
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - run: echo "Deploying to ${{ inputs.env }}"
```

| Field | Type | Description |
|-------|------|-------------|
| `workflow_call` | Object | Trigger for reusable workflows. |
| `inputs` | Object | Parameters passed to the reusable workflow. |
| `outputs` | Object | Data returned from the workflow. |

---

### **3. Matrix Strategy**
```yaml
jobs:
  test-matrix:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [16, 18]
        os: [ubuntu-latest, windows-latest]
    steps:
      - run: node -v
```

| Field | Type | Description |
|-------|------|-------------|
| `strategy` | Object | Defines test matrices. |
| `matrix` | Object | Key-value pairs for variation (e.g., `node-version`). |
| `fail-fast` | Boolean | Stops remaining steps if one fails. |

---

### **4. Artifact Caching**
```yaml
steps:
  - uses: actions/cache@v3
    with:
      path: ~/.npm
      key: ${{ runner.os }}-npm-${{ hashFiles('package-lock.json') }}
  - run: npm install
```

| Field | Type | Description |
|-------|------|-------------|
| `path` | String | Directory to cache. |
| `key` | String | Cache identifier (must be unique). |
| `restore-keys` | Array | Fallback keys if primary fails. |

---

### **5. Secrets & Environments**
```yaml
env:
  AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
jobs:
  deploy:
    environment: production
    runs-on: ubuntu-latest
```

| Field | Type | Description |
|-------|------|-------------|
| `secrets` | Object | Access GitHub-secrets securely. |
| `environment` | String | Restricts workflows to specific environments. |

---

## **Query Examples**

### **1. List All Workflows in a Repository**
```bash
gh api repos/{owner}/{repo}/actions/workflows | jq '.[].name'
```
**Output:**
```json
[
  "CI Pipeline",
  "Deploy to Production"
]
```

---

### **2. Get Job Status for a Specific Workflow Run**
```bash
gh api repos/{owner}/{repo}/actions/runs/{run_id} | jq '.jobs[].status'
```
**Output:**
```json
["completed", "in_progress", "queued"]
```

---

### **3. Trigger a Reusable Workflow**
```bash
gh workflow run deploy.yml --env env=staging
```

---

## **Best Practices**
✅ **Modularize Workflows**: Use reusable workflows and actions to avoid duplication.
✅ **Cache Strategically**: Cache dependencies (e.g., `~/.npm`, `.cache`) to speed up builds.
✅ **Limit Concurrent Jobs**: Set `concurrency: 1` to prevent overlapping runs.
✅ **Secure Secrets**: Use `secrets` and environments to restrict access.
✅ **Monitor Costs**: Self-hosted runners incur costs; optimize usage.

---

## **Common Pitfalls & Fixes**
❌ **Overusing `ubuntu-latest`**: Mix OSes in matrix strategies for broader compatibility.
❌ **Ignoring Dependencies**: Always check `needs` for job dependencies.
❌ **No Artifact Retention**: Set `artifacts_retention_days` to avoid storage bloat.
❌ **Hardcoded Secrets**: Use GitHub Secrets or Vault for sensitive data.

---

## **Related Patterns**
1. **[CI/CD Pipeline]** – End-to-end automation for code testing and deployment.
2. **[Infrastructure as Code (IaC) Orchestration]** – Deploy cloud resources via workflows.
3. **[Dependency Management]** – Automate dependency updates with `dependabot`.
4. **[Security Scanning]** – Integrate tools like `trivy` or `snyk` in workflows.
5. **[Multi-Repository Workflows]** – Use `repository_dispatch` to trigger workflows across repos.

---
Would you like additional examples for a specific pattern (e.g., GitHub Pages deployment, Docker builds)?