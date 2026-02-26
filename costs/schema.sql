-- ============================================================================
-- VelocityBench Cost Simulation & Benchmark Analytics Database Schema
-- ============================================================================
-- Independent schema for framework benchmarking and cost analysis
-- Uses Trinity Pattern: pk (INTEGER), id (UUID), fk (INTEGER)
-- ============================================================================

-- ============================================================================
-- LEVEL 1: FRAMEWORK DEFINITION
-- ============================================================================

CREATE TABLE IF NOT EXISTS tb_framework (
    pk_framework SERIAL PRIMARY KEY,
    id UUID UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL UNIQUE,
    language VARCHAR(50) NOT NULL,
    language_family VARCHAR(50) NOT NULL,
    runtime VARCHAR(100) NOT NULL,
    version VARCHAR(50) NOT NULL,
    repository_url VARCHAR(500),
    documentation_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_framework_name ON tb_framework(name);
CREATE INDEX idx_tb_framework_language ON tb_framework(language);
CREATE INDEX idx_tb_framework_language_family ON tb_framework(language_family);
CREATE INDEX idx_tb_framework_id ON tb_framework(id);

-- Framework metadata: type safety, paradigm, concurrency, etc.
CREATE TABLE IF NOT EXISTS tb_framework_metadata (
    pk_metadata SERIAL PRIMARY KEY,
    fk_framework INTEGER NOT NULL UNIQUE REFERENCES tb_framework(pk_framework) ON DELETE CASCADE,
    metadata JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_framework_metadata_framework ON tb_framework_metadata(fk_framework);

-- ============================================================================
-- LEVEL 2: BENCHMARK DEFINITION
-- ============================================================================

CREATE TABLE IF NOT EXISTS tb_benchmark_suite (
    pk_suite SERIAL PRIMARY KEY,
    id UUID UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    version VARCHAR(50) NOT NULL,
    created_by VARCHAR(255),
    baseline_framework_id UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_benchmark_suite_id ON tb_benchmark_suite(id);
CREATE INDEX idx_tb_benchmark_suite_name ON tb_benchmark_suite(name);

-- Workload types (query complexity, operation types)
CREATE TABLE IF NOT EXISTS tb_workload (
    pk_workload SERIAL PRIMARY KEY,
    id UUID UNIQUE NOT NULL,
    fk_suite INTEGER NOT NULL REFERENCES tb_benchmark_suite(pk_suite) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    query_complexity VARCHAR(50) NOT NULL,  -- "simple", "moderate", "complex"
    operation_count INT,
    estimated_join_depth INT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_workload_suite ON tb_workload(fk_suite);
CREATE INDEX idx_tb_workload_id ON tb_workload(id);
CREATE UNIQUE INDEX idx_tb_workload_suite_name ON tb_workload(fk_suite, name);

-- Load profiles (smoke, small, medium, large, production)
CREATE TABLE IF NOT EXISTS tb_load_profile (
    pk_profile SERIAL PRIMARY KEY,
    id UUID UNIQUE NOT NULL,
    name VARCHAR(50) NOT NULL UNIQUE,
    rps INT NOT NULL,
    duration_seconds INT NOT NULL,
    warmup_seconds INT NOT NULL,
    threads INT NOT NULL,
    ramp_up_time_seconds INT,
    think_time_ms INT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_load_profile_name ON tb_load_profile(name);
CREATE INDEX idx_tb_load_profile_id ON tb_load_profile(id);

-- ============================================================================
-- LEVEL 3: BENCHMARK EXECUTION
-- ============================================================================

CREATE TABLE IF NOT EXISTS tb_benchmark_run (
    pk_run SERIAL PRIMARY KEY,
    id UUID UNIQUE NOT NULL,
    fk_framework INTEGER NOT NULL REFERENCES tb_framework(pk_framework) ON DELETE CASCADE,
    fk_suite INTEGER NOT NULL REFERENCES tb_benchmark_suite(pk_suite) ON DELETE CASCADE,
    fk_workload INTEGER NOT NULL REFERENCES tb_workload(pk_workload) ON DELETE CASCADE,
    fk_load_profile INTEGER NOT NULL REFERENCES tb_load_profile(pk_profile) ON DELETE CASCADE,

    -- Execution metadata
    status VARCHAR(50) NOT NULL DEFAULT 'pending',  -- "pending", "running", "completed", "failed"
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_seconds INT,

    -- Raw results reference
    jmeter_file_path VARCHAR(500),
    jmeter_results JSONB,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_benchmark_run_id ON tb_benchmark_run(id);
CREATE INDEX idx_tb_benchmark_run_framework ON tb_benchmark_run(fk_framework);
CREATE INDEX idx_tb_benchmark_run_suite ON tb_benchmark_run(fk_suite);
CREATE INDEX idx_tb_benchmark_run_workload ON tb_benchmark_run(fk_workload);
CREATE INDEX idx_tb_benchmark_run_status ON tb_benchmark_run(status);
CREATE INDEX idx_tb_benchmark_run_time ON tb_benchmark_run(start_time DESC);
CREATE UNIQUE INDEX idx_tb_benchmark_run_unique ON tb_benchmark_run(fk_framework, fk_suite, fk_workload, fk_load_profile, start_time);

-- ============================================================================
-- LEVEL 4: PERFORMANCE METRICS
-- ============================================================================

CREATE TABLE IF NOT EXISTS tb_performance_metrics (
    pk_metrics SERIAL PRIMARY KEY,
    fk_run INTEGER NOT NULL UNIQUE REFERENCES tb_benchmark_run(pk_run) ON DELETE CASCADE,

    -- Throughput metrics
    total_requests BIGINT NOT NULL,
    total_errors BIGINT NOT NULL,
    error_rate NUMERIC(5,2),
    requests_per_second NUMERIC(10,2),

    -- Latency (milliseconds)
    latency_min INT,
    latency_p50 INT,
    latency_p95 INT,
    latency_p99 INT,
    latency_p999 INT,
    latency_max INT,
    latency_mean INT,
    latency_stddev INT,

    -- Response size
    response_bytes_min INT,
    response_bytes_mean INT,
    response_bytes_max INT,

    -- Connection metrics
    connect_time_mean INT,
    idle_time_mean INT,
    server_processing_mean INT,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_performance_metrics_run ON tb_performance_metrics(fk_run);

-- Latency percentiles (p1, p5, p10, p25, p50, p75, p90, p95, p99)
CREATE TABLE IF NOT EXISTS tb_performance_percentiles (
    pk_percentile SERIAL PRIMARY KEY,
    fk_run INTEGER NOT NULL REFERENCES tb_benchmark_run(pk_run) ON DELETE CASCADE,
    percentile INT NOT NULL,
    latency_ms INT NOT NULL,
    UNIQUE(fk_run, percentile),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_performance_percentiles_run ON tb_performance_percentiles(fk_run);

-- ============================================================================
-- LEVEL 5: INFRASTRUCTURE & RESOURCES
-- ============================================================================

CREATE TABLE IF NOT EXISTS tb_resource_profile (
    pk_profile SERIAL PRIMARY KEY,
    fk_run INTEGER NOT NULL UNIQUE REFERENCES tb_benchmark_run(pk_run) ON DELETE CASCADE,

    -- CPU
    cpu_cores_required INT NOT NULL,
    cpu_cores_with_headroom INT NOT NULL,
    headroom_percent NUMERIC(5,2),
    rps_per_core INT,

    -- Memory
    application_baseline_mb INT,
    connection_pool_memory_mb INT,
    memory_buffer_percent NUMERIC(5,2),
    memory_required_gb NUMERIC(10,2),

    -- Storage
    application_storage_gb NUMERIC(10,2),
    data_growth_gb_per_month NUMERIC(10,4),
    log_storage_gb_per_month NUMERIC(10,4),

    -- Network
    bandwidth_mbps NUMERIC(10,2),
    data_transfer_gb_per_month NUMERIC(10,2),

    -- Derived
    total_monthly_storage_gb NUMERIC(10,2),

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_resource_profile_run ON tb_resource_profile(fk_run);

-- ============================================================================
-- LEVEL 6: COST ANALYSIS
-- ============================================================================

CREATE TABLE IF NOT EXISTS tb_cost_analysis (
    pk_analysis SERIAL PRIMARY KEY,
    fk_run INTEGER NOT NULL UNIQUE REFERENCES tb_benchmark_run(pk_run) ON DELETE CASCADE,

    -- Recommendations
    recommended_cloud_provider VARCHAR(50),  -- "aws", "gcp", "azure"
    recommended_instance_type VARCHAR(100),

    analysis_timestamp TIMESTAMP DEFAULT NOW(),
    estimated_margin_of_error NUMERIC(5,2),

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_cost_analysis_run ON tb_cost_analysis(fk_run);

-- Cloud cost breakdown (AWS, GCP, Azure)
CREATE TABLE IF NOT EXISTS tb_cost_breakdown (
    pk_breakdown SERIAL PRIMARY KEY,
    fk_analysis INTEGER NOT NULL REFERENCES tb_cost_analysis(pk_analysis) ON DELETE CASCADE,

    cloud_provider VARCHAR(50) NOT NULL,  -- "aws", "gcp", "azure"

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
    yearly_with_1yr_reserved NUMERIC(12,2),
    yearly_with_3yr_reserved NUMERIC(12,2),

    -- Per-request metrics
    cost_per_request NUMERIC(12,10),
    requests_per_dollar BIGINT,

    -- Instance details
    instance_type VARCHAR(100),
    instance_hourly_rate NUMERIC(10,4),

    UNIQUE(fk_analysis, cloud_provider),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_cost_breakdown_analysis ON tb_cost_breakdown(fk_analysis);
CREATE INDEX idx_tb_cost_breakdown_provider ON tb_cost_breakdown(cloud_provider);

-- ============================================================================
-- LEVEL 7: EFFICIENCY & RANKING
-- ============================================================================

CREATE TABLE IF NOT EXISTS tb_efficiency_ranking (
    pk_ranking SERIAL PRIMARY KEY,
    fk_run INTEGER NOT NULL UNIQUE REFERENCES tb_benchmark_run(pk_run) ON DELETE CASCADE,

    -- Efficiency score (0-10): 40% cost + 30% latency + 20% throughput + 10% reliability
    efficiency_score NUMERIC(5,2),
    cost_component NUMERIC(5,2),
    latency_component NUMERIC(5,2),
    throughput_component NUMERIC(5,2),
    reliability_component NUMERIC(5,2),

    -- Ranking
    suite_rank INT,
    rank_tie_breaker VARCHAR(50),  -- "cost", "latency", "throughput"

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_efficiency_ranking_run ON tb_efficiency_ranking(fk_run);

-- ============================================================================
-- HISTORICAL & TRENDING
-- ============================================================================

CREATE TABLE IF NOT EXISTS tb_benchmark_comparison (
    pk_comparison SERIAL PRIMARY KEY,
    id UUID UNIQUE NOT NULL,

    fk_suite_old INTEGER NOT NULL REFERENCES tb_benchmark_suite(pk_suite) ON DELETE CASCADE,
    fk_suite_new INTEGER NOT NULL REFERENCES tb_benchmark_suite(pk_suite) ON DELETE CASCADE,

    fk_framework INTEGER NOT NULL REFERENCES tb_framework(pk_framework) ON DELETE CASCADE,
    fk_workload INTEGER NOT NULL REFERENCES tb_workload(pk_workload) ON DELETE CASCADE,

    -- Change metrics (percentage)
    rps_change NUMERIC(5,2),
    latency_change NUMERIC(5,2),
    cost_change NUMERIC(5,2),
    efficiency_change NUMERIC(5,2),

    -- Regression detection
    is_regression BOOLEAN DEFAULT FALSE,
    regression_severity VARCHAR(50),  -- "minor", "moderate", "severe"

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_benchmark_comparison_id ON tb_benchmark_comparison(id);

-- ============================================================================
-- COMPOSITION VIEWS (Zero N+1 Queries)
-- ============================================================================

-- Pre-compose framework, suite, workload, and load profile into BenchmarkRun
CREATE OR REPLACE VIEW tv_benchmark_run AS
SELECT
    r.id,
    r.status,
    r.start_time,
    r.end_time,
    r.duration_seconds,
    r.jmeter_file_path,

    -- Framework (pre-composed)
    jsonb_build_object(
        'id', f.id,
        'name', f.name,
        'language', f.language,
        'languageFamily', f.language_family,
        'runtime', f.runtime,
        'version', f.version
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
        'queryComplexity', w.query_complexity
    ) as workload,

    -- Load Profile (pre-composed)
    jsonb_build_object(
        'id', lp.id,
        'name', lp.name,
        'rps', lp.rps,
        'threads', lp.threads,
        'durationSeconds', lp.duration_seconds
    ) as load_profile

FROM tb_benchmark_run r
JOIN tb_framework f ON r.fk_framework = f.pk_framework
JOIN tb_benchmark_suite s ON r.fk_suite = s.pk_suite
JOIN tb_workload w ON r.fk_workload = w.pk_workload
JOIN tb_load_profile lp ON r.fk_load_profile = lp.pk_profile;

-- Pre-compose cost breakdowns and efficiency ranking
CREATE OR REPLACE VIEW tv_cost_analysis AS
SELECT
    ca.id,
    ca.fk_run,
    ca.recommended_cloud_provider,
    ca.recommended_instance_type,

    -- Cost breakdown array (all 3 clouds)
    jsonb_agg(jsonb_build_object(
        'cloudProvider', cb.cloud_provider,
        'computeCost', cb.compute_cost,
        'databaseCost', cb.database_cost,
        'storageCost', cb.storage_cost,
        'dataTransferCost', cb.data_transfer_cost,
        'monitoringCost', cb.monitoring_cost,
        'contingencyCost', cb.contingency_cost,
        'totalMonthlyCost', cb.total_monthly_cost,
        'totalYearlyCost', cb.total_yearly_cost,
        'yearlyWith1yrReserved', cb.yearly_with_1yr_reserved,
        'yearlyWith3yrReserved', cb.yearly_with_3yr_reserved,
        'costPerRequest', cb.cost_per_request,
        'instanceType', cb.instance_type,
        'instanceHourlyRate', cb.instance_hourly_rate
    ) ORDER BY cb.cloud_provider) FILTER (WHERE cb.cloud_provider IS NOT NULL) as cost_breakdowns,

    -- Efficiency ranking
    jsonb_build_object(
        'efficiencyScore', er.efficiency_score,
        'costComponent', er.cost_component,
        'latencyComponent', er.latency_component,
        'throughputComponent', er.throughput_component,
        'reliabilityComponent', er.reliability_component,
        'suiteRank', er.suite_rank
    ) as efficiency_ranking

FROM tb_cost_analysis ca
LEFT JOIN tb_cost_breakdown cb ON ca.pk_analysis = cb.fk_analysis
LEFT JOIN tb_efficiency_ranking er ON ca.pk_analysis = er.fk_analysis
GROUP BY ca.id, ca.fk_run, ca.recommended_cloud_provider, ca.recommended_instance_type, er.efficiency_score, er.cost_component, er.latency_component, er.throughput_component, er.reliability_component, er.suite_rank;

-- ============================================================================
-- INSERTS: Predefined Load Profiles
-- ============================================================================

INSERT INTO tb_load_profile (id, name, rps, duration_seconds, warmup_seconds, threads, ramp_up_time_seconds, think_time_ms)
VALUES
    (gen_random_uuid(), 'smoke', 10, 60, 5, 1, 0, 0),
    (gen_random_uuid(), 'small', 50, 120, 10, 5, 10, 100),
    (gen_random_uuid(), 'medium', 500, 180, 15, 50, 30, 50),
    (gen_random_uuid(), 'large', 5000, 300, 30, 500, 60, 10),
    (gen_random_uuid(), 'production', 10000, 600, 60, 1000, 120, 5)
ON CONFLICT DO NOTHING;
