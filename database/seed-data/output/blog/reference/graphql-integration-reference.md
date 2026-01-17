# **[Pattern] GraphQL Integration Reference Guide**

---

## **Overview**
GraphQL is a query language for APIs that allows clients to request **only the data they need**, reducing over-fetching and enabling flexible, type-safe interactions. This reference guide details how to integrate GraphQL into your system, covering schema design, query execution, mutations, subscriptions, and best practices.

Key benefits of GraphQL integration:
- **Precise data retrieval** (unlike REST’s fixed endpoints).
- **Single endpoint** for all resource interactions.
- **Strong typing** via GraphQL Schema Definition Language (SDL).
- **Efficient caching & client-side management**.

Integration requires:
- A **GraphQL server** (e.g., Apollo, GraphQL Yoga).
- A **schema definition** (SDL files).
- **Resolvers** to fetch/process data.
- **Client libraries** (e.g., Apollo Client, URQL).

---

## **1. Core Concepts**

| **Term**          | **Description**                                                                 | **Key Details**                                                                 |
|-------------------|-------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **Schema**        | Defines types, queries, mutations, and subscriptions.                          | Written in SDL (e.g., `type User { id: ID! name: String }`).                |
| **Type**          | Represents data structure (scalar, object, interface, union, enum, input). | Objects define nested fields; scalars are primitives (Int, String, etc.). |
| **Query**         | Read-only operations to fetch data.                                           | Example: `query { user(id: "1") { name } }`.                              |
| **Mutation**      | Writes data (create/update/delete).                                            | Example: `mutation { createUser(name: "Alice") { id } }`.                   |
| **Subscription**  | Real-time updates via WebSockets.                                              | Example: `subscription { newUser { name } }`.                              |
| **Resolver**      | Function to fetch/mutate data for a field.                                    | Typically wraps database/API calls.                                          |
| **SDL**           | Schema Definition Language—human-readable schema syntax.                    | Generated from code (e.g., TypeGraphQL, GraphQL Code Generator).             |

---

## **2. Schema Reference**

### **2.1 Schema Definition (SDL Example)**
```graphql
# Types
type User {
  id: ID!
  name: String!
  email: String!
  posts: [Post!]!  # Non-null array of Posts
}

type Post {
  id: ID!
  title: String!
  content: String!
  author: User!     # Reference to User
}

# Input for mutations
input UserInput {
  name: String!
  email: String!
}

# Queries
type Query {
  getUser(id: ID!): User
  listUsers: [User!]!
}

# Mutations
type Mutation {
  createUser(input: UserInput!): User!
  deleteUser(id: ID!): Boolean!
}

# Subscriptions
type Subscription {
  onUserCreated: User!
}
```

#### **Key Rules:**
- **`!`** = Non-nullable field.
- **`[Type]`** = Array of `Type`.
- **Input types** are for mutations/subscriptions (not queries).
- **Interfaces/Unions** enable polymorphic types (e.g., `Node { id: ID! }` for shared IDs).

---

## **3. Query Examples**

### **3.1 Basic Query**
**Request:**
```graphql
query {
  getUser(id: "1") {
    name
    email
    posts {
      title
    }
  }
}
```
**Response:**
```json
{
  "data": {
    "getUser": {
      "name": "Alice",
      "email": "alice@example.com",
      "posts": [
        { "title": "Hello World" }
      ]
    }
  }
}
```

---

### **3.2 Mutation**
**Request:**
```graphql
mutation {
  createUser(input: { name: "Bob", email: "bob@example.com" }) {
    id
    name
  }
}
```
**Response:**
```json
{
  "data": {
    "createUser": {
      "id": "2",
      "name": "Bob"
    }
  }
}
```

---

### **3.3 Subscription (Real-Time)**
**Request:**
```graphql
subscription {
  onUserCreated {
    name
  }
}
```
**Response (WebSocket stream):**
```json
{ "data": { "onUserCreated": { "name": "Charlie" } } }
```

---

### **3.4 Fragment for Reusability**
**Request:**
```graphql
query {
  user: getUser(id: "1") {
    ...userProfile
    posts(limit: 3) {
      title
    }
  }
}

fragment userProfile on User {
  name
  email
}
```

---

## **4. Implementation Details**

