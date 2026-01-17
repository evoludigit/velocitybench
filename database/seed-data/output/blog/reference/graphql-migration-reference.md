---

# **[Pattern] GraphQL Migration Reference Guide**
*Migrating legacy data systems to GraphQL while minimizing downtime and disruption*

---

## **Overview**
The **GraphQL Migration Pattern** provides a structured approach to transitioning monolithic or REST-based APIs to a flexible GraphQL implementation without requiring a complete rewrite. By leveraging a **hybrid layer** (e.g., GraphQL as a facade over legacy services), you can gradually expose data through GraphQL while maintaining backward compatibility. This pattern mitigates risks like system overload, schema drift, or service interruptions.

**Key benefits:**
✔ **Incremental adoption** – Migrate only critical endpoints at a time.
✔ **Flexible querying** – Clients fetch only the data they need (vs. over-fetching in REST).
✔ **Backward compatibility** – Legacy clients remain functional during transition.
✔ **Performance isolation** – Legacy systems operate independently until fully replaced.

---
## **Schema Reference**

| **Component**       | **Description**                                                                 | **Example**                                                                 |
|----------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Hybrid Schema**    | Combines legacy REST/DB schemas with new GraphQL types.                       | `type User @legacy { id: ID! }`                                              |
| **Legacy Adapters**  | Wrappers that translate GraphQL operations to legacy APIs/DB queries.         | Query: `{ legacyUser(id: "123") { name } }`                                 |
| **GraphQL Resolvers** | Functions that fetch data from legacy sources or new GraphQL services.        | `resolve: (_, { id }) => fetchLegacyUser(id)`                                |
| **Data Fusion**      | Merges legacy and GraphQL data (e.g., enriching legacy records with new fields). | `{ user { id legacy: existingName newField: "@graphql" } }`                   |
| **Deprecation Warnings** | Marks legacy fields/types as deprecated to guide clients toward GraphQL.     | `field "name": "Deprecated: Use user.name instead"`                          |
| **Directives**       | Schema annotations for migration control (e.g., `@legacy`, `@deprecated`).   | `query: @legacy { users }`                                                   |

---
## **Implementation Details**

### **1. Migration Strategy**
Choose between **two approaches**:
- **Parallel Run**: Deploy GraphQL alongside legacy systems (recommended for safety).
  *Pros*: Zero downtime, easy rollback.
  *Cons*: Higher operational cost.
- **Shadow Mode**: GraphQL fetches solely from legacy systems until fully migrated.
  *Pros*: Simpler staging.
  *Cons*: Risk of data inconsistency if legacy systems change.

---

### **2. Hybrid Schema Setup**
#### **Example Schema Snippet**
```graphql
# Legacy types (auto-generated or manually annotated)
type LegacyUser @legacy {
  id: ID!
  existingName: String!
}

# New GraphQL-compatible types
type User {
  id: ID! @external
  name: String!       # Replaces existingName
  bio: String         # New field
}

# Query combining both
query {
  legacyUser(id: "123") { existingName }
  user(id: "123") { name bio }
}
```

#### **Key Annotations**:
- **`@legacy`**: Marks types/fields tied to legacy systems.
- **`@external`**: Indicates dependencies on external services.

---

### **3. Resolver Implementation**
#### **Legacy Adapter Resolver (Node.js/TypeScript)**
```typescript
// resolvers/legacyUser.ts
export const resolvers = {
  Query: {
    legacyUser: async (_, { id }, { legacyClient }) => {
      const response = await legacyClient.getUser(id);
      return {
        __typename: 'LegacyUser',
        id: response.id,
        existingName: response.name,
      };
    },
  },
};
```

#### **GraphQL Resolver (New Data Source)**
```typescript
// resolvers/user.ts
export const resolvers = {
  Query: {
    user: async (_, { id }, { db }) => {
      const user = await db.query('SELECT * FROM users WHERE id = $1', [id]);
      return {
        id: user.id,
        name: user.name,
        bio: user.bio, // New field
      };
    },
  },
};
```

---

### **4. Data Fusion Resolvers**
Combine legacy and new data in a single resolver:
```typescript
// resolvers/fullUser.ts
export const resolvers = {
  User: {
    __resolveType: (obj) => obj.isLegacy ? 'LegacyUser' : 'User',
    legacyUser: async (parent) => parent.isLegacy ? parent : legacyClient.getUser(parent.id),
    currentUser: async (parent) => parent.isLegacy ? db.queryUser(parent.id) : parent,
  },
};
```

---

### **5. Deprecation Handling**
- **Schema Directives**:
  ```graphql
  type LegacyUser @deprecated(reason: "Use User.type instead") {
    id: ID!
  }
  ```
- **Error Responses**:
  ```json
  {
    "errors": [
      {
        "message": "Field 'legacyUser' is deprecated",
        "extensions": { "deprecationReason": "Use 'user' instead" }
      }
    ]
  }
  ```

---

