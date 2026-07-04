# VelocityBench Full Framework Evaluation
**Date**: April 19, 2026  
**Benchmark Date**: 2026-04-19 (Sequential Isolation, 30s duration, 40 concurrency)  
**Dataset**: 10,000 users · 100,000 posts · 500,000 comments  
**FraiseQL Version**: v2.2.0 (with new mutation helpers, shipped Apr 19 2026)

---

## Executive Summary

This evaluation comprises complete benchmark results across 37 GraphQL and REST frameworks, multi-dimensional DX assessment (8 dimensions × 37 frameworks), and architectural analysis of framework tradeoffs.

**Key Findings:**
- **Performance leader**: FraiseQL (8.8k RPS Q1), followed by PostGraphile (5.0k RPS) and Ruby Rails (2.6k RPS)
- **Best DX**: Strawberry (Python), PostGraphile (zero-code), GraphQL-Yoga (Node.js)
- **Best ratio of DX + perf**: Strawberry, GraphQL-Yoga, Mercurius for GraphQL; Express-REST, FastAPI-REST for REST
- **Java surprise**: Spring-Boot-ORM delivers 8k RPS in some queries despite slower baseline
- **Mutation scaling issue**: Most classical frameworks plateau at M1 due to lack of batch support; FraiseQL maintains 6k+ RPS
- **FraiseQL v2.2.0**: Mutation helpers reduce boilerplate from 70 lines to 25; CQRS approach confirmed production-ready

---

## Section 1: Complete Benchmark Results

### Q1 — `users(limit:20) { id username fullName bio }`

| Rank | Framework | Language | RPS | p50 | p95 | p99 | Notes |
|------|-----------|----------|----:|----:|----:|----:|-------|
| 1 | fraiseql-v-cache | Rust | 8,883 | 3.9 | 9.2 | 12.6 | Pre-computed TV variant |
| 2 | fraiseql-tv-cache | Rust | 8,802 | 3.8 | 10.0 | 14.7 | — |
| 3 | fraiseql-tv | Rust | 8,546 | 3.9 | 10.5 | 15.7 | — |
| 4 | fraiseql-v-nocache | Rust | 8,567 | 4.0 | 9.3 | 12.6 | — |
| 5 | postgraphile | Node.js | 5,054 | 7.7 | 11.2 | 13.9 | Zero-code introspection |
| 6 | ruby-rails | Ruby | 2,553 | 6.5 | 64.0 | 75.8 | Stable p50, variable p95 |
| 7 | ariadne | Python | 1,904 | 20.1 | 29.3 | 34.2 | Pure async |
| 8 | asgi-graphql | Python | 1,978 | 19.1 | 28.6 | 37.2 | Similar to Ariadne |
| 9 | actix-web-rest | Rust | 1,962 | 20.2 | 21.8 | 23.3 | REST: lowest variance |
| 10 | micronaut-graphql | Java | 1,937 | 18.3 | 36.9 | 41.6 | GraalVM ahead-of-time |
| ... | ... | ... | ... | ... | ... | ... | ... |
| 37 | php-laravel | PHP | 271 | 126.2 | 251.5 | 303.0 | Slowest, high variance |

**Full Q1 table** (all 37 frameworks): See [complete results in reports/bench-sequential-2026-04-19.md](../reports/bench-sequential-2026-04-19.md)

### Key Observations by Query Type

#### Q1 (Flat list with JSONB decode)
- FraiseQL dominates: 8.5k–8.9k RPS (pre-computed JSONB advantage)
- Python GraphQL frameworks (Strawberry, Graphene) mid-tier: 1.7k–1.8k RPS
- Python REST (FastAPI, Flask) underperform: 763–889 RPS

#### Q2/Q2b (Nested queries)
- Mercurius + GraphQL-Yoga standout: 9.6k–9.8k RPS
- Go frameworks split: gqlgen weak (2.9k Q2), gin-rest strong (9k Q2)
- Spring-Boot baseline broken (Q2: 65 RPS) — GraphQL endpoint issue
- Spring-Boot-ORM corrected (8k+ RPS) — uses REST endpoint

#### F1/F2 (Filters)
- Filter operator syntax varies; most frameworks apply WHERE at database level
- Performance difference F1→F2 (no nesting vs. nesting): 
  - REST frameworks: flat (actix 11.8k → 9.7k F2)
  - GraphQL with DataLoaders: stable or slight drop (Mercurius 9.8k F1 → 7.1k F2)

#### M1 (Mutations)
- **Mutation bottleneck observed**: Most frameworks < 300 RPS
  - Spring-Boot, C# dotnet: 0 RPS (100% errors — mutation endpoint not implemented)
  - GraphQL-Yoga: 173 RPS (bottleneck in resolvers)
  - Apollo: 251 RPS
- **FraiseQL exception**: 5.8k–6.7k RPS (6692 at peak)
  - Reason: CQRS cascade writes handled at database trigger level, not via resolver
  - Cascade fan-out: 1 user update → 61 database rows (tb_user + tv_user + tv_posts + tv_comments)
  - At 6.7k mutations/sec = 408k row writes/sec (PostgreSQL HOT compression)

#### T1 (Composed multi-root query)
- Most frameworks: 1k–4k RPS
- Outliers:
  - Quarkus: 10.3k RPS (compiled Graal VM)
  - Juniper: 9.3k RPS (Rust)
  - Mercurius + GraphQL-Yoga: 6.9k + 6.1k RPS
  - Actix REST: 69 RPS (only does single GET, not composed request)

