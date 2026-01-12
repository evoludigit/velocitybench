# **[Pattern] Compliance Validation – Reference Guide**

---

## **Overview**
The **Compliance Validation** pattern ensures that data, configurations, or processes adhere to predefined regulatory, policy, or industry standards. This pattern is critical for systems handling sensitive data (e.g., healthcare, finance, or legal) where non-compliance risks fines, legal action, or operational failures. It automates checks against rules—such as GDPR, HIPAA, or PCI-DSS—during runtime or as part of workflows (e.g., data ingestion, API calls, or system updates).

The pattern typically consists of:
- **Validation rules** (static or dynamic) defining compliance criteria.
- **Rule engine** to evaluate inputs against rules.
- **Audit logging** to track validation outcomes and deviations.
- **Remediation mechanisms** to correct non-compliance (e.g., data masking, notifications).

Common use cases include:
- Verifying patient data against HIPAA privacy rules.
- Checking API requests for PCI-DSS tokenization requirements.
- Validating cloud configurations for SOC 2 compliance.

---

## **Schema Reference**
Below are core components of the **Compliance Validation** pattern, with JSON-like schema structures for clarity.

| **Component**          | **Description**                                                                 | **Schema Example**                                                                                     |
|-------------------------|-------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| **Rule Definition**     | Defines validation rules (mandatory fields, regex, custom logic).            | ```{ "id": "r1", "name": "GDPR-PII-Validation", "type": "regex", "pattern": "^[A-Z]{2}-\d{3}-\d{2}-\d{4}$", "scope": ["person_name", "address"] }``` |
| **Rule Engine**         | Executes rules (supports chained, sequential, or parallel validation).        | ```{ "engine": "lua", "pipeline": [ {"rule": "r1", "action": "fail"}, {"rule": "r2", "action": "warn"} ] }``` |
| **Input Data Model**    | Structure of data subject to validation (e.g., JSON payload, database record). | ```{ "type": "object", "properties": { "patient_id": { "type": "string", "format": "uuid" }, "ssn": { "type": "string", "pattern": "^\\d{3}-\\d{2}-\\d{4}$" } } }``` |
| **Validation Outcome**  | Result of rule execution (pass/fail) + metadata.                            | ```{ "status": "failed", "rule_id": "r1", "reason": "Invalid SSN format", "timestamp": "2024-02-20T12:00:00Z" }``` |
| **Audit Log Entry**     | Immutable record of validation events for compliance reporting.            | ```{ "event_id": "aud-123", "user": "admin", "action": "validate", "result": "failed", "data": { ... } }``` |
| **Remediation Trigger** | Actions to resolve non-compliance (e.g., reformat data, alert admin).       | ```{ "type": "alert", "recipient": ["security-team@example.com"], "severity": "high" }```               |

---

## **Key Implementation Details**

### **1. Rule Types**
Validation rules can be categorized by complexity and source:
- **Static Rules**: Hardcoded logic (e.g., "email must match `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`").
- **Dynamic Rules**: Retrieved from external systems (e.g., "check user role against LDAP").
- **Custom Rules**: Business-specific logic (e.g., "verify tax ID against IRS database").

**Example Dynamic Rule (API Fetch):**
```json
{
  "type": "http",
  "url": "https://api.irs.gov/v1/tax_id/validate",
  "method": "POST",
  "headers": { "Authorization": "Bearer ${API_KEY}" },
  "expected_status": 200
}
```

---

### **2. Rule Engine Options**
| **Engine**       | **Pros**                                  | **Cons**                                  | **Use Case**                          |
|-------------------|-------------------------------------------|-------------------------------------------|----------------------------------------|
| **Lua Scripting** | Lightweight, embedded.                   | Limited to Lua syntax.                   | Edge devices, IoT compliance checks.  |
| **OpenPolicyAgent (OPA)** | Standardized, policy-as-code.          | Steeper learning curve.                  | Kubernetes, cloud compliance.        |
| **Custom (Java/Python)** | Full control over logic.               | Higher maintenance.                      | Enterprise-grade validation.         |
| **No-Code (Zapier/Make)** | Drag-and-drop rules.                     | Scalability limits.                      | Small teams, ad-hoc workflows.        |

---

### **3. Data Flow**
1. **Input**: Data enters the system (e.g., API request, database query).
2. **Preprocessing**: Normalize data (e.g., parse JSON, clean whitespace).
3. **Validation**: Apply rules in sequence/parallel.
4. **Outcome**: Return `pass/fail` + metadata; log to audit system.
5. **Remediation**: Trigger corrective actions (e.g., mask PII, escalate alert).

**Visual Flow**:
```
Input Data → [Preprocess] → [Rule Engine] → [Audit Log] → [Remediate]
```

---

