# **Debugging Hexagonal Architecture: A Troubleshooting Guide**
*Isolating Business Logic from External Concerns*

Hexagonal Architecture (also called "Ports and Adapters") ensures loose coupling between core business logic and external systems (databases, APIs, UI, etc.). When misapplied, this can lead to performance bottlenecks, poor scalability, and maintenance nightmares.

This guide provides a structured approach to diagnosing and fixing common issues in Hexagonal Architecture implementations.

---

## **1. Symptom Checklist**
Before diving into fixes, verify if your system exhibits these signs of misapplied Hexagonal Architecture:

| **Symptom** | **Possible Cause** | **Quick Check** |
|-------------|-------------------|----------------|
| **Core logic tightly coupled to frameworks** | Adapters not properly abstracted | Check if `UserService` directly calls `JdbcTemplate` or `MongoRepository` |
| **Performance degradation under load** | Inefficient port implementations | Profile calls between adapters and use cases |
| **Difficulty mocking dependencies** | Test adapters are hard to isolate | Can you mock `Repository` without touching DB? |
| **System fails when external systems change** | Adapters not following interface contracts | Check if `PaymentGateway` implementation breaks when updated |
| **High maintenance cost** | Overly complex adapters or misplaced logic | Are adapters handling business rules? |
| **Integration tests fail unpredictably** | Fixture setup in use cases instead of adapters | Can you swap implementations without modifying test logic? |

If multiple symptoms appear, proceed to **Common Issues and Fixes**.

---

## **2. Common Issues and Fixes**
### **Issue 1: Adapters Directly Call Domain Logic (Violation of Dependency Rule)**
**Symptom:**
- `UserService` (application port) fetches data directly from `UserRepository` (adapter).
- Use cases modify adapters instead of core entities.

**Root Cause:**
Misunderstanding of dependency flow (external → core vs. core → external).

**Fix:**
Ensure **external systems depend on the core**, not the other way around.

#### **Before (Incorrect)**
```java
// UserService directly calls repository (violation: external → core)
public class UserService {
    private final UserRepository userRepository;

    public User getUser(String id) {
        UserEntity entity = userRepository.findById(id); // Adapter pollutes core
        return new User(entity.getName(), entity.getEmail()); // Logic in service
    }
}
```

#### **After (Correct)**
```java
// Core defines ports, adapters implement them
public interface UserRepository {  // Port (interface)
    Optional<UserEntity> findById(String id);
}

// Adapters implement ports (database, API, etc.)
public class JdbcUserRepository implements UserRepository { // Adapter
    // Implementation details hidden from core
}

// Service works with abstractions
public class UserService {
    private final UserRepository userRepository;

    public User getUser(String id) {
        UserEntity entity = userRepository.findById(id); // Works with abstraction
        return User.fromEntity(entity); // Pure domain logic
    }
}
```

**Key Rule:**
- **Core (hexagon) defines interfaces (ports).**
- **Adapters implement those interfaces.**
- **Never let adapters depend on core logic.**

---

### **Issue 2: Adapters Handle Business Logic**
**Symptom:**
- `PaymentGatewayAdapter` contains validation rules.
- Database migrations introduce business logic.

**Root Cause:**
Confusion between **infrastructure** (adapters) and **domain** (core rules).

**Fix:**
Move all business logic to the core and let adapters **translate domain objects to/from external formats**.

#### **Before (Incorrect)**
```java
// PaymentGatewayAdapter handles validation (should be in core)
public class PaymentGatewayAdapter {
    public boolean processPayment(PaymentRequest request) {
        if (request.amount < 0) throw new InvalidAmountException(); // Business rule!
        return gateway.charge(request.cardDetails);
    }
}
```

#### **After (Correct)**
```java
// Core defines domain rules
public class PaymentValidator {
    public boolean isValid(PaymentRequest request) {
        return request.amount >= 0; // Business rule in core
    }
}

// Adapter only handles external concerns
public class PaymentGatewayAdapter {
    private final PaymentValidator validator;

    public boolean processPayment(PaymentRequest request) {
        if (!validator.isValid(request)) throw new InvalidAmountException();
        return gateway.charge(request.cardDetails); // External call
    }
}
```

**Key Rule:**
- **Adapters only handle external concerns (persistance, networking, etc.).**
- **Business logic resides in core use cases/entities.**

---

### **Issue 3: Performance Bottlenecks in Adapters**
**Symptom:**
- Slow API responses when scaling.
- Database queries leak into use cases.

**Root Cause:**
Adapters are not optimized, or use cases fetch data inefficiently.

**Fix:**
- **Optimize adapter queries** (caching, batching).
- **Use CQRS** for read-heavy workloads.

#### **Before (Inefficient)**
```java
// Use case fetches all data at once (bad for performance)
public class OrderService {
    private final OrderRepository repository;

    public OrderDetails getOrderDetails(String orderId) {
        OrderEntity entity = repository.findById(orderId); // Single query
        return new OrderDetails(
            entity.getItems(), // N+1 problem if items are lazy-loaded
            entity.getCustomer()
        );
    }
}
```

#### **After (Optimized)**
```java
// Adapter returns only needed fields (DTOs)
public interface OrderRepository {
    OrderDetailsDto getOrderDetails(String orderId); // Optimized query
}

// Use case works with DTOs (no N+1)
public class OrderService {
    public OrderDetails getOrderDetails(String orderId) {
        return new OrderDetails(
            repository.getOrderDetails(orderId).getItems(), // Single query
            repository.getOrderDetails(orderId).getCustomer()
        );
    }
}
```

