# frozen_string_literal: true

require 'time'
require 'json'

module VelocityBench
  module HealthCheck
    # Health check manager for Ruby frameworks.
    class HealthCheckManager
      CACHE_TTL_MS = 5000 # 5 seconds

      def initialize(config)
        @config = config
        @start_time = Time.now
        @database = nil
        @cache = {}
      end

      # Set database connection for health checks.
      def with_database(connection)
        @database = connection
        self
      end

      # Execute a health check probe.
      def probe(probe_type)
        probe = ProbeType.from_string(probe_type)

        # Check cache
        cached = get_cached_result(probe)
        return cached if cached

        # Execute probe
        result = case probe
                 when ProbeType::LIVENESS
                   liveness_probe
                 when ProbeType::READINESS
                   readiness_probe
                 when ProbeType::STARTUP
                   startup_probe
                 end

        # Cache result
        cache_result(probe, result)

        result
      end

      private

      # Get cached result if still valid.
      def get_cached_result(probe_type)
        return nil unless @cache[probe_type]

        cached = @cache[probe_type]
        age_ms = (Time.now.to_f - cached[:timestamp]) * 1000

        return cached[:result] if age_ms < CACHE_TTL_MS

        nil
      end

      # Cache a health check result.
      def cache_result(probe_type, result)
        @cache[probe_type] = {
          result: result,
          timestamp: Time.now.to_f
        }
      end

      # Liveness probe: Is the process alive?
      def liveness_probe
        checks = {
          'memory' => check_memory
        }

        overall_status = compute_overall_status(checks)

        HealthCheckResponse.new(
          status: overall_status,
          timestamp: get_timestamp,
          uptime_ms: get_uptime_ms,
          version: @config.version,
          service: @config.service_name,
          environment: @config.environment,
          probe_type: ProbeType::LIVENESS,
          checks: checks
        )
      end

      # Readiness probe: Can the service handle traffic?
      def readiness_probe
        checks = {}

        # Database check
        checks['database'] = check_database if @database

        # Memory check
        checks['memory'] = check_memory

        overall_status = compute_overall_status(checks)

        HealthCheckResponse.new(
          status: overall_status,
          timestamp: get_timestamp,
          uptime_ms: get_uptime_ms,
          version: @config.version,
          service: @config.service_name,
          environment: @config.environment,
          probe_type: ProbeType::READINESS,
          checks: checks
        )
      end

      # Startup probe: Has initialization completed?
      def startup_probe
        checks = {}

        # Database check
        checks['database'] = check_database if @database

        # Warmup check
        checks['warmup'] = check_warmup

        # Memory check
        checks['memory'] = check_memory

        overall_status = compute_overall_status(checks)

        HealthCheckResponse.new(
          status: overall_status,
          timestamp: get_timestamp,
          uptime_ms: get_uptime_ms,
          version: @config.version,
          service: @config.service_name,
          environment: @config.environment,
          probe_type: ProbeType::STARTUP,
          checks: checks
        )
      end

      # Check database connectivity.
      def check_database
        start_time = Time.now

        begin
          # Execute simple query
          @database.exec('SELECT 1')

          response_time = (Time.now - start_time) * 1000

          HealthCheck.new(HealthStatus::UP)
            .with_response_time(response_time.round(2))
            .with_data('pool_size', 0)
            .with_data('pool_available', 0)

        rescue StandardError => e
          HealthCheck.new(HealthStatus::DOWN)
            .with_error("Database connection error: #{e.message}")
        end
      end

      # Check memory usage.
      def check_memory
        # Get process memory usage (RSS)
        pid = Process.pid
        memory_kb = `ps -o rss= -p #{pid}`.strip.to_i
        used_mb = memory_kb / 1024.0

        # Estimate total available memory (simplified)
        total_mb = 2048.0 # Default assumption
        utilization = (used_mb / total_mb) * 100

        check = HealthCheck.new(HealthStatus::UP)
          .with_data('used_mb', used_mb.round(2))
          .with_data('total_mb', total_mb.round(2))
          .with_data('utilization_percent', utilization.round(2))

        if utilization > 90.0
          check.status = HealthStatus::DEGRADED
          check.with_warning(format('Critical memory usage (%.1f%%)', utilization))
        elsif utilization > 80.0
          check.with_warning(format('High memory usage (%.1f%%)', utilization))
        end

        check
      end

      # Check if warmup period has completed.
      def check_warmup
        uptime_ms = get_uptime_ms

        if uptime_ms < @config.startup_duration_ms
          progress = (uptime_ms.to_f / @config.startup_duration_ms) * 100
          HealthCheck.new(HealthStatus::IN_PROGRESS)
            .with_info(format('Warming up (%.0f%% complete)', progress))
            .with_data('progress_percent', progress.round(2))
            .with_data('uptime_ms', uptime_ms)
            .with_data('target_ms', @config.startup_duration_ms)
        else
          HealthCheck.new(HealthStatus::UP)
            .with_info('Warmup complete')
        end
      end

      # Compute overall health status from individual checks.
      def compute_overall_status(checks)
        has_down = false
        has_in_progress = false
        has_degraded = false

        checks.each_value do |check|
          case check.status
          when HealthStatus::DOWN
            has_down = true
          when HealthStatus::IN_PROGRESS
            has_in_progress = true
          when HealthStatus::DEGRADED
            has_degraded = true
          end
        end

        return HealthStatus::DOWN if has_down
        return HealthStatus::IN_PROGRESS if has_in_progress
        return HealthStatus::DEGRADED if has_degraded

        HealthStatus::UP
      end

      # Get service uptime in milliseconds.
      def get_uptime_ms
        ((Time.now - @start_time) * 1000).to_i
      end

      # Get current timestamp in ISO 8601 format.
      def get_timestamp
        Time.now.utc.iso8601(3)
      end
    end
  end
end
