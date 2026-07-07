# VelocityBench

GraphQL & REST framework performance benchmarks — 8 languages, reproducible methodology, real PostgreSQL data.

> **Latest run**: July 2026 · Hetzner CCX33 (dedicated vCPU) · k6 on a separate loadgen
> box · median of three warm sweeps · FraiseQL v2.11 · 0 errors · dataset: 10 000 users /
> 50 000 posts / 200 000 comments. Reproduce it with one command:
> [docs/reproducing-on-hetzner.md](docs/reproducing-on-hetzner.md).

---

## Results

**[▶ Explore the interactive results](site/)** · [publishable report](reports/report-2026-07.md) ·
[full tables](reports/hetzner-2026-07/bench-hetzner-2026-07-07-median.md) ·
[raw JSON](reports/hetzner-2026-07/bench-hetzner-2026-07-07-median.json)

Two comparisons live in one grid, kept separate on purpose. **Schema-to-API engines**
(FraiseQL, Hasura, PostGraphile) turn a schema into an API with no hand-written resolvers —
this is FraiseQL's category. **Hand-written servers** (*actix-web*, *async-graphql*,
*mercurius*) are reference points: the ceiling and the fast-GraphQL baseline, not the
comparison. FraiseQL authors its schema in Python, compiles it ahead of time, and serves it
from a standalone Rust binary — **no Python runs per request**.

### Schema-to-API engines — the direct comparison

| Engine | Q1 RPS | p50 | p99 | Q3 (nested) | RAM | €/1M req | Errors |
|--------|-------:|----:|----:|------------:|----:|---------:|--------|
| **fraiseql-tv** | **6 550** | **6.0 ms** | **9.4 ms** | **3 207** | **12 MB** | **€0.008** | 0% |
| fraiseql-v | 6 451 | 6.1 ms | 9.8 ms | 1 303 | 12 MB | €0.008 | 0% |
| postgraphile v5 | 2 099 | 18.2 ms | 39.4 ms | 1 177 | 127 MB | €0.025 | 0% |
| hasura v2.49 CE | 1 060 | 37.5 ms | 53.9 ms | 820 | 133 MB | €0.050 | 0% |

In its own category it is not close: **3.1× PostGraphile / 6.2× Hasura on Q1**, at a
third-to-a-sixth of the latency, in ~11× less RAM, and its lead *widens* with nesting depth
(no N+1 by construction). `-v` (JSONB composed on the fly) is the conservative variant;
`-tv` (pre-materialized) buys read speed with storage + write-time refresh.

### Reference points — hand-written servers

| Framework | Author | Runtime | Q1 RPS | Q3 | T1 |
|-----------|--------|---------|-------:|---:|---:|
| actix-web-rest | Rust | Rust | 1 339 | 3 281 | 2 568 |
| async-graphql | Rust | Rust | 1 146 | 1 421 | 3 606 |
| mercurius | Node.js | Node.js | 1 233 | 665 | 1 214 |

> Read FraiseQL's position honestly: against **hand-written** servers it does not win the
> trivial flat cases — raw Rust will always beat a compiled-from-schema engine on a query
> someone hand-tuned, and that is why they are shown. Against its **own category** it tops
> the field. The write path is shown just as honestly: FraiseQL's full-cascade mutation is
> deliberately slow (strong consistency), while its delta path competes with the fastest
> writers — see the [write-trade selector](site/#s5-write-trade).

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
overhead and TOAST effects can erase the win on write-heavy or wide-row workloads), which is
why the table above shows `-v` and `-tv` side by side. Per-variant numbers (including
`-tv-audit` and `-nocache` configurations) are in the
[interactive grid](site/) and the dated runs under [`reports/`](reports/).

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
