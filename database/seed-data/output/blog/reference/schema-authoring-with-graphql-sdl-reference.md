---
# **[Pattern] GraphQL Schema Authoring with Schema Definition Language (SDL)**
*Reference Guide*

---

## **Overview**
GraphQL Schema Definition Language (SDL) is a declarative, language-agnostic syntax for defining GraphQL schemas. It enables schema authors to precisely model data, types, queries, mutations, and subscriptions in a human-readable format. SDL separates schema definition from implementation, promoting consistency, collaboration, and tooling support across GraphQL ecosystems. This guide covers the core constructs of SDL, best practices for schema design, and practical examples.

---

## **Core Schema Reference**

All constructs in SDL adhere to the following **grammar**:

| **Category**       | **Syntax**                                                                 | **Description**                                                                                                                                                                                                 |
|--------------------|---------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Scalar Types**   | `scalar <Name>`                                                           | Predefined or custom scalar types (e.g., `String`, `Int`, `Float`, `Boolean`). Custom scalars require a runtime validation strategy.                                                                |
| **Object Types**   | `type <Name> { ... }`                                                      | Defines a type with fields, interfaces, or unions. Fields include type, arguments, and directives.                                                                                                      |
| **Fields**         | `<Name> : <Type> [= <Default>] [Arguments] [Directives]`                     | Field declaration with type, optional default value, input arguments, and directives (e.g., `@deprecated`).                                                                                           |
| **Arguments**      | `[<Name> : <Type> = <Default>]`                                           | Input arguments for fields/mutations with optional default values.                                                                                                                                       |
| **Interfaces**     | `interface <Name> { ... }`                                                 | Shared shape among object types. Implementing types must satisfy all interface fields.                                                                                                                 |
| **Unions**         | `union <Name> = <Type1> | <Type2> | ...`                              | Combines multiple object/interface types under a single type. Resolvers must return one of the unioned types.                                                                                     |
| **Enums**          | `enum <Name> { <Value1>, <Value2>, ... }`                                 | Enumerated values for fixed sets of choices.                                                                                                                                                           |
| **Input Types**    | `input <Name> { ... }`                                                     | Immutable types for query/mutation arguments (e.g., `CreateUserInput`). Cannot contain fields with functions (e.g., `query` or `mutation`).                                                           |
| **Queries**        | `type Query { <Field> : <Type> }`                                           | Top-level type for read-only operations. Fields must resolve to data.                                                                                                                                     |
| **Mutations**      | `type Mutation { <Field> : <Type> }`                                        | Top-level type for write operations (e.g., `createUser`). Fields must return a scalar, object, or input type.                                                                                          |
| **Subscriptions**  | `type Subscription { <Field> : <Type> }`                                   | Top-level type for real-time data streams (e.g., `onUserUpdate`). Requires a `Subscription` type in the GraphQL server implementation.                                                               |
| **Directives**     | `@<Name>(<Argument>)`                                                      | Special annotations for fields/arguments (e.g., `@deprecated(reason: "Use X instead")`). Built-in directives include `include`, `skip`, and custom directives (e.g., `@auth`).                       |
| **Fragments**      | `fragment <Name> on <Type> { ... }`                                        | Reusable field sets for queries/mutations. Referenced via `...<Name>`.                                                                                                                                      |
| **Scalars** (Custom)| `scalar <Name>` + Runtime Definition                                        | Custom scalars require a resolver to validate/serialize data (e.g., `JSON`, `DateTime`).                                                                                                                 |

---

## **Query Examples**

### **1. Basic Query**
Define a schema with a `User` type:
```graphql
type User {
  id: ID!
  name: String!
  email: String!
}

type Query {
  getUser(id: ID!): User
}
```
**Query a single user:**
```graphql
query {
  getUser(id: "123") {
    name
    email
  }
}
```

---

