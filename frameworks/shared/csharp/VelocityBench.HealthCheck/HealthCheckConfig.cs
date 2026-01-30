namespace VelocityBench.HealthCheck;

/// <summary>
/// Health check manager configuration.
/// </summary>
public class HealthCheckConfig
{
    public string ServiceName { get; set; } = "velocitybench";
    public string Version { get; set; } = "1.0.0";
    public string Environment { get; set; } = "development";
    public long StartupDurationMs { get; set; } = 30000; // 30 seconds

    public HealthCheckConfig()
    {
    }

    public HealthCheckConfig(string serviceName, string version, string environment, long startupDurationMs = 30000)
    {
        ServiceName = serviceName;
        Version = version;
        Environment = environment;
        StartupDurationMs = startupDurationMs;
    }
}
