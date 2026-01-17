# **[Pattern] Hybrid Observability: Reference Guide**

## **Overview**
Hybrid Observability is an architectural pattern that combines **distributed tracing, infrastructure monitoring, application metrics, and logs** into a unified visibility layer. Unlike traditional siloed observability tools (e.g., APM for traces, Prometheus for metrics, ELK for logs), this pattern centralizes telemetry data from **on-premises, cloud-native, and edge environments** while maintaining granularity for debugging, performance optimization, and SLO/SLI analysis.

Hybrid Observability is ideal for teams with **multi-cloud, microservices, or legacy systems**, where a single tool cannot provide complete insights. It leverages:
- **Instrumentation**: OpenTelemetry (OTel), custom SDKs, or existing agents.
- **Data Collection**: Distributed tracing (Jaeger, OpenTelemetry Collector), metric scrapers (Prometheus, StatsD), and log shippers (Fluentd, Loki).
- **Correlation**: Context propagation (trace IDs, baggage headers) to link traces, metrics, and logs.
- **Analysis**: Aggregated dashboards, anomaly detection, and root-cause analysis across environments.

---

## **Schema Reference**
Below is a structured schema defining core components of Hybrid Observability:

| **Component**          | **Purpose**                                                                 | **Key Attributes**                                                                 | **Example Tools**                          |
|------------------------|-----------------------------------------------------------------------------|------------------------------------------------------------------------------------|--------------------------------------------|
| **Instrumentation Layer** | Injects metrics, traces, and logs into applications.                        | - Language SDKs (Go, Python, Java)<br>- Auto-instrumentation<br>- Manual annotations | OpenTelemetry, Datadog Agent              |
| **Collector Agents**     | Aggregates, processes, and forwards telemetry to backends.                  | - Batch processing<br>- Filtering/transforming data<br>- Protocol support (OTLP, HTTP) | OpenTelemetry Collector, Fluent Bit        |
| **Telemetry Storage**   | Persists and indexes data for querying.                                      | - Retention policies<br>- Indexing (time-series vs. document)<br>- Query capabilities | TimescaleDB, Elasticsearch, Jaeger storage |
| **Correlation Context**  | Ensures related traces, metrics, and logs are linked across systems.        | - Trace IDs<br>- Span IDs<br>- Baggage headers<br>- Custom key-value pairs       | W3C Trace Context Protocol                |
| **Dashboarding Layer**   | Visualizes aggregated and correlated data.                                   | - Multi-pane views<br>- Alert thresholds<br>- Custom widgets                      | Grafana, Kibana                            |
| **Alerting & Notifications** | Triggers alerts based on thresholds or anomalies.                          | - Policing rules<br>- Integration (Slack, PagerDuty)<br>- Noise reduction           | Prometheus Alertmanager, Datadog Alerts    |
| **Security & Access**   | Controls access to telemetry data.                                         | - RBAC<br>- Audit logging<br>- Data masking for PII                                | HashiCorp Vault, OpenTelemetry Security    |
| **AOT Integration**     | Correlates observability data with AOT (Application Observability Toolchain) | - Linking traces to CI/CD pipelines<br>- Debugging in dev environments               | GitLab Observability, Jira Correlation     |

---

## **Key Implementation Details**

### **1. Instrumentation Strategies**
Choose between:
- **OpenTelemetry (Recommended)**: Universal SDK for metrics, traces, and logs with vendor-agnostic support.
  ```bash
  # Example: Java OpenTelemetry SDK
  OpenTelemetrySdk sdk = OpenTelemetrySdk.builder()
      .setTracerProvider(TracerProvider.builder()
          .addSpanProcessor(SimpleSpanProcessor.create(consoleProcessor()))
          .build())
      .build();
  ```
- **Vendor-Specific SDKs**: Simplifies setup but locks you into an ecosystem (e.g., Datadog, New Relic).

