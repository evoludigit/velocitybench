# VelocityBench Analytics Platform - Complete Redesign

**Date**: 2026-01-13
**Status**: Design Phase (replaces narrow "cost simulator" with comprehensive analytics)
**Scope**: Expose ALL VelocityBench data: code, benchmarks, metrics, costs, comparisons

---

## Executive Summary

The current Phase 2 schema is **too narrow**. It only captures costs, but VelocityBench is about:

1. **Framework Implementations** - The actual source code
2. **Benchmark Execution** - Run data, parameters, timing
3. **Performance Results** - JMeter metrics, latency percentiles, throughput
4. **Resource Analysis** - Infrastructure requirements
5. **Cost Analysis** - Operational costs across clouds
6. **Comparative Analytics** - Which framework is best for what?

**This redesign** expands the schema to be a complete **VelocityBench Results Analytics Platform** that exposes:

- ✅ Framework source code and implementation
- ✅ All benchmark runs with full metadata
- ✅ Complete performance metrics (JMeter data)
- ✅ Infrastructure requirements derived from metrics
- ✅ Multi-cloud cost analysis
- ✅ Historical trends and comparisons
- ✅ Query patterns and complexity analysis

---

## Current Problems with Phase 2

### 1. Missing Framework Implementation Data
```sql
-- Current schema only has metadata:
CREATE TABLE tb_framework (
    id UUID,
    name VARCHAR,
    language VARCHAR,
    -- But NO source code!
    -- No implementation details!
    -- No git repository information!
);
```

Should include:
- Source code files (with versioning)
- Implementation approach (ORM, raw SQL, etc.)
- Database library used
- Query optimization techniques
- Caching strategies

### 2. Missing Query Patterns
```sql
-- Current schema assumes generic "workload"
CREATE TABLE tb_workload (
    name VARCHAR,
    query_complexity VARCHAR,
    -- But WHICH queries? What are they testing?
);
```

Should include:
- Query type (simple GET, nested query, mutation, etc.)
- Query structure (schema excerpt)
- Expected complexity
- Real query strings for reproducibility

### 3. Missing Detailed Metrics
```sql
-- Current schema captures basic metrics
CREATE TABLE tb_performance_metrics (
    latency_p95 INT,
    latency_p99 INT,
    -- But where are percentile details?
    -- Where are error breakdowns?
);
```

Should include:
- Individual request latencies (percentile array)
- Error types and counts
- GC pauses and correlations
- Memory usage patterns
- CPU usage patterns

### 4. Missing Benchmark Session Context
```sql
-- Current schema assumes single dimension:
CREATE TABLE tb_benchmark_run (
    id UUID,
    status VARCHAR,
    -- But WHEN was it run?
    -- On WHAT machine?
    -- With WHAT database setup?
    -- With HOW MANY iterations?
);
```

Should include:
- Test machine specs
- Database version and config
- Timestamp and environmental factors
- Number of iterations/warm-ups
- GC settings and JVM flags
- JMeter configuration

### 5. Missing Code Traceability
```
-- No way to trace from "benchmark run" back to "which code version?"
-- What if a bug was fixed between runs?
-- What if the framework was updated?
```

Should include:
- Git commit hash of framework at time of run
- Git commit hash of benchmark code
- Framework version
- Database schema version

---

## New Unified Analytics Domain

### **8-Level Normalized Schema**

