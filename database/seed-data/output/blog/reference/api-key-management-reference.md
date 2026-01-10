---
# **[Pattern] API Key Management Reference Guide**

---

## **1. Overview**
API Key Management is a security pattern that ensures safe generation, storage, rotation, and revocation of API keys. This guide provides implementation details and best practices to mitigate risks like unauthorized access, key leakage, and account takeover. The pattern emphasizes encryption, access control, and automated key lifecycle management while adhering to principles such as **least privilege**, **defense in depth**, and **auditability**.

Key objectives:
- Secure key generation and storage (e.g., using key derivation functions or hardware security modules).
- Automate rotation to minimize exposure (e.g., short-lived tokens, token expiration).
- Implement granular permissions to limit API key usage.
- Monitor and log key access to detect anomalies or breaches.

This guide targets developers, security architects, and DevOps teams responsible for designing or maintaining API security mechanisms.

---

## **2. Schema Reference**

| **Component**               | **Description**                                                                                     | **Example**                                                                                     |
|-----------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Key Generation**          | Algorithm and parameters for generating cryptographically secure keys.                              | HMAC-SHA256 (salted) or RSA-2048                                                              |
| **Key Storage**             | Secure storage mechanisms (e.g., encrypted secrets manager, HSM).                                    | AWS Secrets Manager, HashiCorp Vault, or Azure Key Vault                                      |
| **Key Rotation Policy**     | Rules for how often keys are rotated (e.g., daily, weekly) or based on usage events.               | Rotate after `N` calls or every 90 days                                                        |
| **Permissions Scope**       | Defines which endpoints or resources a key can access (e.g., `scope: "read:users"`).            | JSON payload: `{ "scopes": ["read", "write:data"], "expires": "2023-12-31" }`                   |
| **Revocable Flag**          | Boolean indicating if the key can be manually or programmatically revoked.                        | `revocable: true` (stored in metadata)                                                        |
| **Usage Audit Logs**        | Event logs tracking key access (e.g., timestamp, user/IP, endpoint).                                | `{ "event": "key_usage", "key_id": "abc123", "timestamp": "2023-10-01T12:00:00Z", "ip": "192.168.1.1" }` |
| **Rate Limiting**           | Thresholds to prevent brute-force attacks (e.g., 100 requests/minute).                             | Header: `X-RateLimit-Limit: 100`                                                              |
| **Honeypot Keys**           | Fake keys to detect unauthorized scanning or misuse.                                               | Prefix: `honey_*` in key IDs                                                                  |
| **Key Metadata**            | Additional attributes like `owner`, `created_at`, `last_used`, or `associated_user_id`.           | `{ "owner": "dev-team-A", "created_at": "2023-01-01", "tier": "premium" }`                    |

---

## **3. Implementation Details**

### **3.1 Key Generation**
- **Algorithms**: Use cryptographically secure algorithms like:
  - Symmetric (AES-256, Fernet for JWT).
  - Asymmetric (RSA/ECC for public/private pairs).
- **Randomness**: Ensure keys are randomly generated (e.g., using `/dev/urandom` or `secrets` module in Python).
- **Avoid Hardcoded Keys**: Never embed keys in source code or client-side scripts.

**Example (Python):**
```python
import secrets
import base64

def generate_key(length=32):
    return base64.urlsafe_b64encode(secrets.token_bytes(length)).decode()
```

### **3.2 Storage**
- **Encrypted Secrets Managers**: Prefer managed services like AWS Secrets Manager, HashiCorp Vault, or Azure Key Vault.
- **Hashicorp Vault**: Supports dynamic key generation and automatic rotation.
  ```bash
  vault kv put secret/api_keys/read_key key="<base64-encoded-key>" metadata="expires=2024-01-01"
  ```
- **On-Premise**: Use HSMs (e.g., AWS CloudHSM) or encrypted databases with field-level encryption.

### **3.3 Rotation**
- **Automated Rotation**: Triggered by:
  - Time-based (e.g., 90-day expiry).
  - Usage-based (e.g., after `N` calls).
  - Manual revocation via API or admin console.
- **Zero-Downtime Rotation**: Use short-lived tokens (JWT with 15-minute expiry) or double-encryption during transitions.
- **Backward Compatibility**: Maintain old keys until new ones are fully adopted (use a grace period).

**Example Rotation Flow:**
1. Generate a new key.
2. Assign it to the service/application.
3. Deactivate the old key after the grace period.

### **3.4 Permissions and Scopes**
- **Granular Access**: Assign scopes to keys (e.g., `read:analytics`, `write:config`).
- **Attribute-Based Access Control (ABAC)**: Consider attributes like `user_role` or `region` in policy evaluation.
- **Example Policy (Open Policy Agent):**
  ```rego
  default allow = false
  allow {
    input.key.scopes[_] == "read:data"
    input.user.role == "analyst"
  }
  ```

