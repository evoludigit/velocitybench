# **[Pattern] Fraisier: Webhook-Event Driven Deployment Reference Guide**

## **1. Overview**
The **Fraisier Webhook Event-Driven Deployment** pattern automates deployments by listening for push events from Git providers (GitHub, GitLab, Gitea, Bitbucket). When a push occurs on a mapped branch, the system routes the event to the corresponding **fraise (microservice)** and **environment**, triggering a zero-touch deployment. This approach eliminates manual intervention while supporting **provider signature verification** to ensure security.

Key benefits:
- **Fully automated CI/CD** without polling (e.g., cron jobs).
- **Multi-provider support** (GitHub, GitLab, Gitea, Bitbucket).
- **Fine-grained control** via branch-to-fraise/environment mapping.
- **Security-first** with cryptographic signature validation.

---

## **2. Core Concepts**

### **2.1 Webhook Server**
- **Purpose**: HTTP endpoint (REST API) that receives `POST` events from Git providers.
- **Supported Events**:
  - `push` (primary trigger for deployments).
  - `pull_request` (optional; can trigger staging deployments).
- **Security**:
  - Requires valid **Git provider signature** to prevent spoofing.
  - Uses **HMAC-SHA256** for verification (provider-specific keys).

### **2.2 Branch Mapping**
- **Routing Rule**: Each branch in a Git repo maps to:
  - A **fraise (microservice)**.
  - An **environment** (e.g., `dev`, `staging`, `prod`).
- **Format**:
  ```json
  {
    "branches": {
      "main": { "fraise": "api-service", "env": "production" },
      "feature/*": { "fraise": "auth-service", "env": "staging" }
    }
  }
  ```

