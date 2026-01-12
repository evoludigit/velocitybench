---
# **[Pattern] Authorization Debugging Reference Guide**

---

## **1. Overview**
The **Authorization Debugging** pattern provides a structured approach to tracing, logging, and analyzing authorization decisions in applications. It ensures that security policies, access controls, and role-based permissions are correctly enforced and helps identify issues like incorrect denials or unexpected approvals.

This guide covers:
- Core concepts and debugging workflows.
- Schema and metadata definitions for observable logs.
- Practical query examples for analyzing authorization events.
- Integration with related security and observability patterns.

---

## **2. Key Concepts**

| **Term**               | **Definition**                                                                                     |
|------------------------|--------------------------------------------------------------------------------------------------|
| **Authorization Flow** | The sequence of steps (e.g., role validation, attribute checks, policy evaluation) that determine access. |
| **Decision Point**     | A specific step (e.g., RBAC check, ABAC condition) where a "yes/no" decision is made.            |
| **Policy Trace**       | A log of decisions made during an authorization request, including inputs, rules, and outcomes. |
| **Debug Context**      | A structured payload containing metadata (e.g., user ID, resource, time) to correlate logs.       |

---

## **3. Schema Reference**

### **Core Schema: `AuthorizationDecisionLog`**
```json
{
  "log_id": "unique-id-string",                  // Identifies this log entry
  "timestamp": "ISO8601-datetime",               // When the decision occurred
  "user_id": "user-identifier",                  // Identity of the requester
  "resource": {                                  // Target resource (e.g., API endpoint, file path)
    "id": "string",
    "type": "enum: [DATABASE, API, FILE_SYSTEM, etc.]",
    "name": "string"
  },
  "action": "string",                           // e.g., "CREATE", "UPDATE", "DELETE"
  "decision": "enum: [ALLOW, DENY, ABSTAIN]",     // Outcome of the check
  "policy_name": "string",                      // Name of the evaluated policy (e.g., "AdminAccessPolicy")
  "policy_version": "string",                   // Version of the policy (e.g., "v1.2")
  "decision_points": [                          // Array of individual decisions
    {
      "rule_id": "string",                      // Unique rule identifier (e.g., "rbac:admin")
      "rule_type": "enum: [RBAC, ABAC, OPA, etc.]", // Type of rule engine
      "input": {                                 // Input variables evaluated
        "user_role": "string",
        "resource_attribute": "string"
      },
      "output": {                                // Result of the rule
        "evaluated_to": "boolean",               // True/False for boolean checks
        "reason": "string"                       // Why the rule returned the result (e.g., "user lacks role")
      }
    }
  ],
  "context": {                                   // Additional metadata
    "ip_address": "string",
    "client_app": "string",
    "trace_id": "string"                         // Correlates with other logs (e.g., HTTP requests)
  }
}
```

---

## **4. Debugging Workflow**
Use the following steps to troubleshoot authorization issues:

1. **Capture Logs**:
   Log all `AuthorizationDecisionLog` events with sufficient context (e.g., `user_id`, `resource_id`).

2. **Reproduce the Issue**:
   Replicate the problematic scenario (e.g., a denied access request) and ensure logs are collected.

3. **Analyze Decisions**:
   Query logs to inspect:
   - Which **decision points** led to denial (`decision: DENY`).
   - Mismatches between **input** and **output** in rules (e.g., `user_role` vs. expected role).

4. **Compare Policies**:
   Check if the **policy_version** aligns with business requirements.

5. **Validate Context**:
   Correlate logs with other traces (e.g., `trace_id`) to understand the full user journey.

---

## **5. Query Examples**
### **Query 1: Find All Denied Requests for a Resource**
```sql
SELECT *
FROM authorization_decision_logs
WHERE decision = 'DENY'
  AND resource.id = 'api:orders'
ORDER BY timestamp DESC
LIMIT 10;
```

### **Query 2: Identify Rules That Block Users**
```sql
SELECT dp.rule_id, dp.rule_type, dp.output.reason
FROM authorization_decision_logs adl
JOIN decision_points dp ON adl.log_id = dp.log_id
WHERE adl.user_id = 'user-123'
  AND adl.decision = 'DENY'
  AND dp.output.evaluated_to = false;
```

### **Query 3: Track Policy Version Changes Over Time**
```sql
SELECT policy_name, policy_version, COUNT(*)
FROM authorization_decision_logs
GROUP BY policy_name, policy_version
ORDER BY COUNT(*) DESC;
```

### **Query 4: Correlate Debug Logs with HTTP Requests**
```sql
SELECT *
FROM authorization_decision_logs adl
JOIN http_requests hr ON adl.trace_id = hr.trace_id
WHERE hr.method = 'POST'
  AND hr.path = '/api/admin/delete';
```

---

## **6. Implementation Considerations**
- **Log Retention**: Retain debug logs for at least **30 days** (adjust based on compliance needs).
- **Performance**: Avoid excessive logging for high-frequency requests (e.g., API calls). Use sampling where appropriate.
- **Privacy**: Mask sensitive fields (e.g., `user_id`) in production logs unless explicitly needed.
- **Tooling Integration**: Leverage SIEM tools (e.g., Splunk, ELK) or custom dashboards for visualization.

---

## **7. Related Patterns**
| **Pattern**                     | **Description**                                                                                     | **When to Use**                                                                                     |
|----------------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| **Open Policy Agent (OPA)**      | Centralized policy enforcement engine for dynamic authorization.                                      | When policies require complex logic (e.g., attribute-based access control).                          |
| **Role-Based Access Control (RBAC)** | Assigns permissions based on predefined roles.                                                       | Simplifying permissions management for large teams.                                                 |
| **Observability for Security**   | Integrates security logging with monitoring/alerting systems.                                      | Detecting anomalies or policy violations in real-time.                                              |
| **Attribute-Based Access Control (ABAC)** | Grants access based on dynamic attributes (e.g., time, location).                                  | Scenarios with contextual access requirements (e.g., time-of-day restrictions).                      |

---

## **8. Example Debug Scenario**
**Problem**: Users with role `Editor` cannot update specific documents in the `Draft` status.

**Steps**:
1. Query logs for `Editor` users denied updates on `Draft` documents:
   ```sql
   SELECT *
   FROM authorization_decision_logs
   WHERE user_id IN (SELECT id FROM users WHERE role = 'Editor')
     AND resource.type = 'DOCUMENT'
     AND resource.status = 'Draft'
     AND action = 'UPDATE'
     AND decision = 'DENY';
   ```
2. Identify the failing rule (e.g., `abac:document_status_restriction`):
   ```sql
   SELECT dp.rule_id, dp.output.reason
   FROM decision_points dp
   JOIN authorization_decision_logs adl ON dp.log_id = adl.log_id
   WHERE adl.resource.status = 'Draft';
   ```
3. **Fix**: Update the policy to exclude `Editor` from the restriction or adjust the status check.

---
**See Also**:
- [OPA Debugging Guide](https://www.openpolicyagent.org/docs/latest/)
- [RBAC Best Practices](https://cloud.google.com/architecture/best-practices-for-role-based-access-control)