# VelocityBench FraiseQL Integration - Revised Plan Summary

**Created:** February 1, 2026
**Status:** Ready for approval and Phase 1 kickoff
**Last Updated:** February 1, 2026 (corrected architecture)

---

## What Changed from Initial Plan

### Initial Plan (INCORRECT)
❌ 15 framework implementations (3 per language)
❌ Embedded Rust runtime in each framework (FFI/WASM)
❌ Frameworks execute queries directly
❌ Performance would be identical across all frameworks
❌ Complex, redundant architecture

### Revised Plan (CORRECT)
✅ 1 fraiseql-server (Rust, serves HTTP)
✅ 5 framework blueprints (1 per language, HTTP proxies)
✅ Clear separation: pure FraiseQL vs framework overhead
✅ Measurable performance differences per language
✅ Clean, focused, benchmarkable architecture

---

## Two Goals Achievement

### Goal 1: Assessing FraiseQL Performance ✅

**How achieved:**
1. **Phase 2**: Establish pure FraiseQL baseline
   - Direct HTTP calls to fraiseql-server
   - No framework overhead
   - Baseline metrics for comparison

2. **Phase 4**: Measure framework overhead
   - Framework latency - FraiseQL baseline = overhead
   - Framework-specific costs quantified
   - Language comparison meaningful

**Result:** Clear understanding of:
- Rust runtime performance (constant)
- HTTP overhead (constant)
- Framework-specific costs (variable per language)

### Goal 2: Blueprint Implementations in All Languages ✅

**How achieved:**
1. **Phase 1**: Schema authoring validates all 5 language generators
   - Python, TypeScript, Go, Java, PHP
   - All compile to identical schema.json
   - Proof of equivalence

2. **Phase 3**: Framework blueprints (1 per language)
   - Idiomatic implementations
   - Best practices
   - Starting points for users
   - Can be extended with features

3. **Phases 5-6**: Features and validation
   - Add advanced features (auth, caching, etc.)
   - Validate parity across languages
   - Comprehensive blueprints

**Result:** Production-ready examples for:
- FastAPI (Python)
- Express (TypeScript)
- Gin (Go)
- Spring Boot (Java)
- Laravel (PHP)

---

## 8-Phase Roadmap

| Phase | Title | Duration | Goal |
|-------|-------|----------|------|
| **1** | Foundation & Schema | Week 1 | Schema in all 5 languages, equivalence proof |
| **2** | FraiseQL Server Baseline | Week 1 | Pure performance metrics, no framework overhead |
| **3** | Framework Blueprints | Weeks 2-3 | 5 frameworks (parallel per language) |
| **4** | Benchmark Suite | Week 3 | Measure framework overhead per language |
| **5** | Feature Enhancements | Week 4 | Add features, validate no regressions |
| **6** | Cross-Language Validation | Week 4 | Parity tests, quality metrics |
| **7** | Documentation | Week 5 | Comprehensive guides and examples |
| **8** | Finalization | Week 5 | Polish, clean artifacts, release |

**Total**: ~5 weeks
**Parallel work possible**: Phases 3 and 5 (5 languages simultaneously)

---

## Architecture Overview

```
┌──────────────────────────────────────────────────┐
│    FraiseQL Rust Server (Shared, Single)         │
│  - Loads schema.compiled.json                    │
│  - Executes queries deterministically            │
│  - HTTP endpoint at :8000/graphql                │
│  - Connects to PostgreSQL                        │
└──────────────────────────────────────────────────┘
                        ▲
                        │ HTTP (measured overhead)
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
    ┌────────┐    ┌────────┐    ┌────────┐
    │FastAPI │    │Express │    │Gin/    │
    │Proxy   │    │Proxy   │    │Spring/ │
    │(8001)  │    │(8002)  │    │Laravel │
    └────────┘    └────────┘    └────────┘
        ▲              ▲              ▲
        └──────────────┼──────────────┘
                       │
            ┌──────────▼──────────┐
            │ Benchmark Suite     │
            │ - Measure overhead  │
            │ - Compare languages │
            │ - Validate parity   │
            └─────────────────────┘
```

---

## Key Deliverables

### Pillar 1: Schema Authoring (Phase 1)
- **schema.fraiseql.py** - Python definition (primary)
- **schema.fraiseql.ts** - TypeScript equivalent
- **schema.fraiseql.go** - Go equivalent
- **schema.fraiseql.java** - Java equivalent
- **schema.fraiseql.php** - PHP equivalent
- **schema.json** - Intermediate (all languages → identical)
- **schema.compiled.json** - Runtime (CLI compiled)

**Proof:** All 5 languages generate identical schema → generators are equivalent

### Pillar 2: Framework Blueprints (Phases 3, 5)
- **Python**: FastAPI proxy framework
- **TypeScript**: Express proxy framework
- **Go**: Gin proxy framework
- **Java**: Spring Boot proxy framework
- **PHP**: Laravel proxy framework

Each includes:
- HTTP proxy to fraiseql-server
- Request validation
- Error handling
- Metrics/observability
- Authentication (Phase 5)
- Documentation with examples

### Pillar 3: Benchmarking Suite (Phases 2, 4)
- **Pure FraiseQL**: Baseline performance (no framework)
- **Framework Overhead**: Per-language HTTP overhead
- **Comparison Report**: Latency, throughput, resource usage
- **Parity Tests**: All frameworks execute identically
- **Load Tests**: Scalability characteristics

