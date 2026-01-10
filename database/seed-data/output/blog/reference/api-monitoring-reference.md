---
**[Pattern] Reference Guide: API Monitoring**

---

## **1. Overview**
API Monitoring is a **practitioner-driven pattern** designed to ensure high availability, performance, and reliability of RESTful and GraphQL APIs by collecting, analyzing, and visualizing runtime metrics. This pattern provides a standardized approach to:
- **Proactively detect anomalies** (latency spikes, error rates, throttling).
- **Trends and capacity planning** through historical data aggregation.
- **Automate alerting** for SLA violations or security breaches.
- **Validate API contracts** (OpenAPI/Swagger) in production.

Common use cases include:
- Enterprise microservices tracking.
- Public-facing APIs (e.g., fintech, e-commerce).
- Hybrid cloud/on-prem deployments with distributed tracing.

---

## **2. Key Concepts**
| **Concept**               | **Definition**                                                                                                                                                                                                 | **Example Implementation**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|
| **Monitoring Metrics**    | Quantitative data (latency, requests/sec, HTTP status codes) collected via instrumentation.                                                                                                               | Prometheus metrics endpoint (`/metrics`): `http_request_duration_seconds{route="/users"}`                    |
| **Tracing**               | Correlation of requests across microservices using unique IDs (e.g., W3C Trace Context).                                                                                                                 | Distributed tracing with Jaeger: `trace_id=12345-67890` in HTTP headers.                                       |
| **Alerting Rules**        | Predefined conditions (e.g., `5xx errors > 1% for 5 min`) that trigger notifications.                                                                                                                   | Alertmanager (via Prometheus): `if rate(http_errors_total[5m]) > 0.01` then notify Slack.                     |
| **Synthetic Monitoring**  | Simulated API calls (e.g., 300 ms pings) to detect outages before users report them.                                                                                                                   | Tools like UptimeRobot or custom scripts checking `/healthz`.                                                   |
| **API Gateway Insights**  | Aggregated metrics (e.g., request rates, auth failures) exposed by API gateways (Kong, AWS API Gateway).                                                                                             | Kong `upstream_response_time` metric in `httpbin.org` logs.                                                  |
| **Log Correlation**       | Linking transaction logs (e.g., `db.query_failed`) to API responses using request/response IDs.                                                                                                       | ELK Stack: `request_id=abc123` in both API logs and database queries.                                         |
| **SLA Compliance**        | Mapping monitored metrics to predefined service-level agreements (e.g., 99.9% availability).                                                                                                               | Grafana dashboard with SLA breach alerts for `availability > 0.1%`.                                          |

---

## **3. Schema Reference**
Below are common data schemas for API monitoring systems.

### **3.1. Core Metrics Schema**
| **Metric Type**          | **Field**               | **Description**                                                                                     | **Example Value**                     | **Unit**          |
|--------------------------|-------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------|-------------------|
| **Request Metrics**      | `timestamp`             | ISO-8601 timestamp of the metric collection.                                                       | `2023-10-05T12:34:56.789Z`           | ISO 8601          |
|                          | `api_version`           | API version (e.g., `v1`, `v2`).                                                                       | `v1`                                  | String            |
|                          | `endpoint`              | HTTP route path (e.g., `/users/{id}`).                                                              | `/users/123`                          | String            |
|                          | `http_method`           | HTTP verb (GET, POST, etc.).                                                                        | `POST`                                | String            |
|                          | `status_code`           | HTTP response status (e.g., `200`, `404`).                                                          | `200`                                 | Integer           |
|                          | `duration_ms`           | Time taken to process the request.                                                                  | `150`                                 | Milliseconds      |
|                          | `client_ip`             | Source IP of the request (for geo/rate-limiting analysis).                                         | `192.168.1.100`                       | IPv4             |
| **Latency Breakdown**    | `parsing_latency`       | Time spent parsing request/response (e.g., JSON).                                                   | `20`                                  | Milliseconds      |
|                          | `db_query_latency`      | Database query execution time.                                                                       | `80`                                  | Milliseconds      |
| **Error Tracking**       | `error_type`            | Type of error (e.g., `Timeout`, `InvalidInput`).                                                    | `Timeout`                             | String            |
|                          | `error_message`         | Human-readable error description.                                                                  | `Database connection refused`         | String            |
| **Throughput**           | `request_count`         | Number of requests in a time window.                                                                | `42`                                  | Count             |
|                          | `rate`                  | Requests per second (rolling window).                                                               | `12.5`                                | Requests/sec      |

---

