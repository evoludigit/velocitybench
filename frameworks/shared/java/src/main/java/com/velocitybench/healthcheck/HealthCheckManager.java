package com.velocitybench.healthcheck;

import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.SQLException;
import java.time.Instant;
import java.time.format.DateTimeFormatter;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Health check manager for Java frameworks.
 */
public class HealthCheckManager {
    private final HealthCheckConfig config;
    private final long startTime;
    private DataSource dataSource;
    private final Map<ProbeType, CachedResult> cache;
    private final long cacheTtlMs = 5000; // 5 seconds

    private static class CachedResult {
        final HealthCheckResponse result;
        final long timestamp;

        CachedResult(HealthCheckResponse result, long timestamp) {
            this.result = result;
            this.timestamp = timestamp;
        }
    }

    public HealthCheckManager(HealthCheckConfig config) {
        this.config = config;
        this.startTime = System.currentTimeMillis();
        this.cache = new ConcurrentHashMap<>();
    }

    /**
     * Set database data source for health checks.
     */
    public HealthCheckManager withDatabase(DataSource dataSource) {
        this.dataSource = dataSource;
        return this;
    }

    /**
     * Execute a health check probe.
     */
    public HealthCheckResponse probe(String probeType) {
        ProbeType probe = ProbeType.fromString(probeType);

        // Check cache
        HealthCheckResponse cached = getCachedResult(probe);
        if (cached != null) {
            return cached;
        }

        // Execute probe
        HealthCheckResponse result;
        switch (probe) {
            case LIVENESS:
                result = livenessProbe();
                break;
            case READINESS:
                result = readinessProbe();
                break;
            case STARTUP:
                result = startupProbe();
                break;
            default:
                throw new IllegalArgumentException("Unknown probe type: " + probeType);
        }

        // Cache result
        cacheResult(probe, result);

        return result;
    }

    /**
     * Get cached result if still valid.
     */
    private HealthCheckResponse getCachedResult(ProbeType probeType) {
        CachedResult cached = cache.get(probeType);
        if (cached != null) {
            long age = System.currentTimeMillis() - cached.timestamp;
            if (age < cacheTtlMs) {
                return cached.result;
            }
        }
        return null;
    }

    /**
     * Cache a health check result.
     */
    private void cacheResult(ProbeType probeType, HealthCheckResponse result) {
        cache.put(probeType, new CachedResult(result, System.currentTimeMillis()));
    }

    /**
     * Liveness probe: Is the process alive?
     */
    private HealthCheckResponse livenessProbe() {
        Map<String, HealthCheck> checks = new HashMap<>();

        // Memory check (lightweight, no DB required)
        checks.put("memory", checkMemory());

        HealthStatus overallStatus = computeOverallStatus(checks);

        return new HealthCheckResponse(
                overallStatus,
                getTimestamp(),
                getUptimeMs(),
                config.getVersion(),
                config.getServiceName(),
                config.getEnvironment(),
                ProbeType.LIVENESS,
                checks
        );
    }

    /**
     * Readiness probe: Can the service handle traffic?
     */
    private HealthCheckResponse readinessProbe() {
        Map<String, HealthCheck> checks = new HashMap<>();

        // Database check
        if (dataSource != null) {
            checks.put("database", checkDatabase());
        }

        // Memory check
        checks.put("memory", checkMemory());

        HealthStatus overallStatus = computeOverallStatus(checks);

        return new HealthCheckResponse(
                overallStatus,
                getTimestamp(),
                getUptimeMs(),
                config.getVersion(),
                config.getServiceName(),
                config.getEnvironment(),
                ProbeType.READINESS,
                checks
        );
    }

    /**
     * Startup probe: Has initialization completed?
     */
    private HealthCheckResponse startupProbe() {
        Map<String, HealthCheck> checks = new HashMap<>();

        // Database check
        if (dataSource != null) {
            checks.put("database", checkDatabase());
        }

        // Warmup check
        checks.put("warmup", checkWarmup());

        // Memory check
        checks.put("memory", checkMemory());

        HealthStatus overallStatus = computeOverallStatus(checks);

        return new HealthCheckResponse(
                overallStatus,
                getTimestamp(),
                getUptimeMs(),
                config.getVersion(),
                config.getServiceName(),
                config.getEnvironment(),
                ProbeType.STARTUP,
                checks
        );
    }

