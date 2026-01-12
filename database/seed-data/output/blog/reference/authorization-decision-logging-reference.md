---
# **[Pattern] Authorization Decision Logging Reference Guide**

---

## **Overview**
Authorization **Decision Logging** is a pattern for systematically recording and tracking authorization outcomes—such as allow/deny decisions—within your application’s audit log. This ensures compliance with regulatory requirements (e.g., GDPR, HIPAA, PCI-DSS), enables forensic investigations, and aids in identifying security or access anomalies.

Implementing this pattern involves:
- Capturing **who**, **when**, and **how** an authorization decision was made.
- Storing detailed attributes (e.g., user identity, resource, action, decision, and context).
- Enabling querying and analysis of past decisions via structured logs.

This reference guide covers key concepts, implementation details, schema references, and query examples to ensure consistent and actionable logging.

---

## **Key Concepts**

| **Concept**               | **Description**                                                                                                                                                                                                 |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Authorization Decision** | A binary outcome (ALLOW/DENY) based on access control policies (e.g., RBAC, ABAC).                                                                                                                               |
| **Decision Log**          | A structured log entry recording the decision, including metadata like timestamps, requesting user, resource, and policy context.                                                                             |
| **Structured Logging**    | Logs formatted in a standardized way (e.g., JSON) for easy parsing, querying, and integration with monitoring tools (e.g., ELK, Splunk).                                                                  |
| **Audit Trail**           | A historical record of decisions to support compliance, security reviews, and troubleshooting.                                                                                                                  |
| **Policy Context**        | Additional details like conditions (e.g., "User role == Admin AND Time > BusinessHours") or dynamic attributes (e.g., device location) that influenced the decision.                                          |

---

## **Schema Reference**

Below is a recommended schema for **Authorization Decision Logs**. Adjust fields based on your organization’s security and compliance needs.

| **Field**               | **Type**   | **Description**                                                                                                      | **Example**                     |
|-------------------------|------------|----------------------------------------------------------------------------------------------------------------------|----------------------------------|
| **log_id**              | UUID       | Unique identifier for the log entry.                                                                                   | `a1b2c3d4-e5f6-7890-1234-567890`|
| **timestamp**           | ISO 8601   | When the decision was made (UTC).                                                                                   | `2024-01-15T14:30:45Z`           |
| **subject**             | String     | Identity of the requester (user/principal).                                                                           | `user:john.doe@company.com`      |
| **action**              | String     | The requested operation (e.g., `GET`, `DELETE`, `update_profile`).                                                     | `read_user_data`                 |
| **resource**            | String     | The target resource (e.g., API endpoint, database entry).                                                             | `/api/users/123`                 |
| **decision**            | Enum       | `ALLOW` or `DENY`.                                                                                                   | `DENY`                           |
| **policy**              | String     | Name of the policy engine or rule set used (e.g., `rbac`, `abac_geolocation`).                                      | `abac:location-based`            |
| **reason**              | String     | Human-readable explanation for the decision (e.g., "Missing 'admin' role").                                          | `User lacks 'edit' permission`   |
| **context**             | Object     | Key-value pairs of dynamic attributes (e.g., `{"ip": "192.168.1.5", "time": "15:30"}`).                             | `{ "time": "15:30", "device": "laptop" }` |
| **request_id**          | String     | Correlates with the original request (useful for distributed systems).                                               | `req_7890abc12`                  |
| **metadata**            | Object     | Additional application-specific fields (e.g., `{"client": "mobile_app", "version": "2.1"}`).                          | `{ "client": "web" }`             |

---
### **Example Log Entry**
```json
{
  "log_id": "a1b2c3d4-e5f6-7890-1234-567890",
  "timestamp": "2024-01-15T14:30:45Z",
  "subject": "user:john.doe@company.com",
  "action": "read_user_data",
  "resource": "/api/users/456",
  "decision": "DENY",
  "policy": "abac:geolocation",
  "reason": "Request originated from outside approved regions.",
  "context": {
    "ip": "203.0.113.45",
    "location": "Europe",
    "time": "15:30"
  },
  "request_id": "req_7890abc12"
}
```

---

## **Implementation Details**

### **1. Logging Integration**
- **Synchronous Logging**: Log decisions immediately after evaluation (e.g., in the auth middleware).
- **Asynchronous Logging**: Use a queue (e.g., Kafka, AWS Kinesis) for high-throughput systems to avoid latency.
- **Tooling**: Integrate with:
  - **Logging Frameworks**: Log4j, ساختار (Node.js), or Python’s `logging` module.
  - **Observability Platforms**: ELK Stack, Datadog, or CloudWatch for centralized storage and querying.

### **2. Policy Context Capture**
Include variables that impacted the decision, such as:
- **Dynamic Attributes**: User role, IP address, time of request.
- **Policy Rules**: Conditional logic (e.g., "Allow if `user.role == 'Admin' AND request.time > 9am`").

Example (ABAC Context):
```json
"context": {
  "user": { "role": "admin", "department": "engineering" },
  "resource": { "sensitivity": "high" },
  "time": "10:00"
}
```

