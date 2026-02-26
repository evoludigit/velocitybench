# VelocityBench .NET Health Check Library

Standardized health check library for VelocityBench .NET frameworks.

## Features

- **Kubernetes-compatible probes**: Liveness, readiness, and startup
- **Database health checks**: DbConnection integration
- **Memory monitoring**: Process and GC memory statistics
- **Result caching**: 5-second TTL to reduce overhead
- **.NET 8.0+**: Modern C# with nullable reference types

## Installation

```bash
dotnet add package VelocityBench.HealthCheck
```

## Usage

### Basic Usage

```csharp
using VelocityBench.HealthCheck;

var config = new HealthCheckConfig
{
    ServiceName = "my-service",
    Version = "1.0.0",
    Environment = "production",
    StartupDurationMs = 30000
};

var healthManager = new HealthCheckManager(config);

// Execute health check
var result = await healthManager.ProbeAsync("readiness");
Console.WriteLine($"Status: {result.Status}");
Console.WriteLine($"HTTP Status Code: {result.GetHttpStatusCode()}");
```

### With Database

```csharp
using System.Data.Common;
using Npgsql;
using VelocityBench.HealthCheck;

// Create database connection
var connectionString = "Host=localhost;Database=mydb;Username=user;Password=password";
var connection = new NpgsqlConnection(connectionString);

var config = new HealthCheckConfig
{
    ServiceName = "my-service",
    Version = "1.0.0"
};

var healthManager = new HealthCheckManager(config)
    .WithDatabase(connection);

var result = await healthManager.ProbeAsync("readiness");
```

### With ASP.NET Core

```csharp
// Program.cs
using Microsoft.AspNetCore.Mvc;
using VelocityBench.HealthCheck;

var builder = WebApplication.CreateBuilder(args);

// Configure health check manager
var healthConfig = new HealthCheckConfig
{
    ServiceName = "my-api",
    Version = "1.0.0",
    Environment = builder.Environment.EnvironmentName
};

var healthManager = new HealthCheckManager(healthConfig);

// Register as singleton
builder.Services.AddSingleton(healthManager);

var app = builder.Build();

// Health check endpoints
app.MapGet("/health", async ([FromServices] HealthCheckManager manager) =>
{
    var result = await manager.ProbeAsync("readiness");
    return Results.Json(result, statusCode: result.GetHttpStatusCode());
});

app.MapGet("/health/live", async ([FromServices] HealthCheckManager manager) =>
{
    var result = await manager.ProbeAsync("liveness");
    return Results.Json(result, statusCode: result.GetHttpStatusCode());
});

app.MapGet("/health/ready", async ([FromServices] HealthCheckManager manager) =>
{
    var result = await manager.ProbeAsync("readiness");
    return Results.Json(result, statusCode: result.GetHttpStatusCode());
});

app.MapGet("/health/startup", async ([FromServices] HealthCheckManager manager) =>
{
    var result = await manager.ProbeAsync("startup");
    return Results.Json(result, statusCode: result.GetHttpStatusCode());
});

app.Run();
```

### With Controllers

```csharp
using Microsoft.AspNetCore.Mvc;
using VelocityBench.HealthCheck;

[ApiController]
[Route("[controller]")]
public class HealthController : ControllerBase
{
    private readonly HealthCheckManager _healthManager;

    public HealthController(HealthCheckManager healthManager)
    {
        _healthManager = healthManager;
    }

    [HttpGet]
    public async Task<IActionResult> Health()
    {
        var result = await _healthManager.ProbeAsync("readiness");
        return StatusCode(result.GetHttpStatusCode(), result);
    }

    [HttpGet("live")]
    public async Task<IActionResult> Liveness()
    {
        var result = await _healthManager.ProbeAsync("liveness");
        return StatusCode(result.GetHttpStatusCode(), result);
    }

    [HttpGet("ready")]
    public async Task<IActionResult> Readiness()
    {
        var result = await _healthManager.ProbeAsync("readiness");
        return StatusCode(result.GetHttpStatusCode(), result);
    }

    [HttpGet("startup")]
    public async Task<IActionResult> Startup()
    {
        var result = await _healthManager.ProbeAsync("startup");
        return StatusCode(result.GetHttpStatusCode(), result);
    }
}
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
