using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace VelocityBench.HealthCheck;

/// <summary>
/// Individual health check result.
/// </summary>
public class HealthCheck
{
    [JsonPropertyName("status")]
    public HealthStatus Status { get; set; }

    [JsonPropertyName("response_time_ms")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public double? ResponseTimeMs { get; set; }

    [JsonPropertyName("error")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Error { get; set; }

    [JsonPropertyName("warning")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Warning { get; set; }

    [JsonPropertyName("info")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Info { get; set; }

    [JsonExtensionData]
    public Dictionary<string, object>? AdditionalData { get; set; }

    public HealthCheck(HealthStatus status)
    {
        Status = status;
        AdditionalData = new Dictionary<string, object>();
    }

    public HealthCheck WithResponseTime(double ms)
    {
        ResponseTimeMs = ms;
        return this;
    }

    public HealthCheck WithError(string error)
    {
        Error = error;
        return this;
    }

    public HealthCheck WithWarning(string warning)
    {
        Warning = warning;
        return this;
    }

    public HealthCheck WithInfo(string info)
    {
        Info = info;
        return this;
    }

    public HealthCheck WithData(string key, object value)
    {
        AdditionalData ??= new Dictionary<string, object>();
        AdditionalData[key] = value;
        return this;
    }
}
