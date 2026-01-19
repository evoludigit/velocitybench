# **[Pattern] Virtual Machines Profiling: Reference Guide**

---

## **1. Overview**

The **Virtual Machines Profiling** pattern captures performance, resource usage, and behavior metrics of virtualized environments to optimize workloads, identify bottlenecks, and ensure operational efficiency. This pattern applies to cloud-native, hybrid, or on-premises virtualized infrastructures (e.g., VMware, AWS EC2, Azure VMs, Kubernetes VMs). Profiling involves collecting data on CPU, memory, disk I/O, network latency, and application-level metrics (e.g., request latency, GC pauses) across VMs—either via agent-based tools (e.g., Prometheus, Datadog), distribution tracing (OpenTelemetry), or logs (ELK Stack). The goal is to correlate infrastructure and application telemetry to diagnose inefficiencies, enforce SLAs, and right-size resources dynamically.

Key use cases include:
- **Performance tuning**: Identifying under/over-provisioned VMs or inefficient workloads.
- **Cost optimization**: Detecting idle VMs or misconfigured autoscaling policies.
- **Incident root cause analysis**: Tracing latency spikes from VM-level metrics to guest OS/application layers.
- **Compliance/auditing**: Tracking VM usage patterns for governance (e.g., security patches, storage quotas).

---
## **2. Schema Reference**

This section defines the core metrics, events, and attributes collected during VM profiling. Use these schemas for instrumentation and querying.

### **2.1 Core Metrics Schema**
| **Category**               | **Metric Name**               | **Unit**       | **Description**                                                                 | **Example Values**                     |
|----------------------------|-------------------------------|----------------|---------------------------------------------------------------------------------|-----------------------------------------|
| **CPU**                    | `cpu_usage_avg`               | %              | Average CPU utilization per VM over a time window.                               | `35.2`, `78.9`                          |
|                            | `cpu_steal_time`              | ms             | Time the VM was blocked by the hypervisor (e.g., due to overcommitment).        | `120`, `0`                              |
|                            | `cpu_guest_time`              | ms             | Time spent executing guest OS/VM processes.                                     | `4560`                                  |
| **Memory**                 | `memory_usage`                | MiB            | Resident memory (RAM) consumed by the VM.                                       | `2562`, `4096`                          |
|                            | `memory_swap`                 | MiB/sec        | Swap activity (indicates pressure).                                             | `50.3`, `0`                             |
|                            | `memory_ballooned`            | MiB            | Memory reclaimed by ballooning driver (if enabled).                             | `128`                                    |
| **Disk I/O**               | `disk_read_ops`               | ops/sec        | Read operations per second for a given disk.                                    | `15`, `1000`                            |
|                            | `disk_write_latency`          | ms             | Average time per write operation.                                               | `20`, `100`                             |
|                            | `disk_queue_depth`            | ops            | Number of pending I/O requests.                                                 | `4`, `50`                               |
| **Network**                | `net_in_bytes`                | B/sec          | Inbound network traffic.                                                        | `1200000`, `0`                          |
|                            | `net_out_bytes`               | B/sec          | Outbound network traffic.                                                       | `850000`, `1000000`                     |
|                            | `packet_loss`                 | %              | Percentage of lost packets (e.g., due to congestion).                           | `0.1`, `5.2`                            |
| **Application**            | `http_request_latency`        | ms             | Latency for HTTP requests (if instrumented).                                    | `85`, `320`                             |
|                            | `gc_pause_time`               | ms             | Garbage collection pauses (Java/Python VMs).                                    | `15`, `0`                               |
| **System**                 | `vm_up_time`                   | seconds        | Time since VM boot.                                                             | `3600` (1 hour)                         |
|                            | `hypervisor_host`             | String         | Name of the host managing the VM.                                               | `"host-west-01"`                        |
|                            | `vm_state`                    | Enum           | Running, paused, suspended, crashed.                                           | `"running"`, `"paused"`                 |

---

### **2.2 Events Schema**
| **Event Name**              | **Description**                                                                 | **Attributes**                                                                 |
|-----------------------------|---------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| `vm_booted`                 | VM started (or restarted).                                                     | `boot_time`, `guest_os`, `hypervisor_version`                               |
| `vm_shutdown`               | VM gracefully halted.                                                          | `shutdown_reason` (user, crash, etc.), `elapsed_uptime`                      |
| `cpu_throttling_event`      | CPU throttling occurred (e.g., due to overcommitment).                          | `throttle_duration_ms`, `affected_vcpus`                                    |
| `disk_iotimeout`            | I/O timeout detected (e.g., disk failure).                                     | `disk_device`, `timeout_ms`, `error_code`                                   |
| `memory_oom_event`          | Out-of-memory event in guest OS.                                               | `memory_limit_mib`, `actual_usage_mib`, `reclaimed_mib`                      |

