/**
 * Type definitions for VelocityBench health checks.
 *
 * Provides TypeScript interfaces for standardized health check responses
 * compatible with Kubernetes probes (liveness, readiness, startup).
 */

/**
 * Health check status values.
 */
export enum HealthStatus {
  UP = 'up',
  DEGRADED = 'degraded',
  DOWN = 'down',
  IN_PROGRESS = 'in_progress',
}

/**
 * Health check probe types (Kubernetes-compatible).
 */
export enum ProbeType {
  LIVENESS = 'liveness',
  READINESS = 'readiness',
  STARTUP = 'startup',
}

/**
 * Individual health check result.
 */
export interface HealthCheck {
  status: HealthStatus;
  response_time_ms?: number;
  error?: string;
  warning?: string;
  info?: string;
  [key: string]: any; // Additional data specific to the check
}

/**
 * Database health check result.
 */
export interface DatabaseCheck extends HealthCheck {
  pool_size?: number;
  pool_available?: number;
  pool_max_size?: number;
}

/**
 * Memory health check result.
 */
export interface MemoryCheck extends HealthCheck {
  used_mb?: number;
  total_mb?: number;
  utilization_percent?: number;
}

/**
 * Complete health check response.
 */
export interface HealthCheckResponse {
  status: HealthStatus;
  timestamp: string; // ISO 8601 format
  uptime_ms: number;
  version: string;
  service: string;
  environment: string;
  probe_type: ProbeType;
  checks: {
    database?: DatabaseCheck;
    memory?: MemoryCheck;
    warmup?: HealthCheck;
    [key: string]: HealthCheck | undefined;
  };
}

/**
 * Options for health check manager initialization.
 */
export interface HealthCheckOptions {
  serviceName: string;
  version: string;
  environment?: string;
  database?: any; // Database pool (type varies by framework)
  startupDurationMs?: number; // Warmup period in milliseconds
}

/**
 * Get HTTP status code based on health status and probe type.
 */
export function getHttpStatusCode(
  status: HealthStatus,
  probeType: ProbeType
): number {
  if (status === HealthStatus.DOWN) {
    return 503;
  } else if (status === HealthStatus.IN_PROGRESS && probeType === ProbeType.STARTUP) {
    return 202;
  } else {
    return 200;
  }
}

/**
 * Compute overall health status from individual checks.
 *
 * Logic:
 * - If any check is DOWN, overall is DOWN
 * - If any check is IN_PROGRESS, overall is IN_PROGRESS
 * - If any check is DEGRADED, overall is DEGRADED
 * - Otherwise, overall is UP
 */
export function computeOverallStatus(checks: { [key: string]: HealthCheck }): HealthStatus {
  const statuses = Object.values(checks).map(check => check.status);

  if (statuses.includes(HealthStatus.DOWN)) {
    return HealthStatus.DOWN;
  } else if (statuses.includes(HealthStatus.IN_PROGRESS)) {
    return HealthStatus.IN_PROGRESS;
  } else if (statuses.includes(HealthStatus.DEGRADED)) {
    return HealthStatus.DEGRADED;
  } else {
    return HealthStatus.UP;
  }
}