### **2. Data Collection Pipeline**
A typical pipeline involves:
1. **Agent Deployment**: Deploy OpenTelemetry Collector or vendor agents (e.g., Datadog Agent) on:
   - Kubernetes pods (`sidecar` or `daemonset`)
   - VMs (via config management tools like Ansible)
   - Edge devices (lightweight collectors)

2. **Protocol Support**: Ensure collectors support:
   - **OTLP (gRPC/HTTP)** for OpenTelemetry data.
   - **HTTP/StatsD** for legacy metrics.
   - **Syslog/FLB** for logs.

3. **Processing Rules**: Apply transformations (e.g., sampling, anonymization) in the collector:
   ```yaml
   # OpenTelemetry Collector config (sample.yaml)
   processors:
     batch:
       timeout: 1s
   exporters:
     logging:
       logLevel: debug
   service:
     pipelines:
       traces:
         receivers: [otlp]
         processors: [batch]
         exporters: [logging]
   ```

4. **Backends**:
   - **Traces**: Jaeger, OpenTelemetry Collector (with memory storage), or cloud providers (AWS X-Ray, Azure Monitor).
   - **Metrics**: Prometheus, TimescaleDB, or cloud-native (GCP Metrics, AWS CloudWatch).
   - **Logs**: Loki, Elasticsearch, or cloud log services (AWS CloudWatch Logs).

### **3. Correlation & Context Propagation**
- **Trace IDs**: Auto-injected into spans, metrics, and logs via OpenTelemetry’s `TraceContext`.
  ```json
  // Example log entry with trace context
  {
    "message": "User checkout failed",
    "trace_id": "a1b2c3d4e5f6-7890-4567-89ab-cdef01234567",
    "span_id": "1234-5678-9abc-def0"
  }
  ```
- **Baggage Headers**: Attach custom key-value pairs (e.g., `user_id`, `session_token`) for debugging:
  ```go
  // Go: Adding baggage to a span
  ctx := otel.GetTextMapPropagator().Fieldpropagate(ctx, baggage.HeaderCarrier(&baggage.HeaderCarrier{
      Header: map[string]string{"baggage": "user_id=12345"},
  }))
  ```

### **4. Querying Correlated Data**
Use **cross-tool queries** to link telemetry:
- **Grafana**: Combine Prometheus metrics + Loki logs + Jaeger traces in dashboards.
- **OpenTelemetry Query API**: Parse traces/metrics via OpenTelemetry Collector:
  ```sql
  -- Pseudo-query: Find slow API calls with errors
  SELECT duration, error_count
  FROM traces
  WHERE http.route = "/checkout"
  GROUP BY duration
  ORDER BY duration DESC
  LIMIT 10;
  ```
- **ELK Stack**: Use `traceparent` headers in Kibana to correlate logs/traces.

### **5. Performance Considerations**
- **Sampling**:
  - Trace sampling (e.g., 1% of spans) to reduce volume.
  - Metric sampling (e.g., Prometheus `rate()` instead of `sum()`).
- **Storage Optimization**:
  - Compress logs (e.g., fluent-bit `gzip` plugin).
  - Use time-series databases (TimescaleDB) for metrics.
- **Latency**:
  - Prefer gRPC over HTTP for OTLP exports.
  - Cache frequently accessed traces (e.g., Redis).

### **6. Security & Compliance**
- **Data Masking**: Redact PII in logs/metrics (e.g., OpenTelemetry `Resource.ID` masking).
- **Encryption**: Use TLS for OTLP exports and secrets management (Vault) for API keys.
- **Audit Logging**: Track who accesses sensitive data (e.g., Jaeger’s `auth` plugin).

---

## **Query Examples**

### **1. Finding Bottlenecks in a Microservice**
**Scenario**: Identify slow API calls in `/payments` with `status_code=500`.
**Tools**: Jaeger + Prometheus + Loki.

**Queries**:
1. **Trace Query (Jaeger)**:
   ```sql
   service = "payment-service" AND http.route = "/payments" AND error = true
   ```
