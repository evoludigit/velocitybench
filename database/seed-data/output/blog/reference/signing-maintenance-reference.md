# **[Pattern] Signing Maintenance Reference Guide**

---

## **Overview**
The **Signing Maintenance** pattern ensures secure and traceable updates to cryptographic signing keys used in systems that rely on digital signatures (e.g., APIs, certificates, firmware, or blockchain transactions). It streamlines the key rotation, revocation, and validation processes while minimizing operational overhead and security risks.

This pattern is critical for systems where:
- Keys expire or are compromised.
- Compliance requires periodic key refreshes.
- Backward compatibility must be maintained during transitions.

It involves:
- **Key lifecycle management** (creation, storage, rotation).
- **Revocation handling** (blacklisting invalid keys).
- **Validation logic** (client/server checks to enforce current keys).
- **Audit trails** (logging changes for compliance).

---

## **Key Concepts**

| **Concept**               | **Description**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------|
| **Signing Key**           | A cryptographic key (public/private) used to generate or verify digital signatures.                |
| **Signing Policy**        | Rules defining key validity periods, rotation frequency, and revocation criteria.                   |
| **Key Store**             | Secure repository (e.g., HSM, vault) for private keys.                                             |
| **Revocation List**       | A list of keys deemed invalid (e.g., expired or compromised).                                      |
| **Validation Endpoint**   | API or service endpoint that clients query to verify a key’s status.                                |
| **Grace Period**          | Time window during which old and new keys are valid simultaneously for seamless transitions.     |
| **Audit Log**             | Immutable record of key changes, used for compliance and debugging.                               |

---

## **Implementation Schema**

### **1. Core Entities**
| **Entity**          | **Properties**                                                                                     | **Notes**                                                                                     |
|---------------------|---------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| `SigningKey`        | `id`, `publicKey`, `privateKey`, `algorithm`, `createdAt`, `expiresAt`, `status` (`active`/`revoked`) | Stored in Key Store.                                                                       |
| `RevocationList`    | `id`, `keys` (array of `SigningKey.id`), `createdAt`, `validUntil`                               | Signed and distributed to clients.                                                          |
| `SigningPolicy`     | `policyId`, `rotationInterval` (e.g., `90d`), `gracePeriod` (e.g., `14d`), `revocationThreshold` | Defines automation rules (e.g., auto-revoke after `expiresAt`).                           |
| `ValidationRequest` | `keyId`, `requestTimestamp`                                                                     | Sent to Validation Endpoint to check key status.                                             |
| `AuditEntry`        | `entryId`, `action` (`rotate`, `revoke`, `register`), `keyId`, `timestamp`, `initiator` (`system`/`user`) | Immutable log for compliance.                                                                |

---

### **2. System Workflow**
1. **Key Rotation**
   - Triggered by `expiresAt` or manual request (e.g., `POST /signing-policies/{policyId}/rotate`).
   - Generate new `SigningKey`, update `RevocationList` (with old key as `revoked`), and set `gracePeriod`.
   - Clients validate using the latest `RevocationList`.

2. **Revocation**
   - Manual revocation via `POST /signing-keys/{keyId}/revoke` or automatic (e.g., after `expiresAt`).
   - Add key to `RevocationList` immediately; remove after `gracePeriod`.

3. **Validation**
   - Clients query the Validation Endpoint:
     ```http
     GET /validation?keyId={keyId}&timestamp={requestTimestamp}
     ```
   - Response:
     ```json
     {
       "status": "active" | "revoked" | "expired",
       "gracePeriodEnds": "2023-12-01T00:00:00Z"
     }
     ```

4. **Audit**
   - All changes log to `AuditEntry` (e.g., `{"action": "rotate", "keyId": "123", "initiator": "system"}`).

---

## **Query Examples**

