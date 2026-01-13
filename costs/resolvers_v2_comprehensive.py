"""Enhanced FraiseQL Resolvers for VelocityBench Comprehensive Analytics.

Implements resolver functions that:
1. Wrap Phase 1 cost calculation modules
2. Handle Trinity Pattern (id, identifier, pk, fk)
3. Handle database persistence with comprehensive schema
4. Support code tracking, detailed metrics, environment tracking
5. Return properly typed FraiseQL objects

Uses psycopg3 with synchronous and async connection pool.
"""

from datetime import datetime
from typing import Any
import uuid
import json

from cost_config import CostConfiguration
from load_profiler import LoadProfiler
from resource_calculator import ResourceCalculator
from fraiseql_types_v2_comprehensive import (
    Framework,
    FrameworkMetadata,
    FrameworkImplementation,
    FrameworkFile,
    DatabaseLibrary,
    OptimizationTechnique,
    CachingStrategy,
    BenchmarkSuite,
    QueryPattern,
    Workload,
    LoadProfile,
    TestMachine,
    TestMachineMemory,
    DatabaseInstance,
    BenchmarkRun,
    PerformanceMetrics,
    ResourceProfile,
    CostAnalysisResult,
    CloudCostBreakdown,
    EfficiencyRanking,
    PerformanceCharacterization,
    RegressionDetection,
    CodeSnapshot,
    ReproducibilityManifest,
)


def generate_identifier(entity_type: str, *parts: str) -> str:
    """Generate Trinity Pattern identifier from entity type and parts.

    Args:
        entity_type: Type of entity (e.g., "framework", "run", "metrics")
        *parts: Variable parts that identify this entity uniquely

    Returns:
        Human-readable identifier like "framework:FastAPI:0.100.0"
    """
    return f"{entity_type}:{':'.join(str(p) for p in parts if p)}"