2. **Metric Query (Prometheus)**:
   ```promql
   rate(http_requests_total{status="500",route="/payments"}[5m])
   ```
3. **Log Query (Loki)**:
   ```logql
   {job="payment-service"} |= "checkout failed" AND status="500"
   ```
**Correlation**: Export `trace_id` from Jaeger to filter logs in Loki.

---

### **2. Anomaly Detection in Multi-Cloud**
**Scenario**: Detect spikes in `latency_p99` for `db-connection-pool` across AWS/GCP.

**Tools**: TimescaleDB + OpenTelemetry Collector.

**Query**:
```sql
SELECT
  bucket,
  p99_latency,
  COUNT(*) as request_count
FROM db_metrics
WHERE service = 'db-connection-pool'
  AND cloud_provider IN ('aws', 'gcp')
GROUP BY bucket, p99_latency
ORDER BY p99_latency DESC
LIMIT 10;
```
**Alert Rule** (Prometheus):
```yaml
- alert: HighLatencyDB
  expr: rate(db_latency_p99[5m]) > 100ms
  for: 5m
  labels:
    severity: critical
```

---

### **3. Debugging a Failed Deployment**
**Scenario**: Identify regressions after a Kubernetes rollout.

**Tools**: OpenTelemetry + GitLab Observability.

**Steps**:
1. **Compare Traces**: Query traces from `main` vs. `dev` branches (using `git_revision` in Resource Attributes).
2. **Log Correlation**: Filter logs for `deployment=rollback` and link to traces via `trace_id`.
3. **Metric Baseline**: Compare `error_rate` before/after deployment (using `deployment_version` label).

**Query (OpenTelemetry Query API)**:
```sql
-- Find traces with high duration post-deployment
SELECT
  duration,
  error_count,
  deployment_version
FROM traces
WHERE deployment_version = "v2.1.0"
  AND duration > 500ms
ORDER BY duration DESC;
```

---

## **Related Patterns**

| **Pattern**               | **Description**                                                                 | **When to Use**                                  |
|---------------------------|-------------------------------------------------------------------------------|--------------------------------------------------|
| **Centralized Logging**   | Aggregates logs from all environments into a searchable store (e.g., ELK).     | Teams needing log analysis without tool sprawl.   |
| **Service Mesh Observability** | Integrates observability into Istio/Linkerd for service-to-service telemetry. | Kubernetes-native microservices.                 |
| **SLO-Based Alerting**    | Alerts on SLO violations (e.g., "99.9% availability") instead of raw metrics.  | SRE teams focused on reliability goals.          |
| **Edge Observability**    | Observes telemetry from IoT/edge devices with high latency constraints.        | Real-time systems (e.g., autonomous vehicles).    |
| **FinOps Observability**  | Correlates cloud costs with performance metrics (e.g., "Why did AWS Lambda costs spike?"). | Cloud finance teams.                          |
| **Chaos Engineering**     | Uses observability to detect failures introduced by chaos experiments.      | Testing resilience (e.g., Netflix Chaos Monkey). |

---

## **Getting Started Checklist**
1. **Assess Telemetry Gaps**:
   - Map current tools (e.g., "Using Prometheus for metrics but no traces").
   - Identify missing data (e.g., "No logs from edge devices").
2. **Adopt OpenTelemetry**:
   - Instrument critical services with OTel SDKs.
   - Deploy OpenTelemetry Collector for aggregation.
3. **Pilot Hybrid Setup**:
   - Start with one environment (e.g., staging) to validate correlation.
   - Use Grafana to prototype dashboards.
4. **Automate Correlation**:
   - Enforce trace IDs/baggage in logging frameworks (e.g., `logrus` hooks).
5. **Iterate**:
   - Adjust sampling rates based on volume.
   - Optimize storage costs (e.g., compress old logs).

---
**Resources**:
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Hybrid Observability Guide (Datadog)](https://docs.datadoghq.com/observability/hybrid/)
- [Grafana Template: Hybrid Observability](https://grafana.com/grafana/templates/)