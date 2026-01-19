# **[Testing Patterns] Reference Guide**

---

## **Overview**

The **Testing Patterns** framework defines reusable, domain-specific testing structures to improve test reliability, maintainability, and scalability. These patterns address common challenges in software testing by providing standardized approaches for test design, execution, and assertion logic. They help decompose complex tests into manageable components, reduce boilerplate code, and promote consistency across test suites.

Testing Patterns are particularly useful for:
- **State-driven testing** (e.g., verifying application state transitions).
- **Behavior-driven testing** (e.g., testing user workflows via scenarios).
- **Data-driven validation** (e.g., parameterized test inputs).
- **Integration and end-to-end (E2E) testing** (e.g., simulating user interactions).

By leveraging these patterns, test automation engineers and developers can write more maintainable, modular, and reusable test code while reducing redundancy and improving test coverage.

---

## **Schema Reference**

Below is a table outlining the core **Testing Patterns**, their purposes, and key attributes.

| **Pattern Name**          | **Purpose**                                                                 | **Key Attributes**                                                                                     | **Use Case Examples**                                                                                     |
|---------------------------|------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| **State Transition**      | Validate that an application correctly transitions between states.           | - **States**: Defined states of the system (e.g., `NewOrder`, `Processing`).                          | Order processing workflow: Verify `NewOrder` → `Processing` → `Shipped`.                               |
| **Scenario-Based**        | Model test cases as user workflows or story-like sequences.                | - **Steps**: Sequence of actions (e.g., `Login`, `AddToCart`, `Checkout`).                          | E-commerce checkout flow: Test from `Homepage` → `Search` → `Payment`.                                |
| **Data-Driven**           | Run the same test logic against multiple input datasets.                     | - **Test Data**: Externalized inputs (CSV, JSON, database).                                            | Validate user registration with different email formats, passwords, or edge cases.                     |
| **Page Object**           | Abstract UI elements into reusable objects for cleaner test code.            | - **Locators**: XPath, CSS selectors, or custom locators.                                              | Selenium/Puppeteer tests: DRY up element interactions like `loginButton.click()`.                       |
| **Mock Service**          | Isolate components by replacing dependencies with mocks or stubs.           | - **Interface**: Mock API response, database records, or external service calls.                      | Test a backend service without hitting a real database.                                                 |
| **Assertion Chaining**    | Combine assertions into logical sequences for validation.                  | - **Chainable Asserts**: Methods like `expect(result).to.be.true().and.equal("OK")`.                | Validate a JSON response contains both a `status` and `data` field.                                     |
| **Retry Mechanism**       | Automatically retry tests under transient failure conditions.                | - **Policy**: Max retries, delay between attempts (e.g., `maxRetries: 3`, `delay: 500ms`).           | Test API endpoints that may fail due to network latency.                                               |
| **Parallel Execution**    | Distribute test execution across multiple environments/threads.             | - **Parallelism Level**: Number of threads/environments (e.g., `parallel: 4`).                       | Run cross-browser tests simultaneously in CI/CD pipelines.                                             |
| **Template-Based**        | Define reusable test templates for common workflows.                        | - **Variables**: Placeholders for dynamic values (e.g., `${username}`).                              | Test login workflows with templatized credentials.                                                    |
| **A/B Test Validation**   | Validate A/B test results or experiment outcomes.                           | - **Metrics**: Click-through rates, conversion rates, or statistical significance.                   | Verify if a new UI button increases user engagement in a live environment.                          |

---

## **Implementation Details**

### **1. State Transition Pattern**
**Purpose**: Ensures the system correctly transitions between defined states.

#### **Structure**:
```plaintext
State1 → Action → State2 → Assertion
```
**Example (Pseudocode)**:
```javascript
const states = {
  NewOrder: { name: "NewOrder", validator: (order) => order.status === "NEW" },
  Processing: { name: "Processing", validator: (order) => order.status === "PROCESSING" }
};

test("Order state transition", async () => {
  const initialState = "NewOrder";
  const action = () => placeOrder(); // Simulate user action
  const expectedState = "Processing";

  const order = startFromState(initialState);
  action();
  const currentState = determineCurrentState(order);

  assert.strictEqual(currentState.name, expectedState.name);
});
```

