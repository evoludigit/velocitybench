# Cost Simulation System - Revised Roadmap with FraiseQL Domain

**Date**: 2026-01-13
**Previous Approach**: Standalone Python modules with REST API
**New Approach**: FraiseQL-integrated domain with database persistence
**Impact**: Phase architecture unchanged, but implementation strategy completely revised

---

## What Changed

### Previous Plan (Before Domain Analysis)
```
Phase 1: Python core modules (cost_config, load_profiler, resource_calculator)
Phase 2: More Python modules (cost_calculator, efficiency_analyzer)
Phase 3: Result builders (JSON/HTML/CSV output)
Phase 4: REST API + Integration
Phase 5: React frontend

Issues:
- Data exists only in memory
- No persistence of benchmark results
- No historical analysis capability
- Separate query layer (REST) from data model
```

### New Plan (With Normalized Domain)
```
Phase 1: Python core modules ✅ DONE (cost_config, load_profiler, resource_calculator)
Phase 2: Database schema + FraiseQL types + Cost calculations
Phase 3: Cost analysis resolvers + Query/Mutation types
Phase 4: Frontend + Grafana dashboard

Improvements:
- All data persisted in database
- Historical benchmarks enable trend analysis
- Single unified domain model (FraiseQL types + tables)
- Type-safe GraphQL API (no separate REST layer)
- Zero N+1 queries via JSONB composition views
```

---

## The Critical Insight

You were right: **This should be database-backed analytics, not just calculations.**

Implications:
1. **Benchmark runs are persistent entities**, not ephemeral results
2. **Cost analysis is derived from benchmarks**, not independent
3. **Framework comparison requires historical context**, not just current run
4. **The frontend queries a unified domain**, not multiple APIs

This completely changes the architecture from:
```
JMeter Results → Calculate → Display
```

To:
```
JMeter Results → Store (Benchmark) → Calculate (Resolver) → Query (GraphQL) → Display
```

---

## Phase 2 Reimagined: Database + FraiseQL Integration

### What Was Phase 2
```python
# cost_calculator.py (350 lines)
def calculate_cloud_costs(resources: ResourceRequirements) -> CostBreakdown:
    ...

# efficiency_analyzer.py (250 lines)
def analyze_efficiency(metrics: PerformanceMetrics, costs: CostBreakdown) -> EfficiencyMetrics:
    ...
```

### What Phase 2 Should Be
```
1. Database Schema Creation (1-2 days)
   - Run migrations for tb_framework, tb_benchmark_run, tb_cost_analysis, etc.
   - Create composition views (tv_benchmark_run, tv_cost_analysis)
   - Create indexes for query performance

2. FraiseQL Type Definitions (2-3 days)
   - @fraiseql.type Framework with nested relationships
   - @fraiseql.type BenchmarkRun with composed objects
   - @fraiseql.type CostAnalysisResult with breakdowns
   - @fraiseql.type EfficiencyRanking

3. Cost Calculation Resolvers (2-3 days)
   - Keep cost_calculator.py and efficiency_analyzer.py from Phase 1
   - Wrap them in FraiseQL resolvers
   - Store results in database via mutations

4. Integration & Testing (2-3 days)
   - Create @fraiseql.mutation RunBenchmark
   - Create @fraiseql.mutation AnalyzeCost
   - Test full pipeline: JMeter → Store → Calculate → Query
```

**Timeline**: Same 1 week, but now producing database-backed types

---

## Phase 3 Reimagined: Query & Mutation Types

### What Was Phase 3
```python
# result_builder.py (300 lines)
def to_json(analysis: CostAnalysisResult) -> str: ...
def to_html(analysis: CostAnalysisResult) -> str: ...
def to_csv(comparison: list[CostAnalysisResult]) -> str: ...
```

### What Phase 3 Should Be
```
1. Root Query Type (1-2 days)
   - query { framework(name: "strawberry") { ... } }
   - query { benchmarkRun(id: "...") { ... } }
   - query { frameworkComparison(suiteId: "...", loadProfile: "small") { ... } }
   - query { performanceTrend(frameworkId: "...", days: 30) { ... } }

2. Root Mutation Type (1-2 days)
   - mutation { runBenchmark(input: {...}) { success { ... } error { ... } } }
   - mutation { analyzeCost(input: {...}) { success { ... } error { ... } } }

3. Aggregation Queries (1-2 days)
   - query { frameworkComparison(...) { frameworks { ... } mostEfficient cheapest } }
   - query { costComparison(...) { providers { cloudProvider averageCost } } }

4. Documentation & Schema (1 day)
   - GraphQL schema documentation
   - Query examples
   - Integration guide
```

**Timeline**: Same 1 week, now with full GraphQL API

**Bonus**: JSON export is automatic (GraphQL result serialization)

---

## Phase 4 Reimagined: Frontend + Dashboard

### What Was Phase 4
```
Integration with run-benchmarks.py
Hook into CI/CD pipeline
```

