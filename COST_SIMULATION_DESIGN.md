# VelocityBench Cost Simulation System - Design Document

**Date**: 2026-01-13
**Status**: Design Phase
**Purpose**: Provide CPU, RAM, and Storage cost analysis for each framework given load requirements

---

## Executive Summary

This design proposes a **Cost Simulation Engine** that integrates with VelocityBench's existing performance testing infrastructure to calculate infrastructure costs (CPU, RAM, storage) for each framework. It answers: **"How much would it cost to run this framework in production given these load requirements?"**

### Key Questions Answered
1. **CPU Cost**: How many CPU cores needed? What's the hourly cost?
2. **RAM Cost**: Peak memory consumption? What's the monthly cost?
3. **Storage Cost**: How much data storage per deployment? Time-series data growth?
4. **Total Cost**: Combined infrastructure cost per framework per month?
5. **Efficiency**: Which framework gives best cost-per-request?

---

## System Architecture

### Overview Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                   Cost Simulation System                      │
└──────────────────────────────────────────────────────────────┘

┌─ Input Layer ──────────────────────────────────────────────┐
│                                                              │
│  ┌─ Benchmark Metrics ─┐  ┌─ Framework Config ─┐          │
│  │ • JMeter Results    │  │ • Language/runtime  │          │
│  │ • Throughput (RPS)  │  │ • Dependencies      │          │
│  │ • Peak Latency      │  │ • Memory baseline   │          │
│  │ • Error rates       │  │ • CPU overhead      │          │
│  └─────────────────────┘  └─────────────────────┘          │
│                                                              │
│  ┌─ Resource Usage ─────┐  ┌─ Infrastructure ──┐           │
│  │ • CPU peak (%)       │  │ • Cloud providers  │           │
│  │ • Memory peak (MB)   │  │ • Instance types   │           │
│  │ • Storage (GB)       │  │ • Pricing tiers    │           │
│  │ • Network (Mbps)     │  │ • Commitment opts  │           │
│  └──────────────────────┘  └────────────────────┘           │
└────────────────────────────────────────────────────────────┘
                              ↓
┌─ Processing Layer ────────────────────────────────────────┐
│                                                             │
│  ┌─ Load Profiling Engine ─────────────────────┐          │
│  │ For each load profile (smoke/small/medium): │          │
│  │ • Calculate actual RPS (requests/second)    │          │
│  │ • Extrapolate to monthly volume (30 days)   │          │
│  │ • Project peak CPU/memory/storage needs     │          │
│  └─────────────────────────────────────────────┘          │
│                              ↓                             │
│  ┌─ Resource Requirement Calculator ───────────┐          │
│  │ Given monthly load volume:                  │          │
│  │ • CPU cores needed (with 70% headroom)      │          │
│  │ • RAM needed (with buffer)                  │          │
│  │ • Storage needed (application + data)       │          │
│  │ • Network bandwidth                         │          │
│  └─────────────────────────────────────────────┘          │
│                              ↓                             │
│  ┌─ Cloud Cost Calculator ─────────────────────┐          │
│  │ For AWS/GCP/Azure:                          │          │
│  │ • Compute: EC2/Compute Engine instance cost │          │
│  │ • Memory: RAM cost per GB-month             │          │
│  │ • Storage: Database + file storage          │          │
│  │ • Transfer: Egress/ingress costs            │          │
│  │ • Reserved instances: Discount options      │          │
│  └─────────────────────────────────────────────┘          │
│                              ↓                             │
│  ┌─ Efficiency Analysis ───────────────────────┐          │
│  │ • Cost per request ($/request)              │          │
│  │ • Cost per RPS                              │          │
│  │ • Cost-performance ranking                  │          │
│  │ • Efficiency score (0-10)                   │          │
│  └─────────────────────────────────────────────┘          │
└────────────────────────────────────────────────────────────┘
                              ↓