### **2. Argument Pass-through**
Include a `filter` argument:
```graphql
type Query {
  getUsers(filter: UserFilter): [User]
}

input UserFilter {
  minAge: Int
}

type User {
  id: ID!
  name: String!
  age: Int!
}
```
**Query with filter:**
```graphql
query {
  getUsers(filter: { minAge: 18 }) {
    name
    age
  }
}
```

---

### **3. Interface Implementation**
Define an interface and multiple implementations:
```graphql
interface Post {
  id: ID!
  title: String!
}

type BlogPost implements Post {
  id: ID!
  title: String!
  content: String!
}

type VideoPost implements Post {
  id: ID!
  title: String!
  duration: Int!
}

type Query {
  getPost(id: ID!): Post
}
```
**Query with interface resolution:**
```graphql
query {
  getPost(id: "456") {
    ... on BlogPost {
      content
    }
    ... on VideoPost {
      duration
    }
  }
}
```

---

### **4. Mutation with Input Type**
Create a `createUser` mutation:
```graphql
input UserInput {
  name: String!
  email: String!
}

type Mutation {
  createUser(input: UserInput!): User
}

type User {
  id: ID!
  name: String!
  email: String!
}
```
**Execute mutation:**
```graphql
mutation {
  createUser(input: { name: "Alice", email: "alice@example.com" }) {
    id
    name
  }
}
```

---

### **5. Subscription with Fragment**
Define a subscription with a reusable fragment:
```graphql
type Subscription {
  onUserUpdate: User
}

fragment userUpdates on User {
  name
  email
}

subscription {
  onUserUpdate {
    ...userUpdates
  }
}
```
**GraphQL Server Implementation Note:**
Subscriptions require a server-side implementation (e.g., using `graphql-subscriptions` or Apollo Server).

---

### **6. Custom Scalar (JSON)**
Declare a custom scalar for JSON data:
```graphql
scalar JSON
```
**Resolver Implementation (Example in Node.js):**
```javascript
const { JSON } = require('graphql-scalars');

const scalarMap = {
  JSON: JSON,
};

const schema = makeExecutableSchema({
  typeDefs: [ /* Your SDL here */ ],
  resolvers: {
    JSON,
    // Other resolvers...
  }
});
```

---

## **Best Practices for Schema Authoring**

### **1. Versioning & Backward Compatibility**
- **Use `@deprecated`** for removing fields:
  ```graphql
  type User {
    oldField: String @deprecated(reason: "Use newField instead")
    newField: String
  }
  ```
- **Avoid breaking changes** in mutations (e.g., renaming required fields).

### **2. Input Types**
- Prefer input types for mutations to enforce consistent data shapes.
- Example:
  ```graphql
  input CreateUserInput {
    name: String!
    email: String!
    roles: [Role!]!
  }
  ```

### **3. Performance**
- **Pagination:** Use `Cursor`-based or offset-limit pagination:
  ```graphql
  type Query {
    getUsers(limit: Int, offset: Int): [User]
  }
  ```
- **Field Selection:** Leverage GraphQL’s runtime filtering to avoid over-fetching.

### **4. Documentation**
- Use **descriptions** in SDL for clarity:
  ```graphql
  """
  Returns all users with optional filtering.
  Default limit is 10 if not provided.
  """
  type Query {
    getUsers(filter: UserFilter, limit: Int): [User]
  }
  ```
- Integrate tools like **GraphQL Playground** or **GraphiQL** for interactive documentation.

### **5. Security**
- **Restrict sensitive fields** with directives (e.g., `@auth`):
  ```graphql
  type User {
    id: ID!
    email: String!
    secret: String @auth(requires: ADMIN)
  }
  ```
- **Validate inputs** rigorously (e.g., regex for emails).

### **6. Testing**
- **Schema Validation:** Use tools like `graphql-tools` or `graphql-language-service` to lint SDL.
- **Mock Resolvers:** Test queries independently of a live server:
  ```javascript
  const mocks = {
    User: () => ({ id: '1', name: 'Mock User' }),
  };
  const mockSchema = makeExecutableSchema({ typeDefs, resolvers: mocks });
  ```

