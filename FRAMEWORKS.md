# VelocityBench Framework Registry

Comprehensive list of all frameworks tested in VelocityBench, organized by tier, type, and readiness status.

## Quick Summary

| Category | Count | Languages |
|----------|-------|-----------|
| **Tier 1: Production-Ready** | 18 | Python, Node.js, Go, Rust, Java, C#, PHP |
| **Tier 2: N+1 Demonstration** | 4 | Node.js, Java |
| **Tier 3: Pending Implementation** | 15 | Various |

---

## Port Strategy

**All frameworks use standardized ports:**

| Type | Internal Port | Host Port | Notes |
|------|---------------|-----------|-------|
| **GraphQL** | 4000 | 4000 | All GraphQL frameworks |
| **REST** | 8080 | 8080 | All REST frameworks |

**Why standardized ports?**
- Benchmarks run **one framework at a time** (no resource contention)
- JMeter configuration stays simple (always targets same port)
- No port conflicts between services
- Matches production deployment patterns

**Usage:**
```bash
# Start a specific framework (only one at a time)
docker-compose up -d fraiseql      # GraphQL on :4000
docker-compose up -d fastapi-rest  # REST on :8080

# Run benchmark against standard port
jmeter -Jhost=localhost -Jport=4000 ...
```

---

## Tier 1: Production-Ready

Optimized implementations for fair performance comparison. All frameworks in this tier have:
- Connection pooling configured
- Health check endpoints (`/health`)
- Prometheus metrics (`/metrics`)
- Passing smoke tests

### GraphQL Frameworks

| Framework | Language | Directory | Internal Port | Status | Notes |
|-----------|----------|-----------|---------------|--------|-------|
| **FraiseQL** | Python | `fraiseql/` | 4000 | Ready | JSONB pre-composition, zero N+1 |
| **Strawberry** | Python | `strawberry/` | 4000 | Ready | DataLoader batching |
| **Graphene** | Python | `graphene/` | 4000 | Ready | DataLoader batching |
| **Apollo Server** | Node.js | `apollo-server/` | 4000 | Ready | DataLoader batching |
| **Mercurius** | Node.js | `mercurius/` | 4000 | Ready | Fastify-based, DataLoader |
| **gqlgen** | Go | `go-gqlgen/` | 4000 | Ready | Code-gen, DataLoader |
| **async-graphql** | Rust | `async-graphql/` | 4000 | Ready | High performance |
| **Spring GraphQL** | Java | `spring-graphql/` | 4000 | Ready | Enterprise-grade |
| **HotChocolate** | C# | `csharp-dotnet/` | 4000 | Ready | .NET 9, Entity Framework |
| **PostGraphile** | Node.js | `postgraphile/` | 4000 | Ready | Auto-generated from DB schema (profile: postgraphile) |
| **Hasura** | Docker | `hasura/` | 4000 | Ready | Auto-generated GraphQL engine (profile: hasura) |

### REST Frameworks

| Framework | Language | Directory | Internal Port | Status | Notes |
|-----------|----------|-----------|---------------|--------|-------|
| **FastAPI** | Python | `fastapi-rest/` | 8080 | Ready | Async, include params |
| **Flask** | Python | `flask-rest/` | 8080 | Ready | Sync, traditional |
| **Express** | Node.js | `express-rest/` | 8080 | Ready | TypeScript, include params |
| **Gin** | Go | `gin-rest/` | 8080 | Ready | High performance |
| **Actix-web** | Rust | `actix-web-rest/` | 8080 | Ready | Ultra-high performance |
| **Spring Boot** | Java | `java-spring-boot/` | 8080 | Ready | Enterprise-grade |
| **Laravel** | PHP | `php-laravel/` | 8080 | Ready | Full-stack PHP |

---

## Tier 2: N+1 Demonstration (Educational)

Naive ORM implementations intentionally showing query explosion impact. Used to demonstrate the N+1 problem and the value of optimization.

| Framework | Optimized Variant | Directory | Internal Port | Purpose |
|-----------|-------------------|-----------|---------------|---------|
| **Apollo ORM** | Apollo Server | `apollo-orm/` | 4000 | Show N+1 impact |
| **Express ORM** | Express REST | `express-orm/` | 8080 | Show N+1 impact |
| **Spring Boot ORM Naive** | Spring Boot | `spring-boot-orm-naive/` | 8080 | Show N+1 impact |
| **Spring Boot ORM** | Spring Boot | `spring-boot-orm/` | 8080 | Moderate optimization |

---

## Tier 3: Pending Implementation

Frameworks with stub directories that need full implementation. All will use standardized ports.

### Python GraphQL (Port 4000)
| Framework | Directory | Notes |
|-----------|-----------|-------|
| **Ariadne** | `ariadne/` | Schema-first GraphQL |
| **ASGI GraphQL** | `asgi-graphql/` | Generic ASGI with graphql-core |

### Node.js GraphQL (Port 4000)
| Framework | Directory | Notes |
|-----------|-----------|-------|
| **GraphQL Yoga** | `graphql-yoga/` | Modern Node.js server |
| **Fastify GraphQL** | `fastify-graphql/` | Fastify + Mercurius |
| **Express GraphQL** | `express-graphql/` | Legacy middleware |

