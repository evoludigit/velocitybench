# Phase 5: Docker Compose Hardening

## Objective

Add resource limits to docker-compose services to prevent any single framework from consuming all host resources during benchmarks.

## Success Criteria

- [ ] All framework services have memory limits
- [ ] All framework services have CPU limits
- [ ] PostgreSQL has appropriate resource limits (compatible with its shared_buffers setting)
- [ ] Limits are generous enough to not affect benchmark results

## Tasks

### 5.1 Add resource limits to framework services

**File:** `docker-compose.yml`

**Strategy:** Add `deploy.resources.limits` to each framework service. Since this is a benchmarking tool, limits should be generous (prevent runaway, not constrain performance).

The benchmark harness uses `docker compose up/down` (confirmed in `bench_sequential.py`), NOT `docker stack deploy`. The `deploy.resources.limits` section works with Docker Compose v2 in non-Swarm mode.

**Recommended limits per service type:**

| Service Type | Memory Limit | CPU Limit | Rationale |
|-------------|-------------|-----------|-----------|
| Go/Rust frameworks | 512M | 2.0 | Compiled, low memory footprint |
| Node.js frameworks | 1G | 2.0 | V8 heap can grow |
| Python frameworks | 1G | 2.0 | Connection pools, GIL |
| Java/JVM frameworks | 2G | 2.0 | JVM heap requirements |
| PHP frameworks | 1G | 2.0 | PHP-FPM worker pools |
| Ruby frameworks | 1G | 2.0 | Rails memory usage |
| C#/.NET frameworks | 1G | 2.0 | CLR overhead |
| PostgreSQL | **12G** | 4.0 | **See critical note below** |
| Monitoring (Prometheus, Grafana) | 1G | 1.0 | Background services |

### 5.2 PostgreSQL memory limit — CRITICAL

**Problem identified during review:** The original plan proposed `memory: 4G` for PostgreSQL, but the actual postgres command configuration includes:

```yaml
-c shared_buffers=${DB_SHARED_BUFFERS:-8GB}
-c effective_cache_size=${DB_EFFECTIVE_CACHE_SIZE:-24GB}
-c work_mem=${DB_WORK_MEM:-64MB}
-c maintenance_work_mem=${DB_MAINTENANCE_WORK_MEM:-2GB}
-c max_connections=${DB_MAX_CONNECTIONS:-300}
```

**`shared_buffers=8GB` alone would exceed a 4G container limit and cause an immediate OOM kill.**

`effective_cache_size=24GB` is an optimizer hint (not an allocation) so it doesn't consume memory, but `shared_buffers` is a real memory allocation at startup.

**Resolution — two approaches (choose one):**

**Option A (recommended): Set PostgreSQL limit to 12G**
```yaml
deploy:
  resources:
    limits:
      memory: 12G
      cpus: '4.0'
```
Rationale: 8G shared_buffers + 2G maintenance_work_mem + overhead for 300 connections × 64MB work_mem (not all concurrent) + OS/PG overhead. 12G provides headroom without being unlimited.

**Option B: Make limits match the env-var defaults**
Since all PostgreSQL memory settings are already configurable via environment variables (`DB_SHARED_BUFFERS`, etc.), the compose limit could reference them too. But compose `deploy.resources.limits` doesn't support variable interpolation — so just use a generous fixed value and document that if someone overrides `DB_SHARED_BUFFERS` upward, they must also raise the container limit.

**Action:** Go with Option A (12G) and add a YAML comment explaining the relationship:
```yaml
postgres:
  # ...
  deploy:
    resources:
      limits:
        memory: 12G  # Must exceed shared_buffers (default 8GB) + work_mem headroom
        cpus: '4.0'
```

### 5.3 Pattern to add to each service

```yaml
services:
  framework-name:
    # ... existing config ...
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '2.0'
```

### 5.4 Verify limits don't affect benchmarks

After adding limits, run a quick benchmark on 2-3 representative frameworks and compare RPS with previous results:
- One Go/Rust framework (low memory: actix-web-rest or go-gqlgen)
- One Node.js framework (medium memory: express-graphql or mercurius)
- One JVM framework (high memory: spring-boot)

If any framework hits OOM or shows >5% RPS degradation, increase its limit.

## Implementation Notes

- Do NOT add `reservations` — only `limits`. Reservations would prevent running multiple services concurrently on smaller machines.
- Sequential benchmark mode means only 1-2 framework services run at a time, so limits are about safety, not scheduling.
- The benchmark harness uses `docker compose` (not `docker stack deploy`), confirmed in `bench_sequential.py` line 1322.
- All PostgreSQL tuning parameters are already env-var configurable — document in a comment that container memory limit must be raised if `DB_SHARED_BUFFERS` is increased beyond default.

## Verification

```bash
# Check all services have limits
docker compose config | grep -A5 "resources:" | head -50

# Verify postgres starts without OOM
docker compose up -d postgres
sleep 5
docker compose exec postgres pg_isready
docker compose down

# Run smoke test with a framework
docker compose up -d postgres actix-web-rest
sleep 3
curl -f http://localhost:8001/health
docker compose down
```

## Status
[x] Complete
