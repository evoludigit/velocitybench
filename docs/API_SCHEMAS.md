# API Schemas Reference

## Overview

VelocityBench provides two API types across 35+ frameworks:

1. **REST APIs** (FastAPI, Flask, Express, Gin, etc.) - HTTP resource-based
2. **GraphQL APIs** (Strawberry, Apollo, Graphene, Ariadne, etc.) - Query-based

Both implement the **same operations** on the same **Trinity Pattern schema**, enabling consistent benchmarking across paradigms.

---

## REST API Operations

### Endpoints Summary

| Operation | Method | Endpoint | Status Codes |
|-----------|--------|----------|-------------|
| List users | `GET` | `/users` | 200, 400 |
| Get user | `GET` | `/users/{id}` | 200, 404 |
| Create user | `POST` | `/users` | 201, 400 |
| Update user | `PUT` | `/users/{id}` | 200, 400, 404 |
| Delete user | `DELETE` | `/users/{id}` | 204, 404 |
| List posts | `GET` | `/posts` | 200, 400 |
| Get post | `GET` | `/posts/{id}` | 200, 404 |
| Create post | `POST` | `/posts` | 201, 400 |
| Update post | `PUT` | `/posts/{id}` | 200, 400, 404 |
| List comments | `GET` | `/posts/{post_id}/comments` | 200, 400 |
| Get comment | `GET` | `/comments/{id}` | 200, 404 |
| Create comment | `POST` | `/comments` | 201, 400 |

---

## REST Request/Response Examples

### Users

#### List Users
```http
GET /users?skip=0&limit=10 HTTP/1.1
Host: localhost:8000

---

HTTP/1.1 200 OK
Content-Type: application/json

[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "alice",
    "email": "alice@example.com",
    "first_name": "Alice",
    "last_name": "Smith",
    "bio": "Software engineer",
    "avatar_url": "https://example.com/avatar.jpg",
    "is_active": true,
    "created_at": "2025-01-31T10:00:00Z",
    "updated_at": "2025-01-31T10:00:00Z"
  }
]
```

#### Get User
```http
GET /users/550e8400-e29b-41d4-a716-446655440000 HTTP/1.1

---

HTTP/1.1 200 OK
Content-Type: application/json

{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "alice",
  "email": "alice@example.com",
  "first_name": "Alice",
  "last_name": "Smith",
  "bio": "Software engineer",
  "avatar_url": null,
  "is_active": true,
  "created_at": "2025-01-31T10:00:00Z",
  "updated_at": "2025-01-31T10:00:00Z"
}
```

#### Get User with Posts (nested)
```http
GET /users/550e8400-e29b-41d4-a716-446655440000?include=posts HTTP/1.1

---

HTTP/1.1 200 OK
Content-Type: application/json

{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "alice",
  "email": "alice@example.com",
  "first_name": "Alice",
  "last_name": "Smith",
  "bio": "Software engineer",
  "avatar_url": null,
  "is_active": true,
  "created_at": "2025-01-31T10:00:00Z",
  "updated_at": "2025-01-31T10:00:00Z",
  "posts": [
    {
      "id": "a0a0a0a0-b1b1-c2c2-d3d3-e4e4e4e4e4e4",
      "title": "My First Post",
      "content": "Hello world!",
      "excerpt": null,
      "status": "published",
      "published_at": "2025-01-31T10:30:00Z",
      "created_at": "2025-01-31T10:30:00Z",
      "updated_at": "2025-01-31T10:30:00Z"
    }
  ]
}
```

#### Create User
```http
POST /users HTTP/1.1
Content-Type: application/json

{
  "username": "bob",
  "email": "bob@example.com",
  "first_name": "Bob",
  "last_name": "Jones",
  "bio": "Data scientist"
}

---

HTTP/1.1 201 Created
Content-Type: application/json
Location: /users/b1b1b1b1-c2c2-d3d3-e4e4-f5f5f5f5f5f5

{
  "id": "b1b1b1b1-c2c2-d3d3-e4e4-f5f5f5f5f5f5",
  "username": "bob",
  "email": "bob@example.com",
  "first_name": "Bob",
  "last_name": "Jones",
  "bio": "Data scientist",
  "avatar_url": null,
  "is_active": true,
  "created_at": "2025-01-31T14:00:00Z",
  "updated_at": "2025-01-31T14:00:00Z"
}
```

