```markdown
# Fraisier Pattern: Abstracting Git Providers for Multi-Platform Support

*How to Build Deployment Tooling That Works Across GitHub, GitLab, Gitea, and Beyond*

---

## Introduction

As backend developers, we’ve all faced it: that moment when our perfectly-tuned deployment pipeline works great with GitHub webhooks, only to realize we forgot to account for GitLab’s `X-GitLab-Token` header *or* that our bitbucket-server instance uses a completely different event format. The reality is that while Git is standardized at the protocol level, each provider (and even sub-platforms like GitLab CE/EE) implements webhooks and events differently.

Over time, I’ve seen teams build increasingly complex abstractions around Git providers—each time adding another layer of indirection to handle "just this one edge case." Instead of treating this as a hack, we can design systems that *expect* this heterogeneity and handle it cleanly from the start. That’s where the **Fraisier Pattern** comes in.

The Fraisier Pattern (named after the French word for "framework"—a playful nod to how this framework-like design lets you manage multiple Git providers) provides a provider-agnostic interface for working with Git webhooks. By defining a consistent contract for provider interactions and normalizing events downstream, Fraisier allows your tooling to seamlessly support GitHub, GitLab, Gitea, Bitbucket, and even custom instances without locking you into one platform.

In this blog post, we’ll design a Fraisier-compatible system from scratch, covering:
- How to abstract provider differences behind a unified interface
- Event normalization techniques that work across platforms
- How to implement signature verification with minimal duplication
- Common pitfalls and how to avoid them

---

## The Problem: Why Git Providers Make Your Life Hard

Each Git provider implements webhooks slightly differently, leading to these common pain points:

1. **Signature Verification Headers Differ**
   GitHub uses `X-Hub-Signature-256`, GitLab uses `X-GitLab-Token` plus HMAC-SHA256, and Bitbucket uses JWT tokens. Each provider’s documentation is a rabbit hole of small, inconsistent details.

2. **Event Payload Structures Vary**
   A "push event" from GitHub looks like this:
   ```json
   {
     "ref": "refs/heads/main",
     "repository": { "name": "my-repo" }
   }
   ```
   While GitLab’s is:
   ```json
   {
     "ref": "refs/heads/main",
     "repository": { "name": "my-repo", "namespace": "my-group" }
   }
   ```

3. **Provider-Specific Metadata**
   Some platforms include extra information like `X-GitHub-Delivery-ID` or `Gitea-Event-ID`—useful for debugging but disruptive when your code assumes a single format.

4. **Configuration Overhead**
   Each provider has its own dashboard UI, API endpoints, and retry logic (e.g., GitHub’s webhook retries are different from GitLab’s). Managing multiple providers becomes a maintenance nightmare.

5. **No Easy Switching**
   Your CICD pipeline might be built for GitHub today, but what if your client wants to move to GitLab? Adding support later is expensive in time and effort.

---

## The Solution: Fraisier Pattern for Multi-Provider Git Webhooks

The Fraisier Pattern solves these problems by:
- Defining a **provider-independent interface** that all supported Git platforms implement.
- **Normalizing event payloads** to a common schema downstream.
- **Centralizing provider-specific logic** (e.g., signature verification) behind a clean abstraction.

This approach lets you add new providers with minimal changes to your core pipeline code, while keeping the public interface stable.

---

## Core Components of Fraisier

### 1. GitProvider Interface (Abstract Base Class)

Every concrete provider implementation must fulfill this contract:

```typescript
interface GitProvider {
  verifyWebhookSignature(
    payload: string,
    signatureHeader: string,
    secret: string
  ): boolean;

  parseEvent(
    payload: string,
    providerEvent: any
  ): NormalizedEvent;

  getWebhookEndpoint(): string;
}
```

### 2. Concrete Provider Implementations

#### Example: GitHub Implementation (`githubProvider.ts`)

```typescript
import crypto from 'crypto';
import { GitProvider, NormalizedEvent } from './types';
import { GitHubEvent } from './githubTypes';

