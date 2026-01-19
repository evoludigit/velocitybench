# **[Pattern] Virtual-Machines Observability – Reference Guide**

---

## **Overview**
This pattern defines observability best practices for monitoring, collecting, and analyzing telemetry data from **virtual machines (VMs)**—including metrics, logs, events, and configurations—in hybrid or cloud-native environments. It ensures visibility into VM performance, resource utilization, guest OS health, and hypervisor interactions. Key objectives include:
- **Proactive incident detection** (e.g., CPU throttling, disk latency).
- **Resource optimization** (e.g., right-sizing, cost allocation).
- **Compliance tracking** (e.g., security patches, audit logs).
- **Root-cause analysis** (e.g., correlating logs across VMs and hosts).

This guide covers telemetry collection, schema conventions, query patterns, and integration considerations for **VMware ESXi, Microsoft Hyper-V, and KVM/QEMU**.

---

## **Schema Reference**
Standardize telemetry data with these schema definitions (adapt for your vendor/tool):

| **Category**               | **Field Name**               | **Type**       | **Description**                                                                 | **Example Values**                          |
|----------------------------|------------------------------|----------------|---------------------------------------------------------------------------------|---------------------------------------------|
| **Metadata**               | `vm_id`                      | string         | Unique identifier per VM (e.g., host UUID + VM name).                             | `vm-1234567890abcdef0`                      |
|                            | `vm_name`                    | string         | Readable name assigned to the VM.                                                | `web-app-prod-01`                          |
|                            | `hypervisor`                 | enum           | Underlying hypervisor type.                                                       | `VMware`, `Hyper-V`, `KVM`                 |
|                            | `host_id`                    | string         | ID of the host managing the VM.                                                   | `host-90abcdef12345678`                     |
|                            | `cloud_provider`             | string         | Cloud environment (if applicable).                                               | `AWS EC2`, `Azure VM`, `On-Prem`           |
|                            | `os_type`                    | enum           | Guest OS type.                                                                   | `Linux`, `Windows`, `Unknown`               |
|                            | `os_version`                 | string         | OS version (e.g., kernel/build number).                                          | `Ubuntu 22.04 LTS`, `Windows Server 2022`  |
| **Performance Metrics**     | `cpu_utilization`            | float          | CPU usage percentage (1-minute avg).                                             | `75.3`                                      |
|                            | `memory_usage`               | float          | RAM consumption (GB).                                                            | `3.2`                                       |
|                            | `disk_io_latency`            | float          | Disk read/write latency (ms).                                                     | `15.4`                                      |
|                            | `network_rx_tx`              | object         | Network bandwidth (bytes/sec) per interface.                                     | `{ "eth0": { "rx": 1024000, "tx": 456000 } }` |
| **Events**                 | `event_type`                 | enum           | Type of event (e.g., `vm_start`, `snapshot_create`).                             | `cpu_throttled`, `disk_full`               |
|                            | `event_timestamp`            | timestamp      | When the event occurred.                                                          | `2023-10-15T14:30:00Z`                     |
|                            | `severity`                   | enum           | Event criticality.                                                                | `critical`, `warning`, `info`               |
|                            | `resource_id`                | string         | Affected resource (e.g., VM disk).                                               | `disk-vdi-12345`                            |
| **Logs**                   | `log_source`                 | string         | Source system (e.g., `guest_agent`, `hypervisor`).                              | `windows_event_log`, `syslog`               |
|                            | `log_message`                | string         | Raw log entry.                                                                   | `"Failed to connect to database at 3:45 PM"` |
|                            | `log_level`                  | enum           | Log verbosity.                                                                   | `debug`, `info`, `error`                    |
| **Configurations**         | `snapshot_count`             | integer        | Number of active snapshots.                                                      | `3`                                         |
|                            | `security_patches`           | array          | Installed patches (CVEs).                                                        | `[ "CVE-2023-1234", "CVE-2023-5678" ]`     |
|                            | `vm_settings`                | object         | VM-specific configurations (e.g., memory limit).                                 | `{ "memory_limit_mb": 8192, "cpu_cores": 4 }` |

---
**Vendor-Specific Notes:**
- **VMware Tools**: Use `vmtoolsd` for guest agent metrics.
- **Hyper-V**: Leverage **Enhanced Session Transport (EST)** for integration.
- **KVM/QEMU**: Monitor via `virsh` or cloud-init logs.

---