#### Update User
```http
PUT /users/550e8400-e29b-41d4-a716-446655440000 HTTP/1.1
Content-Type: application/json

{
  "first_name": "Alicia",
  "bio": "Senior software engineer"
}

---

HTTP/1.1 200 OK
Content-Type: application/json

{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "alice",
  "email": "alice@example.com",
  "first_name": "Alicia",
  "last_name": "Smith",
  "bio": "Senior software engineer",
  "avatar_url": null,
  "is_active": true,
  "created_at": "2025-01-31T10:00:00Z",
  "updated_at": "2025-01-31T14:30:00Z"
}
```

#### Delete User
```http
DELETE /users/550e8400-e29b-41d4-a716-446655440000 HTTP/1.1

---

HTTP/1.1 204 No Content
```

---

### Posts

#### List Posts
```http
GET /posts?skip=0&limit=20&status=published HTTP/1.1

---

HTTP/1.1 200 OK
Content-Type: application/json

[
  {
    "id": "a0a0a0a0-b1b1-c2c2-d3d3-e4e4e4e4e4e4",
    "title": "GraphQL Best Practices",
    "content": "...",
    "excerpt": "Learn how to structure your GraphQL APIs...",
    "status": "published",
    "published_at": "2025-01-31T10:00:00Z",
    "created_at": "2025-01-31T10:00:00Z",
    "updated_at": "2025-01-31T10:00:00Z"
  }
]
```

#### Get Post with Author and Comments
```http
GET /posts/a0a0a0a0-b1b1-c2c2-d3d3-e4e4e4e4e4e4?include=author,comments HTTP/1.1

---

HTTP/1.1 200 OK
Content-Type: application/json

{
  "id": "a0a0a0a0-b1b1-c2c2-d3d3-e4e4e4e4e4e4",
  "title": "GraphQL Best Practices",
  "content": "...",
  "excerpt": "Learn how to structure...",
  "status": "published",
  "published_at": "2025-01-31T10:00:00Z",
  "created_at": "2025-01-31T10:00:00Z",
  "updated_at": "2025-01-31T10:00:00Z",
  "author": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "alice",
    "email": "alice@example.com"
  },
  "comments": [
    {
      "id": "c5c5c5c5-d6d6-e7e7-f8f8-a9a9a9a9a9a9",
      "content": "Great article!",
      "is_approved": true,
      "created_at": "2025-01-31T11:00:00Z"
    }
  ]
}
```

#### Create Post
```http
POST /posts HTTP/1.1
Content-Type: application/json

{
  "author_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "My New Blog Post",
  "content": "This is the post content...",
  "excerpt": "A preview of the content",
  "status": "draft"
}

---

HTTP/1.1 201 Created

{
  "id": "a1a1a1a1-b2b2-c3c3-d4d4-e5e5e5e5e5e5",
  "title": "My New Blog Post",
  "content": "This is the post content...",
  "excerpt": "A preview of the content",
  "status": "draft",
  "published_at": null,
  "created_at": "2025-01-31T15:00:00Z",
  "updated_at": "2025-01-31T15:00:00Z"
}
```

---

### Comments

#### List Comments on Post
```http
GET /posts/a0a0a0a0-b1b1-c2c2-d3d3-e4e4e4e4e4e4/comments HTTP/1.1

---

HTTP/1.1 200 OK
Content-Type: application/json

[
  {
    "id": "c5c5c5c5-d6d6-e7e7-f8f8-a9a9a9a9a9a9",
    "content": "Great article!",
    "is_approved": true,
    "created_at": "2025-01-31T11:00:00Z",
    "updated_at": "2025-01-31T11:00:00Z"
  }
]
```

#### Create Comment
```http
POST /comments HTTP/1.1
Content-Type: application/json

{
  "post_id": "a0a0a0a0-b1b1-c2c2-d3d3-e4e4e4e4e4e4",
  "author_id": "550e8400-e29b-41d4-a716-446655440000",
  "content": "Excellent post!"
}

---

HTTP/1.1 201 Created

{
  "id": "c5c5c5c5-d6d6-e7e7-f8f8-a9a9a9a9a9a9",
  "content": "Excellent post!",
  "is_approved": true,
  "created_at": "2025-01-31T15:30:00Z",
  "updated_at": "2025-01-31T15:30:00Z"
}
```

---

## GraphQL Operations

### Schema Overview

