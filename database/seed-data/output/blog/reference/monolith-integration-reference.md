# **[Pattern] Monolith Integration Reference Guide**

---

## **Overview**
The **Monolith Integration** pattern describes how to aggregate and manage data from multiple microservices or systems by consolidating them into a single database or monolithic backend service. This approach simplifies data access, reduces distributed transaction complexity, and ensures consistency by treating external systems as "data sources" rather than separate services. It is commonly used in:
- **Legacy system modernizations** where replacing individual systems is impractical.
- **API gateways or proxy services** that normalize and route requests to underlying services.
- **Data warehousing or analytics** where centralized data is required for reporting.

Key trade-offs include **reduced scalability** of individual components and **increased coupling** between systems, but it offers strong consistency, simplified data modeling, and easier transaction management.

---

## **Implementation Details**

### **Core Concepts**
| Concept               | Description                                                                                                                                                                                                 |
|-----------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Monolithic Backend** | A single service or layer that aggregates data from multiple external systems into a unified schema. Often acts as a facade for downstream consumers.                          |
| **Data Sync Strategy** | Determines how data is refreshed (e.g., **ETL**, **CDC**, **API polling**, or **event-driven**).                                                                                         |
| **Schema Normalization** | External schemas are mapped to a unified internal schema (e.g., flattening nested JSON or transforming relational data).                                                                           |
| **Idempotency**       | Ensures repeated sync operations (e.g., due to failures) do not cause duplicates or inconsistencies.                                                                                                    |
| **Conflict Resolution** | Defines rules for handling discrepancies (e.g., last-write-wins, manual review, or application-specific logic).                                                                                    |
| **Rate Limiting**     | Prevents external API abuse; critical when polling multiple sources.                                                                                                                                   |
| **Caching Layer**     | Improves performance by storing frequently accessed consolidated data (e.g., Redis, CDN).                                                                                                            |
| **Audit Trail**       | Logs sync operations, changes, and errors for traceability and debugging.                                                                                                                               |

---

### **Data Flow**
1. **External Systems** (microservices, APIs, databases) expose data via REST, gRPC, or direct DB access.
2. **Monolith Integration Layer** fetches, transforms, and stores data in a unified schema.
3. **Consumers** (apps, analytics tools) query the monolith for consolidated data.

```
┌─────────────┐    ┌─────────────┐    ┌─────────────────┐    ┌─────────────┐
│             │    │             │    │                 │    │             │
│ External    ├────▶ Integration ├────▶ Unified Schema  ├────▶ Consumer  │
│ Systems     │    │ (Monolith)   │    │ (Database/Cache)│    │             │
│             │    │             │    │                 │    │             │
└─────────────┘    └─────────────┘    └─────────────────┘    └─────────────┘
```

---

## **Schema Reference**
Below is a **normalized schema template** for a common use case: **e-commerce order processing** with external payment, inventory, and customer systems.

| Table/Entity          | Fields (Source → Dest)                          | Notes                                                                                     |
|-----------------------|-------------------------------------------------|-------------------------------------------------------------------------------------------|
| **Customers**         | `customer_id (ext:payment_system)`              | Merge with `users` (from CRM) using a UUID join key.                                      |
|                       | `name` (ext), `email` (ext)                     | Normalize formats (e.g., trim whitespace).                                              |
|                       | `created_at` (ext), `last_updated` (local)     | Track metadata for sync reconciliation.                                                 |
| **Orders**            | `order_id (ext:inventory_system)`               | Use composite keys if primary IDs differ.                                               |
|                       | `status` (ext), `order_total` (ext)            | Map external enums (e.g., `"pending" → "PENDING"`) to a standardized schema.           |
|                       | `customer_id` (FK → Customers)                  | Resolve customer records before creating orders.                                         |
|                       | `payment_status` (ext), `payment_id` (ext)     | Store raw/transformed data for auditability.                                            |
| **Order Items**       | `order_id`, `product_id (ext:inventory)`        | Denormalize where possible (e.g., include `product_name`).                              |
|                       | `quantity`, `price_at_order`                    | Use timestamps to avoid floating-point discrepancies.                                   |
| **Inventory**         | `product_id (ext)`, `stock_level`               | Sync incrementally (e.g., via CDC) to track real-time changes.                          |

