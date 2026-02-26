using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Data.Common;
using System.Diagnostics;
using System.Threading.Tasks;

namespace VelocityBench.HealthCheck;

/// <summary>
/// Health check manager for .NET frameworks.
/// </summary>
public class HealthCheckManager
{
    private readonly HealthCheckConfig _config;
    private readonly Stopwatch _uptime;
    private DbConnection? _database;
    private readonly ConcurrentDictionary<ProbeType, CachedResult> _cache;
    private readonly TimeSpan _cacheTtl = TimeSpan.FromSeconds(5);

    private class CachedResult
    {
        public HealthCheckResponse Result { get; set; }
        public DateTime Timestamp { get; set; }

        public CachedResult(HealthCheckResponse result, DateTime timestamp)
        {
            Result = result;
            Timestamp = timestamp;
        }
    }

    public HealthCheckManager(HealthCheckConfig config)
    {
        _config = config;
        _uptime = Stopwatch.StartNew();
        _cache = new ConcurrentDictionary<ProbeType, CachedResult>();
    }

    /// <summary>
    /// Set database connection for health checks.
    /// </summary>
    public HealthCheckManager WithDatabase(DbConnection connection)
    {
        _database = connection;
        return this;
    }

    /// <summary>
    /// Execute a health check probe.
    /// </summary>
    public async Task<HealthCheckResponse> ProbeAsync(string probeType)
    {
        var probe = Enum.Parse<ProbeType>(probeType, ignoreCase: true);

        // Check cache
        var cached = GetCachedResult(probe);
        if (cached != null)
        {
            return cached;
        }

        // Execute probe
        var result = probe switch
        {
            ProbeType.Liveness => await LivenessProbeAsync(),
            ProbeType.Readiness => await ReadinessProbeAsync(),
            ProbeType.Startup => await StartupProbeAsync(),
            _ => throw new ArgumentException($"Unknown probe type: {probeType}")
        };

        // Cache result
        CacheResult(probe, result);

        return result;
    }

    /// <summary>
    /// Get cached result if still valid.
    /// </summary>
    private HealthCheckResponse? GetCachedResult(ProbeType probeType)
    {
        if (!_cache.TryGetValue(probeType, out var cached))
        {
            return null;
        }

        var age = DateTime.UtcNow - cached.Timestamp;
        if (age < _cacheTtl)
        {
            return cached.Result;
        }

        return null;
    }

    /// <summary>
    /// Cache a health check result.
    /// </summary>
    private void CacheResult(ProbeType probeType, HealthCheckResponse result)
    {
        _cache[probeType] = new CachedResult(result, DateTime.UtcNow);
    }

    /// <summary>
    /// Liveness probe: Is the process alive?
    /// </summary>
    private Task<HealthCheckResponse> LivenessProbeAsync()
    {
        var checks = new Dictionary<string, HealthCheck>
        {
            ["memory"] = CheckMemory()
        };

        var overallStatus = ComputeOverallStatus(checks);

        return Task.FromResult(new HealthCheckResponse(
            status: overallStatus,
            timestamp: GetTimestamp(),
            uptimeMs: GetUptimeMs(),
            version: _config.Version,
            service: _config.ServiceName,
            environment: _config.Environment,
            probeType: ProbeType.Liveness,
            checks: checks
        ));
    }

    /// <summary>
    /// Readiness probe: Can the service handle traffic?
    /// </summary>
    private async Task<HealthCheckResponse> ReadinessProbeAsync()
    {
        var checks = new Dictionary<string, HealthCheck>();

        // Database check
        if (_database != null)
        {
            checks["database"] = await CheckDatabaseAsync();
        }

        // Memory check
        checks["memory"] = CheckMemory();

        var overallStatus = ComputeOverallStatus(checks);

        return new HealthCheckResponse(
            status: overallStatus,
            timestamp: GetTimestamp(),
            uptimeMs: GetUptimeMs(),
            version: _config.Version,
            service: _config.ServiceName,
            environment: _config.Environment,
            probeType: ProbeType.Readiness,
            checks: checks
        );
    }