```graphql
type User {
  id: ID!
  username: String!
  email: String!
  firstName: String
  lastName: String
  bio: String
  avatarUrl: String
  isActive: Boolean!
  createdAt: DateTime!
  updatedAt: DateTime!
  posts: [Post!]!
  followers: [User!]!
  following: [User!]!
}

type Post {
  id: ID!
  title: String!
  content: String
  excerpt: String
  status: PostStatus!
  publishedAt: DateTime
  createdAt: DateTime!
  updatedAt: DateTime!
  author: User!
  comments: [Comment!]!
  categories: [Category!]!
  likesCount: Int!
}

type Comment {
  id: ID!
  content: String!
  isApproved: Boolean!
  createdAt: DateTime!
  updatedAt: DateTime!
  author: User!
  post: Post!
  replies: [Comment!]!
}

type Category {
  id: ID!
  name: String!
  slug: String!
  description: String
  posts: [Post!]!
}

enum PostStatus {
  DRAFT
  PUBLISHED
  ARCHIVED
}

type Query {
  user(id: ID!): User
  users(skip: Int, limit: Int): [User!]!
  post(id: ID!): Post
  posts(status: PostStatus, skip: Int, limit: Int): [Post!]!
  comment(id: ID!): Comment
  category(slug: String!): Category
  categories: [Category!]!
}

type Mutation {
  createUser(input: CreateUserInput!): User!
  updateUser(id: ID!, input: UpdateUserInput!): User!
  deleteUser(id: ID!): Boolean!

  createPost(input: CreatePostInput!): Post!
  updatePost(id: ID!, input: UpdatePostInput!): Post!
  deletePost(id: ID!): Boolean!
  publishPost(id: ID!): Post!

  createComment(input: CreateCommentInput!): Comment!
  deleteComment(id: ID!): Boolean!

  followUser(userId: ID!): User!
  unfollowUser(userId: ID!): User!
  likePost(postId: ID!): Post!
  unlikePost(postId: ID!): Post!
}
```

---

## GraphQL Request/Response Examples

### Query User
```graphql
query {
  user(id: "550e8400-e29b-41d4-a716-446655440000") {
    id
    username
    email
    firstName
    lastName
    bio
    createdAt
  }
}
```

**Response**:
```json
{
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "username": "alice",
      "email": "alice@example.com",
      "firstName": "Alice",
      "lastName": "Smith",
      "bio": "Software engineer",
      "createdAt": "2025-01-31T10:00:00Z"
    }
  }
}
```

### Query User with Posts
```graphql
query {
  user(id: "550e8400-e29b-41d4-a716-446655440000") {
    id
    username
    posts {
      id
      title
      status
      createdAt
    }
  }
}
```

**Response**:
```json
{
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "username": "alice",
      "posts": [
        {
          "id": "a0a0a0a0-b1b1-c2c2-d3d3-e4e4e4e4e4e4",
          "title": "GraphQL Best Practices",
          "status": "PUBLISHED",
          "createdAt": "2025-01-31T10:00:00Z"
        }
      ]
    }
  }
}
```

### Query Post with Author and Comments
```graphql
query {
  post(id: "a0a0a0a0-b1b1-c2c2-d3d3-e4e4e4e4e4e4") {
    id
    title
    content
    status
    author {
      id
      username
      email
    }
    comments {
      id
      content
      author {
        id
        username
      }
      createdAt
    }
  }
}
```

### Mutation: Create User
```graphql
mutation {
  createUser(input: {
    username: "bob"
    email: "bob@example.com"
    firstName: "Bob"
    lastName: "Jones"
  }) {
    id
    username
    email
    createdAt
  }
}
```

**Response**:
```json
{
  "data": {
    "createUser": {
      "id": "b1b1b1b1-c2c2-d3d3-e4e4-f5f5f5f5f5f5",
      "username": "bob",
      "email": "bob@example.com",
      "createdAt": "2025-01-31T14:00:00Z"
    }
  }
}
```

### Mutation: Create Post
```graphql
mutation {
  createPost(input: {
    authorId: "550e8400-e29b-41d4-a716-446655440000"
    title: "New Blog Post"
    content: "This is the post content..."
    status: DRAFT
  }) {
    id
    title
    status
    createdAt
  }
}
```

### Mutation: Create Comment
```graphql
mutation {
  createComment(input: {
    postId: "a0a0a0a0-b1b1-c2c2-d3d3-e4e4e4e4e4e4"
    authorId: "550e8400-e29b-41d4-a716-446655440000"
    content: "Great post!"
  }) {
    id
    content
    author {
      username
    }
    createdAt
  }
}
```

---

## Common Query Patterns

### REST Pattern: Get User with Posts and Comments

**Option 1: Include Parameter**
```http
GET /users/550e8400-e29b-41d4-a716-446655440000?include=posts.comments.author HTTP/1.1
```

