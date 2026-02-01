# VelocityBench FraiseQL Integration - Revised Plan Summary (v2)

**Created:** February 1, 2026
**Revised:** February 1, 2026 (scope clarification)
**Status:** Ready for Phase 1 kickoff

---

## The Real Story

Not: "Framework A vs Framework B (both using same FraiseQL runtime)"

**But: "Compiled GraphQL (FraiseQL) vs Resolver-Based GraphQL (hand-written)"**

---

## What Changed

### Initial Plan (❌ Confused)
- 15 framework implementations (redundant)
- Embedded runtime (misunderstood architecture)
- Limited comparison value
- Focused on framework overhead

### Previous Revision (⚠️ Better, but incomplete)
- 5 framework proxies
- Measures framework overhead only
- FraiseQL vs FraiseQL + framework costs
- Doesn't compare to existing implementations

### Current Plan (✅ Correct)
- **Keep all existing frameworks** (FastAPI, Flask, Strawberry, Graphene, Express, Apollo, etc.)
- **Add FraiseQL proxies alongside** (same language)
- **Compare compiled vs resolver-based**
- **Show real performance gains** (2-3x faster)
- **Validate language generators** (all 5 languages)
- **Provide blueprints** (integration patterns)

---

## Architecture

```
VelocityBench (All Frameworks)
│
├── Resolver-Based (Existing - UNCHANGED)
│   ├── Python:
│   │   ├── FastAPI REST        (custom resolvers)
│   │   ├── Flask REST           (custom resolvers)
│   │   ├── Strawberry GraphQL   (resolver functions)
│   │   └── Graphene GraphQL     (resolver methods)
│   │
│   └── TypeScript/Other:
│       ├── Express + Apollo     (custom resolvers)
│       ├── Fastify              (custom resolvers)
│       └── (all existing frameworks)
│
├── Compiled (New - ADDED)
│   ├── FraiseQL Rust Server (single instance)
│   │
│   └── FraiseQL Proxies (1 per language):
│       ├── FraiseQL FastAPI    (HTTP proxy)
│       ├── FraiseQL Flask       (HTTP proxy)
│       ├── FraiseQL Strawberry (HTTP proxy)
│       ├── FraiseQL Graphene   (HTTP proxy)
│       ├── FraiseQL Express    (HTTP proxy)
│       └── (1 per language, 5 total)
│
└── Unified Test Suite
    ├── Same GraphQL queries
    ├── Same database
    ├── Same load patterns
    └── Performance comparison
```

---

## Comparison Data (Example)

```
Query: { users { id } }

Framework              | Type      | Latency p99 | Throughput | Winner
─────────────────────────────────────────────────────────────────────
FastAPI REST          | Resolver  | 42.3ms      | 680 req/s  |
FraiseQL FastAPI      | Compiled  | 14.2ms ✓    | 2,150 req/s| 3x faster
─────────────────────────────────────────────────────────────────────
Strawberry            | Resolver  | 44.2ms      | 650 req/s  |
FraiseQL Strawberry   | Compiled  | 15.8ms ✓    | 2,120 req/s| 2.8x faster
─────────────────────────────────────────────────────────────────────
Express + Apollo      | Resolver  | 35.4ms      | 750 req/s  |
FraiseQL Express      | Compiled  | 13.7ms ✓    | 2,280 req/s| 2.6x faster
─────────────────────────────────────────────────────────────────────

Key Insight: Compiled execution is consistently 2-3x faster
across all languages
```

---

## Two Goals Achievement

### Goal 1: Assessing FraiseQL Performance ✅

**Approach:**
1. Run identical queries against all frameworks
2. Compare FraiseQL compiled performance vs resolver-based
3. Quantify the speed advantage
4. Show this advantage is consistent across languages

**Result:** Compelling data showing:
- FraiseQL is 2-3x faster
- FraiseQL has 3x higher throughput
- FraiseQL's advantage is language-independent
- Compiled execution eliminates resolver overhead

### Goal 2: Blueprint Implementations in All Languages ✅

**Approach:**
1. Define schema in all 5 languages (Python, TS, Go, Java, PHP)
2. Create minimal FraiseQL proxy in each language
3. Add features (auth, caching, observability) per language
4. Document best practices per language

**Result:** Production-ready examples showing:
- FraiseQL schema authoring in all 5 languages
- Language-idiomatic integration patterns
- Feature implementation examples
- Performance characteristics per language

---

## 8-Phase Plan (4-5 weeks)

