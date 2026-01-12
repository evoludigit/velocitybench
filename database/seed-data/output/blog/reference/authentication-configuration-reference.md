**[Pattern] Authentication Configuration Reference Guide**

---

### **1. Overview**
The **Authentication Configuration** pattern standardizes how authentication is defined, managed, and enforced across services. It centralizes authentication logic in a structured, reusable configuration, supporting multiple providers (OAuth, JWT, API keys, etc.) while ensuring security, scalability, and consistency. This pattern is used in microservices, cloud-native applications, and API gateways to enforce fine-grained access control without hardcoding credentials.

---

### **2. Key Concepts**
#### **Core Components**
| Component               | Description                                                                                     |
|-------------------------|-------------------------------------------------------------------------------------------------|
| **Auth Provider**       | Source of authentication data (e.g., OAuth 2.0, LDAP, SAML, JWT).                              |
| **Auth Strategy**       | Defines how authentication is validated (e.g., `Bearer Token`, `Basic Auth`, `API Key`).       |
| **Scopes/Roles**        | Granular permissions tied to users/services.                                                   |
| **Configuration**       | JSON/YAML schema defining provider settings, validation rules, and fallback logic.            |
| **Middleware**          | Runtime enforcement of auth rules (e.g., Express.js middleware, Spring Security filters).      |
| **Cache Layer**         | Optional: Reduces redundant validation (e.g., Redis for short-lived tokens).                   |

#### **Implementation Principles**
- **Decoupled Config**: Auth logic is separated from business logic via configuration.
- **Provider Agnosticism**: Easily swap providers (e.g., from OAuth to JWT) without code changes.
- **Legacy Compatibility**: Supports both modern (OAuth) and legacy (static API keys) auth methods.
- **Dynamic Validation**: Rules can be updated at runtime without redeployment.

---

### **3. Schema Reference**
Below is the reference schema for authentication configuration (JSON format). Fields marked with `*` are required.

#### **Root Configuration**
```json
{
  "auth": {
    "defaultStrategy": "BearerToken",  // Default auth strategy; see `strategies` below
    "providers": [                      // Array of configured providers
      {
        "id": "auth0",                  // Unique identifier for the provider
        "type": "oauth2",               // Provider type (oauth2, jwt, api_key, ldap, etc.)
        "enabled": true,                // Provider is active
        "metadata": {                   // Provider-specific settings
          "clientId": "xyz123",
          "clientSecret": "****",
          "issuer": "https://auth0.com",
          "audience": ["api.example.com"]
        },
        "validation": {                 // Token/credential validation rules
          "issuer": "https://auth0.com",
          "algorithms": ["RS256"],       // Allowed signing algorithms
          "maxAge": "1h"                 // Token expiry window
        },
        "scopes": [                     // Required scopes for this provider
          { "name": "read:data", "description": "Access to read-only endpoints" }
        ]
      }
    ],
    "strategies": {                    // Reusable auth strategies
      "BearerToken": {
        "header": "Authorization",
        "prefix": "Bearer ",
        "validator": {
          "type": "provider",           // "provider" or "custom"
          "providerId": "auth0"         // References a provider in `providers`
        }
      },
      "ApiKey": {                      // Example of a non-provider strategy
        "header": "X-API-Key",
        "validator": {
          "type": "static",
          "keys": ["key1", "key2"]     // Hardcoded keys (legacy use only)
        }
      }
    },
    "fallback": {                      // Default auth if all else fails
      "enabled": false,
      "strategy": "ApiKey"             // Fallback strategy ID
    }
  }
}
```

#### **Field Descriptions**
| Field               | Type       | Description                                                                                     | Example Values                     |
|---------------------|------------|-------------------------------------------------------------------------------------------------|------------------------------------|
| `defaultStrategy`   | String     | Fallback strategy if no provider-specific strategy matches.                                     | `"BearerToken"`                     |
| `providers`         | Array      | List of configured authentication providers.                                                    | See schema above.                  |
| `providers.id`      | String     | Unique identifier for the provider (e.g., `"auth0"`, `"jwt-local"`).                           | `"auth0"`                          |
| `providers.type`    | String     | Provider type (`oauth2`, `jwt`, `api_key`, `ldap`, `saas`).                                    | `"oauth2"`                         |
| `providers.metadata`| Object     | Provider-specific credentials/endpoints.                                                      | `{"clientId": "xyz"}`              |
| `providers.validation` | Object | Rules to validate tokens/credentials (e.g., issuer, algorithms).                           | `{"algorithms": ["RS256"]}`        |
| `providers.scopes`  | Array      | Scopes required to use this provider.                                                          | `[{ "name": "read" }]`             |
| `strategies`        | Object     | Named strategies for auth validation.                                                         | See schema above.                  |
| `strategies.[id]`   | Object     | Strategy configuration (e.g., header name, validator).                                         | `{"header": "Authorization"}`      |
| `strategy.validator.type` | String | Validator type (`provider`, `custom`, `static`).                                           | `"provider"`                       |
| `fallback`          | Object     | Default auth if all providers fail.                                                          | `{"enabled": true}`                |

