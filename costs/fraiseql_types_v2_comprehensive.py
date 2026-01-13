"""FraiseQL Domain Types for Comprehensive VelocityBench Analytics.

Defines all FraiseQL types for complete benchmarking analytics domain.
Implements Trinity Pattern: pk (INTEGER), id (UUID), fk (INTEGER).
Uses JSONB composition views for zero N+1 queries.

60+ types organized by 8 levels:
1. Framework Implementation (10 types)
2. Benchmark Definition (8 types)
3. Test Environment (8 types)
4. Execution & Logs (4 types)
5. Performance Metrics (12 types)
6. Analysis & Derived Data (6 types)
7. Comparison & Trends (4 types)
8. Code & Reproducibility (4 types)
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================


class LanguageFamily(str, Enum):
    """Programming language family classification."""
    DYNAMIC = "dynamic"  # Python, JavaScript, Ruby
    STATIC = "static"  # Java, Go, C#
    HYBRID = "hybrid"  # TypeScript, Kotlin


class LoadProfileName(str, Enum):
    """Predefined load profiles."""
    SMOKE = "smoke"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    PRODUCTION = "production"


class BenchmarkStatus(str, Enum):
    """Benchmark run status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class QueryComplexity(str, Enum):
    """Query complexity classification."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class CloudProvider(str, Enum):
    """Cloud provider names."""
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"


class QueryPatternType(str, Enum):
    """Types of query patterns."""
    SIMPLE_QUERY = "simple_query"
    NESTED_QUERY = "nested_query"
    MUTATION = "mutation"
    AGGREGATION = "aggregation"


class ErrorType(str, Enum):
    """Error types in benchmarks."""
    TIMEOUT = "timeout"
    CONNECTION = "connection"
    APPLICATION = "application"
    SERVER_ERROR = "5xx"


class IterationType(str, Enum):
    """Benchmark iteration types."""
    WARMUP = "warmup"
    ACTUAL = "actual"
    COOLDOWN = "cooldown"


# ============================================================================
# LEVEL 1: FRAMEWORK IMPLEMENTATION (10 TYPES)
# ============================================================================


@dataclass
class DatabaseLibraryVersion:
    """Database library version history."""
    version_number: str
    release_date: Optional[datetime] = None
    is_used_in_benchmark: bool = True


@dataclass
class DatabaseLibrary:
    """Database library/ORM used."""
    name: str
    library_type: str  # ORM, query builder, raw driver
    description: Optional[str] = None
    versions: Optional[list[DatabaseLibraryVersion]] = None


@dataclass
class OptimizationTechnique:
    """Query optimization technique used."""
    technique_name: str
    technique_type: str  # batching, caching, query planning, etc.
    description: Optional[str] = None
    implementation_details: Optional[str] = None
    performance_impact_percent: Optional[float] = None


@dataclass
class CachingStrategy:
    """Caching strategy implemented."""
    strategy_type: str  # query cache, object cache, distributed cache
    cache_backend: str  # redis, memcached, in-memory
    cache_ttl_seconds: Optional[int] = None
    hit_rate_percent: Optional[float] = None
    description: Optional[str] = None


@dataclass
class GitRepository:
    """Git repository information."""
    repository_url: str
    default_branch: Optional[str] = None
    latest_commit_hash: Optional[str] = None
    latest_commit_date: Optional[datetime] = None


@dataclass
class FrameworkVersion:
    """Framework version history."""
    version_number: str
    release_date: Optional[datetime] = None
    git_commit_hash: Optional[str] = None
    description: Optional[str] = None


@dataclass
class FrameworkFile:
    """Individual source file in framework."""
    file_path: str
    file_size_bytes: Optional[int] = None
    lines_of_code: Optional[int] = None
    language: Optional[str] = None
    content_hash: Optional[str] = None
    file_content: Optional[str] = None  # Full source code
    is_critical_path: bool = False


@dataclass
class FrameworkImplementation:
    """Complete framework implementation."""
    git_repository_url: Optional[str] = None
    git_commit_hash: Optional[str] = None
    git_branch: Optional[str] = None
    git_tag: Optional[str] = None
    implementation_date: Optional[datetime] = None
    total_lines_of_code: Optional[int] = None
    total_files: Optional[int] = None
    description: Optional[str] = None
    source_files: Optional[list[FrameworkFile]] = None


@dataclass
class FrameworkMetadata:
    """Framework language and operational characteristics."""
    type_safety: Optional[str] = None  # none, partial, full
    paradigm: Optional[str] = None  # OO, functional, hybrid
    concurrency_model: Optional[str] = None  # threaded, async, async+threaded
    garbage_collection: Optional[bool] = None
    memory_management: Optional[str] = None
    startup_time_ms: Optional[int] = None
    cold_start_penalty_ms: Optional[int] = None
    language_expressiveness: Optional[int] = None  # 1-10
    learning_curve: Optional[int] = None  # 1-10
    ecosystem_size: Optional[int] = None  # 1-10
    maturity_years: Optional[int] = None


@dataclass
class Framework:
    """Framework definition with full metadata."""
    id: str  # UUID
    name: str
    language: str
    language_family: str
    runtime: str
    version: str
    repository_url: Optional[str] = None
    documentation_url: Optional[str] = None
    metadata: Optional[FrameworkMetadata] = None
    implementation: Optional[FrameworkImplementation] = None
    database_library: Optional[DatabaseLibrary] = None
    optimization_techniques: Optional[list[OptimizationTechnique]] = None
    caching_strategies: Optional[list[CachingStrategy]] = None
    git_repository: Optional[GitRepository] = None
    versions: Optional[list[FrameworkVersion]] = None


# ============================================================================
# LEVEL 2: BENCHMARK DEFINITION (8 TYPES)
# ============================================================================


@dataclass
class QueryPatternFile:
    """Query pattern source file."""
    query_string: str
    query_structure: Optional[str] = None  # GraphQL structure for reference
    test_data_size: Optional[int] = None  # number of records queried
    is_parameterized: bool = False
    parameters: Optional[dict[str, Any]] = None  # JSON of test parameters


@dataclass
class QueryPatternComplexity:
    """Query pattern complexity metrics."""
    join_depth: Optional[int] = None
    field_count: Optional[int] = None
    subquery_count: Optional[int] = None
    filter_count: Optional[int] = None
    sort_count: Optional[int] = None
    computed_complexity_score: Optional[float] = None


@dataclass
class QueryPattern:
    """Query pattern definition."""
    id: str  # UUID
    pattern_name: str
    pattern_type: str  # simple_query, nested_query, mutation, aggregation
    complexity: str  # simple, moderate, complex
    description: Optional[str] = None
    expected_execution_ms: Optional[int] = None
    query_file: Optional[QueryPatternFile] = None
    complexity_metrics: Optional[QueryPatternComplexity] = None


@dataclass
class LoadProfileRamp:
    """Load profile ramp-up phase."""
    phase_number: int
    start_rps: Optional[int] = None
    end_rps: Optional[int] = None
    duration_seconds: Optional[int] = None


@dataclass
class LoadProfile:
    """Predefined load profile for testing."""
    id: str  # UUID
    name: str
    rps: int
    duration_seconds: int
    warmup_seconds: int
    threads: int
    ramp_up_time_seconds: Optional[int] = None
    think_time_ms: Optional[int] = None
    ramp_phases: Optional[list[LoadProfileRamp]] = None


@dataclass
class BenchmarkSchema:
    """Benchmark schema definition."""
    schema_version: Optional[str] = None
    total_tables: Optional[int] = None
    total_records: Optional[int] = None
    schema_size_mb: Optional[float] = None
    schema_definition: Optional[str] = None  # DDL statements


@dataclass
class Workload:
    """Query workload type with complexity."""
    id: str  # UUID
    name: str
    query_complexity: str  # simple, moderate, complex
    description: Optional[str] = None
    operation_count: Optional[int] = None
    estimated_join_depth: Optional[int] = None


@dataclass
class BenchmarkSuite:
    """Collection of benchmarks for comparison."""
    id: str  # UUID
    name: str
    version: str
    description: Optional[str] = None
    created_by: Optional[str] = None
    baseline_framework_id: Optional[str] = None
    workloads: Optional[list[Workload]] = None
    query_patterns: Optional[list[QueryPattern]] = None
    schema: Optional[BenchmarkSchema] = None


# ============================================================================
# LEVEL 3: TEST ENVIRONMENT (8 TYPES)
# ============================================================================


@dataclass
class TestMachineCPU:
    """CPU details."""
    cpu_flags: Optional[str] = None
    turbo_boost_enabled: Optional[bool] = None
    hyper_threading_enabled: Optional[bool] = None
    max_frequency_mhz: Optional[int] = None
    cache_l1_kb: Optional[int] = None
    cache_l2_kb: Optional[int] = None
    cache_l3_mb: Optional[int] = None


@dataclass
class TestMachineMemory:
    """Memory configuration."""
    total_memory_gb: Optional[int] = None
    available_memory_gb: Optional[int] = None
    memory_speed_mhz: Optional[int] = None
    ecc_enabled: Optional[bool] = None
    numa_nodes: Optional[int] = None


@dataclass
class TestMachine:
    """Hardware specifications."""
    id: str  # UUID
    machine_name: Optional[str] = None
    cpu_model: str
    cpu_cores: int
    cpu_threads: int
    cpu_base_ghz: Optional[float] = None
    cpu_boost_ghz: Optional[float] = None
    ram_gb: int
    ram_type: Optional[str] = None  # DDR4, DDR5
    storage_type: Optional[str] = None  # SSD, HDD, NVMe
    storage_size_gb: Optional[int] = None
    os_name: str
    os_version: Optional[str] = None
    kernel_version: Optional[str] = None
    cpu_details: Optional[TestMachineCPU] = None
    memory_details: Optional[TestMachineMemory] = None


@dataclass
class DatabaseConfiguration:
    """Database configuration setting."""
    config_key: str
    config_value: Optional[str] = None
    data_type: Optional[str] = None


@dataclass
class DatabaseInstance:
    """Database instance configuration."""
    id: str  # UUID
    database_engine: str  # PostgreSQL, MySQL, etc.
    engine_version: Optional[str] = None
    instance_class: Optional[str] = None
    max_connections: Optional[int] = None
    shared_buffers_mb: Optional[int] = None
    effective_cache_size_mb: Optional[int] = None
    configurations: Optional[list[DatabaseConfiguration]] = None


@dataclass
class ExternalDependency:
    """External service dependency."""
    dependency_type: str  # Redis, Memcached, Elasticsearch
    dependency_version: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    is_local: Optional[bool] = None
    memory_limit_mb: Optional[int] = None


@dataclass
class JMeterConfiguration:
    """JMeter test configuration."""
    jmeter_version: Optional[str] = None
    heap_size_mb: Optional[int] = None
    gc_settings: Optional[str] = None  # JVM GC parameters
    connection_timeout_ms: Optional[int] = None
    read_timeout_ms: Optional[int] = None
    socket_timeout_ms: Optional[int] = None
    max_pool_size: Optional[int] = None


@dataclass
class TestEnvironment:
    """Complete test environment."""
    test_machine: Optional[TestMachine] = None
    database_instance: Optional[DatabaseInstance] = None
    external_dependencies: Optional[list[ExternalDependency]] = None
    jmeter_config: Optional[JMeterConfiguration] = None
    environment_variables: Optional[dict[str, str]] = None


# ============================================================================
# LEVEL 4: EXECUTION & LOGS (4 TYPES)
# ============================================================================


@dataclass
class RunIteration:
    """Single iteration of benchmark run."""
    iteration_number: int
    iteration_type: str  # warmup, actual, cooldown
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    request_count: Optional[int] = None


@dataclass
class ExecutionLog:
    """Execution event log."""
    log_time: Optional[datetime] = None
    log_level: str  # INFO, WARNING, ERROR
    log_message: str
    stacktrace: Optional[str] = None


# ============================================================================
# LEVEL 5: PERFORMANCE METRICS (12 TYPES)
# ============================================================================


@dataclass
class LatencyPercentile:
    """Latency at specific percentile."""
    percentile: int  # 1, 5, 10, 25, 50, 75, 90, 95, 99
    latency_ms: int


@dataclass
class LatencyHistogramBucket:
    """Latency histogram bucket."""
    bucket_start_ms: int
    bucket_end_ms: int
    request_count: int


@dataclass
class LatencyDistribution:
    """Complete latency distribution."""
    percentiles: Optional[list[LatencyPercentile]] = None
    histogram: Optional[list[LatencyHistogramBucket]] = None


@dataclass
class ErrorBreakdown:
    """Error metrics breakdown."""
    total_errors: int
    error_type: Optional[str] = None  # timeout, connection, 5xx
    error_code: Optional[str] = None
    error_count: Optional[int] = None
    error_percentage: Optional[float] = None


@dataclass
class ResourceUsage:
    """Resource usage metrics."""
    peak_cpu_percent: Optional[float] = None
    avg_cpu_percent: Optional[float] = None
    peak_memory_mb: Optional[int] = None
    avg_memory_mb: Optional[int] = None
    gc_pause_count: Optional[int] = None
    gc_pause_time_ms: Optional[int] = None
    gc_full_pause_count: Optional[int] = None
    gc_full_pause_time_ms: Optional[int] = None


@dataclass
class TimeBreakdown:
    """Time breakdown (network vs server vs client)."""
    connect_time_mean: Optional[int] = None
    connect_time_max: Optional[int] = None
    connect_time_min: Optional[int] = None
    idle_time_mean: Optional[int] = None
    idle_time_max: Optional[int] = None
    latency_mean: Optional[int] = None  # server processing
    latency_max: Optional[int] = None
    latency_min: Optional[int] = None
    total_latency_mean: Optional[int] = None


@dataclass
class ResponseSizeMetrics:
    """Response size metrics."""
    response_bytes_min: Optional[int] = None
    response_bytes_max: Optional[int] = None
    response_bytes_mean: Optional[int] = None
    response_bytes_median: Optional[int] = None
    response_bytes_stddev: Optional[int] = None
    response_bytes_p95: Optional[int] = None
    response_bytes_p99: Optional[int] = None


@dataclass
class ThroughputMetrics:
    """Throughput metrics."""
    requests_per_second: float
    bytes_per_second: Optional[float] = None
    active_connections_max: Optional[int] = None
    active_connections_avg: Optional[int] = None
    idle_connections: Optional[int] = None
    connection_timeouts: Optional[int] = None


@dataclass
class QueryExecutionDetail:
    """Per-query execution details."""
    query_pattern: Optional[str] = None
    query_count: Optional[int] = None
    avg_execution_ms: Optional[float] = None
    p95_execution_ms: Optional[float] = None
    p99_execution_ms: Optional[float] = None
    max_execution_ms: Optional[float] = None
    error_count: Optional[int] = None


@dataclass
class RequestMetricSample:
    """Individual request metric (sampled)."""
    request_number: Optional[int] = None
    request_time: Optional[datetime] = None
    latency_ms: int
    response_bytes: Optional[int] = None
    response_code: str
    connect_time_ms: Optional[int] = None
    idle_time_ms: Optional[int] = None
    processing_time_ms: Optional[int] = None
    success: bool


@dataclass
class PerformanceMetrics:
    """Complete performance metrics."""
    total_requests: int
    total_errors: int
    error_rate: float  # Percentage 0-100
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
    response_bytes_min: Optional[int] = None
    response_bytes_mean: Optional[int] = None
    response_bytes_max: Optional[int] = None

    # Connection metrics
    connect_time_mean: Optional[int] = None
    idle_time_mean: Optional[int] = None
    server_processing_mean: Optional[int] = None

    # Detailed breakdowns
    latency_distribution: Optional[LatencyDistribution] = None
    error_breakdown: Optional[list[ErrorBreakdown]] = None
    resource_usage: Optional[ResourceUsage] = None
    time_breakdown: Optional[TimeBreakdown] = None
    response_size_metrics: Optional[ResponseSizeMetrics] = None
    throughput_metrics: Optional[ThroughputMetrics] = None
    query_execution_details: Optional[list[QueryExecutionDetail]] = None
    request_samples: Optional[list[RequestMetricSample]] = None


# ============================================================================
# LEVEL 6: ANALYSIS & DERIVED DATA (6 TYPES)
# ============================================================================


@dataclass
class ResourceProfile:
    """Infrastructure resource requirements."""
    # CPU
    cpu_cores_required: int
    cpu_cores_with_headroom: int
    headroom_percent: float
    rps_per_core: Optional[int] = None

    # Memory
    application_baseline_mb: Optional[int] = None
    connection_pool_memory_mb: Optional[int] = None
    memory_buffer_percent: float = 20.0
    memory_required_gb: float

    # Storage
    application_storage_gb: float
    data_growth_gb_per_month: float
    log_storage_gb_per_month: float

    # Network
    bandwidth_mbps: float
    data_transfer_gb_per_month: float

    # Total
    total_monthly_storage_gb: float


@dataclass
class CloudCostBreakdown:
    """Cost breakdown for single cloud provider."""
    cloud_provider: str  # aws, gcp, azure

    # Monthly costs (USD)
    compute_cost: float
    database_cost: float
    storage_cost: float
    data_transfer_cost: float
    monitoring_cost: float
    contingency_cost: float
    total_monthly_cost: float

    # Yearly projections
    total_yearly_cost: float
    yearly_with_1yr_reserved: float  # 40% discount
    yearly_with_3yr_reserved: float  # 55% discount

    # Per-request metrics
    cost_per_request: float
    requests_per_dollar: int

    # Instance details
    instance_type: str
    instance_hourly_rate: float


@dataclass
class EfficiencyRanking:
    """Efficiency score and ranking."""
    efficiency_score: float  # 0-10
    cost_component: float
    latency_component: float
    throughput_component: float
    reliability_component: float

    suite_rank: int
    rank_tie_breaker: Optional[str] = None  # cost, latency, throughput


@dataclass
class CostAnalysisResult:
    """Complete cost analysis for benchmark."""
    recommended_cloud_provider: str
    recommended_instance_type: str
    cost_breakdowns: Optional[list[CloudCostBreakdown]] = None
    efficiency_ranking: Optional[EfficiencyRanking] = None


@dataclass
class PerformanceCharacterization:
    """Performance characterization patterns."""
    scales_linearly_to: Optional[int] = None  # RPS
    optimal_connections: Optional[int] = None
    gc_friendly: Optional[bool] = None
    cache_friendly: Optional[bool] = None
    memory_efficient: Optional[bool] = None
    cpu_efficient: Optional[bool] = None
    bottleneck_type: Optional[str] = None  # CPU, memory, IO, GC
    bottleneck_description: Optional[str] = None


@dataclass
class RegressionDetection:
    """Regression detection results."""
    is_regression: bool = False
    regression_severity: Optional[str] = None  # minor, moderate, severe
    latency_change_percent: Optional[float] = None
    throughput_change_percent: Optional[float] = None
    error_rate_change_percent: Optional[float] = None


# ============================================================================
# LEVEL 7: COMPARISON & TRENDS (4 TYPES)
# ============================================================================


@dataclass
class PerformanceTrend:
    """Performance trend data point."""
    timestamp: datetime
    rps: float
    latency_p95: int
    latency_p99: int
    efficiency_score: float
    cost_per_request: Optional[float] = None


@dataclass
class RecommendationScenario:
    """Use case recommendation."""
    id: str  # UUID
    scenario_name: str
    scenario_description: Optional[str] = None
    target_use_case: Optional[str] = None
    recommended_framework: Optional[Framework] = None
    reasoning: Optional[str] = None
    trade_offs: Optional[str] = None


@dataclass
class FrameworkComparisonRow:
    """Single framework in a comparison."""
    framework: Framework
    metrics: PerformanceMetrics
    resources: ResourceProfile
    cost_analysis: CostAnalysisResult
    efficiency_ranking: EfficiencyRanking


@dataclass
class FrameworkComparison:
    """Framework comparison results."""
    suite: BenchmarkSuite
    load_profile: LoadProfile
    workload: Workload
    frameworks: list[FrameworkComparisonRow]

    # Highlights
    most_efficient: Optional[Framework] = None
    fastest: Optional[Framework] = None
    cheapest_to_run: Optional[Framework] = None

    # Statistics
    average_cost_monthly: Optional[float] = None
    cost_variance: Optional[float] = None


# ============================================================================
# LEVEL 8: CODE & REPRODUCIBILITY (4 TYPES)
# ============================================================================


@dataclass
class CodeFileSnapshot:
    """Code file snapshot."""
    file_path: str
    file_content_hash: Optional[str] = None
    lines_of_code: Optional[int] = None


@dataclass
class CodeSnapshot:
    """Framework code snapshot at time of benchmark."""
    snapshot_type: str  # framework, database_library, optimization
    git_commit_hash: Optional[str] = None
    git_branch: Optional[str] = None
    snapshot_timestamp: datetime
    content_hash: Optional[str] = None
    files: Optional[list[CodeFileSnapshot]] = None


@dataclass
class QuerySnapshot:
    """Query code snapshot."""
    query_content_hash: Optional[str] = None
    snapshot_timestamp: datetime
    git_commit_hash: Optional[str] = None


@dataclass
class ReproducibilityManifest:
    """Complete reproducibility manifest for benchmark run."""
    manifest_data: dict[str, Any]  # Complete run specification
    manifest_version: str
    checksum: Optional[str] = None


# ============================================================================
# BENCHMARK RUN (AGGREGATES ALL DATA)
# ============================================================================


@dataclass
class BenchmarkRun:
    """Single benchmark execution for a framework."""
    id: str  # UUID
    status: str  # pending, running, completed, failed
    start_time: str  # ISO 8601 datetime
    end_time: Optional[str] = None
    duration_seconds: Optional[int] = None
    jmeter_file_path: Optional[str] = None

    # Pre-composed relations (from composition view)
    framework: Optional[Framework] = None
    suite: Optional[BenchmarkSuite] = None
    workload: Optional[Workload] = None
    load_profile: Optional[LoadProfile] = None
    test_machine: Optional[TestMachine] = None
    database_instance: Optional[DatabaseInstance] = None

    # Nested data (from resolvers)
    metrics: Optional[PerformanceMetrics] = None
    resource_profile: Optional[ResourceProfile] = None
    cost_analysis: Optional[CostAnalysisResult] = None
    efficiency_ranking: Optional[EfficiencyRanking] = None
    performance_characterization: Optional[PerformanceCharacterization] = None
    regression_detection: Optional[RegressionDetection] = None

    # Additional context
    iterations: Optional[list[RunIteration]] = None
    execution_logs: Optional[list[ExecutionLog]] = None
    code_snapshots: Optional[list[CodeSnapshot]] = None
    reproducibility_manifest: Optional[ReproducibilityManifest] = None


# ============================================================================
# ROOT QUERY TYPE
# ============================================================================


@dataclass
class Query:
    """Root GraphQL query type for comprehensive analytics."""

    # Framework queries
    async def framework(
        self,
        id: str | None = None,
        name: str | None = None,
    ) -> Framework | None:
        """Get single framework by ID or name."""
        ...

    async def frameworks(
        self,
        language: str | None = None,
        language_family: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Framework]:
        """List frameworks with optional filtering."""
        ...

    # Benchmark run queries
    async def benchmark_run(self, id: str) -> BenchmarkRun | None:
        """Get single benchmark run by ID."""
        ...

    async def benchmark_runs(
        self,
        suite_id: str,
        framework_id: str | None = None,
        workload_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[BenchmarkRun]:
        """Query benchmark runs with filtering."""
        ...

    # Comparison queries
    async def framework_comparison(
        self,
        suite_id: str,
        workload_id: str | None = None,
        load_profile: str = "small",
        rank_by: str = "efficiency",
    ) -> FrameworkComparison:
        """Compare frameworks across different axes."""
        ...

    # Analytics queries
    async def performance_trend(
        self,
        framework_id: str,
        workload_id: str | None = None,
        days: int = 30,
    ) -> list[PerformanceTrend]:
        """Performance trend over time."""
        ...

    async def recommendations(
        self,
        use_case: str | None = None,
    ) -> list[RecommendationScenario]:
        """Get framework recommendations for use case."""
        ...


# ============================================================================
# ROOT MUTATION TYPE
# ============================================================================


@dataclass
class RunBenchmarkInput:
    """Input for running a benchmark."""
    framework_id: str
    suite_id: str
    workload_id: str
    load_profile: str


@dataclass
class RunBenchmarkSuccess:
    """Successful benchmark run."""
    benchmark_run: BenchmarkRun


@dataclass
class RunBenchmarkError:
    """Benchmark run error."""
    reason: str


@dataclass
class RunBenchmark:
    """Mutation to run a benchmark."""
    input: RunBenchmarkInput
    success: RunBenchmarkSuccess | None
    error: RunBenchmarkError | None


@dataclass
class AnalyzeCostInput:
    """Input for cost analysis."""
    benchmark_run_id: str
    include_reserved_instances: bool = True


@dataclass
class AnalyzeCostSuccess:
    """Successful cost analysis."""
    cost_analysis: CostAnalysisResult
    resource_profile: ResourceProfile


@dataclass
class AnalyzeCostError:
    """Cost analysis error."""
    reason: str


@dataclass
class AnalyzeCost:
    """Mutation to analyze costs."""
    input: AnalyzeCostInput
    success: AnalyzeCostSuccess | None
    error: AnalyzeCostError | None


@dataclass
class Mutation:
    """Root GraphQL mutation type."""

    async def run_benchmark(self, input: RunBenchmarkInput) -> RunBenchmark:
        """Run a benchmark for a framework."""
        ...

    async def analyze_cost(self, input: AnalyzeCostInput) -> AnalyzeCost:
        """Analyze costs for a benchmark run."""
        ...