```
Level 1: FRAMEWORK DEFINITION
├─ Framework (name, language, runtime)
├─ FrameworkImplementation (source code, files, git info)
├─ FrameworkMetadata (performance characteristics)
└─ DatabaseSetup (ORM, library, optimizations)

Level 2: BENCHMARK DEFINITION
├─ BenchmarkSuite (collection, version)
├─ QueryPattern (type, complexity, schema)
├─ Workload (combination of patterns)
└─ LoadProfile (RPS, duration, threads)

Level 3: TEST ENVIRONMENT
├─ TestMachine (CPU, RAM, OS)
├─ DatabaseInstance (version, config, setup)
├─ BenchmarkEnvironment (JMeter settings, GC config)
└─ ExternalDependencies (caches, services)

Level 4: BENCHMARK EXECUTION
├─ BenchmarkRun (start, end, status)
├─ RunIteration (warm-up, actual run)
└─ ExecutionLog (events, errors, warnings)

Level 5: PERFORMANCE METRICS
├─ RequestMetrics (individual request data)
├─ LatencyDistribution (percentiles, histogram)
├─ ErrorMetrics (types, counts, patterns)
├─ ResourceMetrics (CPU, memory, GC)
└─ ThroughputMetrics (RPS, connections, threads)

Level 6: ANALYSIS & DERIVED DATA
├─ ResourceProfile (CPU/RAM/storage needed)
├─ CostAnalysis (multi-cloud breakdown)
├─ EfficiencyRanking (composite score)
└─ PerformanceCharacterization (patterns)

Level 7: COMPARISON & TRENDS
├─ FrameworkComparison (head-to-head)
├─ PerformanceTrend (over time)
├─ RegressionDetection (anomalies)
└─ RecommendationEngine (best for scenario)

Level 8: CODE & REPRODUCIBILITY
├─ FrameworkCodeSnapshot (versioned source)
├─ QueryCodeSnapshot (versioned queries)
├─ BenchmarkCodeSnapshot (test harness version)
└─ ResultInspection (query coverage, edge cases)
```

---

## New Database Schema Structure

### **Tables by Category**

**Framework & Implementation (10 tables)**
```sql
tb_framework                    -- Framework definition
tb_framework_metadata          -- Performance characteristics
tb_framework_implementation    -- Source code and files
tb_framework_file              -- Individual source files
tb_database_library            -- ORM, driver, optimization
tb_database_library_version    -- Version history
tb_optimization_technique      -- Query optimization used
tb_caching_strategy            -- Caching approach
tb_git_repository              -- Framework repository
tb_framework_version           -- Framework version history
```

**Benchmark Definition (8 tables)**
```sql
tb_benchmark_suite             -- Test suite definition
tb_query_pattern               -- Query type and structure
tb_query_pattern_file          -- Actual query files
tb_workload                    -- Workload definition (combinations)
tb_load_profile                -- Load testing parameters
tb_load_profile_ramp           -- Ramp-up configuration
tb_query_pattern_complexity    -- Complexity metrics
tb_benchmark_schema            -- Schema for test data
```

**Test Environment (8 tables)**
```sql
tb_test_machine                -- Hardware specifications
tb_test_machine_cpu            -- CPU details
tb_test_machine_memory         -- Memory configuration
tb_database_instance           -- Database version/config
tb_database_configuration      -- Specific settings
tb_external_dependency         -- Redis, cache, etc.
tb_jmeter_configuration        -- Test tool settings
tb_environment_variable        -- Runtime environment
```

**Execution & Metrics (12 tables)**
```sql
tb_benchmark_run               -- Single test run
tb_run_iteration               -- Warm-up vs actual
tb_execution_log               -- Run events/errors
tb_request_metric              -- Individual request data
tb_latency_percentile          -- Percentile breakdown
tb_latency_histogram           -- Histogram buckets
tb_error_metric                -- Error analysis
tb_resource_metric             -- CPU/RAM/GC data
tb_throughput_metric           -- RPS and connection data
tb_response_size_metric        -- Payload analysis
tb_time_breakdown              -- Connect/idle/processing times
tb_query_execution_detail      -- Per-query analysis
```

**Analysis & Cost (6 tables)**
```sql
tb_resource_profile            -- Calculated requirements
tb_cost_analysis               -- Multi-cloud costs
tb_cost_breakdown              -- Per-provider breakdown
tb_efficiency_ranking          -- Composite scores
tb_performance_characterization-- Pattern analysis
tb_regression_detection        -- Anomaly detection
```

