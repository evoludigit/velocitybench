---
title: "Fraiser: The Mixed Git Provider Configuration Pattern for Scalable Deployments"
date: "2023-11-15"
tags: ["devops", "git", "backend", "patterns", "infrastructure"]
---

# Fraiser: The Mixed Git Provider Configuration Pattern for Scalable Deployments

## Introduction

As backend engineers, we're constantly juggling evolving toolchains and organizational changes that force us to work across multiple Git platforms. Maybe your company migrated from GitHub to GitLab, or perhaps you're in a large organization where different teams have different preferences (GitHub for public projects, internal GitLab for private ones, or even self-hosted Gitea). Alternatively, you might be dealing with recent acquisitions where merged teams now use entirely different Git providers.

The challenge becomes: *How do we build deployment tools that work seamlessly across all these providers without forcing a uniform choice?* Worse, how do we handle this without introducing complex branching logic that becomes a management nightmare?

In this post, I'll introduce the **Fraiser** pattern—a flexible configuration strategy for handling multiple Git providers in a single deployment system. Named after the French/Romance word for "fruitcake" (because it's a mix of different ingredients—just like your Git providers!), Fraiser lets you use the right Git platform for each service while keeping your deployment tooling sane.

---

## The Problem: Git Provider Spaghetti

Let's set the scene with a few realistic scenarios:

### Scenario 1: The Gradual Migration
Your company has been using GitHub for years, but after an expensive AWS security audit, you've decided to self-host your Git repositories using **GitLab CE**. You've migrated a few critical services, but most of your services remain on GitHub. How do you keep your deployment pipeline running?

