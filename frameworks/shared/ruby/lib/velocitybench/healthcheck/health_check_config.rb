# frozen_string_literal: true

module VelocityBench
  module HealthCheck
    # Health check manager configuration.
    class HealthCheckConfig
      attr_accessor :service_name, :version, :environment, :startup_duration_ms

      def initialize(service_name: 'velocitybench', version: '1.0.0',
                     environment: 'development', startup_duration_ms: 30_000)
        @service_name = service_name
        @version = version
        @environment = environment
        @startup_duration_ms = startup_duration_ms
      end
    end
  end
end
