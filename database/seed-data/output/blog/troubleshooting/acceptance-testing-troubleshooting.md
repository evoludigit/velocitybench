# **Debugging "Acceptance Testing" Pattern: A Troubleshooting Guide**
*A Focused Guide to Validating Requirements & Preventing System Failures*

---

## **1. Introduction**
Acceptance Testing (AT) ensures that a system meets business requirements before deployment. When acceptance testing is weak or missing, symptoms like performance bottlenecks, integration failures, or unreliable scaling emerge. This guide provides a structured approach to diagnosing and fixing acceptance testing gaps.

---

## **2. Symptom Checklist**
Before diagnosing, document these common indicators:

| **Symptom**                          | **Description**                                                                 | **Impact**                                  |
|---------------------------------------|---------------------------------------------------------------------------------|---------------------------------------------|
| ❌ No formal AT suite                 | Missing test cases for core business flows (e.g., checkout, user registration). | High risk of undetected bugs in production. |
| ✅ Unit & integration tests pass, but AT fails | Tests pass, but real-world scenarios break (e.g., payment gateways, third-party APIs). | Confusion between "test coverage" and "requirements alignment." |
| 📈 Performance degrades under load     | System slows down or crashes during user spikes (e.g., Black Friday sales).     | Poor scalability, user churn.               |
| 🔧 Frequent maintenance fires         | Bugs in "tested" features reappear post-release (e.g., edge cases).             | Eroding trust in testing.                  |
| 🔄 Integration failures               | Third-party APIs (e.g., Stripe, AWS) fail unpredictably in AT but pass locally. | Broken workflows, revenue loss.             |
| 📊 Missing non-functional tests       | No tests for security, compliance, or usability (e.g., GDPR, accessibility).   | Legal/regulatory violations.               |

**Action:** If **2+ symptoms** match, proceed to diagnosis.

---

## **3. Common Issues & Fixes**

### **Issue 1: Missing or Incomplete Acceptance Test Cases**
**Symptom:**
- AT suite covers only happy paths (e.g., successful checkout) but lacks edge cases (e.g., invalid credit cards, network timeouts).
- Requirements are documented but not translated into testable scenarios.

**Root Cause:**
- Poor collaboration between devs and business teams.
- AT is treated as an afterthought, not a validation layer.

**Fix:**
#### **Step 1: Align Tests with Requirements**
Use a **requirements traceability matrix** to link test cases to user stories.

| **User Story**                     | **Acceptance Criteria**                     | **Test Case**                          | **Pass/Fail** |
|-------------------------------------|---------------------------------------------|----------------------------------------|----------------|
| "As a user, I can reset my password" | Works for verified emails, fails for spam | `test_password_reset_valid_email()`    | ✅ Pass        |
|                                     | Handles rate-limiting after 5 attempts      | `test_password_reset_rate_limit()`     | ❌ Fail        |

**Example Fix (Python + pytest):**
```python
import pytest

@pytest.mark.usefixtures("reset_password_flow")
def test_password_reset_invalid_email():
    with patch("smtp_client.send") as mock_send:
        mock_send.side_effect = SMTPException("Email not found")
        response = client.post("/reset-password", data={"email": "invalid@example"})
        assert response.status_code == 404
        assert "No account found" in response.text
```

#### **Step 2: Add Edge Cases**
Extend tests for:
- **Data validation** (e.g., invalid input).
- **Error scenarios** (e.g., API timeouts, partial failures).
- **User flows** (e.g., abandoned cart recovery).

**Example:**
```python
def test_payment_failure_retry():
    # Simulate Stripe API failure
    stripe_mock = patch("stripe.Charge.create", side_effect=StripeError("Gateway refused"))
    with stripe_mock:
        response = client.post("/checkout", data={"card": "4111111111111111"})
        assert response.status_code == 422  # Unprocessable Entity
        assert "Payment declined" in response.text
```

---

### **Issue 2: Performance & Reliability Gaps**
**Symptom:**
- AT passes, but system crashes under real-world load (e.g., 10K concurrent users).
- No tests for database locks, cache invalidation, or network latency.

**Root Cause:**
- AT focuses on correctness, not scalability.
- Missing **non-functional requirements** (NFRs) like latency, throughput.

**Fix:**
#### **Step 1: Add Performance Acceptance Tests**
Use tools like **Locust**, **JMeter**, or **k6** to simulate load.

