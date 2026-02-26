# Phase 6: Ruby, PHP, C# Frameworks

## Objective

Fix all 5 frameworks in these ecosystems to achieve 0% error rates, plus improve webonyx-graphql-php performance.

## Current State

| Framework | Language | Status | Issue |
|-----------|----------|--------|-------|
| ruby-rails | Ruby | Won't start | Complex Docker build/startup |
| hanami | Ruby | Won't start | Framework initialization |
| php-laravel | PHP | 100% errors | Missing config + Octane not configured |
| webonyx-graphql-php | PHP | Working (63 RPS) | Single-threaded PHP built-in server |
| csharp-dotnet | C# | 100% errors | Missing project structure/config |

## Frameworks & Root Causes

### 6.1 ruby-rails (won't start)

**Files:** `frameworks/ruby-rails/Dockerfile`, `frameworks/ruby-rails/docker-entrypoint.sh`, `frameworks/ruby-rails/Gemfile`

**Root causes:**
1. **Complex startup sequence** — docker-entrypoint.sh runs `db:create`, `db:migrate`, `assets:precompile` in sequence. Any failure is silent (`|| true` pattern).
2. **Asset precompilation with dummy SECRET_KEY_BASE** — May fail with Rails 8.1.1
3. **Database already exists** — `db:create` will error because the database is managed by the postgres container. `db:migrate` may also fail if there are no Rails migrations.

**Investigation steps:**
1. `docker compose build ruby-rails` — check if gem install succeeds
2. `docker compose up -d ruby-rails && docker compose logs ruby-rails` — check runtime errors
3. The most likely failure is in the entrypoint script

**Fix strategy:**
1. Simplify entrypoint: skip `db:create` (database already exists), skip `db:migrate` (schema managed by postgres container), skip `assets:precompile` (API-only app)
2. Set `SECRET_KEY_BASE` to a fixed value in docker-compose environment
3. Verify `config/database.yml` uses DATABASE_URL from environment
4. Check that Rails API routes match expected endpoints
5. Verify Rails connects to the `benchmark` schema

**Key consideration:** Rails apps typically manage their own schema via migrations. Since VelocityBench's schema is managed by the postgres container, Rails needs to be configured to use the existing schema without trying to migrate.

**Verification:** `curl http://localhost:<port>/health && curl http://localhost:<port>/api/users?limit=5`

---

### 6.2 hanami (won't start)

**Files:** `frameworks/hanami/Dockerfile`, `frameworks/hanami/Gemfile`, `frameworks/hanami/config/application.rb`

**Root causes:**
1. **Missing Gemfile.lock** — Dockerfile copies `Gemfile.lock*` with optional glob. Without a lock file, `bundle install` resolves deps at build time (slow, non-reproducible).
2. **Hanami 2.1 initialization complexity** — Requires specific directory structure and configuration
3. **Missing Puma configuration** — Dockerfile may reference `config/puma.rb` that doesn't exist
4. **Route configuration** — Hanami 2.x routing may not be configured correctly

**Investigation steps:**
1. `docker compose build hanami` — check if bundle install succeeds
2. Check if all required Hanami directories exist (app/, config/, lib/, etc.)
3. Verify routes are defined correctly for Hanami 2.x

**Fix strategy:**
1. Generate and commit Gemfile.lock: run `bundle lock` locally with correct Ruby version
2. Create `config/puma.rb` if missing (basic config: workers, threads, port)
3. Verify Hanami application boots: `bundle exec hanami server`
4. Fix database connection configuration
5. Verify route definitions match expected API endpoints

**Verification:** `curl http://localhost:<port>/health`

---

### 6.3 php-laravel (starts but 100% errors)

**Files:** `frameworks/php-laravel/Dockerfile`, `frameworks/php-laravel/docker-entrypoint.sh`, `frameworks/php-laravel/composer.json`

**Root causes:**
1. **Missing .env file** — `.env.example` copied but database credentials may not be populated
2. **APP_KEY not generated** — `php artisan key:generate` may fail silently
3. **Lighthouse GraphQL not configured** — GraphQL schema and routes may not be set up
4. **Octane discrepancy** — composer.json requires Octane but Dockerfile may use `artisan serve`
5. **Missing PHP extensions** — Platform requirements ignored during composer install

**Investigation steps:**
1. `docker compose up -d php-laravel && docker compose logs php-laravel`
2. `docker compose exec php-laravel cat .env` — check configuration
3. `docker compose exec php-laravel php artisan route:list` — check if routes exist
4. Test: `curl http://localhost:<port>/graphql -d '{"query":"{ __typename }"}'`