### What Phase 4 Should Be
```
1. Frontend Integration (1-2 days)
   - Apollo Client setup
   - Dashboard layout (framework comparison, cost trends, efficiency ranking)
   - Interactive filtering (by language, load profile, cloud provider)
   - Chart components (cost breakdown, latency distribution, efficiency heatmap)

2. Grafana Dashboard (1 day)
   - Pre-built panels for common queries
   - Real-time benchmark status monitoring
   - Cost trend visualization
   - Framework ranking leaderboard

3. CLI Integration (1 day)
   - Query benchmark results: `velocitybench benchmark query framework strawberry`
   - Trigger analysis: `velocitybench benchmark analyze run-id`
   - Compare frameworks: `velocitybench benchmark compare --suite 2026-q1 --metric cost`

4. Run Integration (1-2 days)
   - Hook into scripts/run-benchmarks.py
   - Auto-store results in database
   - Auto-trigger cost analysis mutation
   - Report links to dashboard

5. Testing & Docs (1 day)
   - E2E integration tests
   - Deployment guide
   - User documentation
```

**Timeline**: Same 1 week, now with complete frontend story

---

## Key Architectural Changes

### Before (Standalone)
```
┌─────────────────────┐
│  Python Modules     │
│  (calculations)     │
└─────────────────────┘
         ↓ (results in memory)
┌─────────────────────┐
│   REST API          │ (FastAPI)
│   (endpoints)       │
└─────────────────────┘
         ↓ (HTTP JSON)
┌─────────────────────┐
│   React Frontend    │
│   (visualization)   │
└─────────────────────┘

Problems:
- No persistence
- Data lost on server restart
- No historical comparison
- N+1 query problems
```

### After (FraiseQL Domain)
```
┌──────────────────────────────────┐
│  Benchmark Database              │
│  (persistent, normalized schema) │
└──────────────────────────────────┘
         ↓ (FraiseQL resolvers)
┌──────────────────────────────────┐
│  FraiseQL GraphQL API            │
│  (typed, composable queries)     │
└──────────────────────────────────┘
         ↓ (GraphQL subscription)
┌──────────────────────────────────┐
│  React + Grafana Frontend        │
│  (rich dashboards)               │
└──────────────────────────────────┘

Advantages:
- Persistent benchmark history
- Zero N+1 queries (JSONB composition)
- Type-safe API (GraphQL schema)
- Historical trend analysis
- Native relationship support
- Single source of truth
```

---

## Implementation Flow

### Phase 1: Core Engine ✅ (Complete)
```python
# Python modules for calculations
cost_config.py           # Pricing models
load_profiler.py         # Load projection
resource_calculator.py   # Resource calculation
exceptions.py            # Error types
```

### Phase 2: Database + FraiseQL Types (NEW)

**What you'll do**:

1. **Create database schema** (from BENCHMARK_DOMAIN_ARCHITECTURE.md)
   ```sql
   CREATE TABLE tb_framework (...)
   CREATE TABLE tb_benchmark_run (...)
   CREATE TABLE tb_cost_analysis (...)
   ...
   CREATE VIEW tv_benchmark_run AS ...
   CREATE VIEW tv_cost_analysis AS ...
   ```

2. **Define FraiseQL types** (mapping database to GraphQL)
   ```python
   @fraiseql.type(sql_source="benchmark.tv_benchmark_run")
   class BenchmarkRun:
       id: str
       framework: Framework
       metrics: PerformanceMetrics
       ...
   ```

3. **Wrap Phase 1 modules in resolvers**
   ```python
   @fraiseql.field
   async def cost_analysis(self, info) -> CostAnalysisResult:
       # Call cost_calculator.py
       # Store result in database
       # Return typed result
   ```

4. **Create mutations for persistence**
   ```python
   @fraiseql.mutation
   class AnalyzeCost:
       # Trigger cost calculation
       # Store results
       # Return success/error
   ```

### Phase 3: GraphQL Queries (NEW)

**What you'll do**:

1. **Define root Query type**
   ```python
   @fraiseql.type
   class Query:
       @fraiseql.field
       async def frameworkComparison(self, ...) -> FrameworkComparison:
           ...
   ```

2. **Define root Mutation type**
   ```python
   @fraiseql.type
   class Mutation:
       @fraiseql.field
       async def runBenchmark(self, ...) -> RunBenchmarkResult:
           ...
   ```

3. **Create aggregation types**
   ```python
   @fraiseql.type
   class FrameworkComparison:
       frameworks: list[FrameworkComparisonRow]
       mostEfficient: Framework
       cheapestToRun: Framework
       ...
   ```

### Phase 4: Frontend (NEW)

**What you'll do**:

1. **Create dashboard** (React + Apollo)
   ```tsx
   <FrameworkComparison suiteId={suiteId} loadProfile="small">
       <CostChart />
       <EfficiencyRanking />
       <ResourceComparison />
   </FrameworkComparison>
   ```

2. **Create Grafana dashboard**
   ```json
   {
       "panels": [
           { "title": "Cost Comparison", "query": "frameworkComparison(...)" },
           { "title": "Efficiency Trend", "query": "performanceTrend(...)" }
       ]
   }
   ```

