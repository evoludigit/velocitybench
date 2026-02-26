# Phase 4: Go Frameworks

## Objective

Fix the 2 broken Go frameworks and resolve go-gqlgen's Q2b known bug.

## Current State

| Framework | Status | Issue |
|-----------|--------|-------|
| gin-rest | Working (5850 RPS Q1) | None |
| go-gqlgen | Partial (Q2b skipped) | Known bug in author resolution for nested queries |
| go-graphql-go | Won't start | Port mismatch: EXPOSE 8007 vs code default 8008 |
| graphql-go | Not registered | Not in bench_sequential.py or docker-compose benchmark profile |

## Frameworks & Root Causes

### 4.1 go-graphql-go (won't start)

**File:** `frameworks/go-graphql-go/cmd/server/main.go`, `frameworks/go-graphql-go/Dockerfile`

**Root cause:** Dockerfile `EXPOSE 8007` but code defaults to port `8008`. Docker-compose maps `8008:8008`. The mismatch between Dockerfile EXPOSE and actual port is cosmetic (EXPOSE is documentation only), but the real issue may be elsewhere.

**Investigation steps:**
1. `docker compose up -d go-graphql-go && docker compose logs go-graphql-go`
2. Check if the binary compiles successfully in Docker
3. Check if DATABASE_URL is correctly passed
4. Verify the health endpoint path

**Fix strategy:**
- Fix Dockerfile: `EXPOSE 8008` to match code default
- Or fix code to read PORT from environment variable: `port = os.Getenv("PORT")` with fallback
- Verify database connection string format for Go's pgx/pq driver
- Check go.mod dependencies compile correctly

**Verification:** `curl http://localhost:8008/health && curl -X POST http://localhost:8008/graphql -d '{"query":"{ users(limit:5) { id } }"}'`

---

### 4.2 graphql-go (not registered)

**File:** `frameworks/graphql-go/`

**Status:** Has code and Dockerfile but is not in the benchmark registry or docker-compose benchmark profile.

**Investigation steps:**
1. Check if this is a duplicate of go-graphql-go or a different library
2. Read the source to understand which Go GraphQL library it uses
3. Check docker-compose.yml for its service entry and port

**Fix strategy:**
1. Verify it builds and starts: `docker compose up -d graphql-go`
2. Test health endpoint and basic queries
3. Add to FRAMEWORKS dict in bench_sequential.py with correct URLs
4. Add to benchmark profile in docker-compose.yml if missing

**Verification:** Full benchmark run after registration.

---

### 4.3 go-gqlgen Q2b Bug

**File:** `frameworks/go-gqlgen/` (resolver files)

**Current state:** Q2b is marked as `None` (skipped) in bench_sequential.py with comment "known bug". Q1 works (5019 RPS), Q2 works (980 RPS but much slower than Q1 — suspicious).

**Root cause investigation:**
- Q2b requires `posts → author` resolution (nested query)
- The author resolver likely has a bug: missing field mapping, incorrect JOIN, or N+1 issue
- The Q2→Q1 performance drop (5019→980 RPS) suggests Q2 may also have issues

**Fix strategy:**
1. Read the gqlgen resolver for posts and author
2. Compare with gin-rest's author JOIN (which works at 2881 RPS on Q2b)
3. Fix the author resolver (likely a DataLoader or SQL query issue)
4. Update bench_sequential.py to re-enable Q2b for go-gqlgen

**Verification:** `python tests/benchmark/bench_sequential.py --frameworks go-gqlgen --duration 10` — all three queries should work.

---

## Execution Order

1. **go-graphql-go** — Port fix + build verification
2. **go-gqlgen Q2b** — Resolver bug fix
3. **graphql-go** — Investigate + register

## Verification Gate

```bash
python tests/benchmark/bench_sequential.py \
  --frameworks go-gqlgen,go-graphql-go,graphql-go,gin-rest \
  --duration 10
```

Expected: 0% errors on Q1, Q2, Q2b for all 4 Go frameworks.

## Dependencies

- **Requires:** Phase 3 complete (Node.js frameworks passing)
- **Blocks:** Phase 5 (JVM frameworks)

## Status
[ ] Not Started
