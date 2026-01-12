---
**# [Pattern] Compliance Debugging Reference Guide**

---

## **1. Overview**
**Compliance Debugging** is a troubleshooting pattern designed to systematically validate system behavior against regulatory, audit, or policy requirements by:
- **Automating compliance checks** (e.g., data integrity, access controls, logging).
- **Generating actionable insights** from deviations (e.g., alerts, remediation steps).
- **Integrating with observability tools** (logs, metrics, traces) to trace non-compliant events back to root causes.

This pattern bridges the gap between static policies (e.g., "users must log in via MFA") and dynamic system states (e.g., "User X logged in without MFA at 3:45 PM"). It is critical for **auditability**, **incident response**, and **proactive risk mitigation**.

**Use cases**:
- Detecting policy violations in real-time (e.g., SOC 2 AICPA criteria).
- Post-incident forensics (e.g., "Why did this API call bypass auth?").
- Third-party compliance audits (e.g., GDPR, HIPAA).

---

## **2. Schema Reference**
Below are key components of a **Compliance Debugging** pipeline, with sample payloads for reference.

| **Component**          | **Description**                                                                 | **Schema Example**                                                                                     | **Data Type**                          |
|-------------------------|---------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|----------------------------------------|
| **Policy Rule**         | Defines a compliance requirement (e.g., "All API responses must include a `timestamp` field"). | `{ "name": "API_Timestamp_Validation", "severity": "high" }`               | JSON object                            |
| **Compliance Check**    | Automated validation of a system state against a rule (e.g., query logs for `timestamp` presence). | `{"rule": "API_Timestamp_Validation", "check_type": "log_query", "query": "filter by path=/api/v1/data"}` | JSON object                            |
| **Compliance Event**    | Record of a rule violation (e.g., a log entry missing a timestamp).              | `{ "rule": "API_Timestamp_Validation", "timestamp": "2023-10-15T12:34:56Z", "violation": "missing_field", "resource": "logs"` } | JSON object                            |
| **Debug Context**       | Additional metadata to trace the root cause (e.g., user session ID, parent request). | `{ "user_id": "abc123", "session_id": "sess-xyz", "related_trace_id": "trc-456" }`               | JSON object                            |
| **Alert**               | Actionable notification (e.g., Slack message, PagerDuty alert).                  | `{"severity": "critical", "message": "API response missing timestamp", "remediation": "Add field to endpoint"}` | JSON object                            |

---

## **3. Implementation Details**
### **3.1 Core Workflow**
1. **Define Policies**: Encode compliance rules as code (e.g., Open Policy Agent policies) or declarative YAML.
2. **Instrument Checks**: Embed checks into system telemetry (logs, traces, metrics) or run as scheduled jobs.
3. **Detect Violations**: Use tools like:
   - **Log-based checks**: `awslogs filter @message = 'missing timestamp'` (AWS CloudWatch).
   - **Traces-based checks**: Add a compliance validator to OpenTelemetry traces.
4. **Enrich Context**: Correlate events with debug metadata (e.g., `debug_context: { user_id: "123" }`).
5. **Trigger Alerts**: Map violations to alerting rules (e.g., Prometheus `alert: NonCompliantAPICall`).

### **3.2 Technical Considerations**
- **Sampling**: For high-volume systems, sample logs/traces (e.g., error-only compliance checks).
- **State Persistence**: Store compliance events in a dedicated database (e.g., Elasticsearch) for replayability.
- **False Positives**: Implement thresholds (e.g., "alert only if >3 violations in 5 mins").

---

## **4. Query Examples**
### **4.1 Log-Based Compliance Queries**
**Scenario**: Audit for missing `timestamp` in API logs (using ELK Stack).
**Query**:
```json
// Kibana Query DSL
{
  "query": {
    "bool": {
      "must_not": [
        { "exists": { "field": "timestamp" } }
      ],
      "filter": [
        { "term": { "path": "api/v1/data" } }
      ]
    }
  }
}
```
**Output**:
```json
[
  { "rule": "API_Timestamp_Validation", "violation": "missing_field", "log": "Request to /api/data at 2023-10-15T12:34:56" }
]
```

### **4.2 Trace-Based Compliance Queries**
**Scenario**: Flag traces where an API call bypasses auth (using OpenTelemetry).
**Query** (Jaeger):
```sql
SELECT * FROM traces
WHERE spans.name = 'auth_check'
AND (attr.key = 'auth_status' AND attr.value = 'failed') LIMIT 100;
```

### **4.3 Metric-Based Alerts**
**Scenario**: Alert if >1% of requests fail compliance checks (Prometheus).
```yaml
# Alert rule in Prometheus
groups:
- name: compliance_alerts
  rules:
  - alert: NonCompliantRequestsSpike
    expr: rate(compliance_checks_failed_total[5m]) / rate(http_requests_total[5m]) > 0.01
    for: 1m
    labels:
      severity: warning
    annotations:
      summary: "1%+ of requests failed compliance checks"
```

---

## **5. Related Patterns**
| **Pattern**               | **Description**                                                                 | **Relation to Compliance Debugging**                                                                 |
|---------------------------|---------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| **Observability Foundations** | Centralized logging, metrics, and tracing.                                    | Compliance Debugging **relies** on this pattern for telemetry data.                                  |
| **Chaos Engineering**     | Proactively test system failure scenarios.                                     | Use **Compliance Debugging** to validate recovery processes meet policy (e.g., "failover must log X"). |
| **Policy as Code**        | Enforce rules via software (e.g., OPA).                                      | **Compliance Debugging** implements runtime checks for these policies.                              |
| **Incident Response**     | Post-incident analysis workflows.                                              | **Compliance Debugging** provides forensic data for incident reviews (e.g., "Did this outage violate SLAs?"). |

---
## **6. Best Practices**
1. **Start Small**: Begin with critical policies (e.g., data encryption) before scaling.
2. **Automate Remediation**: Link alerts to workflows (e.g., "If MFA fails, rotate user keys").
3. **Audit Logs**: Ensure compliance checks are themselves logged (e.g., "Rule 'API_Timestamp_Validation' ran at 14:00").
4. **Collaborate with Security**: Align compliance rules with threat models (e.g., "Block API calls from untrusted IPs").

---
**Example Toolchain**:
| **Component**            | **Tools**                                                                 |
|--------------------------|---------------------------------------------------------------------------|
| Policy Definition        | Open Policy Agent (OPA), Terraform Policies                              |
| Logging/Tracing          | Loki, OpenTelemetry, ELK                                                |
| Alerting                 | Prometheus, PagerDuty, Slack                                             |
| Storage                  | PostgreSQL, Elasticsearch, Datadog                                         |

---
**Footer**:
*This guide assumes familiarity with observability tools and basic automation. For policy-specific compliance (e.g., GDPR), consult legal/regulatory documentation.*