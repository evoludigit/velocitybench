# **[Pattern] GraphQL Standards Reference Guide**

---

## **Overview**
This document establishes **GraphQL Standards** to ensure consistency, scalability, and maintainability across implementations. These standards define best practices for schema design, query conventions, and tooling integration, aligning GraphQL APIs with enterprise-grade quality. Key principles include:
- **Schema Design:** Modular, versioned, and self-documenting schemas.
- **Query Optimization:** Standardized naming, pagination, and filtering conventions.
- **Tooling & Governance:** Enforced linting, testing, and CI/CD validation.

Adhering to these standards improves developer productivity, reduces errors, and enables seamless interoperability between microservices.

---

## **Schema Reference**

| **Category**       | **Standard**                                                                 | **Example**                                                                 |
|--------------------|------------------------------------------------------------------------------|----------------------------------------------------------------------------|
| **Naming**         | Use `PascalCase` for types, `snake_case` for fields/enums.                  | `User` type with `firstName`, `lastName`.                                  |
| **Root Queries**   | All root queries must be prefixed with `query:` or `mutation:`.             | `query: GetUser(id: ID!): User`.                                            |
| **Input Types**    | Input types must end with `Input`.                                           | `UserInput` for mutation arguments.                                        |
| **Mutations**      | Mutations must return a `UserError` or `Void`.                               | `mutation: CreateUser(input: UserInput!): UserError!`.                     |
| **Pagination**     | Use `first`/`after` cursor-based pagination for large datasets.              | `{ users(first: 10, after: "cursor") { edges { cursor node { ... } } } }` |
| **Enums**          | Enums must be prefixed with `Status` or `Type`.                             | `Status: ACTIVE | PENDING`.                          |
| **Relationships**  | Use `@relation` directive for DB relationships (if supported by resolver). | `@relation("users", "user_id")`.                                           |

---

## **Query Examples**

### **1. Basic Query**
```graphql
# Get a single user with nested data
query GetUser($id: ID!) {
  query: getUser(id: $id) {
    id
    firstName
    lastName
    email
    address {
      city
      country
    }
  }
}
```

### **2. Paginated Query**
```graphql
# Fetch users with pagination
query UsersPage($first: Int, $after: String) {
  query: users(first: $first, after: $after) {
    edges {
      cursor
      node {
        id
        firstName
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

### **3. Mutation with Error Handling**
```graphql
# Create a user with validation
mutation CreateUser($input: UserInput!) {
  mutation: createUser(input: $input) {
    ... on User {
      id
      email
    }
    ... on UserError {
      field
      message
    }
  }
}
```

---

## **Key Concepts**

### **1. Schema Design**
- **Modularity:** Split schemas into `core.graphqls`, `auth.graphqls`, etc.
- **Versioning:** Use `v1` prefixes for breaking changes.
- **Self-Documentation:** Include `@description` directives for all types/fields.

### **2. Query Optimization**
- **Batch Loading:** Use `@batch` directives to reduce N+1 queries.
- **Caching:** Standardize `lastUpdated` fields for cache consistency.
- **Depth Limiting:** Enforce max query depth (e.g., 10) via middleware.

### **3. Tooling & Governance**
- **Linting:** Enforce with `graphql-config` and `graphql-lint`.
- **Testing:** Unit tests for schemas using `graphql-codegen`.
- **CI/CD:** Validate schema against standards in merge requests.

---

## **Implementation Details**

### **1. Schema Validation**
```yaml
# graphql-config.yml
schemas:
  - src/**/*.graphql
linting:
  rules:
    - noUndefinedVariables
    - noDeprecatedFields
```

### **2. Query Depth Limiting (Husky Plugin)**
```javascript
// server/middleware/depth-limiter.js
export default (req, res, next) => {
  const queryDepth = getQueryDepth(req.body.query);
  if (queryDepth > 10) return res.status(400).send('Max depth exceeded');
  next();
};
```

### **3. Pagination Directive**
```graphql
directive @paginated(
  first: Int = 10
  after: String
) on FIELD_DEFINITION
```

---

## **Related Patterns**
- **[Pattern] GraphQL Federation:** Decentralize schemas across services.
- **[Pattern] GraphQL Persisted Queries:** Optimize performance for clients.
- **[Pattern] GraphQL Subscription:** Enable real-time updates.
- **[Pattern] GraphQL Resolver Caching:** Reduce redundant DB calls.

---
**See Also:**
- [GraphQL Specification](https://spec.graphql.org/)
- [Apollo Server Best Practices](https://www.apollographql.com/docs/apollo-server/performance/)

---
*Last Updated: [Insert Date]*
*Version: 1.0*