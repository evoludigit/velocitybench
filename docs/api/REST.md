# REST API Documentation

Complete reference for VelocityBench REST endpoints across all frameworks.

## Base URLs

```
http://localhost:8000    # FastAPI, Flask
http://localhost:3000    # Express, Node frameworks
http://localhost:8080    # Go, Java frameworks
http://localhost:9000    # Other frameworks
```

See [Framework Registry](../../tests/qa/framework_registry.yaml) for specific ports.

## Authentication

No authentication required. All endpoints are public.

## Common Parameters

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 10 | Number of results to return |
| `offset` | integer | 0 | Number of results to skip |
| `sort_by` | string | - | Sort field name |
| `order` | string | asc | Sort order (asc, desc) |

### Request Headers

```
Content-Type: application/json
Accept: application/json
```

### Response Headers

```
Content-Type: application/json
X-Total-Count: <total-records>
X-Request-ID: <unique-request-id>
```

---

## Health Check

### `GET /ping`

Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Status Codes:**
- `200` - Service healthy

---

## Users

### `GET /users`

List all users with pagination.

**Parameters:**
```
GET /users?limit=20&offset=0&sort_by=name&order=asc
```

**Response (200):**
```json
{
  "data": [
    {
      "id": 1,
      "email": "user1@example.com",
      "name": "User One",
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-01-15T10:00:00Z"
    },
    {
      "id": 2,
      "email": "user2@example.com",
      "name": "User Two",
      "created_at": "2024-01-15T10:01:00Z",
      "updated_at": "2024-01-15T10:01:00Z"
    }
  ],
  "pagination": {
    "limit": 20,
    "offset": 0,
    "total": 1000
  }
}
```

### `GET /users/:id`

Get a specific user by ID.

**Parameters:**
```
GET /users/42
```

**Response (200):**
```json
{
  "data": {
    "id": 42,
    "email": "john@example.com",
    "name": "John Doe",
    "created_at": "2024-01-15T10:00:00Z",
    "updated_at": "2024-01-15T10:00:00Z"
  }
}
```

**Response (404):**
```json
{
  "status": "error",
  "error": "Not Found",
  "message": "User with id 999 not found"
}
```

### `POST /users`

Create a new user.

**Request Body:**
```json
{
  "email": "newuser@example.com",
  "name": "New User"
}
```