### **1. Rotate a Key**
```http
POST /signing-policies/{policyId}/rotate
Headers:
  Authorization: Bearer {admin-token}
Body:
  {
    "newKey": "{base64-encoded-public-key}",
    "expiresAt": "2024-06-30T00:00:00Z"
  }
```
**Response (200 OK):**
```json
{
  "newKeyId": "456",
  "oldKeyId": "123",
  "gracePeriodEnds": "2023-12-01T00:00:00Z"
}
```

### **2. Revoke a Key Manually**
```http
POST /signing-keys/123/revoke
Headers:
  Authorization: Bearer {admin-token}
```
**Response (200 OK):**
```json
{
  "revokedAt": "2023-11-01T12:00:00Z",
  "gracePeriodEnds": "2023-11-15T00:00:00Z"
}
```

### **3. Validate a Key Status**
```http
GET /validation?keyId=123&timestamp=2023-11-05T09:00:00Z
```
**Response (200 OK):**
```json
{
  "status": "active",
  "gracePeriodEnds": "2023-12-01T00:00:00Z"
}
```

### **4. Fetch Revocation List**
```http
GET /revocation-list
```
**Response (200 OK):**
```json
{
  "revokedKeys": ["123"],
  "validUntil": "2023-12-01T00:00:00Z",
  "signature": "{base64-signature}"
}
```

### **5. List Audit Entries**
```http
GET /audit-entries?keyId=123&limit=10
```
**Response (200 OK):**
```json
[
  {
    "entryId": "789",
    "action": "revoke",
    "timestamp": "2023-11-01T12:00:00Z",
    "initiator": "user:admin@example.com"
  }
]
```

---

## **Related Patterns**

| **Pattern**               | **Relationship**                                                                                     | **When to Use**                                                                               |
|---------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| [Key Rotation](https://example.com/key-rotation)       | Core to Signing Maintenance; defines *how* keys are rotated.                                          | When keys expire or are compromised.                                                          |
| [Circuit Breaker](https://example.com/circuit-breaker) | Complements validation endpoints to handle failures gracefully.                                      | To prevent cascading failures during revocation checks.                                      |
| [Event Sourcing](https://example.com/event-sourcing)   | Enables immutable audit logs for compliance.                                                       | For regulatory requirements (e.g., financial, healthcare).                                  |
| [Secure Token Issuance](https://example.com/token-issuance) | Often uses signing keys for JWT/OAuth.                                                               | For short-lived tokens with key-backed signing.                                              |
| [Canary Deployment](https://example.com/canary-deployment) | Syncs with `gracePeriod` for phased key transitions.                                                | To test new keys before full rollout.                                                        |

---

## **Best Practices**
1. **Automate Rotation**
   - Use cron jobs or event-driven triggers (e.g., AWS EventBridge) to rotate keys before `expiresAt`.
   - Example:
     ```yaml
     # Cron rule (rotate every 90 days)
     0 0 * * */3 ? *
     ```

2. **Secure Key Storage**
   - Store private keys in **Hardware Security Modules (HSMs)** or cloud KMS (e.g., AWS KMS, HashiCorp Vault).
   - Never log private keys in audit trails.

3. **Graceful Degradation**
   - During `gracePeriod`, handle both old and new keys (e.g., prefer new keys but allow fallbacks).

4. **Revocation List Signing**
   - Sign the `RevocationList` with a **long-lived key** (e.g., CA root) to prevent tampering.

5. **Client-Side Caching**
   - Cache `RevocationList` locally with a TTL (e.g., 1 hour) to reduce validation endpoint calls.

6. **Monitoring**
   - Alert on:
     - Keys nearing `expiresAt`.
     - Failed validation requests (potential revocation issues).
     - Anomalous audit entries (e.g., bulk revocations).

7. **Compliance**
   - Retain audit logs for the required period (e.g., 7+ years for GDPR).
   - Include `initiator` metadata (user/system) for accountability.

---
**Last Updated:** [YYYY-MM-DD]
**Version:** 1.2