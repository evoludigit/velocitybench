# **[Pattern] Deployment Verification Reference Guide**

---

## **Overview**
Deployment Verification is a **post-deployment validation pattern** designed to ensure that newly deployed systems, configurations, or code changes function as intended. This pattern systematically checks for **correctness, performance, security, and compliance** in a controlled environment before exposing updates to end-users or production workloads. It typically involves automated checks (e.g., unit tests, integration tests, health probes, or infrastructure-as-code validations) followed by optional manual reviews (e.g., QA or DevOps validation).

This guide outlines the **key components, implementation steps, schema references, query examples**, and related patterns to deploy this effectively in cloud-native, DevOps, or traditional IT environments.

---

## **Key Concepts**
| **Concept**               | **Description**                                                                                                                                                                                                 | **Example Use Cases**                                                                 |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| **Verification Scope**    | Defines what to validate (e.g., code, config files, infrastructure, dependencies).                                                                                                                         | Validating Kubernetes manifests after Helm deployments.                               |
| **Verification Methods**  | Tools or techniques used (e.g., unit tests, security scans, load tests, compliance checks).                                                                                                               | Running Trivy for container image vulnerabilities or Calico for network policies.     |
| **Verification Levels**   | Severity-based categories (e.g., **critical**, **warning**, **info**) to prioritize fixes.                                                                                                                 | Failing a deployment if a security vulnerability ("critical") is detected.              |
| **Rollback Triggers**     | Conditions under which to revert changes (e.g., failed checks, alert thresholds).                                                                                                                        | Automatically rolling back if a database migration fails a transactional test.        |
| **Feedback Loop**         | Mechanism to report results and escalate issues (e.g., Slack alerts, Jira tickets, or dashboards).                                                                                                         | Notifying a DevOps team via PagerDuty if a health check fails.                        |
| **Thresholds**            | Metrics or rules to determine pass/fail (e.g., "CPU usage < 80% for 5 mins").                                                                                                                               | Rejecting a deployment if API response times exceed 99th percentile SLAs.                |

---

## **Implementation Details**

### **1. Define Verification Scope**
- **Inputs to Verify**:
  - **Code**: Unit/integration tests, linting (e.g., ESLint, Pylint).
  - **Configurations**: Infrastructure-as-Code (IaC) (e.g., Terraform plan checks), Kubernetes manifests (e.g., `kubectl validate`).
  - **Dependencies**: Container images (e.g., vulnerability scans), databases (e.g., schema migrations).
  - **Performance**: Load testing (e.g., JMeter, Locust), latency monitoring.
  - **Security**: Secrets rotation, IAM policies, network hardeners (e.g., OpenSCAP).

- **Outputs**:
  - Pass/fail results.
  - Remediation steps for failures.

---

### **2. Select Verification Methods**
| **Method**               | **Tool/Technique**          | **When to Use**                                                                 | **Example Query/Command**                          |
|--------------------------|-----------------------------|---------------------------------------------------------------------------------|----------------------------------------------------|
| **Unit Tests**           | Jest, PyTest, Go Test       | Validate code logic pre-deployment.                                           | `go test ./...`                                   |
| **Integration Tests**    | Postman, TestContainers     | Ensure services communicate correctly.                                         | `curl -X POST http://localhost:8080/api/health`    |
| **Infrastructure Checks**| Terraform, Kustomize, ArgoCD | Validate IaC templates or manifests before apply.                              | `terraform plan -out=tfplan`                      |
| **Security Scans**       | Trivy, OWASP ZAP, OpenSCAP  | Detect vulnerabilities in images/configs.                                       | `trivy image --severity HIGH alpine:latest`       |
| **Performance Tests**    | Locust, Gatling             | Simulate traffic to check stability.                                           | `locust -f load_test.py --host=http://example.com` |
| **Health Probes**        | Liveness/readiness probes   | Verify endpoints are responsive (Kubernetes, Prometheus-based).                  | `kubeectl get pods --show-labels`                 |
| **Compliance Checks**    | CIS Benchmarks, Policy as Code (e.g.,Kyverno)| Enforce security policies (e.g., no root access).                              | `kyverno validate --policy policy.yaml`            |

---

### **3. Define Verification Levels and Rollback Logic**
- **Severity Mapping**:
  - `Critical`: Immediately rollback (e.g., database corruption).
  - `Warning`: Escalate for review (e.g., deprecated APIs used).
  - `Info`: Log for audit (e.g., minor config drift).

- **Rollback Triggers**:
  - **Automated**: Fail a CI/CD pipeline if checks fail.
  - **Manual**: Approve/block deployments via gatekeepers (e.g., GitHub Approval Checks).
  - **Threshold-Based**: Abort if error rates exceed 1%.

- **Example Workflow**:
  ```mermaid
  graph LR
    A[Deploy Changes] --> B{Run Verification}
    B -->|Pass| C[Promote to Staging]
    B -->|Fail Critical| D[Rollback]
    D --> E[Notify Team]
    C --> F{Manual QA}
    F -->|Pass| G[Release to Prod]
    F -->|Fail| D
  ```

---

### **4. Implement Feedback Loops**
- **Automated Alerts**:
  - Slack/Teams notifications for failures.
  - Jira tickets for critical issues.
  - Dashboards (Grafana, Datadog) for trends.