### Go GraphQL (Port 4000)
| Framework | Directory | Notes |
|-----------|-----------|-------|
| **graphql-go** | `graphql-go/` | Reflection-based (vs gqlgen code-gen) |
| **go-graphql-go** | `go-graphql-go/` | Has tests, needs server impl |

### Rust GraphQL (Port 4000)
| Framework | Directory | Notes |
|-----------|-----------|-------|
| **Juniper** | `juniper/` | Alternative to async-graphql |

### Ruby (Port 4000 GraphQL, 8080 REST)
| Framework | Directory | Notes |
|-----------|-----------|-------|
| **Ruby on Rails** | `ruby-rails/` | Fixed, needs verification |
| **Rails** | `rails/` | Possible duplicate |
| **Hanami** | `hanami/` | Lightweight Ruby framework |

### PHP GraphQL (Port 4000)
| Framework | Directory | Notes |
|-----------|-----------|-------|
| **webonyx GraphQL PHP** | `webonyx-graphql-php/` | Core PHP GraphQL library |

### JVM GraphQL (Port 4000)
| Framework | Directory | Notes |
|-----------|-----------|-------|
| **Micronaut GraphQL** | `micronaut-graphql/` | Lightweight JVM |
| **Quarkus GraphQL** | `quarkus-graphql/` | Native compilation |
| **Play GraphQL** | `play-graphql/` | Scala + Sangria |

---

## Removed Frameworks

The following directories were removed as duplicates or empty stubs:

| Directory | Reason |
|-----------|--------|
| `go-gqlgen.broken/` | Broken, superseded by `go-gqlgen/` |
| `gqlgen/` | Empty duplicate of `go-gqlgen/` |
| `hot-chocolate/` | Empty stub, use `csharp-dotnet/` (HotChocolate) |
| `graphql-net/` | Empty stub |
| `entity-framework-core/` | Empty stub, EF Core in `csharp-dotnet/` |
| `graphql-core-php/` | Redundant, webonyx IS the core library |
| `ruby-rails-fixed/` | Helper repo, fixes applied to `ruby-rails/` |

---

## Framework Checklist

Each Tier 1 framework must have:

- [ ] Entry point file (`main.py`, `app.js`, `main.go`, etc.)
- [ ] `Dockerfile` with health check
- [ ] `/health` endpoint returning HTTP 200
- [ ] `/graphql` endpoint (GraphQL) or REST endpoints per spec
- [ ] **Standardized port**: GraphQL=4000, REST=8080
- [ ] Connection pooling configured (min: 10, max: 50)
- [ ] `/metrics` endpoint for Prometheus
- [ ] Passing smoke test
- [ ] Entry in this document

---

## Docker Compose Structure

```yaml
# Example: Each framework exposes same port
services:
  # GraphQL frameworks - all expose 4000
  fraiseql:
    build: ./frameworks/fraiseql
    ports: ["4000:4000"]
    profiles: ["fraiseql"]

  strawberry:
    build: ./frameworks/strawberry
    ports: ["4000:4000"]
    profiles: ["strawberry"]

  # REST frameworks - all expose 8080
  fastapi-rest:
    build: ./frameworks/fastapi-rest
    ports: ["8080:8080"]
    profiles: ["fastapi-rest"]

  flask-rest:
    build: ./frameworks/flask-rest
    ports: ["8080:8080"]
    profiles: ["flask-rest"]

# Usage:
# docker-compose --profile fraiseql up -d
# docker-compose --profile fastapi-rest up -d
```

---

## Query Efficiency Comparison

How each framework handles the "blog page load" scenario (post + author + 10 comments with authors):

| Framework | Strategy | DB Queries | N+1 Safe | Notes |
|-----------|----------|------------|----------|-------|
| **FraiseQL** | JSONB pre-composition | 1-2 | Yes | tv_* views |
| **Strawberry** | DataLoader batching | 3 | Yes | Batched |
| **Graphene** | DataLoader batching | 3 | Yes | Batched |
| **Apollo** | DataLoader batching | 3 | Yes | Batched |
| **gqlgen** | DataLoader batching | 3 | Yes | Batched |
| **PostGraphile** | Auto-generated | 1-2 | Yes | Smart joins |
| **Hasura** | Auto-generated | 1-2 | Yes | Smart joins |
| **FastAPI REST** | Include params + JOINs | 3-4 | Partial | Requires tuning |
| **Express REST** | Include params + JOINs | 3-4 | Partial | Requires tuning |
| **Naive ORM** | No optimization | 13+ | No | N+1 explosion |

---

## Adding a New Framework

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed instructions on adding a new framework.

Quick steps:
1. Create directory under `frameworks/`
2. Implement standard schema
3. Add Dockerfile exposing **standardized port** (4000 or 8080)
4. Expose `/health` and `/metrics`
5. Add to `docker-compose.yml` with profile
6. Pass smoke test
7. Update this document

---

## Related Documentation

- [BENCHMARK_METHODOLOGY.md](BENCHMARK_METHODOLOGY.md) - How benchmarks are conducted
- [BENCHMARK_RESULTS.md](BENCHMARK_RESULTS.md) - Latest benchmark results
- [README.md](README.md) - Project overview
