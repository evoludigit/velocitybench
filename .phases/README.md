# VelocityBench FraiseQL Integration - Revised Phase Plan

## Overview

Comprehensive benchmarking suite integrating FraiseQL v2 to measure GraphQL performance across Rust runtime, framework overhead, and language implementations.

**Start Date:** February 1, 2026
**Status:** Planning → Phase 1
**Approach:** Hybrid (performance measurement + blueprint implementations)

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│         FraiseQL Rust Server (1 instance)           │
│  - Loads schema.compiled.json                       │
│  - Executes GraphQL queries deterministically       │
│  - Serves HTTP endpoint (:8000/graphql)             │
│  - Connects to PostgreSQL database                  │
└─────────────────────────────────────────────────────┘
                        ▲
                        │ HTTP
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
   ┌─────────┐   ┌─────────┐   ┌─────────┐
   │ Python  │   │TypeScript│  │Go/Java/ │
   │FastAPI  │   │Express   │  │PHP      │
   │(proxy)  │   │(proxy)   │  │(proxy)  │
   └────┬────┘   └────┬────┘  └────┬────┘
        │             │            │
        └─────────────┼────────────┘
                      │
        ┌─────────────▼─────────────┐
        │ Benchmark Suite           │
        │ - Pure FraiseQL baseline   │
        │ - Framework overhead       │
        │ - Parity validation        │
        └───────────────────────────┘
```

---

## Three Pillars

### Pillar 1: Pure FraiseQL Performance
**Goal**: Measure Rust runtime performance without framework overhead

- Direct HTTP benchmarks against fraiseql-server
- No framework intermediaries
- Metrics: latency, throughput, p99, memory
- Baseline for framework overhead calculation

### Pillar 2: Language Framework Blueprints
**Goal**: Show how to integrate FraiseQL in each language idiomatically

- 5 framework implementations (1 per language)
- Initial MVP: simple HTTP proxy to fraiseql-server
- Features can be added incrementally (auth, caching, observability)
- Demonstrates best practices per language

### Pillar 3: Schema Authoring Equivalence
**Goal**: Validate that all language generators produce identical schemas

- Define schema in Python, TypeScript, Go, Java, PHP
- All compile to identical schema.json
- Proof that generators are truly equivalent
- Foundation for multi-language support

---

## Phase Roadmap

| Phase | Title | Scope | Goal |
|-------|-------|-------|------|
| **1** | Foundation & Schema | Define schema in all 5 languages, compile, validate | Schema equivalence proof |
| **2** | FraiseQL Server & Baseline | Deploy fraiseql-server, establish performance baseline | Pure FraiseQL metrics |
| **3** | Framework Blueprints | Build 1 proxy framework per language | Language implementations |
| **4** | Benchmark Suite | Measure FraiseQL vs framework overhead | Performance analysis |
| **5** | Feature Enhancements | Add advanced features to frameworks progressively | Blueprint completeness |
| **6** | Cross-Language Validation | Verify all frameworks behave identically | Parity testing |
| **7** | Documentation & Reports | Complete guides, performance reports | Knowledge transfer |
| **8** | Finalize | Clean artifacts, production-ready | Publish results |

---

## Key Differences from Previous Plan

✅ **Correct**: Single fraiseql-server (Rust, no FFI)
✅ **Correct**: Frameworks are HTTP proxies, not embedded runtimes
✅ **Correct**: Language generators for SCHEMA AUTHORING only
✅ **Correct**: Performance comparison includes framework overhead, not just query execution
✅ **Focused**: 5 framework implementations instead of 15
✅ **Measurable**: Clear separation between FraiseQL performance and framework overhead

---

## Success Criteria

### Overall
- [ ] FraiseQL performance established as baseline
- [ ] Framework overhead quantified per language
- [ ] Schema authoring in all 5 languages validated
- [ ] Best-practice blueprint per language
- [ ] Zero development artifacts in final code

### Per Framework (Python, TypeScript, Go, Java, PHP)
- [ ] HTTP proxy to fraiseql-server working
- [ ] Handles all query types (queries, mutations, subscriptions)
- [ ] Proper error handling and logging
- [ ] Performance metrics collected
- [ ] Language idioms followed

### Measurement
- [ ] Pure FraiseQL: < 50ms p99 for simple queries
- [ ] Framework overhead: < 10ms per language (goal)
- [ ] Throughput: ≥ 1000 req/s per language
- [ ] Scalability tested up to 100 concurrent connections

---

## Deliverables (Final)

```
velocitybench/
├── fraiseql-schema/
│   ├── schema.fraiseql.py          # Python
│   ├── schema.fraiseql.ts          # TypeScript
│   ├── schema.fraiseql.go          # Go
│   ├── schema.fraiseql.java        # Java
│   ├── schema.fraiseql.php         # PHP
│   ├── schema.json                 # Intermediate (exported)
│   └── schema.compiled.json        # Runtime (compiled)
│
├── frameworks/
│   ├── fraiseql-python/fastapi/    # Python blueprint
│   ├── fraiseql-typescript/express/# TypeScript blueprint
│   ├── fraiseql-go/gin/            # Go blueprint
│   ├── fraiseql-java/spring-boot/  # Java blueprint
│   └── fraiseql-php/laravel/       # PHP blueprint
│
├── benchmarks/
│   ├── fraiseql-direct/            # Pure FraiseQL baseline
│   ├── framework-overhead/         # Per-framework overhead
│   └── reports/
│       ├── performance.md
│       ├── schema-equivalence.md
│       └── framework-comparison.md
│
└── docs/
    ├── ARCHITECTURE.md
    ├── GETTING_STARTED.md
    ├── DEPLOYMENT.md
    ├── PERFORMANCE.md
    └── FRAMEWORK_GUIDES.md
```

---

## Timeline

| Phase | Estimated Effort | Parallel |
|-------|-----------------|----------|
| 1 | Schema definition | Sequential |
| 2 | FraiseQL deployment | Sequential |
| 3 | Framework implementations | **PARALLEL (5 languages)** |
| 4 | Benchmark suite | Sequential |
| 5 | Feature enhancements | **PARALLEL (5 languages)** |
| 6 | Validation | Sequential |
| 7 | Documentation | Parallel |
| 8 | Finalization | Sequential |

Phases 3 and 5 can be executed in parallel for each language, significantly reducing total timeline.

---

## Next Steps

1. **Review & Approve**: Confirm this approach matches goals
2. **Phase 1 Kickoff**: Schema definition and compilation
3. **Phase 2**: FraiseQL server deployment and baseline benchmarks
4. **Phases 3-5**: Parallel language implementation and benchmarking
5. **Phase 6-8**: Validation, documentation, finalization

---

## Key Success Factors

✅ **Clear Performance Isolation**: Separate FraiseQL performance from framework overhead
✅ **Language Blueprints**: Show idiomatic integration in each language
✅ **Schema Equivalence**: Prove language generators work identically
✅ **Measurable Goals**: Specific latency, throughput, and scalability targets
✅ **Maintainable Code**: Clean architecture, no development artifacts after Phase 8

---

**Created:** February 1, 2026
**Revised:** February 1, 2026 (corrected FraiseQL architecture)
**Status:** Ready for Phase 1 Kickoff
