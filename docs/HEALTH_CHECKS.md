# Health Check Implementation Guide

VelocityBench provides standardized health check libraries across all languages, implementing Kubernetes-compatible probes (liveness, readiness, startup) for production observability.

## Overview

Health checks are critical for:
- **Kubernetes deployments**: Automatic pod lifecycle management
- **Load balancers**: Intelligent traffic routing
- **Monitoring systems**: Service health visibility
- **Zero-downtime deployments**: Graceful startup and shutdown

## Unified Specification

All VelocityBench frameworks implement the same health check specification for consistency.

### Endpoints

| Endpoint | Purpose | K8s Probe |
|----------|---------|-----------|
| `GET /health` | Combined check (default: readiness) | - |
| `GET /health/live` | Is the process alive? | livenessProbe |
| `GET /health/ready` | Can handle traffic? | readinessProbe |
| `GET /health/startup` | Initialization complete? | startupProbe |

### Response Schema

```json
{
  "status": "up|degraded|down|in_progress",
  "timestamp": "2025-01-30T14:30:00.123Z",
  "uptime_ms": 3456789,
  "version": "1.0.0",
  "service": "my-service",
  "environment": "production",
  "probe_type": "liveness|readiness|startup",
  "checks": {
    "database": {
      "status": "up",
      "response_time_ms": 5.2,
      "pool_size": 10,
      "pool_available": 8,
      "pool_max_size": 20
    },
    "memory": {
      "status": "up",
      "used_mb": 128.5,
      "total_mb": 512.0,
      "utilization_percent": 25.1
    }
  }
}
```

### HTTP Status Codes

| Status | Probe State | HTTP Code |
|--------|-------------|-----------|
| `up` | Healthy | 200 OK |
| `degraded` | Functional with warnings | 200 OK |
| `down` | Unhealthy | 503 Service Unavailable |
| `in_progress` | Warming up (startup probe) | 202 Accepted |

### Probe Types Explained

#### Liveness Probe
**Question**: "Is the process alive?"

**Purpose**: Detect deadlocks, infinite loops, or hung processes

**Checks**:
- Memory monitoring only (lightweight)
- No database or external dependencies

**Kubernetes behavior**: Kill and restart pod if fails

**Example response**:
```json
{
  "status": "up",
  "probe_type": "liveness",
  "checks": {
    "memory": {
      "status": "up",
      "used_mb": 45.3,
      "utilization_percent": 8.9
    }
  }
}
```

#### Readiness Probe
**Question**: "Can the service handle traffic?"

**Purpose**: Determine if service should receive requests

**Checks**:
- Database connectivity
- Memory monitoring
- External service dependencies (optional)

**Kubernetes behavior**: Remove from load balancer if fails

**Example response**:
```json
{
  "status": "up",
  "probe_type": "readiness",
  "checks": {
    "database": {
      "status": "up",
      "response_time_ms": 3.2,
      "pool_available": 15
    },
    "memory": {
      "status": "up",
      "utilization_percent": 12.3
    }
  }
}
```

#### Startup Probe
**Question**: "Has initialization completed?"

**Purpose**: Give slow-starting applications time to start

**Checks**:
- Database connectivity
- Warmup progress
- Memory monitoring

**Kubernetes behavior**: Delay liveness/readiness probes until passes

**Example response**:
```json
{
  "status": "in_progress",
  "probe_type": "startup",
  "checks": {
    "database": {
      "status": "up"
    },
    "warmup": {
      "status": "in_progress",
      "info": "Warming up (67% complete)",
      "progress_percent": 67,
      "uptime_ms": 20000,
      "target_ms": 30000
    },
    "memory": {
      "status": "up"
    }
  }
}
```

## Language-Specific Implementations

### Python

**Library**: `frameworks/common/health_check.py`

**Installation**: No separate installation needed (shared library)

**Basic usage**:
```python
from frameworks.common.health_check import HealthCheckManager, HealthCheckConfig

config = HealthCheckConfig(
    service_name="my-service",
    version="1.0.0",
    database=db_pool,
    environment="production",
)

health_manager = HealthCheckManager(config)
result = await health_manager.probe("readiness")
```

