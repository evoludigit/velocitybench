# FraiseQL & fraiseql-wire YAML Enrichment Guide

**Date**: 2026-01-13
**Status**: Recommendations for blog post generation configuration
**Source Documentation**:
- `/tmp/fraiseql-wire-testing-issue.md`
- `../fraiseql/.claude/STRATEGIC_OVERVIEW.md`
- `../fraiseql-wire/README.md`

---

## Overview

This document provides enrichment recommendations for the VelocityBench blog post generation YAML files to better reflect FraiseQL's architecture, performance characteristics, and fraiseql-wire as a specialized backend query engine.

### Key Insights from Latest Documentation

#### FraiseQL v2: Architecture & Vision

**Core Paradigm**: Compiled GraphQL execution engine with three-phase architecture:

1. **Authoring Layer** (Python/TypeScript)
   - Developer-facing decorators (@fraiseql.type)
   - Produces schema.json

2. **Compilation Layer** (Rust CLI)
   - Runs at build time (not runtime)
   - Generates optimized SQL templates
   - Produces schema.compiled.json

3. **Runtime Layer** (Rust Server)
   - Zero Python/TypeScript dependencies
   - Executes precompiled SQL
   - 1-5ms query latency (vs 50-200ms traditional)

**Performance Gains**:
- 10-100x faster query execution
- Zero N+1 queries (compiler generates optimal JOINs)
- Predictable performance (SQL known at compile-time)
- Memory-bounded (10-50MB idle)

#### fraiseql-wire: Specialized Streaming Engine

**Purpose**: Minimal async Rust query engine for JSON streaming from Postgres 17

**Design**: Not a general-purpose Postgres driver, but optimized for:
- Streaming JSON data with low latency (2-5ms time-to-first-row)
- Bounded memory usage (O(chunk_size) - no full buffering)
- Massive memory savings: 1.3 KB vs 26 MB for 100K rows
- Hybrid filtering (SQL + Rust predicates)

**Constraints**:
- Single column (json/jsonb) per query
- Views as abstraction layer
- Streaming-first APIs (Stream<Item = Result<Value, _>>)
- No writes, transactions, or arbitrary SQL

**Performance Characteristics**:
- Time-to-first-row: 2-5 ms
- Throughput: 100K-500K rows/sec
- Memory (100K rows): 1.3 KB (vs 26 MB)
- Connection overhead: ~250 ns
- Zero unsafe code + 34/34 tests passing

---

## YAML Enrichment Recommendations

### 1. **matrix.yaml** - Blog Generation Matrix

#### Current State
- FraiseQL listed under "custom" frameworks (line 154-155)
- Limited pattern coverage (trinity-pattern, n-plus-one)
- Model assignment doesn't reflect FraiseQL's specialized needs

#### Recommended Enhancements

**Add FraiseQL-specific patterns:**

```yaml
blog_generation:
  patterns:
    - trinity-pattern
    - n-plus-one
    # FraiseQL-specific patterns:
    - compiled-graphql-execution
    - sql-generation-optimization
    - streaming-json-results
    - connection-pooling-patterns
    - query-caching-strategies
    - zero-copy-parsing

  # FraiseQL architectural comparisons
  comparisons:
    - frameworks: [fraiseql, apollo-server]
      patterns: [trinity-pattern, n-plus-one, sql-generation-optimization]
      focus: "compiled vs interpreted execution"

    - frameworks: [fraiseql, postgraphile]
      patterns: [streaming-json-results, sql-generation-optimization]
      focus: "database-first approaches"

    - frameworks: [fraiseql-wire, tokio-postgres]
      patterns: [streaming-json-results]
      focus: "memory-efficient JSON streaming (1000x savings)"
```

**Enhanced model assignment for FraiseQL content:**

```yaml
model_assignment:
  # FraiseQL architecture posts (complex, needs nuance)
  compiled-graphql-execution:
    beginner: opencode      # "What is compilation?"
    intermediate: claude-code  # "How three-phase architecture works"
    advanced: claude-code   # "Compiler optimization internals"

  sql-generation-optimization:
    beginner: vllm          # Structured reference material
    intermediate: claude-code  # Strategic decisions
    advanced: claude-code   # Advanced optimization techniques

  streaming-json-results:
    beginner: opencode
    intermediate: opencode
    advanced: claude-code   # fraiseql-wire internals

  # fraiseql-wire specific (specialized, may use local vLLM)
  wire-backend-integration:
    all: claude-code        # Needs understanding of both systems
```