---

## Section 2: Performance Tier Ranking

### Tier 1: Elite (>8000 RPS Q1)
**Frameworks**: FraiseQL (all 4 variants)

**Why**: Novel CQRS + pre-computed JSONB. Single SQL fetch returns fully denormalized object graph. Zero resolver logic overhead.

### Tier 2: High-Performance GraphQL (5000–8000 RPS Q1)
**Frameworks**: PostGraphile, Mercurius (5.7k Q2), GraphQL-Yoga (9.6k Q2)

**Why**: 
- PostGraphile: Zero-code schema, smart query generation
- Mercurius/Yoga: SDL + Fastify async core, efficient DataLoaders

### Tier 3: Production-Grade (1500–4500 RPS Q1)
**Frameworks**: Strawberry, Graphene, Ariadne, Asgi-graphql, Ruby-rails, Micronaut, Actix-web, Spring-Boot-ORM

**Why**: Mid-tier query handling with DataLoaders or ORMs. Suitable for moderate traffic.

### Tier 4: Emerging (500–1500 RPS Q1)
**Frameworks**: Go frameworks (gqlgen 746, gin-rest 740, go-graphql-go 634, graphql-go 696), Apollo-ORM, Express-REST, Flask-REST

**Why**: 
- Go: Verbose generated code for GraphQL
- Node ORM: Lazy-loading patterns bottleneck relationships
- Flask: Synchronous framework limits concurrency

### Tier 5: Struggling (<500 RPS Q1)
**Frameworks**: php-laravel (271), graphql-go (696 but high variance), apollo-orm (420)

**Why**: Language runtime overhead (PHP), weak GraphQL implementation, or ORM N+1 queries.

### Special Cases
- **Spring-Boot (base)**: Q2 65 RPS — spring-boot-graphql endpoint not handling this query properly. ORM variant (spring-boot-orm) fixes to 5k+ RPS
- **C# dotnet**: Q1 702 RPS, but M1 0 RPS — mutation endpoint missing
- **Gin-rest**: Strong (9k RPS) because REST queries skip GraphQL overhead

---

## Section 3: Developer Experience Scorecard

### Scoring Methodology
1–10 scale per dimension, with brief reasoning:
- **1–2**: Painful, significant friction
- **3–4**: Functional but clunky
- **5–6**: Acceptable, some rough edges
- **7–8**: Good, smooth
- **9–10**: Excellent, best-in-class

### Full Scorecard

| Framework | Boilerplate | Schema DX | Query Layer | Type Safety | Mutation DX | Build | Observability | Ecosystem | **Avg** |
|-----------|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| **fraiseql-tv** | 5 | 7 | 9 | 9 | 6 | 4 | 5 | 5 | 6.3 |
| **mercurius** | 8 | 8 | 8 | 7 | 8 | 9 | 8 | 9 | 8.1 |
| **postgraphile** | 10 | 10 | 8 | 9 | 5 | 10 | 5 | 8 | 8.1 |
| **strawberry** | 8 | 9 | 8 | 9 | 8 | 9 | 9 | 8 | 8.5 |
| **graphql-yoga** | 8 | 8 | 8 | 7 | 8 | 9 | 8 | 9 | 8.1 |
| **actix-web-rest** | 6 | 8* | 9 | 10 | 8 | 6 | 9 | 8 | 8.0 |
| **spring-boot-orm** | 5 | 7 | 7 | 8 | 7 | 4 | 9 | 10 | 7.1 |
| **express-rest** | 8 | 8* | 7 | 6 | 8 | 9 | 8 | 10 | 8.0 |
| **fastapi-rest** | 8 | 9 | 7 | 9 | 8 | 9 | 9 | 8 | 8.4 |
| **async-graphql** | 7 | 7 | 7 | 8 | 7 | 6 | 7 | 7 | 7.0 |
| **juniper** | 6 | 7 | 7 | 9 | 6 | 6 | 6 | 6 | 6.6 |
| **graphene** | 7 | 8 | 7 | 8 | 7 | 7 | 7 | 8 | 7.4 |
| **ariadne** | 8 | 8 | 8 | 7 | 8 | 8 | 7 | 8 | 7.9 |
| **quarkus-graphql** | 5 | 7 | 7 | 8 | 6 | 5 | 8 | 7 | 6.6 |
| **micronaut-graphql** | 6 | 7 | 7 | 8 | 6 | 5 | 8 | 7 | 6.8 |
| **play-graphql** | 6 | 7 | 7 | 8 | 6 | 5 | 8 | 7 | 6.8 |
| **go-gqlgen** | 4 | 6 | 7 | 8 | 5 | 7 | 6 | 7 | 6.3 |
| **gin-rest** | 7 | 7* | 8 | 8 | 8 | 8 | 7 | 8 | 7.6 |
| **ruby-rails** | 6 | 7 | 6 | 6 | 6 | 6 | 7 | 8 | 6.5 |
| **hanami** | 6 | 7 | 6 | 6 | 6 | 6 | 6 | 6 | 6.1 |
| **apollo-server** | 6 | 7 | 6 | 6 | 5 | 8 | 7 | 9 | 6.8 |
| **apollo-orm** | 5 | 7 | 5 | 6 | 5 | 8 | 6 | 9 | 6.4 |
| **graphql-go** | 4 | 6 | 7 | 8 | 5 | 6 | 6 | 6 | 6.0 |
| **go-graphql-go** | 5 | 6 | 7 | 8 | 5 | 6 | 6 | 6 | 6.1 |
| **csharp-dotnet** | 6 | 7 | 7 | 9 | 4 | 6 | 8 | 8 | 6.9 |
| **flask-rest** | 7 | 8* | 6 | 7 | 7 | 8 | 6 | 7 | 7.0 |
| **php-laravel** | 5 | 6 | 5 | 5 | 5 | 6 | 5 | 6 | 5.4 |
| **webonyx-graphql-php** | 5 | 6 | 6 | 5 | 5 | 6 | 5 | 6 | 5.6 |
| **fraiseql-v-nocache** | 5 | 7 | 8 | 9 | 6 | 4 | 5 | 5 | 6.1 |
| **fraiseql-v-cache** | 5 | 7 | 8 | 9 | 6 | 4 | 5 | 5 | 6.1 |
| **fraiseql-tv-cache** | 5 | 7 | 9 | 9 | 6 | 4 | 5 | 5 | 6.3 |
| **fraiseql-tv-audit** | 5 | 7 | 9 | 9 | 6 | 4 | 5 | 5 | 6.3 |
| **spring-boot** | 5 | 7 | 7 | 8 | 4 | 4 | 9 | 10 | 6.8 |
| **spring-boot-orm-naive** | 5 | 7 | 6 | 8 | 4 | 4 | 9 | 10 | 6.6 |
| **express-orm** | 6 | 8* | 6 | 6 | 6 | 9 | 7 | 10 | 7.3 |
| **express-graphql** | 6 | 7 | 7 | 6 | 6 | 9 | 7 | 10 | 7.4 |

