# VelocityBench — 100% Framework Coverage Plan

## Goal

Transform VelocityBench from 11 working frameworks (of 33 registered) to **33/33 clean benchmark results** with 0% error rates across all query types (Q1, Q2, Q2b), plus benchmark harness improvements.

## Current State (2026-02-22 Benchmark)

| Status | Count | Frameworks |
|--------|------:|------------|
| **Clean (0% errors)** | 8 | actix-web-rest, async-graphql, juniper, gin-rest, spring-boot-orm, quarkus-graphql, fraiseql-tv, fraiseql-tv-nocache |
| **Clean but slow** | 1 | webonyx-graphql-php (63 RPS) |
| **Clean partial** | 2 | fraiseql-v (0% errors), go-gqlgen (Q2b skipped — known bug) |
| **High error rate** | 6 | fastapi-rest, strawberry, mercurius, express-graphql, graphql-yoga, php-laravel, csharp-dotnet |
| **Won't start** | 14 | graphene, flask-rest, ariadne, asgi-graphql, apollo-server, apollo-orm, express-rest, express-orm, go-graphql-go, spring-boot, spring-boot-orm-naive, micronaut-graphql, play-graphql, ruby-rails, hanami |
| **Not registered** | 2 | postgraphile, graphql-go |

## Phases (Sequential)

| Phase | Title | Scope | Requires |
|-------|-------|-------|----------|
| [1](phase-01-benchmark-harness.md) | Benchmark Harness & Diagnostics | Improve error reporting, add body logging, add Q3/M1 | — |
| [2](phase-02-python-frameworks.md) | Python Frameworks | Fix fastapi-rest, strawberry, graphene, flask-rest, ariadne, asgi-graphql | Phase 1 |
| [3](phase-03-nodejs-frameworks.md) | Node.js/TypeScript Frameworks | Fix apollo-server, apollo-orm, express-rest, express-orm, express-graphql, graphql-yoga, mercurius, postgraphile | Phase 2 |
| [4](phase-04-go-frameworks.md) | Go Frameworks | Fix go-graphql-go, graphql-go, go-gqlgen Q2b bug | Phase 3 |
| [5](phase-05-jvm-frameworks.md) | Java/JVM Frameworks | Fix spring-boot, spring-boot-orm-naive, micronaut-graphql, play-graphql | Phase 4 |
| [6](phase-06-ruby-php-csharp.md) | Ruby, PHP, C# Frameworks | Fix ruby-rails, hanami, php-laravel, webonyx-graphql-php perf, csharp-dotnet | Phase 5 |
| [7](phase-07-validation-reporting.md) | Validation & Reporting | Full benchmark run, auto-categorized results, registry updates, final report | Phase 6 |

## Execution Order

```
Phase 1 (harness)
    │
    ▼
Phase 2 (Python — 6 frameworks)
    │
    ▼
Phase 3 (Node.js — 8 frameworks)
    │
    ▼
Phase 4 (Go — 3 frameworks)
    │
    ▼
Phase 5 (JVM — 4 frameworks)
    │
    ▼
Phase 6 (Ruby/PHP/C# — 5 frameworks)
    │
    ▼
Phase 7 (Validation & Reporting)
```

Each phase must complete (verification gate passes) before the next begins. This ensures:
1. Diagnostic tooling from Phase 1 is available for all subsequent debugging
2. Fixes in earlier phases inform patterns for later phases (e.g., UUID fix in Python reused in Node.js)
3. Each verification gate catches regressions before adding more frameworks
4. Easier to bisect if something breaks

## Success Criteria

- [ ] All 33 frameworks start successfully via `docker compose`
- [ ] All 33 frameworks pass smoke tests (`make smoke-test`)
- [ ] All 33 frameworks pass parity tests (`make parity-test`)
- [ ] All 33 frameworks achieve <1% error rate on Q1, Q2, Q2b in `bench_sequential.py`
- [ ] Q3 (deep nesting) added to sequential benchmark and passes for all GraphQL frameworks
- [ ] M1 (mutation) added to sequential benchmark and passes for all frameworks
- [ ] Benchmark results auto-categorized by type (REST, GraphQL, GraphQL-precomputed)
- [ ] `make status` target shows framework health at a glance

## Principles

1. **Fix, don't rewrite** — Minimal targeted changes to get each framework working
2. **Verify in isolation** — Test each framework individually before full suite
3. **Match existing patterns** — Use working frameworks as reference implementations
4. **Document root causes** — Each fix should note what was wrong and why
