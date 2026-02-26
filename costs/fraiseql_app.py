#!/usr/bin/env python3
"""VelocityBench Comprehensive Analytics FraiseQL Application.

Uses FraiseQL decorators (@fraiseql.type, @fraiseql.query) to expose
the comprehensive analytics database schema as a GraphQL API.

Database architecture:
- tb_* tables: Write layer with Trinity Pattern (id, identifier, pk, fk)
- tv_* views: Composition layer with pre-composed JSONB objects for zero N+1 queries
- FraiseQL: Automatically generates GraphQL from decorated Python types

Three-layer design:
1. Database tables: 54 tables across 8 levels
2. Composition views: Pre-compose nested JSONB objects
3. FraiseQL types: Map to views, automatically become GraphQL types
"""

import logging
import os
from typing import Any

# FraiseQL imports
import fraiseql
import uvicorn
from fraiseql.fastapi import FraiseQLConfig, create_fraiseql_app
from fraiseql.fastapi.config import IntrospectionPolicy
from fraiseql.types import UUID
from graphql import GraphQLResolveInfo


# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_fraiseql_config() -> FraiseQLConfig:
    """Create FraiseQL configuration for VelocityBench analytics."""
    # Password is REQUIRED - fail fast if not provided
    db_password = os.getenv("DB_PASSWORD")
    if not db_password:
        raise ValueError(
            "Database password is required. Set DB_PASSWORD environment variable."
        )

    return FraiseQLConfig(
        database_url=f"postgresql://{os.getenv('DB_USER', 'benchmark')}:{db_password}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'velocitybench')}",
        environment=os.getenv("ENVIRONMENT", "development"),
        introspection_policy=IntrospectionPolicy.PUBLIC,
        enable_playground=True,
        auto_camel_case=True,  # Convert snake_case from DB to camelCase in GraphQL
        cors_enabled=True,
        complexity_enabled=False,  # Disable for benchmarking
        database_pool_size=int(os.getenv("DB_POOL_SIZE", "20")),
        database_max_overflow=10,
        max_query_depth=10,
    )


# ============================================================================
# LEVEL 1: FRAMEWORK TYPES
# ============================================================================


@fraiseql.type(sql_source="public.tv_framework")
class FrameworkType:
    """Framework with metadata, implementation, and optimization details."""
    id: UUID
    identifier: str
    name: str
    language: str
    language_family: str
    runtime: str
    version: str
    repository_url: str | None = None
    documentation_url: str | None = None
    created_at: str


# ============================================================================
# LEVEL 2: BENCHMARK DEFINITION TYPES
# ============================================================================


@fraiseql.type(sql_source="public.tv_benchmark_suite")
class BenchmarkSuiteType:
    """Benchmark suite definition with query patterns."""
    id: UUID
    identifier: str
    name: str
    version: str
    description: str | None = None
    created_by: str | None = None
    created_at: str


@fraiseql.type(sql_source="public.tv_query_pattern")
class QueryPatternType:
    """Query pattern being tested with complexity metrics."""
    id: UUID
    identifier: str
    pattern_name: str
    pattern_type: str  # simple_query, nested_query, mutation, aggregation
    complexity: str  # simple, moderate, complex
    expected_execution_ms: int | None = None
    created_at: str


@fraiseql.type(sql_source="public.tv_workload")
class WorkloadType:
    """Workload combining multiple query patterns."""
    id: UUID
    identifier: str
    name: str
    query_complexity: str | None = None
    operation_count: int | None = None
    created_at: str


@fraiseql.type(sql_source="public.tv_load_profile")
class LoadProfileType:
    """Predefined load profile for testing."""
    id: UUID
    identifier: str
    name: str
    rps: int
    duration_seconds: int
    warmup_seconds: int
    threads: int
    ramp_up_time_seconds: int | None = None
    think_time_ms: int | None = None
    created_at: str


# ============================================================================
# LEVEL 3: TEST ENVIRONMENT TYPES
# ============================================================================


@fraiseql.type(sql_source="public.tv_test_machine")
class TestMachineType:
    """Test machine hardware specifications."""
    id: UUID
    identifier: str
    machine_name: str | None = None
    cpu_model: str
    cpu_cores: int
    cpu_threads: int
    cpu_base_ghz: float | None = None
    cpu_boost_ghz: float | None = None
    ram_gb: int
    storage_type: str | None = None
    os_name: str
    os_version: str | None = None
    created_at: str


@fraiseql.type(sql_source="public.tv_database_instance")
class DatabaseInstanceType:
    """Database instance configuration."""
    id: UUID
    identifier: str
    database_engine: str
    engine_version: str | None = None
    instance_class: str | None = None
    max_connections: int | None = None
    created_at: str