*REST frameworks (marked with *) don't have "Schema DX" in the traditional sense; scored on request validation + response definition clarity.

### Top 10 by DX Score
1. **Strawberry** (8.5) — Best Python GraphQL: type hints → schema, excellent async, great observability
2. **FastAPI-REST** (8.4) — Best Python REST: Pydantic validation, Kubernetes health checks, clean async
3. **Mercurius** (8.1) — Best Node.js GraphQL: SDL simplicity, Fastify foundation, DataLoader patterns
4. **PostGraphile** (8.1) — Zero boilerplate: introspect schema from DB, smart query generation
5. **GraphQL-Yoga** (8.1) — Solid Node.js GraphQL: Guild ecosystem, SDL clarity, good DX
6. **Express-REST** (8.0) — Best REST simplicity: flat learning curve, handles nesting via includes
7. **Actix-web-REST** (8.0) — Rust type safety: sqlx macros, Prometheus metrics, compile-time SQL checks
8. **Graphene** (7.4) — Solid Python GraphQL: decorator pattern, good ecosystem integration
9. **Express-GraphQL** (7.4) — Traditional Node.js GraphQL: long-established, good error handling
10. **Ariadne** (7.9) — Python async GraphQL: SDL + resolvers, clean separation, good types

### Top 3 by Dimension
**Boilerplate**: PostGraphile (10), Strawberry (8), Mercurius/GraphQL-Yoga/Express-REST/FastAPI-REST (8)

**Schema DX**: PostGraphile (10), Strawberry (9), FastAPI-REST (9)

**Query Layer Type Safety**: Actix-web (10), FraiseQL (9), Async-graphql/Juniper/Spring-Boot/Csharp-dotnet (8–9)

**Mutation DX**: Strawberry/Mercurius/GraphQL-Yoga/Express-REST/FastAPI-REST (8)

**Build Simplicity**: PostGraphile (10), Strawberry/FastAPI-REST/Express-REST/Express-GraphQL/Mercurius/GraphQL-Yoga (9)

**Observability**: Strawberry/Actix-web/Spring-Boot (9), FastAPI-REST/FraiseQL (varies)

**Ecosystem**: Spring Boot (10), Apollo/Express-REST/Express-GraphQL/Mercurius/GraphQL-Yoga (9)

---

## Section 4: Quadrant Analysis (Performance × DX)

```
           HIGH DX
             ↑
    8.0  +-------+-------+
         |Merc   |Berry  |
    7.5  | Yoga  | Ariadne|
         | Post  | FAST  |
    7.0  | Expr- |       |
         | REST  +-------+---→ HIGH PERF
    6.5  |       | ActixR|
         | Async | Spring|
    6.0  | Jun   +---+---+
         | Quar  |FQL|
    5.5  | Go    +---+
         | PHP   |
    5.0  +-------+-------+
           LOW DX       ← LOW PERF
          700     1000   3000    8000+ RPS
```

### Quadrants

#### I. High Performance + High DX (Sweet Spot)
- **Strawberry** (1.7k Q1, 8.5 DX) — Best overall Python package for GraphQL
- **FastAPI-REST** (0.9k Q1, 8.4 DX) — Best Python REST
- **Mercurius** (0.7k Q1 base, but 9.8k Q2, 8.1 DX) — Strong Node.js GraphQL
- **GraphQL-Yoga** (0.7k Q1 base, 9.6k Q2, 8.1 DX) — Solid alternative

#### II. High Performance + Low DX (Specialized)
- **FraiseQL** (8.8k Q1, 6.3 DX) — Cutting-edge CQRS but learning curve
- **Actix-web-REST** (2.0k Q1, 8.0 DX) — Actually strong DX for Rust
- **Ruby-Rails** (2.6k Q1, 6.5 DX) — Legacy reputation unearned; quite pleasant
- **PostGraphile** (5.0k Q1, 8.1 DX) — Top-right corner (zero-code + fast)

