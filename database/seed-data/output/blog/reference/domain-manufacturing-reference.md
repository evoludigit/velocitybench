# **[Pattern] Manufacturing Domain Patterns – Reference Guide**

---

## **1. Overview**
Manufacturing Domain Patterns (MDPs) are reusable, domain-specific solutions that standardize how manufacturing systems model, process, and optimize workflows. These patterns address core challenges in **order fulfillment, production planning, quality control, supply chain coordination, and asset management** by encapsulating best practices into modular, reusable components. MDPs bridge the gap between **system design** and **domain semantics**, enabling:
- **Consistent data models** for manufacturing processes (e.g., Bill of Materials, Work Orders).
- **Interoperability** between ERP, MES, SCADA, and IoT systems.
- **Scalability** for complex production environments (e.g., lean manufacturing, agile production).
- **Adaptability** to industry-specific regulations (e.g., FDA for pharma, ISO 9001 for automotive).

This guide covers **implementation details**, **schema references**, **query examples**, and **related patterns** to help architects and developers apply MDPs effectively.

---

## **2. Schema Reference**
Below are key **Manufacturing Domain Patterns** and their core schema elements. Tables use **Entity-Relationship (ER) diagrams** for clarity.

### **2.1 Core Manufacturing Patterns**
| **Pattern**               | **Primary Entity**       | **Key Attributes**                                                                 | **Relationships**                                                                                     | **Example Use Case**                                                                                     |
|---------------------------|--------------------------|-------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|
| **Bill of Materials (BOM)** | `Product`, `Component`   | - `product_id` (UUID) <br>- `description`, `quantity`, `unit` <br>- `version` (e.g., v1.2) | - `Product` ➔ `Component` (1:N, hierarchical) <br>- `Component` ➔ `Supplier` (N:1)                      | Defining assembly requirements for an "Engine Assembly" (e.g., 2x pistons, 1x crankshaft).            |
| **Work Order (WO)**       | `WorkOrder`              | - `wo_id` (UUID) <br>- `status` (e.g., "Planned", "In-Process", "Complete") <br>- `priority` (1-5) | - `WorkOrder` ➔ `Operation` (1:N) <br>- `Operation` ➔ `Resource` (e.g., machine, worker) <br>- `WorkOrder` ➔ `CustomerOrder` (1:1) | Scheduling production of "Widget Batch #42" on Line 3 at 09:00.                                       |
| **Production Line**       | `ProductionLine`         | - `line_id` <br>- `capacity` (units/hour) <br>- `location` (e.g., "Floor A, Bay 5") | - `ProductionLine` ➔ `WorkOrder` (assigns WOs) <br>- `ProductionLine` ➔ `Machine` (N:1)                  | Assigning a "Paint Line" to handle "Car Body WOs" with a capacity of 50/hour.                             |
| **Quality Control (QC)**  | `Inspection`, `Defect`   | - `inspection_id` <br>- `criteria` (e.g., "Tolerance ±0.01mm") <br>- `pass_fail` <br>- `defect_code` (e.g., "D001: Crack") | - `WorkOrder` ➔ `Inspection` (1:N) <br>- `Inspection` ➔ `Defect` (0:N)                               | Recording defects in "Gear Component Lot #123" (e.g., 3x "D001" defects found).                     |
| **Asset Maintenance**     | `Asset`, `MaintenanceLog`| - `asset_id` (e.g., machine ID) <br>- `asset_type` (e.g., "CNC Mill") <br>- `status` (e.g., "Operational") | - `Asset` ➔ `MaintenanceLog` (1:N) <br>- `MaintenanceLog` ➔ `WorkOrder` (N:1, for scheduled maintenance) | Logging a routine check for "CNC-456" on 2024-05-15.                                                  |
| **Supplier Management**   | `Supplier`, `PO`         | - `supplier_id` <br>- `lead_time` (days) <br>- `reliability_score` (0-100)          | - `Product` ➔ `Supplier` (N:1, via BOM) <br>- `CustomerOrder` ➔ `PO` (1:N)                            | Ordering 500 "Raw Material X" from "Supplier Y" with a lead time of 7 days.                          |
| **Inventory**             | `InventoryItem`, `Batch` | - `item_id` <br>- `quantity` <br>- `location` (e.g., "Warehouse B, Shelf 3") <br>- `batch_number` | - `InventoryItem` ➔ `Batch` (1:N) <br>- `Batch` ➔ `ExpiryDate` (for perishables)                  | Tracking "Steel Plate Lot #789" with 100 units in "Warehouse A".                                       |
| **Customer Order**        | `CustomerOrder`          | - `order_id` <br>- `customer_id` <br>- `due_date` <br>- `fulfillment_status` (e.g., "Shipped") | - `CustomerOrder` ➔ `WorkOrder` (1:N) <br>- `CustomerOrder` ➔ `Payment` (1:1)                          | Processing "Order #2024-0542" for 100 "Product Z" with a due date of 2024-06-01.                       |

