---
# **[Pattern] Hybrid Testing Reference Guide**

## **Overview**

**Hybrid Testing** combines **Unit Testing**, **Integration Testing**, and **End-to-End (E2E) Testing** into a cohesive approach, leveraging automation to verify application behavior at multiple layers. Unlike traditional siloed testing, hybrid testing integrates *unit and integration tests* (often via TDD/BDD frameworks) with *UI-based E2E tests*, reducing redundancy while improving coverage.

Key benefits include:
✔ **Faster feedback loops** (unit tests run in CI/CD pipelines)
✔ **Reduced duplication** (shared test logic via test libraries)
✔ **Scalability** (parallel execution of unit/integration tests)
✔ **Better failure isolation** (unit tests pinpoint logical errors; E2E validates system-wide behavioral correctness)

This pattern is ideal for **microservices**, **full-stack applications**, and teams adopting **DevOps** practices.

---

## **Implementation Details**

### **1. Core Components**
Hybrid Testing relies on three interconnected layers:

| **Component**          | **Definition**                                                                 | **Tools examples**                                                                 |
|------------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **Unit Tests**         | Isolated tests validating individual functions/classes (e.g., business logic). | Jest, Pytest, Mocha, JUnit, Cypress (component tests)                             |
| **Integration Tests**  | Tests verifying interactions between services/modules (e.g., DB ↔ API).       | Spring Boot Test, pytest-django, Postman Newman, Karate DSL                        |
| **E2E Tests**          | Tests simulating real user flows (UI + API + backend validation).            | Playwright, Selenium, Appium, Cypress (E2E), TestCafe                                |
| **Test Automation Layer** | Orchestrates test execution, reporting, and environment setup.            | GitHub Actions, Jenkins, Azure DevOps, TestRail, Testim                              |
| **Test Data Management** | Ensures consistent, isolated test environments.                           | Testcontainers, Factory Boy, Faker, Test Data Builder (TDB)                       |

---

### **2. Key Concepts**

#### **A. Test Pyramid Integration**
Hybrid testing aligns with the **test pyramid** but emphasizes *shared test utilities* (e.g., test fixtures, mocks) to avoid redundancy:

```
          [     E2E Tests      ]
         /               \
[Unit Tests]       [Integration Tests]
```
- **Rule of Thumb**: Aim for a **50:30:20 ratio** (Unit:Integration:E2E).
- **Anti-pattern**: Over-reliance on E2E tests (slow, brittle).

#### **B. Test Layer Interdependencies**
| **Layer**       | **Depends On**                          | **Example Dependency**                          |
|-----------------|----------------------------------------|------------------------------------------------|
| Unit Tests      | Pure logic (no external dependencies).  | Pure Python/JS classes                          |
| Integration     | Unit tests + shared modules.           | Mocked DB + API contracts                       |
| E2E Tests       | Integration tests + UI components.      | Playwright interacting with a live backend      |

#### **C. Test Isolation Strategies**
| **Strategy**            | **Use Case**                                  | **Implementation**                              |
|-------------------------|---------------------------------------------|------------------------------------------------|
| **Mocking/Stubs**       | Replace external services (e.g., APIs).     | Sinon.js, Mockito, Pytest-mock                 |
| **Test Containers**     | Spin up real DBs/services for integration.  | Testcontainers (Python/Node), Docker Compose   |
| **Feature Flags**       | Disable non-critical features for testing.   | LaunchDarkly, Flagsmith                        |
| **Parallel Execution**  | Run unit/integration tests concurrently.       | Jest `--maxWorkers`, pytest-xdist                |

---

### **3. Schema Reference**

#### **Hybrid Test Workflow Schema**
```mermaid
flowchart TD
    A[CI Pipeline Trigger] -->|Start| B{Test Type?}
    B -->|Unit| C[Run Unit Tests\n(Jest/Pytest)]
    B -->|Integration| D[Run Integration Tests\n(Spring Boot Test)]
    B -->|E2E| E[Run E2E Tests\n(Playwright)]
    C -->|Fail| F[Notify Team\n(Slack/Webhook)]
    D -->|Fail| F
    E -->|Fail| F
    C -->|Pass| G[Build Artifacts]
    D -->|Pass| G
    E -->|Pass| G
    F -->|Retries| H[Check Test Retry Policy]
    H -->|Exhausted| I[Block Deployment]
```