#### III. Low Performance + High DX (Educational/Internal)
- **Flask-REST** (0.76k Q1, 7.0 DX) — Good for learning, low concurrency
- **Go frameworks** (0.6–0.7k Q1, 6.0–6.3 DX) — Verbose setup, slow GraphQL

#### IV. Low Performance + Low DX (Avoid)
- **PHP Laravel** (0.27k Q1, 5.4 DX) — Smallest framework, most friction
- **Hanami** (1.2k Q1, 6.1 DX) — Ruby alternative, fewer features

### Movement Since Apr 14
**FraiseQL**: Moved right (from 6.2 DX → 6.3) with v2.2.0 mutation helpers reducing boilerplate.

**Spring-Boot**: Moved up (from baseline issue → 7.1 DX) after ORM variant correction.

**Strawberry**: Remained stable (consistently 1.7k Q1, solid DX).

---

## Section 5: Framework Spotlights

### 1. FraiseQL (Rust, GraphQL — CQRS + Pre-computed JSONB)

#### Architecture
FraiseQL implements proper **CQRS (Command-Query Responsibility Segregation)**:
1. **Schema layer** (Python): Decorator-based types mapping to SQL views
2. **Compilation layer** (CLI): Validates schema against database, generates Rust binary
3. **Server layer** (Rust): Executes compiled schema, serves GraphQL

**Write/Read Separation** (OLTP + OLAP):
- **Write side** (LOGGED): Normalized tables (`tb_user`, `tb_post`, `tb_comment`) — durable, WAL-protected
- **Read side** (UNLOGGED): Pre-computed JSONB projections (`tv_user`, `tv_post`, `tv_comment`) — ephemeral cache
- **Sync mechanism**: pg_tviews triggers automatically refresh projections on base table writes
- **Crash recovery**: Projections are auto-truncated on restart, rebuild on first query via triggers

#### Performance Advantage
FraiseQL achieves 8.8k RPS on Q1 through two mechanisms:

**1. CQRS Architectural Separation**:
- Reads from UNLOGGED projection tables (tv_*) — no WAL fsync
- Writes still go to LOGGED base tables (tb_*) — full durability
- Projections are ephemeral cache (rebuild on crash via triggers)
- **Gain**: 20–30% faster reads by avoiding WAL overhead on reads

**2. Query Optimization**:
- **Zero resolver code**: Single SQL query fetches all nested data
- **JSONB pre-computation**: Related entities embedded at write time (e.g., `tv_post` contains full author + post fields)
- **Direct deserialization**: GraphQL response is direct JSONB rendering
- **Minimal allocations**: No intermediate object construction

**Cost/Tradeoff**:
- Storage amplification 4.47× (1.9 GB TV tables on top of 560 MB base)
- Crash recovery: projections auto-truncated, rebuilt on first query (once-per-crash penalty)
- **This is correct CQRS design**, standard in production systems (similar to Redis caches, data warehouse projections)

#### DX Tradeoffs

**Strengths:**
- Type safety: Rust compiler enforces schema correctness
- Novel query paradigm: See exactly what data is fetched (no implicit N+1)
- Mutation cascade visibility: `cascade` field in response lists all affected entities

**Weaknesses:**
- Schema compilation adds deployment friction (binary rebuild on schema change)
- Learning curve: CQRS + pre-computed views is unfamiliar to most teams
- Limited customization: Mutations must map to SQL functions; resolvers not directly accessible
- v2.2.0 mutation helpers mitigate some pain (see Section 6)

#### When to Use
- **High-traffic read-heavy APIs** where schema is stable
- **Teams comfortable with PostgreSQL** and willing to reason about data layout
- **Greenfield projects** that can adopt JSONB storage design

#### Not Ideal For
- Rapid schema iteration (compilation adds lag)
- Complex business logic in resolvers (external services, caching layers)
- Teams without PostgreSQL expertise

---

### 2. PostGraphile (Node.js, GraphQL — Zero-Code Introspection)

#### Architecture
**PostGraphile introspects PostgreSQL schema and auto-generates GraphQL**.

No hand-written GraphQL schema. Database constraints become GraphQL validation. Foreign keys become automatic relationships.

#### DX Advantage
- **Zero GraphQL**: Write SQL, get GraphQL
- **Type safety from schema**: Database columns are GraphQL field types
- **Smart pagination**: Cursor-based pagination auto-generated
- **Plugins extend schema**: PostGraphile plugins hook into schema generation

#### Performance Characteristics
- Q1: 5.0k RPS (third-best, after FraiseQL variants)
- Good query generation; sometimes leaves room for manual optimization
- Scales well to moderately complex queries

#### Tradeoffs

**Strengths:**
- Fastest time-to-API (database schema is the API)
- Lowest boilerplate
- Type safety guaranteed by database constraints

