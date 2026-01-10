```markdown
# **Integration Testing Patterns: Building Reliable Systems in Real-World Scenarios**

*How to write tests that verify components work together—and why you can’t skip them.*

---

## **Introduction: Why Integration Tests Matter**

Imagine this scenario: Your team celebrates because all unit tests pass. You deploy to staging, but when users interact with the system, something breaks—an API call fails because a database constraint isn’t handled, or two microservices don’t synchronize data as expected. The issue? **Unit tests are too narrow—they don’t catch integration failures.**

Integration tests bridge the gap between isolated units and full-system tests. They verify:
- **Component interactions** (e.g., your service calling an external API).
- **Data consistency** (e.g., a database transaction spanning multiple tables).
- **Real-world dependencies** (e.g., a payment gateway or queue system).

This post explores **integration testing patterns**—practical approaches to test real system behavior without sacrificing speed or maintainability. We’ll cover:
- The problem unit tests alone can’t solve.
- Code-first examples for common patterns.
- Tradeoffs and anti-patterns.

---

## **The Problem: Unit Tests Pass, But the System Fails**

Unit tests isolate components (e.g., testing a `UserService` without a database), but **real-world systems rely on interactions**:
- **Database transactions**: A user registration might require updating 3 tables—in unit tests, you mock the DB, but the actual flow fails.
- **API dependencies**: Your service might call Stripe for payments. Unit tests mock this, but the real API rejects malformed requests.
- **Eventual consistency**: Two microservices might update the same cache independently. Unit tests don’t test race conditions.

### **Example: The Broken Payment Flow**
```javascript
// Unit test passes (mocked DB and Stripe)
it("processes payment", async () => {
  const mockStripe = { charge: jest.fn().mockResolvedValue({ status: "success" }) };
  const user = { stripeId: "tok_123" };

  await paymentService.process(user, mockStripe);
  expect(mockStripe.charge).toHaveBeenCalledWith(100);
});
```
**But in production:**
- The real Stripe API rejects the charge due to a missing `currency` field.
- The user’s order isn’t marked as paid, and the system is inconsistent.

**Lesson**: Unit tests validate logic, but **integration tests validate real interactions**.

---

## **The Solution: Integration Testing Patterns**

We’ll explore three key patterns with real-world tradeoffs:

1. **Database Transaction Testing** (Testing DB interactions).
2. **API Contract Testing** (Verifying external API calls).
3. **Event-Driven Testing** (Testing async workflows).

---

### **1. Database Transaction Testing**
**Goal**: Test data consistency across multiple tables or operations.

#### **Pattern: Transaction Rollback Testing**
Run tests in a transaction that rolls back after execution, ensuring no side effects.

#### **Example: Testing a User Registration**
```javascript
import { User, Order } from "./models";
import { connection } from "./config";

describe("User registration flow", () => {
  let testUser;

  beforeEach(async () => {
    // Start a transaction for each test
    await connection.beginTransaction();
    testUser = await User.create({
      name: "Alice",
      email: "alice@example.com",
    });
  });

  afterEach(async () => {
    // Rollback to avoid side effects
    await connection.rollback();
  });

  it("creates user and associated order", async () => {
    await testUser.orders.create({ amount: 99.99, status: "pending" });
    const order = await Order.findOne({ where: { userId: testUser.id } });
    expect(order).toBeDefined();
  });
});
```

#### **Tradeoffs**:
✅ **Isolated**: No risk of polluting the DB.
✅ **Fast**: Transactions are lightweight.
❌ **Not for schema changes**: Use migrations for that.

---

### **2. API Contract Testing**
**Goal**: Ensure your service behaves correctly when calling external APIs.

#### **Pattern: Mock Responses with Real HTTP Calls (Hybrid Testing)**
Use a library like `supertest` or `http-mock` to send real HTTP requests while controlling responses.

#### **Example: Testing a Payment Service**
```javascript
import { app } from "./app";
import { createServer } from "http-mock";
import request from "supertest";

describe("Payment service integration", () => {
  const mockStripe = createServer({
    "/charges": {
      POST: () => ([200, { payment_intent: "pi_123" }]),
    },
  });

  beforeAll(() => {
    mockStripe.listen(8000); // Use a free port
    process.env.STRIPE_API_URL = "http://localhost:8000";
  });

  afterAll(() => mockStripe.close());

  it("processes payment via Stripe", async () => {
    const response = await request(app)
      .post("/payments")
      .send({ amount: 100, token: "tok_123" });

    expect(response.status).toBe(200);
    expect(response.body).toHaveProperty("paymentIntent");
  });
});
```

#### **Tradeoffs**:
✅ **Real-world HTTP**: Catches auth, rate limiting, or malformed responses.
❌ **Slower**: HTTP overhead vs. mocks.
❌ **Flaky**: External service might fail.

**Pro Tip**: Use `nock` or `msw` (Mock Service Worker) for faster HTTP mocking.

---

### **3. Event-Driven Testing**
**Goal**: Test async workflows like event queues (e.g., Kafka, RabbitMQ).

#### **Pattern: Test Event Consumption End-to-End**
Publish an event and verify it triggers the expected side effects.

#### **Example: Testing an Order Processing Event**
```javascript
import { EventBus } from "./eventBus";
import { Order } from "./models";

