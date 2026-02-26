# Work-in-Progress Frameworks

These frameworks are not yet production-ready for benchmarking. They are quarantined here to keep the main benchmark registry clean.

## Frameworks

### `rails/`

**Language:** Ruby
**Status:** Stub — no server implementation
**Missing:** Application code, Gemfile, Dockerfile, working API endpoints
**Path to completion:** Implement a minimal Rails API app with `/api/users`, `/api/posts`, and `/health` endpoints backed by the benchmark PostgreSQL schema.

### `spring-graphql/`

**Language:** Java
**Status:** Skeleton — no build configuration
**Missing:** `pom.xml` or `build.gradle`, GraphQL schema, resolver implementations
**Path to completion:** Add a Maven/Gradle build file and implement Spring for GraphQL resolvers for the `users`, `posts`, and `comments` queries.

### `fastify-graphql/`

**Language:** TypeScript / Node.js
**Status:** Incomplete — has `package.json` and tests but no `Dockerfile` or server entry point
**Missing:** `Dockerfile`, `src/index.ts` with a working Fastify + Mercurius GraphQL server
**Path to completion:** Add a `Dockerfile` and implement the GraphQL server against the benchmark schema; verify with `make framework-start FRAMEWORK=fastify-graphql`.

---

Once a framework is complete, move it back to `frameworks/` and register it in:
- `tests/qa/framework_registry.yaml`
- `tests/benchmark/bench_sequential.py` (FRAMEWORKS dict + DEFAULT_FRAMEWORK_ORDER)
- `docker-compose.yml` (add service with appropriate profile)
- `.github/workflows/unit-tests.yml` (add to language matrix)
