# **Debugging Fraisier: Mixed Git Provider Configuration Strategy – A Troubleshooting Guide**
*For Backend Engineers Managing Multi-Provider Git Workflows*

---

## **1. Introduction**
Fraisier allows centralized management of deployments across **multiple Git providers (GitHub, GitLab, Bitbucket, etc.)** using a single orchestration layer. While this pattern reduces vendor lock-in, mismatched configurations, API inconsistencies, and improper error handling can lead to **failed deployments, cross-provider inconsistencies, or workflow fragmentation**.

This guide focuses on **quick resolution** of common issues when integrating multiple Git providers in Fraisier.

---

## **2. Symptom Checklist**
Before diving into fixes, verify which symptoms match your environment:

| **Symptom** | **Possible Cause** |
|-------------|--------------------|
| Deployments fail inconsistently between providers | API rate limits, credential mismatches, or provider-specific timeout settings |
| Webhook triggers differ per provider | Incorrect webhook payload validation or missing `X-GitHub-Delivery`/`X-GitLab-Token` headers |
| `fraisier deploy` errors like `403 Forbidden` or `429 Too Many Requests` | Expired tokens, missing permissions, or API rate limits |
| Different access patterns (e.g., GitHub uses `repos`, GitLab uses `projects`) | Misconfigured provider abstractions in service classes |
| Teams report "deployments work fine locally but fail in CI" | Environment-specific config differences (e.g., secrets, proxy settings) |
| `fraisier pull-request` shows `Not Found` for GitLab MRs but works for GitHub PRs | Different branch/merge request naming conventions or provider API quirks |
| Logs show `UnsupportedOperation: Provider X does not support this action` | Fraisier’s provider adapter is missing a supported operation |

**Next Steps**:
- Check if symptoms are **provider-specific** (e.g., GitHub vs. GitLab).
- Verify if the issue occurs **locally vs. in CI/CD pipelines**.

---

## **3. Common Issues & Fixes**
### **3.1 Issue 1: Webhook Payload Mismatch**
**Symptoms**:
- Webhooks trigger deployments, but payloads differ between GitHub and GitLab.
- Debug logs show `Invalid payload format`.

**Root Cause**:
- GitHub and GitLab use different payload schemas (e.g., `push` events vs. `merge_request_events`).
- Missing header validation (`X-GitHub-Event` vs. `X-GitLab-Token`).

**Fix**:
#### **Code Snippet: Unified Webhook Handler (Go/Python)**
```python
# Python (Fraisier Webhook Service)
def handle_webhook(payload: dict, headers: dict):
    event = headers.get('X-Github-Event') or headers.get('X-Gitlab-Event')
    provider = "github" if "X-Github-Event" in headers else "gitlab"

    if provider == "github" and event == "push":
        ref = payload["ref"].split("/")[-1]  # GitHub uses 'refs/heads/main'
    elif provider == "gitlab" and event == "merge_request_event":
        ref = payload["object_attributes"]["source_branch"]  # GitLab MRs differ
    else:
        logger.error(f"Unsupported {provider}/{event} event")
        return

    # Proceed with deployment logic
    deploy_branch(ref, provider)
```

**Debugging Tips**:
- Log raw payloads (`fraisier logs --tail`).
- Use `curl` to test webhooks:
  ```bash
  curl -X POST -H "X-GitHub-Event: push" -d '{"ref": "refs/heads/main"}' http://localhost:8080/webhook
  ```

---

### **3.2 Issue 2: Credential/Token Expiry**
**Symptoms**:
- `401 Unauthorized` for GitHub, `403 Forbidden` for GitLab.
- Token rotations break deployments.

**Root Cause**:
- Hardcoded tokens or missing automatic refresh.
- Provider-specific token scopes (`repo` for GitHub, `api` for GitLab).

**Fix**:
#### **Code Snippet: Token Management (Go)**
```go
// fraisier/provider/gitlab/auth.go
func getGitLabToken(provider *GitLabProvider) (string, error) {
    if provider.Token == "" { // Fallback to secrets manager
        token, err := secrets.Get("gitlab-deploy-token")
        if err != nil {
            return "", fmt.Errorf("failed to fetch GitLab token: %w", err)
        }
        provider.Token = token
    }
    return provider.Token, nil
}

func refreshGitLabToken(provider *GitLabProvider) error {
    // Use GitLab’s refresh token flow (if configured)
    newToken, err := provider.client.RefreshToken(provider.RefreshToken)
    if err != nil {
        return err
    }
    provider.Token = newToken
    return secrets.Save("gitlab-deploy-token", newToken) // Re-save
}
```

