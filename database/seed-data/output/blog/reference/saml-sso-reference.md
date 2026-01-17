# **[Pattern] SAML & Single Sign-On (SSO) Reference Guide**

---

## **Overview**
The **SAML (Security Assertion Markup Language) & Single Sign-On (SSO)** pattern standardizes enterprise authentication by enabling seamless, secure user access across multiple applications using a single set of credentials. SAML defines a XML-based protocol for exchanging authentication and authorization data between an **Identity Provider (IdP)** (e.g., Okta, Azure AD) and a **Service Provider (SP)** (e.g., web apps, SaaS tools). This pattern reduces password fatigue, automates authentication flows, and ensures secure access control via cryptographic signatures and digital certificates.

Key use cases include:
- Cross-domain login (e.g., SSO between internal portals and third-party tools).
- Role-based access control (RBAC) with attribute assertions.
- Compliance with standards like **OAuth 2.0** and **OpenID Connect (OIDC)** for hybrid environments.

---

## **1. Key Concepts**

| **Term**               | **Definition**                                                                                                                                                                                                 |
|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Identity Provider (IdP)** | Centralized authentication service that validates user credentials (e.g., username/password) and issues SAML assertions.                                                                                        |
| **Service Provider (SP)**   | Application or service requesting authentication from the IdP (e.g., a company’s CRM or ERP system).                                                                                                           |
| **SAML Assertion**      | XML document containing authentication/authorization data (e.g., username, session timeouts, attributes like `employee_id`).                                                                                 |
| **Authentication Request** | SP initiates a redirect to the IdP with a `SAMLRequest` (base64-encoded) to start the SSO flow.                                                                                                            |
| **Authentication Response** | IdP sends a signed SAML response back to the SP, confirming user identity and granting access.                                                                                                               |
| **Single Sign-Out (SSO)** | IdP invalidates all sessions across SP apps, typically via a `LogoutRequest`.                                                                                                                                  |
| **Assertion Consumer Service (ACS)** | SP’s endpoint (URL) where the IdP posts SAML responses.                                                                                                                                                   |
| **Security Assertion Markup Language (SAML)** | Open standard for exchanging authentication data between systems (versions: **SAML 1.1**, **SAML 2.0** [recommended]).                                                                              |
| **Metadata**           | XML files describing IdP/SP configurations (e.g., certificate fingerprints, ACS URLs). Used to validate trust relationships.                                                                                     |
| **RelayState**         | URL parameter passed to the IdP to return users to a specific SP page post-login.                                                                                                                             |
| **Attribute Statement** | Optional SAML extension to pass user attributes (e.g., `department`, `role`) from IdP to SP.                                                                                                                  |

---

## **2. SAML Message Flow (SAML 2.0)**
The interaction between IdP and SP follows this sequence:

1. **SP initiates login**:
   - User clicks "Sign In" on SP’s page.
   - SP redirects user to IdP with:
     - `SAMLRequest` (encoded assertion to authenticate user).
     - `ReturnURL` (`RelayState`) to post-login redirect.
     - Example:
       ```http
       GET https://idp.example.com/SSOService?
         SAMLRequest=PHNjcmlwdD58fQ==
         RelayState=https%3A%2F%2Fsp.example.com%2Fdashboard
       ```

2. **IdP authenticates user**:
   - User logs in via the IdP (e.g., enters credentials).
   - IdP validates credentials and generates a **signed SAML response**:
     ```xml
     <s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope">
       <s:Header>
         <saml:AuthenticationStatement
           IssueInstant="2023-10-01T12:00:00Z"
           AuthenticationMethod="urn:oasis:names:tc:SAML:2.0:ac:classes:Password"
           NameIdentifier="jane.doe@example.com">
           <saml:Subject>
             <saml:NameID Format="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress">
               jane.doe@example.com
             </saml:NameID>
           </saml:Subject>
         </saml:AuthenticationStatement>
       </s:Header>
     </s:Envelope>
     ```

3. **IdP redirects to SP**:
   - IdP sends the response to the SP’s `ACS URL` (e.g., via HTTP POST).
   - SP extracts the assertion, verifies the signature, and grants access.

4. **Single Sign-Out (Optional)**:
   - IdP invalidates the SAML session via a `LogoutRequest` to all SPs.
   - Example:
     ```http
     POST https://sp.example.com/SAML2/Logout/SSO
     SAMLRequest=<LogoutRequest xmlns="urn:oasis:names:tc:SAML:2.0:protocol">...</LogoutRequest>
     ```

---

