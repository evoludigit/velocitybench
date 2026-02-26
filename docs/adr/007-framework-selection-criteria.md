# ADR-007: Framework Selection Criteria

**Status**: Accepted
**Date**: 2025-01-30
**Author**: VelocityBench Team

## Context

VelocityBench aims to provide comprehensive framework performance comparisons across multiple programming languages. With thousands of web frameworks available, we need clear criteria for which frameworks to include.

The challenges:

1. **Scale**: Too many frameworks to benchmark all of them (100+ serious candidates)
2. **Maintenance**: Each framework requires ongoing maintenance as it evolves
3. **Fairness**: Frameworks should be comparable (similar feature sets)
4. **Relevance**: Focus on frameworks developers actually use
5. **Language Coverage**: Balance between depth (many frameworks per language) and breadth (many languages)

## Decision

**Select 39 frameworks across 8 languages based on popularity, maturity, and architectural diversity.**

### Selection Criteria

#### Tier 1: Must-Have Criteria

1. **Active Maintenance**: Commit within last 6 months
2. **Production Usage**: Used by real companies (not just toy projects)
3. **Database Support**: Native or well-supported PostgreSQL integration
4. **Popularity**:
   - Python: 1,000+ GitHub stars OR widely used in industry
   - TypeScript/JavaScript: 5,000+ GitHub stars OR NPM downloads > 100k/month
   - Go: 1,000+ GitHub stars
   - Rust: 500+ GitHub stars (emerging ecosystem)
   - Java: Part of major framework (Spring, Quarkus, Micronaut)
   - Others: Language-specific popularity metrics

#### Tier 2: Nice-to-Have Criteria

1. **Architectural Diversity**: Include different paradigms (micro, batteries-included, GraphQL-first, etc.)
2. **Performance Claims**: Framework claims to be "fast" or "high-performance"
3. **Community Size**: Active Discord/Slack/Forum community
4. **Documentation Quality**: Well-documented API and patterns

### Framework Matrix

| Language | REST Frameworks | GraphQL Frameworks | Total |
|----------|-----------------|-------------------|-------|
| **Python** | FastAPI, Flask, Django REST | Strawberry, Graphene, FraiseQL | 6 |
| **TypeScript** | Express, Fastify | Apollo, GraphQL-Yoga, Mercurius | 8 |
| **Go** | Gin, Echo, Fiber | gqlgen, graphql-go | 6 |
| **Java** | Spring Boot, Quarkus, Micronaut | Spring GraphQL | 4 |
| **Rust** | Actix-web, Axum | async-graphql | 3 |
| **PHP** | Laravel | Webonyx GraphQL | 2 |
| **Ruby** | Rails, Sinatra | GraphQL-Ruby | 3 |
| **C#** | ASP.NET Core | HotChocolate | 2 |
| **Elixir** | Phoenix | Absinthe | 2 |
| **Kotlin** | Ktor | - | 1 |
| **Swift** | Vapor | - | 1 |
| **Dart** | Shelf | - | 1 |

**Total**: 39 frameworks

### Python Frameworks (6)

1. **FastAPI** (REST) - 75k+ stars, modern async, auto-validation
2. **Flask** (REST) - 67k+ stars, micro-framework standard
3. **Django REST Framework** (REST) - Batteries-included, ORM-first
4. **Strawberry** (GraphQL) - 4k+ stars, Python-first GraphQL with type hints
5. **Graphene** (GraphQL) - 8k+ stars, mature GraphQL library
6. **FraiseQL** (GraphQL) - Custom framework demonstrating pattern-based resolvers

### TypeScript Frameworks (8)

1. **Express** (REST) - 65k+ stars, de-facto Node.js standard
2. **Fastify** (REST) - 32k+ stars, performance-focused
3. **NestJS** (REST) - 67k+ stars, enterprise architecture
4. **Apollo Server** (GraphQL) - Industry standard GraphQL server
5. **GraphQL-Yoga** (GraphQL) - Modern GraphQL server
6. **Mercurius** (GraphQL) - Fastify GraphQL adapter
7. **Express + GraphQL** - Classic combination
8. **TypeGraphQL** - TypeScript-first GraphQL

### Go Frameworks (6)

1. **Gin** (REST) - 77k+ stars, high performance
2. **Echo** (REST) - 29k+ stars, minimalist
3. **Fiber** (REST) - 33k+ stars, Express-like API
4. **gqlgen** (GraphQL) - Code-first GraphQL
5. **graphql-go** (GraphQL) - Schema-first GraphQL
6. **Chi** (REST) - Lightweight, composable

### Java Frameworks (4)