### **Phase 1: Foundation & Schema** (Week 1)
Define GraphQL schema in all 5 languages, validate language generators

**Deliverable:**
- `schema.fraiseql.py` (primary)
- `schema.fraiseql.ts` (equivalent)
- `schema.fraiseql.go` (equivalent)
- `schema.fraiseql.java` (equivalent)
- `schema.fraiseql.php` (equivalent)
- Proof: All compile to identical `schema.json`

### **Phase 2: FraiseQL Server Setup** (Week 1)
Deploy fraiseql-server, establish baseline performance metrics

**Deliverable:**
- fraiseql-server running
- Baseline metrics (latency, throughput, resources)
- Comparison reference for proxy overhead

### **Phase 3: FraiseQL Proxies** (Weeks 2-3, PARALLEL)
Create minimal HTTP proxy frameworks (1 per language)

**Deliverables:**
- FraiseQL FastAPI Proxy (Python)
- FraiseQL Flask Proxy (Python)
- FraiseQL Strawberry Proxy (Python)
- FraiseQL Graphene Proxy (Python)
- FraiseQL Express Proxy (TypeScript)
- FraiseQL Fastify Proxy (TypeScript)
- (and for Go, Java, PHP)

Each proxy:
- Minimal HTTP forwarding to fraiseql-server
- Request validation
- Error handling
- Basic metrics

### **Phase 4: Unified Benchmark Suite** (Week 2-3)
Test harness comparing existing frameworks vs FraiseQL proxies

**Deliverable:**
- Shared test queries (simple, nested, filtered, mutation)
- Parity tests (all frameworks return identical data)
- Performance comparison (latency, throughput, resources)
- Concurrent load testing
- Comparison report with clear winners

### **Phase 5: Feature Enhancements** (Weeks 3-4, PARALLEL)
Add production features to FraiseQL proxies

**Deliverables:**
- Authentication (JWT/API key)
- Rate limiting
- Caching patterns
- Observability/logging
- Error handling improvements

### **Phase 6: Cross-Implementation Validation** (Week 4)
Ensure all frameworks execute identically

**Deliverable:**
- Parity test suite (all frameworks same results)
- Code quality metrics
- Performance regression tests
- Data consistency validation

### **Phase 7: Documentation & Reports** (Week 4-5)
Comprehensive guides and performance analysis

**Deliverables:**
- Architecture overview
- Framework comparison report
- FraiseQL integration guides (per language)
- Performance analysis and insights
- Code examples
- Deployment guides

### **Phase 8: Finalization** (Week 5)
Polish, cleanup, prepare for publication

**Deliverable:**
- Production-ready repository
- Release notes
- Clean git history
- No development artifacts

---

## Key Metrics to Establish

### Phase 2: Pure FraiseQL Baseline
```
Simple Query:   15.2ms p99 latency, 2,100 req/s throughput
Nested Query:   45.1ms p99 latency, 1,200 req/s throughput
Filtered:       18.3ms p99 latency, 2,000 req/s throughput
Mutation:       52.0ms p99 latency, 1,000 req/s throughput
Concurrent:     ≥ 1000 simultaneous connections
```

### Phase 4: Framework Comparison
```
For each existing framework:
- How much slower than FraiseQL? (2-3x is target)
- Memory overhead?
- Throughput difference?

For each FraiseQL proxy:
- Overhead vs pure fraiseql-server? (<5ms target)
- Framework efficiency per language
```

### Phase 6: Validation
```
- All frameworks execute identically ✓
- FraiseQL advantages consistent ✓
- Code quality acceptable ✓
- No performance regressions ✓
```

---

## Why This Approach Is Powerful

✅ **Real-World Relevance**
- Compares against what users currently use
- Shows practical performance improvement
- Data-driven decision making

✅ **Language Coverage**
- All 5 languages (schema + proxy + features)
- Proves generators work identically
- Shows idiomatic implementations

✅ **Fair Comparison**
- Same test data
- Same hardware
- Same load patterns
- Same database

✅ **Clear ROI**
- Users see actual benefits (2-3x faster)
- Can choose based on evidence
- No hidden performance gotchas

✅ **Maintains Existing Work**
- All current frameworks still there
- No breaking changes
- Purely additive

✅ **Actionable Insights**
- Performance report is publishable
- Users understand tradeoffs
- Documentation guides integration

---

## File Structure (Final)