### Scenario 2: The Polyglot Organization
Your company has multiple teams, each with its own culture:
- The public-facing apps team uses GitHub (because it's free and open).
- The security team uses an internal GitLab instance (because they need strict access controls).
- Your open-source contributions live on GitHub again.
- Your legacy monolith uses a self-hosted **Gitea** instance (because it was there before you joined).

Now, you need to deploy all these services from a single deployment tool. How do you structure this?

### Scenario 3: The Acquisition Nightmare
You just merged with another company that uses **Bitbucket Server**. Their team uses Bitbucket for everything, while your team uses GitHub. Now, you have two Git providers in your deployment tooling. Worse, you don’t want to rip and replace everything overnight. How do you handle this without breaking deployments?

### The Common Struggles:
1. **Hardcoding a single provider**: Your deployment tool only works with GitHub, so you have to manually override it for other providers. This is error-prone and hard to maintain.
2. **Complex branching logic**: You end up with `if (provider == GitHub) { ... } else if (provider == GitLab) { ... }`, which becomes unmanageable as your list of providers grows.
3. **Configuration duplication**: You copy-paste provider configurations everywhere, leading to inconsistencies and hard-to-track changes.
4. **Webhook hell**: Each provider has different webhook formats, and you have to handle all of them individually.

The Fraiser pattern solves these issues by treating Git provider configuration as a **hierarchical, overrideable system** where defaults are applied globally, but individual services can opt out or override them.

---

## The Solution: Fraiser Pattern

Fraiser is a **configuration inheritance pattern** that lets you:
1. Define a **default Git provider** (e.g., GitHub) that most services use.
2. Allow **per-service overrides** for services that need a different provider.
3. **Auto-discover** the provider from webhooks (e.g., `X-GitHub-Delivery` headers) when possible.
4. **Inherit common settings** (e.g., branch naming, commit hooks) across providers.

This approach keeps your deployment tooling clean, scalable, and flexible.

---

## Implementation Guide

Let's walk through how to implement Fraiser in your deployment tool. We'll use **TypeScript** and **Node.js** as our example, but the pattern applies to any language or framework.

### 1. Define a Provider Configuration Schema

First, let's define a type-safe interface for Git provider configurations:

```typescript
import { z } from "zod"; // Using Zod for schema validation

const ProviderSchema = z.object({
  name: z.enum(["github", "gitlab", "gitea", "bitbucket"]),
  host: z.string().url(),
  apiPrefix: z.string(), // e.g., "/api/v3", "/api"
  webhookSecret: z.string().optional(),
  repoFormat: z.string(), // e.g., "{owner}/{repo}", "{namespace}/{project}"
  branchPattern: z.string().optional(), // e.g., "refs/heads/{branch}"
  commitHooks: z.record(z.string(), z.string()).optional(), // e.g., { "commit": "some-hook" }
});

type ProviderConfig = z.infer<typeof ProviderSchema>;
```

### 2. Create a Default Provider Configuration

Define a global default provider (e.g., GitHub) with sensible defaults:

```typescript
const DEFAULT_PROVIDER: ProviderConfig = {
  name: "github",
  host: "https://github.com",
  apiPrefix: "/api/v3",
  repoFormat: "{owner}/{repo}",
  branchPattern: "refs/heads/{branch}",
  commitHooks: {
    "pre-push": "run-tests",
    "post-merge": "build",
  },
};
```

### 3. Define a Fraiser Configuration Structure

A `FraiserConfig` will hold:
- The default provider.
- A map of **per-service overrides**.
- A **provider discovery function** to auto-detect the provider from webhooks.

```typescript
type FraiserConfig = {
  defaultProvider: ProviderConfig;
  providerOverrides: Record<string, ProviderConfig>; // Key: service identifier (e.g., "app/orders")
  providerDiscovery: (headers: Record<string, string>) => string | null; // Returns provider name or null
};
```

### 4. Implement Provider Discovery

Auto-detect the provider from webhook headers (e.g., `X-GitHub-Delivery` for GitHub, `X-GitLab-Token` for GitLab):

```typescript
function discoverProviderFromHeaders(
  headers: Record<string, string>
): string | null {
  if (headers["X-GitHub-Delivery"]) return "github";
  if (headers["X-GitLab-Token"]) return "gitlab";
  if (headers["X-Gitea-Event"]) return "gitea";
  if (headers["X-Bitbucket-Event"]) return "bitbucket";
  return null;
}
```

### 5. Create a Fraiser Service

This service will:
1. Resolve the provider for a given service (with fallback to default).
2. Validate the configuration.
3. Apply overrides.

```typescript
class Fraiser {
  constructor(private config: FraiserConfig) {}

  resolveProviderForService(serviceId: string, headers: Record<string, string> = {}): ProviderConfig {
    // Step 1: Try to auto-discover from headers
    const discoveredProvider = discoverProviderFromHeaders(headers);
    if (discoveredProvider) {
      const override = this.config.providerOverrides[serviceId];
      if (override?.name === discoveredProvider) {
        return override;
      }
    }

    // Step 2: Fall back to default if no override exists
    const override = this.config.providerOverrides[serviceId];
    if (override) return override;

    // Step 3: Fall back to global default
    return this.config.defaultProvider;
  }
}
```

### 6. Example Usage

Let’s say you have the following services:
- `app/orders` (default: GitHub).
- `app/security` (override: GitLab).
- `app/legacy` (override: Gitea).

```typescript
const fraiser = new Fraiser({
  defaultProvider: DEFAULT_PROVIDER,
  providerOverrides: {
    "app/security": {
      name: "gitlab",
      host: "https://gitlab.company.internal",
      apiPrefix: "/api/v4",
      repoFormat: "{namespace}/{project}",
    },
    "app/legacy": {
      name: "gitea",
      host: "https://gitea.internal",
      apiPrefix: "/api/v1",
      repoFormat: "{user}/{repo}",
    },
  },
  providerDiscovery: discoverProviderFromHeaders,
});

// Resolve provider for "app/orders" (uses default)
const ordersProvider = fraiser.resolveProviderForService("app/orders");
console.log(ordersProvider.name); // "github"

// Resolve provider for "app/security" (uses override)
const securityProvider = fraiser.resolveProviderForService("app/security");
console.log(securityProvider.name); // "gitlab"

// Resolve provider for a webhook (auto-detected)
const headers = { "X-GitHub-Delivery": "true" };
const detectedProvider = fraiser.resolveProviderForService("app/orders", headers);
console.log(detectedProvider.name); // "github" (no override for "app/orders" in this case)
```

### 7. Apply Fraiser in a Deployment Pipeline

Now, integrate Fraiser into your deployment pipeline (e.g., using a tool like **ArgoCD** or a custom deployment service):

```typescript
// Example: Deploying a service based on its provider
async function deployService(serviceId: string, commitSha: string) {
  const fraiser = new Fraiser(YOUR_FRAISER_CONFIG);
  const provider = fraiser.resolveProviderForService(serviceId);

  // Use the provider's API to fetch the repo details
  const repoDetails = await fetchRepoDetails(provider, serviceId);

  // Use the provider's CLI/API to run deployment steps
  await runDeploymentSteps(provider, repoDetails, commitSha);
}

async function fetchRepoDetails(provider: ProviderConfig, serviceId: string) {
  const repoName = serviceId.replace(/[^\w-]/g, "-"); // e.g., "app/orders" -> "app-orders"
  const parts = repoName.split("/");
  const [owner, repo] = parts.length === 2 ? parts : ["default", repoName];

  const formattedRepo = provider.repoFormat
    .replace("{owner}", owner)
    .replace("{repo}", repo);

  // Call provider's API to get repo details
  const response = await fetch(`${provider.host}/${provider.apiPrefix}/repos/${formattedRepo}`);
  if (!response.ok) throw new Error("Failed to fetch repo details");
  return await response.json();
}
```

---

## Common Mistakes to Avoid

1. **Overusing Overrides**: If you end up with too many per-service overrides, you might be missing a better way to group configurations (e.g., by team or environment).
   - *Fix*: Audit your overrides and see if they can be generalized.

2. **Ignoring Webhook Headers**: Forgetting to pass headers to `resolveProviderForService` can lead to incorrect provider resolution.
   - *Fix*: Always pass headers (or default to an empty object) when resolving providers.

3. **Hardcoding Provider Logic**: Avoid inline `if` statements for provider checks. Use Fraiser consistently.
   - *Fix*: Refactor all provider logic to use `fraiser.resolveProviderForService`.

4. **Not Validating Configurations**: Skipping schema validation can lead to runtime errors.
   - *Fix*: Always validate provider configurations (e.g., using Zod or another schema library).

5. **Forgetting to Update Defaults**: Default providers can drift over time.
   - *Fix*: Document your default provider and update it when policies change.

6. **Assuming All Providers Support the Same Features**: Not all Git providers have identical APIs (e.g., webhook payload structures differ).
   - *Fix*: Write provider-specific adapters (e.g., `GitHubWebhookParser`, `GitLabWebhookParser`).

---

## Key Takeaways

- **Fraiser solves the "Git provider spaghetti" problem** by providing a flexible, overrideable configuration system.
- **Default + override strategy** keeps most services simple while allowing exceptions.
- **Provider discovery** (via webhook headers) reduces manual configuration.
- **Type safety** (via schemas like Zod) prevents runtime errors.
- **Hierarchical inheritance** avoids duplication and makes configurations easier to manage.
- **Adapters for provider differences** keep your codebase clean and maintainable.

---

## Conclusion

Fraiser is a pragmatic pattern for handling multiple Git providers in a single deployment tool. It doesn’t force you to choose one provider over another—it lets you work with the tools you have while keeping your system clean and scalable.

**When to use Fraiser:**
- Your organization uses multiple Git providers.
- You’re migrating between providers and need a smooth transition.
- You’re dealing with acquisitions or mergers that merge different Git platforms.
- You want to avoid hardcoding provider logic everywhere.

**When to avoid Fraiser:**
- You’re using only one Git provider (simpler to hardcode).
- Your providers are identical in features and APIs (no need for flexibility).

By adopting Fraiser, you’ll future-proof your deployment tooling and avoid the technical debt of managing "provider spaghetti." Start small—add Fraiser to one part of your system, then expand it as needed. Over time, you’ll find it becomes the backbone of your multi-provider workflow.

Now go forth and deploy fruitcakes (aka services) with confidence! 🍰