┌─ Output Layer ──────────────────────────────────────────┐
│                                                          │
│  ┌─ JSON Results ──────────────────────────┐           │
│  │ • cost-analysis.json per test result    │           │
│  │ • cost-comparison.json across profiles  │           │
│  │ • infrastructure-requirements.json      │           │
│  └─────────────────────────────────────────┘           │
│                                                          │
│  ┌─ Reports ───────────────────────────────┐           │
│  │ • cost-efficiency-report.html           │           │
│  │ • infrastructure-cost-breakdown.csv     │           │
│  │ • framework-comparison.xlsx             │           │
│  └─────────────────────────────────────────┘           │
│                                                          │
│  ┌─ Grafana Dashboard ──────────────────────┐          │
│  │ • Cost comparison across frameworks     │           │
│  │ • Cost per request trends               │           │
│  │ • Infrastructure requirement matrix     │           │
│  └─────────────────────────────────────────┘           │
└──────────────────────────────────────────────────────────┘
```

---

## Module Design

### 1. **cost_config.py** - Configuration & Pricing Models

**Purpose**: Define pricing for all cloud providers and resource costs

**Classes**:
```python
class CloudProvider(Enum):
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"

class CostConfiguration:
    """Load and manage pricing data"""

    def __init__(self):
        self.aws_pricing = self._load_aws_pricing()
        self.gcp_pricing = self._load_gcp_pricing()
        self.azure_pricing = self._load_azure_pricing()

    @property
    def aws_ec2_pricing(self) -> Dict[str, float]:
        """
        EC2 on-demand pricing per hour (us-east-1)
        Returns: {instance_type: hourly_cost}

        Example:
        {
            "t3.medium": 0.0416,      # 2 vCPU, 4 GB RAM
            "t3.large": 0.0832,       # 2 vCPU, 8 GB RAM
            "m5.large": 0.096,        # 2 vCPU, 8 GB RAM
            "m5.xlarge": 0.192,       # 4 vCPU, 16 GB RAM
            "c5.large": 0.085,        # 2 vCPU, 4 GB RAM
        }
        """

    @property
    def aws_rds_pricing(self) -> Dict[str, float]:
        """
        RDS PostgreSQL on-demand pricing per hour
        """

    @property
    def resource_costs(self) -> Dict[str, float]:
        """
        Cost per unit of resource

        Returns:
        {
            "cpu_per_hour": 0.0416,           # AWS t3.medium = $0.0416/hour per 2 vCPU
            "memory_per_gb_month": 7.5,        # AWS = $7.50/GB/month
            "storage_per_gb_month": 0.023,     # AWS EBS gp3 = $0.023/GB/month
            "data_transfer_per_gb": 0.02,      # AWS egress = $0.02/GB
        }
        """
```

**Data Source**: JSON configuration file with pricing tiers

```json
{
  "pricing_date": "2026-01-13",
  "aws": {
    "ec2": {
      "on_demand": {
        "t3.medium": 0.0416,
        "t3.large": 0.0832,
        "m5.large": 0.096,
        "m5.xlarge": 0.192,
        "c5.large": 0.085,
        "c5.xlarge": 0.17,
        "c5.2xlarge": 0.34
      },
      "reserved_1yr_discount": 0.40,
      "reserved_3yr_discount": 0.55
    },
    "rds": {
      "postgres": {
        "db.t3.micro": 0.0249,
        "db.t3.small": 0.0499,
        "db.t3.medium": 0.0998,
        "db.m5.large": 0.20,
        "db.m5.xlarge": 0.40
      },
      "storage_per_gb": 0.115
    },
    "s3": {
      "storage_per_gb": 0.023,
      "request_per_1k": 0.0004,
      "transfer_out_per_gb": 0.02
    }
  },
  "gcp": { ... },
  "azure": { ... }
}
```

---

### 2. **load_profiler.py** - Convert Test Metrics to Production Load

**Purpose**: Take benchmark results and extrapolate to realistic production loads

**Classes**:
```python
class LoadProfile(Enum):
    SMOKE = "smoke"          # 5 threads, 50 loops, 120s = minimal load
    SMALL = "small"          # 50 threads, real-world baseline
    MEDIUM = "medium"        # 500 threads, higher load
    LARGE = "large"          # 2000+ threads, heavy production load