describe("Order processing event", () => {
  let eventBus;

  beforeAll(() => {
    eventBus = new EventBus();
    // Use an in-memory queue for testing
    eventBus.use("orders", new MemoryQueue());
  });

  it("processes an order event", async () => {
    // Publish an event
    await eventBus.publish("order.created", {
      orderId: "ord_123",
      amount: 99.99,
    });

    // Verify the side effect (e.g., payment processed)
    const payment = await Payment.findOne({ where: { orderId: "ord_123" } });
    expect(payment).toBeDefined();
    expect(payment.status).toBe("completed");
  });
});
```

#### **Tradeoffs**:
✅ **Real async behavior**: Catches race conditions or missed events.
❌ **Complex setup**: Requires a test queue (e.g., `rabbitmq-ct` for RabbitMQ).
❌ **Slow**: Async operations add latency.

**Pro Tip**: Use `bull-board` for monitoring test queues visually.

---

## **Implementation Guide: Best Practices**

### **1. Start Small, Expand Gradually**
- Begin with **unit tests** for core logic.
- Add **integration tests** for critical paths (e.g., payment flow).
- Layer in **end-to-end tests** for user journeys.

### **2. Use Test Containers for Databases**
Spin up real DBs (Postgres, MongoDB) in Docker for stable testing.

```javascript
import { PostgreSqlContainer } from "@testcontainers/postgresql";

const db = await new PostgreSqlContainer().start();
process.env.DATABASE_URL = db.getConnectionUri();
```

### **3. Parallelize Tests Where Possible**
Use tools like `jest` or `pytest` with `--maxWorkers` to speed up CI.

### **4. Isolate Test Data**
- Use **schema migrations** for setup.
- **Seed test data** only what’s needed.
- **Clean up** after tests to avoid leaks.

---

## **Common Mistakes to Avoid**

### **❌ Overusing Integration Tests**
- **Problem**: If every test is slow, CI becomes unbearable.
- **Fix**: Reserve integration tests for **critical paths** (e.g., payments, auth).

### **❌ Mocking Everything**
- **Problem**: Mocks hide real bugs (e.g., network timeouts).
- **Fix**: Use **hybrid testing** (mock some, test others real).

### **❌ Ignoring Flakiness**
- **Problem**: Non-deterministic tests (e.g., race conditions) waste time.
- **Fix**:
  - Add retries for flaky tests.
  - Use transaction rollbacks for DB tests.

### **❌ Testing Infrastructure, Not Logic**
- **Problem**: Testing DB schema or API versions is not your job (use tools like `schema-spellchecker`).
- **Fix**: Focus on **domain logic** (e.g., "Does the order get processed correctly?").

---

## **Key Takeaways**

- **Integration tests catch unit-test-blind spots** (e.g., DB constraints, API failures).
- **Start with hybrid testing** (real dependencies where it matters).
- **Use transactions and containers** to keep tests fast and isolated.
- **Avoid flakiness** with retries and deterministic setup.
- **Balance speed and realism**: Not all tests need to be "real."

---

## **Conclusion: Test Like You Ship**

Integration tests are the **safety net** between unit tests and smoke tests. They bridge the gap between isolation and reality, ensuring your system behaves as expected when components interact.

**Your next steps**:
1. **Pilot**: Pick one critical flow (e.g., payment) and add integration tests.
2. **Automate**: Integrate them into CI/CD.
3. **Refine**: Measure flakiness and optimize.

Remember: **No test is perfect, but smart integration tests prevent painful production failures.**

---
**Further Reading**:
- [Testcontainers for Python/Node.js](https://testcontainers.com/)
- [MSW (Mock Service Worker)](https://mswjs.io/)
- [Event-Driven Testing with Bull](https://github.com/OptimalBits/bull-board)
```

---
**Why This Works**:
- **Code-first**: Every concept is illustrated with examples.
- **Tradeoffs are explicit**: No "do this, it’s magic" advice.
- **Actionable**: Clear next steps for readers to implement.
- **Professional but friendly**: Assumes readers are already advanced but want deeper insights.

Would you like me to expand on any section (e.g., add more patterns or dive deeper into test containers)?