**Option 2: Separate Requests**
```http
GET /users/550e8400-e29b-41d4-a716-446655440000
GET /users/550e8400-e29b-41d4-a716-446655440000/posts
GET /posts/{postId}/comments
```

**Option 3: GraphQL (Single Request)**
```graphql
query {
  user(id: "550e8400-e29b-41d4-a716-446655440000") {
    id
    posts {
      id
      comments {
        id
        author { username }
      }
    }
  }
}
```

---

## Error Responses

### REST Error Format
```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "detail": "Invalid email format",
  "status": 400,
  "title": "Validation Error",
  "type": "validation_error"
}
```

### Common REST Status Codes
| Code | Meaning | Example |
|------|---------|---------|
| 200 | OK | User fetched successfully |
| 201 | Created | User created successfully |
| 204 | No Content | User deleted successfully |
| 400 | Bad Request | Invalid input (missing field, wrong format) |
| 404 | Not Found | User with ID not found |
| 409 | Conflict | Username already exists |
| 422 | Unprocessable Entity | Validation failed |
| 500 | Internal Server Error | Database connection failed |

### GraphQL Error Format
```json
{
  "errors": [
    {
      "message": "User not found",
      "extensions": {
        "code": "NOT_FOUND"
      }
    }
  ],
  "data": null
}
```

---

## Pagination

### REST Pagination
```http
GET /posts?skip=0&limit=20 HTTP/1.1

GET /posts?skip=20&limit=20  # Next page
GET /posts?skip=40&limit=20  # Third page
```

### GraphQL Pagination
```graphql
query {
  posts(skip: 0, limit: 20) {
    id
    title
  }
}
```

---

## Health Check Endpoint

All frameworks provide a health check endpoint for monitoring:

```http
GET /health HTTP/1.1

---

HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "healthy",
  "timestamp": "2025-01-31T15:00:00Z",
  "database": "connected",
  "version": "1.0.0"
}
```

---

## Metrics & Monitoring

### Prometheus Metrics Endpoint (REST)

```http
GET /metrics HTTP/1.1

---

HTTP/1.1 200 OK
Content-Type: text/plain

# HELP rest_requests_total Total API requests
# TYPE rest_requests_total counter
rest_requests_total{method="GET",endpoint="/users"} 1523
rest_requests_total{method="POST",endpoint="/posts"} 456

# HELP rest_request_duration_seconds Request latency
# TYPE rest_request_duration_seconds histogram
rest_request_duration_seconds_bucket{method="GET",endpoint="/users",le="0.1"} 1200
```

### GraphQL Metrics

Most GraphQL frameworks expose metrics via `/metrics` or Prometheus directly:
- `graphql_queries_total` - Total queries executed
- `graphql_mutations_total` - Total mutations executed
- `graphql_request_duration_seconds` - Query execution time

---

## API Differences by Framework

### Input Field Naming

| Style | Framework | Example |
|-------|-----------|---------|
| snake_case | REST (FastAPI, Flask) | `first_name`, `author_id` |
| camelCase | GraphQL (Strawberry, Apollo) | `firstName`, `authorId` |
| camelCase | TypeScript REST (Express) | `firstName`, `authorId` |

Frameworks automatically convert between formats for their respective APIs.

### Response Null Handling

| Framework | Null Fields | Example |
|-----------|----------|---------|
| REST | Include as `null` | `"bio": null` |
| GraphQL | Omit if not requested | (field not in response if not in query) |

### Timestamp Format

All frameworks return timestamps in **ISO 8601 format**:
- `"2025-01-31T10:00:00Z"` - Preferred format (UTC explicit)
- `"2025-01-31T10:00:00+00:00"` - Also valid (UTC timezone)

---

## Testing APIs with Agent Tools

### cURL Examples
```bash
# GET user
curl -X GET "http://localhost:8000/users/550e8400-e29b-41d4-a716-446655440000"

# Create user
curl -X POST "http://localhost:8000/users" \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","email":"alice@example.com"}'

# Update user
curl -X PUT "http://localhost:8000/users/550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{"first_name":"Alice","bio":"Engineer"}'
```

### GraphQL with cURL
```bash
curl -X POST "http://localhost:8000/graphql" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query { user(id: \"550e8400-e29b-41d4-a716-446655440000\") { id username email } }"
  }'
```

---

## Related Documentation

- **Database Schema**: See `docs/DATABASE_SCHEMA.md` for data model
- **Testing**: See `docs/TESTING_README.md` for test patterns
- **Framework Setup**: See individual `frameworks/{name}/README.md`
- **Architecture**: See `docs/ARCHITECTURE.md` for system overview