**Key Considerations**:
- Define states as **immutable objects** to avoid logic duplication.
- Use **state validators** (e.g., lambdas) to verify transitions.
- Handle edge cases (e.g., invalid transitions) with assertions or retries.

---

### **2. Scenario-Based Pattern**
**Purpose**: Model tests as step-by-step user workflows.

#### **Structure**:
```plaintext
Scenario: [Title]
  Given [Initial Context]
  When [User Action]
  Then [Expected Outcome]
```

**Example (Gherkin Syntax)**:
```gherkin
Scenario: Checkout with valid payment
  Given I am on the product page
  When I add "Laptop" to cart and proceed to checkout
  Then I see the payment screen with total "$999.99"
```

**Implementation (Pseudocode)**:
```javascript
const checkoutScenario = {
  steps: [
    { type: "Given", action: () => navigateToProductPage("Laptop") },
    { type: "When", action: () => addToCart("Laptop").then(() => checkout()) },
    { type: "Then", assert: () => expect(paymentScreen.total).toEqual("$999.99") }
  ]
};

testScenario(checkoutScenario);
```

**Key Considerations**:
- Use **step definitions** to map Gherkin steps to executable code.
- Support **data tables** for parameterized scenarios.
- Integrate with tools like **Cucumber** or **SpecFlow**.

---

### **3. Data-Driven Pattern**
**Purpose**: Run tests with varied input datasets without duplicating logic.

#### **Structure**:
```plaintext
Test Logic + External Data Source (CSV/JSON/Database)
```

**Example (CSV Input)**:
| **Email**          | **Password** | **Expected Result** |
|--------------------|--------------|----------------------|
| valid@example.com  | SecurePass123 | Success              |
| invalid@          | WeakPass      | Error: Invalid Email  |

**Implementation (Pseudocode)**:
```javascript
const testData = require("./data-driven-test-data.csv");

testData.forEach((row) => {
  test(`Register with ${row.email}`, async () => {
    const result = await registerUser(row.email, row.password);
    expect(result).toMatch(row.ExpectedResult);
  });
});
```

**Key Considerations**:
- Store test data in **separate files** (e.g., JSON, CSV) for easy maintenance.
- Use **fixture libraries** (e.g., `jest-fixture` for Jest) to load data.
- Handle **data generation** (e.g., Faker.js) for synthetic test cases.

---

### **4. Page Object Pattern**
**Purpose**: Abstract UI elements into reusable objects to reduce duplication.

#### **Structure**:
```javascript
class LoginPage {
  constructor(page) {
    this.emailField = page.locator("#email");
    this.passwordField = page.locator("#password");
    this.loginButton = page.locator("button[type='submit']");
  }

  async fillCredentials(email, password) {
    await this.emailField.type(email);
    await this.passwordField.type(password);
  }

  async submit() {
    await this.loginButton.click();
  }
}
```

**Implementation (Playwright Example)**:
```javascript
const loginPage = new LoginPage(page);

test("Login with valid credentials", async () => {
  await loginPage.fillCredentials("user@example.com", "password123");
  await loginPage.submit();
  await expect(page).toHaveURL("/dashboard");
});
```

**Key Considerations**:
- **Locators should be stable** (avoid fragile XPath/CSS selectors).
- Group related elements into **page objects** (e.g., `DashboardPage`, `CheckoutPage`).
- Use **factory patterns** for dynamic page instantiation.

---

### **5. Mock Service Pattern**
**Purpose**: Isolate tests by replacing real dependencies with mocks.

#### **Structure**:
```plaintext
Real Service → Mock Stub/Stub → Test Logic
```

