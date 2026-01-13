# **Debugging Domain-Driven Design (DDD): A Troubleshooting Guide**

Domain-Driven Design (DDD) is a powerful approach to structuring software around business domains, but misapplications can lead to architectural decay, performance bottlenecks, and maintainability issues. This guide provides a structured approach to diagnosing and fixing common DDD-related problems.

---

## **1. Symptom Checklist**

Before diving deep, verify which symptoms match your situation:

| **Symptom**                          | **Possible Cause**                                                                 |
|--------------------------------------|-------------------------------------------------------------------------------------|
| High coupling between modules        | Poor aggregation boundaries, missing bounded contexts                              |
| Difficulty understanding business logic | Lack of clear domain models, poor Ubiquitous Language usage                       |
| Slow query performance               | Overly complex aggregates, inefficient repository queries                         |
| Frequent null reference errors       | Weak entity/value object boundaries, missing invariants                           |
| Integration failures with other systems | Misaligned bounded contexts, improper event sourcing paradigms                     |
| Refactoring feels risky              | Lack of transactional boundaries, entangled dependencies                          |
| High CPU/memory usage                | Unnecessary object graphs, inefficient event processing                            |
| Poor test coverage                   | Lack of domain-specific tests, complex state transitions not mocked properly       |

If multiple symptoms appear, the issue is likely **architectural**, not just code-level.

---

## **2. Common Issues & Fixes**

### **Issue 1: Poor Bounded Context Definition**
**Symptom:** Modules rely too much on each other, leading to tangled dependencies.

