class MetricsMiddleware
  def initialize(app)
    @app = app
  end

  def call(env)
    start_time = Time.now.to_f
    
    # Extract request information
    request = Rack::Request.new(env)
    method = request.request_method
    path = request.path
    
    # Call the next middleware/app
    status, headers, response = @app.call(env)
    
    # Calculate request duration
    duration = Time.now.to_f - start_time
    
    # Update metrics
    begin
      # Request counter
      $prometheus_requests.increment(labels: { method: method, endpoint: path, status: status.to_s })
      
      # Request duration histogram
      $prometheus_request_duration.observe(duration, labels: { method: method, endpoint: path })
    rescue => e
      # Log error but don't break the response
      Rails.logger.error "Metrics collection error: #{e.message}" if defined?(Rails)
    end
    
    # Return the response
    [status, headers, response]
  end
end
