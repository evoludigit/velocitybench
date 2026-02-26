# frozen_string_literal: true

module VelocityBench
  class DB
    class << self
      def connection
        @connection ||= create_connection
      end

      def create_connection
        Sequel.connect(
          adapter: "postgres",
          host: ENV.fetch("DB_HOST", "localhost"),
          port: ENV.fetch("DB_PORT", "5432").to_i,
          database: ENV.fetch("DB_NAME", "fraiseql_benchmark"),
          user: ENV.fetch("DB_USER", "benchmark"),
          password: ENV.fetch("DB_PASSWORD", "benchmark123"),
          max_connections: ENV.fetch("DB_POOL_MAX", "50").to_i,
          pool_timeout: 10,
          search_path: ["benchmark", "public"]
        )
      end

      def disconnect
        @connection&.disconnect
        @connection = nil
      end

      def healthy?
        connection.test_connection
      rescue StandardError
        false
      end
    end
  end
end
