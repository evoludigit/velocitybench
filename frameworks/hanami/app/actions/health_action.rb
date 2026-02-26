# frozen_string_literal: true

module Actions
  class HealthAction
    def call(_env)
      healthy = VelocityBench::DB.healthy?

      status = healthy ? 200 : 503
      body = Oj.dump({
        status: healthy ? "healthy" : "unhealthy",
        framework: "hanami"
      }, mode: :compat)

      [
        status,
        {
          "Content-Type" => "application/json",
          "Content-Length" => body.bytesize.to_s
        },
        [body]
      ]
    end
  end
end
