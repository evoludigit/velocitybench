# VelocityBench API Documentation

This directory contains comprehensive documentation for all VelocityBench APIs (REST and GraphQL).

## Quick Start

- **REST API**: See [REST.md](./REST.md) for HTTP endpoint documentation
- **GraphQL API**: See [GRAPHQL.md](./GRAPHQL.md) for query/mutation documentation
- **Data Schema**: See [SCHEMA.md](./SCHEMA.md) for database schema details
- **Examples**: See [EXAMPLES.md](./EXAMPLES.md) for code samples

## API Overview

VelocityBench provides two API styles for framework flexibility:

### REST API
- HTTP-based with JSON payloads
- Standard CRUD operations
- Query parameters for filtering/pagination
- Used by: FastAPI, Flask, Express, Gin, Actix-web, Laravel, etc.

### GraphQL API
- Graph query language with strong typing
- Queries for reading data
- Mutations for modifying data
- Subscriptions for real-time updates (supported frameworks)
- Used by: Strawberry, Graphene, Apollo Server, async-graphql, etc.

## Data Models

All frameworks share these core data models:

- **User**: Person using the platform
- **Post**: Blog article or content piece
- **Comment**: Feedback or discussion on a post
- **Persona**: User profile with preferences and interests
- **CommentReply**: Response to a comment

See [SCHEMA.md](./SCHEMA.md) for detailed field definitions.

## Authentication & Authorization

**By Design**: VelocityBench is a benchmarking tool without built-in authentication.

- All endpoints are publicly accessible
- No API keys required
- No authorization checks
- Rationale: Benchmarks measure raw framework performance

**For Production Use**: Implement authentication layers:
- API Gateway (Kong, AWS API Gateway)
- Reverse Proxy (nginx with OAuth)
- Application middleware (JWT, OAuth2)

## Endpoints Summary

### REST Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| **GET** | `/ping` | Health check |
| **GET** | `/users` | List users (paginated) |
| **GET** | `/users/:id` | Get user by ID |
| **POST** | `/users` | Create user |
| **GET** | `/posts` | List posts (paginated, filterable) |
| **GET** | `/posts/:id` | Get post with author |
| **POST** | `/posts` | Create post |
| **GET** | `/comments` | List comments (paginated) |
| **GET** | `/comments/:id` | Get comment |
| **POST** | `/comments` | Create comment |

### GraphQL Queries

```graphql
query {
  # User queries
  users(limit: 10, offset: 0) { ... }
  user(id: "1") { ... }

  # Post queries
  posts(limit: 10, offset: 0) { ... }
  post(id: "1") { ... }

  # Comment queries
  comments(limit: 10, offset: 0) { ... }
  comment(id: "1") { ... }
}
```

### GraphQL Mutations

```graphql
mutation {
  # User mutations
  createUser(email: "...", name: "...") { ... }

  # Post mutations
  createPost(title: "...", content: "...", userId: "1") { ... }

  # Comment mutations
  createComment(text: "...", postId: "1") { ... }
}
```

## Response Format

### Success Response (200 OK)