**FastAPI integration**:
```python
from fastapi import FastAPI
from frameworks.common.health_check import HealthCheckManager

@app.get("/health")
async def health():
    return await app.state.health.probe("readiness")

@app.get("/health/live")
async def health_live():
    return await app.state.health.probe("liveness")

@app.get("/health/ready")
async def health_ready():
    return await app.state.health.probe("readiness")

@app.get("/health/startup")
async def health_startup():
    return await app.state.health.probe("startup")
```

**Flask integration** (synchronous):
```python
from flask import Flask, jsonify
from frameworks.common.health_check_sync import HealthCheckManagerSync

app = Flask(__name__)
health_manager = HealthCheckManagerSync(config)

@app.route("/health")
def health():
    result = health_manager.probe("readiness")
    return jsonify(result), result.get("http_status_code", 200)
```

### TypeScript/Node.js

**Library**: `frameworks/shared/typescript/health-check.ts`

**Installation**:
```bash
npm install --save ../shared/typescript
```

**Basic usage**:
```typescript
import { HealthCheckManager, HealthCheckConfig } from 'velocitybench-healthcheck';

const config: HealthCheckConfig = {
  serviceName: 'my-service',
  version: '1.0.0',
  environment: 'production',
  startupDurationMs: 30000,
};

const healthManager = new HealthCheckManager(config, dbPool);
const result = await healthManager.probe('readiness');
```

**Express integration**:
```typescript
import express from 'express';
import { expressHealthCheckMiddleware } from 'velocitybench-healthcheck';

const app = express();
app.use(expressHealthCheckMiddleware(healthManager));

app.get('/health', async (req, res) => {
  const result = await healthManager.probe('readiness');
  res.status(result.httpStatusCode()).json(result);
});
```

**Fastify integration**:
```typescript
import Fastify from 'fastify';

fastify.get('/health', async (request, reply) => {
  const result = await healthManager.probe('readiness');
  reply.code(result.httpStatusCode()).send(result);
});
```

### Go

**Library**: `frameworks/shared/go/health_check.go`

**Installation**:
```bash
go get ./frameworks/shared/go
```

**Basic usage**:
```go
import "velocitybench/healthcheck"

config := healthcheck.HealthCheckConfig{
    ServiceName: "my-service",
    Version:     "1.0.0",
    Environment: "production",
}

manager := healthcheck.NewHealthCheckManager(config, dbPool)
result, err := manager.Probe("readiness")
```

**HTTP handler**:
```go
func healthHandler(w http.ResponseWriter, r *http.Request) {
    result, err := healthManager.Probe("readiness")
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }

    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(result.HTTPStatusCode())
    json.NewEncoder(w).Encode(result)
}

http.HandleFunc("/health", healthHandler)
```

### Rust

**Library**: `frameworks/shared/rust/`

**Installation** (Cargo.toml):
```toml
[dependencies]
velocitybench-healthcheck = { path = "../shared/rust" }

# Enable features as needed
velocitybench-healthcheck = {
    path = "../shared/rust",
    features = ["actix", "database"]
}
```

**Actix-web integration**:
```rust
use actix_web::{web, App, HttpServer};
use velocitybench_healthcheck::{HealthCheckManager, HealthCheckConfig};
use velocitybench_healthcheck::actix::configure_health_routes;

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    let config = HealthCheckConfig::default();
    let health_manager = web::Data::new(HealthCheckManager::new(config));

    HttpServer::new(move || {
        App::new()
            .app_data(health_manager.clone())
            .configure(configure_health_routes)
    })
    .bind(("127.0.0.1", 8080))?
    .run()
    .await
}
```

**Axum integration**:
```rust
use axum::{Router, routing::get};
use velocitybench_healthcheck::axum_support;

let app = Router::new()
    .nest("/health", axum_support::health_routes())
    .with_state(health_manager);
```

### Java/Spring Boot

**Library**: `frameworks/shared/java/`

**Installation** (pom.xml):
```xml
<dependency>
    <groupId>com.velocitybench</groupId>
    <artifactId>velocitybench-healthcheck</artifactId>
    <version>1.0.0</version>
</dependency>
```

**Spring Boot integration**:
```java
@Configuration
public class HealthCheckConfiguration {
    @Bean
    public HealthCheckManager healthCheckManager(DataSource dataSource) {
        HealthCheckConfig config = new HealthCheckConfig();
        config.setServiceName("my-service");
        config.setVersion("1.0.0");

        return new HealthCheckManager(config)
                .withDatabase(dataSource);
    }

    @Bean
    public SpringHealthCheckController healthCheckController(
            HealthCheckManager healthCheckManager) {
        return new SpringHealthCheckController(healthCheckManager);
    }
}
```

