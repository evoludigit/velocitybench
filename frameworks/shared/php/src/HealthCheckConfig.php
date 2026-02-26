<?php

namespace VelocityBench\HealthCheck;

/**
 * Health check manager configuration.
 */
class HealthCheckConfig
{
    public function __construct(
        public string $serviceName = 'velocitybench',
        public string $version = '1.0.0',
        public string $environment = 'development',
        public int $startupDurationMs = 30000
    ) {
    }
}
