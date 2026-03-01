# VelocityBench

GraphQL & REST framework performance benchmarks — 8 languages, reproducible methodology, real PostgreSQL data.

> **Latest run**: February 2026 · sequential isolation · 40 workers · 20s per framework · dataset: 10 000 users / 50 000 posts / 200 000 comments

---

## Results

Full tables: [reports/bench-sequential-2026-02-22.md](reports/bench-sequential-2026-02-22.md)

### Q1 — `users(limit: 20) { id username fullName }`

| Framework | Language | Type | RPS | p50 | p99 | Errors |
|-----------|----------|------|----:|----:|----:|--------|
| gin-rest | Go | REST | 5 850 | 6.6 ms | 11.6 ms | 0% |
| actix-web-rest | Rust | REST | 5 501 | 7.0 ms | 12.0 ms | 0% |
| go-gqlgen | Go | GraphQL | 5 019 | 7.7 ms | 13.4 ms | 0% |
| quarkus-graphql | Java | GraphQL | 4 913 | 7.5 ms | 20.7 ms | 0% |
| spring-boot-orm | Java | REST | 4 693 | 7.7 ms | 20.1 ms | 0% |
| mercurius | Node.js | GraphQL | 4 681 | 7.6 ms | 14.8 ms | 0% |
| juniper | Rust | GraphQL | 4 658 | 8.3 ms | 15.0 ms | 0% |
| async-graphql | Rust | GraphQL | 4 038 | 8.7 ms | 29.8 ms | 0% |
| fastapi-rest | Python | REST | 1 707 | 12.9 ms | 21.2 ms | 47% |
| strawberry | Python | GraphQL | 906 | 42.3 ms | 53.1 ms | 0% |
| webonyx-graphql-php | PHP | GraphQL | 63 | 644 ms | 813 ms | 0% |

### Q2b — `posts(limit: 10) { id title author { username fullName } }` (nested join)

| Framework | Language | Type | RPS | p50 | p99 | Errors |
|-----------|----------|------|----:|----:|----:|--------|
| actix-web-rest | Rust | REST | 5 752 | 6.6 ms | 14.2 ms | 0% |
| juniper | Rust | GraphQL | 3 417 | 11.5 ms | 16.6 ms | 0% |
| quarkus-graphql | Java | GraphQL | 3 414 | 11.0 ms | 25.3 ms | 0% |
| async-graphql | Rust | GraphQL | 2 992 | 11.8 ms | 34.2 ms | 0% |
| gin-rest | Go | REST | 2 881 | 12.8 ms | 33.3 ms | 0% |
| strawberry | Python | GraphQL | 431 | 54.5 ms | 70.1 ms | 78% |

> **Not included in summary:** apollo-server, express-rest, flask-rest, ruby-rails, ariadne, graphene, and several others did not become healthy in this run. Contributions to fix them are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).

---

## What We Benchmark

Three query scenarios on a shared PostgreSQL dataset, each revealing different characteristics:

| Scenario | Query | What it tests |
|----------|-------|---------------|
| **Q1** | `users(limit: 20) { id username fullName }` | Simple list read |
| **Q2** | `posts(limit: 10) { id title }` | Simple list, different table |
| **Q2b** | `posts(limit: 10) { id title author { … } }` | Nested join — exposes N+1 risks |

**Metrics**: RPS (requests per second), p50 / p95 / p99 latency, error rate.

**Method**: Sequential isolation — each framework runs alone against PostgreSQL. No resource contention between frameworks. Each scenario runs for 20 seconds after a 5-second warmup.

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

| Framework | Language | Status |
|-----------|----------|--------|
| async-graphql | Rust | ✅ |
| juniper | Rust | ✅ |
| go-gqlgen | Go | ✅ |
| mercurius | Node.js | ✅ |
| quarkus-graphql | Java | ✅ |
| strawberry | Python | ✅ |
| fraiseql | Python | ✅ |
| apollo-server | Node.js | ⚠️ needs fix |
| graphene | Python | ⚠️ needs fix |
| ariadne | Python | ⚠️ needs fix |
| webonyx-graphql-php | PHP | ✅ |
| ruby-rails (graphql-ruby) | Ruby | ⚠️ needs fix |
| hasura | — | managed |

### REST

| Framework | Language | Status |
|-----------|----------|--------|
| gin-rest | Go | ✅ |
| actix-web-rest | Rust | ✅ |
| spring-boot-orm | Java | ✅ |
| fastapi-rest | Python | ⚠️ high error rate |
| flask-rest | Python | ⚠️ needs fix |
| express-rest | Node.js | ⚠️ needs fix |
| csharp-dotnet | C# | ⚠️ needs fix |

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
