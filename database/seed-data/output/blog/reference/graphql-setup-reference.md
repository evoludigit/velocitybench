# **[Pattern] GraphQL Setup Reference Guide**

---

## **Overview**
This reference guide provides a structured approach to implementing **GraphQL** in modern applications. GraphQL enables efficient data fetching by allowing clients to request only the fields they need, reducing over-fetching and under-fetching issues common in REST APIs. This guide covers key concepts, schema design, implementation steps, and best practices for setting up a **production-ready GraphQL server** using **Node.js (with Apollo Server)** and **TypeScript**.

---

## **1. Key Concepts**
Before implementation, understand these foundational elements:

| **Term**         | **Description**                                                                                     | **Example**                                                                 |
|------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **GraphQL Schema** | Defines the available data structure, queries, mutations, and scalars.                             | ```graphql type User { id: ID! name: String! } ```                       |
| **Queries**       | Read-only operations to fetch data from the server.                                                  | `{ user(id: "1") { name } }`                                               |
| **Mutations**     | Write operations (e.g., create, update, delete) that modify data.                                    | ```mutation { createUser(name: "Alice") { id } }```                        |
| **Resolvers**     | Functions that fetch data or modify the database.                                                   | `resolve(user: User, args: { id }) { return db.getUser(id) }`            |
| **Type System**   | GraphQL uses **Non-nullable types (`!`)** and **scalars** (e.g., `ID`, `String`, `Int`).           | `email: String!` (required field)                                           |
| **Directives**    | Special keywords to modify execution (e.g., `@auth`, `@deprecated`).                                 | `@auth(requires: ADMIN) type AdminOnly { ... }`                           |
| **Subscriptions** | Real-time updates via WebSockets (e.g., live notifications).                                        | `subscription { onUserUpdate { user { name } } }`                          |

---

## **2. Implementation Steps**
### **2.1 Prerequisites**
- Node.js v16+
- TypeScript (recommended)
- Apollo Server (`npm install @apollo/server @apollo/graphql`)
- Database (PostgreSQL, MongoDB, etc.)

### **2.2 Schema Definition**
Define your schema using **GraphQL Schema Definition Language (SDL)**. Example (`src/schema.graphql`):

```graphql
# Schema for a Blog API
type Post {
  id: ID!
  title: String!
  content: String!
  author: User!
}

type User {
  id: ID!
  name: String!
  email: String!
}

type Query {
  post(id: ID!): Post
  posts: [Post!]!
}

type Mutation {
  createPost(title: String!, content: String!, authorId: ID!): Post!
}

type Subscription {
  onPostCreate: Post!
}
```

### **2.3 Resolver Implementation**
Create resolver mappings (`src/resolvers.ts`):

```typescript
import { GraphQLScalarType } from 'graphql';

const resolvers = {
  Query: {
    post: (_, { id }, context) => {
      return context.db.posts.find(p => p.id === id);
    },
    posts: (_, __, context) => context.db.posts,
  },
  Mutation: {
    createPost: (_, { title, content, authorId }, context) => {
      const newPost = { id: Date.now().toString(), title, content, authorId };
      context.db.posts.push(newPost);
      return newPost;
    },
  },
  Post: {
    author: (post) => context.db.users.find(u => u.id === post.authorId),
  },
  // Custom scalar (e.g., Date)
  Date: new GraphQLScalarType({
    name: 'Date',
    parseValue: (value) => new Date(value),
    serialize: (value) => value.toISOString(),
  }),
};
```

### **2.4 TypeScript Integration**
Generate strongly typed resolvers using `@graphql-codegen` or Apollo’s TypeScript support:

```typescript
// types.generated.ts (auto-generated)
declare namespace App {
  interface Context {
    db: { posts: Post[]; users: User[] };
  }
  // ... TypeScript interfaces for Query/Mutation/Subscription
}
```

### **2.5 Server Setup**
Initialize Apollo Server (`src/index.ts`):

```typescript
import { ApolloServer } from '@apollo/server';
import { startStandaloneServer } from '@apollo/server/standalone';
import { readFileSync } from 'fs';
import { buildSubgraphSchema } from '@apollo/subgraph';
import { resolvers } from './resolvers';

const typeDefs = readFileSync('./src/schema.graphql', { encoding: 'utf-8' });

const server = new ApolloServer({
  schema: buildSubgraphSchema({ typeDefs, resolvers }),
});

startStandaloneServer(server, { listen: { port: 4000 } })
  .then(({ url }) => console.log(`Server ready at ${url}`));
```

### **2.6 Middleware & Authentication**
Add JWT authentication using Apollo’s `AuthenticationError`:

```typescript
import { AuthenticationError } from 'apollo-server';
const authMiddleware = (context: App.Context) => {
  const token = context.req.headers.authorization || '';
  if (!token) throw new AuthenticationError('Missing token');
  // Validate token and attach user to context
};
```

### **2.7 Data Loader (Batching)**
Optimize database queries with DataLoader (`src/loaders.ts`):

```typescript
import DataLoader from 'dataloader';

export const postLoader = new DataLoader(async (postIds: string[]) => {
  const db = context.db.posts;
  return Promise.all(postIds.map(id => db.find(p => p.id === id)));
});
```

