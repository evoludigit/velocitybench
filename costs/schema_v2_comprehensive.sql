-- ============================================================================
-- VelocityBench Comprehensive Analytics Database Schema
-- ============================================================================
-- 54 tables capturing complete benchmark data:
-- Framework implementation, query patterns, environment, execution,
-- metrics, analysis, comparisons, and reproducibility
--
-- Uses Trinity Pattern: pk (INTEGER), id (UUID), fk (INTEGER)
-- ============================================================================

-- ============================================================================
-- LEVEL 1: FRAMEWORK DEFINITION & IMPLEMENTATION (10 TABLES)
-- ============================================================================

-- Core framework definition
CREATE TABLE IF NOT EXISTS tb_framework (
    pk_framework SERIAL PRIMARY KEY,
    id UUID UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL UNIQUE,
    language VARCHAR(50) NOT NULL,
    language_family VARCHAR(50) NOT NULL,  -- dynamic, static, hybrid
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

-- Framework metadata: type safety, paradigm, concurrency
CREATE TABLE IF NOT EXISTS tb_framework_metadata (
    pk_metadata SERIAL PRIMARY KEY,
    fk_framework INTEGER NOT NULL UNIQUE REFERENCES tb_framework(pk_framework) ON DELETE CASCADE,
    type_safety VARCHAR(50),  -- none, partial, full
    paradigm VARCHAR(100),    -- OO, functional, hybrid
    concurrency_model VARCHAR(100),  -- threaded, async, async+threaded
    garbage_collection BOOLEAN,
    memory_management VARCHAR(100),
    startup_time_ms INTEGER,
    cold_start_penalty_ms INTEGER,
    language_expressiveness INT,  -- 1-10
    learning_curve INT,  -- 1-10
    ecosystem_size INT,  -- 1-10
    maturity_years INT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_framework_metadata_framework ON tb_framework_metadata(fk_framework);

-- Framework implementation (source code repository)
CREATE TABLE IF NOT EXISTS tb_framework_implementation (
    pk_implementation SERIAL PRIMARY KEY,
    fk_framework INTEGER NOT NULL UNIQUE REFERENCES tb_framework(pk_framework) ON DELETE CASCADE,
    git_repository_url VARCHAR(500),
    git_commit_hash VARCHAR(50),
    git_branch VARCHAR(255),
    git_tag VARCHAR(255),
    implementation_date TIMESTAMP,
    total_lines_of_code INT,
    total_files INT,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_framework_implementation_framework ON tb_framework_implementation(fk_framework);

-- Individual source code files
CREATE TABLE IF NOT EXISTS tb_framework_file (
    pk_file SERIAL PRIMARY KEY,
    fk_implementation INTEGER NOT NULL REFERENCES tb_framework_implementation(pk_implementation) ON DELETE CASCADE,
    file_path VARCHAR(500) NOT NULL,
    file_size_bytes INT,
    lines_of_code INT,
    language VARCHAR(50),
    content_hash VARCHAR(64),
    file_content TEXT,
    is_critical_path BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(fk_implementation, file_path)
);

CREATE INDEX idx_tb_framework_file_implementation ON tb_framework_file(fk_implementation);
CREATE INDEX idx_tb_framework_file_path ON tb_framework_file(file_path);

-- Database library and ORM
CREATE TABLE IF NOT EXISTS tb_database_library (
    pk_library SERIAL PRIMARY KEY,
    fk_framework INTEGER NOT NULL REFERENCES tb_framework(pk_framework) ON DELETE CASCADE,
    library_name VARCHAR(100) NOT NULL,
    library_type VARCHAR(50),  -- ORM, query builder, raw driver
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_database_library_framework ON tb_database_library(fk_framework);

-- Database library version history
CREATE TABLE IF NOT EXISTS tb_database_library_version (
    pk_version SERIAL PRIMARY KEY,
    fk_library INTEGER NOT NULL REFERENCES tb_database_library(pk_library) ON DELETE CASCADE,
    version_number VARCHAR(50),
    release_date TIMESTAMP,
    is_used_in_benchmark BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_database_library_version_library ON tb_database_library_version(fk_library);

-- Query optimization techniques
CREATE TABLE IF NOT EXISTS tb_optimization_technique (
    pk_technique SERIAL PRIMARY KEY,
    fk_framework INTEGER NOT NULL REFERENCES tb_framework(pk_framework) ON DELETE CASCADE,
    technique_name VARCHAR(255) NOT NULL,
    technique_type VARCHAR(100),  -- batching, caching, query planning, etc.
    description TEXT,
    implementation_details TEXT,
    performance_impact_percent NUMERIC(10,2),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_optimization_technique_framework ON tb_optimization_technique(fk_framework);

-- Caching strategies
CREATE TABLE IF NOT EXISTS tb_caching_strategy (
    pk_strategy SERIAL PRIMARY KEY,
    fk_framework INTEGER NOT NULL REFERENCES tb_framework(pk_framework) ON DELETE CASCADE,
    strategy_type VARCHAR(100),  -- query cache, object cache, distributed cache
    cache_backend VARCHAR(100),  -- redis, memcached, in-memory
    cache_ttl_seconds INT,
    hit_rate_percent NUMERIC(5,2),
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_caching_strategy_framework ON tb_caching_strategy(fk_framework);

-- Git repository tracking
CREATE TABLE IF NOT EXISTS tb_git_repository (
    pk_repository SERIAL PRIMARY KEY,
    fk_framework INTEGER NOT NULL UNIQUE REFERENCES tb_framework(pk_framework) ON DELETE CASCADE,
    repository_url VARCHAR(500) NOT NULL,
    default_branch VARCHAR(255),
    latest_commit_hash VARCHAR(50),
    latest_commit_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_git_repository_framework ON tb_git_repository(fk_framework);

-- Framework version history
CREATE TABLE IF NOT EXISTS tb_framework_version (
    pk_version SERIAL PRIMARY KEY,
    fk_framework INTEGER NOT NULL REFERENCES tb_framework(pk_framework) ON DELETE CASCADE,
    version_number VARCHAR(50) NOT NULL,
    release_date TIMESTAMP,
    git_commit_hash VARCHAR(50),
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(fk_framework, version_number)
);

CREATE INDEX idx_tb_framework_version_framework ON tb_framework_version(fk_framework);

-- ============================================================================
-- LEVEL 2: BENCHMARK DEFINITION (8 TABLES)
-- ============================================================================

-- Benchmark suite (collection of tests)
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

-- Query patterns (types of queries being tested)
CREATE TABLE IF NOT EXISTS tb_query_pattern (
    pk_pattern SERIAL PRIMARY KEY,
    id UUID UNIQUE NOT NULL,
    fk_suite INTEGER NOT NULL REFERENCES tb_benchmark_suite(pk_suite) ON DELETE CASCADE,
    pattern_name VARCHAR(255) NOT NULL,
    pattern_type VARCHAR(100),  -- simple_query, nested_query, mutation, aggregation
    complexity VARCHAR(50),  -- simple, moderate, complex
    description TEXT,
    expected_execution_ms INT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_query_pattern_suite ON tb_query_pattern(fk_suite);
CREATE INDEX idx_tb_query_pattern_id ON tb_query_pattern(id);

-- Query pattern source files
CREATE TABLE IF NOT EXISTS tb_query_pattern_file (
    pk_file SERIAL PRIMARY KEY,
    fk_pattern INTEGER NOT NULL REFERENCES tb_query_pattern(pk_pattern) ON DELETE CASCADE,
    query_string TEXT NOT NULL,
    query_structure TEXT,  -- graphql structure for reference
    test_data_size INT,  -- number of records queried
    is_parameterized BOOLEAN,
    parameters TEXT,  -- JSON of test parameters
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_query_pattern_file_pattern ON tb_query_pattern_file(fk_pattern);

-- Workload (combination of patterns)
CREATE TABLE IF NOT EXISTS tb_workload (
    pk_workload SERIAL PRIMARY KEY,
    id UUID UNIQUE NOT NULL,
    fk_suite INTEGER NOT NULL REFERENCES tb_benchmark_suite(pk_suite) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    query_complexity VARCHAR(50),
    operation_count INT,
    estimated_join_depth INT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_workload_suite ON tb_workload(fk_suite);
CREATE INDEX idx_tb_workload_id ON tb_workload(id);

-- Load profile (testing parameters)
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

-- Load profile ramp-up details
CREATE TABLE IF NOT EXISTS tb_load_profile_ramp (
    pk_ramp SERIAL PRIMARY KEY,
    fk_profile INTEGER NOT NULL REFERENCES tb_load_profile(pk_profile) ON DELETE CASCADE,
    phase_number INT NOT NULL,
    start_rps INT,
    end_rps INT,
    duration_seconds INT,
    UNIQUE(fk_profile, phase_number)
);

CREATE INDEX idx_tb_load_profile_ramp_profile ON tb_load_profile_ramp(fk_profile);

-- Query pattern complexity metrics
CREATE TABLE IF NOT EXISTS tb_query_pattern_complexity (
    pk_complexity SERIAL PRIMARY KEY,
    fk_pattern INTEGER NOT NULL UNIQUE REFERENCES tb_query_pattern(pk_pattern) ON DELETE CASCADE,
    join_depth INT,
    field_count INT,
    subquery_count INT,
    filter_count INT,
    sort_count INT,
    computed_complexity_score NUMERIC(10,2),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_query_pattern_complexity_pattern ON tb_query_pattern_complexity(fk_pattern);

-- Benchmark schema definition
CREATE TABLE IF NOT EXISTS tb_benchmark_schema (
    pk_schema SERIAL PRIMARY KEY,
    fk_suite INTEGER NOT NULL UNIQUE REFERENCES tb_benchmark_suite(pk_suite) ON DELETE CASCADE,
    schema_version VARCHAR(50),
    total_tables INT,
    total_records INT,
    schema_size_mb NUMERIC(10,2),
    schema_definition TEXT,  -- DDL statements
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_benchmark_schema_suite ON tb_benchmark_schema(fk_suite);

-- ============================================================================
-- LEVEL 3: TEST ENVIRONMENT (8 TABLES)
-- ============================================================================

-- Test machine specifications
CREATE TABLE IF NOT EXISTS tb_test_machine (
    pk_machine SERIAL PRIMARY KEY,
    id UUID UNIQUE NOT NULL,
    machine_name VARCHAR(255),
    cpu_model VARCHAR(255) NOT NULL,
    cpu_cores INT NOT NULL,
    cpu_threads INT NOT NULL,
    cpu_base_ghz NUMERIC(5,2),
    cpu_boost_ghz NUMERIC(5,2),
    ram_gb INT NOT NULL,
    ram_type VARCHAR(50),  -- DDR4, DDR5
    storage_type VARCHAR(50),  -- SSD, HDD, NVMe
    storage_size_gb INT,
    os_name VARCHAR(100),
    os_version VARCHAR(50),
    kernel_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_test_machine_id ON tb_test_machine(id);
CREATE INDEX idx_tb_test_machine_name ON tb_test_machine(machine_name);

-- CPU details
CREATE TABLE IF NOT EXISTS tb_test_machine_cpu (
    pk_cpu SERIAL PRIMARY KEY,
    fk_machine INTEGER NOT NULL UNIQUE REFERENCES tb_test_machine(pk_machine) ON DELETE CASCADE,
    cpu_flags TEXT,
    turbo_boost_enabled BOOLEAN,
    hyper_threading_enabled BOOLEAN,
    max_frequency_mhz INT,
    cache_l1_kb INT,
    cache_l2_kb INT,
    cache_l3_mb INT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_test_machine_cpu_machine ON tb_test_machine_cpu(fk_machine);

-- Memory configuration
CREATE TABLE IF NOT EXISTS tb_test_machine_memory (
    pk_memory SERIAL PRIMARY KEY,
    fk_machine INTEGER NOT NULL UNIQUE REFERENCES tb_test_machine(pk_machine) ON DELETE CASCADE,
    total_memory_gb INT,
    available_memory_gb INT,
    memory_speed_mhz INT,
    ecc_enabled BOOLEAN,
    numa_nodes INT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_test_machine_memory_machine ON tb_test_machine_memory(fk_machine);

-- Database instance configuration
CREATE TABLE IF NOT EXISTS tb_database_instance (
    pk_instance SERIAL PRIMARY KEY,
    id UUID UNIQUE NOT NULL,
    database_engine VARCHAR(50) NOT NULL,  -- PostgreSQL, MySQL, etc.
    engine_version VARCHAR(50),
    instance_class VARCHAR(100),
    max_connections INT,
    shared_buffers_mb INT,
    effective_cache_size_mb INT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_database_instance_id ON tb_database_instance(id);

-- Database configuration settings
CREATE TABLE IF NOT EXISTS tb_database_configuration (
    pk_config SERIAL PRIMARY KEY,
    fk_instance INTEGER NOT NULL REFERENCES tb_database_instance(pk_instance) ON DELETE CASCADE,
    config_key VARCHAR(255) NOT NULL,
    config_value VARCHAR(500),
    data_type VARCHAR(50),
    UNIQUE(fk_instance, config_key)
);

CREATE INDEX idx_tb_database_configuration_instance ON tb_database_configuration(fk_instance);

-- External dependencies (Redis, caching services, etc.)
CREATE TABLE IF NOT EXISTS tb_external_dependency (
    pk_dependency SERIAL PRIMARY KEY,
    fk_benchmark_run INTEGER,  -- Optional link to run
    dependency_type VARCHAR(100),  -- Redis, Memcached, Elasticsearch
    dependency_version VARCHAR(50),
    host VARCHAR(255),
    port INT,
    is_local BOOLEAN,
    memory_limit_mb INT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- JMeter test configuration
CREATE TABLE IF NOT EXISTS tb_jmeter_configuration (
    pk_jmeter SERIAL PRIMARY KEY,
    fk_benchmark_run INTEGER,  -- Optional link to run
    jmeter_version VARCHAR(50),
    heap_size_mb INT,
    gc_settings VARCHAR(255),  -- JVM GC parameters
    connection_timeout_ms INT,
    read_timeout_ms INT,
    socket_timeout_ms INT,
    max_pool_size INT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Environment variables at test time
CREATE TABLE IF NOT EXISTS tb_environment_variable (
    pk_variable SERIAL PRIMARY KEY,
    fk_benchmark_run INTEGER,  -- Optional link to run
    variable_name VARCHAR(255) NOT NULL,
    variable_value VARCHAR(500),
    UNIQUE(variable_name)
);

-- ============================================================================
-- LEVEL 4: BENCHMARK EXECUTION & LOGS (4 TABLES)
-- ============================================================================

-- Benchmark run execution
CREATE TABLE IF NOT EXISTS tb_benchmark_run (
    pk_run SERIAL PRIMARY KEY,
    id UUID UNIQUE NOT NULL,
    fk_framework INTEGER NOT NULL REFERENCES tb_framework(pk_framework) ON DELETE CASCADE,
    fk_suite INTEGER NOT NULL REFERENCES tb_benchmark_suite(pk_suite) ON DELETE CASCADE,
    fk_workload INTEGER NOT NULL REFERENCES tb_workload(pk_workload) ON DELETE CASCADE,
    fk_load_profile INTEGER NOT NULL REFERENCES tb_load_profile(pk_profile) ON DELETE CASCADE,
    fk_test_machine INTEGER REFERENCES tb_test_machine(pk_machine),
    fk_database_instance INTEGER REFERENCES tb_database_instance(pk_instance),

    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_seconds INT,
    jmeter_file_path VARCHAR(500),
    jmeter_results JSONB,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_benchmark_run_id ON tb_benchmark_run(id);
CREATE INDEX idx_tb_benchmark_run_framework ON tb_benchmark_run(fk_framework);
CREATE INDEX idx_tb_benchmark_run_suite ON tb_benchmark_run(fk_suite);
CREATE INDEX idx_tb_benchmark_run_status ON tb_benchmark_run(status);
CREATE INDEX idx_tb_benchmark_run_time ON tb_benchmark_run(start_time DESC);
CREATE UNIQUE INDEX idx_tb_benchmark_run_unique ON tb_benchmark_run(fk_framework, fk_suite, fk_workload, fk_load_profile, start_time);

-- Run iterations (warm-up vs actual)
CREATE TABLE IF NOT EXISTS tb_run_iteration (
    pk_iteration SERIAL PRIMARY KEY,
    fk_run INTEGER NOT NULL REFERENCES tb_benchmark_run(pk_run) ON DELETE CASCADE,
    iteration_number INT NOT NULL,
    iteration_type VARCHAR(50),  -- warmup, actual, cooldown
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    request_count INT,
    UNIQUE(fk_run, iteration_number)
);

CREATE INDEX idx_tb_run_iteration_run ON tb_run_iteration(fk_run);

-- Execution log (events, errors, warnings)
CREATE TABLE IF NOT EXISTS tb_execution_log (
    pk_log SERIAL PRIMARY KEY,
    fk_run INTEGER NOT NULL REFERENCES tb_benchmark_run(pk_run) ON DELETE CASCADE,
    log_time TIMESTAMP,
    log_level VARCHAR(50),  -- INFO, WARNING, ERROR
    log_message TEXT,
    stacktrace TEXT
);

CREATE INDEX idx_tb_execution_log_run ON tb_execution_log(fk_run);
CREATE INDEX idx_tb_execution_log_level ON tb_execution_log(log_level);

-- ============================================================================
-- LEVEL 5: PERFORMANCE METRICS (12 TABLES)
-- ============================================================================

-- Overall performance metrics
CREATE TABLE IF NOT EXISTS tb_performance_metrics (
    pk_metrics SERIAL PRIMARY KEY,
    fk_run INTEGER NOT NULL UNIQUE REFERENCES tb_benchmark_run(pk_run) ON DELETE CASCADE,

    total_requests BIGINT NOT NULL,
    total_errors BIGINT NOT NULL,
    error_rate NUMERIC(5,2),
    requests_per_second NUMERIC(10,2),

    latency_min INT,
    latency_p50 INT,
    latency_p95 INT,
    latency_p99 INT,
    latency_p999 INT,
    latency_max INT,
    latency_mean INT,
    latency_stddev INT,

    response_bytes_min INT,
    response_bytes_mean INT,
    response_bytes_max INT,

    connect_time_mean INT,
    idle_time_mean INT,
    server_processing_mean INT,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_performance_metrics_run ON tb_performance_metrics(fk_run);

-- Latency percentiles
CREATE TABLE IF NOT EXISTS tb_latency_percentile (
    pk_percentile SERIAL PRIMARY KEY,
    fk_run INTEGER NOT NULL REFERENCES tb_benchmark_run(pk_run) ON DELETE CASCADE,
    percentile INT NOT NULL,
    latency_ms INT NOT NULL,
    UNIQUE(fk_run, percentile)
);

CREATE INDEX idx_tb_latency_percentile_run ON tb_latency_percentile(fk_run);

-- Latency histogram (buckets)
CREATE TABLE IF NOT EXISTS tb_latency_histogram (
    pk_histogram SERIAL PRIMARY KEY,
    fk_run INTEGER NOT NULL REFERENCES tb_benchmark_run(pk_run) ON DELETE CASCADE,
    bucket_start_ms INT NOT NULL,
    bucket_end_ms INT NOT NULL,
    request_count INT NOT NULL,
    UNIQUE(fk_run, bucket_start_ms, bucket_end_ms)
);

CREATE INDEX idx_tb_latency_histogram_run ON tb_latency_histogram(fk_run);

-- Error breakdown
CREATE TABLE IF NOT EXISTS tb_error_metric (
    pk_error SERIAL PRIMARY KEY,
    fk_run INTEGER NOT NULL REFERENCES tb_benchmark_run(pk_run) ON DELETE CASCADE,
    error_type VARCHAR(100),  -- timeout, connection, 5xx, etc.
    error_code VARCHAR(50),
    error_count INT,
    error_percentage NUMERIC(5,2),
    first_occurrence TIMESTAMP,
    last_occurrence TIMESTAMP,
    UNIQUE(fk_run, error_type, error_code)
);

CREATE INDEX idx_tb_error_metric_run ON tb_error_metric(fk_run);

-- Resource metrics (CPU, memory, GC)
CREATE TABLE IF NOT EXISTS tb_resource_metric (
    pk_resource SERIAL PRIMARY KEY,
    fk_run INTEGER NOT NULL REFERENCES tb_benchmark_run(pk_run) ON DELETE CASCADE,

    peak_cpu_percent NUMERIC(5,2),
    avg_cpu_percent NUMERIC(5,2),
    peak_memory_mb INT,
    avg_memory_mb INT,
    gc_pause_count INT,
    gc_pause_time_ms INT,
    gc_full_pause_count INT,
    gc_full_pause_time_ms INT,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_resource_metric_run ON tb_resource_metric(fk_run);

-- Throughput metrics
CREATE TABLE IF NOT EXISTS tb_throughput_metric (
    pk_throughput SERIAL PRIMARY KEY,
    fk_run INTEGER NOT NULL REFERENCES tb_benchmark_run(pk_run) ON DELETE CASCADE,

    requests_per_second NUMERIC(10,2),
    bytes_per_second NUMERIC(15,2),
    active_connections_max INT,
    active_connections_avg INT,
    idle_connections INT,
    connection_timeouts INT,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_throughput_metric_run ON tb_throughput_metric(fk_run);

-- Response size metrics
CREATE TABLE IF NOT EXISTS tb_response_size_metric (
    pk_size SERIAL PRIMARY KEY,
    fk_run INTEGER NOT NULL REFERENCES tb_benchmark_run(pk_run) ON DELETE CASCADE,

    response_bytes_min INT,
    response_bytes_max INT,
    response_bytes_mean INT,
    response_bytes_median INT,
    response_bytes_stddev INT,
    response_bytes_p95 INT,
    response_bytes_p99 INT,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_response_size_metric_run ON tb_response_size_metric(fk_run);

-- Time breakdown (network vs server vs client)
CREATE TABLE IF NOT EXISTS tb_time_breakdown (
    pk_breakdown SERIAL PRIMARY KEY,
    fk_run INTEGER NOT NULL REFERENCES tb_benchmark_run(pk_run) ON DELETE CASCADE,

    connect_time_mean INT,
    connect_time_max INT,
    connect_time_min INT,

    idle_time_mean INT,
    idle_time_max INT,

    latency_mean INT,  -- server processing
    latency_max INT,
    latency_min INT,

    total_latency_mean INT,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_time_breakdown_run ON tb_time_breakdown(fk_run);

-- Per-query execution details
CREATE TABLE IF NOT EXISTS tb_query_execution_detail (
    pk_query_exec SERIAL PRIMARY KEY,
    fk_run INTEGER NOT NULL REFERENCES tb_benchmark_run(pk_run) ON DELETE CASCADE,
    fk_query_pattern INTEGER REFERENCES tb_query_pattern(pk_pattern),

    query_count INT,
    avg_execution_ms NUMERIC(10,2),
    p95_execution_ms NUMERIC(10,2),
    p99_execution_ms NUMERIC(10,2),
    max_execution_ms NUMERIC(10,2),
    error_count INT,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_query_execution_detail_run ON tb_query_execution_detail(fk_run);
CREATE INDEX idx_tb_query_execution_detail_pattern ON tb_query_execution_detail(fk_query_pattern);

-- Individual request metrics (sampled)
CREATE TABLE IF NOT EXISTS tb_request_metric (
    pk_request SERIAL PRIMARY KEY,
    fk_run INTEGER NOT NULL REFERENCES tb_benchmark_run(pk_run) ON DELETE CASCADE,

    request_number INT,
    request_time TIMESTAMP,
    latency_ms INT,
    response_bytes INT,
    response_code VARCHAR(10),
    connect_time_ms INT,
    idle_time_ms INT,
    processing_time_ms INT,
    success BOOLEAN,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_request_metric_run ON tb_request_metric(fk_run);
CREATE INDEX idx_tb_request_metric_response_code ON tb_request_metric(response_code);

-- ============================================================================
-- LEVEL 6: ANALYSIS & DERIVED DATA (6 TABLES)
-- ============================================================================

-- Infrastructure requirements
CREATE TABLE IF NOT EXISTS tb_resource_profile (
    pk_profile SERIAL PRIMARY KEY,
    fk_run INTEGER NOT NULL UNIQUE REFERENCES tb_benchmark_run(pk_run) ON DELETE CASCADE,

    cpu_cores_required INT,
    cpu_cores_with_headroom INT,
    headroom_percent NUMERIC(5,2),
    rps_per_core INT,

    application_baseline_mb INT,
    connection_pool_memory_mb INT,
    memory_buffer_percent NUMERIC(5,2),
    memory_required_gb NUMERIC(10,2),

    application_storage_gb NUMERIC(10,2),
    data_growth_gb_per_month NUMERIC(10,4),
    log_storage_gb_per_month NUMERIC(10,4),

    bandwidth_mbps NUMERIC(10,2),
    data_transfer_gb_per_month NUMERIC(10,2),

    total_monthly_storage_gb NUMERIC(10,2),

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_resource_profile_run ON tb_resource_profile(fk_run);

-- Cost analysis
CREATE TABLE IF NOT EXISTS tb_cost_analysis (
    pk_analysis SERIAL PRIMARY KEY,
    fk_run INTEGER NOT NULL UNIQUE REFERENCES tb_benchmark_run(pk_run) ON DELETE CASCADE,

    recommended_cloud_provider VARCHAR(50),
    recommended_instance_type VARCHAR(100),

    analysis_timestamp TIMESTAMP DEFAULT NOW(),
    estimated_margin_of_error NUMERIC(5,2),

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_cost_analysis_run ON tb_cost_analysis(fk_run);

-- Cost breakdown (AWS, GCP, Azure)
CREATE TABLE IF NOT EXISTS tb_cost_breakdown (
    pk_breakdown SERIAL PRIMARY KEY,
    fk_analysis INTEGER NOT NULL REFERENCES tb_cost_analysis(pk_analysis) ON DELETE CASCADE,

    cloud_provider VARCHAR(50) NOT NULL,

    compute_cost NUMERIC(10,2),
    database_cost NUMERIC(10,2),
    storage_cost NUMERIC(10,2),
    data_transfer_cost NUMERIC(10,2),
    monitoring_cost NUMERIC(10,2),
    contingency_cost NUMERIC(10,2),

    total_monthly_cost NUMERIC(10,2),

    total_yearly_cost NUMERIC(12,2),
    yearly_with_1yr_reserved NUMERIC(12,2),
    yearly_with_3yr_reserved NUMERIC(12,2),

    cost_per_request NUMERIC(12,10),
    requests_per_dollar BIGINT,

    instance_type VARCHAR(100),
    instance_hourly_rate NUMERIC(10,4),

    UNIQUE(fk_analysis, cloud_provider),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_cost_breakdown_analysis ON tb_cost_breakdown(fk_analysis);

-- Efficiency ranking
CREATE TABLE IF NOT EXISTS tb_efficiency_ranking (
    pk_ranking SERIAL PRIMARY KEY,
    fk_run INTEGER NOT NULL UNIQUE REFERENCES tb_benchmark_run(pk_run) ON DELETE CASCADE,

    efficiency_score NUMERIC(5,2),
    cost_component NUMERIC(5,2),
    latency_component NUMERIC(5,2),
    throughput_component NUMERIC(5,2),
    reliability_component NUMERIC(5,2),

    suite_rank INT,
    rank_tie_breaker VARCHAR(50),

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_efficiency_ranking_run ON tb_efficiency_ranking(fk_run);

-- Performance characterization
CREATE TABLE IF NOT EXISTS tb_performance_characterization (
    pk_characterization SERIAL PRIMARY KEY,
    fk_run INTEGER NOT NULL UNIQUE REFERENCES tb_benchmark_run(pk_run) ON DELETE CASCADE,

    scales_linearly_to INT,  -- RPS
    optimal_connections INT,
    gc_friendly BOOLEAN,
    cache_friendly BOOLEAN,
    memory_efficient BOOLEAN,
    cpu_efficient BOOLEAN,
    bottleneck_type VARCHAR(100),  -- CPU, memory, IO, GC
    bottleneck_description TEXT,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_performance_characterization_run ON tb_performance_characterization(fk_run);

-- Regression detection
CREATE TABLE IF NOT EXISTS tb_regression_detection (
    pk_regression SERIAL PRIMARY KEY,
    fk_run INTEGER NOT NULL UNIQUE REFERENCES tb_benchmark_run(pk_run) ON DELETE CASCADE,
    fk_previous_run INTEGER REFERENCES tb_benchmark_run(pk_run),

    is_regression BOOLEAN DEFAULT FALSE,
    regression_severity VARCHAR(50),  -- minor, moderate, severe
    latency_change_percent NUMERIC(5,2),
    throughput_change_percent NUMERIC(5,2),
    error_rate_change_percent NUMERIC(5,2),

    detected_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_regression_detection_run ON tb_regression_detection(fk_run);

-- ============================================================================
-- LEVEL 7: COMPARISON & TRENDS (4 TABLES)
-- ============================================================================

-- Framework comparisons
CREATE TABLE IF NOT EXISTS tb_framework_comparison (
    pk_comparison SERIAL PRIMARY KEY,
    id UUID UNIQUE NOT NULL,

    fk_suite INTEGER NOT NULL REFERENCES tb_benchmark_suite(pk_suite) ON DELETE CASCADE,
    fk_workload INTEGER NOT NULL REFERENCES tb_workload(pk_workload) ON DELETE CASCADE,

    framework_count INT,
    comparison_date TIMESTAMP,

    fastest_framework_id UUID,
    cheapest_framework_id UUID,
    most_efficient_framework_id UUID,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_framework_comparison_id ON tb_framework_comparison(id);

-- Performance trends
CREATE TABLE IF NOT EXISTS tb_performance_trend (
    pk_trend SERIAL PRIMARY KEY,
    fk_framework INTEGER NOT NULL REFERENCES tb_framework(pk_framework) ON DELETE CASCADE,
    fk_workload INTEGER NOT NULL REFERENCES tb_workload(pk_workload) ON DELETE CASCADE,

    trend_date TIMESTAMP,
    rps NUMERIC(10,2),
    latency_p95 INT,
    latency_p99 INT,
    efficiency_score NUMERIC(5,2),
    cost_per_request NUMERIC(12,10),

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_performance_trend_framework ON tb_performance_trend(fk_framework);
CREATE INDEX idx_tb_performance_trend_workload ON tb_performance_trend(fk_workload);
CREATE INDEX idx_tb_performance_trend_date ON tb_performance_trend(trend_date DESC);

-- Scenario recommendations
CREATE TABLE IF NOT EXISTS tb_recommendation_scenario (
    pk_scenario SERIAL PRIMARY KEY,
    id UUID UNIQUE NOT NULL,

    scenario_name VARCHAR(255) NOT NULL,
    scenario_description TEXT,
    target_use_case VARCHAR(255),

    recommended_framework_id UUID,
    reasoning TEXT,
    trade_offs TEXT,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_recommendation_scenario_id ON tb_recommendation_scenario(id);

-- Result exports
CREATE TABLE IF NOT EXISTS tb_result_export (
    pk_export SERIAL PRIMARY KEY,
    fk_run INTEGER NOT NULL REFERENCES tb_benchmark_run(pk_run) ON DELETE CASCADE,

    export_format VARCHAR(50),  -- JSON, CSV, PDF, HTML
    export_timestamp TIMESTAMP,
    export_file_path VARCHAR(500),
    file_size_bytes INT,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_result_export_run ON tb_result_export(fk_run);

-- ============================================================================
-- LEVEL 8: CODE & REPRODUCIBILITY (4 TABLES)
-- ============================================================================

-- Framework code snapshots
CREATE TABLE IF NOT EXISTS tb_code_snapshot (
    pk_snapshot SERIAL PRIMARY KEY,
    fk_run INTEGER NOT NULL REFERENCES tb_benchmark_run(pk_run) ON DELETE CASCADE,

    snapshot_type VARCHAR(50),  -- framework, database_library, optimization
    git_commit_hash VARCHAR(50),
    git_branch VARCHAR(255),
    snapshot_timestamp TIMESTAMP,
    content_hash VARCHAR(64),

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_code_snapshot_run ON tb_code_snapshot(fk_run);

-- Code file snapshots
CREATE TABLE IF NOT EXISTS tb_code_file_snapshot (
    pk_file_snapshot SERIAL PRIMARY KEY,
    fk_snapshot INTEGER NOT NULL REFERENCES tb_code_snapshot(pk_snapshot) ON DELETE CASCADE,

    file_path VARCHAR(500) NOT NULL,
    file_content_hash VARCHAR(64),
    lines_of_code INT,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_code_file_snapshot_snapshot ON tb_code_file_snapshot(fk_snapshot);

-- Query snapshots
CREATE TABLE IF NOT EXISTS tb_query_snapshot (
    pk_query_snapshot SERIAL PRIMARY KEY,
    fk_run INTEGER NOT NULL REFERENCES tb_benchmark_run(pk_run) ON DELETE CASCADE,

    query_content_hash VARCHAR(64),
    snapshot_timestamp TIMESTAMP,
    git_commit_hash VARCHAR(50),

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_query_snapshot_run ON tb_query_snapshot(fk_run);

-- Reproducibility manifest
CREATE TABLE IF NOT EXISTS tb_reproducibility_manifest (
    pk_manifest SERIAL PRIMARY KEY,
    fk_run INTEGER NOT NULL UNIQUE REFERENCES tb_benchmark_run(pk_run) ON DELETE CASCADE,

    manifest_data JSONB NOT NULL,  -- Complete run specification
    manifest_version VARCHAR(50),
    checksum VARCHAR(64),

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tb_reproducibility_manifest_run ON tb_reproducibility_manifest(fk_run);

-- ============================================================================
-- COMPOSITION VIEWS (Zero N+1 Queries)
-- ============================================================================

-- Pre-compose benchmark run with all basic data
CREATE OR REPLACE VIEW tv_benchmark_run AS
SELECT
    r.id,
    r.status,
    r.start_time,
    r.end_time,
    r.duration_seconds,
    r.jmeter_file_path,

    jsonb_build_object(
        'id', f.id,
        'name', f.name,
        'language', f.language,
        'languageFamily', f.language_family,
        'runtime', f.runtime,
        'version', f.version
    ) as framework,

    jsonb_build_object(
        'id', s.id,
        'name', s.name,
        'version', s.version
    ) as suite,

    jsonb_build_object(
        'id', w.id,
        'name', w.name,
        'queryComplexity', w.query_complexity
    ) as workload,

    jsonb_build_object(
        'id', lp.id,
        'name', lp.name,
        'rps', lp.rps,
        'threads', lp.threads,
        'durationSeconds', lp.duration_seconds
    ) as load_profile,

    jsonb_build_object(
        'id', tm.id,
        'cpuModel', tm.cpu_model,
        'cpuCores', tm.cpu_cores,
        'ramGb', tm.ram_gb,
        'osName', tm.os_name
    ) as test_machine,

    jsonb_build_object(
        'id', di.id,
        'engine', di.database_engine,
        'version', di.engine_version
    ) as database_instance

FROM tb_benchmark_run r
JOIN tb_framework f ON r.fk_framework = f.pk_framework
JOIN tb_benchmark_suite s ON r.fk_suite = s.pk_suite
JOIN tb_workload w ON r.fk_workload = w.pk_workload
JOIN tb_load_profile lp ON r.fk_load_profile = lp.pk_profile
LEFT JOIN tb_test_machine tm ON r.fk_test_machine = tm.pk_machine
LEFT JOIN tb_database_instance di ON r.fk_database_instance = di.pk_instance;

-- Pre-compose cost analysis with breakdowns
CREATE OR REPLACE VIEW tv_cost_analysis AS
SELECT
    ca.id,
    ca.fk_run,
    ca.recommended_cloud_provider,
    ca.recommended_instance_type,

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
        'requestsPerDollar', cb.requests_per_dollar,
        'instanceType', cb.instance_type,
        'instanceHourlyRate', cb.instance_hourly_rate
    ) ORDER BY cb.cloud_provider) FILTER (WHERE cb.cloud_provider IS NOT NULL) as cost_breakdowns,

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
LEFT JOIN tb_efficiency_ranking er ON ca.fk_run = er.fk_run
GROUP BY ca.id, ca.fk_run, ca.recommended_cloud_provider, ca.recommended_instance_type,
         er.efficiency_score, er.cost_component, er.latency_component,
         er.throughput_component, er.reliability_component, er.suite_rank;

-- ============================================================================
-- SEED DATA: Predefined Load Profiles
-- ============================================================================

INSERT INTO tb_load_profile (id, name, rps, duration_seconds, warmup_seconds, threads, ramp_up_time_seconds, think_time_ms)
VALUES
    (gen_random_uuid(), 'smoke', 10, 60, 5, 1, 0, 0),
    (gen_random_uuid(), 'small', 50, 120, 10, 5, 10, 100),
    (gen_random_uuid(), 'medium', 500, 180, 15, 50, 30, 50),
    (gen_random_uuid(), 'large', 5000, 300, 30, 500, 60, 10),
    (gen_random_uuid(), 'production', 10000, 600, 60, 1000, 120, 5)
ON CONFLICT DO NOTHING;