### **4.1 Setting Up a GraphQL Server**
#### **Node.js (Apollo Server)**
```javascript
const { ApolloServer, gql } = require('apollo-server');
const typeDefs = gql`.../* Your SDL here */`;
const resolvers = { /* Field resolvers */ };

const server = new ApolloServer({ typeDefs, resolvers });
server.listen().then(({ url }) => console.log(`Server ready at ${url}`));
```

#### **Resolver Example**
```javascript
resolvers = {
  Query: {
    getUser: (_, { id }) => db.getUser(id),
    listUsers: () => db.listUsers(),
  },
  User: {
    posts: (user) => db.getUserPosts(user.id),
  },
};
```

---

### **4.2 Client-Side (Apollo Client)**
```javascript
import { ApolloClient, InMemoryCache, gql } from '@apollo/client';

const client = new ApolloClient({
  uri: 'http://localhost:4000',
  cache: new InMemoryCache(),
});

const GET_USER = gql`
  query GetUser($id: ID!) {
    getUser(id: $id) {
      name
    }
  }
`;

// Fetch data
client.query({ query: GET_USER, variables: { id: "1" } }).then(console.log);
```

---

### **4.3 Schema Evolution**
- **Add fields** (backward-compatible).
- **Remove deprecated fields** (add `@deprecated` first).
- **Use GraphQL Playground/Studio** for testing.

---

## **5. Best Practices**

| **Practice**               | **Description**                                                                 |
|----------------------------|-------------------------------------------------------------------------------|
| **Avoid over-fetching**    | Use `!` sparingly; let clients specify fields.                               |
| **Use interfaces/unions**  | For shared fields (e.g., `Node { id: ID! }`).                                |
| **Input validation**       | Validate mutations (e.g., `email` format).                                    |
| **Pagination**             | Use `offset/limit` or cursors for large datasets.                            |
| **Performance**            | Implement data loaders to avoid N+1 queries.                                 |
| **Authentication**         | Use `context` in resolvers for JWT/OAuth.                                     |
| **Testing**                | Mock resolvers; test fragments/queries in isolation.                          |

---

## **6. Related Patterns**

| **Pattern**               | **Description**                                                                 | **When to Use**                          |
|---------------------------|-------------------------------------------------------------------------------|------------------------------------------|
| **REST ↔ GraphQL Bridge** | Convert REST APIs into GraphQL fields.                                        | Legacy systems with REST endpoints.      |
| **GraphQL + DataLoader**  | Batch/resolve N+1 queries efficiently.                                        | High-traffic apps with complex joins.    |
| **GraphQL Subscriptions** | Real-time updates via WebSockets.                                             | Chat apps, live dashboards.              |
| **Persisted Queries**     | Cache queries to reduce network overhead.                                     | Mobile/web clients with limited bandwidth.|
| **GraphQL Federation**    | Combine microservices into a single schema.                                  | Distributed systems with multiple databases.|

---

## **7. Troubleshooting**

| **Issue**                  | **Solution**                                                                   |
|----------------------------|-------------------------------------------------------------------------------|
| **400 Bad Request**        | Check query syntax (missing `{}` or `!`).                                     |
| **500 Server Error**       | Debug resolver logic (e.g., `db.getUser()` failing).                          |
| **Slow Queries**           | Use `dataLoader` or optimize resolvers.                                       |
| **CORS Errors**            | Configure `cors: true` in Apollo Server or set headers manually.             |
| **WebSocket Connection**   | Ensure server supports subscriptions (e.g., Apollo Server v3+).               |

---

## **8. Tools & Libraries**
| **Category**               | **Tools**                                                                     |
|----------------------------|-------------------------------------------------------------------------------|
| **Servers**                | Apollo Server, GraphQL Yoga, Express + graphql.                             |
| **Clients**                | Apollo Client, URQL, Relay.                                                   |
| **SDL Generation**         | TypeGraphQL, GraphQL Code Generator.                                          |
| **Testing**                | Jest + `graphql-testing`, JestMockExtender.                                 |
| **Monitoring**             | Apollo Studio, GraphiQL.                                                     |

---
**References:**
- [GraphQL Spec](https://spec.graphql.org/)
- [Apollo Docs](https://www.apollographql.com/docs/)
- [GraphQL Code Generator](https://www.graphql-code-generator.com/)