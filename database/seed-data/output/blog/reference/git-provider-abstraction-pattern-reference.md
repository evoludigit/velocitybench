# **[Pattern] Fraisier: Git Provider Abstraction & Multi-Provider Support – Reference Guide**

---

## **1. Overview**
Fraisier is a **Git provider abstraction layer** that standardizes interactions with multiple Git platforms (e.g., GitHub, GitLab, Gitea, Bitbucket) under a single API. It resolves variability in:

- **Webhook signatures** (HMAC, SHA-256, custom headers)
- **Event payload schemas** (e.g., `push_event` vs. `push` via GitHub API)
- **HTTP methods & endpoints** (e.g., `/hooks`, `/events`)
- **Configuration options** (e.g., branch filters, secret management)

By implementing the **Fraisier pattern**, developers avoid duplicating provider-specific logic while maintaining flexibility to override defaults via **per-fraise provider configurations**.

---

## **2. Schema Reference**
Below are core schemas and interfaces defining Fraisier’s architecture.

### **2.1 Core Interfaces**
| **Interface**               | **Purpose**                                                                 | **Key Methods**                                                                 |
|-----------------------------|-----------------------------------------------------------------------------|--------------------------------------------------------------------------------|
| `GitProvider` (Abstract)    | Defines mandatory provider operations.                                      | `verifySignature()`, `parseEvent()`, `sendWebhook()`, `getConfig()`           |
| `WebhookSignatureVerifier`  | Handles signature validation per provider.                                 | `verify(string payload, string signature)`                                    |
| `EventNormalizer`           | Converts raw provider events to a unified format.                          | `normalize(providerEvent)`                                                     |

### **2.2 Provider Config Schema**
```json
{
  "$schema": "http://json-schema.org/schema#",
  "title": "Fraisier Provider Config",
  "type": "object",
  "properties": {
    "provider": { "type": "string", "enum": ["github", "gitlab", "gitea", "bitbucket"] },
    "webhook_url": { "type": "string", "format": "uri" },
    "secrets": {
      "type": "object",
      "properties": {
        "secret": { "type": "string" },  // Provider-specific secret
        "header": { "type": "string" }   // e.g., `X-Hub-Signature-256`
      },
      "required": ["secret"]
    },
    "events": {
      "type": "array",
      "items": { "type": "string" }  // e.g., ["push", "pull_request"]
    },
    "branch_filters": {
      "type": "array",
      "items": { "type": "string" }  // e.g., ["main", "dev/*"]
    }
  },
  "required": ["provider", "webhook_url"]
}
```

### **2.3 Unified Event Payload Schema**
```json
{
  "$schema": "http://json-schema.org/schema#",
  "title": "Fraisier Event",
  "type": "object",
  "properties": {
    "provider": { "type": "string" },
    "event": { "type": "string" },  // e.g., "push", "issue_comment"
    "repo": {
      "type": "object",
      "properties": {
        "name": { "type": "string" },
        "owner": { "type": "string" }
      }
    },
    "payload": { "type": "object" }  // Provider-specific data (normalized)
  },
  "required": ["provider", "event", "repo"]
}
```

---

## **3. Components & Implementation**

### **3.1 GitProvider Interface (Abstract Base Class)**
```typescript
interface GitProvider {
  verifySignature(payload: string, signature: string): boolean;
  parseEvent(rawEvent: any): FraisierEvent;
  sendWebhook(event: FraisierEvent): Promise<void>;
  getConfig(): ProviderConfig;
}
```

**Purpose**:
- Enforces consistency across providers.
- Delegates provider-specific logic to concrete implementations.

---

### **3.2 Provider Implementations**
Each provider extends `GitProvider` with its unique behavior.

#### **Example: GitHub Implementation**
```typescript
class GitHubProvider implements GitProvider {
  private readonly config: ProviderConfig;

  constructor(config: ProviderConfig) { this.config = config; }

  async verifySignature(payload: string, signature: string): Promise<boolean> {
    const hmac = crypto.createHmac("sha1", this.config.secrets.secret);
    return hmac.update(payload).digest("hex") === signature;
  }

  parseEvent(rawEvent: any): FraisierEvent {
    // Convert GitHub's `push_event` to Fraisier format.
    return {
      provider: "github",
      event: "push",
      repo: { name: rawEvent.repository.name, owner: rawEvent.repository.owner.login },
      payload: rawEvent
    };
  }
}
```

**Key Differences Handled**:
| **Provider** | **Signature Algorithm** | **Event Payload Key** | **Webhook Endpoint**       |
|--------------|--------------------------|-----------------------|----------------------------|
| GitHub       | HMAC-SHA1                | `x-hub-signature`     | `/repos/{owner}/{repo}/hooks` |
| GitLab       | HMAC-SHA256              | `X-Gitlab-Token`      | `/projects/{id}/web_hooks`  |
| Gitea        | SHA-256 (raw header)     | `X-Gitea-Signature`   | `/user/settings/hooks`      |

---

### **3.3 Provider Registry (Factory Pattern)**
Maps provider names to concrete implementations:
```typescript
const providerRegistry: Record<string, new (config: ProviderConfig) => GitProvider> = {
  github: GitHubProvider,
  gitlab: GitLabProvider,
  // ...
};

function createProvider(providerName: string, config: ProviderConfig): GitProvider {
  const ProviderClass = providerRegistry[providerName];
  if (!ProviderClass) throw new Error(`Unsupported provider: ${providerName}`);
  return new ProviderClass(config);
}
```

---