### **2.3 Event Parser**
- **Provider Abstraction**: Normalizes Git provider webhook payloads into a unified schema.
  - Example formats:
    - **GitHub**: [`push` event](https://docs.github.com/en/webhooks/events/push).
    - **GitLab**: [`push_events` payload](https://docs.gitlab.com/ee/web_hooks/web_hook_events.html#push-event-payloads).
- **Key Fields Parsed**:
  - `ref` (branch/tag name).
  - `head_commit` (commit hash, messages, author).
  - `repository` (name, URL).

### **2.4 Deployment Executor**
- **Action**: Triggers deployment for the matched `fraise/environment`.
- **Steps**:
  1. Validates branch against mapping rules.
  2. Fetches latest commit from Git provider.
  3. Executes deployment via Fraisier’s CLI/API:
     ```bash
     fraise deploy --fraise=api-service --env=production --commit=abc123
     ```
- **Rollback Mechanism**: Optional automatic rollback on failure.

---

## **3. Schema Reference**

| **Field**               | **Type**       | **Description**                                                                 | **Example Values**                     |
|-------------------------|----------------|---------------------------------------------------------------------------------|----------------------------------------|
| **Event Type**          | String         | Type of Git event (e.g., `push`, `pull_request`).                              | `push`, `pull_request`                 |
| **Signature**           | Base64-encoded | HMAC signature for verification.                                              | `sha256=abc123...`                    |
| **Provider**            | String         | Git provider (GitHub, GitLab, Gitea, Bitbucket).                               | `github`, `gitlab`                     |
| **Branch**              | String         | Ref name (e.g., `main`, `feature/*`).                                          | `main`, `v1.0`                         |
| **Commit Hash**         | String         | Latest commit SHA in the push event.                                           | `abc1234567890`                        |
| **Commit Message**      | String         | Commit message (used for deployment context).                                  | `Fix login bug`                        |
| **Repository URL**      | String         | Source repo URL.                                                               | `https://github.com/user/repo.git`     |
| **Fraiser Mapping**     | Object         | Branch-to-fraise/environment mapping.                                          | `{ "main": { "fraise": "api", "env": "prod" } }` |
| **Deployment Status**   | String         | Result of deployment (success/failure).                                        | `success`, `failed`                    |

---

## **4. Implementation Steps**

### **4.1 Set Up Webhook Server**
1. **Deploy the Fraisier Webhook Listener**:
   ```bash
   # Using Docker (example)
   docker run -p 3000:3000 fraisier/webhook:latest
   ```
2. **Configure Git Provider Webhook**:
   - **GitHub/GitLab/Gitea/Bitbucket**: Add a webhook pointing to:
     ```
     http://<your-server>/webhook
     ```
   - **Payload URL**: `http://<your-server>/webhook`.
   - **Content Type**: `application/json`.
   - **Secret Key**: Provide a shared HMAC key (used for signature verification).

### **4.2 Define Branch Mappings**
Store mappings in a config file (e.g., `fraise-mappings.json`):
```json
{
  "default_provider": "github",
  "branches": {
    "main": {
      "fraise": "backend",
      "env": "production"
    },
    "feature/*": {
      "fraise": "frontend",
      "env": "staging"
    },
    "release/*": {
      "fraise": "mobile-app",
      "env": "production"
    }
  }
}
```
**Load mappings**:
```bash
fraise config set mappings ./fraise-mappings.json
```

### **4.3 Verify Webhook Signatures**
Fraisier validates signatures using a provider-specific key (stored in `fraise.config`):
```bash
fraise config set github_webhook_secret "your_hmac_key_here"
```
**Algorithm**: HMAC-SHA256 with the shared key.

### **4.4 Test Webhook Events**
Manually trigger a test event (e.g., `curl`):
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature: sha256=abc123..." \
  http://localhost:3000/webhook \
  -d '{
    "ref": "main",
    "head_commit": { "message": "Fix bug" },
    "repository": { "url": "https://github.com/user/repo" }
  }'
```

---

## **5. Query Examples**

### **5.1 GitHub Webhook Payload**
```json
{
  "ref": "refs/heads/main",
  "head_commit": {
    "message": "Update README",
    "id": "abc1234567890"
  },
  "repository": {
    "name": "my-app",
    "url": "https://github.com/user/my-app.git"
  },
  "x_hub_signature": "sha256=abc123..."
}
```
**Action**: Deploys `backend` service to `production`.

---

### **5.2 GitLab Webhook Payload**
```json
{
  "object_kind": "push",
  "ref": "refs/heads/feature/login",
  "before": "1234567890",
  "after": "abc1234567890",
  "project": { "url": "https://gitlab.com/user/repo.git" },
  "checkout_sha": "abc1234567890"
}
```
**Action**: Deploys `frontend` service to `staging`.

---

## **6. Error Handling & Debugging**
| **Error**                          | **Cause**                                  | **Solution**                                  |
|------------------------------------|--------------------------------------------|-----------------------------------------------|
| `InvalidSignatureError`            | Wrong HMAC key or malformed signature.     | Verify `fraise.config` for correct key.       |
| `BranchNotMapped`                  | Branch not in mappings.                    | Add branch rule in `fraise-mappings.json`.    |
| `DeploymentFailed`                 | Fraise/environment unreachable.            | Check Fraisier cluster health.                |
| `ProviderUnsupported`              | Unsupported Git provider.                  | Add support in `fraise/event_parser.go`.      |

**Debugging Commands**:
```bash
# Check webhook logs
fraise logs webhook

# Validate signature manually
fraise validate-signature --payload="..." --secret="..."
```

---

## **7. Related Patterns**
| **Pattern**                          | **Description**                                                                 |
|--------------------------------------|---------------------------------------------------------------------------------|
| **[Fraisier: Canary Deployments]**   | Gradual rollout of changes with traffic splitting.                              |
| **[Fraisier: Blue-Green Deployments]** | Instant cutoff to old version on failure.                                       |
| **[GitFlow Integration]**            | Enforce branch naming conventions (e.g., `release/*` → production).             |
| **[Multi-Provider Sync]**            | Mirror webhooks across GitHub/GitLab for redundancy.                            |
| **[Rollback Automation]**            | Auto-revert to last good commit on health checks.                               |

---

## **8. Security Considerations**
1. **Webhook Secrets**:
   - Store provider keys in **vaults** (not config files).
   - Rotate keys periodically.
2. **HTTPS Enforcement**:
   - Always use `HTTPS` for webhook endpoints.
3. **Rate Limiting**:
   - Add rate limits to prevent abuse (e.g., `100 reqs/min`).
4. **Audit Logging**:
   - Log all webhook events for compliance:
     ```json
     {
       "timestamp": "2023-10-01T12:00:00Z",
       "event": "push",
       "branch": "main",
       "action": "deploy",
       "status": "success"
     }
     ```

---
**End of Reference Guide**
*For updates, see [Fraisier Docs](https://docs.fraisier.dev).*