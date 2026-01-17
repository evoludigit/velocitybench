# **[Pattern] Fraisier: Mixed Git Provider Configuration Strategy – Reference Guide**

---

## **1. Overview**
Fraisier’s **Mixed Git Provider Configuration Strategy** allows organizations to manage services distributed across multiple Git platforms (GitHub, GitLab, Gitea, Bitbucket) while maintaining a centralized configuration approach. Instead of requiring separate tooling for each service or provider, teams can define a **default Git provider** for all services while overriding individual **fraises** (services) to use alternative providers based on team needs.

This pattern is ideal for **multi-team environments** with varying provider preferences, ensuring flexibility without sacrificing consistency. Fraisier abstracts provider-specific nuances (e.g., webhook formats, API endpoints) while enabling seamless integration across heterogeneous Git ecosystems.

---

## **2. Key Concepts**

| **Concept**               | **Description**                                                                                     | **Use Case Example**                          |
|---------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------|
| **Default Provider**      | Fallback Git provider applied to all fraises unless explicitly overridden.                          | Corporate GitLab as the primary provider.     |
| **Per-Fraise Override**   | Fine-grained control to configure an individual fraise with a different Git provider.              | DevOps team uses GitHub for CI/CD pipelines. |
| **Provider Discovery**    | Automatically detects the Git provider from webhook headers or service metadata.                   | Fraisier parses `X-GitHub-Delivery` headers.  |
| **Configuration Inheritance** | Fraises reuse common settings (e.g., authentication, branch policies) unless overridden.         | Shared OAuth token for all providers.         |

---

## **3. Schema Reference**

### **Core Structures**

#### **3.1. Default Provider Configuration**
```yaml
default_provider:
  type: string
  enum: ["github", "gitlab", "gitea", "bitbucket"]
  description: "Fallback Git provider for all fraises."
  example: "gitlab"

  # Optional provider-specific settings
  settings:
    type: object
    properties:
      api_url:
        type: string
        description: "Custom API root URL (e.g., self-hosted GitLab)."
        example: "https://gitlab.example.com/api/v4"
```

#### **3.2. Per-Fraise Provider Override**
```yaml
fraise:
  type: object
  required: ["name"]
  properties:
    name:
      type: string
      description: "Unique identifier for the fraise (e.g., 'frontend-ci')."

    # Override default provider if needed
    provider:
      type: string
      enum: ["github", "gitlab", "gitea", "bitbucket"]
      optional: true
      description: "Explicit provider for this fraise."
      example: "github"

    # Inherits default_provider.settings unless overridden
    provider_settings:
      type: object
      description: "Provider-specific overrides (e.g., webhook secrets)."
      example:
        webhook_secret: "abc123"
```

#### **3.3. Provider Discovery (Webhook Context)**
```yaml
webhook_headers:
  type: object
  required: ["provider"]
  properties:
    provider:
      type: string
      enum: ["github", "gitlab", "bitbucket"]
      description: "Auto-detected from `X-GitHub-Delivery` or similar headers."
      example: "github"
    payload_url:
      type: string
      description: "Webhook delivery URL for validation."
      example: "https://hooks.example.com/webhook"
```

---

## **4. Query Examples**

### **4.1. Default Provider Configuration**
**Request:**
```bash
GET /api/v1/config/default-provider
```
**Response:**
```json
{
  "provider": "gitlab",
  "settings": {
    "api_url": "https://gitlab.example.com/api/v4",
    "auth_token": "[REDACTED]"
  }
}
```

---

### **4.2. List Fraises with Provider Overrides**
**Request:**
```bash
GET /api/v1/fraises?fields=name,provider,provider_settings
```
**Response:**
```json
[
  {
    "name": "frontend-ci",
    "provider": "github",
    "provider_settings": {
      "webhook_secret": "gh_abc123"
    }
  },
  {
    "name": "backend-service",
    "provider": null  # Inherits default_provider (gitlab)
  }
]
```

---

### **4.3. Discover Provider from Webhook**
**Request (HTTP Headers):**
```
X-GitHub-Delivery: abc123...
```
**Response:**
```json
{
  "detected_provider": "github",
  "payload_url": "https://hooks.example.com/webhook"
}
```

---

### **4.4. Update a Fraise’s Provider**
**Request:**
```bash
PATCH /api/v1/fraises/frontend-ci
```
**Body:**
```json
{
  "provider": "gitea",
  "provider_settings": {
    "api_url": "https://gitea.example.com/api/v1"
  }
}
```

---

## **5. Configuration Inheritance Rules**
1. **Default Provider Applies First**:
   All fraises default to `default_provider` unless overridden.
2. **Per-Fraise Overrides**:
   Explicit `provider` in a fraise’s config supersedes the default.
3. **Webhook Context Takes Precedence**:
   If a webhook is received, Fraisier uses the detected provider (e.g., `X-GitHub-Delivery`) over static config.

---
## **6. Related Patterns**
| **Pattern**                          | **Description**                                                                 |
|--------------------------------------|---------------------------------------------------------------------------------|
| **[Single Git Provider]**            | Simplifies deployment by using one provider (e.g., GitHub) across the board.   |
| **[Provider-Agnostic Webhook Handling]** | Standardizes webhook payloads regardless of Git provider.                       |
| **[Fractional Git Operations]**       | Breaks Git tasks (e.g., PR reviews, merges) into modular, provider-independent steps. |

---

## **7. Limitations & Considerations**
- **Webhook Validation**: Ensure webhook secrets are provider-specific (e.g., GitHub vs. GitLab).
- **API Rate Limits**: Some providers (e.g., GitLab) have stricter rate limits than others.
- **Legacy Systems**: Older services may require manual provider mapping.

---
**Last Updated**: `[Insert Date]`
**Version**: `1.2`