---

## Measurement Framework

### Phase 2: Pure FraiseQL Baseline
```
Query → HTTP → fraiseql-server → Database → Result

Metrics:
- Latency (p50, p99)
- Throughput (req/s)
- Resource usage (memory, CPU)
- Concurrent handling
```

### Phase 4: Framework Overhead
```
Query → HTTP → Framework Proxy → HTTP → fraiseql-server → Database

Framework Overhead = (Framework Latency) - (FraiseQL Baseline)

Example (FastAPI):
  FraiseQL baseline: 15.2ms
  FastAPI latency: 23.1ms
  Overhead: 7.9ms (52%)
```

### Key Insight
- **Overhead varies by language** → measures framework efficiency
- **Overhead doesn't include** query execution (identical for all)
- **Overhead includes** HTTP parsing, validation, serialization
- **Comparable across languages** because same hardware/network

---

## Success Metrics

### Performance (Phase 2-4)
- [ ] FraiseQL baseline: < 50ms p99 for simple queries
- [ ] Framework overhead: < 10-15ms per language
- [ ] Throughput: ≥ 100 req/s pure, ≥ 50 req/s with framework
- [ ] No memory leaks under sustained load

### Quality (Phase 6)
- [ ] Functional parity: all frameworks return identical data
- [ ] Test coverage: ≥ 80% across all frameworks
- [ ] Zero warnings: all linters pass
- [ ] Type safety: no type errors

### Documentation (Phase 7)
- [ ] Architecture documented
- [ ] API examples complete
- [ ] Framework guides comprehensive
- [ ] Performance analysis clear

---

## File Structure (Final)

```
velocitybench/
│
├── fraiseql-schema/
│   ├── schema.fraiseql.py / .ts / .go / .java / .php
│   ├── schema.json (shared output)
│   └── schema.compiled.json (runtime)
│
├── frameworks/
│   ├── fraiseql-python/fastapi/      # Blueprint
│   ├── fraiseql-typescript/express/  # Blueprint
│   ├── fraiseql-go/gin/              # Blueprint
│   ├── fraiseql-java/spring-boot/    # Blueprint
│   └── fraiseql-php/laravel/         # Blueprint
│
├── benchmarks/
│   ├── fraiseql-direct/    # Phase 2: pure baseline
│   ├── framework-overhead/ # Phase 4: overhead analysis
│   └── reports/            # Generated reports
│
├── tests/
│   ├── parity/     # Phase 6: equivalence tests
│   ├── quality/    # Linting, coverage
│   └── integration/# End-to-end workflows
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── GETTING_STARTED.md
│   ├── PERFORMANCE_RESULTS.md
│   ├── frameworks/        # Per-language guides
│   └── examples/          # Code examples
│
├── README.md
├── RELEASE_NOTES.md
└── LICENSE
```

---

## Advantages of This Approach

✅ **Clear Performance Isolation**
- FraiseQL performance separate from framework overhead
- Can identify optimization targets
- Fair comparison across languages

✅ **Practical Blueprints**
- Users see production-ready examples
- Language-idiomatic implementations
- Can extend and customize

✅ **Schema Authoring Validation**
- Proves language generators work
- Identical behavior across languages
- Single schema source of truth

✅ **Focused Scope**
- 5 frameworks instead of 15
- No redundant implementations
- Faster to complete, easier to maintain

✅ **Measurable Goals**
- Clear metrics for both goals
- Performance differences quantifiable
- Parity provable through tests

---

## What Happens Next

### Approval Needed
Please review and approve this revised plan. Key decision points:

1. **Architecture**: Single fraiseql-server + framework proxies? ✅
2. **Framework Count**: 5 blueprints (1 per language)? ✅
3. **Measurement Approach**: Phase 2 baseline + Phase 4 overhead? ✅
4. **Timeline**: 5-week execution? ✅

### Phase 1 Tasks (Upon Approval)
1. Design comprehensive schema
2. Implement in Python (primary)
3. Implement in TypeScript, Go, Java, PHP
4. Validate all compile to identical schema.json
5. Establish schema as foundation for all subsequent phases

### Critical Path
```
Phase 1: Schema (blocking)
  ↓
Phase 2: FraiseQL baseline (blocking)
  ↓
Phases 3-5: Frameworks (parallel)
  ↓
Phase 6: Validation
  ↓
Phase 7: Documentation
  ↓
Phase 8: Release
```

---

## Risk Mitigation

**Risk**: Framework overhead measurements don't show significant differences
**Mitigation**: Network latency dominates, focus on relative overhead percentages

**Risk**: Language generators not truly equivalent
**Mitigation**: Schema validation tests catch any deviations

**Risk**: Performance regressions during feature addition (Phase 5)
**Mitigation**: Baseline established Phase 4, regression tests in Phase 6

**Risk**: Scope creep on framework features
**Mitigation**: MVP approach: minimal proxy initially, features optional

---

## Conclusion

This revised plan:
- ✅ Correctly models FraiseQL v2 architecture
- ✅ Achieves both goals clearly and measurably
- ✅ Provides production-ready blueprints
- ✅ Establishes meaningful performance baselines
- ✅ Validates language generator equivalence
- ✅ Deliverable in ~5 weeks
- ✅ Maintainable long-term

**Recommendation**: Approve and proceed to Phase 1.

---

**Questions?** Let's discuss the architecture, timeline, or scope before kickoff.
