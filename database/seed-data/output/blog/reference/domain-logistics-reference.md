---
# **[Pattern] Logistics Domain Patterns – Reference Guide**

---

## **Overview**
The **Logistics Domain Patterns** reference guide provides structured patterns for modeling, querying, and optimizing logistics workflows in enterprise systems. It focuses on **standardized data structures**, **cohesive business rules**, and **scalable implementation strategies** to handle supply chain, inventory, transportation, and order fulfillment.

This guide addresses key concerns:
- **Data consistency** across warehouse, shipping, and fulfillment systems.
- **Efficient batch processing** for high-volume logistics operations.
- **Enforcement of SLAs (Service Level Agreements)** via event-driven triggers.
- **Interoperability** with third-party logistics (3PL) APIs.

Whether integrating with ERP systems or designing microservices, these patterns ensure **traceability**, **predictive analytics support**, and **compliance** with industry regulations (e.g., GDPR, SCRA).

---

## **Schema Reference**
Below are core entity schemas and relationships. All fields are optional unless marked with `*` (required).

### **1. Core Entities**
| **Entity**          | **Field**          | **Type**       | **Description**                                                                                     | **Example Values**                     |
|---------------------|--------------------|----------------|-----------------------------------------------------------------------------------------------------|----------------------------------------|
| **Location**        | `id`               | `UUID` (R)     | Unique identifier.                                                                                 | `550e8400-e29b-41d4-a716-446655440000` |
|                     | `name`*            | `String`       | Human-readable name (e.g., warehouse, distribution center).                                       | `Amazon Fulfillment DC-NA-1`           |
|                     | `type`*            | `Enum`         | `WAREHOUSE`, `DEPOT`, `RETAIL_STORE`, `TRANSPORT_HUB`.                                             | `WAREHOUSE`                            |
|                     | `address`*         | `GeoJSON`      | Latitude/longitude + postal address.                                                                | `{"type": "Point", "coordinates": [-73.935242, 40.730610]}` |
|                     | `capacity_kgs`     | `Integer`      | Max storage capacity in kilograms.                                                                  | `1,250,000`                           |
|                     | `is_active`        | `Boolean`      | Logical flag for soft deletion.                                                                     | `true`                                  |
|                     | `created_at`       | `Timestamp`    | Audit field.                                                                                       | `2023-01-15T14:30:00Z`                 |
|                     | `updated_at`       | `Timestamp`    | Audit field.                                                                                       | `2023-05-20T09:15:00Z`                 |

| **Entity**          | **Field**          | **Type**       | **Description**                                                                                     | **Example Values**                     |
|---------------------|--------------------|----------------|-----------------------------------------------------------------------------------------------------|----------------------------------------|
| **InventoryItem**   | `id`               | `UUID` (R)     | Unique identifier.                                                                                 | `3ae7e441-8cc3-437d-8f7a-16c250eb0000` |
|                     | `sku`*             | `String`       | Stock Keeping Unit (required for upstream systems).                                                 | `AMZN-WHT-2023`                       |
|                     | `name`             | `String`       | Human-readable product name.                                                                    | `Wireless Bluetooth Headphones`       |
|                     | `current_quantity` | `Integer`      | Real-time stock level.                                                                             | `42`                                    |
|                     | `unit_weight_kg`   | `Decimal`      | Weight per unit (for shipping calculations).                                                        | `0.25`                                  |
|                     | `location_id`*     | `UUID (FK)`    | Reference to `Location` entity.                                                                    | `550e8400-e29b-41d4-a716-446655440000` |
|                     | `last_stock_update`| `Timestamp`    | When inventory was last synced.                                                                    | `2023-06-01T11:45:00Z`                 |

---
**Key:**
- `(R)` = Read-only (auto-generated).
- `(FK)` = Foreign Key.
- Enums are **case-sensitive** and **immutable** after deployment.

---

