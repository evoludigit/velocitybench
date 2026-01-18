---
# **[Authentication Troubleshooting] Reference Guide**

---

## **1. Overview**
Authentication failures can disrupt application workflows, security policies, and user experiences. This guide provides a **structured troubleshooting approach** for diagnosing and resolving common authentication issues. It covers **error patterns, validation steps, and remediation techniques** for OAuth 2.0, API Keys, JWT, password-based auth, and multi-factor authentication (MFA) systems. The guide is organized by **symptom**, **root cause**, and **correction**, ensuring rapid issue resolution.

Key focus areas:
- **Client-side vs. server-side** authentication failures
- **Token-related issues** (expiry, revocation, invalid signatures)
- **Configuration mismatches** (CORS, redirect URIs, scopes)
- **Dependency failures** (IDP, OAuth providers, databases)

---

## **2. Schema Reference**

| **Category**               | **Field**                  | **Description**                                                                                     | **Example Values**                                                                 |
|----------------------------|----------------------------|-----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **General Auth Errors**    | `error_code`               | Standardized error code (e.g., `401`, `403`, `429`)                                                 | `"error": "invalid_grant"`                                                        |
|                            | `error_description`        | Human-readable explanation of the failure                                                           | `"message": "Token expired at 15:30 UTC"`                                           |
|                            | `timestamp`                | ISO-8601 formatted timestamp of the failure                                                         | `"timestamp": "2023-11-15T14:22:58Z"`                                              |
| **OAuth 2.0**              | `grant_type`               | OAuth flow type (e.g., `authorization_code`, `client_credentials`)                                  | `"grant_type": "refresh_token"`                                                   |
|                            | `auth_server`              | ID of the OAuth provider (e.g., `auth0`, `okta`)                                                    | `"auth_server": "okta"`                                                             |
|                            | `scope`                    | Requested permissions (e.g., `openid profile email`)                                                | `"scope": "read write"`                                                             |
| **JWT Validation**         | `alg`                      | Algorithm used for JWT signing (e.g., `RS256`, `HS256`)                                             | `"alg": "HS256"`                                                                   |
|                            | `kid`                      | Key ID for asymmetric keys (if applicable)                                                          | `"kid": "abc123-4567-890"`                                                         |
|                            | `exp`                      | Expiration time (UNIX timestamp)                                                                   | `"exp": 1700000000`                                                                |
| **MFA**                    | `mfa_factor`               | Secondary auth method (e.g., `totp`, `sms`, `hardware_key`)                                        | `"mfa_factor": "totp"`                                                              |
|                            | `retry_count`              | Number of failed attempts before MFA lockout                                                         | `"retry_count": 3`                                                                 |
| **API Key Auth**           | `api_key_name`             | Name of the key used in headers (e.g., `X-API-Key`)                                                 | `"X-API-Key": "sk_123abc"`                                                          |
|                            | `key_rotation_status`      | Whether the key has expired/been revoked                                                           | `"status": "revoked"`                                                               |

---

## **3. Query Examples**

### **3.1 Common Authentication Query Patterns**
Use these `curl`/`HTTP` requests to diagnose issues. Replace placeholders (`{}`) with actual values.

#### **A. Token Validation Request**
```http
GET /auth/validate?token={JWT_TOKEN}
Headers:
  Authorization: Bearer {JWT_TOKEN}
```
**Expected Response (Success):**
```json
{
  "valid": true,
  "expires_at": "2023-12-01T12:00:00Z",
  "scopes": ["read", "write"]
}
```
**Expected Response (Failure):**
```json
{
  "error": "invalid_token",
  "description": "Token not found in database"
}
```

#### **B. OAuth 2.0 Token Refresh**
```http
POST /oauth/token
Headers:
  Content-Type: application/x-www-form-urlencoded
Body:
  grant_type=refresh_token
  &refresh_token={REFRESH_TOKEN}
  &client_id={CLIENT_ID}
  &client_secret={CLIENT_SECRET}
```
**Failure Example (Invalid Refresh Token):**
```json
{
  "error": "invalid_grant",
  "error_description": "Refresh token expired"
}
```

#### **C. MFA Challenge (SMS/TOTP)**
```http
POST /auth/mfa/challenge
Headers:
  Content-Type: application/json
Body:
  {
    "factor": "sms",
    "phone": "+1234567890"
  }
```
**Failure Example (Invalid Phone Number):**
```json
{
  "error": "invalid_request",
  "message": "Phone not registered"
}
```

