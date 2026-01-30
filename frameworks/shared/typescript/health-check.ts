/**
 * Health check manager for VelocityBench TypeScript/Node.js frameworks.
 *
 * Provides unified health check functionality with support for:
 * - Kubernetes liveness, readiness, and startup probes
 * - Database connectivity checks (PostgreSQL via node-postgres)
 * - Memory monitoring (process.memoryUsage())
 * - Connection pool statistics
 */

import { Pool } from 'pg';
import {
  HealthStatus,
  ProbeType,
  HealthCheck,
  HealthCheckResponse,
  HealthCheckOptions,
  DatabaseCheck,
  MemoryCheck,
  computeOverallStatus,
} from './types';

/**
 * Health check manager for Node.js frameworks.
 */
export class HealthCheckManager {
  private serviceName: string;
  private version: string;
  private environment: string;
  private database?: Pool;
  private startupDurationMs: number;
  private startTime: number;
  private cache: Map<string, { result: HealthCheckResponse; timestamp: number }>;
  private cacheTtl: number = 5000; // 5 seconds

  constructor(options: HealthCheckOptions) {
    this.serviceName = options.serviceName;
    this.version = options.version;
    this.environment = options.environment || 'development';
    this.database = options.database;
    this.startupDurationMs = options.startupDurationMs || 30000; // 30 seconds default
    this.startTime = Date.now();
    this.cache = new Map();
  }

  /**
   * Execute a health check probe.
   */
  async probe(probeType: string): Promise<HealthCheckResponse> {
    const probe = probeType.toLowerCase() as ProbeType;

    // Check cache
    const cached = this.getCachedResult(probe);
    if (cached) {
      return cached;
    }

    // Execute probe
    let result: HealthCheckResponse;
    switch (probe) {
      case ProbeType.LIVENESS:
        result = await this.livenessProbe();
        break;
      case ProbeType.READINESS:
        result = await this.readinessProbe();
        break;
      case ProbeType.STARTUP:
        result = await this.startupProbe();
        break;
      default:
        throw new Error(`Invalid probe type: ${probeType}`);
    }

    // Cache result
    this.cache.set(probe, { result, timestamp: Date.now() });

    return result;
  }

  /**
   * Get cached health check result if still valid.
   */
  private getCachedResult(probeType: ProbeType): HealthCheckResponse | null {
    const cached = this.cache.get(probeType);
    if (cached && Date.now() - cached.timestamp < this.cacheTtl) {
      return cached.result;
    }
    return null;
  }

  /**
   * Liveness probe: Is the process alive?
   *
   * Checks:
   * - Process is running
   * - Event loop is responsive
   *
   * Does NOT check database or external dependencies.
   */
  private async livenessProbe(): Promise<HealthCheckResponse> {
    const checks: { [key: string]: HealthCheck } = {};

    // Memory check (lightweight, no DB required)
    checks.memory = this.checkMemory();

    const overallStatus = computeOverallStatus(checks);

    return {
      status: overallStatus,
      timestamp: new Date().toISOString(),
      uptime_ms: this.getUptimeMs(),
      version: this.version,
      service: this.serviceName,
      environment: this.environment,
      probe_type: ProbeType.LIVENESS,
      checks,
    };
  }

  /**
   * Readiness probe: Can the service handle traffic?
   *
   * Checks:
   * - Process is running
   * - Database connection is healthy
   * - Connection pool has capacity
   * - Memory usage is acceptable
   */
  private async readinessProbe(): Promise<HealthCheckResponse> {
    const checks: { [key: string]: HealthCheck } = {};

    // Database check
    if (this.database) {
      checks.database = await this.checkDatabase();
    }

    // Memory check
    checks.memory = this.checkMemory();

    const overallStatus = computeOverallStatus(checks);

    return {
      status: overallStatus,
      timestamp: new Date().toISOString(),
      uptime_ms: this.getUptimeMs(),
      version: this.version,
      service: this.serviceName,
      environment: this.environment,
      probe_type: ProbeType.READINESS,
      checks,
    };
  }

