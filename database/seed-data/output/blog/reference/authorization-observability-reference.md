---

# **[Pattern] Authorization Observability: Reference Guide**
*Monitoring, logging, and tracing decisions around authorization to ensure security, compliance, and troubleshooting.*

---

## **1. Overview**
Authorization Observability is the practice of systematically collecting, analyzing, and acting on data related to **who is allowed to do what**, **why decisions are made**, and **how policy violations occur**. Unlike traditional logging (which records events) or monitoring (which tracks metrics), authorization observability provides **context-aware visibility** into dynamic permission checks, helping security teams enforce policies, detect anomalies, and debug permissions failures without intrusive modifications to code or infrastructure.

This pattern is critical for:
- **Compliance Auditing:** Proving that access controls align with regulatory requirements (e.g., GDPR, SOC2).
- **Incident Response:** Identifying unauthorized accesses or policy misconfigurations post-breach.
- **Performance Tuning:** Optimizing fine-grained permissions without over-broadening them.
- **User Experience:** Diagnosing why a legitimate request was denied (e.g., "You lack the `edit-document` permission").

---
## **2. Key Concepts**
| **Term**               | **Definition**                                                                                     | **Example**                                                                 |
|------------------------|---------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Authorization Event** | A record of a permission check (deny/allow), including subject, resource, action, and context.  | `User: alice@company.com → denied access to /api/data → action: `delete` → reason: missing `admin` role.` |
| **Subject**            | The entity requesting access (user, service account, or system).                                   | `alice@company.com`, `service-account-analytics`.                          |
| **Resource**           | The target of the authorization check (file, API endpoint, database table).                      | `/api/orders`, `user-profile:john-doe`, `database:users`.                   |
| **Action**             | The operation attempted (read, write, delete, etc.).                                             | `read`, `execute`, `modify`.                                               |
| **Decision**           | The outcome of the check (`allow`, `deny`, `unknown`).                                            | `deny` due to missing `billing` permission.                                 |
| **Policy Context**     | Metadata influencing the decision (time, IP, session state, attributes like `department`).         | `department=Finance`, `request-time=14:30:00`, `device=mobile`.             |
| **Policy Violation**   | A decision that deviates from expected behavior (e.g., `allow` when `deny` was intended).       | `Service account was granted `admin` access unexpectedly.`                  |
| **Observability Signals** | Data points emitted during or after an event (logs, metrics, traces, anomalies).                 | Log: `{event: "deny", user: "alice", reason: "missing-role"}`, Metric: `deny_rate: 3%`. |

---

## **3. Schema Reference**
Below is a **standardized event schema** for authorization observability. Implementations may extend this with additional fields.

| **Field**            | **Type**       | **Required** | **Description**                                                                 | **Example Values**                                  |
|----------------------|---------------|--------------|---------------------------------------------------------------------------------|-----------------------------------------------------|
| `event_id`           | String        | Yes          | Unique identifier for correlation across logs/metrics.                           | `a1b2c3d4-e5f6-7890`                                |
| `timestamp`          | ISO 8601      | Yes          | When the decision was made.                                                      | `2023-10-15T12:34:56.123Z`                        |
| `event_type`         | String        | Yes          | `authorization_check`, `policy_evaluation`, `permission_grant`, etc.          | `authorization_check`                               |
| `action`             | String        | Yes          | The requested operation.                                                        | `read`, `write`, `delete`                           |
| **Subject**          |               |              |                                                                                 |                                                     |
| `subject_type`       | String        | Yes          | `user`, `service_account`, `group`, `system`.                                  | `user`                                              |
| `subject_id`         | String        | Yes          | Unique identifier for the subject.                                              | `alice@example.com`, `sa-analytics`                 |
| `subject_attributes` | Object        | No           | Key-value pairs (e.g., roles, department).                                     | `{role: ["editor"], department: "marketing"}`      |
| **Resource**         |               |              |                                                                                 |                                                     |
| `resource_type`      | String        | Yes          | `api`, `document`, `database`, `file_system`.                                  | `api`                                              |
| `resource_id`        | String        | Yes          | Unique identifier for the resource.                                             | `/api/orders/123`, `document:contract-xyz`         |
| `resource_attributes`| Object        | No           | Metadata (e.g., `owner`, `sensitivity`).                                        | `{owner: "bob", sensitivity: "high"}`              |
| `decision`           | String        | Yes          | `allow`, `deny`, `unknown`, or `timeout`.                                       | `deny`                                              |
| `reason`             | String        | No           | Explanation for the decision (e.g., missing role, policy rule).                | `missing-role: admin`, `policy: no-overnight-access` |
| `policy`             | Object        | No           | Rule or module name that made the decision.                                     | `{name: "least-privilege", version: "v2"}`         |
| `policy_context`     | Object        | No           | Context used in evaluation (e.g., time, IP, session).                          | `{time: "14:30", ip: "192.168.1.1", session_id: "xyz"}` |
| `metadata`           | Object        | No           | Free-form data (e.g., `request_id`, `client_software`).                        | `{request_id: "req-456", client: "postman"}`        |

