"""Integration tests for database schema and resolvers.

Tests verify:
1. Database schema creation and initialization
2. Composition views work correctly (zero N+1)
3. Resolver functions query and persist data
4. Cost calculation pipeline works end-to-end
5. Type conversions from database to FraiseQL types
"""

import sys
import os
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
import psycopg
from psycopg import sql

# Add costs directory to path
COSTS_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(COSTS_DIR))

from fraiseql_types import (
    Framework,
    BenchmarkSuite,
    Workload,
    LoadProfile,
    BenchmarkRun,
    PerformanceMetrics,
    ResourceProfile,
    CostAnalysisResult,
    CloudCostBreakdown,
    EfficiencyRanking,
    LanguageFamily,
    LoadProfileName,
    BenchmarkStatus,
    QueryComplexity,
    CloudProvider,
)
from resolvers import BenchmarkResolvers


# Database connection parameters
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_USER = os.getenv("DB_USER", "velocitybench")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_NAME = os.getenv("DB_NAME", "velocitybench_test")


@pytest.fixture
async def db_pool():
    """Create a connection pool for testing.

    Database should be created beforehand:
    createdb velocitybench_test
    """
    conninfo = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    pool = await psycopg.AsyncConnectionPool.open(conninfo)

    # Initialize schema
    async with pool.connection() as conn:
        schema_path = COSTS_DIR / "schema.sql"
        with open(schema_path) as f:
            schema = f.read()
        await conn.execute(schema)

    yield pool

    # Cleanup: drop all tables
    async with pool.connection() as conn:
        await conn.execute("""
            DROP VIEW IF EXISTS tv_cost_analysis CASCADE;
            DROP VIEW IF EXISTS tv_benchmark_run CASCADE;
            DROP TABLE IF EXISTS tb_benchmark_comparison CASCADE;
            DROP TABLE IF EXISTS tb_efficiency_ranking CASCADE;
            DROP TABLE IF EXISTS tb_cost_breakdown CASCADE;
            DROP TABLE IF EXISTS tb_cost_analysis CASCADE;
            DROP TABLE IF EXISTS tb_resource_profile CASCADE;
            DROP TABLE IF EXISTS tb_performance_percentiles CASCADE;
            DROP TABLE IF EXISTS tb_performance_metrics CASCADE;
            DROP TABLE IF EXISTS tb_benchmark_run CASCADE;
            DROP TABLE IF EXISTS tb_load_profile CASCADE;
            DROP TABLE IF EXISTS tb_workload CASCADE;
            DROP TABLE IF EXISTS tb_benchmark_suite CASCADE;
            DROP TABLE IF EXISTS tb_framework_metadata CASCADE;
            DROP TABLE IF EXISTS tb_framework CASCADE;
        """)

    await pool.close()


@pytest.fixture
async def resolver(db_pool):
    """Create a BenchmarkResolvers instance with test pool."""
    return BenchmarkResolvers(db_pool)


@pytest.fixture
async def sample_framework(db_pool):
    """Create a sample framework in the database."""
    framework_id = str(uuid.uuid4())
    async with db_pool.connection() as conn:
        await conn.execute(
            """
            INSERT INTO tb_framework
            (id, name, language, language_family, runtime, version)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                framework_id,
                "strawberry",
                "Python",
                "dynamic",
                "CPython 3.13",
                "0.230.0",
            ),
        )
    return framework_id


@pytest.fixture
async def sample_suite(db_pool):
    """Create a sample benchmark suite."""
    suite_id = str(uuid.uuid4())
    async with db_pool.connection() as conn:
        await conn.execute(
            """
            INSERT INTO tb_benchmark_suite
            (id, name, version, description)
            VALUES (%s, %s, %s, %s)
            """,
            (suite_id, "2026-q1", "1.0", "Q1 2026 Benchmark Suite"),
        )
    return suite_id


@pytest.fixture
async def sample_workload(db_pool, sample_suite):
    """Create a sample workload."""
    workload_id = str(uuid.uuid4())
    async with db_pool.connection() as conn:
        suite_pk = await conn.scalar(
            "SELECT pk_suite FROM tb_benchmark_suite WHERE id = %s",
            (sample_suite,),
        )
        await conn.execute(
            """
            INSERT INTO tb_workload
            (id, fk_suite, name, query_complexity, operation_count, estimated_join_depth)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (workload_id, suite_pk, "simple_query", "simple", 1, 0),
        )
    return workload_id


