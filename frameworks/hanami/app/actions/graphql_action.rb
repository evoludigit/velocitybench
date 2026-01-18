# frozen_string_literal: true

module Actions
  class GraphqlAction
    def call(env)
      request = Rack::Request.new(env)

      # Parse request body
      body = request.body.read
      params = body.empty? ? {} : Oj.load(body, symbol_keys: true)

      query = params[:query]
      variables = params[:variables] || {}
      operation_name = params[:operationName]

      # Execute GraphQL query
      result = VelocityBench::GraphQL::Schema.execute(
        query,
        variables: variables,
        operation_name: operation_name,
        context: {}
      )

      response_body = Oj.dump(result.to_h, mode: :compat)

      [
        200,
        {
          "Content-Type" => "application/json",
          "Content-Length" => response_body.bytesize.to_s
        },
        [response_body]
      ]
    rescue StandardError => e
      error_response = Oj.dump({ errors: [{ message: e.message }] }, mode: :compat)

      [
        500,
        {
          "Content-Type" => "application/json",
          "Content-Length" => error_response.bytesize.to_s
        },
        [error_response]
      ]
    end
  end
end
