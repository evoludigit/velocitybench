# **Debugging *Mocking & Stubbing in Tests*: A Troubleshooting Guide**

---

## **Introduction**
Mocking and stubbing are essential techniques for isolating dependencies in unit tests, ensuring deterministic behavior and reducing flakiness. However, poorly implemented mocks can lead to slow tests, unreliable behavior, and hard-to-debug issues.

This guide provides a structured approach to diagnosing and resolving common problems with mocking and stubbing in tests.

---

## **1. Symptom Checklist**
Check these signs when tests exhibit mocking/stubbing-related issues:

✅ **Tests are slow** (e.g., long setup/teardown times, excessive mocking logic)
✅ **Tests fail intermittently** (unexpected real dependencies being called)
✅ **Mocks return incorrect data** (wrong state or null/undefined responses)
✅ **Overly complex mocks** (boilerplate, hard-to-maintain stubs)
✅ **Real dependencies are still being hit** (mocks not properly intercepting calls)
✅ **"Mocked" objects behave unexpectedly** (side effects, incorrect sequencing)
✅ **Tests pass locally but fail in CI/CD** (environment-specific mocking issues)

---

## **2. Common Issues and Fixes**

### **Issue 1: Real Dependencies Still Being Called**
**Symptoms:**
- Tests fail with `ConnectionRefused`, `NullPointerException`, or unexpected API responses.
- Mocks are ignored because they aren’t properly configured.

**Root Cause:**
- Mocks/stubs not injected correctly.
- Test isolation not enforced (e.g., shared state between tests).

**Fix:**
Use **dependency injection** and **strict mocking frameworks** (e.g., Mockito’s `@Mock`, `@InjectMocks`).

**Example (Java with Mockito):**
```java
@Test
public void testService_CallsRepository_Correctly() {
    // Arrange
    Repository mockRepo = mock(Repository.class);
    when(mockRepo.getUser(anyInt())).thenReturn(new User("TestUser"));

    Service service = new Service(mockRepo); // Inject mock via constructor

    // Act & Assert
    User result = service.fetchUser(1);
    assertEquals("TestUser", result.getName());
    verify(mockRepo, times(1)).getUser(1); // Ensure mock was used
}
```

**Key Fixes:**
- **Mock everything that can vary** (configuration, external APIs, databases).
- **Use `@Mock` for dependencies** and **`@InjectMocks`** for classes under test.

---

### **Issue 2: Mocks Returning Wrong/Null Data**
**Symptoms:**
- Tests fail with `NullPointerException` or incorrect assertions.
- Stubbed methods return unexpected values.

**Root Cause:**
- Missing or incorrect stubbing.
- Mocks not initialized before use.

**Fix:**
Ensure proper stubbing with **exact matchers** (e.g., `any()`, `eq()`).

**Example (JavaScript with Jest):**
```javascript
test("mocked API returns correct response", async () => {
  const mockApi = {
    fetchUser: jest.fn().mockResolvedValue({ id: 1, name: "Test" }),
  };

  const service = new UserService(mockApi);
  const user = await service.getUser(1);

  expect(user.name).toBe("Test");
  expect(mockApi.fetchUser).toHaveBeenCalledWith(1); // Verify call
});
```

**Key Fixes:**
- **Explicitly stub all possible return values** (avoid `undefined` defaults).
- **Use mock assertions** (`toHaveBeenCalledWith`) to verify correct usage.

---

### **Issue 3: Tests Are Too Slow Due to Over-Mocking**
**Symptoms:**
- Test suite runs slowly due to complex mock setups.
- Mocks introduce unnecessary boilerplate.

**Root Cause:**
- Overuse of mocks (e.g., mocking simple in-memory data).
- Recursive mocking (nested dependencies).

**Fix:**
- **Prefer real dependencies for simple cases** (e.g., in-memory collections).
- **Use partial mocks** (e.g., `Spy` instead of full mocks when only a few methods need isolation).

**Example (TypeScript with Sinon):**
```typescript
test("fast in-memory lookup", () => {
  const users = [{ id: 1, name: "Alice" }]; // No mock needed
  const userService = new UserService(users);

  const user = userService.findById(1);
  expect(user.name).toBe("Alice");
});
```