### **3.2. Distributed Tracing Schema**
| **Field**          | **Description**                                                                                     | **Example Value**                     |
|--------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------|
| `trace_id`         | Global unique identifier for the end-to-end transaction.                                             | `123e4567-e89b-12d3-a456-426614174000` |
| `span_id`          | Sub-operation ID (e.g., `db.query`).                                                                  | `abcdef123456`                        |
| `parent_span_id`   | ID of the parent span (for hierarchical tracing).                                                    | `000000000000` (root span)             |
| `operation_name`   | Name of the service/component (e.g., `auth-service:validate_token`).                                | `auth-service:validate_token`         |
| `start_time`       | Unix timestamp when the span began.                                                                 | `1696441096.123`                      |
| `end_time`         | Unix timestamp when the span ended.                                                                 | `1696441097.456`                      |
| `duration`         | Span duration in milliseconds.                                                                       | `323`                                 |
| `tags`             | Key-value pairs (e.g., `http.method=POST`, `db.table=users`).                                       | `{"http.method":"POST", "db.table":"users"}` |

---

### **3.3. Alerting Rule Schema**
| **Field**          | **Description**                                                                                     | **Example Value**                     |
|--------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------|
| `rule_name`        | Human-readable name (e.g., `HighErrorRate`).                                                       | `HighErrorRateForUsersAPI`             |
| `condition`        | Metric + threshold (e.g., `rate(http_errors_total[5m]) > 0.05`).                                     | `rate(http_request_duration_seconds{status=5xx}[5m]) > 0.1` |
| `for_duration`     | Minimum time window the condition must persist.                                                    | `300s`                                | (300 seconds = 5 minutes)             |
| `annotations`      | Additional context (e.g., `severity=critical`, `team=backend`).                                     | `{"severity":"critical", "team":"backend"}` |
| `labels`           | Filters for grouping rules (e.g., `service=order-service`).                                         | `{service="order-service"}`           |
| `silence`          | Time range during which alerts are muted (e.g., `2023-10-06T00:00:00Z` to `2023-10-07T00:00:00Z`).   | `["2023-10-06T00:00:00Z","2023-10-07T00:00:00Z"]` |

---

## **4. Query Examples**
### **4.1. Prometheus Metrics Query**
**Use Case:** Alert if API response time exceeds 500ms for 1 minute.
```promql
rate(http_request_duration_seconds_bucket{job="api-server", status=~"2.."}[1m])
    > 0.5
    and on(instance) group_left endpoint
    sum(increase(http_request_duration_seconds_count[1m])) by (endpoint) > 0
```
**Explanation:**
- `rate(...[1m])`: Requests per minute with duration > 500ms.
- `status=~"2.."`: Focus on success status codes (2xx).
- `sum(...)`: Ensure traffic exists for the endpoint.

---

### **4.2. Grafana Dashboard Panel (Custom)**
**Use Case:** Top 5 endpoints by latency (last 7 days).
```grafana-panel-query
{
  "datasource": "Prometheus",
  "metricsQuery": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint))",
  "interval": "1d",
  "limit": 5,
  "orderBy": "max"
}
```
**Visualization:** Use a **Time Series** panel with:
- X-axis: `Time (UTC)`.
- Y-axis: `"95th percentile latency (ms)"`.
- Legend: `endpoint`.

---

### **4.3. Distributed Tracing Filter (Jaeger)**
**Use Case:** Find slow `user-service` calls involving `payment-gateway`.
```jaeger-query
operation=payment-gateway
and service=user-service
and duration > 300ms
sort:duration
limit:10
```
**Result:** Display spans with:
- `trace_id`, `span_id`, `operation_name`.
- `start_time`, `end_time`, `duration`.

---

### **4.4. Log Correlation (ELK Stack)**
**Use Case:** Correlate API errors with database failures using `request_id`.
```logstash-query
request_id: "abc123"
and (
  (message: "Database connection refused" AND service: "user-service")
  OR
  (status: "500" AND endpoint: "/users/delete")
)
sort: @timestamp desc
```

---

## **5. Implementation Steps**
### **5.1. Instrumentation**
1. **Add Metrics Endpoint:**
   Use libraries like:
   - **Java:** Micrometer + Spring Boot Actuator.
   - **Node.js:** Prom-client.
   - **Python:** Prometheus Client.
   Example (Node.js):
   ```javascript
   const client = new prom.BasicClient();
   app.get('/metrics', (req, res) => {
     res.set('Content-Type', client.contentType);
     res.end(client.register.metrics());
   });
   ```

2. **Distributed Tracing:**
   Integrate OpenTelemetry SDK:
   ```python
   from opentelemetry import trace
   tracer = trace.get_tracer(__name__)
   with tracer.start_as_current_span("process_user"):
       # Your API logic here
   ```

3. **Log Request/Response IDs:**
   Inject `X-Request-ID` header and correlate logs:
   ```go
   ctx := context.WithValue(ctx, "request_id", uuid.New().String())
   ```