### **6. Performance Considerations**
- **Caching**: Use Apollo Cache or Redis to avoid redundant legacy API calls.
- **Rate Limiting**: Isolate legacy adapters to prevent overload.
- **Batch Queries**: Use DataLoader for N+1 query optimization.

```typescript
// Example: DataLoader for legacy users
const loadLegacyUsers = new DataLoader(async (keys) => {
  const responses = await legacyClient.getUsers(keys);
  return keys.map(key => responses.find(r => r.id === key));
});
```

---

## **Query Examples**

### **1. Hybrid Query (Legacy + GraphQL Data)**
```graphql
query HybridUser {
  legacyUser(id: "123") {
    existingName
  }
  user(id: "123") {
    name
    bio
  }
}
```
*Response*:
```json
{
  "data": {
    "legacyUser": { "existingName": "Alice" },
    "user": { "name": "Alice", "bio": "GraphQL enthusiast" }
  }
}
```

---

### **2. Deprecated Field Warning**
```graphql
query DeprecatedField {
  legacyUser(id: "123") {
    existingName
  }
}
```
*Response* (includes deprecation notice in extensions):
```json
{
  "data": { "legacyUser": { "existingName": "Alice" } },
  "errors": [{
    "message": "Field 'existingName' is deprecated",
    "extensions": { "deprecationReason": "Use 'user.name' instead" }
  }]
}
```

---

### **3. Merged Legacy+GraphQL Fields**
```graphql
query FullUser {
  user(id: "123") {
    id
    legacyName: legacyUser { existingName }
    currentName: name
  }
}
```
*Response*:
```json
{
  "data": {
    "user": {
      "id": "123",
      "legacyName": "Alice",
      "currentName": "Alice Updated"
    }
  }
}
```

---

## **Tools & Libraries**
| **Tool**               | **Purpose**                                                                 |
|-------------------------|-----------------------------------------------------------------------------|
| **Apollo Federation**  | Split GraphQL schemas across microservices (legacy + new).                  |
| **Prisma**              | Migrate databases to GraphQL with type-safe queries.                         |
| **GraphQL Code Generator** | Auto-generate TypeScript types from legacy schemas.                      |
| **GraphQL Playground**  | Test hybrid queries without deploying.                                      |
| **AWS AppSync**         | Managed GraphQL with DataSources for legacy integrations.                   |

---

## **Related Patterns**
1. **Adapter Pattern**
   - *Use case*: Isolate legacy system interactions behind clean GraphQL interfaces.
   - *Example*: A `LegacyUserAdapter` translates GraphQL `user` queries to REST calls.

2. **Schema Stitching**
   - *Use case*: Combine multiple GraphQL schemas (e.g., legacy + new microservices).
   - *Tools*: Apollo Federation, GraphQL Relay.

3. **Incremental Migration**
   - *Use case*: Phase out legacy fields/types over time.
   - *Strategy*: Deprecate fields in releases, remove after adoption.

4. **GraphQL Subscriptions for Legacy Events**
   - *Use case*: Expose legacy event streams (e.g., WebSocket) via GraphQL subscriptions.
   - *Example*:
     ```graphql
     subscription {
       legacyEvent { type payload }
     }
     ```

5. **Canary Deployment**
   - *Use case*: Gradually shift traffic from legacy to GraphQL.
   - *Tools*: Feature flags in Apollo Server or AWS ALB.

---

## **Anti-Patterns & Pitfalls**
❌ **Blocking Legacy Systems**: Don’t rewrite all resolvers at once; use parallel paths.
❌ **Ignoring Deprecation**: Clients may rely on deprecated fields indefinitely.
❌ **Over-Fetching in Legacy**: Avoid exposing entire legacy tables as GraphQL types.
❌ **No Caching**: Legacy adapters without caching cause performance bottlenecks.

---
## **Checklist for Implementation**
| **Step**                  | **Action Items**                                                                 |
|---------------------------|--------------------------------------------------------------------------------|
| **Phase 1: Discovery**    | Inventory legacy endpoints; map to GraphQL types.                              |
| **Phase 2: Hybrid Setup** | Implement `@legacy` annotations; create adapter resolvers.                     |
| **Phase 3: Testing**      | Validate hybrid queries with staging data; test deprecation warnings.         |
| **Phase 4: Rollout**      | Deploy GraphQL alongside legacy; monitor error rates.                         |
| **Phase 5: Sunset**       | Remove deprecated fields; document breaking changes.                          |

---
## **Example Roadmap**
| **Release** | **Focus Area**                     | **Example Tasks**                                  |
|-------------|------------------------------------|----------------------------------------------------|
| 1.0         | Hybrid Schema                     | Define `LegacyUser` + `User` types; basic resolvers.|
| 2.0         | Deprecation                        | Flag `existingName` as deprecated.                 |
| 3.0         | Full Migration                    | Remove `LegacyUser`; replace with graphql-only schema. |

---
**Final Note**: Successful GraphQL migrations require **collaboration** between frontend (clients driving adoption) and backend (owning the hybrid layer). Use tools like Apollo Studio to track schema drift and client usage.