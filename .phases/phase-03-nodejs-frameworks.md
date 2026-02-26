# Phase 3: Node.js/TypeScript Frameworks

## Objective

Fix all 8 Node.js frameworks to achieve 0% error rates across Q1, Q2, Q2b.

## Frameworks & Root Causes

### 3.1 Apollo Server (won't start)

**File:** `frameworks/apollo-server/src/index.ts`

**Root cause:** Uses deprecated/non-existent `server.executeOperation()` pattern with Apollo Server 4.10+. The code tries to manually wire Apollo into a custom HTTP server instead of using the standard `startStandaloneServer` or `expressMiddleware` pattern.

**Fix strategy:**
- Option A: Rewrite to use `expressMiddleware` from `@apollo/server/express4` (recommended — matches other Node frameworks)
- Option B: Use `startStandaloneServer` (simpler but less flexible)

**Reference implementation:** Use `mercurius` or `graphql-yoga` as the pattern — they both successfully wire GraphQL into an HTTP server.

**Key changes:**
1. Replace manual `executeOperation` with `expressMiddleware`
2. Wire health endpoint separately on the Express app
3. Ensure DataLoaders are created per-request in the context factory

**Verification:** `docker compose up -d apollo && curl http://localhost:4002/health`

---

### 3.2 Apollo-ORM (won't start)

**File:** `frameworks/apollo-orm/src/index.ts`, `frameworks/apollo-orm/src/db.ts`

**Root causes:**
1. **TypeORM API misuse** — `AppDataSource.getRepository('User')` passes a string instead of the entity class. Should be `AppDataSource.getRepository(User)`.
2. **Dual-port setup** — GraphQL on 4004, health/metrics on 4005. The metrics server may not initialize before Docker's health check hits it.
3. **Same Apollo Server API issue as apollo-server**

**Fix strategy:**
1. Fix all `getRepository(string)` calls to use entity class imports
2. Fix Apollo Server integration (same as 3.1)
3. Ensure health endpoint is available before main server finishes setup (start metrics server first)

**Verification:** `curl http://localhost:4005/health && curl -X POST http://localhost:4004/graphql ...`

---

### 3.3 Express-REST (won't start)

**File:** `frameworks/express-rest/src/index.ts`, `frameworks/express-rest/src/db.ts`

**Root cause:** PostgreSQL `pg` library's `Pool` constructor doesn't support `min` property (line 12 in db.ts). The pool creation may throw or silently fail.

**Fix:**
```typescript
// db.ts — Remove `min` property:
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: parseInt(process.env.DB_POOL_MAX || '50'),
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 5000,
});
```

**Additional checks:**
- Verify DATABASE_URL is set in docker-compose for this service
- Check if Dockerfile builds successfully (TypeScript compilation)
- Verify port 8005 is correctly mapped

**Verification:** `curl http://localhost:8005/health && curl http://localhost:8005/users?limit=5`

---

### 3.4 Express-ORM (won't start)

**File:** `frameworks/express-orm/src/index.ts`, `frameworks/express-orm/src/db.ts`

**Root causes:**
1. **Missing `await` on `initDatabase()`** — Line 11 calls async function without awaiting, so the server starts before the database is connected
2. **Wrong default PORT** — Code defaults to 8001 but docker-compose sets PORT=8007
3. **Sequelize model relationships** — Foreign key definitions use `sourceKey: 'pk_user'` but queries may expect UUID `id` field

**Fixes:**
1. Add `await` to `initDatabase()` call (wrap in async IIFE or use top-level await)
2. Change default port: `const PORT = parseInt(process.env.PORT || '8007');`
3. Verify Sequelize model associations use correct keys

**Verification:** `curl http://localhost:8007/health && curl http://localhost:8007/users?limit=5`

---

### 3.5 Express-GraphQL (79.7% errors on Q1)

**File:** `frameworks/express-graphql/src/index.ts`

**Root cause:** The high error rate suggests the framework starts but most requests fail. Likely causes:
- Connection pool exhaustion under concurrency 40
- GraphQL execution errors (schema mismatch)
- Missing error handling causing unhandled promise rejections

