---
# **[Pattern] Anti-Corruption Layer Reference Guide**

---

## **Overview**
The **Anti-Corruption Layer (ACL)** is a **pattern** that isolates a **domain model** from an underlying **legacy system** to prevent domain logic from being polluted by legacy system constraints, complexities, or anti-patterns. It acts as a **translator** and **adapter**, ensuring that domain entities and business rules remain clean while still integrating with legacy systems (e.g., databases, APIs, or monoliths).

The ACL is particularly useful when:
- Refactoring or migrating away from a legacy system gradually.
- Domain logic must remain decoupled from external dependencies.
- A new, modern system interacts with an outdated backend.

By using the **ACL**, you abstract away legacy-specific details (e.g., ORM quirks, SQL patterns, or transaction semantics) while exposing a **simplified, domain-aligned interface**.

---

## **Key Concepts**
| Concept               | Description                                                                 |
|----------------------|-----------------------------------------------------------------------------|
| **Domain Model**     | Represents business logic and entities in a clean, object-oriented way.  |
| **Legacy System**    | Existing system with outdated architecture, anti-patterns, or rigid APIs. |
| **Adapter Layer**    | Converts between domain objects and legacy system representations.      |
| **Facade (Optional)**| Simplifies the interaction between the ACL and the legacy system.         |
| **Query Mappings**   | Defines how legacy queries translate into domain-friendly operations.       |

---

## **Schema Reference**
The ACL follows a **layered architecture** with distinct responsibilities:

| Layer            | Purpose                                                                 | Example Implementation (Pseudocode)                          |
|------------------|--------------------------------------------------------------------------|----------------------------------------------------------------|
| **Domain Layer** | Pure business logic, no external dependencies.                              | `class Order { void process(); }`                           |
| **Anti-Corruption Layer** | Adapts legacy data structures to/from domain models.                    | `class OrderAdapter { Order toDomain(LegacyOrder); LegacyOrder toLegacy(Order); }` |
| **Legacy Layer** | Directly interacts with the legacy system (e.g., SQL, REST calls).      | `class LegacyOrderRepo { LegacyOrder findById(int id); }`    |
| **Persistence Layer** | Handles storage/retieval (optional; if using a new DB alongside legacy). | `class DomainOrderRepo { Order save(Order); }`               |

### **Core Interface Example**
```java
// Domain Model
interface Order {
    String getId();
    void setStatus(String status);
}

// Legacy Model (unclean, legacy-specific)
class LegacyOrder {
    String legacyId;
    String rawStatus; // e.g., "PENDING", "COMPLETED"
}

// Adapter translates between them
class OrderAdapter implements Order {
    private LegacyOrder legacyOrder;

    public OrderAdapter(LegacyOrder legacyOrder) {
        this.legacyOrder = legacyOrder;
    }

    @Override public String getId() { return legacyOrder.legacyId; }

    @Override public void setStatus(String status) {
        legacyOrder.rawStatus = convertToLegacyStatus(status);
    }

    private String convertToLegacyStatus(String domainStatus) {
        // Example: Map "SHIPPED" (domain) → "PROCESSING" (legacy)
        return legacyStatusMap.get(domainStatus);
    }
}
```

---

## **Implementation Best Practices**
### **1. Define a Clear Boundary**
- **Do not** expose legacy system logic (e.g., SQL joins, batch processing) in the domain layer.
- **Do** hide legacy complexity behind the ACL.

### **2. Use Mapping Strategies**
- **Manual Mapping**: Explicit adapter methods (as shown above).
- **Auto-Mapping (ORM Tools)**: Use tools like **MapStruct** (Java) or **AutoMapper** (.NET) for boilerplate reduction.
- **Repository Pattern**: Implement repositories to abstract legacy queries.

### **3. Handle Idempotency & Transactions**
- Legacy systems may have **idiosyncratic transaction behaviors** (e.g., timeouts, retries).
- **Use compensating transactions** or **event sourcing** where needed.

### **4. Test Thoroughly**
- **Unit Tests**: Verify adapter conversions (e.g., `OrderAdapter.toDomain()`).
- **Integration Tests**: Test ACL interactions with the legacy system under stress (e.g., timeouts).

### **5. Avoid Tight Coupling**
- **Dependency Injection (DI)**: Inject the ACL adapter into domain services.
- **Avoid Reflection**: Prefer compile-time safety over dynamic mapping.

---

## **Query Examples**
### **Example 1: Fetching an Order**
**Domain Query:**
```java
Order order = orderService.findById("ORD123");
```

**Legacy Database Schema:**
```sql
CREATE TABLE legacy_orders (
    id VARCHAR(20) PRIMARY KEY,
    customer_id VARCHAR(50),
    status_code INT  -- 1=Pending, 2=Shipped
);
```

**ACL Implementation:**
```java
public Order findById(String orderId) {
    LegacyOrder legacyOrder = legacyRepo.findById(orderId);
    if (legacyOrder == null) return null;
    return new OrderAdapter(legacyOrder);
}
```

### **Example 2: Updating an Order Status**
**Domain Call:**
```java
orderService.updateStatus(orderId, "SHIPPED");
```

**Legacy System Requirement:**
- Legacy expects `status_code = 2` for "SHIPPED."
- ACL maps `"SHIPPED" → 2`.

