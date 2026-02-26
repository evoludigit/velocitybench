# Phase 5: Java/JVM Frameworks

## Objective

Fix all 4 broken JVM frameworks to achieve 0% error rates.

## Current State

| Framework | Status | Issue |
|-----------|--------|-------|
| spring-boot-orm | Working (4693 RPS Q1) | None |
| quarkus-graphql | Working (4913 RPS Q1) | None |
| java-spring-boot | Won't start | Port mismatch |
| spring-boot-orm-naive | Won't start | Port hardcoded + old Spring Boot |
| micronaut-graphql | Won't start | Build/config issues |
| play-graphql | Won't start | SBT/Scala build issues |

## Frameworks & Root Causes

### 5.1 java-spring-boot (won't start)

**Files:** `frameworks/java-spring-boot/src/main/resources/application.yaml`, `frameworks/java-spring-boot/Dockerfile`

**Root cause:** Port configuration mismatch:
- Dockerfile `EXPOSE 8018`
- application.yaml default: `port: ${SERVER_PORT:8018}`
- docker-compose.yml maps `8010:8010` and sets `SERVER_PORT=8010`

This should actually work because docker-compose passes `SERVER_PORT=8010` as an environment variable, and Spring will use it. The real issue is likely elsewhere.

**Investigation steps:**
1. `docker compose up -d java-spring-boot && docker compose logs java-spring-boot`
2. Check if Maven build succeeds in Docker
3. Check for missing database migration or schema issues
4. Verify `spring.datasource.url` matches the benchmark database
5. Check if Java 21 runtime is correctly configured

**Common Spring Boot issues:**
- Flyway/Liquibase migration failures (if configured)
- Missing JDBC driver
- Wrong schema name in queries (`benchmark.tb_user` vs just `tb_user`)
- Spring Boot actuator not exposing health endpoint

**Fix strategy:** Diagnose from Docker logs, then apply targeted fix.

**Verification:** `curl http://localhost:8010/actuator/health && curl http://localhost:8010/api/users?page=0&size=5`

---

### 5.2 spring-boot-orm-naive (won't start)

**Files:** `frameworks/spring-boot-orm-naive/src/main/resources/application.yaml`, `frameworks/spring-boot-orm-naive/pom.xml`

**Root causes:**
1. **Port hardcoded to 8017** — application.yaml line 11: `port: 8017` (no `${SERVER_PORT:}` placeholder). Docker-compose expects 8010 inside the container.
2. **Spring Boot 2.7.18** — Very old version, may have compatibility issues with Java 21 or PostgreSQL driver
3. **Duplicate dependencies** — `spring-boot-starter-jdbc` declared twice in pom.xml

**Fixes:**
1. Change `port: 8017` to `port: ${SERVER_PORT:8017}` in application.yaml
2. Consider upgrading Spring Boot version to match spring-boot-orm (which works)
3. Remove duplicate dependency in pom.xml
4. Verify docker-compose passes SERVER_PORT environment variable

**Verification:** `curl http://localhost:8014/actuator/health`

---

### 5.3 micronaut-graphql (won't start)

**Files:** `frameworks/micronaut-graphql/build.gradle`, `frameworks/micronaut-graphql/src/main/resources/application.yml`

**Root causes:**
- Gradle build may fail during Docker build
- Database configuration in application.yml may be incomplete
- Schema `benchmark` may not be set correctly in JDBC URL

**Investigation steps:**
1. `docker compose up -d micronaut-graphql && docker compose logs micronaut-graphql`
2. Check if Gradle build succeeds (this is the most likely failure point)
3. Verify JDBC URL format: `jdbc:postgresql://postgres:5432/velocitybench_benchmark?currentSchema=benchmark`
4. Check if GraphQL schema files are present and valid

**Fix strategy:**
- Fix Gradle build if it fails (dependency resolution, Java version)
- Fix database configuration (connection string, schema)
- Verify GraphQL schema definition matches expected queries

**Verification:** `curl http://localhost:<port>/health`

---

### 5.4 play-graphql (won't start)

**Files:** `frameworks/play-graphql/build.sbt`, `frameworks/play-graphql/Dockerfile`, `frameworks/play-graphql/conf/application.conf`

**Root causes:**
1. **Complex build chain** — Scala 2.13.8 + SBT 1.6.2 + Play Framework = very slow, fragile Docker build
2. **Application secret handling** — Dockerfile passes `APPLICATION_SECRET` env var but may not be set
3. **Old dependency versions** — Scala 2.13.8 and SBT 1.6.2 are outdated

**Investigation steps:**
1. `docker compose build play-graphql` (watch for build failures — this will take a long time)
2. If build succeeds, check runtime logs
3. Verify application.conf database configuration

**Fix strategy:**
- Fix application secret: add default in application.conf or docker-compose environment
- Update SBT/Scala versions if build fails
- Verify database configuration
- This is the highest-effort JVM fix due to the Scala/SBT/Play stack complexity

**Verification:** `curl http://localhost:<port>/health`

---

## Execution Order

1. **spring-boot-orm-naive** — Simple port fix
2. **java-spring-boot** — Diagnose from logs, likely simple fix
3. **micronaut-graphql** — Build investigation
4. **play-graphql** — Complex build chain, do last

## Verification Gate

```bash
python tests/benchmark/bench_sequential.py \
  --frameworks spring-boot,spring-boot-orm,spring-boot-orm-naive,quarkus-graphql,micronaut-graphql,play-graphql \
  --duration 10
```

Expected: 0% errors on Q1, Q2, Q2b for all 6 JVM frameworks.

## Notes

- JVM frameworks have long startup times (10-30s) — increase health check timeouts if needed
- Spring Boot ORM (the working one) is the reference implementation for Java
- Quarkus (also working) is the reference for JVM GraphQL
- play-graphql may need significant effort due to Scala ecosystem complexity — consider deprioritizing if time-constrained

## Dependencies

- **Requires:** Phase 4 complete (Go frameworks passing)
- **Blocks:** Phase 6 (Ruby/PHP/C# frameworks)

## Status
[ ] Not Started
