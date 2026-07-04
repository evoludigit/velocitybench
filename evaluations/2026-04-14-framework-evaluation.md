# Framework Evaluation: Multi-Dimensional Analysis
**Date**: 2026-04-14
**Benchmark basis**: VelocityBench sequential run 2026-03-04 (all frameworks); fraiseql updated to 2026-04-14 v2.1.6 post-compression-fix
**Scenario**: Q1 = `{ users(limit:20) { id username fullName bio } }` at 40 concurrent workers

---

## 1. Simplicity vs. Performance Matrix

### Methodology

- **Y-axis (Performance)**: Q1 RPS from benchmark data. Threshold: ≥ 5,000 RPS = High-P.
- **X-axis (Simplicity)**: Scored 1–10 across 5 dimensions. Threshold: ≥ 7 = High-S.

| Dimension | Weight |
|-----------|--------|
| Boilerplate to first working endpoint | 25% |
| Schema / type definition overhead | 20% |
| ORM / query layer friction | 20% |
| Build & toolchain setup | 15% |
| Ecosystem maturity & docs | 10% |
| Runtime debugging simplicity | 10% |

### Scored Table

| Framework | Language | Type | Q1 RPS | Simplicity | Quadrant |
|-----------|----------|------|-------:|----------:|---------|
| actix-web-rest | Rust | REST | 12,588 | 5 | Low-S / High-P |
| fraiseql-tv-cache | Rust | GraphQL | 10,637 | 6 | Low-S / High-P |
| fraiseql-tv | Rust | GraphQL | 10,611 | 6 | Low-S / High-P |
| spring-boot | Java | REST | 9,150 | 4 | Low-S / High-P |
| mercurius | Node.js | GraphQL | 9,008 | 7 | High-S / High-P |
| fraiseql-v-nocache | Rust | GraphQL | 7,975 | 5 | Low-S / High-P |
| async-graphql | Rust | GraphQL | 7,905 | 6 | Low-S / High-P |
| graphql-go | Go | GraphQL | 7,576 | 4 | Low-S / High-P |
| express-rest | Node.js | REST | 7,513 | 8 | High-S / High-P |
| fraiseql-v-cache | Rust | GraphQL | 7,165 | 5 | Low-S / High-P |
| go-graphql-go | Go | GraphQL | 7,045 | 4 | Low-S / High-P |
| go-gqlgen | Go | GraphQL | 6,442 | 5 | Low-S / High-P |
| play-graphql | Scala | GraphQL | 6,182 | 3 | Low-S / High-P |
| graphql-yoga | Node.js | GraphQL | 5,712 | 8 | High-S / High-P |
| ruby-rails | Ruby | REST | 5,642 | 7 | High-S / High-P |
| gin-rest | Go | REST | 5,586 | 8 | High-S / High-P |
| postgraphile | Node.js | GraphQL | 5,403 | 9 | High-S / High-P |
| express-graphql | Node.js | GraphQL | 4,624 | 7 | High-S / Low-P |
| apollo-server | Node.js | GraphQL | 4,513 | 7 | High-S / Low-P † |
| webonyx-graphql-php | PHP | GraphQL | 4,501 | 4 | Low-S / Low-P |
| juniper | Rust | GraphQL | 4,499 | 5 | Low-S / Low-P |
| express-orm | Node.js | REST+ORM | 4,185 | 6 | Low-S / Low-P |
| fastapi-rest | Python | REST | 3,623 | 8 | High-S / Low-P |
| csharp-dotnet | C# | GraphQL | 3,338 | 5 | Low-S / Low-P |
| apollo-orm | Node.js | GraphQL+ORM | 2,984 | 5 | Low-S / Low-P |
| quarkus-graphql | Java | GraphQL | 2,647 | 5 | Low-S / Low-P |
| spring-boot-orm | Java | REST+ORM | 2,523 | 3 | Low-S / Low-P |
| micronaut-graphql | Java | GraphQL | 2,515 | 4 | Low-S / Low-P |
| spring-boot-orm-naive | Java | REST+ORM | 2,474 | 3 | Low-S / Low-P |
| ariadne | Python | GraphQL | 1,100 | 7 | High-S / Low-P |
| asgi-graphql | Python | GraphQL | 1,118 | 7 | High-S / Low-P |
| graphene | Python | GraphQL | 1,074 | 7 | High-S / Low-P |
| hanami | Ruby | GraphQL | 938 | 5 | Low-S / Low-P |
| strawberry | Python | GraphQL | 868 | 8 | High-S / Low-P |
| php-laravel | PHP | REST | 376 | 7 | High-S / Low-P |
| flask-rest | Python | REST | 238 | 8 | High-S / Low-P |

