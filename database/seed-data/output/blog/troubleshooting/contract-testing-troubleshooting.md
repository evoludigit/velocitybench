# **Debugging Contract Testing & API Mocking: A Troubleshooting Guide**

## **1. Pattern Summary**
The **Contract Testing & API Mocking** pattern ensures that API consumers (e.g., microservices) remain compatible with providers (e.g., payment gateways, databases) without relying on live services. This approach:
- Defines API contracts (e.g., OpenAPI/Swagger specs, JSON Schema, or Protobuf).
- Uses **Consumer-Driven Contracts (CDC)** to validate that consumers behave correctly against a mock of the provider’s contract.
- Avoids slow integration tests by replacing real dependencies with lightweight mocks.

---

## **2. Symptom Checklist**
Check if these issues align with contract testing problems:

✅ **Provider changes break consumers**
   - New API field introduced → Consumers fail to parse.
   - Endpoint removed → Consumers throw `404` in production.

✅ **Slow integration tests**
   - Tests require spinning up databases, message brokers, or external services.
   - CI/CD pipeline hangs due to dependencies.

✅ **Flaky tests**
   - Tests fail intermittently due to network latency, timeouts, or external service instability.
   - Mocks behave differently in different environments.

✅ **Late discovery of contract violations**
   - Bugs only appear in staging/production, not in unit or contract tests.
   - No early feedback when providers change their APIs.

✅ **Mocks not aligned with real provider responses**
   - Mock responses differ from the actual API due to manual updates.
   - Consumer logic fails when mocked `200 OK` responses don’t match real `200 OK` responses.

✅ **Missing contract definitions**
   - No OpenAPI/Swagger spec or JSON Schema exists.
   - No clear definition of expected request/response formats.

---

## **3. Common Issues & Fixes**

### **Issue 1: Provider Changes Break Consumers**
**Symptom:**
A provider introduces a new field in a response schema, but consumers fail to handle it (e.g., `NullPointerException` on missing property).

**Debugging Steps:**
1. **Check contract definitions**
   - Compare the **current contract spec** (e.g., OpenAPI file) with the **provider’s actual response**.
   - Example: If a provider adds `{ "new_field": "string" }` but consumers expect `{ "old_field": "string" }`, they’ll crash.

2. **Update consumer tests to match new contract**
   ```java
   // Before (failing test)
   assertThat(response.get("old_field")).isEqualTo("value");

   // After (updated test)
   assertThat(response.get("old_field")).isEqualTo("value");
   assertThat(response.get("new_field")).isEqualTo("value"); // New field
   ```

3. **Use a contract testing tool to auto-generate mocks**
   - Tools like **Pact**, **WireMock**, or **Spring Cloud Contract** can generate mocks from the latest contract.

**Fix:**
```bash
# Example: Update Pact contract with new field
pact-broker update-contract --provider=payment-gateway --consumer=order-service --version=1.2.0
```

---

### **Issue 2: Slow Integration Tests**
**Symptom:**
Tests take 10+ minutes due to database/broker initialization.

**Debugging Steps:**
1. **Identify the bottleneck**
   - Is the mock slow? (e.g., WireMock takes 2s per request)
   - Is the database mock (e.g., H2) slower than the real one?

2. **Replace slow mocks with in-memory alternatives**
   - Example: Use **Mockito** for simple object mocking.
   - Example: Use **Testcontainers** for lightweight containers.

**Fix: Replace H2 with Testcontainers (PostgreSQL)**
```java
@DynamicPropertySource
static void configureProperties(DynamicPropertyRegistry registry) {
    registry.add("spring.datasource.url", () ->
        Testcontainers.forClass(OrderService.class)
            .postgres()
            .getJdbcUrl());
}
```

---

### **Issue 3: Flaky Tests**
**Symptom:**
Tests pass in CI but fail locally due to environmental differences.

**Debugging Steps:**
1. **Check for timing issues**
   - Example: A mock returns a delay (`Thread.sleep(1000)`), but CI runs faster.

2. **Use deterministic mocks**
   - Avoid `Thread.sleep()`; use **fixed delays** or **asynchronous mocks**.
   - Example: WireMock with `fixedDelayMillis(500)`

**Fix:**
```java
@WireMockRule
public void setupMocks() {
    stubFor(get(urlEqualTo("/api/orders"))
        .withHeader("Authorization", equalTo("Bearer token"))
        .willReturn(aResponse()
            .withStatus(200)
            .withBody("{\"id\":123}")
            .withFixedDelay(MILLISECONDS, 200))); // Fixed delay
}
```

---

### **Issue 4: Late Discovery of Contract Violations**
**Symptom:**
Bugs only appear in production, not in contract tests.

**Debugging Steps:**
1. **Check if tests are running against outdated contracts**
   - Example: Pact tests use `version=1.0.0`, but the real provider is on `2.0.0`.

