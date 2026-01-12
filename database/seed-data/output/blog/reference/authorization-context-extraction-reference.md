**[Pattern] Authorization Context Extraction – Reference Guide**
*Extract and centralize role, claims, and tenant data for consistent authorization decisions.*

---

## **1. Overview**
The **Authorization Context Extraction** pattern standardizes how application components retrieve identity and entitlement data (e.g., roles, scopes, tenant IDs) from disparate sources like **JWT tokens**, **session cookies**, or **database caches**. By normalizing this extraction into a reusable context object, the pattern ensures consistent authorization checks across microservices, APIs, and client applications. This reduces redundant logic, minimizes security risks from inconsistent data access, and simplifies integration with authorization frameworks (e.g., OAuth2, RBAC).

The pattern is typically applied at the **entry point** of an execution pipeline (e.g., API gateway, middleware layer) to populate a structured context before authorization decisions are made. For example:
- Extracting `tenant_id: "acme", roles: ["admin", "billing"]` from a JWT payload.
- Falling back to a session store if the JWT is invalid.
- Validating claims against a claims cache for performance.

---

## **2. Key Concepts**
| **Concept**               | **Definition**                                                                 | **Example**                                  |
|---------------------------|-------------------------------------------------------------------------------|---------------------------------------------|
| **Authorization Context** | Structured object containing user roles, claims, tenant info, and other attributes. | `{ userId: "123", roles: ["editor"], tenant: "prod" }` |
| **Source Types**          | Where context data originates (priority order): JWT, session, database.      | JWT (first), Session (fallback), DB (cached) |
| **Context Provider**      | Service/module responsible for extracting and validating context.            | `AuthorizationContextService`               |
| **Claims Cache**          | In-memory or database store for frequently accessed claims (e.g., role mappings). | Redis cache for `role:userId` lookups        |
| **Fallback Strategy**     | Rules for handling missing/invalid sources (e.g., deny by default).           | Reject if JWT invalid, use session if available. |

---

## **3. Schema Reference**
The **Authorization Context** follows this schema:

| **Field**               | **Type**       | **Required** | **Description**                                                                 | **Example Values**                          |
|-------------------------|----------------|--------------|---------------------------------------------------------------------------------|---------------------------------------------|
| `userId`                | `string`       | Yes          | Unique identifier for the authenticated user.                                | `"xyz456"`                                   |
| `roles`                 | `array<string>`| Yes          | List of user roles (e.g., RBAC roles).                                       | `["admin", "auditor"]`                      |
| `tenantId`              | `string`       | Yes          | Tenant/environment identifier (e.g., "acme", "sandbox").                     | `"acme-prod"`                               |
| `scopes`                | `array<string>`| Optional     | OAuth2 scopes or custom permissions.                                        | `["openid", "profile:read"]`                |
| `claims`                | `object`       | Optional     | Custom claims (e.g., `dept: "finance"`).                                     | `{ "dept": "finance", "cost_center": "NY" }` |
| `isAuthenticated`       | `boolean`      | Yes          | Indicates if the user is authenticated.                                      | `true`                                       |
| `source`                | `enum`         | Optional     | Source of the context (e.g., "jwt", "session").                              | `"jwt"`                                      |
| `expiresAt`             | `timestamp`    | Optional     | When the context (e.g., JWT) expires.                                        | `"2024-05-20T12:00:00Z"`                    |
| `metadata`              | `object`       | Optional     | Additional context-specific data (e.g., IP address, device info).            | `{ "ip": "192.168.1.1", "user_agent": "..." }` |

---

## **4. Implementation Steps**
### **4.1. Define the Context Provider**
Create a service to extract and validate context from sources. Example in **TypeScript**:

```typescript
interface AuthorizationContext {
  userId: string;
  roles: string[];
  tenantId: string;
  // ... (other fields from schema)
}

class ContextProvider {
  private sources: { priority: number; extractor: () => Promise<AuthorizationContext> }[];

  constructor() {
    this.sources = [
      {
        priority: 1,
        extractor: this.extractFromJWT.bind(this),
      },
      {
        priority: 2,
        extractor: this.extractFromSession.bind(this),
      },
    ];
  }

  async extract(): Promise<AuthorizationContext> {
    for (const source of this.sources.sort((a, b) => a.priority - b.priority)) {
      try {
        const context = await source.extractor();
        if (context) return context;
      } catch (error) {
        // Log error, continue to next source.
      }
    }
    throw new Error("No valid authorization context found.");
  }

  private async extractFromJWT(): Promise<AuthorizationContext | null> {
    const token = this.getTokenFromHeader();
    if (!token) return null;
    const decoded = await decodeJWT(token);
    if (decoded.exp < Date.now()) return null; // Expired
    return this.mapToContext(decoded);
  }
}
```

### **4.2. Map Sources to Context**
Convert raw data (e.g., JWT payload, session object) to the `AuthorizationContext` schema. Example:

```typescript
private mapToContext(raw: any): AuthorizationContext {
  return {
    userId: raw.sub || raw.uid,
    roles: raw.roles || [],
    tenantId: raw.tenant || process.env.DEFAULT_TENANT,
    scopes: raw.scopes || [],
    claims: raw.extra || {},
    isAuthenticated: true,
    source: "jwt",
  };
}
```

