---
# **[Database Patterns] Reference Guide**

## **Overview**
Database patterns describe common architectures, strategies, and best practices for designing efficient, scalable, and maintainable database systems. These patterns address recurring challenges such as data normalization, performance optimization, concurrency control, and schema evolution. By leveraging proven patterns like **Single-Table Inheritance (STI)**, **Repository Pattern**, **CQRS**, or **Sharding**, developers can reduce redundancy, improve query performance, and ensure long-term flexibility. This guide categorizes key database patterns into structural, transactional, and scalability-focused approaches, providing implementation details, trade-offs, and real-world use cases.

---

## **1. Structural Patterns**
Structural patterns address schema design and data organization.

### **1.1 Single Table Inheritance (STI)**
**Purpose:** Model hierarchical data (e.g., parent-child relationships) in a single table for simplicity.

#### **Schema Reference**
| Column          | Type          | Description                                                                 |
|-----------------|---------------|-----------------------------------------------------------------------------|
| `id`            | `SERIAL`      | Primary key.                                                               |
| `type`          | `VARCHAR(50)` | Discriminates between inherited classes (e.g., `User`, `Admin`).           |
| `common_field`  | `TEXT`        | Shared attribute for all subclasses.                                       |
| `subclass_field`| `VARCHAR(255)`| Column populated only if `type = Subclass` (NULL otherwise).                 |

#### **Query Examples**
```sql
-- Fetch all records
SELECT * FROM entities WHERE type = 'User';

-- Conditional filtering
SELECT * FROM entities WHERE type = 'Admin' AND status = 'active';
```

**Trade-offs:**
✅ **Pros:** Simple queries, no joins.
❌ **Cons:** Data redundancy, scaling constraints with large datasets.

---

### **1.2 Repository Pattern**
**Purpose:** Abstract database access with a service layer to decouple business logic from persistence.

#### **Schema Reference**
*(No schema changes; focuses on application code.)*
- **Interface:** `IRepository<T>`
  ```csharp
  public interface IRepository<T> where T : class
  {
      Task<IEnumerable<T>> GetAllAsync();
      Task<T> GetByIdAsync(int id);
      Task AddAsync(T entity);
      Task UpdateAsync(T entity);
  }
  ```

#### **Implementation (EF Core Example)**
```csharp
public class UserRepository : IRepository<User>
{
    private readonly ApplicationDbContext _context;

    public UserRepository(ApplicationDbContext context) => _context = context;

    public async Task<IEnumerable<User>> GetAllAsync()
        => await _context.Users.ToListAsync();
}
```

**Trade-offs:**
✅ **Pros:** Clean separation of concerns, testability.
❌ **Cons:** Boilerplate code, Indirection overhead.

---

## **2. Transactional Patterns**
Transactional patterns manage data consistency and concurrency.

### **2.1 Saga Pattern**
**Purpose:** Handle distributed transactions by breaking them into local transactions (sagas).

#### **Schema Reference**
*(No schema; relies on microservices event logs.)*
- **Example Tables (Service A):**
  ```sql
  CREATE TABLE Orders (
      OrderId INT PRIMARY KEY,
      Status VARCHAR(20) -- "Created", "Processing", "Completed"
  );
  ```

#### **Query Example (Saga Step)**
```sql
-- "Order Created" event -> "Inventory Deduct" saga step
UPDATE Inventory
SET Quantity = Quantity - 1
WHERE ProductId = 123
AND Status = 'Available';
```

**Trade-offs:**
✅ **Pros:** Works with eventual consistency.
❌ **Cons:** Complex error handling, debugging overhead.

---

### **2.2 Optimistic Concurrency Control**
**Purpose:** Prevent lost updates by validating a version column.

#### **Schema Reference**
| Column       | Type    | Description                          |
|--------------|---------|--------------------------------------|
| `id`         | `INT`   | Primary key.                         |
| `version`    | `INT`   | Row version (auto-incremented).      |

#### **Query Example (EF Core)**
```csharp
// Attempt update with version check
await _context.SaveChangesAsync(); // Throws DbUpdateConcurrencyException if version mismatch.
```

**Trade-offs:**
✅ **Pros:** No locks, simple to implement.
❌ **Cons:** Risk of phantom reads, retries needed.

---

## **3. Scalability Patterns**
Patterns for horizontal scaling and performance.

### **3.1 Sharding**
**Purpose:** Split data across multiple database instances (shards) based on keys.

#### **Schema Reference**
- **Shard Key Example:**
  ```sql
  -- User table partitioned by country_code
  CREATE TABLE Users (
      user_id INT,
      country_code VARCHAR(2) NOT NULL,
      -- other columns
      PRIMARY KEY (country_code, user_id)
  );
  ```

#### **Query Example (Shard Routing)**
*(Application logic routes queries to the correct shard.)*
```python
# Pseudo-code: Route to 'US' shard
def get_user_shard(user: User) -> str:
    return f"shard_{user.country_code}"
```

**Trade-offs:**
✅ **Pros:** Horizontal scaling, improved query performance.
❌ **Cons:** Complexity in cross-shard joins, eventual consistency for joins.

---

### **3.2 Read Replicas**
**Purpose:** Offload read queries to replica instances.

#### **Schema Reference**
*(Replicas mirror the primary schema.)*

#### **Query Example (Route Reads)**
```sql
-- Primary write
INSERT INTO Orders (OrderId, Status) VALUES (1, 'Created');

-- Read from replica (application logic)
SELECT * FROM Orders WHERE OrderId = 1;
```

**Trade-offs:**
✅ **Pros:** Scales reads, reduces primary load.
❌ **Cons:** Stale reads (unless async replication fixed).

---

## **4. Query Patterns**

### **4.1 Materialized Views**
**Purpose:** Pre-compute aggregation results for faster reporting.

#### **Schema Reference**
```sql
CREATE MATERIALIZED VIEW SalesSummary AS
SELECT
    product_id,
    SUM(quantity) AS total_sold,
    MAX(order_date) AS last_sale_date
FROM orders
GROUP BY product_id;
```

#### **Refresh Command**
```sql
REFRESH MATERIALIZED VIEW CONCURRENTLY SalesSummary;
```

**Trade-offs:**
✅ **Pros:** Blazing-fast aggregations.
❌ **Cons:** Storage overhead, manual refreshes.

---

## **5. Related Patterns**
- **[CQRS] (Command Query Responsibility Segregation):** Separates reads/writes into distinct models.
- **[Event Sourcing]:** Stores state changes as immutable events (complements Saga).
- **[Database Per Service]:** Isolates schemas per microservice for autonomy.
- **[Denormalization]:** Trade data consistency for read performance (e.g., caches).

---

## **Implementation Checklist**
1. **Design Schema First:** Use ER diagrams for structural patterns.
2. **Validate Concurrency:** Test optimistic locking in high-contention scenarios.
3. **Monitor Shards:** Use tools like Vitess or Citus for distributed DBs.
4. **Optimize Queries:** Add indexes; avoid `SELECT *`.
5. **Document Sagas:** Log event flows for debugging.

---
**Key Takeaway:** Choose patterns based on trade-offs (e.g., STI for simplicity vs. Sharding for scale). Always validate with benchmarks.