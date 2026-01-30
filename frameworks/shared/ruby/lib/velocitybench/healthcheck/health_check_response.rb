# frozen_string_literal: true

module VelocityBench
  module HealthCheck
    # Complete health check response.
    class HealthCheckResponse
      attr_reader :status, :timestamp, :uptime_ms, :version, :service,
                  :environment, :probe_type, :checks

      def initialize(status:, timestamp:, uptime_ms:, version:, service:,
                     environment:, probe_type:, checks:)
        @status = status
        @timestamp = timestamp
        @uptime_ms = uptime_ms
        @version = version
        @service = service
        @environment = environment
        @probe_type = probe_type
        @checks = checks
      end

      # Get HTTP status code based on health status and probe type.
      def http_status_code
        case @status
        when HealthStatus::DOWN
          503
        when HealthStatus::IN_PROGRESS
          @probe_type == ProbeType::STARTUP ? 202 : 200
        else
          200
        end
      end

      def to_h
        {
          status: @status,
          timestamp: @timestamp,
          uptime_ms: @uptime_ms,
          version: @version,
          service: @service,
          environment: @environment,
          probe_type: @probe_type,
          checks: @checks.transform_values(&:to_h)
        }
      end

      def to_json(*_args)
        to_h.to_json
      end
    end
  end
end