    /**
     * Check database connectivity.
     */
    private HealthCheck checkDatabase() {
        long start = System.currentTimeMillis();

        try (Connection conn = dataSource.getConnection()) {
            // Execute simple query
            conn.createStatement().execute("SELECT 1");

            double responseTime = (System.currentTimeMillis() - start);

            return new HealthCheck(HealthStatus.UP)
                    .withResponseTime(responseTime)
                    .withData("pool_size", getPoolSize())
                    .withData("pool_available", getPoolAvailable());

        } catch (SQLException e) {
            return new HealthCheck(HealthStatus.DOWN)
                    .withError("Database connection error: " + e.getMessage());
        }
    }

    /**
     * Check memory usage.
     */
    private HealthCheck checkMemory() {
        Runtime runtime = Runtime.getRuntime();
        long totalMemory = runtime.totalMemory();
        long freeMemory = runtime.freeMemory();
        long usedMemory = totalMemory - freeMemory;
        long maxMemory = runtime.maxMemory();

        double usedMb = usedMemory / (1024.0 * 1024.0);
        double totalMb = maxMemory / (1024.0 * 1024.0);
        double utilization = (usedMemory * 100.0) / maxMemory;

        HealthCheck check = new HealthCheck(HealthStatus.UP)
                .withData("used_mb", Math.round(usedMb * 100.0) / 100.0)
                .withData("total_mb", Math.round(totalMb * 100.0) / 100.0)
                .withData("utilization_percent", Math.round(utilization * 100.0) / 100.0);

        if (utilization > 90.0) {
            check.setStatus(HealthStatus.DEGRADED);
            check.withWarning(String.format("Critical memory usage (%.1f%%)", utilization));
        } else if (utilization > 80.0) {
            check.withWarning(String.format("High memory usage (%.1f%%)", utilization));
        }

        return check;
    }

    /**
     * Check if warmup period has completed.
     */
    private HealthCheck checkWarmup() {
        long uptimeMs = getUptimeMs();

        if (uptimeMs < config.getStartupDurationMs()) {
            double progress = (uptimeMs * 100.0) / config.getStartupDurationMs();
            return new HealthCheck(HealthStatus.IN_PROGRESS)
                    .withInfo(String.format("Warming up (%.0f%% complete)", progress))
                    .withData("progress_percent", Math.round(progress * 100.0) / 100.0)
                    .withData("uptime_ms", uptimeMs)
                    .withData("target_ms", config.getStartupDurationMs());
        } else {
            return new HealthCheck(HealthStatus.UP)
                    .withInfo("Warmup complete");
        }
    }

    /**
     * Compute overall health status from individual checks.
     */
    private HealthStatus computeOverallStatus(Map<String, HealthCheck> checks) {
        boolean hasDown = false;
        boolean hasInProgress = false;
        boolean hasDegraded = false;

        for (HealthCheck check : checks.values()) {
            switch (check.getStatus()) {
                case DOWN:
                    hasDown = true;
                    break;
                case IN_PROGRESS:
                    hasInProgress = true;
                    break;
                case DEGRADED:
                    hasDegraded = true;
                    break;
                case UP:
                    break;
            }
        }

        if (hasDown) {
            return HealthStatus.DOWN;
        } else if (hasInProgress) {
            return HealthStatus.IN_PROGRESS;
        } else if (hasDegraded) {
            return HealthStatus.DEGRADED;
        } else {
            return HealthStatus.UP;
        }
    }

    /**
     * Get service uptime in milliseconds.
     */
    private long getUptimeMs() {
        return System.currentTimeMillis() - startTime;
    }

    /**
     * Get current timestamp in ISO 8601 format.
     */
    private String getTimestamp() {
        return Instant.now().toString();
    }

    /**
     * Get database pool size (framework-specific).
     */
    private int getPoolSize() {
        // Override in framework-specific subclass if needed
        return 0;
    }

    /**
     * Get available connections (framework-specific).
     */
    private int getPoolAvailable() {
        // Override in framework-specific subclass if needed
        return 0;
    }
}
