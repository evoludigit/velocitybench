# VelocityBench

GraphQL & REST framework performance benchmarks — 8 languages, reproducible methodology, real PostgreSQL data.

> **Latest run**: March 2026 · sequential isolation · 40 workers · 30s per framework · dataset: 10 000 users / 50 000 posts / 200 000 comments

---

## Results

Full tables: [reports/bench-sequential-2026-03-04.md](reports/bench-sequential-2026-03-04.md)

The **Author** column is the language the developer writes in; the **Runtime** column is
what actually executes requests. For most frameworks these are the same. FraiseQL is the
exception: schemas are authored in Python, compiled ahead of time, and served by a
standalone Rust binary — **no Python runs per request**. See
[FraiseQL variants](#fraiseql-variants) for what `-v` means.

### Q1 — `users(limit: 20) { id username fullName }`

| Framework | Author | Runtime | Type | RPS | p50 | p99 | Errors |
|-----------|--------|---------|------|----:|----:|----:|--------|
| actix-web-rest | Rust | Rust | REST | 12 588 | 2.0 ms | 17.2 ms | 0% |
| spring-boot | Java | JVM | REST | 9 150 | 3.3 ms | 17.4 ms | 0% |
| mercurius | Node.js | Node.js | GraphQL | 9 008 | 4.0 ms | 10.7 ms | 0% |
| async-graphql | Rust | Rust | GraphQL | 7 905 | 4.7 ms | 12.1 ms | 0% |
| graphql-go | Go | Go | GraphQL | 7 576 | 4.3 ms | 19.3 ms | 0% |
| express-rest | Node.js | Node.js | REST | 7 513 | 3.8 ms | 7.7 ms | 0% |
| **fraiseql-v** | **Python** | **Rust** | GraphQL | 6 513 | 5.6 ms | 13.8 ms | 0% |
| go-gqlgen | Go | Go | GraphQL | 6 442 | 4.3 ms | 30.1 ms | 0% |
| play-graphql | Scala | JVM | GraphQL | 6 182 | 5.0 ms | 26.9 ms | 0% |
| ruby-rails | Ruby | Ruby | REST | 5 642 | 5.5 ms | 26.8 ms | 0% |
| gin-rest | Go | Go | REST | 5 586 | 4.5 ms | 37.2 ms | 0% |

### Q2b — `posts(limit: 10) { id title author { username fullName } }` (nested join)

| Framework | Author | Runtime | Type | RPS | p50 | p99 | Errors |
|-----------|--------|---------|------|----:|----:|----:|--------|
| actix-web-rest | Rust | Rust | REST | 11 019 | 2.4 ms | 19.1 ms | 0% |
| mercurius | Node.js | Node.js | GraphQL | 8 252 | 4.5 ms | 11.6 ms | 0% |
| express-rest | Node.js | Node.js | REST | 7 573 | 4.3 ms | 11.5 ms | 0% |
| play-graphql | Scala | JVM | GraphQL | 7 421 | 4.6 ms | 16.6 ms | 0% |
| graphql-go | Go | Go | GraphQL | 7 323 | 4.5 ms | 18.1 ms | 0% |
| gin-rest | Go | Go | REST | 6 818 | 4.3 ms | 23.8 ms | 0% |
| graphql-yoga | Node.js | Node.js | GraphQL | 6 437 | 5.6 ms | 10.8 ms | 0% |
| csharp-dotnet | C# | .NET | REST | 6 386 | 5.2 ms | 15.6 ms | 0% |
| go-gqlgen | Go | Go | GraphQL | 6 271 | 5.0 ms | 24.6 ms | 0% |
| spring-boot | Java | JVM | REST | 5 265 | 6.0 ms | 27.9 ms | 0% |
| async-graphql | Rust | Rust | GraphQL | 4 229 | 8.2 ms | 25.3 ms | 0% |

> Read FraiseQL's position honestly: `fraiseql-v` is **competitive mid-pack throughput from
> a compiled-from-schema engine with zero hand-written resolvers** — not the fastest raw
> server here. The architectural story (Python ergonomics, Rust runtime, no N+1 by
> construction) is the point, not a top-of-table RPS number.

---

## FraiseQL variants

FraiseQL appears under more than one row because the same Rust binary serves two read-side
strategies. Both author in Python and run in Rust; they differ only in how the read model
is stored:

| Variant | Read model | Trades |
|---------|-----------|--------|
| **`fraiseql-v`** | `v_*` views — JSONB composed on the fly per request | No storage multiplier, no write amplification; pays the composition cost at read time |
| **`fraiseql-tv`** | `tv_*` tables — JSONB pre-materialized via incremental refresh ([pg_tviews](../fraiseql/)) | Faster reads; spends storage + write-time refresh to buy them |

This is a **tradeoff, not a strict upgrade** — `tv-` is not universally faster (materialization
overhead and TOAST effects can erase the win on write-heavy or wide-row workloads). The
headline tables above show the conservative `-v` baseline on purpose. Per-variant numbers
(including `-tv`, `-tv-audit`, and `-nocache` configurations) are in the dated runs under
[`reports/`](reports/).

---

## What We Benchmark

Three query scenarios on a shared PostgreSQL dataset, each revealing different characteristics:

| Scenario | Query | What it tests |
|----------|-------|---------------|
| **Q1** | `users(limit: 20) { id username fullName }` | Simple list read |
| **Q2** | `posts(limit: 10) { id title }` | Simple list, different table |
| **Q2b** | `posts(limit: 10) { id title author { … } }` | Nested join — exposes N+1 risks |

**Metrics**: RPS (requests per second), p50 / p95 / p99 latency, error rate.

**Method**: Sequential isolation — each framework runs alone against PostgreSQL. No resource contention between frameworks. Each scenario runs for 30 seconds after a 10-second warmup.

---

## Running the Benchmarks

### Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| RAM | 8 GB | 16 GB |
| Disk | 15 GB free | 25 GB |
| Docker | 24+ | latest |
| Time | ~20 min (subset) | ~60 min (full suite) |

### Quick start

```bash
git clone https://github.com/evoludigit/velocitybench.git
cd velocitybench

# Start PostgreSQL + seed medium dataset (10K users, 50K posts, 200K comments)
make up-medium

# Optional: verify frameworks are healthy before benchmarking
make smoke-test

# Run the canonical sequential benchmark
make bench-sequential

# Results are written to reports/bench-sequential-YYYY-MM-DD.md
```

### Partial run (faster)

```bash
# Test a subset of frameworks
make bench-sequential FRAMEWORKS="gin-rest actix-web-rest go-gqlgen async-graphql"

# Shorter measurement window (10s instead of 20s)
make bench-sequential DURATION=10 CONCURRENCY=20
```

### Benchmark a single framework

```bash
make bench-one FRAMEWORK=strawberry
```

### Tear down

```bash
make down
```

---

## Frameworks

### GraphQL

| Framework | Author | Runtime | Status |
|-----------|--------|---------|--------|
| async-graphql | Rust | Rust | ✅ |
| juniper | Rust | Rust | ✅ |
| go-gqlgen | Go | Go | ✅ |
| mercurius | Node.js | Node.js | ✅ |
| quarkus-graphql | Java | JVM | ✅ |
| strawberry | Python | Python | ✅ |
| fraiseql | Python | Rust | ✅ |
| apollo-server | Node.js | Node.js | ✅ |
| graphene | Python | Python | ✅ |
| ariadne | Python | Python | ✅ |
| webonyx-graphql-php | PHP | PHP | ✅ |
| ruby-rails (graphql-ruby) | Ruby | Ruby | ✅ |
| hasura | — | Haskell | managed |

### REST

| Framework | Author | Runtime | Status |
|-----------|--------|---------|--------|
| gin-rest | Go | Go | ✅ |
| actix-web-rest | Rust | Rust | ✅ |
| spring-boot-orm | Java | JVM | ✅ |
| fastapi-rest | Python | Python | ✅ |
| flask-rest | Python | Python | ✅ |
| express-rest | Node.js | Node.js | ✅ |
| csharp-dotnet | C# | .NET | ✅ |

---

## Security Model

VelocityBench is a **local benchmarking tool**, not a production service. It uses hardcoded test credentials, no authentication, and no rate limiting — intentionally, to remove overhead that would confound results.

**Do not expose the Docker Compose stack to the internet.**

See [SECURITY.md](SECURITY.md) for the full security model.

---

## Contributing

- **Fix a broken framework**: see the ⚠️ entries above — PRs welcome
- **Add a new framework**: see [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/ADD_FRAMEWORK_GUIDE.md](docs/ADD_FRAMEWORK_GUIDE.md)
- **Improve methodology**: open an issue to discuss before implementing

---

## Documentation

| Document | Purpose |
|----------|---------|
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to add frameworks or fix issues |
| [DEVELOPMENT.md](DEVELOPMENT.md) | Local dev setup, architecture details |
| [SECURITY.md](SECURITY.md) | Security model and intended use |
| [docs/ADD_FRAMEWORK_GUIDE.md](docs/ADD_FRAMEWORK_GUIDE.md) | Step-by-step guide to add a new framework |
| [docs/FRAMEWORK_SELECTION_GUIDE.md](docs/FRAMEWORK_SELECTION_GUIDE.md) | How to choose a framework for your project |
| [docs/adr/](docs/adr/) | Architecture Decision Records |

---

**Version**: v0.2.0 · **License**: MIT