**Example (Mocking an API with Sinon)**:
```javascript
const sinon = require("sinon");
const { expect } = require("chai");

sinon.stub(apiService, "getUser").returns(Promise.resolve({ id: 1, name: "Test User" }));

test("Should fetch user data", async () => {
  const user = await apiService.getUser();
  expect(user.name).to.equal("Test User");
});

sinon.restore(); // Cleanup
```

**Key Considerations**:
- Use libraries like **Sinon**, **Mock Service Worker (MSW)**, or **WireMock**.
- Define **mock contracts** (expected calls, responses).
- Avoid **over-mocking** (keep tests focused on behavior, not implementation).

---

## **Query Examples**

### **1. Querying Test Results with a Retry Mechanism**
**Use Case**: Retry a flaky API test up to 3 times with a 1-second delay.

```javascript
import { retry } from "@testing-library/jest-dom";

const retryPolicy = { maxRetries: 3, delayMs: 1000 };

test("API response should be 200 (with retry)", async () => {
  await retry(
    async () => {
      const response = await fetch("/api/user");
      expect(response.status).toBe(200);
    },
    retryPolicy
  );
});
```

### **2. Parallel Execution in CI/CD**
**Use Case**: Run 4 parallel test suites in GitHub Actions.

```yaml
# .github/workflows/tests.yml
jobs:
  test:
    strategy:
      matrix:
        browser: [chrome, firefox, safari]
        parallel: [1, 2, 3, 4]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm install
      - run: npx playwright test --project=${{ matrix.browser }} --workers=${{ matrix.parallel }}
```

### **3. Data-Driven Test with JSON Input**
**Use Case**: Test login with multiple credential sets.

```javascript
const credentials = [
  { email: "valid@example.com", password: "Pass123!", status: "success" },
  { email: "invalid@", password: "wrong", status: "error" }
];

credentials.forEach((cred) => {
  test(`Login with ${cred.email} should ${cred.status}`, async () => {
    await login(cred.email, cred.password);
    if (cred.status === "success") {
      expect(page.url()).toContain("/dashboard");
    } else {
      expect(page).toHaveErrorMessage("Invalid credentials");
    }
  });
});
```

---

## **Related Patterns**

| **Related Pattern**       | **Description**                                                                 | **When to Use**                                                                 |
|---------------------------|---------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Page Object Model (POM)** | Extends **Page Object** with a factory for dynamic page instantiation.        | When managing many page objects in large applications.                           |
| **BDD (Behavior-Driven Dev)** | Combines **Scenario-Based** with natural language testing.                  | For collaborative testing with non-technical stakeholders.                       |
| **Test Containers**       | Spins up lightweight containers for reliable test environments.              | When tests require isolated, ephemeral environments (e.g., databases).          |
| **Property-Based Testing** | Tests against mathematical properties (e.g., "for all inputs X, output Y").  | For mathematical correctness (e.g., financial systems).                          |
| **Chaos Engineering**     | Intentionally introduces failures to test resilience.                          | For SLA/uptime guarantees (e.g., "System remains available during DB outages"). |
| **Contract Testing**      | Verifies API contracts between services using Pact.                            | For microservices architectures to ensure backward compatibility.              |
| **Non-Destructive Testing** | Tests without modifying production data.                                     | For compliance or security tests in live environments.                         |

---

## **Best Practices**
1. **Modularity**: Keep test files small and focused (e.g., `login.spec.js`, `checkout.spec.js`).
2. **Idempotency**: Design tests to be repeatable without side effects.
3. **Isolation**: Use mocks/stubs to avoid test interference (e.g., shared database state).
4. **Reporting**: Integrate with tools like **Allure**, **JUnit**, or **HTML reports**.
5. **Documentation**: Annotate test files with **purpose**, **preconditions**, and **expected outcomes**.
6. **Performance**: Optimize slow tests (e.g., parallel execution, caching).
7. **Security**: Avoid hardcoding credentials; use environment variables or vaults.