**Debugging Steps:**
1. **Profile queries** (e.g., with **PostgreSQL `EXPLAIN ANALYZE`** or **Redis CLI**).
2. **Check for N+1** using slow query logs.
3. **Implement caching** (e.g., **Redis**, **Caffeine**).

---

### **Issue 4: Integration Problems with External Systems**
**Symptom:**
- Payment gateway failures break the system.
- Database schema changes break adapters.

**Root Cause:**
Adapters are not resilient to external changes.

**Fix:**
- **Use adapter patterns** (e.g., **Strategy**, **Factory**) to swap implementations.
- **Implement retries/fallbacks** for external calls.

#### **Before (Fragile)**
```java
// Tight coupling to Stripe
public class StripePaymentAdapter {
    public boolean charge(CardDetails card) {
        return stripeClient.charge(card); // Fails if Stripe updates API
    }
}
```

#### **After (Resilient)**
```java
// Decoupled via Strategy pattern
public interface PaymentGateway {
    boolean charge(CardDetails card);
}

public class StripePaymentGateway implements PaymentGateway { // Adapter
    // Implementation
}

public class FallbackPaymentGateway implements PaymentGateway { // Backup
    // Retry or use backup service
}

public class PaymentService {
    private final PaymentGateway gateway;

    public PaymentService(PaymentGateway gateway) {
        this.gateway = gateway; // Dependency injection
    }

    public boolean processPayment(CardDetails card) {
        return gateway.charge(card); // Works with any adapter
    }
}
```

**Debugging Steps:**
1. **Mock external calls** (e.g., **WireMock**, **Postman Collections**).
2. **Log adapter failures** (e.g., **Sentry**, **ELK**).
3. **Implement circuit breakers** (e.g., **Resilience4j**).

---

## **3. Debugging Tools and Techniques**
| **Tool/Technique** | **Purpose** | **Example** |
|--------------------|------------|------------|
| **Dependency Injection (DI) Inspection** | Check if adapters depend on core | Use **Spring Profiles** or **Dagger/Hilt** to verify flows |
| **Mocking Frameworks** | Isolate adapters for testing | **Mockito**, **WireMock** for HTTP adapters |
| **AOP (Aspect-Oriented Programming)** | Log adapter calls | **Spring AOP** for tracing |
| **Database Profiling** | Identify slow queries | **PostgreSQL `pg_stat_statements`**, **MySQL Slow Query Log** |
| **API Mocking** | Simulate external services | **Postman Mock Server**, **WireMock** |
| **Circuit Breaker Libraries** | Handle external failures | **Resilience4j**, **Hystrix** |
| **Heap Dump Analysis** | Detect memory leaks in adapters | **VisualVM**, **YourKit** |

**Recommended Workflow:**
1. **Isolate the adapter** (mock all dependencies).
2. **Unit test adapter behavior** (verify translation logic).
3. **Integration test with a real external system** (e.g., **TestContainers**).
4. **Profile under load** (e.g., **JMeter**, **Locust**).

---

## **4. Prevention Strategies**
To avoid Hexagonal Architecture pitfalls in the future:

### **1. Strict Layer Separation**
- **Core (Hexagon):**
  - Use cases, entities, domain services.
  - No framework dependencies.
- **Adapters:**
  - Only handle external concerns (DB, HTTP, etc.).
  - Never call core directly.

### **2. Automated Dependency Checks**
- Use **static analysis tools** (e.g., **Checkstyle**, **PMD**) to enforce:
  ```java
  // Rule: Core layers must not import adapter layers
  @SuppressWarnings("PMD.AvoidImportsFromRuntime")
  public class CoreService { // Should not import "adapter" packages
  }
  ```

### **3. Test Adapter Contracts**
- Write **contract tests** (e.g., **Pact**) to ensure adapters follow expected behavior.
- Example: Verify `UserRepository` always returns `Optional<UserEntity>`.

### **4. Use DTOs for Crossing Boundaries**
- Never expose entities directly to adapters.
- Example:
  ```java
  // Bad: Adapters modify entities
  userRepository.update(entity); // Entity has adapter-specific fields

  // Good: Use DTOs
  userRepository.update(userDto); // Adapter handles conversion
  ```

### **5. Document Adapter Responsibilities**
- Clearly define what each adapter does (e.g., **README.md** in adapter package).
- Example:
  ```
  # PaymentGatewayAdapter
  - Implements `PaymentGateway` interface
  - Handles Stripe API calls
  - Translates `PaymentRequest` ↔ `StripeCharge`
  ```

### **6. Regular Architecture Reviews**
- **Spike sessions** to refactor tightly coupled components.
- **SonarQube** for dependency complexity warnings.

---

## **Final Checklist for a Healthy Hexagonal Architecture**
| **Check** | **Pass/Fail** |
|-----------|--------------|
| Core depends only on interfaces (not implementations) | ✅/❌ |
| Adapters implement ports, not core logic | ✅/❌ |
| Use cases work with abstractions (DTOs, entities) | ✅/❌ |
| External system changes don’t break core | ✅/❌ |
| Adapters are mockable for testing | ✅/❌ |
| Performance tests show no adapter bottlenecks | ✅/❌ |

---
### **Next Steps**
- **If failing**: Refactor immediately (start with the most critical adapter).
- **If passing**: Document the architecture and train new devs.
- **For large systems**: Gradually migrate one layer at a time.

By following this guide, you’ll ensure your Hexagonal Architecture remains **scalable, maintainable, and resilient**. 🚀