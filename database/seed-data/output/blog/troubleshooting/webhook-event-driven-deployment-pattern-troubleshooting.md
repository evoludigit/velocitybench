# **Debugging *Fraisier: Webhook Event-Driven Deployment* – A Troubleshooting Guide**

## **1. Overview**
The **Webhook Event-Driven Deployment** pattern automates deployments by triggering CI/CD pipelines on Git push events. This guide helps diagnose and resolve issues when webhooks fail to trigger deployments or behave unexpectedly.

---

## **2. Symptom Checklist**
Check which symptoms apply to your environment:

| Symptom | Description |
|---------|-------------|
| ❌ No Deployment Trigger | Pushes to a branch don’t trigger deployments |
| ❌ Delayed Deployments | Webhooks fire but deployments take longer than expected |
| ❌Wrong Service Deployed | Wrong Git branch/service gets deployed |
| ❌Duplicate Deployments | Same commit triggers multiple deployments |
| ❌Webhook Errors | HTTP 5xx responses, timeouts, or 4xx errors |
| ❌OAuth/Token Errors | Authentication failures in Git/GitHub webhook |
| ❌CI/CD Pipeline Fails | Webhook fires but pipeline fails silently |
| ❌No Logging | Hard to trace why a deployment failed |

---

## **3. Common Issues & Fixes**

### **A. Webhook Not Firing on Push**
**Symptoms:**
- `curl -v <WEBHOOK_URL>` returns a 200 but no deployment occurs.
- Git push logs show no webhook invocation.

**Root Causes & Fixes:**

1. **Webhook Not Configured Correctly**
   - Ensure the webhook URL is correctly pointing to your CI/CD service (GitHub Actions, GitLab CI, etc.).
   - Verify the **secret key** (if used for HMAC verification) matches the webhook settings.

   ```bash
   # Check GitHub webhook URL (should match CI/CD webhook endpoint)
   curl -H "Accept: application/vnd.github+json" \
   -H "Authorization: Bearer <TOKEN>" \
   "https://api.github.com/repos/<OWNER>/<REPO>/hooks/<WEBHOOK_ID>"

   # Compare with your CI/CD webhook URL (e.g., GitHub Actions)
   ```
   **Fix:** Update the webhook URL in Git/GitHub → Settings → Webhooks.

2. **Event Filtering (Wrong Triggers)**
   - GitHub/GitLab may not be sending events due to event restrictions.
   - Example: Only `push` events should trigger deployments.

   ```yaml
   # Example GitHub Actions webhook config (ensure `push` is included)
   # https://github.com/<ORG>/<REPO>/settings/hooks/<WEBHOOK_ID>
   ```
   **Fix:** Check `Events` → Ensure `push` is selected.

3. **Network/API Rate Limits**
   - GitHub/GitLab may block requests if too many failed webhooks occur.
   - Check `/repos/{owner}/{repo}/hooks/{hook_id}` for API limits.

   ```bash
   curl -H "Authorization: Bearer <TOKEN>" \
   "https://api.github.com/repos/<OWNER>/<REPO>/hooks/<WEBHOOK_ID>/deliveries"
   ```
   **Fix:** Retry with exponential backoff or increase API rate limits.

---

### **B. Delayed or Failed Deployments**
**Symptoms:**
- Webhook fires but deployment never completes.
- CI/CD logs show `timeout` or `webhook timeout`.

**Root Causes & Fixes:**

1. **CI/CD Pipeline Timeout**
   - Default GitHub Actions/GitLab runner timeouts may block deployments.
   - Common timeout: **6 hours** (GitHub) or **1 hour** (GitLab).

   ```yaml
   # Example GitHub Actions with increased timeout (max 6h)
   jobs:
     deploy:
       runs-on: ubuntu-latest
       steps:
         - name: Deploy
           run: ./deploy.sh
           timeout-minutes: 300  # Max 300m (5h)
   ```
   **Fix:** Extend timeout or optimize deployment scripts.

2. **Webhook Payload Validation Failed**
   - If using HMAC, the payload may not match the expected signature.

   ```bash
   # Check GitHub webhook payload integrity
   HASH=$(curl -s -H "Authorization: token <TOKEN>" \
   --data-urlencode 'payload={"ref":"refs/heads/main"}' \
   "https://api.github.com/repos/<OWNER>/<REPO>/hooks/<WEBHOOK_ID>/deliveries")

   curl -H "X-Hub-Signature: sha256=<HASH>" \
   -H "Content-Type: application/json" \
   -X POST <CI_CD_WEBHOOK_URL>
   ```
   **Fix:** Verify the `X-Hub-Signature` in logs and regenerate secrets if needed.

3. **Race Conditions in GitOps Deployments**
   - If using ArgoCD/Kustomize, multiple deployments may conflict.
   - Check ArgoCD logs for `conflicting resources`.

   ```bash
   kubectl logs -n argocd <ARGOCD_POD> | grep "conflict"
   ```
   **Fix:** Use `helm lock` or ensure idempotent deployments.

---

