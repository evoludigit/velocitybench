# Framework Benchmarking Domain - Normalized Architecture

**Status**: Design Phase
**Date**: 2026-01-13
**Purpose**: Define a pure, normalized FraiseQL domain for comprehensive framework analysis across all axes

---

## Executive Summary

This document defines a **complete normalized domain model** for benchmarking frameworks across:
- **Raw Performance** (RPS, latency, throughput, errors)
- **Language Complexity** (language family, paradigm, type safety, runtime)
- **Hardware Cost** (CPU, memory, storage requirements for different loads)
- **Operational Characteristics** (startup time, memory footprint, scaling behavior)

The model uses FraiseQL's Trinity Pattern and JSONB composition for efficient querying and zero N+1 problems.

---

## Domain Model Overview

### Core Entities

```
┌─────────────────────────────────────────────────────────────────┐
│                    BENCHMARKING DOMAIN                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Framework ─────┬──→ Deployment            BenchmarkSuite       │
│                 │                                │               │
│                 ├──→ FrameworkMetadata     Workload             │
│                 │                                │               │
│                 └──→ BenchmarkRun ───────→ Metrics              │
│                        │                    │                   │
│                        ├──→ ResourceProfile │                   │
│                        │                    └──→ PerformanceData│
│                        └──→ CostAnalysis                         │
│                             ├──→ InfrastructureRequirements     │
│                             ├──→ CloudCostBreakdown             │
│                             └──→ EfficiencyRanking              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Normalized Schema Design

### Level 1: Framework Definition

#### tb_framework
```sql
CREATE TABLE tb_framework (
    pk_framework SERIAL PRIMARY KEY,
    id UUID UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,                  -- "Strawberry", "FastAPI", "Spring Boot"
    language VARCHAR(50) NOT NULL,              -- "Python", "Java", "Go", "Node.js"
    language_family VARCHAR(50) NOT NULL,       -- "Dynamic", "Static", "Hybrid"
    runtime VARCHAR(100) NOT NULL,              -- "CPython 3.13", "JVM 21", "Go 1.21"
    version VARCHAR(50) NOT NULL,               -- Framework version
    repository_url VARCHAR(500),                -- GitHub link
    documentation_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE UNIQUE INDEX idx_tb_framework_name ON tb_framework(name);
CREATE INDEX idx_tb_framework_language ON tb_framework(language);
CREATE INDEX idx_tb_framework_family ON tb_framework(language_family);
```

#### FrameworkMetadata
```sql
CREATE TABLE tb_framework_metadata (
    pk_metadata SERIAL PRIMARY KEY,
    fk_framework INTEGER NOT NULL UNIQUE REFERENCES tb_framework(pk_framework),
    metadata JSONB NOT NULL,  -- Extensible key-value storage
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Example metadata JSONB structure:
{
  "type_safety": "full",          -- "none", "partial", "full"
  "paradigm": "functional",       -- "OO", "functional", "hybrid"
  "concurrency_model": "async",   -- "threaded", "async", "async+threaded"
  "garbage_collection": true,
  "memory_management": "automatic",
  "startup_time_ms": 250,
  "cold_start_penalty_ms": 500,
  "language_expressiveness": 8,   -- 1-10 scale
  "learning_curve": 6,            -- 1-10 (easier-harder)
  "ecosystem_size": 9,            -- 1-10
  "maturity_years": 5
}
```

### Level 2: Benchmark Definition

#### tb_benchmark_suite
```sql
CREATE TABLE tb_benchmark_suite (
    pk_suite SERIAL PRIMARY KEY,
    id UUID UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,                 -- "VelocityBench 2026 Q1"
    description TEXT,
    version VARCHAR(50) NOT NULL,
    created_by VARCHAR(255),
    baseline_framework_id UUID,                 -- Reference framework for comparison
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### tb_workload
```sql
CREATE TABLE tb_workload (
    pk_workload SERIAL PRIMARY KEY,
    id UUID UNIQUE NOT NULL,
    fk_suite INTEGER NOT NULL REFERENCES tb_benchmark_suite(pk_suite),
    name VARCHAR(255) NOT NULL,                 -- "Simple Queries", "Complex Aggregations"
    description TEXT,
    query_complexity VARCHAR(50) NOT NULL,     -- "simple", "moderate", "complex"
    operation_count INT,
    estimated_join_depth INT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_tb_workload_suite ON tb_workload(fk_suite);
```

#### tb_load_profile
```sql
CREATE TABLE tb_load_profile (
    pk_profile SERIAL PRIMARY KEY,
    id UUID UNIQUE NOT NULL,
    name VARCHAR(50) NOT NULL UNIQUE,          -- "smoke", "small", "medium", "large", "production"
    rps INT NOT NULL,                          -- 10, 50, 500, 5000, 10000
    duration_seconds INT NOT NULL,             -- 120
    warmup_seconds INT NOT NULL,               -- 10
    threads INT NOT NULL,
    ramp_up_time_seconds INT,
    think_time_ms INT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Level 3: Benchmark Execution

#### tb_benchmark_run
```sql
CREATE TABLE tb_benchmark_run (
    pk_run SERIAL PRIMARY KEY,
    id UUID UNIQUE NOT NULL,
    fk_framework INTEGER NOT NULL REFERENCES tb_framework(pk_framework),
    fk_suite INTEGER NOT NULL REFERENCES tb_benchmark_suite(pk_suite),
    fk_workload INTEGER NOT NULL REFERENCES tb_workload(fk_workload),
    fk_load_profile INTEGER NOT NULL REFERENCES tb_load_profile(pk_profile),

    -- Execution metadata
    status VARCHAR(50) NOT NULL,               -- "running", "completed", "failed"
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_seconds INT,

    -- Raw results (will be decomposed)
    jmeter_results JSONB,                      -- Aggregated JTL data
    jmeter_file_path VARCHAR(500),             -- Path to .jtl file for reference

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX idx_tb_benchmark_run_framework ON tb_benchmark_run(fk_framework);
CREATE INDEX idx_tb_benchmark_run_suite ON tb_benchmark_run(fk_suite);
CREATE INDEX idx_tb_benchmark_run_status ON tb_benchmark_run(status);
CREATE INDEX idx_tb_benchmark_run_time ON tb_benchmark_run(start_time DESC);
CREATE UNIQUE INDEX idx_tb_benchmark_run_unique ON tb_benchmark_run(fk_framework, fk_suite, fk_workload, fk_load_profile);
```

### Level 4: Performance Metrics

#### tb_performance_metrics
```sql
CREATE TABLE tb_performance_metrics (
    pk_metrics SERIAL PRIMARY KEY,
    fk_run INTEGER NOT NULL UNIQUE REFERENCES tb_benchmark_run(pk_run),

    -- Throughput
    total_requests BIGINT NOT NULL,
    total_errors BIGINT NOT NULL,
    error_rate NUMERIC(5,2),                   -- Percentage 0-100
    requests_per_second NUMERIC(10,2),         -- Steady-state RPS

    -- Latency (milliseconds)
    latency_min INT,
    latency_p50 INT,
    latency_p95 INT,
    latency_p99 INT,
    latency_p999 INT,
    latency_max INT,
    latency_mean INT,
    latency_stddev INT,

    -- Request size
    response_bytes_min INT,
    response_bytes_mean INT,
    response_bytes_max INT,

    -- Streaming/progressive metrics
    connect_time_mean INT,                     -- Time to establish connection
    idle_time_mean INT,                        -- Idle time between requests

    -- Server response timing
    server_processing_mean INT,                -- Latency - Connect

    created_at TIMESTAMP DEFAULT NOW()
);

-- Index
CREATE INDEX idx_tb_performance_metrics_run ON tb_performance_metrics(fk_run);
```

#### tb_performance_percentiles
```sql
CREATE TABLE tb_performance_percentiles (
    pk_percentile SERIAL PRIMARY KEY,
    fk_run INTEGER NOT NULL REFERENCES tb_benchmark_run(pk_run),
    percentile INT NOT NULL,                   -- 1, 5, 10, 25, 50, 75, 90, 95, 99
    latency_ms INT NOT NULL,
    UNIQUE(fk_run, percentile),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Level 5: Infrastructure & Resources

#### tb_resource_profile
```sql
CREATE TABLE tb_resource_profile (
    pk_profile SERIAL PRIMARY KEY,
    fk_run INTEGER NOT NULL UNIQUE REFERENCES tb_benchmark_run(pk_run),

    -- CPU
    cpu_cores_required INT NOT NULL,
    cpu_cores_with_headroom INT NOT NULL,
    headroom_percent NUMERIC(5,2),             -- Default 30
    rps_per_core INT,                          -- Derived: rps / cores

    -- Memory
    application_baseline_mb INT,
    connection_pool_memory_mb INT,
    memory_buffer_percent NUMERIC(5,2),
    memory_required_gb NUMERIC(10,2),

    -- Storage
    application_storage_gb NUMERIC(10,2),      -- Code + static assets
    data_growth_gb_per_month NUMERIC(10,4),
    log_storage_gb_per_month NUMERIC(10,4),

    -- Network
    bandwidth_mbps NUMERIC(10,2),
    data_transfer_gb_per_month NUMERIC(10,2),

    -- Derived metrics
    total_monthly_storage_gb NUMERIC(10,2),    -- With compression & replication

    created_at TIMESTAMP DEFAULT NOW()
);
```

### Level 6: Cost Analysis

#### tb_cost_analysis
```sql
CREATE TABLE tb_cost_analysis (
    pk_analysis SERIAL PRIMARY KEY,
    fk_run INTEGER NOT NULL UNIQUE REFERENCES tb_benchmark_run(pk_run),

    -- Provider selection (which provider was cheapest)
    recommended_cloud_provider VARCHAR(50),    -- "aws", "gcp", "azure"
    recommended_instance_type VARCHAR(100),   -- "m5.xlarge", "n1-standard-4"

    -- Analysis metadata
    analysis_timestamp TIMESTAMP DEFAULT NOW(),
    estimated_margin_of_error NUMERIC(5,2),   -- ±10% typical

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_cost_analysis_run ON tb_cost_analysis(fk_run);
```

#### tb_cost_breakdown
```sql
CREATE TABLE tb_cost_breakdown (
    pk_breakdown SERIAL PRIMARY KEY,
    fk_analysis INTEGER NOT NULL REFERENCES tb_cost_analysis(pk_analysis),

    cloud_provider VARCHAR(50) NOT NULL,      -- "aws", "gcp", "azure"

    -- Monthly costs (USD)
    compute_cost NUMERIC(10,2),
    database_cost NUMERIC(10,2),
    storage_cost NUMERIC(10,2),
    data_transfer_cost NUMERIC(10,2),
    monitoring_cost NUMERIC(10,2),
    contingency_cost NUMERIC(10,2),

    total_monthly_cost NUMERIC(10,2),

    -- Yearly projections
    total_yearly_cost NUMERIC(12,2),
    yearly_with_1yr_reserved NUMERIC(12,2),   -- 40% discount
    yearly_with_3yr_reserved NUMERIC(12,2),   -- 55% discount

    -- Per-request metrics
    cost_per_request NUMERIC(12,10),
    requests_per_dollar BIGINT,

    -- Instance details
    instance_type VARCHAR(100),
    instance_hourly_rate NUMERIC(10,4),

    UNIQUE(fk_analysis, cloud_provider),
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### tb_efficiency_ranking
```sql
CREATE TABLE tb_efficiency_ranking (
    pk_ranking SERIAL PRIMARY KEY,
    fk_run INTEGER NOT NULL UNIQUE REFERENCES tb_benchmark_run(pk_run),

    -- Efficiency score (0-10) using weighted formula
    -- 40% cost + 30% latency + 20% throughput + 10% reliability
    efficiency_score NUMERIC(5,2),
    cost_component NUMERIC(5,2),               -- Normalized 0-10
    latency_component NUMERIC(5,2),            -- Normalized 0-10
    throughput_component NUMERIC(5,2),        -- Normalized 0-10
    reliability_component NUMERIC(5,2),       -- Normalized 0-10

    -- Ranking context
    suite_rank INT,                            -- Position in suite (1 = most efficient)
    rank_tie_breaker VARCHAR(50),              -- "cost", "latency", "throughput"

    created_at TIMESTAMP DEFAULT NOW()
);
```

### Level 7: Historical & Trending

#### tb_benchmark_comparison
```sql
CREATE TABLE tb_benchmark_comparison (
    pk_comparison SERIAL PRIMARY KEY,
    id UUID UNIQUE NOT NULL,

    fk_suite_old INTEGER NOT NULL REFERENCES tb_benchmark_suite(pk_suite),
    fk_suite_new INTEGER NOT NULL REFERENCES tb_benchmark_suite(pk_suite),

    fk_framework INTEGER NOT NULL REFERENCES tb_framework(pk_framework),
    fk_workload INTEGER NOT NULL REFERENCES tb_workload(pk_workload),

    -- Change metrics
    rps_change NUMERIC(5,2),                   -- Percentage change
    latency_change NUMERIC(5,2),
    cost_change NUMERIC(5,2),
    efficiency_change NUMERIC(5,2),

    -- Regression detection
    is_regression BOOLEAN,
    regression_severity VARCHAR(50),           -- "minor", "moderate", "severe"

    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## FraiseQL Type Definitions

### Core Types

```python
# Framework Definition
@fraiseql.type(sql_source="benchmark.tv_framework")
class Framework:
    id: str                              # UUID
    name: str
    language: str
    language_family: str
    runtime: str
    version: str
    repository_url: str | None

    # Nested relationships
    @fraiseql.field
    async def benchmark_runs(
        self,
        info: GraphQLResolveInfo,
        suite_id: str | None = None,
        limit: int = 50
    ) -> list["BenchmarkRun"]:
        """All benchmark runs for this framework."""
        ...

    @fraiseql.field
    async def latest_analysis(
        self,
        info: GraphQLResolveInfo,
        suite_id: str | None = None
    ) -> "CostAnalysisResult" | None:
        """Most recent cost analysis."""
        ...

    @fraiseql.field
    async def metadata(self, info: GraphQLResolveInfo) -> dict[str, any]:
        """Language, paradigm, and feature metadata."""
        ...

# Benchmark Metadata
@fraiseql.type
class FrameworkMetadata:
    type_safety: str                    # "none", "partial", "full"
    paradigm: str                       # "OO", "functional", "hybrid"
    concurrency_model: str
    garbage_collection: bool
    startup_time_ms: int
    cold_start_penalty_ms: int
    language_expressiveness: int        # 1-10
    learning_curve: int                 # 1-10
    ecosystem_size: int                 # 1-10
    maturity_years: int

# Benchmark Suite
@fraiseql.type(sql_source="benchmark.tv_benchmark_suite")
class BenchmarkSuite:
    id: str
    name: str
    description: str | None
    version: str
    created_at: str

    @fraiseql.field
    async def workloads(
        self,
        info: GraphQLResolveInfo,
        limit: int = 50
    ) -> list["Workload"]:
        """Workloads in this suite."""
        ...

# Workload Definition
@fraiseql.type(sql_source="benchmark.tv_workload")
class Workload:
    id: str
    name: str
    description: str | None
    query_complexity: str               # "simple", "moderate", "complex"
    operation_count: int | None
    estimated_join_depth: int | None

# Load Profile
@fraiseql.type(sql_source="benchmark.tv_load_profile")
class LoadProfile:
    id: str
    name: str                           # "smoke", "small", "medium", "large", "production"
    rps: int
    duration_seconds: int
    warmup_seconds: int
    threads: int

# Benchmark Run
@fraiseql.type(sql_source="benchmark.tv_benchmark_run")
class BenchmarkRun:
    id: str
    framework: Framework                # Pre-composed
    suite: BenchmarkSuite               # Pre-composed
    workload: Workload                  # Pre-composed
    load_profile: LoadProfile           # Pre-composed

    status: str                         # "running", "completed", "failed"
    start_time: str
    end_time: str | None
    duration_seconds: int | None

    @fraiseql.field
    async def metrics(
        self,
        info: GraphQLResolveInfo
    ) -> "PerformanceMetrics":
        """Performance metrics from JMeter results."""
        ...

    @fraiseql.field
    async def resource_profile(
        self,
        info: GraphQLResolveInfo
    ) -> "ResourceProfile":
        """Calculated infrastructure requirements."""
        ...

    @fraiseql.field
    async def cost_analysis(
        self,
        info: GraphQLResolveInfo
    ) -> "CostAnalysisResult":
        """Cost analysis across cloud providers."""
        ...

    @fraiseql.field
    async def efficiency_ranking(
        self,
        info: GraphQLResolveInfo
    ) -> "EfficiencyRanking":
        """Efficiency score and ranking."""
        ...

# Performance Metrics
@fraiseql.type(sql_source="benchmark.tv_performance_metrics")
class PerformanceMetrics:
    total_requests: int
    total_errors: int
    error_rate: float
    requests_per_second: float

    # Latency distribution
    latency_min: int
    latency_p50: int
    latency_p95: int
    latency_p99: int
    latency_p999: int
    latency_max: int
    latency_mean: int
    latency_stddev: int

    # Response size
    response_bytes_min: int
    response_bytes_mean: int
    response_bytes_max: int

    # Connection metrics
    connect_time_mean: int
    idle_time_mean: int
    server_processing_mean: int

    @fraiseql.field
    async def latency_percentiles(
        self,
        info: GraphQLResolveInfo
    ) -> list["LatencyPercentile"]:
        """Detailed latency percentiles (p1, p5, p10, p25, p50, p75, p90, p95, p99)."""
        ...

@fraiseql.type(sql_source="benchmark.tv_performance_percentiles")
class LatencyPercentile:
    percentile: int
    latency_ms: int

# Resource Profile
@fraiseql.type(sql_source="benchmark.tv_resource_profile")
class ResourceProfile:
    cpu_cores_required: int
    cpu_cores_with_headroom: int
    headroom_percent: float
    rps_per_core: int

    application_baseline_mb: int
    connection_pool_memory_mb: int
    memory_required_gb: float

    application_storage_gb: float
    data_growth_gb_per_month: float
    log_storage_gb_per_month: float

    bandwidth_mbps: float
    data_transfer_gb_per_month: float

    total_monthly_storage_gb: float

# Cost Analysis Result (Composition of breakdown + ranking)
@fraiseql.type(sql_source="benchmark.tv_cost_analysis")
class CostAnalysisResult:
    recommended_cloud_provider: str     # "aws", "gcp", "azure"
    recommended_instance_type: str

    @fraiseql.field
    async def cost_breakdown(
        self,
        info: GraphQLResolveInfo
    ) -> list["CloudCostBreakdown"]:
        """Cost breakdown for each cloud provider."""
        ...

    @fraiseql.field
    async def cheapest_provider(
        self,
        info: GraphQLResolveInfo
    ) -> "CloudCostBreakdown":
        """Cheapest option among AWS, GCP, Azure."""
        ...

# Cloud Cost Breakdown
@fraiseql.type(sql_source="benchmark.tv_cost_breakdown")
class CloudCostBreakdown:
    cloud_provider: str

    compute_cost: float
    database_cost: float
    storage_cost: float
    data_transfer_cost: float
    monitoring_cost: float
    contingency_cost: float

    total_monthly_cost: float
    total_yearly_cost: float
    yearly_with_1yr_reserved: float     # 40% discount
    yearly_with_3yr_reserved: float     # 55% discount

    cost_per_request: float
    requests_per_dollar: int

    instance_type: str
    instance_hourly_rate: float

# Efficiency Ranking
@fraiseql.type(sql_source="benchmark.tv_efficiency_ranking")
class EfficiencyRanking:
    efficiency_score: float             # 0-10
    cost_component: float
    latency_component: float
    throughput_component: float
    reliability_component: float

    suite_rank: int
    rank_tie_breaker: str
```

### Query Types

```python
@fraiseql.type
class Query:
    # Framework queries
    @fraiseql.field
    async def framework(
        self,
        info: GraphQLResolveInfo,
        id: str | None = None,
        name: str | None = None
    ) -> Framework | None:
        """Get single framework by ID or name."""
        ...

    @fraiseql.field
    async def frameworks(
        self,
        info: GraphQLResolveInfo,
        language: str | None = None,
        language_family: str | None = None,
        limit: int = 50,
        offset: int = 0
    ) -> list[Framework]:
        """List frameworks with optional filtering."""
        ...

    # Benchmark run queries
    @fraiseql.field
    async def benchmark_run(
        self,
        info: GraphQLResolveInfo,
        id: str
    ) -> BenchmarkRun | None:
        """Get single benchmark run by ID."""
        ...

    @fraiseql.field
    async def benchmark_runs(
        self,
        info: GraphQLResolveInfo,
        suite_id: str,
        framework_id: str | None = None,
        workload_id: str | None = None,
        status: str | None = None,
        limit: int = 50
    ) -> list[BenchmarkRun]:
        """Query benchmark runs with filtering."""
        ...

    # Comparison & Analysis Queries
    @fraiseql.field
    async def framework_comparison(
        self,
        info: GraphQLResolveInfo,
        suite_id: str,
        workload_id: str | None = None,
        load_profile: str = "small",
        rank_by: str = "efficiency"  # "efficiency", "cost", "latency"
    ) -> "FrameworkComparison":
        """Compare frameworks across different axes."""
        ...

    @fraiseql.field
    async def cost_comparison(
        self,
        info: GraphQLResolveInfo,
        suite_id: str,
        framework_id: str | None = None,
        load_profile: str = "small"
    ) -> "CostComparison":
        """Compare costs across cloud providers and frameworks."""
        ...

    @fraiseql.field
    async def performance_trend(
        self,
        info: GraphQLResolveInfo,
        framework_id: str,
        workload_id: str | None = None,
        days: int = 30
    ) -> list["PerformanceTrend"]:
        """Performance trend over time."""
        ...

# Comparison Result Types
@fraiseql.type
class FrameworkComparison:
    suite: BenchmarkSuite
    frameworks: list["FrameworkComparisonRow"]
    most_efficient: Framework
    fastest: Framework
    cheapest_to_run: Framework
    best_for_simple_loads: Framework

@fraiseql.type
class FrameworkComparisonRow:
    framework: Framework
    metrics: PerformanceMetrics
    resources: ResourceProfile
    cost_analysis: CostAnalysisResult
    efficiency_ranking: EfficiencyRanking

@fraiseql.type
class CostComparison:
    frameworks: list[Framework]
    load_profile: LoadProfile
    cloud_providers: list["ProviderCostSummary"]
    total_cost_difference_percent: float
    recommended_provider: str

@fraiseql.type
class ProviderCostSummary:
    provider: str
    average_monthly_cost: float
    average_yearly_cost: float
    cheapest_framework: Framework
    most_expensive_framework: Framework

@fraiseql.type
class PerformanceTrend:
    timestamp: str
    rps: float
    latency_p95: int
    latency_p99: int
    efficiency_score: float
```

### Mutation Types

```python
@fraiseql.input
class RunBenchmarkInput:
    framework_id: str
    suite_id: str
    workload_id: str
    load_profile: str

@fraiseql.success
class RunBenchmarkSuccess:
    benchmark_run: BenchmarkRun
    # Auto-injected: status="success", message

@fraiseql.error
class RunBenchmarkError:
    reason: str
    # Auto-injected: status="error", message, errors

@fraiseql.mutation
class RunBenchmark:
    input: RunBenchmarkInput
    success: RunBenchmarkSuccess
    error: RunBenchmarkError

@fraiseql.input
class AnalyzeCostInput:
    benchmark_run_id: str
    include_reserved_instances: bool = True

@fraiseql.success
class AnalyzeCostSuccess:
    cost_analysis: CostAnalysisResult
    resource_profile: ResourceProfile

@fraiseql.error
class AnalyzeCostError:
    reason: str

@fraiseql.mutation
class AnalyzeCost:
    input: AnalyzeCostInput
    success: AnalyzeCostSuccess
    error: AnalyzeCostError
```

---

## Composition Views (Zero N+1 Queries)

### tv_benchmark_run
Pre-composes framework, suite, workload, and load profile data:

```sql
CREATE VIEW tv_benchmark_run AS
SELECT
    r.id,
    r.status,
    r.start_time,
    r.end_time,
    r.duration_seconds,

    -- Framework (pre-composed)
    jsonb_build_object(
        'id', f.id,
        'name', f.name,
        'language', f.language,
        'runtime', f.runtime
    ) as framework,

    -- Suite (pre-composed)
    jsonb_build_object(
        'id', s.id,
        'name', s.name,
        'version', s.version
    ) as suite,

    -- Workload (pre-composed)
    jsonb_build_object(
        'id', w.id,
        'name', w.name,
        'query_complexity', w.query_complexity
    ) as workload,

    -- Load Profile (pre-composed)
    jsonb_build_object(
        'id', lp.id,
        'name', lp.name,
        'rps', lp.rps,
        'threads', lp.threads
    ) as load_profile

FROM tb_benchmark_run r
JOIN tb_framework f ON r.fk_framework = f.pk_framework
JOIN tb_benchmark_suite s ON r.fk_suite = s.pk_suite
JOIN tb_workload w ON r.fk_workload = w.pk_workload
JOIN tb_load_profile lp ON r.fk_load_profile = lp.pk_profile;
```

### tv_cost_analysis
Pre-composes cost breakdowns and efficiency ranking:

```sql
CREATE VIEW tv_cost_analysis AS
SELECT
    ca.id,
    ca.recommended_cloud_provider,
    ca.recommended_instance_type,

    -- Cost breakdown array (all 3 clouds)
    jsonb_agg(jsonb_build_object(
        'cloud_provider', cb.cloud_provider,
        'compute_cost', cb.compute_cost,
        'total_monthly_cost', cb.total_monthly_cost,
        'cost_per_request', cb.cost_per_request,
        'instance_type', cb.instance_type
    )) as cost_breakdowns,

    -- Efficiency ranking
    jsonb_build_object(
        'efficiency_score', er.efficiency_score,
        'cost_component', er.cost_component,
        'latency_component', er.latency_component,
        'suite_rank', er.suite_rank
    ) as efficiency_ranking

FROM tb_cost_analysis ca
LEFT JOIN tb_cost_breakdown cb ON ca.pk_analysis = cb.fk_analysis
LEFT JOIN tb_efficiency_ranking er ON ca.pk_analysis = er.fk_analysis
GROUP BY ca.id;
```

---

## Query Examples

### 1. Framework Comparison (All Axes)
```graphql
query FrameworkComparison($suiteId: String!, $loadProfile: String!) {
  frameworkComparison(suiteId: $suiteId, loadProfile: $loadProfile) {
    frameworks {
      name
      language
      metadata {
        typeSafety
        paradigm
        startupTimeMs
        learningCurve
      }
      metrics {
        requestsPerSecond
        latencyP95
        latencyP99
        errorRate
      }
      resources {
        cpuCoresRequired
        memoryRequiredGb
        bandwidthMbps
      }
      costAnalysis {
        costBreakdown {
          cloudProvider
          totalMonthlyCost
          costPerRequest
        }
        efficiencyRanking {
          efficiencyScore
          costComponent
          latencyComponent
          throughputComponent
        }
      }
    }
    mostEfficient { name }
    cheapestToRun { name }
  }
}
```

### 2. Cost-to-Performance Trade-off
```graphql
query CostPerformanceAnalysis($suiteId: String!) {
  benchmarkRuns(suiteId: $suiteId, limit: 100) {
    framework { name language }
    metrics { requestsPerSecond latencyP95 errorRate }
    costAnalysis {
      recommendedCloudProvider
      costBreakdown {
        cloudProvider
        totalMonthlyCost
        costPerRequest
      }
    }
    efficiencyRanking {
      efficiencyScore
      suiteRank
    }
  }
}
```

### 3. Historical Performance Trend
```graphql
query PerformanceTrend($frameworkId: String!) {
  performanceTrend(frameworkId: $frameworkId, days: 30) {
    timestamp
    rps
    latencyP95
    latencyP99
    efficiencyScore
  }
}
```

---

## Design Principles

### 1. **Normalization**
- Each fact stored once (no duplication)
- Relationships explicit via foreign keys
- Computed values stored separately (not in multiple tables)

### 2. **Trinity Pattern**
- `pk_*` INTEGER: Internal, hidden from API, optimized for joins
- `id` UUID: Public API identifier, stable across time
- `fk_*` INTEGER: Fast foreign key relationships

### 3. **Zero N+1 Queries**
- Composition views (tv_*) pre-compose related data in JSONB
- FraiseQL directly maps JSONB to nested types
- Single query returns all nested data

### 4. **Extensibility**
- `metadata` JSONB columns for framework properties
- `jmeter_results` JSONB for extensible raw data
- Easy to add new cloud providers or metrics

### 5. **Historical Analysis**
- All timestamps tracked (created_at, updated_at)
- Comparison tables for trend detection
- Immutable benchmark runs (append-only)

---

## Integration Points with Phase 1-2 Modules

### Cost Simulator Integration
```python
# Load benchmark run from database
run: BenchmarkRun = query_run(run_id)

# Calculate resources
calc = ResourceCalculator(framework_config=run.framework.metadata)
resources = calc.calculate_requirements(run.metrics.to_load_projection())

# Store in database
db.update_resource_profile(run.id, resources)

# Calculate costs
simulator = CostSimulator(config=CostConfiguration())
costs = simulator.analyze(resources, run.metrics)

# Store cost analysis
db.store_cost_analysis(run.id, costs)

# Calculate efficiency
analyzer = EfficiencyAnalyzer()
efficiency = analyzer.score(run.metrics, costs)

# Store efficiency ranking
db.store_efficiency_ranking(run.id, efficiency)
```

---

## Next Steps

This domain model enables:

1. **Phase 2**: Cost calculations populated via resolvers
2. **Phase 3**: FraiseQL schema integration with database
3. **Phase 4**: Rich GraphQL queries for comparison and analysis
4. **Frontend**: Real dashboard showing all axes of comparison

All normalized, queryable, and zero N+1 queries.
