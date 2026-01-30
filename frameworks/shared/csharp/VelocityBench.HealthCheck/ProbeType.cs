using System.Runtime.Serialization;
using System.Text.Json.Serialization;

namespace VelocityBench.HealthCheck;

/// <summary>
/// Health check probe types (Kubernetes-compatible).
/// </summary>
[JsonConverter(typeof(JsonStringEnumConverter))]
public enum ProbeType
{
    [EnumMember(Value = "liveness")]
    Liveness,

    [EnumMember(Value = "readiness")]
    Readiness,

    [EnumMember(Value = "startup")]
    Startup
}
