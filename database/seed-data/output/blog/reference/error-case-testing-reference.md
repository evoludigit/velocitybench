---
# **[Pattern] Error Case Testing Reference Guide**

---

## **Overview**
The **Error Case Testing** pattern systematically validates how a system behaves under unexpected or invalid conditions. Unlike positive testing (which verifies normal workflows), this pattern focuses on identifying weaknesses in error handling, input validation, edge cases, and fallback mechanisms. By testing error scenarios, developers can ensure robustness, improve resilience, and minimize production failures.

Key goals of this pattern:
- Expose hidden bugs in error recovery pathways.
- Validate system behavior under invalid inputs, resource constraints, or external failures.
- Ensure graceful degradation (e.g., fallback responses, retries, or notifications).
- Adhere to defensive programming principles (e.g., input sanitization, timeouts).

This guide covers implementation strategies, schema references, query examples, and related patterns for structured error case testing.

---

## **Schema Reference**

Use the following schema to define error cases systematically. Adjust fields based on your system’s needs.

| **Field**               | **Description**                                                                                     | **Example Values/Notes**                                                                                     |
|-------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| **Error Type**          | Category of error (e.g., input validation, network failure, permission denied).                   | `InvalidInput`, `ExternalAPIFailure`, `DatabaseTimeout`, `RateLimitExceeded`                              |
| **Error Trigger**       | Action/input that causes the error (e.g., malformed JSON, null value, missing field).               | `POST /api/data?user=null`, `DELETE /api/resource/99999999` (ID out of range)                          |
| **Expected Outcome**    | Desired system behavior (e.g., HTTP 400, retry logic, fallback UI).                                | `Return 400 Bad Request with { "error": "Invalid ID" }`, `Show toast: "Retrying..."`                       |
| **Actual Outcome**      | Observed system behavior (for validation).                                                          | `Crash with NullPointerException`, `Return 500 Internal Server Error`                                       |
| **Severity**            | Impact level (Critical: downtime, High: degraded functionality, Low: cosmetic).                     | `Critical`, `High`, `Medium`, `Low`                                                                       |
| **Test Steps**          | Step-by-step instructions to reproduce the error.                                                   | `1. Send PUT /api/user with "name": "" (empty string). 2. Check response code and payload.`            |
| **Dependencies**        | External systems/resources required (e.g., third-party API, mock database).                        | `Mocked Stripe API`, `PostgreSQL with corrupted index`                                                   |
| **Environment**         | Test environment (e.g., staging, production-like mocks).                                           | `Local Docker setup`, `AWS Lambda with mocked DynamoDB`                                                   |
| **Automation Status**   | Whether the test is automated (e.g., unit, integration, load tests).                               | `Unit: Yes`, `Integration: No`, `Load: Partially`                                                        |
| **Retest Scenarios**    | Follow-up tests after fixing the error (e.g., boundary values, race conditions).                    | `Test ID = 99999998 (next invalid ID)`, `Concurrent API calls under load`                                 |
| **Notes**               | Additional context (e.g., race conditions, intermittent failures, known workarounds).             | `Error occurs only under high concurrency (>1000 RPS). Fixed in v2.3 with circuit breaker.`              |

---

## **Implementation Details**

### **Phase 1: Define Error Taxonomy**
Categorize errors based on:
1. **Source**:
   - **Client-side**: Invalid inputs, missing fields, malformed requests.
   - **Server-side**: Database failures, permission errors, timeouts.
   - **External**: Third-party API failures, rate limits, network partitions.
2. **Severity**:
   - **Critical**: System halt (e.g., disk failure).
   - **High**: Data loss or partial functionality (e.g., payment gateway timeout).
   - **Medium**: User-facing issues (e.g., slow load times).
   - **Low**: Non-functional but noticeable (e.g., missing styling).

*Example Taxonomy*:
```plaintext
High-Severity Errors:
  - ExternalAPIFailure
  - DatabaseCorruption
  - AuthenticationTimeout
Low-Severity Errors:
  - InputFormatWarning (e.g., deprecated API usage)
  - FeatureDeprecationNotice
```

---

### **Phase 2: Design Test Cases**
Use the **Error Case Testing Matrix** (see below) to map errors to test scenarios.

| **Error Type**          | **Test Scenario**                                                                 | **Technique**                          | **Validation**                          |
|-------------------------|------------------------------------------------------------------------------------|----------------------------------------|-----------------------------------------|
| `InvalidInput`          | Send `POST /api/login` with `password: "a"`.                                       | Unit Test (mock auth service)          | Reject with `401 Unauthorized`          |
| `RateLimitExceeded`     | Spam `/api/health` with 1000 requests/sec.                                         | Load Test (JMeter/Gatling)             | Return `429 Too Many Requests`          |
| `ExternalAPIFailure`    | Mock Stripe API to return `502 Bad Gateway`.                                        | Integration Test (wiremock)           | Fallback to cached payment data         |
| `DatabaseTimeout`       | Simulate DB latency (e.g., 5s delay on query).                                     | Integration Test (PostgreSQL mock)    | Return `504 Gateway Timeout`             |

