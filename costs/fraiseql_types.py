"""FraiseQL Domain Types for Benchmark Analytics.

Defines all FraiseQL types for the independent benchmarking and cost analysis domain.
Implements Trinity Pattern: pk (INTEGER), id (UUID), fk (INTEGER).
Uses JSONB composition views for zero N+1 queries.
"""

from dataclasses import dataclass
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


# ============================================================================
# LEVEL 1: FRAMEWORK DEFINITION
# ============================================================================


@dataclass
class FrameworkMetadata:
    """Framework language and operational characteristics."""

    type_safety: str  # "none", "partial", "full"
    paradigm: str  # "OO", "functional", "hybrid"
    concurrency_model: str  # "threaded", "async", "async+threaded"
    garbage_collection: bool
    memory_management: str
    startup_time_ms: int
    cold_start_penalty_ms: int
    language_expressiveness: int  # 1-10
    learning_curve: int  # 1-10
    ecosystem_size: int  # 1-10
    maturity_years: int


@dataclass
class Framework:
    """Framework definition with metadata."""

    id: str  # UUID
    name: str
    language: str
    language_family: str
    runtime: str
    version: str
    repository_url: str | None = None
    documentation_url: str | None = None
    metadata: FrameworkMetadata | None = None

    # Relations (populated by resolvers)
    benchmark_runs: list["BenchmarkRun"] | None = None
    latest_analysis: "CostAnalysisResult" | None = None


# ============================================================================
# LEVEL 2: BENCHMARK DEFINITION
# ============================================================================


@dataclass
class BenchmarkSuite:
    """Collection of benchmarks for comparison."""

    id: str  # UUID
    name: str
    version: str
    description: str | None = None
    created_by: str | None = None
    baseline_framework_id: str | None = None

    # Relations
    workloads: list["Workload"] | None = None


@dataclass
class Workload:
    """Query workload type with complexity."""

    id: str  # UUID
    name: str
    query_complexity: str  # "simple", "moderate", "complex"
    description: str | None = None
    operation_count: int | None = None
    estimated_join_depth: int | None = None


@dataclass
class LoadProfile:
    """Predefined load profile for testing."""

    id: str  # UUID
    name: str
    rps: int
    duration_seconds: int
    warmup_seconds: int
    threads: int
    ramp_up_time_seconds: int | None = None
    think_time_ms: int | None = None


# ============================================================================
# LEVEL 3: BENCHMARK EXECUTION
# ============================================================================


@dataclass
class BenchmarkRun:
    """Single benchmark execution for a framework."""

    id: str  # UUID
    status: str  # "pending", "running", "completed", "failed"
    start_time: str  # ISO 8601 datetime
    end_time: str | None = None
    duration_seconds: int | None = None
    jmeter_file_path: str | None = None

    # Pre-composed relations (from tv_benchmark_run view)
    framework: Framework | None = None
    suite: BenchmarkSuite | None = None
    workload: Workload | None = None
    load_profile: LoadProfile | None = None

    # Nested data (from resolvers)
    metrics: "PerformanceMetrics | None" = None
    resource_profile: "ResourceProfile | None" = None
    cost_analysis: "CostAnalysisResult | None" = None
    efficiency_ranking: "EfficiencyRanking | None" = None


# ============================================================================
# LEVEL 4: PERFORMANCE METRICS
# ============================================================================


@dataclass
class LatencyPercentile:
    """Latency at specific percentile."""

    percentile: int  # 1, 5, 10, 25, 50, 75, 90, 95, 99
    latency_ms: int


@dataclass
class PerformanceMetrics:
    """Performance metrics from JMeter results."""

    total_requests: int
    total_errors: int
    error_rate: float  # Percentage 0-100
    requests_per_second: float

    # Latency distribution (milliseconds)
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

    # Percentile details
    percentiles: list[LatencyPercentile] | None = None


# ============================================================================
# LEVEL 5: INFRASTRUCTURE & RESOURCES
# ============================================================================


@dataclass
class ResourceProfile:
    """Infrastructure resource requirements."""

    # CPU
    cpu_cores_required: int
    cpu_cores_with_headroom: int
    headroom_percent: float
    rps_per_core: int

    # Memory
    application_baseline_mb: int
    connection_pool_memory_mb: int
    memory_buffer_percent: float
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


# ============================================================================
# LEVEL 6: COST ANALYSIS
# ============================================================================


