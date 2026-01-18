# Plan: Complete Experimental Frameworks Implementation

## Pre-requisites (Before Running Benchmarks)

**Generate test data** - The `post_ids.csv` file only has headers, no data:
```bash
cd /home/lionel/code/velocitybench/tests/perf/scripts
python generate-post-ids.py --count 1000 --output ../data/post_ids.csv
```
This requires the database to be seeded first.

---

## Status Summary

| Phase | Description | Status |
|-------|-------------|--------|
| **Phase 1** | Cleanup Duplicates and Broken Frameworks | ✅ **COMPLETE** |
| **Phase 2** | Configure Auto-Generated Tools (Hasura, PostGraphile) | ✅ **COMPLETE** |
| **Phase 3** | Implement Python GraphQL Frameworks | ✅ **COMPLETE** |
| **Phase 4** | Implement Node.js GraphQL Frameworks | ✅ **COMPLETE** |
| **Phase 5** | Implement Go GraphQL Framework | 🔲 Pending |
| **Phase 6** | Implement Rust GraphQL Framework | 🔲 Pending |
| **Phase 7** | Implement Ruby Framework | 🔲 Pending |
| **Phase 8** | Implement PHP GraphQL Framework | 🔲 Pending |
| **Phase 9** | Implement JVM GraphQL Frameworks | 🔲 Pending |
| **Phase 10** | Update Documentation and Infrastructure | 🔲 Pending |

**Estimated Remaining Effort**: ~35 hours (Phases 1-4 complete = 17 hours saved)

---

## Port Strategy (IMPORTANT)

**All frameworks use standardized ports** since benchmarks run one framework at a time:

| Type | Internal Port | Host Port |
|------|---------------|-----------|
| **GraphQL** | 4000 | 4000 |
| **REST** | 8080 | 8080 |

Docker Compose profiles ensure only one framework runs:
```bash
docker-compose --profile fraiseql up -d      # GraphQL on :4000
docker-compose --profile fastapi-rest up -d  # REST on :8080
```

---

## Phase 1: Cleanup Duplicates and Broken Frameworks ✅ COMPLETE

### What Was Done

**Directories Removed (7 total):**
1. `frameworks/go-gqlgen.broken/` - Broken, superseded by go-gqlgen
2. `frameworks/gqlgen/` - Empty duplicate of go-gqlgen
3. `frameworks/hot-chocolate/` - Empty stub, csharp-dotnet has HotChocolate
4. `frameworks/graphql-net/` - Empty stub
5. `frameworks/entity-framework-core/` - Empty stub (EF Core is in csharp-dotnet)
6. `frameworks/graphql-core-php/` - Redundant, webonyx IS the core PHP GraphQL library
7. `frameworks/ruby-rails-fixed/` - Helper repo, fixes applied to ruby-rails

**Ruby Rails Fixes Applied:**
- Copied models, controllers, and GraphQL types from ruby-rails-fixed to ruby-rails
- Then removed the ruby-rails-fixed helper directory

**Documentation Updated:**
- FRAMEWORKS.md - Added "Removed Frameworks" section and port strategy
- BENCHMARK_METHODOLOGY.md - Added standardized ports documentation

---

## Phase 2: Configure Auto-Generated Tools ✅ COMPLETE

**Completed**: 2026-01-18

### 2.1 Hasura Setup ✅

**Location:** `frameworks/hasura/`

**What Was Done:**
1. ✅ Created `docker-compose.yml` for standalone testing
2. ✅ Created `metadata/` directory structure:
   - `metadata/version.yaml` - Metadata format version
   - `metadata/actions.yaml` - Empty actions config
   - `metadata/databases/databases.yaml` - Database connection config
   - `metadata/databases/default/tables/tables.yaml` - Table tracking with:
     - `benchmark.tb_user` (with posts relationship)
     - `benchmark.tb_post` (with author, comments relationships)
     - `benchmark.tb_comment` (with author, post relationships)
     - `benchmark.tv_user`, `tv_post`, `tv_comment` (JSONB query views)
3. ✅ Created `.env.example` with configuration template
4. ✅ Updated `README.md` with comprehensive documentation
5. ✅ Added to main `docker-compose.yml` with profile: `hasura`

