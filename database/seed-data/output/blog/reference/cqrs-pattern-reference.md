---
# **[Pattern] CQRS (Command Query Responsibility Segregation) Reference Guide**

---

## **1. Overview**
**CQRS (Command Query Responsibility Segregation)** is a software architectural pattern that separates the **write model** (commands for state changes) from the **read model** (queries for data retrieval). This decoupling improves scalability, performance, and maintainability by allowing independent optimizations for read/write operations.

CQRS is widely used in **event-sourced systems** and **microservices**. By treating reads and writes as distinct concerns, applications can:
- Optimize query performance via denormalized read models.
- Handle high-throughput writes with streams or event logs.
- Use different technologies for read/write paths (e.g., SQL for writes, NoSQL for reads).

**Key Tenets:**
- **Commands** modify state (e.g., `UpdateUserAddress`).
- **Queries** retrieve state (e.g., `GetUserOrders`).
- Models are **eventually consistent** (synchronized via events or triggers).

---

## **2. Schema Reference**

| **Component**         | **Description**                                                                                     | **Common Tools**                                                                 |
|-----------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **Command Model**     | Defines read-only projections optimized for queries.                                                | DDD aggregates, event stores, or CQRS frameworks (e.g., **MediatR**, **MassTransit**). |
| **Read Model**        | Stores data in a form optimized for querying (often denormalized).                                  | Databases (PostgreSQL, MongoDB), caches (Redis), or event-sourced events.        |
| **Command Handler**   | Processes write operations (e.g., `SaveOrderCommand`). Returns no data.                              | Unit of Work, transactional outbox, or event stores.                              |
| **Query Handler**     | Retrieves read data via domain queries (e.g., `GetCustomerHistory`).                                | Repository pattern, projection jobs.                                              |
| **Event Store**       | Logs immutable events (e.g., `OrderPlacedEvent`) for replayability.                                 | **Event Store** (e.g., EventStoreDB), Kafka.                                     |
| **Event Sourced Projection** | Rebuilds the read model from events.                                                              | Event-driven projections (e.g., **NEventStore**, **Akka.Events**).            |

---

## **3. Implementation Details**

### **3.1 Key Concepts**
1. **Command vs. Query**
   - **Command**: Modifies state (e.g., `UpdateShippingAddress`). Results in a side effect.
   - **Query**: Reads state (e.g., `GetCustomerAddress`). No side effects.
   - *Example:*
     ```csharp
     // Command (write)
     public class UpdateCustomerAddressCommand : ICommand {
         public string Id { get; set; }
         public string NewAddress { get; set; }
     }

     // Query (read)
     public class GetCustomerAddressQuery : IQuery<string> {
         public string Id { get; set; }
     }
     ```

2. **Read-Only Projections**
   - Denormalized, optimized for queries (e.g., aggregating orders for a dashboard).
   - Updated via **event handlers** or **scheduled jobs**.

3. **Eventual Consistency**
   - Writes first, reads later. Useful for scalability but requires conflict resolution (e.g., **optimistic concurrency**).

4. **Eventual Synchronization**
   - Commands emit events (e.g., `AddressUpdatedEvent`).
   - Event handlers update the read model.

---

### **3.2 Architecture Diagram**
```
┌───────────────────────┐       ┌───────────────────────┐
│                       │       │                       │
│   UI/Application     │────▶│   Command Handler      │
│   Layer (Commands)    │       │                       │
│                       │       └──────────────┬───────┘
├───────────────────────┤               │
│                       │       ┌───────┴───────┐
│   Event Store         │─────▶│   Event Bus   │─────▶ Read Model
│   (e.g., Kafka)       │       └───────────────┘
└───────────────────────┘
                                    └───────────┬───────┘
                                                │
                                                ▼
                  ┌───────────────────────┐
                  │   Query Handler      │
                  │                       │
                  └───────┬───────────────┘
                          │
                          ▼
               ┌───────────────────────┐
               │     Read Model        │ (e.g., SQL, NoSQL)
               └───────────────────────┘
```

---

### **3.3 Implementation Steps**
1. **Define Commands & Queries**
   - Use a **command/query bus** (e.g., **MediatR** in .NET).
   - Example:
     ```csharp
     // Command (write)
     public class PlaceOrderCommand : IRequest<Order>
     {
         public string CustomerId { get; set; }
         public List<OrderItem> Items { get; set; }
     }

     // Query (read)
     public class GetOrderStatusQuery : IRequest<OrderStatus>
     {
         public string OrderId { get; set; }
     }
     ```

2. **Implement Handlers**
   - Commands: Update the **write model** (e.g., entity framework) and **publish events**.
   - Queries: Query the **read model** (e.g., Dapper, LINQ to SQL).

3. **Set Up Event Projections**
   - Subscribe to events (e.g., `OrderPlacedEvent`) and update the read model:
     ```csharp
     public class OrderPlacedEventHandler : IEventHandler<OrderPlacedEvent>
     {
         private readonly IOrderReadRepository _repo;
         public OrderPlacedEventHandler(IOrderReadRepository repo) => _repo = repo;

         public async Task Handle(OrderPlacedEvent @event)
         {
             await _repo.AddOrderSummary(@event.OrderId, @event.CustomerId);
         }
     }
     ```

