# GraphQL API Documentation

Complete reference for VelocityBench GraphQL endpoints across frameworks supporting GraphQL.

## Supported Frameworks

- Strawberry (Python)
- Graphene (Python)
- Apollo Server (Node.js)
- async-graphql (Rust)
- And other GraphQL implementations

## GraphQL Endpoints

```
POST /graphql              # Query/Mutation endpoint
GET  /graphql              # Introspection (some frameworks)
POST /graphql/batch        # Batch queries (if supported)
WS   /graphql              # WebSocket subscriptions (real-time)
GET  /graphql/playground   # GraphQL playground UI
GET  /graphql/schema       # Schema definition
```

## Query Syntax

### Basic Query

```graphql
query {
  users(limit: 10, offset: 0) {
    id
    name
    email
    createdAt
  }
}
```

### With Aliases

```graphql
query {
  recentUsers: users(limit: 5, offset: 0) {
    id
    name
  }
  allUsers: users(limit: 100, offset: 0) {
    id
    name
  }
}
```

### With Fragments

```graphql
fragment UserFields on User {
  id
  name
  email
  createdAt
}

query {
  users(limit: 10) {
    ...UserFields
  }
}
```

---

## Schema Types

### User Type

```graphql
type User {
  id: ID!
  email: String!
  name: String!
  createdAt: DateTime!
  updatedAt: DateTime!
  posts: [Post!]!
  postCount: Int!
}
```

### Post Type

```graphql
type Post {
  id: ID!
  title: String!
  content: String!
  author: User!
  comments: [Comment!]!
  commentCount: Int!
  createdAt: DateTime!
  updatedAt: DateTime!
}
```

### Comment Type

```graphql
type Comment {
  id: ID!
  text: String!
  author: User!
  post: Post!
  createdAt: DateTime!
  updatedAt: DateTime!
}
```

---

## Queries

### Users Query

```graphql
query {
  users(limit: 10, offset: 0) {
    id
    name
    email
    createdAt
  }
}
```

**Parameters:**
- `limit` (Int): Number of results (default: 10)
- `offset` (Int): Results to skip (default: 0)

**Response:**
```json
{
  "data": {
    "users": [
      {
        "id": "1",
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "createdAt": "2024-01-15T10:00:00Z"
      }
    ]
  }
}
```

### User Query (Single)

```graphql
query {
  user(id: "42") {
    id
    name
    email
    posts(limit: 5) {
      id
      title
    }
    postCount
  }
}
```

**Parameters:**
- `id` (ID!): User ID (required)

### Posts Query

```graphql
query {
  posts(limit: 20, offset: 0) {
    id
    title
    author {
      id
      name
    }
    commentCount
    createdAt
  }
}
```

### Post Query (Single)

```graphql
query {
  post(id: "42") {
    id
    title
    content
    author {
      id
      name
      email
    }
    comments(limit: 10) {
      id
      text
      author {
        name
      }
    }
  }
}
```

### Comments Query

```graphql
query {
  comments(limit: 50) {
    id
    text
    author {
      name
    }
    post {
      id
      title
    }
    createdAt
  }
}
```

### Comments by Post

```graphql
query {
  post(id: "42") {
    title
    comments {
      id
      text
      author {
        name
      }
    }
  }
}
```

---

## Mutations

### Create User

```graphql
mutation {
  createUser(input: {
    email: "newuser@example.com"
    name: "New User"
  }) {
    id
    email
    name
    createdAt
  }
}
```

**Input:**
- `email` (String!): User email
- `name` (String!): User name

### Create Post

```graphql
mutation {
  createPost(input: {
    title: "My First Post"
    content: "This is the content..."
    userId: "5"
  }) {
    id
    title
    author {
      name
    }
    createdAt
  }
}
```

**Input:**
- `title` (String!): Post title
- `content` (String!): Post content
- `userId` (ID!): Author user ID

### Create Comment

```graphql
mutation {
  createComment(input: {
    text: "Great post!"
    postId: "42"
    userId: "7"
  }) {
    id
    text
    author {
      name
    }
    post {
      title
    }
    createdAt
  }
}
```

**Input:**
- `text` (String!): Comment text
- `postId` (ID!): Post ID
- `userId` (ID!): Author user ID

