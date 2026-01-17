# **[Development Pattern] Mocking & Stubbing in Tests – Reference Guide**

---

## **1. Overview**
**Mocking & Stubbing in Tests** is a unit-testing technique used to isolate components by replacing dependencies (e.g., external services, databases, or other modules) with controlled, simulated alternatives. This ensures tests remain deterministic, reproducible, and focused on the code’s behavior rather than its external interactions.

Mocks simulate **behavior** (e.g., returning predefined responses) while stubs provide **fixed responses** without enforcing interaction rules. The pattern enhances test reliability by avoiding flaky tests due to external factors like network latency or database state.

---

## **2. Key Concepts & Implementation**

### **2.1 Core Terms**
| Term          | Definition                                                                 | When to Use                                                                 |
|---------------|-----------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **Mock**      | A simulated dependency with predefined answers to method calls; enforces expected interactions. | When testing relies on validating *how* a dependency is used (e.g., calling `.save()`). |
| **Stub**      | A simplified dependency that returns fixed responses; no interaction checks. | When testing only needs *reliable* inputs/outputs (e.g., API responses).     |
| **Spy**       | A mock that records actual calls made (combines mock + spy functionality). | Debugging or auditing interactions (e.g., "Was `.login()` called with correct params?"). |
| **Fake**      | A simplified implementation of a dependency (e.g., in-memory database).   | Avoiding mock/stub complexity for lightweight alternatives.                 |

---

### **2.2 When to Use**
✅ **Unit Tests**:
- Isolate a single class/method by replacing dependencies.
- Example: Test a `PaymentService` without calling a real payment gateway.

❌ **Avoid When**:
- Tests become overly complex (e.g., mocking 10+ methods).
- Integration scenarios require real dependencies (use integration tests instead).

---

### **2.3 Implementation Workflow**
1. **Identify Dependencies**
   List the external services, databases, or other classes interacted with.

2. **Choose Mock/Stub/Spy**
   - Use **stubs** for predictable inputs (e.g., mocking HTTP responses).
   - Use **mocks** to enforce expected interactions (e.g., verifying a database query is called).

3. **Implement the Test**
   - **Setup**: Replace dependencies with mocks/stubs.
   - **Execute**: Trigger the code under test.
   - **Verify**: Assert expected behavior (e.g., method calls, returned values).

4. **Clean Up**
   Reset mocks/stubs to avoid test pollution (e.g., `.reset()` in libraries like Jest/Mockito).

---

### **2.4 Tools & Libraries**
| Language/Framework | Tool                     | Key Features                                                                 |
|--------------------|--------------------------|------------------------------------------------------------------------------|
| JavaScript/TypeScript | Jest                     | `.mockImplementation()` (mocks), `.mockReturnValue()` (stubs).               |
| Java                | Mockito                  | `@Mock`, `@Spy`, `verify()`, `when().thenReturn()`.                           |
| Python              | `unittest.mock`          | `Mock()`, `patch()`, `Mock.return_value`.                                    |
| C#                  | Moq                      | `Mock<T>.Setup()`, `Verify()`, `It.IsAny<T>`.                               |
| Ruby                | RSpec + `double`         | `allow(call).to receive(:method).and_return(value)`.                        |

---

## **3. Schema Reference**
### **Mock/Stub Structure**
| Field            | Description                                                                 | Example                                                                     |
|------------------|-----------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Dependency**   | The external class/service being replaced.                                 | `PaymentGateway`                                                           |
| **Type**         | Mock/Stub/Spy/Fake.                                                        | `Stub`                                                                        |
| **Method**       | The method to override (e.g., `.process()`).                              | `mockPaymentGateway.process()`                                              |
| **Return Value** | Fixed response (for stubs) or dynamic logic (for mocks).                   | `.mockReturnValue("success")` or `.mockImplementation(() => { ... })`     |
| **Interaction**  | Expected calls (for mocks only; e.g., `.verify()`).                       | `verify(mockGateway, times(1)).process(any())`                              |
| **Reset**        | Whether the mock/stub resets between tests.                                | `afterEach(() => mockReset(mockGateway))`                                   |