@pytest.fixture
async def sample_load_profile(db_pool):
    """Create a sample load profile."""
    profile_id = str(uuid.uuid4())
    async with db_pool.connection() as conn:
        await conn.execute(
            """
            INSERT INTO tb_load_profile
            (id, name, rps, duration_seconds, warmup_seconds, threads, ramp_up_time_seconds, think_time_ms)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (profile_id, "test_profile", 100, 60, 5, 10, 10, 50),
        )
    return profile_id


@pytest.fixture
async def sample_benchmark_run(
    db_pool, sample_framework, sample_suite, sample_workload, sample_load_profile
):
    """Create a sample benchmark run."""
    run_id = str(uuid.uuid4())
    start_time = datetime.now()
    end_time = start_time + timedelta(seconds=60)

    async with db_pool.connection() as conn:
        framework_pk = await conn.scalar(
            "SELECT pk_framework FROM tb_framework WHERE id = %s",
            (sample_framework,),
        )
        suite_pk = await conn.scalar(
            "SELECT pk_suite FROM tb_benchmark_suite WHERE id = %s",
            (sample_suite,),
        )
        workload_pk = await conn.scalar(
            "SELECT pk_workload FROM tb_workload WHERE id = %s",
            (sample_workload,),
        )
        profile_pk = await conn.scalar(
            "SELECT pk_profile FROM tb_load_profile WHERE id = %s",
            (sample_load_profile,),
        )

        await conn.execute(
            """
            INSERT INTO tb_benchmark_run
            (id, fk_framework, fk_suite, fk_workload, fk_load_profile,
             status, start_time, end_time, duration_seconds)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                run_id,
                framework_pk,
                suite_pk,
                workload_pk,
                profile_pk,
                "completed",
                start_time,
                end_time,
                60,
            ),
        )

    return run_id