---

### **3.2 Debugging Logs**
**Server-Side Logs (Example):**
```
[ERROR] auth_service: Token validation failed for user_id=123.
  - JWT 'kid' mismatch: expected 'abc123', got 'def456'.
  - Possible cause: Key rotation not propagated to client.
```
**Client-Side Logs (Example):**
```javascript
console.error("Auth Error:", {
  status: 403,
  message: "Forbidden: Missing required scope 'admin'",
  path: "/admin/dashboard"
});
```

---

## **4. Troubleshooting Workflow**

### **4.1 Symptom-Based Root Cause Analysis**
| **Symptom**                          | **Likely Cause**                          | **Solution**                                                                 |
|--------------------------------------|-------------------------------------------|------------------------------------------------------------------------------|
| `401 Unauthorized`                   | Missing/invalid `Authorization` header    | Verify header format (`Bearer {token}`), check token validity.               |
| `403 Forbidden`                      | Expired token or insufficient scopes      | Issue a new token; check `scope` permissions in response.                   |
| `400 Bad Request`                    | Malformed payload (e.g., OAuth params)   | Validate `grant_type`, `client_id`, and `redirect_uri`.                    |
| MFA lockout                          | Too many failed attempts                 | Reset MFA via admin panel; review `retry_count` limits.                      |
| Redirect loops                       | Incorrect `redirect_uri` in OAuth config  | Match `redirect_uri` exactly in client registration.                        |
| Slow responses (JWT validation)     | Asymmetric key decryption delay          | Optimize key caching; use `kid` hint for faster lookup.                     |

---

### **4.2 Step-by-Step Corrections**

#### **A. Token Expiry Issues**
1. **Check `exp` claim** in JWT:
   ```json
   {
     "exp": 1700000000  // Compare with current UNIX timestamp
   }
   ```
2. **Refresh token** using `refresh_token` grant:
   ```http
   POST /oauth/token?grant_type=refresh_token&refresh_token={TOKEN}
   ```
3. **Configure token TTL** (e.g., 30 minutes) in auth server settings.

#### **B. CORS/Redirect URI Mismatches**
1. **Verify `allowed_redirect_uris`** in OAuth client config:
   ```json
   {
     "redirect_uris": [
       "https://app.example.com/callback",
       "https://dev.example.com/callback"
     ]
   }
   ```
2. **Check browser console** for CORS errors (e.g., `Origin` mismatch).

#### **C. MFA Bypass Attempts**
1. **Audit failed MFA attempts**:
   ```sql
   SELECT * FROM mfa_attempts WHERE user_id = 123 AND status = 'failed';
   ```
2. **Adjust `retry_count`** in auth config (default: 5 attempts).
3. **Log MFA events** for security monitoring.

---

## **5. Related Patterns**
| **Pattern**                     | **Description**                                                                 | **Use Case**                                                                 |
|----------------------------------|---------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **[Idempotent OAuth Flows]**      | Ensure OAuth requests are repeatable without side effects.                     | Protect against duplicate token requests during network retries.             |
| **[Token Blacklisting]**         | Revoke tokens proactively (e.g., on session end or breach).                     | Mitigate credential theft risks.                                              |
| **[JWT Key Rotation]**            | Automate private key updates without client disruption.                         | Secure long-lived tokens against key compromise.                              |
| **[Rate Limiting for Auth]**     | Throttle login attempts to prevent brute-force attacks.                         | Harden against credential stuffing.                                          |
| **[Federated Identity]**         | Integrate with SAML/OpenID Connect for SSO.                                     | Unify auth across multiple applications.                                      |

---

## **6. Best Practices**
1. **Centralized Logging**: Correlate auth events with application logs (e.g., ELK stack).
2. **Token Analytics**: Monitor token issuance/expires to detect anomalies (e.g., sudden spikes).
3. **Client-Side Validation**: Validate tokens before sending to the server (e.g., `jwt-decode` library).
4. **Key Management**: Use HSMs for asymmetric keys; rotate keys quarterly.
5. **Deprecation Policy**: Gracefully handle deprecated auth methods (e.g., Basic Auth → API Keys).

---
**Last Updated:** `2023-11-15`
**Version:** `1.2`