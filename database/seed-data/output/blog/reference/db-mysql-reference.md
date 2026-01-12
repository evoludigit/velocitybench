**[Pattern] MySQL Database Design Patterns Reference Guide**

---

### **Overview**
This guide documents common **MySQL Database Design Patterns**, providing implementation best practices, schema structures, query examples, and troubleshooting tips. Patterns cover **single-table, multi-table, normalization, denormalization, indexing strategies, and transactional patterns**.

---

---

## **1. Core Pattern Categories**

### **1.1. Single-Table Design**
**Use Case:** Simplifying queries for small, frequently accessed datasets.

#### **Schema Reference**
| Column        | Data Type       | Description                          |
|---------------|-----------------|--------------------------------------|
| `id`          | `INT (PK)`      | Primary key                          |
| `name`        | `VARCHAR(255)`  | Primary attribute                    |
| `value`       | `VARCHAR(512)`  | Data payload                         |
| `created_at`  | `DATETIME`      | Timestamp                            |

**Example: Individual records in one table**
```sql
CREATE TABLE `customers` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(255) NOT NULL,
    `email` VARCHAR(255) UNIQUE,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**When to Use:**
✔ Low write/read complexity
✔ <1M records
❌ Avoid for complex joins or large datasets

---

### **1.2. Multi-Table (Normalized) Design**
**Use Case:** Reducing redundancy for large, relational datasets.

#### **Schema Reference**
| Table          | Key Column   | Related Table | Foreign Key  |
|----------------|--------------|---------------|--------------|
| `users`        | `user_id`    | `orders`      | `order_user_id` |
| `orders`       | `order_id`   | `order_items` | `item_order_id` |

**Example: Orders with normalized structure**
```sql
CREATE TABLE `users` (
    `user_id` INT AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(50) UNIQUE
);

CREATE TABLE `orders` (
    `order_id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT,
    `order_date` TIMESTAMP,
    FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`)
);

CREATE TABLE `order_items` (
    `item_id` INT AUTO_INCREMENT PRIMARY KEY,
    `order_id` INT,
    `product_name` VARCHAR(100),
    FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`)
);
```

**When to Use:**
✔ High write/read efficiency
✔ Large datasets (>1M records)
❌ Requires complex joins for queries

---

### **1.3. Denormalized Design**
**Use Case:** Optimizing read-heavy workloads at the cost of write performance.

#### **Schema Reference**
| Column            | Data Type       | Description                          |
|-------------------|-----------------|--------------------------------------|
| `user_id`         | `INT`           | Foreign key                          |
| `product_name`    | `VARCHAR(100)`  | Embedded relation                    |
| `quantity`        | `SMALLINT`      | Normalized field                     |

**Example: Storing order items inline**
```sql
CREATE TABLE `orders` (
    `order_id` INT,
    `user_id` INT,
    `product1_name` VARCHAR(100),
    `product1_qty` SMALLINT,
    `product2_name` VARCHAR(100),
    `product2_qty` SMALLINT
);
```

**When to Use:**
✔ Read-heavy systems (e.g., analytics dashboards)
✔ Complex queries where joins are inefficient
❌ Write operations become slower

---

## **2. Indexing Patterns**

### **2.1. B-Tree Indexes (Default)**
**Use Case:** Optimizing range queries and equality checks.

```sql
CREATE INDEX `idx_user_email` ON `users` (`email`);
```

**Best Practices:**
- Index columns used in `WHERE`, `ORDER BY`, or `JOIN` clauses.
- Avoid indexing columns with low cardinality (e.g., `status` with 2 values).

---

### **2.2. Hash Indexes (Memory-Optimized)**
**Use Case:** Fast key lookups in `MEMORY` tables.

```sql
CREATE TABLE `cache` (
    `key` VARCHAR(32) PRIMARY KEY HASH,
    `value` TEXT
) ENGINE=MEMORY;
```

**When to Use:**
✔ In-memory caching (e.g., Redis alternative)
❌ Not suitable for range queries

---

### **2.3. Full-Text Indexes**
**Use Case:** Searching unstructured text (e.g., blog posts).

```sql
ALTER TABLE `articles` ADD FULLTEXT (`content`);
```

**Example Query:**
```sql
SELECT * FROM `articles`
WHERE MATCH (`content`) AGAINST ('database patterns');
```

---

## **3. Transactional Patterns**

### **3.1. ACID Transactions**
**Use Case:** Ensuring data integrity across multiple operations.

```sql
START TRANSACTION;
    -- Operation 1
    UPDATE `users` SET `balance` = `balance` - 100 WHERE `id` = 1;

    -- Operation 2
    UPDATE `account_history` SET `amount` = -100 WHERE `user_id` = 1;

COMMIT; -- or ROLLBACK on failure
```

**Best Practices:**
- Keep transactions short to avoid locks.
- Use `BEGIN`/`COMMIT` instead of `START TRANSACTION` for simplicity.

---

### **3.2. Distributed Transactions (XA)**
**Use Case:** Multi-database consistency (e.g., MySQL + PostgreSQL).

```sql
CREATE TABLE `xadistribution` (
    `tx_id` VARCHAR(50) PRIMARY KEY,
    `status` ENUM('active', 'complete', 'failed')
);
```

**Limitations:**
- High overhead; use sparingly.
- Avoid long-running XA transactions.

---

## **4. Query Examples**

### **4.1. Joining Tables Efficiently**
```sql
-- Compare: Left Join vs. Inner Join
SELECT u.username, o.order_id
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id;
```

**Optimization Tip:** Use `EXPLAIN` to analyze query performance.

---

### **4.2. Batch Inserts**
```sql
-- Single query for multiple inserts
INSERT INTO `logs` (`user_id`, `action`, `timestamp`)
VALUES
    (1, 'login', NOW()),
    (2, 'logout', NOW());
```

**Best Practice:** Use prepared statements for security.

---

### **4.3. Pagination**
```sql
-- Efficient pagination with LIMIT/OFFSET
SELECT * FROM `products`
ORDER BY `price` DESC
LIMIT 10 OFFSET 20;
```

**Alternative:** Keyset pagination (better for deep offsets)
```sql
SELECT * FROM `products`
WHERE `id` > 20
ORDER BY `id`
LIMIT 10;
```

---

## **5. Common Pitfalls & Fixes**

| Pitfall                          | Solution                                  |
|----------------------------------|-------------------------------------------|
| Table locking during writes      | Increase `innodb_buffer_pool_size`       |
| Slow full-table scans            | Add appropriate indexes                   |
| Foreign key constraints slowing writes | Disable FK checks during bulk inserts   |
| Schema bloat                      | Regularly optimize tables (`OPTIMIZE TABLE`) |

---

## **6. Related Patterns**
1. **[MySQL Scaling Patterns]** – Sharding, replication, read replicas.
2. **[Connection Pooling]** – Optimizing MySQL client connections.
3. **[Data Backup & Recovery]** – Automated backups with `mysqldump`.
4. **[Query Optimization]** – Using `EXPLAIN`, slow query logs.

---
**References:**
- MySQL Documentation: [https://dev.mysql.com/doc/](https://dev.mysql.com/doc/)
- Google’s BigQuery Patterns (similar principles)