class LoadProfiler:
    """
    Convert benchmark test metrics to production volume estimates
    """

    def calculate_rps_from_jmeter(self,
        results_file: Path,
        profile: LoadProfile) -> float:
        """
        Calculate requests per second from JMeter results

        Given: JMeter .jtl file with timestamp, elapsed, response_code
        Returns: RPS (float)

        Example:
        - Smoke: 5 threads × (50 requests / 120 sec) = ~2 RPS
        - Small: 50 threads × similar = ~20 RPS
        - Medium: 500 threads × similar = ~200 RPS
        """

    def project_monthly_volume(self,
        rps: float,
        hours_per_day: int = 24,
        days_per_month: int = 30,
        peak_variance: float = 2.5) -> Dict[str, int]:
        """
        Project monthly request volume from RPS

        Args:
            rps: Requests per second from benchmark
            hours_per_day: Operating hours per day (default 24)
            days_per_month: Days per month (default 30)
            peak_variance: Ratio of peak to average load (default 2.5x)

        Returns:
        {
            "rps_avg": 100,
            "rps_peak": 250,
            "requests_per_day": 8_640_000,
            "requests_per_month": 259_200_000,
        }

        Example calculation:
        - 100 RPS average × 3600 sec/hour × 24 hours × 30 days
        - = 259,200,000 requests/month
        """

    def estimate_data_growth(self,
        requests_per_month: int,
        avg_request_size_kb: float = 2.0,
        avg_response_size_kb: float = 5.0,
        replication_factor: float = 2.0) -> Dict[str, float]:
        """
        Estimate data storage growth from request volume

        Returns:
        {
            "logs_per_month_gb": 2.5,
            "database_per_month_gb": 1.2,
            "cache_per_month_gb": 0.5,
            "total_per_month_gb": 4.2,
            "total_per_year_gb": 50.4,
        }
        """
```

---

### 3. **resource_calculator.py** - Estimate Infrastructure Requirements

**Purpose**: Convert test metrics to actual resource requirements

**Classes**:
```python
class ResourceRequirements:
    """Data class for resource needs"""
    cpu_cores: int
    memory_gb: int
    storage_gb: int
    network_mbps: int
    replicas: int = 1  # For horizontal scaling

class ResourceCalculator:
    """
    Calculate actual resource requirements from benchmark metrics
    """

    def calculate_cpu_cores(self,
        rps_peak: float,
        rps_per_core: Dict[str, float],
        headroom_pct: float = 0.30) -> int:
        """
        Calculate CPU cores needed

        Args:
            rps_peak: Peak RPS from load profiling
            rps_per_core: {framework: rps_per_core} from benchmarks
            headroom_pct: Extra capacity (default 30%)

        Formula:
        cores_needed = ceil(rps_peak / rps_per_core * (1 + headroom))

        Example:
        - Peak: 250 RPS
        - Strawberry: 100 RPS/core
        - Cores: ceil(250 / 100 * 1.30) = 4 cores (with 30% headroom)
        """

    def calculate_memory(self,
        rps_peak: float,
        memory_per_connection_mb: float = 5.0,
        connection_pool_size: int = 50,
        application_baseline_mb: int = 256,
        buffer_pct: float = 0.20) -> int:
        """
        Calculate memory needed

        Formula:
        memory = app_baseline + (pool_size × memory_per_connection) + buffer

        Example:
        - App baseline: 256 MB
        - Connection pool: 50 connections × 5 MB = 250 MB
        - Buffer: 20%
        - Total: (256 + 250) × 1.20 = 606 MB ≈ 1 GB
        """

    def calculate_storage(self,
        rps_per_second: float,
        days_retention: int = 30,
        backup_copies: int = 2,
        compression_ratio: float = 0.7) -> int:
        """
        Calculate storage needed

        Includes:
        - Application code (~1 GB per container)
        - Database data
        - Transaction logs
        - Backups
        - Cache/buffers

        Formula:
        storage = code + (data_growth × days × backup_copies / compression)
        """

    def recommend_instance_type(self,
        cpu_cores: int,
        memory_gb: int,
        provider: CloudProvider = CloudProvider.AWS) -> str:
        """
        Recommend specific instance type based on requirements

        Args:
            cpu_cores: Required cores
            memory_gb: Required memory
            provider: Cloud provider (AWS/GCP/Azure)

        Returns: Instance type string (e.g., "t3.large", "m5.xlarge")

        Logic:
        1. Find all instance types matching/exceeding requirements
        2. Filter by cost-per-performance
        3. Prefer burstable instances (t3) for low traffic
        4. Prefer compute-optimized (c5) for high CPU
        5. Prefer memory-optimized (r5) for high memory
        """
