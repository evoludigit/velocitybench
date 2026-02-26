# VelocityBench Java Health Check Library

Standardized health check library for VelocityBench Java frameworks.

## Features

- **Kubernetes-compatible probes**: Liveness, readiness, and startup
- **Database health checks**: JDBC DataSource integration
- **Memory monitoring**: JVM memory statistics
- **Framework integrations**: Spring Boot support
- **Result caching**: 5-second TTL to reduce overhead

## Installation

Add to your `pom.xml`:

```xml
<dependency>
    <groupId>com.velocitybench</groupId>
    <artifactId>velocitybench-healthcheck</artifactId>
    <version>1.0.0</version>
</dependency>
```

## Usage

### Basic Usage

```java
import com.velocitybench.healthcheck.*;

public class Application {
    public static void main(String[] args) {
        HealthCheckConfig config = new HealthCheckConfig();
        config.setServiceName("my-service");
        config.setVersion("1.0.0");
        config.setEnvironment("production");
        config.setStartupDurationMs(30000);

        HealthCheckManager healthManager = new HealthCheckManager(config);

        // Execute health check
        HealthCheckResponse result = healthManager.probe("readiness");
        System.out.println("Status: " + result.getStatus());
        System.out.println("HTTP Status Code: " + result.getHttpStatusCode());
    }
}
```

### With Database

```java
import com.velocitybench.healthcheck.*;
import javax.sql.DataSource;

public class Application {
    public static void main(String[] args) {
        // Create database data source
        DataSource dataSource = createDataSource();

        HealthCheckConfig config = new HealthCheckConfig();
        config.setServiceName("my-service");
        config.setVersion("1.0.0");

        HealthCheckManager healthManager = new HealthCheckManager(config)
                .withDatabase(dataSource);

        HealthCheckResponse result = healthManager.probe("readiness");
    }
}
```

### With Spring Boot

```java
import com.velocitybench.healthcheck.*;
import com.velocitybench.healthcheck.spring.SpringHealthCheckController;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import javax.sql.DataSource;

@SpringBootApplication
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}

@Configuration
class HealthCheckConfiguration {
    @Bean
    public HealthCheckManager healthCheckManager(DataSource dataSource) {
        HealthCheckConfig config = new HealthCheckConfig();
        config.setServiceName("spring-boot-service");
        config.setVersion("1.0.0");
        config.setEnvironment("production");

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

This automatically registers the following endpoints:
- `GET /health` - Combined health (default: readiness)
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe
- `GET /health/startup` - Startup probe

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
      "used_mb": 128.5,
      "total_mb": 512.0,
      "utilization_percent": 25.1
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