---

## **Query Examples**
### **1. Fetching Consolidated Orders**
```sql
-- Combine orders with customer and payment details
SELECT
    o.order_id,
    o.order_total,
    o.status,
    c.name AS customer_name,
    p.payment_method,
    p.transaction_date
FROM
    Orders o
JOIN
    Customers c ON o.customer_id = c.customer_id
JOIN
    Payments p ON o.payment_id = p.payment_id
WHERE
    o.status = 'COMPLETED'
    AND o.created_at > '2024-01-01';
```

### **2. Incremental Sync (CDC-Style)**
```sql
-- Capture only new/updated order items since last sync
WITH changes AS (
    SELECT
        order_id,
        product_id,
        quantity,
        ROW_NUMBER() OVER (PARTITION BY order_id, product_id ORDER BY last_updated DESC) AS rn
    FROM
        OrderItems
    WHERE
        last_updated > (SELECT MAX(sync_time) FROM sync_log WHERE source = 'inventory_system')
)
INSERT INTO Consolidated_OrderItems (
    order_id,
    product_id,
    quantity
)
SELECT
    order_id,
    product_id,
    quantity
FROM
    changes
WHERE
    rn = 1;
```

### **3. Conflict Resolution (Last-Write-Wins)**
```sql
-- Overwrite local record if external timestamp is newer
INSERT INTO Customers (customer_id, name, email, last_updated)
SELECT
    customer_id,
    name,
    email,
    external_updated
FROM
    ExternalCustomers
ON CONFLICT (customer_id)
DO UPDATE SET
    name = EXCLUDED.name,
    email = EXCLUDED.email,
    last_updated = EXCLUDED.external_updated
WHERE
    ExternalCustomers.last_updated > Customers.last_updated;
```

### **4. API Polling (Rate-Limited)**
```python
# Pseudocode for batch polling with retries
def poll_external_system(max_retries=3, batch_size=100):
    retry_count = 0
    while retry_count < max_retries:
        try:
            response = requests.get(
                f"https://api.external.com/orders?limit={batch_size}",
                headers={"Authorization": "Bearer <token>"}
            )
            response.raise_for_status()
            process_batch(response.json())
            return
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:  # Rate limited
                sleep(2 ** retry_count)  # Exponential backoff
                retry_count += 1
            else:
                raise
```

---

## **Implementation Steps**
1. **Assess External Systems**
   - Document APIs/databases, schemas, and access constraints (e.g., CORS, auth).
   - Identify critical fields (e.g., `order_id`, `timestamp`) for reconciliation.

2. **Design Unified Schema**
   - Use **denormalization** for performance where applicable.
   - Create **audit tables** to track sync history (e.g., `sync_log`).

3. **Choose Sync Strategy**
   - **ETL (Batch):** Use tools like Apache NiFi or custom scripts (best for large datasets).
   - **CDC (Streaming):** Leverage Debezium or Kafka Connect for real-time changes.
   - **Polling:** Implement for systems without event streams (e.g., REST APIs).

4. **Build Synchronization Logic**
   - Implement **idempotency keys** (e.g., `(source_id, sync_timestamp)`).
   - Add **circuit breakers** to handle upstream failures gracefully.

5. **Test Edge Cases**
   - Simulate API downtime, data conflicts, and schema drifts.
   - Validate query performance with real-world data volumes.

6. **Deploy and Monitor**
   - Set up alerts for sync failures (e.g., Prometheus + Alertmanager).
   - Use feature flags to enable the monolith layer incrementally.

---

## **Schema Migration Example**
### **Before (External Systems)**
| **Payment System**       | **Inventory System**         |
|--------------------------|------------------------------|
| `payment_id` (UUID)      | `product_id` (SKU string)    |
| `customer_id` (int)      | `order_id` (UUID)            |
| `amount` (decimal)       | `quantity` (int)             |

