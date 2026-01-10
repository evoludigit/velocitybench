# **[Pattern] Integration Testing Patterns – Reference Guide**
*Best practices and implementation details for validating component interactions in your software system.*

---

## **Overview**
Integration tests bridge the gap between **unit tests** (isolated) and **end-to-end (E2E) tests** (full system), ensuring components interact as expected. They simulate real-world dependencies (e.g., databases, services, APIs) to expose integration flaws, data inconsistencies, or synchronization issues that unit tests miss.

Unlike unit tests, which mock dependencies, integration tests use **real or stubbed live systems**, requiring careful setup to avoid flakiness and overhead. This pattern helps:
- Catch **cross-component bugs** early (e.g., API payload mismatches, transaction errors).
- Validate **data consistency** across services (e.g., caching layers, event queues).
- Ensure **system-wide behavior** aligns with requirements.

---

## **Schema Reference**
A **standardized structure** for integration tests improves maintainability. Below are key elements, configurable per project.

| **Field**               | **Description**                                                                 | **Example Value**                          | **Required?** |
|-------------------------|-------------------------------------------------------------------------------|--------------------------------------------|----------------|
| `testName`              | Descriptive name of the test case (e.g., `UserSubscriptionService_UpdateCart`). | `"OrderService_ProcessPayment_Failure"`    | ✅ Yes          |
| `components`            | List of **real components** involved (avoid mocks unless necessary).           | `["PaymentGateway", "OrderDB"]`             | ✅ Yes          |
| `dependencies`          | External systems needed (e.g., databases, APIs). Specify **setup/teardown**.   | `{"db": "PostgreSQL:9.6", "api": "AuthService"}` | ⚠️ Conditional |
| `testType`              | **Category** of integration test (see *Test Types* below).                     | `"Service-to-Service", "Database"`         | ✅ Yes          |
| `dataSetup`             | Initial state (e.g., seed data, environment variables).                       | `{"users": [{"id": "1", "email": "test@example.com"}]}` | ⚠️ Conditional |
| `assertions`            | Expected outcomes (e.g., side effects, responses).                            | `{"status": "200", "paymentId": "valid"}`  | ✅ Yes          |
| `flakinessMitigation`   | Strategies to reduce unreliable tests (e.g., retries, timeouts).               | `{"retries": 3, "timeout": "30s"}`         | ⚠️ Recommended |
| `cleanup`               | Actions to reset state (e.g., delete temp data, rollback transactions).       | `{"dropTables": ["temp_orders"]}`           | ⚠️ Conditional |

---

### **Test Types**
| **Type**                          | **Scope**                                  | **Example Use Case**                          |
|-----------------------------------|--------------------------------------------|-----------------------------------------------|
| **Service-to-Service**            | Interactions between microservices.         | OrderService → PaymentService → EmailService. |
| **Database**                      | Data consistency across tables/layers.     | Verify `user_id` matches across `users` and `orders`. |
| **API Gateway**                   | Integration with external APIs.            | Validate auth token forwarding to `Stripe`.   |
| **Event-Driven**                  | Queue/message broker consumption.          | Kafka consumer → Process event → Update DB.   |
| **Hybrid (Unit + Integration)**   | Partial integration (e.g., mocked DB).     | Test `ServiceA` with a **stubbed** `ServiceB`. |

---

## **Implementation Details**

### **1. Dependency Management**
#### **Real Dependencies (Production-like)**
- **Pros**: High confidence, catches real issues.
- **Cons**: Slow, fragile (network/database outages).
- **Best Practices**:
  - Use **test databases** (e.g., Dockerized Postgres) with **schema migration tools** (Flyway/Liquibase).
  - **Isolate test environments** (e.g., separate cluster for test suites).
  - **Limit test duration** with timeouts (e.g., 10s for DB queries).

#### **Stubs/Mocks (Fake Dependencies)**
- **Pros**: Fast, predictable.
- **Cons**: May miss **real-world edge cases**.
- **When to Use**:
  - Expensive dependencies (e.g., third-party APIs).
  - Tests where **deterministic behavior** is critical (e.g., UI integration).