---

## **4. Implementation Details**
### **4.1. Where to Collect Events**
Authorize decisions **everywhere** permission checks occur:
- **Applications:** Log checks in your business logic (e.g., `if (user.hasPermission("edit")) { allow }`).
- **API Gateways:** Capture requests/responses (e.g., Kong, AWS API Gateway).
- **Databases:** Hook into RBAC systems (e.g., PostgreSQL Row-Level Security).
- **Microservices:** Instrument SDKs (e.g., Open Policy Agent, Casbin).
- **Cloud Services:** Use provider-specific logs (e.g., AWS IAM Decision Logs, GCP IAM Audit Logs).

### **4.2. Data Collection Strategies**
| **Method**               | **Pros**                                      | **Cons**                                  | **Tools**                                  |
|--------------------------|-----------------------------------------------|------------------------------------------|--------------------------------------------|
| **Logging**              | Low overhead, persistent storage.            | Noisy if unfiltered; hard to query.      | Fluentd, Loki, ELK Stack                  |
| **Metrics**              | Aggregates decisions (e.g., deny rate).      | Loses context; requires aggregations.    | Prometheus, Datadog, New Relic             |
| **Tracing**              | Correlates across services (e.g., OpenTelemetry). | High overhead; complex setup.          | Jaeger, Zipkin, AWS X-Ray                  |
| **Event Streaming**      | Real-time processing (e.g., detect anomalies). | Infrastructure cost.                     | Kafka, Pulsar, AWS Kinesis                 |
| **Database Auditing**    | Captures SQL-level permissions.               | Limited to DB layers.                   | PostgreSQL Logical Decoding                |

### **4.3. Example Instrumentation Code (Python)**
```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger import JaegerExporter

# Initialize tracer
trace.set_tracer_provider(TracerProvider())
jaeger_exporter = JaegerExporter(
    endpoint="http://jaeger-collector:14268/api/traces",
    service_name="my-app"
)
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(jaeger_exporter))

def check_permission(subject_id: str, resource_id: str, action: str, roles: list[str]):
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("authorization_check"):
        span = trace.get_current_span()
        span.set_attribute("subject.id", subject_id)
        span.set_attribute("resource.id", resource_id)
        span.set_attribute("action", action)
        span.set_attribute("roles", roles)

        # Simulate policy check
        if "admin" not in roles:
            span.set_attribute("decision", "deny")
            span.set_attribute("reason", "missing-role: admin")
            raise PermissionError("Insufficient permissions")
        span.set_attribute("decision", "allow")
```

### **4.4. Querying Authorization Events**
#### **Log Query (ELK/Kibana)**
```json
// Find all denied requests to sensitive resources
event_type: "authorization_check"
AND decision: "deny"
AND resource.resource_type: "api"
AND resource.resource_id: "/api/finance*"
```
**Result Example:**
```
{
  "subject": { "id": "alice@example.com", "attributes": { "department": "HR" } },
  "resource": { "id": "/api/finance/invoices", "attributes": { "sensitivity": "high" } },
  "action": "write",
  "decision": "deny",
  "reason": "policy: no-hr-access-to-finance",
  "timestamp": "2023-10-15T12:34:56Z"
}
```

#### **Metric Query (Prometheus)**
```promql
# Rate of denied requests per hour
rate(authorization_denies_total[1h])
by (resource_type, action)

# Deny rate per user
sum(rate(authorization_denies_total{subject_id=~".*"}[1h]))
/
sum(rate(authorization_checks_total{subject_id=~".*"}[1h]))
by (subject_id)
```

#### **Trace Query (Jaeger)**
```
Find traces where:
- Operation = "authorization_check"
- Subject.id = "sa-analytics"
- Decision = "allow"
```
**Visualization:**
```
[Request] → [Service A] (span: auth_check, decision=deny, reason=missing-role) → [Service B]
```

---

## **5. Query Examples**
### **5.1. Detect Unusual Access Patterns**
```sql
-- Find users who denied to access the same resource repeatedly
SELECT subject_id, COUNT(*) AS deny_count
FROM authorization_events
WHERE decision = 'deny'
  AND resource_id = '/api/config'
GROUP BY subject_id
HAVING deny_count > 5
ORDER BY deny_count DESC;
```

### **5.2. Audit Policy Changes**
```sql
-- Compare current policy versions with past decisions
SELECT p.version, COUNT(e.event_id) AS deny_count
FROM policies p
JOIN authorization_events e ON p.name = e.policy.name
WHERE e.decision = 'deny'
  AND p.version IN ('v1', 'v2')
GROUP BY p.version;
```

### **5.3. Correlate with Incidents**
```python
# Link a denied request to a subsequent data breach
denied_event = log_query(filters={"decision": "deny", "resource": "/api/orders"})
breach_events = log_query(filters={"event_type": "data_leak"})
if denied_event["subject_id"] in breach_events["subject_ids"]:
    alert(f"Potential policy bypass: {denied_event['subject_id']}")
```

---