## **2. Relationships**
Logistics patterns rely on **hierarchical and temporal relationships**. Below are critical parent-child links:

| **Parent Entity**  | **Child Entity**      | **Relationship Type**       | **Cardinality**       | **Example Scenario**                          |
|--------------------|-----------------------|----------------------------|-----------------------|-----------------------------------------------|
| `Location`         | `InventoryItem`       | One-to-Many                | 1:N                   | A warehouse (`Location`) holds 1,000 SKUs.    |
| `Location`         | `Shipment`            | One-to-One (optional)      | 1:1 (optional)        | A depot may be the **origin** of a shipment.  |
| `Shipment`         | `ShipmentItem`        | One-to-Many                | 1:N                   | One shipment (`Shipment`) contains 50 items.  |
| `Order`            | `OrderItem`           | One-to-Many                | 1:N                   | One customer order (`Order`) has 3 line items.|
| `OrderItem`        | `InventoryItem`       | Many-to-One (via `sku`*)   | N:1                   | Multiple orders (`OrderItem`) reference `sku`. |

---

## **3. Query Examples**
### **A. Inventory Level Checks**
**Use Case:** Verify if an order can be fulfilled before processing.
```sql
SELECT
    i.sku,
    i.name,
    i.location_id,
    i.current_quantity,
    l.name AS location_name
FROM
    InventoryItem i
JOIN
    Location l ON i.location_id = l.id
WHERE
    i.sku IN ('AMZN-WHT-2023', 'GADG-HEAD-2023')
    AND l.is_active = true
    AND l.type = 'WAREHOUSE';
```
**Optimization:** Add a **composite index** on `(sku, location_id, current_quantity)`.

---

### **B. Shipment Tracking**
**Use Case:** Retrieve all active shipments for a given customer.
```sql
SELECT
    s.id,
    s.tracking_number,
    s.status,
    s.origin_location_id,
    s.destination_location_id,
    s.estimated_delivery_date,
    COUNT(shi.id) AS total_items
FROM
    Shipment s
JOIN
    ShipmentItem shi ON s.id = shi.shipment_id
WHERE
    s.customer_id = 'CUST-12345'
    AND s.status IN ('IN_TRANSIT', 'DELIVERED')
GROUP BY
    s.id
ORDER BY
    s.estimated_delivery_date DESC;
```
**Filtering:** Use `s.status` enum to limit to `IN_TRANSIT` only.

---

### **C. Deadlock Prevention (Batch Updates)**
**Use Case:** Update inventory in bulk without race conditions.
```sql
-- Step 1: Lock all inventory items for the SKU
BEGIN TRANSACTION;
SELECT * FROM InventoryItem
WHERE sku = 'AMZN-WHT-2023'
FOR UPDATE;

-- Step 2: Atomic update
UPDATE InventoryItem
SET
    current_quantity = current_quantity - 10,
    updated_at = NOW()
WHERE
    sku = 'AMZN-WHT-2023'
    AND current_quantity >= 10;
COMMIT;
```
**Pitfall:** Avoid long-running transactions; use **sagas** for distributed systems.

---

## **4. Business Rules & Triggers**
### **A. Auto-Replenishment**
**Rule:** If `current_quantity < 20% of max_capacity`, trigger a purchase order.
```sql
CREATE OR REPLACE FUNCTION check_replenishment()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.current_quantity < (SELECT capacity_kgs * 0.2 FROM Location WHERE id = NEW.location_id) THEN
        -- Fire event: "ReplenishmentRequired" (e.g., via Kafka)
        PERFORM pg_notify('replenishment', json_build_object(
            'sku', NEW.sku,
            'threshold', NEW.current_quantity,
            'location', NEW.location_id
        ));
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE 'plpgsql';

CREATE TRIGGER trg_replenish
AFTER UPDATE OF current_quantity ON InventoryItem
FOR EACH ROW EXECUTE FUNCTION check_replenishment();
```

