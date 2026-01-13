# **[Pattern] Deterministic Authorization Enforcement – Reference Guide**

---

## **Overview**
This pattern enforces consistent, auditable authorization decisions by **pre-compiling rule logic into structured metadata** rather than relying on runtime resolvers or dynamic logic. Unlike traditional authorization models that evaluate permissions dynamically (e.g., role-based or attribute-based access control), this approach uses **immutable, versioned rule sets** to ensure deterministic outcomes. This guarantees that **no two requests with identical inputs ever receive different authorization decisions**, improving security, compliance, and observability.

Key benefits:
- **Predictability**: Decisions are repeatable for the same inputs.
- **Auditability**: Rules are version-controlled and immutable.
- **Performance**: Eliminates runtime evaluation overhead.
- **Scalability**: Stateless decisions enable horizontal scaling.

---

## **Key Concepts**

| **Term**               | **Definition**                                                                                     | **Example**                                                                                     |
|------------------------|---------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Rule Set**           | A collection of deterministic policies encoded as metadata.                                         | `{ "allow": "user:write" → { "resource": "app:doc", "action": "update" } }`                  |
| **Metadata Rule**      | A compiled permission rule with fixed inputs (not generated at runtime).                         | `allow { user_id: "123", resource_type: "invoice", action: "view" }`                          |
| **Rule Versioning**    | Rules are tagged with immutable versions to track policy state over time.                          | `rule_set_001_v2` (backward-compatible updates enforced)                                        |
| **Decision Engine**    | A lightweight component that applies metadata rules to incoming requests.                         | `if (rule_set_001_v2.match(request.user_id, request.action)) { allow(); }`                     |
| **Request Fingerprint**| A hash of request attributes used to select the appropriate rule set.                             | `sha256(user_id || action || resource_id)`                                                      |
| **Audit Log**          | Immutable record of rule matches/denials with metadata (user, rule set, timestamp).              | `[{ "request": { "user_id": "123" }, "rule": "rule_set_001_v2", "decision": "allow", "ts": "2024-01-01" }]` |

---

## **Schema Reference**
### **1. Rule Set Definition**
A rule set is a JSON object with **immutable policies** and versioning metadata.

```json
{
  "id": "rule_set_001",
  "version": "v2",
  "schema_version": "1.0.0",
  "policies": [
    {
      "id": "policy_user_write_documents",
      "description": "Allow users to update their own documents.",
      "rules": [
        {
          "condition": {
            "type": "attribute_match",
            "selector": {
              "user_id": "{user_id}",
              "resource_type": "document",
              "action": "update"
            },
            "operator": "equals"
          },
          "action": "allow"
        }
      ],
      "expiry": "2025-12-31"  // Optional: Soft expiry for compliance
    }
  ]
}
```

---

### **2. Request Input Schema**
Requests include **fingerprintable attributes** and an optional `rule_set_override` for testing.

```json
{
  "user_id": "abc123",
  "resource_id": "doc_456",
  "action": "update",
  "rule_set_override": "rule_set_001_v2"  // Defaults to latest stable if omitted
}
```

---

### **3. Decision Output Schema**
The response includes a **deterministic result** and traceability metadata.

```json
{
  "authorized": true,
  "rule_match": {
    "rule_set_id": "rule_set_001_v2",
    "policy_id": "policy_user_write_documents",
    "matching_rule_id": "rule_001"
  },
  "audit_traces": [
    {
      "timestamp": "2024-01-01T12:00:00Z",
      "decision": "allow",
      "user_agent": "browser/Chrome_120"
    }
  ]
}
```

---

## **Query Examples**

### **1. Basic Rule Match**
**Request**:
```json
{
  "user_id": "abc123",
  "resource_id": "doc_456",
  "action": "update"
}
```

**Response**:
```json
{
  "authorized": true,
  "rule_match": {
    "rule_set_id": "rule_set_001_v2",
    "policy_id": "policy_user_write_documents"
  }
}
```

---
### **2. Denial with Explicit Reason**
**Request**:
```json
{
  "user_id": "xyz789",
  "resource_id": "doc_456",  // User doesn’t own this doc
  "action": "update"
}
```

**Response**:
```json
{
  "authorized": false,
  "denial_reason": "policy_user_write_documents: User does not match document owner."
}
```

---
### **3. Rule Set Version Override**
**Request** (testing a future version):
```json
{
  "user_id": "abc123",
  "action": "delete",
  "rule_set_override": "rule_set_001_v3"  // New version may block deletions
}
```

**Response**:
```json
{
  "authorized": false,
  "rule_match": {
    "rule_set_id": "rule_set_001_v3",
    "denial_reason": "Deletion requires admin approval."
  }
}
```

---

## **Implementation Steps**

### **1. Define Rule Sets**
- Use a **policy-as-code** tool (e.g., Open Policy Agent, Springside) to generate metadata rules.
- Enforce **immutability**: Rules cannot be modified post-deployment (use versioned copies).

### **2. Compile Rules**
Convert high-level policies (e.g., JSON/YAML) into optimized metadata:
```bash
# Example: Compile with a policy compiler
policy-compile -i policy.yaml -o rules/rule_set_001_v2.json
```