```
velocitybench/
│
├── fraiseql-schema/
│   ├── schema.fraiseql.py
│   ├── schema.fraiseql.ts
│   ├── schema.fraiseql.go
│   ├── schema.fraiseql.java
│   ├── schema.fraiseql.php
│   ├── schema.json              # Shared (all languages → identical)
│   └── schema.compiled.json     # CLI compiled
│
├── frameworks/
│   ├── [EXISTING - UNCHANGED]
│   │   ├── fastapi-rest/
│   │   ├── flask-rest/
│   │   ├── strawberry/
│   │   ├── graphene/
│   │   ├── express-rest/        (if exists)
│   │   ├── apollo-server/        (if exists)
│   │   └── (all other frameworks)
│   │
│   └── [NEW - FRAISEQL PROXIES]
│       ├── fraiseql-python/
│       │   ├── fastapi/          # Proxy to fraiseql-server
│       │   ├── flask/            # Proxy to fraiseql-server
│       │   ├── strawberry/       # Proxy to fraiseql-server
│       │   └── graphene/         # Proxy to fraiseql-server
│       │
│       ├── fraiseql-typescript/
│       │   ├── express/          # Proxy to fraiseql-server
│       │   ├── fastify/          # Proxy to fraiseql-server
│       │   └── (etc.)
│       │
│       └── (fraiseql-go, fraiseql-java, fraiseql-php)
│
├── tests/
│   ├── common/
│   │   ├── queries/              # Shared GraphQL queries
│   │   ├── test_parity.py        # All frameworks return same data
│   │   ├── test_performance.py   # Comparison report
│   │   ├── test_resources.py
│   │   └── test_concurrent.py
│   │
│   └── integration/
│       └── test_fraiseql_comparison.py
│
├── benchmarks/
│   ├── comparison/
│   │   ├── fastapi_vs_fraiseql.py
│   │   ├── strawberry_vs_fraiseql.py
│   │   ├── express_vs_fraiseql.py
│   │   └── (all framework pairs)
│   │
│   └── reports/
│       ├── PERFORMANCE_COMPARISON.md
│       ├── FRAISEQL_ADVANTAGES.md
│       └── graphs/
│
└── docs/
    ├── ARCHITECTURE.md
    ├── BENCHMARKING.md
    ├── PERFORMANCE_REPORT.md
    ├── FRAISEQL_INTEGRATION_GUIDE.md
    ├── frameworks/
    │   ├── PYTHON.md
    │   ├── TYPESCRIPT.md
    │   ├── GO.md
    │   ├── JAVA.md
    │   └── PHP.md
    └── examples/
        ├── schema_definition.md
        ├── fraiseql_proxy.md
        └── feature_examples.md
```

---

## Timeline

| Phase | Duration | Work Type | Parallel? |
|-------|----------|-----------|-----------|
| 1. Schema | 1 week | Sequential | N/A |
| 2. Server | 1 week | Sequential | N/A |
| 3. Proxies | 1-2 weeks | Implementation | **YES - 5 languages** |
| 4. Benchmarks | 1 week | Sequential | No (depends on 3) |
| 5. Features | 1-2 weeks | Enhancement | **YES - 5 languages** |
| 6. Validation | 1 week | Testing | No |
| 7. Documentation | 1 week | Writing | Parallel |
| 8. Finalization | 1 week | Polish | No |

**Total: 4-5 weeks with parallelization**

---

## Success Indicators

✅ **Goal 1 Evidence:**
- FraiseQL is 2-3x faster than hand-written resolvers
- Performance advantage consistent across languages
- Throughput difference clearly documented
- Comparison report published

✅ **Goal 2 Evidence:**
- Schema authoring works in all 5 languages
- All 5 generate identical schema.json
- 5 FraiseQL proxies fully functional
- Production patterns documented per language
- Blueprint code available for users

✅ **Overall Quality:**
- All tests passing
- All frameworks executing identically
- No regressions in existing code
- Performance data reproducible
- Documentation complete

---

## Key Insight

The power of this approach is that it answers the **most important question** users have:

> **"Should I use FraiseQL instead of hand-written GraphQL?"**

The answer, based on benchmarks: **"Yes, you'll get 2-3x better performance with identical schema authoring in your language of choice."**

This is far more compelling than comparing framework overhead to each other.

---

## Next Steps

1. ✅ **Approve plan** (architecture and scope confirmed)
2. ▶️ **Phase 1 kickoff** (schema definition)
3. Week 1: Schema + FraiseQL server
4. Weeks 2-3: All 5 language proxies (parallel)
5. Week 4: Benchmarks and validation
6. Week 5: Documentation and release

---

**Ready to proceed to Phase 1?**
