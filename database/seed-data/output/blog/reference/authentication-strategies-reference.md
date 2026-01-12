**[Pattern] Authentication Strategies – Reference Guide**

---
### **Overview**
The **Authentication Strategies** pattern defines frameworks, algorithms, and workflows to securely verify user identities before granting access to resources. Authentication is foundational to security systems, balancing usability, performance, and resilience against attacks. This guide covers key strategies (e.g., OAuth, SAML, JWT), their use cases, implementation steps, and security considerations.

---

### **Key Concepts**
| **Term**               | **Definition**                                                                 | **Purpose**                                                                 |
|------------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Authenticator**      | Mechanism (e.g., password, biometric) used to prove identity.               | Validates user claims before granting access.                              |
| **Authenticator Flow** | Sequence of interactions (e.g., OAuth’s Authorization Code Flow).          | Manages consent and session management.                                    |
| **Federated Identity** | Delegating authentication to third parties (e.g., Google, Facebook).       | Reduces credential management overhead.                                   |
| **Multi-Factor Auth**  | Requiring 2+ verification methods (e.g., password + SMS code).              | Mitigates credential theft risks.                                          |
| **Token-Based Auth**   | Using JWTs or stateless tokens for session handling.                        | Scalable for APIs and distributed systems.                                |

---

### **Implementation Details**

#### **1. Authentication Strategies by Type**
Choose a strategy based on requirements:

| **Strategy**      | **Description**                                                                 | **Use Case**                          | **Security Risks**                     | **Example Tools/Libraries**                     |
|-------------------|-------------------------------------------------------------------------------|---------------------------------------|----------------------------------------|--------------------------------------------------|
| **OAuth 2.0**     | Standard for delegated authorization (e.g., "Log in with Google").         | Web/mobile apps, APIs                | Token leakage, phishing                | Spring Security OAuth, Auth0, Okta              |
| **SAML 2.0**      | XML-based single sign-on (SSO) for enterprises.                              | Enterprise apps, cloud services       | XML parsing vulnerabilities           | OneLogin, Azure AD, Ping Identity               |
| **JWT**           | Stateless tokens with headers/payload/signature (e.g., for APIs).           | Microservices, REST APIs              | Signature forgery, short expiration   | JWT.io, Spring Security JWT, Auth0             |
| **LDAP**          | Directory-based authentication (e.g., Active Directory).                     | On-premises systems                   | Credential stuffing                  | OpenLDAP, Apache Directory Server              |
| **Biometric**     | Fingerprint, facial recognition, or voice authentication.                   | High-security apps, mobile devices    | Spoofing attacks, privacy concerns   | Apple Face ID, Android Biometric API            |
| **MFA**           | Combines multiple verifiers (e.g., TOTP + hardware key).                     | Sensitive data access                 | User friction, device loss            | Duo Security, Google Authenticator              |

---

#### **2. Implementation Workflow**
##### **A. OAuth 2.0 (Authorization Code Flow)**
1. **Redirect to Authorization Endpoint**
   ```http
   GET /authorize?response_type=code&client_id=CLIENT_ID&redirect_uri=REDIRECT_URI&scope=read:user
   ```
2. **User Consents** → **Redirects with Code**
   ```http
   GET /redirect_uri?code=AUTHORIZATION_CODE
   ```
3. **Exchange Code for Token**
   ```http
   POST /token
   Content-Type: application/x-www-form-urlencoded
   grant_type=authorization_code&code=AUTHORIZATION_CODE&redirect_uri=REDIRECT_URI&client_id=CLIENT_ID&client_secret=SECRET
   ```
   **Response:**
   ```json
   {
     "access_token": "ACCESS_TOKEN",
     "refresh_token": "REFRESH_TOKEN",
     "token_type": "Bearer",
     "expires_in": 3600
   }
   ```

##### **B. JWT Stateless Auth**
1. **User Logs In** → Server Issues JWT:
   ```json
   {
     "alg": "HS256",
     "headers": {"kid": "key-1"},
     "payload": {
       "sub": "user123",
       "iat": 1609459200,
       "exp": 1609462800
     },
     "signature": "HMACSHA256(...)"
   }
   ```