- **Example Alert Rule (Prometheus)**:
  ```yaml
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High error rate on {{ $labels.instance }}"
      description: "{{ $labels.job }} has {{ $value }} errors."
  ```

---

### **5. Example Schema Reference**
Below is a schema for a **Verification Report** (e.g., JSON/YAML output):

| **Field**               | **Type**   | **Description**                                                                 | **Example Value**                          |
|-------------------------|------------|---------------------------------------------------------------------------------|--------------------------------------------|
| `verification_id`       | String     | Unique ID for the verification run.                                              | `v20230915-1430`                          |
| `timestamp`             | ISO8601    | When the verification occurred.                                                  | `2023-09-15T14:30:00Z`                    |
| `scope`                 | Object     | What was verified (e.g., code, config).                                         | `{"type": "kubernetes", "namespace": "default"}` |
| `method`                | String     | Verification tool/technique used.                                                | `trivy`, `kubectl validate`                 |
| `result`                | String     | `pass`, `fail`, or `warning`.                                                    | `pass`                                     |
| `severity`              | String     | `critical`, `warning`, or `info`.                                                 | `critical`                                 |
| `details`               | Object     | Failure/error messages or metrics.                                               | `{"vulnerabilities": [{"CVE": "CVE-2023-1234"}]}` |
| `remediation`           | String     | Steps to fix the issue.                                                          | `Patch container to alpine:3.17`           |
| `rollback_required`     | Boolean    | Whether to reverse changes.                                                       | `true`                                     |

---

## **Query Examples**
### **1. Query Verification Results (API Example)**
**Endpoint**: `GET /api/verifications`
**Request**:
```bash
curl -X GET "http://verification-service/api/verifications?severity=critical&scope=database"
```
**Response**:
```json
{
  "data": [
    {
      "verification_id": "v20230915-1430",
      "timestamp": "2023-09-15T14:30:00Z",
      "scope": { "type": "database", "name": "orders_db" },
      "method": "schema_migration_test",
      "result": "fail",
      "severity": "critical",
      "details": "Migration to v3.2 failed due to constraint violation.",
      "remediation": "Revert migration and apply incremental updates."
    }
  ]
}
```

### **2. Filter Failed Verifications (Kubernetes)**
```bash
kubectl get deployments -n staging --field-selector=status.conditions.type=VerificationPassed=false
```

### **3. Security Scan Query (Trivy)**
```bash
trivy image --exit-code 1 alpine:latest  # Fails if vulnerabilities exist
```

### **4. Performance Test Results (Locust)**
```bash
locust -f load_test.py --headless --run-time 5m --users 100  # Outputs metrics to CSV.
```

---

## **Related Patterns**
1. **[Canary Releases]**
   - Deploy small subsets of users to verify new features before full rollout.
   - *Use Case*: Gradually roll out a database schema change to monitor impact.

2. **[Feature Flags]**
   - Toggle features on/off based on verification results.
   - *Use Case*: Disable a new UI component if user tests fail.

3. **[Shift-Left Testing]**
   - Integrate verification early in the pipeline (e.g., pre-commit hooks).
   - *Use Case*: Block PRs with failing unit tests.

4. **[Chaos Engineering]**
   - Intentionally induce failures to test resilience during verification.
   - *Use Case*: Kill pods to verify auto-scaling works.

5. **[Infrastructure as Code (IaC) Validation]**
   - Validate IaC templates before deployment (e.g., Terraform `plan`).
   - *Use Case*: Detect drift in AWS CloudFormation templates.

6. **[Observability-Driven Deployment]**
   - Use metrics/logs to dynamically adjust verification thresholds.
   - *Use Case*: Adjust alert thresholds based on real-time traffic patterns.

---

## **Best Practices**
1. **Automate Everything**:
   - Use CI/CD pipelines (GitHub Actions, GitLab CI, ArgoCD) to run verifications.
   - Example: Add a `verify` job in `.github/workflows/deploy.yml`.

2. **Isolate Verifications**:
   - Run checks in **staging-like environments**, not production.
   - Use tools like **Kind** (Kubernetes-in-Docker) for local testing.

3. **Document Thresholds**:
   - Clearly define what constitutes a `pass`/ `fail` (e.g., "API < 500ms latency."

4. **Escalate Strategically**:
   - Use **multi-level alerts** (e.g., Slack for warnings, PagerDuty for critical).

5. **Retain Verification History**:
   - Store results in a database (e.g., Elasticsearch) or log aggregator (Loki).

6. **Integrate with Incident Management**:
   - Link verification failures to tickets (e.g., Jira, Linear).

---

## **Example Full Pipeline (GitHub Actions)**
```yaml
name: Deployment Verification
on: [push]
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Unit Tests
        run: go test ./...
      - name: Scan Images for Vulnerabilities
        run: trivy image --severity HIGH alpine:latest
      - name: Validate Kubernetes Manifests
        run: kubectl validate -f k8s/
      - name: Deploy to Staging
        if: success()
        run: kubectl apply -f k8s/
      - name: Wait for Verification
        run: |
          until kubectl get pods -n staging -o jsonpath='{.items[*].status.phase}' | grep "Running"; do
            sleep 1
          done
      - name: Run Integration Tests
        run: curl -X GET http://staging-api:8080/health || exit 1
      - name: Rollback on Failure
        if: failure()
        run: kubectl rollout undo -f k8s/ --to-revision=1
```

---
**Word Count: ~1,100**