**Comparison & Trends (4 tables)**
```sql
tb_framework_comparison        -- Head-to-head results
tb_performance_trend           -- Historical tracking
tb_recommendation_scenario     -- Use case recommendations
tb_result_export               -- Export formats
```

**Code & Reproducibility (6 tables)**
```sql
tb_code_snapshot               -- Framework code version
tb_code_file_snapshot          -- Individual file versions
tb_query_snapshot              -- Query code version
tb_benchmark_code_snapshot     -- Test harness version
tb_result_inspection           -- Query coverage details
tb_reproducibility_manifest    -- Full run specification
```

**Total: 54 tables** (up from 15)

---

## What Each Layer Exposes

### **Level 1: Framework Implementation**

```python
# Users can see:
framework = Framework(
    id="strawberry-0.230",
    name="Strawberry GraphQL",
    language="Python",
    language_family="dynamic",
    runtime="CPython 3.13",
    version="0.230.0",

    # NEW: Source code
    implementation=FrameworkImplementation(
        git_repository="https://github.com/strawberry-graphql/strawberry",
        git_commit="a1b2c3d...",  # At time of benchmark
        source_files=[
            SourceFile(path="main.py", content="...", lines=250),
            SourceFile(path="resolvers.py", content="...", lines=400),
            SourceFile(path="models.py", content="...", lines=300),
        ],
        database_library=DatabaseLibrary(
            name="SQLAlchemy",
            version="2.0.23",
            optimization="lazy loading with batching",
        ),
        caching_strategies=[
            CachingStrategy(type="query caching", library="redis"),
            CachingStrategy(type="object cache", library="memcached"),
        ],
    ),

    # Characteristics
    metadata=FrameworkMetadata(
        type_safety="partial",
        paradigm="OO with functional",
        concurrency_model="async+threaded",
        startup_time_ms=150,
        learning_curve=7,  # 1-10 scale
    ),
)
```

### **Level 2: Benchmark Execution**

```python
run = BenchmarkRun(
    id="run-20260113-001",
    framework_id="strawberry-0.230",
    suite_id="2026-q1",

    # NEW: Full execution context
    test_environment=TestEnvironment(
        machine=TestMachine(
            cpu_model="Intel Core i7-12700K",
            cpu_cores=12,
            cpu_ghz=5.0,
            ram_gb=32,
            os="Linux 6.1.0",
        ),
        database=DatabaseInstance(
            engine="PostgreSQL",
            version="15.1",
            config={
                "shared_buffers": "8GB",
                "effective_cache_size": "24GB",
                "work_mem": "64MB",
            },
        ),
        jmeter_config=JMeterConfiguration(
            version="5.6",
            gc_settings="-Xmx4g -XX:+UseG1GC",
            ramp_up_seconds=30,
            warm_up_iterations=100,
        ),
    ),

    # NEW: Query patterns
    query_patterns=[
        QueryPattern(
            type="simple_query",
            complexity="simple",
            query_structure="{ user(id: 1) { id name email } }",
            expected_execution_ms=5,
        ),
        QueryPattern(
            type="nested_query",
            complexity="moderate",
            query_structure="{ user(id: 1) { posts { comments { author { name } } } } }",
            expected_execution_ms=45,
        ),
    ],

    # Execution results
    metrics=PerformanceMetrics(
        total_requests=6000,
        requests_per_second=100.0,
        latency_p50=25,
        latency_p95=95,
        latency_p99=150,

        # NEW: Detailed breakdown
        latency_distribution=LatencyDistribution(
            percentiles=[1, 5, 10, 25, 50, 75, 90, 95, 99],
            values=[5, 8, 12, 18, 25, 45, 80, 95, 150],
            histogram={
                "0-10ms": 800,
                "10-20ms": 2100,
                "20-50ms": 2400,
                "50-100ms": 600,
                "100-200ms": 100,
            },
        ),
        error_breakdown=ErrorBreakdown(
            total_errors=0,
            timeout_5xx_errors=0,
            connection_errors=0,
            application_errors=0,
        ),
        resource_usage=ResourceUsage(
            peak_cpu_percent=85.0,
            avg_cpu_percent=65.0,
            peak_memory_mb=1024,
            avg_memory_mb=768,
            gc_pause_count=12,
            gc_pause_time_ms=450,
        ),
    ),
)
```

