# Health Check Specification

VelocityBench uses a unified health check specification across all 39+ frameworks in 8 languages. This specification defines standardized endpoints, response schemas, and status codes for service health monitoring.

## Overview

Health checks enable:
- **Kubernetes liveness probes** - Detect and restart crashed services
- **Kubernetes readiness probes** - Route traffic only to ready services
- **Kubernetes startup probes** - Handle slow-starting services
- **Load balancer health checks** - Remove unhealthy instances from rotation
- **Monitoring and alerting** - Track service availability

## Endpoints

### GET /health

Combined health check endpoint (defaults to readiness check).

**Purpose**: Single endpoint for simple health monitoring

**Response**: Readiness probe result (can serve traffic?)

**Example**:
```bash
curl http://localhost:8000/health
```

---

### GET /health/live

Liveness probe - Is the process alive?

**Purpose**: Kubernetes liveness probe to detect crashed/deadlocked processes

**Criteria**:
- ✅ Process is running
- ✅ Event loop is responsive
- ❌ Does NOT check database connectivity
- ❌ Does NOT check external dependencies

**When to use**: Kubernetes `livenessProbe` to restart crashed pods

**Example**:
```bash
curl http://localhost:8000/health/live
```

---

### GET /health/ready

Readiness probe - Can the service handle traffic?

**Purpose**: Kubernetes readiness probe to control traffic routing

**Criteria**:
- ✅ Process is running
- ✅ Database connection is healthy
- ✅ Connection pool has available connections
- ✅ Memory usage is within limits
- ❌ Does NOT wait for warmup (use startup probe)

**When to use**: Kubernetes `readinessProbe` to route traffic

**Example**:
```bash
curl http://localhost:8000/health/ready
```

---

### GET /health/startup

Startup probe - Has initialization completed?

**Purpose**: Kubernetes startup probe for slow-starting services

**Criteria**:
- ✅ Process is running
- ✅ Database connection established
- ✅ Migration checks complete (if applicable)
- ✅ Warmup period finished (cache populated, connections pooled)

**When to use**: Kubernetes `startupProbe` to delay liveness checks

**Example**:
```bash
curl http://localhost:8000/health/startup
```

---

## Response Schema

### Healthy Response (200 OK)