---

### **5.2. Aggregate & Store Data**
| **Component**       | **Tool**               | **Purpose**                                                                 |
|---------------------|------------------------|-----------------------------------------------------------------------------|
| **Metrics**         | Prometheus              | Real-time collection + querying.                                            |
| **Logging**         | ELK Stack (Elasticsearch) | Full-text search + log enrichment.                                          |
| **Tracing**         | Jaeger / Zipkin        | Visualize latency across services.                                          |
| **Alerting**        | Alertmanager            | Route alerts to Slack/PagerDuty.                                             |
| **Synthetic Checks**| UptimeRobot / Pingdom   | Simulate user requests (e.g., `GET /health`).                               |

---

### **5.3. Alerting Configuration**
1. **Define Rules (Prometheus):**
   ```yaml
   groups:
   - name: api-monitoring
     rules:
     - alert: HighLatencyUsersAPI
       expr: rate(http_request_duration_seconds_bucket{endpoint="/users"}[5m]) > 0.3
       for: 1m
       labels:
         severity: warning
       annotations:
         summary: "High latency for /users ({{ $value }}s)"
   ```

2. **Set Up Notifications:**
   - **Slack:** Use `slack_notify` receiver in Alertmanager.
   - **PagerDuty:** Integrate via API key.
   Example Slack config:
   ```yaml
   receiver: "slack"
   slack_configs:
   - channel: "#alerts"
     api_url: "https://hooks.slack.com/services/..."
     send_resolved: true
   ```

---

### **5.4. Validate with Synthetic Checks**
1. **Schedule Checks:**
   - **UptimeRobot:** Free tier allows 50 checks/month.
   - **Custom Script (Python):**
     ```python
     import requests
     response = requests.get("https://api.example.com/health", timeout=5)
     assert response.status_code == 200, f"Status: {response.status_code}"
     ```

2. **Store Results:**
   - Log to a database (e.g., SQLite) with:
     ```sql
     CREATE TABLE synthetic_checks (
       timestamp TIMESTAMP,
       endpoint TEXT,
       status_code INTEGER,
       duration_ms INTEGER,
       status BOOLEAN  -- TRUE if check passed
     );
     ```

---

## **6. Common Pitfalls & Solutions**
| **Pitfall**                          | **Solution**                                                                                                                                                     |
|---------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Metric Cardinality Explosion**     | Limit labels (e.g., only track `endpoint` + `http_method`). Use `relabel_configs` in Prometheus to hash unique IDs.                                             |
| **High Latency in Tracing**          | Sample traces (e.g., 1% of requests) to reduce overhead.                                                                                                      |
| **Alert Fatigue**                    | Use multi-level thresholds (e.g., `warning` at 90%, `critical` at 99%). Silence during known outages.                                                          |
| **Log Correlation Overhead**         | Use structured logging (JSON) and include `request_id` in all relevant logs.                                                                                     |
| **Synthetic Checks Too Frequent**    | Throttle checks (e.g., 1 check/minute) and use shared proxies to avoid rate-limiting.                                                                         |
| **Missing Context in Alerts**        | Include dynamic fields like `instance`, `endpoint`, and `value` in alert annotations.                                                                         |

---

## **7. Related Patterns**
| **Pattern**               | **Description**                                                                                                                                                     | **When to Use**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| **[Circuit Breaker]**     | Temporarily halt requests to a failing dependency to prevent cascading failures.                                                                                  | When an API depends on a flaky microservice (e.g., payment processor).                              |
| **[Rate Limiting]**       | Control the number of requests per client/IP to prevent abuse.                                                                                                     | For public APIs prone to DDoS (e.g., free-tier services).                                            |
| **[Canary Releases]**     | Gradually roll out API changes to a subset of users.                                                                                                             | During refactoring or schema migrations to catch regressions early.                                   |
| **[API Versioning]**      | Maintain backward compatibility by supporting multiple API versions.                                                                                             | When API contracts are stable but require frequent updates (e.g., `/v1/users`, `/v2/users`).          |
| **[Service Mesh (e.g., Istio)]** | Manage traffic, observability, and security for microservices via a proxy layer.                                                                               | For complex distributed systems with 10+ services.                                                  |

---

## **8. Further Reading**
- **[OpenTelemetry Specs](https://opentelemetry.io/docs/specs/)**: Standard for instrumentation.
- **[Prometheus Docs](https://prometheus.io/docs/prometheus/latest/)**: Metrics best practices.
- **[Grafana Dashboard Examples](https://grafana.com/grafana/dashboards/)**: Pre-built API monitoring templates.
- **[SRE Book (Google)](https://sre.google/sre-book/table-of-contents/)**: Observability chapter (p. 200+).