---
### **Example: Mocking an HTTP Client**
```plaintext
Dependency: AxiosHTTPClient
Type: Mock
Method: .get("/api/users")
Return Value: { stubbedData: "unittest" }
Interaction: Calls `.get()` with URL containing "users"
Reset: Yes (between tests)
```

---

## **4. Query Examples (Pseudocode)**
### **4.1 Stubbing a Database Query**
**Goal**: Return hardcoded user data for a `UserRepository` test.

```javascript
// Setup (Stubs the query)
const mockUserRepo = {
  findById: () => Promise.resolve({ id: 1, name: "Test User" })
};

// Test
await userService.getUser(1).then(user => {
  expect(user.name).toBe("Test User");
});
```

### **4.2 Mocking an API Call**
**Goal**: Verify a `PaymentService` calls the gateway with correct params.

```java
// Setup (Mock)
PaymentGateway gateway = mock(PaymentGateway.class);

// Test
paymentService.processPayment(100, "user123");
verify(gateway).charge(eq(100), eq("user123"), any(PaymentMethod.class));
```

### **4.3 Spying on a Method**
**Goal**: Confirm `OrderService` logs errors to a spy logger.

```python
spy_logger = unittest.mock.MagicMock()
orderService.log = spy_logger

orderService.processOrder(fail=True)  # Triggers error logging
spy_logger.info.assert_called_with("Order failed!")
```

---

## **5. Common Pitfalls & Solutions**
| Pitfall                          | Solution                                                                 |
|----------------------------------|--------------------------------------------------------------------------|
| **Over-mocking**                 | Limit mocks to essential dependencies; use fakes where possible.          |
| **Test Pollution**               | Reset mocks/stubs after each test (e.g., `afterEach` in Jest).           |
| **Ignoring Side Effects**        | Use mocks to enforce interactions (e.g., verify database calls).         |
| **Unrealistic Test Data**        | Combine stubs with dynamic logic (e.g., mock responses based on inputs). |
| **Circular Dependencies**        | Refactor to reduce dependencies between tested units.                     |

---

## **6. Related Patterns**
| Pattern                          | Description                                                                 | Use Case Example                                                              |
|----------------------------------|-----------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **Dependency Injection**         | Decouple dependencies via interfaces/containers (e.g., Spring, DIY injectors). | Replace real `Database` with a `MockDatabase` in tests.                      |
| **Integration Testing**          | Test interactions between components (e.g., service + database).            | Verify `PaymentService` works with a test database, not a mock.              |
| **Test Doubles**                 | General term for mocks, stubs, fakes, and spies.                            | Use `FakeAuthService` for lightweight testing.                                |
| **Behavior-Driven Development**  | Define tests as scenarios (e.g., Gherkin).                                  | "Given user logs in, when payment fails, then show error."                   |
| **Property-Based Testing**       | Generate test inputs (e.g., Hypothesis, QuickCheck).                       | Test `PaymentService` with random amounts/IDs to catch edge cases.            |

---

## **7. Best Practices**
1. **Minimize Mocks**: Prefer stubs for simple replacements; mocks only for interaction verification.
2. **Descriptive Names**: Use clear variable names (e.g., `mockUserService` instead of `m`).
3. **Isolate Tests**: Each test should reset its own mocks/stubs.
4. **Document Assumptions**: Comment why a dependency is mocked (e.g., "Mocking `EmailService` to avoid real sends").
5. **Avoid Production Code Logic**: Keep mock logic in tests; never leak into actual implementations.

---
**Example of a Poor Test** (over-mocked):
```python
@mock.patch('requests.get')
@mock.patch('database.query')
def test_user_flow(mock_db, mock_request):
    # Complex setup mixing stubs/mocks...
    # Hard to read, fragile to changes.
```

**Refactored**:
```python
# Stub only the critical HTTP call
def test_user_flow():
    mock_response = MagicMock(); mock_response.json.return_value = {"id": 1}
    with patch('api_client.get', return_value=mock_response):
        user = userService.fetchUser(1)
        assert user.id == 1
```

---
**Key Takeaway**: Mocking/Stubbing should simplify tests, not complicate them. Focus on isolating the unit under test while keeping the approach maintainable.