```json
{
  "status": "up",
  "timestamp": "2025-01-30T14:30:00.123Z",
  "uptime_ms": 3456789,
  "version": "1.0.0",
  "service": "fastapi-rest",
  "environment": "production",
  "probe_type": "readiness",
  "checks": {
    "database": {
      "status": "up",
      "response_time_ms": 5.2,
      "pool_size": 50,
      "available_connections": 45
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

### Degraded Response (200 OK with warnings)

```json
{
  "status": "degraded",
  "timestamp": "2025-01-30T14:30:00.123Z",
  "uptime_ms": 3456789,
  "version": "1.0.0",
  "service": "fastapi-rest",
  "environment": "production",
  "probe_type": "readiness",
  "checks": {
    "database": {
      "status": "up",
      "response_time_ms": 5.2,
      "pool_size": 50,
      "available_connections": 5,
      "warning": "Low available connections (10% of pool)"
    },
    "memory": {
      "status": "degraded",
      "used_mb": 480.0,
      "total_mb": 512.0,
      "utilization_percent": 93.8,
      "warning": "High memory usage (>90%)"
    }
  }
}
```

### Unhealthy Response (503 Service Unavailable)

```json
{
  "status": "down",
  "timestamp": "2025-01-30T14:30:00.123Z",
  "uptime_ms": 3456789,
  "version": "1.0.0",
  "service": "fastapi-rest",
  "environment": "production",
  "probe_type": "readiness",
  "checks": {
    "database": {
      "status": "down",
      "error": "Connection refused: unable to connect to PostgreSQL",
      "last_success": "2025-01-30T14:25:00.000Z"
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

### Warming Up Response (202 Accepted)

Used during startup period.

```json
{
  "status": "up",
  "timestamp": "2025-01-30T14:30:00.123Z",
  "uptime_ms": 5000,
  "version": "1.0.0",
  "service": "fastapi-rest",
  "environment": "production",
  "probe_type": "startup",
  "checks": {
    "database": {
      "status": "up",
      "response_time_ms": 5.2,
      "pool_size": 50,
      "available_connections": 10,
      "info": "Connection pool still warming up (10/50)"
    },
    "warmup": {
      "status": "in_progress",
      "progress_percent": 20,
      "info": "Warming up caches and connection pool"
    }
  }
}
```

## Response Fields

### Top-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | string | ✅ | Overall health: `up`, `degraded`, `down` |
| `timestamp` | string (ISO 8601) | ✅ | UTC timestamp of health check |
| `uptime_ms` | integer | ✅ | Service uptime in milliseconds |
| `version` | string | ✅ | Service version (semantic versioning) |
| `service` | string | ✅ | Service name (e.g., "fastapi-rest") |
| `environment` | string | ✅ | Environment (development, staging, production) |
| `probe_type` | string | ✅ | Type of probe: `liveness`, `readiness`, `startup` |
| `checks` | object | ✅ | Individual health check results |

### Check Fields

Each check in the `checks` object:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | string | ✅ | Check status: `up`, `degraded`, `down`, `in_progress` |
| `response_time_ms` | float | ❌ | Response time for the check (ms) |
| `error` | string | ❌ | Error message (if `status: "down"`) |
| `warning` | string | ❌ | Warning message (if `status: "degraded"`) |
| `info` | string | ❌ | Informational message |
| Additional fields | varies | ❌ | Check-specific fields (see below) |

### Database Check Fields

| Field | Type | Description |
|-------|------|-------------|
| `pool_size` | integer | Total connection pool size |
| `available_connections` | integer | Available connections in pool |
| `active_connections` | integer | Active connections |
| `idle_connections` | integer | Idle connections |

### Memory Check Fields

| Field | Type | Description |
|-------|------|-------------|
| `used_mb` | float | Memory used (MB) |
| `total_mb` | float | Total memory available (MB) |
| `utilization_percent` | float | Memory utilization percentage |

## HTTP Status Codes

| Code | Status | Meaning |
|------|--------|---------|
| `200 OK` | `up` | Service is healthy and ready |
| `200 OK` | `degraded` | Service is functional but has warnings |
| `202 Accepted` | `up` | Service is starting up (startup probe only) |
| `503 Service Unavailable` | `down` | Service is unhealthy |

**Important**: `degraded` status still returns `200 OK` because the service can still handle traffic, just with reduced capacity or performance.

## Probe Types

### Liveness Probe

**Question**: Is the process alive?

**Checks**:
- Process is running
- Event loop is responsive

**Does NOT check**:
- Database connectivity
- External dependencies
- Memory usage

**Kubernetes config**:
```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
```

---

### Readiness Probe

**Question**: Can the service handle traffic?

**Checks**:
- Process is running
- Database connection is healthy
- Connection pool has capacity
- Memory usage is acceptable

**Kubernetes config**:
```yaml
readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 2
```

---

### Startup Probe

**Question**: Has initialization completed?

**Checks**:
- Process is running
- Database connection established
- Connection pool warmed up
- Caches populated (if applicable)

**Kubernetes config**:
```yaml
startupProbe:
  httpGet:
    path: /health/startup
    port: 8000
  initialDelaySeconds: 0
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 30  # Allow 5 minutes for startup
```

## Health Check Decision Matrix

| Probe Type | Process OK? | DB Connected? | Pool Ready? | Cache Warmed? | Returns |
|------------|-------------|---------------|-------------|---------------|---------|
| Liveness   | ✅ | - | - | - | 200 OK |
| Liveness   | ❌ | - | - | - | 503 Unavailable |
| Readiness  | ✅ | ✅ | ✅ | - | 200 OK |
| Readiness  | ✅ | ❌ | - | - | 503 Unavailable |
| Readiness  | ✅ | ✅ | ⚠️ Low | - | 200 OK (degraded) |
| Startup    | ✅ | ✅ | ✅ | ✅ | 200 OK |
| Startup    | ✅ | ✅ | ⚠️ Warming | ⚠️ Warming | 202 Accepted |

## Implementation Requirements

### 1. Response Time

Health check endpoints MUST respond within:
- **Liveness**: < 1 second
- **Readiness**: < 3 seconds
- **Startup**: < 5 seconds

Timeouts beyond these values should return `503 Service Unavailable`.

### 2. Database Check

Database checks should:
- Execute a simple `SELECT 1` query (or equivalent)
- Measure response time
- Check connection pool statistics
- NOT execute complex queries or scans

**Example query**:
```sql
SELECT 1;  -- PostgreSQL
```

### 3. Memory Check

Memory checks should:
- Use language-specific memory introspection (e.g., `process.memoryUsage()` in Node.js)
- Report resident set size (RSS)
- Calculate utilization percentage
- Warn if > 90% utilized

### 4. Caching

Health check results MAY be cached for up to 5 seconds to avoid excessive database queries.

### 5. Error Handling

Health check endpoints MUST NOT throw unhandled exceptions. All errors should be caught and reported in the response.

## Language-Specific Implementations

### Python (FastAPI, Flask, etc.)

```python
from frameworks.common.health_check import HealthCheckManager

# Initialize
health = HealthCheckManager(
    service_name="fastapi-rest",
    version="1.0.0",
    database=db_pool,
    environment="production"
)

# Add endpoint
@app.get("/health/ready")
async def health_ready():
    return await health.probe("readiness")
```

### TypeScript (Express, Fastify, etc.)

```typescript
import { HealthCheckManager } from '@shared/health-check';

const health = new HealthCheckManager({
  serviceName: 'express-rest',
  version: '1.0.0',
  database: dbPool,
  environment: 'production'
});

app.get('/health/ready', async (req, res) => {
  const result = await health.probe('readiness');
  res.status(result.status === 'down' ? 503 : 200).json(result);
});
```

### Go

```go
import "github.com/velocitybench/shared/healthcheck"

health := healthcheck.New(healthcheck.Config{
    ServiceName: "gin-rest",
    Version:     "1.0.0",
    Database:    dbPool,
    Environment: "production",
})

router.GET("/health/ready", func(c *gin.Context) {
    result := health.Probe("readiness")
    statusCode := 200
    if result.Status == "down" {
        statusCode = 503
    }
    c.JSON(statusCode, result)
})
```

## Testing Health Checks

### Manual Testing

```bash
# Test liveness
curl http://localhost:8000/health/live

# Test readiness
curl http://localhost:8000/health/ready

# Test startup
curl http://localhost:8000/health/startup

# Test with verbose output
curl -v http://localhost:8000/health/ready

# Test with timing
time curl http://localhost:8000/health/ready
```

### Automated Testing

Health checks should be validated in the QA test suite:

```python
# tests/health/test_health_python.py
async def test_health_ready_returns_200_when_healthy(framework_url):
    response = await client.get(f"{framework_url}/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["up", "degraded"]
    assert data["probe_type"] == "readiness"
    assert "checks" in data
    assert "database" in data["checks"]

async def test_health_live_responds_quickly(framework_url):
    start = time.time()
    response = await client.get(f"{framework_url}/health/live")
    duration = time.time() - start
    assert duration < 1.0  # Must respond in < 1 second
```

## Monitoring Integration

### Prometheus Metrics

Health check status can be exported as Prometheus metrics:

```
# HELP service_health Service health status (1=up, 0.5=degraded, 0=down)
# TYPE service_health gauge
service_health{service="fastapi-rest",probe="readiness"} 1

# HELP service_health_check_duration_seconds Duration of health check
# TYPE service_health_check_duration_seconds histogram
service_health_check_duration_seconds{service="fastapi-rest",check="database"} 0.005
```

### Alerting

Example Prometheus alert:

```yaml
- alert: ServiceUnhealthy
  expr: service_health{probe="readiness"} == 0
  for: 2m
  labels:
    severity: critical
  annotations:
    summary: "Service {{ $labels.service }} is unhealthy"
```

## References

- [Kubernetes Liveness, Readiness and Startup Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [Health Check Response Format for HTTP APIs (RFC)](https://tools.ietf.org/html/draft-inadarei-api-health-check-06)
- [ADR-009: Six-Dimensional QA Testing](adr/009-six-dimensional-qa-testing.md)
