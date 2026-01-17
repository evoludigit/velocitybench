```markdown
---
title: "Hexagonal Architecture: Keeping Your Business Logic Clean and Decoupled"
date: "2024-05-15"
category: "backend"
tags: ["architecture", "design patterns", "clean code", "backend", "decoupling"]
---

# Hexagonal Architecture: Keeping Your Business Logic Clean and Decoupled

![Hexagonal Architecture Diagram](https://miro.medium.com/max/1400/1*FtLkG1ZQ4j2w28JXVvF6OQ.png)

Ever found yourself caught in a tangled web of dependencies—where changes to one part of your system break unrelated functionality? Perhaps you've watched databases evolve alongside application logic, or struggled to swap out payment gateways without rewriting core business rules. These are classic symptoms of a system that lacks clear boundaries between its core logic and external concerns. Enter **Hexagonal Architecture**, also known as **Ports and Adapters**: a pattern that forces you to explicitly separate what your system *does* (business logic) from *how* it does it (infrastructure).

In this tutorial, we’ll explore how hexagonal architecture can help you build resilient, testable, and maintainable systems by isolating business rules from external dependencies. We’ll break down the core concepts, walk through practical examples, and discuss tradeoffs while avoiding common pitfalls. By the end, you’ll have a clear roadmap for applying hexagonal architecture to your next project.

---

## The Problem: Spaghetti Code and Tight Coupling

Imagine building an e-commerce system where the `OrderService` class directly instantiates a database connection and handles both order validation and persistence logic. When you later need to:
1. Swap out PostgreSQL for MongoDB,
2. Add a retry mechanism for failed payment transactions,
3. Or simply run unit tests without touching a database,

...you’re in for a world of pain. This is the reality of **tight coupling**: when your code’s structure mirrors its dependencies rather than its business rules.

Here’s why this happens:
- **Dependencies leak into the core**: Business logic is intertwined with implementation details (e.g., SQL queries, HTTP clients).
- **Testing becomes brittle**: Dependencies like databases or external APIs make unit testing difficult.
- **Infrastructure becomes the bottleneck**: Changes to databases, message brokers, or payment providers require code changes.
- **"But it works!" syndrome**: Short-term solutions become long-term technical debt as the system grows.

This isn’t just theoretical. Teams using hexagonal architecture report:
- **30-50% fewer integration tests** (fewer moving parts to test).
- **Faster feature development** (business logic can be written independently of infrastructure).
- **Easier adoption of new technologies** (e.g., swapping Kafka for RabbitMQ without rewriting core logic).

---

## The Solution: Hexagonal Architecture in Action

The **solution** to these problems is to draw a clear line between what your system *does* (business logic) and *how* it does it (infrastructure). Hexagonal architecture achieves this by:
1. **Separating ports (interfaces) from adapters (implementations)**.
2. **Using dependency inversion** (high-level modules depend on abstractions, not concrete implementations).
3. **Keeping the core (domain layer) free of external dependencies**.

### Core Concepts

1. **Core (Domain Layer)**:
   - Contains the **business rules** and **domain logic**.
   - Depends only on **ports** (interfaces), not adapters.
   - Example: `OrderService` defines how to validate an order but doesn’t know how to save it to a database.

2. **Ports (Interfaces)**:
   - Define **contracts** for interactions with external systems.
   - Divided into:
     - **Primary ports** (e.g., `OrderRepository`): Called by the core.
     - **Secondary ports** (e.g., `PaymentGateway`): Used by adapters to interact with external systems.
   - Example: `OrderRepository` might define `save(Order order)`, but the core doesn’t care if it’s implemented with SQL or NoSQL.

3. **Adapters**:
   - Implement **ports** using concrete technologies.
   - Can be:
     - **Inbound adapters** (e.g., REST APIs, GraphQL): Receive requests.
     - **Outbound adapters** (e.g., database drivers, message brokers): Send requests.
   - Example: A `PostgresOrderRepository` adapter implements `OrderRepository` using a JDBC connection.

![Hexagonal Architecture Flow](https://dzone.com/storage/img/blog/v2020/03/05/hexagonal-architecture-f0e9b08f288a4d44a1ff4497bcb918cd.png)

---

## Code Examples: Building a Simple Order Service

Let’s implement a hexagonal order service with the following components:
- **Domain**: `OrderService` (core business logic).
- **Primary Port**: `OrderRepository` (interface).
- **Adapter**: `PostgresOrderRepository` (concrete implementation).
- **Secondary Port**: `PaymentGateway` (interface).
- **Adapter**: `StripePaymentGateway` (concrete implementation).

### 1. Domain Layer (Core Logic)
This layer contains the pure business rules, with no infrastructure dependencies.

```java
// Order.java (Domain Entity)
public class Order {
    private String orderId;
    private List<OrderItem> items;
    private PaymentStatus status;

    public boolean validate() {
        return items.stream().noneMatch(item -> item.getQuantity() <= 0);
    }
}