```

---

### 4. **cost_calculator.py** - Calculate Cloud Costs

**Purpose**: Convert resource requirements to actual cloud costs

**Classes**:
```python
class CostBreakdown:
    """Detailed cost breakdown"""
    compute: float          # EC2 instance cost
    memory: float           # Memory-specific costs
    storage: float          # Database + file storage
    database: float         # RDS or managed database
    transfer: float         # Data egress
    monitoring: float       # Observability
    contingency: float      # 10% buffer for misc costs

    @property
    def total(self) -> float:
        """Sum of all costs"""
        return sum([
            self.compute, self.memory, self.storage,
            self.database, self.transfer, self.monitoring,
            self.contingency
        ])

class CostCalculator:
    """
    Calculate infrastructure costs for each framework
    """

    def __init__(self, config: CostConfiguration):
        self.config = config

    def calculate_compute_cost(self,
        instance_type: str,
        hours_per_month: int = 730,  # 24 × 30.42
        reserved_instance: bool = False,
        provider: CloudProvider = CloudProvider.AWS) -> float:
        """
        Calculate compute instance cost

        Args:
            instance_type: "t3.large", "m5.xlarge", etc.
            hours_per_month: Operating hours (default 730)
            reserved_instance: Use 1-year reserved pricing
            provider: Cloud provider

        Returns: Monthly cost (float)

        Formula:
        cost = hourly_rate × hours_per_month × (1 - discount if reserved)

        Example:
        - t3.large: $0.0832/hour
        - 730 hours/month × $0.0832 = $60.74/month
        - With 1-year RI (40% discount): $36.44/month
        """

    def calculate_database_cost(self,
        instance_type: str,
        storage_gb: int,
        backup_retention_days: int = 30,
        multi_az: bool = True,
        provider: CloudProvider = CloudProvider.AWS) -> float:
        """
        Calculate RDS/managed database cost

        Components:
        - Instance hourly rate
        - Storage per GB
        - Backup storage
        - Multi-AZ replication
        - IOPS (if applicable)
        """

    def calculate_storage_cost(self,
        storage_gb: int,
        monthly_requests: int,
        provider: CloudProvider = CloudProvider.AWS) -> float:
        """
        Calculate file/object storage cost (S3, GCS, Azure Blob)

        Components:
        - Storage per GB-month
        - API requests (PUT, GET, DELETE)
        - Data transfer (egress)
        """

    def calculate_total_monthly_cost(self,
        framework: str,
        rps_peak: float,
        days_retention: int = 30,
        reserved_instances: bool = False,
        multi_region: bool = False,
        provider: CloudProvider = CloudProvider.AWS) -> CostBreakdown:
        """
        Calculate complete monthly cost for a framework

        Returns: CostBreakdown with all components

        Example output:
        CostBreakdown(
            compute=60.74,
            memory=15.00,
            storage=2.30,
            database=45.00,
            transfer=1.50,
            monitoring=5.00,
            contingency=12.95,
            total=142.49  # Monthly cost
        )
        """

    def calculate_yearly_cost(self,
        cost_breakdown: CostBreakdown,
        escalation_pct: float = 0.05) -> float:
        """
        Calculate yearly cost with escalation

        Formula:
        yearly = monthly × 12 × (1 + escalation%)
        """