3. **Integrate with CI/CD**
   ```python
   # In run-benchmarks.py
   await mutation("""
       mutation {
           runBenchmark(input: {
               frameworkId: "strawberry"
               suiteId: "2026-q1"
           }) { success { run { id } } }
       }
   """)
   ```

---

## Data Flow After Redesign

### Complete Pipeline

```
1. JMeter generates results
   └─ File: tests/perf/results/strawberry/simple/small/timestamp/results.jtl

2. Parse & Store in Database
   └─ runBenchmark mutation
   └─ Creates tb_benchmark_run entry
   └─ Inserts tb_performance_metrics row

3. Calculate Resources
   └─ Resolver calls resource_calculator.py
   └─ Stores in tb_resource_profile table

4. Calculate Costs
   └─ Resolver calls cost_calculator.py
   └─ Stores in tb_cost_analysis and tb_cost_breakdown tables

5. Calculate Efficiency
   └─ Resolver calls efficiency_analyzer.py
   └─ Stores in tb_efficiency_ranking table

6. Query Results
   └─ Frontend queries: frameworkComparison(suiteId, loadProfile)
   └─ Composition view tv_benchmark_run returns in 1 query
   └─ Composition view tv_cost_analysis returns in 1 query
   └─ Frontend receives fully nested data
   └─ Display comparison table

7. Historical Analysis
   └─ Query performanceTrend(frameworkId, days: 30)
   └─ Get all benchmarks for framework in last 30 days
   └─ Visualize trends in dashboard
```

---

## What Stays the Same

Your Phase 1 modules:
```python
cost_config.py          # ✅ No changes needed
load_profiler.py        # ✅ No changes needed
resource_calculator.py  # ✅ No changes needed
exceptions.py           # ✅ No changes needed
```

These are called by resolvers, not directly by users.

---

## What's New

1. **Database schema** (benchmark persistence)
2. **FraiseQL types** (domain model)
3. **Resolvers** (wrapping Phase 1 + database)
4. **Query/Mutation types** (GraphQL API)
5. **Frontend** (React dashboard)
6. **Grafana** (monitoring dashboard)

---

## Timeline

```
Phase 1 ✅                          COMPLETE
├─ cost_config.py, load_profiler.py, resource_calculator.py
├─ 45 unit tests
└─ 909 lines of code

Phase 2 🟡 (1 week)                 DATABASE + FRAISEQL TYPES
├─ Database migrations
├─ FraiseQL type definitions
├─ Cost calculation resolvers
├─ Integration tests
└─ 7 days

Phase 3 🟡 (1 week)                 GRAPHQL API
├─ Root Query type
├─ Root Mutation type
├─ Aggregation types
├─ Schema documentation
└─ 7 days

Phase 4 🟡 (1 week)                 FRONTEND + INTEGRATION
├─ React dashboard
├─ Grafana panels
├─ CLI integration
├─ E2E tests
└─ 7 days

Total: 4 weeks
Completion: Early March 2026
```

---

## Success Metrics (Updated)

### Phase 2
- [ ] Database schema created and tested
- [ ] All 7 FraiseQL types defined
- [ ] Cost analyzer resolvers store results in DB
- [ ] Integration tests verify data persistence
- [ ] Performance tests verify zero N+1 queries

### Phase 3
- [ ] Root Query supports framework comparison
- [ ] Root Mutation supports benchmark execution
- [ ] Aggregation types enable complex queries
- [ ] GraphQL schema introspection works
- [ ] Query examples documented

### Phase 4
- [ ] Dashboard displays framework comparison
- [ ] Grafana shows cost trends
- [ ] CLI works for queries
- [ ] CI/CD integration auto-stores results
- [ ] End-to-end test passes

---

## Architecture Comparison

| Aspect | Old Plan | New Plan |
|--------|----------|----------|
| **Data Storage** | In-memory Python objects | PostgreSQL database |
| **Persistence** | Lost on restart | Permanent, queryable |
| **API Type** | REST (multiple endpoints) | GraphQL (single endpoint) |
| **Query Complexity** | Multiple requests for nested data | Single request with composition views |
| **Type Safety** | Python types only | Python types + GraphQL schema |
| **Historical Analysis** | Not possible | Trend queries over time |
| **N+1 Problem** | Likely (REST endpoints) | Impossible (JSONB composition) |
| **Frontend Data** | Must assemble from multiple APIs | Single structured response |
| **Extensibility** | Add new endpoint per feature | Extend GraphQL schema |

---

## Why This Matters

Instead of **"Here's a cost simulator tool"**, you now have:

> **"A comprehensive benchmarking analytics system that measures frameworks across raw performance, language complexity, and hardware cost—with historical tracking and rich visualization."**

This is a **real product**, not just a utility.

---

## Next Immediate Step

Would you like me to:

1. **Create Phase 2 plan** with detailed database schema and FraiseQL type definitions?
2. **Start Phase 2 implementation** with database migrations and type definitions?
3. **Design the frontend architecture** for the React dashboard?
4. **Create CLI tool design** for querying results?

Which would be most valuable next?
