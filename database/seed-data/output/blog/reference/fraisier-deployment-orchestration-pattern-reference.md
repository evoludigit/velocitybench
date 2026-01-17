# **[Pattern] Fraisier: Multi-Service Deployment Orchestration – Reference Guide**

---
## **1. Overview**
Fraisier is a **deployment orchestration pattern** that centralizes the management of multiple services via a **single `fraises.yaml` configuration file**. It automates deployments across environments (dev, staging, prod) when Git repositories receive push events, supporting **GitHub, GitLab, Gitea, and Bitbucket** (cloud/self-hosted).

Key features:
- **Single-config** (`fraises.yaml`) for all services, environments, and Git integrations.
- **Event-driven** deployments via Git webhooks (no manual triggers).
- **Health checks** and **systemd integration** for reliability.
- **SQLite-backed deployment history** for auditing.
- **Python-based** with modular design for extensibility.

---

## **2. Key Components**
| Component               | Purpose                                                                 |
|-------------------------|-------------------------------------------------------------------------|
| **fraises.yaml**        | Unified configuration for all services, environments, and Git providers |
| **Fraisier CLI**        | Deploy (`fraisier deploy`), status (`fraisier status`), and history (`fraisier history`) commands |
| **Webhook Server**      | Listens for Git push events and triggers deployments automatically      |
| **Git Provider Abstraction** | Unified interface for GitHub, GitLab, Gitea, Bitbucket (cloud/self-hosted) |
| **Deployment Database** | SQLite database tracking deployments (status, logs, timing)            |

---

## **3. Schema Reference**
Below is the structure of `fraises.yaml`. Each service, environment, and Git integration is defined here.

### **Top-Level Schema**
```yaml
services: # List of all services managed by Fraisier
  - name: my_service_1
    provider: my_git_provider  # Reference to a Git provider config below
    environments: # Maps to environment configs
      - dev
      - staging
      - prod
  - name: another_service
    provider: another_git_provider
    environments:
      - staging
      - prod

# Git provider configurations (GitHub, GitLab, Gitea, Bitbucket)
git_providers:
  my_git_provider:
    type: github
    url: https://github.com/myorg/repo.git
    webhook_secret: "my-secret-key"
    branch_mapping: # Maps branches to environments
      main: prod
      develop: staging
      feature/*: dev

  another_git_provider:
    type: gitlab
    url: https://gitlab.com/myorg/repo.git
    webhook_secret: "another-secret-key"
    branch_mapping:
      main: prod
      staging: staging

# Environment configurations (shared or per-service)
environments:
  dev:
    host: dev.example.com
    ports:
      - 8080:80
      - 9090:22
    health_check: http://dev.example.com/health
    systemd_unit: my_service_dev.service

  staging:
    host: staging.example.com
    ports:
      - 8080:80
    health_check: http://staging.example.com/health
```

### **Field Definitions**
| Field               | Type     | Required | Description                                                                 |
|---------------------|----------|----------|-----------------------------------------------------------------------------|
| `services`          | `list`   | Yes      | List of services with Git provider and environment references.              |
| `name`              | `string` | Yes      | Unique identifier for the service.                                           |
| `provider`          | `string` | Yes      | Reference to a Git provider config (`git_providers.*`).                     |
| `environments`      | `list`   | Yes      | List of environments this service deploys to (e.g., `dev`, `staging`).     |
| `git_providers`     | `dict`   | Yes      | Git provider configurations (GitHub, GitLab, etc.).                          |
| `type`              | `string` | Yes      | Git provider type (`github`, `gitlab`, `gitea`, `bitbucket`).                |
| `url`               | `string` | Yes      | Repository URL.                                                              |
| `webhook_secret`    | `string` | Yes      | Secret for Git webhook verification.                                         |
| `branch_mapping`    | `dict`   | Yes      | Maps branches to environments (e.g., `main: prod`).                         |
| `environments`      | `dict`   | No*      | Shared environment configs (applied to all services unless overridden).     |
| `host`              | `string` | Yes      | Deployment host (e.g., `dev.example.com`).                                  |
| `ports`             | `list`   | Yes      | Map container ports to host ports (e.g., `[8080:80]`).                      |
| `health_check`      | `string` | Yes      | URL for health checks (e.g., `/health`).                                    |
| `systemd_unit`      | `string` | No       | Name of the `systemd` unit file for service management.                     |

*(Optional if per-service environments are defined in `services.*`.)*

---

## **4. Query Examples**
### **4.1 Deploy a Service to an Environment**
```bash
fraisier deploy my_service_1 dev
```
- Deploys `my_service_1` to the `dev` environment (as defined in `fraises.yaml`).
- Uses the Git provider configured for `my_service_1`.

