# **[Pattern] SQL Server Microsoft DB Reference Guide**

---

## **1. Overview**
This guide outlines the **SQL Server Microsoft DB pattern**, a standardized approach for implementing relational database solutions using **Microsoft SQL Server**. Designed for scalability, performance, and maintainability, this pattern ensures consistency across applications, databases, and environments. It supports enterprise-grade applications, BI workloads, and hybrid cloud deployments, leveraging best practices for schema design, indexing, security, and high availability.

Key features include:
- **Schema-first design** (logical/physical separation)
- **Standardized naming conventions** (tables, columns, constraints)
- **Performance-optimized indexing** (clustered, non-clustered, filtered)
- **Security best practices** (least-privilege access, audit logging)
- **High availability & disaster recovery** (always-on availability groups, backups)

This guide is applicable for:
- New database implementations
- Migrations from legacy systems
- Scaling existing SQL Server deployments
- Integration with Azure SQL or on-premises instances.

---

## **2. Key Concepts & Implementation Details**

### **2.1 Core Components**
| **Component**          | **Description**                                                                                     |
|------------------------|-----------------------------------------------------------------------------------------------------|
| **Logical Schema**     | High-level design (tables, relationships, business domains)                                        |
| **Physical Schema**    | Implementation-specific details (partitioning, filegroups, collation)                             |
| **Indexing Strategy**  | Optimized for query patterns (clustered PK, non-clustered UKs, included columns)                     |
| **Security Model**     | Role-based access control, column-level security, encryption (TDE)                                |
| **Monitoring**         | Performance, auditing (SQL Audit), and maintenance hooks (index rebuilds, stats update)            |
| **Backup/Recovery**    | Automated backups, point-in-time recovery, and geo-redundancy                                       |

---

### **2.2 Best Practices**
#### **Schema Design**
- **Normalization**: Use **3NF** for transactional data; denormalize for reporting tables.
- **Naming Conventions**:
  - Tables: `PascalCase` (e.g., `CustomerOrders`, `ProductCategories`)
  - Columns: `snake_case` with prefixes (`fk_customer_id`, `created_at`)
  - Constraints: `PK_`, `UK_`, `CHK_` (e.g., `PK_CustomerOrders`, `CHK_ValidEmail`)
- **Partitioning**: Large tables (>10M rows) should be partitioned by date or range.

#### **Performance**
- **Clustered Indexes**: Always on the **primary key** (surrogate keys preferred).
- **Non-Clustered Indexes**: Only for frequently filtered/sorted columns.
- **Included Columns**: Add non-key columns to indexes to avoid key lookups.
- **Query Tuning**: Use **Execution Plans**, **Query Store**, and **DMVs** (`sys.dm_exec_query_stats`).

#### **Security**
- **Principals**: Separate roles for **app users**, **admins**, and **auditors**.
- **Row-Level Security (RLS)**: Enforce data isolation (e.g., `WHERE user_id = current_user_id`).
- **Encryption**: Use **Transparent Data Encryption (TDE)** for at-rest security.

#### **High Availability**
- **Always-On Availability Groups**: For multi-site redundancy.
- **Read-Replicas**: For reporting/query offloading.
- **Log Shipping**: Secondary replication with minimal downtime.

---

## **3. Schema Reference**

Below is a **standardized schema template** for a **Customer-Order-Payment** example.

| **Table**               | **Columns**                                                                                     | **PK/FK**                     | **Indexes**                          | **Notes**                                  |
|-------------------------|-------------------------------------------------------------------------------------------------|--------------------------------|---------------------------------------|-------------------------------------------|
| **Customers**           | `customer_id` (INT, IDENTITY), `first_name` (NVARCHAR(50)), `last_name`, `email`, `created_at`     | PK (`customer_id`)             | Non-Clustered (`email`)              | Denormalized for reporting.               |
| **Orders**              | `order_id` (INT, IDENTITY), `customer_id` (INT), `order_date`, `status`, `total_amount`          | PK (`order_id`)                | Clustered (`order_id`) + Non-Clustered (`status`) | Partitioned by `order_date`.          |
| **OrderItems**          | `order_item_id` (INT, IDENTITY), `order_id` (INT), `product_id` (INT), `quantity`, `unit_price`   | PK (`order_item_id`) + FK (`order_id`, `product_id`) | Clustered (`order_id`, `product_id`) | Included column: `quantity * unit_price`. |
| **Products**            | `product_id` (INT, IDENTITY), `name`, `category_id` (INT), `price`, `stock_quantity`              | PK (`product_id`)              | Non-Clustered (`name`)               | Full-text index on `name` for search.     |
| **Categories**          | `category_id` (INT, IDENTITY), `name`, `description`                                               | PK (`category_id`)             | None                                  | Small table; no need for indexes.        |
| **Payments**            | `payment_id` (INT, IDENTITY), `order_id` (INT), `amount`, `payment_date`, `method`               | PK (`payment_id`) + FK (`order_id`) | Non-Clustered (`method`, `payment_date`) | Audit log table.                        |