**Fix strategy:**
1. Create proper `.env` file with database credentials in Dockerfile or entrypoint
2. Ensure APP_KEY is generated before server starts
3. Verify Lighthouse schema file exists and defines User/Post/Comment types
4. Either configure Octane properly or switch to `php artisan serve` consistently
5. Install required PHP extensions in Dockerfile

**Verification:** `curl http://localhost:<port>/graphql -d '{"query":"{ users(limit:5) { id } }"}'`

---

### 6.4 webonyx-graphql-php (working but 63 RPS — performance fix)

**Files:** `frameworks/webonyx-graphql-php/Dockerfile`, `frameworks/webonyx-graphql-php/public/index.php`

**Root cause:** Uses PHP's built-in development server (`php -S 0.0.0.0:4000`) which is **single-threaded**. Every request blocks the entire server. Under concurrency 40, this creates massive queuing.

**Fix strategy — Option A (recommended): Add PHP-FPM + Nginx**
1. Install php-fpm and nginx in Dockerfile
2. Configure nginx to proxy to php-fpm
3. Configure php-fpm with appropriate worker count (pm = dynamic, max_children = 20)
4. This should increase RPS by 10-50x

**Fix strategy — Option B: Use RoadRunner or Swoole**
1. Install RoadRunner (Go-based PHP application server)
2. Configure worker pool
3. Higher performance than FPM but more complex setup

**Fix strategy — Option C: Use FrankenPHP**
1. Modern PHP application server
2. Single binary, easy Docker setup
3. Good performance with worker mode

**Recommendation:** Option A (FPM + Nginx) is the most standard approach and easiest to debug. Target: 500+ RPS (comparable to Python frameworks).

**Verification:** `python tests/benchmark/bench_sequential.py --frameworks webonyx-graphql-php --duration 10`

---

### 6.5 csharp-dotnet (starts but 100% errors)

**Files:** `frameworks/csharp-dotnet/Dockerfile`, `frameworks/csharp-dotnet/FraiseQL.Benchmark/`

**Root causes:**
1. **Missing or incomplete project structure** — The `.csproj` and `Program.cs` may not define proper endpoints
2. **No appsettings.json** — Database connection string not configured
3. **Health endpoint may not be implemented** — Dockerfile expects `/health` but code may not define it
4. **No database connectivity setup** — Missing Npgsql or Entity Framework configuration

**Investigation steps:**
1. `docker compose build csharp-dotnet` — check if `dotnet build` succeeds
2. `docker compose up -d csharp-dotnet && docker compose logs csharp-dotnet`
3. Check if the app starts and which port it listens on
4. Verify `Program.cs` or `Startup.cs` defines the expected endpoints

**Fix strategy:**
1. Add `appsettings.json` with database connection string
2. Implement or fix health endpoint at `/health`
3. Verify GraphQL or REST endpoints match expected query patterns
4. Add Npgsql connection pooling
5. May need significant implementation work if the project is skeletal

**Note:** The project directory is named `FraiseQL.Benchmark` which suggests it may have been scaffolded specifically for this project but left incomplete.

**Verification:** `curl http://localhost:8080/health && curl http://localhost:8080/graphql -d '{"query":"{ users(limit:5) { id } }"}'`

---

## Execution Order

1. **php-laravel** — Likely closest to working (starts, just misconfigured)
2. **ruby-rails** — Simplify entrypoint, fix config
3. **webonyx-graphql-php** — Performance improvement (already works functionally)
4. **csharp-dotnet** — May need significant implementation
5. **hanami** — Niche framework, most complex Ruby setup

## Verification Gate

```bash
python tests/benchmark/bench_sequential.py \
  --frameworks ruby-rails,hanami,php-laravel,webonyx-graphql-php,csharp-dotnet \
  --duration 10
```

Expected: 0% errors on Q1, Q2, Q2b for all 5 frameworks. webonyx-graphql-php should achieve 300+ RPS on Q1.

## Notes

- Ruby/PHP/C# frameworks have the least institutional knowledge in this project — expect more surprises
- Each ecosystem has its own dependency management complexity (Bundler, Composer, NuGet)
- Consider whether hanami and csharp-dotnet add enough value to justify the effort — they're niche frameworks. If time-constrained, deprioritize these.

## Dependencies

- **Requires:** Phase 5 complete (JVM frameworks passing)
- **Blocks:** Phase 7 (Validation & Reporting)

## Status
[ ] Not Started
