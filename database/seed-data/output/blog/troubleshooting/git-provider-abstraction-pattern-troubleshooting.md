# **Debugging Fraisier: Git Provider Abstraction & Multi-Provider Support – A Troubleshooting Guide**

This guide helps diagnose and resolve common issues when implementing **Fraisier**, a pattern for abstracting multiple Git providers (GitHub, GitLab, Gitea, Bitbucket) into a unified interface. The goal is to ensure seamless multi-provider support without vendor lock-in.

---

## **1. Symptom Checklist**
Before diving into debugging, verify which symptoms match your issues:

| **Symptom** | **Description** | **Likely Cause** |
|-------------|----------------|------------------|
| **Provider-specific logic** | Conditional checks (e.g., `if (provider === "GitHub")`) spread across code | Poor abstraction layer |
| **Webhook failures** | Different signature verification logic for each provider | Missing unified webhook handler |
| **Migration pain** | Cannot switch from GitHub to GitLab without refactoring | Tight coupling to one provider |
| **Error: "Unsupported provider"** | Runtime errors on unsupported Git providers | Missing provider implementations |
| **Rate limiting issues** | Different API rate limits per provider handled inconsistently | Incomplete provider-specific throttling |
| **Authentication failures** | OAuth/Git credentials not working across providers | Hardcoded provider-specific auth flows |
| **Webhook payload mismatch** | Incorrect parsing of different payload structures | No schema validation for provider differences |
| **Slow performance** | Provider-specific optimizations missing, causing delays | Inefficient provider-agnostic abstractions |

---

## **2. Common Issues & Fixes**

### **Issue 1: Scattered Provider-Specific Logic**
**Symptoms:**
- `if (provider === "GitHub") { ... }` checks everywhere.
- New providers require extensive refactoring.

**Root Cause:**
Lack of a **unified adapter/abstraction layer** forces direct conditional logic.

**Fix:**
Implement a **provider abstraction layer** using **Strategy Pattern** or **Adapter Pattern**.

#### **Example (GitHub & GitLab Abstraction)**
```typescript
// Base Provider Interface
interface GitProvider {
  fetchRepository(name: string): Promise<Repository>;
  createWebhook(payload: WebhookPayload): Promise<void>;
  verifyWebhookSignature(payload: string, signature: string): boolean;
}

// GitHub Adapter
class GitHubProvider implements GitProvider {
  async fetchRepository(name: string) {
    // GitHub-specific API call
    const res = await fetch(`https://api.github.com/repos/${name}`);
    return res.json();
  }

  verifyWebhookSignature(payload: string, signature: string): boolean {
    // GitHub's HMAC-SHA1 verification
    const hmac = crypto.createHmac("sha1", process.env.GITHUB_WEBHOOK_SECRET);
    return hmac.update(payload).digest("hex") === signature;
  }
}

// GitLab Adapter
class GitLabProvider implements GitProvider {
  async fetchRepository(name: string) {
    // GitLab-specific API call
    const res = await fetch(`https://gitlab.example.com/api/v4/projects/${name}`);
    return res.json();
  }

  verifyWebhookSignature(payload: string, signature: string): boolean {
    // GitLab's OAuth-style verification
    const token = process.env.GITLAB_WEBHOOK_TOKEN;
    const expectedSig = `sha256=${crypto.createHmac("sha256", token).update(payload).digest("hex")}`;
    return signature === expectedSig;
  }
}

// Usage (Fraisier)
function useProvider(providerName: string): GitProvider {
  switch (providerName) {
    case "GitHub": return new GitHubProvider();
    case "GitLab": return new GitLabProvider();
    default: throw new Error(`Unsupported provider: ${providerName}`);
  }
}

// Client code (no provider-specific logic)
const provider = useProvider("GitHub");
const repo = await provider.fetchRepository("myorg/myrepo");
```

### **Issue 2: Webhook Payload Parsing Failures**
**Symptoms:**
- `Cannot read property 'payload' of undefined` in webhook handlers.
- Different payload structures (GitHub vs. GitLab).

**Root Cause:**
No **payload schema validation** or **provider-specific parsing**.

**Fix:**
Use **Zod (TypeScript)** or **JSON Schema** to validate and transform payloads.

```javascript
const webhookPayloadSchema = {
  GitHub: z.object({
    payload: z.string(),
    action: z.string(),
    ref: z.string().optional(),
  }),
  GitLab: z.object({
    object_kind: z.string(),
    before: z.string(),
    after: z.string(),
  }),
};

function parseWebhook(provider: string, rawPayload: string) {
  const schema = webhookPayloadSchema[provider];
  return schema.parse(JSON.parse(rawPayload));
}

// Usage in Fraisier
const parsedPayload = parseWebhook("GitHub", req.body);
```

### **Issue 3: Authentication & Rate Limiting Mismatches**
**Symptoms:**
- OAuth flows fail for non-GitHub providers.
- API rate limits not handled per-provider.

**Root Cause:**
Hardcoded authentication/rate limit logic.

**Fix:**
Abstract auth and rate limits in provider adapters.

```typescript
// Base Provider with Auth & Rate Limiting
interface GitProvider {
  fetchRepository(name: string, token?: string): Promise<Repository>;
  setToken(token: string): void;
  getRateLimitInfo(): Promise<{ remaining: number; reset: number }>;
}

// GitHub Auth Example
class GitHubProvider implements GitProvider {
  private token: string;

  setToken(token: string) {
    this.token = token;
  }

