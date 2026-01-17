# **[Pattern] Logging Approaches: Reference Guide**
*Best practices, configurations, and implementation strategies for structured logging in distributed systems.*

---

## **Overview**
The **Logging Approaches** pattern defines standardized ways to capture, structure, and process logs across components in distributed systems. Well-designed logging ensures observability, troubleshooting efficiency, and compliance with audit requirements. This guide covers **log formats, collection strategies, retention policies, and integration patterns** to optimize log management.

Key benefits:
- **Consistency** – Uniform log structure across services.
- **Efficiency** – Reduced noise via structured filtering and sampling.
- **Scalability** – Optimized log ingestion and storage.
- **Regulatory Compliance** – Audit trails for security and governance.

---

## **1. Key Concepts**
| **Term**               | **Definition**                                                                 |
|-------------------------|---------------------------------------------------------------------------------|
| **Structured Logging**  | Logs formatted as key-value pairs (e.g., JSON) for machine-parsability.         |
| **Log Levels**         | Severity classifications (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL).        |
| **Log Sampling**       | Selectively logging a subset of events to reduce volume.                       |
| **Log Sharding**       | Splitting logs by source/resource (e.g., `app=order-service`, `env=prod`).     |
| **Retention Policy**   | Rules for log storage duration (e.g., 30 days hot storage, 1 year cold storage).|
| **Fluentd/Loki/Promtail** | Open-source tools for log collection, parsing, and querying.                  |

---

## **2. Schema Reference**
### **Standardized Log Structure**
Use this schema for consistency across services. Adjust fields as needed per use case.

| **Field**          | **Type**   | **Description**                                                                 | **Example Values**                          |
|--------------------|------------|-------------------------------------------------------------------------------|--------------------------------------------|
| `timestamp`        | ISO 8601   | Event occurrence time (UTC).                                                  | `2024-05-20T12:34:56.123Z`                |
| `service`          | String     | Service/component name.                                                       | `order-service`, `payment-gateway`          |
| `level`            | String     | Severity level (mandatory).                                                   | `ERROR`, `WARNING`                         |
| `message`          | String     | Human-readable log content.                                                   | `User payment failed: invalid card`        |
| `trace_id`         | UUID       | Correlation ID for distributed tracing.                                       | `123e4567-e89b-12d3-a456-426614174000`    |
| `span_id`          | UUID       | Sub-operation ID (if applicable).                                             | `987f654e-321c-4321-9876-543216547890`    |
| `metadata`         | Object     | Free-form key-value pairs (e.g., user, error details).                        | `{ "user_id": "123", "error_code": "500" }`|
| `env`              | String     | Deployment environment.                                                       | `prod`, `staging`, `dev`                    |

---
### **Example JSON Log Entry**
```json
{
  "timestamp": "2024-05-20T12:34:56.123Z",
  "service": "order-service",
  "level": "ERROR",
  "message": "Payment declined",
  "trace_id": "123e4567-e89b-12d3-a456-426614174000",
  "metadata": {
    "user_id": "123",
    "order_id": "ord_abc123",
    "error_code": "402",
    "payment_gateway": "stripe"
  },
  "env": "prod"
}
```

---

## **3. Implementation Approaches**
### **A. Log Collection Strategies**
| **Approach**               | **Use Case**                                  | **Tools**                          | **Pros**                                  | **Cons**                                  |
|----------------------------|-----------------------------------------------|------------------------------------|------------------------------------------|------------------------------------------|
| **Agent-Based (Fluentd/Fluent Bit)** | High-volume logs from multiple sources.      | Fluentd, Fluent Bit, Logstash.      | Real-time, efficient.                    | Higher operational overhead.             |
| **API-Based (HTTP/Protobuf)** | Lightweight logging from edge services.      | OpenTelemetry Collector, Loki.     | Minimal resource usage.                 | Latency if network is slow.              |
| **File Tailing**           | Simple local log aggregation.                | Logstash, rsyslog.                 | Low cost, easy setup.                    | Not scalable for distributed systems.    |
| **Serverless (AWS CloudWatch, GCP Logging)** | Serverless/app engine logs.               | AWS Lambda, GCP Functions.         | Auto-scaling, integrated monitoring.     | Vendor lock-in; cost at scale.           |

---
### **B. Log Processing Pipelines**
1. **Produced** → Application logs to stdout/stderr.
2. **Forwarded** → Agent/HTTP endpoint (e.g., Fluentd → Loki).
3. **Parsed** → Structured via regex/grok patterns (e.g., `\%{TIMESTAMP_ISO8601} \[\%{LOGLEVEL}\]\%{SPACE}\%{GREEDYDATA}`).
4. **Stored** → Centralized system (e.g., Loki, Elasticsearch, S3).
5. **Queried** → Tools like Grafana, Promtail, or Kibana.

