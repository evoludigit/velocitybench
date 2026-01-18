# **[Pattern] Smoke Testing – Reference Guide**

---

## **Overview**
**Smoke Testing** is a lightweight, pre-deployment validation process that ensures core system functionality works as expected after minimal changes (e.g., builds, deployments, or configuration updates). Unlike exhaustive regression testing, smoke tests validate critical paths (e.g., login, basic APIs, UI navigation) in a fraction of the time. This pattern defines best practices for designing, implementing, and integrating smoke tests into CI/CD pipelines to catch high-risk failures early.

Key goals:
- **Fail fast**: Detect catastrophic failures before deeper testing.
- **Reduce false positives**: Avoid flaky tests by focusing on stability-critical components.
- **Automate**: Integrate with pipelines to enable continuous validation.
- **Maintainability**: Keep tests concise, readable, and low-maintenance.

---

## **Schema Reference**
| **Component**               | **Description**                                                                                     | **Example Tools/Frameworks**                     |
|-----------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------|
| **Test Scope**              | Defines what to test (e.g., core APIs, critical UI flows).                                             | Manual list, configuration file (e.g., `test-config.yml`). |
| **Test Cases**              | Individual checks (e.g., "Verify login redirects to dashboard").                                      | Test scripts (Python, JavaScript), UI automation.   |
| **Execution Environment**   | Staging/pre-prod environment mirroring production.                                                   | Dockerized staging, cloud VMs, or hybrid setups.   |
| **Thresholds**              | Defines "pass/fail" criteria (e.g., response time < 500ms, error rate = 0%).                         | Custom metrics, OWASP ZAP for security checks.     |
| **Trigger Conditions**      | When to run (e.g., post-build, manual gate).                                                       | CI/CD hooks (Jenkins, GitHub Actions), cron jobs. |
| **Artifacts**               | Outputs (logs, screenshots, metrics) for debugging.                                                  | Test reports (Allure, JUnit XML), Dashboards (Grafana). |
| **Rollback Plan**           | Steps to revert if smoke tests fail (e.g., rollback to last known good deployment).                 | Blue-green deployments, canary releases.         |
| **Maintenance**             | Process to update tests when requirements change (e.g., refactoring, new features).                 | Version control (Git), test suites (TestNG, Pytest). |

---

## **Implementation Details**

### **1. Design Principles**
- **Selectivity**: Test only what’s *likely* to break (e.g., auth, data persistence). Omit edge cases.
  - *Anti-pattern*: Testing every API endpoint.
- **Speed**: Target <5-minute runtime per suite. Prioritize endpoints with the highest failure impact.
- **Determinism**: Avoid flakiness by:
  - Using clean environments (separate DB instances for non-idempotent tests).
  - Mocking external services (e.g., payment gateways) where possible.
- **Isolation**: Tests should run independently to avoid cascading failures.

### **2. Test Case Design**
| **Test Type**            | **Purpose**                                                                                     | **Implementation Example**                                  |
|--------------------------|-------------------------------------------------------------------------------------------------|----------------------------------------------------------------|
| **API Smoke Tests**      | Validate endpoints return expected status codes and payloads.                                    | `POST /api/auth/login` → Assert `200 OK` + `session_id` in response. |
| **UI Smoke Tests**       | Check browser interactions (e.g., login form submission).                                        | Selenium/Cypress: Click login → Verify redirect to `/dashboard`. |
| **Data Integrity Tests** | Ensure critical data isn’t corrupted post-deployment.                                           | Query DB → Assert `active_users` count matches expected range. |
| **Security Checks**      | Scan for OWASP Top 10 vulnerabilities (e.g., SQLi, XSS).                                          | OWASP ZAP automated scan in CI pipeline.                      |
| **Performance Thresholds** | Benchmark response times and throughput.                                                        | Locust/Gatling: Simulate 100 RPS → Assert `< 500ms p99`.      |

**Example Test Suite Structure** (Pseudocode):
```python
# tests/smoke/login_test.py
def test_login_redirects_to_dashboard():
    response = requests.post("/api/auth/login", data={"email": "user@test.com", "password": "pass123"})
    assert response.status_code == 200
    assert redirect_url(response.headers) == "/dashboard"

def test_db_connection_healthy():
    conn = connect_to_db()
    assert conn.ping() is True
```

### **3. Tooling Stack**
| **Category**       | **Tools**                                                                                     | **Considerations**                                      |
|--------------------|-----------------------------------------------------------------------------------------------|----------------------------------------------------------|
| **CI/CD Integration** | Jenkins, GitHub Actions, GitLab CI                                                      | Use parallel execution to reduce runtime.              |
| **Testing Frameworks** | Postman (API), Cypress (UI), Pytest/TestNG (general)                                    | Prefer frameworks with built-in smoke-testing features.   |
| **Infrastructure**   | Docker, Kubernetes, AWS ECS                                                          | Spin up disposable environments for isolation.         |
| **Monitoring**       | Prometheus, Datadog                                                              | Alert on smoke test failures via metrics/grafana.       |
| **Reporting**        | Allure, JUnit XML, Custom dashboards                                                   | Generate pass/fail summaries for CI logs.               |

