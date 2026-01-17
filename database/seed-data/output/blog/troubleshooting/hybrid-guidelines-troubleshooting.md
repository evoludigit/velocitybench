# **Debugging Hybrid Guidelines Pattern: A Troubleshooting Guide**

The **Hybrid Guidelines Pattern** is used to enforce consistent behavior across microservices, APIs, and client applications by defining both **mandatory** (strict) and **advisory** (best practice) guidelines. These guidelines are enforced via runtime checks, static validation, or monitoring tools.

This guide helps you diagnose and resolve common issues when implementing or debugging **Hybrid Guidelines** in distributed systems.

---

## **1. Symptom Checklist**
Before diving into debugging, verify the following symptoms to narrow down the problem:

| **Symptom** | **Possible Cause** | **Action** |
|-------------|-------------------|------------|
| **Invalid API responses** (e.g., 4xx/5xx errors when not expected) | Missing mandatory validation or misconfigured advisory checks | Check API contracts, logs, and guideline enforcement rules |
| **Inconsistent behavior** (e.g., some services follow guidelines, others don’t) | Misaligned versioning, local overrides, or misconfigured hybrid policies | Verify guideline versioning and service configurations |
| **Performance degradation** (e.g., slow response times due to heavy validation) | Overzealous hybrid checks or unoptimized validation logic | Review guideline complexity and caching strategies |
| **Client-side violations** (e.g., apps ignore advisory checks) | Missing client-side enforcement or weak monitoring | Check client SDKs, logs, and monitoring dashboards |
| **Debugging tools fail to detect violations** | Incorrect instrumentation or misconfigured logging | Validate debug probes, metrics, and event streams |
| **Guideline updates not applied** | Delayed propagation or misconfigured service mesh | Check policy sync mechanisms and service mesh logs |
| **Unclear guideline documentation** (leading to misinterpretation) | Poor documentation or version drift | Audit guideline specs and update docs |

If multiple symptoms appear, the issue likely stems from **misconfiguration, version mismatches, or lack of enforcement**.

---

## **2. Common Issues & Fixes**

### **2.1. Mandatory Guidelines Not Enforced**
**Symptoms:**
- API calls bypass validation despite strict rules
- Errors appear intermittently

**Root Causes:**
- Missing annotation in OpenAPI/Swagger schema
- Gateway or API proxy bypassing validation
- Client bypassing server-side checks

**Fixes:**

#### **Fix 1: Ensure API Contract Enforcement**
If using OpenAPI/Swagger, validate the schema with `swagger-codegen` or `json-schema-validator`:

```yaml
# Example OpenAPI schema with mandatory validation
components:
  schemas:
    UserRequest:
      type: object
      required:
        - email
      properties:
        email:
          type: string
          format: email
          # Advisory: Should follow RFC 2142 for official use
```

**Debugging Steps:**
1. Check API proxy logs (e.g., Kong, Apigee) for skipped validations.
2. Verify if the `swagger-validation` middleware is enabled.

```bash
# Example using Kong to enforce validation
plugin: request-transformer
config:
  remove: 'header.x-guidelines-bypass'
  add: 'header.x-guidelines-checked=true'
```

---

#### **Fix 2: Service Mesh Policy Enforcement**
If using Istio/Linkerd, ensure hybrid policies are applied:

```yaml
# Istio VirtualService with hybrid policy
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
...
  http:
  - route:
      - destination:
          host: user-service
    corsPolicy:
      allowOrigins:
        - exact: "https://clientapp.com"  # Advisory: Only allow trusted domains
      allowMethods:
        - GET  # Mandatory: Only allow GET
```

**Debugging Steps:**
1. Check Istio `envoyaccesslog` for skipped rules.
2. Verify if `AuthorizationPolicy` is correctly applied:

```bash
kubectl get authorizationpolicy -n default
```

---

#### **Fix 3: Client-Side Bypass**
If clients ignore advisory checks (e.g., logging but not enforcing), enforce via SDK:

```javascript
// Node.js example with Axios + Hybrid Guidelines
const axios = require('axios');

const client = axios.create({
  validateStatus: (status) => {
    // Mandatory: Reject 400+ errors
    if (status >= 400) throw new Error(`API Error: ${status}`);
  },
  beforeRequest: (config) => {
    // Advisory: Log structured data for observability
    console.log('Guideline: Attaching trace ID', { traceId: uuidv4() });
    return config;
  }
});
```

**Debugging Steps:**
1. Check client logs for missing `traceId` or other advisory metadata.
2. Use **Sentry** or **OpenTelemetry** to trace guideline violations.

---

### **2.2. Advisory Guidelines Ignored**
**Symptoms:**
- Logs show advisory violations but no action is taken
- Best practices (e.g., rate limiting, caching) are not followed

**Root Causes:**
- Missing instrumentation
- Logs not monitored
- No automated remediation

**Fixes:**

#### **Fix 1: Instrument Advisory Checks**
Use structured logging to track advisory violations:

```go
// Go example with logging advisory rules
func validateUserRequest(req *http.Request) error {
    email := req.FormValue("email")
    if !strings.Contains(email, "@") {
        // Advisory: Log but don't fail
        log.Printf("Advisory: Email validation failed (non-standard format): %s", email)
        return nil // Non-fatal
    }
    return nil
}
```

**Debugging Steps:**
1. Query logs for `Advisory` messages:
   ```bash
   # Example using ELK Stack
   curl 'http://elasticsearch:9200/_search?q=Advisory'
   ```
2. Set up alerts for repeated advisory violations.

---

#### **Fix 2: Automate Remediation with OpenTelemetry**
Use OpenTelemetry to detect and act on advisory issues:

```python
# Python with OpenTelemetry advisory checks
from opentelemetry import trace
import logging

tracer = trace.get_tracer("hybrid-guidelines")

def checkRateLimit(operation: str):
    span = tracer.start_as_current_span("rate_limit_check")
    try:
        if operation == "delete_user":
            span.add_event("Advisory: Consider adding rate limiting")
        span.end()
    except Exception as e:
        logging.error(f"Advisory violation: {e}")
```

**Debugging Steps:**
1. Check traces in **Jaeger** or **Grafana Tempo**:
   ```bash
   curl "http://jaeger:16686/search?service=api-service&limit=10"
   ```
2. Use **OpenTelemetry Alerts** to trigger remediation.

---

### **2.3. Policy Version Drift**
**Symptoms:**
- Some services follow old guidelines, others follow new ones
- Conflicting behavior in distributed transactions

**Root Causes:**
- No versioned guideline enforcement
- Manual overrides in deployments

**Fixes:**

#### **Fix 1: Versioned Policy Propagation**
Use a **policy registry** (e.g., **GitOps + Policy-as-Code**):

```yaml
# Example: ArgoCD App of Apps with versioned policies
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: hybrid-guidelines-v1
spec:
  source:
    repoURL: https://github.com/yourorg/policy-repo.git
    targetRevision: v1.2.0  # Enforces v1.2.0 guidelines
```

**Debugging Steps:**
1. Check deployed policy versions:
   ```bash
   kubectl get cm | grep guidelines
   ```
2. Use **Git blame** to track policy changes:
   ```bash
   git blame docs/guidelines/v1.2.0.yaml
   ```

---

#### **Fix 2: Canary Rollouts for Policy Updates**
Deploy policy changes gradually to avoid cascading failures:

```bash
# Example using Istio traffic shifting
kubectl apply -f - <<EOF
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: user-service-v2
spec:
  hosts:
  - user-service
  http:
  - route:
    - destination:
        host: user-service
        subset: v1
      weight: 90
    - destination:
        host: user-service
        subset: v2
      weight: 10
EOF
```

**Debugging Steps:**
1. Monitor error rates in **Grafana**:
   ```bash
   grafana explore -db=prometheus -panel=20
   ```
2. Roll back if errors spike:
   ```bash
   kubectl rollout undo deployment/user-service -revision=2
   ```