# ============================================================================
# LEVEL 4: BENCHMARK EXECUTION TYPES
# ============================================================================


@fraiseql.type(sql_source="public.tv_benchmark_run")
class BenchmarkRunType:
    """Benchmark run with pre-composed framework, suite, workload, environment."""
    id: UUID
    identifier: str
    status: str
    start_time: str
    end_time: str | None = None
    duration_seconds: int | None = None
    jmeter_file_path: str | None = None
    # Nested objects are pre-composed in tv_benchmark_run JSONB
    framework: dict[str, Any]
    suite: dict[str, Any]
    workload: dict[str, Any]
    load_profile: dict[str, Any]
    test_machine: dict[str, Any] | None = None
    database_instance: dict[str, Any] | None = None
    created_at: str


# ============================================================================
# LEVEL 5: PERFORMANCE METRICS TYPES
# ============================================================================


@fraiseql.type(sql_source="public.tv_performance_metrics")
class PerformanceMetricsType:
    """Complete performance metrics."""
    id: UUID
    identifier: str
    total_requests: int
    total_errors: int
    error_rate: float
    requests_per_second: float
    latency_min: int
    latency_p50: int
    latency_p95: int
    latency_p99: int
    latency_p999: int
    latency_max: int
    latency_mean: int
    latency_stddev: int
    created_at: str


# ============================================================================
# LEVEL 6: ANALYSIS & DERIVED DATA TYPES
# ============================================================================


@fraiseql.type(sql_source="public.tv_cost_analysis")
class CostAnalysisType:
    """Cost analysis with pre-composed cost breakdowns and efficiency ranking."""
    id: UUID
    identifier: str
    recommended_cloud_provider: str
    recommended_instance_type: str
    # Nested arrays/objects pre-composed in tv_cost_analysis JSONB
    cost_breakdowns: list[dict[str, Any]] | None = None
    efficiency_ranking: dict[str, Any] | None = None
    created_at: str


@fraiseql.type(sql_source="public.tv_efficiency_ranking")
class EfficiencyRankingType:
    """Efficiency ranking combining cost, latency, throughput, reliability."""
    id: UUID
    identifier: str
    efficiency_score: float
    cost_component: float
    latency_component: float
    throughput_component: float
    reliability_component: float
    suite_rank: int | None = None
    created_at: str


# ============================================================================
# LEVEL 7: COMPARISON & TRENDS TYPES
# ============================================================================


@fraiseql.type(sql_source="public.tv_framework_comparison")
class FrameworkComparisonType:
    """Framework comparison results."""
    id: UUID
    identifier: str
    framework_count: int
    comparison_date: str | None = None
    fastest_framework_id: UUID | None = None
    cheapest_framework_id: UUID | None = None
    most_efficient_framework_id: UUID | None = None
    created_at: str


@fraiseql.type(sql_source="public.tv_performance_trend")
class PerformanceTrendType:
    """Performance trend point over time."""
    id: UUID
    identifier: str
    trend_date: str
    rps: float
    latency_p95: int
    latency_p99: int
    efficiency_score: float
    cost_per_request: float
    created_at: str


# ============================================================================
# LEVEL 8: CODE & REPRODUCIBILITY TYPES
# ============================================================================


@fraiseql.type(sql_source="public.tv_code_snapshot")
class CodeSnapshotType:
    """Code snapshot taken at benchmark time."""
    id: UUID
    identifier: str
    snapshot_type: str  # framework, database_library, optimization
    git_commit_hash: str | None = None
    git_branch: str | None = None
    content_hash: str | None = None
    created_at: str


@fraiseql.type(sql_source="public.tv_reproducibility_manifest")
class ReproducibilityManifestType:
    """Complete reproducibility manifest for exact run reproduction."""
    id: UUID
    identifier: str
    manifest_data: dict[str, Any]
    manifest_version: str | None = None
    checksum: str | None = None
    created_at: str


# ============================================================================
# QUERY RESOLVERS
# ============================================================================


@fraiseql.query
async def ping(info: GraphQLResolveInfo) -> str:
    """Health check query."""
    return "pong"


