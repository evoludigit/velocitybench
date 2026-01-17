---
# **[Pattern] Observability-Driven Development (ODD) – Reference Guide**

---

## **1. Overview**
Observability-Driven Development (ODD) is a **application delivery pattern** that embeds observability practices (metrics, logs, traces, and events) early and holistically into software design, development, and deployment. Unlike traditional approaches where observability is tacked on post-launch, ODD ensures that systems are inherently **monitorable, debuggable, and self-documenting** throughout their lifecycle. This reduces blind spots, accelerates troubleshooting, and shifts debugging from reactive "firefighting" to proactive, data-backed decision-making.

ODD aligns with DevOps and SRE principles by fostering **collaboration between engineers, operators, and developers** to build resilient systems. The pattern emphasizes **outcome-driven instrumentation**—collecting data not just for monitoring, but to answer critical questions about system health, performance, and user impact. By integrating observability into CI/CD pipelines, teams can validate system behavior in staging environments, reducing risk in production rollouts.

---

## **2. Schema Reference**
ODD relies on three foundational observability pillars, each with key **data models, collection methods, and tools**. Use this schema to design and implement observability systems.

| **Pillar**       | **Data Type**               | **Key Metrics/Events**                          | **Collection Methods**                          | **Common Tools/Standards**                     | **ODD-Specific Implementation Notes**                          |
|-------------------|-----------------------------|--------------------------------------------------|--------------------------------------------------|------------------------------------------------|---------------------------------------------------------------|
| **Metrics**       | Numeric time-series data     | - Latency (e.g., `response_time_ms`)            | SDKs (Prometheus), agents (Datadog, New Relic)    | OpenTelemetry, Prometheus (metrics)           | Define **business-centric metrics** (e.g., "95th percentile error rate for user A") alongside infrastructure metrics. Use **histograms** for distribution analysis. |
|                   |                             | - Error rates (e.g., `5xx_errors_total`)         | Instrumentation libraries (e.g., OpenTelemetry)   | Grafana (visualization)                       | Align metrics with **SLOs/SLIs** (e.g., "P99 latency < 500ms"). |
|                   |                             | - Throughput (e.g., `requests_per_second`)       | Embedded agents (Dynatrace)                     | Thanos, Cortex (long-term storage)            | Avoid vanity metrics; focus on **user-facing outcomes** (e.g., "orders processed successfully"). |
| **Logs**          | Textual records with context | - Structured logs (e.g., `{timestamp, level, trace_id, user_id}`) | Centralized log shippers (Fluentd, Fluent Bit)   | Loki, ELK Stack (Elasticsearch, Logstash)    | **Replace unstructured logs** with JSON-structured logs for queryability. Include **trace IDs** for correlation. |
|                   |                             | - Audit trails (e.g., "user_authentication_failed") | Application instrumentation (e.g., `logging` module) | Datadog, Honeycomb                            | Log **business events** (e.g., "payment_processed_success") alongside technical events. |
| **Traces**        | Distributed request graphs   | - Span attributes (e.g., `service_name`, `operation`) | SDKs (OpenTelemetry, Jaeger, Zipkin)            | Jaeger UI, OpenTelemetry Collector            | **Instrument critical paths** (e.g., payment flows) with spans. Use **propagation headers** (e.g., `traceparent`) for cross-service tracing. |
|                   |                             | - Latency breakdowns (e.g., `db_query_time`)      | Auto-instrumentation (e.g., Datadog APM)        | Tempo (trace storage)                          | Correlate traces with **metrics/logs** (e.g., link a slow span to a 5xx error log). |
| **Events**        | High-cardinality signals     | - User actions (e.g., `session_started`)         | Event pipelines (Kafka, NATS)                   | M3, TimescaleDB                                | Use for **real-time alerts** (e.g., "unexpected drop in API calls"). |
|                   |                             | - System alerts (e.g., `disk_space_critical`)    | Custom scripts + brokers (e.g., RabbitMQ)         | Viktor (event store)                          | Design **event schemas** for future queries (e.g., "list all failed logins for admin users"). |

---

## **3. Query Examples**
ODD encourages **data-driven exploration** of system behavior. Below are practical query examples for each pillar, using tools like PromQL, LogQL, and Jaeger.

### **Metrics (PromQL)**
```sql
# High-cardinality error rate by service (ODD: correlate with SLOs)
sum(rate(http_requests_total{status=~"5.."}[5m])) by (service)
/ sum(rate(http_requests_total[5m])) by (service)

# Business metric: Failed payments (key for ODD)
increase(payment_processing_errors_total{status="failed"}[1h])
/ increase(payment_processing_attempts_total[1h])

# Histogram: Latency percentiles (ODD: tie to user impact)
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

### **Logs (Loki LogQL)**
```sql
# Users with failed logins (ODD: correlate with auth traces)
logfmt | json | {level="ERROR", event="auth_failed"}
| json | {user_id} | count by (user_id)