---

## **Related Patterns**

| **Pattern**                     | **Description**                                                                                                                                                                                                 | **SDL Integration**                                                                                     |
|----------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|
| **Federation**                   | Split schema across services while enabling composite queries.                                                                                                                                             | Extends SDL with `@extends`, `@key`, and `@external`.                                                  |
| **Persisted Queries**           | Optimize performance by pre-registering queries.                                                                                                                                                      | Not part of SDL, but SDL queries can be persisted via tools like Apollo’s `persistedQueryStats`.        |
| **Relay Cursor Connections**     | Standardized pagination for client-side libraries.                                                                                                                                                     | SDL includes `Edge` and `Connection` types (e.g., `cursor`, `pageInfo`).                                |
| **DataLoader**                   | Batch/resolve operations to improve server performance.                                                                                                                                                  | SDL defines types; DataLoader implements resolvers.                                                     |
| **Query Complexity Analysis**    | Enforce query depth/width limits to prevent abuse.                                                                                                                                                     | SDL doesn’t enforce; use middleware (e.g., `graphql-depth-limit`).                                   |
| **Subscriptions**               | Real-time data updates via WebSockets.                                                                                                                                                                 | SDL defines `Subscription` type; requires server implementation (e.g., Apollo Server).                 |
| **Schema Stitching**             | Combine multiple SDL files into a unified schema.                                                                                                                                                     | Use tools like `graphql-schema-stitching` or `graphql-tools`.                                        |

---

## **Tools & Libraries**
| **Tool/Library**                | **Purpose**                                                                                                                                                                                                 |
|----------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [GraphQL SDL](https://graphql.org/learn/schema/) | Official reference for SDL syntax.                                                                                                                                                                     |
| [graphql-codegen](https://graphql-codegen.com/) | Generate types from SDL (e.g., TypeScript, Python).                                                                                                                                                  |
| [graphql-inspector](https://github.com/realworldoc/graphql-inspector) | Analyze SDL for common anti-patterns.                                                                                                                                                              |
| [SDL Validation](https://github.com/apollographql/graphql-config/blob/main/docs/schema-validation.md) | Lint SDL for errors/warnings.                                                                                                                                                                     |
| [GraphQL Playground](https://github.com/graphql/graphql-playground) | Interactive IDE for testing SDL.                                                                                                                                                                       |
| [Apollo Studio](https://studio.apollographql.com/) | Visualize and document SDL schemas.                                                                                                                                                                   |

---

## **Troubleshooting**
| **Issue**                          | **Cause**                              | **Solution**                                                                                                                                                     |
|-------------------------------------|----------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `Cannot query field "X" on type "Y"`| Typo in SDL or field name.            | Verify SDL syntax and field names. Use `graphql-inspector` to validate.                                                                                           |
| `Argument "Z" is required`          | Missing required argument in query.    | Ensure all required arguments are provided. Check SDL defaults.                                                                                                  |
| `Cannot return null for non-nullable field` | Resolver returns `null`.        | Implement fallback logic or use non-nullable types judiciously.                                                                                                  |
| `Union type has no possible types` | Empty union definition.               | Ensure union includes at least one type.                                                                                                                         |
| `Custom scalar "JSON" is undefined`| Missing resolver for custom scalar. | Implement the scalar resolver (e.g., `graphql-scalars`).                                                                                                       |

---

## **Further Reading**
1. [GraphQL SDL Specification](https://spec.graphql.org/October2021/#sec-Schema-Definition-Language)
2. [Understanding GraphQL SDL](https://www.howtographql.com/basics/1-graphql-is-a-queries-language/)
3. [Advanced SDL Patterns](https://www.apollographql.com/docs/graphql/guides/schema/#advanced) (Apollo Docs)
4. [SDL as Code](https://www.graphqlbin.com/) (Online SDL editor with persistence).