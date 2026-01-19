# **[Pattern] Testing Conventions Reference Guide**

---

## **Overview**
This guide outlines **Testing Conventions**, a structured approach to naming, organizing, and executing tests to ensure consistency, maintainability, and scalability across codebases. By following predefined conventions, teams reduce cognitive load, improve test discoverability, and streamline CI/CD pipelines. This pattern applies to unit, integration, and end-to-end tests, enforcing clarity in test intent, dependencies, and execution order.

---

## **Core Principles**
1. **Consistency**: Uniform naming, directory structure, and file extensions.
2. **Self-documenting**: Test names reflect their purpose and scope.
3. **Isolation**: Tests are modular and avoid shared state.
4. **Explicit Dependencies**: Mocks/stubs align with real-world conditions.
5. **Versioned Fixtures**: Test data evolves alongside application changes.

---

## **Schema Reference**

| **Category**               | **Convention**                                                                 | **Purpose**                                                                                     |
|---------------------------|-------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Test Suites**           | `/src/{module}/__tests__/` or `/test/{module}/`                             | Logical grouping of tests by module/component.                                                 |
| **Test Files**            | `{module}-{feature}.test.[js|ts|py]`                                                           | Filename includes module + feature (e.g., `auth-service.login.test.js`).                      |
| **Test Naming**           | `{describe}{optional: context} > {it|test} {scenario} [optional: of {context}]` | Describes "what" and "why" (e.g., `describe('UserService', () => { it('should validate email', () => { ... } })`). |
| **Test Order**            | **No implicit dependencies**: Run in parallel unless explicitly sequential.   | Prevents race conditions; use `test.order()` sparingly.                                         |
| **Data Fixtures**         | `/test/fixtures/{module}/`                                                 | Shared test data stored separately (e.g., `/test/fixtures/users.json`).                        |
| **Mocks/Stubs**           | Named files: `{module}-mock.[js|py]` or inline with `jest.mock()`/`pytest-mock`. | Mocks isolate dependencies (e.g., `userRepoMock = require('./userRepo-mock')`).               |
| **Test Metadata**         | Comments or pre-test hooks (e.g., `@tag:slow` in pytest).                  | Categorize tests for filtering (e.g., `@tag:integration`).                                      |
| **Configuration**         | Shared config in `/test/config/{env}.json` (e.g., `/test/config/dev.json`).   | Environment-specific settings (e.g., API endpoints).                                            |
| **Snapshots**             | `.snapshot` files (e.g., `__mocks__/user.snapshot.json`).                   | Store expected outputs for non-regression checks.                                               |
| **Error Handling**        | `it.shouldReject()` or `expect(() => { ... }).toThrow()`.                   | Explicit test for failure cases.                                                                |
| **Async/Await**           | Always handle async with `.resolves`/`.rejects` or `await`.                  | Avoid callback hell; use `done()` only for legacy test runners.                                  |
| **Performance Tests**     | Prefix with `benchmark-` (e.g., `benchmark-route-performance.test.js`).     | Isolate slow tests; exclude from default runs with `@tag:benchmark`.                           |

---

## **Query Examples**
### **1. Finding Tests by Module**
**Command** (CLI Agnostic):
```bash
# Glob pattern to list all tests for 'auth' module
find ./test -type f -name '*auth*.test.*'
```
**Output**:
```
/test/auth-service/login.test.js
/test/auth-service/token.test.ts
```

### **2. Running Feature-Specific Tests**
**Jest**:
```bash
# Run all tests for the 'user' feature across modules
npx jest --findRelatedTests user
```
**Pytest**:
```bash
# Filter tests with 'user' in the filename
pytest -k "user" --collect-only
```

### **3. Parallel Test Execution**
**Jest**:
```bash
# Run tests in parallel with chunking
npx jest --runInBand=false --maxWorkers=4 --testWorkers=2
```
**Pytest**:
```bash
# Distribute tests across processes
pytest -n 4 --dist=loadfile
```

### **4. Filtering Slow Tests**
**Jest**:
```bash
# Exclude benchmark tests
npx jest --testPathIgnorePatterns="/benchmark-"
```
**Pytest**:
```bash
# Run only tagged tests
pytest -m "not benchmark"
```