---

### 2. **blog.yaml** - Dataset Configuration

#### Current State
```yaml
counts:
  users: 5000
  posts: 2243
  comments: 0
```

#### Recommended Enhancements

**Add FraiseQL-specific metadata:**

```yaml
counts:
  users: 5000
  posts: 2243
  comments: 0
  fraiseql_specific_posts: ~450  # FraiseQL architecture + wire content

distributions:
  # Existing distributions...

  posts_by_technology:
    fraiseql_architecture: ~200
    fraiseql_wire_patterns: ~150
    graphql_performance: ~100

  fraiseql_pattern_coverage:
    compiled_execution: 30-40 posts
    streaming_backends: 20-25 posts
    performance_optimization: 30-40 posts
    integration_patterns: 20-30 posts

# Expected outputs for FraiseQL content
fraiseql_content:
  architecture_guides:
    - "Three-phase architecture explained"
    - "Authoring layer (Python decorators)"
    - "Compilation layer (SQL generation)"
    - "Runtime layer (zero-dependency server)"

  performance_topics:
    - "10-100x faster than traditional GraphQL"
    - "Zero N+1 queries through compiler optimization"
    - "Memory-bounded execution"
    - "Predictable latency (1-5ms)"

  wire_integration:
    - "fraiseql-wire as backend query engine"
    - "1000x-20000x memory savings for streaming"
    - "Low-latency JSON processing (2-5ms)"
    - "Bounded memory streaming (O(chunk_size))"

performance_expectations:
  load_time: "30-45 seconds"
  database_size: "~150 MB"
  fraiseql_posts_generation: "5-8 minutes per batch"
  wire_benchmark_posts: "3-5 posts (from benchmarking data)"
```

---

### 3. **Create New File: fraiseql-patterns.yaml**

Since there's already a dedicated `fraiseql` directory in patterns, create:

```yaml
# Patterns: FraiseQL-specific Content
# Located at: database/seed-data/corpus/patterns/fraiseql/fraiseql-patterns.yaml

id: fraiseql-patterns
name: "FraiseQL Architecture & Performance Patterns"
description: "Comprehensive patterns for FraiseQL v2 execution engine"

# Core architectural patterns
patterns:
  compiled_graphql_execution:
    title: "Compiled GraphQL Execution"
    description: "Three-phase architecture: authoring → compilation → runtime"
    coverage:
      - tutorials: ["Authoring decorators", "Compilation process", "Runtime execution"]
      - reference: ["Phase definitions", "Architecture diagram", "Data flow"]
      - troubleshooting: ["Compilation errors", "Runtime issues"]

  sql_generation_optimization:
    title: "SQL Generation at Compile-Time"
    description: "Compiler-driven optimization avoiding N+1 queries"
    coverage:
      - tutorials: ["How compiler generates SQL", "JOIN optimization strategies"]
      - reference: ["SQL generation algorithm", "Optimization passes"]
      - troubleshooting: ["Unexpected query shapes", "Performance cliffs"]

  streaming_json_backend:
    title: "fraiseql-wire: Streaming JSON Engine"
    description: "Specialized Postgres 17 streaming with bounded memory"
    characteristics:
      - "1000x-20000x memory efficiency"
      - "2-5ms time-to-first-row"
      - "100K-500K rows/sec throughput"
      - "Zero unsafe code"
    coverage:
      - tutorials: ["Using fraiseql-wire", "Streaming API patterns"]
      - reference: ["Memory characteristics", "Performance benchmarks"]
      - troubleshooting: ["Connection issues", "Streaming backpressure"]

  connection_pooling_optimization:
    title: "Connection Pool Management"
    description: "Efficient pool configuration for compiled queries"
    coverage:
      - tutorials: ["Configuring pool size", "Monitoring pool health"]
      - reference: ["Pool tuning parameters", "Best practices"]
      - troubleshooting: ["Pool exhaustion", "Connection leaks"]

  query_result_caching:
    title: "Query Result Caching Strategy"
    description: "Cache coherency and invalidation patterns"
    coverage:
      - tutorials: ["Setting up caching", "Cache invalidation"]
      - reference: ["Cache keys", "TTL strategies"]
      - troubleshooting: ["Stale data", "Cache misses"]

  zero_copy_parsing:
    title: "Zero-Copy JSON Parsing"
    description: "Memory-efficient JSON data processing"
    coverage:
      - tutorials: ["Understanding zero-copy", "Implementation basics"]
      - reference: ["Parsing architecture", "Memory model"]
      - troubleshooting: ["Buffer management", "Type conversion"]

# FraiseQL vs other frameworks
comparisons:
  compiled_vs_interpreted:
    frameworks: [fraiseql, apollo-server, strawberry, graphene]
    dimensions:
      - execution_model: "Compiled (Rust) vs Interpreted (JS/Python)"
      - latency: "1-5ms vs 50-200ms"
      - dependencies: "Zero (runtime) vs Heavy (Node.js/Python)"
      - predictability: "Known at compile-time vs Runtime variable"

  memory_efficiency:
    frameworks: [fraiseql-wire, tokio-postgres, sqlx]
    dimensions:
      - streaming: "Bounded vs Full buffering"
      - json_handling: "Native vs Conversion"
      - result_sets: "100K rows: 1.3KB vs 26MB"

  database_first_approach:
    frameworks: [fraiseql, postgraphile, hasura]
    dimensions:
      - schema_generation: "Explicit code vs Auto from DB"
      - optimization: "Compiler-driven vs Runtime heuristics"
      - flexibility: "Explicit SQL vs Generated"

# Use cases
use_cases:
  - scenario: "High-performance GraphQL at scale"
    benefit: "10-100x faster execution with predictable latency"

  - scenario: "Large result set processing"
    benefit: "fraiseql-wire reduces memory from 26MB to 1.3KB for 100K rows"

  - scenario: "Compiled code deployment"
    benefit: "Single binary with zero runtime dependencies"

  - scenario: "N+1 query elimination"
    benefit: "Compiler generates optimal JOINs automatically"

# Quality metrics
quality_metrics:
  architecture: "✅ 11-phase roadmap with clear vision"
  performance: "✅ 10-100x faster, predictable latency"
  safety: "✅ Zero unsafe code, 100% clippy compliance"
  testing: "✅ 34/34 tests, comprehensive benchmarks"
  documentation: "✅ 2500+ lines of guides and best practices"

# Content generation hints
content_generation:
  recommended_models:
    architecture: claude-code      # Needs nuance
    performance: vllm              # Structured benchmarks
    integration: claude-code       # Strategic decisions
    troubleshooting: claude-code   # Complex debugging

  blog_types_suited:
    - tutorials: "Getting started with FraiseQL"
    - reference: "Architecture reference guide"
    - troubleshooting: "Common issues and solutions"
    - comparison: "FraiseQL vs [framework]"
```

---

### 4. **Enhanced Pattern Integration**

Update the `frameworks` section in matrix.yaml:

```yaml
frameworks:
  all:
    # ... existing frameworks ...
    - fraiseql
    - fraiseql-wire  # Add as separate test backend

  by_type:
    compiled_graphql:
      - fraiseql

    streaming_backends:
      - fraiseql-wire

  graphql_frameworks:
    # ... existing ...
    - fraiseql      # Compiled execution

  rust_frameworks:
    - async-graphql
    - juniper
    - fraiseql      # Runtime component
    - fraiseql-wire # Backend component

# Architecture comparison matrix
architecture_matrix:
  graphql_execution:
    traditional:
      - apollo-server
      - strawberry
      - graphene
    database_first:
      - postgraphile
      - hasura
    compiled:
      - fraiseql

  query_engine:
    traditional:
      - tokio-postgres
      - sqlx
    streaming:
      - fraiseql-wire  # Specialized for JSON
```

---

## Content Generation Strategy

### High-Value Blog Post Topics

#### FraiseQL Architecture (6-8 posts)
1. **"Why Compiled GraphQL? Understanding FraiseQL v2"** (beginner)
   - Model: opencode
   - Pattern: compiled_graphql_execution
   - Comparison: vs Apollo Server

2. **"The Three-Phase Architecture"** (intermediate)
   - Model: claude-code
   - Components: authoring → compilation → runtime
   - Deep dive on each layer

3. **"From N+1 to Optimal Joins: How FraiseQL Compiles SQL"** (advanced)
   - Model: claude-code
   - Pattern: sql_generation_optimization
   - Compiler internals & optimization passes