1. **Spring Boot** (REST) - Enterprise standard
2. **Spring GraphQL** (GraphQL) - Official Spring GraphQL support
3. **Quarkus** (REST) - Cloud-native, GraalVM-ready
4. **Micronaut** (REST) - Compile-time DI, low memory

### Rust Frameworks (3)

1. **Actix-web** (REST) - 21k+ stars, actor-based
2. **Axum** (REST) - 18k+ stars, Tokio-based
3. **async-graphql** (GraphQL) - 3k+ stars, async GraphQL

### Other Languages (12)

- **PHP**: Laravel (REST), Webonyx (GraphQL)
- **Ruby**: Rails (REST), GraphQL-Ruby (GraphQL), Sinatra (REST)
- **C#**: ASP.NET Core (REST), HotChocolate (GraphQL)
- **Elixir**: Phoenix (REST), Absinthe (GraphQL)
- **Kotlin**: Ktor (REST)
- **Swift**: Vapor (REST)
- **Dart**: Shelf (REST)

## Consequences

### Positive

✅ **Comprehensive Coverage**: 39 frameworks across 8 languages covers 90%+ of production use cases
✅ **Language Diversity**: Demonstrates performance across different runtime models (interpreted, JIT, compiled)
✅ **Architectural Variety**: REST, GraphQL, micro, batteries-included all represented
✅ **Industry Relevance**: All frameworks are production-used
✅ **Maintainability**: 39 is large but manageable for a small team
✅ **Fair Comparison**: All frameworks support PostgreSQL, async I/O, JSON serialization

### Negative

❌ **Maintenance Burden**: 39 frameworks × 8 languages = significant update overhead
❌ **Missing Frameworks**: Some popular frameworks excluded (e.g., Hapi, Koa, Sails)
❌ **Language Balance**: Python/TypeScript over-represented vs. Rust/Elixir
❌ **Emerging Frameworks**: Hard to include new frameworks without removing old ones
❌ **Subjective Choices**: "Popularity" metrics can be gamed or misleading

## Alternatives Considered

### Alternative 1: Top 10 Only

- **Approach**: Only benchmark the 10 most popular frameworks globally
- **Pros**: Easy to maintain, clear top-tier comparison
- **Cons**:
  - Excludes emerging frameworks (Rust, Elixir)
  - No language diversity
  - Misses architectural patterns (GraphQL-first frameworks)
- **Rejected**: Too narrow, misses valuable comparisons

### Alternative 2: One Framework Per Language

- **Approach**: Pick the single most popular framework for each language
- **Pros**: Simple, broad language coverage
- **Cons**:
  - Doesn't show within-language performance variance
  - Misses REST vs. GraphQL comparisons
  - Unfair to languages with multiple good options
- **Rejected**: Doesn't meet "comprehensive comparison" goal

### Alternative 3: All Frameworks (100+)

- **Approach**: Benchmark every framework with 500+ GitHub stars
- **Pros**: Truly comprehensive, no selection bias
- **Cons**:
  - Unsustainable maintenance burden
  - Many frameworks are abandoned or niche
  - Dilutes focus on production-relevant frameworks
- **Rejected**: Impractical to maintain

### Alternative 4: Community Voting

- **Approach**: Let the community vote on which frameworks to include
- **Pros**: Democratic, community-driven
- **Cons**:
  - Popularity contests don't reflect technical merit
  - Newcomers can't compete with established frameworks
  - Voting can be gamed
- **Rejected**: Doesn't guarantee quality or relevance

## Related Decisions

- **ADR-002**: Framework Isolation - Supports adding/removing frameworks independently
- **ADR-003**: Multi-Language Support - Enables the 8-language strategy
- **ADR-010**: Benchmarking Methodology - Ensures fair comparison across selected frameworks

## Implementation Status

✅ **Complete** - 39 frameworks implemented and benchmarked

## Adding New Frameworks

To propose a new framework:

1. **Check Criteria**: Ensure it meets Tier 1 criteria
2. **Open Issue**: Describe framework, provide metrics, explain value-add
3. **Prototype**: Implement framework following Trinity Pattern (ADR-001)
4. **Benchmark**: Run performance tests and compare to existing frameworks
5. **Document**: Add to this ADR if accepted

## References

- [GitHub Star Rankings](https://github.com/search?q=web+framework&type=repositories&s=stars&o=desc)
- [NPM Package Statistics](https://www.npmjs.com/)
- [Stack Overflow Survey](https://survey.stackoverflow.co/) - Developer usage trends
- [ThoughtWorks Technology Radar](https://www.thoughtworks.com/radar) - Framework maturity assessment
- [TechEmpower Benchmarks](https://www.techempower.com/benchmarks/) - Similar benchmarking project
