package com.velocitybench.healthcheck;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.Map;

/**
 * Complete health check response.
 */
public class HealthCheckResponse {
    private HealthStatus status;
    private String timestamp;

    @JsonProperty("uptime_ms")
    private long uptimeMs;

    private String version;
    private String service;
    private String environment;

    @JsonProperty("probe_type")
    private ProbeType probeType;

    private Map<String, HealthCheck> checks;

    public HealthCheckResponse(
            HealthStatus status,
            String timestamp,
            long uptimeMs,
            String version,
            String service,
            String environment,
            ProbeType probeType,
            Map<String, HealthCheck> checks) {
        this.status = status;
        this.timestamp = timestamp;
        this.uptimeMs = uptimeMs;
        this.version = version;
        this.service = service;
        this.environment = environment;
        this.probeType = probeType;
        this.checks = checks;
    }

    /**
     * Get HTTP status code based on health status and probe type.
     */
    public int getHttpStatusCode() {
        if (status == HealthStatus.DOWN) {
            return 503;
        } else if (status == HealthStatus.IN_PROGRESS && probeType == ProbeType.STARTUP) {
            return 202;
        }
        return 200;
    }

    // Getters
    public HealthStatus getStatus() {
        return status;
    }

    public String getTimestamp() {
        return timestamp;
    }

    public long getUptimeMs() {
        return uptimeMs;
    }

    public String getVersion() {
        return version;
    }

    public String getService() {
        return service;
    }

    public String getEnvironment() {
        return environment;
    }

    public ProbeType getProbeType() {
        return probeType;
    }

    public Map<String, HealthCheck> getChecks() {
        return checks;
    }
}