---

## **3. Query Examples**
### **Basic Queries**
```graphql
# Fetch a single post
query GetPost($id: ID!) {
  post(id: $id) {
    id
    title
  }
}
```

### **Fragmented Responses**
```graphql
# Reuse fields with fragments
fragment PostTitle on Post {
  title
}

query {
  posts {
    ...PostTitle
    author { name }
  }
}
```

### **Mutations**
```graphql
mutation CreatePost($input: CreatePostInput!) {
  createPost(input: $input) {
    id
    title
  }
}
```

### **Subscriptions (Real-Time)**
```graphql
subscription OnPostCreate {
  onPostCreate {
    title
    author { name }
  }
}
```

---

## **4. Schema Reference**
| **Component**       | **Description**                                                                 | **Example**                                                                 |
|----------------------|---------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Root Query**       | Top-level entry point for read operations.                                      | `Query: { posts: [Post!]! }`                                                 |
| **Root Mutation**    | Top-level entry point for write operations.                                      | `Mutation: { createPost: Post! }`                                            |
| **Root Subscription**| Real-time updates via WebSockets.                                                | `Subscription: { onPostUpdate: Post! }`                                       |
| **Types**            | Custom objects with fields (e.g., `User`, `Post`).                              | `type User { id: ID! name: String }`                                         |
| **Interfaces**       | Shared shape between types (e.g., `Node`).                                       | `interface Node { id: ID! }`                                                |
| **Unions**           | Union of multiple types (e.g., `SearchResult`).                                | `union SearchResult = User | Post`                                  |
| **Input Types**      | Data structures for mutations (e.g., `CreateUserInput`).                         | `input CreateUserInput { name: String! }`                                   |
| **Enums**            | Fixed sets of values (e.g., `UserRole`).                                        | `enum UserRole { ADMIN, EDITOR, USER }`                                      |
| **Scalars**          | Custom types (e.g., `Date`, `JSON`).                                             | `scalar Date`                                                                 |
| **Directives**       | Modify execution (e.g., `@auth`).                                                | `@auth(requires: ADMIN)`                                                     |

---

## **5. Query Variables**
GraphQL supports variables for dynamic queries:

```graphql
query GetFilteredPosts($title: String) {
  posts(filter: { title_contains: $title }) {
    title
  }
}
```

**Variables (JSON):**
```json
{ "title": "GraphQL" }
```

---

## **6. Performance Optimization**
- **Use `@deprecated`** for legacy fields.
- **Leverage Apollo Client’s caching** (`@apollo/client`).
- **Implement rate limiting** in middleware.
- **Monitor queries** with Apollo Studio.

---

## **7. Error Handling**
Handle errors gracefully:
```typescript
const resolvers = {
  Query: {
    post: (_, { id }) => {
      if (!id) throw new Error('ID is required');
      // ...
    },
  },
};
```

**Client-side error handling (React Example):**
```javascript
useQuery(GET_POST, {
  variables: { id: '1' },
  errorPolicy: 'all', // Handle all errors
});
```

---

## **8. Deployment**
Deploy with:
- **Serverless:** Apollo Server + AWS Lambda
- **Containerized:** Docker + Kubernetes
- **Edge:** Apollo Federation for microservices

Example Dockerfile:
```dockerfile
FROM node:18
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
CMD ["node", "dist/index.js"]
```

---

## **9. Related Patterns**
| **Pattern**               | **Purpose**                                                                 | **When to Use**                                                                 |
|---------------------------|-----------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **[GraphQL Federation]**   | Combine multiple GraphQL services into a single API.                        | Microservices architecture.                                                     |
| **[Apollo Client]**       | Optimized GraphQL client for browsers/Node.                                | Frontend applications.                                                          |
| **[Relay]**               | Facebook’s GraphQL client with caching.                                     | Large-scale SPAs (e.g., React).                                                 |
| **[GraphQL Persisted Queries]** | Cache query strings to reduce bandwidth.                                  | High-throughput APIs.                                                          |
| **[Query Complexity]**    | Limit query complexity to prevent abuse.                                   | Public APIs (e.g., social media).                                              |
| **[Schema Stitching]**    | Merge schemas from separate GraphQL servers.                               | Legacy system integration.                                                      |

---

## **10. Troubleshooting**
| **Issue**               | **Solution**                                                                 |
|--------------------------|-----------------------------------------------------------------------------|
| **Deprecated Directives** | Update clients or remove `@deprecated` from schema.                       |
| **Slow Queries**         | Use Apollo Tracing or DataLoader.                                           |
| **CORS Errors**          | Configure Apollo Server’s `cors` option.                                      |
| **Type Mismatches**      | Ensure TypeScript interfaces match GraphQL types.                             |
| **WebSocket Subscriptions** | Verify CORS and `allow_credentials` in Apollo Server setup.              |

---
**References:**
- [Apollo Docs](https://www.apollographql.com/docs/)
- [GraphQL Spec](https://spec.graphql.org/)
- [GraphQL Code Generator](https://graphql-code-generator.com/)