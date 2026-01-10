# **[Pattern] Reference Guide: API Observability**

---

## **Overview**
API Observability is a **proactive monitoring and analysis framework** designed to track, diagnose, and optimize API performance, reliability, and security in real time. Unlike traditional logging or basic metrics, observability provides deep insights into the **end-to-end behavior** of APIs—from request handling to dependency interactions—across distributed systems. This pattern ensures developers, DevOps, and SREs can **detect anomalies, troubleshoot failures, and improve system resilience** by correlating raw event data with business context.

Key use cases include:
- **Performance tuning** (latency, throughput, error rates)
- **Fault detection** (rate limits, timeouts, dependency failures)
- **Security monitoring** (abuse, misuse, unauthorized access)
- **SLO/SLA compliance** (uptime, error budgets, SLI tracking)

By integrating **traces, metrics, logs, and contextual metadata**, API Observability bridges the gap between infrastructure observability and business outcomes, enabling **data-driven API improvements**.

---

## **Key Concepts & Schema Reference**

### **Core Components**
| **Component**       | **Description**                                                                 | **Example Data Sources**                          |
|----------------------|---------------------------------------------------------------------------------|--------------------------------------------------|
| **Metrics**          | Quantitative measurements (e.g., request counts, error rates, latency percentiles). | Prometheus, Datadog, New Relic metrics endpoints. |
| **Traces**           | End-to-end request flow with timestamps, spans (operations), and annotations.   | Jaeger, Zipkin, OpenTelemetry traces.           |
| **Logs**             | Structured or unstructured text logs from API servers, gateways, databases.      | ELK Stack, Loki, Cloud Logging.                  |
| **Contextual Data**  | Business-related attributes (e.g., user ID, API key, service version).         | Custom annotations, headers, or distributed context. |
| **Anomaly Detection**| AI/ML-based alerts for deviations (e.g., sudden traffic spikes, error bursts).    | Prometheus Alertmanager, Datadog Synthetics.     |
| **Dependency Graphs** | Visual representation of API interactions (e.g., microservices, databases).      | Grafana, Thanos, or custom dashboards.           |

---

### **Implementation Schema**
Below is a **standardized schema** for API observability data collection and analysis. Adapt fields to your stack.

#### **1. Metrics Schema (Time-Series)**
| Field               | Type      | Description                                                                 | Example Values                     |
|---------------------|-----------|-----------------------------------------------------------------------------|------------------------------------|
| `timestamp`         | ISO 8601  | When the metric was recorded.                                              | `2024-01-15T14:30:00.123Z`        |
| `service_name`      | String    | Name of the API/service emitting the metric.                                | `auth-service`, `user-service`     |
| `resource`          | String    | Endpoint or component (e.g., `/v1/users`, `DBConnection`).                  | `/v1/users/create`                |
| `metric_type`       | Enum      | Type of metric (`latency`, `error_rate`, `throughput`, `memory_usage`).     | `latency`                          |
| `value`             | Float     | Numeric value (e.g., latency in ms, error count).                          | `456.7`                            |
| `unit`              | String    | Measurement unit (`ms`, `req/sec`, `bytes`).                                 | `milliseconds`                     |
| `context`           | Object    | Key-value pairs for filtering (e.g., `user_id`, `api_key_hash`).            | `{ "user_id": "123", "region": "us-east" }` |

---
#### **2. Trace Schema (Distributed Tracing)**
| Field               | Type      | Description                                                                 | Example Values                     |
|---------------------|-----------|-----------------------------------------------------------------------------|------------------------------------|
| `trace_id`          | UUID      | Unique identifier for the end-to-end request.                              | `a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6` |
| `span_id`           | UUID      | Unique identifier for a sub-operation (e.g., DB query).                    | `b2c3d4e5-f678-90g1-h2i3-j4k5l6m7` |
| `operation_name`    | String    | Name of the operation (e.g., `authenticate`, `fetch_user`).               | `authenticate:jwt_verify`          |
| `parent_span_id`    | UUID      | ID of the parent span (for hierarchical traces).                          | `a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6` |
| `start_time`        | ISO 8601  | When the span began.                                                        | `2024-01-15T14:30:00.123Z`        |
| `end_time`          | ISO 8601  | When the span completed.                                                   | `2024-01-15T14:30:00.567Z`        |
| `duration_ms`       | Float     | Time taken (in milliseconds).                                               | `444`                              |
| `attributes`        | Object    | Key-value pairs (e.g., `status_code`, `database:postgres`).                | `{ "status": 200, "db": "postgres" }` |
| `logs`              | Array     | Structured logs attached to the span.                                       | `[{ "timestamp": "...", "message": "Query executed" }]` |

