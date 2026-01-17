# **Debugging "Per-Tenant Observability" Pattern: A Troubleshooting Guide**

## **Introduction**
The **Per-Tenant Observability** pattern ensures that metrics, logs, and traces are isolated per tenant to prevent cross-tenant data leakage, improve tenant-specific debugging, and comply with privacy regulations. Common issues arise due to incorrect instrumentation, misconfigured storage, or improper access controls.

This guide helps diagnose and resolve issues efficiently by covering symptoms, common failures, debugging techniques, and prevention strategies.

---

## **Symptom Checklist**
Before diving into fixes, verify the following symptoms:

### **1. Metrics-Level Issues**
- [ ] Metrics data is **not being recorded** for specific tenants.
- [ ] Metrics from different tenants are **mixed together** in aggregated views.
- [ ] High cardinality leading to **unexpected cost spikes** in observability tools.
- [ ] Missing **tenant-specific tags** in metrics labels (e.g., `tenant_id`).

### **2. Logs-Level Issues**
- [ ] Logs from one tenant are **visible to another**.
- [ ] Logs contain **sensitive data** (e.g., PII) from unintended tenants.
- [ ] Logs are not being **filtered or masked** per tenant.

### **3. Traces-Level Issues**
- [ ] Distributed traces **cross tenant boundaries**, showing unrelated activity.
- [ ] Span context propagation **fails** due to incorrect tenant ID injection.
- [ ] Trace queries return **unexpected tenant data** due to tag misconfiguration.

### **4. Storage & Access Issues**
- [ ] Observability backend (e.g., Prometheus, OpenTelemetry Collector) **rejects writes** due to tenant isolation constraints.
- [ ] Permission errors when querying tenant-specific data.
- [ ] Unnecessary **data duplication** across tenants due to misconfigured sharding.

### **5. Frontend/Application Issues**
- [ ] Dashboard filters **not working** for tenant isolation.
- [ ] API calls to observability tools **time out** due to inefficient tenant queries.

---

## **Common Issues & Fixes**

### **1. Metrics Not Recording Per Tenant**
**Symptom:**
`tenant_id` is missing or incorrectly set in metric labels, causing aggregation across tenants.

**Root Cause:**
- Missing or incorrect **tenant ID propagation** in instrumentation.
- Metric tool (e.g., Prometheus, OpenTelemetry) **not configured for tenant sharding**.

**Fix:**
#### **Option 1: Ensure Tenant ID in Metrics (Prometheus Example)**
```go
// Correct: Tenant ID is explicitly added
func recordMetrics(ctx context.Context, tenantID string) {
    counter.WithLabelValues(tenantID).Inc()
}
```
- Use a **structured logger** or **context propagation** to inject `tenant_id`:
  ```go
  func main() {
      ctx := context.WithValue(context.Background(), "tenant_id", "tenant-123")
      recordMetrics(ctx)
  }
  ```

#### **Option 2: Configure OpenTelemetry with Tenant Context**
```python
# Python example using OpenTelemetry
from opentelemetry import trace
from opentelemetry.context import set_value, get_value

tenant_id = "tenant-123"
set_value("tenant_id", tenant_id)

# Propagate in traces
trace.get_current_span().set_attribute("tenant_id", tenant_id)
```

**Prevention:**
- Use **automatic tenant ID injection** via middleware (e.g., AWS Lambda, Cloudflare Workers).
- Validate tenant ID in **metric labels** before recording.

---

### **2. Mixed Tenant Metrics in Aggregations**
**Symptom:**
Prometheus/Grafana shows **combined data** instead of per-tenant metrics.

**Root Cause:**
- **No tenant-based sharding** in Prometheus storage.
- Grafana dashboards **not filtering by tenant**.

**Fix:**
#### **Option 1: Prometheus Tenant Sharding**
Configure Prometheus to **store metrics separately per tenant**:
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'app'
    metrics_path: '/metrics'
    params:
      tenant_id: ['{{ $tenant_id }}']  # Pass tenant ID via scrape config
    relabel_configs:
      - source_labels: [tenant_id]
        target_label: tenant