**Investigation steps:**
1. `docker compose up -d express-graphql && docker compose logs express-graphql`
2. Send single Q1 query manually and inspect response
3. Send 40 concurrent queries and check for pool errors

**Fix strategy:**
- Add `pool.on('error', ...)` handler to prevent unhandled errors
- Verify pool size supports concurrency 40 (needs max >= 40)
- Add proper error handling in GraphQL resolver context
- Check if DataLoaders are created correctly per-request

**Verification:** `python tests/benchmark/bench_sequential.py --frameworks express-graphql --diagnose`

---

### 3.6 GraphQL-Yoga (64-100% errors)

**File:** `frameworks/graphql-yoga/src/index.ts`

**Root cause:** Similar to express-graphql — likely connection pool issues or unhandled errors under load.

**Investigation & fix:** Same approach as 3.5:
- Check pool configuration
- Add error handlers
- Verify schema matches expected queries
- Test under load

**Verification:** `python tests/benchmark/bench_sequential.py --frameworks graphql-yoga --diagnose`

---

### 3.7 Mercurius (3.3% Q1, 96.1% Q2 errors)

**File:** `frameworks/mercurius/src/index.ts`

**Root cause:** Q1 (users) nearly works but Q2 (posts) fails massively. This pattern matches a posts-specific bug:
- Possible: Posts query hits a different resolver path that has a bug
- Possible: Connection pool exhausted during Q2 (which touches more data)
- Possible: Fastify logger overhead causing timeouts

**Investigation steps:**
1. Send Q2 manually: `curl -X POST http://localhost:<port>/graphql -d '{"query":"{ posts(limit:10) { id title } }"}'`
2. Check if the posts resolver exists and returns correct structure
3. Disable Fastify logger (`logger: false`) and re-test

**Fix strategy:**
- Fix posts resolver if it's returning errors
- Reduce logger overhead for benchmarks
- Verify pool configuration

**Verification:** `python tests/benchmark/bench_sequential.py --frameworks mercurius --diagnose`

---

### 3.8 PostGraphile (not in benchmark registry)

**File:** `frameworks/postgraphile/src/index.ts`, `frameworks/postgraphile/src/middleware.ts`

**Root causes:**
1. **CommonJS/ESM mismatch** — `require.main === module` in an ESM package
2. **Wrong default DB port** — Defaults to 5434 instead of 5432
3. **Not registered in bench_sequential.py**

**Fix strategy:**
1. Replace `require.main === module` with `import.meta.url` check
2. Fix DB port default to 5432
3. Add PostGraphile to FRAMEWORKS dict in bench_sequential.py
4. Determine correct GraphQL endpoint path and query format

**Note:** PostGraphile auto-generates schema from database — queries may use different field names. Need to test introspection first and adapt queries accordingly. PostGraphile may need its own query variants in the benchmark registry.

**Verification:** `curl http://localhost:<port>/graphql` with introspection query, then Q1/Q2/Q2b adapted to PostGraphile's schema.

---

## Execution Order

1. **Express-REST** — Simplest fix (remove `min` from pool config)
2. **Express-ORM** — Quick fix (add await, fix port)
3. **Apollo Server** — Medium effort (rewrite server setup)
4. **Apollo-ORM** — Medium effort (fix TypeORM + Apollo)
5. **Mercurius** — Diagnosis first, then targeted fix
6. **Express-GraphQL** — Diagnosis first
7. **GraphQL-Yoga** — Diagnosis first
8. **PostGraphile** — ESM fix + registration

## Verification Gate

```bash
python tests/benchmark/bench_sequential.py \
  --frameworks apollo-server,apollo-orm,express-rest,express-orm,express-graphql,graphql-yoga,mercurius,postgraphile \
  --duration 10
```

Expected: 0% errors on Q1, Q2, Q2b for all 8 frameworks.

## Dependencies

- **Requires:** Phase 2 complete (Python frameworks passing, patterns established)
- **Blocks:** Phase 4 (Go frameworks)

## Status
[ ] Not Started
