# frozen_string_literal: true

module Actions
  class MetricsAction
    def call(_env)
      body = <<~METRICS
        # HELP hanami_requests_total Total number of GraphQL requests
        # TYPE hanami_requests_total counter
        hanami_requests_total 0
        # HELP hanami_db_pool_size Database connection pool size
        # TYPE hanami_db_pool_size gauge
        hanami_db_pool_size #{VelocityBench::DB.connection.pool.size}
      METRICS

      [
        200,
        {
          "Content-Type" => "text/plain; charset=utf-8",
          "Content-Length" => body.bytesize.to_s
        },
        [body]
      ]
    end
  end
end
