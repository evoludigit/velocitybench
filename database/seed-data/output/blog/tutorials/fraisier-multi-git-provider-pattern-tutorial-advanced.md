```markdown
# **Fraisier: The Mixed-Git-Provider Configuration Pattern for Scalable DevOps**

*Handling GitHub, GitLab, Gitea, and Bitbucket in a single deployment pipeline—without monolithic tooling.*

---

## **Introduction**

Imagine this: Your engineering organization has grown beyond a single Git provider. Your team works across **GitHub for public projects**, **GitLab for internal services**, and **self-hosted Gitea for proprietary tools**. Meanwhile, just last month, your company acquired a startup that relies on **Bitbucket** for their workflows. Now, your deployment tooling must handle all four platforms—**without forcing everyone to switch**.

This is the **multi-Git-provider challenge**, and it’s more common than you’d think. Monolithic CI/CD tools often assume a single provider, leading to fragmented workflows, redundant integrations, and technical debt. The **Fraisier pattern** solves this by introducing a **flexible, composable configuration** that lets teams choose their preferred Git provider per-service, with sensible defaults for consistency.

In this post, we’ll explore:
- Why teams end up with mixed Git providers
- How Fraisier enables seamless integration
- Practical code examples in Go (but easily adaptable to other languages)
- Common pitfalls and how to avoid them

---

## **The Problem: Fragmented Git Providers**

The reality is that organizations evolve over time:
- **Company migrations**: Moving from GitHub to GitLab (or vice versa) is common.
- **Team autonomy**: Different squads may prefer different tools—some love GitLab’s UI, others favor GitHub’s ecosystem.
- **Hybrid scenarios**:
  - Open-source projects on GitHub
  - Internal services on self-hosted Gitea
  - Acquisitions bringing in old Bitbucket repos
- **Deployment tooling limitations**: Most CI/CD systems (e.g., GitHub Actions, GitLab CI) are **provider-locked**, forcing teams into a single workflow.

### **The Consequences**
1. **Toolchain sprawl**: Each provider requires separate webhooks, secrets, and integrations.
2. **Configuration duplication**: Per-provider logic bloats your codebase.
3. **Developer friction**: Engineers must remember which provider to use for which service.
4. **Security risks**: Hardcoding provider-specific credentials in configs is error-prone.

### **The Fraisier Solution**
Instead of forcing a single Git provider, **Fraisier** introduces:
- A **default provider** for most services (e.g., GitHub).
- **Per-service overrides** for teams using alternative platforms.
- **Provider discovery** from webhooks or environment variables.
- **Configuration inheritance** to avoid redundancy.

This lets teams **work as they wish** while maintaining a unified deployment pipeline.

---

## **The Solution: Flexible Provider Configuration**

The Fraisier pattern works by treating Git providers as **configurable components**, not hardcoded dependencies. Here’s how it breaks down:

### **1. Default Provider (Fallback)**
Most services inherit a **provider config** defined at the **infrastructure level** (e.g., Kubernetes ConfigMap or environment variable). This avoids repetitive setup.

#### **Example Config (YAML)**
```yaml
# config/mixed-providers.yaml
default_provider:
  type: github
  api_url: https://api.github.com
  token_secret_name: "github-token"

# Per-service overrides (optional)
services:
  my-internal-service:
    provider:
      type: gitea
      api_url: https://gitea.example.com/api/v1
      token_secret_name: "gitea-token"
```

### **2. Per-Service Overrides (Flexibility)**
Some services need **custom providers**. Fraisier supports this via:
- **Explicit config files** (like above).
- **Dynamic overrides** (e.g., via environment variables).
- **Webhook-based discovery** (we’ll see this in code).

#### **Example in Go**
```go
package main

import (
	"fmt"
	"os"
)

// ProviderConfig defines how to interact with a Git provider.
type ProviderConfig struct {
	Type           string
	APIURL         string
	TokenSecretName string
}

// GetProviderConfig loads config from defaults or service-specific overrides.
func GetProviderConfig(serviceName string) (*ProviderConfig, error) {
	// 1. Check for explicit override (e.g., from config file or env vars)
	if explicit, exists := os.LookupEnv(serviceName + "-provider-type"); exists {
		return &ProviderConfig{
			Type:           explicit,
			APIURL:         os.Getenv(serviceName+"-api-url"),
			TokenSecretName: os.Getenv(serviceName+"-token-secret"),
		}, nil
	}

	// 2. Fallback to default provider
	return &ProviderConfig{
		Type:           os.Getenv("DEFAULT_PROVIDER_TYPE"),
		APIURL:         os.Getenv("DEFAULT_PROVIDER_API_URL"),
		TokenSecretName: os.Getenv("DEFAULT_PROVIDER_TOKEN_SECRET"),
	}, nil
}

func main() {
	service := "backend-service"
	config, err := GetProviderConfig(service)
	if err != nil {
		panic(err)
	}

	fmt.Printf("Using %s at %s (token secret: %s)\n",
		config.Type, config.APIURL, config.TokenSecretName)
}
```

### **3. Provider Discovery (Convenience)**
Instead of manually setting configs, **Fraisier can auto-detect** the provider from:
- **Webhook headers** (e.g., `X-GitHub-Event`).
- **Git refs** (e.g., `git remote url` for self-hosted repos).

#### **Example: Webhook-Based Discovery**
```go
import (
	"net/http"
)

type GitProviderDetector struct{}

