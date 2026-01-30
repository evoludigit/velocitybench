# VelocityBench Ruby Health Check Library

Standardized health check library for VelocityBench Ruby frameworks.

## Features

- **Kubernetes-compatible probes**: Liveness, readiness, and startup
- **Database health checks**: PostgreSQL/ActiveRecord integration
- **Memory monitoring**: Process memory statistics
- **Result caching**: 5-second TTL to reduce overhead
- **Ruby 3.0+**: Modern Ruby with pattern matching

## Installation

Add to your `Gemfile`:

```ruby
gem 'velocitybench-healthcheck'
```

Or install directly:

```bash
gem install velocitybench-healthcheck
```

## Usage

### Basic Usage

```ruby
require 'velocitybench/healthcheck'

config = VelocityBench::HealthCheck::HealthCheckConfig.new(
  service_name: 'my-service',
  version: '1.0.0',
  environment: 'production',
  startup_duration_ms: 30_000
)

health_manager = VelocityBench::HealthCheck::HealthCheckManager.new(config)

# Execute health check
result = health_manager.probe('readiness')
puts "Status: #{result.status}"
puts "HTTP Status Code: #{result.http_status_code}"
```

### With Database

```ruby
require 'velocitybench/healthcheck'
require 'pg'

# Create PostgreSQL connection
db = PG.connect(dbname: 'mydb', user: 'user', password: 'password')

config = VelocityBench::HealthCheck::HealthCheckConfig.new(
  service_name: 'my-service',
  version: '1.0.0'
)

health_manager = VelocityBench::HealthCheck::HealthCheckManager.new(config)
  .with_database(db)

result = health_manager.probe('readiness')
```

### With Rails

```ruby
# app/controllers/health_controller.rb
class HealthController < ApplicationController
  def initialize
    super
    config = VelocityBench::HealthCheck::HealthCheckConfig.new(
      service_name: Rails.application.class.module_parent_name,
      version: '1.0.0',
      environment: Rails.env
    )

    @health_manager = VelocityBench::HealthCheck::HealthCheckManager.new(config)
      .with_database(ActiveRecord::Base.connection.raw_connection)
  end

  def health
    result = @health_manager.probe('readiness')
    render json: result.to_h, status: result.http_status_code
  end

  def liveness
    result = @health_manager.probe('liveness')
    render json: result.to_h, status: result.http_status_code
  end

  def readiness
    result = @health_manager.probe('readiness')
    render json: result.to_h, status: result.http_status_code
  end

  def startup
    result = @health_manager.probe('startup')
    render json: result.to_h, status: result.http_status_code
  end
end
```

Add routes in `config/routes.rb`:

```ruby
get '/health', to: 'health#health'
get '/health/live', to: 'health#liveness'
get '/health/ready', to: 'health#readiness'
get '/health/startup', to: 'health#startup'
```

### With Sinatra

```ruby
require 'sinatra'
require 'velocitybench/healthcheck'

config = VelocityBench::HealthCheck::HealthCheckConfig.new(
  service_name: 'sinatra-app',
  version: '1.0.0'
)

health_manager = VelocityBench::HealthCheck::HealthCheckManager.new(config)

get '/health' do
  result = health_manager.probe('readiness')
  status result.http_status_code
  content_type :json
  result.to_json
end

get '/health/live' do
  result = health_manager.probe('liveness')
  status result.http_status_code
  content_type :json
  result.to_json
end

get '/health/ready' do
  result = health_manager.probe('readiness')
  status result.http_status_code
  content_type :json
  result.to_json
end

get '/health/startup' do
  result = health_manager.probe('startup')
  status result.http_status_code
  content_type :json
  result.to_json
end
```

## Response Format

```json
{
  "status": "up",
  "timestamp": "2025-01-30T14:30:00.123Z",
  "uptime_ms": 3456789,
  "version": "1.0.0",
  "service": "my-service",
  "environment": "production",
  "probe_type": "readiness",
  "checks": {
    "database": {
      "status": "up",
      "response_time_ms": 5.2,
      "pool_size": 10,
      "pool_available": 8
    },
    "memory": {
      "status": "up",
      "used_mb": 45.3,
      "total_mb": 2048.0,
      "utilization_percent": 2.2
    }
  }
}
```

## Probe Types

### Liveness Probe
Checks if the process is alive. Returns:
- Memory monitoring only (lightweight check)

### Readiness Probe
Checks if the service can handle traffic. Returns:
- Database connectivity check
- Memory monitoring

### Startup Probe
Checks if initialization has completed. Returns:
- Database connectivity check
- Warmup progress (based on startup duration)
- Memory monitoring

## HTTP Status Codes

- `200 OK` - Service is healthy (status: up or degraded)
- `202 Accepted` - Service is warming up (startup probe only)
- `503 Service Unavailable` - Service is unhealthy (status: down)

## Kubernetes Deployment

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-service
spec:
  containers:
  - name: app
    image: my-service:latest
    ports:
    - containerPort: 8080
    livenessProbe:
      httpGet:
        path: /health/live
        port: 8080
      initialDelaySeconds: 10
      periodSeconds: 10
      timeoutSeconds: 3
      failureThreshold: 3
    readinessProbe:
      httpGet:
        path: /health/ready
        port: 8080
      initialDelaySeconds: 5
      periodSeconds: 5
      timeoutSeconds: 3
      failureThreshold: 3
    startupProbe:
      httpGet:
        path: /health/startup
        port: 8080
      initialDelaySeconds: 0
      periodSeconds: 10
      timeoutSeconds: 3
      failureThreshold: 30
```

## License

MIT
