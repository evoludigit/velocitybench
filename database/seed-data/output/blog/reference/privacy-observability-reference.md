**[Pattern] Reference Guide: Privacy Observability**
*Version: 1.2*
*Last Updated: [Date]*

---

### **Overview**
Privacy Observability enables organizations to monitor, detect, and respond to privacy-related events (e.g., unintended data exposure, compliance breaches, or user consent violations) while preserving regulatory compliance (e.g., GDPR, CCPA). This pattern integrates privacy controls with observability tools (logs, metrics, and traces) to provide real-time visibility into data flows and user interactions.

Key use cases:
- **Data Leak Detection**: Monitor for unauthorized data exports or unauthorized access.
- **Consent Management**: Track user consent status and revocation requests.
- **Compliance Auditing**: Log and query privacy-related actions for regulatory reporting.
- **User Rights Support**: Validate "right to be forgotten" requests or data portability requests.

This guide covers schemas, query patterns, and integrations for implementing Privacy Observability.

---

## **1. Key Concepts**
### **Core Components**
| Concept               | Description                                                                                     | Example/Metric                          |
|-----------------------|-------------------------------------------------------------------------------------------------|-----------------------------------------|
| **Privacy Event**     | A record of a privacy-relevant action (e.g., consent granted, data deletion).                 | `{ event_id: "123", action: "consent", user_id: "456", timestamp: "2024-01-01" }` |
| **Data Flow Log**     | Tracks how user data moves through systems (e.g., API calls, database queries).                | `{ source: "auth_service", destination: "analytics_db", data_type: "PII" }` |
| **Anonymization Tag** | Metadata tagging to identify PII in logs (e.g., `user_email` or `payment_data`).             | `{ data_field: "email", field_type: "PII" }` |
| **Compliance Rule**   | Policy-based trigger for alerts (e.g., "Log all GDPR Article 30 records").                    | `{ rule_id: "gdpr_article_30", severity: "high" }` |
| **User Consent State**| Current status of user consent (e.g., "granted," "revoked," "pending").                       | `{ user_id: "789", consent_status: "revoked", timestamp: "2024-03-15" }` |

---
## **2. Schema Reference**
### **Core Schemas**
Use the following schemas to standardize Privacy Observability data in observability tools (e.g., OpenTelemetry, Prometheus, or custom systems).

#### **2.1. PrivacyEvent Schema**
```json
{
  "event_id": "string (UUID)",          // Unique identifier for the event.
  "user_id": "string (UUID)",           // Anonymous ID or hashed user reference (e.g., SHA-256).
  "action": "string (enum)",            // ["consent", "deletion", "access", "data_export", "audit"].
  "data_type": "string (enum)",         // ["PII", "payment", "location", "health", "other"].
  "timestamp": "datetime (ISO 8601)",   // When the event occurred.
  "source_system": "string",           // Originating service (e.g., "auth_service", "marketing_platform").
  "details": "object",                  // Additional context (e.g., { "requested_by": "user_agent" }).
  "compliance_tags": ["string"],        // Tags linking to compliance rules (e.g., ["gdpr", "ccpa"]).
  "anonymized_fields": ["string"]        // Fields redacted in logs (e.g., ["email", "phone"]).
}
```

#### **2.2. DataFlowLog Schema**
```json
{
  "flow_id": "string (UUID)",         // Unique flow identifier.
  "source": "string",                 // Origin system (e.g., "mobile_app", "web_portal").
  "destination": "string",            // Target system (e.g., "storage_bucket", "third-party_api").
  "data_type": "string (enum)",       // ["PII", "non_pii", "sensitive_pii"].
  "operation": "string (enum)",       // ["read", "write", "delete", "share"].
  "timestamp": "datetime (ISO 8601)", // When the flow occurred.
  "user_context": "object",           // Minimal user data (e.g., { "user_id": "123", "ip_address": "192.168.1.1" }).
  "compliance_rule": "string",        // Applicable rule (e.g., "gdpr_article_6").
  "sanitized_payload": "string"       // Redacted payload snippet (e.g., "[REDACTED] email=...").
}
```

#### **2.3. UserConsent Schema**
```json
{
  "user_id": "string (UUID)",         // User identifier (hashed if applicable).
  "consent_status": "string (enum)", // ["granted", "revoked", "pending", "withdrawn"].
  "timestamp": "datetime (ISO 8601)", // When status was updated.
  "consent_type": ["string"],         // ["analytics", "marketing", "profiling"].
  "jurisdiction": "string (enum)",   // ["gdpr", "ccpa", "schrems_ii"].
  "revocation_requested": "boolean",  // True if user requested revocation.
  "last_updated_by": "string",        // System/agent performing the update.
}
```

---
## **3. Query Examples**
### **3.1. Detecting Unauthorized Data Access**
**Query (LogQL/PromQL):**
```sql
# Logs of PII data writes without explicit consent
privacy_events
  | where action == "access" and data_type == "PII"
  | where compliance_tags contains "gdpr_article_9"
  | where consent_status != "granted"
| sort by timestamp desc
```
**Output Columns:**
| timestamp          | user_id  | action  | source_system | compliance_tags | consent_status |
|--------------------|----------|---------|---------------|-----------------|----------------|
| 2024-03-10T14:30:00 | 123abc   | access  | analytics_db  | ["gdpr_article_9"] | "revoked"      |

---

### **3.2. Tracking GDPR "Right to Erasure" Requests**
**Query (SQL-like):**
```sql
# Count deletions by user for GDPR compliance
SELECT
  user_id,
  COUNT(*) as deletion_count,
  MAX(timestamp) as last_deletion
FROM privacy_events
WHERE action = "deletion" AND compliance_tags = "gdpr_article_17"
GROUP BY user_id
ORDER BY deletion_count DESC;
```
**Output Columns:**
| user_id   | deletion_count | last_deletion          |
|-----------|----------------|------------------------|
| 456def    | 3              | 2024-03-05T09:15:00    |

