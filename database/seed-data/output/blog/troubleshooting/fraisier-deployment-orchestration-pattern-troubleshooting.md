# **Debugging *Fraisier*: A Troubleshooting Guide for Multi-Service Deployment Orchestration**

## **1. Introduction**
*Fraisier* is designed to streamline deployment orchestration for multiple services (called "fraises") by centralizing configuration, automating webhook-based deployments, and ensuring consistency across environments (dev, staging, prod). When things go wrong, symptoms can range from scattered deployment artifacts to failed health checks—this guide helps you diagnose and resolve issues efficiently.

---

## **2. Symptom Checklist**
Before diving into fixes, quickly verify which symptoms match your issue:

| **Symptom**                          | **Likely Cause**                          | **Action** |
|--------------------------------------|------------------------------------------|------------|
| Manual deployments via SSH scripts   | Missing centralized orchestration layer  | Check `fraisier` CLI or API usage |
| Webhook failures for multiple services | Misconfigured secrets or Git provider     | Review webhook payloads in logs |
| Inconsistent deployments across envs | Hardcoded paths in service configs        | Validate templates in `fraisier.yml` |
| No deployment history                | Missing logging or audit trail          | Check `fraisier db:query` or logs |
| Health checks failing after deploy   | Misaligned service dependencies          | Verify `fraisier service:check` |
| Git provider-specific errors          | Unsupported webhook endpoints            | Test with `curl` and Git provider docs |
| Slow deployments                     | Overlapping systemd services or I/O bottlenecks | Monitor with `systemd-cgls` |

---

## **3. Common Issues & Fixes**

### **A. Deployment Configuration Scattered**
**Symptom:** Each service has separate webhook configs, health checks, and systemd units.
**Root Cause:** No unified orchestrator enforcing consistency.

#### **Fix: Centralize with `fraisier.yml`**
```yaml
# /etc/fraisier/fraisier.yml (template example)
deployments:
  - name: api-service
    git_repo: git@github.com:org/api-service.git
    webhook_secret: ${{GITHUB_WEBHOOK_SECRET}}  # From env vars
    systemd_unit: /etc/systemd/system/api.service
    health_check: http://localhost:8080/health
    dependencies: [db-service]

  - name: frontend
    git_repo: gitlab://org/frontend.git  # GitLab support
    webhook_secret: ${{GITLAB_DEPLOY_KEY}}
    systemd_unit: /etc/systemd/system/frontend.service
    health_check: http://localhost:3000/api/health
```

**Steps:**
1. **Validate `fraisier.yml`** with `fraisier validate`:
   ```bash
   fraisier validate /etc/fraisier/fraisier.yml
   ```
2. **Generate systemd units dynamically**:
   ```bash
   fraisier systemd:generate --all
   ```
3. **Reload systemd**:
   ```bash
   sudo systemctl daemon-reload
   ```

---

### **B. Manual Deployments via SSH**
**Symptom:** Engineers SSH into servers to run deployment scripts.
**Root Cause:** Missing automation or `fraisier` CLI misuse.

#### **Fix: Use `fraisier deploy`**
```bash
# Deploy a single service (e.g., "api-service")
fraisier deploy api-service --env=prod

# Deploy all services in parallel (depends on `dependencies` in config)
fraisier deploy --parallel
```

**Debugging:**
- Check logs with `journalctl -u api.service -f`.
- If stuck, run in dry-run mode:
  ```bash
  fraisier deploy api-service --dry-run
  ```

---

### **C. Git Provider Lock-In**
**Symptom:** Only GitHub webhooks work; GitLab/Bitbucket fail.
**Root Cause:** Hardcoded GitHub-specific payload handling.

#### **Fix: Support Multi-Git Providers**
Modify `fraisier/webhooks.go` (or use a plugin system):
```go
// Example: Parse GitHub/GitLab webhook payloads
func HandleWebhook(payload []byte, provider string) error {
    switch provider {
    case "github":
        return parseGithubPayload(payload)
    case "gitlab":
        return parseGitlabPayload(payload)
    default:
        return fmt.Errorf("unsupported provider: %s", provider)
    }
}
```
**Test Locally:**
```bash
# Test GitHub payload
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"ref": "refs/heads/main"}' \
  http://localhost:3000/webhook?provider=github
```

---

### **D. No Deployment History**
**Symptom:** Can’t track what was deployed or when.
**Root Cause:** No logging/audit trail.

