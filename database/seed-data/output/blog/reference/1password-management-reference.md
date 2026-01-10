**[Pattern] 1Password Management Integration Patterns – Reference Guide**

---

### **Overview**
This reference guide outlines **1Password Management Integration Patterns**, focusing on how to securely synchronize, manage, and automate credential workflows between 1Password and external systems. Integration patterns cover:
- **Direct API interactions** (REST, CLI, Webhooks)
- **Vault synchronization** (Pull/Push)
- **Credential provisioning** (Autofill, CLI, SDKs)
- **Audit & compliance** (Activity logs, event sync)

This guide is structured for architects, DevOps engineers, and security teams implementing 1Password in CI/CD pipelines, SSO workflows, or enterprise applications. Key principles include **least-privilege access**, **zero-trust validation**, and **minimal data exposure**.

---

---

### **1. Schema Reference**
The following tables define core entities and relationships in 1Password integration patterns.

#### **1.1. Core Entities**
| **Entity**               | **Description**                                                                                     | **Fields**                                                                                     |
|--------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| **Vault**                | Logical container for secrets (e.g., `dev`, `prod`).                                               | `id`, `name`, `shared?`, `default?`, `quota_remaining` (MB)                                  |
| **Item**                 | Secure entry (password, certificate, API key).                                                     | `id`, `title`, `type` (e.g., `login`, `secret`), `favorite?`                                |
| **Collection**           | Organizes Items (e.g., by team/project).                                                          | `id`, `name`, `shared?`, `items` (array of `Item` references)                                |
| **User**                 | Authentication entity (user/group).                                                              | `id`, `name`, `account_type` (e.g., `personal`, `organization`), `status` (e.g., `active`) |
| **Application**          | Third-party app integrating with 1Password (e.g., CI/CD tool, browser extension).                  | `id`, `name`, `permissions` (e.g., `read_items`, `write_items`), `webhook_url` (optional)     |
| **Event Log**            | Audit trail of Vault/Item changes.                                                                  | `id`, `timestamp`, `user_id`, `action` (e.g., `create`, `update`), `item_id`                |

---

#### **1.2. API Endpoints**
| **Category**            | **Endpoint**                          | **Method** | **Purpose**                                                                                     | **Authentication**                     |
|-------------------------|---------------------------------------|------------|-------------------------------------------------------------------------------------------------|-----------------------------------------|
| **Vaults**              | `/v2/vaults`                         | GET        | List all vaults.                                                                                 | `X-1Password-Token` (Admin API Key)    |
| **Items**               | `/v2/items/{vault_id}/{item_id}`     | GET/PUT    | Fetch/update an Item (e.g., password).                                                        | `X-1Password-Token` (User/Org Key)     |
| **Collections**         | `/v2/collections`                    | POST       | Create a collection to organize Items.                                                         | `X-1Password-Token` (Org Key)          |
| **Applications**        | `/v2/applications`                    | POST       | Register a third-party app for integration.                                                    | `X-1Password-Token` (Admin Key)        |
| **Webhooks**            | `/v2/webhooks`                       | POST       | Configure event-triggered callbacks (e.g., on `item.create`).                                  | `X-1Password-Token` (Admin Key)        |
| **Audit Logs**          | `/v2/events`                         | GET        | Retrieve activity logs for compliance.                                                          | `X-1Password-Token` (Audit Key)        |

**Notes:**
- **Admin API Keys** require elevated permissions (e.g., `admin` role).
- **User/Org Keys** scope access to specific vaults/items.
- Endpoints support pagination (`?page={number}`) and filtering (`?items.per_page=20`).

---

---

### **2. Implementation Patterns**

#### **2.1. Vault Synchronization (Pull/Push)**
**Use Case:** Sync credentials between 1Password and a CI/CD tool (e.g., GitHub Actions, Jenkins).

##### **Pattern: Pull-Based Sync**
1. **Trigger:** CI job starts (e.g., `workflow_dispatch` in GitHub).
2. **Action:**
   - Fetch Secrets via 1Password CLI:
     ```bash
     op item get "vault_123/SECRET_API_KEY" --format json
     ```
   - Inject into environment variables:
     ```bash
     export API_KEY=$(op item get ... | jq -r '.secret')
     ```