### **5. Generating Test Coverage**
**Istanbul (via Jest)**:
```bash
# Generate HTML coverage report
npx jest --coverage --coverageReporters=html
```
**Output**:
```
Coverage report generated in: coverage/lcov-report/index.html
```

### **6. Dynamic Test Generation**
**Jest** (with `jest-dynamic-title`):
```javascript
// Dynamic test titles based on input data
const users = ['alice', 'bob'];
users.forEach(user => {
  it(`should greet ${user}`, () => {
    // ...
  });
});
```
**Output**:
```
PASS  ./greet.test.js
  ✓ should greet alice (3ms)
  ✓ should greet bob (1ms)
```

---

## **Implementation Details**
### **1. Directory Structure**
```
project-root/
├── src/
│   ├── modules/
│   │   ├── auth/
│   │   │   ├── service.js
│   │   │   └── __tests__/
│   │   │       ├── login.test.js
│   │   │       └── token.test.ts
│   │   └── user/
│   │       ├── model.js
│   │       └── __tests__/
│   │           └── validation.test.js
├── test/
│   ├── fixtures/
│   │   ├── users.json
│   │   └── roles.json
│   ├── __mocks__/
│   │   └── userRepo-mock.js
│   └── config/
│       ├── dev.json
│       └── prod.json
```

### **2. Test Naming Conventions**
| **Pattern**               | **Example**                                      | **Avoid**                              |
|---------------------------|--------------------------------------------------|----------------------------------------|
| **Verify behavior**       | `it('should validate email')`                   | `it('tests email validation')`         |
| **Edge cases**            | `it('should reject empty name')`                | `it('tests name validation failure')`  |
| **State transitions**     | `it('should transition to "active"')`           | `it('tests user state change')`        |
| **Mock interactions**     | `it('should call getUser() once')`               | `it('tests mock calls')`               |

### **3. Handling Dependencies**
- **Explicit Mocks**: Prefix mocks with `mock-` in filenames (e.g., `authService-mock.js`).
- **Dependency Injection**: Pass mocks via constructor or test setup:
  ```javascript
  // Example: Injecting a mock database
  const { UserService } = require('../src/modules/user/service');
  const mockDb = require('./userRepo-mock');

  test('findUser', () => {
    const service = new UserService(mockDb);
    // ...
  });
  ```
- **Environment Variables**: Use `.env.test` for test-specific configs:
  ```env
  # .env.test
  API_BASE_URL=http://test.api.local
  ```

### **4. Test Data Versioning**
- **Snapshot Tests**: Update snapshots incrementally:
  ```javascript
  // Update snapshot (Jest)
  npx jest --updateSnapshot
  ```
- **Fixture Versioning**: Add timestamps or versions to fixtures:
  ```
  /test/fixtures/users-v1.json
  /test/fixtures/users-v2.json
  ```

### **5. Async Test Strategies**
| **Scenario**               | **Approach**                                                                 |
|---------------------------|-----------------------------------------------------------------------------|
| **Promises**               | Use `.resolves.toEqual()` or `await`.                                      |
| **SetTimeout**             | Mock `setTimeout` or use `jest.useFakeTimers()`.                           |
| **Timeouts**               | Set test timeout globally (`jest.setTimeout(10000)`) or per-test (`timeout: 5000`). |
| **Event Emitters**         | Use `testEventEmitter` libraries or manual listeners with cleanup.         |

### **6. Performance Optimization**
- **Skip Redundant Tests**: Use `@tag:unit` to exclude integration tests from CI:
  ```javascript
  // pytest.ini
  [pytest]
  markers =
      unit: mark test as unit test
  ```
- **Cache Fixtures**: Reuse fixtures across tests (e.g., pytest’s `cache` fixture).
- **Parallelize Independent Tests**: Group tests by file/module to minimize overhead.

### **7. Error Handling**
- **Assertions**: Prefer chained assertions for clarity:
  ```javascript
  // Bad
  expect(user).toBeDefined();
  expect(user.name).toBe('Alice');

  // Good
  expect(user).toBeDefined().toHaveProperty('name', 'Alice');
  ```
- **Custom Matchers**: Extend Jest/Pytest with custom matchers:
  ```javascript
  // jest-extended
  expect(response).toBeUserError('Invalid token');
  ```

