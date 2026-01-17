---
# **[Pattern] OAuth, SAML, and SSO Authentication Patterns – Reference Guide**

---

## **1. Overview**
This guide outlines authentication patterns using **OAuth 2.0**, **SAML 2.0**, and **Single Sign-On (SSO)**. These protocols enable secure, centralized authentication and authorization across applications and services.

- **OAuth 2.0** (modern) handles token-based delegation, allowing third-party access without exposing credentials.
- **SAML 2.0** (legacy) uses XML-based assertions for enterprise SSO, often tied to identity providers (IdP) like Active Directory Federation Services (ADFS).
- **SSO** simplifies user login by maintaining a single session across systems.

This guide compares key concepts, provides implementation details, and includes schema references for interoperability.

---

## **2. Key Concepts**

| **Term**          | **OAuth 2.0**                                      | **SAML 2.0**                                      | **SSO**                          |
|-------------------|----------------------------------------------------|---------------------------------------------------|----------------------------------|
| **Purpose**       | Delegated authorization (access tokens)            | SSO via identity federation                         | Single sign-on across systems    |
| **Mechanism**     | Bearer tokens (JWT, opaque)                        | XML assertions (signed/encrypted)                 | Shared session management        |
| **Common Use Cases** | APIs, web/mobile apps (e.g., Google Auth)        | Enterprise apps (e.g., Microsoft 365)             | Corporate portals                |
| **Flow Types**    | Authorization Code, Client Credentials, etc.       | AuthnRequest/Response, LogoutRequest               | IdP-initiated or SP-initiated    |
| **Security**      | PKCE, OIDC extensions                              | X.509 certificates, SPNego                         | Session cookies, tokens          |
| **Legacy vs Modern** | Modern (JWT OIDC)                               | Legacy (XML-heavy)                               | Hybrid-deployable                |

---

## **3. Schema Reference**

### **3.1 OAuth 2.0 Token Response (JWT/Opaque)**
| Field            | Type      | Description                                                                                     |
|------------------|-----------|-------------------------------------------------------------------------------------------------|
| `access_token`   | String    | Bearer token (JWT or opaque), typically expires in `expires_in`.                               |
| `token_type`     | String    | `Bearer` (default) or `refresh_token` (if returned).                                           |
| `expires_in`     | Integer   | Token lifetime in seconds.                                                                      |
| `refresh_token`  | String    | Optional token for re-acquiring `access_token`; may have longer validity.                      |
| `scope`          | String    | Space-separated list of permissions (e.g., `read write`).                                      |
| `id_token`       | JWT       | Optional OpenID Connect (OIDC) identity token for user claims.                                  |

**Example (JWT Response):**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "tGzv3JOkF0XG5Qx2TlKWIA",
  "scope": "profile email"
}
```

---

### **3.2 SAML 2.0 Assertion (XML)**
```xml
<saml:Assertion xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
                IssueInstant="2023-10-01T12:00:00Z"
                Version="2.0">
  <saml:Conditions NotBefore="2023-10-01T11:50:00Z"
                    NotOnOrAfter="2023-10-01T13:00:00Z">
    <saml:AudienceRestriction>
      <saml:Audience>https://sp.example.com</saml:Audience>
    </saml:AudienceRestriction>
  </saml:Conditions>
  <saml:Subject>
    <saml:NameID Format="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress">
      user@example.com
    </saml:NameID>
  </saml:Subject>
  <saml:AttributeStatement>
    <saml:Attribute Name="http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name">
      <saml:AttributeValue>John Doe</saml:AttributeValue>
    </saml:Attribute>
  </saml:AttributeStatement>
  <ds:Signature xmlns:ds="http://www.w3.org/2000/09/xmldsig#">
    <!-- Key signing metadata -->
  </ds:Signature>
</saml:Assertion>
```

**Key Elements:**
- `Conditions`: Validity window for the assertion.
- `Audience`: Target SP (Service Provider) URI.
- `Subject`: User identity (e.g., `NameID`).
- `AttributeStatement`: Claims (e.g., `name`, `email`).
- `Signature`: XML-DSig validation.

---

### **3.3 SSO Session Token (Cookie/JWT)**
| Field            | Type      | Description                                                                                     |
|------------------|-----------|-------------------------------------------------------------------------------------------------|
| `ssid`           | String    | Session identifier (e.g., cookie or JWT `sid`).                                               |
| `expires`        | ISO8601   | Session validity (e.g., `2023-10-02T12:00:00Z`).                                               |
| `user_id`        | String    | Unique user identifier (e.g., `uid:123`).                                                        |
| `claims`         | Map       | User attributes (e.g., `{"name": "John Doe", "groups": ["admin"]}`).                           |
| `nonce`          | String    | Anti-replay token for web SSO.                                                                 |

**Example (JWT Session Token):**
```json
{
  "ssid": "abc123xyz",
  "expires": "2023-10-02T12:00:00Z",
  "user_id": "uid:123",
  "claims": {
    "name": "John Doe",
    "groups": ["admin"]
  },
  "nonce": "a1b2c3"
}
```

---

## **4. Implementation Patterns**

### **4.1 OAuth 2.0 Flows**
| Flow Name               | Description                                                                                     | Use Case                          |
|-------------------------|-------------------------------------------------------------------------------------------------|-----------------------------------|
| **Authorization Code** | User redirects to `authorization_endpoint`, grants consent, receives `code` → exchanges for `token`. | Web/mobile apps.                  |
| **Implicit**            | Deprecated; replaced by **PKCE** (deprecated due to CSRF risks).                                | Legacy apps (avoid).              |
| **Client Credentials**  | Machine-to-machine auth using `client_id`/`client_secret`.                                     | Backend services.                 |
| **PKCE (Proof Key)**    | Adds `code_challenge`/`code_verifier` to prevent authorization code interception.           | Public clients (e.g., native apps). |
| **Resource Owner Password** | Direct `username`/`password` submission (avoid; low-security).                               | Internal tools (use cautiously). |

**Query Example (Authorization Code Flow):**
```http
# Step 1: Redirect to Authorization Server
GET /oauth/authorize?
  response_type=code&
  client_id=SplxlOBeZQQYbYS6WxSbIA&
  redirect_uri=https://client.example.com/callback&
  scope=read%20write&
  state=random_state

