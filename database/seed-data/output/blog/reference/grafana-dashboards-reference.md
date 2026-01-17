**[Pattern] Grafana Dashboards Integration Patterns Reference Guide**
*Version: 1.2*
*Last Updated: [Date]*

---

### **Overview**
This guide provides a structured reference for integrating Grafana dashboards into observability, monitoring, and analytics workflows. Whether you’re embedding dashboards, syncing them with external systems, or customizing visualization logic, this pattern outlines:
- **Core integration patterns** (standalone, embedded, federated, dynamic)
- **Implementation trade-offs** (performance, scalability, security)
- **Best practices** for data sourcing, authentication, and governance
- **Common pitfalls** (e.g., query latency, permission mismatches)

---

## **1. Schema Reference**
Below are the key integration patterns, their **data flows**, and **requirements**.

| **Pattern**               | **Description**                                                                 | **Data Sources**                          | **Key Components**                          | **Authentication Methods**               | **Data Latency**       |
|---------------------------|---------------------------------------------------------------------------------|------------------------------------------|--------------------------------------------|----------------------------------------|------------------------|
| **Standalone**            | Self-hosted Grafana with direct query to time-series databases (e.g., Prometheus, InfluxDB). | Prometheus, InfluxDB, Elasticsearch      | Grafana Server, Dashboard YAML/JSON      | API Key, Bearer Tokens (`Bearer <token>`) | Near Real-time         |
| **Embedded (iFrame)**     | Dashboards rendered within a parent application (e.g., React, Angular) via iFrame. | Same as Standalone                      | Grafana Server, Parent App                | OAuth2, JWT (via `origin` header)       | Near Real-time         |
| **Federated**             | Dashboards pulled from remote Grafana instances (Grafana Enterprise or self-managed). | Prometheus Federation, External APIs     | Grafana Server (source + target), Proxy   | Cross-domain JWT, SAML              | Medium (dep. on sync) |
| **Dynamic (API-Based)**   | Dashboards generated or updated via Grafana API (e.g., CI/CD pipelines, dashlet updates). | External APIs (REST/gRPC)                | Grafana API (v1/v3), Webhooks, Alertmanager | API Tokens, OAuth2                  | Configurable (sync)  |
| **Webhook-Driven**        | Dashboards updated in real-time via webhooks (e.g., Kubernetes events).          | Alertmanager, External Event Streams     | Grafana Webhook Endpoint, Trigger Rules   | API Keys, Mutual TLS            | Sub-second (async)     |

---