---

### **3.1 Relationships**
| **Parent Table**  | **Child Table** | **Relationship Type** | **Foreign Key**       |
|--------------------|-----------------|-----------------------|-----------------------|
| `Customers`        | `Orders`        | One-to-Many           | `customer_id` (FK)    |
| `Orders`           | `OrderItems`    | One-to-Many           | `order_id` (FK)       |
| `OrderItems`       | `Products`      | Many-to-Many          | `product_id` (FK)     |
| `Orders`           | `Payments`      | One-to-One            | `order_id` (FK)       |

---

## **4. Query Examples**

### **4.1 Basic CRUD Operations**
#### **Insert Customer**
```sql
BEGIN TRANSACTION;
INSERT INTO Customers (first_name, last_name, email)
VALUES ('John', 'Doe', 'john.doe@example.com');
-- Add audit log (if applicable)
INSERT INTO AuditLog (action, table_name, record_id, changed_by)
VALUES ('INSERT', 'Customers', SCOPE_IDENTITY(), SYSTEM_USER);
COMMIT;
```

#### **Retrieve Orders with Customer Details**
```sql
SELECT
    c.first_name,
    c.last_name,
    o.order_id,
    o.order_date,
    oi.product_id,
    p.name AS product_name,
    oi.quantity,
    oi.unit_price
FROM Orders o
JOIN Customers c ON o.customer_id = c.customer_id
JOIN OrderItems oi ON o.order_id = oi.order_id
JOIN Products p ON oi.product_id = p.product_id
WHERE o.order_date > '2023-01-01'
ORDER BY o.order_date DESC;
```

#### **Update Product Price (Batch)**
```sql
UPDATE Products
SET price = price * 1.1  -- 10% increase
WHERE category_id = 5    -- Apply only to a specific category
AND stock_quantity < 10; -- Only for low-stock items
```

#### **Delete Expired Orders**
```sql
-- Soft delete (recommended)
UPDATE Orders
SET is_deleted = 1, deleted_at = GETDATE()
WHERE order_date < DATEADD(YEAR, -1, GETDATE());

-- Hard delete (use with caution)
-- DELETE FROM Orders WHERE order_date < DATEADD(YEAR, -1, GETDATE());
```

---

### **4.2 Performance-Optimized Queries**
#### **Filtered Index Scan for Common Reports**
```sql
-- Create a filtered index for active customers only
CREATE NONCLUSTERED INDEX IX_Customers_Active ON Customers (email)
WHERE is_active = 1;

-- Query benefits from the filtered index
SELECT email, first_name
FROM Customers WITH (NOLOCK)
WHERE is_active = 1;
```

#### **Temporary Table for Aggregations**
```sql
-- Create a temp table to avoid repeated calculations
CREATE TABLE #OrderTotals (
    category_id INT,
    total_revenue MONEY
);

-- Populate with aggregated data
INSERT INTO #OrderTotals (category_id, total_revene)
SELECT
    p.category_id,
    SUM(oi.quantity * oi.unit_price)
FROM OrderItems oi
JOIN Products p ON oi.product_id = p.product_id
GROUP BY p.category_id;

-- Use in main query
SELECT
    c.name AS category_name,
    ot.total_revenue
FROM Categories c
JOIN #OrderTotals ot ON c.category_id = ot.category_id
ORDER BY ot.total_revenue DESC;

-- Clean up
DROP TABLE #OrderTotals;
```

