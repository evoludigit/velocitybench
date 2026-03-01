# VelocityBench — Quick Start

Everything you need to run your first benchmark in 15 minutes.

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Docker | 24+ | with Compose v2 |
| RAM | 8 GB minimum | 16 GB recommended for full suite |
| Disk | 15 GB free | containers + dataset |

No other local tooling required — Python, Go, Rust, etc. all run inside Docker.

---

## 1. Clone and start the stack

```bash
git clone https://github.com/evoludigit/velocitybench.git
cd velocitybench

# Start PostgreSQL + all benchmark frameworks with a medium dataset
# (10 000 users / 50 000 posts / 200 000 comments)
make up-medium
```

This pulls and starts all containers. First run takes a few minutes to download images and seed the database.

**Smaller dataset** (faster startup, less representative):
```bash
make up   # xs dataset — good for verifying setup
```

---

## 2. Verify health (optional but recommended)

```bash
make smoke-test
```

This runs health checks and basic queries against all frameworks. Frameworks that fail will be reported — don't worry if some are unhealthy, not all are fully functional yet (see the status table in [README.md](README.md)).

Quick status dashboard:
```bash
make status
```

---

## 3. Run the benchmark

```bash
make bench-sequential
```

Each framework runs alone for 20 seconds (after a 5-second warmup), with a 5-second cooldown between them. Results are written to `reports/bench-sequential-YYYY-MM-DD.md` and `.json`.

**Customise the run:**

```bash
# Fewer frameworks, quicker run (~5 min)
make bench-sequential FRAMEWORKS="gin-rest actix-web-rest go-gqlgen async-graphql juniper"

# Shorter measurement window
make bench-sequential DURATION=10 CONCURRENCY=20

# Single framework
make bench-one FRAMEWORK=strawberry
```

---

## 4. Read the results

```bash
cat reports/bench-sequential-$(date +%Y-%m-%d).md
```

Or open the `.json` file for programmatic processing. The Markdown report contains three tables (Q1, Q2, Q2b) and a cross-framework summary sorted by RPS.

Previous runs are in `reports/archive/`.

---

## 5. Tear down

```bash
make down
```

---

## Common Tasks

### Check what frameworks are available

```bash
make framework-list
```

### Start / stop a single framework

```bash
make framework-start FRAMEWORK=fraiseql
make framework-stop FRAMEWORK=fraiseql
```

### Run parity check (verify all frameworks return identical data)

```bash
make parity-test
```

### Run N+1 regression guard

```bash
make n1-guard
```

### Full pre-benchmark validation gate

```bash
make validate   # smoke-test + parity-test + n1-guard
```

---

## Troubleshooting

**Containers don't start / immediately exit**
```bash
docker compose logs <service-name>   # check specific container logs
```

**Seed data missing or incorrect row counts**
```bash
make test-seed
```

**A framework reports unhealthy**

Check the known-broken list in [README.md](README.md). If it's not listed there, check its container logs:
```bash
docker compose logs <framework-name>
```

**Out of memory during benchmark**

Reduce concurrency:
```bash
make bench-sequential CONCURRENCY=10
```

Or benchmark fewer frameworks at once.

---

## Next Steps

- **Add a framework**: [docs/ADD_FRAMEWORK_GUIDE.md](docs/ADD_FRAMEWORK_GUIDE.md)
- **Understand the methodology**: [docs/SCOPE_AND_LIMITATIONS.md](docs/SCOPE_AND_LIMITATIONS.md)
- **Architecture deep-dive**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Database schema**: [docs/DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md)
- **All docs**: [docs/MASTER_INDEX.md](docs/MASTER_INDEX.md)
