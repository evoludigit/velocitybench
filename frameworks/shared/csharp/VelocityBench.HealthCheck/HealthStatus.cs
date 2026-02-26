using System.Runtime.Serialization;
using System.Text.Json.Serialization;

namespace VelocityBench.HealthCheck;

/// <summary>
/// Health check status values.
/// </summary>
[JsonConverter(typeof(JsonStringEnumConverter))]
public enum HealthStatus
{
    [EnumMember(Value = "up")]
    Up,

    [EnumMember(Value = "degraded")]
    Degraded,

    [EnumMember(Value = "down")]
    Down,

    [EnumMember(Value = "in_progress")]
    InProgress
}