```

---

### 5. **efficiency_analyzer.py** - Compute Efficiency Metrics

**Purpose**: Calculate cost-performance ratios and efficiency scores

**Classes**:
```python
class EfficiencyMetrics:
    """Efficiency metrics for a framework"""
    cost_per_request_usd: float      # $/request
    cost_per_rps_monthly_usd: float  # $/RPS/month
    requests_per_dollar: int         # Requests per $1
    efficiency_score: float          # 0-10 score
    ranking: int                     # Rank among all frameworks

    def __str__(self) -> str:
        return f"Cost: ${self.cost_per_request_usd:.6f}/req | Score: {self.efficiency_score:.1f}/10"

class EfficiencyAnalyzer:
    """
    Analyze cost-performance efficiency
    """

    def calculate_cost_per_request(self,
        total_monthly_cost: float,
        requests_per_month: int) -> float:
        """
        Calculate cost per single request

        Formula: total_cost / requests_per_month

        Example:
        - Monthly cost: $142.49
        - Requests/month: 259,200,000
        - Cost/request: $0.00000055 (0.55 millicents)
        """

    def calculate_efficiency_score(self,
        cost_per_request: float,
        latency_p95_ms: float,
        throughput_rps: float,
        error_rate_pct: float) -> float:
        """
        Calculate overall efficiency score (0-10)

        Weighted formula:
        score = 10 - (0.4 × cost_factor + 0.3 × latency_factor
                      + 0.2 × throughput_factor + 0.1 × error_factor)

        Where:
        - cost_factor: normalized cost/request (0-10)
        - latency_factor: normalized p95 latency (0-10)
        - throughput_factor: normalized RPS (0-10)
        - error_factor: normalized error rate (0-10)

        Example:
        Strawberry: 8.5/10 (good efficiency)
        Express REST: 7.2/10 (moderate efficiency)
        """

    def rank_frameworks(self,
        efficiency_metrics: Dict[str, EfficiencyMetrics]) -> List[Tuple[str, EfficiencyMetrics]]:
        """
        Rank frameworks by efficiency score

        Returns: List of (framework_name, metrics) sorted by score
        """

    def generate_efficiency_report(self,
        frameworks_metrics: Dict[str, EfficiencyMetrics]) -> str:
        """
        Generate human-readable efficiency report

        Example output:

        Framework Cost Efficiency Report
        ==================================

        Rank  Framework       Cost/Req    RPS/Month      Score
        ────  ──────────────  ──────────  ────────────  ──────
        1.    Strawberry      $0.00055    259.2M        8.5/10
        2.    FastAPI         $0.00058    259.2M        8.3/10
        3.    Apollo Server   $0.00062    194.4M        7.8/10
        ...
        """
```

---

### 6. **result_builder.py** - Format Results

**Purpose**: Generate JSON, HTML, and CSV outputs

**Classes**:
```python
class CostAnalysisResult:
    """Complete cost analysis for one benchmark run"""
    framework: str
    workload: str
    profile: str
    timestamp: str

    # Metrics
    requests_per_second: float
    requests_per_month: int
    peak_latency_ms: float
    error_rate_pct: float

    # Resource Requirements
    cpu_cores_required: int
    memory_gb_required: int
    storage_gb_required: int

    # Costs (AWS, GCP, Azure)
    cost_aws: CostBreakdown
    cost_gcp: CostBreakdown
    cost_azure: CostBreakdown

    # Efficiency
    efficiency: EfficiencyMetrics

