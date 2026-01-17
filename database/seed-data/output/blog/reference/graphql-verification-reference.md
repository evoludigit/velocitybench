# **[Pattern] GraphQL Verification Reference Guide**

---

## **1. Overview**
The **GraphQL Verification pattern** ensures secure, authenticated, and role-validated access to GraphQL endpoints by integrating verification checks (authentication, authorization, and data consistency) directly into the query resolution process. This pattern enforces **request validation** before field resolution, preventing unauthorized access, tampering, and data corruption.

Key use cases:
- **Authentication:** Verify user identities via JWT/OAuth tokens.
- **Authorization:** Enforce role-based restrictions (e.g., `ADMIN`, `USER`).
- **Input Validation:** Ensure queries adhere to schema constraints (e.g., no deep introspection).
- **Rate Limiting:** Throttle malicious or excessive requests.

This pattern complements **GraphQL Security** (e.g., Query Depth Limiting) and **Data Fetching** (e.g., Batched Loading) patterns by adding a verification layer before data exposure.

---

## **2. Schema Reference**
Below are the core schema elements and directives required for verification.

### **2.1 Core Directives**
| Directive               | Purpose                                                                 | Example Usage                                                                 |
|-------------------------|-------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| `@auth`                 | Marks a field as requiring authentication.                              | `type Query { user(id: ID!): User @auth }`                                  |
| `@role`                 | Restricts access to specific roles (e.g., `ADMIN`, `EDITOR`).           | `type Mutation { deletePost(id: ID!): Boolean @role("ADMIN") }`             |
| `@validate`             | Enforces input validation (e.g., regex, range checks).                 | `input UserInput { name: String! @validate(regex: "/^[a-zA-Z ]+$/" }`        |
| `@rateLimit`            | Limits query frequency per user or IP.                                  | `type Query { dashboard: Dashboard @rateLimit(max: 5, window: "1m") }`     |

---

### **2.2 Example Schema Snippet**
```graphql
# Core Types
enum UserRole {
  ADMIN
  EDITOR
  USER
}

type User {
  id: ID!
  name: String!
  role: UserRole!
}

# Queries with Verification
type Query {
  currentUser: User @auth
  sensitiveData: String @role("ADMIN")
}

# Mutations with Validation
type Mutation {
  updateProfile(input: UserInput!): User @auth
}

input UserInput {
  name: String! @validate(regex: "/^[a-zA-Z ]+$/", maxLength: 20)
}
```

---

## **3. Implementation Details**
### **3.1 Authentication Flow**
1. **Token Extraction:** Parse the `Authorization: Bearer <token>` header.
2. **Validation:** Verify the token signature (JWT) or session cookie.
3. **User Resolution:** Fetch user data from a database or cache (e.g., Redis).
4. **Context Injection:** Attach the authenticated user to the execution context:
   ```javascript
   const context = {
     user: decodedToken, // { id: "...", role: "ADMIN" }
     dbClient: // Database client
   };
   ```

### **3.2 Authorization Logic**
- **Role-Based:** Check if the user’s `role` matches the required permission:
  ```graphql
  schema {
    directive @role(roles: [UserRole!]!) on FIELD_DEFINITION
  }
  ```
  Implementation (Apollo Server):
  ```javascript
  const resolvers = {
    Query: {
      sensitiveData: (_parent, _args, context) {
        if (!context.user.role.includes("ADMIN")) throw new Error("Forbidden");
        return "Secret data";
      }
    }
  };
  ```

- **Custom Policies:** Extend with custom logic (e.g., IP whitelisting):
  ```javascript
  const isAllowed = (context) => context.request.ip in WHITELISTED_IPS;
  ```