---

### **2.2 Example Relationships (ER Diagram Snippet)**
```
CustomerOrder (1)───┬───(N) WorkOrder
                     │
                     └───(1)───(N) Operation
                              │
                              └───(N) Resource (Machine/Worker)
                              │
                              └───(1)───(N) InventoryItem (Consumed)
                              │
                              └───(N) Inspection (QC)
```

---

## **3. Implementation Details**
### **3.1 Core Principles**
1. **Modularity**:
   - Decompose manufacturing workflows into **reusable patterns** (e.g., BOM, WO) to avoid redundancy.
   - Example: Share a `Component` entity across BOMs, Inventory, and Supplier patterns.

2. **State Management**:
   - Use **finite state machines (FSM)** for entities like `WorkOrder` (e.g., "Planned" → "In-Process" → "Complete").
   - Example:
     ```json
     {
       "status": "In-Process",
       "transition": {
         "from": "Planned",
         "timestamp": "2024-05-20T14:30:00Z",
         "actor": "Machine-123"
       }
     }
     ```

3. **Versioning**:
   - Track **BOM versions** and **production recipes** to support retroactive changes.
   - Example:
     ```sql
     ALTER TABLE product ADD COLUMN bom_version VARCHAR(10) DEFAULT '1.0';
     ```

4. **Event-Driven Architecture**:
   - Trigger actions via events (e.g., `WO_Started`, `QC_Failed`).
   - Example (Kafka topic):
     ```json
     {
       "event": "WO_Started",
       "wo_id": "WO-789",
       "timestamp": "2024-05-20T15:00:00Z",
       "details": {
         "operation": "Assembly",
         "resource": "Line-4"
       }
     }
     ```

5. **Performance Considerations**:
   - **Index critical fields** (e.g., `work_order.status`, `inventory.location`).
   - Use **materialized views** for frequent queries (e.g., "Available inventory by supplier").
   - Example:
     ```sql
     CREATE INDEX idx_wo_status ON work_order(status);
     ```

---

### **3.2 Best Practices**
| **Best Practice**               | **Implementation Guidance**                                                                                                                                 |
|----------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Standardize Naming Conventions** | Use **kebab-case** for entities (`production_line`), **PascalCase** for enums (`WorkOrderStatus`).                                                      |
| **Immutable Logs**               | Store `MaintenanceLog` entries as immutable records with only `created_at` timestamps.                                                                    |
| **Graceful Degradation**         | Design for partial failures (e.g., if QC system fails, mark inspection as `pending`).                                                                   |
| **Audit Trails**                 | Track changes via `last_modified_by` and `change_timestamp` fields.                                                                                   |
| **Unit of Work**                 | Batch-related operations (e.g., update `InventoryItem` and `WorkOrder` in a single transaction).                                                        |
| **Localization**                 | Support multi-language `Product.description` fields for global supply chains.                                                                          |
| **Compliance Hooks**             | Embed regulatory checks (e.g., FDA 21 CFR Part 11) in patterns (e.g., `Inspection.cgmp_compliance`).                                                      |

---

### **3.3 Common Pitfalls & Mitigations**
| **Pitfall**                          | **Mitigation**                                                                                                                                   |
|---------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|
| **Overly Complex BOMs**               | Enforce a **maximum depth** (e.g., 5 levels) and use **modular sub-assemblies** to simplify hierarchies.                                       |
| **Unstable Work Order Priorities**    | Implement a **dynamic priority algorithm** (e.g., weighted by `due_date` and `profit_margin`).                                                |
| **Poor Inventory Visibility**         | Use **real-time sensors** (IoT) to auto-update `inventory.quantity` via events.                                                                |
| **Supplier Risk Not Tracked**         | Add `supplier_risk_score` (0-100) and alert on thresholds (e.g., <60).                                                                          |
| **Lack of Disaster Recovery**         | Backup `CustomerOrder` and `WorkOrder` data hourly with **point-in-time recovery**.                                                              |
| **Silos Between Systems**             | Use **API gateways** (e.g., Kafka, gRPC) to decouple MES, ERP, and SCADA systems.                                                              |
| **Ignoring Asset Lifecycle**         | Model assets with `asset_lifecycle_stage` (e.g., "New", "Worn", "Scrapped") and trigger maintenance based on age.                              |

---

## **4. Query Examples**
### **4.1 SQL Queries**
#### **Find Overdue Work Orders**
```sql
SELECT wo.*, co.due_date
FROM work_order wo
JOIN customer_order co ON wo.order_id = co.order_id
WHERE wo.status = 'In-Process'
  AND co.due_date < CURRENT_DATE
ORDER BY co.due_date ASC;
```

