# **[Pattern] OAuth 2.0 Delegated Authorization – Reference Guide**

---

## **Overview**
The **OAuth 2.0 Delegated Authorization** pattern enables secure delegation of user authentication and resource access between third-party applications (clients) and identity providers (e.g., Google, Microsoft, or custom systems). Unlike direct password-based auth, OAuth delegates credentials via tokens, minimizing risk while granting granular permissions. This pattern standardizes four key flows for flexibility: **Authorization Code**, **Implicit**, **Client Credentials**, and **Resource Owner Password Credentials (ROPC)**.

Best practices emphasize:
- **Security-first design** (e.g., PKCE for public clients, short-lived tokens).
- **Minimal permissions** (scopes) for least privilege.
- **Token handling** (storing refresh tokens securely, revoking expired tokens).
- **Postures for different client types** (confidential vs. public clients).

This guide covers implementation details, mandatory/optional schema elements, query examples, and related security patterns.

---

## **1. Core Components (Schema Reference)**

| **Component**               | **Description**                                                                                     | **Required?** | **Notes (Best Practices)**                                                                                     |
|-----------------------------|-----------------------------------------------------------------------------------------------------|---------------|---------------------------------------------------------------------------------------------------------------|
| **Client Registration**     | Unique client ID, redirect URIs, and optional secrets (confidential clients).                         | Yes           | Register with identity provider (IdP). Avoid hardcoding secrets; use environment variables.                  |
| **User Agent**              | End user’s browser, app, or mobile client initiating auth flow.                                       | Indirect*     | Public clients (e.g., SPAs) use **Authorization Code + PKCE**; confidential clients (e.g., servers) can use **Client Credentials**. |
| **Authorization Server**    | Issues tokens (access/refresh) after validating client credentials and user consent.                 | Yes           | Must support [RFC 6749](https://datatracker.ietf.org/doc/html/rfc6749).                                        |
| **Resource Server**         | Hosts protected resources (e.g., APIs) and validates access tokens.                                 | Yes           | Enforce [JWT validation](https://datatracker.ietf.org/doc/html/rfc7519) (e.g., signature, expiration, scopes). |
| **Redirect URI**            | Callback URL for OAuth responses (e.g., `https://client.com/callback`).                             | Yes           | Must match registered URIs; use HTTPS.                                                                      |
| **Access Token**            | Short-lived (e.g., 1-hour) token for API access.                                                    | Yes (for flows requiring it) | Store server-side if sensitive; use [OAuth 2.1](https://datatracker.ietf.org/doc/html/rfc9101) for stricter specs. |
| **Refresh Token**           | Long-lived token to obtain new access tokens without re-authenticating.                              | Optional      | Issue only if user explicitly consents; rotate after use.                                                  |
| **Scope**                   | Defines permitted resource access (e.g., `openid`, `profile`, `read:api`).                           | Optional      | Limit granularity (e.g., avoid wildcard `*` scopes).                                                      |
| **PKCE (Proof Key for Code Exchange)** | Security mechanism for public clients to prevent code interception.                      | Recommended*  | Required for **Authorization Code** flow in public clients.                                                  |
| **OpenID Connect (OIDC) Extensions** | Optional layer for identity info (e.g., `id_token` for user claims).                             | Optional      | Use if user profile/email is needed; define in `scope` (e.g., `openid`).                                  |

---
*Indirect = Depends on client type (public/confidential).
*Required for public clients; optional for confidential clients.

---

## **2. OAuth 2.0 Flows (Implementation Patterns)**

### **A. Authorization Code Flow (Confidential Clients)**
**Use Case:** Server-side apps (e.g., web backends, mobile backends).
**Security:** High (access/refresh tokens exchanged server-side).

#### **Query Examples**
1. **Auth Request to IdP** (User redirects):
   ```
   GET /authorize?
     response_type=code&
     client_id=<CLIENT_ID>&
     redirect_uri=https://client.com/callback&
     scope=openid%20profile%20read:api&
     state=abc123
   ```
2. **Token Request** (Server exchanges code for tokens):
   ```
   POST /token
   Content-Type: application/x-www-form-urlencoded

   code=<AUTH_CODE>&
   redirect_uri=https://client.com/callback&
   client_id=<CLIENT_ID>&
   client_secret=<CLIENT_SECRET>&
   grant_type=authorization_code
   ```
3. **Access Token Usage** (Call protected API):
   ```
   GET /api/user-data
   Authorization: Bearer <ACCESS_TOKEN>
   ```

---

### **B. Implicit Flow (Public Clients)**
**Use Case:** Single-page apps (SPAs) with no backend.
**Security:** Lower (access token in URL); **avoid new projects** (use **PKCE + Authorization Code** instead).

#### **Query Example (Deprecated)**
```
GET /authorize?
  response_type=token&
  client_id=<CLIENT_ID>&
  redirect_uri=https://client.com/callback&
  scope=openid%20profile
```
→ Returns:
```
# Fragment in URL:
  #access_token=abc123&
  #token_type=Bearer&
  #expires_in=3600&
  #state=abc123
```
**⚠️ Warning:** Use **PKCE + Authorization Code** instead:
```
GET /authorize?
  response_type=code&
  client_id=<CLIENT_ID>&
  redirect_uri=https://client.com/callback&
  code_challenge=<CODE_CHALLENGE>&
  code_challenge_method=S256&
  state=abc123
```

---

### **C. Client Credentials Flow (Machine-to-Machine)**
**Use Case:** Backend services (e.g., API-to-API auth).
**Security:** Medium (no user auth; rely on client secret).

#### **Query Example**
```
POST /token
Content-Type: application/x-www-form-urlencoded

client_id=<CLIENT_ID>&
client_secret=<CLIENT_SECRET>&
grant_type=client_credentials&
scope=read:api
```

---

### **D. Resource Owner Password Credentials (ROPC) Flow**
**Use Case:** Legacy systems (e.g., syncing credentials).
**Security:** **Low** (transmits username/password; avoid unless necessary).
**Best Practice:** Use only for internal apps with secure transport (TLS).

#### **Query Example**
```
POST /token
Content-Type: application/x-www-form-urlencoded

username=<USER>&
password=<PASS>&
grant_type=password&
client_id=<CLIENT_ID>&
client_secret=<CLIENT_SECRET>&
scope=openid%20profile
```

---

## **3. Token Handling Best Practices**
| **Pattern**               | **Recommendation**                                                                                     | **Example**                                                                                     |
|---------------------------|-------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Token Storage**         | Use **short-lived access tokens** (e.g., 1 hour) + **refresh tokens** (cached securely).             | Store refresh token in HTTP-only cookie (same-site).                                          |
| **Token Revocation**      | Implement **token blacklisting** or [RFC 7009](https://datatracker.ietf.org/doc/html/rfc7009) (introspection). | Call `/revoke?token=<TOKEN>` endpoint.                                                          |
| **Scopes**                | Define **explicit scopes** (avoid `*`); validate server-side.                                         | `scope=read:profile write:posts` instead of `openid`.                                           |
| **PKCE for Public Clients** | Always use **PKCE** with `code_challenge`/`code_verifier`.                                           | Generate verifier (`sha256("random")`), encode challenge (`base64url(sha256(verifier))`).       |
| **Token Validation**      | Verify **issuer**, **audience**, **expiration**, and **signature** (JWT).                             | Use libraries like [`jose`](https://github.com/panva/jose) (Node.js) or `python-jose`.            |

---

## **4. Error Handling**
| **Error Code**  | **Description**                                                                                     | **Response Example**                                                                             |
|-----------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| `invalid_request` | Missing/invalid parameters (e.g., `redirect_uri` mismatch).                                         | `{"error":"invalid_request","error_description":"Redirect URI invalid"}`.                        |
| `access_denied`  | User rejected consent.                                                                              | `{"error":"access_denied","error_description":"User denied access"}`.                            |
| `unauthorized_client` | Invalid/client_secret pair.                                                                      | `{"error":"unauthorized_client","error_description":"Client credentials invalid"}`.              |
| `unsupported_grant_type` | Unsupported `grant_type` (e.g., `password` flow with public client).                             | `{"error":"unsupported_grant_type","error_description":"Grant type not supported"}`.              |
| `server_error`   | IdP/server failure.                                                                                 | `{"error":"server_error","error_description":"Internal server error"}`.                          |

---

## **5. Related Patterns**
1. **[OpenID Connect (OIDC)]**
   - Extends OAuth 2.0 with **identity claims** (e.g., `id_token` with `sub`, `name`, `email`).
   - Use when you need user profile data beyond scope claims.

2. **[JWT (JSON Web Tokens)]**
   - Tokens issued by OAuth 2.0 are typically JWTs. Validate:
     - Signature (`HS256`/`RS256`).
     - Issuer (`iss` claim).
     - Audience (`aud` claim).
     - Expiration (`exp` claim).

3. **[OAuth 2.0 Token Introspection]**
   - Server-side validation via `/introspect` endpoint to check token revocation.

4. **[PKCE (Proof Key for Code Exchange)]**
   - **Critical for public clients** (e.g., SPAs) to prevent **authorization code interception**.

5. **[Dynamic Client Registration]**
   - Automatically register clients via `/register` endpoint (useful for microservices).

6. **[OAuth 2.1]**
   - Upcoming standard with **stricter security** (e.g., mandatory PKCE, no implicit flow).

---

## **6. Security Considerations**
- **Never expose client secrets** in frontend code.
- **Use HTTPS** for all endpoints (OAuth 2.0 requires secure transport).
- **Rotate refresh tokens** after use (issue new ones on next request).
- **Avoid `read:all` scopes**—granularize permissions.
- **Log token revocations** for auditing.

---
**Further Reading:**
- [RFC 6749 (OAuth 2.0)](https://datatracker.ietf.org/doc/html/rfc6749)
- [OAuth 2.0 Security Best Current Practices](https://datatracker.ietf.org/doc/html/rfc6819)
- [PKCE RFC 7636](https://datatracker.ietf.org/doc/html/rfc7636)