4. **Optimize Read Path**
   - Use **caching** (Redis) for frequent queries.
   - Pre-compute aggregations (e.g., sales reports).

5. **Handle Concurrency**
   - Optimistic concurrency checks for conflicting updates.

---

## **4. Query Examples**
### **4.1 Command (Write) Example**
**Input:**
```csharp
var command = new UpdateProductPriceCommand
{
    ProductId = "prod-123",
    NewPrice = 9.99m
};
```
**Handler (Command):**
```csharp
public class UpdateProductPriceCommandHandler : IRequestHandler<UpdateProductPriceCommand, Unit>
{
    private readonly IProductRepository _repo;
    public UpdateProductPriceCommandHandler(IProductRepository repo) => _repo = repo;

    public async Task<Unit> Handle(UpdateProductPriceCommand request, CancellationToken ct)
    {
        var product = await _repo.GetByIdAsync(request.ProductId);
        product.UpdatePrice(request.NewPrice);
        await _repo.SaveAsync();
        await _eventBus.Publish(new ProductPriceUpdatedEvent(product.Id, request.NewPrice));
        return Unit.Value;
    }
}
```

### **4.2 Query (Read) Example**
**Input:**
```csharp
var query = new GetCustomerOrdersQuery { CustomerId = "cust-abc" };
```
**Handler (Query):**
```csharp
public class GetCustomerOrdersQueryHandler : IRequestHandler<GetCustomerOrdersQuery, List<OrderDto>>
{
    private readonly IOrderReadRepository _repo;
    public GetCustomerOrdersQueryHandler(IOrderReadRepository repo) => _repo = repo;

    public async Task<List<OrderDto>> Handle(GetCustomerOrdersQuery request, CancellationToken ct)
    {
        return await _repo.GetOrdersByCustomerAsync(request.CustomerId);
    }
}
```

---

## **5. Performance Considerations**
| **Scenario**               | **Optimization Strategy**                                                                 |
|----------------------------|-------------------------------------------------------------------------------------------|
| High-write volume          | Use **event sourcing** to batch writes.                                                    |
| Complex queries            | Denormalize the read model (e.g., materialized views).                                    |
| Real-time analytics        | Stream events to a **data warehouse** (e.g., Snowflake).                                  |
| Read-heavy workloads       | Cache frequently accessed data (e.g., **Redis**).                                          |

---

## **6. Related Patterns**
| **Pattern**               | **Description**                                                                             | **When to Use**                                                                       |
|---------------------------|---------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| **Event Sourcing**        | Stores state changes as immutable events.                                                  | When audit trails or complex state recovery are needed.                                |
| **Saga Pattern**          | Manages distributed transactions via compensating actions.                                 | Microservices with distributed writes.                                                 |
| **Repository Pattern**    | Abstraction over data access (shared for both read/write).                                  | Simplifying data access in layered architectures.                                     |
| **Event-Driven Architecture** | Decouples components via published events.                                               | Scalable, event-driven systems (e.g., IoT, financial systems).                         |
| **DDD (Domain-Driven Design)** | Focuses on domain models and bounded contexts.                                          | Complex business domains requiring rich modeling.                                     |

---

## **7. Anti-Patterns & Pitfalls**
1. **Over-Engineering CQRS**
   - Avoid CQRS if the system is simple (add complexity only when needed).

2. **Ignoring Eventual Consistency**
   - Users may see stale data. Use **optimistic locking** or **compensating transactions**.

3. **Tight Coupling Between Models**
   - Keep read/write models **loosely coupled**; avoid sharing entities directly.

4. **Poor Event Projection Strategy**
   - If projections are slow, use **incremental updates** or **batch processing**.

5. **Missing Error Handling**
   - Commands/queries should handle failures gracefully (e.g., retries, dead-letter queues).

---
## **8. Tools & Libraries**
| **Purpose**               | **Tools/Libraries**                                                                         |
|---------------------------|-------------------------------------------------------------------------------------------|
| Command/Query Bus         | MediatR (C#), Axon Framework, CommandBus (Java)                                           |
| Event Store               | EventStoreDB, Kafka, RabbitMQ                                                              |
| Projection Engine         | NEventStore (C#), Akka Streams, Flink                                                       |
| Caching                   | Redis, Memcached                                                                           |
| ORM/ODM                   | Entity Framework (SQL), MongoDB (.NET Driver), Dapper                                     |

---
## **9. When to Use CQRS**
✅ **Use CQRS when:**
- Your **reads and writes** have **different performance requirements**.
- You need **scalability** (e.g., high-throughput writes).
- Your system is **event-driven** (e.g., financial transactions).
- You require **auditability** (via event sourcing).

❌ **Avoid CQRS when:**
- The system is **small and simple** (CQRS adds complexity).
- Your team lacks expertise in **eventual consistency** or **asynchronous workflows**.
- **Low latency** is critical for both reads and writes (e.g., real-time trading).

---
**Reference:**
- *CQRS Docs* – [Microsoft Docs](https://docs.microsoft.com/en-us/azure/architecture/patterns/cqrs)
- *Event Sourcing* – [Greg Young’s Talks](https://www.youtube.com/watch?v=ZLv2Bk0_1Iw)
- *Domain-Driven Design* – *Eric Evans*