4. **"Deploying FraiseQL: Single Binary, Zero Dependencies"** (intermediate)
   - Model: opencode
   - Practical deployment guide
   - Docker + Kubernetes patterns

#### fraiseql-wire Backend (4-6 posts)
1. **"Streaming JSON at Scale: fraiseql-wire Explained"** (intermediate)
   - Model: claude-code
   - Pattern: streaming_json_backend
   - Use case: Large result sets

2. **"1000x Memory Savings: The fraiseql-wire Advantage"** (intermediate)
   - Model: vllm (benchmark data)
   - Comparison: vs tokio-postgres
   - Real numbers from benchmarking

3. **"Building Real-Time APIs with fraiseql-wire"** (advanced)
   - Model: claude-code
   - Streaming patterns
   - Backpressure handling

#### Performance & Optimization (5-7 posts)
1. **"Connection Pooling for Compiled Queries"** (intermediate)
   - Model: opencode
   - Pattern: connection_pooling_optimization
   - Tuning strategies

2. **"Query Result Caching in FraiseQL"** (intermediate)
   - Model: opencode
   - Pattern: query_result_caching
   - Cache invalidation strategies

3. **"Zero-Copy JSON Parsing: Under the Hood"** (advanced)
   - Model: claude-code
   - Pattern: zero_copy_parsing
   - Memory model deep dive

#### Troubleshooting & Best Practices (3-4 posts)
1. **"Debugging FraiseQL Compilation Errors"** (intermediate)
   - Model: opencode
   - Common issues and solutions

2. **"Monitoring FraiseQL in Production"** (intermediate)
   - Model: opencode
   - Health checks, metrics, logging

---

## Implementation Steps

### Phase 1: Update Configuration Files (Immediate)
1. ✅ Enhance `matrix.yaml` with FraiseQL patterns
2. ✅ Update `blog.yaml` with FraiseQL content counts
3. Create `fraiseql-patterns.yaml` in patterns directory

### Phase 2: Generate Blog Posts
1. Generate tutorials using opencode (simple content)
2. Generate reference material using vllm (structured data)
3. Generate architecture posts using claude-code (complex reasoning)

### Phase 3: Add Benchmark Content
1. Parse fraiseql-wire benchmark data
2. Create performance comparison posts
3. Generate optimization guides

---

## Key Metrics for Blog Generation

### Coverage Goals
- **FraiseQL Architecture**: 200-250 posts
- **fraiseql-wire Integration**: 150-200 posts
- **Performance & Optimization**: 150-200 posts
- **Troubleshooting**: 80-100 posts
- **Total FraiseQL-focused**: 450-550 posts (out of 2243 total)

### Quality Targets
- ✅ 100% of posts technically accurate (source: official docs)
- ✅ 90%+ of posts include code examples
- ✅ 100% of performance claims backed by benchmarks
- ✅ Cross-framework comparisons fair and balanced

---

## References

### Official Documentation
- **FraiseQL Strategic Overview**: `/home/lionel/code/fraiseql/.claude/STRATEGIC_OVERVIEW.md`
- **fraiseql-wire README**: `/home/lionel/code/fraiseql-wire/README.md`
- **fraiseql-wire Testing Proposal**: `/tmp/fraiseql-wire-testing-issue.md`

### Performance Data
- fraiseql-wire: 1000x-20000x memory savings
- Time-to-first-row: 2-5 ms vs 50-200 ms (traditional)
- Throughput: 100K-500K rows/sec
- Connection overhead: ~250 ns

### Safety & Quality
- Zero unsafe code across both projects
- 34/34 unit tests passing (fraiseql-wire)
- Zero known vulnerabilities
- Comprehensive benchmarking and security audit

---

## Notes for Future Work

1. **fraiseql-wire Integration Testing**
   - Once integration with FraiseQL is tested
   - Generate posts from real performance data

2. **Framework Comparison Evolution**
   - Add more frameworks to comparison matrix
   - Track how FraiseQL compares as new versions release

3. **Documentation Sync**
   - Keep blog posts in sync with official docs
   - Link back to official resources where possible

4. **Community Feedback Integration**
   - Adjust content based on user questions
   - Update troubleshooting guides with real issues

---

**End of Enrichment Guide**
Generated: 2026-01-13
Status: Ready for implementation