## **3. Schema Reference**
### **SAML Assertion Schema (Simplified)**
| **Element**               | **Description**                                                                 | **Required** | **Example Value**                     |
|---------------------------|---------------------------------------------------------------------------------|--------------|----------------------------------------|
| `<saml:AuthenticationStatement>` | Asserts user identity and authentication method.                               | Yes          | `urn:oasis:names:tc:SAML:2.0:ac:classes:Password` |
| `<saml:NameIdentifier>`    | Unique identifier for the user (e.g., email, UUID).                           | Yes          | `jane.doe@example.com`                 |
| `<saml:Conditions>`       | Defines validity period of the assertion.                                       | Optional     | `NotBefore="2023-10-01T11:30:00Z"`     |
| `<saml:Attribute>`        | Custom attributes (e.g., `employee_id`, `department`).                         | Optional     | `<saml:Attribute Name="department">Engineering</saml:Attribute>` |
| `<ds:Signature>`          | XML-DSig signature to verify IdP authenticity (using IdP’s private key).      | Yes          | Base64-encoded signature value         |

---

## **4. Query Examples**
### **SP Initiates SAML Request (URL Encoding)**
```http
GET https://idp.example.com/SSOService?
  SAMLRequest=PHNjcmlwdD58fQ==  # Base64-encoded XML payload
  &RelayState=https://sp.example.com%2Fcallback
  &RequestID=_e3a1354f0cc545848a1522f2765076f4
```

**SAMLRequest payload (decoded):**
```xml
<samlp:AuthnRequest
  xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
  IssueInstant="2023-10-01T12:00:00Z"
  ID="_e3a1354f0cc545848a1522f2765076f4"
  Version="2.0"
  ProviderName="SP Example">
  <saml:Issuer>https://sp.example.com/saml/metadata</saml:Issuer>
  <samlp:AssertionConsumerService
    Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
    Location="https://sp.example.com/acs" />
</samlp:AuthnRequest>
```

---

### **IdP Returns SAML Response**
```http
POST https://sp.example.com/acs
Host: sp.example.com
Content-Type: application/x-www-form-urlencoded

SAMLResponse=PHNjcmlwdD58fQ==  # Base64-encoded response
RelayState=https%3A%2F%2Fsp.example.com%2Fcallback
```

**SAMLResponse payload (decoded):**
```xml
<samlp:Response
  xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
  ID="_abc123"
  IssueInstant="2023-10-01T12:05:00Z"
  Version="2.0"
  Destination="https://sp.example.com/acs">
  <saml:Issuer>https://idp.example.com/saml/metadata</saml:Issuer>
  <ds:Signature>...</ds:Signature>  <!-- Base64-encoded -->
  <saml:AuthnStatement
    AuthnInstant="2023-10-01T12:00:00Z"
    SessionIndex="_sess123">
    <saml:Subject>
      <saml:NameID Format="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress">
        jane.doe@example.com
      </saml:NameID>
    </saml:Subject>
  </saml:AuthnStatement>
</samlp:Response>
```

---

## **5. Implementation Steps**
### **Step 1: Configure IdP & SP**
1. **Generate Metadata**:
   - IdP: Export SP metadata (e.g., `sp-metadata.xml`).
     ```xml
     <md:EntityDescriptor entityID="https://sp.example.com/metadata">
       <md:SPSSODescriptor AuthnRequestsSigned="true" WantAssertionsSigned="true">
         <md:KeyDescriptor use="signing">
           <ds:KeyInfo>
             <ds:X509Data><ds:X509Certificate>...</ds:X509Certificate></ds:KeyInfo>
         </md:KeyDescriptor>
         <md:AssertionConsumerService
           Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
           Location="https://sp.example.com/acs" />
       </md:SPSSODescriptor>
     </md:EntityDescriptor>
     ```
   - SP: Import IdP metadata to trust its certificates.

2. **Configure SP**:
   - Set `ACS URL` (e.g., `https://sp.example.com/acs`).
   - Configure `EntityID` (unique identifier for SP).
   - Enable **signature validation** for assertions/responses.

### **Step 2: Handle SAML Requests/Responses**
- **SP-side (e.g., Python with `python3-saml`)**:
  ```python
  from saml2 import BINDING_HTTP_REDIRECT, BINDING_HTTP_POST

  # Configure metadata
  metadata = {
      'entityId': 'https://sp.example.com/metadata',
      'service': {
          'sp': {
              'name': 'SP Example',
              'acs_url': 'https://sp.example.com/acs',
              'binding': BINDING_HTTP_POST,
          }
      }
  }
  metadata['idp'] = ...  # Load IdP metadata

  # Handle incoming SAML requests
  def acs_handler(request):
      binding = BINDING_HTTP_POST
      authn_response = request.POST.get('SAMLResponse')
      if not authn_response:
          return "No SAMLResponse found"
      # Decode and validate response
      response = saml2.process_response(binding, authn_response, metadata)
      user = response.get('attributes').get('nameid')
      return f"Welcome, {user}!"
  ```