func (d *GitProviderDetector) DetectFromRequest(r *http.Request) (string, error) {
	switch {
	case strings.Contains(r.Header.Get("X-GitHub-Event"), "push"):
		return "github", nil
	case strings.Contains(r.Header.Get("X-Gitlab-Token"), "gitlab"):
		return "gitlab", nil
	case strings.Contains(r.URL.Path, "/gitea/"):
		return "gitea", nil
	default:
		return os.Getenv("DEFAULT_PROVIDER_TYPE"), nil
	}
}

// Usage in a webhook handler:
func webhookHandler(w http.ResponseWriter, r *http.Request) {
	provider, _ := detector.DetectFromRequest(r)
	config := getProviderConfigFromProvider(provider)
	// Process webhook...
}
```

### **4. Configuration Inheritance (Reusability)**
To avoid redundancy, Fraisier lets **services inherit** common settings (e.g., token rotation policies).

#### **Example: Shared Config**
```yaml
# shared-provider-settings.yaml
auth:
  token_rotation_days: 30
  max_retries: 3

services:
  analytics:
    inherits: "default"
    provider: github
    plugin: "prometheus-exporter"

  internal-dashboard:
    provider: gitlab
    org: "internal"
```

---

## **Implementation Guide**

### **Step 1: Define the Default Provider**
Set a **global default** in your deployment environment:
```bash
# In your CI/CD (e.g., Dockerfile or Kubernetes ConfigMap)
export DEFAULT_PROVIDER_TYPE="github"
export DEFAULT_PROVIDER_API_URL="https://api.github.com"
export DEFAULT_PROVIDER_TOKEN_SECRET="git-provider-token"
```

### **Step 2: Override for Specific Services**
For services needing a different provider, either:
- **Explicitly override** in a config file:
  ```yaml
  backend-service:
    provider: gitea
    api_url: "https://gitea.example.com/api/v1"
  ```
- **Pass via environment variables**:
  ```bash
  export BACKEND_SERVICE_PROVIDER_TYPE="gitea"
  export BACKEND_SERVICE_API_URL="https://gitea.example.com/api/v1"
  ```

### **Step 3: Implement Provider-Specific Logic**
Write a **provider-agnostic client** that routes calls to the correct backend.

#### **Example: Generic Git Client**
```go
type GitClient struct {
	config *ProviderConfig
}

func (c *GitClient) GetBranches() ([]string, error) {
	switch c.config.Type {
	case "github":
		return c.githubGetBranches()
	case "gitlab":
		return c.gitlabGetBranches()
	case "gitea":
		return c.giteaGetBranches()
	default:
		return nil, fmt.Errorf("unsupported provider: %s", c.config.Type)
	}
}

func (c *GitClient) githubGetBranches() ([]string, error) {
	// Implement GitHub-specific API call
	// ...
}
```

### **Step 4: Dynamic Webhook Handling**
Use **Fraisier’s provider detection** to auto-route webhooks:
```go
func handleWebhook(r *http.Request) {
	provider, _ := detector.DetectFromRequest(r)
	client := NewGitClient(GetProviderConfig(provider))
	client.HandlePushEvent(r)
}
```

---

## **Common Mistakes to Avoid**

1. **Hardcoding Providers Everywhere**
   - ❌ Directly calling `github.NewClient()` in service code.
   - ✅ Always use `GetProviderConfig()` to abstract the choice.

2. **Ignoring Security in Overrides**
   - ❌ Storing tokens in plain config files.
   - ✅ Use Kubernetes secrets, HashiCorp Vault, or provider-specific token rotation.

3. **Over-Engineering Discovery**
   - ❌ Trying to auto-detect the provider *everywhere* (e.g., in logs).
   - ✅ Only use discovery for webhooks/CLI tools where ambiguity exists.

4. **Not Testing Mixed Scenarios**
   - ❌ Writing tests that assume one provider.
   - ✅ Mock multiple providers in CI (e.g., use `gitlab.MockClient`).

5. **Breaking Change Without Migration Path**
   - ❌ Removing a provider without deprecation warnings.
   - ✅ Support old providers for 6+ months post-migration.

---

## **Key Takeaways**

✅ **Flexibility**: Teams choose their Git provider per-service.
✅ **Sustainability**: Avoids locked-in tooling decisions.
✅ **Scalability**: Handles mergers, acquisitions, and migrations cleanly.
✅ **Security**: Centralized secrets management works across providers.

⚠️ **Tradeoffs**:
- Slightly more complex config management.
- Requires discipline to keep provider-specific logic DRY.

---

## **Conclusion**

The **Fraisier pattern** lets organizations **embrace mixed Git providers** without chaotic refactoring. By treating provider choice as a **configurable option**—not a hard constraint—you enable:
- **Team autonomy** (no forced GitHub/GitLab/bitbucket).
- **Smooth migrations** (switch providers per-service).
- **Future-proofing** (add new providers without rewriting logic).

### **Next Steps**
1. Start with a **default provider** and add overrides as needed.
2. Use **environment variables** for overrides (better than hardcoded YAML).
3. **Test provider-specific flows** in CI (e.g., mock GitHub/GitLab).

Would you add any other Git providers (e.g., Azure DevOps) or features (e.g., provider-specific webhook signatures)? Let me know in the comments!

---
**Further Reading**:
- [GitHub’s API docs](https://docs.github.com)
- [GitLab’s API best practices](https://docs.gitlab.com/ee/api/)
- [Kubernetes Secrets for credential management](https://kubernetes.io/docs/concepts/configuration/secret/)
```