// PaymentStatus.java (Domain Model)
public enum PaymentStatus {
    PAID, PENDING, FAILED
}

// OrderService.java (Core Logic)
public class OrderService {
    private final OrderRepository orderRepository;
    private final PaymentGateway paymentGateway;

    // Dependency Injection
    public OrderService(OrderRepository orderRepository, PaymentGateway paymentGateway) {
        this.orderRepository = orderRepository;
        this.paymentGateway = paymentGateway;
    }

    public void createOrder(Order order) {
        if (!order.validate()) {
            throw new IllegalArgumentException("Invalid order items");
        }
        orderRepository.save(order);
        paymentGateway.processPayment(order.getOrderId());
    }
}
```

### 2. Primary Port: `OrderRepository`
This is an interface that the core logic depends on.

```java
// OrderRepository.java (Primary Port)
public interface OrderRepository {
    void save(Order order);
    Order findById(String orderId);
}
```

### 3. Adapter: `PostgresOrderRepository`
This implements the `OrderRepository` interface using PostgreSQL.

```java
// PostgresOrderRepository.java (Adapter)
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

@Repository
public class PostgresOrderRepository implements OrderRepository {
    private final JdbcTemplate jdbcTemplate;

    public PostgresOrderRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    @Override
    public void save(Order order) {
        String sql = "INSERT INTO orders (order_id, items, status) VALUES (?, ?, ?)";
        jdbcTemplate.update(sql,
            order.getOrderId(),
            JSON.stringify(order.getItems()),
            order.getStatus().name()
        );
    }

    @Override
    public Order findById(String orderId) {
        String sql = "SELECT * FROM orders WHERE order_id = ?";
        // ... (omitted for brevity; assume RowMapper handles deserialization)
        return jdbcTemplate.queryForObject(sql, orderId, Order.class);
    }
}
```

### 4. Secondary Port: `PaymentGateway`
This defines how the core interacts with external payment systems.

```java
// PaymentGateway.java (Secondary Port)
public interface PaymentGateway {
    void processPayment(String orderId);
    boolean verifyPayment(String orderId);
}
```

### 5. Adapter: `StripePaymentGateway`
This implements `PaymentGateway` using Stripe’s API.

```java
// StripePaymentGateway.java (Adapter)
import com.stripe.Stripe;
import com.stripe.exception.StripeException;

public class StripePaymentGateway implements PaymentGateway {
    @Override
    public void processPayment(String orderId) {
        Stripe.apiKey = System.getenv("STRIPE_SECRET_KEY");
        try {
            // Call Stripe API to charge the customer
            com.stripe.Charge.create(params -> params
                .setAmount(1000)
                .setCurrency("usd")
                .setDescription("Order #" + orderId)
            );
        } catch (StripeException e) {
            throw new PaymentProcessingException("Failed to process payment", e);
        }
    }

    @Override
    public boolean verifyPayment(String orderId) {
        // Implement payment verification logic
        return true;
    }
}
```

### 6. Inbound Adapter: REST API
This is an example of how you might expose the `OrderService` via a REST endpoint.

```java
// OrderController.java (Inbound Adapter)
@RestController
@RequestMapping("/orders")
public class OrderController {
    private final OrderService orderService;

    public OrderController(OrderService orderService) {
        this.orderService = orderService;
    }

