# **[Pattern] Domain-Driven Design (DDD) Reference Guide**

---
## **Overview**
Domain-Driven Design (DDD) is a software development approach centered around structuring code, models, and team collaboration around a **business domain**—the core problem space the software addresses. Introduced by Eric Evans (*Domain-Driven Design: Tackling Complexity in the Heart of Software*), DDD ensures that technical solutions align with business logic, reducing misalignment between developers and stakeholders. It emphasizes **ubiquitous language** (shared vocabulary between devs and domain experts), **rich domain models** (objects that encapsulate business rules), and **bounded contexts** (self-contained areas of domain expertise). While not a programming language or framework, DDD provides patterns like Aggregates, Entities, and Value Objects to tackle complexity in large-scale systems.

---
## **Key Concepts (Schema Reference)**

| **Concept**               | **Definition**                                                                                     | **Key Characteristics**                                                                                     | **Example**                                                                                     |
|---------------------------|---------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Ubiquitous Language**  | Shared vocabulary between developers and domain experts.                                         | Reduces ambiguity; evolves iteratively.                                                                  | "Order" vs. "Transaction" → "Customer Order" (avoids technical jargon).                         |
| **Bounded Context**       | Delimitates the scope of a domain model and its language.                                           | Defines boundaries where a model’s terms apply uniquely.                                               | E-commerce: *Checkout Context* vs. *Inventory Context* (both use "Product," but with different rules). |
| **Entity**                | Object with identity (uniqueness is intrinsic).                                                    | Defined by attributes + identity (e.g., ID).                                                             | `Customer { id: string, name: string }` (identity via `id`).                                     |
| **Value Object**          | Immutable, defined *entirely* by attributes (no identity).                                          | Comparison by value, not reference.                                                                       | `Money { amount: number, currency: string }` (no `id`).                                            |
| **Aggregate**             | Cluster of objects treated as a single unit for data changes (invariant preservation).             | Defined by a **root entity**; transactions must update the whole aggregate atomically.                   | `Order` (root) + `OrderItem` objects (child entities) cannot be modified independently.          |
| **Repository**            | Interface for storing/retrieving aggregates (abstraction over persistence).                           | Hides implementation (database, ORM) while exposing domain operations.                                   | `IOrderRepository.Find(long orderId)` (maps to SQL query or in-memory collection).               |
| **Domain Service**        | Stateless operation that doesn’t belong to a single aggregate but applies domain logic.          | Aggregates logic not fitting in entities/value objects.                                                 | `ShippingService.CalculateCost(Order order)`.                                                   |
| **Module**                | Grouping of related modules, services, or contexts (logical separation).                           | Used to organize large domains (e.g., by feature or subsystem).                                          | `PaymentModule`, `InventoryModule` in an e-commerce system.                                      |
| **Context Map**           | Diagram showing relationships between bounded contexts (e.g., shared kernel, separate ways).       | Visualizes integration patterns (e.g., shared kernel vs. open host service).                               | ![Context Map Example](https://ddd-by-examples.github.io/dddsamplev24/images/context-map.png)   |

---

## **Implementation Details**

### **1. Modeling the Domain**
- **Start with the Ubiquitous Language**:
  Collaborate with domain experts to define terms (e.g., "Delivery" vs. "Shipping").
  Example: *Avoid* `TableProduct`; use `CatalogItem` (if in product catalog context).
- **Identify Bounded Contexts**:
  Partition the domain into self-contained modules. Use context maps to resolve conflicts (e.g., if two contexts define "Discount," choose *conformist* or *separate way* patterns).
- **Design Aggregates**:
  Define invariants and choose a **root entity** (e.g., `Order` is the root; `OrderItem` cannot exist without it).
  **Rule**: All modifications to an aggregate must be made via the root.

### **2. Code Structure**
Use a **domain-driven layer architecture**:
```
src/
├── domain/          # Core business logic (entities, value objects, aggregates)
│   ├── entities/
│   │   └── Order.java
│   ├── valueObjects/
│   │   └── Money.java
│   └── repositories/
│       └── OrderRepository.java
├── application/     # Use cases (services interacting with domain)
│   └── services/
│       └── OrderService.java
├── infrastructure/  # External dependencies (DB, APIs)
│   ├── persistence/
│   │   └── JpaOrderRepository.java
│   └── clients/
│       └── PaymentClient.java
└── interfaces/      # API/controllers (REST, gRPC)
```

### **3. Persistence Strategies**
- **Repository Pattern**:
  Implement `IOrderRepository` with a concrete class (e.g., `JpaOrderRepository`) that maps to a database.
  ```java
  // Domain Layer (interface)
  public interface OrderRepository {
      Order findById(Long id);
      void save(Order order);
  }

  // Infrastructure Layer (implementation)
  @Repository
  public class JpaOrderRepository implements OrderRepository {
      @PersistenceContext
      private EntityManager entityManager;

      @Override
      public Order findById(Long id) {
          return entityManager.find(Order.class, id);
      }
  }
  ```
- **Event Sourcing** (Optional):
  Store state changes as a sequence of events (e.g., `OrderCreatedEvent`). Useful for auditing and replayability.
  Example:
  ```java
  // Event
  public record OrderCreatedEvent(Long orderId, LocalDateTime timestamp) {}

  // Repository
  public interface OrderEventRepository {
      List<OrderEvent> loadEvents(Long orderId);
  }
  ```

### **4. Communication Between Contexts**
- **Shared Kernel**:
  Share a core model (e.g., `Customer` entity) between contexts but avoid over-sharing.
- **Customer-Supplier**:
  One context publishes events (e.g., `OrderShipped`), another subscribes (e.g., Inventory updates stock).
- **Anti-Corruption Layer**:
  Wrap external APIs (e.g., payment gateway) to translate their models into domain terms.

---

## **Query Examples**
### **1. Finding an Order (Repository Query)**
```java
// Domain Layer
Order order = orderRepository.findById(orderId);
if (order == null) {
    throw new OrderNotFoundException("Order not found");
}

// Infrastructure Layer (JPA)
@Repository
public class JpaOrderRepository implements OrderRepository {
    @Override
    public Order findById(Long id) {
        return entityManager.find(Order.class, id);
    }
}
```

### **2. Calculating Order Total (Domain Service)**
```java
// Domain Service
public class OrderTotalCalculator {
    public Money calculate(Order order) {
        return order.getItems().stream()
            .map(item -> item.getProduct().getPrice().multiply(item.getQuantity()))
            .reduce(Money.ZERO, Money::add);
    }
}

// Usage in Application Layer
Order order = orderRepository.findById(orderId);
Money total = new OrderTotalCalculator().calculate(order);
```

### **3. Event-Driven Workflow (Order Shipped)**
```java
// Domain Event
public class OrderShippedEvent implements DomainEvent {
    private final Long orderId;
    private final String trackingNumber;

    public OrderShippedEvent(Long orderId, String trackingNumber) {
        this.orderId = orderId;
        this.trackingNumber = trackingNumber;
    }
}

// Publisher (Domain Layer)
public class Order {
    public void ship(String trackingNumber) {
        this.trackingNumber = trackingNumber;
        // Publish event (handled by DomainEventPublisher)
        DomainEventPublisher.publish(new OrderShippedEvent(id, trackingNumber));
    }
}

// Subscriber (Infrastructure Layer)
@Componentscan
public class ShippingNotificationService {
    @EventListener
    public void handle(OrderShippedEvent event) {
        sendEmail(event.orderId(), event.trackingNumber());
    }
}
```

---

## **Related Patterns**
| **Pattern**               | **Purpose**                                                                                     | **When to Use**                                                                                     |
|---------------------------|-------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| **Repository**            | Abstracts data access for aggregates.                                                          | When modeling persistence layer independently of the domain.                                         |
| **Factory**               | Creates domain objects with consistent initialization.                                          | When object creation logic is complex (e.g., validating inputs).                                    |
| **Unit of Work**          | Manages transactional boundaries for aggregates.                                               | When multiple aggregates must be updated atomically.                                                 |
| **CQRS**                  | Separates read (queries) and write (commands) models.                                          | For high-performance read-heavy systems (e.g., dashboards).                                          |
| **Event Sourcing**        | Stores state changes as a sequence of events.                                                  | When auditability and replayability are critical (e.g., financial systems).                           |
| **Strategic DDD**         | Focuses on modeling the business domain at a high level.                                        | Early stages of domain analysis to define bounded contexts.                                           |
| **Tactical DDD**          | Implements specific patterns (e.g., aggregates, entities) within a bounded context.             | Mid-to-late design when refining domain models.                                                     |
| **Hexagonal Architecture**| Decouples domain from external frameworks (e.g., databases, APIs).                              | When isolating the domain for testability and flexibility.                                           |

---
## **Anti-Patterns to Avoid**
1. **Over-Engineering**:
   Don’t apply DDD to simple CRUD apps where the domain is trivial.
2. **Ignoring Ubiquitous Language**:
   Mixing technical terms (e.g., "table" for "order") with business terms (e.g., "customer order").
3. **Leaky Abstractions**:
   Exposing persistence details (e.g., SQL queries) in the domain layer.
4. **Tight Coupling Between Contexts**:
   Sharing aggregates across contexts without clear boundaries (leads to spaghetti architecture).
5. **Premature Aggregates**:
   Creating aggregates too early without understanding invariants (e.g., splitting `User` into `User` + `Profile` unnecessarily).

---
## **Tools & Libraries**
| **Tool/Library**          | **Purpose**                                                                                     | **Languages/Frameworks**                                                                             |
|---------------------------|-------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| **EventStore**            | Persistence for event-sourced aggregates.                                                      | .NET, Java (e.g., [EventStoreDB](https://www.eventstore.com/)).                                  |
| **DDD Framework**         | Opinionated implementations (e.g., Axon Framework).                                             | Java (Axon), .NET (Vienna).                                                                    |
| **ORM/ODM**               | Maps aggregates to databases.                                                                   | JPA (Java), Entity Framework (.NET), Mongoose (Node.js).                                          |
| **Context Mapping Tools** | Visualize bounded contexts (e.g., [DDD Tools](https://ddd-by-examples.github.io/)).             | Diagram generation for context maps.                                                              |
| **Behavior-Driven Dev**  | Test domain logic with business rules (e.g., Cucumber).                                          | Any language with BDD support.                                                                       |

---
## **Further Reading**
1. **Books**:
   - *Domain-Driven Design: Tackling Complexity in the Heart of Software* – Eric Evans.
   - *Implementing Domain-Driven Design* – Vaughn Vernon.
2. **Articles**:
   - [DDD by Example (GitHub)](https://github.com/ddd-by-examples) (Practical code samples).
   - [Vaughn Vernon’s Blog](https://vaughnvernon.co/) (DDD principles).
3. **Courses**:
   - [DDD Europe Conference Talks](https://ddd-europe.com/) (Recorded sessions).
   - [Pluralsight: Domain-Driven Design Fundamentals](https://www.pluralsight.com/).