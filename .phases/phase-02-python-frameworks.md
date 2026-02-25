# Phase 2: Python Frameworks

## Objective

Fix all 6 Python frameworks to achieve 0% error rates across Q1, Q2, Q2b.

## Frameworks & Root Causes

### 2.1 FastAPI-REST (47% Q1 errors, 97.7% Q2 errors)

**File:** `frameworks/fastapi-rest/main.py`

**Root cause:** The `/posts` endpoint returns `author_id` and `author_username` as flat fields on the post object instead of nesting them as an `author` sub-object. When the benchmark sends Q2 (`posts(limit:10) { id title }`), the response likely contains extra fields or the query is actually hitting a different code path that fails.

**Investigation steps:**
1. Start fastapi-rest in isolation: `docker compose up -d postgres fastapi-rest`
2. Send Q1 manually: `curl http://localhost:8003/users?limit=20 | jq .`
3. Send Q2 manually: `curl http://localhost:8003/posts?limit=10 | jq .`
4. Compare response shapes with working frameworks (gin-rest, actix-web-rest)

**Likely fixes:**
- Check if the posts query is failing due to connection pool exhaustion under concurrency 40
- Check if the response shape matches what bench_sequential.py expects
- Verify database queries work with the medium dataset (50K posts)
- Fix any async connection pool sizing issues (asyncpg pool may be too small for concurrent load)

**Verification:** `python tests/benchmark/bench_sequential.py --frameworks fastapi-rest --diagnose`

---

### 2.2 Strawberry (0% Q1 errors, 95.8% Q2 errors)

**File:** `frameworks/strawberry/main.py`

**Root cause:** UUID type mismatch in DataLoader. The `load_posts_batch()` function (around line 73) passes string UUIDs to asyncpg's `ANY($1)` operator, but asyncpg may return UUID objects. The `post_map` dict uses UUID keys from the database but string lookups from the DataLoader, causing all lookups to return `None`.

**Fix:**
```python
# In load_posts_batch (line ~86):
# Change:
post_map = {post["id"]: post for post in result}
return [post_map.get(key) for key in keys]
# To:
post_map = {str(post["id"]): post for post in result}
return [post_map.get(str(key)) for key in keys]
```

Apply the same fix to all batch loader functions:
- `load_users_batch()` — likely works because Q1 doesn't use DataLoader
- `load_posts_batch()` — Q2 fails here
- `load_posts_by_author_batch()` — used for user→posts resolution
- `load_comments_by_post_batch()` — used for post→comments resolution

**Why Q1 works:** The `users` query fetches directly from the database with a simple `SELECT` — no DataLoader involved. Only nested field resolution (posts on a user, author on a post) uses DataLoaders.

**Verification:** `python tests/benchmark/bench_sequential.py --frameworks strawberry --diagnose`

---

### 2.3 Graphene (won't start)

**File:** `frameworks/graphene/main.py`

**Root causes:**
1. **Duplicate `/health` route** — Line ~476 defines a second `/health` endpoint that overrides the proper HealthCheckManager-based one from line ~410
2. **Port conflict** — Graphene uses port 8000 internally but docker-compose maps it to 8002 externally. Check that the container actually starts on the correct port.
3. **Possible startup crash** — Need to check Docker logs: `docker compose logs graphene`

**Investigation steps:**
1. `docker compose up -d postgres graphene && docker compose logs graphene`
2. If container exits, check for import errors or port binding issues
3. Check if HealthCheckManager import path is correct (uses `common/` module)

**Fix strategy:**
- Remove duplicate health endpoint (keep the HealthCheckManager-based one)
- Verify port matches docker-compose mapping
- Fix any import path issues for the `common/` shared module
- Apply same UUID string conversion fix as Strawberry if DataLoaders have the same issue

**Verification:** `curl http://localhost:8002/health && curl -X POST http://localhost:8002/graphql -H 'Content-Type: application/json' -d '{"query":"{ users(limit:5) { id } }"}'`

---

### 2.4 Flask-REST (won't start)

**File:** `frameworks/flask-rest/main.py`

**Root causes:**
1. **Logic bug in includes processing** — Around line 281-282, the includes processing block is inside an `else` branch after checking `includes = []`, making it unreachable
2. **Development server instead of Gunicorn** — The Dockerfile should use `gunicorn` (listed in requirements) but `main.py` uses `app.run()` directly
3. **Possible startup crash** — Check Docker logs

**Investigation steps:**
1. `docker compose up -d postgres flask-rest && docker compose logs flask-rest`
2. Check if the container starts at all
3. Test with `curl http://localhost:8004/health`

**Fix strategy:**
- Fix the includes logic: move the includes processing to a standalone `if` block, not nested inside `else`
- Verify Dockerfile CMD uses gunicorn or at least flask with proper host/port
- Check psycopg3 pool initialization (sync pool for sync Flask)

**Verification:** `curl http://localhost:8004/users?limit=5 | jq .`

---

### 2.5 Ariadne (won't start)

**File:** `frameworks/ariadne/main.py`

**Root causes:**
1. **Schema field name mismatch** — Schema expects `fullName` (camelCase) but resolvers return `full_name` (snake_case)
2. **Port conflict** — Uses port 4000 internally, which conflicts with multiple other frameworks. However, docker-compose should map to a unique external port, so this may not be the real issue.

**Investigation steps:**
1. `docker compose up -d postgres ariadne && docker compose logs ariadne`
2. Check if the issue is a build failure, import error, or runtime crash
3. Test schema introspection if it starts

**Fix strategy:**
- Add `snake_case_fallback_resolvers` to Ariadne's `make_executable_schema()` call, or
- Add explicit field resolvers for camelCase→snake_case mapping
- Fix any import path issues for shared modules

**Verification:** `curl -X POST http://localhost:<port>/graphql -H 'Content-Type: application/json' -d '{"query":"{ users(limit:5) { id username fullName } }"}'`

---

### 2.6 ASGI-GraphQL (won't start)

**File:** `frameworks/asgi-graphql/main.py`

**Root causes:**
1. **Schema/resolver field name mismatch** — Same camelCase vs snake_case issue as Ariadne
2. **Missing schema validation** — Uses graphql-core directly without proper type/resolver wiring
3. **Port conflict** — Same port 4000 issue

**Investigation steps:**
1. `docker compose up -d postgres asgi-graphql && docker compose logs asgi-graphql`
2. Identify whether it's a build, import, or runtime failure

**Fix strategy:**
- Fix schema field mapping (camelCase resolvers)
- Verify graphql-core schema definition matches expected query structure
- Fix any import/module issues

**Verification:** Same as Ariadne but on ASGI-GraphQL's port.

---

## Execution Order

1. **Strawberry** — Highest confidence fix (UUID type conversion), highest value (popular framework)
2. **FastAPI-REST** — Need diagnosis first, then targeted fix
3. **Graphene** — Likely quick fix (duplicate route removal)
4. **Flask-REST** — Logic bug fix + server configuration
5. **Ariadne** — Schema field mapping
6. **ASGI-GraphQL** — Schema field mapping (similar to Ariadne)

## Verification Gate

All 6 frameworks must pass:
```bash
make smoke-test    # health checks
make parity-test   # data consistency
python tests/benchmark/bench_sequential.py --frameworks strawberry,graphene,fastapi-rest,flask-rest,ariadne,asgi-graphql --duration 10
```

Expected: 0% errors on Q1, Q2, Q2b for all 6 frameworks.

## Dependencies

- **Requires:** Phase 1 complete (diagnostic tooling available for debugging)
- **Blocks:** Phase 3 (Node.js frameworks)

## Status
[ ] Not Started
