<?php

namespace VelocityBench\HealthCheck;

/**
 * Health check manager for PHP frameworks.
 */
class HealthCheckManager
{
    private float $startTime;
    private ?\PDO $database = null;
    private array $cache = [];
    private int $cacheTtlMs = 5000; // 5 seconds

    public function __construct(
        private HealthCheckConfig $config
    ) {
        $this->startTime = microtime(true);
    }

    /**
     * Set database connection for health checks.
     */
    public function withDatabase(\PDO $pdo): self
    {
        $this->database = $pdo;
        return $this;
    }

    /**
     * Execute a health check probe.
     */
    public function probe(string $probeType): HealthCheckResponse
    {
        $probe = ProbeType::fromString($probeType);

        // Check cache
        $cached = $this->getCachedResult($probe);
        if ($cached !== null) {
            return $cached;
        }

        // Execute probe
        $result = match ($probe) {
            ProbeType::LIVENESS => $this->livenessProbe(),
            ProbeType::READINESS => $this->readinessProbe(),
            ProbeType::STARTUP => $this->startupProbe(),
        };

        // Cache result
        $this->cacheResult($probe, $result);

        return $result;
    }

    /**
     * Get cached result if still valid.
     */
    private function getCachedResult(ProbeType $probeType): ?HealthCheckResponse
    {
        $key = $probeType->value;

        if (!isset($this->cache[$key])) {
            return null;
        }

        $cached = $this->cache[$key];
        $age = (microtime(true) * 1000) - $cached['timestamp'];

        if ($age < $this->cacheTtlMs) {
            return $cached['result'];
        }

        return null;
    }

    /**
     * Cache a health check result.
     */
    private function cacheResult(ProbeType $probeType, HealthCheckResponse $result): void
    {
        $this->cache[$probeType->value] = [
            'result' => $result,
            'timestamp' => microtime(true) * 1000,
        ];
    }

    /**
     * Liveness probe: Is the process alive?
     */
    private function livenessProbe(): HealthCheckResponse
    {
        $checks = [
            'memory' => $this->checkMemory(),
        ];

        $overallStatus = $this->computeOverallStatus($checks);

        return new HealthCheckResponse(
            status: $overallStatus,
            timestamp: $this->getTimestamp(),
            uptimeMs: $this->getUptimeMs(),
            version: $this->config->version,
            service: $this->config->serviceName,
            environment: $this->config->environment,
            probeType: ProbeType::LIVENESS,
            checks: $checks
        );
    }

    /**
     * Readiness probe: Can the service handle traffic?
     */
    private function readinessProbe(): HealthCheckResponse
    {
        $checks = [];

        // Database check
        if ($this->database !== null) {
            $checks['database'] = $this->checkDatabase();
        }

        // Memory check
        $checks['memory'] = $this->checkMemory();

        $overallStatus = $this->computeOverallStatus($checks);

        return new HealthCheckResponse(
            status: $overallStatus,
            timestamp: $this->getTimestamp(),
            uptimeMs: $this->getUptimeMs(),
            version: $this->config->version,
            service: $this->config->serviceName,
            environment: $this->config->environment,
            probeType: ProbeType::READINESS,
            checks: $checks
        );
    }

    /**
     * Startup probe: Has initialization completed?
     */
    private function startupProbe(): HealthCheckResponse
    {
        $checks = [];

        // Database check
        if ($this->database !== null) {
            $checks['database'] = $this->checkDatabase();
        }

        // Warmup check
        $checks['warmup'] = $this->checkWarmup();

        // Memory check
        $checks['memory'] = $this->checkMemory();

        $overallStatus = $this->computeOverallStatus($checks);

        return new HealthCheckResponse(
            status: $overallStatus,
            timestamp: $this->getTimestamp(),
            uptimeMs: $this->getUptimeMs(),
            version: $this->config->version,
            service: $this->config->serviceName,
            environment: $this->config->environment,
            probeType: ProbeType::STARTUP,
            checks: $checks
        );
    }

