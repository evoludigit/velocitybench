# **[Pattern] Authentication Standards Reference Guide**

---

## **Overview**
The **Authentication Standards** pattern defines a structured, interoperable framework for secure user authentication across distributed systems. It ensures consistent identity verification while supporting scalability, compliance (e.g., GDPR, OAuth, OpenID), and extensibility for emerging protocols (e.g., FIDO2, biometrics). This guide outlines key standards, implementation rules, and best practices to integrate authentication flows effectively into modern architectures.

---

## **Schema Reference**
| **Standard**          | **Purpose**                                                                 | **Key Attributes**                                                                 | **Common Use Cases**                          | **Version** |
|-----------------------|-----------------------------------------------------------------------------|------------------------------------------------------------------------------------|-----------------------------------------------|-------------|
| **OAuth 2.0**         | Delegated authorization between clients (e.g., apps) and authorization servers. | `client_id`, `client_secret`, `scope`, `redirect_uri`, `access_token` (JWT).         | Third-party logins (e.g., Google, GitHub).    | 2.1         |
| **OpenID Connect (OIDC)** | Extends OAuth to provide user identity (ID tokens) and authentication.       | `id_token` (JWT), `nonce`, `state` (CSRF protection), `userinfo` endpoint.           | Single Sign-On (SSO) via OAuth providers.     | 1.0         |
| **SAML 2.0**          | XML-based SSO for enterprise environments (e.g., Active Directory).         | `Assertion`, `NameID`, `SessionIndex`, `SigningCertificates`.                      | Legacy enterprise integrations.              | 2.0         |
| **FIDO2/WebAuthn**    | Passwordless authentication using public-key cryptography (biometrics/hardware keys). | `authenticatorSelection`, `publicKeyCredential`, `attestation` data.              | High-security applications (e.g., banking).   | 2.0         |
| **LDAP**              | Directory-based authentication (e.g., Windows Active Directory).            | `bindDN`, `bindPassword`, `searchFilter` (e.g., `(&(objectClass=user)(uid={username}))`). | On-premises authentication.                  | 3.0         |
| **JWT (JSON Web Tokens)** | Stateless tokens for stateless authentication/authorization.              | `header` (alg: `HS256`, typ: `JWT`), `payload` (iss, sub, exp, claims), `signature`. | REST APIs, microservices.                     | 1.1         |
| **SCIM 2.0**          | Standardized user provisioning/deprovisioning (complements auth).          | `Schema`, `User` objects (e.g., `urn:ietf:params:scim:schemas:core:2.0:User`).     | HR/IT systems.                                | 2.0         |

---
**Notes:**
- **OAuth 2.0/OIDC**: Prefer short-lived `access_tokens` and encrypted `id_tokens`.
- **FIDO2**: Requires browser/OS support; fallback to traditional auth if unavailable.
- **LDAP**: Use TLS for bindings to prevent MITM attacks.
- **JWT**: Store `secret` keys securely (e.g., AWS KMS, HashiCorp Vault).

---

## **Implementation Details**
### **1. Core Components**
| **Component**       | **Description**                                                                                                                                                                                                 |
|---------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Relying Party (RP)** | Client app (web/mobile) that initiates/authenticates users.                                                                                                                                             |
| **Authorization Server (AS)** | Issues tokens (OAuth/OIDC) or validates credentials (LDAP).                                                                                                                                              |
| **Identity Provider (IdP)**   | External service (e.g., Okta, Auth0) managing user identities for SSO.                                                                                                                                  |
| **Resource Server**         | API/endpoint protected by tokens (e.g., `access_token` in OAuth).                                                                                                                                           |
| **Token Store**            | Secure storage for tokens (e.g., Redis, database) if short-lived tokens aren’t self-contained (e.g., JWT).                                                                                                 |

---
### **2. Flow Examples**
#### **OAuth 2.0 Authorization Code Flow (Recommended)**
1. **RP** redirects user to **AS**:
   ```
   GET /authorize?
     response_type=code&
     client_id=ABC123&
     redirect_uri=https://app.example/callback&
     scope=openid%20profile%20email&
     state=xyz789
   ```
2. **AS** prompts user for consent; redirects to `redirect_uri` with `code`:
   ```
   GET https://app.example/callback?
     code=AUTH_CODE_123&
     state=xyz789
   ```
3. **RP** exchanges `code` for `access_token`/`id_token`:
   ```http
   POST /token
   Content-Type: application/x-www-form-urlencoded
   body:
     grant_type=authorization_code&
     code=AUTH_CODE_123&
     redirect_uri=https://app.example/callback&
     client_id=ABC123&
     client_secret=XYZ456
   ```
   **Response**:
   ```json
   {
     "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6...",
     "id_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6...",
     "token_type": "Bearer",
     "expires_in": 3600
   }
   ```