class ResultBuilder:
    """
    Build cost analysis results in multiple formats
    """

    def to_json(self, result: CostAnalysisResult) -> str:
        """
        Export to JSON format

        File: cost-analysis.json
        """

    def to_html_report(self,
        results: List[CostAnalysisResult],
        output_path: Path) -> None:
        """
        Generate HTML report with:
        - Summary table
        - Cost breakdown charts
        - Efficiency rankings
        - Recommendations

        File: cost-efficiency-report.html
        """

    def to_csv(self,
        results: List[CostAnalysisResult],
        output_path: Path) -> None:
        """
        Export to CSV for analysis

        Columns:
        framework, workload, profile, cpu_cores, memory_gb,
        storage_gb, cost_aws, cost_gcp, cost_azure,
        cost_per_request, efficiency_score, ranking
        """

    def to_comparison_table(self,
        frameworks: List[str],
        profile: str,
        provider: CloudProvider) -> str:
        """
        Generate comparison table for multiple frameworks

        Format:
        Framework           CPU   Memory  Storage  Monthly  $/Request  Score
        ──────────────────  ───   ──────  ───────  ───────  ─────────  ─────
        Strawberry          2     4 GB    10 GB    $142.49  $0.00055   8.5/10
        FastAPI             2     4 GB    10 GB    $149.99  $0.00058   8.3/10
        """
```

---

### 7. **integration.py** - Hook into VelocityBench

**Purpose**: Integration with existing benchmark pipeline

**Classes**:
```python
class CostSimulator:
    """
    Main integration point for cost simulation
    """

    def __init__(self, config_file: Path = None):
        self.cost_config = CostConfiguration(config_file)
        self.profiler = LoadProfiler()
        self.calculator = ResourceCalculator()
        self.cost_calc = CostCalculator(self.cost_config)
        self.analyzer = EfficiencyAnalyzer()

    def analyze_benchmark_result(self,
        jmeter_result_file: Path,
        framework_config: Dict[str, any],
        profile: LoadProfile = LoadProfile.SMALL) -> CostAnalysisResult:
        """
        Complete analysis pipeline:
        1. Parse JMeter results
        2. Calculate RPS and monthly volume
        3. Calculate resource requirements
        4. Calculate cloud costs (AWS/GCP/Azure)
        5. Analyze efficiency
        6. Return complete result
        """

    def analyze_all_frameworks(self,
        results_directory: Path,
        profile: LoadProfile = LoadProfile.SMALL,
        framework_filter: List[str] = None) -> Dict[str, CostAnalysisResult]:
        """
        Analyze cost for all frameworks in directory

        Searches: results/{framework}/{workload}/{profile}/results.jtl
        Returns: {framework_name: CostAnalysisResult}
        """

    def generate_cost_comparison_report(self,
        output_path: Path,
        framework_results: Dict[str, CostAnalysisResult],
        providers: List[CloudProvider] = [CloudProvider.AWS, CloudProvider.GCP, CloudProvider.AZURE]) -> None:
        """
        Generate comprehensive comparison report
        - HTML report with charts
        - CSV export
        - Efficiency rankings
        """
```

---

## Data Flow Integration

### 1. **During Benchmark Execution**

```python
# In scripts/run-benchmarks.py, after framework test completes:

from monitoring.cost_simulator import CostSimulator

simulator = CostSimulator()

# For each framework that was tested:
result = simulator.analyze_benchmark_result(
    jmeter_result_file=Path(f"tests/perf/results/{framework}/*/small/*/results.jtl"),
    framework_config=framework_registry[framework],
    profile=LoadProfile.SMALL
)

# Save result
result.to_json(Path(f"tests/perf/results/{framework}/*/small/*/cost-analysis.json"))
```

### 2. **Framework Configuration Enhancement**

```json
// In tests/integration/framework-config.json

