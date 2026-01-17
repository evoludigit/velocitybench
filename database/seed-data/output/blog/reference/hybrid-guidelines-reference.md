# **[Pattern] Hybrid Guidelines Reference Guide**

## **Overview**
The **Hybrid Guidelines** pattern enables applications to enforce *localized compliance* while allowing flexibility for dynamic or user-specific configurations. Unlike rigid **Strict** or **Adaptive** heuristic rules, Hybrid Guidelines blend predefined constraints with context-aware adjustments, ensuring consistency where needed while accommodating nuanced exceptions. This pattern is ideal for systems where regulatory compliance, industry standards, or best practices must coexist with personalized or situational overrides.

Hybrid Guidelines are structured as a **two-tier hierarchy**:
1. **Fixed Rules** – Non-negotiable constraints (e.g., GDPR compliance for data processing).
2. **Modifiable Overrides** – Customizable exceptions or preferences (e.g., a user’s preferred date format).

This separation ensures traceability for audits while permitting granular control. The pattern is commonly used in **enterprise workflows, AI-driven systems, and multi-tenant applications** where compliance must align with variability.

---

## **Schema Reference**

| **Field**               | **Type**       | **Description**                                                                 | **Constraints**                          | **Example**                          |
|-------------------------|----------------|-------------------------------------------------------------------------------|------------------------------------------|--------------------------------------|
| `guideline_id`          | `String` (UUID)| Unique identifier for the guideline.                                          | Required, immutable                     | `"550e8400-e29b-41d4-a716-446655440000"` |
| `name`                  | `String`       | Human-readable title (e.g., "Payment Terms Compliance").                      | Max 128 chars, unique within scope      | `"Data Retention Policy"`            |
| `version`               | `String`       | Semantic version (e.g., `1.2.0`).                                             | Immutable; follows [SemVer](https://semver.org). | `"2.1.3"`                           |
| `severity`              | `Enum`         | Priority level: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`.                          | Default: `MEDIUM`                       | `"HIGH"`                             |
| `scope`                 | `Array<String>`| Target entities (e.g., `["users", "contracts", "api-endpoints"]`).            | At least one required                   | `["contracts", "invoices"]`           |
| `is_fixed`              | `Boolean`      | Whether the guideline is immutable (`true`) or modifiable (`false`).          | Overrides take precedence if `false`    | `true`                               |
| `rules`                 | `Object`       | **Fixed Rules** (non-editable):                                              |                                      |                                      |
| &nbsp;&nbsp;`condition` | `String`       | Business logic (e.g., `user.role === "admin" && region === "EU"`).           | Must validate against schema constraints | `"contract.amount > 10000"`            |
| &nbsp;&nbsp;`action`    | `String`       | Enforced behavior (e.g., `log_audit`, `reject_transaction`).                | Must map to system endpoints            | `"log_audit"`                        |
| `overrides`             | `Object`       | **Modifiable Overrides** (user/system-specific):                              |                                      |                                      |
| &nbsp;&nbsp;`policy`    | `String`       | Override rule (e.g., `default_currency: "USD"`).                            | Optional; overrides `rules` if `is_fixed: false` | `"default_currency: 'GBP'"` |
| &nbsp;&nbsp;`priority`  | `Number`       | Override precedence (higher = applied first).                               | Range: `1–1000`                         | `50`                                 |
| `metadata`              | `Object`       | Non-functional attributes (e.g., `created_at`, `author`).                     | Optional                               | `{ "author": "compliance-team" }`    |
| `valid_from`            | `Date`         | Effective date (UTC).                                                         | Future dates allowed                    | `"2024-01-15T00:00:00Z"`              |

**Example JSON Payload:**
```json
{
  "guideline_id": "550e8400-e29b-41d4-a716-446655440001",
  "name": "Tax Reporting",
  "version": "1.0.0",
  "severity": "HIGH",
  "scope": ["tax_reports", "financial_audit"],
  "is_fixed": false,
  "rules": {
    "condition": "report.status === 'pending' && report.country === 'USA'",
    "action": "flag_for_review"
  },
  "overrides": [
    {
      "policy": "exception_threshold: 500000",
      "priority": 80,
      "metadata": { "justification": "bulk_filing_exemption" }
    }
  ],
  "valid_from": "2023-11-01T00:00:00Z"
}
```

---

## **Implementation Details**

### **1. Key Concepts**
- **Fixed Rules**:
  - Enforced via system policies (e.g., "All contracts must include a 7-day cooling period").
  - Immutable unless explicitly upgraded via `guideline_id`.
- **Modifiable Overrides**:
  - Allowed for administrators/users with elevated permissions.
  - Stored in a separate index for versioning and rollback capability.
- **Context-Aware Evaluation**:
  - Overrides are evaluated **only if the fixed condition is met**.
  - Priority determines which override applies (e.g., higher `priority` overrides lower).

### **2. Storage & Caching**
- **Fixed Rules**: Stored in a **read-only database** (e.g., PostgreSQL) with versioning.
- **Overrides**: Cached in **Redis** for low-latency access; flushed on policy updates.
- **Conflict Resolution**:
  - If an override conflicts with a fixed rule, emit a **warning log** and apply the override (configurable).

### **3. Validation**
- **Schema Enforcement**:
  - Use **JSON Schema** to validate payloads (e.g., `severity` must be in `["CRITICAL", "HIGH", ...]`).
  - Example schema snippet:
    ```json
    {
      "$schema": "http://json-schema.org/draft-07/schema#",
      "properties": {
        "is_fixed": { "type": "boolean", "description": "Immutable if true" }
      }
    }
    ```
- **Condition Validation**:
  - Fixed `condition` strings are evaluated via **server-side Templ** or **OpenPolicyAgent**.

### **4. API Endpoints**
| **Endpoint**                          | **Method** | **Description**                                                                 | **Response Example**                     |
|----------------------------------------|------------|---------------------------------------------------------------------------------|------------------------------------------|
| `/v1/guidelines/{guideline_id}`       | `GET`      | Fetch guideline (fixed + overrides).                                           | `200 OK` with merged rules.              |
| `/v1/guidelines/{guideline_id}/overrides` | `POST`    | Add/modify overrides (admin-only).                                              | `201 Created` or `403 Forbidden`.        |
| `/v1/guidelines/evaluate`             | `POST`     | Apply guidelines to a payload (e.g., contract).                                | `{ "compliance": true, "warnings": [...] }` |
| `/v1/guidelines/upgrade`              | `PATCH`    | Modify fixed rules (requires `version` bump).                                  | `200 OK` with new `guideline_id`.        |

---

## **Query Examples**

### **1. Fetch a Guideline with Overrides**
```bash
curl -X GET \
  "https://api.example.com/v1/guidelines/550e8400-e29b-41d4-a716-446655440001" \
  -H "Authorization: Bearer xxxx"
```
**Response**:
```json
{
  "rules": {
    "condition": "user.age >= 18",
    "action": "allow_access"
  },
  "overrides": [
    {
      "policy": { "waiver": true },
      "priority": 100,
      "metadata": { "granted_by": "admin_42" }
    }
  ]
}
```

### **2. Evaluate Compliance**
```bash
curl -X POST \
  "https://api.example.com/v1/guidelines/evaluate" \
  -H "Content-Type: application/json" \
  -d '{
    "guideline_id": "550e8400-e29b-41d4-a716-446655440001",
    "context": {
      "user": { "age": 17, "role": "guest" },
      "action": "checkout"
    }
  }'
