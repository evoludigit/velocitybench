```markdown
---
title: "Compliance Profiling: Enforcing Rules Across Your API with Dynamic Policy Evaluation"
date: 2023-10-15
author: "Jane Doe"
tags: ["database design", "API patterns", "compliance", "security", "backend engineering"]
---

# Compliance Profiling: Enforcing Rules Across Your API with Dynamic Policy Evaluation

Regulations like [GDPR](https://gdpr-info.eu/), [HIPAA](https://www.hhs.gov/hipaa/), or [PCI DSS](https://www.pcisecuritystandards.org/) aren’t static—they evolve, and so do your business needs. Yet many systems treat compliance as a rigid checklist: "We implemented encryption," "We run audits quarterly," and "We’ll do the rest when we have time." This approach is brittle, scaling poorly as new rules emerge or as your organization grows.

The **Compliance Profiling** pattern is designed to address this gap. It allows you to model compliance requirements as dynamic, reusable policies that can be applied to data, operations, and user roles. By treating compliance like a first-class concern in your architecture—rather than an afterthought—you create systems that adapt to regulations without costly refactoring. This tutorial will take you through why compliance profiling matters, how to implement it, and how to avoid common pitfalls while maintaining performance and scalability.

---

## The Problem: When Compliance Stays Static

Compliance isn’t a one-time fix—it’s a **lifecycle problem**. Here’s what happens when you don’t treat it as such:

### 1. **Regulatory Catch-22: "We’ll comply later"**
   Many APIs are designed without considering compliance early, leading to retrofitting. For example:
   - A REST endpoint for PII (Personally Identifiable Information) might expose raw data instead of masking it.
   - Logging might include sensitive fields that violate auditability requirements.
   - User permissions might grant access to data without considering jurisdictions (e.g., GDPR’s right to erasure).

   **Real-world example:** A healthcare API might initially store patient records in plaintext, then scramble to anonymize them when HIPAA audits surface. The cost? Downtime, reputational damage, and fines.

### 2. **Fragmented Policies**
   Compliance rules often live in disparate silos:
   - Hardcoded checks (e.g., `if user.is_admin: allow`).
   - Ad-hoc middleware (e.g., a "GDPR filter" applied only to specific endpoints).
   - Human review processes (e.g., lawyers manually checking API contracts).

   This fragmentation makes it hard to:
   - Verify that all compliance rules are applied consistently.
   - Update policies when regulations change.
   - Trace compliance for audits.

### 3. **Performance and Scalability Bottlenecks**
   If compliance checks are synchronous and tightly coupled to business logic, they can slow down requests. For example:
   ```python
   # Example of a slow, coupled compliance check
   def get_user_data(user_id):
       user = db.query("SELECT * FROM users WHERE id = ?", user_id)
       if not user.is_gdpr_compliant:  # Expensive DB lookup!
           raise PermissionError("User not registered for GDPR")
       return user
   ```
   This forces every API call to wait for a compliance resolution, creating latency and scalability issues.

### 4. **Over/Under-Enforcement**
   - **Over-enforcement:** Blocking legitimate requests because of overly restrictive policies.
   - **Under-enforcement:** Allowing violations due to misconfigured or missing rules.

   Neither is ideal—over-enforcement frustrates users, while under-enforcement risks non-compliance.

---

## The Solution: Compliance Profiling

Compliance Profiling is a **declarative** way to model and enforce rules dynamically. It separates compliance logic from business logic, allowing you to:
- Define rules **once** and apply them **contextually** (e.g., per endpoint, per user, per data field).
- Test and validate rules independently.
- Scale checks to handle high-volume traffic.

At its core, this pattern involves:
1. **Policy definitions** (what the rules are).
2. **Policy context** (where and when to apply them).
3. **Policy evaluation** (how to enforce them without blocking performance).

---

## Components of the Compliance Profiling Pattern

### 1. **Policy Engine**
   A centralized system that defines, stores, and evaluates compliance rules. It can be:
   - **Embedded** (in-code rules, e.g., using decorators or middleware).
   - **Externalized** (rules stored in a database or config service).

   Example policy types:
   - **Data masking:** Redact PII in responses.
   - **Access control:** Restrict data by jurisdiction.
   - **Audit logging:** Track who accessed sensitive data.

### 2. **Context Providers**
   These inject runtime information (e.g., user location, request context) to determine which policies apply. Example providers:
   - **User context:** `user_id`, `user_role`, `user_jurisdiction`.
   - **Request context:** `endpoint`, `method`, `headers`.
   - **Data context:** `table_name`, `column_name`, `field_value`.

### 3. **Policy Registry**
   A catalog of available policies, often stored in a structured format (e.g., JSON, YAML). Example:
   ```json
   {
     "policies": {
       "gdpr_erasure": {
         "description": "Delete user data on request",
         "applies_to": ["users", "orders"],
         "conditions": ["user.jurisdiction === 'EU'"],
         "action": "mask_or_delete"
       },
       "hipaa_encryption": {
         "description": "Encrypt PHI at rest",
         "applies_to": ["patient_records"],
         "action": "encrypt_field"
       }
     }
   }
   ```

### 4. **Evaluation Strategy**
   Decide *when* and *how* to apply policies. Options:
   - **Pre-flight:** Evaluate before processing the request (fast rejection).
   - **Post-flight:** Evaluate after processing (slower, but allows recovery).
   - **Real-time:** Evaluate during processing (e.g., masking fields on-the-fly).

### 5. **Observability**
   Tools to track policyviolations, performance, and compliance status. Example metrics:
   - Number of blocked requests due to policy X.
   - Latency added by policy engine.

---

## Implementation Guide: A Step-by-Step Example

Let’s build a compliance-profiled API for a fictional healthcare platform, `HealthSync`, that must comply with **HIPAA** and **GDPR**.

### Step 1: Define Policies
Store policies in a database (e.g., PostgreSQL) for dynamic updates:
```sql
-- Policies table
CREATE TABLE compliance_policies (
  id UUID PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  description TEXT,
  applies_to TEXT[],  -- JSON array (e.g., ["user_profiles", "diagnoses"])
  conditions JSONB,   -- Key-value pairs for evaluation (e.g., {"user.jurisdiction": "EU"})
  action VARCHAR(50), -- e.g., "mask", "encrypt", "block"
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Example: GDPR right to erasure
INSERT INTO compliance_policies (
  id, name, description, applies_to, conditions, action
) VALUES (
  uuid_generate_v4(), 'gdpr_erasure', 'Mask PII for users in EU on request',
  ARRAY['users'], '{"user.jurisdiction": "EU"}', 'mask'
);
```

### Step 2: Create a Policy Engine
Write a service to evaluate policies dynamically. Here’s a Python example using FastAPI:
```python
from fastapi import FastAPI, Depends, HTTPException
from typing import List, Dict, Any
import json

app = FastAPI()

# Mock database of policies (in reality, query the `compliance_policies` table)
POLICIES_DB = {
    "gdpr_erasure": {
        "applies_to": ["users"],
        "conditions": {"user.jurisdiction": "EU"},
        "action": "mask"
    }
}

def evaluate_policies(
    policies: List[Dict[str, Any]],
    context: Dict[str, Any],
    data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Apply policies to data based on context (e.g., user, request).
    Returns filtered/masked data.
    """
    for policy in policies:
        if (policy["applies_to"] and not any(
            p in data.keys() for p in policy["applies_to"]
        )):
            continue  # Policy doesn’t apply to this data

        if not all(
            context.get(k) == v
            for k, v in policy["conditions"].items()
        ):
            continue  # Conditions not met

        # Apply the policy action (simplified)
        if policy["action"] == "mask":
            for field in policy["applies_to"]:
                if field in data and isinstance(data[field], str):
                    data[field] = "[MASKED]"  # Replace with actual masking logic
    return data

@app.get("/user/{user_id}")
def get_user(user_id: str, user: Dict = Depends(lambda: {"jurisdiction": "EU"})):
    # Simulate fetching user data
    user_data = {
        "id": user_id,
        "name": "John Doe",
        "ssn": "123-45-6789",
        "email": "john@example.com"
    }

    # Get relevant policies (in reality, query the DB)
    policies = [POLICIES_DB["gdpr_erasure"]]

    # Apply policies
    filtered_data = evaluate_policies(policies, user, user_data)

    return filtered_data
```

### Step 3: Add Context Providers
Extend the engine to support runtime context (e.g., user location from IP):
```python
from fastapi import Request
import geoip2.database

def get_user_context(request: Request) -> Dict[str, Any]:
    """
    Inject context from the request (e.g., user location, headers).
    """
    context = {"user": {}}

    # Example: Detect user jurisdiction from IP
    try:
        with geoip2.database.Reader('GeoLite2-City.mmdb') as reader:
            ip = request.client.host
            response = reader.city(ip)
            context["user"]["jurisdiction"] = response.country.iso_code
    except:
        context["user"]["jurisdiction"] = "US"  # Default

    return context

@app.get("/user/{user_id}")
def get_user(user_id: str, context: Dict = Depends(get_user_context)):
    user_data = {"id": user_id, "name": "John Doe", "ssn": "123-45-6789"}
    policies = [POLICIES_DB["gdpr_erasure"]]
    return evaluate_policies(policies, context, user_data)
```

### Step 4: Integrate with Database Operations
Extend the pattern to database queries. Here’s an SQL example using a PostgreSQL trigger to mask data on-the-fly:
```sql
-- Create a function to mask PII based on policies
CREATE OR REPLACE FUNCTION mask_pii_for_policy()
RETURNS TRIGGER AS $$
DECLARE
    masked_record RECORD;
BEGIN
    -- Simulate fetching policies (in reality, query your policies table)
    IF EXISTS (
        SELECT 1 FROM compliance_policies
        WHERE applies_to = ARRAY['users']
        AND conditions->>'user.jurisdiction' = 'EU'
        AND action = 'mask'
    ) THEN
        -- Mask sensitive fields (e.g., SSN, email)
        NEW.name = '[MASKED]';
        NEW.ssn = '[MASKED]';
        RETURN NEW;
    END IF;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

-- Apply the function to a trigger on the users table
CREATE TRIGGER mask_users_before_select
BEFORE SELECT ON users
FOR EACH ROW EXECUTE FUNCTION mask_pii_for_policy();
```

### Step 5: Add Observability
Log policy violations and performance:
```python
from prometheus_client import Counter, Histogram

# Metrics
POLICY_VIOLATIONS = Counter(
    'compliance_policy_violations',
    'Number of policy violations',
    ['policy_name', 'violation_type']
)
POLICY_LATENCY = Histogram(
    'compliance_policy_latency_seconds',
    'Time spent evaluating policies',
    ['policy_name']
)

@app.get("/user/{user_id}")
def get_user(user_id: str, context: Dict = Depends(get_user_context)):
    start_time = time.time()
    try:
        user_data = {"id": user_id, "name": "John Doe", "ssn": "123-45-6789"}
        policies = [POLICIES_DB["gdpr_erasure"]]
        filtered_data = evaluate_policies(policies, context, user_data)
    except Exception as e:
        POLICY_VIOLATIONS.labels("gdpr_erasure", str(e)).inc()
        raise HTTPException(status_code=403, detail=str(e))
    finally:
        POLICY_LATENCY.labels("gdpr_erasure").observe(time.time() - start_time)

    return filtered_data
```

---

## Common Mistakes to Avoid

### 1. **Overloading the Policy Engine**
   - **Mistake:** Applying policies to every single field in every response.
   - **Impact:** Slows down requests and increases complexity.
   - **Fix:** Use granular policies (e.g., only mask SSN for EU users) and default to "no action" where possible.

### 2. **Hardcoding Context**
   - **Mistake:** Assuming user jurisdiction is always known (e.g., from a cookie).
   - **Impact:** Policies may fail silently or incorrectly (e.g., allowing EU data exposure).
   - **Fix:** Use multiple context providers (IP, headers, user preferences) and default to conservative assumptions (e.g., treat unknown jurisdictions as EU for GDPR).

### 3. **Ignoring Performance**
   - **Mistake:** Evaluating policies synchronously for every request.
   - **Impact:** High latency under load.
   - **Fix:**
     - Use async policy evaluation where possible.
     - Cache policy results (e.g., "User X is in EU" → don’t re-evaluate for every call).
     - Offload heavy checks (e.g., IP geolocation) to a sidecar service.

### 4. **Brittle Policy Definitions**
   - **Mistake:** Storing policies as raw strings (e.g., `conditions = "user.jurisdiction == EU"`).
   - **Impact:** Hard to validate, debug, or extend.
   - **Fix:** Use structured formats (e.g., JSON Schema) and validate policies at runtime.

### 5. **Forgetting Audit Trails**
   - **Mistake:** Not logging policy decisions (e.g., "Allowed because of exception").
   - **Impact:** Cannot prove compliance during audits.
   - **Fix:** Log all policy evaluations, including:
     - Which policies were applied.
     - Why a policy was skipped (e.g., "Conditions not met").
     - Who triggered the evaluation (e.g., user ID).

### 6. **Static Policy Versions**
   - **Mistake:** Not tracking which policies are active (e.g., "We’re complying with GDPR v1 but not v2").
   - **Impact:** Risk of non-compliance due to outdated rules.
   - **Fix:** Store policy versions and enforce a "latest" flag. Example:
     ```sql
     ALTER TABLE compliance_policies ADD COLUMN version INTEGER NOT NULL DEFAULT 1;
     ALTER TABLE compliance_policies ADD COLUMN is_latest BOOLEAN NOT NULL DEFAULT FALSE;
     ```

---

## Key Takeaways

- **Compliance is a lifecycle concern**, not a one-time setup. Treat policies as first-class citizens in your architecture.
- **Separate policy logic from business logic** to avoid brittle, hard-to-maintain code.
- **Dynamic evaluation** allows policies to adapt to context (user, request, data) without code changes.
- **Observability is critical**—you can’t enforce what you can’t measure.
- **Tradeoffs exist**:
  - **Flexibility** (dynamic policies) vs. **performance** (async evaluation).
  - **Granularity** (fine-grained rules) vs. **complexity** (managing many policies).
- **Start small**—pilot compliance profiling in one high-risk area (e.g., PII handling) before scaling.

---

## Conclusion

Compliance Profiling shifts the paradigm from "complying by exception" to "complying by design." By modeling rules as dynamic, reusable policies, you create APIs that adapt to regulations, not the other way around. The key is balancing flexibility with performance—using structured policy definitions, smart context providers, and observability to keep your system both secure and scalable.

### Next Steps
1. **Pilot the pattern** in a non-critical area (e.g., a new microservice).
2. **Measure impact** on latency and compliance coverage.
3. **Iterate** based on feedback from auditors or security teams.

As regulations evolve, your compliance architecture should too. With Compliance Profiling, you’re not just checking boxes—you’re building a system that grows with your needs.

---
**Further Reading:**
- [EU GDPR Article 5: Data Processing Principles](https://gdpr-info.eu/art-5-gdpr/)
- [HIPAA Security Rule Overview](https://www.hhs.gov/hipaa/for-professionals/security/guidance/index.html)
- [Open Policy Agent (OPA) for Policy-as-Code](https://www.openpolicyagent.org/)

**Code Repository:** [GitHub - compliance-profiling-example](https://github.com/janedoe/compliance-profiling-example)
```