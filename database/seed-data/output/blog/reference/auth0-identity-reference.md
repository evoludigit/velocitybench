---
# **[Pattern] Auth0 Identity Integration Patterns – Reference Guide**

---

## **1. Overview**
Auth0’s **Identity Integration Patterns** provide structured approaches to integrating third-party identity providers, authentication flows, and authorization systems with Auth0. This guide covers **implementation details**, **best practices**, and **common pitfalls** across common patterns, including:
- **Social Login (OAuth 2.0/OpenID Connect)**
- **Enterprise Identity (SAML 2.0, WS-Fed)**
- **Multi-Factor Authentication (MFA)**
- **Role-Based Access Control (RBAC)**
- **Delegated Authentication (IdP-Initiated Login)**

Each pattern ensures secure, scalable, and maintainable authentication workflows while aligning with **OAuth 2.0**, **OpenID Connect**, and **Auth0’s Core Identity APIs**.

---

## **2. Schema Reference**
Below are key integration **data schemas** for common Auth0 Identity Integration Patterns.

### **2.1 Social Login (OAuth 2.0/OpenID Connect)**
| **Field**               | **Type**       | **Description**                                                                 | **Example**                              | **Required?** |
|--------------------------|---------------|-------------------------------------------------------------------------------|------------------------------------------|----------------|
| `connection`            | `String`      | Auth0’s predefined connection (e.g., `google-oauth2`, `facebook`).           | `"google-oauth2"`                        | Yes            |
| `client_id`             | `String`      | OAuth client ID from the third-party provider.                               | `"5555555555555555555"`                  | Yes            |
| `client_secret`         | `String`      | OAuth client secret (use **Auth0 as the confidential client**).                | *(Hidden in config)*                     | No (if Auth0 is confidential client) |
| `redirect_uri`          | `String`      | Callback URL for the OAuth flow (must match Auth0’s configured URIs).         | `"https://yourdomain.com/callback"`      | Yes            |
| `scope`                 | `String[]`    | OAuth scopes (e.g., `openid`, `profile`, `email`).                           | `["openid", "profile", "email"]`        | Yes            |
| `id_token_signed_alg`   | `String`      | JWS algorithm for ID tokens (default: `RS256`).                              | `"RS256"`                                | No             |
| `mfa_level`             | `String`      | Enforced MFA level (e.g., `passwordless`, `sms`).                            | `"sms"`                                  | No             |

---
### **2.2 Enterprise Identity (SAML 2.0)**
| **Field**               | **Type**       | **Description**                                                                 | **Example**                              | **Required?** |
|--------------------------|---------------|-------------------------------------------------------------------------------|------------------------------------------|----------------|
| `issuer`                | `String`      | SAML Identity Provider (IdP) entity ID.                                        | `"https://sso.company.com/saml"`         | Yes            |
| `acs_url`               | `String`      | Assertion Consumer Service (ACS) URL (Auth0’s SAML endpoint).                  | `"https://yourdomain.auth0.com/samlp/acs"` | Yes            |
| `signing_cert`          | `String`      | IdP’s X.509 signing certificate (PEM format).                                 | *(Base64-encoded cert)*                  | Yes            |
| `audience`              | `String`      | Expected SP entity ID (Auth0’s SAML endpoint).                               | `"https://yourdomain.auth0.com/samlp/sp"` | Yes            |
| `email_attribute`       | `String`      | SAML attribute mapping for user email (e.g., `EmailAddress`).                 | `"EmailAddress"`                         | Yes            |
| `name_id_format`        | `String`      | SAML NameID format (e.g., `urn:oasis:names:tc:SAML:1.1:nameid-format:email`).| `"urn:oasis:names:tc:SAML:1.1:nameid-format:email"` | No            |

---
### **2.3 Multi-Factor Authentication (MFA)**
| **Field**               | **Type**       | **Description**                                                                 | **Example**                              | **Required?** |
|--------------------------|---------------|-------------------------------------------------------------------------------|------------------------------------------|----------------|
| `strategy`              | `String`      | MFA method (`totp`, `sms`, `email`, `webauthn`).                              | `"sms"`                                  | Yes            |
| `provider`              | `String`      | Auth0 MFA provider (e.g., `auth0`).                                           | `"auth0"`                                | Yes            |
| `sms_signature`         | `String`      | SMS message prefix (e.g., `"Your Auth0 Code"`).                              | `"Your Auth0 Code: {code}"`              | No             |
| `email_subject`         | `String`      | Email MFA subject line.                                                       | `"Your Auth0 Verification Code"`         | No             |
| `webauthn_rp_id`        | `String`      | WebAuthn Relying Party ID (for FIDO2).                                        | `"yourdomain.com"`                       | No (if WebAuthn enabled) |