### **3. Security Considerations**
- **Log Protection**: Encrypt logs at rest and in transit.
- **Retention Policy**: Comply with regulations (e.g., GDPR’s 6-month retention for personal data).
- **Audit Access**: Restrict log access to security teams only.

---

## **Query Examples**
Use structured logs to analyze authorization patterns. Below are example queries for common use cases.

### **Tools Supported**
- **ELK Stack** (Elasticsearch + Kibana)
- **Splunk**
- **AWS Athena** (for CloudWatch or S3-stored logs)

---

### **1. Find All Denied Requests for a User**
**Query (Elasticsearch/Kibana)**:
```json
GET /authorization_logs/_search
{
  "query": {
    "bool": {
      "must": [
        { "term": { "subject": "user:john.doe@company.com" } },
        { "term": { "decision": "DENY" } }
      ]
    }
  },
  "sort": [ { "timestamp": { "order": "desc" } } ]
}
```

**Output Columns**:
| **Timestamp**       | **Action**      | **Resource**       | **Reason**                          |
|---------------------|-----------------|--------------------|-------------------------------------|
| 2024-01-15 14:30:45 | read_user_data  | `/api/users/456`   | User lacks 'edit' permission        |
| 2024-01-14 09:15:22 | delete_record  | `/api/data/789`    | Insufficient privileges              |

---

### **2. Identify Location-Based Blocked Requests**
**Query (Splunk)**:
```splunk
index=authorization_logs
| search decision=DENY policy="abac:geolocation"
| stats count by _time, subject, resource, "context.location"
| sort -_time
```

**Output Columns**:
| **Time**            | **Subject**          | **Resource**       | **Location** |
|---------------------|----------------------|--------------------|--------------|
| 2024-01-15 14:00:00 | user:alice@example.com | `/api/config`      | Asia         |
| 2024-01-14 16:30:00 | user:bob@example.com   | `/api/data/123`    | Europe       |

---

### **3. Analyze Failed Login Attempts**
**Query (AWS Athena)**:
```sql
SELECT
  timestamp,
  subject,
  action,
  reason
FROM authorization_logs
WHERE action = 'authenticate'
  AND decision = 'DENY'
  AND reason LIKE '%failed%'
ORDER BY timestamp DESC
LIMIT 10;
```

**Output Columns**:
| **Timestamp**       | **Subject**          | **Action**      | **Reason**                          |
|---------------------|----------------------|-----------------|-------------------------------------|
| 2024-01-15 10:10:00 | user:guest@example.com | authenticate   | Incorrect password                  |
| 2024-01-14 11:45:00 | user:temp@test.com    | authenticate   | Account suspended                   |

---

### **4. Correlate Decisions with Requests**
**Query (ELK: Join with Request Logs)**:
```json
GET /authorization_logs/_search
{
  "query": {
    "bool": {
      "must": [
        { "term": { "request_id": "req_7890abc12" } }
      ]
    }
  }
}
```
Then join with:
```json
GET /request_logs/_search
{
  "query": {
    "term": { "id": "req_7890abc12" }
  }
}
```

---

## **Related Patterns**

| **Pattern**                          | **Description**                                                                                                                                                                                                 | **When to Use**                                                                                     |
|--------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| **Structured Logging**               | Standardize log formats (e.g., JSON) for machine readability.                                                                                                                                                   | Always pairing with Authorization Decision Logging.                                                  |
| **Audit Logging**                    | Record all system events (e.g., user logins, file access) for compliance.                                                                                                                               | When broader system auditing is required beyond auth decisions.                                      |
| **Policy as Code**                   | Define access policies in code (e.g., Open Policy Agent).                                                                                                                                                  | For dynamic, version-controlled policy enforcement.                                                  |
| **Just-In-Time Access (JIT)**        | Grant temporary access based on contextual approvals (e.g., VPN + MFA).                                                                                                                                | High-security environments requiring ephemeral permissions.                                          |
| **Attribute-Based Access Control (ABAC)** | Grant access based on attributes (e.g., user role, time, location).                                                                                                                                   | When fine-grained, context-aware policies are needed.                                                  |
| **Request Tracing**                  | Correlate auth decisions with broader request flows (e.g., distributed systems).                                                                                                                      | Debugging latency or failed transactions in microservices.                                           |

---

## **Best Practices**
1. **Consistency**: Use the same schema across all services to enable cross-service queries.
2. **Retention**: Align with compliance (e.g., GDPR’s 6 months for personal data) but avoid excessive costs.
3. **Performance**: Avoid logging excessively large payloads (e.g., entire request bodies).
4. **Redaction**: Mask sensitive data (e.g., PII) in logs unless compliance requires full disclosure.
5. **Automation**: Set up alerts for anomalous patterns (e.g., repeated denials for the same user).

---
## **Further Reading**
- [NIST SP 800-61](https://csrc.nist.gov/publications/detail/sp/800-61/rev-2/final) (Incident Handling Guide)
- [Open Policy Agent (OPA)](https://www.openpolicyagent.org/) (Policy-as-Code toolkit)
- [Elasticsearch Guide to Structured Logging](https://www.elastic.co/guide/en/elasticsearch/reference/current/logging.html)