### **3.3 Input Validation**
Use libraries like:
- **GraphQL Input Validation:** [`graphql-input-validation`](https://www.npmjs.com/package/graphql-input-validation)
  ```javascript
  const schema = makeExecutableSchema({
    directives: [
      {
        validate: (value, { regex }, input) => {
          if (!new RegExp(regex).test(value)) throw new Error("Invalid format");
          return true;
        }
      }
    ]
  });
  ```
- **Zod:** Validate input shapes before resolution:
  ```javascript
  import { z } from "zod";
  const UserSchema = z.object({ name: z.string().regex(/^[a-zA-Z ]+/).max(20) });
  ```

### **3.4 Rate Limiting**
- **Middleware:** Use libraries like [`rate-limiter-flexible`](https://www.npmjs.com/package/rate-limiter-flexible):
  ```javascript
  const limiter = new RateLimiterFlexible({
    points: 5,
    duration: 60,
  });

  const rateLimit = async (resolve, parent, args, context, info) => {
    const key = `${context.user.id}-${info.parentType.name}`;
    await limiter.consume(key);
    return resolve(parent, args, context, info);
  };
  ```
- **Schema Integration:**
  ```graphql
  type Query {
    feed: [Post!]! @rateLimit(max: 10, window: "5m")
  }
  ```

---

## **4. Query Examples**
### **4.1 Valid Query (Authenticated User)**
```graphql
query GetProfile {
  currentUser {
    id
    name
    role
  }
}
```
**Context:**
```json
{
  "user": {
    "id": "123",
    "role": "USER"
  }
}
```
**Response:**
```json
{
  "data": {
    "currentUser": {
      "id": "123",
      "name": "Alice",
      "role": "USER"
    }
  }
}
```

### **4.2 Forbidden Query (Missing Token)**
```graphql
query GetAdminData {
  sensitiveData
}
```
**Header:** Missing `Authorization` header.
**Response:**
```json
{
  "errors": [
    {
      "message": "Authentication required",
      "path": ["sensitiveData"]
    }
  ]
}
```

### **4.3 Validated Mutation**
```graphql
mutation UpdateProfile {
  updateProfile(input: { name: "Bob" }) {
    name
  }
}
```
**Schema Validation:**
- `name` must match `/^[a-zA-Z ]+/`.
- `maxLength` of 20 enforced.
**Response:**
```json
{
  "data": {
    "updateProfile": {
      "name": "Bob"
    }
  }
}
```

### **4.4 Rate-Limited Query**
```graphql
query Feed {
  feed {
    title
  }
}
```
**After 5th request in 5 minutes:**
**Response:**
```json
{
  "errors": [
    {
      "message": "Rate limit exceeded (5 requests/minute)",
      "path": ["feed"]
    }
  ]
}
```

---

## **5. Error Handling**
| Scenario               | Error Type               | Example Response                                      |
|------------------------|--------------------------|-------------------------------------------------------|
| Invalid Token          | `AuthenticationError`    | `{ "message": "Invalid token" }`                      |
| Missing Role           | `AuthorizationError`     | `{ "message": "Forbidden: Requires ADMIN role" }`     |
| Invalid Input          | `ValidationError`        | `{ "message": "Invalid name format" }`               |
| Rate Limit Exceeded    | `RateLimitError`         | `{ "message": "Too many requests" }`                  |

Use structured errors for client-side handling:
```javascript
throw new Error(`Forbidden: Required role ${requiredRole}`);
```

---

## **6. Related Patterns**
| Pattern                          | Description                                                                 | Integration Point                          |
|----------------------------------|-----------------------------------------------------------------------------|--------------------------------------------|
| **GraphQL Security**             | Protect against DoS, introspection, and deep queries.                      | Schema directives (e.g., `@maxDepth`).     |
| **Batched Loading**              | Optimize nested queries with DataLoader.                                    | Resolver context.                          |
| **Authentication**               | Centralized auth (JWT/OAuth) with libraries like `apollo-server-auth`.     | Middleware before query resolution.        |
| **Input Masking**                | Hide sensitive fields in queries (e.g., `input User { email: String! }`). | Schema design.                             |
| **Query Complexity Analysis**   | Enforce query depth/field count limits.                                    | Execution context.                          |

---

## **7. Tools & Libraries**
| Tool/Library               | Purpose                                                                   | Link                                  |
|----------------------------|--------------------------------------------------------------------------|---------------------------------------|
| Apollo Server              | Built-in `@auth`, `@role` directives.                                    | [Apollo Docs](https://www.apollographql.com/docs/apollo-server/) |
| GraphQL Rate Limiter       | Query throttling middleware.                                              | [NPM](https://www.npmjs.com/package/graphql-rate-limit) |
| Zod                       | Input validation schema language.                                         | [Zod Docs](https://zod.dev/)          |
| AWS Cognito                | Managed authentication with GraphQL integrations.                         | [AWS Cognito](https://aws.amazon.com/cognito/) |
| GraphQL Shield             | Advanced authorization (e.g., `@shield` directives).                     | [NPM](https://www.npmjs.com/package/graphql-shield) |

---

## **8. Best Practices**
1. **Fail Fast:** Reject invalid requests during verification, not resolution.
2. **Audit Logs:** Log verification failures (e.g., `403 Forbidden`).
3. **Cache Tokens:** Use Redis to cache JWT validation results.
4. **Document Rules:** Clearly list required roles/permissions in the schema comments.
5. **Test Edge Cases:** Test with:
   - Expired tokens.
   - Malformed input (e.g., `name: "123"`).
   - Concurrent rate-limited requests.

---
**See also:**
- [GraphQL Security Cheatsheet](https://www.graphql.guide/security/)
- [Apollo Server Auth Docs](https://www.apollographql.com/docs/apollo-server/data/authentication/)