**Key Fixes:**
- **Mock only external dependencies** (APIs, DBs, files).
- **Reduce test scope** (e.g., integration tests for slow cases).

---

### **Issue 4: Mocks Introduce Hidden Side Effects**
**Symptoms:**
- Tests pass, but production fails due to **unintended mock calls**.
- Unexpected state changes in mocked objects.

**Root Cause:**
- Mocks with **stateful behavior** (e.g., incrementing counters).
- **Partial mocks** with side effects.

**Fix:**
- **Use static mocks** (return fixed values).
- **Verify no unintended calls** with `verifyNoMoreInteractions()`.

**Example (Python with unittest.mock):**
```python
def test_service_avoids_unintended_calls():
    mock_db = MagicMock()
    service = Service(mock_db)

    service.process()
    mock_db.save.assert_not_called()  # Ensure no extra calls
```

**Key Fixes:**
- **Avoid stateful mocks** (e.g., don’t modify internal state in stubs).
- **Use `never()` assertions** to catch unused mocks.

---

### **Issue 5: Mocks Fail in CI/CD But Work Locally**
**Symptoms:**
- Tests pass locally but fail in CI (e.g., `ClassNotFoundException`).
- Mocks rely on environment-specific setup.

**Root Cause:**
- Mocks depend on **external files/configs** not present in CI.
- **Hardcoded paths** in test setups.

**Fix:**
- **Isolate mocks fully** (no file/DB dependencies).
- **Use test containers** for DB/API mocks in CI.

**Example (Dockerized DB Mock):**
```bash
# CI setup (Testcontainers)
docker run -d --name test-db postgres
# Initialize mock DB in test setup
```

**Key Fixes:**
- **Never rely on local files** in tests.
- **Use test doubles** (e.g., `Testcontainers`) for synchronous mocking.

---

### **Issue 6: Tests Are Hard to Maintain Due to Overly Complex Mocks**
**Symptoms:**
- Mocks are **100+ lines** with deep nesting.
- Changes break multiple tests.

**Root Cause:**
- **Deeply nested mock hierarchies**.
- **Mocks as part of the test logic** (not isolated).

**Fix:**
- **Flatten mocks into separate test classes**.
- **Use factories** for complex mock setup.

**Example (Python with `factory_boy`):**
```python
from factory import Factory

class UserFactory(Factory):
    class Meta:
        model = User
        django_get_or_create = ('email',)

    email = Faker('email')
    password = 'testpass123'

# In test:
user = UserFactory()
```

**Key Fixes:**
- **Centralize mocks in a `MockData` class**.
- **Use generators/lambdas** for dynamic mock data.

---

## **3. Debugging Tools and Techniques**

### **A. Mock Verification Tools**
| Tool/Library | Purpose |
|--------------|---------|
| **Mockito (`verify()`)** | Ensures mocks were called correctly. |
| **Jest (`toHaveBeenCalledWith`)** | Tracks mock interactions. |
| **Python `unittest.mock` (`assert_called_once`)** | Debugs mock calls. |
| **TypeScript `Sinon` (`spy.andCallThrough`)** | Debugs partial mocks. |

**Example (Debugging Unintended Calls with Mockito):**
```java
@Test
public void test_mock_debug_example() {
    Repository mockRepo = mock(Repository.class);
    Service service = new Service(mockRepo);

    service.doSomething(); // Should NOT call repo

    verify(mockRepo, never()).saveAnything(); // Fails if called
}
```

### **B. Logging & Tracing**
- **Enable debug logs** for mocks:
  ```python
  mock_db = MagicMock()
  mock_db.save = MagicMock(side_effect=lambda *args: print(f"Mock save called: {args}"))
  ```
- **Use `console.log` in JS mocks** to trace calls:
  ```javascript
  jest.spyOn(api, 'fetch').mockImplementation(() => console.log("API called!"));
  ```

### **C. Static Analysis Tools**
| Tool | Purpose |
|------|---------|
| **SonarQube** | Detects overly complex mocks. |
| **ESLint Plugin (jest-dom)** | Ensures mocks are used properly. |
| **Pylint (Python)** | Flags unused mocks. |

**Example (ESLint Rule for Mock Usage):**
```javascript
// Ensure mocks are verified
jest-dom.expect(mockApi.fetch).toHaveBeenCalled();
```