    @PostMapping
    public ResponseEntity<Order> createOrder(@RequestBody Order order) {
        orderService.createOrder(order);
        return ResponseEntity.created(URI.create("/orders/" + order.getOrderId())).build();
    }
}
```

### 7. Dependency Injection Setup
To tie everything together, use a framework like Spring’s dependency injection.

```java
// Application.java (Main Class)
@SpringBootApplication
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }

    // Configure dependencies
    @Bean
    public OrderService orderService(OrderRepository orderRepository, PaymentGateway paymentGateway) {
        return new OrderService(orderRepository, paymentGateway);
    }

    @Bean
    public OrderRepository orderRepository(JdbcTemplate jdbcTemplate) {
        return new PostgresOrderRepository(jdbcTemplate);
    }

    @Bean
    public PaymentGateway paymentGateway() {
        return new StripePaymentGateway();
    }
}
```

---

## Implementation Guide: Step-by-Step

Follow these steps to adopt hexagonal architecture in your project:

### 1. **Identify Your Core Domain**
   - What are the **business rules** that define your product? (e.g., order validation, discount calculations).
   - Example: In our case, `OrderService` and `Order` are the core.

### 2. **Define Primary Ports**
   - For each interaction with external systems (database, cache, etc.), define an interface.
   - Example: `OrderRepository`, `PaymentGateway`.

### 3. **Implement Adapters**
   - Write concrete implementations for each port.
   - Example: `PostgresOrderRepository`, `StripePaymentGateway`.

### 4. **Design Inbound Adapters**
   - Expose your core logic via APIs (REST, GraphQL) or CLI commands.
   - Example: `OrderController`.

### 5. **Test Your Core Independently**
   - Mock ports to test business logic without external dependencies.
   - Example: Use `Mockito` to mock `OrderRepository` and `PaymentGateway`.

### 6. **Iterate and Refactor**
   - Start small: Refactor one module at a time.
   - Example: Begin with the `OrderService` before tackling payment logic.

### 7. **Gradually Adopt**
   - Not every project needs full hexagonal architecture. Start with critical components (e.g., payment processing) and expand.

---

## Common Mistakes to Avoid

1. **Treating Adapters as the Core**:
   - ❌ Mistake: Writing `OrderService` to directly call Stripe API.
   - ✅ Fix: Keep `OrderService` independent, and inject `PaymentGateway`.

2. **Ignoring Secondary Ports**:
   - ❌ Mistake: Hardcoding database queries in `OrderService`.
   - ✅ Fix: Define `OrderRepository` as a port and implement adapters separately.

3. **Overcomplicating the Architecture**:
   - ❌ Mistake: Adding hexagonal layers to a small script.
   - ✅ Fix: Use hexagonal architecture for complex systems; keep it simple for small projects.

4. **Tight Coupling with Testing Frameworks**:
   - ❌ Mistake: Using JUnit directly in domain logic.
   - ✅ Fix: Keep domain logic framework-agnostic (e.g., no `@Test` annotations in `OrderService`).

5. **Not Mocking Ports for Testing**:
   - ❌ Mistake: Testing `OrderService` with real database calls.
   - ✅ Fix: Use mock objects (e.g., `Mockito`) to simulate `OrderRepository`.

6. **Assuming One Adapter Fits All**:
   - ❌ Mistake: Using only PostgreSQL for all environments (dev, staging, prod).
   - ✅ Fix: Write adapters for different databases (e.g., `MongoOrderRepository`) and inject the right one per environment.

---

## Key Takeaways

Here’s what you should remember from this tutorial:

- **Hexagonal Architecture separates what from how**:
  - **What**: Business logic (core).
  - **How**: Infrastructure (adapters).

- **Ports are contracts, not implementations**:
  - Define interfaces (`OrderRepository`) before writing code for databases or APIs.

- **Dependency inversion principle**:
  - High-level modules (core) depend on abstractions (ports), not concrete details.

- **Testability improves**:
  - Business logic can be unit-tested without external dependencies.

- **Infrastructure becomes interchangeable**:
  - Swap databases, payment gateways, or APIs with minimal code changes.

- **Start small**:
  - Refactor one critical module at a time; don’t boil the ocean.

- **Avoid over-engineering**:
  - Hexagonal architecture is a tool, not a silver bullet. Use it where it adds value.

- **Document your ports**:
  - Clear interface contracts make the system easier to maintain and extend.

---

## Conclusion

Hexagonal Architecture is more than just a pattern—it’s a **mindset shift** toward designing systems that prioritize business logic over implementation details. By explicitly defining ports and adapters, you create a system that’s:
- **Easier to test** (isolated business logic).
- **More maintainable** (changes in infrastructure don’t break core logic).
- **More flexible** (swap databases, APIs, or message brokers without rewriting business rules).

### When to Use Hexagonal Architecture
- You’re building a **complex domain** (e.g., e-commerce, banking).
- You need **high testability** (unit tests over integration tests).
- Infrastructure changes are **frequent** (e.g., testing different databases in CI).
- Your team values **decoupling** and **modularity**.

### When to Avoid It
- For **small scripts or prototypes** where simplicity outweighs flexibility.
- If your stack is **stable** and unlikely to change soon.
- When **overhead** of interfaces and adapters isn’t justified by the complexity.

### Next Steps
1. **Try it on a small project**: Refactor one module (e.g., user authentication) using hexagonal principles.
2. **Experiment with mocks**: Test your core logic without touching a database or API.
3. **Explore alternatives**: Combine hexagonal with other patterns like CQRS or Event Sourcing for even more flexibility.
4. **Share your learnings**: Discuss with your team how hexagonal architecture can improve your codebase.

---

## Final Thoughts
Hexagonal Architecture isn’t about rigid layers or dumbing down your code—it’s about **keeping your business logic sharp** while letting infrastructure adapt to the needs of your project. By following this pattern, you’ll build systems that are resilient, testable, and easy to evolve.

Now go ahead and try it! Start by extracting one interface from your spaghetti code, and watch how much cleaner your system becomes.

---

### References
1. [Alistair Cockburn’s Hexagonal Architecture (2005)](https://alistair.cockburn.us/hexagonal-architecture/)
2. [Martin Fowler on Ports and Adapters](https://martinfowler.com/bliki/PortsAndAdapters.html)
3. [Spring Boot + Hexagonal Architecture Example](https://refactoring.guru/design-patterns/hexagonal-architecture)
4. [Göktuğ Başaran’s Hexagonal Architecture in Java](https://www.baeldung.com/java-hexagonal-architecture)
```