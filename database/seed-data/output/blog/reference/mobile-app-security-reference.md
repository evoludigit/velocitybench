# **[App Security Patterns] Reference Guide**

## **Overview**
This guide provides a structured framework for implementing **security best practices** in application development. The **App Security Patterns** pattern ensures robust protection against common threats (e.g., injection, CSRF, data leakage) through standardized architectural techniques. It categorizes security controls into **authentication, authorization, data protection, and defense mechanisms**, allowing developers to adopt proven strategies while adapting to specific use cases. By following these patterns, teams can reduce vulnerabilities, enhance compliance, and improve resilience without reinventing security solutions from scratch.

---

## **Schema Reference**
The pattern consists of **five core categories**, each with associated sub-patterns and implementation rules.

| **Category**          | **Sub-Pattern**                          | **Purpose**                                                                 | **Key Components**                                                                 | **Implementation Rules**                                                                 |
|-----------------------|------------------------------------------|------------------------------------------------------------------------------|-------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| **Authentication**    | **Multi-Factor Authentication (MFA)**    | Reduces risk of credential compromise.                                        | Tokens (TOTP/HOTP), Biometrics, SMS/Email backup.                                  | Require **at least 2 factors** (something you know + something you have/are).           |
|                       | **OAuth 2.0 / OpenID Connect**           | Secure delegation of access without sharing credentials.                     | `access_token`, `id_token`, `refresh_token`, Scopes, PKCE for PKAuth.              | Enforce **short-lived tokens** (max 1h) and revoke on logout.                          |
| **Authorization**     | **Role-Based Access Control (RBAC)**     | Fine-grained permission management.                                          | User roles, policies, attribute-based access control (ABAC).                        | Assign least-privilege roles; audit role elevation.                                   |
|                       | **Attribute-Based Access Control (ABAC)**| Dynamic permissions based on context (e.g., time, location).                 | Policies (e.g., "Admin access only during business hours").                       | Combine with RBAC for hybrid models.                                                  |
| **Data Protection**   | **Encryption at Rest (EaR)**             | Protects data stored in databases/filesystems.                               | AES-256, TLS, Key Management System (KMS).                                          | Encrypt **all sensitive data** (PII, financials). Use hardware security modules (HSMs). |
|                       | **End-to-End Encryption (E2EE)**         | Secures data in transit and in use.                                          | Public/private key pairs, Signal Protocol, TLS 1.3.                                 | Enforce E2EE for **high-risk communications** (e.g., healthcare, finance).            |
| **Defense Mechanisms**| **SQL Injection Prevention**             | Blocks malicious SQL input.                                                  | Prepared statements, ORMs, input validation.                                       | **Never** use string concatenation for queries. Use parameterized queries.           |
|                       | **Cross-Site Request Forgery (CSRF) Protection** | Prevents unauthorized actions via hijacked sessions.                   | `SameSite` cookies, CSRF tokens, Double Submit Cookie pattern.                      | Set `SameSite=Strict` for all session cookies.                                        |
|                       | **Rate Limiting**                       | Mitigates brute-force/DDoS attacks.                                          | Token bucket, sliding window filters.                                               | Cap requests to **≤ 100/min per IP**. Use adaptive thresholds for high-risk actions. |
| **Monitoring & Audit**| **Real-Time Anomaly Detection**        | Identifies suspicious activities (e.g., login attempts from unusual locations). | Behavioral analytics, SIEM integration.                                            | Flag **failed logins > 3 attempts/5 mins**.                                          |
|                       | **Audit Logging**                       | Tracks actions for compliance and forensics.                               | Immutable logs, JSON/W3C format, retention policies.                                | Log **all security events** (auth, data access) with timestamps and user context.      |

---

## **Implementation Details**

### **1. Authentication Workflows**
#### **Multi-Factor Authentication (MFA)**
- **How it works**:
  - User authenticates with password (Factor 1).
  - System sends a **time-based one-time password (TOTP)** via SMS/email or generates a QR code for an authenticator app (Factor 2).
  - Optional: Biometric verification (e.g., fingerprint) for Factor 3.
- **Example Flow**:
  1. User enters credentials → Server validates.
  2. Server generates TOTP (e.g., `123456`) and sends to user’s phone.
  3. User submits TOTP → Session established.