### **Level 3: Comparative Analytics**

```python
comparison = FrameworkComparison(
    query_pattern="nested_query",
    load_profile="small",
    frameworks=[
        ComparisonRow(
            framework=Framework("strawberry"),
            metrics=PerformanceMetrics(...),
            resources=ResourceProfile(...),
            costs=CostAnalysisResult(...),
            efficiency_rank=1,
            efficiency_score=9.2,
            highlights={
                "fastest": True,
                "cheapest": True,
                "best_scaling": True,
                "lowest_variance": True,
            },
        ),
        ComparisonRow(
            framework=Framework("graphene"),
            metrics=PerformanceMetrics(...),
            resources=ResourceProfile(...),
            costs=CostAnalysisResult(...),
            efficiency_rank=2,
            efficiency_score=8.1,
        ),
        # ... more frameworks
    ],

    # NEW: Insights
    insights=Insights(
        best_for_scenarios=[
            Scenario(
                name="simple_queries_high_throughput",
                recommended_framework="strawberry",
                reason="Lowest latency p99 (150ms vs 280ms for others)",
            ),
            Scenario(
                name="nested_queries_cost_sensitive",
                recommended_framework="strawberry",
                reason="Lowest operational cost ($45/mo vs $120/mo for Laravel)",
            ),
        ],
        performance_characteristics={
            "strawberry": {
                "scales_linearly_to": 10000,  # RPS
                "optimal_connections": 50,
                "gc_friendly": True,
            },
        },
    ),
)
```

---

## Migration Path from Phase 2

### **What Stays the Same**
- Phase 1 cost calculation modules (no changes needed)
- Overall 7-level architecture concept
- Composition view patterns (zero N+1)
- Trinity Pattern usage

### **What Changes**

1. **Expand schema from 15 to 54 tables** to capture all data

2. **Add framework code tracking**
   - Source files with versioning
   - Git commit hashes for reproducibility
   - Implementation choices visible

3. **Add detailed environment tracking**
   - Test machine specs
   - Database configuration
   - JMeter settings
   - External dependencies

4. **Expand metrics collection**
   - Percentile distributions (not just p50/p95/p99)
   - Latency histograms
   - Error categorization
   - Resource metrics (CPU, memory, GC)
   - Time breakdowns (connect, idle, processing)

5. **Add query-level tracking**
   - Query patterns with actual query strings
   - Per-query execution metrics
   - Query complexity analysis
   - Coverage tracking

6. **Add reproducibility**
   - Code snapshots (versioned source)
   - Benchmark configuration snapshots
   - Full execution manifest
   - Result inspection tools

### **New FraiseQL Type Hierarchy**

```python
# Currently 25 types, expand to 60+ types:

# Framework layer (was 3 types)
Framework
FrameworkImplementation        # NEW
FrameworkFile                  # NEW
DatabaseLibrary               # NEW
OptimizationTechnique         # NEW
CachingStrategy               # NEW

# Benchmark layer (was 3 types)
BenchmarkSuite
QueryPattern                  # NEW (detailed)
QueryPatternFile              # NEW
Workload
LoadProfile

# Execution layer (was 1 type)
BenchmarkRun
RunIteration                  # NEW
ExecutionLog                  # NEW

# Metrics layer (expand from 1 type to 8 types)
PerformanceMetrics
LatencyDistribution           # NEW
LatencyHistogram              # NEW
ErrorBreakdown                # NEW
ResourceUsage                 # NEW (CPU, memory, GC)
TimeBreakdown                 # NEW (connect, idle, processing)
ResponseSizeMetrics           # NEW
QueryExecutionDetail          # NEW

# Environment layer (NEW - 5 types)
TestEnvironment
TestMachine
DatabaseInstance
JMeterConfiguration
ExternalDependency

# Analysis layer (expand from 3 types to 6 types)
ResourceProfile
CostAnalysisResult
EfficiencyRanking
PerformanceCharacterization   # NEW
RegressionDetection           # NEW
Insights                      # NEW

# Comparison layer (expand from 3 types to 6 types)
FrameworkComparison
FrameworkComparisonRow
ProviderCostSummary
CostComparison
PerformanceTrend
RecommendationScenario        # NEW

# Code & Reproducibility (NEW - 4 types)
CodeSnapshot
QuerySnapshot
BenchmarkCodeSnapshot
ReproducibilityManifest
```