**Debugging Tips**:
- Check token expiry in provider docs:
  - GitHub: [Token scopes](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
  - GitLab: [API docs](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html)
- Use `strace -e trace=openat` to debug secrets fetches in Linux.

---

### **3.3 Issue 3: Provider-Specific API Quirks**
**Symptoms**:
- `fraisier deploy` works for GitHub but fails on GitLab with `repository not found`.
- CI jobs fail with `missing required attribute`.

**Root Cause**:
- Fraisier’s provider adapter assumes uniform APIs (e.g., GitHub uses `repos/{owner}/{repo}`, GitLab uses `projects/{id}`).
- Missing fallback logic for optional fields (e.g., `description` in GitHub vs. `path_with_namespace` in GitLab).

**Fix**:
#### **Code Snippet: Adapter Layer (TypeScript)**
```typescript
// fraisier/adapter/provider.ts
export class GitProviderAdapter {
  constructor(private provider: GitHub | GitLab) {}

  async getRepositoryRef(repoId: string): Promise<string> {
    if (this.provider.type === 'github') {
      return await this.provider.repos.get({ repo: repoId }).then(r => r.data.ssh_url);
    } else { // GitLab
      const project = await this.provider.projects.show(repoId);
      return project.ssh_url_to_repo;
    }
  }
}
```

**Debugging Tips**:
- Use provider SDKs to inspect differences:
  ```bash
  # Test GitHub API
  curl -H "Authorization: token YOUR_GITHUB_TOKEN" \
    https://api.github.com/repos/owner/repo

  # Test GitLab API
  curl -H "Private-Token: YOUR_GITLAB_TOKEN" \
    https://gitlab.com/api/v4/projects/123
  ```

---

### **3.4 Issue 4: Rate Limiting & Retry Logic**
**Symptoms**:
- `429 Too Many Requests` during CI deployments.
- Retries fail silently.

**Root Cause**:
- No exponential backoff or rate-limit handling.
- GitHub/GitLab rate limits differ (e.g., 5k/hour for GitHub vs. 400/min for GitLab).

**Fix**:
#### **Code Snippet: Retry with Backoff (Python)**
```python
# fraisier/retry.py
import time
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def callProviderAPI(provider: GitProvider, endpoint: str) -> Response:
    try:
        return provider.client.get(endpoint)
    except RateLimitError as e:
        if "reset" in e.headers:
            time.sleep(int(e.headers["reset"]) - time.time())
        raise
```

**Debugging Tips**:
- Check rate limits in headers:
  ```bash
  # GitHub example
  X-RateLimit-Limit: 5000
  X-RateLimit-Remaining: 4998

  # GitLab example
  X-RateLimit-Limit: 400
  X-RateLimit-Remaining: 399
  ```
- Use `jq` to parse API responses:
  ```bash
  curl ... | jq '.message, .rate_limit_remaining'
  ```

---

### **3.5 Issue 5: Environment-Specific Configs**
**Symptoms**:
- Deployments work locally but fail in CI.
- Secrets or logging levels differ between environments.

**Root Cause**:
- Hardcoded configs (e.g., `debug: true` in dev vs. `false` in prod).
- Missing CI environment variables.

**Fix**:
#### **Code Snippet: Environment-Aware Config (Bash)**
```bash
#!/bin/bash
# fraisier/scripts/config-loader.sh

# Load from environment or defaults
PROVIDER=${PROVIDER:-"github"}
DEBUG=${DEBUG:-"false"}

if [ "$PROVIDER" = "gitlab" ]; then
  export GITLAB_TOKEN="$GITLAB_TOKEN_CI"
  export GITLAB_URL="${GITLAB_URL:-https://gitlab.com/api/v4}"
fi

if [ "$DEBUG" = "true" ]; then
  export LOG_LEVEL="debug"
  fraisier logs --tail
fi
```

**Debugging Tips**:
- Run CI jobs with debug logging:
  ```yaml
  # .github/workflows/deploy.yml
  steps:
    - run: DEBUG=true fraisier deploy --verbose
  ```
- Use `env` to inspect variables:
  ```bash
  env | grep FRAISIER_
  ```

---

## **4. Debugging Tools & Techniques**
| **Tool/Technique** | **Use Case** |
|---------------------|--------------|
| **Provider SDKs** (`go-github`, `gitlab`, `bithound`) | Validate API calls |
| **`curl` + `jq`** | Inspect raw API responses |
| **Fraisier Logs** (`fraisier logs --tail`) | Trace provider-specific flows |
| **Postman Collectives** | Test webhook payloads |
| **`strace`/`ltrace`** | Debug secrets/HTTP calls (Linux) |
| **Docker Health Checks** | Verify provider adapters |
| **Provider API Docs** (GitHub/GitLab) | Check rate limits & endpoints |

**Example Debug Flow**:
1. Reproduce the error locally.
2. Compare logs between working (GitHub) and failing (GitLab) cases:
   ```bash
   fraisier deploy --provider github --debug > github.log
   fraisier deploy --provider gitlab --debug > gitlab.log
   ```
3. Use `diff github.log gitlab.log` to spot differences.

---

## **5. Prevention Strategies**
### **5.1 Design for Multi-Provider Consistency**
- **Use a schema validator** (e.g., JSON Schema) for provider configs.
- **Abstract provider-specific logic** behind interfaces:
  ```go
  type GitProvider interface {
      GetRepository(url string) (*Repository, error)
      Deploy(repo *Repository, config DeployConfig) error
  }
  ```
- **Test with all providers in CI**:
  ```yaml
  # .github/workflows/test-providers.yml
  jobs:
    test:
      strategy:
        matrix:
          provider: [github, gitlab]
      steps:
        - run: go test -tags=${{ matrix.provider }}
  ```

### **5.2 Automate Token Management**
- Use **short-lived tokens** (rotated via Fraisier’s secrets manager).
- Implement **auto-refresh** for GitLab Personal Access Tokens (PATs):
  ```python
  # fraisier/secrets/token_refresher.py
  async def refresh_all_tokens():
      for provider in ["github", "gitlab"]:
          await refresh_provider_token(provider)
  ```

### **5.3 Monitor Cross-Provider Drift**
- **Alert on API deprecations** (e.g., GitHub’s `repos/{owner}/{repo}` → `/repos/{id}`).
- **Audit provider APIs weekly** using:
  ```bash
  # Check GitHub API changes
  curl -s https://api.github.com/meta | jq '.feature_state.urls[]'
  ```

### **5.4 Standardize Workflows**
- **Enforce a single `DeployConfig` schema** across providers.
- **Use provider-agnostic event names** (e.g., `onPush` instead of `onPushGitHub`).
- **Document provider quirks** in a `PROVIDER_QUirks.md` wiki page.

---

## **6. Example Debugging Workflow**
**Scenario**: `fraisier deploy` fails on GitLab but works on GitHub.

1. **Check Symptoms**:
   - `404 Not Found` for GitLab `projects/{id}`.
   - Logs show `repository not found`.

2. **Isolate the Issue**:
   - Compare `fraisier deploy --provider=github` vs. `--provider=gitlab`.

3. **Debug**:
   - Use `curl` to test the GitLab API:
     ```bash
     curl -H "Private-Token: YOUR_TOKEN" \
       https://gitlab.com/api/v4/projects/12345
     ```
   - Find the correct endpoint (e.g., `projects/{id}` instead of `repos/{id}`).

4. **Fix**:
   - Update the GitLab adapter to use `projects.show()`:
     ```go
     func (g *GitLabProvider) GetRepository(id string) (*Repository, error) {
         project, _, err := g.Client.Projects.Get(id, &gitlab.GetProjectsOptions{})
         if err != nil { return nil, err }
         return &Repository{Id: id, SshUrl: project.SshUrlToRepo}, nil
     }
     ```

5. **Prevent**:
   - Add a unit test:
     ```go
     func TestGitLabRepositoryResolution(t *testing.T) {
         provider := &GitLabProvider{Client: &gitlab.Client{APIURL: "https://gitlab.com"}}
         repo, err := provider.GetRepository("12345")
         assert.NoError(t, err)
         assert.NotEmpty(t, repo.SshUrl)
     }
     ```

---

## **7. When to Escalate**
| **Issue** | **Escalation Path** |
|-----------|----------------------|
| **Provider API changes** (e.g., GitHub deprecates an endpoint) | Fraisier team + provider support |
| **Rate limit exploits** (e.g., CI hitting 429s) | Adjust quotas or use GitLab’s `async` API |
| **Undocumented provider behavior** | Open an issue in Fraisier’s GitHub repo |

---

## **8. Key Takeaways**
1. **Treat each provider as unique**—even if they share a Git backend.
2. **Log everything**—raw payloads, headers, and provider-specific responses.
3. **Automate token handling** to avoid manual rotations.
4. **Test cross-provider workflows in CI**.
5. **Document quirks** to avoid "works on my machine" issues.

By following this guide, you can **quickly diagnose and resolve mixed-provider issues** while keeping deployments consistent across GitHub, GitLab, and beyond.

---
**Need further help?** Check:
- [Fraisier’s Provider Adapter Docs](https://docs.fraisier.io/providers)
- [GitHub API Limits](https://docs.github.com/en/rest/overview/resources-in-the-rest-api#rate-limiting)
- [GitLab Rate Limits](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html#rate-limits)