package com.velocitybench.healthcheck.spring;

import com.velocitybench.healthcheck.HealthCheckManager;
import com.velocitybench.healthcheck.HealthCheckResponse;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * Spring Boot health check controller.
 *
 * Usage:
 * <pre>
 * {@code
 * @Configuration
 * public class HealthCheckConfiguration {
 *     @Bean
 *     public HealthCheckManager healthCheckManager(DataSource dataSource) {
 *         HealthCheckConfig config = new HealthCheckConfig();
 *         config.setServiceName("my-service");
 *         config.setVersion("1.0.0");
 *         return new HealthCheckManager(config).withDatabase(dataSource);
 *     }
 * }
 * }
 * </pre>
 */
@RestController
@RequestMapping("/health")
public class SpringHealthCheckController {
    private final HealthCheckManager healthCheckManager;

    public SpringHealthCheckController(HealthCheckManager healthCheckManager) {
        this.healthCheckManager = healthCheckManager;
    }

    /**
     * Combined health check endpoint (defaults to readiness).
     */
    @GetMapping
    public ResponseEntity<HealthCheckResponse> health() {
        HealthCheckResponse response = healthCheckManager.probe("readiness");
        return ResponseEntity
                .status(response.getHttpStatusCode())
                .body(response);
    }

    /**
     * Liveness probe endpoint.
     */
    @GetMapping("/live")
    public ResponseEntity<HealthCheckResponse> liveness() {
        HealthCheckResponse response = healthCheckManager.probe("liveness");
        return ResponseEntity
                .status(response.getHttpStatusCode())
                .body(response);
    }

    /**
     * Readiness probe endpoint.
     */
    @GetMapping("/ready")
    public ResponseEntity<HealthCheckResponse> readiness() {
        HealthCheckResponse response = healthCheckManager.probe("readiness");
        return ResponseEntity
                .status(response.getHttpStatusCode())
                .body(response);
    }

    /**
     * Startup probe endpoint.
     */
    @GetMapping("/startup")
    public ResponseEntity<HealthCheckResponse> startup() {
        HealthCheckResponse response = healthCheckManager.probe("startup");
        return ResponseEntity
                .status(response.getHttpStatusCode())
                .body(response);
    }
}