---

### **2.3 Tags (Filtering Context)**
| **Tag Key**          | **Description**                     | **Example Values**               |
|----------------------|-------------------------------------|-----------------------------------|
| `vm_id`              | Unique identifier for the VM.        | `"vm-1234567890abcdef"`           |
| `project`            | Organizational/project context.      | `"finance-team"`                   |
| `vm_type`            | VM role (e.g., web, db, batch).     | `"web-server"`, `"redis"`          |
| `region`             | Cloud region/hypervisor cluster.     | `"us-west-2"`, `"on-prem"`         |
| `guest_os`           | Operating system of the VM.          | `"Ubuntu 22.04"`, `"Windows 10"`  |

---
## **3. Query Examples**

### **3.1 Basic Aggregations**
**Query 1: Average CPU usage across VMs**
```sql
SELECT
  vm_id,
  avg(cpu_usage_avg) as avg_cpu_usage
FROM virtual_machines_metrics
WHERE timestamp > now() - 1h
GROUP BY vm_id
ORDER BY avg_cpu_usage DESC;
```

**Query 2: Disk I/O anomalies (high latency)**
```sql
SELECT
  vm_id,
  avg(disk_write_latency) as avg_write_latency
FROM virtual_machines_metrics
WHERE timestamp > now() - 6h
GROUP BY vm_id
HAVING avg_write_latency > 100  -- Threshold for "slow" disks
ORDER BY avg_write_latency DESC;
```

---

### **3.2 Time-Series Analysis**
**Query 3: CPU usage over time (per VM)**
```sql
SELECT
  vm_id,
  time_bucket('10m', timestamp) as interval,
  avg(cpu_usage_avg) as cpu_usage
FROM virtual_machines_metrics
WHERE vm_id = 'vm-1234567890abcdef'
  AND timestamp > now() - 24h
GROUP BY vm_id, interval
ORDER BY interval;
```

**Query 4: Detect VMs approaching memory limits**
```sql
SELECT
  vm_id,
  max(memory_usage) as peak_memory_usage,
  memory_usage_limit_mib as limit
FROM (
  SELECT
    vm_id,
    memory_usage,
    (SELECT config.mem_limit FROM vm_configs WHERE vm_id = virtual_machines_metrics.vm_id) as memory_usage_limit_mib
  FROM virtual_machines_metrics
  WHERE timestamp > now() - 1h
)
GROUP BY vm_id
HAVING peak_memory_usage > limit * 0.9  -- 90% of limit
ORDER BY peak_memory_usage DESC;
```

---

### **3.3 Correlating Infrastructure + Application Metrics**
**Query 5: HTTP latency spikes with high CPU**
```sql
WITH cpu_spikes AS (
  SELECT
    vm_id,
    time_bucket('1m', timestamp) as interval,
    avg(cpu_usage_avg) as avg_cpu
  FROM virtual_machines_metrics
  WHERE timestamp > now() - 1h
    AND avg(cpu_usage_avg) > 80  -- High CPU threshold
  GROUP BY vm_id, interval
),
latency_spikes AS (
  SELECT
    vm_id,
    time_bucket('1m', timestamp) as interval,
    avg(http_request_latency) as avg_latency
  FROM application_traces
  WHERE timestamp > now() - 1h
    AND avg(http_request_latency) > 200  -- High latency threshold
  GROUP BY vm_id, interval
)
SELECT
  cs.vm_id,
  cs.interval,
  cs.avg_cpu,
  ls.avg_latency
FROM cpu_spikes cs
JOIN latency_spikes ls ON cs.vm_id = ls.vm_id AND cs.interval = ls.interval;
```

---

### **3.4 Alerting Rules**
**Query 6: Alert when VMs are idle for >1h**
```sql
SELECT
  vm_id,
  time_bucket('1h', timestamp) as hour
FROM virtual_machines_metrics
WHERE cpu_usage_avg < 5  -- Threshold for "idle"
  AND memory_usage < 5  -- Threshold for "idle"
  AND timestamp > now() - 24h
GROUP BY vm_id, hour
HAVING COUNT(*) = 1  -- Only 1 hour of data (implying inactivity)
ORDER BY vm_id;
```

---
## **4. Implementation Techniques**