### **4.2 Check Deployment Status**
```bash
fraisier status my_service_1
```
- Returns the latest deployment status for `my_service_1` across all environments.

### **4.3 View Deployment History**
```bash
fraisier history my_service_1 prod --limit 5
```
- Lists the last 5 deployments for `my_service_1` in the `prod` environment.
- Includes timestamps, commit hashes, and status (success/failure).

### **4.4 Trigger a Manual Deployment (Bypass Webhook)**
```bash
fraisier deploy my_service_1 staging --force
```
- Forces a deployment to `staging` regardless of Git webhook triggers.
- Useful for testing or emergency updates.

### **4.5 Get Environment-Specific Config**
```bash
fraisier env dev
```
- Outputs the full `environments.dev` config (host, ports, health check, etc.).

---

## **5. Webhook Integration**
### **GitHub/GitLab/Gitea/Bitbucket Setup**
1. **Configure a webhook** in your Git provider’s repo settings:
   - **Endpoint:** `https://your-fraisier-server/webhook`
   - **Secret:** Match the `webhook_secret` in `fraises.yaml`.
   - **Triggers:** `Push events` (or `Merge request events` for MR-based deployments).

2. **Branch Mapping**:
   - Pushes to `main` → Deploys to `prod`.
   - Pushes to `feature/*` → Deploys to `dev`.
   - Custom rules can be added in `branch_mapping`.

3. **Example GitHub Webhook Payload**:
   ```json
   {
     "ref": "refs/heads/main",
     "before": "abc123",
     "after": "def456",
     "repository": { "url": "https://github.com/myorg/repo.git" }
   }
   ```
   - Fraisier matches `main` to `prod` (from `branch_mapping`) and triggers deployment.

---

## **6. Deployment Workflow**
1. **Git Push** → Webhook fires to Fraisier.
2. **Fraisier** parses the event, checks `branch_mapping`, and resolves the target environment.
3. **Deployments** run in parallel (or sequentially, if configured) for all matched environments.
4. **Health checks** verify success; results are logged to the SQLite DB.
5. **systemd** manages long-running services (if configured).

---

## **7. Database Schema (SQLite)**
| Table         | Columns                          | Description                                  |
|---------------|----------------------------------|----------------------------------------------|
| `deployments` | `id`, `service`, `environment`, `commit_hash`, `status`, `started_at`, `ended_at`, `logs` | Tracks all deployments with metadata.         |
| `services`    | `id`, `name`, `provider`          | References services defined in `fraises.yaml`.|
| `environments`| `id`, `name`, `host`, `ports`     | References environment configs.              |

**Example Query:**
```sql
SELECT service, environment, status, ended_at
FROM deployments
WHERE service = 'my_service_1'
ORDER BY ended_at DESC
LIMIT 10;
```

---

## **8. Systemd Integration**
Fraisier supports `systemd` for service management:
- **Unit File Example (`my_service_dev.service`)**:
  ```ini
  [Unit]
  Description=My Service (Dev)
  After=network.target

  [Service]
  ExecStart=/path/to/start-my-service.sh
  Restart=always
  User=myuser

  [Install]
  WantedBy=multi-user.target
  ```
- Deployments link to this unit for lifecycle control (start/restart/stop).

---

## **9. Error Handling & Retries**
| Error Scenario               | Action Taken                                      |
|------------------------------|---------------------------------------------------|
| Git webhook signature mismatch | Logs error, ignores request.                      |
| Failed health check           | Marks deployment as `failed`, retries once.        |
| Database lock conflict        | Retries deployment after a delay.                 |
| Missing environment config   | Fails fast with clear error in logs.              |

---

## **10. Related Patterns**
1. **GitOps with ArgoCD/Flux**
   - Fraisier can complement GitOps by handling **manual overrides** or **legacy deployments** not managed by ArgoCD.
   - Use Fraisier for **one-off deployments** while keeping ArgoCD for declarative syncs.

2. **Canary Deployments**
   - Extend `fraises.yaml` to support **traffic splitting** by adding a `canary` field:
     ```yaml
     environments:
       prod:
         canary:
           target: 10%  # Routes 10% of traffic to the new deploy
     ```

3. **Multi-Cloud Deployments**
   - Add a `cloud_providers` section to `fraises.yaml`:
     ```yaml
     cloud_providers:
       aws:
         region: us-west-2
         role_arn: arn:aws:iam::123456789012:role/DeployRole
     ```
   - Integrate with AWS CLI, GCP SDK, or Azure CLI for cross-cloud support.

4. **Secret Management**
   - Use **HashiCorp Vault** or **AWS Secrets Manager** for dynamic secrets:
     ```yaml
     environments:
       prod:
         secrets:
           db_password: "vault:secret/data/myapp/db_password"
     ```