### **8. Local vs. CI Environments**
| **Config**                 | **Local**                          | **CI**                              |
|---------------------------|------------------------------------|-------------------------------------|
| **Timeouts**               | Default (e.g., 5s)                  | Higher (e.g., 30s)                   |
| **Parallel Jobs**          | Limited (e.g., 2 workers)           | Max parallelism (e.g., 8 workers)   |
| **Debug Mode**             | `DEBUG=true` (verbose logs)         | Disabled (`DEBUG=false`)             |
| **Mock Behavior**          | Partial mocks allowed              | Strict mocks enforced               |

---
## **Query Examples (Advanced)**
### **1. Generating Test Reports**
**Allure Framework** (with Jest):
```bash
# Run tests and generate Allure report
npx jest --runInBand --reporters=allure-jest
npx allure generate --clean
```
**Output**:
```
Report generated at: allure-report/index.html
```

### **2. Dynamic Test Generation from API Specs**
**OpenAPI/Swagger**:
```bash
# Generate tests from OpenAPI spec using tools like json-schema-to-test
npx json-schema-to-test openapi.yml --out ./test/api/
```
**Example Output**:
```
test/api/
├── get-users.test.js
└── post-user.test.js
```

### **3. Cross-Browser Testing**
**Selenium WebDriver**:
```javascript
// Example test for multiple browsers
const browsers = ['chrome', 'firefox', 'edge'];
browsers.forEach(browser => {
  it(`should work in ${browser}`, async () => {
    const driver = await browserDriver(browser);
    // ...
  });
});
```

### **4. Mutability Testing**
**Detect Side Effects**:
```javascript
// Use libraries like `jest-mutator` to detect unintended mutations
const originalConsoleLog = console.log;
beforeEach(() => {
  console.log = jest.fn();
});

afterEach(() => {
  console.log.mockRestore();
});
```

### **5. Test Coverage Gaps**
**Identify Uncovered Code**:
```bash
# Generate a list of uncovered functions
npx istanbul report lcov --print "summary" | grep "Lines:  100.0"
```
**Output**:
```
Coverage summary:
Lines:   100.0% (0/0)
Statements: 100.0% (0/0)
Functions: 100.0% (0/0)
Branches: 100.0% (0/0)
```