### **4.1 Data Collection**
| **Tool/Method**               | **Pros**                                      | **Cons**                                      | **Use Case**                          |
|--------------------------------|-----------------------------------------------|-----------------------------------------------|---------------------------------------|
| **Prometheus + Node Exporter** | Lightweight, high-resolution metrics.       | Requires agents on each VM.                   | Cloud/on-prem VMs.                   |
| **OpenTelemetry (OTel)**       | Unified tracing/metrics/logs.                | Higher overhead; requires instrumentation.    | Microservices in VMs.                |
| **Cloud Provider Metrics**     | Native integration (AWS CloudWatch, Azure VM Insights). | Vendor lock-in; slower ingestion.         | Managed cloud VMs.                   |
| **Log-Based (ELK/Fluentd)**    | Full context from logs.                       | Lower granularity; harder to parse.          | Debugging guest OS/application issues. |

---
### **4.2 Sampling Strategies**
| **Strategy**               | **Description**                                                                 | **When to Use**                                      |
|----------------------------|-------------------------------------------------------------------------------|------------------------------------------------------|
| **Fixed Interval**         | Collect metrics every `N` seconds (e.g., 15s, 1m).                           | General-purpose monitoring.                          |
| **Event-Triggered**        | Emit metrics on specific events (e.g., `vm_booted`, OOM).                     | Alerting/correlation.                                |
| **Adaptive Sampling**      | Increase frequency during anomalies (e.g., CPU spikes).                       | Performance debugging.                               |
| **Trace Sampling**         | Sample application traces at a low rate (e.g., 1%).                           | Distributed systems in VMs.                         |

---
### **4.3 Storage Optimization**
| **Strategy**               | **Description**                                                                 | **Tools**                                  |
|----------------------------|-------------------------------------------------------------------------------|--------------------------------------------|
| **Time-Series DB**         | Optimized for metrics (e.g., Prometheus, InfluxDB).                          | High-cardinality metrics.                 |
| **Log Archival**           | Move cold logs to S3/Blob Storage after retention period.                     | ELK, Graylog.                              |
| **Compression**            | Use Snappy/GZIP for logs/metrics.                                             | Fluentd, Logstash.                         |
| **Downsampling**           | Aggregate metrics over longer windows (e.g., 1m → 5m).                       | Prometheus, Grafana.                       |

---
## **5. Related Patterns**

| **Pattern**                          | **Description**                                                                 | **When to Combine**                                  |
|--------------------------------------|-------------------------------------------------------------------------------|------------------------------------------------------|
| **[Resource Auto-Scaling]**         | Automatically adjust VM resources based on load.                              | Use profiling data to inform scaling decisions.       |
| **[Distributed Tracing]**           | Trace requests across microservices in VMs.                                   | Correlate application latency with VM metrics.        |
| **[Anomaly Detection]**              | Detect unusual patterns in VM metrics.                                         | Identify outlier VMs in large fleets.                 |
| **[Performance Budgeting]**         | Enforce SLAs for VM performance.                                              | Set thresholds for CPU/memory in profilers.           |
| **[Observability Pipeline]**         | Unified logs, metrics, and traces.                                            | Replace siloed monitoring tools.                     |
| **[Cost Optimization]**             | Reduce VM costs via rightsizing/spot instances.                                | Profile VM usage before down-sizing.                 |

---
## **6. Troubleshooting**
| **Issue**                          | **Diagnostic Queries**                                                                 | **Solution**                                                                 |
|-------------------------------------|--------------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **High disk latency**             | `SELECT avg(disk_write_latency) FROM ... WHERE disk_device = 'sda1'`                 | Check for disk I/O bottlenecks; consider NVMe or RAID.                      |
| **CPU throttling**                 | `SELECT * FROM cpu_throttling_event WHERE timestamp > now() - 1d`                   | Reduce VM count on host or increase CPU quota.                                |
| **Memory leaks**                   | `SELECT vm_id, max(memory_usage) FROM ... GROUP BY vm_id ORDER BY max(memory_usage) DESC` | Restart the VM or investigate application leaks.                             |
| **Network congestion**             | `SELECT vm_id, avg(packet_loss) FROM ... WHERE timestamp > now() - 5m`             | Isolate VMs or upgrade network capacity.                                       |

---
## **7. Best Practices**
1. **Instrument at Layer 4+**:
   - Profile both guest OS (e.g., `top`, `htop`) and application layers (e.g., JVM stats, MySQL slow queries).
2. **Set Contextual Alerts**:
   - Use tags (e.g., `vm_type`) to distinguish between critical vs. background VMs.
3. **Retain Historical Data**:
   - Store 1-day metrics at high resolution; 1-month at low resolution (e.g., hourly).
4. **Benchmark Baseline**:
   - Profile VMs under "normal" load to establish thresholds for anomalies.
5. **Minimize Overhead**:
   - Sample metrics aggressively during profiling; reduce frequency in production.