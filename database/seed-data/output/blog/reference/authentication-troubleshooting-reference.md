**[Pattern] Authentication Troubleshooting Reference Guide**

---

### **Overview**
Authentication troubleshooting ensures users, applications, and services can securely verify identities while resolving common access failures. This guide covers root causes, diagnostic steps, validation techniques, and remediation strategies for authentication errors in systems integrating with identity providers (IdPs), OAuth 2.0, OpenID Connect (OIDC), or local databases. It applies to developers, DevOps teams, and administrators handling login failures, token expiry, or permission issues across APIs, microservices, or cloud platforms.

---

### **Schema Reference**

| **Category**               | **Key Components**                                                                 | **Attributes (Example)**                                                                 | **Notes**                                                                                     |
|----------------------------|------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------|
| **Authentication Errors**  | Error Type                                                                      | `error_type: "invalid_token"`, `"expired_token"`, `"permission_denied"`                   | Distinguish between client, server, or IdP errors                                             |
| **Token Validation**       | Token Format                                                                      | `JWT` (access/refresh), `SAML Assertion`, `OAuth 2.0 Bearer Token`                        | Check token header/payload for `iss`, `sub`, `exp` claims                                     |
| **IdP Configuration**      | Identity Provider Details                                                         | `provider: "AzureAD"`, `client_id: "abc123"`, `audience: "api.example.org"`                 | Verify `redirect_uri`, `response_type`, and scopes                                            |
| **Network & Logging**      | Logs, Headers, and Metrics                                                        | `X-Forwarded-For`, `User-Agent`, `auth_request_latency_ms`                              | Correlate logs with metrics (e.g., `auth_failure_count`)                                      |
| **Policy Rules**           | Security Policies (e.g., MFA, Conditional Access)                                 | `mfa_required: true`, `ip_restriction: ["192.168.0.0/24"]`                              | Review policy overrides or conflicting rules                                                   |
| **API Endpoints**          | Authentication Endpoints                                                          | `/oauth/token`, `/connect/token`, `/authorize`, `/login`                                  | Test with `curl`, Postman, or SDKs (e.g., `axios`, `requests`)                                |
| **Client-Side Values**     | User Input/Configuration                                                            | `username: "user@example.com"`, `password: "********"`, `refresh_token: "abc..."`        | Validate input for typos, encoding issues, or injection risks                                 |
| **Server-Side Values**     | Server Events/State                                                              | `session_id: "xyz789"`, `last_active: "2023-10-01T12:00:00Z"`, `status: "inactive"`     | Check database/redis for stale sessions                                                      |
| **Third-Party Integrations**| External Services (e.g., LDAP, SSO)                                             | `ldap_server: "ldap://ldap.example.com"`, `sso_provider: "Keycloak"`                     | Test LDAP bind operations or SSO federation flows                                             |

---

### **Query Examples**

#### **1. Validating OAuth 2.0 Token in a Request**
**Scenario**: A `403 Forbidden` error occurs when accessing an API.
**Steps**:
1. **Extract the Token**:
   ```bash
   curl -v -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
        https://api.example.org/protected-resource
   ```