---
### **2.4 Role-Based Access Control (RBAC)**
| **Field**               | **Type**       | **Description**                                                                 | **Example**                              | **Required?** |
|--------------------------|---------------|-------------------------------------------------------------------------------|------------------------------------------|----------------|
| `role_mapping`          | `JsonObject`  | Mapping of SAML attributes to Auth0 roles (e.g., `{"attribute":"groups", "prefix":"GROUP_"}`). | `{"Email": "user@email.com", "groups": ["admin", "editor"]}` | No (if manual role assignment) |
| `role_prefix`           | `String`      | Prefix for dynamically assigned roles.                                       | `"GROUP_"`                               | No             |
| `pipeline`              | `String[]`    | Custom Auth0 pipeline steps (e.g., `assign-role`).                            | `["assign-role", "audit-log"]`           | No             |

---
### **2.5 Delegated Authentication (IdP-Initiated Login)**
| **Field**               | **Type**       | **Description**                                                                 | **Example**                              | **Required?** |
|--------------------------|---------------|-------------------------------------------------------------------------------|------------------------------------------|----------------|
| `sp_entity_id`          | `String`      | Service Provider (SP) entity ID (Auth0’s endpoint).                          | `"https://yourdomain.auth0.com/samlp/sp"` | Yes            |
| `acs_url`               | `String`      | IdP’s Assertion Consumer Service URL.                                         | `"https://yourdomain.com/saml/acs"`      | Yes            |
| `signing_cert`          | `String`      | Auth0’s SAML signing certificate (PEM format).                                | *(Base64-encoded cert)*                  | Yes            |
| `start_url`             | `String`      | Post-Authentication redirect URL.                                             | `"https://yourdomain.com/dashboard"`     | No             |

---

## **3. Query Examples**
Below are **API, SDK, and configuration** examples for common patterns.

---

### **3.1 Social Login (OAuth 2.0)**
#### **Auth0 Dashboard Configuration (JSON)**
```json
{
  "connections": [
    {
      "strategy": "oauth2",
      "name": "Google",
      "enabled_clients": ["your_app_client"],
      "options": {
        "client_id": "5555555555555555555",
        "client_secret": "hidden",
        "scope": "openid profile email",
        "redirect_uri": "https://yourdomain.com/callback"
      }
    }
  ]
}
```

#### **Code (Node.js SDK)**
```javascript
const auth0 = require('auth0');

const client = new auth0.Auth0Client({
  domain: 'yourdomain.auth0.com',
  clientId: 'your_app_client',
  clientSecret: 'your_secret',
});

async function loginWithGoogle() {
  const authUrl = client.buildAuthorizeUrl({
    connection: 'google-oauth2',
    scope: ['openid', 'profile', 'email'],
    redirectUri: 'https://yourdomain.com/callback',
  });
  return authUrl;
}
```

---

### **3.2 SAML 2.0 (Enterprise Identity)**
#### **Auth0 Dashboard SAML Configuration**
| **Setting**            | **Value**                                      |
|------------------------|------------------------------------------------|
| **Issuer**             | `https://sso.company.com/saml`                 |
| **ACS URL**            | `https://yourdomain.auth0.com/samlp/acs`      |
| **Signing Certificate**| *(Upload PEM file)*                            |
| **Audience**           | `https://yourdomain.auth0.com/samlp/sp`       |
| **Email Attribute**    | `EmailAddress`                                 |

#### **Code (Python SDK)**
```python
from auth0_v3 import Auth0Client

client = Auth0Client(
  domain='yourdomain.auth0.com',
  client_id='your_app_client',
  client_secret='your_secret',
)

# Test SAML metadata endpoint
metadata = client.get_saml_metadata()
print(metadata)
```

---

### **3.3 MFA Configuration**
#### **Auth0 Dashboard MFA Rules**
1. Navigate to **Authentication > Advanced > MFA & WebAuthn**.
2. Enable **SMS/Email/TOTP/WebAuthn**.
3. Configure:
   - **SMS Signature**: `"Your Auth0 Code: {code}"`
   - **Email Subject**: `"Auth0 Verification Required"`

#### **Code (Enforce MFA via Rules)**
```javascript
// Auth0 Rule to enforce MFA for admins
function (user, context, callback) {
  if (user.app_metadata && user.app_metadata.role === "admin") {
    context.mfa.enabled = true;
  }
  callback(null, user, context);
}
```

---

