# frozen_string_literal: true

module VelocityBench
  module HealthCheck
    # Health check status values.
    module HealthStatus
      UP = 'up'
      DEGRADED = 'degraded'
      DOWN = 'down'
      IN_PROGRESS = 'in_progress'

      ALL = [UP, DEGRADED, DOWN, IN_PROGRESS].freeze

      def self.valid?(status)
        ALL.include?(status)
      end
    end
  end
end