# Trace-linked logs (ODD: debug distributed failures)
{job="api-service"} | line_format "{{.trace_id}} {{.level}} {{.message}}"
| logfmt | json | {trace_id} | {level} | {message}
```

### **Traces (Jaeger Query)**
```sql
# Slowest RPC calls in payment service (ODD: identify bottlenecks)
service:payment-service | duration > 500ms | limit 10

# Correlate traces with logs (ODD: link trace_id to log entries)
service:payment-service | trace_id = "abc123..." | log | limit 5
```

### **Events (Kafka/Grafana)**
```sql
# Alert on sudden drop in user activity (ODD: detect anomalies early)
sum(rate(user_activity_events_total[1m])) by (user_segment) < 0.8 * avg_over_time(...)
```

---

## **4. Implementation Best Practices**
| **Category**               | **ODD Best Practice**                                                                 | **Tools/Techniques**                                                                 |
|----------------------------|---------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Design Phase**           | Instrument **before** coding (e.g., mock traces for APIs).                            | OpenTelemetry SDK stubs, contract tests.                                             |
| **Code Instrumentation**   | Use **auto-instrumentation** where possible; manually instrument **business logic**.  | OpenTelemetry auto-instrumentation + custom spans for critical flows.              |
| **Data Lifecycle**         | Retain **long-term metrics** (e.g., 6 months) for trend analysis; **short-term traces/logs** (1 week). | Prometheus + Thanos, Loki retention policies.                                      |
| **Alerting**               | Alert on **anomalies**, not thresholds alone.                                          | Mimir + Cortex for anomaly detection, PagerDuty for triage.                          |
| **CI/CD Integration**      | Run **observability validation** in staging (e.g., trace sampling rate).               | SLO dashboards in PR reviews, GitHub Actions checks.                                |
| **Security**               | Mask sensitive data (e.g., PII in logs).                                              | Dynamic data redaction (e.g., Datadog mask rules).                                 |
| **Cost Optimization**      | Sample **high-volume services** (e.g., 1% of traces) while capturing **critical paths**.| OpenTelemetry sampling strategies, cost dashboards.                                  |

---

## **5. Anti-Patterns**
| **Anti-Pattern**                     | **Why It Fails in ODD**                                                                 | **ODD Alternative**                                                                 |
|---------------------------------------|------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Instrumentation as an afterthought** | Leads to **"incomplete observability"**—missing critical paths.                          | **Design observability into requirements** (e.g., "This API must emit traces for X flows"). |
| **Vanity metrics**                    | Track **what’s easy to measure**, not what matters (e.g., "line-of-code complexity").    | **Focus on user outcomes** (e.g., "time-to-payment-success").                         |
| **Log dumping**                       | Unstructured logs are **impossible to query** for anomalies.                              | **Structured logs + schemas** (e.g., `{event: "order_created", user_id, status}`).|
| **Silos between teams**               | Devs instrument; Ops monitors; no shared context.                                       | **Collaborative observability** (e.g., shared SLOs in Confluence).                  |
| **Over-collecting**                   | High cardinality metrics/traces **break performance** and inflate costs.                | **Sampling + targeted instrumentation** (e.g., trace only payment flows).          |

---

## **6. Related Patterns**
| **Pattern**                          | **Relationship to ODD**                                                                 | **When to Combine**                                                                 |
|---------------------------------------|------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **[Site Reliability Engineering (SRE)]** | ODD provides the **data** SRE uses to define SLIs/SLOs and error budgets.               | Use ODD metrics to **validate SRE targets** (e.g., "99.9% availability via trace-based error rates"). |
| **[Chaos Engineering]**                | ODD helps **instrument** chaos experiments to measure resilience.                       | Instrument **failure modes** (e.g., "latency injection impact on user flows").      |
| **[Feature Flags]**                   | ODD can **track flag usage** and its impact on metrics/events.                          | Use traces to **correlate flag toggles** with performance anomalies.                |
| **[Infrastructure as Code (IaC)]**   | ODD observability configs (e.g., Prometheus rules) should be **version-controlled**.   | Define observability in Terraform/CloudFormation (e.g., "deploy Prometheus alerts alongside the app"). |
| **[Canary Releases]**                 | ODD helps **compare canary vs. production metrics** in real time.                       | Use **traces** to compare canary path latency with production.                      |

---

## **7. Getting Started Checklist**
1. **Define observability goals**: Align with business outcomes (e.g., "reduce payment failures by 20%").
2. **Instrument critical paths**: Start with **end-to-end flows** (e.g., user checkout).
3. **Adopt OpenTelemetry**: Standardize collection and reduce vendor lock-in.
4. **Integrate into CI/CD**: Add **observability gates** (e.g., "no 5xx errors in staging").
5. **Train teams**: Run **observability workshops** to correlate metrics/traces/logs.
6. **Iterate**: Use **retrospectives** to refine instrumentation based on debugging pain points.

---
**Key Resource**: [OpenTelemetry Documentation](https://opentelemetry.io/docs/) | [Google SLOs Guide](https://sre.google/sre-book/metrics/)