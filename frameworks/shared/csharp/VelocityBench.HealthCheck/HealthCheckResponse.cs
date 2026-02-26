using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace VelocityBench.HealthCheck;

/// <summary>
/// Complete health check response.
/// </summary>
public class HealthCheckResponse
{
    [JsonPropertyName("status")]
    public HealthStatus Status { get; set; }

    [JsonPropertyName("timestamp")]
    public string Timestamp { get; set; }

    [JsonPropertyName("uptime_ms")]
    public long UptimeMs { get; set; }

    [JsonPropertyName("version")]
    public string Version { get; set; }

    [JsonPropertyName("service")]
    public string Service { get; set; }

    [JsonPropertyName("environment")]
    public string Environment { get; set; }

    [JsonPropertyName("probe_type")]
    public ProbeType ProbeType { get; set; }

    [JsonPropertyName("checks")]
    public Dictionary<string, HealthCheck> Checks { get; set; }

    public HealthCheckResponse(
        HealthStatus status,
        string timestamp,
        long uptimeMs,
        string version,
        string service,
        string environment,
        ProbeType probeType,
        Dictionary<string, HealthCheck> checks)
    {
        Status = status;
        Timestamp = timestamp;
        UptimeMs = uptimeMs;
        Version = version;
        Service = service;
        Environment = environment;
        ProbeType = probeType;
        Checks = checks;
    }

    /// <summary>
    /// Get HTTP status code based on health status and probe type.
    /// </summary>
    public int GetHttpStatusCode()
    {
        return Status switch
        {
            HealthStatus.Down => 503,
            HealthStatus.InProgress when ProbeType == ProbeType.Startup => 202,
            _ => 200
        };
    }
}