```
**Response**:
```json
{
  "compliant": false,
  "reasons": ["user_age_mismatch"],
  "overrides_applied": []
}
```

### **3. Add an Override (Admin)**
```bash
curl -X POST \
  "https://api.example.com/v1/guidelines/550e8400-e29b-41d4-a716-446655440001/overrides" \
  -H "Authorization: Bearer admin-xxxx" \
  -d '{
    "policy": "age_threshold: 16",
    "priority": 90,
    "metadata": { "reason": "underage_exemption" }
  }'
```
**Response**:
```json
{
  "status": "success",
  "override_id": "override_789..."
}
```

---

## **Requirements & Edge Cases**
| **Scenario**                          | **Action**                                                                                     |
|----------------------------------------|------------------------------------------------------------------------------------------------|
| **Override Conflict**                  | Log warning; apply override (configurable).                                                    |
| **Fixed Rule Violation**               | Reject transaction/update; emit audit log.                                                      |
| **Empty Overrides**                    | Fall back to fixed rules.                                                                    |
| **Concurrent Override Updates**        | Use **optimistic locking** (e.g., `version` field in override payload).                       |
| **Deprecated Guidelines**              | Set `valid_from` in the future; flag via `metadata.deprecated: true`.                          |

---

## **Related Patterns**
1. **[Strict Heuristics]**
   - **Difference**: No overrides allowed; guidelines are fully immutable.
   - **Use Case**: Highly regulated industries (e.g., healthcare, finance) where no exceptions exist.

2. **[Adaptive Rules]**
   - **Difference**: Dynamic rules adjust based on ML models or real-time data; no fixed hierarchy.
   - **Use Case**: Personalized recommendations or fraud detection.

3. **[Policy-as-Code]**
   - **Relation**: Hybrid Guidelines can be stored/versioned as code (e.g., Terraform modules).
   - **Tooling**: Integrate with **Open Policy Agent (OPA)** or **Kyverno** for Kubernetes.

4. **[Audit Logging]**
   - **Complement**: Log all override applications and fixed-rule violations for compliance tracking.

5. **[Canary Deployments]**
   - **Use Case**: Test new Hybrid Guidelines in parallel with legacy rules before full rollout.

---
**See Also**:
- [Schema Validation Best Practices](https://json-schema.org/understanding-json-schema/)
- [Semantic Versioning](https://semver.org/)
- [OpenPolicyAgent Documentation](https://www.openpolicyagent.org/docs/latest/)