---

### **3.3. Monitoring Data Flow Anomalies**
**Query (OpenTelemetry Trace Query):**
```
# Traces for suspicious data flows (e.g., PII shared externally)
traces
  | where spans.operation == "share_data"
  | where spans.attributes.data_type == "PII"
  | where spans.attributes.destination contains "third-party"
  | summarize count() by destination, user_context.ip_address
  | filter count() > 5  # Threshold for alerting
```
**Output:**
| destination          | ip_address        | count |
|----------------------|-------------------|-------|
| vendor_api_123.com   | 192.168.2.10      | 7     |

---

### **3.4. Auditing Consent Changes**
**Query (Time-Series Database):**
```sql
# Consent status changes over time
SELECT
  user_id,
  consent_status,
  timestamp
FROM user_consent
WHERE jurisdiction = "gdpr"
ORDER BY timestamp;
```
**Output:**
| user_id   | consent_status | timestamp          |
|-----------|----------------|--------------------|
| 789ghi    | revoked         | 2024-03-10T11:00:00 |
| 789ghi    | granted         | 2023-11-15T08:00:00 |

---

## **4. Implementation Best Practices**
### **4.1. Data Minimization**
- **Log Only Necessary Fields**: Avoid logging full PII (e.g., email addresses). Use hashes or aliases (e.g., `{ user_email: "[REDACTED]" }`).
- **Anonymize User IDs**: Replace direct user IDs with hashed/tokenized identifiers in logs.

### **4.2. Compliance Alignment**
| Regulation   | Key Observability Requirements                                      |
|--------------|------------------------------------------------------------------------|
| **GDPR**     | Log Article 30 records, track consent changes, monitor "right to erasure." |
| **CCPA**     | Audit data sales, honor opt-out requests, log consumer requests.       |
| **HIPAA**    | Monitor access to PHI, log security incidents.                         |
| **LGPD**     | Document data processing activities, enforce subject rights.           |

### **4.3. Tooling Integrations**
| Tool                | Implementation Notes                                                                 |
|---------------------|--------------------------------------------------------------------------------------|
| **OpenTelemetry**   | Extend `OpenTelemetry/SDK` to auto-tag PII fields in traces/logs.                     |
| **Prometheus/Grafana** | Use custom metrics for `privacy_events_total{status="failure"}`.                   |
| **ELK Stack**       | Use Filebeat to ingest `privacy_events` with PII redaction via Logstash filters.     |
| **AWS CloudTrail**  | Enable logs for S3/API Gateway with privacy compliance rules (e.g., IAM policies).  |
| **Datadog**         | Create dashboards for `privacy_events` with anomaly detection (e.g., spike in deletions). |

### **4.4. Alerting Rules**
| Rule ID               | Trigger Condition                                                                 | Action                          |
|-----------------------|-----------------------------------------------------------------------------------|---------------------------------|
| `leak_detected`       | `data_flow_logs` with `destination = "public_bucket"` and `data_type = "PII"`     | Escalate to security team.      |
| `consent_mismatch`    | `privacy_events.action = "access"` but `consent_status = "revoked"`               | Notify legal/compliance.        |
| `erasure_failure`     | `privacy_events.action = "deletion"` fails twice in a row.                         | Trigger backup verification.    |

---

## **5. Related Patterns**
| Pattern                          | Description                                                                                     | Integration Points                          |
|----------------------------------|-------------------------------------------------------------------------------------------------|----------------------------------------------|
| **[Event Sourcing for Privacy](https://...)** | Decouple privacy events into immutable event streams for auditing.                          | Share event schemas with Privacy Observability. |
| **[Data Masking](https://...)**    | Dynamically redact PII in queries/logs.                                                      | Use in `sanitized_payload` fields.           |
| **[Right to be Forgotten](https://...)** | Automate deletion workflows triggered by user requests.                                | Query `user_consent` for revocations.        |
| **[Privacy by Design](https://...)** | Embed privacy controls in system architecture (e.g., access controls, encryption).      | Log compliance checks in `privacy_events`.  |
| **[Real-Time Anonymization](https://...)** | Process data in transit to strip PII before storage.                               | Work with `DataFlowLog` for flow validation. |

---
## **6. Troubleshooting**
| Issue                          | Diagnosis                                                                 | Solution                                                                 |
|--------------------------------|----------------------------------------------------------------------------|---------------------------------------------------------------------------|
| **False Positives in Leak Alerts** | Alerts triggered by legitimate data exports (e.g., analytics).          | Add `compliance_tags` filter to exclude non-sensitive flows.               |
| **High Cardinality Logs**       | User IDs expand 1:1 in logs, degrading performance.                        | Use probabilistic data structures (e.g., HyperLogLog) for unique user counts. |
| **Consent State Drift**         | Discrepancies between `user_consent` and `privacy_events`.                 | Implement reconciliation jobs to sync sources.                              |
| **Tooling Latency**             | Alerts delayed in processing (e.g., Prometheus scraping).                   | Increase scrape interval or use edge nodes closer to data sources.          |

---
## **7. References**
- **GDPR Article 5 (Principle of Accountability)**: [EU GDPR Text](https://gdpr.eu/)
- **OpenTelemetry Privacy Extension**: [OTel Docs](https://opentelemetry.io/docs/specs/extensions/privacy/)
- **CCPA Jurisdiction Mapping**: [CCPA FAQ](https://oag.ca.gov/privacy/ccpa)
- **IEEE P7000 Standard**: [Privacy Engineering](https://standards.ieee.org/standard/7000-2016.html)