# **[Pattern] Per-Tenant Observability – Reference Guide**

---

## **Overview**

**Per-Tenant Observability** is a pattern used in multi-tenant architectures to isolate and monitor application metrics, logs, and traces on a per-tenant basis. This ensures that performance and operational data for one tenant does not interfere with another, enabling accurate diagnostics, compliance tracking, and resource optimization. The pattern is particularly critical in systems where tenants may have diverse workloads, SLAs, or regulatory requirements (e.g., SaaS applications, cloud platforms, or financial services).

By tagging observability data with tenant identifiers (e.g., `tenant_id`, `customer_id`), teams can:
- **Segregate performance issues** to specific tenants.
- **Enforce quota limits** (e.g., CPU/memory per tenant) via observability signals.
- **Comply with regulations** (e.g., GDPR, HIPAA) by restricting access to tenant-specific data.
- **Optimize auto-scaling** based on tenant-specific usage patterns.

This guide covers key concepts, schema design, query examples, and integration considerations for implementing Per-Tenant Observability.

---

## **Implementation Details**

### **Core Components**
1. **Tenant Identification**:
   - A unique identifier (e.g., UUID, string) per tenant, embedded in observability data (metrics, logs, traces).
   - Avoid hardcoding tenant IDs; derive them dynamically (e.g., from auth tokens, request headers, or database contexts).

2. **Tagging Strategy**:
   - **Metrics/Traces**: Use labels (Prometheus) or custom dimensions (OpenTelemetry, Datadog) for `tenant_id`.
     Example: `job: {tenant_id="acme123", service="orders"}`
   - **Logs**: Include `tenant_id` in log message fields (e.g., `{"tenant_id": "acme123", "event": "payment_failed"}`).
   - **Distributed Traces**: Propagate `tenant_id` via headers (e.g., `x-tenant-id`) across microservices.

3. **Data Separation**:
   - **Option 1 (Recommended)**: Store tenant-specific data in separate buckets/databases (e.g., partitioned time-series databases like InfluxDB or dedicated log shards).
   - **Option 2**: Use tenant-aware queries (e.g., `WHERE tenant_id = ?`) in centralized stores (e.g., Loki, Elasticsearch).

4. **Access Control**:
   - Enforce **row-level security** (e.g., PostgreSQL policies) or **query-level filters** (e.g., Grafana variable scopes) to restrict observability data access.
   - Integrate with **IAM/ABAC** systems to map tenant IDs to user permissions.

5. **Aggregation & Alerting**:
   - Design dashboards/alerts to support:
     - **Per-tenant metrics** (e.g., "Latency for tenant `acme123`").
     - **Cross-tenant comparisons** (e.g., "Top 5 tenants by error rate").
   - Use query languages like PromQL (with `by (tenant_id)`) or KQL (Kustodian) to filter tenant data.

---

## **Schema Reference**

| **Component**       | **Field/Dimension**       | **Data Type**               | **Description**                                                                                     | **Example Values**                     |
|----------------------|---------------------------|-----------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------|
| **Metrics**          | `tenant_id`                | String (UUID/Slug)           | Unique identifier for the tenant.                                                              | `"acme123"`, `"customer-456"`           |
|                      | `service`                 | String                      | Microservice name (e.g., `auth-service`).                                                       | `"orders"`, `"payments"`                |
|                      | `environment`             | Enum (`dev`, `staging`, `prod`) | Deployment environment for context.                                                          | `"production"`                         |
| **Logs**             | `tenant_id`                | String                      | Embedded in log records for filtering.                                                          | `{"tenant_id": "acme123"}`             |
|                      | `source`                  | String                      | Log source (e.g., `application`, `database`).                                                    | `"api-gateway"`                        |
| **Traces**           | `tenant_id` (Trace Header)| String                      | Propagated via W3C Trace Context or custom headers.                                               | `x-tenant-id: "acme123"`               |
|                      | `span_kind`               | Enum (`server`, `client`)    | Span type for distributed tracing.                                                              | `"server"`                             |
| **Databases**        | `tenant_metadata`         | JSONB/JSON                  | Store tenant-specific attributes (e.g., quota limits, features).                                 | `{"quota": 1000, "features": ["premium"]}` |
| **Alert Rules**      | `tenant_filter`           | String (PromQL/KQL)         | Query filter to restrict alerts to specific tenants.                                           | `tenant_id = "acme123"`                 |

