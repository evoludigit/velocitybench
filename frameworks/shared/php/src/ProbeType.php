<?php

namespace VelocityBench\HealthCheck;

/**
 * Health check probe types (Kubernetes-compatible).
 */
enum ProbeType: string
{
    case LIVENESS = 'liveness';
    case READINESS = 'readiness';
    case STARTUP = 'startup';

    public static function fromString(string $value): self
    {
        return match (strtolower($value)) {
            'liveness' => self::LIVENESS,
            'readiness' => self::READINESS,
            'startup' => self::STARTUP,
            default => throw new \InvalidArgumentException("Unknown probe type: $value"),
        };
    }
}