export class GitHubProvider implements GitProvider {
  verifyWebhookSignature(
    payload: string,
    signatureHeader: string,
    secret: string
  ): boolean {
    // GitHub uses sha256= prefix + hex-encoded HMAC
    const expectedKey = 'sha256=' + crypto
      .createHmac('sha256', secret)
      .update(payload)
      .digest('hex');

    return signatureHeader === expectedKey;
  }

  parseEvent(
    payload: string,
    githubEvent: GitHubEvent
  ): NormalizedEvent {
    return {
      eventType: githubEvent['x-github-event'] as string,
      ref: githubEvent.ref,
      repository: {
        id: githubEvent.repository.id,
        name: githubEvent.repository.name,
        owner: githubEvent.repository.owner.login,
        // Normalize GitHub's path format
        path: githubEvent.repository.full_name,
      },
      commit: githubEvent.after || undefined,
      actor: githubEvent.actor?.login,
      createdAt: new Date(githubEvent.created_at),
    };
  }

  getWebhookEndpoint(): string {
    return '/github-webhook';
  }
}
```

#### Example: GitLab Implementation (`gitlabProvider.ts`)

```typescript
import crypto from 'crypto';
import { GitProvider, NormalizedEvent } from './types';
import { GitLabEvent } from './gitlabTypes';

export class GitLabProvider implements GitProvider {
  verifyWebhookSignature(
    payload: string,
    signatureHeader: string,
    secret: string
  ): boolean {
    // GitLab's X-GitLab-Token + HMAC-SHA256
    const expectedSig = crypto
      .createHmac('sha256', secret)
      .update(payload)
      .digest('hex');

    return signatureHeader === expectedSig;
  }

  parseEvent(
    payload: string,
    gitlabEvent: GitLabEvent
  ): NormalizedEvent {
    return {
      eventType: gitlabEvent.event_type as string,
      ref: gitlabEvent.ref,
      repository: {
        id: gitlabEvent.project.id,
        name: gitlabEvent.project.name,
        owner: gitlabEvent.project.namespace,
        path: gitlabEvent.project.full_path,
      },
      commit: gitlabEvent['after'] || undefined,
      actor: gitlabEvent.user?.username,
      createdAt: new Date(gitlabEvent.created_at),
    };
  }

  getWebhookEndpoint(): string {
    return '/gitlab-webhook';
  }
}
```

---

### 3. Provider Registry and Dispatcher

Use a **factory/registry pattern** to dynamically load providers:

```typescript
class ProviderRegistry {
  private registry = new Map<string, GitProvider>();

  register(providerName: string, provider: GitProvider): void {
    this.registry.set(providerName, provider);
  }

  getProvider(providerName: string): GitProvider | null {
    return this.registry.get(providerName);
  }
}

// Usage:
const registry = new ProviderRegistry();
registry.register('github', new GitHubProvider());
registry.register('gitlab', new GitLabProvider());
```

---

### 4. Webhook Event Normalization

Normalized events (e.g., `NormalizedEvent` in the types file) should include only the fields you care about, with consistent naming:

```typescript
type NormalizedEvent = {
  eventType: string;    // 'push', 'pull_request' etc.
  ref: string;           // 'refs/heads/main'
  repository: {
    id: string;
    name: string;
    owner: string;
    path: string;
  };
  commit?: string;       // Optional for some events
  actor?: string;        // Optional for some events
  createdAt: Date;
};
```

---

## Implementation Guide: Building a Fraisier-Compatible System

### Step 1: Define Your Normalized Schema

Start by documenting the minimal event fields your pipeline needs. For example:

```typescript
type NormalizedEvent = {
  eventType: 'push' | 'pull_request' | 'issue_comment' | 'deploy_key';
  // ...
  action?: 'create' | 'open' | 'closed'; // Optional for some events
};
```

### Step 2: Implement Provider Interfaces

For each provider you support, create a class that:
- Implements `GitProvider`
- Parses payloads into your normalized format
- Handles provider-specific signature verification

### Step 3: Create a Webhook Handler

A single entry point to dispatch events:

```typescript
import express from 'express';
const app = express();

