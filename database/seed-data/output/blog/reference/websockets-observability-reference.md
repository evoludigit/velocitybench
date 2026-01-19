# **[Pattern] Websockets Observability Reference Guide**

---

## **Overview**
Websockets Observability ensures real-time monitoring, troubleshooting, and optimization of WebSocket-based applications. Unlike traditional HTTP-based observability, WebSockets require deep inspection of persistent, bidirectional connections to capture latency, message volume, errors, and resource consumption. This guide covers key metrics, schema definitions, query examples, and integration strategies to implement comprehensive observability for WebSocket applications.

---

## **Key Concepts**
1. **Real-Time Metrics**
   - Track connection state (open/close), message throughput, and latency.
   - Example: `ws_connection_duration_seconds` (histogram) to measure P99 response times.

2. **Error Tracking**
   - Capture disconnected messages, timeouts, and protocol violations (e.g., malformed frames).
   - Example: `ws_error_count` (counter) with labels for error type (e.g., "timeout", "parsing_error").

3. **Traffic Analysis**
   - Monitor message frequency, payload size, and message types (e.g., "heartbeat", "command").
   - Example: `ws_messages_received_bytes` (counter) to analyze bandwidth usage.

4. **Resource Pressure**
   - Detect bottlenecks in CPU, memory, or connection limits (e.g., max_connections exceeded).
   - Example: `ws_server_memory_usage_mb` (gauge).

5. **Client-Side Metrics**
   - Include client-side latency (e.g., time from message send to server acknowledgment).
   - Example: `ws_client_ping_pong_latency_ms` (histogram).

---

## **Schema Reference**
| **Metric Name**               | **Type**       | **Description**                                      | **Labels (Key-Value)**                     | **Unit**               |
|-------------------------------|----------------|------------------------------------------------------|--------------------------------------------|------------------------|
| `ws_connections_open`          | Counter        | Total active WebSocket connections.                 | `service: <service_name>`, `namespace: <namespace>` | `{}`                   |
| `ws_connection_duration`       | Histogram      | Time between connection open and close.            | `status: <success/failure>`, `version: <proto_version>` | Seconds               |
| `ws_messages_sent`            | Counter        | Total messages sent (server ↔ client).              | `direction: <in/out>`, `message_type: <type>` | `{}`                   |
| `ws_messages_size_bytes`      | Counter        | Payload size of messages sent.                      | `direction: <in/out>`, `message_type: <type>`| Bytes                  |
| `ws_errors_total`              | Counter        | Total WebSocket errors (e.g., disconnects, timeouts).| `error_type: <type>`, `reason: <reason>`    | `{}`                   |
| `ws_ping_pong_latency`        | Histogram      | Time for ping/pong handshake.                       | `direction: <client/server>`              | Milliseconds          |
| `ws_server_cpu_usage_percent` | Gauge          | CPU usage by WebSocket server.                       | `pod: <pod_name>`, `instance: <instance>`   | `%`                    |
| `ws_backpressure_dropped`     | Counter        | Messages dropped due to queue overflow.            | `queue: <queue_name>`, `reason: <reason>`  | `{}`                   |

*Notes:*
- Use **histograms** for latency/throughput to support percentiles (e.g., P90).
- Include **labels** for multi-dimensional analysis (e.g., by service, namespace, or error type).
- For client-side metrics, include `client_id` or `user_agent` for correlation.

---

## **Query Examples**
### **1. Active Connections by Service**
```sql
# Prometheus
sum by (service) (ws_connections_open) > 0

# MetricsQL (Thanos/Grafana)
approximate_histogram_quantile(0.95, ws_connection_duration_seconds{})
```

### **2. Error Rate for Disconnections**
```sql
# Alert if >1% of connections fail
rate(ws_errors_total{error_type="disconnect"}[1m])
/ rate(ws_connections_open[1m]) > 0.01
```

### **3. Message Throughput by Type**
```sql
# Top 5 message types by volume
topk(5, sum by (message_type) (rate(ws_messages_sent[5m])))
```

### **4. Ping-Pong Latency SLA Violation**
```sql
# Alert if P99 latency exceeds 500ms
histogram_quantile(0.99, ws_ping_pong_latency{direction="client"}) > 500
```

### **5. Backpressure Detection**
```sql
# Drop rate >1000 messages/minute
rate(ws_backpressure_dropped[1m]) > 1000
```

---