{
  "frameworks": {
    "strawberry": {
      "port": 8011,
      "type": "graphql",
      "health": "/health",
      "endpoint": "/graphql",
      "language": "python",
      "category": "graphql-library",

      // NEW: Infrastructure profile for cost simulation
      "infrastructure": {
        "application_baseline_mb": 256,
        "connection_pool_size": 50,
        "memory_per_connection_mb": 5,
        "estimated_rps_per_core": 100,
        "typical_instance_type": "t3.large",
        "typical_memory_gb": 4,
        "dependencies": ["python3.11", "postgresql-client"],
        "container_size_mb": 450
      }
    }
  }
}
```

### 3. **Result Storage**

```
tests/perf/results/
├── strawberry/
│   ├── simple/
│   │   └── small/
│   │       └── 20260113_142000/
│   │           ├── results.jtl
│   │           ├── jmeter.log
│   │           └── cost-analysis.json  ← NEW
│   │
│   ├── aggregation/
│   │   └── small/
│   │       └── 20260113_150000/
│   │           └── cost-analysis.json  ← NEW
│   │
│   └── cost-summary.json  ← Aggregated across workloads
│
├── fastapi/
│   ├── simple/...
│   ├── cost-summary.json
│   └── ...
│
└── cost-comparison.json  ← Across all frameworks
```

---

## Pricing Data Integration

### Pricing Configuration File

**Location**: `monitoring/cost-config.json`

```json
{
  "pricing_date": "2026-01-13",
  "source": "AWS Pricing API, GCP, Azure official pricing",

  "aws": {
    "region": "us-east-1",
    "ec2": {
      "on_demand_hourly": {
        "t3.micro": 0.0104,
        "t3.small": 0.0208,
        "t3.medium": 0.0416,
        "t3.large": 0.0832,
        "t3.xlarge": 0.1664,
        "t3.2xlarge": 0.3328,
        "m5.large": 0.096,
        "m5.xlarge": 0.192,
        "m5.2xlarge": 0.384,
        "c5.large": 0.085,
        "c5.xlarge": 0.17,
        "c5.2xlarge": 0.34
      },
      "reserved_instance_discount": {
        "1_year": 0.40,
        "3_year": 0.55
      }
    },
    "rds": {
      "postgres_hourly": {
        "db.t3.micro": 0.017,
        "db.t3.small": 0.034,
        "db.t3.medium": 0.068,
        "db.m5.large": 0.20,
        "db.m5.xlarge": 0.40
      },
      "storage_per_gb_month": 0.115,
      "backup_storage_per_gb_month": 0.095
    },
    "ebs": {
      "gp3_per_gb_month": 0.085,
      "io1_per_gb_month": 0.125,
      "st1_per_gb_month": 0.045
    },
    "transfer": {
      "data_out_per_gb": 0.02,
      "inter_region_per_gb": 0.02
    }
  },

  "gcp": { ... },
  "azure": { ... }
}
```

---

## Grafana Dashboard Integration

### New Dashboard: "Cost Analysis"

**Panels** (6-8):

1. **Cost Comparison** (Bar chart)
   - X-axis: Frameworks
   - Y-axis: Monthly cost (AWS)
   - Grouped by: workload/profile

2. **Cost per Request** (Ranking)
   - Metric: $/request
   - Sorted by efficiency
   - Shows top 10 and bottom 5

3. **Resource Requirements** (Heatmap)
   - X-axis: Frameworks
   - Y-axis: Resource type (CPU, RAM, Storage)
   - Color: Value (cores, GB, GB)

4. **Cost Trends** (Line graph)
   - X-axis: Benchmark date
   - Y-axis: Monthly cost
   - Lines: Per framework
   - Shows cost evolution over time

5. **Efficiency Score** (Gauge)
   - Current leader's score
   - Ranking vs others
   - Trend indicator (↑/↓/→)

6. **Cost Distribution Pie** (Pie chart)
   - Compute, Database, Storage, Transfer, Other
   - For selected framework

7. **Total Cost of Ownership** (Table)
   - Framework, 1Y cost, 3Y cost
   - With reserved instance savings
   - Sorted by 3Y cost

---

## Example Output

### cost-analysis.json

```json
{
  "framework": "strawberry",
  "workload": "simple",
  "profile": "small",
  "timestamp": "2026-01-13T14:30:00Z",
  "benchmark_metrics": {
    "requests_per_second": 125.3,
    "latency_p50_ms": 45,
    "latency_p95_ms": 182,
    "latency_p99_ms": 356,
    "error_rate_pct": 0.02
  },
  "load_projection": {
    "rps_average": 125.3,
    "rps_peak": 313.25,
    "requests_per_day": 10_825_920,
    "requests_per_month": 324_777_600,
    "data_growth_per_month_gb": 4.2
  },
  "infrastructure_requirements": {
    "cpu_cores": 4,
    "memory_gb": 8,
    "storage_gb": 50,
    "recommended_instance": "m5.xlarge",
    "replicas": 2
  },
  "costs": {
    "aws": {
      "compute_monthly": 60.74,
      "compute_yearly": 728.88,
      "database_monthly": 45.00,
      "database_yearly": 540.00,
      "storage_monthly": 2.30,
      "storage_yearly": 27.60,
      "transfer_monthly": 1.50,
      "transfer_yearly": 18.00,
      "monitoring_monthly": 5.00,
      "monitoring_yearly": 60.00,
      "total_monthly": 114.54,
      "total_yearly": 1374.48,
      "total_with_1yr_ri": 1031.68,
      "total_with_3yr_ri": 771.26
    },
    "gcp": {
      "total_monthly": 119.30,
      "total_yearly": 1431.60
    },
    "azure": {
      "total_monthly": 112.45,
      "total_yearly": 1349.40
    }
  },
  "efficiency": {
    "cost_per_request": 3.53e-7,
    "requests_per_dollar": 2_830_189,
    "efficiency_score": 8.5,
    "ranking": 1
  }
}
```

### cost-efficiency-report.html

Shows:
- Summary table: Framework | Cores | Memory | Storage | Monthly Cost | $/Request | Score
- Cost breakdown pie chart per framework
- Cost comparison bar chart
- Efficiency score ranking
- Infrastructure requirements matrix
- Recommendation: "Strawberry is most cost-efficient at $0.000000353/request"

---

## Implementation Phases

### Phase 1: Core Engine (1 week)
- [ ] cost_config.py - Pricing data
- [ ] load_profiler.py - Load projection
- [ ] resource_calculator.py - Resource requirements
- [ ] Unit tests for all modules

### Phase 2: Cost Calculation (1 week)
- [ ] cost_calculator.py - Cloud cost calculation
- [ ] efficiency_analyzer.py - Efficiency metrics
- [ ] integration.py - Pipeline orchestration
- [ ] Integration tests

### Phase 3: Reporting (1 week)
- [ ] result_builder.py - JSON/HTML/CSV output
- [ ] Grafana dashboard integration
- [ ] CLI tool for manual analysis
- [ ] Documentation

### Phase 4: Integration (1 week)
- [ ] Hook into run-benchmarks.py
- [ ] Extend framework-config.json
- [ ] Add cost results to benchmark output
- [ ] End-to-end testing

---

## Success Criteria

- ✅ Can calculate monthly infrastructure cost for each framework
- ✅ Provides CPU, RAM, storage requirements
- ✅ Supports AWS, GCP, Azure pricing
- ✅ Generates efficiency scores and rankings
- ✅ Produces HTML reports and JSON data
- ✅ Integrates with benchmark pipeline
- ✅ Grafana dashboard shows cost metrics
- ✅ < 10 second analysis per framework

---

## Benefits

1. **Cost Visibility**: Understand infrastructure cost per framework
2. **Cost-Performance Trade-offs**: See cost vs latency vs throughput
3. **ROI Analysis**: Calculate true cost per request
4. **Infrastructure Planning**: Know resource requirements in advance
5. **Decision Support**: Objective comparison data for framework selection
6. **Cloud Optimization**: Compare costs across AWS/GCP/Azure

---

**Status**: Ready for implementation
**Next Step**: Begin Phase 1 - Core Engine development