### PHP

**Library**: `frameworks/shared/php/`

**Installation** (composer.json):
```json
{
    "require": {
        "velocitybench/healthcheck": "^1.0"
    }
}
```

**Laravel integration**:
```php
<?php
namespace App\Http\Controllers;

use VelocityBench\HealthCheck\{HealthCheckManager, HealthCheckConfig};

class HealthController extends Controller
{
    private HealthCheckManager $healthManager;

    public function __construct()
    {
        $config = new HealthCheckConfig(
            serviceName: config('app.name'),
            version: '1.0.0',
            environment: config('app.env')
        );

        $this->healthManager = (new HealthCheckManager($config))
            ->withDatabase(DB::connection()->getPdo());
    }

    public function health()
    {
        $result = $this->healthManager->probe('readiness');
        return response()->json($result, $result->getHttpStatusCode());
    }
}
```

### Ruby

**Library**: `frameworks/shared/ruby/`

**Installation** (Gemfile):
```ruby
gem 'velocitybench-healthcheck'
```

**Rails integration**:
```ruby
class HealthController < ApplicationController
  def health
    result = health_manager.probe('readiness')
    render json: result.to_h, status: result.http_status_code
  end

  private

  def health_manager
    @health_manager ||= VelocityBench::HealthCheck::HealthCheckManager.new(config)
      .with_database(ActiveRecord::Base.connection.raw_connection)
  end

  def config
    VelocityBench::HealthCheck::HealthCheckConfig.new(
      service_name: Rails.application.class.module_parent_name,
      version: '1.0.0',
      environment: Rails.env
    )
  end
end
```

### C#/.NET

**Library**: `frameworks/shared/csharp/`

**Installation** (.csproj):
```xml
<ItemGroup>
    <PackageReference Include="VelocityBench.HealthCheck" Version="1.0.0" />
</ItemGroup>
```

**ASP.NET Core integration**:
```csharp
// Program.cs
var builder = WebApplication.CreateBuilder(args);

var healthConfig = new HealthCheckConfig
{
    ServiceName = "my-api",
    Version = "1.0.0",
    Environment = builder.Environment.EnvironmentName
};

builder.Services.AddSingleton(new HealthCheckManager(healthConfig));

var app = builder.Build();

app.MapGet("/health", async (HealthCheckManager manager) =>
{
    var result = await manager.ProbeAsync("readiness");
    return Results.Json(result, statusCode: result.GetHttpStatusCode());
});
```

## Kubernetes Deployment

### Basic Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-service
  template:
    metadata:
      labels:
        app: my-service
    spec:
      containers:
      - name: app
        image: my-service:latest
        ports:
        - containerPort: 8080
          name: http

        # Liveness probe: Restart if unhealthy
        livenessProbe:
          httpGet:
            path: /health/live
            port: http
          initialDelaySeconds: 10
          periodSeconds: 10
          timeoutSeconds: 3
          failureThreshold: 3

        # Readiness probe: Remove from load balancer if not ready
        readinessProbe:
          httpGet:
            path: /health/ready
            port: http
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3

        # Startup probe: Give time for slow startup
        startupProbe:
          httpGet:
            path: /health/startup
            port: http
          initialDelaySeconds: 0
          periodSeconds: 10
          timeoutSeconds: 3
          failureThreshold: 30  # 5 minutes max startup time
```

### Probe Configuration Best Practices

**Liveness Probe**:
- `initialDelaySeconds`: 10-30s (time for app to start basic processes)
- `periodSeconds`: 10s (check every 10 seconds)
- `timeoutSeconds`: 3s (probe must respond within 3 seconds)
- `failureThreshold`: 3 (restart after 3 consecutive failures)

**Readiness Probe**:
- `initialDelaySeconds`: 5-15s (time for app to connect to dependencies)
- `periodSeconds`: 5s (check frequently for quick recovery)
- `timeoutSeconds`: 3s
- `failureThreshold`: 3 (remove from LB after 3 failures)

**Startup Probe**:
- `initialDelaySeconds`: 0 (start checking immediately)
- `periodSeconds`: 10s (don't check too frequently during startup)
- `timeoutSeconds`: 3s
- `failureThreshold`: 30 (allow up to 5 minutes for startup)

### Rolling Update Strategy

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-service
spec:
  replicas: 5
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0  # Zero-downtime deployments
  template:
    spec:
      containers:
      - name: app
        # ... health probes configured ...

        # Graceful shutdown
        lifecycle:
          preStop:
            exec:
              command: ["sh", "-c", "sleep 15"]

        terminationGracePeriodSeconds: 30
```