---

### **2.4. Debugging Hybrid Guidelines in Distributed Systems**
**Symptom:** "Inconsistent behavior across services"

**Root Causes:**
- **Eventual consistency** in guideline enforcement
- **Local overrides** in microservices
- **Caching bypasses** validation

**Fixes:**

#### **Fix 1: Use Distributed Transactions for Enforcement**
Ensure all services in a transaction follow guidelines:

```typescript
// Node.js with observable transactions
import { trace } from '@opentelemetry/api';

async function createUser(userData: any) {
  const span = trace.getActiveSpan()?.clone('user_creation');
  try {
    span?.addEvent('Check Mandatory Fields');
    if (!userData.email) throw new Error("Mandatory: Email required");

    span?.addEvent('Check Advisory: Email Format');
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(userData.email)) {
      console.warn("Advisory: Email format non-standard");
    }

    span?.end();
  } catch (err) {
    span?.setStatus({ code: trace.StatusCode.ERROR, message: err.message });
    throw err;
  }
}
```

**Debugging Steps:**
1. Check trace spans for advisory warnings:
   ```bash
   curl "http://jaeger:16686/search?service=api-service&span.endTs%5B=1670000000&span.endTs%5D=1671000000"
   ```
2. Verify **saga pattern** coordination if multiple services are involved.

---

#### **Fix 2: Audit Local Overrides**
If services bypass guidelines (e.g., for testing), enforce via **policy as code**:

```python
# Python with local override detection
import os
from pydantic import BaseModel, ValidationError

class UserRequest(BaseModel):
    email: str

    class Config:
        extra = "forbid"  # Advisory: Reject unknown fields

def validate(request: dict):
    try:
        UserRequest(**request)
    except ValidationError as e:
        if "extra fields" in e.json():
            print(f"Advisory: Unknown fields detected: {e}")
        else:
            raise  # Mandatory failure
```

**Debugging Steps:**
1. Search logs for `extra fields` warnings.
2. Use **Snyk** or **Trivy** to scan for hardcoded overrides.

---

## **3. Debugging Tools & Techniques**

### **3.1. Logging & Monitoring**
| **Tool** | **Use Case** | **Command/Query** |
|----------|-------------|-------------------|
| **ELK Stack** | Centralized logging | `curl 'http://elasticsearch:9200/_search?q=Advisory'` |
| **Grafana** | Metrics + alerts | `select sum(error) by (service)` |
| **Jaeger** | Distributed tracing | `curl "http://jaeger:16686/search?service=api"` |
| **OpenTelemetry Collector** | Policy enforcement tracing | `otelcol --config-file=otel-config.yaml` |

**Example Alert (Grafana):**
```promql
# Alert if mandatory violations exceed threshold
increase(api_errors_mandatory_total[5m]) > 10
```

---

### **3.2. Static Analysis**
| **Tool** | **Use Case** |
|----------|-------------|
| **Swagger Validator** | Check OpenAPI contracts | `swagger-validator -u http://api-docs` |
| **Pydantic / JSON Schema** | Runtime validation | `python -m pydantic validate user.json` |
| **Snyk / Trivy** | Detect hardcoded bypasses | `snyk test --target=./` |

---

### **3.3. Dynamic Analysis**
| **Tool** | **Use Case** |
|----------|-------------|
| **Postman / Newman** | Test API compliance | `newman run hybrid-guidelines.postman_collection.json` |
| **K6** | Load test guideline enforcement | `k6 run script.js --vus 100` |
| **Chaos Mesh** | Test resilience to policy violations | `kubectl apply -f chaos-policy.yaml` |

**Example K6 Script:**
```javascript
import http from 'k6/http';
import { check } from 'k6';

export default function () {
  const res = http.post('http://api/user', JSON.stringify({ email: "invalid" }));
  check(res, {
    'Mandatory: Should return 4xx': (r) => r.status === 400,
    'Advisory: Logs warning': (r) => r.json().message.includes("Advisory"),
  });
}
```