    /// <summary>
    /// Startup probe: Has initialization completed?
    /// </summary>
    private async Task<HealthCheckResponse> StartupProbeAsync()
    {
        var checks = new Dictionary<string, HealthCheck>();

        // Database check
        if (_database != null)
        {
            checks["database"] = await CheckDatabaseAsync();
        }

        // Warmup check
        checks["warmup"] = CheckWarmup();

        // Memory check
        checks["memory"] = CheckMemory();

        var overallStatus = ComputeOverallStatus(checks);

        return new HealthCheckResponse(
            status: overallStatus,
            timestamp: GetTimestamp(),
            uptimeMs: GetUptimeMs(),
            version: _config.Version,
            service: _config.ServiceName,
            environment: _config.Environment,
            probeType: ProbeType.Startup,
            checks: checks
        );
    }

    /// <summary>
    /// Check database connectivity.
    /// </summary>
    private async Task<HealthCheck> CheckDatabaseAsync()
    {
        var sw = Stopwatch.StartNew();

        try
        {
            if (_database!.State != System.Data.ConnectionState.Open)
            {
                await _database.OpenAsync();
            }

            using var command = _database.CreateCommand();
            command.CommandText = "SELECT 1";
            command.CommandTimeout = 3;
            await command.ExecuteScalarAsync();

            sw.Stop();
            var responseTime = sw.Elapsed.TotalMilliseconds;

            return new HealthCheck(HealthStatus.Up)
                .WithResponseTime(responseTime)
                .WithData("pool_size", 0)
                .WithData("pool_available", 0);
        }
        catch (Exception ex)
        {
            return new HealthCheck(HealthStatus.Down)
                .WithError($"Database connection error: {ex.Message}");
        }
    }

    /// <summary>
    /// Check memory usage.
    /// </summary>
    private HealthCheck CheckMemory()
    {
        var process = Process.GetCurrentProcess();
        var usedMemory = process.WorkingSet64;
        var totalMemory = GC.GetTotalMemory(false);

        var usedMb = usedMemory / (1024.0 * 1024.0);
        var totalMb = totalMemory / (1024.0 * 1024.0);
        var utilization = (usedMemory * 100.0) / totalMemory;

        var check = new HealthCheck(HealthStatus.Up)
            .WithData("used_mb", Math.Round(usedMb, 2))
            .WithData("total_mb", Math.Round(totalMb, 2))
            .WithData("utilization_percent", Math.Round(utilization, 2));

        if (utilization > 90.0)
        {
            check.Status = HealthStatus.Degraded;
            check.WithWarning($"Critical memory usage ({utilization:F1}%)");
        }
        else if (utilization > 80.0)
        {
            check.WithWarning($"High memory usage ({utilization:F1}%)");
        }

        return check;
    }

    /// <summary>
    /// Check if warmup period has completed.
    /// </summary>
    private HealthCheck CheckWarmup()
    {
        var uptimeMs = GetUptimeMs();

        if (uptimeMs < _config.StartupDurationMs)
        {
            var progress = (uptimeMs * 100.0) / _config.StartupDurationMs;
            return new HealthCheck(HealthStatus.InProgress)
                .WithInfo($"Warming up ({progress:F0}% complete)")
                .WithData("progress_percent", Math.Round(progress, 2))
                .WithData("uptime_ms", uptimeMs)
                .WithData("target_ms", _config.StartupDurationMs);
        }

        return new HealthCheck(HealthStatus.Up)
            .WithInfo("Warmup complete");
    }

    /// <summary>
    /// Compute overall health status from individual checks.
    /// </summary>
    private HealthStatus ComputeOverallStatus(Dictionary<string, HealthCheck> checks)
    {
        var hasDown = false;
        var hasInProgress = false;
        var hasDegraded = false;

        foreach (var check in checks.Values)
        {
            switch (check.Status)
            {
                case HealthStatus.Down:
                    hasDown = true;
                    break;
                case HealthStatus.InProgress:
                    hasInProgress = true;
                    break;
                case HealthStatus.Degraded:
                    hasDegraded = true;
                    break;
            }
        }

        if (hasDown) return HealthStatus.Down;
        if (hasInProgress) return HealthStatus.InProgress;
        if (hasDegraded) return HealthStatus.Degraded;
        return HealthStatus.Up;
    }

    /// <summary>
    /// Get service uptime in milliseconds.
    /// </summary>
    private long GetUptimeMs()
    {
        return _uptime.ElapsedMilliseconds;
    }

    /// <summary>
    /// Get current timestamp in ISO 8601 format.
    /// </summary>
    private string GetTimestamp()
    {
        return DateTime.UtcNow.ToString("o");
    }
}