- **Tools**:
  - **Mock Servers**: WireMock, Postman Mock Server.
  - **In-Memory DBs**: H2, SQLite (for lightweight tests).

---

### **2. Test Scope & Granularity**
| **Granularity**          | **Description**                                                                 | **Example**                                      |
|--------------------------|-------------------------------------------------------------------------------|--------------------------------------------------|
| **Unit-adjacent**        | Test **one interaction** (e.g., `ServiceA` calls `ServiceB` once).            | `PaymentService_ValidateCard_WithMockAPI`.        |
| **Modular**              | Test a **small module** (e.g., `OrderController` + `OrderService`).           | `OrderFlow_PlaceOrder_WithRealDB`.               |
| **System-wide**          | Test **end-to-end flow** (e.g., checkout → payment → confirmation).            | `E2E_CheckoutWithPaymentGateway`.                |

**Guideline**: Prefer **smaller, modular tests** to isolate failures. Use E2E tests for **critical user journeys**.

---

### **3. Setup & Teardown**
#### **Common Patterns**
| **Pattern**               | **Use Case**                                      | **Implementation**                              |
|---------------------------|---------------------------------------------------|-------------------------------------------------|
| **Transaction Rollback**   | ACID compliance testing.                          | Wrap tests in a transaction; rollback after.    |
| **Clean Slate**           | Start with empty DB/messages.                     | Seed data **only before tests**; drop after.    |
| **Test Containers**       | Spin up real services (e.g., Redis, MongoDB).   | Use Docker + [Testcontainers](https://testcontainers.com/). |
| **Parallelization**       | Run tests concurrently (e.g., per service).      | Group tests by dependency (e.g., `OrderService` tests run together). |

**Example Workflow**:
```python
# Pseudocode for setup/teardown
def setup():
    db.seed("users", user_data)  # Populate test data
    api.start_mock("payment_gateway")  # Start stub

def teardown():
    db.drop_all_tables()  # Reset state
    api.stop()  # Cleanup stub
```

---

### **4. Flakiness Mitigation**
Flaky tests waste time and reduce confidence. Mitigate with:

| **Strategy**              | **Description**                                      | **Example**                                  |
|---------------------------|------------------------------------------------------|----------------------------------------------|
| **Retry Logic**           | Retry failed tests a limited number of times (e.g., 3). | `test.retry(max_retries=3, delay=5s)`.       |
| **Idempotent Operations** | Ensure retries don’t cause side effects.             | Use `PUT` instead of `POST` for updates.    |
| **Timeouts**              | Fail fast if dependencies hang.                     | `requests.get(url, timeout=5)`.              |
| **Deterministic Seeds**   | Use fixed random seeds for reproducible data.       | `random.seed(42)` for test data generation.  |
| **Isolation**             | Run tests in **separate environments**.             | Use Kubernetes namespaces for each test suite. |

---

### **5. Tooling & Frameworks**
| **Tool/Framework**        | **Purpose**                                      | **Languages**               |
|---------------------------|--------------------------------------------------|-----------------------------|
| **JUnit/Pytest**          | Test discovery and execution.                    | Java/Python                 |
| **Postman/Newman**        | API integration testing.                         | JavaScript, CLI             |
| **Cypress/TestCafe**      | Browser integration (frontend + backend).        | JavaScript                  |
| **K6/Locust**             | Load testing for integration points.             | JavaScript, Python          |
| **Selenium**              | UI + backend integration.                        | Java, Python, JavaScript    |
| **Testcontainers**        | Spin up real services (e.g., PostgreSQL).       | Java, Python, Go            |
| **Mock Server**           | Stub APIs/endpoints.                             | WireMock, Postman Mocks     |

---

## **Query Examples**
### **1. Service-to-Service Test (Python + Requests)**
```python
import requests

def test_order_service_pays_to_payment_gateway():
    # Setup: Create a test order
    order = {"user_id": 1, "amount": 100.00}
    response = requests.post("http://order-service/api/orders", json=order)
    assert response.status_code == 201

    # Assert: Payment gateway was called
    payment_resp = requests.get("http://payment-gateway/api/transactions/1")
    assert payment_resp.json()["status"] == "completed"
```

### **2. Database Integration Test (Java + JUnit)**
```java
@Test
void userSubscription_shouldUpdateCart() {
    // Setup: Insert test data
    User user = new User("test@example.com");
    userRepository.save(user);

    // Test: Update subscription
    user.updateSubscription("premium");
    userRepository.flush();  // Force DB sync

    // Assert: Data consistency
    assertTrue(userRepository.existsByEmail("test@example.com"));
    assertEquals("premium", user.getSubscriptionLevel());
}
```

### **3. Event-Driven Test (Node.js + Kafka)**
```javascript
const { Kafka } = require('kafkajs');

const kafka = new Kafka({ brokers: ['kafka:9092'] });
const consumer = kafka.consumer({ groupId: 'test-group' });

test('processOrderEvent_updatesInventory', async () => {
    await consumer.connect();
    await consumer.subscribe({ topic: 'order-events', fromBeginning: true });

    // Simulate event
    const producer = kafka.producer();
    await producer.connect();
    await producer.send({
        topic: 'order-events',
        messages: [{ value: JSON.stringify({ productId: 123, quantity: 1 }) }],
    });

    // Assert: Inventory was updated
    const inventory = await db.query('SELECT stock FROM products WHERE id = 123');
    assert.equal(inventory[0].stock, 99);  // Assuming initial stock was 100
});
```

---

## **Related Patterns**
| **Pattern**                          | **Description**                                                                 | **When to Use**                                  |
|---------------------------------------|-------------------------------------------------------------------------------|--------------------------------------------------|
| **[Unit Testing]**                    | Test individual components in isolation.                                       | Before integration tests; for **fast feedback**. |
| **[Mocking & Stubs]**                 | Replace dependencies with controlled fakes.                                   | When real dependencies are **slow or unavailable**. |
| **[Test Containers]**                 | Run real services (e.g., DBs, Kafka) in containers.                           | For **production-like integration tests**.       |
| **[Feature Flags]**                   | Toggle test flows without deployment.                                          | To **enable/disable** test paths dynamically.   |
| **[Canary Testing]**                  | Gradually roll out tests to a subset of users.                                | For **high-risk** production integrations.      |
| **[Contract Testing]**                | Validate API contracts between services (e.g., Pact).                         | When services are **loosely coupled**.          |
| **[End-to-End Testing]**              | Test the full user flow (slow but critical).                                  | For **critical user journeys**.                  |

---

## **Anti-Patterns to Avoid**
1. **Over-Mocking**:
   - *Problem*: Tests become unrealistic, missing true integration bugs.
   - *Fix*: Use **real dependencies** where possible.

2. **Ignoring Flakiness**:
   - *Problem*: Tests fail intermittently, wasting time.
   - *Fix*: Implement **retries**, **timeouts**, and **deterministic seeds**.

3. **Testing Everything at Once**:
   - *Problem*: Large E2E tests are slow and hard to debug.
   - *Fix*: **Modularize** tests by component/function.

4. **No Isolation**:
   - *Problem*: Tests interfere with each other (e.g., shared DB state).
   - *Fix*: Use **transactions**, **cleanup**, or **separate environments**.

5. **Skipping Test Setup**:
   - *Problem*: Tests fail due to **missing data** or **untested edge cases**.
   - *Fix*: Document **preconditions** and **seed data** clearly.

---
**Further Reading**:
- [Google’s Testing Blog](https://testing.googleblog.com/)
- [Martin Fowler on Integration Testing](https://martinfowler.com/articles/microservice-testing/)
- [Testcontainers Documentation](https://testcontainers.com/)