# Step 2: Receive Code (via redirect)
https://client.example.com/callback?
  code=SplxlOBeZQQYbYS6WxSbIA&
  state=random_state

# Step 3: Exchange Code for Token
POST /token
Headers:
  Content-Type: application/x-www-form-urlencoded
Body:
  grant_type=authorization_code&
  code=SplxlOBeZQQYbYS6WxSbIA&
  redirect_uri=https://client.example.com/callback&
  client_id=SplxlOBeZQQYbYS6WxSbIA&
  client_secret=...
```

---

### **4.2 SAML 2.0 Binding**
| Binding         | Transport | Port       | Use Case                          |
|-----------------|-----------|------------|-----------------------------------|
| **HTTP Post**   | Form      | 80/443     | Most common (SP-initiated SSO).    |
| **HTTP Redirect** | URL       | 80/443     | IdP-initiated redirect.           |
| **SOAP**        | XML        | 80/443     | Legacy enterprise integrations.   |
| **Artifact**    | URI encode | 80/443     | Scalable but complex.             |

**Query Example (SP-Initiated SAML):**
```http
# Step 1: SP Sends AuthnRequest to IdP
POST /sso/idp/SSOService
Headers:
  Content-Type: application/x-www-form-urlencoded
Body:
  SAMLResponse=<samlp:AuthnRequest ... />
  RelayState=random_state

# Step 2: IdP Returns SAMLResponse
GET /acs?SAMLResponse=<samlp:Response ...>&RelayState=random_state
```

---

### **4.3 SSO Integration Patterns**
| Pattern                | Description                                                                                     | Tools/Frameworks                     |
|------------------------|-------------------------------------------------------------------------------------------------|--------------------------------------|
| **Identity Provider (IdP)** | Centralized auth service (e.g., Okta, Azure AD).                                           | Okta, Ping Identity, Shibboleth     |
| **Service Provider (SP)** | App consuming SSO (e.g., web app).                                                            | Spring Security SAML, Azure AD FS   |
| **Federated SSO**      | Multiple IdPs (e.g., SAML + OAuth hybrid).                                                     | Keycloak, Auth0                       |
| **Session Management** | Shared session across SP/IdP (e.g., via `ssid` cookie).                                      | CAS, SimpleSAMLphp                    |
| **Conditional Access** | Policy-based access (e.g., MFA, device compliance).                                           | Microsoft Entra ID, Duo Security     |

---

## **5. Security Considerations**
### **OAuth 2.0 Best Practices**
- Use **PKCE** for public clients.
- Enforce **short-lived tokens** (`expires_in` < 1 hour).
- Validate **scope** and **token type**.
- Store `client_secret` securely (not in frontend).

### **SAML 2.0 Best Practices**
- Enforce **X.509 certificate validation**.
- Use **SPNego** for Kerberos integration.
- Restrict `Audience` to trusted SP URIs.
- Sign assertions to prevent tampering.

### **SSO Best Practices**
- **Single logout** (e.g., via SAML `LogoutResponse`).
- **Session timeouts** (e.g., 14 days max).
- **Multi-factor authentication** (MFA) for IdP.
- **Audit logs** for failed SSO attempts.

---

## **6. Troubleshooting Common Issues**

| Issue                          | OAuth 2.0 Fix                                  | SAML 2.0 Fix                                  | SSO Fix                          |
|--------------------------------|-----------------------------------------------|-----------------------------------------------|----------------------------------|
| **401 Unauthorized**           | Check `scope`/`client_secret`.                | Validate `Signature`/`Audience`.               | Verify `ssid` cookie.            |
| **Token Expired**              | Use `refresh_token`.                          | Extend assertion `NotOnOrAfter`.              | Revoke stale sessions.           |
| **CSRF Attacks**               | Use `state` + PKCE.                           | Bind to `RelayState`.                         | Anti-replay tokens.              |
| **Certificate Errors**         | —                                             | Update SP/IdP certs.                          | —                                |
| **Session Stuck**              | Clear browser cache.                          | Reset `SessionIndex` in IdP.                  | Force logout via `/slo`.         |

---

## **7. Related Patterns**
1. **[OpenID Connect (OIDC)]**: Extends OAuth 2.0 with identity claims (e.g., `id_token`).
2. **[JWT Validation]**: Standards for decoding/validating JSON Web Tokens (RFC 7519).
3. **[API Gateway Authentication]**: Centralized auth for microservices (e.g., Kong, Apigee).
4. **[Attribute-Based Access Control (ABAC)]**: Fine-grained permissions via SAML/OAuth attributes.
5. **[Federated Identity]**: Cross-organization SSO (e.g., InCommon, eduGAIN).

---
**References:**
- [OAuth 2.0 RFC 6749](https://datatracker.ietf.org/doc/html/rfc6749)
- [SAML 2.0 Core](https://docs.oasis-open.org/security/saml/v2.0/saml-core-2.0-os.pdf)
- [IETF JWT RFC 7519](https://datatracker.ietf.org/doc/html/rfc7519)