  /**
   * Startup probe: Has initialization completed?
   *
   * Checks:
   * - Process is running
   * - Database connection established
   * - Warmup period finished
   */
  private async startupProbe(): Promise<HealthCheckResponse> {
    const checks: { [key: string]: HealthCheck } = {};

    // Database check
    if (this.database) {
      checks.database = await this.checkDatabase();
    }

    // Warmup check
    checks.warmup = this.checkWarmup();

    // Memory check
    checks.memory = this.checkMemory();

    const overallStatus = computeOverallStatus(checks);

    return {
      status: overallStatus,
      timestamp: new Date().toISOString(),
      uptime_ms: this.getUptimeMs(),
      version: this.version,
      service: this.serviceName,
      environment: this.environment,
      probe_type: ProbeType.STARTUP,
      checks,
    };
  }

  /**
   * Check database connectivity and pool health.
   */
  private async checkDatabase(): Promise<DatabaseCheck> {
    if (!this.database) {
      return {
        status: HealthStatus.DOWN,
        error: 'Database pool not initialized',
      };
    }

    const startTime = Date.now();

    try {
      // Execute simple query to verify connectivity
      const result = await Promise.race([
        this.database.query('SELECT 1 as health_check'),
        new Promise((_, reject) =>
          setTimeout(() => reject(new Error('Timeout')), 3000)
        ),
      ]);

      const responseTime = Date.now() - startTime;

      // Get pool statistics
      const poolSize = this.database.totalCount;
      const poolIdle = this.database.idleCount;
      const poolWaiting = this.database.waitingCount;
      const poolMaxSize = (this.database as any).options?.max || 10;

      // Calculate utilization
      const utilization = (poolSize / poolMaxSize) * 100;

      let status = HealthStatus.UP;
      let warning: string | undefined;

      if (utilization > 95) {
        status = HealthStatus.DEGRADED;
        warning = `Connection pool nearly exhausted (${poolSize}/${poolMaxSize})`;
      } else if (utilization > 80) {
        warning = `High connection pool utilization (${utilization.toFixed(1)}%)`;
      }

      return {
        status,
        response_time_ms: Math.round(responseTime * 100) / 100,
        pool_size: poolSize,
        pool_available: poolIdle,
        pool_max_size: poolMaxSize,
        warning,
      };
    } catch (error: any) {
      if (error.message === 'Timeout') {
        return {
          status: HealthStatus.DOWN,
          error: 'Database query timeout (>3s)',
        };
      }
      return {
        status: HealthStatus.DOWN,
        error: `Database connection error: ${error.message}`,
      };
    }
  }

  /**
   * Check memory usage.
   */
  private checkMemory(): MemoryCheck {
    try {
      const memUsage = process.memoryUsage();
      const rssMb = memUsage.rss / 1024 / 1024;
      const heapUsedMb = memUsage.heapUsed / 1024 / 1024;
      const heapTotalMb = memUsage.heapTotal / 1024 / 1024;

      // Estimate total system memory (approximation)
      // In production, could use os.totalmem() if needed
      const totalMb = heapTotalMb * 4; // Rough estimate
      const utilization = (rssMb / totalMb) * 100;

      let status = HealthStatus.UP;
      let warning: string | undefined;

      if (utilization > 90) {
        status = HealthStatus.DEGRADED;
        warning = `Critical memory usage (${utilization.toFixed(1)}%)`;
      } else if (utilization > 80) {
        warning = `High memory usage (${utilization.toFixed(1)}%)`;
      }

      return {
        status,
        used_mb: Math.round(rssMb * 100) / 100,
        total_mb: Math.round(totalMb * 100) / 100,
        utilization_percent: Math.round(utilization * 100) / 100,
        warning,
      };
    } catch (error: any) {
      return {
        status: HealthStatus.DEGRADED,
        warning: `Memory check error: ${error.message}`,
      };
    }
  }

  /**
   * Check if warmup period has completed.
   */
  private checkWarmup(): HealthCheck {
    const uptimeMs = this.getUptimeMs();

    if (uptimeMs < this.startupDurationMs) {
      const progress = (uptimeMs / this.startupDurationMs) * 100;
      return {
        status: HealthStatus.IN_PROGRESS,
        info: `Warming up (${progress.toFixed(0)}% complete)`,
        progress_percent: Math.round(progress * 10) / 10,
        uptime_ms: uptimeMs,
        target_ms: this.startupDurationMs,
      };
    } else {
      return {
        status: HealthStatus.UP,
        info: 'Warmup complete',
      };
    }
  }

  /**
   * Get service uptime in milliseconds.
   */
  private getUptimeMs(): number {
    return Date.now() - this.startTime;
  }
}