```
- Use **Prometheus remote storage** (e.g., Thanos, Cortex) with **tenant-based partitioning**.

#### **Option 2: Grafana Tenant Filtering**
Create a **tenant-aware dashboard variable**:
```sql
-- Grafana query (Prometheus)
SELECT * FROM (
  SELECT var_tenant_id as tenant, metric_name, value
  FROM metrics
  WHERE tenant = "$tenant"
)
```
- Use **Grafana’s "Variables"** to dynamically filter by tenant.

**Prevention:**
- Enforce **tenant-aware PromQL queries** in dashboards.
- Use **open standards (W3C Trace Context)** for tenant propagation.

---

### **3. Logs Leaking Across Tenants**
**Symptom:**
Logs from **Tenant A** appear in **Tenant B’s** console.

**Root Cause:**
- **No tenant filtering** in log shipping (e.g., Fluentd, Loki).
- **Sensitive data** not masked in logs.

**Fix:**
#### **Option 1: Tenant-Based Log Filtering (Fluentd Example)**
```xml
<match **>
  <filter_tenant>
    @type record_transformer
    <record>
      tenant_id ${tenant_id}  # Inject tenant ID from context
    </record>
  </filter_tenant>
  <filter>
    @type grep
    <exclude>
      key tenant_id
      pattern /^${another_tenant_id}/
    </exclude>
  </filter>
  <store>
    @type loki
    urls http://loki:3100/loki/api/v1/push
    tenant_id ${tenant_id}  # Ensure logs go to correct tenant bucket
  </store>
</match>
```

#### **Option 2: Masking Sensitive Data (Loki Example)**
```yaml
# Loki config (tenant_isolation enabled)
target_config:
  tenant_isolation: true
  tenant_id_header: "X-Tenant-ID"
```
- Use **log redaction** for PII:
  ```go
  func maskLogs(log string, tenantID string) string {
      return strings.ReplaceAll(log, "secret_${tenantID}", "*****")
  }
  ```

**Prevention:**
- **Always pass tenant ID** in log headers (`X-Tenant-ID`).
- Use **Loki’s tenant isolation** or **Elasticsearch tenant-specific indices**.

---

### **4. Cross-Tenant Traces**
**Symptom:**
Traces show **API calls between unrelated tenants**.

**Root Cause:**
- **No tenant-based sampling** in OpenTelemetry.
- **Span propagation** fails due to missing context.

**Fix:**
#### **Option 1: Tenant-Aware Sampling (OpenTelemetry)**
```go
// Configure OpenTelemetry to sample per tenant
provider := instrumentation.NewTenantAwareProvider(
    instrumentation.WithSampler(
        sampling.NewProbabilitySampler(0.1),
        sampling.WithContext(sampling.ContextFunc(func(ctx context.Context) string {
            return getTenantIDFromContext(ctx)
        })),
    ),
)
```

#### **Option 2: Propagate Tenant ID in Traces**
```python
# Python OpenTelemetry
from opentelemetry import trace
from opentelemetry.context import set_value

tenant_id = "tenant-123"
set_value("tenant_id", tenant_id, trace.get_current_span())