---
## **Related Patterns**
1. **[Unit Testing](https://example.com/unit-testing)**
   - Focuses on individual functions/classes; Testing Conventions define how units are tested.

2. **[Mocking and Stubs](https://example.com/mocking-patterns)**
   - Provides strategies for isolating dependencies in tests (e.g., `jest.mock()`, `unittest.mock`).

3. **[Test Pyramid](https://example.com/test-pyramid)**
   - Recommends a ratio of unit:integration:end-to-end tests (Testing Conventions help enforce this ratio).

4. **[Fixture Management](https://example.com/fixture-pattern)**
   - Centralizes test data generation and versioning (complements Testing Conventions’ `/test/fixtures/`).

5. **[CI/CD Integration](https://example.com/ci-cd-patterns)**
   - Ensures tests run in pipelines (Testing Conventions ensure test names/files are discoverable).

6. **[Behavior-Driven Development (BDD)](https://example.com/bdd-patterns)**
   - Uses Gherkin syntax (`Given-When-Then`) for test descriptions (Testing Conventions can map to BDD steps).

7. **[Test Data Builder](https://example.com/test-data-builder)**
   - Generates test data programmatically (reduces boilerplate in tests using Testing Conventions).

8. **[Test Containers](https://example.com/test-containers)**
   - Spins up ephemeral services (e.g., databases) for integration tests (Testing Conventions define where these tests live).

---
## **Anti-Patterns to Avoid**
1. **Overly Nested Describes**:
   ```javascript
   // Anti-pattern: Deeply nested describes reduce readability
   describe('AuthService', () => {
     describe('Login', () => {
       describe('Happy Path', () => {
         it('should work', () => { ... });
       });
     });
   });
   ```
   **Fix**: Flatten or use `# of context`:
   ```javascript
   describe('AuthService.login', () => {
     it('should succeed with valid credentials', () => { ... });
   });
   ```

2. **Shared State Between Tests**:
   ```javascript
   // Anti-pattern: Tests interfere with each other
   let user;
   beforeEach(() => {
     user = db.createUser(); // State carries over!
   });
   ```
   **Fix**: Reset state or use fresh fixtures per test.

3. **Testing Implementation Details**:
   ```javascript
   // Anti-pattern: Tests internal methods
   it('should check array length', () => {
     expect(_internalHelper.length).toBe(5); // Breaks when refactored
   });
   ```
   **Fix**: Test public APIs and behaviors.

4. **Ignoring Flaky Tests**:
   ```javascript
   // Anti-pattern: Silent flakes
   it('should fetch data', async () => {
     await api.getData(); // Fails intermittently
   }, 10000); // High timeout hides root cause
   ```
   **Fix**: Debug and fix flakiness; use `@tag:flaky` to track.

5. **Hardcoded Values in Tests**:
   ```javascript
   // Anti-pattern: Magic strings
   it('should use correct API key', () => {
     expect(apiKey).toBe('abc123'); // Key changes untested
   });
   ```
   **Fix**: Inject keys via config or environment variables.

6. **Missing Test Metadata**:
   ```javascript
   // Anti-pattern: No tags or descriptions
   it('users');
   ```
   **Fix**: Always include clear intent:
   ```javascript
   it('should return sorted users by date', () => { ... });
   ```

7. **Overusing Test Doubles**:
   ```javascript
   // Anti-pattern: Heavy mocking
   const mockDb = {
     find: jest.fn().mockReturnValue({ id: 1 }),
     save: jest.fn()
   };
   ```
   **Fix**: Use spies or minimal mocks; favor real implementations when possible.

---
## **Tools and Libraries**
| **Tool**               | **Purpose**                                                                 | **Example Use Case**                                  |
|------------------------|-----------------------------------------------------------------------------|------------------------------------------------------|
| **Jest**               | Unit/integration testing framework.                                         | Default in JavaScript/TypeScript projects.            |
| **Pytest**             | Python testing framework with plugins.                                      | Python projects with rich plugins (e.g., `pytest-html`).|
| **Mocha**              | BDD-style test runner (Node.js).                                           | Legacy Node.js projects.                              |
| **Jest-Mock**          | Extend Jest’s mocking capabilities.                                          | Custom mock factories.                                |
| **Unittest (Python)**  | Built-in Python testing framework.                                           | Simple, lightweight tests.                           |
| **Allure Framework**   | Test reporting for multiple languages.                                       | Cross-platform test dashboards.                       |
| **Selenium**           | Browser automation for integration tests.                                   | UI/end-to-end tests.                                  |
| **Testcontainers**     | Spin up containers for integration tests.                                  | PostgreSQL, Redis in tests.                           |
| **JSON Schema to Test**| Generate tests from OpenAPI/Swagger specs.                                  | API contract tests.                                   |
| **Jest Extended**      | Custom matchers for Jest.                                                   | `toBeUserError()`, `toMatchSnapshot()`.                |
| **Factory Boy**        | Test data generation (Python).                                             | Rapid fixture creation.                               |
| **Faker**              | Fake data generation (JS/Python).                                           | Generate test users.                                  |
| **Istanbul**           | Code coverage reporting.                                                     | Ensure 100% statement coverage.                        |
| **Cypress**            | End-to-end testing with built-in assertions.                                | UI workflow testing.                                  |
| **Postman/Newman**     | API test automation.                                                        | CI/CD API test runs.                                  |

---
## **Versioning Tests**
### **Backward Compatibility**
- **Breaking Changes**:
  - Update test filenames/modules if logic moves (e.g., `auth-service` → `auth/core`).
  - Increment fixture versions (e.g., `users-v2.json`).
  - Add deprecation warnings in test comments:
    ```javascript
    // WARNING: This test will be removed in v2.0. Use `authService.login()` instead.
    ```

### **Test Deprecation Policy**
| **Action**               | **Signal**                                                                 | **Timeline**                     |
|--------------------------|--------------------------------------------------------------------------|-----------------------------------|
| **Deprecated**           | Prefix with `legacy/` in filename (e.g., `/test/legacy/auth.test.js`).    | Remove in next major version.    |
| **