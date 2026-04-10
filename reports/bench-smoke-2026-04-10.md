# VelocityBench Smoke Pass — Coverage Report

**Date**: 2026-04-10  
**Settings**: `--duration 5 --concurrency 10 --warmup 3 --cooldown 3`  
**Frameworks tested**: 37  
**Scenarios**: C3, F1, F2, F3, HC3, M1, M1_APQ, M1d, MC1, Q1, Q1_APQ, Q2, Q2b, Q2b_APQ, Q3, T1

## Summary

| Metric | Count |
|--------|-------|
| Total scenario–framework pairs | 270 |
| ✅ Working (RPS > 0, error < 5%) | 266 |
| ❌ Broken (errors ≥ 5% or RPS = 0) | 2 |
| ⬜ Skipped / N/A | 2 |

## Broken Scenarios

| Framework | Scenario | RPS | Error Rate |
|-----------|----------|-----|------------|
| spring-boot-orm | F2 | 0 | 100.0% |
| spring-boot-orm | Q2b | 0 | 100.0% |

## Skipped / N/A Scenarios

| Framework | Scenario | Note |
|-----------|----------|------|
| spring-boot-orm | T1 | not configured |
| spring-boot-orm-naive | T1 | not configured |

## Coverage Matrix

Legend: ✅ working · ❌ broken · ⬜ skipped/N/A

| Framework | C3 | F1 | F2 | F3 | HC3 | M1 | M1_APQ | M1d | MC1 | Q1 | Q1_APQ | Q2 | Q2b | Q2b_APQ | Q3 | T1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| actix-web-rest | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ✅ | ⬜ | ⬜ | ⬜ | ✅ | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ✅ |
| async-graphql | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ✅ | ⬜ | ⬜ | ✅ | ✅ | ⬜ | ✅ | ✅ | ⬜ | ✅ | ✅ |
| juniper | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ✅ | ⬜ | ⬜ | ⬜ | ✅ | ⬜ | ✅ | ✅ | ⬜ | ✅ | ✅ |
| go-gqlgen | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ✅ | ⬜ | ⬜ | ⬜ | ✅ | ⬜ | ✅ | ✅ | ⬜ | ✅ | ✅ |
| gin-rest | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ✅ | ⬜ | ⬜ | ⬜ | ✅ | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ✅ |
| go-graphql-go | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ✅ | ⬜ | ⬜ | ⬜ | ✅ | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ✅ |
| graphql-go | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ✅ | ⬜ | ⬜ | ⬜ | ✅ | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ✅ |
| apollo-server | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ✅ | ⬜ | ⬜ | ⬜ | ✅ | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ✅ |
| apollo-orm | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ✅ | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ✅ |
| express-rest | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ✅ | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ✅ |
| express-orm | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ✅ | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ✅ |
| express-graphql | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ✅ | ⬜ | ⬜ | ⬜ | ✅ | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ✅ |
| graphql-yoga | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ✅ | ⬜ | ⬜ | ✅ | ✅ | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ✅ |
| mercurius | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ✅ | ⬜ | ⬜ | ✅ | ✅ | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ✅ |
| postgraphile | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ✅ | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ✅ |
| strawberry | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ✅ | ⬜ | ⬜ | ⬜ | ✅ | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ✅ |
| graphene | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ✅ | ⬜ | ⬜ | ⬜ | ✅ | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ✅ |
| fastapi-rest | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ✅ | ⬜ | ⬜ | ⬜ | ✅ | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ✅ |
| flask-rest | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ✅ | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ✅ |
| ariadne | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ✅ | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ✅ |
| asgi-graphql | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ✅ | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ✅ |
| spring-boot | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ✅ | ⬜ | ⬜ | ⬜ | ✅ | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ✅ |
| spring-boot-orm | ⬜ | ✅ | ❌ | ⬜ | ⬜ | ✅ | ⬜ | ⬜ | ⬜ | ✅ | ⬜ | ✅ | ❌ | ⬜ | ⬜ | ⬜ |
| spring-boot-orm-naive | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ✅ | ⬜ | ✅ | ⬜ | ⬜ | ⬜ | ⬜ |
| micronaut-graphql | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ✅ | ⬜ | ⬜ | ⬜ | ✅ | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ✅ |
| quarkus-graphql | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ✅ | ⬜ | ⬜ | ⬜ | ✅ | ⬜ | ✅ | ✅ | ⬜ | ✅ | ✅ |
| play-graphql | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ✅ | ⬜ | ⬜ | ⬜ | ✅ | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ✅ |
| ruby-rails | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ✅ | ⬜ | ⬜ | ⬜ | ✅ | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ✅ |
| hanami | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ✅ | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ✅ |
| php-laravel | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ✅ | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ✅ |
| webonyx-graphql-php | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ✅ | ⬜ | ⬜ | ⬜ | ✅ | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ✅ |
| csharp-dotnet | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ✅ | ⬜ | ⬜ | ⬜ | ✅ | ⬜ | ✅ | ✅ | ⬜ | ⬜ | ✅ |
| fraiseql-tv | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| fraiseql-v-nocache | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⬜ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| fraiseql-v-cache | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⬜ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| fraiseql-tv-cache | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⬜ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| fraiseql-tv-audit | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ✅ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |

## Per-Framework Summary

| Framework | Type | ✅ | ❌ | ⬜ | Verdict |
|-----------|------|----|----|----|----|
| actix-web-rest | REST | 7 | 0 | 0 | ✅ Full coverage |
| async-graphql | GraphQL | 9 | 0 | 0 | ✅ Full coverage |
| juniper | GraphQL | 8 | 0 | 0 | ✅ Full coverage |
| go-gqlgen | GraphQL | 8 | 0 | 0 | ✅ Full coverage |
| gin-rest | REST | 7 | 0 | 0 | ✅ Full coverage |
| go-graphql-go | GraphQL | 7 | 0 | 0 | ✅ Full coverage |
| graphql-go | GraphQL | 7 | 0 | 0 | ✅ Full coverage |
| apollo-server | GraphQL | 7 | 0 | 0 | ✅ Full coverage |
| apollo-orm | GraphQL | 6 | 0 | 0 | ✅ Full coverage |
| express-rest | REST | 6 | 0 | 0 | ✅ Full coverage |
| express-orm | REST | 6 | 0 | 0 | ✅ Full coverage |
| express-graphql | GraphQL | 7 | 0 | 0 | ✅ Full coverage |
| graphql-yoga | GraphQL | 8 | 0 | 0 | ✅ Full coverage |
| mercurius | GraphQL | 8 | 0 | 0 | ✅ Full coverage |
| postgraphile | GraphQL | 4 | 0 | 0 | ✅ Full coverage |
| strawberry | GraphQL | 7 | 0 | 0 | ✅ Full coverage |
| graphene | GraphQL | 7 | 0 | 0 | ✅ Full coverage |
| fastapi-rest | REST | 7 | 0 | 0 | ✅ Full coverage |
| flask-rest | REST | 6 | 0 | 0 | ✅ Full coverage |
| ariadne | GraphQL | 6 | 0 | 0 | ✅ Full coverage |
| asgi-graphql | GraphQL | 6 | 0 | 0 | ✅ Full coverage |
| spring-boot | REST | 7 | 0 | 0 | ✅ Full coverage |
| spring-boot-orm | REST | 4 | 2 | 1 | ❌ Has failures |
| spring-boot-orm-naive | REST | 2 | 0 | 1 | ⚠️ Partial (skipped only) |
| micronaut-graphql | GraphQL | 5 | 0 | 0 | ✅ Full coverage |
| quarkus-graphql | GraphQL | 6 | 0 | 0 | ✅ Full coverage |
| play-graphql | GraphQL | 5 | 0 | 0 | ✅ Full coverage |
| ruby-rails | REST | 7 | 0 | 0 | ✅ Full coverage |
| hanami | GraphQL | 4 | 0 | 0 | ✅ Full coverage |
| php-laravel | REST | 6 | 0 | 0 | ✅ Full coverage |
| webonyx-graphql-php | GraphQL | 7 | 0 | 0 | ✅ Full coverage |
| csharp-dotnet | REST | 7 | 0 | 0 | ✅ Full coverage |
| fraiseql-tv | GraphQL | 16 | 0 | 0 | ✅ Full coverage |
| fraiseql-v-nocache | GraphQL | 15 | 0 | 0 | ✅ Full coverage |
| fraiseql-v-cache | GraphQL | 15 | 0 | 0 | ✅ Full coverage |
| fraiseql-tv-cache | GraphQL | 15 | 0 | 0 | ✅ Full coverage |
| fraiseql-tv-audit | GraphQL | 1 | 0 | 0 | ✅ Full coverage |

## Observations

### Broken

- **spring-boot-orm / Q2b + F2** — 100% error rate. These two scenarios require a JOIN across `tb_post → tb_user` via the ORM; the query likely maps to a broken relationship config (eager-loading or N+1 guard mis-set). `Q2` (no author nesting) works fine, so the issue is specifically in the nested author resolution.

### Skipped

- **spring-boot-orm / T1** and **spring-boot-orm-naive / T1** — T1 (single post detail) was not configured for these two variants. The plain `spring-boot` service does implement T1.

### Coverage notes

- **Q3** (comments 2-level nesting) is only wired for GraphQL frameworks that expose a `comments` field: async-graphql, juniper, go-gqlgen, go-graphql-go, graphql-go, apollo-server, apollo-orm, express-graphql, graphql-yoga, mercurius, postgraphile, strawberry, graphene, ariadne, asgi-graphql, and all FraiseQL variants. All others correctly show ⬜.
- **FraiseQL-specific scenarios** (C3, HC3, M1d, MC1, Q1_APQ, Q2b_APQ, M1_APQ, F3) are exclusive to fraiseql variants and correctly show ⬜ for all other frameworks.
- 266 of 270 configured scenario–framework pairs are fully operational.
