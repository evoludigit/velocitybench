# VelocityBench Blog Posts

Generated educational content about backend best practices, database patterns, and API design.

## Content Overview

| Category | Pattern/Topic | Tutorials | Troubleshooting | Reference | Comparisons |
|----------|---------------|-----------|-----------------|-----------|-------------|
| **Database Patterns** | Trinity Pattern | 3 | 1 | 1 | - |
| **Query Patterns** | N+1 Query Problem | 3 | 1 | 1 | - |
| **Query Patterns** | GraphQL Cascade | 3 | 1 | 1 | - |
| **Architecture** | REST vs GraphQL vs gRPC | - | - | - | 3 |
| **Frameworks** | GraphQL Frameworks | - | - | - | 3 |

**Total: 21 blog posts**

---

## Tutorials

Step-by-step educational content for different skill levels.

### Trinity Pattern
The Trinity Pattern uses three identifier types (pk_*, id UUID, slug) for optimal database design.

| Level | File | Description |
|-------|------|-------------|
| Beginner | [trinity-pattern-tutorial-beginner.md](tutorials/trinity-pattern-tutorial-beginner.md) | Introduction to the pattern with analogies |
| Intermediate | [trinity-pattern-tutorial-intermediate.md](tutorials/trinity-pattern-tutorial-intermediate.md) | Implementation details and ORM integration |
| Advanced | [trinity-pattern-tutorial-advanced.md](tutorials/trinity-pattern-tutorial-advanced.md) | Performance optimization and edge cases |

### N+1 Query Problem
The N+1 problem occurs when an app executes N+1 queries instead of 1-2 optimized queries.

| Level | File | Description |
|-------|------|-------------|
| Beginner | [n-plus-one-tutorial-beginner.md](tutorials/n-plus-one-tutorial-beginner.md) | Understanding the problem with examples |
| Intermediate | [n-plus-one-tutorial-intermediate.md](tutorials/n-plus-one-tutorial-intermediate.md) | Solutions: eager loading, batching |
| Advanced | [n-plus-one-tutorial-advanced.md](tutorials/n-plus-one-tutorial-advanced.md) | DataLoader, denormalization, caching |

### GraphQL Cascade Problem
GraphQL-specific N+1 problem in resolver execution with DataLoader solutions.

| Level | File | Description |
|-------|------|-------------|
| Beginner | [graphql-cascade-tutorial-beginner.md](tutorials/graphql-cascade-tutorial-beginner.md) | Understanding the cascade problem |
| Intermediate | [graphql-cascade-tutorial-intermediate.md](tutorials/graphql-cascade-tutorial-intermediate.md) | DataLoader implementation patterns |
| Advanced | [graphql-cascade-tutorial-advanced.md](tutorials/graphql-cascade-tutorial-advanced.md) | Query complexity and optimization |

---

## Troubleshooting Guides

Practical debugging guides for common issues.

| Pattern | File | Description |
|---------|------|-------------|
| Trinity Pattern | [trinity-pattern-troubleshooting.md](troubleshooting/trinity-pattern-troubleshooting.md) | Debugging identifier-related issues |
| N+1 Query Problem | [n-plus-one-troubleshooting.md](troubleshooting/n-plus-one-troubleshooting.md) | Detecting and fixing N+1 queries |
| GraphQL Cascade | [graphql-cascade-troubleshooting.md](troubleshooting/graphql-cascade-troubleshooting.md) | Debugging GraphQL resolver issues |

---

## Reference Documentation

Quick-reference guides for each pattern.

| Pattern | File | Description |
|---------|------|-------------|
| Trinity Pattern | [trinity-pattern-reference.md](reference/trinity-pattern-reference.md) | Schema, queries, and API reference |
| N+1 Query Problem | [n-plus-one-reference.md](reference/n-plus-one-reference.md) | Query examples and solutions |
| GraphQL Cascade | [graphql-cascade-reference.md](reference/graphql-cascade-reference.md) | DataLoader patterns and framework guides |

---

## Comparison Articles

In-depth comparisons of technologies and frameworks.

### REST vs GraphQL vs gRPC
Comparing the three major API paradigms.

| Level | File | Description |
|-------|------|-------------|
| Beginner | [rest-vs-graphql-vs-grpc-beginner.md](comparisons/rest-vs-graphql-vs-grpc-beginner.md) | Basic concepts and when to use each |
| Intermediate | [rest-vs-graphql-vs-grpc-intermediate.md](comparisons/rest-vs-graphql-vs-grpc-intermediate.md) | Implementation tradeoffs and patterns |
| Advanced | [rest-vs-graphql-vs-grpc-advanced.md](comparisons/rest-vs-graphql-vs-grpc-advanced.md) | Performance, federation, and hybrid approaches |

### GraphQL Frameworks
Comparing popular GraphQL frameworks: Apollo, Strawberry, PostGraphile, Hasura, gqlgen.

| Level | File | Description |
|-------|------|-------------|
| Beginner | [graphql-frameworks-beginner.md](comparisons/graphql-frameworks-beginner.md) | Framework overview and selection criteria |
| Intermediate | [graphql-frameworks-intermediate.md](comparisons/graphql-frameworks-intermediate.md) | Features, performance, and use cases |
| Advanced | [graphql-frameworks-advanced.md](comparisons/graphql-frameworks-advanced.md) | Federation, advanced patterns, and optimization |

---

## Generation

These blog posts were generated using local AI models from the VelocityBench seed data corpus.

### Source Material
- Pattern definitions: `database/seed-data/corpus/patterns/`
- Generator script: `database/seed-data/generator/generate_blog_vllm.py`

### Regenerate Posts
```bash
# Ensure vLLM is running
vllm-switch status

# Generate all posts
python database/seed-data/generator/generate_blog_vllm.py --all

# Generate specific post
python database/seed-data/generator/generate_blog_vllm.py \
  --pattern trinity-pattern \
  --type tutorial \
  --depth beginner

# Generate comparison article
python database/seed-data/generator/generate_blog_vllm.py \
  --pattern rest-vs-graphql-vs-grpc \
  --type comparison \
  --depth intermediate
```

### Available Patterns
- **Standard patterns**: `trinity-pattern`, `n-plus-one`, `graphql-cascade`
- **Comparison patterns**: `rest-vs-graphql-vs-grpc`, `graphql-frameworks`

### Available Options
- `--pattern`: Pattern ID (see above)
- `--type`: `tutorial`, `troubleshooting`, `reference`, `comparison`
- `--depth`: `beginner`, `intermediate`, `advanced`
- `--all`: Generate all posts
- `--stdout`: Output to console instead of file