† apollo-server: 25.7% M1 error rate — effectively broken for write workloads.

### Quadrant Summaries

**High-S / High-P** — mercurius, express-rest, graphql-yoga, ruby-rails, gin-rest, postgraphile
All Node.js, Go REST, one Ruby entry, and one zero-code tool. Mature ecosystems, thin query layers, no ORM friction. Postgraphile (simplicity 9) requires zero custom code. Mercurius is the standout: highest simplicity in this quadrant, near-top throughput.

**Low-S / High-P** — actix-web, fraiseql variants, spring-boot, async-graphql, graphql-go, go-graphql-go, go-gqlgen, play-graphql
Three complexity sources: Rust ownership, Go's verbose GraphQL type registration, JVM + DI ceremony. Spring-boot at 9,150 RPS is the surprise — JVM JIT on warm sequential workloads nearly matches Rust throughput, but at a large RAM cost (see §3).

**High-S / Low-P** — express-graphql, apollo-server†, fastapi-rest, ariadne, asgi-graphql, graphene, strawberry, php-laravel, flask-rest
Python dominates (5 of 9). CPython GIL + WSGI/ASGI overhead create a hard throughput ceiling. Note: flask-rest at 238 RPS reflects single-threaded WSGI, not a production deployment.

**Low-S / Low-P** — webonyx, juniper, express-orm, csharp-dotnet, apollo-orm, quarkus, spring-boot-orm, micronaut, spring-boot-orm-naive, hanami
ORM overhead (spring-boot-orm shows 72% throughput drop vs. spring-boot), JVM + GraphQL layering without JVM warmup payoff, and manual PHP GraphQL type registration all land here.

### Key Trade-offs

1. **graphql-yoga (8, 5,712) → mercurius (7, 9,008)**: +3,296 RPS, −1 simplicity. Fastify vs Express/standalone. Worth it under tight latency SLA.
2. **express-rest (8, 7,513) → actix-web-rest (5, 12,588)**: +5,075 RPS, −3 simplicity. Multi-month Rust onboarding cost vs. performance ceiling lift.
3. **spring-boot (4, 9,150) → spring-boot-orm (3, 2,523)**: −6,627 RPS for adding Hibernate. ORM friction in Java is not just complexity — it destroys throughput.
4. **fastapi-rest (8, 3,623) → express-rest (8, 7,513)**: +3,890 RPS, same simplicity. Choose Python for ecosystem reasons, not performance.
5. **postgraphile (9, 5,403) → graphql-yoga (8, 5,712)**: +309 RPS, −1 simplicity, full resolver control gained. Choose postgraphile when GraphQL surface maps cleanly to DB schema; yoga when custom business logic is needed.

### Honest Caveats

- **apollo-server M1**: 25.7% error rate disqualifies it for production write workloads. Q1 placement is valid; M1 comparison is not.
- **hanami p99 634ms**: 83× p50 — graphql-ruby concurrency contention under load, not a baseline performance issue.
- **fraiseql M1 asymmetry**: Cascade mutations update/return 61 rows per call vs. 1 row for other frameworks. M1 RPS not directly comparable.
- **flask-rest 238 RPS**: Single-threaded WSGI. Gunicorn + 4 workers would reach ~900–1,200 RPS.
- **fraiseql-v-cache M1 range (692–4,921 RPS)**: Run-order fragmentation — mutation performance effectively unmeasured.

### Standouts

**Over-performers**: spring-boot (simplicity 4, 9,150 RPS — JVM JIT on warm workloads), mercurius (simplicity 7, 9,008 RPS — best productivity-per-RPS), ruby-rails (simplicity 7, 5,642 RPS — Rails REST competitive despite reputation).