# Ensure it propagates
trace.get_current_span().set_attribute("tenant_id", tenant_id)
```

**Prevention:**
- **Reject traces** with missing tenant IDs.
- Use **OpenTelemetry’s W3C Trace Context** with tenant ID.

---

## **Debugging Tools & Techniques**

| **Tool**               | **Purpose**                                                                 | **Example Command/Query**                          |
|------------------------|-----------------------------------------------------------------------------|----------------------------------------------------|
| **Prometheus**         | Check if metrics are recorded per tenant.                                  | `sum(rate(http_requests_total{tenant="X"}[5m]))`   |
| **Grafana**            | Verify tenant filtering in dashboards.                                    | `explore query with tenant variable`               |
| **Loki**               | Inspect logs per tenant.                                                    | `{tenant_id="X"} | logfmt`                               |
| **OpenTelemetry Collector** | Validate trace context propagation. | `otelcol --log-level=debug --config=config.yaml` |
| **AWS CloudWatch**     | Check per-tenant log/metric isolation.                                      | `filter by "tenant_id" in log groups`              |
| **ELK Stack**          | Audit log access per tenant.                                                | `kibana query: tenant_id:"X" AND @timestamp>now-1h`|
| **Kubernetes Audit Logs** | Debug tenant isolation in K8s deployments.                               | `kubectl logs -l tenant-id=X`                     |

### **Key Techniques:**
1. **Context Propagation**
   - Use `context.WithValue()` in Go or `opentelemetry.context` in Python.
   - Verify propagation with `otelcol` debug logs.

2. **Metric Tag Validation**
   - Run PromQL queries like:
     ```sql
     sum(by(tenant_id) (rate(http_requests_total[5m])))  -- Check per-tenant distribution
     ```

3. **Log Sampling**
   - Filter Loki logs by tenant:
     ```bash
     loki debug --query '{tenant_id="X"} | json' --format table
     ```

4. **Trace Analysis**
   - In Jaeger/Grafana, apply tenant filter:
     ```sql
     SELECT * FROM spans WHERE tenant_id = "X"
     ```

---

## **Prevention Strategies**
### **1. Infrastructure-Level Isolation**
- **Shard Prometheus/Thanos** by tenant.
- Use **Loki’s tenant isolation** (`tenant_isolation: true`).
- **Segment OpenTelemetry Collector** by tenant (multi-process worker pools).

### **2. Code-Level Best Practices**
- **Always inject tenant ID early** (API gateway, middleware).
- **Validate tenant ID** before processing requests.
- **Mask logs** automatically (e.g., using Fluentd redaction).

### **3. Observability Tooling**
- **Grafana Dashboards:** Enforce tenant filters by default.
- **Prometheus Alerts:** Use `tenant_id` in alert rules.
- **Trace Sampling:** Apply per-tenant sampling policies.

### **4. Testing & Validation**
- **Unit Tests:** Verify tenant ID propagation.
  ```go
  func TestTenantIDPropagation(t *testing.T) {
      ctx := context.WithValue(context.Background(), "tenant_id", "test-tenant")
      span := trace.StartSpan("test", context.Background())
      span.SetAttribute("tenant_id", getTenantID(ctx)) // Should not panic
  }
  ```
- **Chaos Testing:** Simulate tenant ID injection failures.

### **5. Security & Compliance**
- **Role-Based Access Control (RBAC):** Restrict tenant data access.
- **Audit Logs:** Track who accesses tenant-specific observability data.
- **Data Encryption:** Ensure tenant logs/metrics are encrypted at rest.

---

## **Final Checklist for Resolution**
| **Issue**               | **Fix Applied?** | **Verification Step**                          |
|-------------------------|------------------|-----------------------------------------------|
| Missing tenant ID in metrics | ✅/❌ | Query Prometheus: `sum(rate(metric{tenant="X"}[5m]))` |
| Mixed tenant logs       | ✅/❌ | Check Loki: `{job="app"} | json | tenant_id="X"` |
| Cross-tenant traces     | ✅/❌ | Jaeger query: `tenant_id="X"`                  |
| Permission errors       | ✅/❌ | Test RBAC: `kubectl auth can-i get pods -n tenant-X` |
| High cardinality        | ✅/❌ | Prometheus relabeling: `relabel_configs`      |

---

## **Conclusion**
The **Per-Tenant Observability** pattern ensures data isolation but requires careful instrumentation, tooling configuration, and access control. By following this guide, you can:
✅ **Diagnose** why metrics/logs/traces are misbehaving.
✅ **Fix** common issues (missing tags, mixed data, permission errors).
✅ **Prevent** future problems with automated tenant context propagation and tooling policies.

**Next Steps:**
- Automate tenant ID injection in your CI/CD pipeline.
- Schedule **quarterly reviews** of observability tooling for tenant isolation.
- Use **OpenTelemetry’s multi-tenancy specs** for future-proofing.

---
**Need more help?** Check [OpenTelemetry’s multi-tenancy docs](https://opentelemetry.io/docs/specs/otel/multi-tenancy/).