## Monitoring Integration

### Prometheus Metrics

Export health check results as Prometheus metrics:

```python
# Python example
from prometheus_client import Gauge

health_status = Gauge('app_health_status', 'Health status', ['probe_type', 'check'])

@app.get("/health/ready")
async def health_ready():
    result = await health_manager.probe("readiness")

    # Export to Prometheus
    for check_name, check in result.checks.items():
        status_value = 1 if check.status == "up" else 0
        health_status.labels(
            probe_type="readiness",
            check=check_name
        ).set(status_value)

    return result
```

### Grafana Dashboard

Example PromQL queries:

```promql
# Health status by probe type
app_health_status{probe_type="readiness"}

# Database health across all services
app_health_status{check="database"}

# Services with degraded health
app_health_status < 1

# Alert: Service unhealthy for 2 minutes
ALERTS{alertname="ServiceUnhealthy"}
  FOR 2m
  IF app_health_status{probe_type="readiness"} == 0
```

## Testing Health Checks

### Manual Testing

```bash
# Test liveness
curl http://localhost:8080/health/live

# Test readiness
curl http://localhost:8080/health/ready

# Test startup
curl http://localhost:8080/health/startup

# Check response time
time curl http://localhost:8080/health/ready
```

### Automated Testing

```python
import pytest
import httpx

@pytest.mark.asyncio
async def test_health_endpoints():
    async with httpx.AsyncClient() as client:
        # Test liveness
        response = await client.get("http://localhost:8080/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["up", "degraded"]
        assert data["probe_type"] == "liveness"

        # Test readiness
        response = await client.get("http://localhost:8080/health/ready")
        assert response.status_code in [200, 503]
        data = response.json()
        assert "checks" in data
        assert "database" in data["checks"]
```

## Troubleshooting

### Issue: Health checks timing out

**Symptoms**: Kubernetes restarting pods, 503 errors

**Causes**:
- Database queries too slow
- Memory monitoring taking too long
- Timeout too short

**Solutions**:
```yaml
# Increase timeout
livenessProbe:
  timeoutSeconds: 5  # Increase from 3

# Or simplify liveness (no DB check)
# Liveness should only check if process is alive
```

### Issue: Pods restarting during deployment

**Symptoms**: Service disruption during rolling updates

**Causes**:
- Startup probe too aggressive
- Not enough time for graceful shutdown

**Solutions**:
```yaml
# Increase startup probe failure threshold
startupProbe:
  failureThreshold: 60  # Allow more time

# Add preStop hook
lifecycle:
  preStop:
    exec:
      command: ["sh", "-c", "sleep 20"]
```

### Issue: False positive health failures

**Symptoms**: Intermittent health check failures

**Causes**:
- Noisy environment
- Database connection pool exhausted temporarily

**Solutions**:
- Increase failure threshold
- Add connection pool monitoring
- Use degraded status instead of down

## Best Practices

1. **Keep liveness checks simple**: Only check if process is alive
2. **Readiness checks dependencies**: Check database, cache, external APIs
3. **Use startup probes for slow apps**: Give time for initialization
4. **Set appropriate timeouts**: 3-5 seconds for most cases
5. **Monitor health check response times**: Slow checks can cause cascading failures
6. **Use degraded status for warnings**: Don't fail immediately on minor issues
7. **Cache results**: 5-second TTL prevents check storms
8. **Test locally**: Use curl to verify before deploying
9. **Log health check failures**: Include diagnostic info
10. **Document expected startup time**: Configure startup probe accordingly

## See Also

- [Kubernetes Liveness, Readiness, and Startup Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [ADR-010: Benchmarking Methodology](adr/010-benchmarking-methodology.md)
- [HEALTH_CHECK_SPEC.md](HEALTH_CHECK_SPEC.md) - Detailed specification
- Per-language library READMEs in `frameworks/shared/{language}/README.md`