---

### **Phase 3: Automate Error Case Testing**
#### **Tools/Libraries**:
- **Unit Tests**:
  - `pytest` (Python) with `unittest.mock`.
  - `Jest` (JavaScript) for edge-case assertions.
- **Integration Tests**:
  - **Mocking**: `WireMock` (HTTP), `Mockito` (Java), `Faker` (database rows).
  - **Chaos Engineering**: `Gremlin`, `Chaos Monkey` (random failures).
- **Performance/Load Testing**:
  - `Locust`, `k6` (simulate rate limits).
- **CI/CD**:
  - Run error tests in a separate pipeline phase (e.g., after unit tests).
  - Example GitHub Actions snippet:
    ```yaml
    name: Error Case Tests
    on: [push]
    jobs:
      test-errors:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - run: python -m pytest tests/error_cases/ --tb=short
    ```

---

### **Phase 4: Validate Error Handling**
1. **Assertions**:
   - **HTTP Responses**: Check status codes (e.g., `assert response.status == 404`).
   - **Logs**: Verify error messages (e.g., `assert "DatabaseConnectionRefused" in logs`).
   - **Fallbacks**: Test grace degradation (e.g., cached response instead of 500 error).
2. **Edge Cases**:
   - **Boundary Values**: Test `null`, `min/max`, or empty inputs.
     Example:
     ```python
     # Unit test for empty string
     def test_empty_name_rejection():
         response = requests.post("/api/user", json={"name": ""})
         assert response.status_code == 400
         assert "name" in response.json()["errors"]
     ```
   - **Race Conditions**: Use async tools (e.g., `pytest-asyncio`) to test concurrent errors.
   - **Intermittent Failures**: Run tests multiple times (e.g., 10 iterations) to catch flakiness.

---

### **Phase 5: Document and Retest**
- **Update Schema**: Add fixed errors to the schema with `Status: Resolved` and `FixedIn: vX.Y.Z`.
- **Retest Scenarios**: Verify new edge cases introduced by fixes (e.g., if you patch a timeout, test longer delays).
- **Knowledge Base**: Maintain a **Failure Modes Catalog** (e.g., Confluence page) with:
  - Root causes of past errors.
  - Mitigation strategies (e.g., retries, circuit breakers).
  - Ownership (team responsible for fixing similar errors).

---

## **Query Examples**

### **1. API Error Testing (REST)**
**Scenario**: Test `POST /api/payment` with invalid card details.
**Query**:
```http
POST /api/payment HTTP/1.1
Host: payments.example.com
Content-Type: application/json

{
  "card_number": "1234",  // Invalid (too short)
  "expiry_date": "12/2025",
  "cvc": "123"
}
```
**Expected**:
- Response: `400 Bad Request` with body:
  ```json
  {
    "errors": {
      "card_number": "Must be 16 digits."
    }
  }
  ```

**Automated Test (Python)**:
```python
import requests
import pytest

def test_invalid_card_number():
    response = requests.post(
        "https://payments.example.com/api/payment",
        json={"card_number": "1234", "expiry_date": "12/2025", "cvc": "123"}
    )
    assert response.status_code == 400
    assert response.json()["errors"]["card_number"] == "Must be 16 digits."
```

---

### **2. Database Error Testing**
**Scenario**: Simulate a `FOREIGN KEY` violation in PostgreSQL.
**Query**:
```sql
-- Insert invalid data (orphan record)
INSERT INTO orders (user_id) VALUES (99999999);  -- user_id doesn't exist
```
**Expected**:
- Rollback transaction with error:
  ```
  ERROR: insert or update on table "orders" violates foreign key constraint
  "orders_user_id_fkey"
  ```

**Automated Test (SQLAlchemy)**:
```python
from sqlalchemy.exc import IntegrityError
from models import session, Order

def test_foreign_key_violation():
    with pytest.raises(IntegrityError) as exc_info:
        session.add(Order(user_id=99999999))  # Invalid user_id
        session.commit()
    assert "violates foreign key" in str(exc_info.value)
```

---

### **3. External API Error Testing**
**Scenario**: Mock Stripe API to return `402 Payment Required`.
**Setup**: Use `WireMock` to intercept `/v1/charges`:
```java
// WireMock server (Java)
stubFor(
    post(urlEqualTo("/v1/charges"))
        .willReturn(aResponse()
            .withStatus(402)
            .withBody("{\"error\":{\"code\":\"card_declined\"}}")));
```
**Query**:
```http
POST /api/charge HTTP/1.1
Host: payments.example.com
Content-Type: application/json

{
  "amount": 100,
  "currency": "USD"
}
```
**Expected**:
- Frontend shows: *"Payment declined. Try another card."*
- Backend logs error and retries (if configured).

