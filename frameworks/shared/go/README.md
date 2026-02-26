# VelocityBench Go Health Check Library

Standardized health check library for VelocityBench Go frameworks.

## Features

- **Kubernetes-compatible probes**: Liveness, readiness, and startup
- **Database health checks**: Connection testing and pool statistics
- **Memory monitoring**: Runtime memory statistics
- **Zero external dependencies**: Uses only Go standard library
- **Framework agnostic**: Works with any Go HTTP framework

## Installation

```bash
go get github.com/velocitybench/frameworks/shared/go/healthcheck
```

## Usage

### Basic Usage

```go
package main

import (
    "database/sql"
    "net/http"

    healthcheck "github.com/velocitybench/frameworks/shared/go/healthcheck"
)

func main() {
    // Initialize database
    db, _ := sql.Open("postgres", "...")

    // Create health check manager
    healthManager := healthcheck.New(healthcheck.Config{
        ServiceName: "my-service",
        Version:     "1.0.0",
        Environment: "production",
        Database:    db,
    })

    // Register health check routes
    healthcheck.RegisterRoutes(http.DefaultServeMux, healthManager)

    // Or register individual endpoints
    http.HandleFunc("/health", healthcheck.HTTPHandler(healthManager, "readiness"))
    http.HandleFunc("/health/live", healthcheck.HTTPHandler(healthManager, "liveness"))
    http.HandleFunc("/health/ready", healthcheck.HTTPHandler(healthManager, "readiness"))
    http.HandleFunc("/health/startup", healthcheck.HTTPHandler(healthManager, "startup"))

    http.ListenAndServe(":8080", nil)
}
```

### With Gin Framework

```go
import (
    "github.com/gin-gonic/gin"
    healthcheck "github.com/velocitybench/frameworks/shared/go/healthcheck"
)

router := gin.Default()
healthManager := healthcheck.New(healthcheck.Config{ ... })

router.GET("/health", func(c *gin.Context) {
    result, _ := healthManager.Probe("readiness")
    c.JSON(result.GetHTTPStatusCode(), result)
})
```

### With Echo Framework

```go
import (
    "github.com/labstack/echo/v4"
    healthcheck "github.com/velocitybench/frameworks/shared/go/healthcheck"
)

e := echo.New()
healthManager := healthcheck.New(healthcheck.Config{ ... })

e.GET("/health", func(c echo.Context) error {
    result, _ := healthManager.Probe("readiness")
    return c.JSON(result.GetHTTPStatusCode(), result)
})
```

## Health Check Endpoints

- `GET /health` - Combined health check (defaults to readiness)
- `GET /health/live` - Liveness probe (process alive?)
- `GET /health/ready` - Readiness probe (can serve traffic?)
- `GET /health/startup` - Startup probe (initialization complete?)

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
      "pool_available": 8,
      "pool_max_size": 20
    },
    "memory": {
      "status": "up",
      "used_mb": 45.3,
      "total_mb": 512.0,
      "utilization_percent": 8.8
    }
  }
}
```

## Configuration

```go
type Config struct {
    ServiceName       string   // Required: Service name
    Version           string   // Required: Service version
    Environment       string   // Optional: Environment (default: "development")
    Database          *sql.DB  // Optional: Database connection for health checks
    StartupDurationMs int64    // Optional: Warmup period in ms (default: 30000)
}
```

## HTTP Status Codes

- `200 OK` - Service is healthy (`up` or `degraded`)
- `202 Accepted` - Service is warming up (`in_progress`, startup probe only)
- `503 Service Unavailable` - Service is unhealthy (`down`)

## License

MIT
