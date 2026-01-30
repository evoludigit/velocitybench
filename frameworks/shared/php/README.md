# VelocityBench PHP Health Check Library

Standardized health check library for VelocityBench PHP frameworks.

## Features

- **Kubernetes-compatible probes**: Liveness, readiness, and startup
- **Database health checks**: PDO integration
- **Memory monitoring**: PHP memory statistics
- **Result caching**: 5-second TTL to reduce overhead
- **PHP 8.1+**: Modern PHP with enums and attributes

## Installation

```bash
composer require velocitybench/healthcheck
```

## Usage

### Basic Usage

```php
<?php

use VelocityBench\HealthCheck\{HealthCheckManager, HealthCheckConfig};

$config = new HealthCheckConfig(
    serviceName: 'my-service',
    version: '1.0.0',
    environment: 'production',
    startupDurationMs: 30000
);

$healthManager = new HealthCheckManager($config);

// Execute health check
$result = $healthManager->probe('readiness');
echo "Status: " . $result->status->value . "\n";
echo "HTTP Status Code: " . $result->getHttpStatusCode() . "\n";
```

### With Database

```php
<?php

use VelocityBench\HealthCheck\{HealthCheckManager, HealthCheckConfig};

// Create PDO connection
$pdo = new PDO('pgsql:host=localhost;dbname=mydb', 'user', 'password');

$config = new HealthCheckConfig(
    serviceName: 'my-service',
    version: '1.0.0'
);

$healthManager = (new HealthCheckManager($config))
    ->withDatabase($pdo);

$result = $healthManager->probe('readiness');
```

### With Laravel

```php
<?php

namespace App\Http\Controllers;

use Illuminate\Http\JsonResponse;
use Illuminate\Support\Facades\DB;
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

    public function health(): JsonResponse
    {
        $result = $this->healthManager->probe('readiness');
        return response()->json($result, $result->getHttpStatusCode());
    }

    public function liveness(): JsonResponse
    {
        $result = $this->healthManager->probe('liveness');
        return response()->json($result, $result->getHttpStatusCode());
    }

    public function readiness(): JsonResponse
    {
        $result = $this->healthManager->probe('readiness');
        return response()->json($result, $result->getHttpStatusCode());
    }

    public function startup(): JsonResponse
    {
        $result = $this->healthManager->probe('startup');
        return response()->json($result, $result->getHttpStatusCode());
    }
}
```

Add routes in `routes/web.php`:

```php
Route::get('/health', [HealthController::class, 'health']);
Route::get('/health/live', [HealthController::class, 'liveness']);
Route::get('/health/ready', [HealthController::class, 'readiness']);
Route::get('/health/startup', [HealthController::class, 'startup']);
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