**Response (201):**
```json
{
  "data": {
    "id": 1001,
    "email": "newuser@example.com",
    "name": "New User",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

**Response (400):**
```json
{
  "status": "error",
  "error": "Bad Request",
  "message": "Email is required"
}
```

**Response (409):**
```json
{
  "status": "error",
  "error": "Conflict",
  "message": "User with email newuser@example.com already exists"
}
```

---

## Posts

### `GET /posts`

List all posts with optional filtering.

**Parameters:**
```
GET /posts?limit=10&offset=0&title=sql&author_id=5
```

**Response (200):**
```json
{
  "data": [
    {
      "id": 1,
      "title": "SQL Performance Tips",
      "content": "Here are some tips for optimizing SQL queries...",
      "author_id": 5,
      "author_name": "Alice Johnson",
      "author_email": "alice@example.com",
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-01-15T10:00:00Z",
      "comment_count": 12
    }
  ],
  "pagination": {
    "limit": 10,
    "offset": 0,
    "total": 345
  }
}
```

### `GET /posts/:id`

Get a specific post with author and comments.

**Parameters:**
```
GET /posts/42
```

**Response (200):**
```json
{
  "data": {
    "id": 42,
    "title": "Getting Started with GraphQL",
    "content": "GraphQL is a query language...",
    "author": {
      "id": 5,
      "name": "Alice Johnson",
      "email": "alice@example.com"
    },
    "comments": [
      {
        "id": 101,
        "text": "Great article!",
        "author_id": 7,
        "author_name": "Bob Smith",
        "created_at": "2024-01-15T10:05:00Z"
      }
    ],
    "comment_count": 3,
    "created_at": "2024-01-15T10:00:00Z",
    "updated_at": "2024-01-15T10:00:00Z"
  }
}
```

### `POST /posts`

Create a new post.

**Request Body:**
```json
{
  "title": "My New Post",
  "content": "This is the content of my new post...",
  "user_id": 5
}
```

**Response (201):**
```json
{
  "data": {
    "id": 5001,
    "title": "My New Post",
    "content": "This is the content of my new post...",
    "author_id": 5,
    "author_name": "Alice Johnson",
    "author_email": "alice@example.com",
    "comment_count": 0,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

---

## Comments

### `GET /comments`

List all comments with pagination.

**Parameters:**
```
GET /comments?limit=20&offset=0&post_id=42
```

**Response (200):**
```json
{
  "data": [
    {
      "id": 1,
      "text": "Great article!",
      "post_id": 42,
      "author_id": 7,
      "author_name": "Bob Smith",
      "author_email": "bob@example.com",
      "created_at": "2024-01-15T10:05:00Z",
      "updated_at": "2024-01-15T10:05:00Z"
    }
  ],
  "pagination": {
    "limit": 20,
    "offset": 0,
    "total": 523
  }
}
```

### `GET /comments/:id`

Get a specific comment.

**Parameters:**
```
GET /comments/1
```

**Response (200):**
```json
{
  "data": {
    "id": 1,
    "text": "Great article!",
    "post_id": 42,
    "post_title": "Getting Started with GraphQL",
    "author_id": 7,
    "author_name": "Bob Smith",
    "author_email": "bob@example.com",
    "created_at": "2024-01-15T10:05:00Z",
    "updated_at": "2024-01-15T10:05:00Z"
  }
}
```

### `POST /comments`

Create a new comment.

**Request Body:**
```json
{
  "text": "This is a great article!",
  "post_id": 42,
  "user_id": 7
}
```

**Response (201):**
```json
{
  "data": {
    "id": 2001,
    "text": "This is a great article!",
    "post_id": 42,
    "author_id": 7,
    "author_name": "Bob Smith",
    "author_email": "bob@example.com",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

---

## Error Responses

### Common Errors

**400 Bad Request**
```json
{
  "status": "error",
  "error": "Bad Request",
  "message": "Invalid limit parameter: must be > 0",
  "details": {
    "field": "limit",
    "value": "-5"
  }
}
```

**404 Not Found**
```json
{
  "status": "error",
  "error": "Not Found",
  "message": "Resource not found"
}
```

**500 Server Error**
```json
{
  "status": "error",
  "error": "Internal Server Error",
  "message": "An unexpected error occurred",
  "request_id": "req-12345"
}
```

---

## Examples

### Get All Users

```bash
curl -H "Accept: application/json" \
  http://localhost:8000/users?limit=50
```

### Create a User

```bash
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "name": "Test User"
  }'
```

### Get Post with Comments

```bash
curl http://localhost:8000/posts/42
```

### Create a Comment

```bash
curl -X POST http://localhost:8000/comments \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Great post!",
    "post_id": 42,
    "user_id": 7
  }'
```

---

## Performance Tips

1. **Use Pagination**: Don't fetch all records at once
   ```
   GET /users?limit=100&offset=0  # Good
   GET /users                      # Bad - might be slow
   ```

2. **Filter Early**: Use query parameters to reduce results
   ```
   GET /posts?author_id=5  # Good - filters in database
   GET /posts              # Bad - fetch all, filter in client
   ```

3. **Batch Operations**: Create multiple resources efficiently
   ```
   POST /users (3x)        # OK
   POST /users/bulk        # Better (if supported)
   ```

---

## Related Documentation

- [API Overview](./README.md)
- [GraphQL API](./GRAPHQL.md)
- [Schema Reference](./SCHEMA.md)
- [Examples](./EXAMPLES.md)
