# frozen_string_literal: true

module VelocityBench
  module HealthCheck
    # Health check probe types (Kubernetes-compatible).
    module ProbeType
      LIVENESS = 'liveness'
      READINESS = 'readiness'
      STARTUP = 'startup'

      ALL = [LIVENESS, READINESS, STARTUP].freeze

      def self.from_string(value)
        normalized = value.to_s.downcase
        return normalized if ALL.include?(normalized)

        raise ArgumentError, "Unknown probe type: #{value}"
      end

      def self.valid?(probe_type)
        ALL.include?(probe_type)
      end
    end
  end
end
