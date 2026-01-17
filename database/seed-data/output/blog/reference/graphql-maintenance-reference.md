**[Pattern] GraphQL Maintenance Reference Guide**

---

### **Overview**
This reference details the **GraphQL Maintenance Pattern**, a structured approach to managing schema updates, versioning, and backward compatibility while minimizing disruption to existing clients. Unlike traditional REST API versioning, GraphQL’s declarative nature allows for **"feature flags" and **deprecation warnings** via schema directives, enabling phased rollouts and graceful degradation. This pattern ensures long-term maintainability by explicitly defining:
- **Deletion policies** for obsolete fields/resolvers,
- **Migration strategies** for breaking changes,
- **Client-side adoption controls** via `@deprecated` and `@maintenance` directives.

Use this guide when introducing breaking changes, adding new features, or refactoring resolvers in a GraphQL API with multiple consumers.

---

### **Key Concepts**
| Term               | Description                                                                                                                                                                                                 |
|--------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Maintenance Field** | A field marked with `@maintenance` (custom directive) to warn clients of upcoming removal or alteration. Clients ignore it post-migration.                                      |
| **Deprecation Cycle**  | A defined timeline (e.g., 6 months) where `@deprecated` fields are replaced by new alternatives.                                                                                                           |
| **Feature Flag**      | A client-configurable directive (e.g., `@experimental`) to opt into unstable or preview features without affecting production.                                                                |
| **Schema Aliasing**      | Temporarily renaming fields (e.g., `oldField` → `legacy_oldField`) to avoid breaking queries during transition.                                                                                     |
| **Backward Compatibility Window** | Period (e.g., 3 months) where deprecated fields continue to resolve but emit warnings.                                                                                        |

---

### **Implementation Details**

#### **1. Schema Directives**
Extend your schema with custom directives to enforce maintenance policies. Example using GraphQL Tools (JavaScript):

```graphql
directive @maintenance(
  reason: String!
  deprecationDate: String!
  replacement: String
) on FIELD_DEFINITION

directive @deprecated(
  reason: String! = "No longer supported"
) on FIELD_DEFINITION | ENUM_VALUE
```

**Apply to a field:**
```graphql
type Query {
  user(id: ID!): User
    @maintenance(reason: "Password fields will be removed in 2024-06-01", replacement: "useAuthToken")
}
```

#### **2. Deprecation Workflow**
1. **Announce**: Add `@deprecated` to the field with a clear replacement.
   ```graphql
   type User {
     email: String @deprecated(reason: "Use contactEmail instead")
     contactEmail: String
   }
   ```
2. **Warn Clients**: Log deprecation warnings in resolver middleware (e.g., Apollo Server):
   ```javascript
   const { ApolloServer } = require('apollo-server');
   const server = new ApolloServer({
     schema,
     formatError: (err) => {
       if (err.extensions?.deprecation) {
         console.warn(`[DEPRECATED] ${err.extensions.deprecation.message}`);
       }
       return err;
     }
   });
   ```