---

## **Query Examples**

### **1. Prometheus Metrics**
**Query Tenant-Specific Latency (by 95th percentile):**
```promql
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{tenant_id="acme123"}[5m])) by (le))
```
**Compare Across Tenants (Top 3 by Errors):**
```promql
topk(3, sum(rate(http_errors_total{tenant_id=~"acme|contoso"}[1m])) by (tenant_id))
```

### **2. LogQL (Loki)**
**Filter Logs by Tenant and Error Type:**
```logql
{tenant_id="acme123"} |= "ERROR" AND level="critical"
```
**Count Events per Tenant (Last 24h):**
```logql
count_over_time({tenant_id}!="" [24h]) by (tenant_id)
```

### **3. Distributed Tracing (Jaeger/Zipkin)**
**Find Traces for a Specific Tenant:**
```bash
# Jaeger CLI (curl)
curl "http://jaeger:16686/api/traces?tags=tenant_id:acme123"
```
**Query Traces with Tenant ID in Headers:**
```promql
# OpenTelemetry Prometheus exporter
sum by (tenant_id)(rate(otel_traces_sum{tenant_id=~"acme|contoso"}[1m]))
```

### **4. Database Queries (PostgreSQL)**
**Fetch Tenant Quota Usage:**
```sql
SELECT
  tenant_id,
  SUM(used_resources) AS total_usage,
  quota_limit
FROM tenant_resources
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY tenant_id;
```
**Apply Row-Level Security (RLS):**
```sql
-- Enable RLS policy for tenant isolation
CREATE POLICY tenant_isolation_policy
ON tenant_resources USING (current_user = tenant_id);
```

---

## **Implementation Steps**

### **1. Instrumentation**
- **Metrics**: Use Prometheus client libraries or OpenTelemetry to auto-inject `tenant_id` (e.g., via middleware).
  ```go
  // Example: Prometheus middleware in Go
  reqctx.Set("tenant_id", tenantIDFromHeader(req.Header.Get("x-tenant-id")))
  ```
- **Logs**: Structured logging libraries (e.g., `structlog`, `zap`) to include `tenant_id`.
  ```python
  # Python example with structlog
  structlog.contextvars.bind_contextvars(tenant_id=tenant_id).configure()
  logger.info("Order processed", tenant_id=tenant_id)
  ```
- **Traces**: Propagate `tenant_id` in trace headers using W3C Trace Context or custom headers.
  ```yaml
  # OpenTelemetry auto-instrumentation (Node.js)
  headers:
    x-tenant-id: tenant_id
  ```

### **2. Storage Configuration**
- **Time-Series Databases**:
  - **InfluxDB**: Use tenant_id as a tag (e.g., `SELECT * FROM metrics WHERE tenant_id = 'acme123'`).
  - **Prometheus**: Label metrics with `tenant_id` and query with `by (tenant_id)`.
- **Log Aggregators**:
  - **Loki**: Use `tenant_id` as a label in log records.
  - **Elasticsearch**: Index logs with `tenant_id` as a field (mapped as keyword).

### **3. Access Control**
- **Grafana**:
  - Use **variables** to filter dashboards by tenant:
    ```yaml
    variables:
      tenant:
        type: query-results
        query: 'SELECT DISTINCT tenant_id FROM metrics'
    ```
  - Apply **row-level filters** in panels:
    ```
    $__timeFilter($__interval)
    | $__alias($tenant)
    ```
- **Alertmanager**:
  - Filter alerts by tenant in rule groups:
    ```yaml
    groups:
    - name: tenant-alerts
      rules:
      - alert: HighLatencyForTenant
        expr: histogram_quantile(0.99, rate(http_request_duration_seconds_bucket{tenant_id="acme123"}[5m])) > 1
    ```

### **4. Monitoring & Alerting**
- **SLOs per Tenant**:
  - Define tenant-specific error budgets (e.g., "Tenant `acme123` can tolerate 1% errors").
  - Use **SLO calculators** (e.g., Google’s SLO tool) to track compliance.
- **Quota Enforcement**:
  - Set up alerts when tenant usage exceeds limits:
    ```promql
    alert: TenantQuotaExceeded
    expr: sum(tenant_resource_usage{tenant_id="acme123"}) > tenant_quota{tenant_id="acme123"}
    ```