5. **Blue-Green Deployments**
   - Add a `blue_green` field to `fraises.yaml`:
     ```yaml
     environments:
       prod:
         blue_green:
           swap_after: 5m  # Switch traffic after 5 minutes of health checks
     ```

---

## **11. Troubleshooting**
| Issue                          | Solution                                                                 |
|--------------------------------|--------------------------------------------------------------------------|
| Webhook not triggering deploy  | Verify `webhook_secret` matches and the Git provider’s webhook URL is correct. |
| Deployment hangs               | Check `systemd` logs: `journalctl -u my_service_dev.service`              |
| Missing environment config     | Ensure `environments.*` is defined in `fraises.yaml`.                    |
| Database corruption            | Run `fraisier db migrate` to reset and reapply migrations.                |

---

## **12. Extending Fraisier**
To add support for a new Git provider:
1. **Implement the Provider Interface**:
   ```python
   class GitProvider:
       def fetch_latest_commit(self, repo_url: str) -> str:
           # Returns latest commit hash
       def listen_for_webhooks(self, secret: str, callback: Callable):
           # Starts webhook server
   ```

2. **Register in `fraises.yaml`**:
   ```yaml
   git_providers:
     new_provider:
       type: custom_provider  # Add this to supported types
       url: https://example.com/repo.git
       webhook_secret: "my-secret"
   ```

3. **Add Health Checks**:
   Extend the `health_check` logic to support custom endpoints (e.g., gRPC, DB connectivity).

---
## **13. CLI Reference**
| Command               | Description                                                                 |
|-----------------------|-----------------------------------------------------------------------------|
| `fraisier deploy <service> <env>` | Deploy a service to an environment.                                        |
| `fraisier status <service>`       | Show latest deployment status.                                               |
| `fraisier history <service> <env>` | List deployment history.                                                     |
| `fraisier env <name>`              | Output environment config.                                                   |
| `fraisier db migrate`              | Run database migrations (if schema changes).                                |
| `fraisier webhook test <secret>`   | Verify webhook setup (returns 200 if working).                              |

---
## **14. Example `fraises.yaml`**
```yaml
services:
  - name: frontend
    provider: github_frontend
    environments: [dev, staging, prod]

  - name: backend
    provider: gitlab_backend
    environments: [staging, prod]

git_providers:
  github_frontend:
    type: github
    url: https://github.com/myorg/frontend.git
    webhook_secret: "github-secret-123"
    branch_mapping:
      main: prod
      feature/*: dev

  gitlab_backend:
    type: gitlab
    url: https://gitlab.com/myorg/backend.git
    webhook_secret: "gitlab-secret-456"
    branch_mapping:
      main: prod
      staging: staging

environments:
  dev:
    host: frontend-dev.example.com
    ports: [8080:80, 9090:22]
    health_check: http://frontend-dev.example.com/health

  prod:
    host: frontend-prod.example.com
    ports: [80:80]
    health_check: http://frontend-prod.example.com/health
    systemd_unit: frontend_prod.service
```

---
## **15. Migration from Legacy Systems**
### **From Docker Compose**
- Move service configs from `docker-compose.yml` → `fraises.yaml`.
- Replace `docker-compose up` with `fraisier deploy`.

### **From Manual Git Hooks**
- Remove local Git hooks; rely on Fraisier’s webhook server.
- Ensure `branch_mapping` covers all legacy triggers.

### **From Kubernetes**
- Use Fraisier for **ad-hoc deployments** while keeping Kubernetes for CI/CD.
- Add a `k8s` provider to `fraises.yaml`:
  ```yaml
  cloud_providers:
    kubernetes:
      context: my-cluster
      namespace: my-namespace
  ```

---
## **16. Limits & Quotas**
| Resource          | Limit                          |
|-------------------|--------------------------------|
| Concurrent deploy | 10 per environment (configurable) |
| Webhook rate      | 5 requests/second (default)    |
| Deployment history| 10,000 entries (SQLite auto-prunes) |
| Git providers     | 5 simultaneously (extend with async workers) |

---
## **17. Security**
- **Webhook Secrets**: Always use HTTPS and enforce `webhook_secret` validation.
- **Database**: Store SQLite in a restricted directory (`/var/lib/fraisier/db/`).
- **Logs**: Rotate logs daily (`/var/log/fraisier/deployments.log`).

---
## **18. Conclusion**
Fraisier simplifies **multi-service deployments** by centralizing configs, automating Git-triggered deployments, and integrating seamlessly with **systemd**, **health checks**, and **Git providers**. Use it for:
- **Legacy systems** needing GitOps without rewriting.
- **Hybrid deployments** (CI/CD + manual overrides).
- **Cross-cloud** or **multi-provider** workflows.

For feedback or issues, open a GitHub issue in the [Fraisier repo](https://github.com/yourorg/fraisier).