### **After (Monolith Schema)**
```sql
CREATE TABLE Orders (
    order_id UUID PRIMARY KEY,           -- Unified key
    status VARCHAR(20) NOT NULL,         -- Standardized enum
    customer_id UUID NOT NULL REFERENCES Customers(customer_id),
    total_amount DECIMAL(10, 2) NOT NULL,
    last_updated TIMESTAMP DEFAULT NOW(),
    -- Sync metadata
    source_system VARCHAR(50),
    last_sync_time TIMESTAMP
);

-- Add indexes for performance
CREATE INDEX idx_orders_customer ON Orders(customer_id);
CREATE INDEX idx_orders_status ON Orders(status);
```

---

## **Query Performance Optimization**
| Technique               | Implementation Example                                                                 |
|-------------------------|-----------------------------------------------------------------------------------------|
| **Partial Indexes**     | `CREATE INDEX idx_orders_recent ON Orders(status) WHERE last_sync_time > NOW() - INTERVAL '7 days';` |
| **Materialized Views**  | Refresh daily: `CREATE MATERIALIZED VIEW daily_orders AS SELECT ... WHERE order_date = CURRENT_DATE;` |
| **Caching**            | Use Redis to cache frequent queries (e.g., `GET /orders/{id}`).                         |
| **Batch Inserts**      | Bulk-insert synced data: `COPY consolidated_orders FROM stdin;`                         |
| **Query Hints**         | Force index usage: `SELECT * FROM orders/*+ INDEX(orders_status) WHERE status = 'SHIPPED';` |

---

## **Related Patterns**
| Pattern                     | Description                                                                                  | When to Use                                                                                     |
|-----------------------------|----------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **API Composition**         | Aggregates responses from multiple APIs into a single endpoint.                            | When external endpoints are stable but need unified access.                                     |
| **Event Sourcing**          | Uses append-only event logs for auditability and replayability.                             | When real-time consistency and audit trails are critical.                                        |
| **CQRS**                    | Separates read (monolith) and write (microservices) paths.                                  | For high-write systems with complex read patterns.                                              |
| **Data Virtualization**     | Provides a virtual DB layer without physical consolidation.                                 | When ETL is too slow or storage is a concern.                                                   |
| **Saga Pattern**            | Manages distributed transactions via compensating actions.                                  | When external systems must participate in ACID-like workflows.                                   |
| **Microservice Chaining**   | Sequentially calls multiple microservices in a pipeline.                                    | When gradual migration from monolith to microservices is needed.                                |

---
## **Anti-Patterns to Avoid**
❌ **Tight Coupling:** Avoid modifying external schemas to fit your monolith; use transformations.
❌ **Ignoring Latency:** Polling high-latency APIs can cause timeouts; prefer CDC or event-driven syncs.
❌ **No Fallback:** Always design for partial failures (e.g., retry logic, graceful degradation).
❌ **Over-Normalization:** Excessive joins can hurt performance; denormalize where query patterns align.
❌ **No Monitoring:** Without observability, you’ll miss sync failures until users report issues.

---
## **Tools & Libraries**
| Category               | Tools                                                                                     |
|------------------------|-------------------------------------------------------------------------------------------|
| **ETL/ELT**            | Apache NiFi, Airbyte, Fivetran, Talend                                                          |
| **CDC**               | Debezium, Kafka Connect, AWS DMS                                                                |
| **API Sync**          | Postman (mocking), Apache Camel, MuleSoft                                                      |
| **Caching**           | Redis, Memcached, CDNs (Cloudflare, Fastly)                                                 |
| **Monitoring**        | Prometheus + Grafana, Datadog, New Relic                                                      |
| **Conflict Resolution**| Custom scripts, Postgres `ON CONFLICT`, Apache Kafka conflict resolvers                     |

---
**Final Note:** The Monolith Integration pattern is ideal for **temporary consolidation** or when external systems lack modern APIs. For long-term scalability, consider migrating to **event-driven architectures** or **hybrid approaches** (e.g., CQRS). Always document the **data lineage** (how records flow from source to sink) for maintainability.