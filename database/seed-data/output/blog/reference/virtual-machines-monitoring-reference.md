# **[Pattern] Virtual-Machines Monitoring – Reference Guide**

---

## **Overview**
The **Virtual-Machines Monitoring** pattern ensures continuous observation and performance tracking of virtual machines (VMs) across cloud, on-premises, or hybrid environments. It provides real-time visibility into **CPU load, memory usage, disk I/O, network throughput, and guest OS metrics**, while correlating data with infrastructure events (e.g., scale-out, live migration, or VM failures). This pattern supports:
- **Proactive issue detection** (throttling, high latency, or misallocated resources).
- **Capacity planning** (forecasting workload growth).
- **Compliance and auditing** (VM state tracking, guest OS health).
- **Automated remediation** (triggering scale adjustments, snapshots, or alerts).

It integrates with cloud providers (AWS, Azure, GCP), hypervisors (VMware, Hyper-V), and agents (e.g., Prometheus, Datadog, Azure Monitor) via **metrics APIs, logs, or events**. This guide covers key concepts, schema design, query patterns, and related best practices.

---

## **Implementation Details**

### **Core Components**
| Component                     | Responsibility                                                                 | Example Tools/Technologies                          |
|-------------------------------|---------------------------------------------------------------------------------|----------------------------------------------------|
| **Metrics Collectors**        | Gathers performance data (CPU, memory, disk, network) from VMs and host.       | Prometheus, OpenTelemetry, VMware vSphere Metrics   |
| **Log Aggregators**           | Stores VM logs (e.g., guest OS events, agent logs) for debugging.               | ELK Stack, Azure Monitor Logs                      |
| **EventHubs**                 | Captures VM lifecycle events (start/stop, snapshot, migration).                | AWS CloudWatch Events, Azure Event Grid             |
| **Alerting Engine**           | Triggers notifications (e.g., SLO violations, anomalies).                      | Alertmanager, PagerDuty, Opsgenie                    |
| **Dashboarding**              | Visualizes metrics/logs for teams (e.g., usage trends, capacity alerts).       | Grafana, Azure Portal, AWS CloudWatch Dashboards    |
| **Remediation Workflows**     | Automates actions (e.g., scaling, restarting VMs, or sending support tickets). | Kubernetes Operators, AWS Lambda, Azure Logic Apps |

---

### **Key Metrics**
Monitor these **core VM metrics** to detect performance issues or inefficiencies:

| **Category**       | **Metric**                                | **Description**                                                                 | **Unit**       | **Critical Thresholds**                     |
|--------------------|-------------------------------------------|---------------------------------------------------------------------------------|----------------|---------------------------------------------|
| **CPU**            | CPU Usage (per core/vCPU)                 | Percentage of CPU time consumed by the VM.                                      | %              | >90% sustained may indicate bottleneck.     |
|                    | CPU Steal Time                            | Time VM is unable to access CPU due to host scheduling.                           | %              | >10% suggests overloaded hypervisor.        |
| **Memory**         | Memory Usage (Reserved/Committed)         | Actual memory consumption vs. allocated capacity.                               | GB/MB          | Near-capacity may trigger ballooning or OOM. |
|                    | Ballooning (Memory Overcommit)            | Guest OS "donates" unused memory to host (if enabled).                           | GB             | High values indicate under-allocation.       |
| **Disk**           | Disk I/O Latency                          | Time taken for disk read/write operations.                                        | ms             | >100ms may affect application performance.   |
|                    | Disk Queue Length                         | Number of pending I/O requests.                                                   | # requests     | >100 suggests disk bottleneck.              |
| **Network**        | Network In/Out Bytes                      | Bandwidth usage per interface.                                                     | GB/s           | Sudden spikes may indicate DDoS or misconfig. |
|                    | Packet Drop Rate                          | Packets lost due to buffer overflows.                                             | %              | >1% may indicate NIC or switch issues.       |
| **Guest OS**       | Guest OS Uptime                           | Time since VM last reboot (helps track stability).                                | Hours          | Frequent crashes (<24h uptime) may require troubleshooting. |
|                    | Guest Agent Status                        | Indicates if guest OS agent (e.g., VMware Tools) is running.                     | Status (Online/Offline) | Offline = missing metrics.                  |
| **Host**           | Host CPU/Memory Pressure                  | Aggregated impact of all VMs on the host.                                         | %              | Host pressure >70% may throttle VMs.         |

---
## **Schema Reference**
Design your monitoring schema to capture **time-series metrics**, **logs**, and **events** efficiently. Below is a normalized schema for cloud-native storage (e.g., **InfluxDB, TimescaleDB, or Azure Monitor**).