---

## **Related Patterns**

| **Pattern**                  | **Purpose**                                                                 | **When to Use**                                                                 | **Dependencies**                     |
|------------------------------|-----------------------------------------------------------------------------|---------------------------------------------------------------------------------|---------------------------------------|
| **[Multi-Tenancy Isolation](#)** | Isolate tenant data at the application/database layer.                     | When tenants require **data segregation** (e.g., healthcare, finance).         | Per-Tenant Observability              |
| **[Context Propagation](#)**  | Pass request context (e.g., auth, tenant_id) across services.               | In **microservices architectures** with distributed tracing/logs.              | OpenTelemetry, W3C Trace Context       |
| **[Quota Management](#)**    | Enforce resource limits per tenant (CPU, storage, API calls).               | When tenants have **SLA-based quotas** or billing requirements.                | Prometheus, custom metrics backends   |
| **[Rate Limiting](#)**       | Throttle API requests per tenant to prevent abuse.                        | For **public-facing SaaS APIs** or high-risk tenants.                         | Redis + Envoy, NGINX rate limiting    |
| **[Canary Deployments](#)**  | Gradually roll out changes to a subset of tenants.                        | When testing **feature flags** or **breaking changes** with minimal risk.      | Istio, Flagger                       |

---

## **Common Pitfalls & Mitigations**

| **Pitfall**                          | **Impact**                                                                 | **Mitigation**                                                                 |
|---------------------------------------|-----------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| Missing `tenant_id` in observability data | **Data loss**: Queries return incomplete or incorrect results.              | Enforce instrumentation via **linters** (e.g., Go `staticcheck`) or **CI checks**. |
| Overhead from per-tenant queries       | **Performance degradation** in dashboards/alerts.                         | Use **aggregation at rest** (e.g., Prometheus pre-aggregated metrics).      |
| Inconsistent tenant identifiers       | **Mismatched data**: Logs/metrics don’t align with traces.                   | Standardize IDs via **attribute validation** (e.g., UUID regex in logs).     |
| Overly granular tenant permissions    | **Access complexity**: Hard to manage RBAC for many tenants.                 | Use **tenant groups** (e.g., `tenant_id ~ "^acme|contoso"` in Grafana variables). |
| No observability for anonymous tenants | **Blind spots**: Unidentified tenants generate noise.                       | Use **default tenant IDs** (e.g., `"anonymous"`) and exclude from alerts.   |

---

## **Tools & Libraries**

| **Category**          | **Tools**                                                                 | **Use Case**                                                                 |
|-----------------------|---------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **Metrics**           | Prometheus, OpenTelemetry Collector, Datadog, New Relic                   | Per-tenant time-series data, alerting.                                    |
| **Logging**           | Loki, ELK Stack (Elasticsearch, Logstash, Kibana), Honeycomb               | Structured logs with tenant context.                                       |
| **Tracing**           | Jaeger, Zipkin, OpenTelemetry, Datadog APM                              | Distributed traces with `tenant_id` propagation.                           |
| **Access Control**    | Grafana Row-Level Security, OpenPolicyAgent (OPA), AWS IAM                 | Restrict dashboard/alert visibility by tenant.                            |
| **Instrumentation**   | OpenTelemetry Auto-Instrumentation, Prometheus Client Libraries, Zipkin | Embed `tenant_id` in metrics/logs/traces.                                  |

---

## **Example Architecture**

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│             │    │             │    │             │    │             │
│  Tenant A   │───▶│  Service A  │───▶│  Service B  │───▶│  Database  │
│ (tenant_id=1)│    │             │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────┬─────┘
                                                       │
                                                       ▼
┌───────────────────────────────────────────────────────────────────────┐
│                                                                       │
│  Centralized Observability Stack: Prometheus + Loki + Jaeger       │
│  - All metrics/logs/traces tagged with `tenant_id=1`                │
│  - Row-level security in Grafana to isolate Tenant A data          │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

---
**Key Takeaways**:
1. **Tag everything** (`tenant_id`, `service`, `environment`) for granular observability.
2. **Enforce consistency** in tenant IDs across systems (metrics, logs, traces).
3. **Design for access control** early (Grafana variables, RLS, ABAC).
4. **Test edge cases** (anonymous tenants, quota breaches, data deletion).