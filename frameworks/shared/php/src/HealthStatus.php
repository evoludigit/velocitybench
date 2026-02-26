<?php

namespace VelocityBench\HealthCheck;

/**
 * Health check status values.
 */
enum HealthStatus: string
{
    case UP = 'up';
    case DEGRADED = 'degraded';
    case DOWN = 'down';
    case IN_PROGRESS = 'in_progress';
}