**Debugging Steps:**
1. **Draw the Context Map**
   - Use a whiteboard or tool like [Mermaid.js](https://mermaid.js.org/) to visualize bounded contexts.
   - Example:
     ```mermaid
     graph TD
         A[Order Context] -->|uses| B[Payment Context]
         A -->|depends on| C[Inventory Context]
     ```
2. **Check for Shared Kernels**
   - If two contexts share code, refactor into a **Shared Kernel** with strict API contracts.
3. **Resolution:**
   - Introduce **explicit interfaces** (e.g., `IOrderRepository`, `IPaymentService`) to decouple contexts.
   - Example (C#):
     ```csharp
     // Order Service (Bounded Context)
     public interface IInventoryService
     {
         bool CheckStock(int productId, int quantity);
     }

     // Inventory Service (Separate Context)
     public class InventoryService : IInventoryService
     {
         public bool CheckStock(int productId, int quantity) { ... }
     }
     ```

### **Issue 2: Overly Complex Aggregates**
**Symptom:** Transactions fail due to large aggregates loading unnecessary data.

**Debugging Steps:**
1. **Profile Aggregate Loading**
   - Use a **repository query** to inspect loaded data:
     ```csharp
     public class OrderRepository : IOrderRepository
     {
         public Order GetById(int id)
         {
             var order = _dbContext.Orders
                 .Include(o => o.Items)
                 .Include(o => o.Customer)
                 .FirstOrDefault(o => o.Id == id);
             // If Customer is rarely needed, fetch it lazily instead.
             return order;
         }
     }
     ```
2. **Resolution:**
   - **Split aggregates** into smaller ones (e.g., `Order` vs. `OrderItem`).
   - Use **DTOs** for read models:
     ```csharp
     public class OrderSummaryDto
     {
         public int Id { get; set; }
         public decimal Total { get; set; }
         public List<OrderItemDto> Items { get; set; }
     }
     ```

### **Issue 3: Missing Domain Events**
**Symptom:** Business rules aren’t reflected in real-time (e.g., stock updates delayed).

**Debugging Steps:**
1. **Audit Event Flows**
   - Check if `IDomainEvent` handlers are subscribed in the event store.
   - Example (C# with MediatR):
     ```csharp
     public class OrderShippedEventHandler : INotificationHandler<OrderShippedEvent>
     {
         public Task Handle(OrderShippedEvent notification, CancellationToken ct)
         {
             // Trigger async operations (e.g., update warehouse)
             return Task.CompletedTask;
         }
     }
     ```
2. **Resolution:**
   - Ensure events are **published** correctly:
     ```csharp
     public class OrderService
     {
         private readonly IMediator _mediator;

         public void PlaceOrder(Order order)
         {
             order.Ship(); // Triggers OrderShippedEvent
             _mediator.Publish(order.Shipped);
         }
     }
     ```

### **Issue 4: Weak Invariants**
**Symptom:** Business rules (e.g., "Inventory > 0") are violated.

**Debugging Steps:**
1. **Validate Business Rules in Domain Logic**
   - Move checks into **entities/values** (not services):
     ```csharp
     public class Product
     {
         public int Quantity { get; private set; }

         public void ReduceStock(int amount)
         {
             if (Quantity - amount < 0)
                 throw new BusinessException("Insufficient stock");
             Quantity -= amount;
         }
     }
     ```
2. **Test with Unit Tests**
   - Fail fast with assertions:
     ```csharp
     [Fact]
     public void ReduceStock_ShouldThrowWhenInsufficient()
     {
         var product = new Product { Quantity = 5 };
         Assert.Throws<BusinessException>(() => product.ReduceStock(6));
     }
     ```

### **Issue 5: Integration Failures**
**Symptom:** Payments fail because the `PaymentContext` doesn’t align with `OrderContext`.

**Debugging Steps:**
1. **Check Context Alignment**
   - Ensure **Ubiquitous Language** is consistent (e.g., `PaymentStatus` vs. `PaymentState`).
2. **Resolution:**
   - Use **API Gateways** or **CQRS** to mediate interactions:
     ```csharp
     public class PaymentService
     {
         public async Task<bool> ProcessPayment(int orderId)
         {
             var order = await _orderRepository.GetAsync(orderId);
             var paymentResult = await _paymentClient.ChargeAsync(order.Total);
             if (!paymentResult.Success)
                 throw new PaymentFailedException();
             return true;
         }
     }
     ```

---

## **3. Debugging Tools & Techniques**

| **Tool/Technique**               | **Use Case**                                                                 |
|-----------------------------------|-----------------------------------------------------------------------------|
| **Log Aggregators (ELK, Seq)**   | Track domain events across microservices.                                   |
| **APM Tools (Dapr, OpenTelemetry)** | Profile repository queries and event flows.                               |
| **Code Coverage (Coverlet)**      | Ensure domain logic is tested (aim for ≥90% coverage).                      |
| **Domain Event Replay**           | Debug event sourcing by replaying past events in a sandbox.                 |
| **Static Analysis (Roslyn, SonarQube)** | Detect anti-patterns (e.g., cyclic dependencies).          |
| **Schema Migration Tools (Flyway, EF Migrations)** | Audit changes in aggregates over time.                        |

**Example Debugging Workflow:**
1. **Reproduce the Issue** with log correlation IDs.
2. **Inspect Database Changes** via EF Core’s `Audit` feature:
   ```csharp
   protected override void OnModelCreating(ModelBuilder modelBuilder)
   {
       modelBuilder.Entity<Order>().Property(o => o.Version)
           .HasDefaultValue(1);
   }
   ```
3. **Test Hypotheses** with a **local sandbox** (e.g., Dockerized Order/Payment services).

---

## **4. Prevention Strategies**

### **1. Enforce Clean Architecture**
- **Rules:**
  - Domain layer should **not** depend on infrastructure.
  - Use dependency inversion (e.g., `IOrderRepository` → `EfCoreOrderRepository`).

### **2. Automate Domain Testing**
- **Test Pyramid:**
  - **Unit:** Validate invariants (e.g., `Assert.Throws`).
  - **Integration:** Test event flows with `TestContainers`.
  - **E2E:** Simulate user flows (e.g., "Place Order → Ship").

### **3. Adopt Event Sourcing Gradually**
- Start with **commands-first** (CRUD), then introduce events for auditing.
- Example:
  ```csharp
  // Command (CQRS)
  public class PlaceOrderCommand : IRequest<OrderId>
  {
      public int ProductId { get; set; }
      public int Quantity { get; set; }
  }

  public class PlaceOrderHandler : IRequestHandler<PlaceOrderCommand, OrderId>
  {
      public async Task<OrderId> Handle(PlaceOrderCommand request, CancellationToken ct)
      {
          var order = AggregateRoot.Create(request.ProductId, request.Quantity);
          _eventStore.Append(order.Id, order.GetUncommittedChanges());
          return order.Id;
      }
  }
  ```

### **4. Document Ubiquitous Language**
- Use **domain events** to clarify behavior:
  ```csharp
  // Instead of vague "Updated", use:
  public class OrderShippedEvent : IDomainEvent
  {
      public DateTime ShippedAt { get; set; }
      public TrackingNumber TrackingNumber { get; set; }
  }
  ```

### **5. Review Boundaries Quarterly**
- Run **context mapping exercises** (e.g., "Does the Payment team understand the Inventory rules?").
- Use **story mapping** to align stakeholders.

---

## **5. Final Checklist for DDD Health**
| **Category**          | **Good Practice**                          | **Red Flag**                          |
|-----------------------|--------------------------------------------|----------------------------------------|
| **Bounded Contexts**  | Clear separation, explicit APIs            | Shared libraries, hidden dependencies |
| **Aggregates**        | Small, focused, single-responsibility      | Monolithic aggregates                |
| **Events**           | Used for async workflows                   | Events ignored or duplicated          |
| **Invariants**       | Enforced in domain, tested rigorously      | Checks moved to services              |
| **Ubiquitous Language** | Shared between devs/business stakeholders | Technical jargon over business terms   |

---

### **Next Steps**
1. **Prioritize** symptoms (e.g., fix invariants before splitting contexts).
2. **Start small** (e.g., refactor one aggregate).
3. **Measure impact** (e.g., reduce null errors by 70% in 2 weeks).

By focusing on **boundaries, events, and invariants**, you’ll systematically improve DDD adoption. For deeper dives, explore:
- [DDD Patterns by Vaughn Vernon](https://vaughnvernon.co/)
- [EventStorming](https://eventstorming.com/) workshops.