---
#### **FIDO2 WebAuthn Flow**
1. **RP** challenges user to authenticate:
   ```javascript
   const challenge = await window.crypto.subtle.generateRandom(32);
   const authOptions = {
     challenge: Array.from(new Uint8Array(challenge)),
     rpId: "example.com",
     userVerification: "preferred"
   };
   const credential = await navigator.credentials.get({
     publicKey: authOptions
   });
   ```
2. **Server** validates `authenticatorResponse` (attestation/assertion) and issues a session.

---
#### **LDAP Bind Example**
```python
from ldap3 import Server, Connection, SUBTREE

server = Server('ldap.example.com', get_info=ALL, use_ssl=True)
conn = Connection(server, user='CN=admin', password='secret', auto_bind=True)
conn.search('DC=example,DC=com', '(objectClass=user)', attributes=['cn', 'mail'])
```

---
### **3. Security Considerations**
- **Token Expiry**: Set `exp` claim in JWT/OAuth tokens (e.g., 1 hour for `access_token`).
- **CSRF Protection**: Use `state` parameter (OAuth/OIDC) or `SameSite` cookies.
- **Rate Limiting**: Throttle `/authorize` and `/token` endpoints to prevent brute-force attacks.
- **Token Revocation**: Implement short-lived tokens + refresh tokens (OAuth) or token blacklisting.
- **Phishing Resistance**: Enforce **User Verification** (FIDO2) or **Proof-of-Possession** (OAuth PKCE).

---

## **Query Examples**
### **1. Validate a JWT (Node.js)**
```javascript
const jwt = require('jsonwebtoken');
const token = req.headers.authorization.split(' ')[1];
try {
  const decoded = jwt.verify(token, 'your-secret-key');
  return decoded; // { sub: 'user123', exp: 1234567890 }
} catch (err) {
  throw new Error('Invalid token');
}
```

### **2. OIDC User Info Endpoint**
```http
GET https://idp.example/userinfo
Authorization: Bearer eyJhbGciOiJSUzI1NiIs...
Accept: application/json
```
**Response**:
```json
{
  "sub": "1234567890",
  "name": "Jane Doe",
  "email": "jane@example.com",
  "iss": "https://idp.example",
  "iat": 1516239022,
  "exp": 1516242622
}
```

### **3. FIDO2 Assertion Validation (Python)**
```python
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import padding, ec

public_key = ec.EllipticCurvePublicKey.from_encoded_point(
    ec.SECP256R1(),
    bytes.fromhex("04...")  # User's public key from registration
)
signature = bytes.fromhex("30440220...")  # user's signature from assertion
data_to_verify = bytes.fromhex("A1B2...")
public_key.verify(
    signature,
    data_to_verify,
    ec.ECDSA(hashes.SHA256()),
    default_backend()
)
```

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                                                                                                                                                 | **When to Use**                                                                                                                                                     |
|---------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **[Identity Federation](#)** | Leverages standards like SAML/OIDC to share user identities across domains.                                                                                                                            | Multi-tenant SaaS apps or enterprise SSO.                                                                                                                      |
| **[Token-Based Authorization](#)** | Uses JWT/OAuth scopes to enforce fine-grained permissions.                                                                                                                                              | Secure APIs with role-based access control (RBAC).                                                                                                               |
| **[Multi-Factor Authentication (MFA)](#)** | Combines passwords + TOTP/SMS/biometrics for higher security.                                                                                                                                           | High-risk applications (e.g., banking).                                                                                                                   |
| **[Session Management](#)** | Maintains user sessions via cookies or tokens with expiration/refresh logic.                                                                                                                       | Traditional web apps (cookies) or stateless APIs (tokens).                                                                                                    |
| **[Identity Provisioning (SCIM)](#)** | Automates user lifecycle (create/update/delete) via SCIM API.                                                                                                                                         | HR systems or automated onboarding.                                                                                                                       |

---
**Key Integrations:**
- **Auth Providers**: Okta, Auth0, Azure AD (OIDC/OAuth).
- **API Gateways**: Kong, Apigee (token validation proxies).
- **Databases**: PostgreSQL (JWT storage), MongoDB (user profiles via SCIM).

---
**Further Reading:**
- [OAuth 2.0 RFC 6749](https://tools.ietf.org/html/rfc6749)
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)
- [FIDO2 Technical Overview](https://fidoalliance.org/specs/fido-v2.0-ps-20190130/fido-client-to-authenticator-protocol-v2.0-ps-20190130.html)