# **[Pattern] Containers Monitoring: Reference Guide**

---

## **Overview**
Containers Monitoring is a **critical operational pattern** for tracking runtime behavior, resource utilization, and performance of containerized applications. Unlike traditional monitoring, containerized environments require specialized tools to capture ephemeral, dynamically scaling workloads. This guide covers key concepts, implementation schemas, sample queries, and related patterns to ensure visibility into containerized infrastructure—**from orchestration layers (e.g., Kubernetes) to individual microservices**.

Key use cases include:
- Detecting resource bottlenecks (CPU/memory/disk) in microservices.
- Managing auto-scaling events and pod health.
- Logging and tracing distributed requests across containers.
- Alerting on misconfigurations (e.g., excessive restarts).
- Debugging orchestration failures (e.g., node affinity violations).

---

## **Implementation Details**

### **Key Concepts**
| **Concept**               | **Description**                                                                                                                                                                                                 | **Example Tools/Techniques**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------|
| **Container Metrics**     | Real-time data on CPU, memory, network, storage metrics from containers (e.g., Prometheus metrics).                                                                                                          | Prometheus, cAdvisor, Datadog Agent                                                                           |
| **Orchestration Metrics** | Insights into Kubernetes/Docker Swarm state (pods, nodes, deployments, events).                                                                                                                               | Kubernetes API, Metrics Server, OpenTelemetry                                                                 |
| **Logging Aggregation**   | Centralized logs from containers for troubleshooting (e.g., Docker logs, structured JSON).                                                                                                                   | ELK Stack, Loki, Fluent Bit                                                                                 |
| **Tracing**               | End-to-end request tracing across containers (latency, dependencies).                                                                                                                                          | Jaeger, OpenTelemetry, Zipkin                                                                              |
| **Custom Business Metrics** | Application-specific telemetry (e.g., user sessions, API call volumes) emitted by containers.                                                                                                                  | Custom instrumentation (Prometheus Exporters, OpenTelemetry SDKs)                                            |
| **Resource Quotas**       | Enforcement of CPU/memory limits per container (preventing noisy neighbors).                                                                                                                                  | Kubernetes `ResourceRequests/Limits`, Docker `--memory` flags                                                 |
| **Health Checks**         | Liveness/readiness probes to monitor container health and trigger restarts.                                                                                                                                     | Kubernetes `LivenessProbe`, `ReadinessProbe`, Docker `HEALTHCHECK`                                             |

---

## **Schema Reference**

### **1. Container Metrics Schema (Prometheus Format)**
| **Metric Type**       | **Name**                          | **Description**                                                                               | **Unit**         | **Example Value**       |
|-----------------------|-----------------------------------|-----------------------------------------------------------------------------------------------|------------------|-------------------------|
| **CPU**               | `container_cpu_usage_seconds_total` | Total CPU time consumed by the container.                                                     | Seconds          | `30.5`                  |
|                       | `container_cpu_usage_rate`        | CPU usage rate (normalized to 1 core).                                                       | (per second)     | `0.75` (75% of 1 core) |
| **Memory**            | `container_memory_working_set_bytes` | Resident memory usage.                                                                        | Bytes            | `1.2e9` (1.2 GB)       |
|                       | `container_memory_max_usage_bytes` | Peak memory usage since last restart.                                                         | Bytes            | `1.5e9` (1.5 GB)       |
| **Network**           | `container_network_receive_bytes_total` | Incoming network traffic.                                                                     | Bytes            | `4500000`               |
|                       | `container_network_transmit_bytes_total` | Outgoing network traffic.                                                                     | Bytes            | `6000000`               |
| **Disk**              | `container_fs_writes_total`       | Disk writes by the container.                                                                   | Bytes            | `2.3e6`                 |
| **Restarts**          | `container_restart_total`         | Number of container restarts.                                                                 | Count            | `2`                     |
| **Liveness**          | `kube_pod_container_status_restarts` | Restarts due to liveness probe failures.                                                     | Count            | `1`                     |

---
### **2. Orchestration Metrics Schema (Kubernetes)**
| **Metric Type**       | **Name**                          | **Description**                                                                               | **Unit**         | **Example Value**       |
|-----------------------|-----------------------------------|-----------------------------------------------------------------------------------------------|------------------|-------------------------|
| **Pod State**         | `kube_pod_status_phase{phase="Running"}` | Current phase of pods (Running/Failed/Pending).                                           | Count            | `42`                    |
| **Node Usage**        | `kube_node_status_allocatable{resource="memory"}` | Available resources on nodes.                                                               | Bytes/CPU Core   | `8e9` (8 GB)            |
| **Deployment Rollouts** | `kube_deployment_status_replicas_available` | Successful pod replications during deployments.                                            | Count            | `5/5`                   |
| **Event Alerts**      | `kube_event_total`                | Kubernetes event counts (e.g., `FailedScheduling`, `CrashLoopBackOff`).                        | Count            | `15` (last 5m)          |
| **Auto-Scaling**      | `kube_hpa_status_current_replicas` | Current replicas after HPA scaling.                                                         | Count            | `3`                     |

---
### **3. Logs Schema (Structured JSON)**
```json
{
  "timestamp": "2023-10-01T12:00:00Z",
  "container": {
    "name": "web-app",
    "pod": "web-app-7fcd4d5f8-abc12",
    "namespace": "default"
  },
  "level": "ERROR",
  "message": "Database connection timeout",
  "metadata": {
    "source": "app/logs",
    "trace_id": "abc123-xyz456"
  }
}
```