**ACL Code:**
```java
public void updateStatus(String orderId, String domainStatus) {
    LegacyOrder legacyOrder = legacyRepo.findById(orderId);
    legacyOrder.status_code = mapStatusToLegacy(domainStatus);
    legacyRepo.update(legacyOrder);
}

private int mapStatusToLegacy(String domainStatus) {
    return switch (domainStatus) {
        case "SHIPPED" -> 2;
        case "PENDING" -> 1;
        default -> throw new IllegalArgumentException("Unsupported status");
    };
}
```

### **Example 3: Querying Multiple Orders (Pagination)**
**Domain Request:**
```java
List<Order> orders = orderService.getOrdersByCustomer("CUST456", 0, 10);
```

**Legacy SQL:**
```sql
SELECT * FROM legacy_orders
WHERE customer_id = 'CUST456'
LIMIT 10 OFFSET 0;
```

**ACL Implementation:**
```java
public List<Order> getOrdersByCustomer(String customerId, int offset, int limit) {
    return legacyRepo.queryForCustomer(customerId, offset, limit)
        .stream()
        .map(OrderAdapter::new)
        .collect(Collectors.toList());
}
```

---

## **Error Handling & Edge Cases**
| Scenario                     | ACL Strategy                                                                 |
|------------------------------|------------------------------------------------------------------------------|
| **Null Fields in Legacy Data** | Use `Optional` or default values (e.g., `legacyOrder.getStatus() ?: "PENDING"`). |
| **Legacy Data Mismatch**      | Fail fast with `IllegalArgumentException` or log warnings.                  |
| **Transaction Rollbacks**     | Implement compensating actions (e.g., revert legacy status changes).        |
| **Legacy API Rate Limits**    | Cache responses or use a queue (e.g., Kafka) for deferred processing.       |

---
## **Performance Considerations**
- **Batching**: Fetch multiple legacy records in one call to reduce latency.
- **Caching**: Cache frequently accessed legacy entities (e.g., Redis).
- **Async Processing**: Use event-driven patterns (e.g., **CQRS**) for write-heavy workloads.

---

## **Related Patterns**
| Pattern                  | Purpose                                                                 | When to Use                                      |
|--------------------------|--------------------------------------------------------------------------|--------------------------------------------------|
| **Repository Pattern**   | Abstracts data access for domain objects.                                | When the ACL needs to query/update legacy data. |
| **Adapter Pattern**      | Converts interfaces between incompatible systems.                         | Core of the ACL; translates domain ↔ legacy.     |
| **Strategy Pattern**     | Defines interchangeable algorithms (e.g., for legacy-specific logic).   | When legacy interactions vary by use case.       |
| **CQRS**                 | Separates read/write concerns for scalability.                           | For high-traffic systems with legacy constraints.|
| **Event Sourcing**       | Audits changes as a sequence of events.                                  | When legacy systems lack consistent transactions.|
| **Factory Pattern**      | Creates domain objects from legacy data.                                 | When mapping complex legacy structures.          |

---

## **Anti-Patterns to Avoid**
| ❌ **Anti-Pattern**              | **Why It’s Bad**                                                                 | **ACL Solution**                                  |
|-----------------------------------|----------------------------------------------------------------------------------|--------------------------------------------------|
| **"Direct Legacy Calls"**         | Domain logic becomes tangled with legacy quirks.                               | Always route through the ACL.                    |
| **"Manual SQL in Domain Layer"**  | Violates separation of concerns.                                                | Use the ACL to abstract SQL logic.                |
| **"Tight Coupling to Legacy IDs"**| Makes refactoring harder (e.g., `Order.new(String legacyId)`).                | Map legacy IDs to domain-friendly identifiers.    |
| **"Ignoring Errors"**             | Silent failures corrupt state.                                                  | Validate/convert data strictly in the ACL.       |

---
## **Tools & Libraries**
| Tool/Library               | Purpose                                                                       |
|----------------------------|-------------------------------------------------------------------------------|
| **MapStruct**              | Auto-generates mapping between domain ↔ legacy objects.                     |
| **JOOQ**                   | SQL query builder for cleaner legacy interactions.                           |
| **Spring Data JDBC**       | Type-safe JDBC access for legacy databases.                                  |
| **Apache Kafka**           | Decouples ACL from legacy system for async processing.                       |
| **Mockito**                | Unit test ACL adapters without legacy dependencies.                          |

---
## **Migration Strategy**
1. **Start Small**: Isolate one critical domain entity (e.g., `Order`).
2. **Phase Out Legacy Calls**: Gradually replace direct legacy calls with ACL-mediated ones.
3. **Deprecate Legacy APIs**: Once the ACL is stable, mark legacy APIs as deprecated.
4. **Full Cutover**: Once the domain layer is self-sufficient, phase out the legacy system entirely.

---
## **Example: Full Workflow**
```mermaid
graph TD
    A[Domain Service] -->|findById("ORD123")| B[ACL Adapter]
    B -->|legacyRepo.findById()| C[Legacy Database]
    C -->|LegacyOrder| B
    B -->|new OrderAdapter()| D[Domain Order]
    D --> A
```

---
## **Summary Checklist**
- [ ] **Abstract legacy details** behind the ACL.
- [ ] **Map IDs/statuses** bidirectionally (domain ↔ legacy).
- [ ] **Test edge cases** (nulls, invalid data).
- [ ] **Avoid mixing** domain logic with legacy code.
- [ ] **Use caching** for performance-critical queries.
- [ ] **Plan incremental migration** to reduce risk.

---
**References:**
- *Domain-Driven Design* by Eric Evans (Blue Book).
- [Martin Fowler: Anti-Corruption Layer](https://martinfowler.com/bliki/AntiCorruptionLayer.html).
- *Clean Architecture* by Robert C. Martin.