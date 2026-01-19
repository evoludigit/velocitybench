# **[Pattern] Websockets Monitoring – Reference Guide**

---
## **Overview**
Websockets Monitoring is a pattern designed to **track, analyze, and troubleshoot** real-time bidirectional communication between clients and servers over WebSocket connections. This pattern ensures high availability, latency optimization, and early detection of connection issues (e.g., dropped messages, reconnections, or protocol violations).

Unlike traditional HTTP monitoring (which is request-based), WebSocket monitoring focuses on **persistent connections**, message flow, and continuous state validation. This guide covers key concepts, implementation schemas, query patterns, and integration considerations for observability pipelines.

---

## **Implementation Details**

### **Core Components**
| Component          | Description                                                                                     |
|--------------------|-------------------------------------------------------------------------------------------------|
| **WebSocket Client** | Manages bidirectional communication via `ws://` or `wss://` protocol.                          |
| **Monitoring Agent** | Intercepts WebSocket traffic (e.g., via proxy, middleware, or browser extensions).          |
| **Telemetry Pipeline** | Collects metrics (latency, message count, reconnections) and logs (errors, payloads).          |
| **Alerting System** | Triggers alerts for anomalies (e.g., high latency, failed handshakes, or unsent messages).    |
| **Storage Backend** | Stores raw data for long-term analysis (e.g., Prometheus, OpenSearch, or custom databases).   |

### **Key Metrics to Monitor**
| Metric Category       | Metrics                                                                                       | Example Use Case                                  |
|-----------------------|-----------------------------------------------------------------------------------------------|---------------------------------------------------|
| **Connection Health** | `connection_open`, `connection_close`, `handshake_timeout`, `reconnection_attempts`          | Detect failed connections or slow handshakes.    |
| **Latency**           | `ping_latency`, `message_processing_time`, `round_trip_time`                                | Optimize real-time performance.                  |
| **Message Flow**      | `messages_sent`, `messages_received`, `messages_dropped`, `message_size`                  | Identify bottlenecks or protocol violations.     |
| **Error Tracking**    | `protocol_errors`, `payload_validation_failures`, `connection_refused`                   | Debug WebSocket-specific issues.                 |
| **Throughput**        | `messages_per_second`, `bytes_per_second`, `connection_throughput`                         | Scale infrastructure based on traffic.           |

---

## **Schema Reference**
Below are standardized schemas for collecting and querying WebSocket metrics. Adapt these to your monitoring stack (e.g., Prometheus, Loki, or custom systems).

### **1. Connection Metrics (Prometheus Format)**
```promql
# Connection state
ws_connection_open{service="chat_app", environment="prod"} 1
ws_connection_close{reason="timeout", pod="user-123"} 0

# Latency (seconds)
ws_ping_latency{endpoint="/updates"} 0.123

# Reconnection attempts
ws_reconnection_attempts_total{service="multiplayer"} 42
```

### **2. Message Flow (Structured Logging Example)**
```json
{
  "timestamp": "2024-05-15T12:00:00Z",
  "service": "order_processing",
  "endpoint": "/transactions",
  "message_id": "msg-456",
  "type": "received",
  "size_bytes": 1024,
  "processing_ms": 85,
  "status": "success"
}
```

### **3. Alert Conditions**
| Alert Rule Name          | Condition                                                                                     | Severity  |
|--------------------------|-----------------------------------------------------------------------------------------------|-----------|
| `HighReconnectionRate`   | `rate(ws_reconnection_attempts_total[5m]) > 5`                                             | Critical  |
| `PingTimeout`            | `ws_ping_latency > 3` (for >1 minute)                                                        | Warning   |
| `MessageDrops`           | `rate(ws_messages_dropped_total[1m]) > 0.1% of total`                                      | Critical  |
| `PayloadValidationFail`  | `ws_payload_validation_failures_total > 0`                                                   | Error     |

---

## **Query Examples**
### **1. Detecting Unusual Reconnection Patterns (Grafana/PromQL)**
```promql
# Alert if reconnections spike >3x baseline
rate(ws_reconnection_attempts_total[5m])
  > (avg_over_time(rate(ws_reconnection_attempts_total[30d])) * 3)
```