---

### **B. SLAs for Shipment Delays**
**Rule:** Notify customers if `estimated_delivery_date` > `actual_delivery_date` by 2 days.
```sql
-- Scheduled Daily Check (via Airflow/Cron)
SELECT
    s.tracking_number,
    s.customer_id,
    s.estimated_delivery_date,
    s.actual_delivery_date,
    (s.actual_delivery_date - s.estimated_delivery_date) AS delay_days
FROM
    Shipment s
WHERE
    s.status = 'DELIVERED'
    AND s.actual_delivery_date > (s.estimated_delivery_date + INTERVAL '2 days');
```

---

## **5. Common Pitfalls & Mitigations**
| **Pitfall**                          | **Mitigation**                                                                                     | **Recommendation**                          |
|--------------------------------------|---------------------------------------------------------------------------------------------------|---------------------------------------------|
| **Inventory overcounting**           | Use **distributed locks** (e.g., Redis) during high-volume transactions.                          | Implement **optimistic concurrency control**.|
| **3PL API rate limits**              | Cache responses with **TTL=5 mins** and retry with exponential backoff.                            | Use **circuit breakers** (e.g., Hystrix).    |
| **Schema evolution without migration**| Document all schema changes in a **versioned changelog**.                                          | Enforce **backward compatibility**.           |
| **Eventual consistency delays**      | Set **timeouts** for critical events (e.g., 30s for order confirmation).                          | Use **idempotency keys** for retries.         |
| **Geospatial queries underperforming**| Pre-compute **spatial indices** (e.g., PostGIS) for `LOCATION` queries.                          | Avoid `SELECT *`; project only needed fields.|

---

## **6. Related Patterns**
| **Pattern**                          | **Purpose**                                                                                       | **When to Use**                                      |
|--------------------------------------|---------------------------------------------------------------------------------------------------|------------------------------------------------------|
| **[Event Sourcing](https://patterns.gatech.edu/)** | Track state changes as immutable events for auditability.                                         | Logistics workflows requiring **full traceability**.  |
| **[CQRS](https://cqrs.files.wordpress.com/2010/11/cqrs_documents.pdf)** | Separate read/write models for scalability.                                                      | High-read scenarios (e.g., inventory dashboards).    |
| **[Saga Pattern](https://microservices.io/patterns/data/saga.html)** | Manage distributed transactions (e.g., order → payment → shipping).                              | Microservices architecture.                          |
| **[API Composition](https://msdn.microsoft.com/en-us/library/dn589780.aspx)** | Aggregate real-time data (e.g., shipping + inventory) into a single API.                         | Legacy system integration.                           |
| **[Time-Series Database](https://www.timescale.com/)** | Optimize for **high-frequency updates** (e.g., live GPS tracking).                              | IoT-connected logistics fleets.                      |

---
## **7. Tools & Integrations**
| **Tool**               | **Use Case**                                                                                     | **Example Libraries**                     |
|------------------------|---------------------------------------------------------------------------------------------------|--------------------------------------------|
| **PostgreSQL + PostGIS** | Geospatial queries for route optimization.                                                       | `psycopg2`, `pgrouting`                   |
| **Kafka**              | Event-driven logistics (e.g., order → warehouse → shipment).                                      | `confluent-kafka-python`                  |
| **Apache Airflow**     | Scheduled batch processing (e.g., daily inventory reports).                                       | `apache-airflow-providers-postgres`       |
| **GraphQL**            | Flexible query layers for frontend apps (e.g., order tracking UI).                               | `graphene`, `strawberry`                   |
| **Docker + Kubernetes**| Containerize microservices (e.g., shipping API, inventory service).                                | `K8s Helm charts`                          |

---
**Note:** For **high-scale deployments**, consider **sharding** the `InventoryItem` table by `location_id`.

---
**Last Updated:** `2023-06-15`
**Version:** `1.2` (Added CQRS integration notes)