## **Implementation Details**
### **Server-Side Metrics**
**Libraries/Tools:**
- **Prometheus:** Expose metrics via `/metrics` endpoint.
  ```go
  // Example in Go (net/http)
  wsServer.RegisterMetrics(metrics.WsConnectionOpened())
  ```
- **OpenTelemetry:** Trace WebSocket sessions with context propagation.
  ```python
  # Python (OTel)
  tracer = opentelemetry.trace.get_tracer(__name__)
  with tracer.start_as_current_span("ws_session"):
      # Handle WebSocket events
  ```

**Key Code Patterns:**
1. **Connection Lifecycle Hooks:**
   ```javascript
   // Node.js (Socket.IO)
   io.on("connection", (socket) => {
     const startTime = Date.now();
     socket.on("disconnect", () => {
       recordDuration("ws_connection_duration", startTime);
     });
   });
   ```
2. **Error Handling:**
   ```java
   // Java (Jetty WebSocket)
   @OnError
   public void onError(Throwable cause) {
     metrics.increment(
       "ws_errors_total",
       Map.of("error_type", "exception", "reason", cause.getMessage())
     );
   }
   ```

### **Client-Side Metrics**
- **Browser:** Use [WebSocket Performance API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket/performance) or custom instrumentation.
  ```javascript
  // Track send/acknowledgment latency
  const start = performance.now();
  socket.send(message);
  socket.onmessage = (e) => {
    const latency = performance.now() - start;
    recordMetric("ws_client_latency", latency);
  };
  ```
- **Mobile (Flutter):** Integrate with [`prometheus_client`](https://pub.dev/packages/prometheus_client) for local metrics collection.

### **Storage & Alerting**
- **Prometheus:** Store metrics for 1–7 days; alert on anomalies (e.g., sudden disconnect spikes).
- **OpenSearch/Grafana:** Visualize message types and latency distributions.
- **SLOs:** Define SLIs like:
  - **"99% of messages delivered within 200ms."**
  - **"<0.1% error rate for connections."**

---

## **Common Pitfalls & Mitigations**
| **Pitfall**                  | **Mitigation**                                  |
|-------------------------------|-------------------------------------------------|
| **High Cardinality Labels**  | Limit labels to essential dimensions (e.g., `service`, `message_type`). |
| **Missing Client Metrics**   | Use client-side libraries or SDKs (e.g., OpenTelemetry JS). |
| **No Latency Baselines**      | Track P50/P90/P99 over time to detect regressions. |
| **Ignoring Backpressure**    | Set alerts for `ws_backpressure_dropped` spikes. |
| **Protocol Errors Unnoticed**| Validate frames (e.g., mask checks for client-side) and log violations. |

---

## **Related Patterns**
1. **[Distributed Tracing](https://www.cncf.io/blog/2022/04/05/distributed-tracing-guide/)**
   - Correlate WebSocket events with downstream services (e.g., databases) using OpenTelemetry traces.
2. **[Rate Limiting](https://cloud.google.com/blog/products/management-tools/rate-limiting-best-practices)**
   - Combine with WebSocket observability to detect throttling (e.g., `ws_messages_dropped`).
3. **[Chaos Engineering](https://chaoss.github.io/)**
   - Test resilience by simulating WebSocket failures (e.g., random disconnections) and measure recovery metrics.
4. **[Service Mesh Observability](https://istio.io/latest/docs/concepts/traffic-management/)**
   - Use Istio’s mTLS and metrics to secure and observe WebSocket traffic in microservices.
5. **[Log Aggregation](https://www.elastic.co/guide/en/observability/current/logs-overview.html)**
   - Log WebSocket payloads (sanitized) for debugging (e.g., `ws_message_log{type: "command", payload: "..."}`).

---

## **Tools & Ecosystem**
| **Category**               | **Tools**                                  |
|----------------------------|--------------------------------------------|
| **Metrics Collection**     | Prometheus, Datadog, New Relic, OpenTelemetry |
| **Visualization**          | Grafana, Kibana, InfluxDB                  |
| **Alerting**               | Alertmanager, PagerDuty, Opsgenie          |
| **Client-Side SDKs**       | OpenTelemetry JS, Prometheus JS Client    |
| **Server Libraries**       | Prometheus Go Client, Spring Boot Actuator |

---
**Next Steps:**
1. Instrument your WebSocket server/client with the schema above.
2. Set up dashboards for `ws_connection_duration` and `ws_errors_total`.
3. Define SLOs and alert on anomalies (e.g., 99th percentile > 300ms).