### **C. Wrong Service Deployed**
**Symptoms:**
- Wrong branch/service is deployed (e.g., `main` instead of `dev`).

**Root Causes & Fixes:**

1. **Incorrect Branch Filtering**
   - Webhook triggers but pipeline ignores branch checks.

   ```yaml
   # GitHub Actions: Only deploy from `main` or `dev`
   jobs:
     deploy:
       if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/dev'
   ```
   **Fix:** Strictly enforce branch matching.

2. **Webhook Payload Misinterpretation**
   - GitHub sends `ref` as `refs/heads/main` but your pipeline expects `main`.

   ```bash
   # Check payload structure (e.g., GitHub Actions env vars)
   echo "${{ github.ref }}"
   ```
   **Fix:** Map `ref` to branch names in your workflow.

---

### **D. Duplicate Deployments**
**Symptoms:**
- Same commit triggers multiple deployments.

**Root Causes & Fixes:**

1. **Multiple Webhooks Configured**
   - Duplicate GitHub/GitLab webhooks may fire simultaneously.

   ```bash
   # List all webhooks (GitHub)
   curl -H "Authorization: token <TOKEN>" \
   "https://api.github.com/repos/<OWNER>/<REPO>/hooks"
   ```
   **Fix:** Delete redundant webhooks.

2. **Webhook Delivery Retries**
   - GitHub/GitLab may retry failed webhooks.

   ```yaml
   # GitHub Actions: Prevent retries
   on:
     push:
       branches: [ main ]
     # Remove redundant triggers
   ```
   **Fix:** Disable retries in webhook settings.

---

## **4. Debugging Tools & Techniques**

### **A. Webhook Payload Debugging**
Use `curl` to inspect GitHub/GitLab payloads:

```bash
# Check GitHub webhook payload
curl -H "Authorization: token <TOKEN>" \
"https://api.github.com/repos/<OWNER>/<REPO>/hooks/<WEBHOOK_ID>/deliveries"

# Test webhook manually
curl -X POST -H "Content-Type: application/json" \
-H "Authorization: token <TOKEN>" \
--data '{"ref":"refs/heads/main"}' <CI_CD_WEBHOOK_URL>
```

### **B. CI/CD Logs**
- **GitHub Actions:** `Actions` tab → Check workflow runs.
- **GitLab CI:** `CI/CD → Pipelines` → Check job logs.

```bash
# View GitHub Actions logs
gh run view <RUN_ID> --log

# View GitLab CI logs
glab ci log <PIPELINE_ID>
```

### **C. Network Inspection**
- Check webhook delivery times:

```bash
# Measure webhook response time
time curl -v <WEBHOOK_URL> >/dev/null
```

### **D. GitOps Auditing**
If using ArgoCD/Kustomize:
```bash
# Verify ArgoCD sync status
kubectl get syncstatus -n argocd
```

---

## **5. Prevention Strategies**

### **A. Automate Webhook Validation**
- Use a test webhook endpoint to verify payloads before production.

```bash
# Example test webhook (FastAPI)
@app.post("/webhook-test")
def test_webhook(payload: dict):
    if payload["ref"] != "refs/heads/main":
        raise ValueError("Wrong branch")
    return {"status": "ok"}
```

### **B. Rate-Limit Webhooks**
- Use GitHub/GitLab `deliveries` API to monitor webhook health.

```bash
# Track failed webhook deliveries
curl -H "Authorization: token <TOKEN>" \
"https://api.github.com/repos/<OWNER>/<REPO>/hooks/<WEBHOOK_ID>/deliveries?per_page=10"
```

### **C. Idempotent Deployments**
- Ensure pipelines handle duplicate triggers gracefully:

```yaml
# GitHub Actions: Idempotent step
- name: Deploy
  run: ./deploy.sh || true  # Ignore failure if already deployed
```

### **D. Branch Protection Rules**
- Enforce `require status checks` to prevent bad deployments:

```bash
# GitHub: Branch protection
gh api repos/<OWNER>/<REPO>/branches/main/protection --input '{"required_status_checks": {"strict": true}}'
```

---

## **6. Summary Checklist**
| Step | Action |
|------|--------|
| ✅ Check webhook URL | Ensure it matches CI/CD endpoint |
| ✅ Validate payload | Test with `curl` and verify `ref` |
| ✅ Review CI/CD logs | Look for timeouts/errors |
| ✅ Audit GitOps sync | Check ArgoCD/Kustomize status |
| ✅ Disable duplicate triggers | Remove redundant webhooks |
| ✅ Set branch protection | Prevent wrong deployments |

---

## **7. When to Escalate**
- ✅ **API rate limits exceeded** → Contact GitHub/GitLab support.
- ✅ **CI/CD pipeline hangs forever** → Check runner health.
- ✅ **No logs available** → Reach out to infrastructure team.

---
**Final Tip:** Use **GitHub/GitLab API** to automate webhook health checks in your monitoring stack!

---
This guide ensures quick resolution of Fraisier webhook issues while preventing future failures. Optimize deployments with **idempotency**, **branch protection**, and **debugging automation**. 🚀