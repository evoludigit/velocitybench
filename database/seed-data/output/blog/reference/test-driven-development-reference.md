# **[Pattern] Test-Driven Development (TDD) Reference Guide**

---

## **Overview**
**Test-Driven Development (TDD)** is a software development methodology where tests are written *before* implementing functionality. The core principle is the **Red-Green-Refactor** cycle: **Red** (write a failing test), **Green** (implement minimal code to pass the test), and **Refactor** (optimize while preserving test coverage). TDD ensures high code quality, early bug detection, and maintainable designs by aligning implementation with explicit, automated test expectations. It is widely adopted in agile and iterative development workflows to reduce technical debt and improve collaboration between developers and testers.

---

## **Key Schema Reference**
| **Component**               | **Description**                                                                                     | **Key Attributes**                                                                                     |
|-----------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| **Test Cycle**              | The core TDD workflow comprising three phases: **Red**, **Green**, and **Refactor**.                  | - **Red**: Write a failing test for new/changed functionality.                                           |
|                             |                                                                                                     | - **Green**: Implement minimal code to pass the test (no dependencies on other features).              |
|                             |                                                                                                     | - **Refactor**: Clean code while preserving test coverage (no regression).                              |
| **Test Fixtures**           | Setup or mock data required to execute a test suite.                                               | - **Static Data**: Hardcoded inputs (e.g., dummy user objects).                                       |
|                             |                                                                                                     | - **Dynamic Data**: Generated data (e.g., random API responses).                                      |
|                             |                                                                                                     | - **Mocks/Stubs**: Isolated dependencies (e.g., simulated database calls).                              |
| **Test Coverage**           | Metrics tracking lines of code or branches tested.                                                 | - **Line Coverage**: Percentage of code executed by tests.                                              |
|                             |                                                                                                     | - **Branch Coverage**: Percentage of conditional paths tested.                                          |
|                             |                                                                                                     | - **Mutation Coverage**: Tests’ ability to detect mutants (intentionally introduced bugs).              |
| **Assertion Rules**         | Expected outcomes for test cases.                                                                   | - **Equality Checks** (`assertEquals()`).                                                               |
|                             |                                                                                                     | - **Range/Threshold Checks** (`assertTrue(x > 5)`).                                                   |
|                             |                                                                                                     | - **Exception Handling** (`assertThrows(Exception.class, () -> riskyOperation())`).                     |
| **Refactoring Constraints** | Rules to avoid breaking existing tests during optimization.                                         | - **Test-Driven Refactor**: Run tests after each change; revert if failures occur.                     |
|                             |                                                                                                     | - **Behavioral Invariants**: Ensure refactored code matches pre-refactor test behavior.                 |
| **Tooling**                 | Tools to support TDD workflows.                                                                    | - **Test Frameworks**: JUnit (Java), pytest (Python), RSpec (Ruby).                                   |
|                             |                                                                                                     | - **Mocking Libraries**: Mockito (Java), unittest.mock (Python).                                       |
|                             |                                                                                                     | - **CI/CD Integration**: Build tools (Maven/Gradle) + CI systems (Jenkins/GitHub Actions).              |

---

## **Implementation Workflow**
### **1. Red Phase: Write a Failing Test**
- **Purpose**: Define the desired functionality as a test case.
- **Steps**:
  1. Identify the smallest feature to implement (e.g., "User login validation").
  2. Write a test that **fails** due to unimplemented logic.
     ```java
     // Example: Failing JUnit test (Red phase)
     @Test
     public void login_shouldFailForEmptyCredentials() {
         User user = new User("", "");
         assertFalse(user.validateLogin()); // Fails (user.validateLogin() not implemented)
     }
     ```
- **Key Rules**:
  - Tests must fail *before* implementation.
  - Use **descriptive test names** (e.g., `login_shouldFailForEmptyCredentials`).
  - Avoid testing implementation details (test behavior, not internals).

### **2. Green Phase: Implement Minimal Code**
- **Purpose**: Write the *bare minimum* code to pass the test.
- **Steps**:
  1. Implement the feature **only** to satisfy the failing test.
     ```java
     // Minimal Green-phase implementation
     public boolean validateLogin(String username, String password) {
         return !username.isEmpty() && !password.isEmpty(); // Passes the test
     }
     ```
  2. Run tests to confirm **single success**. No additional features yet.