### **4.3. Cache Claims (Optional)**
For performance, cache roles/claims to avoid repeated database lookups:

```typescript
// Pseudo-code for a Redis-backed cache
const cache = new RedisCache({
  keyPrefix: "auth:roles:",
  ttl: 3600, // 1 hour
});

async function getCachedRoles(userId: string): Promise<string[]> {
  const key = `roles:${userId}`;
  const cached = await cache.get(key);
  if (cached) return cached;
  const roles = await database.getRoles(userId);
  await cache.set(key, roles);
  return roles;
}
```

### **4.4. Initialize Context in Pipeline**
Inject the context into middleware or API route handlers:

```typescript
// Express middleware example
async function authMiddleware(req: Request, res: Response, next: NextFunction) {
  const provider = new ContextProvider();
  req.context = await provider.extract();
  next();
}
```

---

## **5. Query Examples**
### **5.1. Extract from JWT (Node.js)**
```typescript
import jwt from "jsonwebtoken";

const token = req.headers.authorization?.split(" ")[1];
const decoded = jwt.verify(token, "SECRET_KEY") as JwtPayload;

const context = {
  userId: decoded.sub,
  roles: decoded.roles,
  tenantId: decoded.tenant,
};
```

### **5.2. Fallback to Session (PHP)**
```php
// Pseudocode for Laravel session
$session = session()->all();
if (!isset($session['jwt'])) {
    $context = [
        'userId' => $session['user_id'],
        'roles'  => $session['roles'] ?? [],
        'tenantId' => $session['tenant'] ?? null,
    ];
} else {
    $context = json_decode($session['jwt'], true);
}
```

### **5.3. Query Claims Cache (Python)**
```python
from redis import Redis

redis = Redis(host="localhost", port=6379)
cache_key = f"roles:{user_id}"

def get_roles(user_id: str) -> list[str]:
    roles = redis.get(cache_key)
    if roles:
        return roles.decode("utf-8").split(",")
    # Fallback to DB
    roles = database.get_roles(user_id)
    redis.set(cache_key, ",".join(roles))
    return roles
```

---

## **6. Error Handling**
| **Scenario**               | **Handling Strategy**                                                                 | **Example Response**                     |
|----------------------------|---------------------------------------------------------------------------------------|------------------------------------------|
| Invalid JWT                | Return `401 Unauthorized` with no context.                                          | `{ "error": "Unauthorized" }`            |
| Missing tenantId           | Reject or route to default tenant.                                                 | Set `tenantId` to `process.env.DEFAULT_TENANT`. |
| Expired context            | Return `401` or refresh the token (e.g., via `401 With Refresh Token`).         | `{ "error": "Token expired", "refresh_uri": "/refresh" }` |
| Claims validation failure | Log audit event, deny access.                                                        | `{ "error": "Invalid claims" }`           |

---

## **7. Validation Rules**
Example rules to validate the extracted context:

```typescript
function validateContext(ctx: AuthorizationContext): boolean {
  if (!ctx.userId || !ctx.tenantId) return false; // Mandatory fields
  if (!ctx.roles.includes("auditor")) { // Example: Auditors can't perform actions
    throw new Error("User must have 'auditor' role.");
  }
  return true;
}
```

---

## **8. Related Patterns**
| **Pattern**                          | **Description**                                                                                     | **Use Case Example**                                  |
|--------------------------------------|---------------------------------------------------------------------------------------------------|------------------------------------------------------|
| **Attribute-Based Access Control (ABAC)** | Extends context with policies beyond roles (e.g., `cost_center: "NY"`).                           | "Only allow users in `cost_center:NY` to edit NY data." |
| **Token Introspection**              | Validates JWTs against an introspection endpoint (OAuth2).                                           | Verify JWT against `https://auth.acme.com/introspect`. |
| **Permission as Code**              | Stores permissions in code/config instead of claims (e.g., `PERMISSIONS = { editor: ["view"] }`).  | Decouple permissions from user attributes.            |
| **Dynamic Tenant Routing**           | Routes requests based on `tenantId` in the context.                                                | `/api/v1/orders?tenant=acme` → Tenant-specific DB.    |
| **Authorization Decorators (Microservices)** | Injects context into gRPC/RPC calls for downstream services.                                     | Pass `tenantId` via gRPC metadata.                    |

---

## **9. Best Practices**
1. **Minimize Context Size**: Only include necessary fields (e.g., avoid sending all claims for every request).
2. **Immutable Context**: Treat the context as read-only after extraction to prevent tampering.
3. **Rate-Limit Claims Cache**: Use TTLs to avoid stale data (e.g., role changes).
4. **Log Extraction Failures**: Audit attempts to extract invalid/missing context (e.g., for security monitoring).
5. **Support Token Refresh**: Handle expired tokens gracefully (e.g., via `401 With Refresh Token`).
6. **Document Context Schema**: Publish the schema as an OpenAPI/Swagger extension for API consumers.

---
**See Also**: [OAuth2 Token Introspection](https://datatracker.ietf.org/doc/html/rfc7662), [RBAC (Role-Based Access Control)](https://datatracker.ietf.org/doc/html/rfc6920).