## **6. Related Patterns**
| **Pattern**                  | **Description**                                                                 | **When to Use**                                                                 |
|------------------------------|---------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **[Permission Boundary](https://code-carbon.com/patterns/permission-boundary)** | Restrict permissions by context (e.g., time, location).                       | When fine-grained access is needed (e.g., time-based restrictions).            |
| **[Attribute-Based Access Control (ABAC)](https://code-carbon.com/patterns/abac)** | Inventories attributes (e.g., `department`, `clearance`) for dynamic policies. | When policies require complex logic beyond RBAC.                              |
| **[Observability-Driven Development](https://code-carbon.com/patterns/observability-driven)** | Use telemetry to guide policy design.                                         | During pilot phases or when refactoring permissions.                        |
| **[Least Privilege](https://code-carbon.com/patterns/least-privilege)**         | Grant only necessary permissions.                                             | Reducing attack surface and compliance risks.                                 |
| **[Policy as Code](https://code-carbon.com/patterns/policy-as-code)**           | Define policies in declarative languages (e.g., OPA, Terraform).             | Managing policies in CI/CD or cloud environments.                            |
| **[Event-Driven Authorization](https://code-carbon.com/patterns/event-driven-authz)** | Evaluate permissions on events (e.g., Kafka streams).                        | Real-time systems (e.g., fraud detection, live gaming).                       |

---
## **7. Best Practices**
1. **Standardize Event Schema:** Use a schema registry (e.g., JSON Schema, Avro) to ensure consistency across tools.
2. **Retain Raw Data:** Log decisions for audit purposes (retention: **2+ years** for compliance).
3. **Anonymize Sensitive Data:** Mask PII (e.g., `subject_id: "user-123*"`) in observability tools.
4. **Alert on Anomalies:**
   - Sudden spikes in denials.
   - Policy violations by high-privilege accounts.
   - Changes to policies without approval.
5. **Instrument Before Production:** Test observability overhead in staging.
6. **Integrate with SIEM:** Forward authorization events to Splunk/Sentinel for threat detection.
7. **Document Policies:** Link observability data to policy documents (e.g., in a **policy registry**).

---
## **8. Anti-Patterns**
| **Anti-Pattern**               | **Problem**                                                                 | **Fix**                                                                       |
|---------------------------------|-----------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **Logging Only Decisions**      | Lose context for debugging (e.g., "Why was this denied?").               | Log **input attributes** and **policy context** (not just `allow/deny`).    |
| **No Correlation IDs**          | Hard to trace cross-service requests.                                       | Use **trace IDs** or **request IDs** to link logs/metrics.                  |
| **Overlogging Permissions**     | Noise drowns out critical events.                                          | Filter low-risk checks (e.g., `GET` requests).                              |
| **Ignoring Policy Context**     | Miss time- or location-based rules.                                         | Include `policy_context` in every event.                                     |
| **Static Analysis Only**        | Can’t detect runtime violations (e.g., shadow admin).                     | Combine **static analysis** (e.g., Checkov) with **runtime observability**. |

---
## **9. Tools & Frameworks**
| **Category**          | **Tools**                                                                 | **Use Case**                                                                 |
|-----------------------|---------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **OpenTelemetry**     | [OpenTelemetry Python SDK](https://opentelemetry.io/docs/instrumentation/python/), [Auto-instrumentation](https://github.com/open-telemetry/opentelemetry-auto-instrumentation) | Distributed tracing of auth decisions.                                      |
| **Policy Engines**    | [Open Policy Agent (OPA)](https://www.openpolicyagent.org/), [Casbin](https://casbin.org/) | Evaluate dynamic policies (e.g., ABAC).                                      |
| **Logging**           | [Loki](https://grafana.com/oss/loki/), [ELK Stack](https://www.elastic.co/elk-stack) | Store and query authorization logs.                                          |
| **Metrics**           | [Prometheus](https://prometheus.io/), [Datadog](https://www.datadoghq.com/) | Track deny rates, latency, or policy violations.                            |
| **Event Streaming**   | [Kafka](https://kafka.apache.org/), [AWS Kinesis](https://aws.amazon.com/kinesis/) | Real-time anomaly detection (e.g., fraud).                                   |
| **SIEM**              | [Splunk](https://www.splunk.com/), [Microsoft Sentinel](https://azure.microsoft.com/en-us/products/microsoft-sentinel/) | Correlate auth events with security incidents.                               |
| **Audit Tools**       | [AWS IAM Access Analyzer](https://aws.amazon.com/iam/features/access-analyzer/), [GCP Audit Logs](https://cloud.google.com/logging/docs/audit) | Pre-built compliance reporting.                                              |

---
## **10. Further Reading**
- [IETF Draft: Authorization Observability](https://datatracker.ietf.org/doc/draft-ietf-oauth-authorization-observability/)
- [Gartner: Authorization Observability](https://www.gartner.com/en/documents/3989452)
- [OpenTelemetry Authorization Example](https://github.com/open-telemetry/opentelemetry-specification/blob/main/specs/semconv/metric/metrics.yaml#L500)