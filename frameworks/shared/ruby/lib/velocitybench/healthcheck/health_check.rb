# frozen_string_literal: true

module VelocityBench
  module HealthCheck
    # Individual health check result.
    class HealthCheck
      attr_accessor :status
      attr_reader :response_time_ms, :error, :warning, :info, :additional_data

      def initialize(status)
        @status = status
        @response_time_ms = nil
        @error = nil
        @warning = nil
        @info = nil
        @additional_data = {}
      end

      def with_response_time(ms)
        @response_time_ms = ms
        self
      end

      def with_error(error)
        @error = error
        self
      end

      def with_warning(warning)
        @warning = warning
        self
      end

      def with_info(info)
        @info = info
        self
      end

      def with_data(key, value)
        @additional_data[key] = value
        self
      end

      def to_h
        result = { status: @status }
        result[:response_time_ms] = @response_time_ms if @response_time_ms
        result[:error] = @error if @error
        result[:warning] = @warning if @warning
        result[:info] = @info if @info
        result.merge(@additional_data)
      end

      def to_json(*_args)
        to_h.to_json
      end
    end
  end
end