#### **Calculate Inventory Turnover Rate**
```sql
SELECT
  i.product_id,
  p.description,
  SUM(i.quantity) AS total_inventory,
  SUM(i.quantity * (SELECT AVG(price) FROM product WHERE product.id = i.product_id)) AS inventory_value,
  (SUM(i.quantity) / (SELECT SUM(quantity) FROM inventory_history WHERE product_id = i.product_id)) AS turnover_rate
FROM inventory i
JOIN product p ON i.product_id = p.id
GROUP BY i.product_id;
```

#### **List Defective Components by Supplier**
```sql
SELECT
  d.defect_code,
  d.quantity,
  s.supplier_name,
  s.reliability_score
FROM defect d
JOIN work_order wo ON d.wo_id = wo.id
JOIN supplier s ON wo.supplier_id = s.id
GROUP BY d.defect_code, s.supplier_name
ORDER BY s.reliability_score ASC;
```

---

### **4.2 GraphQL Queries**
#### **Fetch Work Order with Nested Operations**
```graphql
query GetWorkOrder($woId: ID!) {
  workOrder(id: $woId) {
    id
    status
    operations {
      id
      description
      resource {
        type
        id
      }
    }
    relatedCustomerOrder {
      orderId
      dueDate
    }
  }
}
```

#### **Filter Inventory by Location and Low Stock**
```graphql
query GetLowStockInventory($location: String!) {
  inventory(filter: { location: { eq: $location }, quantity: { lt: 50 } }) {
    productId
    quantity
    product {
      description
    }
  }
}
```

---

### **4.3 NoSQL (MongoDB) Queries**
#### **Find All Maintenance Logs for a Critical Asset**
```javascript
db.maintenanceLogs.find({
  asset: {
    $elemMatch: {
      id: "MACHINE-456",
      type: "CNC Mill",
      critical: true
    }
  }
}).sort({ timestamp: -1 });
```

#### **Aggregate QC Inspection Trends**
```javascript
db.inspections.aggregate([
  { $match: { product: "Gear Component" } },
  { $group: {
      _id: "$inspectionDate",
      passRate: { $avg: { $cond: ["$pass_fail", 1, 0] } },
      defectCount: { $sum: 1 }
    }
  }},
  { $sort: { "_id": -1 } }
]);
```

---

## **5. Related Patterns**
| **Pattern**                          | **Description**                                                                                                                                 | **When to Use**                                                                                          |
|---------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| **[Event Sourcing](https://martinfowler.com/eaaT.html)** | Capture state changes as a sequence of events for auditability.                                                                               | When **full audit trails** are required (e.g., FDA compliance, financial audits).                      |
| **[CQRS](https://martinfowler.com/bliki/CQRS.html)**     | Separate read and write models for scalability.                                                                                              | For **high-throughput systems** (e.g., real-time production monitoring dashboards).                    |
| **[Saga Pattern](https://microservices.io/patterns/data/saga.html)** | Manage distributed transactions via compensatory actions.                                                                                     | When **microservices** coordinate complex workflows (e.g., order fulfillment across 3 services).      |
| **[Bulkhead Pattern](https://martinfowler.com/bliki/BulkheadPattern.html)** | Isolate failures in resource-intensive operations.                                                                                             | To prevent **cascading failures** in batch processing (e.g., inventory updates).                        |
| **[Strangler Fig Pattern](https://martinfowler.com/bliki/StranglerFigApplication.html)** | Incrementally replace legacy systems with MDPs.                                                                                              | When **migrating from monolithic ERP** to modular manufacturing systems.                                |
| **[Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html)** | Abstract data access for domain entities.                                                                                                   | To **decouple business logic** from database operations (e.g., `WorkOrderRepository`).                  |
| **[Data Mesh](https://tmcw.com/data-mesh.html)**         | Distribute data ownership to domain teams.                                                                                                   | For **large-scale manufacturing ecosystems** with decentralized data (e.g., plants, suppliers).       |
| **[Kanban System](https://www.atlassian.com/agile/kanban)** | Visualize workflow bottlenecks.                                                                                                               | To **optimize production lines** with real-time WIP (Work In Progress) tracking.                        |

---

## **6. Further Reading**
- **[Enterprise Integration Patterns](https://www.enterpriseintegrationpatterns.com/)** (Hoare, et al.) – Core patterns for manufacturing systems.
- **[Domain-Driven Design](https://domainlanguage.com/ddd/)** (Eric Evans) – Foundations for modeling manufacturing domains.
- **[IIoT Security Frameworks](https://www.nist.gov/itl/applied-cybersecurity-and-infrastructure-resilience/iiot-security-framework)** – For securing connected assets.
- **[ISO 8000-EX](https://www.iso.org/standard/75191.html)** – Standard for structured data in manufacturing.
- **[OPC UA](https://opcfoundation.org/)** – Industry standard for machine communication.

---
**Last Updated:** 2024-05-20
**Version:** 1.2