**Automated Test (Python + requests)**:
```python
import requests_mock

def test_stripe_payment_decline():
    with requests_mock.Mocker() as m:
        m.post("https://api.stripe.com/v1/charges", json={
            "error": {"code": "card_declined"}
        }, status_code=402)

        response = requests.post(
            "https://payments.example.com/api/charge",
            json={"amount": 100, "currency": "USD"}
        )
        assert response.json() == {"status": "failed", "message": "Payment declined"}
```

---

### **4. Load/Concurrency Error Testing**
**Scenario**: Test rate limiting with 1000 concurrent requests.
**Tool**: `Locust` file (`locustfile.py`):
```python
from locust import HttpUser, task

class ApiUser(HttpUser):
    @task
    def trigger_rate_limit(self):
        self.client.get("/api/health")
```
**Expected**:
- After 500 requests, server returns `429 Too Many Requests`.
- Error logs include:
  ```
  [2023-10-01T12:00:00] [ERROR] Rate limit exceeded (1000 reqs/min)
  ```

**Run Locust**:
```bash
locust -f locustfile.py --host=https://api.example.com --users 1000 --spawn-rate 100
```

---

## **Related Patterns**

1. **[Chaos Engineering]**
   - *Purpose*: Intentionally disrupt systems to test resilience.
   - *Connection*: Error case testing is a subset of chaos engineering (focused on specific failures).
   - *Tools*: Gremlin, Chaos Monkey, Chaos Mesh.

2. **[Boundary Value Analysis]**
   - *Purpose*: Test extreme values (e.g., min/max inputs, nulls).
   - *Connection*: Complements Error Case Testing by identifying edge cases that may trigger errors.
   - *Example*: Test `age = -1` or `age = 150` in user registration.

3. **[Defensive Programming]**
   - *Purpose*: Write code to handle errors proactively (e.g., input validation, timeouts).
   - *Connection*: Error Case Testing validates whether defensive measures work.
   - *Techniques*:
     - Use `try-catch` blocks (avoid swallowing exceptions).
     - Validate inputs early (e.g., with Pydantic/Zod).
     - Set timeouts for external calls.

4. **[Retries and Circuit Breakers]**
   - *Purpose*: Automatically retry failed operations or avoid cascading failures.
   - *Connection*: Error Case Testing validates retry logic (e.g., does the system recover from a `503` after retries?).
   - *Tools*: `resilience4j` (Java), `tenacity` (Python), `Hystrix` (legacy).

5. **[Property-Based Testing]**
   - *Purpose*: Generate random inputs to find errors (e.g., Fuzz Testing).
   - *Connection*: Useful for uncovering unseen error cases.
   - *Tools*: `Hypothesis` (Python), `QuickCheck` (Haskell), ` AFL` (low-level fuzzing).

6. **[Mocking and Stubs]**
   - *Purpose*: Isolate tests by replacing dependencies with controlled fakes.
   - *Connection*: Critical for testing external errors (e.g., mocking a failed database).
   - *Example*: Use `unittest.mock` or `Sinon.js` to simulate API timeouts.

7. **[Observability Patterns]**
   - *Purpose*: Log, monitor, and alert on errors in production.
   - *Connection*: Error Case Testing should include checks for observability (e.g., logs, metrics, traces).
   - *Example*: Verify that a `500` error triggers a Slack alert.

---

## **Anti-Patterns to Avoid**
1. **Overlapping Error Cases**:
   - *Problem*: Testing the same error twice (e.g., duplicate `404` scenarios).
   - *Fix*: Use a **unique error case ID** and track coverage.

2. **Ignoring Intermittent Errors**:
   - *Problem*: Skipping tests that fail sporadically (e.g., race conditions).
   - *Fix*: Retry tests multiple times or use chaos tools to force conditions.

3. **Testing Only Happy Paths**:
   - *Problem*: Writing tests that assume valid inputs.
   - *Fix*: Adopt [Failure-Driven Development](https://www.oreilly.com/library/view/failure-driven-development/9781680500756/) (start with errors).

4. **Hardcoding Error Responses**:
   - *Problem*: Mocking errors in a way that hides real-world variability.
   - *Fix*: Use parameterized tests or generate random error payloads.

5. **No Retesting After Fixes**:
   - *Problem*: Fixing a bug without verifying it didn’t break other scenarios.
   - *Fix*: Run the full error case suite in CI after fixes.

---

## **Further Reading**
- **Books**:
  - *The Art of Software Testing* (Glenford Myers) – Foundations of error testing.
  - *Chaos Engineering* (Gregorski) – Advanced resilience testing.
- **Papers**:
  - [Error Guessing for Software Testing](https://ieeexplore.ieee.org/document/6584468) (Fraser & Arcuri).
- **Tools**:
  - [ErrorStorm](https://github.com/ErrorStorm/errorstorm) (Qt error testing).
  - [Fuzz Testing with AFL](https://afl.fuzzingbook.org/) (low-level input generation).

---
**Last Updated**: [Date]
**Version**: 1.2