### **3.5 Monitoring and Logging**
- **Audit Trails**: Log all key operations (creation, revocation, usage).
  **Sample Log Format (JSON):**
  ```json
  {
    "event_type": "key_revoked",
    "key_id": "xyz789",
    "revoked_by": "admin@example.com",
    "timestamp": "2023-10-01T14:30:00Z"
  }
  ```
- **Anomaly Detection**: Alert on unusual patterns (e.g., sudden spikes in usage).
- **Tools**: Integrate with SIEMs (e.g., Splunk, ELK Stack) or cloud-native logging (AWS CloudTrail).

### **3.6 Rate Limiting and Throttling**
- **API-Gateway Policies**: Enforce rate limits at the gateway (e.g., Kong, AWS API Gateway).
  ```yaml
  # Kong Configuration
  plugins:
    - name: rate-limiting
      config:
        policy: local
        limit: 100
        window_size: 1
        redirect: /error
  ```
- **Client-Side Limits**: Encourage clients to implement exponential backoff.

### **3.7 Honeypot Keys**
- **Purpose**: Detect automated scraping or credential stuffing.
- **Implementation**:
  - Prefix keys with `honey_` and disable them after a few attempts.
  - Monitor for failed logins or unusual endpoints.

### **3.8 Key Metadata**
- **Track Usage**: Store metadata like `last_used_at` to identify stale keys.
- **Owner Tracking**: Link keys to teams/individuals for accountability.
- **Tiering**: Assign keys to tiers (e.g., `free`, `premium`) with differing quotas.

---

## **4. Query Examples**

### **4.1 Generate a New Key (REST API)**
**Endpoint**: `POST /api/v1/keys`
**Request Body**:
```json
{
  "scopes": ["read:data"],
  "expires": "2024-01-01",
  "revocable": true,
  "metadata": { "owner": "dev-team-B" }
}
```
**Response**:
```json
{
  "key_id": "abc123",
  "key": "base64-encoded-key",
  "expires": "2024-01-01",
  "scopes": ["read:data"]
}
```

### **4.2 List All Keys (Filter by Owner)**
**Endpoint**: `GET /api/v1/keys?owner=dev-team-B`
**Response**:
```json
[
  {
    "key_id": "abc123",
    "created_at": "2023-09-01",
    "last_used": "2023-09-30",
    "revoked": false,
    "scopes": ["read:data"]
  }
]
```

### **4.3 Revoke a Key**
**Endpoint**: `POST /api/v1/keys/abc123/revoke`
**Response**:
```json
{
  "status": "success",
  "revoked_at": "2023-10-01T15:00:00Z"
}
```

### **4.4 Fetch Key Usage Analytics**
**Endpoint**: `GET /api/v1/keys/abc123/usage`
**Response**:
```json
{
  "total_calls": 500,
  "last_call": "2023-10-01T14:00:00Z",
  "ip_addresses": ["192.168.1.1", "203.0.113.45"]
}
```

---

## **5. Best Practices**
1. **Never Log Keys**: Avoid logging or printing keys in plaintext.
2. **Use Short-Lived Tokens**: For internal services, prefer JWT with 15-minute expiry.
3. **Automate Rotation**: Implement CI/CD pipelines to rotate keys during deployments.
4. **Educate Teams**: Train developers on secure key handling (e.g., avoiding `git commit` leaks).
5. **Regular Audits**: Schedule quarterly reviews of key permissions and revocations.

---

## **6. Related Patterns**
| **Pattern**                     | **Description**                                                                                     | **When to Use**                                                                                     |
|---------------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| **JWT Authentication**          | Secure token-based authentication with short-lived tokens.                                           | When fine-grained access control is needed across microservices.                                   |
| **OAuth 2.0**                   | Delegated authorization using third-party identities (e.g., Google, GitHub).                       | For user-facing applications requiring SSO.                                                        |
| ** Mutual TLS (mTLS)**          | Encrypts communication between services using client certificates.                                    | High-security environments (e.g., financial services).                                             |
| **API Gateway Security**        | Centralized management of authentication, rate limiting, and DDoS protection.                       | For APIs with high traffic or public consumption.                                                 |
| **Secret Rotation Automation**  | Automates key/certificate rotation using DevOps tools (e.g., Ansible, Terraform).                 | When manual rotation is error-prone or unscalable.                                                |

---

## **7. References**
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security-top-10/)
- [NIST SP 800-63B](https://pages.nist.gov/800-63-3/sp800-63b.html) (Digital Identity Guidelines)
- [AWS Secrets Manager Best Practices](https://docs.aws.amazon.com/secretsmanager/latest/userguide/best-practices.html)
- [HashiCorp Vault Documentation](https://developer.hashicorp.com/vault/docs)

---
**Last Updated**: `YYYY-MM-DD`
**Version**: `1.2`