- **Tools**:
  - Libraries: [Google Authenticator (TOTP)](https://github.com/google/google-authenticator), [Duo Security](https://duo.com/).
  - Services: AWS MFA, Okta, Ping Identity.

#### **OAuth 2.0 / OpenID Connect**
- **Key Steps**:
  1. Client redirects user to **authorization server** with `response_type=code` and `scope=openid profile`.
  2. User logs in → Authorization server issues an **authorization code**.
  3. Client exchanges code for `access_token` and `id_token` (JWT).
  4. Client validates tokens using the **issuer’s public key**.
- **Security Hardening**:
  - Use **Proof Key for Code Exchange (PKCE)** to prevent code interception.
  - Set `access_token` expiry to **≤ 1 hour**; enforce token rotation.
- **Example Request**:
  ```http
  POST /token HTTP/1.1
  Content-Type: application/x-www-form-urlencoded

  grant_type=authorization_code&code=AUTH_CODE&redirect_uri=https://client.com/callback&client_id=CLIENT_ID&client_secret=SECRET
  ```

---

### **2. Authorization Patterns**
#### **Role-Based Access Control (RBAC)**
- **Implementation**:
  - Define roles (e.g., `Admin`, `Editor`, `Guest`) in a database.
  - Attach permissions to roles (e.g., `Admin: delete_user`).
  - Check permissions during API calls:
    ```javascript
    if (user.role.includes('Admin') && action === 'delete_user') {
      allow();
    } else {
      deny();
    }
    ```
- **Tools**:
  - Open-source: [Casbin](https://casbin.org/), [OAuth2 Proxy](https://oauth2-proxy.github.io/).
  - Enterprise: Azure AD, AWS IAM.

#### **Attribute-Based Access Control (ABAC)**
- **Use Case**: Grant access based on dynamic attributes (e.g., "only allow data access during business hours").
- **Example Policy**:
  ```
  ALLOW if:
    - request.user.department == "Finance"
    - request.time.in_business_hours == true
    - request.client.ip == trusted_subnet
  ```
- **Tools**: [OpenPolicyAgent (OPA)](https://www.openpolicyagent.org/), [AWS IAM Conditions](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html).

---

### **3. Data Protection**
#### **Encryption at Rest**
- **Steps**:
  1. Generate a **data encryption key (DEK)** per table/column.
  2. Encrypt DEK with a **key encryption key (KEK)** stored in a [HSM](https://en.wikipedia.org/wiki/Hardware_security_module).
  3. Encrypt data (e.g., `AES-256-GCM`) before storage.
- **Example (Python with PyCryptodome)**:
  ```python
  from Crypto.Cipher import AES

  key = b'32-byte-secret-key-1234567890abcdef'  # Must be 16/24/32 bytes
  cipher = AES.new(key, AES.MODE_GCM)
  ciphertext, tag = cipher.encrypt_and_digest(b"Sensitive data")
  ```
- **Database-Specific**:
  - **PostgreSQL**: Use [`pgcrypto`](https://www.postgresql.org/docs/current/pgcrypto.html).
  - **MongoDB**: [`client-side field-level encryption`](https://www.mongodb.com/docs/manual/core/field-level-encryption/).

#### **End-to-End Encryption (E2EE)**
- **Protocols**:
  - **Signal Protocol**: Used by WhatsApp, Signal. Supports forward secrecy.
  - **TLS 1.3**: For transport security (avoid TLS 1.0/1.1).
- **Implementation**:
  - Client generates a **public/private key pair**.
  - Server encrypts data with client’s public key; client decrypts with private key.
  - Example (using [libsodium](https://libsodium.gitbook.io/)):
    ```python
    import sodium
    sodium.init()

    private_key = sodium.crypto_sign_seed_keypair().sign_private_key
    public_key = sodium.crypto_sign_seed_keypair().sign_public_key
    message = b"Secret message"
    encrypted = sodium.crypto_sign_detached(message, private_key)
    decrypted = sodium.crypto_sign_open(encrypted, public_key)
    ```

---

### **4. Defense Mechanisms**
#### **SQL Injection Prevention**
- **Do**:
  - Use **parameterized queries** (prepared statements).
    ```python
    # Safe (Python + psycopg2)
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    ```
  - Validate input against a **whitelist**.
- **Don’t**:
  ```sql
  # UNSAFE (string concatenation)
  query = f"SELECT * FROM users WHERE username = '{username}'"
  cursor.execute(query)
  ```

#### **CSRF Protection**
- **SameSite Cookies**:
  - Set `HttpOnly`, `Secure`, and `SameSite=Strict/Lax` for session cookies.
    ```http
    Set-Cookie: sessionid=abc123; SameSite=Strict; Secure; HttpOnly
    ```
- **Double Submit Cookie Pattern**:
  1. Server sets a hidden field (`<input type="hidden" name="csrf_token" value="...">`).
  2. Server also stores the token in a cookie.
  3. On form submission, verify cookie == hidden field.

#### **Rate Limiting**
- **Tools**:
  - **Open-source**: [Redis Rate Limiter](https://github.com/alizain/redis-rate-limiter), [NGINX `limit_req`](https://nginx.org/en/docs/http/ngx_http_limit_req_module.html).
  - **Cloud**: AWS WAF, Cloudflare Rate Limiting.
- **Example (Redis)**:
  ```python
  import redis
  r = redis.Redis()
  key = f"rate_limit:{user_ip}:login"
  if r.incr(key) > 5:  # Block after 5 attempts
      deny_access()
      r.expire(key, 300)  # Reset in 5 mins
  ```

---

### **5. Monitoring & Audit**
#### **Real-Time Anomaly Detection**
- **Signals to Monitor**:
  - **Failed logins** (>3 in 5 mins).
  - **Unexpected location changes** (e.g., login from Brazil → sudden login from China).
  - **Unusual access times** (e.g., 3 AM during business hours).
- **Tools**:
  - **SIEM**: Splunk, ELK Stack (Elasticsearch + Logstash + Kibana).
  - **Behavioral Analytics**: Darktrace, Vectra AI.

#### **Audit Logging**
- **Mandatory Fields**:
  - Timestamp (ISO 8601).
  - User ID/role.
  - IP address.
  - Action performed (e.g., `USER_DELETED`, `DATA_ACCESS`).
  - Outcome (success/failure).
- **Example Log Entry**:
  ```json
  {
    "timestamp": "2023-10-01T12:00:00Z",
    "user_id": "user123",
    "role": "Admin",
    "ip": "192.0.2.1",
    "action": "delete_user",
    "target": "user456",
    "status": "success"
  }
  ```
- **Storage**:
  - **Encrypted** logs (e.g., AWS KMS).
  - **Immutable** logs (e.g., WORM storage like AWS S3 Object Lock).

---

## **Query Examples**
### **1. Check User Permissions (RBAC)**
**Request**:
```http
GET /api/permissions?user_id=user123&action=edit_post
```
**Response (200 OK)**:
```json
{
  "allowed": true,
  "roles": ["Editor", "Moderator"]
}
```
**Response (403 Forbidden)**:
```json
{
  "error": "Insufficient permissions"
}
```

### **2. Validate OAuth Token**
**Request**:
```http
GET /api/profile?access_token=eyJhbGci...  # JWT
```
**Response (200 OK)**:
```json
{
  "user": {
    "id": "user123",
    "name": "Alice",
    "email": "alice@example.com"
  }
}
```
**Response (401 Unauthorized)**:
```json
{
  "error": "Invalid or expired token"
}
```

### **3. Fetch Encrypted Data**
**Request**:
```http
GET /api/data?key=ENCRYPTED_DATA_KEY
```
**Response (200 OK)**:
```json
{
  "data": "AQIDBAUGBwgJCgsMDQ4PEBESExQVFhcYGRobHBC...
  // (Base64-encoded ciphertext)
}
```

### **4. Rate Limit Check**
**Request**:
```http
POST /api/login
Host: example.com
```
**Response (429 Too Many Requests)**:
```http
HTTP/1.1 429 Too Many Requests
Retry-After: 60
```

---

## **Related Patterns**
For deeper integration, combine **App Security Patterns** with:

1. **[Zero Trust Architecture (ZTA)](https://docs.microsoft.com/en-us/azure/architecture/framework/security/zero-trust)**
   - Extends security beyond the perimeter (e.g., verify every request, even internal).

2. **[Secret Management](https://www.owasp.org/index.php/Secret_Management)**
   - Stores credentials/keys securely (e.g., AWS Secrets Manager, HashiCorp Vault).

3. **[Secure API Design](https://docs.microsoft.com/en-us/azure/architecture/best-practices/api-design)**
   - Defines best practices for API authentication (OAuth), rate limiting, and input validation.

4. **[Secure Configuration Management](https://www.owasp.org/index.php/Secure_Configuration_Management)**
   - Hardens infrastructure (e.g., disable unused services, rotate keys automatically).

5. **[Incident Response](https://www.nist.gov/topics/incident-response)**
   - Complements monitoring by defining playbooks for breaches (e.g., containment, forensics).

---
## **Further Reading**
- **[OWASP Application Security Patterns](https://cheatsheetseries.owasp.org/cheatsheets/Application_Security_Patterns_Cheat_Sheet.html)**
- **[MITRE ATT&CK for Application Security](https://attack.mitre.org/)**
- **[NIST SP 800-41 Rev. 2 (Secure Application Development)](https://csrc.nist.gov/publications/detail/sp/800-41/rev-2/final)**