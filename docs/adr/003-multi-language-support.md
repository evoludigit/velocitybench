# ADR-003: Multi-Language Framework Support

**Status**: Accepted
**Date**: 2024-01-17
**Author**: VelocityBench Team

## Context

The web development ecosystem is diverse, with frameworks across multiple languages:
- Python: FastAPI, Flask, Strawberry, Graphene
- JavaScript/TypeScript: Express, Apollo Server, Next.js
- Go: gqlgen, Gin
- Java: Spring Boot
- Rust: async-graphql, Actix-web
- PHP: Laravel
- Ruby: Rails
- C#: .NET

To provide comprehensive benchmarking, VelocityBench must support frameworks across all these languages while maintaining fair comparison and equivalent functionality.

## Decision

Implement **language-agnostic benchmarking** with:

### 1. Common API Contracts

Both REST and GraphQL define standardized endpoints/queries that all frameworks must implement:

**REST Endpoints** (mandatory):
```
GET    /ping              - Health check
GET    /users             - List users with pagination
GET    /users/:id         - Get user by ID
POST   /users             - Create user
GET    /posts             - List posts with filtering
GET    /posts/:id         - Get post with author
POST   /posts             - Create post
GET    /comments          - List comments
GET    /comments/:id      - Get comment
POST   /comments          - Create comment
```

**GraphQL Queries** (mandatory):
```graphql
query {
  users(limit: 10, offset: 0) { ... }
  user(id: "1") { ... }
  posts(limit: 10, offset: 0) { ... }
  post(id: "1") { ... }
  comments(limit: 10, offset: 0) { ... }
}

mutation {
  createUser(email: "...", name: "...") { ... }
  createPost(title: "...", content: "...", userId: "1") { ... }
  createComment(text: "...", postId: "1") { ... }
}
```

### 2. Standardized Data Schema

All frameworks use the same Trinity Pattern schema:

```
Write Layer (tb_*)
├── tb_users
├── tb_posts
├── tb_comments
├── tb_personas
└── tb_comment_replies

Projection Layer (v_*)
├── v_users
├── v_posts
├── v_comments
└── v_personas

Composition Layer (tv_*)
├── tv_users_with_stats
├── tv_posts_with_author
├── tv_comments_with_author
└── tv_posts_with_comments
```

All frameworks query the same views, ensuring fair comparison.

### 3. Framework-Specific Implementation

Each language implements the contract in its native idiom:

```python
# Python (FastAPI)
@app.get("/users")
def list_users(limit: int = 10, offset: int = 0):
    return db.query(v_users).limit(limit).offset(offset).all()
```

```javascript
// JavaScript (Express)
app.get("/users", (req, res) => {
    const limit = req.query.limit || 10;
    const offset = req.query.offset || 0;
    db.query(`SELECT * FROM v_users LIMIT $1 OFFSET $2`, [limit, offset])
        .then(users => res.json(users));
});
```

```rust
// Rust (Actix-web)
#[get("/users")]
async fn list_users(
    limit: web::Query<u32>,
    offset: web::Query<u32>,
    db: web::Data<Pool>,
) -> impl Responder {
    let conn = db.get().unwrap();
    let users = v_users
        .limit(limit.into_inner() as i64)
        .offset(offset.into_inner() as i64)
        .load::<User>(&mut conn)
        .unwrap();
    HttpResponse::Ok().json(users)
}
```

### 4. Testing Framework Consistency

CI/CD validates all frameworks implement the contract:

```python
# tests/qa/test_framework_contracts.py
def test_rest_endpoints_exist():
    """Verify all frameworks have required REST endpoints."""
    for framework in FRAMEWORKS:
        response = requests.get(f"{framework['url']}/ping")
        assert response.status_code == 200

def test_graphql_schema_valid():
    """Verify all GraphQL implementations have required fields."""
    for framework in GRAPHQL_FRAMEWORKS:
        result = graphql_query(framework['url'], REQUIRED_QUERY)
        assert "users" in result
        assert "posts" in result
```

## Consequences

### Positive

✅ **Comprehensive Comparison**: Compare Python vs Node vs Go vs Rust fairly
✅ **Fair Metrics**: All frameworks execute identical operations
✅ **Easy Addition**: New language just needs to implement the contract
✅ **Reduced Bias**: No framework gets special optimizations
✅ **Community Value**: Results are meaningful to polyglot developers

### Negative

❌ **Lowest Common Denominator**: Can't use language-specific optimizations
❌ **Constraint Friction**: Each language may have idiomatic differences
❌ **Testing Complexity**: Must test contract compliance across languages
❌ **Documentation Burden**: Must document patterns for 8 languages
❌ **Maintenance**: Bug fixes needed in multiple languages

## Alternatives Considered

### Alternative 1: Language-Specific Tests
- Each language measures its own contract
- Pros: Can use language features, faster
- Cons: Not comparable, unfair, different operations measured
- **Rejected**: Defeats purpose of benchmarking

### Alternative 2: Simple Endpoints Only
- Just implement GET /users, POST /users, etc.
- Pros: Minimal implementation required
- Cons: Doesn't exercise framework capabilities, unrealistic
- **Rejected**: Not representative of real applications

### Alternative 3: Framework in Multiple Languages
- Implement same framework (e.g., FastAPI) in all languages
- Pros: Identical implementation, fair comparison
- Cons: Doesn't compare frameworks, defeats purpose
- **Rejected**: Not what we're benchmarking

## Implementation Strategy

### Phase 1: Core Contract (REST + GraphQL)
- Define REST endpoints
- Define GraphQL queries/mutations
- Schema in PostgreSQL

### Phase 2: Framework Implementation
- Python frameworks (FastAPI, Flask, Strawberry, Graphene)
- JavaScript frameworks (Express, Apollo, Next.js)
- Go frameworks (Gin, gqlgen)
- Java frameworks (Spring Boot)
- Rust frameworks (Actix-web, async-graphql)
- PHP/Ruby/C# frameworks

### Phase 3: Validation
- Integration tests verify contract
- Performance tests measure identical workloads
- Results published with methodology

## Related Decisions

- ADR-001: Trinity Pattern (enforces same schema for all)
- ADR-002: Framework Isolation (supports multiple languages)
- ADR-004: Synthetic Data Generation (same data for all)

## Implementation Status

✅ Complete - 38 frameworks across 8 languages implement contract

## Quality Metrics

**Contract Compliance**:
- ✅ All REST endpoints implemented
- ✅ All GraphQL queries/mutations working
- ✅ All frameworks pass integration tests
- ✅ Response times recorded for identical queries

## References

- [GraphQL Spec](https://spec.graphql.org/)
- [OpenAPI / Swagger](https://swagger.io/specification/)
- [REST API Design Best Practices](https://restfulapi.net/)
- [JSON API Standard](https://jsonapi.org/)
