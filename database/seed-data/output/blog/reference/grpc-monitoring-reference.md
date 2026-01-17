# **[Pattern] gRPC Monitoring Reference Guide**

---

## **Overview**
The **gRPC Monitoring** pattern provides a structured approach to observing gRPC service health, performance, and usage. gRPC is a modern RPC framework optimized for high performance and efficiency, making monitoring essential for detecting anomalies (e.g., latency spikes, errors, or traffic bottlenecks). This guide details key metrics, implementation best practices, and tooling integration to ensure reliable, observable gRPC services.

Key benefits include:
- **Proactive issue detection** via real-time telemetry.
- **Performance optimization** by analyzing latency, throughput, and error rates.
- **Compliance and debugging** with standardized metrics.

---

## **Implementation Details**

### **1. Core Monitoring Concepts**
Monitoring gRPC involves tracking metrics grouped under **Dimensions** and **Metrics**:

| **Dimension**       | **Description**                                                                 | **Example Values**                     |
|----------------------|---------------------------------------------------------------------------------|-----------------------------------------|
| `Service`            | The gRPC service name (e.g., `UserService`).                                   | `UserService`, `OrderService`           |
| `Method`             | The gRPC method called (e.g., `GetUser`).                                       | `GetUser`, `CreateOrder`                |
| `Peer`               | The client/peer address (e.g., `IP:port`).                                    | `192.168.1.1:50051`                     |
| `StatusCode`         | gRPC status codes (e.g., `OK`, `UNAVAILABLE`).                               | `OK`, `INTERNAL`, `UNAUTHENTICATED`     |

---

### **2. Key Metrics**
Monitor these **mandatory** and **recommended** metrics:

| **Metric**               | **Description**                                                                 | **Type**          | **Unit**       | **Tags**                          |
|--------------------------|---------------------------------------------------------------------------------|-------------------|----------------|------------------------------------|
| `grpc_server_started_total` | Count of gRPC server start events (useful for uptime tracking).                 | Counter           | `{}`            | `service`, `version`              |
| `grpc_server_handled_total` | Total number of gRPC method calls (successful or failed).                        | Counter           | `{}`            | `service`, `method`, `status_code` |
| `grpc_server_msg_received_total` | Incoming message volume (for streaming/RPC calls).                              | Counter           | `{}`            | `service`, `method`               |
| `grpc_server_msg_sent_total`   | Outgoing message volume (for streaming/RPC calls).                              | Counter           | `{}`            | `service`, `method`               |
| `grpc_server_latency_microseconds` | Latency distribution (e.g., P99, P95) of RPC calls.                            | Histogram         | microseconds    | `service`, `method`, `status_code` |
| `grpc_server_handling_seconds`  | Time spent processing a request (excluding network time).                       | Histogram         | seconds         | `service`, `method`               |
| `grpc_client_started_total`     | Client-initiated gRPC calls (mirrors server-side `grpc_server_handled_total`).   | Counter           | `{}`            | `service`, `method`, `status_code` |

---

### **3. Protocol Buffers (protobuf) Schema**
Define metrics in a `.proto` schema for consistency. Example:

```protobuf
syntax = "proto3";

message GrpcMetric {
  string name = 1;  // e.g., "grpc_server_handled_total"
  double value = 2;
  map<string, string> tags = 3;  // Key-value pairs (e.g., `service="UserService"`)
  string counter_type = 4;       // "counter" or "histogram"
  map<string, double> histogram_buckets = 5;  // For latencies (e.g., P99=100)
}
```

---

## **Schema Reference**
Use the following table to track metrics in your monitoring system:

| **Metric Name**                     | **Type**       | **Description**                                  | **Tags Required**                     |
|-------------------------------------|----------------|--------------------------------------------------|----------------------------------------|
| `grpc_server_handled_total`         | Counter        | Total RPC calls (success/failure).               | `service`, `method`, `status_code`    |
| `grpc_client_sent_rpc_total`        | Counter        | Client-initiated RPCs (mirrors server metrics).   | `service`, `method`                   |
| `grpc_server_latency_microseconds`  | Histogram      | RPC latency distribution (P50, P99).            | `service`, `method`                   |
| `grpc_server_received_bytes_total`  | Counter        | Bytes received per RPC.                          | `service`, `method`                   |
| `grpc_server_sent_bytes_total`      | Counter        | Bytes sent per RPC.                              | `service`, `method`                   |

---

## **Tooling Support**
### **1. Built-in gRPC Metrics**
- **gRPC Go/Protobuf**: Enable server-side metrics via [`grpc-stats`](https://pkg.go.dev/google.golang.org/grpc/stats) or [`grpc-prometheus`](https://github.com/grpc-ecosystem/grpc-prometheus).
- **Java**: Use [`grpc-prometheus`](https://github.com/grpc-ecosystem/grpc-prometheus) for Prometheus integration.
- **Python**: [`grpcio`](https://grpc.io/docs/languages/python/) supports metrics via `grpc_services`.

### **2. Prometheus Integration**
Example Prometheus scrape config:
```yaml
scrape_configs:
  - job_name: "grpc_server"
    metrics_path: "/metrics"
    static_configs:
      - targets: ["localhost:8080"]  # gRPC server with Prometheus exporter
```

### **3. OpenTelemetry (OTel)**
For distributed tracing:
```go
// Example: OTel instrumentation for gRPC
import (
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/trace"
)

func init() {
    provider := trace.NewTracerProvider()
    otel.SetTracerProvider(provider)
    grpcServer := grpc.NewServer(
        grpc.StatsHandler(&stats.Tracer{Trace: trace.NewTracer("grpc-server")}),
    )
}
```

---

## **Query Examples**
### **1. Prometheus Queries**
- **Total RPC calls (last 5 minutes):**
  ```promql
  sum(rate(grpc_server_handled_total[5m])) by (service, method)
  ```
- **Error rate (status != OK):**
  ```promql
  sum(rate(grpc_server_handled_total{status_code!="OK"}[5m]))
    /
  sum(rate(grpc_server_handled_total[5m]))
  ```
- **P99 latency (microseconds):**
  ```promql
  histogram_quantile(0.99, sum(rate(grpc_server_latency_microseconds_bucket[5m]))
    by (le, service, method))
  ```

### **2. Grafana Dashboards**
- **Key panels**:
  - **RPC calls/s** (counter rate).
  - **Latency distribution** (histogram).
  - **Error rate** (fraction of non-`OK` calls).
  - **Throughput by service**.

---

## **Related Patterns**
1. **[Distributed Tracing]** – Correlate gRPC spans across services.
2. **[Metrics Aggregation]** – Use Prometheus/Federation to centralize metrics.
3. **[gRPC Load Testing]** – Validate performance under load (e.g., with [`k6`](https://k6.io/)).
4. **[Service Mesh Integration]** – Istio/Envoy injects metrics/tracing automatically.
5. **[Alerting Rules]** – Define alerts for anomalies (e.g., `grpc_server_latency_microseconds > 1000`).

---

## **Best Practices**
1. **Tag Consistency**: Use uniform tags (`service`, `method`, `peer`) across all metrics.
2. **Sampling**: For high-throughput services, sample latencies to reduce overhead.
3. **Retention**: Store metrics for at least **1 week** (longer for billing/audit).
4. **Alert Thresholds**:
   - **Latency**: P99 > 2x baseline.
   - **Error Rate**: > 1% non-`OK` calls.
5. **Security**: Restrict metric access via Prometheus role-based access control (RBAC).

---
**Example Alert Rule (Prometheus):**
```yaml
groups:
- name: grpc-alerts
  rules:
  - alert: HighLatency
    expr: histogram_quantile(0.99, rate(grpc_server_latency_microseconds_bucket[5m])) > 2000
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High gRPC latency for {{ $labels.method }} ({{ $labels.service }})"
```