### **4. Performance Considerations**
- **Rule Optimization**:
  - Cache frequent checks (e.g., regex compilation).
  - Batch validation for bulk operations.
- **Parallelization**:
  - Use worker pools for independent rules (e.g., 10 rules in parallel).
- **Caching**:
  - Store validation outcomes for repeated inputs (e.g., "user_X@example.com" → `valid`).

---

## **Query Examples**
### **1. Validate GDPR-Compliant Email**
**Request** (API):
```http
POST /validate/gdpr
Content-Type: application/json

{
  "email": "user@example.com",
  "rules": ["email-format", "domain-whitelist"]
}
```
**Response**:
```json
{
  "status": "pass",
  "rules": {
    "email-format": { "valid": true },
    "domain-whitelist": { "valid": true, "allowed_domains": ["example.com", "company.org"] }
  }
}
```

---

### **2. Check PCI-DSS Credit Card Token**
**Request** (Database Trigger):
```sql
-- Pseudocode for PostgreSQL
DO $$
BEGIN
  PERFORM validate_credit_card_token('4111111111111111', 'token_123', 'PCI-DSS');
  IF NOT FOUND THEN
    RAISE EXCEPTION 'Token validation failed: Checksum mismatch';
  END IF;
END $$;
```
**Rule Logic**:
```python
# Pseudocode for checksum validation
def validate_token(card_number: str, token: str) -> bool:
    return luhn_check(card_number) and token.startswith("tok_")
```

---

### **3. Dynamic HIPAA Field Masking**
**Request** (Microservice):
```http
POST /mask/hipaa
Content-Type: application/json

{
  "data": {
    "ssn": "123-45-6789",
    "patient_name": "John Doe"
  },
  "rules": ["mask-ssn", "partial-name"]
}
```
**Response** (Masked Output):
```json
{
  "data": {
    "ssn": "***-***-6789",
    "patient_name": "John ***"
  },
  "rules_applied": ["mask-ssn", "partial-name"]
}
```

---

## **Handling Edge Cases**
| **Scenario**               | **Solution**                                                                 |
|-----------------------------|-----------------------------------------------------------------------------|
| **Rule Conflicts**          | Prioritize rules via `weight` field or explicit dependencies.              |
| **Performance Bottlenecks** | Use async validation for non-critical rules (e.g., log only).               |
| **Rule Changes**            | Version rules (e.g., `rule_v1`, `rule_v2`) and use feature flags.           |
| **False Positives**         | Add "whitelist" exceptions (e.g., `exclude_domains: ["internal.test"]`).  |
| **Data Volume**             | Stream validation (e.g., Kafka topics) for real-time systems.              |

---

## **Related Patterns**
1. **[Data Masking]**
   - *Use Case*: Complements validation by obscuring sensitive data during transit/storage.
   - *Integration*: Apply masking *after* validation fails (e.g., fail-open with masked output).

2. **[Event Sourcing]**
   - *Use Case*: Log validation events as immutable audit trails.
   - *Integration*: Store `ComplianceValidationEvent` objects in an event store.

3. **[Canary Releases]**
   - *Use Case*: Test rule changes in staging before full deployment.
   - *Integration*: Route 5% of traffic through new validation rules.

4. **[Policy as Code]**
   - *Use Case*: Define rules in infrastructure-as-code (e.g., Terraform modules).
   - *Integration*: Validate IaC templates against compliance policies pre-deploy.

5. **[Rate Limiting]**
   - *Use Case*: Prevent brute-force attacks on validation endpoints.
   - *Integration*: Apply rate limits to `/validate` endpoints.

---

## **Best Practices**
1. **Rule Maintainability**:
   - Use a **rule registry** (e.g., database/table) to manage definitions centrally.
   - Tag rules by compliance standard (e.g., `tag: GDPR`, `tag: HIPAA`).

2. **Testing**:
   - **Unit Tests**: Mock inputs for each rule (e.g., test `validate_ssn()` with valid/invalid formats).
   - **Integration Tests**: Simulate real-world data flows (e.g., API → Validation → Audit).

3. **Documentation**:
   - Include **rule change logs** (e.g., "2024-02-15: Updated PCI-DSS card regex").
   - Provide **compliance mappings** (e.g., "Rule `r3` covers GDPR Article 9").

4. **Observability**:
   - Export metrics to tools like Prometheus (e.g., `validation_failures_total`).
   - Set up alerts for repeated failures (e.g., "Rule `r1` failed 5x in 1 hour").

5. **Automation**:
   - Integrate with CI/CD (e.g., fail build if new code triggers validation errors).
   - Use **pre-commit hooks** to validate SDK/config changes.

---
**Final Note**: The **Compliance Validation** pattern is most effective when embedded into the **data lifecycle** (ingest → process → store → retire). Pair it with **[Data Governance]** and **[Access Control]** patterns for end-to-end compliance.