### **1. Metrics Schema**
```sql
CREATE TABLE vm_metrics (
    metric_id SERIAL PRIMARY KEY,
    vm_id VARCHAR(64) NOT NULL,       -- Unique VM identifier (e.g., AWS Instance ID)
    timestamp TIMESTAMP NOT NULL,     -- UTC timestamp of measurement
    metric_name VARCHAR(50) NOT NULL, -- e.g., "cpu.usage", "disk.latency"
    value FLOAT,                      -- Numeric value (e.g., 85.2 for CPU%)
    unit VARCHAR(10),                 -- e.g., "percent", "bytes", "milliseconds"
    tags JSONB,                       -- Structured metadata:
    -- Example:
    -- {"host": "esxi-01", "datastore": "datastore1", "os_type": "linux"}
    host_id VARCHAR(64),              -- Optional: Link to host metrics
    metadata JSONB                    -- Additional context (e.g., workload type)
);
```

**Example Rows:**
| `metric_id` | `vm_id`      | `timestamp`          | `metric_name`   | `value` | `unit`  | `tags`                          | `host_id` |
|-------------|--------------|----------------------|-----------------|---------|---------|---------------------------------|-----------|
| 1           | i-123456     | 2023-10-01T12:00:00Z | `cpu.usage`     | 87.5    | percent | `{"datacenter": "us-east-1"}`   | h-7890    |
| 2           | vm-abc123    | 2023-10-01T12:05:00Z | `disk.read_latency` | 250     | ms      | `{"os": "windows"}`             |           |

---

### **2. Logs Schema**
```sql
CREATE TABLE vm_logs (
    log_id SERIAL PRIMARY KEY,
    vm_id VARCHAR(64) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    log_level VARCHAR(10),         -- INFO, WARNING, ERROR, CRITICAL
    message TEXT,
    log_source VARCHAR(50),        -- e.g., "guest_agent", "hypervisor"
    tags JSONB                     -- Structured log metadata
);
```
**Example:**
| `log_id` | `vm_id`      | `timestamp`          | `log_level` | `message`                          | `log_source`          | `tags`                  |
|----------|--------------|----------------------|--------------|-------------------------------------|------------------------|-------------------------|
| 1        | i-123456     | 2023-10-01T11:30:00Z | ERROR        | "Disk full: /var"                   | guest_agent           | `{"os": "ubuntu"}`      |
| 2        | vm-abc123    | 2023-10-01T12:10:00Z | CRITICAL     | "Failed to boot: kernel panic"       | hypervisor            | `{"cause": "driver_fault"}` |

---

### **3. Events Schema**
```sql
CREATE TABLE vm_events (
    event_id SERIAL PRIMARY KEY,
    vm_id VARCHAR(64) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    event_type VARCHAR(30),          -- e.g., "vm_started", "snapshot_created"
    event_data JSONB                 -- Structured payload
);
```
**Example:**
| `event_id` | `vm_id`      | `timestamp`          | `event_type`         | `event_data`                          |
|------------|--------------|----------------------|----------------------|---------------------------------------|
| 1          | i-123456     | 2023-10-01T09:00:00Z | `vm_started`         | `{"user": "admin", "host": "esxi-01"}` |
| 2          | vm-abc123    | 2023-10-01T11:45:00Z | `snapshot_created`   | `{"name": "pre-migration-snap", "size": 1024}` |

---

## **Query Examples**
### **1. Alerting: CPU Throttling Detection**
**Goal:** Detect VMs experiencing CPU steal time >5% for 5+ minutes.
```sql
-- Query (TimescaleDB/InfluxQL)
SELECT
    vm_id,
    AVG(value) AS avg_cpu_throttle
FROM vm_metrics
WHERE
    metric_name = 'cpu.steal'
    AND timestamp > now() - 5m
GROUP BY vm_id
HAVING avg_cpu_throttle > 0.05
ORDER BY avg_cpu_throttle DESC;
```

**Output:**
| `vm_id`      | `avg_cpu_throttle` |
|--------------|--------------------|
| i-789abc     | 0.07               |
| vm-def456    | 0.12               |

---

### **2. Capacity Planning: Memory Overcommit Analysis**
**Goal:** Identify hosts with >300% memory overcommit ratio.
```sql
-- Assumes `host_metrics` table with:
-- host_id, total_memory_gb, used_memory_gb, vm_count
SELECT
    h.host_id,
    (h.total_memory_gb / SUM(v.value)::float) * 100 AS overcommit_ratio
FROM host_metrics h
JOIN vm_metrics v ON h.host_id = v.host_id
WHERE
    v.metric_name = 'memory.used'
    AND v.timestamp > now() - 1h
GROUP BY h.host_id
HAVING overcommit_ratio > 300;
```

**Output:**
| `host_id` | `overcommit_ratio` |
|-----------|--------------------|
| h-456xyz  | 320.1              |

---

