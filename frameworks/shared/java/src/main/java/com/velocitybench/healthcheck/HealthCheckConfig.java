package com.velocitybench.healthcheck;

/**
 * Health check manager configuration.
 */
public class HealthCheckConfig {
    private String serviceName;
    private String version;
    private String environment;
    private long startupDurationMs;

    public HealthCheckConfig() {
        this.serviceName = "velocitybench";
        this.version = "1.0.0";
        this.environment = "development";
        this.startupDurationMs = 30000; // 30 seconds
    }

    public HealthCheckConfig(String serviceName, String version, String environment, long startupDurationMs) {
        this.serviceName = serviceName;
        this.version = version;
        this.environment = environment;
        this.startupDurationMs = startupDurationMs;
    }

    // Getters and setters
    public String getServiceName() {
        return serviceName;
    }

    public void setServiceName(String serviceName) {
        this.serviceName = serviceName;
    }

    public String getVersion() {
        return version;
    }

    public void setVersion(String version) {
        this.version = version;
    }

    public String getEnvironment() {
        return environment;
    }

    public void setEnvironment(String environment) {
        this.environment = environment;
    }

    public long getStartupDurationMs() {
        return startupDurationMs;
    }

    public void setStartupDurationMs(long startupDurationMs) {
        this.startupDurationMs = startupDurationMs;
    }
}