app.post('/webhook', async (req, res) => {
  const provider = registry.getProvider(req.headers['x-git-provider'] as string);
  if (!provider) {
    return res.status(400).send('Unsupported provider');
  }

  // Verify signature
  const hmac = req.headers['x-hub-signature-256'] ||
               req.headers['x-gitlab-token'];
  const isValid = provider.verifyWebhookSignature(
    req.body,
    hmac || '',
    process.env[`${provider.getWebhookEndpoint()}_SECRET`]
  );

  if (!isValid) {
    return res.status(401).send('Invalid signature');
  }

  // Parse and normalize event
  const normalizedEvent = provider.parseEvent(
    req.body,
    req.body  // Pass raw payload to provider
  );

  // Route to business logic
  await handleEvent(normalizedEvent);

  res.status(200).send();
});
```

### Step 4: Configure Providers via a Configuration System

Allow per-fraise (per-repository) provider configuration:

```typescript
type RepositoryConfig = {
  gitProvider: string;  // 'github', 'gitlab', etc.
  webhookSecret: string;
};

const configs: Map<string, RepositoryConfig> = new Map();
configs.set('my-repo', {
  gitProvider: 'github',
  webhookSecret: 'my-github-secret',
});
```

---

## Common Mistakes to Avoid

1. **Over-normalizing Events**
   Don’t throw out provider-specific fields unless you have a good reason. For example, GitHub’s `X-Hub-Delivery-ID` can be useful for debugging retries. Instead of stripping it entirely, consider making it optional:
   ```typescript
   type NormalizedEvent = {
     ...,
     deliveryId?: string; // Populated by provider if available
   };
   ```

2. **Assuming All Providers Support the Same Events**
   Not all platforms send identical events. GitHub has `push` and `repository_dispatch` events, while GitLab has `push` and `job_customer_event`. Plan for missing fields gracefully:
   ```typescript
   parseEvent(payload, providerEvent) {
     const normalizedEvent: NormalizedEvent = {
       eventType: providerEvent.event_type || 'unknown',
       // ...
     };
     return normalizedEvent;
   }
   ```

3. **Ignoring Rate Limits and Retries**
   GitHub allows 5000 webhooks per hour, while GitLab has stricter limits. Implement provider-specific retry logic or let providers handle it internally.

4. **Hardcoding Provider-Specific Logic**
   If your code starts checking `if (provider === 'github')` to handle special cases, you’re violating the abstraction principle. Refactor by extracting these cases into providers.

5. **Neglecting Provider Documentation**
   Git providers constantly change their webhook formats. Set up alerts when you detect breaking changes, and test new versions early.

---

## Key Takeaways

- **Fraisier Pattern** reduces coupling between your deployment tooling and Git providers by abstracting differences behind a clean interface.
- **Normalization** ensures your business logic works consistently across platforms, even if events differ.
- **Provider-specific logic** is encapsulated in implementations, making it easy to add or switch providers.
- **Test thoroughly**—provider implementations can significantly affect behavior (e.g., GitHub’s `X-GitHub-Delivery-ID` for retry tracking).
- **Start small**: Add support for one provider first, then incrementally add others, validating each step.

---

## Conclusion

The Fraisier Pattern isn’t about avoiding the complexity of multi-provider Git integrations—it’s about managing that complexity *explicitly* so it doesn’t derail your deployment pipelines. By abstracting provider differences, you create a system that’s:

- **Extensible**: Add new providers without rewriting core logic.
- **Maintainable**: Changes to one provider don’t break others.
- **Flexible**: Your deployment tooling can work seamlessly across GitHub, GitLab, Gitea, or any future Git platform.

If you’re building deployment tooling, CI/CD systems, or any Git-integrated workflow, Fraisier’s pattern is a proven way to keep your codebase clean and your architecture future-proof. Start with one provider, validate your normalization logic, and gradually add support for more platforms—your future self (and your clients) will thank you.

---

### Next Steps

1. Try implementing a simplified Fraisier system for just GitHub and GitLab.
2. Benchmark performance: Is the abstraction layer adding noticeable overhead?
3. Document your normalized schema and provider-specific fields in a public repository.

Happy coding!
```