### **2. Calculating Message Throughput (Per Endpoint)**
```promql
# Messages per second by endpoint
rate(ws_messages_received_total{endpoint=~".+"}[1m])
  by (endpoint)
```

### **3. Identifying Lagging Connections (Loki/Grafana)**
```logql
# Filter slow message processing (>2s)
{service="game_server"} | json | processing_ms > 2000
```

### **4. Correlating Errors with Payload Size (Custom Query)**
```sql
-- SQL-like pseudoquery for OpenSearch
SELECT
  endpoint,
  AVG(size_bytes) as avg_payload_size,
  COUNT(*) as error_count
FROM ws_errors
WHERE timestamp > now() - 1d
GROUP BY endpoint
HAVING error_count > 10;
```

---

## **Querying with SDKs**
Most monitoring tools offer SDKs to instrument WebSocket traffic. Examples:

#### **Node.js (with `ws` library)**
```javascript
const WebSocket = require('ws');
const client = new WebSocket('wss://api.example.com');

client.on('open', () => {
  // Track connection metrics
  trackConnection('open', { endpoint: '/chat' });
});

client.on('message', (data) => {
  // Track message flow
  trackMessage('received', {
    endpoint: '/chat',
    size: data.length,
    timestamp: new Date().toISOString()
  });
});
```

#### **Python (with `websockets` library)**
```python
import asyncio
import websockets

async def monitor_socket():
    async with websockets.connect("wss://api.example.com") as ws:
        while True:
            data = await ws.recv()
            # Log message metrics
            log_metrics('received', {'size': len(data)})
```

---

## **Related Patterns**
| Pattern                     | Description                                                                                     | When to Use                                                                 |
|-----------------------------|-------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **HTTP Rate Limiting**      | Mitigate abuse by throttling WebSocket connections when combined with HTTP APIs.               | High-traffic real-time apps (e.g., gaming, live dashboards).               |
| **Connection Pooling**      | Reuse WebSocket connections for efficiency (e.g., in microservices).                         | Server-side architectures with many clients.                                |
| **Graceful Degradation**    | Fall back to HTTP Long-Polling if WebSocket fails (e.g., due to firewalls).                   | Legacy systems or networks blocking WebSockets.                             |
| **Protocol Validation**     | Ensure messages adhere to a schema (e.g., Avro, JSON Schema) before processing.                 | Mission-critical apps where correctness is critical.                       |
| **A/B Testing**             | Compare WebSocket message formats or latency optimizations.                                    | Experimenting with protocol changes or feature rollouts.                   |

---

## **Best Practices**
1. **Label Metrics** Use consistent labels (e.g., `service`, `environment`, `endpoint`) for queries.
2. **Sample Logs** Avoid logging full payloads; focus on metadata (size, timestamps, errors).
3. **Set Alert Thresholds** Define baselines for reconnections, latency, and message drops.
4. **Replay Debugging** Keep raw WebSocket traffic logs for post-mortem analysis.
5. **Secure Connections** Monitor `wss://` traffic only; raw `ws://` is vulnerable.
6. **Optimize Sampling** For high-throughput services, sample messages to reduce storage costs.

---
## **Troubleshooting**
| Issue                          | Diagnosis Query                                                                 | Solution                                                                 |
|---------------------------------|---------------------------------------------------------------------------------|---------------------------------------------------------------------------|
| High reconnection rate          | `rate(ws_reconnection_attempts_total[5m])` > threshold                          | Check for network latency, firewall rules, or client-side issues.         |
| Dropped messages                | `ws_messages_dropped_total` increasing                                           | Increase buffer size or reduce message frequency.                         |
| Ping latency spikes             | `histogram_quantile(0.95, ws_ping_latency)` > 1s                                | Optimize server-side processing or scale horizontally.                     |
| Protocol errors                 | `ws_protocol_errors_total` by `error_type`                                       | Validate payload schemas or update client/server libraries.               |

---
**References:**
- [WebSocket RFC 6455](https://datatracker.ietf.org/doc/html/rfc6455)
- [Prometheus WebSocket Exporter](https://github.com/prometheus-community/websockets_exporter)
- [OpenTelemetry Protocol (OTLP) for WebSockets](https://opentelemetry.io/docs/specs/otlp/)