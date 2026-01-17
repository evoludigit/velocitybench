# VelocityBench Clarity Plan

## Status Summary

**Last Updated**: 2026-01-18

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | Framework Classification | ✅ COMPLETE |
| Phase 2 | Benchmark Methodology | ✅ COMPLETE |
| Phase 2.5 | Blog Page Load Workload | ✅ COMPLETE |
| Phase 3 | Results Presentation | 🔲 Pending |
| Phase 4 | Documentation Structure | 🔲 Partial |
| Phase 5 | Automation | 🔲 Pending |

**Related Work**: Experimental Frameworks Implementation → See `.plan/experimental-frameworks-completion.md`

---

## Goal

Make VelocityBench a **clear, reproducible, publication-quality** framework benchmark comparison for the FraiseQL v2 release.

---

## Phase 1: Framework Classification ✅ COMPLETE

### What Was Done

- ✅ Created `FRAMEWORKS.md` with tiered classification
- ✅ Documented 18 Tier 1 (Production-Ready) frameworks
- ✅ Documented 4 Tier 2 (N+1 Demonstration) frameworks
- ✅ Documented 15 Tier 3 (Pending Implementation) frameworks
- ✅ Added "Removed Frameworks" section documenting cleanup
- ✅ Removed 7 duplicate/broken framework directories:
  - `go-gqlgen.broken/`
  - `gqlgen/`
  - `hot-chocolate/`
  - `graphql-net/`
  - `entity-framework-core/`
  - `graphql-core-php/`
  - `ruby-rails-fixed/`
- ✅ Applied Ruby Rails fixes before removing helper repo
- ✅ Standardized port strategy (GraphQL=4000, REST=8080)

### Files Created/Updated

- `FRAMEWORKS.md` - Complete framework registry with tiers

---

## Phase 2: Benchmark Methodology ✅ COMPLETE

### What Was Done

- ✅ Created `BENCHMARK_METHODOLOGY.md` documenting:
  - Test environment specifications
  - Workload types (9 total including blog-page)
  - Load levels (smoke, light, medium, heavy, stress)
  - Warmup protocol
  - Metrics collected (latency, throughput, error rate, resources)
  - Standardized configuration (connection pooling, HTTP settings)
  - Test data generation
  - Reproducibility checklist
- ✅ Documented standardized port strategy

### Files Created/Updated

- `BENCHMARK_METHODOLOGY.md` - Complete methodology documentation

---

## Phase 2.5: Blog Page Load Workload ✅ COMPLETE

### What Was Done

- ✅ Created `tests/perf/jmeter/workloads/blog-page.jmx` with:
  - GraphQL thread group (1 request)
  - REST Batched thread group (3 requests via Transaction Controller)
  - REST Naive thread group (N+1 requests via ForEach Controller)
  - CSV Data Set for post IDs
  - Configurable parameters (threads, rampup, loops, hosts, ports)

- ✅ Added batch endpoints to REST frameworks:
  - `frameworks/fastapi-rest/main.py` - `GET /users?ids=` and `GET /posts/{id}/comments`
  - `frameworks/flask-rest/main.py` - Same endpoints
  - `frameworks/express-rest/src/index.ts` - Same endpoints
  - `frameworks/gin-rest/` - Same endpoints

- ✅ Created test data infrastructure:
  - `tests/perf/scripts/generate-post-ids.py` - Script to generate random post IDs
  - `tests/perf/data/post_ids.csv` - Header file (needs population with script)

### Remaining

- 🔲 **Run `generate-post-ids.py`** to populate `post_ids.csv` (requires seeded database)

---

## Phase 3: Results Presentation 🔲 PENDING

### Tasks

| Task | Status | Notes |
|------|--------|-------|
| Create `tests/perf/scripts/generate-report.py` | 🔲 Pending | Report generator |
| Create `BENCHMARK_RESULTS.md` template | 🔲 Pending | Markdown format |
| Add `benchmark-results.json` output | 🔲 Pending | Machine-readable |
| Create Grafana benchmark dashboard | 🔲 Pending | Visual comparison |
| Add blog-page comparison to report | 🔲 Pending | Key comparison |

---

## Phase 4: Documentation Structure 🔲 PARTIAL

### Tasks

| Task | Status | Notes |
|------|--------|-------|
| Create `FRAMEWORKS.md` | ✅ Complete | Framework registry |
| Create `BENCHMARK_METHODOLOGY.md` | ✅ Complete | Methodology docs |
| Create `BENCHMARK_RESULTS.md` | 🔲 Pending | Results report |
| Restructure `README.md` | 🔲 Pending | Add quick results section |
| Update `CONTRIBUTING.md` | 🔲 Pending | Framework addition guide |
| Move completed docs to `docs/completed/` | ✅ Complete | 11 files moved |

### Current Documentation Structure