---
### **C. Retention Policies**
| **Tier**       | **Duration**  | **Storage Medium**       | **Use Case**                          |
|----------------|--------------|--------------------------|---------------------------------------|
| **Hot**        | 30–90 days   | SSD, fast storage        | Real-time debugging.                  |
| **Warm**       | 3–12 months  | HDD, slower storage      | Incident analysis.                    |
| **Cold**       | 1+ years     | S3 Glacier, tape storage | Compliance/audit.                     |

**Example Policy (Loki):**
```yaml
retention_period: 30d
retention_rolling_policy: {
  "max_rolling_days": 365,
  "replication_factor": 1
}
```

---

## **4. Query Examples**
### **Tool: Loki (By Grafana)**
**Query:** Filter `ERROR` logs from `order-service` in the last 15 minutes.
```graphql
{ job="order-service" }
| filter level="ERROR"
| logfmt
| line_format "{{.timestamp}} {{.level}} {{.message}}"
| timeshift(15m)
```

**Output:**
```
2024-05-20T12:34:56Z ERROR User payment failed: invalid card
```

---
### **Tool: Elasticsearch**
**Query (Kibana Discovery):**
```json
{
  "query": {
    "bool": {
      "must": [
        { "term": { "level.keyword": "ERROR" } },
        { "range": { "timestamp": { "gte": "now-15m" } } }
      ]
    }
  }
}
```

---
### **Tool: CloudWatch (AWS)**
**CLI Query:**
```bash
aws logs filter-log-events \
  --log-group-name "/aws/lambda/order-service" \
  --filter-pattern "ERROR" \
  --start-time 1716232096000 \
  --end-time 1716235696000
```

---

## **5. Best Practices**
1. **Standardize Fields:**
   - Use `service`, `level`, and `timestamp` universally.
   - Avoid hardcoding dynamic values (e.g., IP addresses).

2. **Optimize Volume:**
   - **Sample logs** for `DEBUG` levels (e.g., 1% sampling).
   - **Drop redundant logs** (e.g., HTTP 200 OK without metadata).

3. **Security:**
   - Mask sensitive data (e.g., PII, tokens) via redaction tools.
   - Encrypt logs in transit (TLS) and at rest.

4. **Performance:**
   - Batch log streams (e.g., Fluentd buffer `chunk_limit_size=2M`).
   - Use compression (e.g., `gzip`) for long-term storage.

5. **Alerting:**
   - Set up anomaly detection (e.g., Loki alerts for spike in `ERROR` logs).
   - Example rule (Grafana Alerting):
     ```yaml
     for: 5m
     condition: rate(loki_logs_count{level="ERROR"}[5m]) > 100
     annotations:
       summary: "High error rate in {{ $labels.service }}"
     ```

---

## **6. Related Patterns**
| **Pattern**                     | **Connection to Logging Approaches**                                                                 |
|----------------------------------|-----------------------------------------------------------------------------------------------------|
| **[Distributed Tracing](...)**  | Logs + traces combine for end-to-end request analysis.                                             |
| **[Metric Aggregation](...)**   | Logs inform custom metrics (e.g., `log_count{level="ERROR"}`).                                  |
| **[Observability Pipeline]**     | Logs, metrics, and traces feed into unified dashboards (Grafana, Prometheus).                |
| **[Secure Configuration]**      | Logging secrets (e.g., API keys) requires dynamic masking.                                       |
| **[Circuit Breaker]**           | Log failures to detect cascading failures in microservices.                                    |

---
## **7. Troubleshooting**
| **Issue**                          | **Diagnosis**                                                                 | **Solution**                                                                 |
|-------------------------------------|--------------------------------------------------------------------------------|--------------------------------------------------------------------------------|
| Logs missing in central store       | Check agent connectivity (Fluentd `status` endpoint).                         | Verify network policies, retries, and buffer limits.                          |
| High latency in log ingestion      | Monitor `ingestion_time` in Loki/Elasticsearch.                              | Scale collectors, increase batch size, or use a faster storage tier.          |
| Schema drift across services        | Compare log samples via `jq` or Grafana.                                      | Enforce logging libraries (e.g., `json-logfmt` in Go).                        |
| Alert fatigue from too many logs   | Analyze `level=WARNING` volume spikes.                                       | Adjust sampling or filter noise (e.g., exclude `INFO` logs).                 |

---
## **8. Further Reading**
- **[OpenTelemetry Logs Specification](https://github.com/open-telemetry/specification/blob/main/specification/logs/api.md)**
- **[Loki Documentation](https://grafana.com/docs/loki/latest/)**
- **[Fluentd Configuration Guide](https://docs.fluentd.org/v1.0/articles/quick-start)**

---
**Last Updated:** `2024-05-20` | **Version:** `1.2`