### **3. Debugging: Disk Latency Spikes**
**Goal:** Find VMs with disk latency >150ms in the last 10 minutes.
```sql
-- Grafana/InfluxQL
query = 'from(bucket:"vm-metrics")\
  |> range(start=-10m)\
  |> filter(fn: (r) => r._measurement == "disk_latency")\
  |> filter(fn: (r) => r.vm_id == "$vm_id")\
  |> mean()\
  |> threshold(min: 150)'
```
**Output (Grafana Table):**
| `vm_id`      | `mean_disk_latency_ms` |
|--------------|------------------------|
| vm-ghi789    | 180                    |

---
### **4. Correlation: Events Leading to VM Restarts**
**Goal:** Find VMs that restarted after a disk error event.
```sql
SELECT
    e1.vm_id,
    e1.timestamp AS restart_time,
    e2.timestamp AS error_time
FROM vm_events e1
JOIN vm_events e2 ON e1.vm_id = e2.vm_id
WHERE
    e1.event_type = 'vm_restarted'
    AND e2.event_type = 'disk_error'
    AND e1.timestamp BETWEEN e2.timestamp - 1h AND e2.timestamp + 1h
ORDER BY restart_time DESC;
```

**Output:**
| `vm_id`      | `restart_time`         | `error_time`          |
|--------------|------------------------|------------------------|
| i-123xyz     | 2023-10-01T13:15:00Z    | 2023-10-01T13:00:00Z    |

---

## **Best Practices**
1. **Sampling Rate:**
   - **CPU/Memory:** 1 minute (high cardinality).
   - **Disk/Network:** 5–10 seconds (volatile metrics).
   - **Logs:** Retain critical logs for 30 days; compress older data.

2. **Alert Granularity:**
   - Use **multi-level thresholds** (e.g., warn at 80%, alert at 90% CPU).
   - Avoid "alert fatigue" by correlating metrics (e.g., only alert on CPU + disk spikes).

3. **Guest Agent Reliability:**
   - Deploy lightweight agents (e.g., Prometheus Node Exporter) to avoid VM performance impact.
   - Fallback to **host-level metrics** if guest agent fails.

4. **Cost Optimization:**
   - Cloud providers: Use **reserved instances** for long-term metrics storage.
   - Downsample metrics after 1 week (e.g., from 1m to 5m intervals).

5. **Security:**
   - Encrypt sensitive logs (e.g., credentials in VM console output).
   - Restrict access to monitoring dashboards via **RBAC** (e.g., AWS IAM, Azure RB).

---

## **Related Patterns**
| Pattern                          | Description                                                                 | When to Use                                      |
|----------------------------------|-----------------------------------------------------------------------------|--------------------------------------------------|
| **[Multi-Cloud Observability]**   | Aggregates metrics from AWS, Azure, GCP, and on-prem.                        | Teams using hybrid/cloud-native deployments.      |
| **[Infrastructure as Code (IaC) Monitoring]** | Deploys monitoring via Terraform/CloudFormation.                          | CI/CD pipelines requiring consistent monitoring setups. |
| **[Anomaly Detection]**           | Uses ML to flag unusual patterns (e.g., sudden disk growth).                | Detecting zero-day attacks or misconfigurations.  |
| **[Cost Optimization]**          | Tracks VM usage to right-size instances and avoid over-provisioning.        | Reducing cloud bills by 15–25%.                  |
| **[Chaos Engineering for VMs]**   | Simulates failures (e.g., network partitions) to validate resilience.     | Testing disaster recovery plans.                 |

---

## **Troubleshooting**
| **Issue**                          | **Diagnostic Query**                                                                 | **Resolution**                                                                 |
|-------------------------------------|--------------------------------------------------------------------------------------|--------------------------------------------------------------------------------|
| Missing VM metrics                  | `SELECT COUNT(*) FROM vm_metrics WHERE vm_id = 'i-123456' AND timestamp > now() - 24h;` | Verify guest agent is running; check cloud provider API permissions.            |
| High host CPU pressure              | `SELECT host_id, SUM(value) FROM vm_metrics WHERE metric_name = 'cpu.usage' GROUP BY host_id;` | Migrate VMs to another host; add vCPUs to overloaded hosts.                   |
| Log retention issues                | `SELECT COUNT(*) FROM vm_logs WHERE log_level = 'ERROR' AND timestamp < now() - 7d;` | Increase log retention in the aggregator (e.g., ELK or Azure Monitor).        |
| Alert noise                         | Review alert rules for **false positives** (e.g., transient spikes).                | Tune thresholds or use statistical methods (e.g., P95).                         |

---
**Note:** Adjust queries for your database (e.g., replace `InfluxQL` with `PromQL` for Prometheus). For cloud providers, leverage their native APIs (e.g., AWS CloudWatch Metrics SQL).