```
velocitybench/
├── README.md                    # Project overview
├── FRAMEWORKS.md                # Framework registry ✅
├── BENCHMARK_METHODOLOGY.md     # Methodology docs ✅
├── BENCHMARK_CLARITY_PLAN.md    # This plan
├── CONTRIBUTING.md              # Basic contribution guide
├── QUICK_START.md               # Getting started
├── MAKEFILE_USAGE.md            # Makefile reference
│
├── docs/
│   └── completed/               # 11 archived completed docs ✅
│
├── .plan/
│   └── experimental-frameworks-completion.md  # Framework implementation plan
│
├── [COST_SIMULATION_*.md]       # Cost simulation design (separate effort)
├── [DATASET_SCALING_*.md]       # Dataset scaling plans (separate effort)
└── [Other pending docs]         # Various in-progress work
```

---

## Phase 5: Automation 🔲 PENDING

### Tasks

| Task | Status | Notes |
|------|--------|-------|
| Add `make benchmark` target | 🔲 Pending | Single framework |
| Add `make benchmark-all` target | 🔲 Pending | All frameworks |
| Add `make smoke-test` target | 🔲 Pending | Verify all |
| Add `make report` target | 🔲 Pending | Generate report |
| CI/CD workflow (optional) | 🔲 Pending | Automated runs |

---

## Implementation Order (Updated)

### Completed Work

| Phase | Task | Status |
|-------|------|--------|
| 2.5 | Create blog-page.jmx workload | ✅ Complete |
| 2.5 | Add REST batch endpoints | ✅ Complete |
| 1.1 | Create FRAMEWORKS.md | ✅ Complete |
| 2.1 | Write BENCHMARK_METHODOLOGY.md | ✅ Complete |
| 1.3 | Cleanup broken/legacy frameworks | ✅ Complete |
| 2.5 | Create generate-post-ids.py | ✅ Complete |

### Remaining Work

| Phase | Task | Priority | Effort |
|-------|------|----------|--------|
| 2.5 | Run generate-post-ids.py (needs DB) | High | 5 min |
| 3.1 | Create report generator script | High | 4 hours |
| 3.2 | Add blog-page comparison to report | High | 1 hour |
| 4.2 | Restructure README.md | Medium | 1 hour |
| 4.3 | Improve CONTRIBUTING.md | Medium | 1 hour |
| 5.1 | Add Makefile targets | Medium | 1 hour |
| 5.2 | CI/CD automation | Low | 4 hours |

**Remaining Estimated Effort**: ~12 hours

---

## Related Plans

### Experimental Frameworks Completion

**Location**: `.plan/experimental-frameworks-completion.md`

**Status**: Phase 1 Complete, Phases 2-10 Pending (~51 hours)

This plan covers implementing the 15 stub frameworks to reach 25+ production-ready frameworks:
- Phase 2: Configure Hasura and PostGraphile
- Phase 3-9: Implement Python, Node.js, Go, Rust, Ruby, PHP, JVM frameworks
- Phase 10: Update docker-compose.yml and documentation

### Cost Simulation System

**Location**: `COST_SIMULATION_*.md` files (6 documents)

**Status**: Design Complete, Implementation 25% done

Separate effort for CPU/RAM/Storage cost projections per framework.

### Dataset Scaling

**Location**: `DATASET_SCALING_*.md` and `DYNAMIC_DATASET_SCALING_PLAN.md`

**Status**: Plan complete, implementation partial

5K gold corpus → 1M posts scaling system.

---

## Success Criteria

After implementing this plan:

1. ✅ **Framework classification clear** - FRAMEWORKS.md with tiers
2. ✅ **Methodology documented** - BENCHMARK_METHODOLOGY.md complete
3. ✅ **Blog page load workload ready** - blog-page.jmx created
4. ✅ **REST batch endpoints added** - /users?ids= on all REST frameworks
5. 🔲 **Results are publishable** - Report generator needed
6. 🔲 **Automation exists** - Makefile targets needed
7. 🔲 **README updated** - Quick results section needed

---

## Appendix: Current State

### What Exists (Strong Foundation)

- ✅ 28+ framework implementations
- ✅ JMeter infrastructure with 9 workload types (including blog-page)
- ✅ Prometheus + Grafana monitoring
- ✅ Docker orchestration
- ✅ Cost simulation engine (45 tests passing)
- ✅ Realistic blog post seed data (10,000+ posts)
- ✅ Statistical analysis scripts
- ✅ Clear framework classification (FRAMEWORKS.md)
- ✅ Documented methodology (BENCHMARK_METHODOLOGY.md)
- ✅ Blog page load workload (blog-page.jmx)
- ✅ REST batch endpoints for GraphQL comparison

### What's Still Missing

- 🔲 Publication-ready results report generator
- 🔲 Updated README with quick results
- 🔲 Makefile targets for common operations
- 🔲 CI/CD automation
- 🔲 Test data populated (post_ids.csv needs generation)