## **2. Implementation Details**
### **2.1 Core Components**
| **Component**          | **Purpose**                                                                 | **Example Implementation**                                                                 |
|------------------------|-----------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| **Grafana Server**     | Hosts dashboards and processes queries.                                     | Self-hosted (Prometheus + Grafana) or Enterprise (cloud-managed).                         |
| **Data Source Plugins**| Connects to databases/APIs (e.g., Loki, PostgreSQL).                        | Configure via `Configuration > Data Sources` in Grafana UI.                                |
| **Embedded SDK**       | For iFrame/iframe-less embedding (React/Vue plugins).                         | Use Grafana’s [Embedding API](https://grafana.com/docs/grafana/latest/developers/embed/) or `@grafana/data` SDK. |
| **Proxy/Reverse Proxy**| Handles cross-origin requests (for federated dashboards).                   | Nginx/Grafana Enterprise Proxy (`grafana.ini` under `[server]`).                          |

---

### **2.2 Query Examples**
#### **Basic Prometheus Query (Standalone)**
```promql
# Metrics: HTTP request latency (95th percentile)
sum by (job)(rate(http_request_duration_seconds_bucket{le="0.5"}[5m])) > 0
```
**Grafana Panel JSON Snippet:**
```json
{
  "targets": [
    {
      "expr": "sum by (job)(rate(http_request_duration_seconds_bucket{le=\"0.5\"}[5m])) > 0",
      "legendFormat": "{{job}}"
    }
  ]
}
```

#### **InfluxDB Query (Dynamic Pattern)**
```influxql
# Time-series: Server CPU usage
SELECT mean(value) FROM "cpu_usage" WHERE $timeFilter GROUP BY time($__interval), "host"
```
**Variable Substitution:**
Replace `$timeFilter` and `$__interval` with Grafana’s [dashboard variables](https://grafana.com/docs/grafana/latest/variables/).

---

### **2.3 Authentication Scenarios**
| **Scenario**               | **Method**                          | **Configuration**                                                                 |
|----------------------------|-------------------------------------|-----------------------------------------------------------------------------------|
| **Standalone API Access**  | API Key                             | `Authorization: Bearer <key>` (via `admin/api-keys`).                             |
| **Embedded iFrame**        | OAuth2 + `origin` Header            | Set `allowed_origins` in `grafana.ini`: `[auth.anonymous] allowed_origins = http://myapp.com`. |
| **Federated Dashboards**   | Mutual TLS                          | Configure TLS certs in `grafana_enterprise.ini` under `[proxy]` and `[server]`.    |
| **Webhook Security**       | JWT Validation                      | Validate tokens in Grafana webhook config: `{ "headers": { "Authorization": "Bearer {{.Token}}" } }`. |

---

### **2.4 Performance Considerations**
- **Query Optimization**:
  - Use `min_step` in Prometheus for aggregated queries (e.g., `min_step=1h`).
  - Limit panels with high-cardinality metrics (e.g., `label_join` for tags).
- **Caching**:
  - Enable Grafana’s [Query Caching](https://grafana.com/docs/grafana/latest/administration/query-caching/) for repeated queries.
  - For federated dashboards, use `grafana-proxy` with Redis caching.
- **Scalability**:
  - Distribute Prometheus instances behind Grafana for horizontal scaling.
  - Use [Grafana Agent](https://grafana.com/docs/grafana-cloud/agent/) to forward metrics to multiple backends.

---

## **3. Best Practices**
### **3.1 Data Governance**
- **Labeling**: Standardize metric labels (e.g., `namespace=production`).
- **Retention**: Configure TTL for time-series data (e.g., InfluxDB’s `retention_policy`).
- **Access Control**:
  - Use Grafana’s [Role-Based Access Control (RBAC)](https://grafana.com/docs/grafana/latest/security/rbac/).
  - Restrict dashboard exports via `grafana.ini`:
    ```ini
    [auth]
    export_allowed_origins = http://trusted-domain.com
    ```

### **3.2 Embedding Guidelines**
- **Iframe vs. SDK**:
  - Use **iFrame** for simple embeds (e.g., shared dashboards).
  - Use **Grafana SDK** for interactive components (e.g., dynamic filters).
- **Responsive Design**:
  ```html
  <iframe
    src="https://grafana-instance.com/dashboards/123"
    width="100%"
    height="600px"
    frameborder="0"
  ></iframe>
  ```

### **3.3 Monitoring Integrations**
- **Alerting**: Link dashboards to Alertmanager rules via `alert` panel type.
- **Logging**: Forward Grafana logs to Loki/Fluent Bit:
  ```ini
  [log]
  mode = file
  outputs = [console, file]
  ```

---

## **4. Common Pitfalls & Mitigations**
| **Pitfall**                     | **Cause**                                  | **Solution**                                                                 |
|----------------------------------|--------------------------------------------|------------------------------------------------------------------------------|
| **High Latency in Federated**    | Overloaded Prometheus federation targets.   | Use `prometheus_federation` with `max_samples` limit.                      |
| **Permission Errors**            | Mismatched org/user roles.                 | Audit Grafana [permissions](https://grafana.com/docs/grafana/latest/security/permissions/). |
| **Query Timeouts**               | Complex PromQL queries.                    | Simplify queries (e.g., use `unless` instead of nested `if` statements).    |
| **Webhook Flooding**             | High-frequency events (e.g., Kubernetes pods). | Throttle webhooks via `rate_limit` in Grafana’s `alerting` config.         |

---

## **5. Related Patterns**
- **[Observability Data Collection]** – How to ingest metrics/logs into Grafana’s data sources.
  *Reference*: [Grafana Data Sources Pattern](link-to-pattern).
- **[Real-Time Alerting]** – Integrating Grafana alerts with PagerDuty/Slack.
  *Reference*: [Alert Routing Pattern](link-to-pattern).
- **[Multi-Tenant Observability]** – Isolating dashboards for different teams.
  *Reference*: [Isolation Strategies Pattern](link-to-pattern).

---
**Appendix**
- **[Grafana API Docs](https://grafana.com/docs/grafana/latest/developers/http_api/)**
- **[Embedding SDK](https://grafana.com/docs/grafana/latest/developers/embed/)**