## **Query Examples**
### **1. CPU Throttling Alert**
**Objective**: Detect VMs exceeding CPU limits for 5+ minutes.
**Query** (using PromQL for Prometheus):
```sql
rate(vm_cpu_utilization{hypervisor="VMware"}[5m])
  > 95
  and on(vm_id) group_left(hypervisor)
  vm_info{hypervisor="VMware"}
```
**Output**:
```json
[
  { "vm_id": "vm-1234", "vm_name": "db-server", "utilization": 98.2 },
  { "vm_id": "vm-5678", "vm_name": "app-tier", "utilization": 102.1 }
]
```

### **2. Disk Full Alert**
**Query** (using Elasticsearch DSL):
```json
GET /vm_observability/_search
{
  "query": {
    "bool": {
      "must": [
        { "match": { "event_type": "disk_full" } },
        { "range": { "event_timestamp": { "gte": "now-1h" } } }
      ]
    }
  },
  "aggs": {
    "affected_vms": { "terms": { "field": "vm_name.keyword" } }
  }
}
```

### **3. Patch Compliance Audit**
**Query** (SQL-inspired for a time-series DB):
```sql
SELECT vm_name, COUNT(DISTINCT patch_id) AS missing_patches
FROM vm_configurations
WHERE os_type = 'Linux'
  AND patch_id NOT IN (
    SELECT patch_id FROM security_compliance
    WHERE status = 'installed'
  )
GROUP BY vm_name
HAVING COUNT(DISTINCT patch_id) > 0
ORDER BY missing_patches DESC;
```

### **4. Correlate Network + CPU Spikes**
**Objective**: Find VMs with network spikes *and* high CPU during peak hours.
**Query** (using Grafana Explorer):
```sql
(
  sum by(vm_id) (rate(network_rx_tx_bytes{interface="eth0"}[1h]))
    > quantile(0.95, sum by(vm_id) (rate(network_rx_tx_bytes{interface="eth0"}[1h])))
)
and
(
  avg by(vm_id) (vm_cpu_utilization[1h])
    > 80
)
```

---

## **Implementation Details**
### **1. Data Collection**
| **Source**               | **Method**                          | **Frequency**       | **Tools**                                  |
|--------------------------|-------------------------------------|---------------------|--------------------------------------------|
| Hypervisor Metrics       | VMware vCenter API / Hyper-V Manager | 15s–60s             | Prometheus, Datadog Agent                  |
| Guest Agent             | VMware Tools / Hyper-V Integration  | Real-time           | Fluentd, Logstash                          |
| Cloud Provider          | AWS Instance Monitoring / Azure VM Insights | 5m–1m       | AWS CloudWatch, Azure Monitor              |
| Logs                    | Syslog / Windows Event Forwarding    | Continuous          | ELK Stack, Splunk                         |
| Configurations          | API Polling (e.g., `virsh` for KVM) | Daily               | Terraform, Ansible                        |

### **2. Processing Pipeline**
```
[Sources] → [Normalization Layer] → [Storage] → [Alerting/Visualization]
    ↓
[VMware Tools] → [Fluentd] → [Kafka] → [Elasticsearch]
    ↓
[Prometheus] ← [Hyper-V Metrics] → [Grafana]
```

### **3. Alerting Strategies**
- **Anomaly Detection**: Use ML models (e.g., Prometheus Anomaly Detection) for baseline shifts.
- **SLA Violation**: Alert if `memory_usage > allocated_memory * 0.95` for >10 minutes.
- **Compliance**: Trigger alerts for unpatched servers (e.g., `security_patches` array empty).

### **4. Storage Optimization**
- **Metrics**: Time-series DB (e.g., InfluxDB, Prometheus) for high-cardinality data.
- **Logs**: Cold storage (e.g., S3 + Glacier) with tiered retention (7 days hot, 1 year cold).

---

## **Related Patterns**
1. **[Host Observability]** – Extend VM metrics to hypervisor health (e.g., host CPU, memory).
2. **[Container Observability]** – Use VMs as hosts for Kubernetes clusters (monitor via `cAdvisor`).
3. **[Security Observability]** – Integrate with **SIEM** tools for VM-specific threats (e.g., CVE scanning).
4. **[Cost Observability]** – Allocate cloud VM costs to teams using **FinOps** metrics.
5. **[Configuration as Code]** – Manage VM observability via **Infrastructure as Code (IaC)** (e.g., Terraform modules for Prometheus exporters).

---
**References**:
- [VMware vSphere Monitoring Guide](https://docs.vmware.com/)
- [Azure VM Observability Best Practices](https://learn.microsoft.com/azure/virtual-machines/)
- [Prometheus VM Metrics Exporters](https://github.com/prometheus-community)

---
**Last Updated**: [Insert Date]
**Version**: 1.2