3. **Output:** Secrets securely injected into the pipeline.

**Schema Example:**
```json
{
  "vault": "vault_123",
  "collection": "ci-cd-secrets",
  "items": [
    {
      "id": "secret_456",
      "title": "API_KEY",
      "type": "secret",
      "value": "s3cr3t"  // Masked in logs
    }
  ]
}
```

**Best Practices:**
- Use **short-lived tokens** for CI integrations.
- Rotate secrets on every pipeline run (via 1Password **Rotation Rules**).
- Validate secrets post-injection (e.g., `curl -H "Authorization: Bearer $API_KEY" ...`).

---

##### **Pattern: Push-Based Sync**
**Use Case:** Automatically update 1Password when a secret changes (e.g., password reset).

1. **Trigger:** Secret update in external system (e.g., database).
2. **Action:**
   - Update Item via REST API:
     ```bash
     curl -X PUT "https://api.1password.com/v2/items/vault_123/secret_456" \
       -H "Authorization: Bearer ${API_KEY}" \
       -H "Content-Type: application/json" \
       -d '{"secret": "new_password"}'
     ```
3. **Output:** 1Password Item updated + webhook triggered.

**Schema Example (Request Body):**
```json
{
  "secret": "new_password",
  "last_modified_by": {
    "user_id": "user_789",
    "name": "automation-bot"
  }
}
```

**Best Practices:**
- Use **idempotency keys** to avoid duplicate updates.
- Log failed updates to a dead-letter queue for manual review.

---

#### **2.2. Credential Provisioning**
**Use Case:** Automate credential autofill for users/applications.

##### **Pattern: Browser Extension (Autofill)**
1. **Trigger:** User visits a login page (e.g., `example.com/login`).
2. **Action:**
   - Extension queries 1Password for matching credentials:
     ```javascript
     const credentials = await window.op.getItem("vault_123/Login_example_com");
     document.getElementById("username").value = credentials.username;
     document.getElementById("password").value = credentials.password;
     ```
3. **Output:** Fields auto-populated.

**Schema Example (Item Response):**
```json
{
  "type": "login",
  "username": "user@example.com",
  "password": "*****",  // Masked
  "urls": ["https://example.com"]
}
```

**Best Practices:**
- Limit autofill to **trusted origins**.
- Use **MFA prompts** for sensitive vaults.

---

##### **Pattern: CLI-Based Provisioning**
**Use Case:** Dynamically inject secrets into containers (e.g., Docker, Kubernetes).

1. **Trigger:** Container startup.
2. **Action:**
   - Fetch secret via 1Password CLI:
     ```bash
     #!/bin/bash
     DB_PASS=$(op item get "vault_123/DB_PASSWORD" --format plaintext)
     export DB_PASS
     ```
   - Inject into environment:
     ```yaml
     # docker-compose.yml
     services:
       db:
         environment:
           - DB_PASSWORD=${DB_PASS}
     ```
3. **Output:** Container receives secrets.

**Best Practices:**
- Use **short-lived CLI tokens** (expire after 1 use).
- Restrict CLI access to **specific vaults**.

---

#### **2.3. Audit & Compliance**
**Use Case:** Monitor API usage for security incidents.

##### **Pattern: Event Webhooks**
1. **Trigger:** Any change to an Item/Vault (e.g., `item.create`).
2. **Action:**
   - Configure webhook in 1Password Console:
     ```bash
     curl -X POST "https://api.1password.com/v2/webhooks" \
       -H "Authorization: Bearer ${ADMIN_KEY}" \
       -d '{
             "url": "https://compliance.example.com/webhook",
             "events": ["item.create", "item.update"],
             "secret": "s3cr3t_webhook"
           }'
     ```
3. **Output:** Event forwarded to SIEM (e.g., Splunk).