**Example (Locust):**
```python
from locust import HttpUser, task, between

class PaymentUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def checkout(self):
        self.client.post("/checkout", json={
            "user_id": 123,
            "items": [{"id": 456, "quantity": 2}]
        })
        # Assert successful response
        assert self.client.last_response.status_code == 200
```

#### **Step 2: Test Failure Modes**
Ensure the system handles:
- **Database timeouts** (e.g., `pg_timeout` in PostgreSQL).
- **API rate-limiting** (e.g., Stripe’s `max_retries`).
- **Network partitions** (use `chaos engineering` tools like Gremlin).

**Example (chaos-mesh):**
```yaml
# chaos-mesh experiment to simulate pod failures
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: simulate-db-timeout
spec:
  action: pod-failure
  mode: all
  selector:
    namespaces:
      - default
    labelSelectors:
      app: payment-service
  duration: "30s"
  frequency: 1
  errors:
    - code: 504
```

---

### **Issue 3: Integration Failures**
**Symptom:**
- AT passes locally, but fails in staging/production due to external dependencies (e.g., auth0, AWS S3).
- Mocks don’t match real-world behavior (e.g., API response times).

**Root Cause:**
- Over-reliance on **unit-like** AT (tests pass, but integration is weak).
- Mocking doesn’t account for real-world variability.

**Fix:**
#### **Step 1: Use Hybrid Testing (Mocks + Real APIs)**
- **Mock** fast responses for happy paths.
- **Stub** real APIs for error cases (e.g., 503 errors).

**Example (pytest with `httpx`):**
```python
def test_auth0_login_with_rate_limit():
    # Mock Auth0’s /oauth/token endpoint to return 429
    with httpx.Client() as client:
        client.post.register(
            "https://auth0.auth0.com/oauth/token",
            json={"error": "Too Many Requests"}
        )
        response = client.post("/login", data={"token": "fake"})
        assert response.status_code == 429
```

#### **Step 2: Test Retry Logic**
Ensure the system retries failed requests (e.g., AWS SDK retries).

```python
def test_s3_upload_with_retry():
    # Simulate S3 timeout
    with patch("boto3.client.post") as mock_post:
        mock_post.side_effect = [botocore.exceptions.ClientError(
            {"Error": {"Code": "RequestTimeout"}}, "put_object"
        ), None]  # Second call succeeds
        s3 = boto3.client("s3")
        s3.put_object(Bucket="test", Key="file.txt", Body=b"data")
        assert s3.put_object.call_count == 2  # Retried once
```

---

### **Issue 4: Missing Non-Functional Tests**
**Symptom:**
- No tests for security (OWASP Top 10), compliance (GDPR), or accessibility (WCAG).

**Root Cause:**
- AT focuses only on functional correctness.
- Security/compliance is treated as a "devops" problem.

**Fix:**
#### **Step 1: Add Security Acceptance Tests**
Use **OWASP ZAP** or **Semgrep** to scan for vulnerabilities.

**Example (Semgrep):**
```yaml
# semgrep.yml
rules:
  - id: insecure-cookie
    pattern: Response.setCookie(...)
    message: "Cookies should use `Secure` and `HttpOnly` flags"
    severity: ERROR
```

#### **Step 2: Test Compliance Scenarios**
Example: GDPR right to erasure.

```python
def test_user_data_deletion():
    # Add test user
    user = create_user(email="test@example.com")
    assert db.query("SELECT * FROM users WHERE email = ?", ("test@example.com",)).count == 1

    # Delete via API
    response = client.delete("/users/123/delete", headers={"Authorization": "Bearer token"})
    assert response.status_code == 200

    # Verify deletion
    assert db.query("SELECT * FROM users WHERE email = ?", ("test@example.com",)).count == 0
```

#### **Step 3: Accessibility Testing**
Use **axe-core** or **Pylint** to check HTML/JS for WCAG compliance.

**Example (axe-core):**
```javascript
// Test for ARIA labels
const results = await axe.run('#app');
expect(results.violations).toEqual([]);
```

---

## **4. Debugging Tools & Techniques**
| **Tool**               | **Use Case**                                  | **Example Command/Integration**          |
|------------------------|-----------------------------------------------|-------------------------------------------|
| **Locust/JMeter**      | Load testing                                  | `locust -f payment_tests.py --host http://api.example.com` |
| **Chaos Mesh**         | Test failure recovery                         | Apply YAML chaos experiment.             |
| **OWASP ZAP**          | Security scanning                             | `zap-baseline.py -t http://localhost:8000` |
| **Semgrep**            | Static code analysis                          | `semgrep scan --config=pylint`            |
| **Postman/Newman**     | API contract testing                          | `newman run tests.postman_collection.json` |
| **Pytest + Fixtures**  | Isolated test execution                      | `@pytest.fixture(scope="module")`         |
| **Docker Compose**     | Reproduce staging env locally                 | `docker-compose up --scale app=3`         |