### **Step 3: Test & Debug**
- **Validate Metadata**:
  Use tools like [SAML Tracer](https://ssoassertiontester.azurewebsites.net/) to inspect flows.
- **Check Logs**:
  Ensure IdP/SP logs include:
  - SAML request/response timestamps.
  - Signature validation errors (e.g., `ds:SignatureValidationFailed`).

---

## **6. Security Best Practices**
| **Practice**                          | **Description**                                                                                     |
|----------------------------------------|----------------------------------------------------------------------------------------------------|
| **Use HTTPS**                          | Prevent man-in-the-middle attacks during SAML message exchanges.                                       |
| **Sign Assertions/Requests**           | Recommended: `AuthnRequestsSigned="true"` and `WantAssertionsSigned="true"` in SP metadata.         |
| **Certificate Management**             | Rotate IdP/SP certificates regularly. Use **OCSP stapling** for fresh certificate status.              |
| **Session Timeout**                    | Set short-lived SAML assertions (e.g., `NotOnOrAfter` within 1 hour).                                |
| **Attribute Filtering**                | Only expose required attributes (e.g., `email` instead of `PII`).                                     |
| **CSRF Protection**                    | Use `RelayState` and `NameIDPolicy` to bind user sessions to SP.                                      |
| **Audit Logs**                         | Track failed authentications (e.g., invalid signatures, expired sessions).                            |

---

## **7. Common Pitfalls & Fixes**
| **Issue**                          | **Root Cause**                          | **Solution**                                                                 |
|-------------------------------------|----------------------------------------|------------------------------------------------------------------------------|
| **Signature Validation Failure**    | IdP/SP public key mismatch.             | Re-import metadata or regenerate certificates.                                |
| **NameID Format Mismatch**          | IdP sends `Format="urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified"` but SP expects `emailAddress`. | Configure `NameIDPolicy` in SP metadata.                                     |
| **Session Expiry**                  | SAML assertions expire too quickly.     | Extend `NotOnOrAfter` in IdP configuration or implement session relay.       |
| **RelayState Injection**            | SP redirects users to malicious URLs.   | Validate `RelayState` against allowed SP URLs.                               |
| **Attribute Not Found**             | SP requests attributes not provided by IdP. | Configure IdP to include required attributes (e.g., `department`).             |

---

## **8. Related Patterns**
| **Pattern**               | **Description**                                                                                     | **When to Use**                                                                 |
|---------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **[OAuth 2.0 & OpenID Connect]** | Token-based authentication with JWTs for APIs and web apps.                                          | When integrating with mobile apps or REST APIs (SAML is SP-agnostic).           |
| **[JWT (JSON Web Tokens)]** | Stateless authentication with encrypted claims.                                                     | For microservices or APIs where SAML’s XML overhead is undesirable.              |
| **[API Gateway SSO]**      | Centralized SSO proxy for multiple backends (e.g., Kong, Apigee).                                   | To consolidate authentication across heterogeneous services.                     |
| **[Multi-Factor Authentication (MFA)]** | Extend SAML with TOTP/HOTP or hardware tokens (e.g., YubiKey).                                     | For high-security environments (e.g., finance, healthcare).                     |
| **[Federated Identity]** | Combine SAML with other standards (e.g., OAuth for user provisioning).                               | In hybrid cloud environments (e.g., on-prem + cloud IdPs).                      |

---

## **9. Tools & Libraries**
| **Category**       | **Tools/Libraries**                                                                                     | **Language**       |
|--------------------|--------------------------------------------------------------------------------------------------------|--------------------|
| **IdP**           | Okta, Azure AD, Ping Identity, Keycloak                                                      | Server-side        |
| **SP SDKs**       | `python3-saml`, `ruby-saml`, `spring-security-saml` (Java), `dotnet-saml`                              | Python, Ruby, Java |
| **Metadata Tools**| `samltrace`, OpenSAML, [SAML Tracer](https://ssoassertiontester.azurewebsites.net/)               | CLI/Web            |
| **Debugging**     | Wireshark (filter for `SAMLRequest`), Postman (for manual testing)                                   | Network/HTTP       |

---
**References:**
- [SAML 2.0 Core Specification](https://docs.oasis-open.org/security/saml/v2.0/saml-core-2.0-os.pdf)
- [OAuth 2.0 & OpenID Connect](https://openid.net/specs/openid-connect-core-1_0.html)