**Schema Example (Webhook Payload):**
```json
{
  "event": {
    "id": "event_101",
    "type": "item.create",
    "timestamp": "2023-10-01T12:00:00Z",
    "item_id": "secret_456"
  }
}
```

**Best Practices:**
- Validate webhook signatures (`secret` field).
- Rate-limit webhook calls to prevent abuse.

---

---

### **3. Query Examples**
#### **3.1. List All Items in a Vault**
```bash
curl -X GET "https://api.1password.com/v2/items?vault_id=vault_123" \
  -H "Authorization: Bearer ${USER_KEY}" \
  -H "Accept: application/json"
```
**Response:**
```json
{
  "items": [
    {
      "id": "secret_456",
      "title": "API_KEY",
      "type": "secret"
    }
  ]
}
```

#### **3.2. Get Item by UUID**
```bash
op item get "vault_123/secret_456" --format json
```
**Response:**
```json
{
  "id": "secret_456",
  "title": "API_KEY",
  "type": "secret",
  "secret": "*****",  // Masked in CLI output
  "created_at": "2023-01-01T00:00:00Z"
}
```

#### **3.3. Update an Item**
```bash
curl -X PUT "https://api.1password.com/v2/items/vault_123/secret_456" \
  -H "Authorization: Bearer ${USER_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
        "secret": "new_password",
        "last_modified_by": {
          "user_id": "user_789",
          "name": "bot-account"
        }
      }'
```

#### **3.4. Trigger a Webhook**
```bash
curl -X POST "https://api.1password.com/v2/webhooks/test" \
  -H "Authorization: Bearer ${ADMIN_KEY}" \
  -d '{
        "event": {
          "type": "item.create",
          "item_id": "secret_456"
        },
        "signature": "s3cr3t_webhook_signature"
      }'
```
*(Simulates an event for testing webhook validation.)*

---

---

### **4. Common Pitfalls & Mitigations**
| **Pitfall**                          | **Mitigation**                                                                                     |
|---------------------------------------|---------------------------------------------------------------------------------------------------|
| **Hardcoded API keys**                | Use **1Password Connect** or **CLI tokens** with short TTLs.                                      |
| **Over-permissive roles**            | Assign **least-privilege roles** (e.g., `vault_access` instead of `admin`).                     |
| **No secret rotation**                | Enable **Rotation Rules** for Items (e.g., `passwords` rotate every 90 days).                     |
| **Webhook spoofing**                  | Validate webhook signatures with `secret` field.                                                   |
| **Missing error handling**            | Implement **dead-letter queues** for failed syncs.                                                  |
| **Exposing masked secrets in logs**   | Use `op item get --format plaintext` carefully; prefer CLI masking.                              |

---

---
### **5. Related Patterns**
| **Pattern**                          | **Description**                                                                                     | **Reference**                          |
|---------------------------------------|-----------------------------------------------------------------------------------------------------|----------------------------------------|
| **[1Password Connect]**               | Secure proxy for credential autofill in custom apps.                                               | [1Password Connect Docs](https://developer.1password.com/docs/connect) |
| **[Secure Environment Variables]**    | Best practices for managing secrets in CI/CD (e.g., GitHub Secrets, AWS SSM).                     | [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets) |
| **[Zero-Trust SAML]**                 | Integrate 1Password with SAML for SSO and credential validation.                                    | [1Password SAML Guide](https://support.1password.com/authenticators/saml-integrations) |
| **[Dynamic Credential Rotation]**     | Automate secret rotation using 1Password + external tools (e.g., HashiCorp Vault).                | [1Password Rotation Rules](https://support.1password.com/rotation) |
| **[Incident Response Playbooks]**     | Use 1Password audit logs to trace credential leaks.                                                 | [1Password Incident Response](https://support.1password.com/incident-response) |

---

---
### **6. Further Reading**
- [1Password API Docs](https://developer.1password.com/docs/api)
- [1Password CLI Guide](https://developer.1password.com/docs/cli)
- [Security Best Practices](https://support.1password.com/security)
- [Enterprise Integration Examples](https://developer.1password.com/docs/integrations)