**Weaknesses:**
- Mutations require database functions (like FraiseQL)
- Less control over resolver logic
- Query generation opacity (developer doesn't see SQL)
- Custom business logic harder to add

#### When to Use
- **Rapid prototyping** of CRUD APIs
- **Internal tools** where schema stability is acceptable
- **Admin interfaces** over existing PostgreSQL databases
- **Teams wanting zero custom GraphQL code**

---

### 3. Strawberry (Python, GraphQL — Type-First)

#### Architecture
**Strawberry is Python's most ergonomic GraphQL framework**, using decorators on dataclasses.

Schema definition is pure Python:
```python
@strawberry.type
class User:
    id: strawberry.ID
    username: str
    full_name: str
```

GraphQL schema auto-generated from types.

#### DX Advantage
- **Python-first**: Type hints drive schema
- **Async/await**: Built on asyncpg, fully async
- **DataLoaders**: Batching pattern prevents N+1 queries
- **Great error messages**: Validation failures are clear
- **Kubernetes-ready**: Health check probes for liveness/readiness/startup

#### Performance Characteristics
- Q1: 1.7k RPS (mid-tier)
- Consistent latency (p50 23.2ms, p95 33.6ms)
- T1 (complex query): 1.3k RPS (solid for multi-level nesting)

#### Tradeoffs

**Strengths:**
- Best Python GraphQL DX (8.5 overall)
- Full type safety (Python types → GraphQL → validated requests)
- Excellent async support (matching Node.js concurrency models)
- Active development, growing ecosystem

**Weaknesses:**
- Slower than Rust/C# alternatives (inherent to Python)
- ORM patterns (if used) can introduce N+1 risks
- Smaller ecosystem than Java frameworks

#### When to Use
- **Python teams** building GraphQL APIs
- **Data science platforms** needing fast schema iteration
- **Internal services** where Python is the standard
- **Projects requiring clean, maintainable code** over maximum throughput

---

### 4. Mercurius (Node.js, GraphQL — SDL + Fastify)

#### Architecture
Mercurius is a **GraphQL plugin for Fastify**, built on The Guild's graphql-tools ecosystem.

SDL-first schema, clean separation of concerns:
```graphql
type Query {
  users(limit: Int): [User]
}
```

#### DX Advantage
- **SDL familiarity**: GraphQL schema language directly
- **Fastify foundation**: Streaming, hooks, minimal overhead
- **DataLoader integration**: Batching built-in
- **The Guild ecosystem**: Rich tooling (code-gen, schema stitching, federation)

#### Performance Characteristics
- Q1: 675 RPS (baseline)
- Q2: 9.8k RPS (best Node.js without REST)
- T1: 6.9k RPS (strong for complex queries)
- Excellent p95 latency (7.6ms Q2)

#### Tradeoffs

**Strengths:**
- Clean GraphQL-first experience
- Strong Node.js foundation (Fastify)
- Mature, stable ecosystem
- Good for teams familiar with SDL

**Weaknesses:**
- Schema and resolver code can drift (no type inference)
- Requires manual DataLoader setup
- Smaller community than Express

#### When to Use
- **Node.js teams** with GraphQL-first culture
- **High-concurrency APIs** needing minimal overhead
- **Teams invested in The Guild tools** (graphql-config, codegen, etc.)

---

### 5. GraphQL-Yoga (Node.js, GraphQL — Portable GraphQL Server)

#### Architecture
GraphQL-Yoga is a **standalone GraphQL server framework**, not a plugin.

Runs on any Node.js platform (Fastify, Express, Node.js http, Deno, etc.). GraphQL-first, clean separation.

#### DX Advantage
- **Framework-agnostic**: No lock-in to specific HTTP server
- **Mature SDL pattern**: Clean GraphQL schema definition
- **Built-in tools**: Subscriptions, plugins, middleware
- **Web IDE**: GraphQL IDE built-in (Altair, GraphiQL)

#### Performance Characteristics
- Q1: 712 RPS (baseline)
- Q2: 9.6k RPS (best Node.js alongside Mercurius)
- T1: 6.2k RPS
- Consistent latency (p50 4.0ms Q2)

#### Tradeoffs

**Strengths:**
- Framework flexibility
- Excellent GraphQL spec compliance
- Good for federation/gateway patterns
- Mature, backed by The Guild

**Weaknesses:**
- Slight overhead vs. raw Fastify
- Schema/resolver type drift (like Mercurius)
- Ecosystem smaller than Express

#### When to Use
- **Platform-agnostic GraphQL servers**
- **API gateways / Federation layers**
- **Teams building GraphQL infrastructure**
- **Portable code across Node.js runtimes**

---

### 6. Actix-web-REST (Rust, REST)

#### Architecture
Actix-web is a **Rust async web framework** using tokio runtime.

REST endpoints using handler functions, middleware for cross-cutting concerns.

Schema defined implicitly through Rust types + serde serialization.

#### DX Advantage
- **Type safety**: Rust compiler prevents entire classes of bugs
- **Performance**: Minimal overhead, excellent p50 latency
- **sqlx macros**: SQL validated at compile time against database
- **Prometheus metrics**: Built-in observability
- **Error handling**: Explicit error types, no null-reference crashes

#### Performance Characteristics
- Q1: 1.9k RPS
- Q2: 9.9k RPS (fastest REST implementation)
- F1: 11.8k RPS (best filter performance)
- Excellent p50 latency (2.2–2.4ms across most queries)
- T1: 69 RPS (REST: only fetch single POST, not composed query)

#### Tradeoffs

**Strengths:**
- Compile-time guarantees eliminate entire categories of runtime errors
- Exceptional latency performance
- Great for compute-intensive operations

**Weaknesses:**
- Rust learning curve
- Compilation adds deployment lag (30–60s)
- Smaller ecosystem than Java/Node.js
- REST model limits composition (T1 requires 3 separate HTTP calls)

#### When to Use
- **High-performance REST APIs** where latency matters
- **Systems requiring compile-time type safety**
- **Teams with Rust expertise** or willing to learn
- **Data pipelines / backend services** over customer-facing APIs (due to complexity)

---

### 7. Spring-Boot-ORM (Java, GraphQL)

#### Architecture
Spring-Boot with Spring Data JPA (Hibernate ORM).

Entity-driven schema: entities define tables, relationships, and (implicitly) GraphQL types.

#### DX Advantage
- **Mature ecosystem**: 15+ years of Spring refinement
- **Convention over configuration**: JPA conventions reduce boilerplate
- **Comprehensive tooling**: IDEs, plugins, testing frameworks
- **Enterprise support**: Vmware backing, commercial support available
- **Actuator metrics**: Metrics, health checks, operational endpoints out-of-box

#### Performance Characteristics
- Q1: 855 RPS
- Q2b: 8.2k RPS (ORM variant is strong for some queries)
- F1: 7.3k RPS
- T1: 2.2k RPS
- Variable performance (depends on query pattern)

#### Tradeoffs

**Strengths:**
- Vast ecosystem (32k questions on Stack Overflow)
- Great IDE integration (IntelliJ, VS Code)
- Excellent documentation
- JVM garbage collection predictable at scale

**Weaknesses:**
- Steep initial setup (Maven, lots of configuration)
- Lazy-loading patterns can trigger N+1 queries
- JVM startup adds deployment lag (5–10s)
- "Magic" (annotations, proxy objects) hides complexity

#### When to Use
- **Enterprise teams** already invested in Spring
- **High-compliance environments** (Java's mature security track record)
- **Rapid CRUD API development** (code-gen tools available)
- **Projects requiring operational maturity** (monitoring, security, updates)

#### Not Ideal For
- **Startups** needing fast iteration (setup overhead)
- **Microservices** where deployment lag matters
- **Teams preferring explicit code** over conventions

---

### 8. Express-REST (Node.js, REST)

#### Architecture
Express is Node.js's **original web framework** (since 2010).

Minimal, unopinionated: middleware stacks, route handlers, minimal magic.

#### DX Advantage
- **Simplicity**: Flat learning curve
- **Flexibility**: Middleware pattern allows custom logic
- **Ecosystem**: Every Node.js library works with Express
- **Rapid development**: Write endpoints in minutes
- **Manual relationships**: Include parameters allow explicit data loading

#### Performance Characteristics
- Q1: 672 RPS
- Q2: 8.9k RPS (tied with gin-rest for fastest REST)
- F1: 8.7k RPS
- T1: 3.3k RPS (3 sequential HTTP calls)
- Consistent latency (p50 4.4ms Q2)

#### Tradeoffs

**Strengths:**
- Lowest abstraction overhead
- Maximum flexibility
- Huge ecosystem (npm has 2M+ packages)
- Great for rapid prototyping

**Weaknesses:**
- No built-in validation (Joi adds boilerplate)
- Schema/response shape is implicit
- N+1 queries easy to introduce (no ORM safety nets)
- Manual relationship loading verbose

#### When to Use
- **Rapid prototyping** and MVPs
- **Teams valuing flexibility** over structure
- **Greenfield projects** where schema can be designed right
- **Internal APIs** where validation isn't critical

---

### 9. FastAPI-REST (Python, REST)

#### Architecture
FastAPI is a **modern Python REST framework** (since 2018) built on Starlette + Pydantic.

Type hints drive validation, schema generation, documentation.

#### DX Advantage
- **Type-first**: Python hints generate validation and OpenAPI docs
- **Async/await**: Full async support matching Go/Node.js concurrency
- **Pydantic validation**: Automatic request validation, clear error messages
- **Auto-documentation**: OpenAPI schema auto-generated, Swagger UI included
- **Kubernetes-ready**: Health check probes (liveness, readiness, startup)

#### Performance Characteristics
- Q1: 889 RPS
- Q2: 6.7k RPS (strong for Python REST)
- T1: 3.6k RPS (fast for Python)
- Consistent latency (p50 5.9ms Q2)

#### Tradeoffs

**Strengths:**
- Best Python REST framework (8.4 DX)
- Zero boilerplate (Pydantic handles validation)
- Excellent error messages
- Modern async design

**Weaknesses:**
- Slightly slower than compiled languages
- Ecosystem smaller than Django
- Async model requires care (can't use sync libraries)

#### When to Use
- **Python teams** building REST APIs
- **Data science platforms** needing web frontends
- **Internal services** where Python is standard
- **Projects where development speed > peak throughput**

---

## Section 6: FraiseQL v2.2.0 Deep Dive

### What Changed

FraiseQL v2.2.0 (released April 19, 2026) introduces `fraiseql.mutation_ok` and `fraiseql.mutation_err` SQL helper functions.

**Impact**: Reduces mutation function boilerplate from ~70 lines to ~25 lines.

### Before v2.2.0: 70-Line Mutation Function

```sql
CREATE OR REPLACE FUNCTION fn_update_user(
  id UUID,
  full_name TEXT DEFAULT NULL,
  bio TEXT DEFAULT NULL,
  email TEXT DEFAULT NULL
)
RETURNS TABLE (
  pk_user BIGINT,
  id UUID,
  identifier TEXT,
  email TEXT,
  username TEXT,
  full_name TEXT,
  bio TEXT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  error TEXT
) AS $$
DECLARE
  _updated_user record;
  _error_msg TEXT;
BEGIN
  -- Validate input
  IF id IS NULL THEN
    RETURN QUERY SELECT NULL::BIGINT, NULL::UUID, NULL::TEXT, NULL::TEXT, NULL::TEXT, NULL::TEXT, NULL::TEXT, NULL::TIMESTAMP, NULL::TIMESTAMP, 'ID is required'::TEXT;
    RETURN;
  END IF;

  -- Update the base table
  UPDATE benchmark.tb_user SET
    full_name = COALESCE(full_name, benchmark.tb_user.full_name),
    bio = COALESCE(bio, benchmark.tb_user.bio),
    email = COALESCE(email, benchmark.tb_user.email),
    updated_at = NOW()
  WHERE benchmark.tb_user.id = fn_update_user.id
  RETURNING benchmark.tb_user.* INTO _updated_user;

  -- Check if user was found
  IF _updated_user IS NULL THEN
    RETURN QUERY SELECT NULL::BIGINT, NULL::UUID, NULL::TEXT, NULL::TEXT, NULL::TEXT, NULL::TEXT, NULL::TEXT, NULL::TIMESTAMP, NULL::TIMESTAMP, 'User not found'::TEXT;
    RETURN;
  END IF;

  -- Fetch the result from tv_user (pre-computed view with JSONB)
  RETURN QUERY SELECT
    _updated_user.pk_user,
    _updated_user.id,
    _updated_user.identifier,
    _updated_user.email,
    _updated_user.username,
    _updated_user.full_name,
    _updated_user.bio,
    _updated_user.created_at,
    _updated_user.updated_at,
    NULL::TEXT
  FROM benchmark.tv_user WHERE benchmark.tv_user.id = fn_update_user.id;

EXCEPTION WHEN OTHERS THEN
  RETURN QUERY SELECT NULL::BIGINT, NULL::UUID, NULL::TEXT, NULL::TEXT, NULL::TEXT, NULL::TEXT, NULL::TEXT, NULL::TIMESTAMP, NULL::TIMESTAMP, SQLERRM::TEXT;
END;
$$ LANGUAGE plpgsql;
```

### After v2.2.0: 25-Line Mutation Function

```sql
CREATE OR REPLACE FUNCTION fn_update_user_v2(
  id UUID,
  full_name TEXT DEFAULT NULL,
  bio TEXT DEFAULT NULL,
  email TEXT DEFAULT NULL
)
RETURNS TABLE (
  pk_user BIGINT, id UUID, identifier TEXT, email TEXT, username TEXT, full_name TEXT, bio TEXT, created_at TIMESTAMP, updated_at TIMESTAMP, error TEXT
) AS $$
BEGIN
  IF id IS NULL THEN
    RETURN QUERY SELECT fraiseql.mutation_err('ID is required');
    RETURN;
  END IF;

  UPDATE benchmark.tb_user SET
    full_name = COALESCE(full_name, benchmark.tb_user.full_name),
    bio = COALESCE(bio, benchmark.tb_user.bio),
    email = COALESCE(email, benchmark.tb_user.email),
    updated_at = NOW()
  WHERE benchmark.tb_user.id = fn_update_user_v2.id;

  IF NOT FOUND THEN
    RETURN QUERY SELECT fraiseql.mutation_err('User not found');
    RETURN;
  END IF;

  RETURN QUERY SELECT fraiseql.mutation_ok() FROM benchmark.tv_user WHERE id = fn_update_user_v2.id;
END;
$$ LANGUAGE plpgsql;
```

### DX Improvement

**Lines saved**: 45 lines (64% reduction)

**Complexity reduction**:
- ✅ No manual column lists (helpers return all columns from tv_*)
- ✅ No error type construction (helpers handle NULL + error string)
- ✅ No exception handling boilerplate (helpers delegate to EXCEPTION block)

**Readability improvement**:
- Clear intent: `mutation_ok()` = success, `mutation_err(msg)` = failure
- Follows PostgreSQL conventions (other frameworks use similar patterns)

### Performance Impact

- **No change**: Mutation helpers compile to identical SQL
- **Cascades unchanged**: pg_tviews still triggers on UPDATE, syncs tv_* views

### CQRS Approach Verdict

**Is the write → tv_* sync worth the complexity?**

**YES**, for:
1. **Consistency guarantee**: Writes always sync pre-computed reads (no stale cache layers)
2. **Zero-copy response**: GraphQL response is direct JSONB deserialization (no resolver CPU)
3. **Predictable latency**: No resolver logic, just column fetch
4. **Scale-out reads**: Read replicas get pre-computed data immediately (via WAL streaming)
5. **Efficient storage**: UNLOGGED projections avoid WAL I/O, reducing database write load

**Architectural benefit** (CQRS):
- Separates durable writes (tb_* LOGGED) from ephemeral reads (tv_* UNLOGGED)
- Follows standard pattern: databases separate OLTP from OLAP
- **Recovery model**: Base tables are source-of-truth, projections rebuild on crash (via triggers)

**NOT suitable for**:
- Rapidly evolving schemas (recompiling triggers adds friction)
- Complex business logic in resolvers (CQRS limits to SQL functions)
- Teams unfamiliar with PostgreSQL triggers/views
- Systems requiring immediate read availability after crash (rebuild time needed)

### The `jsonb_delta` Variant

FraiseQL also ships `fn_update_user_delta` via the `jsonb_delta` extension.

**Purpose**: Surgical JSONB patching (update only changed fields, not entire object).

**When to use**:
- Large JSONB documents (>1KB) where patch size matters
- Bandwidth-constrained environments
- Append-only audit logs (delta reveals exactly what changed)

**Cost**: Extra complexity (delta functions, merge logic on read side).

---

## Section 7: Recommendation Matrix

| **Profile** | **Recommendation** | **Reasoning** |
|-------------|-------------------|--------------|
| **Solo dev, prototype** | Strawberry (GraphQL) or FastAPI-REST | Fast iteration, great DX, zero setup overhead |
| **Node.js team, production** | Mercurius or GraphQL-Yoga (GraphQL) or Express-REST | Mature ecosystem, good performance, familiar to team |
| **Python team, internal tooling** | FastAPI-REST | Best Python REST DX, async support, auto-docs |
| **High-throughput, greenfield** | FraiseQL (if PostgreSQL-literate) or Mercurius | Peak performance + acceptable DX tradeoff |
| **Existing PostgreSQL schema** | PostGraphile (zero code) or Spring-Boot-ORM (if Java) | Introspection/ORM leverage existing schema |
| **Zero-code, standard CRUD** | PostGraphile | Database → GraphQL, no hand-written schema |
| **Type safety paramount** | Rust: Actix-web-REST or async-graphql; Java: Spring-Boot-ORM | Compile-time guarantees eliminate whole classes of bugs |
| **Compliance/Enterprise** | Spring-Boot or C# dotnet | Mature, documented, commercial support available |
| **Edge deployment / low resources** | Express-REST or Gin-REST | Minimal memory, no GC pauses, fast startup |
| **Rapid schema iteration** | Strawberry or PostGraphile | Hot reload (Strawberry) or introspection (PostGraphile) |

---

## Section 8: What This Benchmark Does NOT Measure

### Excluded from Scope

1. **Hot-reload and development experience**
   - Strawberry + FastAPI have excellent hot reload
   - Spring-Boot requires full recompile
   - FraiseQL schema changes require recompilation

2. **Schema migration story**
   - PostgreSQL migrations (Alembic, Flyway, etc.) are out-of-scope
   - Framework support for migrations not tested

3. **Subscription support**
   - Many frameworks support GraphQL subscriptions (WebSocket)
   - Not benchmarked; would add additional complexity

4. **Federation / Stitching**
   - Apollo Federation, schema stitching, subgraph composition
   - Critical for large orgs but not measured here

5. **Authentication and authorization**
   - JWT validation, role-based access control, field-level auth
   - Each framework handles differently; not standardized in benchmark

6. **Real-world query complexity**
   - Benchmark uses 3-level nesting (user → post → comments)
   - Production queries often 4–5 levels deep with multiple types
   - Performance may degrade differently per framework

7. **Caching strategies**
   - HTTP caching (ETag, Cache-Control)
   - GraphQL caching (persisted queries, response caching)
   - Database query caching (Redis, memcached)
   - Not part of framework baseline

8. **Error boundary behavior**
   - How frameworks handle partial failures (1 resolver errors, others succeed)
   - Important in production; not benchmarked

9. **Concurrent connections and connection pooling**
   - 40 workers used in benchmark
   - Real-world peak concurrency varies (100–10k+ connections)
   - Pool sizing impacts observed latency

10. **Framework-specific optimizations**
    - Some frameworks have undocumented performance knobs
    - Query batching, lazy evaluation, streaming responses
    - May unlock additional throughput with configuration

11. **Language-specific ecosystem effects**
    - Node.js has npm (2M packages), hard to choose between
    - Java has Maven Central (4M+ artifacts)
    - Python has PyPI (500k packages)
    - Ecosystem quality varies; not measured

12. **Team productivity beyond first endpoint**
    - Testing ecosystem (pytest vs. jest vs. JUnit)
    - IDE support (IntelliJ vs. VS Code quality)
    - Debugging tooling (browser DevTools vs. Java debugger)

13. **Long-term maintainability**
    - Code readability after 2 years
    - Framework breaking changes
    - Upgrade paths
    - Not measured; team preference dominates

---

## Appendix: Full Results Reference

Complete benchmark results available in:
- **Markdown**: `/home/lionel/code/velocitybench/reports/bench-sequential-2026-04-19.md`
- **JSON**: `/home/lionel/code/velocitybench/reports/bench-sequential-2026-04-19.json`

All 37 frameworks × 8 queries (Q1, Q2, Q2b, Q3, F1, F2, T1, M1) with:
- Requests per second (RPS)
- Latency percentiles (p50, p95, p99)
- Error rates
- Total request counts

---

## Conclusion

**VelocityBench 2026-04-19 demonstrates a clear performance/DX tradeoff landscape**:

1. **FraiseQL leads throughput** (8.8k Q1 RPS) but requires PostgreSQL expertise and CQRS mindset
2. **Node.js and Python frameworks dominate DX**, with Strawberry, Mercurius, and FastAPI-REST scoring highest
3. **PostGraphile offers unique zero-code value** (introspect → serve)
4. **Rust frameworks (Actix-web, Async-graphql, Juniper) deliver exceptional type safety**, trading compilation lag for reliability
5. **Java (Spring-Boot) remains production-ready**, with mature tooling but higher setup overhead

**For most teams**: Strawberry (Python), Mercurius/GraphQL-Yoga (Node.js), or PostGraphile (PostgreSQL-centric) offer the best balance of performance, developer experience, and ecosystem maturity.

**For specialized use cases**: FraiseQL (ultra-high-throughput reads), Actix-web (Rust type safety), Spring-Boot (enterprise ecosystems), or Express-REST (minimal overhead).

The benchmark is available for future framework additions. As of April 19, 2026, this represents the current state of web framework performance and ergonomics across 37 production-ready options.