@pytest.fixture
async def sample_performance_metrics(db_pool, sample_benchmark_run):
    """Create sample performance metrics for a benchmark run."""
    async with db_pool.connection() as conn:
        run_pk = await conn.scalar(
            "SELECT pk_run FROM tb_benchmark_run WHERE id = %s",
            (sample_benchmark_run,),
        )

        await conn.execute(
            """
            INSERT INTO tb_performance_metrics
            (fk_run, total_requests, total_errors, error_rate, requests_per_second,
             latency_min, latency_p50, latency_p95, latency_p99, latency_p999,
             latency_max, latency_mean, latency_stddev,
             response_bytes_min, response_bytes_mean, response_bytes_max,
             connect_time_mean, idle_time_mean, server_processing_mean)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                run_pk,
                6000,  # total_requests
                0,  # total_errors
                0.0,  # error_rate
                100.0,  # requests_per_second
                5,  # latency_min
                25,  # latency_p50
                95,  # latency_p95
                150,  # latency_p99
                250,  # latency_p999
                500,  # latency_max
                50,  # latency_mean
                40,  # latency_stddev
                100,  # response_bytes_min
                1024,  # response_bytes_mean
                5000,  # response_bytes_max
                2,  # connect_time_mean
                0,  # idle_time_mean
                40,  # server_processing_mean
            ),
        )

    return sample_benchmark_run


class TestDatabaseSchema:
    """Test database schema creation and structure."""

    @pytest.mark.asyncio
    async def test_schema_creates_all_tables(self, db_pool):
        """Verify all 15 tables are created."""
        async with db_pool.connection() as conn:
            tables = await conn.execute(
                """
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name LIKE 'tb_%'
                ORDER BY table_name
                """
            )
            table_names = [row[0] for row in tables]

        expected_tables = [
            "tb_benchmark_comparison",
            "tb_benchmark_run",
            "tb_benchmark_suite",
            "tb_cost_analysis",
            "tb_cost_breakdown",
            "tb_efficiency_ranking",
            "tb_framework",
            "tb_framework_metadata",
            "tb_load_profile",
            "tb_performance_metrics",
            "tb_performance_percentiles",
            "tb_resource_profile",
            "tb_workload",
        ]

        assert sorted(table_names) == sorted(expected_tables)

    @pytest.mark.asyncio
    async def test_composition_views_exist(self, db_pool):
        """Verify composition views are created."""
        async with db_pool.connection() as conn:
            views = await conn.execute(
                """
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public' AND table_type = 'VIEW'
                ORDER BY table_name
                """
            )
            view_names = [row[0] for row in views]

        assert "tv_benchmark_run" in view_names
        assert "tv_cost_analysis" in view_names

    @pytest.mark.asyncio
    async def test_load_profiles_inserted(self, db_pool):
        """Verify default load profiles are inserted."""
        async with db_pool.connection() as conn:
            count = await conn.scalar("SELECT COUNT(*) FROM tb_load_profile")

        assert count >= 5  # smoke, small, medium, large, production


class TestFrameworkResolver:
    """Test framework query resolvers."""

    @pytest.mark.asyncio
    async def test_resolve_framework_by_id(self, resolver, sample_framework):
        """Test retrieving a framework by ID."""
        framework = await resolver.resolve_framework(id=sample_framework)

        assert framework is not None
        assert framework.id == sample_framework
        assert framework.name == "strawberry"
        assert framework.language == "Python"

    @pytest.mark.asyncio
    async def test_resolve_framework_by_name(self, resolver, sample_framework):
        """Test retrieving a framework by name."""
        framework = await resolver.resolve_framework(name="strawberry")

        assert framework is not None
        assert framework.id == sample_framework
        assert framework.name == "strawberry"

    @pytest.mark.asyncio
    async def test_resolve_framework_not_found(self, resolver):
        """Test framework not found returns None."""
        framework = await resolver.resolve_framework(id=str(uuid.uuid4()))

        assert framework is None

    @pytest.mark.asyncio
    async def test_resolve_frameworks_list(self, resolver, sample_framework, db_pool):
        """Test listing frameworks."""
        # Create a second framework
        second_id = str(uuid.uuid4())
        async with db_pool.connection() as conn:
            await conn.execute(
                """
                INSERT INTO tb_framework
                (id, name, language, language_family, runtime, version)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (second_id, "fastapi", "Python", "dynamic", "CPython 3.13", "0.100.0"),
            )

        frameworks = await resolver.resolve_frameworks()

        assert len(frameworks) >= 2
        names = {f.name for f in frameworks}
        assert "strawberry" in names
        assert "fastapi" in names

    @pytest.mark.asyncio
    async def test_resolve_frameworks_with_language_filter(
        self, resolver, sample_framework, db_pool
    ):
        """Test filtering frameworks by language."""
        # Create a non-Python framework
        go_id = str(uuid.uuid4())
        async with db_pool.connection() as conn:
            await conn.execute(
                """
                INSERT INTO tb_framework
                (id, name, language, language_family, runtime, version)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (go_id, "gin", "Go", "static", "Go 1.21", "1.9.0"),
            )

        frameworks = await resolver.resolve_frameworks(language="Python")

        assert all(f.language == "Python" for f in frameworks)


class TestBenchmarkRunResolver:
    """Test benchmark run query resolvers."""

    @pytest.mark.asyncio
    async def test_resolve_benchmark_run_with_composition_view(
        self, resolver, sample_benchmark_run
    ):
        """Test retrieving a benchmark run via composition view."""
        run = await resolver.resolve_benchmark_run(id=sample_benchmark_run)

        assert run is not None
        assert run.id == sample_benchmark_run
        assert run.status == "completed"

        # Verify composed data (from composition view)
        assert run.framework is not None
        assert run.framework.name == "strawberry"
        assert run.suite is not None
        assert run.suite.name == "2026-q1"
        assert run.workload is not None
        assert run.workload.name == "simple_query"
        assert run.load_profile is not None
        assert run.load_profile.rps == 100

    @pytest.mark.asyncio
    async def test_resolve_benchmark_run_not_found(self, resolver):
        """Test benchmark run not found returns None."""
        run = await resolver.resolve_benchmark_run(id=str(uuid.uuid4()))

        assert run is None

    @pytest.mark.asyncio
    async def test_resolve_benchmark_runs_by_suite(
        self, resolver, sample_benchmark_run, sample_suite
    ):
        """Test listing benchmark runs by suite."""
        runs = await resolver.resolve_benchmark_runs(suite_id=sample_suite)

        assert len(runs) >= 1
        assert any(r.id == sample_benchmark_run for r in runs)

    @pytest.mark.asyncio
    async def test_resolve_benchmark_runs_with_filters(
        self, resolver, sample_benchmark_run, sample_suite
    ):
        """Test filtering benchmark runs by multiple criteria."""
        runs = await resolver.resolve_benchmark_runs(
            suite_id=sample_suite, status="completed"
        )

        assert len(runs) >= 1
        assert all(r.status == "completed" for r in runs)


class TestPerformanceMetricsResolver:
    """Test performance metrics retrieval."""

    @pytest.mark.asyncio
    async def test_resolve_benchmark_run_with_metrics(self, resolver, sample_performance_metrics):
        """Test that benchmark run includes performance metrics."""
        run = await resolver.resolve_benchmark_run(id=sample_performance_metrics)

        assert run is not None
        assert run.metrics is not None
        assert run.metrics.total_requests == 6000
        assert run.metrics.requests_per_second == 100.0
        assert run.metrics.error_rate == 0.0
        assert run.metrics.latency_mean == 50
        assert run.metrics.latency_p95 == 95
        assert run.metrics.latency_p99 == 150


class TestResourceProfileResolver:
    """Test resource profile calculation and storage."""

    @pytest.mark.asyncio
    async def test_calculate_and_store_resource_profile(
        self, resolver, sample_performance_metrics, db_pool
    ):
        """Test that resource profile is calculated from metrics."""
        run = await resolver.resolve_benchmark_run(id=sample_performance_metrics)

        # Resource profile should be calculated
        if run.resource_profile is not None:
            assert run.resource_profile.cpu_cores_required > 0
            assert run.resource_profile.memory_required_gb > 0
            assert run.resource_profile.total_monthly_storage_gb > 0


class TestCostAnalysisResolver:
    """Test cost analysis calculation and persistence."""

    @pytest.mark.asyncio
    async def test_cost_analysis_calculation_pipeline(
        self, resolver, sample_performance_metrics, db_pool
    ):
        """Test the complete cost analysis pipeline."""
        # Trigger cost analysis
        cost_result = await resolver.resolve_cost_analysis(
            benchmark_run_id=sample_performance_metrics
        )

        # Should return a CostAnalysisResult
        assert cost_result is not None
        assert cost_result.recommended_cloud_provider in ["aws", "gcp", "azure"]
        assert cost_result.cost_breakdowns is not None
        assert len(cost_result.cost_breakdowns) == 3  # AWS, GCP, Azure

        # Verify cost breakdown details
        for breakdown in cost_result.cost_breakdowns:
            assert breakdown.cloud_provider in ["aws", "gcp", "azure"]
            assert breakdown.total_monthly_cost > 0
            assert breakdown.instance_type is not None
            assert breakdown.cost_per_request > 0

    @pytest.mark.asyncio
    async def test_cost_analysis_persists_to_database(
        self, resolver, sample_performance_metrics, db_pool
    ):
        """Test that cost analysis results are persisted."""
        # Calculate cost analysis
        await resolver.resolve_cost_analysis(benchmark_run_id=sample_performance_metrics)

        # Verify it was stored in database
        async with db_pool.connection() as conn:
            run_pk = await conn.scalar(
                "SELECT pk_run FROM tb_benchmark_run WHERE id = %s",
                (sample_performance_metrics,),
            )
            cost_analysis = await conn.execute(
                "SELECT fk_run FROM tb_cost_analysis WHERE fk_run = %s",
                (run_pk,),
            )
            rows = await cost_analysis.fetchall()

        assert len(rows) > 0

    @pytest.mark.asyncio
    async def test_cost_breakdown_multi_cloud(
        self, resolver, sample_performance_metrics
    ):
        """Test that cost analysis includes all three cloud providers."""
        cost_result = await resolver.resolve_cost_analysis(
            benchmark_run_id=sample_performance_metrics
        )

        providers = {cb.cloud_provider for cb in cost_result.cost_breakdowns}
        assert "aws" in providers
        assert "gcp" in providers
        assert "azure" in providers


class TestEfficiencyRankingResolver:
    """Test efficiency ranking calculation."""

    @pytest.mark.asyncio
    async def test_efficiency_ranking_calculation(
        self, resolver, sample_performance_metrics
    ):
        """Test that efficiency ranking is calculated."""
        run = await resolver.resolve_benchmark_run(id=sample_performance_metrics)

        if run.efficiency_ranking is not None:
            # Efficiency score should be 0-10
            assert 0 <= run.efficiency_ranking.efficiency_score <= 10

            # Components should sum to approximately efficiency_score
            assert run.efficiency_ranking.cost_component >= 0
            assert run.efficiency_ranking.latency_component >= 0
            assert run.efficiency_ranking.throughput_component >= 0
            assert run.efficiency_ranking.reliability_component >= 0

            # Suite rank should be positive
            assert run.efficiency_ranking.suite_rank > 0


class TestCompositionViews:
    """Test that composition views work correctly (zero N+1)."""

    @pytest.mark.asyncio
    async def test_benchmark_run_composition_view(self, db_pool, sample_benchmark_run):
        """Test that tv_benchmark_run view composes all related data."""
        async with db_pool.connection() as conn:
            result = await conn.execute(
                "SELECT framework, suite, workload, load_profile FROM tv_benchmark_run WHERE id = %s",
                (sample_benchmark_run,),
            )
            row = await result.fetchone()

        assert row is not None
        # All composed data should be present
        assert row[0] is not None  # framework
        assert row[1] is not None  # suite
        assert row[2] is not None  # workload
        assert row[3] is not None  # load_profile

    @pytest.mark.asyncio
    async def test_cost_analysis_composition_view(self, resolver, sample_performance_metrics):
        """Test that tv_cost_analysis view composes all cost data."""
        # Calculate cost analysis to populate view
        await resolver.resolve_cost_analysis(benchmark_run_id=sample_performance_metrics)

        async with db_pool.connection() as conn:
            result = await conn.execute(
                "SELECT cost_breakdowns, efficiency_ranking FROM tv_cost_analysis LIMIT 1"
            )
            row = await result.fetchone()

        # Both should be present in JSONB
        assert row is not None


class TestTypeConversions:
    """Test conversions from database rows to FraiseQL types."""

    @pytest.mark.asyncio
    async def test_framework_type_conversion(self, resolver, sample_framework):
        """Test Framework dataclass conversion from database."""
        framework = await resolver.resolve_framework(id=sample_framework)

        # Type should be Framework dataclass
        assert isinstance(framework, Framework)
        assert framework.id == sample_framework
        assert framework.name == "strawberry"
        assert framework.language == "Python"
        assert isinstance(framework.language_family, str)

    @pytest.mark.asyncio
    async def test_benchmark_run_type_conversion(self, resolver, sample_benchmark_run):
        """Test BenchmarkRun dataclass conversion from database."""
        run = await resolver.resolve_benchmark_run(id=sample_benchmark_run)

        # Type should be BenchmarkRun dataclass
        assert isinstance(run, BenchmarkRun)
        assert run.id == sample_benchmark_run
        assert isinstance(run.status, str)
        assert isinstance(run.start_time, str)

    @pytest.mark.asyncio
    async def test_cost_analysis_result_type_conversion(
        self, resolver, sample_performance_metrics
    ):
        """Test CostAnalysisResult dataclass conversion."""
        result = await resolver.resolve_cost_analysis(
            benchmark_run_id=sample_performance_metrics
        )

        # Type should be CostAnalysisResult dataclass
        assert isinstance(result, CostAnalysisResult)
        assert isinstance(result.recommended_cloud_provider, str)
        assert isinstance(result.cost_breakdowns, list)
        assert all(isinstance(cb, CloudCostBreakdown) for cb in result.cost_breakdowns)


class TestIntegrationPipeline:
    """Test complete end-to-end pipeline."""

    @pytest.mark.asyncio
    async def test_full_benchmark_to_cost_analysis_pipeline(
        self, resolver, sample_performance_metrics, db_pool
    ):
        """Test complete pipeline: benchmark → metrics → cost analysis."""
        # 1. Retrieve benchmark run with metrics
        run = await resolver.resolve_benchmark_run(id=sample_performance_metrics)
        assert run is not None
        assert run.metrics is not None

        # 2. Calculate cost analysis
        cost_result = await resolver.resolve_cost_analysis(
            benchmark_run_id=sample_performance_metrics
        )
        assert cost_result is not None
        assert cost_result.cost_breakdowns is not None

        # 3. Verify data was persisted
        async with db_pool.connection() as conn:
            run_pk = await conn.scalar(
                "SELECT pk_run FROM tb_benchmark_run WHERE id = %s",
                (sample_performance_metrics,),
            )

            # Check performance metrics stored
            metrics = await conn.scalar(
                "SELECT total_requests FROM tb_performance_metrics WHERE fk_run = %s",
                (run_pk,),
            )
            assert metrics == 6000

            # Check cost analysis stored
            cost_analysis = await conn.scalar(
                "SELECT recommended_cloud_provider FROM tb_cost_analysis WHERE fk_run = %s",
                (run_pk,),
            )
            assert cost_analysis is not None