#### **Fix: Enable Audit Logging**
1. **Configure PostgreSQL for `fraisier`:**
   ```bash
   fraisier db:migrate
   ```
2. **Query deployment history:**
   ```bash
   fraisier db:query "SELECT * FROM deployments ORDER BY created_at DESC LIMIT 5;"
   ```
3. **Enable JSON logs:**
   ```bash
   export LOG_LEVEL=debug
   fraisier deploy api-service --log-format=json
   ```

---

### **E. Health Checks Failing**
**Symptom:** Services fail health checks post-deploy.
**Root Cause:** Missing dependencies or misaligned configs.

#### **Fix: Verify Dependencies**
1. **Check `fraisier.yml` dependencies:**
   ```yaml
   dependencies: [db-service]  # Ensures DB is up before API
   ```
2. **Run health checks manually:**
   ```bash
   fraisier service:check api-service
   ```
3. **Debug slow services:**
   ```bash
   # Check systemd resource limits
   systemctl list-units --type=service --state=failed
   ```

---

## **4. Debugging Tools & Techniques**
| **Tool**               | **Use Case**                                  | **Example Command**                          |
|-------------------------|-----------------------------------------------|---------------------------------------------|
| `fraisier validate`     | Check config syntax                           | `fraisier validate /etc/fraisier.yml`        |
| `journalctl`            | Debug systemd service failures               | `journalctl -u api.service -xe`              |
| `fraisier db:query`     | Inspect deployment history                    | `fraisier db:query "SELECT * FROM deployments"` |
| `curl`                  | Test webhook endpoints                        | `curl -X POST http://localhost:3000/webhook` |
| `systemd-analyze`       | Profile service startup time                  | `systemd-analyze blame`                     |
| `strace`                | Trace system calls (for deep dives)         | `strace -f /usr/bin/api-service 2>&1 | head` |

---

## **5. Prevention Strategies**
1. **Enforce Template Consistency**
   - Use `fraisier template:validate` to ensure all services use the same config structure.
   - Example:
     ```bash
     fraisier template:validate /path/to/service-configs
     ```

2. **Automate Rollback Testing**
   - Add a `--dry-run` flag to `fraisier deploy` to simulate rollbacks.
   - Example:
     ```bash
     fraisier deploy --dry-run | grep "Rollback steps"
     ```

3. **Git Provider Agnosticism**
   - Abstract webhook handling (see **Fix B**).
   - Test with `ngrok` for self-hosted providers:
     ```bash
     ngrok http 3000  # Expose webhook endpoint temporarily
     ```

4. **Health Check Timeouts**
   - Configure `fraisier.yml` with timeouts:
     ```yaml
     health_check:
       endpoint: /health
       timeout: 10s
     ```
   - Use `healthchecks.io` for external monitoring.

5. **CI/CD Integration**
   - Trigger deployments from multiple Git providers via `fraisier webhook:start`.
   - Example `.gitlab-ci.yml`:
     ```yaml
     deploy:
       script:
         - curl -X POST http://fraisier-server/webhook?provider=gitlab
     ```

---

## **6. When All Else Fails: Reset & Reconfigure**
1. **Reinitialize `fraisier`:**
   ```bash
   sudo systemctl stop fraisier
   rm -rf /var/lib/fraisier/*  # WARNING: Clears all state!
   fraisier db:migrate
   sudo systemctl start fraisier
   ```
2. **Re-deploy all services:**
   ```bash
   fraisier deploy --all --force
   ```

---

## **7. Summary Checklist for Quick Resolution**
| **Issue**                     | **Quick Fix**                                  | **Verify With**                     |
|-------------------------------|-----------------------------------------------|-------------------------------------|
| Scattered configs             | Use `fraisier.yml` + `fraisier validate`      | `fraisier systemd:generate`        |
| Manual SSH deployments        | `fraisier deploy <service>`                    | `journalctl` logs                   |
| Git provider errors           | Add `provider` field to webhook payloads      | Test with `curl`                    |
| No history                    | Enable PostgreSQL + `fraisier db:query`        | Query results                       |
| Health check failures         | Check `dependencies` in `fraisier.yml`         | `fraisier service:check`            |
| Slow deployments              | Review `systemd-analyze`                       | Top resource consumers              |

---
**Final Note:** *Fraisier* thrives on consistency—standardize configs, validate early, and automate rollbacks. If issues persist, check the [Fraisier GitHub Issues](link) or enable debug logging (`LOG_LEVEL=debug`). Happy debugging! 🍓