2. **Decode and Verify JWT** (using [jwt.io](https://jwt.io)):
   ```json
   {
     "alg": "HS256",
     "typ": "JWT"
   }
   .
   {
     "iss": "https://auth.example.com",
     "sub": "user123",
     "aud": "api.example.org",
     "exp": 1700000000  # Check if token is expired
   }
   ```
3. **Check Token Validity** (using `openssl`):
   ```bash
   openssl dgst -sha256 -verify public_key.pem -signature signature_base64 \
     <(echo -n "header.payload")
   ```

#### **2. Debugging MFA Failures**
**Scenario**: User repeatedly fails MFA prompts.
**Logs to Check**:
- **Azure AD**:
  ```bash
  # Azure Portal: Audit Logs → Filter by "Authentication Request"
  ```
- **Keycloak**:
  ```bash
  # Keycloak Admin Console: Events → Filter by "Factor Verify" → "FAILED"
  ```
**Remediation**:
- **Reset MFA**:
  ```bash
  # Example: Keycloak CLI
  ./keycloak-admin-cli.sh --server-url http://localhost:8080 \
    --user admin --password admin \
    --realm master execute-cli "update-user-factors --user-id user123 --factor-id mfa-otp --status DISABLED"
  ```

#### **3. Troubleshooting Redirect URI Mismatch**
**Scenario**: OAuth flow fails with `redirect_uri` mismatch.
**Diagnosis**:
- **Check Registered URI** (e.g., Azure AD App Registration):
  ```
  https://api.example.org/callback
  ```
- **Inspect Redirect Request**:
  ```bash
  curl -v "https://auth.example.com/authorize?response_type=code&client_id=abc123&redirect_uri=https://api.example.org/callback&scope=openid%20profile"
  ```
  **Error Response**:
  ```json
  {
    "error": "redirect_uri_mismatch",
    "error_description": "The 'redirect_uri' parameter does not match the registered value."
  }
  ```
**Fix**: Update the `redirect_uri` in the IdP configuration.

#### **4. Validating LDAP Bind Operations**
**Scenario**: Local authentication fails with `530 Authentication Failure`.
**Steps**:
1. **Test LDAP Connection**:
   ```bash
   ldapsearch -x -H ldap://ldap.example.com -b "dc=example,dc=com" -D "cn=admin,dc=example,dc=com" -w "adminpassword"
   ```
2. **Check Bind DN/Password**:
   - Ensure the `bind_dn` and `bind_pw` in the application match the LDAP server.
3. **Enable Debugging** (e.g., Spring Security):
   ```properties
   # application.properties
   spring.ldap.debug=TRUE
   ```

---

### **Root Cause Analysis Table**

| **Symptom**                     | **Possible Cause**                                                                 | **Diagnosis Steps**                                                                 | **Solution**                                                                                     |
|---------------------------------|------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| `401 Unauthorized`              | Expired token, missing `Authorization` header, invalid credentials                | Check `exp` claim, inspect headers, validate credentials in logs                      | Regenerate token, retry request, or update credentials                                           |
| `403 Forbidden`                 | Insufficient scope, permission denied, or stale token                              | Review JWT scopes (`scope` claim), check `nbf`/`exp`, audit policies                | Request additional scopes, revoke stale tokens, or adjust policies                              |
| MFA Prompt Loop                 | Wrong MFA code, device trust issues, or policy errors                              | Verify MFA method (SMS/OTP), check device registration, inspect logs                 | Reset MFA, re-enroll device, or override policy temporarily                                       |
| `redirect_uri_mismatch`         | Incorrect URI in request or IdP configuration                                       | Compare `redirect_uri` in request vs. IdP settings                                   | Update URI in both client and IdP                                                               |
| `invalid_client`                | Invalid `client_id` or secret                                                   | Check `client_id` and `client_secret` in logs                                       | Verify credentials in IdP dashboard                                                             |
| Slow Authentication            | IdP latency, network issues, or heavy load                                         | Measure latency with `time curl`, check IdP status pages                            | Optimize network, scale IdP, or implement caching                                                |
| Session Timeout                 | Inactive session, cookie expiration, or server misconfig                           | Check session duration settings, inspect cookies (`JSESSIONID`, `auth_token`)       | Extend session timeout, verify cookie attributes (`Secure`, `HttpOnly`)                           |

---

### **Validation Techniques**

1. **Token Introspection**
   - **Endpoint**: `POST /introspect`
   - **Request**:
     ```http
     POST /introspect HTTP/1.1
     Host: auth.example.com
     Content-Type: application/x-www-form-urlencoded

     token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...&client_id=abc123&client_secret=...&token_type_hint=access_token
     ```
   - **Response**:
     ```json
     {
       "active": true,
       "scope": "openid profile email",
       "client_id": "abc123"
     }
     ```

2. **Silent Token Refresh**
   - **Use Case**: Avoid user re-authentication.
   - **Workflow**:
     1. Send `refresh_token` to `/token` endpoint.
     2. Validate `access_token` in subsequent requests.

3. **Audit Log Correlation**
   - **Tools**:
     - **Azure AD**: Azure Monitor + Log Analytics.
     - **Keycloak**: Event Listener + Database queries.
   - **Query Example** (Keycloak):
     ```sql
     SELECT * FROM events
     WHERE eventId LIKE '%AUTHENTICATION_FAILURE%' AND username = 'user123'
     ORDER BY createdDate DESC LIMIT 10;
     ```

---

### **Common Pitfalls & Mitigations**

| **Pitfall**                          | **Impact**                                                                       | **Mitigation**                                                                         |
|---------------------------------------|-------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| **Hardcoded Secrets**                 | Security breach if credentials leak in code                                    | Use environment variables (e.g., `client_secret`) or secrets managers (Vault, AWS SSM). |
| **No Token Expiry Handling**          | Session hijacking, stale data                                                | Implement short-lived tokens (`exp` ≤ 1 hour) + refresh tokens.                        |
| **Ignoring IdP Time Sync Issues**      | Clock skew causing `nbf`/`exp` mismatches                                     | Sync system clocks (NTP) and validate token timestamps.                                |
| **Over-Permissive Scopes**            | Unauthorized data access                                                      | Scope down permissions; use `openid` + minimal role-based scopes.                     |
| **No Circuit Breaker for IdP**        | Cascading failures during IdP downtime                                         | Implement retry logic + fallback to cache/local auth.                                  |
| **Logging Sensitive Data**            | Exposure of tokens/credentials in logs                                        | Redact logs (e.g., `expired_token` instead of full token).                            |

---

### **Related Patterns**

1. **[Secure API Design](https://example.com/api-design)**
   - Ensures authentication integrates with rate limiting, CORS, and input validation.

2. **[Token Management](https://example.com/token-management)**
   - Covers token generation, rotation, and storage best practices (e.g., JWT vs. opaque tokens).

3. **[Conditional Access Policies](https://example.com/conditional-access)**
   - Configures dynamic access rules based on user/device context (e.g., MFA for risky locations).

4. **[Multi-Factor Authentication (MFA)](https://example.com/mfa)**
   - Details implementation of TOTP, hardware keys, or biometrics.

5. **[IdP Federation](https://example.com/idp-federation)**
   - Standardizes cross-provider authentication (SAML, OAuth 2.0, OIDC).

6. **[Rate Limiting for Auth Endpoints](https://example.com/rate-limiting)**
   - Protects against brute-force attacks on `/token` or `/authorize`.

7. **[Session Management](https://example.com/session-management)**
   - Handles session lifecycles, invalidation, and concurrent logins.

---
### **Further Reading**
- [OAuth 2.0 Spec](https://oauth.net/2/)
- [OpenID Connect Core](https://openid.net/specs/openid-connect-core-1_0.html)
- [Azure AD Troubleshooting Guide](https://learn.microsoft.com/en-us/azure/active-directory/develop/troubleshoot-ad)
- [Keycloak Admin Guide](https://www.keycloak.org/documentation)