### **3.4 Webhook Event Normalization (Adapter Pattern)**
Converts raw provider events to a **unified schema** (see [Schema Reference](#23-unified-event-payload-schema)).

**Example Adapter for `push` Event**:
```typescript
function normalizePushEvent(providerEvent: any): FraisierEvent {
  return {
    provider: providerEvent.provider,
    event: "push",
    repo: { name: providerEvent.repository.name, owner: providerEvent.repository.owner },
    payload: {
      ref: providerEvent.ref,
      commits: providerEvent.commits,
      // ...other normalized fields
    }
  };
}
```

---

### **3.5 Signature Verification (Strategy Pattern)**
Dynamically selects the correct verification algorithm per provider:
```typescript
const signatureStrategies: Record<string, (payload: string, signature: string) => boolean> = {
  github: (payload, signature) => verifyGitHubSignature(payload, signature),
  gitlab: (payload, signature) => verifyGitLabSignature(payload, signature),
  // ...
};

function verifySignature(provider: string, payload: string, signature: string): boolean {
  const strategy = signatureStrategies[provider];
  if (!strategy) throw new Error(`Unsupported signature strategy for ${provider}`);
  return strategy(payload, signature);
}
```

---

## **4. Usage Examples**

### **4.1 Creating a Provider**
```typescript
const config: ProviderConfig = {
  provider: "github",
  webhook_url: "https://your-service/webhook",
  secrets: { secret: "your_github_webhook_secret", header: "X-Hub-Signature" },
  events: ["push", "pull_request"]
};

const provider = createProvider(config.provider, config);
```

### **4.2 Handling Incoming Webhooks**
```typescript
async function handleWebhook(req: Request): Promise<void> {
  const signature = req.headers["x-hub-signature-256"];
  const rawEvent = await req.text();

  if (!provider.verifySignature(rawEvent, signature)) {
    throw new Error("Invalid signature");
  }

  const event = provider.parseEvent(JSON.parse(rawEvent));
  await processEvent(event);  // Generic logic (no provider-specific code)
}
```

### **4.3 Sending Outgoing Webhooks**
```typescript
async function triggerWebhook(event: FraisierEvent): Promise<void> {
  await provider.sendWebhook(event);
  // Works identically for GitHub, GitLab, etc.
}
```

---

## **5. Query Examples**
### **5.1 List Supported Providers**
```bash
curl -X GET "http://localhost:3000/api/providers" \
  -H "Authorization: Bearer YOUR_TOKEN"
```
**Response**:
```json
{
  "providers": ["github", "gitlab", "gitea", "bitbucket"]
}
```

### **5.2 Override Provider Config for a Specific Repo**
```bash
curl -X POST "http://localhost:3000/api/fraises/my-fraise/providers" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "gitea",
    "webhook_url": "https://my-gitea-service/webhook",
    "secrets": { "secret": "gitea-secret" },
    "branch_filters": ["main"]
  }'
```

---

## **6. Related Patterns**
| **Pattern**                     | **Purpose**                                                                 | **When to Use**                                                                 |
|----------------------------------|-----------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Adapter**                      | Convert provider-specific formats to a common interface.                      | Normalizing webhook payloads.                                                    |
| **Strategy**                     | Dynamically select signature verification algorithms.                        | Handling HMAC-SHA1 (GitHub) vs. SHA-256 (GitLab).                               |
| **Factory**                      | Create provider instances without tight coupling.                            | Dynamically loading `GitHubProvider` or `GitLabProvider` based on config.      |
| **Repository Pattern**           | Decouple data access from business logic.                                   | Storing provider configs in a database.                                        |
| **Event Sourcing**               | Persist event history for replayability.                                    | Auditing webhook deliveries.                                                    |

---

## **7. Error Handling & Edge Cases**
| **Scenario**                     | **Solution**                                                                 |
|-----------------------------------|-----------------------------------------------------------------------------|
| **Unsupported Provider**          | Return `400 Bad Request` with `UnsupportedProviderError`.                   |
| **Invalid Signature**             | Reject request with `401 Unauthorized`.                                     |
| **Missing Required Fields**       | Validate config schema (e.g., `webhook_url` is mandatory).                  |
| **Rate Limiting**                 | Implement retry logic for provider API calls (e.g., GitHub’s rate limits).   |
| **Schema Mismatch**               | Use a validator (e.g., `ajv`) to enforce event payload structure.           |

---
## **8. Migration Guide**
1. **Replace Direct Provider Calls**:
   Before:
   ```typescript
   await githubClient.createWebhook(config);
   ```
   After:
   ```typescript
   const provider = createProvider("github", config);
   await provider.sendWebhook(event);
   ```

2. **Normalize Events**:
   Use `provider.parseEvent()` to convert raw payloads to the unified schema.

3. **Override Provider-Specific Logic**:
   Extend `GitProvider` for custom behavior (e.g., GitLab-specific branch filters).

---
## **9. Best Practices**
- **Default Configs**: Provide sensible defaults (e.g., `events: ["push"]`) to reduce boilerplate.
- **Testing**: Mock provider implementations for unit tests.
- **Logging**: Log provider-specific errors (e.g., `GitHubAPIError`).
- **Performance**: Cache provider instances if reusing them frequently.

---
## **10. Full Example: Fraisier Integration**
```typescript
// Initialize Fraisier
const fraisier = new Fraisier({
  webhook_url: "https://app.example.com/webhooks",
  providers: [
    { provider: "github", config: { /* ... */ } },
    { provider: "gitlab", config: { /* ... */ } }
  ]
});

// Handle incoming webhook
app.post("/webhook", async (req, res) => {
  const event = await fraisier.handleWebhook(req);
  await processEvent(event);  // Generic handler
});
```

---
**Documentation Version**: `1.0.0`
**Last Updated**: `YYYY-MM-DD`