**Debugging Workflow:**
1. **Reproduce the issue** in a staging-like environment.
2. **Check logs**:
   - Application logs (`/var/log/app/`).
   - Database queries (`pgbadger` for PostgreSQL).
   - External API calls (`aws logs tail` for Lambda).
3. **Isolate the failure**:
   - Use `strace` to trace system calls.
   - Profile memory with `py-spy` (Python) or `pprof` (Go).
4. **Compare mock vs. real behavior**:
   - If a test passes with a mock but fails in staging, add variability (e.g., random delays in mocks).

---

## **5. Prevention Strategies**
To avoid future acceptance testing gaps:

### **✅ Best Practices for AT Design**
1. **Start AT Early**
   - Write tests **before** implementation (TDD-style).
   - Use **Cucumber** or **Behavior-Driven Development (BDD)** for clarity.

2. **Automate Everything**
   - **CI/CD Integration**: Run AT on every PR merge (e.g., GitHub Actions).
   - **Monitor Test Flakiness**: Use tools like **Pytest-flakes**.

3. **Include Non-Functional Tests**
   - **Security**: Scan with **OWASP ZAP** in CI.
   - **Performance**: Add load tests to critical paths.
   - **Compliance**: Automate GDPR/CCPA checks.

4. **Mock Realistically**
   - Use **factory-boy** (Python) or **MockServiceWorker** (JS) to generate testable data.
   - Example:
     ```python
     # Mock a slow third-party API
     @patch("services.external_api.get_data", side_effect=lambda: time.sleep(1))
     def test_slow_api_handling(mock_api):
         start_time = time.time()
         data = external_api.get_data()
         assert time.time() - start_time >= 1  # Ensure delay is enforced
     ```

5. **Collaborate with Business Teams**
   - Hold **test review meetings** with Product Owners.
   - Use **excel-based test case management** (e.g., TestRail) for traceability.

### **🚀 Advanced Strategies**
- **Chaos Engineering**: Proactively test failure modes (e.g., kill pods randomly).
- **Canary Releases**: Gradually roll out features to a subset of users, with AT monitoring.
- **Property-Based Testing**: Use **Hypothesis** (Python) or **QuickCheck** (Java) to generate random inputs and validate invariants.

---

## **6. Example Debugging Session**
**Scenario**: Payment failures in production, but AT passes.

| **Step**               | **Action**                                                                 | **Tool Used**                     |
|------------------------|--------------------------------------------------------------------------|------------------------------------|
| 1. Reproduce           | Run AT locally with real Stripe API (not mock).                          | `pytest -m stripe_integration`    |
| 2. Debug               | Check Stripe logs: "Rate limit exceeded" (429).                          | `stripe api:logs --limit 100`      |
| 3. Fix                 | Add retry logic with exponential backoff in AT.                           | Update `payment_service.py`       |
| 4. Verify              | Run AT with simulated rate limits.                                        | Chaos Mesh + Locust             |
| 5. Prevent             | Add a test for `StripeRateLimitError` in CI.                              | Pytest fixture + `stripe.error`   |

---

## **7. Key Takeaways**
| **Problem**               | **Diagnosis**                          | **Fix**                                  | **Prevention**                          |
|---------------------------|----------------------------------------|------------------------------------------|-----------------------------------------|
| Missing AT cases          | No test coverage for edge cases.       | Add BDD-style tests.                     | Start AT early; use Cucumber.          |
| Performance issues        | AT lacks load testing.                 | Use Locust + chaos engineering.          | Include NFRs in requirements.           |
| Integration failures      | Mocks don’t match real APIs.           | Hybrid testing (mocks + stubs).          | Test against staging-like environments. |
| Security/compliance gaps  | No automated checks.                   | Integrate OWASP ZAP + Semgrep.           | Treat security as a first-class test.   |

---
**Final Tip**: If AT is weak, **start small**:
1. Pick **one critical user flow** (e.g., checkout).
2. Write **100% coverage** for that flow.
3. Gradually expand to other areas.

By following this guide, you’ll shift AT from a "checkbox" exercise to a **reliable validation layer** that catches issues before they reach production.