- **Key Rules**:
  - Prioritize **testability**: Design code to be easily mocked or isolated.
  - Avoid premature optimization (e.g., database queries before validation logic).
  - Use **dependency injection** to mock external services (e.g., APIs, databases).

### **3. Refactor Phase: Optimize Without Breaking Tests**
- **Purpose**: Improve code structure while maintaining test coverage.
- **Steps**:
  1. Run tests to establish a **baseline**.
  2. Refactor **one small change at a time** (e.g., extract methods, rename variables).
  3. Verify tests still pass after each change.
     ```java
     // Refactored version (same behavior, cleaner code)
     public boolean validateLogin(String username, String password) {
         return isFieldValid(username) && isFieldValid(password);
     }

     private boolean isFieldValid(String field) {
         return !field.isEmpty();
     }
     ```
- **Key Rules**:
  - **Never** remove or alter tests during refactoring.
  - Use **static analysis tools** (e.g., SonarQube) to identify refactoring opportunities.
  - Document breaking changes in a **changelog** if tests are modified intentionally.

---

## **Query Examples**
### **Example 1: Writing a TDD Test for a Calculator**
**Goal**: Implement a `add()` method in a `Calculator` class.
1. **Red Phase**:
   ```java
   @Test
   public void add_shouldReturnSumOfTwoNumbers() {
       Calculator calc = new Calculator();
       assertEquals(5, calc.add(2, 3)); // Fails (Calculator.add() not implemented)
   }
   ```
2. **Green Phase**:
   ```java
   public class Calculator {
       public int add(int a, int b) {
           return a + b; // Passes the test
       }
   }
   ```
3. **Refactor Phase**:
   - Extract `add()` into a private method if reusable (though not needed here).
   - Add edge-case tests (e.g., negative numbers, zero).

### **Example 2: Testing API Communication with Mocks**
**Goal**: Mock an external API to test a `WeatherService`.
1. **Red Phase**:
   ```java
   @Test
   public void getWeather_shouldReturnSunnyForGivenLocation() {
       WeatherService service = new WeatherService();
       assertEquals("Sunny", service.getWeather("New York")); // Fails
   }
   ```
2. **Green Phase** (using Mockito):
   ```java
   @Test
   public void getWeather_shouldReturnSunnyForGivenLocation() {
       WeatherService service = Mockito.spy(new WeatherService());
       Mockito.when(service.fetchFromAPI("New York")).thenReturn("Sunny");
       assertEquals("Sunny", service.getWeather("New York")); // Passes
   }
   ```
3. **Refactor Phase**:
   - Replace hardcoded "Sunny" with a configuration.
   - Add tests for error cases (e.g., `APIConnectionException`).

### **Example 3: Refactoring Without Breaking Tests**
**Scenario**: The `add()` method now has duplicate logic.
1. **Before**:
   ```java
   public int add(int a, int b) {
       return a + b;
   }
   public int multiply(int a, int b) {
       return a * b;
   }
   ```
2. **Red Phase**: Add a test for a shared `performOperation()` method.
   ```java
   @Test
   public void performOperation_shouldReturnSum() {
       Calculator calc = new Calculator();
       assertEquals(5, calc.performOperation("add", 2, 3)); // Fails
   }
   ```
3. **Green Phase**: Implement `performOperation()`.
   ```java
   public int performOperation(String op, int a, int b) {
       if ("add".equals(op)) return a + b;
       else if ("multiply".equals(op)) return a * b;
       throw new UnsupportedOperationException(op);
   }
   ```
4. **Refactor Phase**: Update `add()` and `multiply()` to use `performOperation()`.
   ```java
   public int add(int a, int b) {
       return performOperation("add", a, b);
   }
   public int multiply(int a, int b) {
       return performOperation("multiply", a, b);
   }
   ```
   - Run all tests to confirm no regressions.

---