---

## Benefits of This Redesign

### **For Users**
- ✅ See exactly which code was benchmarked
- ✅ Understand performance at query level
- ✅ Trace results back to specific git commits
- ✅ Reproduce results exactly
- ✅ Understand trade-offs (code complexity vs performance)
- ✅ Get recommendations for their use case

### **For Developers**
- ✅ Track performance regression from code changes
- ✅ Measure impact of optimizations
- ✅ Identify performance characteristics by language
- ✅ Compare ORM strategies empirically
- ✅ Benchmark caching strategies

### **For Organizations**
- ✅ Make framework selection data-driven
- ✅ Calculate total cost of ownership
- ✅ Plan infrastructure needs
- ✅ Identify scaling bottlenecks
- ✅ Justify technology decisions

---

## Implementation Plan

### **Phase 2.1: Database Schema Expansion** (1-2 days)
- Expand `schema.sql` from 15 to 54 tables
- Add indexes for new query patterns
- Create composition views for code+metrics
- Migrate existing data structure

### **Phase 2.2: FraiseQL Type Expansion** (1-2 days)
- Expand `fraiseql_types.py` from 25 to 60+ types
- Update type hierarchy to match new schema
- Add docstrings explaining each field
- Define new aggregation types

### **Phase 2.3: Resolver Enhancement** (2-3 days)
- Add code snapshot resolvers
- Add detailed metrics resolvers
- Add comparison query resolvers
- Add recommendation engine resolvers

### **Phase 2.4: Test Suite Expansion** (2-3 days)
- Add tests for code tracking
- Add tests for detailed metrics
- Add tests for recommendations
- Add performance tests

### **Phase 3: GraphQL API** (Same as before)
- Root Query/Mutation types
- Field resolvers
- Schema generation

### **Phase 4: Frontend** (Same as before)
- Dashboard components
- Code inspector
- Comparison visualizations
- Recommendation display

---

## Key Insight

**The schema should capture ENOUGH DATA that someone could:**

1. **Understand WHY** framework A is faster than framework B
   - Is it the language? (Python vs Go)
   - Is it the ORM? (SQLAlchemy vs raw SQL)
   - Is it the caching? (Redis vs memcached)
   - Is it the query optimization? (batching vs N+1)

2. **Reproduce the EXACT result**
   - Same code version (git commit)
   - Same database configuration
   - Same test machine specs
   - Same JMeter settings
   - Same data set

3. **Apply insights to THEIR situation**
   - "Which framework for my use case?"
   - "What's the cost at 10x load?"
   - "How much infrastructure do I need?"
   - "Where are the bottlenecks?"

---

## Recommendation

**I suggest we redesign Phase 2 to be this comprehensive analytics platform** rather than just a cost simulator.

This is:
- ✅ More valuable (complete benchmark analytics)
- ✅ More extensible (new frameworks, new queries)
- ✅ More professional (enterprise-grade analytics)
- ✅ Better aligned with VelocityBench's mission
- ✅ Still achievable in same timeframe (just broader scope)

Would you like me to:

1. **Redesign the schema** to be comprehensive (54 tables vs 15)?
2. **Expand FraiseQL types** to expose all this data (60+ types vs 25)?
3. **Create new resolvers** for code tracking and detailed analytics?
4. **Update tests** to cover the expanded functionality?

This would make VelocityBench a **true analytics platform**, not just a cost calculator.