### **D. Test Coverage Analysis**
- **Check if mocks are overused:**
  - High **mock-only coverage** → Likely integration tests needed.
  - **No mock coverage** → Tests are flaky.
- **Tools:**
  - **Jest Coverage** (`--coverage`)
  - **Pytest Coverage**
  - **JaCoCo (Java)**

**Example (JaCoCo Report):**
```bash
mvn test jacoco:report
# Look for 100% mock coverage (if too high, refactor)
```

---

## **4. Prevention Strategies**

### **A. Follow the Mocking Religion**
- **One Rule Mocking:** Only mock **external dependencies** (APIs, DBs, files).
- **No Mocking:** Avoid mocking simple in-memory logic.

### **B. Use Test Double Patterns**
| Pattern | When to Use |
|---------|-------------|
| **Mock** | Mocking interfaces for strict verification. |
| **Stub** | Predefined return values for simple cases. |
| **Spy** | Partial mocking for verification. |
| **Fake** | Lightweight in-memory implementations (e.g., `InMemoryDB`). |

### **C. Test Data Management**
- **Use factories** for consistent test data:
  ```python
  # Instead of:
  mock_user = {"id": 1, "name": "Alice"}

  # Use:
  mock_user = UserFactory()
  ```
- **Mock responses in a `fixtures` directory** (JSON/YAML).

### **D. Automate Mock Setup**
- **Extract mocks into a `TestUtils` class**:
  ```java
  public class MockRepoUtils {
      public static Repository createMockRepo() {
          Repository mock = mock(Repository.class);
          when(mock.findById(anyInt())).thenReturn(new User(1, "Alice"));
          return mock;
      }
  }
  ```

### **E. Test Isolation Rules**
1. **No shared state** between tests (use `@BeforeEach`/`@AfterEach`).
2. **Reset mocks after each test** (Jest’s `beforeEach` or Mockito’s `@Before`).
3. **Use `@DirtiesContext` (Spring) to reset test state**.

**Example (Spring `@DirtiesContext`):**
```java
@DirtiesContext(methodMode = DirtiesContext.MethodMode.AFTER_EACH_TEST_METHOD)
@Test
public void testWithCleanState() {
    // Mocks are reset here
}
```

### **F. Performance Optimization**
- **Cache expensive mocks** (e.g., `MockitoAnnotations.initMocks()`).
- **Use `spy()` instead of full mocks** when possible.
- **Parallelize tests** (CI tools like GitHub Actions, GitLab CI).

**Example (Parallel Jest):**
```json
// package.json
"test": "jest --runInBand"  // Sequential
"test:parallel": "jest --maxWorkers=4"  // Faster
```

---

## **5. When to Use What**
| Scenario | Recommended Approach |
|----------|----------------------|
| **Unit Tests (Fast, Isolated)** | Full mocking (Mockito, Jest) |
| **Integration Tests (Real DB/API)** | Fakes/Testcontainers |
| **E2E Tests (Full Stack)** | No mocks, real dependencies |
| **Slow Tests (DB/API Calls)** | Testcontainers + caching |
| **Complex Mock Logic** | Mock factories + spies |

---

## **6. Final Checklist Before Debugging**
✔ Are **all external dependencies mocked**?
✔ Do **mocks return predictable data**?
✔ Are **tests isolated** (no shared state)?
✔ Are **mocks verified** (`verify()`, `toHaveBeenCalled`)?
✔ Are **tests fast** (no over-mocking)?
✔ Do **mocks fail in CI**? (Check environment setup).

---

## **Conclusion**
Mocking and stubbing should **isolate tests from variability**, not **introduce new complexity**. By following this guide:
- **Diagnose** issues with slow, flaky, or hard-to-maintain tests.
- **Fix** problems with proper mocking techniques.
- **Prevent** regressions with automation and isolation.

**Key Takeaway:**
*"Mock only what you must, verify what you mock, and kill tests that are too slow."*

---
**Further Reading:**
- [Mockito User Guide](https://site.mockito.org/)
- [Jest Mocking Docs](https://jestjs.io/docs/mock-functions)
- [Testcontainers for DB Mocking](https://www.testcontainers.org/)