@dataclass
class CloudCostBreakdown:
    """Cost breakdown for single cloud provider."""

    cloud_provider: str  # "aws", "gcp", "azure"

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
class CostAnalysisResult:
    """Complete cost analysis for a benchmark run."""

    recommended_cloud_provider: str  # "aws", "gcp", "azure"
    recommended_instance_type: str

    # Cost breakdowns for all providers
    cost_breakdowns: list[CloudCostBreakdown] | None = None

    # Efficiency ranking
    efficiency_ranking: "EfficiencyRanking | None" = None

    # Helpers
    def cheapest_provider(self) -> CloudCostBreakdown | None:
        """Get the cheapest cloud provider."""
        if not self.cost_breakdowns:
            return None
        return min(self.cost_breakdowns, key=lambda x: x.total_monthly_cost)

    def most_expensive_provider(self) -> CloudCostBreakdown | None:
        """Get the most expensive cloud provider."""
        if not self.cost_breakdowns:
            return None
        return max(self.cost_breakdowns, key=lambda x: x.total_monthly_cost)


# ============================================================================
# LEVEL 7: EFFICIENCY & RANKING
# ============================================================================


@dataclass
class EfficiencyRanking:
    """Efficiency score and ranking."""

    efficiency_score: float  # 0-10
    cost_component: float
    latency_component: float
    throughput_component: float
    reliability_component: float

    suite_rank: int
    rank_tie_breaker: str | None = None  # "cost", "latency", "throughput"


# ============================================================================
# AGGREGATION & COMPARISON TYPES
# ============================================================================


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
    most_efficient: Framework | None = None
    fastest: Framework | None = None
    cheapest_to_run: Framework | None = None
    best_for_simple_loads: Framework | None = None

    # Statistics
    average_cost_monthly: float | None = None
    cost_variance: float | None = None


@dataclass
class ProviderCostSummary:
    """Cost summary for cloud provider."""

    provider: str  # "aws", "gcp", "azure"
    average_monthly_cost: float
    average_yearly_cost: float
    cheapest_framework: Framework | None = None
    most_expensive_framework: Framework | None = None


@dataclass
class CostComparison:
    """Multi-cloud cost comparison."""

    load_profile: LoadProfile
    frameworks: list[Framework]
    providers: list[ProviderCostSummary]

    total_cost_difference_percent: float | None = None
    recommended_provider: str | None = None


@dataclass
class PerformanceTrend:
    """Performance trend data point."""

    timestamp: str  # ISO 8601 datetime
    rps: float
    latency_p95: int
    latency_p99: int
    efficiency_score: float
    cost_per_request: float | None = None


# ============================================================================
# BENCHMARK COMPARISON (HISTORICAL)
# ============================================================================


@dataclass
class BenchmarkComparisonResult:
    """Comparison between two benchmark suites."""

    id: str  # UUID
    framework: Framework
    workload: Workload

    # Change metrics
    rps_change: float  # Percentage
    latency_change: float  # Percentage
    cost_change: float  # Percentage
    efficiency_change: float  # Percentage

    # Regression detection
    is_regression: bool
    regression_severity: str | None = None  # "minor", "moderate", "severe"


# ============================================================================
# ROOT QUERY TYPE
# ============================================================================


@dataclass
class Query:
    """Root GraphQL query type for benchmarking analytics."""

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

    async def cost_comparison(
        self,
        suite_id: str,
        framework_id: str | None = None,
        load_profile: str = "small",
    ) -> CostComparison:
        """Compare costs across cloud providers and frameworks."""
        ...

    async def performance_trend(
        self,
        framework_id: str,
        workload_id: str | None = None,
        days: int = 30,
    ) -> list[PerformanceTrend]:
        """Performance trend over time."""
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
    # Auto-injected by FraiseQL: status="success", message


@dataclass
class RunBenchmarkError:
    """Benchmark run error."""

    reason: str
    # Auto-injected by FraiseQL: status="error", message, errors


@dataclass
class RunBenchmark:
    """Mutation to run a benchmark."""

    input: RunBenchmarkInput
    success: RunBenchmarkSuccess
    error: RunBenchmarkError


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
    # Auto-injected by FraiseQL: status="success", message


@dataclass
class AnalyzeCostError:
    """Cost analysis error."""

    reason: str
    # Auto-injected by FraiseQL: status="error", message, errors


@dataclass
class AnalyzeCost:
    """Mutation to analyze costs."""

    input: AnalyzeCostInput
    success: AnalyzeCostSuccess
    error: AnalyzeCostError


@dataclass
class Mutation:
    """Root GraphQL mutation type."""

    async def run_benchmark(self, input: RunBenchmarkInput) -> RunBenchmark:
        """Run a benchmark for a framework."""
        ...

    async def analyze_cost(self, input: AnalyzeCostInput) -> AnalyzeCost:
        """Analyze costs for a benchmark run."""
        ...