## **Common Pitfalls & Mitigations**
| **Pitfall**                          | **Description**                                                                                     | **Mitigation**                                                                                           |
|---------------------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| **Over-Testing**                      | Writing tests for implementation details (e.g., private methods) instead of behavior.               | Follow the **"Arrange-Act-Assert"** pattern; test public APIs only.                                     |
| **Test Bloating**                     | Tests become too complex to maintain.                                                               | Split large tests into smaller, focused ones (e.g., separate validation from business logic tests).   |
| **Skipping Tests**                    | Manually bypassing tests to "save time" during development.                                        | Integrate tests into the **build pipeline** (e.g., CI/CD). Every commit must pass tests.                |
| **Ignoring Test Coverage Gaps**        | High line coverage but low branching/mutation coverage.                                            | Use **mutation testing tools** (e.g., PITest) to identify weak tests.                                     |
| **Circular Dependencies**             | Tests depend on other tests, making isolated debugging difficult.                                  | Design tests to be **independent** (e.g., use separate test classes or namespaces).                     |
| **Premature Refactoring**             | Refactoring before tests are fully passing.                                                          | Adhere strictly to the **Red-Green-Refactor** cycle.                                                   |

---

## **Tooling & Integrations**
| **Category**          | **Tools**                                                                                     | **Use Case**                                                                                             |
|-----------------------|-------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| **Test Frameworks**   | JUnit (Java), pytest (Python), RSpec (Ruby), Jest (JavaScript)                              | Writing and executing unit tests.                                                                        |
| **Mocking Libraries** | Mockito (Java), unittest.mock (Python), Sinon.js (JavaScript)                              | Isolating dependencies (e.g., databases, APIs) in unit tests.                                            |
| **CI/CD Integration** | Jenkins, GitHub Actions, GitLab CI, CircleCI                                                | Automating test execution on every commit/push.                                                          |
| **Test Coverage**     | JaCoCo (Java), Coverage.py (Python), Istanbul (JavaScript)                                   | Tracking and visualizing test coverage metrics.                                                         |
| **Mutation Testing**  | PITest (Java), Stryker (JavaScript), MutPy (Python)                                         | Detecting weak tests by introducing bugs and checking if tests catch them.                               |
| **Test Data Generation** | Testcontainers (containers), Faker (fake data), Hypothesis (Python)                   | Generating realistic test data for integration/tests.                                                    |

---

## **Related Patterns**
1. **Behavior-Driven Development (BDD)**
   - **Connection**: TDD focuses on unit tests, while BDD extends this to **acceptance criteria** using language like Gherkin (e.g., `Given-When-Then` scenarios).
   - **When to Use**: Combine TDD for unit tests with BDD for higher-level requirements validation.

2. **Continuous Integration (CI)**
   - **Connection**: TDD tests are **automated and run in CI pipelines** to catch regressions early.
   - **When to Use**: Mandate TDD in CI to ensure every commit is test-covered.

3. **Dependency Injection (DI)**
   - **Connection**: TDD encourages **mocking dependencies**, which is facilitated by DI (e.g., Spring, Dagger).
   - **When to Use**: Implement DI to make TDD easier (e.g., swapping real databases with in-memory mocks).

4. **Contract Testing**
   - **Connection**: TDD tests can serve as **contract tests** for microservices (e.g., `Pact` framework).
   - **When to Use**: Validate inter-service communication without deploying full stack.

5. **Property-Based Testing**
   - **Connection**: TDD tests can be supplemented with **property-based tests** (e.g., Hypothesis, QuickCheck) to validate invariants.
   - **When to Use**: Test edge cases dynamically (e.g., "For any `x`, `f(x) > 0` if `x > 0`").

---

## **When to Avoid TDD**
- **Exploratory Development**: When quick iterations require flexibility over strict test-driven design.
- **Legacy Codebases**: Refactoring existing code may require **test-first** adjustments to avoid fragility.
- **Prototyping**: Early-stage ideas may change rapidly; TDD can slow down iteration.
- **Non-Critical Features**: Low-priority modules may not justify initial test overhead.

---
## **Key Takeaways**
- **Start Small**: TDD works best for **modular, isolated features**.
- **Automate Everything**: Tests should run on every build (CI).
- **Balance Speed and Quality**: TDD reduces long-term bugs but may slow initial development.
- **Collaborate**: Pair programming with TDD improves knowledge sharing.
- **Iterate**: Use refactoring to keep code clean while preserving test coverage.

---
**Further Reading**:
- [Martin Fowler: Test-Driven Development](https://martinfowler.com/articles/tdd.html)
- *Growing Object-Oriented Software, Guided by Tests* – Freeman & Pryce
- [JUnit User Guide](https://junit.org/junit5/docs/current/user-guide/)