### **3.4 RBAC with Role Assignment**
#### **Auth0 Dashboard Role Mapping**
1. Go to **Users & Roles > Roles**.
2. Create roles (`admin`, `editor`).
3. Use **Rules or Actions** to assign dynamically:
   - **Rule Example**:
     ```javascript
     // Assign role based on SAML attribute
     if (context.saml && context.saml.attributes.groups.includes("admin")) {
       user.assign_roles('admin');
     }
     ```

#### **API Call (Assign Role)**
```bash
curl --location 'https://yourdomain.auth0.com/api/v2/users/{user_id}/roles' \
--header 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
--header 'Content-Type: application/json' \
--data '[
  {
    "role_id": "urn:auth0:role:admin"
  }
]'
```

---

### **3.5 IdP-Initiated Login (SAML)**
#### **IdP Configuration (XML Snippet)**
```xml
<samlp:AuthnRequest
  xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
  Version="2.0"
  IssueInstant="2023-10-01T12:00:00Z"
  ID="_7d3f1c8f-4d6e-4366-90d2-6d669d9336b3"
  Destiny="https://yourdomain.auth0.com/samlp/sp">
  <saml:Issuer xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion">
    https://sso.company.com/saml
  </saml:Issuer>
</samlp:AuthnRequest>
```

#### **Auth0 SP Configuration**
| **Setting**            | **Value**                                      |
|------------------------|------------------------------------------------|
| **Entity ID**          | `https://yourdomain.auth0.com/samlp/sp`       |
| **ACS URL**            | `https://yourdomain.auth0.com/samlp/acs`      |
| **Signing Certificate**| *(Auth0’s cert)*                              |

---

## **4. Related Patterns**
| **Pattern**                          | **Description**                                                                 | **Reference**                          |
|--------------------------------------|-------------------------------------------------------------------------------|----------------------------------------|
| **[Auth0 Universal Login]**          | Customizable login pages with Auth0’s hosted UI.                               | [Auth0 Docs](https://auth0.com/docs)    |
| **[Token Exchanges (OIDC)]**         | Use short-lived tokens for API access via token introspection.                | [Token Exchange Guide](https://auth0.com/docs) |
| **[Custom Domains & Branding]**      | Brand Auth0’s Universal Login with custom CSS/HTML.                           | [Branding Guide](https://auth0.com/docs) |
| **[Auth0 Actions]**                  | Serverless logic for pre/post-authentication (replaces Rules).               | [Actions Docs](https://auth0.com/docs)  |
| **[OAuth 2.0 Device Flow]**         | Authenticate via QR code (e.g., for IoT devices).                             | [Device Flow Guide](https://auth0.com/docs) |

---

## **5. Common Pitfalls & Mitigations**
| **Pitfall**                          | **Cause**                                      | **Mitigation**                          |
|--------------------------------------|------------------------------------------------|------------------------------------------|
| **OAuth Redirect Mismatch**          | Incorrect `redirect_uri` in OAuth config.       | Always validate `redirect_uri` in Auth0 Dashboard. |
| **SAML Certificate Expiry**          | IdP/SP certs not updated.                     | Monitor certs via `https://yourdomain.auth0.com/samlp/metadata`. |
| **Token Leakage (JWT)**              | `access_token` exposed in logs.                | Use short-lived tokens + refresh tokens. |
| **MFA Bypass**                       | Admin bypasses MFA via debug mode.             | Require MFA for all roles; audit logs.    |
| **RBAC Over-Permission**             | Roles assigned too broadly.                   | Scope roles to least privilege (e.g., `admin:read`, `admin:write`). |

---

## **6. Best Practices**
1. **Use Auth0 as the Confidential Client** for OAuth 2.0 to avoid exposing `client_secret`.
2. **Enable `id_token_signed_alg` Validation** to prevent token forgery (e.g., `RS256`).
3. **Leverage Auth0 Actions** instead of Rules for serverless logic.
4. **Monitor SAML Certificates** via `metadata` endpoint to avoid failures.
5. **Enforce MFA for Admins** and high-risk users.
6. **Rotate Secrets Regularly** (e.g., `client_secret` every 90 days).
7. **Use Auth0’s Universal Login** for consistent UX across all connectors.

---
**For further reading, see:**
- [Auth0 OAuth 2.0 Documentation](https://auth0.com/docs/get-started/tutorials-and-examples/oauth-oauth2)
- [SAML 2.0 Integration Guide](https://auth0.com/docs/get-started/tutorials-and-examples/saml)
- [Auth0 Actions Developer Guide](https://auth0.com/docs/actions)