---
#### **3. Log Schema (Structured Logging)**
| Field               | Type      | Description                                                                 | Example Values                     |
|---------------------|-----------|-----------------------------------------------------------------------------|------------------------------------|
| `log_id`            | String    | Unique ID for the log entry.                                                | `log-20240115-143000-abc123`      |
| `service_name`      | String    | Name of the service emitting the log.                                       | `user-service`                     |
| `timestamp`         | ISO 8601  | When the log was generated.                                                 | `2024-01-15T14:30:00.123Z`        |
| `level`             | Enum      | Severity (`INFO`, `WARN`, `ERROR`, `CRITICAL`).                            | `ERROR`                            |
| `message`           | String    | Human-readable log message.                                                 | `User authentication failed`       |
| `context`           | Object    | Structured metadata (e.g., `user_id`, `endpoint`).                         | `{ "user_id": "456", "endpoint": "/login" }` |
| `traces`            | Array     | References to related trace IDs.                                            | `[ "a1b2c3d4..." ]`                |

---

## **Implementation Steps**
### **1. Instrumentation**
Deploy **OpenTelemetry** or vendor-specific SDKs (e.g., Datadog, New Relic) to collect:
- **Metrics**: Auto-instrument HTTP endpoints (e.g., `latency_p50`, `status_code_count`).
- **Traces**: Wrap business logic with `Span` contexts (e.g., database calls, external APIs).
- **Logs**: Standardize log formats (e.g., JSON) with correlation IDs.

#### **Example: OpenTelemetry Instrumentation (Node.js)**
```javascript
import { NodeTracerProvider } from '@opentelemetry/sdk-trace-node';
import { HttpInstrumentation } from '@opentelemetry/instrumentation-http';

const provider = new NodeTracerProvider();
const instrumentation = new HttpInstrumentation();
provider.addSpanProcessor(new SimpleSpanProcessor());
provider.register();
instrumentation.enable();
```

---
### **2. Data Collection & Storage**
| **Component**       | **Tool Options**                          | **Use Case**                          |
|---------------------|-------------------------------------------|---------------------------------------|
| **Metrics**         | Prometheus, Grafana Loki, Datadog         | Short-term storage + aggregation.    |
| **Traces**          | Jaeger, Zipkin, OpenTelemetry Collector  | Long-term trace analysis.             |
| **Logs**            | ELK Stack, Loki, Cloud Logging           | Full log retention + searchability.   |
| **Alerting**        | Prometheus Alertmanager, Datadog Alerts  | Real-time anomaly detection.         |

---
### **3. Visualization & Analysis**
- **Dashboards**: Grafana (metrics + traces), Kibana (logs + traces).
- **Query Languages**:
  - **Metrics**: PromQL (`rate(http_requests_total[5m])`), Datadog Query Language.
  - **Traces**: Jaeger Query API (`/search?service=auth-service`).
  - **Logs**: ELK DSL (`GET /_search?query=level:ERROR`).
- **Correlation**: Use `trace_id` or `log_id` to link metrics, traces, and logs.

---
### **4. Alerting & Automation**
Configure alerts for:
- **Thresholds**: `error_rate > 1%` for 5 minutes.
- **Anomalies**: Sudden spikes in `latency_p99`.
- **Dependency Failures**: `db_connection_errors > 0`.
Use tools like:
- Prometheus Alertmanager.
- Datadog Monitor + PagerDuty integration.
- OpenTelemetry Exporter + Slack/Email.

