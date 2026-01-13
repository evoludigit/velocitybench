"""FraiseQL Resolvers for Benchmark Analytics.

Implements resolver functions that:
1. Wrap Phase 1 cost calculation modules
2. Handle database persistence
3. Return properly typed FraiseQL objects

Uses psycopg3 with synchronous connection pool.
"""

from datetime import datetime
from typing import Any
import uuid

from cost_config import CostConfiguration
from load_profiler import LoadProfiler
from resource_calculator import ResourceCalculator
from fraiseql_types import (
    Framework,
    BenchmarkSuite,
    Workload,
    LoadProfile as LoadProfileType,
    BenchmarkRun,
    PerformanceMetrics,
    ResourceProfile,
    CostAnalysisResult,
    CloudCostBreakdown,
    EfficiencyRanking,
)


class BenchmarkResolvers:
    """Resolver functions for benchmark analytics queries.

    Uses psycopg3 connection pool with cursor context managers.
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
            Framework object or None if not found
        """
        # For testing with psycopg2-compatible interface
        if hasattr(self.db, "cursor"):
            # Synchronous interface (test)
            cursor = self.db.cursor()
            try:
                if id:
                    cursor.execute(
                        "SELECT id, name, language, language_family, runtime, version, repository_url, documentation_url FROM tb_framework WHERE id = %s",
                        (id,),
                    )
                elif name:
                    cursor.execute(
                        "SELECT id, name, language, language_family, runtime, version, repository_url, documentation_url FROM tb_framework WHERE name = %s",
                        (name,),
                    )
                else:
                    return None

                row = cursor.fetchone()
                if not row:
                    return None

                return self._row_to_framework(row)
            finally:
                cursor.close()
        else:
            # Async interface (psycopg3)
            async with self.db.connection() as conn:
                if id:
                    cursor = await conn.cursor()
                    await cursor.execute(
                        "SELECT id, name, language, language_family, runtime, version, repository_url, documentation_url FROM tb_framework WHERE id = %s",
                        (id,),
                    )
                elif name:
                    cursor = await conn.cursor()
                    await cursor.execute(
                        "SELECT id, name, language, language_family, runtime, version, repository_url, documentation_url FROM tb_framework WHERE name = %s",
                        (name,),
                    )
                else:
                    return None

                row = await cursor.fetchone()
                if not row:
                    return None

                return self._row_to_framework(row)

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
            List of Framework objects
        """
        query = "SELECT id, name, language, language_family, runtime, version, repository_url, documentation_url FROM tb_framework WHERE TRUE"
        params = []

        if language:
            params.append(language)
            query += f" AND language = %s"

        if language_family:
            params.append(language_family)
            query += f" AND language_family = %s"

        params.extend([limit, offset])
        query += f" LIMIT %s OFFSET %s"

        if hasattr(self.db, "cursor"):
            # Synchronous interface
            cursor = self.db.cursor()
            try:
                cursor.execute(query, params)
                rows = cursor.fetchall()
                return [self._row_to_framework(row) for row in rows]
            finally:
                cursor.close()
        else:
            # Async interface
            async with self.db.connection() as conn:
                cursor = await conn.cursor()
                await cursor.execute(query, params)
                rows = await cursor.fetchall()
                return [self._row_to_framework(row) for row in rows]

    # ========================================================================
    # BENCHMARK RUN QUERIES
    # ========================================================================

    async def resolve_benchmark_run(self, id: str) -> BenchmarkRun | None:
        """Resolve single benchmark run by ID.

        Args:
            id: BenchmarkRun UUID

        Returns:
            BenchmarkRun object with nested data
        """
        if hasattr(self.db, "cursor"):
            # Synchronous interface
            cursor = self.db.cursor()
            try:
                # Get run from composition view
                cursor.execute(
                    "SELECT id, status, start_time, end_time, duration_seconds, jmeter_file_path, framework, suite, workload, load_profile FROM tv_benchmark_run WHERE id = %s",
                    (id,),
                )
                run_row = cursor.fetchone()

                if not run_row:
                    return None

                run = self._row_to_benchmark_run(run_row)

                # Fetch nested data
                run.metrics = self._fetch_performance_metrics(cursor, id)
                run.resource_profile = self._fetch_resource_profile(cursor, id)
                run.cost_analysis = self._fetch_cost_analysis(cursor, id)
                run.efficiency_ranking = self._fetch_efficiency_ranking(cursor, id)

                return run
            finally:
                cursor.close()
        else:
            # Async interface
            async with self.db.connection() as conn:
                cursor = await conn.cursor()
                await cursor.execute(
                    "SELECT id, status, start_time, end_time, duration_seconds, jmeter_file_path, framework, suite, workload, load_profile FROM tv_benchmark_run WHERE id = %s",
                    (id,),
                )
                run_row = await cursor.fetchone()

                if not run_row:
                    return None

                run = self._row_to_benchmark_run(run_row)

                # Fetch nested data
                run.metrics = await self._fetch_performance_metrics(cursor, id)
                run.resource_profile = await self._fetch_resource_profile(cursor, id)
                run.cost_analysis = await self._fetch_cost_analysis(cursor, id)
                run.efficiency_ranking = await self._fetch_efficiency_ranking(cursor, id)

                return run

    async def resolve_benchmark_runs(
        self,
        suite_id: str,
        framework_id: str | None = None,
        workload_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[BenchmarkRun]:
        """Resolve benchmark runs with filtering.

        Args:
            suite_id: Benchmark suite UUID (required)
            framework_id: Filter by framework UUID
            workload_id: Filter by workload UUID
            status: Filter by status
            limit: Result limit

        Returns:
            List of BenchmarkRun objects
        """
        query = """
            SELECT r.id, r.status, r.start_time, r.end_time, r.duration_seconds,
                   r.jmeter_file_path, r.framework, r.suite, r.workload, r.load_profile
            FROM tv_benchmark_run r
            WHERE r.suite->>'id' = %s
        """
        params = [suite_id]

        if framework_id:
            params.append(framework_id)
            query += f" AND r.framework->>'id' = %s"

        if workload_id:
            params.append(workload_id)
            query += f" AND r.workload->>'id' = %s"

        if status:
            params.append(status)
            query += f" AND r.status = %s"

        params.append(limit)
        query += f" LIMIT %s"

        if hasattr(self.db, "cursor"):
            # Synchronous interface
            cursor = self.db.cursor()
            try:
                cursor.execute(query, params)
                rows = cursor.fetchall()
                return [self._row_to_benchmark_run(row) for row in rows]
            finally:
                cursor.close()
        else:
            # Async interface
            async with self.db.connection() as conn:
                cursor = await conn.cursor()
                await cursor.execute(query, params)
                rows = await cursor.fetchall()
                return [self._row_to_benchmark_run(row) for row in rows]

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
                    "SELECT * FROM tv_benchmark_run WHERE id = %s",
                    (benchmark_run_id,),
                )
                run = cursor.fetchone()

                if not run:
                    return None

                # Check if analysis already exists
                cursor.execute(
                    "SELECT * FROM tv_cost_analysis WHERE fk_run = (SELECT pk_run FROM tb_benchmark_run WHERE id = %s)",
                    (benchmark_run_id,),
                )
                analysis = cursor.fetchone()

                if analysis:
                    return self._row_to_cost_analysis(analysis)

                # Calculate new analysis
                return self._calculate_cost_analysis(cursor, run)
            finally:
                cursor.close()
        else:
            # Async interface
            async with self.db.connection() as conn:
                cursor = await conn.cursor()
                await cursor.execute(
                    "SELECT * FROM tv_benchmark_run WHERE id = %s",
                    (benchmark_run_id,),
                )
                run = await cursor.fetchone()

                if not run:
                    return None

                await cursor.execute(
                    "SELECT * FROM tv_cost_analysis WHERE fk_run = (SELECT pk_run FROM tb_benchmark_run WHERE id = %s)",
                    (benchmark_run_id,),
                )
                analysis = await cursor.fetchone()

                if analysis:
                    return self._row_to_cost_analysis(analysis)

                # Calculate new analysis
                return await self._calculate_cost_analysis(cursor, run)

    def _calculate_cost_analysis(
        self,
        cursor,
        run_row: tuple | dict,
    ) -> CostAnalysisResult:
        """Calculate cost analysis from benchmark run.

        Args:
            cursor: Database cursor
            run_row: Benchmark run row from tv_benchmark_run view

        Returns:
            CostAnalysisResult with calculated costs
        """
        # Extract run ID
        run_id = run_row[0] if isinstance(run_row, tuple) else run_row["id"]

        # Extract metrics from run
        cursor.execute(
            "SELECT * FROM tb_performance_metrics WHERE fk_run = (SELECT pk_run FROM tb_benchmark_run WHERE id = %s)",
            (run_id,),
        )
        metrics_row = cursor.fetchone()

        if not metrics_row:
            raise ValueError(f"No metrics found for run {run_id}")

        # Load projection from metrics
        rps = float(metrics_row[4])  # requests_per_second is at index 4
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
        cursor.execute(
            "SELECT pk_run FROM tb_benchmark_run WHERE id = %s",
            (run_id,),
        )
        pk_run = cursor.fetchone()[0]

        cursor.execute(
            "INSERT INTO tb_cost_analysis (id, fk_run, recommended_cloud_provider, recommended_instance_type) VALUES (%s, %s, %s, %s)",
            (analysis_id, pk_run, cheapest.cloud_provider, cheapest.instance_type),
        )

        # Store cost breakdowns
        cursor.execute(
            "SELECT pk_analysis FROM tb_cost_analysis WHERE id = %s",
            (analysis_id,),
        )
        pk_analysis = cursor.fetchone()[0]

        for breakdown in cost_breakdowns:
            cursor.execute(
                """
                INSERT INTO tb_cost_breakdown (
                    fk_analysis, cloud_provider, compute_cost, database_cost,
                    storage_cost, data_transfer_cost, monitoring_cost, contingency_cost,
                    total_monthly_cost, total_yearly_cost, yearly_with_1yr_reserved,
                    yearly_with_3yr_reserved, cost_per_request, requests_per_dollar,
                    instance_type, instance_hourly_rate
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
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
        """Calculate cloud cost for a provider.

        Args:
            provider: "aws", "gcp", or "azure"
            requirements: ResourceRequirements from Phase 1

        Returns:
            CloudCostBreakdown with calculated costs
        """
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

    # ========================================================================
    # HELPER METHODS
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
                repository_url=row.get("repository_url"),
                documentation_url=row.get("documentation_url"),
            )
        else:
            # Tuple format: (id, name, language, language_family, runtime, version, repo_url, doc_url)
            return Framework(
                id=str(row[0]),
                name=row[1],
                language=row[2],
                language_family=row[3],
                runtime=row[4],
                version=row[5],
                repository_url=row[6] if len(row) > 6 else None,
                documentation_url=row[7] if len(row) > 7 else None,
            )

    def _row_to_benchmark_run(self, row: tuple | dict) -> BenchmarkRun:
        """Convert database row to BenchmarkRun object."""
        if isinstance(row, dict):
            framework_data = row.get("framework", {})
            suite_data = row.get("suite", {})
            workload_data = row.get("workload", {})
            load_profile_data = row.get("load_profile", {})

            framework = Framework(**framework_data) if framework_data else None
            suite = BenchmarkSuite(**suite_data) if suite_data else None
            workload = Workload(**workload_data) if workload_data else None
            load_profile = LoadProfileType(**load_profile_data) if load_profile_data else None
        else:
            # Tuple format from composition view
            framework = None
            suite = None
            workload = None
            load_profile = None

        return BenchmarkRun(
            id=str(row[0] if isinstance(row, tuple) else row["id"]),
            status=row[1] if isinstance(row, tuple) else row["status"],
            start_time=(row[2] if isinstance(row, tuple) else row["start_time"]).isoformat()
            if (row[2] if isinstance(row, tuple) else row["start_time"])
            else None,
            end_time=(row[3] if isinstance(row, tuple) else row["end_time"]).isoformat()
            if (row[3] if isinstance(row, tuple) else row["end_time"])
            else None,
            duration_seconds=row[4] if isinstance(row, tuple) else row.get("duration_seconds"),
            jmeter_file_path=row[5] if isinstance(row, tuple) else row.get("jmeter_file_path"),
            framework=framework,
            suite=suite,
            workload=workload,
            load_profile=load_profile,
        )

    def _fetch_performance_metrics(
        self,
        cursor,
        run_id: str,
    ) -> PerformanceMetrics | None:
        """Fetch performance metrics for a run."""
        cursor.execute(
            "SELECT * FROM tb_performance_metrics WHERE fk_run = (SELECT pk_run FROM tb_benchmark_run WHERE id = %s)",
            (run_id,),
        )
        row = cursor.fetchone()

        if not row:
            return None

        # Column order from schema
        return PerformanceMetrics(
            total_requests=row[1],
            total_errors=row[2],
            error_rate=float(row[3]) if row[3] else 0,
            requests_per_second=float(row[4]),
            latency_min=row[5],
            latency_p50=row[6],
            latency_p95=row[7],
            latency_p99=row[8],
            latency_p999=row[9],
            latency_max=row[10],
            latency_mean=row[11],
            latency_stddev=row[12],
            response_bytes_min=row[13],
            response_bytes_mean=row[14],
            response_bytes_max=row[15],
            connect_time_mean=row[16],
            idle_time_mean=row[17],
            server_processing_mean=row[18],
        )

    def _fetch_resource_profile(
        self,
        cursor,
        run_id: str,
    ) -> ResourceProfile | None:
        """Fetch resource profile for a run."""
        cursor.execute(
            "SELECT * FROM tb_resource_profile WHERE fk_run = (SELECT pk_run FROM tb_benchmark_run WHERE id = %s)",
            (run_id,),
        )
        row = cursor.fetchone()

        if not row:
            return None

        return ResourceProfile(
            cpu_cores_required=row[1],
            cpu_cores_with_headroom=row[2],
            headroom_percent=float(row[3]),
            rps_per_core=row[4],
            application_baseline_mb=row[5],
            connection_pool_memory_mb=row[6],
            memory_buffer_percent=float(row[7]),
            memory_required_gb=float(row[8]),
            application_storage_gb=float(row[9]),
            data_growth_gb_per_month=float(row[10]),
            log_storage_gb_per_month=float(row[11]),
            bandwidth_mbps=float(row[12]),
            data_transfer_gb_per_month=float(row[13]),
            total_monthly_storage_gb=float(row[14]),
        )

    def _fetch_cost_analysis(
        self,
        cursor,
        run_id: str,
    ) -> CostAnalysisResult | None:
        """Fetch cost analysis for a run."""
        cursor.execute(
            "SELECT * FROM tv_cost_analysis WHERE fk_run = (SELECT pk_run FROM tb_benchmark_run WHERE id = %s)",
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
        """Fetch efficiency ranking for a run."""
        cursor.execute(
            "SELECT * FROM tb_efficiency_ranking WHERE fk_run = (SELECT pk_run FROM tb_benchmark_run WHERE id = %s)",
            (run_id,),
        )
        row = cursor.fetchone()

        if not row:
            return None

        return EfficiencyRanking(
            efficiency_score=float(row[2]),
            cost_component=float(row[3]),
            latency_component=float(row[4]),
            throughput_component=float(row[5]),
            reliability_component=float(row[6]),
            suite_rank=row[7],
            rank_tie_breaker=row[8] if len(row) > 8 else None,
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
            return CostAnalysisResult(
                recommended_cloud_provider=row[1],
                recommended_instance_type=row[2],
                cost_breakdowns=[],
            )