**Under-performers**: strawberry (simplicity 8, 868 RPS — cleanest Python GraphQL DX, hard throughput floor), apollo-server (simplicity 7, broken M1 — simplicity doesn't equal reliability), juniper (simplicity 5, 4,499 RPS — Rust without async; async-graphql outperforms it 75% at same simplicity tier).

---

## 2. Adding CPU Efficiency

Efficiency metric: RPS per CPU-percent.

**Key findings:**
- Rust (actix, fraiseql) achieves high RPS at full CPU saturation efficiently — every CPU cycle produces output.
- spring-boot's "near-Rust performance" narrative weakens when CPU efficiency is considered alongside RAM (§3). JVM JIT produces throughput via sustained CPU pressure, not algorithmic efficiency.
- Python GraphQL is both low-throughput and CPU-inefficient — GIL-locked to one core regardless of concurrency, producing ~1,000 RPS while burning 100% of that core.
- Node.js event loop is efficient per-core but does not parallelize CPU work — single-threaded throughput ceiling.
- fraiseql-tv-cache: 10,637 RPS at 98% CPU → ~108 RPS/CPU-percent. Competitive with other Rust frameworks.

**What changes in rankings**: CPU efficiency primarily splits the Low-S / High-P quadrant — Rust and Go frameworks are computationally principled; JVM frameworks achieve throughput via resource pressure.

---

## 3. Adding RAM / Memory Efficiency

### Measured data (fraiseql only)

| Framework | RAM (measured) | Image MB | Q1 RPS | RPS/MB RAM |
|-----------|---------------:|--------:|-------:|-----------:|
| fraiseql-tv-cache | 15 MB | 44 | 10,637 | 709 |
| fraiseql-tv | 15 MB | 44 | 10,611 | 707 |
| fraiseql-v-nocache | 18 MB | 44 | 7,975 | 443 |
| fraiseql-v-cache | 18 MB | 44 | 7,165 | 398 |

### Estimated RAM by runtime

| Runtime | Typical RAM | Est. RPS/MB (best-in-cluster) |
|---------|------------|------------------------------|
| Rust (actix, fraiseql, async-graphql) | 8–25 MB | 400–840 |
| Go (gin, gqlgen, graphql-go) | 20–60 MB | 140–190 |
| Node.js (all) | 80–180 MB | 44–75 |
| Python (all) | 50–120 MB | 4–45 |
| PHP-FPM | 60–150 MB | 4–10 |
| C# .NET | 100–200 MB | ~17 |
| JVM — Micronaut | 150–250 MB | ~13 |
| JVM — Quarkus | 200–350 MB | ~9 |
| JVM — Spring Boot | 350–600 MB | ~5–20 |
| Ruby | 150–350 MB | ~16–23 |

### What changes

**Spring-boot collapses on efficiency**: 9,150 RPS at ~450 MB RAM = ~20 RPS/MB. fraiseql-tv-cache achieves similar throughput at 15 MB = 709 RPS/MB — 35× more memory-efficient. At scale this is a 30× density advantage (30 fraiseql instances per node for every 1 spring-boot instance, same memory).

**JVM GraphQL frameworks have no redeeming axis**: Already Low-S / Low-P. Add 200–350 MB RAM and ~9–13 RPS/MB. No workload profile justifies this over alternatives.

**Node.js holds position but loses ground to Go**: Mercurius at 9,008 RPS with ~120 MB RAM (~75 RPS/MB) vs. gin-rest at 5,586 RPS with ~30 MB (~186 RPS/MB). Go is 2.5× more memory-efficient at 60% of the throughput.

**Python GraphQL: expensive and slow**: strawberry at 868 RPS / ~85 MB RAM = ~10 RPS/MB. Not just a throughput problem — memory is also underutilized relative to output.

### Three-tier structure (integrating all three axes)

**Tier A — Efficient high performance** (Rust): actix-web, fraiseql variants, async-graphql.
High RPS, tiny RAM, efficient CPU use. The only frameworks where you get all three dimensions.

**Tier B — Reasonable balance** (Go, Node.js): gin, gqlgen, mercurius, express-rest, graphql-yoga.
Moderate RPS, moderate RAM. Go edges Node.js on efficiency; Node.js edges Go on simplicity and ecosystem.

**Tier C — Pay more, get less** (JVM, Python GraphQL, PHP): Every JVM framework, every Python GraphQL framework, PHP Laravel. Either high RAM for moderate throughput (JVM) or low throughput for medium RAM (Python GraphQL). Justified only by team expertise or ecosystem lock-in.

---

## 4. Agentic LLM as Developer

Reframes the evaluation: which frameworks does an LLM agent write, extend, and debug most reliably?

### Relevant dimensions

| Dimension | Why it matters |
|-----------|---------------|
| Training data volume | Agent draws on prior exposure — zero training data means hallucinated APIs |
| Pattern regularity | Every new feature follows the same template = reliable code generation |
| Compile-time feedback | Agent learns it's wrong from compiler, not from runtime failure |
| Iteration speed | Try → fail → fix cycle speed; Rust compile times are a bottleneck |
| Explicit over implicit | Magic conventions fail silently in ways agents don't catch |
| Error message clarity | Agent must parse errors autonomously to self-correct |

### Agent-developer tiers

**Tier 1 — Agent-native**: FastAPI, express-rest, graphql-yoga, gin-rest
Massive training corpus + regular patterns + fast iteration. FastAPI is the standout: Pydantic models are self-documenting, OpenAPI spec auto-generation provides immediate feedback, Pydantic validation errors are precise and parseable. Go compiler (gin-rest) gives fast, strict feedback without Rust's borrow-checker complexity.

**Tier 2 — Workable**: graphene, strawberry, flask-rest, apollo-server, spring-boot
High training data but one friction point each. Spring Boot's annotation pattern is templated but DI lifecycle creates silent failures. Python GraphQL frameworks are easy to extend but have no compile-time check.

**Tier 3 — Agent friction**: ruby-rails, mercurius, actix-web, async-graphql, go-gqlgen
Rails: enormous training data, but implicit magic (before_action, ActiveRecord conventions) means agent-generated code works in isolation and breaks in context. Rust frameworks: slow compile cycle + borrow-checker creates agent loops.

**Tier 4 — Agent-hostile** (initial assessment, revised below): fraiseql, postgraphile, play, webonyx, hanami

### Correction: fraiseql is agent-friendly

Initial Tier 4 placement was wrong. It conflated "training data on the fraiseql framework name" with "training data on what the agent actually writes."

What an agent writes for fraiseql:
- PostgreSQL views (standard SQL — massive training data)
- SQL functions (standard SQL)
- A JSON schema file (trivial for agents)
- One compile command

The agent is NOT writing Rust, resolvers, ORM mappings, or framework-specific decorators.

| Dimension | Reality |
|-----------|---------|
| Training data | SQL = massive, JSON = trivial |
| Pattern regularity | Extremely regular: new feature = new view + schema entry |
| Compile feedback | PostgreSQL errors when view is wrong; `fraiseql-cli compile` validates schema immediately |
| Iteration speed | SQL changes apply immediately; no Rust compile cycle |
| Explicit over implicit | Everything is in the view — no hidden callbacks, no ORM magic |
| Error clarity | PostgreSQL errors are precise and highly searchable |

**Revised fraiseql tier: Tier 1–2** alongside FastAPI and graphql-yoga.

The agent's strong suit (SQL generation) is the primary development artifact. There is no application-layer code to get wrong. The server binary is a black box; the agent only touches SQL and JSON.

**Implication**: An agent-developed fraiseql-tv-cache backend sits in the top 3 of the RPS ranking and top tier of memory efficiency while using artifacts the agent generates reliably. This is the combination with the best aggregate profile across all four evaluation dimensions.

---

## 5. Summary Matrix

| Framework | Perf | Simplicity | RAM efficiency | Agent-dev tier | Overall |
|-----------|:----:|:----------:|:--------------:|:--------------:|---------|
| fraiseql-tv-cache | ★★★★★ | ★★★☆☆ | ★★★★★ | ★★★★☆ | Best all-round if SQL-first |
| actix-web-rest | ★★★★★ | ★★☆☆☆ | ★★★★★ | ★★★☆☆ | Performance ceiling, Rust team required |
| mercurius | ★★★★☆ | ★★★★☆ | ★★★☆☆ | ★★★☆☆ | Best Node.js option |
| gin-rest | ★★★☆☆ | ★★★★☆ | ★★★★☆ | ★★★★☆ | Best Go REST |
| graphql-yoga | ★★★☆☆ | ★★★★☆ | ★★★☆☆ | ★★★★☆ | Best Node.js GraphQL for agent |
| express-rest | ★★★☆☆ | ★★★★☆ | ★★★☆☆ | ★★★★★ | Highest agent-dev reliability |
| fastapi-rest | ★★☆☆☆ | ★★★★☆ | ★★★☆☆ | ★★★★★ | Best for Python-native teams |
| spring-boot | ★★★★☆ | ★★☆☆☆ | ★★☆☆☆ | ★★★☆☆ | JVM teams only; memory cost is real |
| postgraphile | ★★★☆☆ | ★★★★★ | ★★★☆☆ | ★★☆☆☆ | Zero-code read APIs only |
| Python GraphQL | ★☆☆☆☆ | ★★★★☆ | ★★☆☆☆ | ★★★☆☆ | Prototyping only |
| JVM GraphQL | ★★☆☆☆ | ★★☆☆☆ | ★☆☆☆☆ | ★★☆☆☆ | No compelling production use case |

---

*Generated from VelocityBench benchmark analysis session, 2026-04-14.*
*Benchmark data: `reports/bench-sequential-2026-03-04.{json,md}` (all frameworks), `reports/bench-sequential-2026-04-14.{json,md}` (fraiseql v2.1.6).*