---

### **4. Query Examples**
#### **Example 1: Validate a JWT Token (Using Config)**
**Input Request Headers:**
```
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
X-API-Version: 1.0
```

**Config Snippet (Relevant Section):**
```json
"strategies": {
  "BearerToken": {
    "header": "Authorization",
    "prefix": "Bearer ",
    "validator": {
      "type": "provider",
      "providerId": "jwt-local"
    }
  }
},
"providers": [
  {
    "id": "jwt-local",
    "type": "jwt",
    "metadata": {
      "publicKey": "-----BEGIN PUBLIC KEY-----..."
    },
    "validation": {
      "algorithms": ["RS256"],
      "issuer": "example.com"
    }
  }
]
```

**Validation Flow:**
1. Middleware extracts token from `Authorization` header.
2. Strips `Bearer ` prefix and validates JWT using `jwt-local` provider’s public key.
3. Checks issuer (`example.com`) and algorithm (`RS256`).
4. If valid, attaches decoded claims (e.g., `sub`, `scopes`) to the request context.

---

#### **Example 2: OAuth 2.0 Redirection (Using Config)**
**Request:**
```
GET /oauth/authorize?response_type=code&client_id=xyz123&redirect_uri=https://client.com/callback
```

**Config Snippet:**
```json
"providers": [
  {
    "id": "google",
    "type": "oauth2",
    "metadata": {
      "clientId": "xyz123",
      "clientSecret": "****",
      "authUrl": "https://accounts.google.com/o/oauth2/auth",
      "tokenUrl": "https://oauth2.googleapis.com/token",
      "scopes": ["openid", "profile", "email"]
    }
  }
]
```

**Middleware Behavior:**
1. Redirects to Google’s auth URL with configured scopes and `redirect_uri`.
2. On callback, exchanges `code` for a token using `clientId`/`clientSecret`.
3. Validates token and extracts user info (e.g., `email`, `sub`).

---

#### **Example 3: API Key Authentication**
**Request Headers:**
```
X-API-Key: abc123xyz
```

**Config Snippet:**
```json
"strategies": {
  "ApiKey": {
    "header": "X-API-Key",
    "validator": {
      "type": "static",
      "keys": ["abc123xyz", "def456ghi"]
    }
  }
}
```

**Validation Flow:**
1. Middleware reads `X-API-Key` header.
2. Checks against `keys` array (static validation).
3. If `abc123xyz` matches, grants access; otherwise, rejects.

---

### **5. Related Patterns**
| Pattern                          | Description                                                                                     | Integration Points                                |
|----------------------------------|-------------------------------------------------------------------------------------------------|---------------------------------------------------|
| **[Authorization Configuration]** | Defines role-based access control (RBAC) after authentication.                                  | Uses scopes/roles from `providers.scopes`.        |
| **[Rate Limiting]**              | Throttles requests to prevent abuse, often integrated with authentication.                     | Attach `userId` from auth middleware to rate-limit rules. |
| **[Circuit Breaker]**            | Handles provider failures (e.g., OAuth 2.0 downtime).                                         | Fallback to `fallback.strategy`.                 |
| **[Event-Driven Auth]**          | Uses pub/sub (e.g., Kafka) to propagate auth decisions.                                        | Emit `AuthDecision` event after validation.       |
| **[Multi-Tenant Isolation]**      | Isolates authentication per tenant (e.g., subdomains).                                         | Inject `tenantId` from auth claims.               |

---

### **6. Best Practices**
1. **Security**:
   - Never log raw tokens or sensitive metadata.
   - Rotate `clientSecret`s and `apiKey`s regularly.
   - Use short-lived tokens (e.g., 15-minute expiry for OAuth).

2. **Performance**:
   - Cache validated tokens (e.g., Redis) to avoid repeated validation.
   - Batch validate tokens in high-throughput scenarios.

3. **Extensibility**:
   - Use `custom` validators for provider-specific logic (e.g., custom JWT claims).
   - Support dynamic configuration updates (e.g., ConfigMaps in Kubernetes).

4. **Observability**:
   - Log auth events (success/failure) with correlating IDs.
   - Monitor provider latency and failure rates.

---
### **7. Troubleshooting**
| Issue                          | Cause                          | Solution                                      |
|--------------------------------|--------------------------------|-----------------------------------------------|
| **401 Unauthorized**           | Invalid token/scopes.          | Check `validation` rules and provider config. |
| **502 Bad Gateway**            | Provider downtime.             | Use `fallback` strategy.                     |
| **Token Expired**              | `maxAge` too short.            | Extend token expiry or implement refresh tokens. |
| **Missing Scope**              | User lacks required scope.     | Assign scope via provider metadata.           |

---
**See Also:**
- [Auth0 Configuration Schema](https://auth0.com/docs/api/management/v2#!/Configuration/get_config)
- [OpenID Connect Core](https://openid.net/specs/openid-connect-core-1_0.html)