---
### **4. Tracing Schema (OpenTelemetry)**
| **Span Attribute**    | **Description**                                                                               |
|-----------------------|-----------------------------------------------------------------------------------------------|
| `span.kind`           | Client/server/Producer/Consumer.                                                             |
| `http.method`         | HTTP request method (e.g., `POST`).                                                          |
| `http.url`            | Request URL.                                                                                |
| `container.id`        | Container ID (e.g., `docker://abc123`).                                                      |
| `service.name`        | Service name (e.g., `user-service`).                                                        |
| `latency`             | End-to-end latency (ms).                                                                     |

---

## **Query Examples**

### **1. CPU Throttling Alert (Prometheus)**
```promql
sum by (pod) (
  rate(container_cpu_usage_seconds_total{image!="", namespace!=""}[5m])
  /
  container_spec_cpu_shares{image!="", namespace!=""}
) * 100 > 90  # Alert if CPU usage exceeds 90% of allocated shares
```
**Alert Condition:**
- **Severity:** Critical
- **Summary:** `High CPU Throttling in Pod {pod}`
- **Description:** `Pod {pod} CPU usage is {value}% over its limit.`

---

### **2. Unhealthy Pods (Kubernetes Metrics)**
```promql
kube_pod_status_phase{phase="Failed"} > 0
```
**Alert Rule:**
```
- name: FailedPods
  expr: kube_pod_status_phase{phase="Failed"} > 0
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Pod failed: {{ $labels.pod }}"
```

---

### **3. Logs: Errors in `nginx` Pods**
**Loki Query:**
```gql
{container="nginx"} | logfmt | error("message")
```
**Filter for:**
- Last 30 minutes.
- Only `ERROR`/`CRITICAL` logs.

---

### **4. End-to-End Latency (OpenTelemetry)**
**Query (Jaeger/Zipkin):**
```
service_name: "payment-service"
op: "ProcessOrder"
duration > 500ms
```
**Visualization:**
- **Trace:** Show requests flowing from `user-service` → `payment-service` → `db-service`.
- **Heatmap:** Highlight slow spans (e.g., DB queries).

---

### **5. Resource Quota Violation (Kubernetes)**
**Audit Rule:**
```yaml
apiVersion: audit.k8s.io/v1beta1
kind: Policy
rules:
- level: Warning
  resources:
  - group: ""
    resources: ["pods"]
  verbs: ["create"]
  omitStages:
  - "RequestReceived"
  fields:
  - resourceRequestCPU
  - resourceRequestMemory
  - resourceLimitCPU
  - resourceLimitMemory
  auditFilterPolicy:
    rule: |
      level: Admission
      when:
        request.object.limits > request.object.requests
```

---

## **Related Patterns**

| **Pattern**                          | **Description**                                                                                                                                                                                                 | **When to Use**                                                                                          |
|--------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| **[Auto-Scaling Containers](link)**   | Dynamically adjust container resources based on metrics (e.g., CPU/memory).                                                                                                                                       | Handling unpredictable workloads (e.g., e-commerce spikes).                                             |
| **[Service Mesh Monitoring](link)**  | Monitoring for service meshes (Istio/Linkerd) with observability for sidecars, mTLS, and retries.                                                                                                                   | Multi-service architectures with complex traffic patterns.                                             |
| **[Multi-Cluster Management](link)** | Observing containerized apps across multiple Kubernetes clusters.                                                                                                                                               | Global deployments with regional failover.                                                          |
| **[Security Hardening](link)**       | Scan containers for vulnerabilities (CVE) and enforce runtime security (e.g., gVisor).                                                                                                                               | Compliance (e.g., SOC2, PCI-DSS) or zero-trust environments.                                            |
| **[Chaos Engineering](link)**         | Intentionally inject failures (e.g., pod kills) to test resilience.                                                                                                                                                 | Proactively validate SLOs/SLs during deployments.                                                       |

---

## **Best Practices**
1. **Aggregate Signals:**
   - Correlate metrics (CPU), logs, and traces to diagnose root causes (e.g., `5xx` errors + high latency).
   - Use **SLOs** (e.g., "99% of requests < 500ms") to set thresholds.

2. **Labeling Strategy:**
   - Standardize labels (e.g., `pod_name`, `service`, `environment`) for efficient querying.
   - Example: `kube_pod_status_phase{namespace="prod", app="frontend"}`.

3. **Cost Optimization:**
   - Right-size containers using metrics (avoid over-provisioning).
   - Monitor **requests/limits** vs. actual usage (e.g., `container_cpu_usage_seconds_total`).

4. **Tooling Stack:**
   - **Metrics:** Prometheus + Grafana.
   - **Logs:** Loki + Tempo (for traces).
   - **Orchestration:** Kubernetes Metrics Server + OpenTelemetry Collector.

5. **Incident Response:**
   - Define **RTOs/RPOs** for containerized systems.
   - Use **golden signals** (latency, traffic, errors, saturation) for proactive alerts.

---
**See also:**
- [Kubernetes Metrics API Docs](https://kubernetes.io/docs/concepts/cluster-administration/monitoring/)
- [OpenTelemetry Container Scraping](https://opentelemetry.io/docs/collector/configuration/)