### **3. Deploy Rule Sets**
Store rules in a **version-controlled repository** (Git) or **immutable storage** (e.g., S3 with object locking).

### **4. Integrate with Decision Engine**
Embed a lightweight engine (e.g., embedded in microservices) to:
1. Hash request attributes to select the rule set.
2. Apply the rule set to determine the decision.

```python
# Pseudocode for decision engine
def authorize(request, rule_set):
    fingerprint = hash(request.user_id + request.action)
    matching_rule = rule_set.policies[fingerprint].rules[0]
    return matching_rule.action == "allow"
```

### **5. Log All Decisions**
Use a **write-ahead log** (e.g., Kafka, ELK) to record:
- Request attributes.
- Rule set version.
- Decision (`allow`/`deny`).
- Timestamp and user context.

---
## **Performance Considerations**
| **Component**          | **Optimization**                                                                 |
|------------------------|---------------------------------------------------------------------------------|
| **Rule Storage**       | Use **L2/L3 caching** (Redis) for hot rule sets.                                 |
| **Fingerprinting**     | Precompute hashes for common request patterns to reduce runtime cost.           |
| **Decision Engine**    | Deploy as a **stateless service** (e.g., AWS Lambda) to scale horizontally.    |
| **Audit Logs**         | Batch-write logs to minimize I/O overhead.                                       |

---

## **Related Patterns**
1. **[Policy as Code](https://www.oreilly.com/library/view/building-secure-software/9781491976564/ch05.html)**
   *Defines authorization logic in declarative files for versioning and collaboration.*

2. **[Attribute-Based Access Control (ABAC)](https://www.ietf.org/rfc/rfc7159)**
   *Extends authorship by evaluating dynamic attributes (e.g., time-of-day).*
   **Difference**: ABAC may introduce runtime variability; this pattern enforces determinism.

3. **[Immutable Infrastructure](https://www.oreilly.com/library/view/designing-data-intensive-applications/9781491903063/ch04.html)**
   *Aligns with rule set versioning to avoid drift.*

4. **[Permissionless API Design](https://auth0.com/blog/permissionless-api-design/)**
   *Complements this pattern by reducing reliance on runtime checks.*

---
## **Anti-Patterns to Avoid**
| **Anti-Pattern**               | **Risk**                                                                 | **Mitigation**                                  |
|---------------------------------|--------------------------------------------------------------------------|------------------------------------------------|
| **Dynamic Rule Generation**     | Introduces unpredictability.                                             | Pre-compile all rules.                          |
| **Runtime Policy Injection**    | Bypasses auditability.                                                   | Use immutable rule sets only.                  |
| **No Rule Versioning**         | Hard to track changes or roll back.                                     | Tag all rule sets with immutable versions.     |
| **Overly Complex Conditions**   | Slows decision-making.                                                   | Simplify rules; split into smaller policies.    |

---
## **Tools & Libraries**
| **Tool**                     | **Purpose**                                                                 |
|------------------------------|-----------------------------------------------------------------------------|
| [Open Policy Agent (OPA)](https://www.openpolicyagent.org/) | Compiles policies to Rego (deterministic DSL).                           |
| [Springside](https://springside.dev/) | Generates metadata rules from YAML/JSON.                                   |
| [AWS IAM Policy Simulator](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_simulator.html) | Test rule sets in AWS environments.                                        |
| [Grafana Loki](https://grafana.com/oss/loki/) | Store and query audit logs.                                                |
| [Calypto](https://www.calyptosystems.com/) | Commercial deterministic auth enforcement tool.                            |

---
## **When to Use This Pattern**
✅ **Use when**:
- You need **auditable, repeatable** decisions (e.g., financial systems, healthcare).
- **Performance** is critical (e.g., high-throughput APIs).
- Rules must be **version-controlled** (e.g., compliance requirements).

❌ **Avoid when**:
- Authorization **must** adapt to runtime conditions (e.g., dynamic group memberships).
- Rules are **frequently updated** (use a hybrid model instead).

---
## **Example Workflow: E-Commerce Order Processing**
1. **Rule Set**:
   ```json
   {
     "id": "order_processing_v1",
     "policies": [
       {
         "id": "customer_fulfillment",
         "rules": [
           { "condition": { "user.is_cart_owner": true }, "action": "allow" }
         ]
       }
     ]
   }
   ```
2. **Request**:
   ```json
   { "user_id": "user_42", "cart_id": "cart_99", "action": "fulfill" }
   ```
3. **Decision**:
   ```json
   { "authorized": true, "rule_match": { "rule_set_id": "order_processing_v1" } }
   ```
4. **Audit Log Entry**:
   ```json
   { "user": "user_42", "action": "fulfill", "ts": "2024-01-01", "rule_set": "order_processing_v1" }
   ```

---
## **Further Reading**
- [Deterministic vs. Non-Deterministic Authorization](https://auth0.com/blog/deterministic-authorization/)
- [Immutable Infrastructure Patterns](https://www.oreilly.com/library/view/designing-data-intensive-applications/9781491903063/ch04.html)
- [RFC 7608: Attribute-Based Access Control](https://datatracker.ietf.org/doc/html/rfc7608)