2. **Update contract tests with the latest provider version**
   ```bash
   pact-broker update-contract --provider=payment-gateway --consumer=order-service --version=2.0.0
   ```

**Fix: Enforce contract updates in CI**
```yaml
# GitHub Actions example
- name: Update Pact contracts
  run: pact-broker publish-version --version=2.0.0
```

---

### **Issue 5: Mocks Not Aligned with Real API**
**Symptom:**
Mock returns `{ "status": "success" }`, but real API returns `{ "success": true }`.

**Debugging Steps:**
1. **Compare mock responses with real API calls**
   ```bash
   # Record a real API call with Pact
   pact-mock-service provider --port=8080 --pact-dir=pacts
   curl -XGET http://localhost:8080/api/orders/1 | jq .
   ```

2. **Update mocks to match real responses**
   ```java
   // WireMock setup matching real API
   stubFor(get(urlEqualTo("/api/orders/1"))
       .willReturn(aResponse()
           .withStatus(200)
           .withBody("{\"success\": true, \"data\": [...]}")));
   ```

---

## **4. Debugging Tools & Techniques**

| **Tool**               | **Use Case**                                                                 |
|-------------------------|-----------------------------------------------------------------------------|
| **Pact**               | Consumer-Driven Contract Testing (CDCT). Records provider expectations.     |
| **WireMock**           | Lightweight HTTP mock server for testing.                                  |
| **Postman/Newman**     | Generate mocks from Postman collections.                                   |
| **Spring Cloud Contract** | Integration tests using WireMock + assertions.                           |
| **Mockito**            | Unit-level mocking for complex objects.                                   |
| **Testcontainers**     | Spin up lightweight Docker containers for testing.                       |
| **OpenAPI Validator**  | Validate API specs against real responses.                                |
| **Grafana/Tempo**      | Debug contract failures in distributed tracing.                           |

---

### **Debugging Workflow**
1. **Reproduce the issue**
   - Run `pact-broker verify` to check if consumer contracts match the provider.
   - Use `curl` to manually test the mock vs. real API.

2. **Check logs**
   - Pact: `pact-broker logs --consumer=order-service`
   - WireMock: `curl http://localhost:8080/__admin/info`

3. **Update contracts & mocks**
   - If a mismatch exists, update the consumer’s contract test or the mock server.

---

## **5. Prevention Strategies**

### **1. Automate Contract Testing in CI**
```yaml
# GitHub Actions example
jobs:
  test-contracts:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pact-broker verify --provider=payment-gateway --consumer=order-service
```

### **2. Use Versioned Contracts**
- Tag contract versions (`v1.0.0`, `v1.1.0`) to track changes.
- Use **Pact Broker** to enforce backward/forward compatibility.

### **3. Shift Left with Early Contract Validation**
- Validate contracts **before** writing business logic.
- Example: Use **OpenAPI** to generate mocks before coding consumers.

### **4. Document API Changes**
- Maintain a **CHANGELOG** for the provider API.
- Example:
  ```
  v2.0.0:
    - Added: `payment_status` field in `/orders/{id}`
    - Deprecated: `status_code` (use `payment_status` instead)
  ```

### **5. Use Schema Validation**
- Validate responses against **JSON Schema** or **Protobuf**.
- Example (using `ajv` in Node.js):
  ```javascript
  const ajv = require('ajv');
  const validate = ajv.compile({
    type: 'object',
    properties: {
      id: { type: 'number' },
      name: { type: 'string' }
    }
  });
  validate(response); // Throws if invalid
  ```

### **6. Monitor Contract Health**
- Use **Pact Broker** to track contract violations over time.
- Set up alerts for broken contracts:
  ```bash
  pact-broker event listen --event=contract-broken --webhook-url=https://webhook.example.com
  ```

---

## **6. Summary Checklist for Resolution**
| **Issue**                     | **Quick Fix**                                  | **Long-Term Fix**                          |
|-------------------------------|------------------------------------------------|--------------------------------------------|
| Provider changes break consumers | Update contract tests + mocks                  | Use versioned contracts + backward compat |
| Slow integration tests         | Replace slow mocks (H2 → Testcontainers)       | Pre-generate mocks in CI                   |
| Flaky tests                    | Use fixed delays in mocks                     | Remove environmental dependencies         |
| Late contract violations       | Run `pact-broker verify` in CI                 | Enforce contract testing before PR merge   |
| Mocks misaligned with real API  | Record real API calls with Pact                | Auto-sync mocks with provider changes      |

---

## **7. Final Recommendations**
- **Adopt Pact/WireMock early** to avoid last-minute contract issues.
- **Run contract tests in CI** before merging PRs.
- **Use schema validation** to catch mismatches early.
- **Document API changes** to prevent silent breaking changes.

By following this guide, you’ll minimize contract-related bugs, reduce flaky tests, and ensure API consumers stay resilient against provider changes. 🚀