#### **Test Environment Schema**
| **Field**               | **Description**                                                                 | **Example Value**                          |
|-------------------------|-------------------------------------------------------------------------------|--------------------------------------------|
| `test_type`             | Unit, Integration, or E2E.                                                    | `"integration"`                            |
| `environment`           | Dev, Staging, Production-like.                                                | `"staging"`                                |
| `parallelism`           | Number of concurrent test runs.                                               | `"4"`                                      |
| `retries`               | Max retries on failure.                                                       | `2`                                        |
| `seeds`                 | Randomized inputs for deterministic tests.                                   | `["user123", "order456"]`                  |
| `mocking_strategy`      | How external dependencies are handled.                                       | `"testcontainers"`                         |
| `reporting_tool`        | Where test results are sent.                                                   | `"testrail"`                               |

---

## **Query Examples**

### **1. Running Unit Tests in CI**
```bash
# Example: Jest with parallel execution
npx jest --runInBand=false --maxWorkers=4 --coverage
```
**Output**:
```json
{
  "numFailedTests": 0,
  "numPassedTests": 120,
  "testEnvironment": "jsdom"
}
```

### **2. Triggering Integration Tests via API**
```bash
# Karate DSL example (API integration test)
# Run via Maven:
mvn test -Dgroups=integration
```
**Test File (`apiTests.feature`)**:
```javascript
Feature: Payment Service
  Scenario: Process payment
    Given url 'https://api.example.com/payments'
    And request {'amount': 100, 'token': 'valid_token'}
    When method post
    Then status 200
    And response contains 'success'
```

### **3. Executing E2E Tests with Playwright**
```typescript
// playwright.test.ts
import { test, expect } from '@playwright/test';

test('User flow: Login and checkout', async ({ page }) => {
  await page.goto('https://demo-app.com/login');
  await page.fill('#username', 'user@example.com');
  await page.fill('#password', 'secure123');
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL('https://demo-app.com/dashboard');
  // ... assert checkout flow
});
```
**Run via CLI**:
```bash
npx playwright test --project=chromium --workers=2
```

### **4. Filtering Test Results in TestRail**
```sql
-- SQL-like filter for TestRail API (JSON)
{
  "filter": {
    "test_cases": [
      {"id": 123},  -- Specific test case
      {"status_id": 5},  -- Only failed tests
      {"suite_id": 42}   -- Tests in "API Suite"
    ]
  }
}
```

---

## **Related Patterns**

| **Pattern**               | **Description**                                                                 | **When to Use**                              |
|---------------------------|-------------------------------------------------------------------------------|---------------------------------------------|
| **Test Data Factory**     | Generates synthetic test data (e.g., Faker, Factory Boy).                     | When mocking complex domains (e.g., user profiles). |
| **Contract Testing**      | Validates API contracts via Pact (e.g., consumer-driven contracts).           | Microservices communicating via APIs.       |
| **Canary Testing**        | Gradually rolls out E2E tests to a subset of users.                            | High-traffic apps (e.g., Netflix).          |
| **Behavior-Driven Dev (BDD)** | Uses Gherkin (Given-When-Then) for shared test specs.                        | Collaborative teams (QA + Devs).            |
| **Chaos Engineering**     | Intentionally fails components to test resilience (e.g., Kubernetes chaos). | Tolerant systems (e.g., cloud-native apps).  |
| **Performance Testing**   | Validates system under load (e.g., JMeter, k6).                               | Scalability-critical apps.                  |

---

## **Anti-Patterns to Avoid**
1. **Overlap**: Don’t duplicate tests across layers (e.g., write a unit test AND an E2E test for the same logic).
2. **Ignoring Flakiness**: E2E tests often fail intermittently. Use retries with **deterministic assertions**.
3. **Tight Coupling**: Avoid testing implementation details in E2E tests (focus on **user flows**, not code paths).
4. **No Test Isolation**: Shared test data across layers can cause flaky integration tests. Use **test containers** or **feature flags**.
5. **Slow CI Pipelines**: Prioritize unit/integration tests in CI; reserve E2E for **pre-production stages**.

---
**Further Reading**:
- [Martin Fowler: Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html)
- [TestContainers Documentation](https://testcontainers.com/)
- [Playwright Documentation](https://playwright.dev/)