**Port:** 4000 (map Hasura's internal 8080 → 4000)

### 2.2 PostGraphile ✅

**Location:** `frameworks/postgraphile/`

**What Was Done:**
1. ✅ Fixed port from 4003 → 4000 (standardized)
2. ✅ Created `Dockerfile` with health check
3. ✅ Created `.dockerignore` for efficient builds
4. ✅ Created `.env.example` with configuration template
5. ✅ Added to main `docker-compose.yml` with profile: `postgraphile`
6. ✅ Updated smoke test script with profile-based framework support

**Existing Implementation Verified:**
- `src/index.ts` - Express server with health/ready endpoints
- `src/middleware.ts` - PostGraphile configuration for benchmark schema
- `src/db.ts` - pg connection pool with smart tags for schema customization
- `package.json` - Dependencies and build scripts
- `tsconfig.json` - TypeScript configuration

**Port:** 4000 (standardized GraphQL port)

### Additional Updates
- ✅ Removed `go-gqlgen-alt` service from docker-compose.yml (referenced deleted `go-gqlgen.broken/`)
- ✅ Updated `tests/integration/smoke-test.sh` with profile-based framework testing
- ✅ Updated `FRAMEWORKS.md` to show both frameworks as Ready

---

## Phase 3: Implement Python GraphQL Frameworks ✅ COMPLETE

**Completed**: 2026-01-18

### 3.1 Ariadne (Schema-First Python GraphQL) ✅

**Location:** `frameworks/ariadne/`

**What Was Done:**
1. ✅ Created `schema.graphql` - SDL schema definition matching other frameworks
2. ✅ Created `app.py` - Starlette + Ariadne server with:
   - Custom DataLoader implementation for N+1 prevention
   - Query resolvers (ping, user, users, post, posts, comment)
   - Mutation resolver (updateUser)
   - Object type resolvers for nested relationships
   - Context factory with per-request DataLoaders
3. ✅ Created `requirements.txt` with ariadne, starlette, uvicorn, asyncpg
4. ✅ Created `Dockerfile` with health check
5. ✅ Created `.dockerignore` and `.env.example`
6. ✅ Added to docker-compose.yml with profile: `ariadne`

**Port:** 4000 (standardized GraphQL port)

### 3.2 ASGI-GraphQL (Generic graphql-core) ✅

**Location:** `frameworks/asgi-graphql/`

**What Was Done:**
1. ✅ Created `app.py` - Direct graphql-core usage with Starlette:
   - Uses GraphQL reference implementation directly (no framework abstraction)
   - Programmatic schema definition using GraphQLObjectType, GraphQLField, etc.
   - Custom DataLoader implementation
   - All resolvers implemented inline
   - Demonstrates "raw" GraphQL without framework overhead
2. ✅ Created `requirements.txt` with graphql-core, starlette, uvicorn, asyncpg
3. ✅ Created `Dockerfile` with health check
4. ✅ Created `.dockerignore` and `.env.example`
5. ✅ Added to docker-compose.yml with profile: `asgi-graphql`

**Port:** 4000 (standardized GraphQL port)

### Additional Updates
- ✅ Updated smoke-test.sh with ariadne and asgi-graphql entries
- ✅ Updated FRAMEWORKS.md to move both to Tier 1 (Ready)

---

## Phase 4: Implement Node.js GraphQL Frameworks ✅ COMPLETE

**Completed**: 2026-01-18

### 4.1 GraphQL Yoga ✅

**Location:** `frameworks/graphql-yoga/`

**What Was Done:**
1. ✅ Created `src/index.ts` - Server with Yoga and schema
2. ✅ Created `src/db.ts` - pg connection pool
3. ✅ Created `src/dataloaders.ts` - DataLoader for N+1 prevention
4. ✅ Created `package.json` with graphql-yoga, dataloader, pg
5. ✅ Created `tsconfig.json` for TypeScript compilation
6. ✅ Created `Dockerfile` with health check
7. ✅ Created `.dockerignore` and `.env.example`
8. ✅ Added to docker-compose.yml with profile: `graphql-yoga`

**Port:** 4000 (standardized GraphQL port)

### 4.2 Mercurius (Fastify GraphQL) ✅

**Location:** `frameworks/mercurius/`

**What Was Done:**
1. ✅ Created `src/index.ts` - Fastify server with Mercurius
2. ✅ Created `src/db.ts` - pg connection pool
3. ✅ Created `src/dataloaders.ts` - DataLoader for N+1 prevention
4. ✅ Created `package.json` with fastify, mercurius, dataloader, pg
5. ✅ Created `tsconfig.json` for TypeScript compilation
6. ✅ Created `Dockerfile` with health check
7. ✅ Created `.dockerignore` and `.env.example`
8. ✅ Added to docker-compose.yml with profile: `mercurius`

**Note:** `frameworks/fastify-graphql/` remains as stub - Mercurius IS the Fastify GraphQL adapter.

**Port:** 4000 (standardized GraphQL port)

### 4.3 Express-GraphQL ✅

**Location:** `frameworks/express-graphql/`

**What Was Done:**
1. ✅ Created `src/index.ts` - Express server with graphql-http
2. ✅ Created `src/db.ts` - pg connection pool
3. ✅ Created `src/dataloaders.ts` - DataLoader for N+1 prevention
4. ✅ Created `package.json` with express, graphql-http, dataloader, pg
5. ✅ Created `tsconfig.json` for TypeScript compilation
6. ✅ Created `Dockerfile` with health check
7. ✅ Created `.dockerignore` and `.env.example`
8. ✅ Added to docker-compose.yml with profile: `express-graphql`

**Note:** Uses `graphql-http` instead of deprecated `express-graphql` package.

**Port:** 4000 (standardized GraphQL port)

### Additional Updates
- ✅ Updated smoke-test.sh with all 3 new frameworks
- ✅ Updated FRAMEWORKS.md to move frameworks to Tier 1 (Ready)
- ✅ Removed Node.js section from Tier 3 (Pending) in FRAMEWORKS.md

---

## Phase 5: Implement Go GraphQL Framework 🔲 PENDING

**Estimated Effort**: 4 hours

### 5.1 graphql-go (Reflection-Based)

**Location:** `frameworks/graphql-go/`

**Current State:** Empty stub

**Files to Create:**
```
graphql-go/
├── cmd/server/
│   └── main.go         # Server entry point
├── internal/
│   ├── schema/
│   │   └── schema.go   # GraphQL schema definition
│   ├── resolvers/
│   │   └── resolvers.go
│   ├── loaders/
│   │   └── loaders.go  # DataLoader equivalent
│   └── db/
│       └── db.go       # pgx connection pool
├── go.mod
├── go.sum
├── Dockerfile
└── .env.example
```

**Dependencies:**
- github.com/graphql-go/graphql
- github.com/graphql-go/handler
- github.com/jackc/pgx/v5
- github.com/graph-gophers/dataloader/v7
- github.com/prometheus/client_golang

**Port:** 4000

---

## Phase 6: Implement Rust GraphQL Framework 🔲 PENDING

**Estimated Effort**: 5 hours

### 6.1 Juniper (Rust GraphQL)

**Location:** `frameworks/juniper/`

**Files to Create:**
```
juniper/
├── src/
│   ├── main.rs         # Actix-web server
│   ├── schema.rs       # Juniper schema
│   ├── models.rs       # Data models
│   ├── loaders.rs      # DataLoader equivalent
│   └── db.rs           # deadpool-postgres
├── Cargo.toml
├── Dockerfile
└── .env.example
```

**Dependencies:**
- juniper
- juniper_actix
- actix-web
- tokio-postgres
- deadpool-postgres
- prometheus

**Port:** 4000

---

## Phase 7: Implement Ruby Framework 🔲 PENDING

**Estimated Effort**: 4 hours

### 7.1 Hanami (Ruby Web Framework)

**Location:** `frameworks/hanami/`

**Files to Create:**
```
hanami/
├── app/
│   ├── actions/
│   │   └── graphql/execute.rb
│   └── graphql/
│       ├── schema.rb
│       ├── loaders/     # GraphQL::Batch loaders
│       └── types/
├── config/
│   ├── app.rb
│   └── routes.rb
├── lib/
├── Gemfile
├── Dockerfile
└── .env.example
```

**Dependencies:**
- hanami
- graphql-ruby
- graphql-batch (for N+1 prevention)
- pg
- prometheus-client

**Port:** 4000

---

## Phase 8: Implement PHP GraphQL Framework 🔲 PENDING

**Estimated Effort**: 3 hours

### 8.1 webonyx-graphql-php

**Location:** `frameworks/webonyx-graphql-php/`

**Files to Create:**
```
webonyx-graphql-php/
├── public/
│   └── index.php       # Entry point
├── src/
│   ├── Schema.php      # GraphQL schema
│   ├── Resolvers.php   # Query resolvers
│   ├── DataLoader.php  # Batch loading
│   └── Database.php    # PDO connection pool
├── composer.json
├── Dockerfile
└── .env.example
```

**Dependencies:**
- webonyx/graphql-php
- overblog/dataloader-php
- nyholm/psr7
- nyholm/psr7-server

**Port:** 4000

---

## Phase 9: Implement JVM GraphQL Frameworks 🔲 PENDING

**Estimated Effort**: 15 hours

### 9.1 Micronaut-GraphQL

**Location:** `frameworks/micronaut-graphql/`

**Files to Create:**
```
micronaut-graphql/
├── src/main/
│   ├── java/benchmark/
│   │   ├── Application.java
│   │   ├── GraphQLFactory.java
│   │   ├── DataLoaderRegistry.java
│   │   └── resolvers/
│   └── resources/
│       ├── application.yml
│       └── schema.graphqls
├── build.gradle (or pom.xml)
├── Dockerfile
└── .env.example
```

**Dependencies:**
- micronaut-graphql
- micronaut-data-jdbc
- postgresql

**Port:** 4000

### 9.2 Quarkus-GraphQL

**Location:** `frameworks/quarkus-graphql/`

**Files to Create:**
```
quarkus-graphql/
├── src/main/
│   ├── java/benchmark/
│   │   ├── GraphQLResource.java
│   │   ├── DataLoaderConfig.java
│   │   └── resolvers/
│   └── resources/
│       └── application.properties
├── pom.xml
├── Dockerfile
└── .env.example
```

**Dependencies:**
- quarkus-smallrye-graphql
- quarkus-jdbc-postgresql
- quarkus-hibernate-orm-panache

**Port:** 4000

### 9.3 Play-GraphQL (Scala)

**Location:** `frameworks/play-graphql/`

**Files to Create:**
```
play-graphql/
├── app/
│   ├── controllers/
│   │   └── GraphQLController.scala
│   └── graphql/
│       ├── Schema.scala
│       ├── Resolvers.scala
│       └── Fetchers.scala  # Sangria Fetchers for batching
├── conf/
│   ├── application.conf
│   └── routes
├── build.sbt
├── Dockerfile
└── .env.example
```

**Dependencies:**
- play-framework
- sangria (Scala GraphQL)
- sangria-slowlog
- slick (database)

**Port:** 4000

---

## Phase 10: Update Documentation and Infrastructure 🔲 PENDING

**Estimated Effort**: 4 hours

### 10.1 Update docker-compose.yml

Add all new framework services with:
- Health checks
- Port mappings (all using standardized ports)
- Environment variables
- Network configuration
- Docker Compose profiles

Example entry:
```yaml
ariadne:
  build: ./frameworks/ariadne
  ports:
    - "4000:4000"
  environment:
    DATABASE_URL: postgresql://benchmark:benchmark123@postgres:5432/fraiseql_benchmark
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:4000/health"]
    interval: 10s
    timeout: 5s
    retries: 5
  profiles:
    - ariadne
  depends_on:
    postgres:
      condition: service_healthy
```

### 10.2 Update FRAMEWORKS.md

Move all completed frameworks from Tier 3 to Tier 1.

### 10.3 Update Makefile

Add targets for new frameworks:
```makefile
start-%:
	docker-compose --profile $* up -d

smoke-%:
	./tests/integration/smoke-test.sh $*

benchmark-%:
	./tests/perf/scripts/run-benchmark.sh $* blog-page medium
```

### 10.4 Create/Update Smoke Tests

For each new framework, ensure smoke test covers:
- Health endpoint returns 200
- GraphQL introspection works
- Basic query returns data
- Basic mutation works

---

## Success Criteria

After all phases complete:

- [ ] All duplicate/broken directories removed ✅ (Phase 1 complete)
- [ ] 25+ frameworks in Tier 1 (production-ready)
- [ ] Each framework has:
  - [ ] Working `/health` endpoint
  - [ ] Working `/graphql` endpoint (port 4000) or REST endpoints (port 8080)
  - [ ] Dockerfile with health check
  - [ ] Connection pooling configured (min: 10, max: 50)
  - [ ] DataLoader or equivalent for N+1 prevention
  - [ ] Prometheus `/metrics` endpoint
  - [ ] Passing smoke test
- [ ] FRAMEWORKS.md updated with all frameworks
- [ ] docker-compose.yml includes all frameworks with profiles
- [ ] Blog-page benchmark runs successfully on all frameworks

---

## Risk Mitigation

1. **Language expertise**: Some frameworks require specific language knowledge
   - Mitigation: Use reference implementations from existing Tier 1 frameworks
   - Reference: `frameworks/strawberry/` (Python), `frameworks/apollo-server/` (Node.js)

2. **Database schema compatibility**: All frameworks must work with same schema
   - Mitigation: Use `benchmark` schema with tb_*, v_*, tv_* naming
   - Tables: tb_user, tb_post, tb_comment, tb_tag

3. **DataLoader complexity**: N+1 prevention varies by language
   - Python: `aiodataloader`
   - Node.js: `dataloader`
   - Go: `github.com/graph-gophers/dataloader`
   - Rust: Custom or `async-graphql` built-in
   - Ruby: `graphql-batch`
   - PHP: `overblog/dataloader-php`
   - Java: `java-dataloader`

4. **Testing coverage**: Need consistent testing approach
   - Mitigation: Use JMeter smoke tests for all frameworks
   - Verify with `tests/perf/jmeter/workloads/blog-page.jmx`

---

## Remaining Effort Summary

| Phase | Hours |
|-------|-------|
| Phase 2: Auto-gen tools | 4 |
| Phase 3: Python | 6 |
| Phase 4: Node.js | 6 |
| Phase 5: Go | 4 |
| Phase 6: Rust | 5 |
| Phase 7: Ruby | 4 |
| Phase 8: PHP | 3 |
| Phase 9: JVM | 15 |
| Phase 10: Docs | 4 |
| **Total Remaining** | **51 hours** |