### **4. Automation Workflow**
1. **Trigger**: Run on:
   - Post-build (e.g., `on_deploy` hook).
   - Manual gate (e.g., pre-feature rollout).
   - Scheduled intervals (e.g., nightly health checks).
2. **Execution**:
   - Deploy artifact to staging.
   - Execute smoke tests in parallel (e.g., API + UI suites concurrently).
   - Validate thresholds (e.g., error rate < 1%).
3. **Decision Logic**:
   - **Pass**: Proceed to full regression/QA.
   - **Fail**: Block deployment; notify team (Slack/PagerDuty).
   - **Partial Fail**: Escalate critical failures; retry non-critical tests.

**Example GitHub Actions Workflow**:
```yaml
name: Smoke Test Suite
on:
  push:
    branches: [main]
jobs:
  smoke-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: docker-compose up -d staging
      - run: pytest tests/smoke/ -v --junitxml=report.xml
      - uses: actions/upload-artifact@v2
        with: { name: smoke-report, path: report.xml }
```

### **5. Maintenance**
- **Update Tests**: When:
  - Core functionality changes (e.g., new login flow).
  - Dependencies upgrade (e.g., DB schema migration).
- **Test Coverage**: Aim for **80%+ of critical paths** (prioritize by failure impact).
- **Flakiness**: Retry failed tests 2–3 times; flag persistently failing tests for debugging.
- **Documentation**: Maintain a `SMOKE_TESTS.md` file listing test cases, dependencies, and failure modes.

---

## **Query Examples**
### **1. API Smoke Test (Postman/Newman)**
```bash
# Run API smoke tests using Newman (Postman CLI)
newman run 'smoke-tests.postman_collection.json' \
  --environment 'staging.env.json' \
  --reporters cli,junit \
  --reporter-junit-export report.xml
```

### **2. UI Smoke Test (Cypress)**
```bash
# Run browser smoke tests with headless Chrome
npx cypress run --config baseUrl=https://staging.example.com
```

### **3. CI/CD Trigger (GitHub Actions)**
```yaml
# Conditional run if build passes *and* it's a Sunday (nightly health check)
if: github.event_name != 'pull_request' && (github.event_name == 'push' || github.event_name == 'schedule') && (github.event.schedule == '0 3 * * 0')  # Sunday at 3 AM
```

### **4. Threshold Validation (Python)**
```python
# Validate response times meet SLOs
import statistics
response_times = [420, 450, 500, 380]  # ms
assert statistics.p99(response_times) <= 500  # 99th percentile < 500ms
```

---

## **Related Patterns**
| **Pattern**               | **Relationship to Smoke Testing**                                                                 | **When to Use Together**                                  |
|---------------------------|----------------------------------------------------------------------------------------------------|-----------------------------------------------------------|
| **[Canary Releases](https://docs.microsoft.com/en-us/azure/architecture/patterns/canary)** | Smoke tests validate canary traffic before full rollout.                                      | Gradual deployment strategies.                            |
| **[Chaos Engineering](https://chaoss.com/)** | Smoke tests are lightweight "pre-flight" checks before chaos experiments.                        | Resilience testing post-smoke validation.                 |
| **[Shift-Left Testing](https://guru99.com/shift-left-testing.html)** | Smoke tests align with shift-left principles by catching issues early in the pipeline.           | Pipeline optimization.                                   |
| **[Feature Flags](https://launchdarkly.com/)** | Smoke tests can validate feature flag toggles before enabling for all users.                     | A/B testing or phased rollouts.                           |
| **[Infrastructure as Code (IaC)](https://www.terraform.io/)** | Smoke tests require reproducible staging environments (IaC enables this).                      | Environment provisioning.                                |
| **[Monitoring Dashboards](https://prometheus.io/)** | Correlate smoke test failures with real-time metrics (e.g., error rates).                      | Post-mortem analysis.                                     |

---

## **Anti-Patterns**
- **Over-Testing**: Including non-critical paths (e.g., admin-only features) slows the pipeline unnecessarily.
- **Ignoring Flakiness**: Flaky tests erode confidence in the smoke suite. Use retries or flakiness detection (e.g., Pytest’s `--flake8`).
- **Static Test Suites**: Not updating tests when requirements change leads to false positives/negatives.
- **Production-Like Without Isolation**: Running smoke tests in production or shared environments risks contamination.
- **Silent Failures**: Failing to notify teams of smoke test failures leads to undetected issues.

---
**See Also**:
- [Google’s Site Reliability Engineering (SRE) Book](https://sre.google/sre-book/) (Chapter 3: Reliability).
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/) (for security smoke tests).