---

## Subscriptions

### Post Created (Real-time)

```graphql
subscription {
  postCreated {
    id
    title
    author {
      name
    }
  }
}
```

**Availability**: Only frameworks with subscription support (Strawberry, Apollo Server with WebSocket)

---

## Batch Queries

```graphql
query {
  users(limit: 10) { id name }
  posts(limit: 10) { id title }
  comments(limit: 10) { id text }
}
```

Response returns all three queries together:
```json
{
  "data": {
    "users": [...],
    "posts": [...],
    "comments": [...]
  }
}
```

---

## Error Handling

### Validation Error

```json
{
  "errors": [
    {
      "message": "Argument \"limit\" has invalid value -5",
      "extensions": {
        "code": "BAD_USER_INPUT"
      }
    }
  ]
}
```

### Not Found Error

```json
{
  "errors": [
    {
      "message": "User with id 999 not found",
      "extensions": {
        "code": "NOT_FOUND"
      }
    }
  ]
}
```

### Server Error

```json
{
  "errors": [
    {
      "message": "Internal server error",
      "extensions": {
        "code": "INTERNAL_SERVER_ERROR"
      }
    }
  ]
}
```

---

## Request Format

### HTTP POST

```http
POST /graphql HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "query": "{ users(limit: 10) { id name } }"
}
```

### With Variables

```http
POST /graphql HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "query": "query GetUsers($limit: Int!) { users(limit: $limit) { id name } }",
  "variables": {
    "limit": 20
  }
}
```

### With Operation Name

```http
POST /graphql HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "query": "query GetUsers { ... } query GetPosts { ... }",
  "operationName": "GetUsers"
}
```

---

## Examples

### Python (graphql-core)

```python
from graphql import graphql_sync, build_schema

schema = build_schema(SCHEMA_STRING)

result = graphql_sync(
    schema,
    """
    query {
      users(limit: 10) {
        id
        name
      }
    }
    """
)

print(result.data)
```

### JavaScript (apollo-client)

```javascript
import { gql, ApolloClient } from "@apollo/client";

const query = gql`
  query GetUsers($limit: Int!) {
    users(limit: $limit) {
      id
      name
    }
  }
`;

const result = await client.query({
  query,
  variables: { limit: 10 }
});

console.log(result.data);
```

### With curl

```bash
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ users(limit: 10) { id name } }"
  }'
```

---

## Introspection

Get schema information:

```graphql
query {
  __schema {
    types {
      name
      kind
      fields {
        name
        type {
          name
        }
      }
    }
  }
}
```

Get query type:

```graphql
query {
  __type(name: "Query") {
    name
    fields {
      name
      args {
        name
        type { name }
      }
      type { name }
    }
  }
}
```

---

## Performance Tips

1. **Request Only Needed Fields**
   ```graphql
   # Good - specific fields
   query {
     users { id name }
   }

   # Bad - all fields
   query {
     users { id name email createdAt updatedAt ... }
   }
   ```

2. **Use Pagination**
   ```graphql
   # Good - paginated
   query {
     users(limit: 20, offset: 0) { id }
   }

   # Bad - unbounded
   query {
     users { id }  # Could fetch thousands
   }
   ```

3. **Batch Related Queries**
   ```graphql
   # Good - one request
   query {
     user(id: "5") { name posts { title } }
   }

   # Bad - multiple requests
   query { user(id: "5") { name } }
   query { posts(userId: "5") { title } }
   ```

4. **Limit Nested Depth**
   ```graphql
   # Good - shallow depth
   query {
     posts {
       title
       author { name }
     }
   }

   # Risky - deep nesting
   query {
     posts {
       comments {
         author {
           posts {
             comments { ... }
           }
         }
       }
     }
   }
   ```

---

## Schema Definition

Download complete schema:

```bash
# GraphQL SDL
curl http://localhost:8000/graphql/schema

# Introspection JSON
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __schema { ... } }"}'
```

---

## Related Documentation

- [API Overview](./README.md)
- [REST API](./REST.md)
- [Schema Reference](./SCHEMA.md)
- [Examples](./EXAMPLES.md)
- [GraphQL Spec](https://spec.graphql.org/)