#### **Stored Procedure for Transactional Workflow**
```sql
CREATE PROCEDURE usp_PlaceOrder
    @customer_id INT,
    @order_items JSON  -- e.g., '[{"product_id": 1, "quantity": 2}]'
AS
BEGIN
    BEGIN TRANSACTION;

    -- Validate customer
    IF NOT EXISTS (SELECT 1 FROM Customers WHERE customer_id = @customer_id)
        RAISERROR('Customer not found', 16, 1);

    -- Insert order header
    DECLARE @order_id INT = SCOPE_IDENTITY();
    INSERT INTO Orders (customer_id, order_date, status)
    VALUES (@customer_id, GETDATE(), 'Pending');

    -- Parse and insert order items
    DECLARE @json NVARCHAR(MAX) = @order_items;
    DELETE FROM OrderItems WHERE order_id = @order_id; -- Clear previous items

    INSERT INTO OrderItems (order_id, product_id, quantity, unit_price)
    SELECT
        @order_id,
        value.product_id,
        value.quantity,
        p.price
    FROM OPENJSON(@json) WITH (
        product_id INT '$.product_id',
        quantity INT '$.quantity'
    ) AS value
    JOIN Products p ON value.product_id = p.product_id;

    -- Update stock (optimistic concurrency)
    UPDATE p
    SET stock_quantity = stock_quantity - oi.quantity
    FROM OrderItems oi
    JOIN Products p ON oi.product_id = p.product_id
    WHERE oi.order_id = @order_id
    OPTION (OPTIMIZE FOR UNKNOWN);

    -- Create payment record
    INSERT INTO Payments (order_id, amount, payment_date, method)
    VALUES (@order_id, (SELECT SUM(quantity * unit_price) FROM OrderItems WHERE order_id = @order_id),
            GETDATE(), 'Credit Card');

    COMMIT;
END;
```

---

### **4.3 DDL for Common Patterns**
#### **Add Column with Default Value**
```sql
-- Add nullable column
ALTER TABLE Orders ADD COLUMN confirmation_email NVARCHAR(255) NULL;

-- Add non-nullable column with default
ALTER TABLE Orders ADD COLUMN created_by NVARCHAR(50) NOT NULL
CONSTRAINT DF_Orders_CreatedBy DEFAULT SYSTEM_USER;
```

#### **Add Check Constraint**
```sql
ALTER TABLE Products
ADD CONSTRAINT CHK_ValidStock
CHECK (stock_quantity >= 0);
```

#### **Create Table with Computed Column**
```sql
CREATE TABLE ProductPricing (
    product_id INT,
    base_price DECIMAL(10, 2),
    discount_percentage DECIMAL(5, 2),
    sale_price AS base_price * (1 - discount_percentage / 100),
    PRIMARY KEY (product_id)
);
```

---

## **5. Related Patterns**

| **Pattern Name**               | **Description**                                                                                     | **Use Case**                                  |
|---------------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------|
| **[Microsoft Azure SQL DB]**   | Cloud-optimized version of SQL Server with auto-scaling and managed backups.                       | Multi-cloud deployments, serverless workloads. |
| **[SQL Server Always-On]**      | High availability with synchronous/asynchronous replication.                                          | Critical applications requiring <5s RPO.     |
| **[Read-Replica Pattern]**      | Offload reporting queries to a read-only replica.                                                    | Analytics, BI dashboards.                      |
| **[Sharding Pattern]**          | Horizontal partition large tables by key ranges.                                                     | Global-scale applications.                      |
| **[CDC (Change Data Capture)]**| Track changes for real-time integration (e.g., with Azure Synapse).                                | Event-driven architectures.                  |
| **[SQL Injection Protection]**  | Parameterized queries and stored procedures to prevent SQLi.                                           | Secure web applications.                      |
| **[Audit Logging Pattern]**     | Track all DML operations via triggers or Change Data Capture.                                         | Compliance (GDPR, HIPAA).                      |

---

## **6. References**
- [Microsoft SQL Server Documentation](https://learn.microsoft.com/en-us/sql/)
- [SQL Server Performance Tuning Guide](https://learn.microsoft.com/en-us/sql/relational-databases/performance/performance-tuning-guide)
- [Azure SQL Database Best Practices](https://learn.microsoft.com/en-us/azure/azure-sql/database/performance-checklist)
- [T-SQL Fundamentals](https://learn.microsoft.com/en-us/t-sql/language-reference)