@fraiseql.query
async def framework(info: GraphQLResolveInfo, id: UUID | None = None, name: str | None = None) -> FrameworkType | None:
    """Query single framework by ID or name."""
    pool = info.context.get("db_pool")
    if not pool:
        return None

    async with pool.connection() as conn:
        cursor = await conn.cursor()

        if id:
            await cursor.execute(
                "SELECT id, identifier, name, language, language_family, runtime, version, repository_url, documentation_url, created_at FROM public.tv_framework WHERE id = %s",
                (str(id),)
            )
        elif name:
            await cursor.execute(
                "SELECT id, identifier, name, language, language_family, runtime, version, repository_url, documentation_url, created_at FROM public.tv_framework WHERE name = %s",
                (name,)
            )
        else:
            return None

        row = await cursor.fetchone()
        if not row:
            return None

        return FrameworkType(
            id=row[0],
            identifier=row[1],
            name=row[2],
            language=row[3],
            language_family=row[4],
            runtime=row[5],
            version=row[6],
            repository_url=row[7],
            documentation_url=row[8],
            created_at=row[9].isoformat() if row[9] else None,
        )


@fraiseql.query
async def benchmark_run(info: GraphQLResolveInfo, id: UUID) -> BenchmarkRunType | None:
    """Query single benchmark run with all nested data from composition view."""
    pool = info.context.get("db_pool")
    if not pool:
        return None

    async with pool.connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            """
            SELECT id, identifier, status, start_time, end_time, duration_seconds,
                   jmeter_file_path, framework, suite, workload, load_profile,
                   test_machine, database_instance, created_at
            FROM public.tv_benchmark_run WHERE id = %s
            """,
            (str(id),)
        )
        row = await cursor.fetchone()
        if not row:
            return None

        return BenchmarkRunType(
            id=row[0],
            identifier=row[1],
            status=row[2],
            start_time=row[3].isoformat() if row[3] else None,
            end_time=row[4].isoformat() if row[4] else None,
            duration_seconds=row[5],
            jmeter_file_path=row[6],
            framework=row[7],
            suite=row[8],
            workload=row[9],
            load_profile=row[10],
            test_machine=row[11],
            database_instance=row[12],
            created_at=row[13].isoformat() if row[13] else None,
        )


@fraiseql.query
async def cost_analysis(info: GraphQLResolveInfo, run_id: UUID) -> CostAnalysisType | None:
    """Query cost analysis for a benchmark run from composition view."""
    pool = info.context.get("db_pool")
    if not pool:
        return None

    async with pool.connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            """
            SELECT id, identifier, recommended_cloud_provider,
                   recommended_instance_type, cost_breakdowns, efficiency_ranking, created_at
            FROM public.tv_cost_analysis
            WHERE fk_run = (SELECT pk_run FROM public.tb_benchmark_run WHERE id = %s)
            """,
            (str(run_id),)
        )
        row = await cursor.fetchone()
        if not row:
            return None

        return CostAnalysisType(
            id=row[0],
            identifier=row[1],
            recommended_cloud_provider=row[2],
            recommended_instance_type=row[3],
            cost_breakdowns=row[4] if row[4] else None,
            efficiency_ranking=row[5] if row[5] else None,
            created_at=row[6].isoformat() if row[6] else None,
        )


@fraiseql.query
async def performance_metrics(info: GraphQLResolveInfo, run_id: UUID) -> PerformanceMetricsType | None:
    """Query performance metrics for a benchmark run."""
    pool = info.context.get("db_pool")
    if not pool:
        return None

    async with pool.connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            """
            SELECT id, identifier, total_requests, total_errors, error_rate,
                   requests_per_second, latency_min, latency_p50, latency_p95,
                   latency_p99, latency_p999, latency_max, latency_mean, latency_stddev, created_at
            FROM public.tv_performance_metrics
            WHERE fk_run = (SELECT pk_run FROM public.tb_benchmark_run WHERE id = %s)
            """,
            (str(run_id),)
        )
        row = await cursor.fetchone()
        if not row:
            return None

        return PerformanceMetricsType(
            id=row[0],
            identifier=row[1],
            total_requests=row[2],
            total_errors=row[3],
            error_rate=float(row[4]) if row[4] else 0,
            requests_per_second=float(row[5]),
            latency_min=row[6],
            latency_p50=row[7],
            latency_p95=row[8],
            latency_p99=row[9],
            latency_p999=row[10],
            latency_max=row[11],
            latency_mean=row[12],
            latency_stddev=row[13],
            created_at=row[14].isoformat() if row[14] else None,
        )


# ============================================================================
# APPLICATION FACTORY
# ============================================================================


def create_app():
    """Create and configure the FraiseQL FastAPI application."""
    config = create_fraiseql_config()
    app = create_fraiseql_app(config)

    # Add health check middleware
    @app.get("/health")
    async def health_check():
        return {"status": "ok"}

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", 8000))

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
    )