---
## **Query Examples**
### **1. PromQL (Metrics)**
**Query**: Find APIs with `5xx` errors in the last 5 minutes.
```promql
sum(rate(http_requests_status_code_count{status=~"5.."}[5m])) by (service_name, resource)
```

**Query**: Latency percentiles for `/v1/users`.
```promql
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, resource))
```

---
### **2. Jaeger Trace Query (API Flags)**
**Endpoint**: `GET /api/traces?service=auth-service&start=1673888000&end=1673974400`
**Flags**:
- Filter by `status_code:401`:
  ```json
  {
    "tags": [
      { "key": "http.status_code", "values": ["401"] }
    ]
  }
  ```

---
### **3. ELK Log Query (Kibana DSL)**
**Query**: Find `ERROR` logs for `user-service` with `user_id` in the last hour.
```json
{
  "query": {
    "bool": {
      "must": [
        { "match": { "service_name": "user-service" } },
        { "match": { "level": "ERROR" } },
        { "range": { "@timestamp": { "gte": "now-1h" } } },
        { "term": { "context.user_id": "123" } }
      ]
    }
  }
}
```

---

## **Related Patterns**
1. **[Resilience Patterns](link)**
   - **Service Mesh (e.g., Istio, Linkerd)**: Integrates with observability for circuit breaking, retries, and traffic shifting.
   - **Bulkheads**: Isolate API failures by limiting concurrency.

2. **[Security Patterns](link)**
   - **API Rate Limiting**: Observe `429 Too Many Requests` metrics to detect abuse.
   - **JWT Validation Traces**: Trace failed `authenticate` spans for security incidents.

3. **[Performance Optimization](link)**
   - **Caching (Redis)**: Monitor `cache_hit_rate` metrics to justify caching layers.
   - **Async Processing**: Decouple APIs from slow dependencies (e.g., Kafka, SQS) and observe queue lag.

4. **[Distributed Tracing](link)**
   - **Context Propagation**: Use W3C Trace Context headers to correlate requests across services.
   - **Baggage**: Attach business context (e.g., `order_id`) to traces for debugging.

5. **[Infrastructure Observability](link)**
   - **Container Monitoring**: Correlate API traces with Kubernetes pod logs/metrics.
   - **Database Observability**: Track SQL query traces in PostgreSQL/Redis.

---

## **Best Practices**
1. **Standardize Naming**:
   - Use consistent `service_name` and `resource` labels across all observability tools.
2. **Sampling**:
   - Apply **adaptive sampling** (e.g., higher sampling for `5xx` errors) to reduce overhead.
3. **Retention**:
   - Metrics: 1 month (aggregated), Traces: 30 days, Logs: 7–30 days (compressed).
4. **SLOs**:
   - Define **API-level SLIs** (e.g., `p99 latency < 500ms`) and alert on deviations.
5. **Cost Optimization**:
   - Use **managed observability** (e.g., Datadog, New Relic) for vendor maintenance.
   - For self-hosted, prioritize **storage-efficient formats** (e.g., Protocol Buffers for traces).

---
## **Troubleshooting**
| **Issue**               | **Diagnostic Queries**                          | **Solution**                          |
|--------------------------|-------------------------------------------------|---------------------------------------|
| High latency             | `histogram_quantile(0.99, http_request_duration)` | Optimize DB queries, add caching.    |
| Spikes in errors         | `rate(http_requests_status_code_count{status=~"5.."}[1m])` | Check dependency health.            |
| Missing traces           | Verify OpenTelemetry SDK is deployed.           | Re-deploy instrumentation.            |
| Alert fatigue            | Tune thresholds (e.g., reduce `error_rate` sensitivity). | Adjust PromQL/PagerDuty rules.      |

---
## **Further Reading**
- [OpenTelemetry API Observability Guide](https://opentelemetry.io/docs/concepts/observability-api/)
- [Grafana API Observability Documentation](https://grafana.com/docs/grafana-cloud/observability/)
- [Datadog API Monitoring](https://docs.datadoghq.com/api/latest/api_overview/)