    /**
     * Check database connectivity.
     */
    private function checkDatabase(): HealthCheck
    {
        $start = microtime(true);

        try {
            // Execute simple query with timeout
            $this->database->setAttribute(\PDO::ATTR_TIMEOUT, 3);
            $stmt = $this->database->query('SELECT 1');
            $stmt->fetch();

            $responseTime = (microtime(true) - $start) * 1000;

            return (new HealthCheck(HealthStatus::UP))
                ->withResponseTime($responseTime)
                ->withData('pool_size', 0)
                ->withData('pool_available', 0);

        } catch (\PDOException $e) {
            return (new HealthCheck(HealthStatus::DOWN))
                ->withError('Database connection error: ' . $e->getMessage());
        }
    }

    /**
     * Check memory usage.
     */
    private function checkMemory(): HealthCheck
    {
        $usedMemory = memory_get_usage(true);
        $peakMemory = memory_get_peak_usage(true);
        $memoryLimit = $this->getMemoryLimit();

        $usedMb = $usedMemory / (1024 * 1024);
        $totalMb = $memoryLimit / (1024 * 1024);
        $utilization = ($usedMemory / $memoryLimit) * 100;

        $check = (new HealthCheck(HealthStatus::UP))
            ->withData('used_mb', round($usedMb, 2))
            ->withData('total_mb', round($totalMb, 2))
            ->withData('utilization_percent', round($utilization, 2));

        if ($utilization > 90.0) {
            $check->status = HealthStatus::DEGRADED;
            $check->withWarning(sprintf('Critical memory usage (%.1f%%)', $utilization));
        } elseif ($utilization > 80.0) {
            $check->withWarning(sprintf('High memory usage (%.1f%%)', $utilization));
        }

        return $check;
    }

    /**
     * Check if warmup period has completed.
     */
    private function checkWarmup(): HealthCheck
    {
        $uptimeMs = $this->getUptimeMs();

        if ($uptimeMs < $this->config->startupDurationMs) {
            $progress = ($uptimeMs / $this->config->startupDurationMs) * 100;
            return (new HealthCheck(HealthStatus::IN_PROGRESS))
                ->withInfo(sprintf('Warming up (%.0f%% complete)', $progress))
                ->withData('progress_percent', round($progress, 2))
                ->withData('uptime_ms', $uptimeMs)
                ->withData('target_ms', $this->config->startupDurationMs);
        }

        return (new HealthCheck(HealthStatus::UP))
            ->withInfo('Warmup complete');
    }

    /**
     * Compute overall health status from individual checks.
     */
    private function computeOverallStatus(array $checks): HealthStatus
    {
        $hasDown = false;
        $hasInProgress = false;
        $hasDegraded = false;

        foreach ($checks as $check) {
            match ($check->status) {
                HealthStatus::DOWN => $hasDown = true,
                HealthStatus::IN_PROGRESS => $hasInProgress = true,
                HealthStatus::DEGRADED => $hasDegraded = true,
                default => null,
            };
        }

        if ($hasDown) {
            return HealthStatus::DOWN;
        } elseif ($hasInProgress) {
            return HealthStatus::IN_PROGRESS;
        } elseif ($hasDegraded) {
            return HealthStatus::DEGRADED;
        }

        return HealthStatus::UP;
    }

    /**
     * Get service uptime in milliseconds.
     */
    private function getUptimeMs(): int
    {
        return (int) ((microtime(true) - $this->startTime) * 1000);
    }

    /**
     * Get current timestamp in ISO 8601 format.
     */
    private function getTimestamp(): string
    {
        return (new \DateTime('now', new \DateTimeZone('UTC')))
            ->format('Y-m-d\TH:i:s.v\Z');
    }

    /**
     * Get PHP memory limit in bytes.
     */
    private function getMemoryLimit(): int
    {
        $memoryLimit = ini_get('memory_limit');

        if ($memoryLimit === '-1') {
            // Unlimited memory, return a large value
            return PHP_INT_MAX;
        }

        // Parse memory limit (e.g., "128M", "1G")
        $value = (int) $memoryLimit;
        $unit = strtoupper(substr($memoryLimit, -1));

        return match ($unit) {
            'G' => $value * 1024 * 1024 * 1024,
            'M' => $value * 1024 * 1024,
            'K' => $value * 1024,
            default => $value,
        };
    }
}