3. **Remove**: After the deprecation window, delete the field (e.g., via codegen tools like [graphql-codegen](https://graphql-codegen.com/)).

#### **3. Maintenance Mode**
For **breaking changes** (e.g., removing a field), use `@maintenance`:
```graphql
type Query {
  legacyUser(id: ID!): LegacyUser @maintenance(
    reason: "Use the new User type in v2.0",
    deprecationDate: "2023-12-31",
    replacement: "{ user(id: $id) { id name } }"
  )
}
```
- **Client Behavior**: Queries referencing `legacyUser` resolve but emit a warning:
  ```json
  {
    "data": { "legacyUser": { "id": "123", "name": "John" } },
    "extensions": {
      "maintenance": {
        "reason": "Use the new User type...",
        "replacementQuery": "{ user(id: $id) { id name } }"
      }
    }
  }
  ```

#### **4. Feature Flags**
Enable experimental fields via client-side directives:
```graphql
type Query {
  userAnalytics(id: ID!): UserAnalytics
    @experimental(reason: "Preview: Analytics API under heavy development")
}
```
- **Client Implementation** (Apollo Cache Controls):
  ```javascript
  const client = new ApolloClient({
    cache: new InMemoryCache({
      typePolicies: {
        Query: {
          fields: {
            userAnalytics: {
              read: (_, { readField }) => {
                // Only return if client has opted into experiments
                const hasOptedIn = localStorage.getItem('experiment:analytics') === 'true';
                return hasOptIn ? readField('userAnalytics') : null;
              }
            }
          }
        }
      }
    })
  });
  ```

---

### **Schema Reference**
| Directive          | Location       | Required Args               | Purpose                                                                                                                                 |
|--------------------|----------------|----------------------------|-------------------------------------------------------------------------------------------------------------------------------------|
| `@maintenance`     | FIELD_DEFINITION | `reason`, `deprecationDate` | Mark fields for removal after a deadline. Clients should migrate to a replacement query.                                            |
| `@deprecated`      | FIELD_DEFINITION | `reason`                    | Soft-deprecates fields; logs warnings but continues resolving during a configured window.                                             |
| `@experimental`    | FIELD_DEFINITION | `reason`                    | Opt-in fields for unstable or preview functionality.                                                                               |
| `@alias`           | FIELD_DEFINITION | `alias: String`             | *Custom directive*: Temporarily renames a field to avoid breaking queries (e.g., `oldName: fieldName @alias(alias: "legacy_oldName")`). |

---
### **Query Examples**

#### **1. Querying a Deprecated Field**
```graphql
query {
  user(id: "1") {
    email  # Deprecated; client receives a warning
    contactEmail
  }
}
```
**Response:**
```json
{
  "data": {
    "user": {
      "contactEmail": "john@example.com"
    }
  },
  "extensions": {
    "deprecation": {
      "message": "email: Use contactEmail instead"
    }
  }
}
```

#### **2. Querying a Maintenance Field**
```graphql
query {
  legacyUser(id: "1") { name }  # Maintenance field
}
```
**Response:**
```json
{
  "data": { "legacyUser": { "name": "John" } },
  "extensions": {
    "maintenance": {
      "reason": "Use the new User type in v2.0",
      "replacement": "{ user(id: $id) { id name } }"
    }
  }
}
```

#### **3. Opting into Experimental Features**
```graphql
query {
  user(id: "1") {
    ... on User {
      name
      analytics @experimental  # Client must opt in
    }
  }
}
```
**Client-Side Opt-In (JavaScript):**
```javascript
// Enable experiments before querying
const { setContext } = client;
setContext({ experimentalFeatures: true });
```

---

### **Migration Strategies**
| Scenario               | Strategy                                                                                                                                                     | Tools/Libraries                          |
|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------|
| **Field Removal**      | Use `@maintenance` + deprecation window (e.g., 6 months).                                                                                             | graphql-codegen, Apollo Studio          |
| **Breaking Changes**   | Schema aliasing (e.g., `oldField: newField @alias`) + backward-compatible resolvers.                                                               | Prisma, Hasura                              |
| **New Features**       | Feature flags (`@experimental`) + client-side opt-in.                                                                                                | Apollo Cache Controls, Relay Experimental|
| **Resolvers Refactoring** | Deprecate old resolver → add new resolver → remove old after adoption.                                                                         | GraphQL Inspector, GraphQL Playground    |

---

### **Related Patterns**
1. **[GraphQL Schema Stitching](https://www.apollographql.com/docs/apollo-server/schema/stitching/)**
   - Combine multiple schemas for gradual migration (e.g., merge old API with new v2).
   - *Use Case*: Phase out a legacy GraphQL service while introducing a new one.

2. **[Query Complexity Analysis](https://www.apollographql.com/docs/apollo-server/performance/query-complexity/)**
   - Monitor maintenance fields for excessive usage before removal.
   - *Tool*: `graphql-query-complexity`.

3. **[Subscription rate limiting](https://www.apollographql.com/docs/apollo-server/data/subscriptions/)**
   - Apply limits to maintenance-mode subscriptions to avoid overload during migration.

4. **[GraphQL Persisted Queries](https://www.apollographql.com/docs/apollo-server/data/persisted-queries/)**
   - Hash deprecated queries to log usage and enforce migration deadlines.

5. **[Canary Releases](https://www.apollographql.com/docs/apollo-server/feature-flagging/)**
   - Gradually roll out `@experimental` fields to a subset of clients for testing.

---
### **Best Practices**
- **Document Deadlines**: Clearly state deprecation and removal dates in your changelog.
- **Monitor Adoption**: Use tools like [GraphQL Insights](https://www.apollographql.com/docs/apollo-server/insights/) to track usage of deprecated fields.
- **Automate Warnings**: Integrate deprecation checks into CI (e.g., [graphql-validation-complexity](https://github.com/ UrsulaMaster/apollo-server/tree/master/packages/graphql-validation-complexity)).
- **Alias Fields Aggressively**: During migrations, alias old fields to new ones to avoid breaking queries:
  ```graphql
  type Query {
    user(id: ID!): User
      @alias(oldUser: "legacyUser")
  }
  ```
- **Train Clients**: Publish migration guides and provide SDK helpers to update queries automatically.

---
### **Example Migration Timeline**
| Phase          | Duration | Action                                                                                                                                 |
|----------------|----------|----------------------------------------------------------------------------------------------------------------------------------------|
| **Announce**   | 3 months | Add `@deprecated` + replacement field. Log warnings in resolvers.                                                                  |
| **Warning**    | 6 months | Continue resolving deprecated field but emit warnings. Monitor client usage.                                                       |
| **Deprecation**| 1 month  | Remove deprecated field from schema. Provide aliasing for backward compatibility.                                                 |
| **Removal**    | 1 month  | Delete field completely. Update documentation to reference new replacement.                                                          |

---
**References**:
- [Apollo GraphQL Deprecation Guide](https://www.apollographql.com/docs/apollo-server/api/deprecation/)
- [GraphQL Operations Architecture](https://graphql.github.io/learn/operations/)
- [Schema Directives RFC](https://github.com/graphql/graphql-spec/blob/main/spec.md#section-5.18.3)