  async fetchRepository(name: string) {
    const headers = { Authorization: `Bearer ${this.token}` };
    const res = await fetch(`https://api.github.com/repos/${name}`, { headers });
    return res.json();
  }

  async getRateLimitInfo() {
    const res = await fetch(`https://api.github.com/rate_limit`, {
      headers: { Authorization: `Bearer ${this.token}` },
    });
    return res.json();
  }
}
```

### **Issue 4: Missing Provider Implementations**
**Symptoms:**
- Error: `Unsupported provider: Gitea`.
- New providers require full code rewrites.

**Root Cause:**
No **extensibility mechanism** for new providers.

**Fix:**
Use **Dependency Injection (DI)** for providers.

```typescript
// Register providers dynamically (Fraisier)
const providers = {
  GitHub: GitHubProvider,
  GitLab: GitLabProvider,
  Gitea: GiteaProvider, // Add later
};

function getProvider(providerName: string) {
  const ProviderClass = providers[providerName];
  if (!ProviderClass) throw new Error(`Provider ${providerName} not registered`);
  return new ProviderClass();
}
```

---

## **3. Debugging Tools & Techniques**

| **Tool/Technique** | **Purpose** | **How to Use** |
|--------------------|------------|----------------|
| **Postman/Insomnia** | Test webhook payloads | Send mock webhooks to verify parsing. |
| **Swagger/OpenAPI** | Document provider APIs | Generate client SDKs for each provider. |
| **Logging Middleware** | Track provider-specific issues | Log errors with `provider: "GitHub"` metadata. |
| **Error Boundaries** | Isolate provider failures | Wrap provider calls in try-catch. |
| **Mocking (Vitest/MSW)** | Simulate provider APIs | Mock GitHub/GitLab responses in tests. |
| **Rate Limit Testers** | Check API throttling | Use `curl` or Postman to trigger limits. |
| **Schema Validation** | Catch payload mismatches | Use Zod/JSON Schema in webhook handlers. |
| **Feature Flags** | Toggle providers safely | Enable/disable providers without deployment. |

**Example Debugging Flow:**
1. **Error**: Webhook fails with `Invalid signature`.
   - Check if `verifyWebhookSignature()` is called correctly.
   - Verify `process.env[PROVIDER]_WEBHOOK_SECRET` exists.
2. **Error**: `403 Forbidden` on API calls.
   - Check if `setToken()` was called.
   - Validate rate limits via `getRateLimitInfo()`.
3. **Error**: `Unsupported provider`.
   - Check `providers` registry (dynamic DI).

---

## **4. Prevention Strategies**

### **1. Enforce Provider Abstraction Early**
- **Rule**: Never write provider-specific logic outside adapters.
- **Example**: If fetching a repo, always call `provider.fetchRepository()`.

### **2. Use a Schema Enforcement Layer**
- **Rule**: Validate all webhook payloads with Zod/JSON Schema.
- **Example**:
  ```javascript
  const payload = parseWebhook("GitHub", req.body); // Throws if invalid
  ```

### **3. Implement Dynamic Provider Registration**
- **Rule**: Use a registry pattern for new providers.
- **Example**:
  ```typescript
  const providers = {}; // Registered at runtime
  providers.GitHub = GitHubProvider; // Can add Gitea later
  ```

### **4. Rate Limit & Retry Logic Per Provider**
- **Rule**: Each provider adapter should handle its own throttling.
- **Example**:
  ```typescript
  async function fetchWithRetry(provider: GitProvider, name: string) {
    while (true) {
      try {
        return await provider.fetchRepository(name);
      } catch (err) {
        if (err.status === 403 && provider.isRateLimited()) {
          await provider.waitForRateLimitReset();
        } else throw err;
      }
    }
  }
  ```

### **5. Automated Testing for Each Provider**
- **Rule**: Write integration tests for every provider.
- **Example (Jest + MSW)**:
  ```javascript
  describe("GitHub Webhook", () => {
    it("should parse push event", async () => {
      mockGitHubWebhook({
        payload: '{"ref":"refs/heads/main","action":"push"}',
        signature: "valid-sig",
      });
      const parsed = parseWebhook("GitHub", req.body);
      expect(parsed.action).toBe("push");
    });
  });
  ```

### **6. Monitor & Alert on Provider-Specific Failures**
- **Rule**: Log provider names in errors for quick debugging.
- **Example**:
  ```typescript
  try {
    await provider.fetchRepository("myrepo");
  } catch (err) {
    console.error({ provider: provider.constructor.name, error: err });
    // Send to Sentry/LogRocket
  }
  ```

---

## **5. Quick Checklist for Fraisier Implementation**
| **Action** | **Done?** |
|------------|----------|
| ✅ All provider logic is behind `GitProvider` interface | |
| ✅ Webhook payloads validated with schema | |
| ✅ Dynamic provider registration in place | |
| ✅ Authentication & rate limits abstracted | |
| ✅ Error logs include provider metadata | |
| ✅ Tests cover all supported providers | |
| ✅ New providers can be added without refactoring | |

---

## **Final Notes**
- **Fraisier’s goal** is to **eliminate hard dependencies** on a single Git provider.
- **Key to success**: **Consistent abstractions** and **schema enforcement**.
- **Debugging tip**: Always start with **logs** and **provider-specific error codes** before diving into code.

By following this guide, you should be able to **diagnose, fix, and prevent** common issues in a multi-provider Git setup. 🚀