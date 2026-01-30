<?php

namespace VelocityBench\HealthCheck;

/**
 * Complete health check response.
 */
class HealthCheckResponse implements \JsonSerializable
{
    /**
     * @param array<string, HealthCheck> $checks
     */
    public function __construct(
        public HealthStatus $status,
        public string $timestamp,
        public int $uptimeMs,
        public string $version,
        public string $service,
        public string $environment,
        public ProbeType $probeType,
        public array $checks
    ) {
    }

    /**
     * Get HTTP status code based on health status and probe type.
     */
    public function getHttpStatusCode(): int
    {
        return match ($this->status) {
            HealthStatus::DOWN => 503,
            HealthStatus::IN_PROGRESS => $this->probeType === ProbeType::STARTUP ? 202 : 200,
            default => 200,
        };
    }

    public function jsonSerialize(): array
    {
        return [
            'status' => $this->status->value,
            'timestamp' => $this->timestamp,
            'uptime_ms' => $this->uptimeMs,
            'version' => $this->version,
            'service' => $this->service,
            'environment' => $this->environment,
            'probe_type' => $this->probeType->value,
            'checks' => $this->checks,
        ];
    }
}