**REST:**
```json
{
  "status": "success",
  "data": { "id": 1, "name": "John Doe", "email": "john@example.com" },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**GraphQL:**
```json
{
  "data": {
    "user": { "id": "1", "name": "John Doe", "email": "john@example.com" }
  }
}
```

### Error Response (4xx/5xx)

**REST:**
```json
{
  "status": "error",
  "error": "Not Found",
  "message": "User with id 999 not found",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**GraphQL:**
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

## Pagination

### REST Pagination

```
GET /users?limit=20&offset=40

Response:
{
  "data": [ ... 20 users ... ],
  "pagination": {
    "limit": 20,
    "offset": 40,
    "total": 1000
  }
}
```

### GraphQL Pagination

```graphql
query {
  users(limit: 20, offset: 40) {
    id
    name
    email
  }
}
```

## Filtering

### REST Filtering

```
GET /posts?title=sql&author_id=5&limit=10

Returns posts with "sql" in title by author 5
```

### GraphQL Filtering

Currently supported through pagination and query parameters. Full GraphQL filtering available per framework.

## Performance Characteristics

### Expected Response Times

- Typical GET: **10-50 ms** (depends on framework and query complexity)
- Pagination (20 items): **15-100 ms**
- Create (POST): **20-200 ms** (includes database write)
- List with filtering: **30-150 ms** (depends on result set size)

### Load Testing

See [tests/perf/](../../tests/perf/) for performance benchmarking tools.

## Rate Limiting

**No built-in rate limiting**. For production:

```bash
# Example with nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=100r/s;

server {
    location /api/ {
        limit_req zone=api burst=200;
        proxy_pass http://framework_backend;
    }
}
```

## Error Codes

| Code | Status | Meaning | REST | GraphQL |
|------|--------|---------|------|---------|
| 200 | OK | Success | ✅ | ✅ |
| 201 | Created | Resource created | ✅ | ✅ |
| 400 | Bad Request | Invalid parameters | ✅ | Error |
| 401 | Unauthorized | Not authenticated | ✅ | - |
| 403 | Forbidden | Not authorized | ✅ | - |
| 404 | Not Found | Resource not found | ✅ | Error |
| 409 | Conflict | Duplicate resource | ✅ | Error |
| 500 | Server Error | Unexpected error | ✅ | Error |

## Version Control

APIs are versioned for stability:

- **Current Version**: 1.0
- **Breaking Changes**: Major version (v2, v3)
- **Additions**: Minor version (1.1, 1.2)
- **Fixes**: Patch version (1.0.1, 1.0.2)

REST: Use path versioning (`/v1/users`)
GraphQL: Use schema versioning

## Integration Examples

### Python (requests)

```python
import requests

# REST
users = requests.get("http://localhost:8000/users?limit=10")
print(users.json())

# GraphQL
query = """
query {
  users(limit: 10) { id name }
}
"""
response = requests.post(
    "http://localhost:8000/graphql",
    json={"query": query}
)
print(response.json())
```

### JavaScript (fetch)

```javascript
// REST
const users = await fetch("http://localhost:3000/users?limit=10")
  .then(r => r.json());

// GraphQL
const query = `{ users(limit: 10) { id name } }`;
const response = await fetch("http://localhost:3000/graphql", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ query })
});
const data = await response.json();
```

### cURL

```bash
# REST
curl http://localhost:8000/users?limit=10

# GraphQL
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ users(limit: 10) { id name } }"}'
```

## Testing APIs

### Using pytest

```python
import pytest
import requests

def test_get_users():
    response = requests.get("http://localhost:8000/users")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) > 0
```

### Using GraphQL Testing

See [examples/graphql-testing.py](./examples/graphql-testing.py) for full examples.

## Troubleshooting

### Common Issues

**Connection Refused**
```
Error: Cannot connect to http://localhost:8000
Fix: Ensure framework is running: python main.py
```

**Invalid JSON**
```
Error: JSON decode error
Fix: Check Content-Type header: application/json
```

**Timeout**
```
Error: Request timed out
Fix: Increase timeout or check framework performance
```

## API Comparison Table

| Feature | REST | GraphQL |
|---------|------|---------|
| Query Language | HTTP + JSON | GraphQL syntax |
| Payload Size | Larger | Smaller (exact fields) |
| Multiple Resources | Multiple requests | Single request |
| Caching | Easy (HTTP) | Complex |
| Learning Curve | Easy | Moderate |
| Real-time | Polling | Subscriptions |
| Debugging | Easy | Requires tools |

## Related Documentation

- [REST.md](./REST.md) - Detailed REST API reference
- [GRAPHQL.md](./GRAPHQL.md) - Detailed GraphQL reference
- [SCHEMA.md](./SCHEMA.md) - Database and type schemas
- [EXAMPLES.md](./EXAMPLES.md) - Code examples
- [tests/qa/](../../tests/qa/) - Integration tests
- [tests/perf/](../../tests/perf/) - Performance tests

## Specification Files

- [OpenAPI/Swagger](./openapi.yaml) - REST API specification
- [GraphQL Schema](./graphql-schema.graphql) - GraphQL type definitions

## Contributing

To improve API documentation:

1. Update relevant .md file
2. Update OpenAPI/GraphQL specs
3. Add examples if documenting new features
4. Run integration tests to verify

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for contribution guidelines.

---

**Questions?** See [DEVELOPMENT.md](../../DEVELOPMENT.md#troubleshooting) for troubleshooting.