2. **Client Stores Token** → Includes in Requests:
   ```http
   GET /protected-resource
   Authorization: Bearer ACCESS_TOKEN
   ```

##### **C. SAML 2.0 Single Sign-On (SSO)**
1. **SP Initiates Login**
   ```xml
   <AuthnRequest xmlns="urn:oasis:names:tc:SAML:2.0:protocol"
                 ID="authreq-123"
                 IssueInstant="2023-10-01T12:00:00Z"
                 Version="2.0">
     <Issuer>https://sp.example.org</Issuer>
     <NameIDPolicy Format="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"/>
   </AuthnRequest>
   ```
2. **IdP Validates → Returns SAML Response**:
   ```xml
   <Response xmlns="urn:oasis:names:tc:SAML:2.0:protocol"
             Destination="https://sp.example.org/acs"
             ID="resp-456"
             IssueInstant="2023-10-01T12:01:00Z"
             Version="2.0">
     <Issuer>https://idp.example.org</Issuer>
     <Assertion>
       <Subject>
         <NameID Format="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress">user@example.com</NameID>
       </Subject>
       <Conditions NotBefore="2023-10-01T12:00:00Z" NotOnOrAfter="2023-10-01T12:30:00Z"/>
     </Assertion>
   </Response>
   ```

---

### **Security Best Practices**
- **Rotate Secrets**: Use short-lived tokens (e.g., JWT expiry < 1 hour).
- **Rate Limiting**: Mitigate brute-force attacks (e.g., 5 failed attempts → lockout).
- **Zero Trust**: Validate identity *and* context (e.g., device health, location).
- **Audit Logs**: Track failed authentications for anomaly detection.
- **Hardware Keys**: Enforce FIDO2/U2F for high-risk actions.

---

### **Query Examples**
#### **1. OAuth Token Introspection**
```http
POST /introspect HTTP/1.1
Host: auth-server.example.com
Content-Type: application/x-www-form-urlencoded

token=ACCESS_TOKEN&client_id=CLIENT_ID&client_secret=SECRET
```
**Response (Valid):**
```json
{ "active": true, "sub": "user123", "scope": "read write" }
```

#### **2. JWT Validation (Python Example)**
```python
import jwt
from jwt.exceptions import InvalidTokenError

try:
    payload = jwt.decode(
        token="USER_TOKEN",
        key="SECRET_KEY",
        algorithms=["HS256"]
    )
    print(f"Valid user: {payload['sub']}")
except InvalidTokenError:
    print("Invalid token")
```

#### **3. SAML Metadata Fetch**
```xml
<!-- Fetch IdP Metadata (e.g., from Azure AD) -->
<md:EntityDescriptor xmlns:md="urn:oasis:names:tc:SAML:metadata:1.0"
                     entityID="urn:federation:MicrosoftOnline">
  <md:IDPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
    <md:SingleSignOnService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
                           Location="https://login.microsoftonline.com/common/saml2"/>
  </md:IDPSSODescriptor>
</md:EntityDescriptor>
```

---

### **Related Patterns**
1. **[Authorization Patterns](link)** – Role-based access control (RBAC), attribute-based access control (ABAC).
2. **[Session Management](link)** – Stateless vs. stateful sessions, token refresh strategies.
3. **[API Gateway Security](link)** – Rate limiting, DDoS protection for auth endpoints.
4. **[Passwordless Auth](link)** – Magic links, WebAuthn for credential-less flows.
5. **[Federated Identity](link)** – Cross-domain identity propagation (e.g., OpenID Connect).

---
**Notes:**
- For **high-security apps**, combine MFA + hardware keys.
- **Mobile apps** favor OAuth + PKCE (Proof Key for Code Exchange) to prevent token hijacking.
- **Legacy systems** may require LDAP or Kerberos; evaluate migration to modern tokens (JWT).

**See Also:**
- RFC 6749 (OAuth 2.0)
- [OAuth 2.0 Authorization Framework](https://datatracker.ietf.org/doc/html/rfc6749)
- [SAML 2.0 Core](https://docs.oasis-open.org/security/saml/v2.0/saml-core-2.0-os.pdf).