class BenchmarkResolversV2:
    """Resolver functions for comprehensive benchmark analytics.

    Uses psycopg3 connection pool with cursor context managers.
    Supports Trinity Pattern (id, identifier, pk, fk).
    """

    def __init__(self, db_connection):
        """Initialize resolvers with database connection.

        Args:
            db_connection: psycopg3 connection object or connection pool
        """
        self.db = db_connection
        self.cost_config = CostConfiguration()
        self.load_profiler = LoadProfiler()

    # ========================================================================
    # FRAMEWORK QUERIES
    # ========================================================================

    async def resolve_framework(
        self,
        id: str | None = None,
        name: str | None = None,
    ) -> Framework | None:
        """Resolve single framework by ID or name.

        Args:
            id: Framework UUID
            name: Framework name

        Returns:
            Framework object with metadata and implementation details
        """
        if hasattr(self.db, "cursor"):
            # Synchronous interface (test)
            cursor = self.db.cursor()
            try:
                if id:
                    cursor.execute(
                        """
                        SELECT f.id, f.identifier, f.name, f.language,
                               f.language_family, f.runtime, f.version
                        FROM tb_framework f WHERE f.id = %s
                        """,
                        (id,),
                    )
                elif name:
                    cursor.execute(
                        """
                        SELECT f.id, f.identifier, f.name, f.language,
                               f.language_family, f.runtime, f.version
                        FROM tb_framework f WHERE f.name = %s
                        """,
                        (name,),
                    )
                else:
                    return None

                row = cursor.fetchone()
                if not row:
                    return None

                framework = self._row_to_framework(row)

                # Load nested data
                framework.metadata = self._fetch_framework_metadata(cursor, framework.id)
                framework.implementation = self._fetch_framework_implementation(cursor, framework.id)

                return framework
            finally:
                cursor.close()
        else:
            # Async interface (psycopg3)
            async with self.db.connection() as conn:
                cursor = await conn.cursor()
                if id:
                    await cursor.execute(
                        """
                        SELECT f.id, f.identifier, f.name, f.language,
                               f.language_family, f.runtime, f.version
                        FROM tb_framework f WHERE f.id = %s
                        """,
                        (id,),
                    )
                elif name:
                    await cursor.execute(
                        """
                        SELECT f.id, f.identifier, f.name, f.language,
                               f.language_family, f.runtime, f.version
                        FROM tb_framework f WHERE f.name = %s
                        """,
                        (name,),
                    )
                else:
                    return None

                row = await cursor.fetchone()
                if not row:
                    return None

                framework = self._row_to_framework(row)

                # Load nested data
                framework.metadata = await self._fetch_framework_metadata(cursor, framework.id)
                framework.implementation = await self._fetch_framework_implementation(cursor, framework.id)

                return framework

    async def resolve_frameworks(
        self,
        language: str | None = None,
        language_family: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Framework]:
        """Resolve list of frameworks with optional filtering.

        Args:
            language: Filter by language (e.g., 'Python')
            language_family: Filter by family (e.g., 'dynamic')
            limit: Result limit
            offset: Result offset for pagination

        Returns:
            List of Framework objects with nested data
        """
        query = """
            SELECT f.id, f.identifier, f.name, f.language,
                   f.language_family, f.runtime, f.version
            FROM tb_framework f WHERE TRUE
        """
        params = []

        if language:
            params.append(language)
            query += f" AND f.language = %s"

        if language_family:
            params.append(language_family)
            query += f" AND f.language_family = %s"

        params.extend([limit, offset])
        query += f" LIMIT %s OFFSET %s"

        if hasattr(self.db, "cursor"):
            # Synchronous interface
            cursor = self.db.cursor()
            try:
                cursor.execute(query, params)
                rows = cursor.fetchall()

                frameworks = []
                for row in rows:
                    framework = self._row_to_framework(row)
                    framework.metadata = self._fetch_framework_metadata(cursor, framework.id)
                    framework.implementation = self._fetch_framework_implementation(cursor, framework.id)
                    frameworks.append(framework)

                return frameworks
            finally:
                cursor.close()
        else:
            # Async interface
            async with self.db.connection() as conn:
                cursor = await conn.cursor()
                await cursor.execute(query, params)
                rows = await cursor.fetchall()

                frameworks = []
                for row in rows:
                    framework = self._row_to_framework(row)
                    framework.metadata = await self._fetch_framework_metadata(cursor, framework.id)
                    framework.implementation = await self._fetch_framework_implementation(cursor, framework.id)
                    frameworks.append(framework)

                return frameworks

    # ========================================================================
    # BENCHMARK RUN QUERIES
    # ========================================================================

    async def resolve_benchmark_run(self, id: str) -> BenchmarkRun | None:
        """Resolve single benchmark run by ID with all nested data.

        Args:
            id: BenchmarkRun UUID

        Returns:
            BenchmarkRun object with complete nested structure
        """
        if hasattr(self.db, "cursor"):
            # Synchronous interface
            cursor = self.db.cursor()
            try:
                # Get run from composition view
                cursor.execute(
                    """
                    SELECT id, identifier, status, start_time, end_time,
                           duration_seconds, jmeter_file_path,
                           framework, suite, workload, load_profile
                    FROM tv_benchmark_run WHERE id = %s
                    """,
                    (id,),
                )
                run_row = cursor.fetchone()

                if not run_row:
                    return None

                run = self._row_to_benchmark_run(run_row)

                # Fetch detailed metrics and analysis
                run.metrics = self._fetch_performance_metrics(cursor, id)
                run.resource_profile = self._fetch_resource_profile(cursor, id)
                run.cost_analysis = self._fetch_cost_analysis(cursor, id)
                run.efficiency_ranking = self._fetch_efficiency_ranking(cursor, id)
                run.performance_characterization = self._fetch_performance_characterization(cursor, id)
                run.regression_detection = self._fetch_regression_detection(cursor, id)
                run.code_snapshots = self._fetch_code_snapshots(cursor, id)
                run.reproducibility_manifest = self._fetch_reproducibility_manifest(cursor, id)

                return run
            finally:
                cursor.close()
        else:
            # Async interface
            async with self.db.connection() as conn:
                cursor = await conn.cursor()
                await cursor.execute(
                    """
                    SELECT id, identifier, status, start_time, end_time,
                           duration_seconds, jmeter_file_path,
                           framework, suite, workload, load_profile
                    FROM tv_benchmark_run WHERE id = %s
                    """,
                    (id,),
                )
                run_row = await cursor.fetchone()

                if not run_row:
                    return None

                run = self._row_to_benchmark_run(run_row)

                # Fetch detailed metrics and analysis
                run.metrics = await self._fetch_performance_metrics(cursor, id)
                run.resource_profile = await self._fetch_resource_profile(cursor, id)
                run.cost_analysis = await self._fetch_cost_analysis(cursor, id)
                run.efficiency_ranking = await self._fetch_efficiency_ranking(cursor, id)
                run.performance_characterization = await self._fetch_performance_characterization(cursor, id)
                run.regression_detection = await self._fetch_regression_detection(cursor, id)
                run.code_snapshots = await self._fetch_code_snapshots(cursor, id)
                run.reproducibility_manifest = await self._fetch_reproducibility_manifest(cursor, id)

                return run

    # ========================================================================
    # COST ANALYSIS & CALCULATION
    # ========================================================================

    async def resolve_cost_analysis(
        self,
        benchmark_run_id: str,
    ) -> CostAnalysisResult | None:
        """Resolve cost analysis for a benchmark run.

        Calculates costs if not already stored.

        Args:
            benchmark_run_id: BenchmarkRun UUID

        Returns:
            CostAnalysisResult with multi-cloud breakdown
        """
        if hasattr(self.db, "cursor"):
            # Synchronous interface
            cursor = self.db.cursor()
            try:
                # Get benchmark run
                cursor.execute(
                    "SELECT id FROM tv_benchmark_run WHERE id = %s",
                    (benchmark_run_id,),
                )
                run = cursor.fetchone()

                if not run:
                    return None

                # Check if analysis already exists
                cursor.execute(
                    """
                    SELECT id, recommended_cloud_provider, recommended_instance_type,
                           cost_breakdowns, efficiency_ranking
                    FROM tv_cost_analysis
                    WHERE id = (SELECT id FROM tb_cost_analysis
                                WHERE fk_run = (SELECT pk_run FROM tb_benchmark_run WHERE id = %s))
                    """,
                    (benchmark_run_id,),
                )
                analysis = cursor.fetchone()

                if analysis:
                    return self._row_to_cost_analysis(analysis)

                # Calculate new analysis
                return self._calculate_cost_analysis(cursor, benchmark_run_id)
            finally:
                cursor.close()
        else:
            # Async interface
            async with self.db.connection() as conn:
                cursor = await conn.cursor()
                await cursor.execute(
                    "SELECT id FROM tv_benchmark_run WHERE id = %s",
                    (benchmark_run_id,),
                )
                run = await cursor.fetchone()

                if not run:
                    return None

                await cursor.execute(
                    """
                    SELECT id, recommended_cloud_provider, recommended_instance_type,
                           cost_breakdowns, efficiency_ranking
                    FROM tv_cost_analysis
                    WHERE id = (SELECT id FROM tb_cost_analysis
                                WHERE fk_run = (SELECT pk_run FROM tb_benchmark_run WHERE id = %s))
                    """,
                    (benchmark_run_id,),
                )
                analysis = await cursor.fetchone()

                if analysis:
                    return self._row_to_cost_analysis(analysis)

                # Calculate new analysis
                return await self._calculate_cost_analysis(cursor, benchmark_run_id)

    # ========================================================================
    # HELPER METHODS: Row Conversion
    # ========================================================================

    def _row_to_framework(self, row: tuple | dict) -> Framework:
        """Convert database row to Framework object."""
        if isinstance(row, dict):
            return Framework(
                id=str(row["id"]),
                name=row["name"],
                language=row["language"],
                language_family=row["language_family"],
                runtime=row["runtime"],
                version=row["version"],
            )
        else:
            # Tuple format: (id, identifier, name, language, language_family, runtime, version)
            return Framework(
                id=str(row[0]),
                name=row[2],
                language=row[3],
                language_family=row[4],
                runtime=row[5],
                version=row[6],
            )

    def _row_to_benchmark_run(self, row: tuple | dict) -> BenchmarkRun:
        """Convert database row to BenchmarkRun object."""
        if isinstance(row, dict):
            framework_data = row.get("framework", {})
            suite_data = row.get("suite", {})
            workload_data = row.get("workload", {})
            load_profile_data = row.get("load_profile", {})

            return BenchmarkRun(
                id=str(row["id"]),
                status=row["status"],
                start_time=row["start_time"].isoformat() if row["start_time"] else None,
                end_time=row["end_time"].isoformat() if row["end_time"] else None,
                duration_seconds=row.get("duration_seconds"),
                jmeter_file_path=row.get("jmeter_file_path"),
                framework=Framework(**framework_data) if framework_data else None,
                suite=BenchmarkSuite(**suite_data) if suite_data else None,
                workload=Workload(**workload_data) if workload_data else None,
                load_profile=LoadProfile(**load_profile_data) if load_profile_data else None,
            )
        else:
            # Tuple format from composition view
            return BenchmarkRun(
                id=str(row[0]),
                status=row[2],
                start_time=row[3].isoformat() if row[3] else None,
                end_time=row[4].isoformat() if row[4] else None,
                duration_seconds=row[5],
                jmeter_file_path=row[6],
            )

    # ========================================================================
    # HELPER METHODS: Data Fetching
    # ========================================================================

    def _fetch_framework_metadata(
        self,
        cursor,
        framework_id: str,
    ) -> FrameworkMetadata | None:
        """Fetch framework metadata."""
        cursor.execute(
            """
            SELECT id, identifier, type_safety, paradigm, concurrency_model,
                   garbage_collection, memory_management, startup_time_ms
            FROM tb_framework_metadata
            WHERE fk_framework = (SELECT pk_framework FROM tb_framework WHERE id = %s)
            """,
            (framework_id,),
        )
        row = cursor.fetchone()

        if not row:
            return None

        return FrameworkMetadata(
            type_safety=row[2],
            paradigm=row[3],
            concurrency_model=row[4],
            garbage_collection=row[5],
            memory_management=row[6],
            startup_time_ms=row[7],
        )

    def _fetch_framework_implementation(
        self,
        cursor,
        framework_id: str,
    ) -> FrameworkImplementation | None:
        """Fetch framework implementation with source code visibility."""
        cursor.execute(
            """
            SELECT id, identifier, git_repository_url, git_commit_hash,
                   git_branch, git_tag, total_lines_of_code
            FROM tb_framework_implementation
            WHERE fk_framework = (SELECT pk_framework FROM tb_framework WHERE id = %s)
            """,
            (framework_id,),
        )
        row = cursor.fetchone()

        if not row:
            return None

        # Fetch source files
        cursor.execute(
            """
            SELECT id, identifier, file_path, lines_of_code, file_content
            FROM tb_framework_file
            WHERE fk_implementation = (SELECT pk_implementation FROM tb_framework_implementation
                                       WHERE fk_framework = (SELECT pk_framework FROM tb_framework WHERE id = %s))
            ORDER BY file_path
            """,
            (framework_id,),
        )
        files_rows = cursor.fetchall()

        source_files = []
        for file_row in files_rows:
            source_files.append(
                FrameworkFile(
                    file_path=file_row[2],
                    lines_of_code=file_row[3],
                    file_content=file_row[4],
                )
            )

        return FrameworkImplementation(
            git_repository_url=row[2],
            git_commit_hash=row[3],
            git_branch=row[4],
            git_tag=row[5],
            total_lines_of_code=row[6],
            source_files=source_files if source_files else None,
        )

    def _fetch_performance_metrics(
        self,
        cursor,
        run_id: str,
    ) -> PerformanceMetrics | None:
        """Fetch comprehensive performance metrics including distributions."""
        cursor.execute(
            """
            SELECT total_requests, total_errors, error_rate, requests_per_second,
                   latency_min, latency_p50, latency_p95, latency_p99, latency_p999,
                   latency_max, latency_mean, latency_stddev
            FROM tb_performance_metrics
            WHERE fk_run = (SELECT pk_run FROM tb_benchmark_run WHERE id = %s)
            """,
            (run_id,),
        )
        row = cursor.fetchone()

        if not row:
            return None

        return PerformanceMetrics(
            total_requests=row[0],
            total_errors=row[1],
            error_rate=float(row[2]) if row[2] else 0,
            requests_per_second=float(row[3]),
            latency_min=row[4],
            latency_p50=row[5],
            latency_p95=row[6],
            latency_p99=row[7],
            latency_p999=row[8],
            latency_max=row[9],
            latency_mean=row[10],
            latency_stddev=row[11],
        )

    def _fetch_resource_profile(
        self,
        cursor,
        run_id: str,
    ) -> ResourceProfile | None:
        """Fetch calculated resource profile."""
        cursor.execute(
            """
            SELECT cpu_cores_required, cpu_cores_with_headroom, headroom_percent,
                   rps_per_core, application_baseline_mb, connection_pool_memory_mb,
                   memory_buffer_percent, memory_required_gb, application_storage_gb,
                   data_growth_gb_per_month, log_storage_gb_per_month, bandwidth_mbps,
                   data_transfer_gb_per_month, total_monthly_storage_gb
            FROM tb_resource_profile
            WHERE fk_run = (SELECT pk_run FROM tb_benchmark_run WHERE id = %s)
            """,
            (run_id,),
        )
        row = cursor.fetchone()

        if not row:
            return None

        return ResourceProfile(
            cpu_cores_required=row[0],
            cpu_cores_with_headroom=row[1],
            headroom_percent=float(row[2]),
            rps_per_core=row[3],
            application_baseline_mb=row[4],
            connection_pool_memory_mb=row[5],
            memory_buffer_percent=float(row[6]),
            memory_required_gb=float(row[7]),
            application_storage_gb=float(row[8]),
            data_growth_gb_per_month=float(row[9]),
            log_storage_gb_per_month=float(row[10]),
            bandwidth_mbps=float(row[11]),
            data_transfer_gb_per_month=float(row[12]),
            total_monthly_storage_gb=float(row[13]),
        )

    def _fetch_cost_analysis(
        self,
        cursor,
        run_id: str,
    ) -> CostAnalysisResult | None:
        """Fetch cost analysis from composition view."""
        cursor.execute(
            """
            SELECT recommended_cloud_provider, recommended_instance_type,
                   cost_breakdowns, efficiency_ranking
            FROM tv_cost_analysis
            WHERE fk_run = (SELECT pk_run FROM tb_benchmark_run WHERE id = %s)
            """,
            (run_id,),
        )
        row = cursor.fetchone()

        if not row:
            return None

        return self._row_to_cost_analysis(row)

    def _fetch_efficiency_ranking(
        self,
        cursor,
        run_id: str,
    ) -> EfficiencyRanking | None:
        """Fetch efficiency ranking."""
        cursor.execute(
            """
            SELECT efficiency_score, cost_component, latency_component,
                   throughput_component, reliability_component, suite_rank
            FROM tb_efficiency_ranking
            WHERE fk_run = (SELECT pk_run FROM tb_benchmark_run WHERE id = %s)
            """,
            (run_id,),
        )
        row = cursor.fetchone()

        if not row:
            return None

        return EfficiencyRanking(
            efficiency_score=float(row[0]),
            cost_component=float(row[1]),
            latency_component=float(row[2]),
            throughput_component=float(row[3]),
            reliability_component=float(row[4]),
            suite_rank=row[5],
        )

    def _fetch_performance_characterization(
        self,
        cursor,
        run_id: str,
    ) -> PerformanceCharacterization | None:
        """Fetch performance characterization."""
        cursor.execute(
            """
            SELECT scales_linearly_to, optimal_connections, gc_friendly,
                   cache_friendly, bottleneck_type, bottleneck_description
            FROM tb_performance_characterization
            WHERE fk_run = (SELECT pk_run FROM tb_benchmark_run WHERE id = %s)
            """,
            (run_id,),
        )
        row = cursor.fetchone()

        if not row:
            return None

        return PerformanceCharacterization(
            scales_linearly_to=row[0],
            optimal_connections=row[1],
            gc_friendly=row[2],
            cache_friendly=row[3],
            bottleneck_type=row[4],
            bottleneck_description=row[5],
        )

    def _fetch_regression_detection(
        self,
        cursor,
        run_id: str,
    ) -> RegressionDetection | None:
        """Fetch regression detection results."""
        cursor.execute(
            """
            SELECT is_regression, regression_severity, latency_change_percent,
                   throughput_change_percent
            FROM tb_regression_detection
            WHERE fk_run = (SELECT pk_run FROM tb_benchmark_run WHERE id = %s)
            """,
            (run_id,),
        )
        row = cursor.fetchone()

        if not row:
            return None

        return RegressionDetection(
            is_regression=row[0],
            regression_severity=row[1],
            latency_change_percent=float(row[2]) if row[2] else None,
            throughput_change_percent=float(row[3]) if row[3] else None,
        )

    def _fetch_code_snapshots(
        self,
        cursor,
        run_id: str,
    ) -> list[CodeSnapshot] | None:
        """Fetch code snapshots taken at benchmark time."""
        cursor.execute(
            """
            SELECT id, identifier, snapshot_type, git_commit_hash,
                   git_branch, content_hash
            FROM tb_code_snapshot
            WHERE fk_run = (SELECT pk_run FROM tb_benchmark_run WHERE id = %s)
            ORDER BY snapshot_type
            """,
            (run_id,),
        )
        rows = cursor.fetchall()

        if not rows:
            return None

        snapshots = []
        for row in rows:
            snapshots.append(
                CodeSnapshot(
                    snapshot_type=row[2],
                    git_commit_hash=row[3],
                    git_branch=row[4],
                    content_hash=row[5],
                )
            )

        return snapshots if snapshots else None

    def _fetch_reproducibility_manifest(
        self,
        cursor,
        run_id: str,
    ) -> ReproducibilityManifest | None:
        """Fetch reproducibility manifest for exact run reproduction."""
        cursor.execute(
            """
            SELECT manifest_data, manifest_version, checksum
            FROM tb_reproducibility_manifest
            WHERE fk_run = (SELECT pk_run FROM tb_benchmark_run WHERE id = %s)
            """,
            (run_id,),
        )
        row = cursor.fetchone()

        if not row:
            return None

        manifest_data = row[0] if isinstance(row[0], dict) else json.loads(row[0])

        return ReproducibilityManifest(
            manifest_data=manifest_data,
            manifest_version=row[1],
            checksum=row[2],
        )

    # ========================================================================
    # HELPER METHODS: Async Versions
    # ========================================================================

    async def _fetch_framework_metadata(
        self,
        cursor,
        framework_id: str,
    ) -> FrameworkMetadata | None:
        """Fetch framework metadata (async)."""
        await cursor.execute(
            """
            SELECT id, identifier, type_safety, paradigm, concurrency_model,
                   garbage_collection, memory_management, startup_time_ms
            FROM tb_framework_metadata
            WHERE fk_framework = (SELECT pk_framework FROM tb_framework WHERE id = %s)
            """,
            (framework_id,),
        )
        row = await cursor.fetchone()

        if not row:
            return None

        return FrameworkMetadata(
            type_safety=row[2],
            paradigm=row[3],
            concurrency_model=row[4],
            garbage_collection=row[5],
            memory_management=row[6],
            startup_time_ms=row[7],
        )

    async def _fetch_framework_implementation(
        self,
        cursor,
        framework_id: str,
    ) -> FrameworkImplementation | None:
        """Fetch framework implementation with source code visibility (async)."""
        await cursor.execute(
            """
            SELECT id, identifier, git_repository_url, git_commit_hash,
                   git_branch, git_tag, total_lines_of_code
            FROM tb_framework_implementation
            WHERE fk_framework = (SELECT pk_framework FROM tb_framework WHERE id = %s)
            """,
            (framework_id,),
        )
        row = await cursor.fetchone()

        if not row:
            return None

        # Fetch source files
        await cursor.execute(
            """
            SELECT id, identifier, file_path, lines_of_code, file_content
            FROM tb_framework_file
            WHERE fk_implementation = (SELECT pk_implementation FROM tb_framework_implementation
                                       WHERE fk_framework = (SELECT pk_framework FROM tb_framework WHERE id = %s))
            ORDER BY file_path
            """,
            (framework_id,),
        )
        files_rows = await cursor.fetchall()

        source_files = []
        for file_row in files_rows:
            source_files.append(
                FrameworkFile(
                    file_path=file_row[2],
                    lines_of_code=file_row[3],
                    file_content=file_row[4],
                )
            )

        return FrameworkImplementation(
            git_repository_url=row[2],
            git_commit_hash=row[3],
            git_branch=row[4],
            git_tag=row[5],
            total_lines_of_code=row[6],
            source_files=source_files if source_files else None,
        )

    async def _fetch_performance_metrics(
        self,
        cursor,
        run_id: str,
    ) -> PerformanceMetrics | None:
        """Fetch performance metrics (async)."""
        await cursor.execute(
            """
            SELECT total_requests, total_errors, error_rate, requests_per_second,
                   latency_min, latency_p50, latency_p95, latency_p99, latency_p999,
                   latency_max, latency_mean, latency_stddev
            FROM tb_performance_metrics
            WHERE fk_run = (SELECT pk_run FROM tb_benchmark_run WHERE id = %s)
            """,
            (run_id,),
        )
        row = await cursor.fetchone()

        if not row:
            return None

        return PerformanceMetrics(
            total_requests=row[0],
            total_errors=row[1],
            error_rate=float(row[2]) if row[2] else 0,
            requests_per_second=float(row[3]),
            latency_min=row[4],
            latency_p50=row[5],
            latency_p95=row[6],
            latency_p99=row[7],
            latency_p999=row[8],
            latency_max=row[9],
            latency_mean=row[10],
            latency_stddev=row[11],
        )

    async def _fetch_resource_profile(
        self,
        cursor,
        run_id: str,
    ) -> ResourceProfile | None:
        """Fetch resource profile (async)."""
        await cursor.execute(
            """
            SELECT cpu_cores_required, cpu_cores_with_headroom, headroom_percent,
                   rps_per_core, application_baseline_mb, connection_pool_memory_mb,
                   memory_buffer_percent, memory_required_gb, application_storage_gb,
                   data_growth_gb_per_month, log_storage_gb_per_month, bandwidth_mbps,
                   data_transfer_gb_per_month, total_monthly_storage_gb
            FROM tb_resource_profile
            WHERE fk_run = (SELECT pk_run FROM tb_benchmark_run WHERE id = %s)
            """,
            (run_id,),
        )
        row = await cursor.fetchone()

        if not row:
            return None

        return ResourceProfile(
            cpu_cores_required=row[0],
            cpu_cores_with_headroom=row[1],
            headroom_percent=float(row[2]),
            rps_per_core=row[3],
            application_baseline_mb=row[4],
            connection_pool_memory_mb=row[5],
            memory_buffer_percent=float(row[6]),
            memory_required_gb=float(row[7]),
            application_storage_gb=float(row[8]),
            data_growth_gb_per_month=float(row[9]),
            log_storage_gb_per_month=float(row[10]),
            bandwidth_mbps=float(row[11]),
            data_transfer_gb_per_month=float(row[12]),
            total_monthly_storage_gb=float(row[13]),
        )

    async def _fetch_cost_analysis(
        self,
        cursor,
        run_id: str,
    ) -> CostAnalysisResult | None:
        """Fetch cost analysis (async)."""
        await cursor.execute(
            """
            SELECT recommended_cloud_provider, recommended_instance_type,
                   cost_breakdowns, efficiency_ranking
            FROM tv_cost_analysis
            WHERE fk_run = (SELECT pk_run FROM tb_benchmark_run WHERE id = %s)
            """,
            (run_id,),
        )
        row = await cursor.fetchone()

        if not row:
            return None

        return self._row_to_cost_analysis(row)

    async def _fetch_efficiency_ranking(
        self,
        cursor,
        run_id: str,
    ) -> EfficiencyRanking | None:
        """Fetch efficiency ranking (async)."""
        await cursor.execute(
            """
            SELECT efficiency_score, cost_component, latency_component,
                   throughput_component, reliability_component, suite_rank
            FROM tb_efficiency_ranking
            WHERE fk_run = (SELECT pk_run FROM tb_benchmark_run WHERE id = %s)
            """,
            (run_id,),
        )
        row = await cursor.fetchone()

        if not row:
            return None

        return EfficiencyRanking(
            efficiency_score=float(row[0]),
            cost_component=float(row[1]),
            latency_component=float(row[2]),
            throughput_component=float(row[3]),
            reliability_component=float(row[4]),
            suite_rank=row[5],
        )

    async def _fetch_performance_characterization(
        self,
        cursor,
        run_id: str,
    ) -> PerformanceCharacterization | None:
        """Fetch performance characterization (async)."""
        await cursor.execute(
            """
            SELECT scales_linearly_to, optimal_connections, gc_friendly,
                   cache_friendly, bottleneck_type, bottleneck_description
            FROM tb_performance_characterization
            WHERE fk_run = (SELECT pk_run FROM tb_benchmark_run WHERE id = %s)
            """,
            (run_id,),
        )
        row = await cursor.fetchone()

        if not row:
            return None

        return PerformanceCharacterization(
            scales_linearly_to=row[0],
            optimal_connections=row[1],
            gc_friendly=row[2],
            cache_friendly=row[3],
            bottleneck_type=row[4],
            bottleneck_description=row[5],
        )

    async def _fetch_regression_detection(
        self,
        cursor,
        run_id: str,
    ) -> RegressionDetection | None:
        """Fetch regression detection (async)."""
        await cursor.execute(
            """
            SELECT is_regression, regression_severity, latency_change_percent,
                   throughput_change_percent
            FROM tb_regression_detection
            WHERE fk_run = (SELECT pk_run FROM tb_benchmark_run WHERE id = %s)
            """,
            (run_id,),
        )
        row = await cursor.fetchone()

        if not row:
            return None

        return RegressionDetection(
            is_regression=row[0],
            regression_severity=row[1],
            latency_change_percent=float(row[2]) if row[2] else None,
            throughput_change_percent=float(row[3]) if row[3] else None,
        )

    async def _fetch_code_snapshots(
        self,
        cursor,
        run_id: str,
    ) -> list[CodeSnapshot] | None:
        """Fetch code snapshots (async)."""
        await cursor.execute(
            """
            SELECT id, identifier, snapshot_type, git_commit_hash,
                   git_branch, content_hash
            FROM tb_code_snapshot
            WHERE fk_run = (SELECT pk_run FROM tb_benchmark_run WHERE id = %s)
            ORDER BY snapshot_type
            """,
            (run_id,),
        )
        rows = await cursor.fetchall()

        if not rows:
            return None

        snapshots = []
        for row in rows:
            snapshots.append(
                CodeSnapshot(
                    snapshot_type=row[2],
                    git_commit_hash=row[3],
                    git_branch=row[4],
                    content_hash=row[5],
                )
            )

        return snapshots if snapshots else None

    async def _fetch_reproducibility_manifest(
        self,
        cursor,
        run_id: str,
    ) -> ReproducibilityManifest | None:
        """Fetch reproducibility manifest (async)."""
        await cursor.execute(
            """
            SELECT manifest_data, manifest_version, checksum
            FROM tb_reproducibility_manifest
            WHERE fk_run = (SELECT pk_run FROM tb_benchmark_run WHERE id = %s)
            """,
            (run_id,),
        )
        row = await cursor.fetchone()

        if not row:
            return None

        manifest_data = row[0] if isinstance(row[0], dict) else json.loads(row[0])

        return ReproducibilityManifest(
            manifest_data=manifest_data,
            manifest_version=row[1],
            checksum=row[2],
        )

    # ========================================================================
    # HELPER METHODS: Cost Analysis
    # ========================================================================

    def _calculate_cost_analysis(
        self,
        cursor,
        run_id: str,
    ) -> CostAnalysisResult:
        """Calculate cost analysis from benchmark run.

        Args:
            cursor: Database cursor
            run_id: Benchmark run UUID

        Returns:
            CostAnalysisResult with calculated costs
        """
        # Extract metrics from run
        cursor.execute(
            """
            SELECT requests_per_second FROM tb_performance_metrics
            WHERE fk_run = (SELECT pk_run FROM tb_benchmark_run WHERE id = %s)
            """,
            (run_id,),
        )
        metrics_row = cursor.fetchone()

        if not metrics_row:
            raise ValueError(f"No metrics found for run {run_id}")

        # Load projection from metrics
        rps = float(metrics_row[0])
        projection = self.load_profiler.project_from_jmeter(rps)

        # Calculate resource requirements
        calc = ResourceCalculator()
        requirements = calc.calculate_requirements(projection)

        # Calculate costs for each cloud provider
        cost_breakdowns = []
        for provider in ["aws", "gcp", "azure"]:
            breakdown = self._calculate_cloud_cost(provider, requirements)
            cost_breakdowns.append(breakdown)

        # Determine cheapest provider
        cheapest = min(
            cost_breakdowns,
            key=lambda x: x.total_monthly_cost,
        )

        # Store in database
        analysis_id = str(uuid.uuid4())
        identifier = generate_identifier("cost", "run", run_id)

        cursor.execute(
            "SELECT pk_run FROM tb_benchmark_run WHERE id = %s",
            (run_id,),
        )
        pk_run = cursor.fetchone()[0]

        cursor.execute(
            """
            INSERT INTO tb_cost_analysis
            (id, identifier, fk_run, recommended_cloud_provider, recommended_instance_type)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (analysis_id, identifier, pk_run, cheapest.cloud_provider, cheapest.instance_type),
        )

        # Store cost breakdowns
        cursor.execute(
            "SELECT pk_analysis FROM tb_cost_analysis WHERE id = %s",
            (analysis_id,),
        )
        pk_analysis = cursor.fetchone()[0]

        for breakdown in cost_breakdowns:
            breakdown_id = str(uuid.uuid4())
            breakdown_identifier = generate_identifier("breakdown", "analysis", analysis_id, breakdown.cloud_provider)

            cursor.execute(
                """
                INSERT INTO tb_cost_breakdown (
                    id, identifier, fk_analysis, cloud_provider, compute_cost, database_cost,
                    storage_cost, data_transfer_cost, monitoring_cost, contingency_cost,
                    total_monthly_cost, total_yearly_cost, yearly_with_1yr_reserved,
                    yearly_with_3yr_reserved, cost_per_request, requests_per_dollar,
                    instance_type, instance_hourly_rate
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    breakdown_id,
                    breakdown_identifier,
                    pk_analysis,
                    breakdown.cloud_provider,
                    breakdown.compute_cost,
                    breakdown.database_cost,
                    breakdown.storage_cost,
                    breakdown.data_transfer_cost,
                    breakdown.monitoring_cost,
                    breakdown.contingency_cost,
                    breakdown.total_monthly_cost,
                    breakdown.total_yearly_cost,
                    breakdown.yearly_with_1yr_reserved,
                    breakdown.yearly_with_3yr_reserved,
                    breakdown.cost_per_request,
                    breakdown.requests_per_dollar,
                    breakdown.instance_type,
                    breakdown.instance_hourly_rate,
                ),
            )

        return CostAnalysisResult(
            recommended_cloud_provider=cheapest.cloud_provider,
            recommended_instance_type=cheapest.instance_type,
            cost_breakdowns=cost_breakdowns,
        )

    async def _calculate_cost_analysis(
        self,
        cursor,
        run_id: str,
    ) -> CostAnalysisResult:
        """Calculate cost analysis from benchmark run (async)."""
        # Extract metrics from run
        await cursor.execute(
            """
            SELECT requests_per_second FROM tb_performance_metrics
            WHERE fk_run = (SELECT pk_run FROM tb_benchmark_run WHERE id = %s)
            """,
            (run_id,),
        )
        metrics_row = await cursor.fetchone()

        if not metrics_row:
            raise ValueError(f"No metrics found for run {run_id}")

        # Load projection from metrics
        rps = float(metrics_row[0])
        projection = self.load_profiler.project_from_jmeter(rps)

        # Calculate resource requirements
        calc = ResourceCalculator()
        requirements = calc.calculate_requirements(projection)

        # Calculate costs for each cloud provider
        cost_breakdowns = []
        for provider in ["aws", "gcp", "azure"]:
            breakdown = self._calculate_cloud_cost(provider, requirements)
            cost_breakdowns.append(breakdown)

        # Determine cheapest provider
        cheapest = min(
            cost_breakdowns,
            key=lambda x: x.total_monthly_cost,
        )

        # Store in database
        analysis_id = str(uuid.uuid4())
        identifier = generate_identifier("cost", "run", run_id)

        await cursor.execute(
            "SELECT pk_run FROM tb_benchmark_run WHERE id = %s",
            (run_id,),
        )
        pk_run = (await cursor.fetchone())[0]

        await cursor.execute(
            """
            INSERT INTO tb_cost_analysis
            (id, identifier, fk_run, recommended_cloud_provider, recommended_instance_type)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (analysis_id, identifier, pk_run, cheapest.cloud_provider, cheapest.instance_type),
        )

        # Store cost breakdowns
        await cursor.execute(
            "SELECT pk_analysis FROM tb_cost_analysis WHERE id = %s",
            (analysis_id,),
        )
        pk_analysis = (await cursor.fetchone())[0]

        for breakdown in cost_breakdowns:
            breakdown_id = str(uuid.uuid4())
            breakdown_identifier = generate_identifier("breakdown", "analysis", analysis_id, breakdown.cloud_provider)

            await cursor.execute(
                """
                INSERT INTO tb_cost_breakdown (
                    id, identifier, fk_analysis, cloud_provider, compute_cost, database_cost,
                    storage_cost, data_transfer_cost, monitoring_cost, contingency_cost,
                    total_monthly_cost, total_yearly_cost, yearly_with_1yr_reserved,
                    yearly_with_3yr_reserved, cost_per_request, requests_per_dollar,
                    instance_type, instance_hourly_rate
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    breakdown_id,
                    breakdown_identifier,
                    pk_analysis,
                    breakdown.cloud_provider,
                    breakdown.compute_cost,
                    breakdown.database_cost,
                    breakdown.storage_cost,
                    breakdown.data_transfer_cost,
                    breakdown.monitoring_cost,
                    breakdown.contingency_cost,
                    breakdown.total_monthly_cost,
                    breakdown.total_yearly_cost,
                    breakdown.yearly_with_1yr_reserved,
                    breakdown.yearly_with_3yr_reserved,
                    breakdown.cost_per_request,
                    breakdown.requests_per_dollar,
                    breakdown.instance_type,
                    breakdown.instance_hourly_rate,
                ),
            )

        return CostAnalysisResult(
            recommended_cloud_provider=cheapest.cloud_provider,
            recommended_instance_type=cheapest.instance_type,
            cost_breakdowns=cost_breakdowns,
        )

    def _calculate_cloud_cost(
        self,
        provider: str,
        requirements,
    ) -> CloudCostBreakdown:
        """Calculate cloud cost for a provider."""
        # Get instance pricing
        instances = self.cost_config.get_compute_instances_for_cores(
            requirements.cpu_cores
        )
        if not instances:
            instances = self.cost_config.get_compute_instances_for_cores(2)
        instance = instances[0]

        # Get provider-specific pricing
        if provider == "aws":
            hourly = instance.aws_hourly
        elif provider == "gcp":
            hourly = instance.gcp_hourly
        else:  # azure
            hourly = instance.azure_hourly

        # Calculate monthly costs (730 hours/month = 365 days * 24 hours / 12 months)
        compute_cost = float(hourly) * 730
        database_cost = 45.0
        storage_cost = float(requirements.storage_gb) * 0.10
        data_transfer_cost = float(requirements.data_transfer_gb_per_month) * 0.09
        monitoring_cost = 5.0
        contingency = (
            compute_cost + database_cost + storage_cost + data_transfer_cost + monitoring_cost
        ) * 0.10

        total_monthly = (
            compute_cost
            + database_cost
            + storage_cost
            + data_transfer_cost
            + monitoring_cost
            + contingency
        )

        # Calculate yearly
        total_yearly = total_monthly * 12
        yearly_1yr = total_monthly * 12 * 0.60  # 40% discount
        yearly_3yr = total_monthly * 12 * 0.45  # 55% discount

        # Cost per request
        monthly_requests = 2_592_000  # 86,400 * 30
        cost_per_request = total_monthly / monthly_requests
        requests_per_dollar = int(1.0 / cost_per_request) if cost_per_request > 0 else 0

        return CloudCostBreakdown(
            cloud_provider=provider,
            compute_cost=compute_cost,
            database_cost=database_cost,
            storage_cost=storage_cost,
            data_transfer_cost=data_transfer_cost,
            monitoring_cost=monitoring_cost,
            contingency_cost=contingency,
            total_monthly_cost=total_monthly,
            total_yearly_cost=total_yearly,
            yearly_with_1yr_reserved=yearly_1yr,
            yearly_with_3yr_reserved=yearly_3yr,
            cost_per_request=cost_per_request,
            requests_per_dollar=requests_per_dollar,
            instance_type=instance.instance_id,
            instance_hourly_rate=hourly,
        )

    def _row_to_cost_analysis(self, row: tuple | dict) -> CostAnalysisResult:
        """Convert database row to CostAnalysisResult."""
        if isinstance(row, dict):
            cost_breakdowns = []
            if row.get("cost_breakdowns"):
                for breakdown_data in row["cost_breakdowns"]:
                    cost_breakdowns.append(CloudCostBreakdown(**breakdown_data))
            return CostAnalysisResult(
                recommended_cloud_provider=row["recommended_cloud_provider"],
                recommended_instance_type=row["recommended_instance_type"],
                cost_breakdowns=cost_breakdowns,
            )
        else:
            # Tuple from composition view
            cost_breakdowns = []
            if row[2]:  # cost_breakdowns
                for breakdown_data in row[2]:
                    cost_breakdowns.append(CloudCostBreakdown(**breakdown_data))
            return CostAnalysisResult(
                recommended_cloud_provider=row[0],
                recommended_instance_type=row[1],
                cost_breakdowns=cost_breakdowns,
            )