---

## **4. Prevention Strategies**

### **4.1. Enforce Hybrid Guidelines via CI/CD**
- **Pre-commit Hooks:** Run `swagger-validator` on PRs.
- **GitHub Actions:** Block merges without policy compliance.
  ```yaml
  # .github/workflows/validate-guidelines.yml
  name: Validate Hybrid Guidelines
  on: [push, pull_request]

  jobs:
    validate:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v3
        - run: npm install -g @openapitools/openapi-generator-cli
        - run: oas-validate -u ./api.yaml
  ```

---

### **4.2. Use Policy-as-Code**
- **Tools:** Open Policy Agent (OPA), Kyverno, KubeArmor.
- **Example OPA Policy:**
  ```rego
  # hybrid-policy.rego
  package api

  default allow = true

  allow {
    input.method == "GET"
    input.path == "/users"
    not input.query_params["unsafe"]
  }

  allow {
    input.method != "DELETE"  # Advisory: Log DELETE warnings
    input.method == "DELETE"
    log["Advisory: DELETE may affect data integrity"]
  }
  ```

**Debugging OPA:**
```bash
opa eval --data=file:data.rego '[allow] api.allow(input)' --input=file:request.json
```

---

### **4.3. Automate Remediation with Feedback Loops**
- **SLOs:** Define hygiene SLIs (e.g., "99% of requests must follow mandatory fields").
- **Auto-Remediation:**
  ```bash
  # Example: Auto-patch Kubernetes if guideline violated
  kubectl apply -f - <<EOF
  apiVersion: policy.open-policy-agent.org/v1beta1
  kind: Policy
  metadata:
    name: guideline-enforcement
  spec:
    rules:
      deny:
        apiVersion: ["apps/v1"]
        kind: Deployment
        metadata:
          name: "user-service"
        spec:
          template:
            spec:
              containers:
                - name: app
                  env:
                    - name: GUIDELINE_BYPASS
                      value: "true"  # Deny deployments with this env
  EOF
  ```

---

### **4.4. Document & Version Guidelines**
- **Versioned Docs:** Use **Confluence + Git Sync**.
- **Change Logs:** Track guideline updates in `CHANGELOG.md`.
- **Example Versioned Schema:**
  ```json
  {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "https://api.example.com/guidelines/v2.1.json",
    "title": "User API Guidelines v2.1",
    "mandatory": {
      "email": { "type": "string", "format": "email" }
    },
    "advisory": {
      "email": { "description": "Should use RFC 2142 for official emails" }
    }
  }
  ```

---

## **5. Final Checklist for Debugging**
| **Step** | **Action** | **Tool** |
|----------|------------|----------|
| 1 | Check logs for `Mandatory`/`Advisory` errors | ELK, CloudWatch |
| 2 | Verify OpenAPI/Swagger contract | `swagger-validator` |
| 3 | Audit service mesh policies | Istio `kubectl get AuthorizationPolicy` |
| 4 | Trace distributed transactions | Jaeger, OpenTelemetry |
| 5 | Test client-side enforcement | Postman, K6 |
| 6 | Check CI/CD for policy violations | GitHub Actions, GitLab CI |
| 7 | Review OPA/Kyverno policies | `opa test` |
| 8 | Update docs & versions | Confluence + Git |

---

## **Conclusion**
Debugging **Hybrid Guidelines** requires:
1. **Clear separation** of mandatory (enforced) vs. advisory (best practice) rules.
2. **End-to-end validation** from API contracts to client SDKs.
3. **Observability** via logs, metrics, and traces.
4. **Automation** to prevent drift and enforce consistency.

By following this guide, you can **quickly identify, reproduce, and fix** issues in hybrid guideline enforcement while ensuring long-term reliability.

---
**Next Steps:**
- Audit your current hybrid policies using the checklist above.
- Implement **pre-commit hooks** for OpenAPI validation.
- Set up **SLOs** for guideline compliance.
- Use **chaos engineering** to test policy resilience.