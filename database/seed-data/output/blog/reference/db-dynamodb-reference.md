# **[Pattern Name] DynamoDB Database Patterns – Reference Guide**

## **Overview**
DynamoDB Database Patterns provide structured approaches to designing scalable, performant, and maintainable database schemas in **AWS DynamoDB**. Unlike traditional relational databases, DynamoDB is a **NoSQL key-value/document database** with **single-table design flexibility**, **auto-scaling**, and **low-latency access**.

This guide covers **common DynamoDB patterns**, including:
- **Single-Table Design**
- **Partition Key & Sort Key Strategies**
- **Access Patterns & Query Optimization**
- **Secondary Indexes (GSI/LSI)**
- **Data Modeling for Relationships**
- **Caching & Read-Heavy Workloads**
- **Time-Series & High-Write Patterns**

Each pattern includes **implementation best practices**, **schema examples**, **query patterns**, and **anti-patterns** to avoid.

---

## **1. Single-Table Design Pattern**
**Use Case:** Maximize flexibility, minimize tables, and centralize data access.

### **Schema Reference**
| **Item Type**       | **PK (Partition Key)**               | **SK (Sort Key)**                     | **Attributes**                     |
|---------------------|--------------------------------------|---------------------------------------|-------------------------------------|
| **User**            | `USER#<user_id>`                     | `USER#<user_id>`                      | `name`, `email`, `created_at`      |
| **User’s Orders**   | `USER#<user_id>`                     | `ORDER#<order_id>`                    | `order_date`, `status`, `total`     |
| **Order Items**     | `USER#<user_id>`                     | `ORDER_ITEMS#<order_id>#<item_id>`    | `product_id`, `quantity`, `price`   |
| **Product Reviews** | `PRODUCT#<product_id>`               | `REVIEW#<review_id>`                  | `rating`, `comment`, `reviewer_id`  |

**Key Concepts:**
- **PK/SK Combinations:**
  - `USER#<user_id>` → Access all user-related data in one partition.
  - `ORDER#<order_id>` → Sort orders by date/time.
  - `PRODUCT#<product_id>` → Global secondary index (GSI) on product metadata.
- **Denormalization:** Store related data in the same table to avoid joins.
- **Item-Level Access:** Each record has a unique PK/SK combination.

### **Query Examples**
| **Query Type**               | **Example**                                      | **Use Case**                          |
|------------------------------|--------------------------------------------------|---------------------------------------|
| **Get User by ID**           | `GetItem(PK="USER#123")`                         | User profile page                     |
| **List User’s Orders**       | `Query(PK="USER#123", SK="ORDER#", Limit=10)`    | Order history                         |
| **Get Order Details**        | `GetItem(PK="USER#123", SK="ORDER#456")`         | View a specific order                 |
| **Search Products by GSI**   | `Query(GSI=GSI1, KeyCondition=GSI1PK="PRODUCT#123")` | Product catalog search                |
| **Scan All Reviews**         | `Scan(FilterExpression="starts_with(SK, 'REVIEW#')")` | Aggregate reviews (avoid in production) |

**⚠️ Anti-Patterns:**
- Avoid **wide items** (>400KB) or **hot partitions** (uneven traffic).
- **Scan operations** should be minimized (always use `Query` instead).

---

## **2. Partition Key & Sort Key Strategies**
**Use Case:** Optimize read/write performance and avoid throttling.

### **Schema Reference**
| **Pattern**               | **PK Strategy**                          | **SK Strategy**                          | **Best For**                          |
|---------------------------|------------------------------------------|------------------------------------------|---------------------------------------|
| **High-Write Pattern**    | `USER_ID` (simple hash distribution)     | `TIMESTAMP` (auto-generated)             | User activity logs                    |
| **Time-Series Data**      | `DEVICE#<device_id>`                     | `TIMESTAMP` (reverse sort: `2024-01-01`) | IoT sensor data                       |
| **Hierarchical Data**     | `USER#<user_id>`                         | `DEPARTMENT#<dept_id>#EMPLOYEE#<id>`     | Organizational chart                   |
| **Composite Keys**        | `CATEGORY#<category_id>`                 | `PRODUCT#<product_id>#SIZE#<size>`      | E-commerce filtering                  |

### **Query Examples**
| **Use Case**               | **PK/SK Design**                          | **Query**                              |
|----------------------------|------------------------------------------|----------------------------------------|
| **Time-Series Aggregation** | `PK="DEVICE#123", SK="2024-01-01"`      | `Query(PK="DEVICE#123", SK_Begin="2024-01-01", SK_End="2024-01-31")` |
| **Department Employees**   | `PK="USER#123", SK="DEPARTMENT#HR#EMP#456"` | `Query(PK="USER#123", SK_Begin="DEPARTMENT#HR#")` |
| **Product Filtering**      | `PK="CATEGORY#ELECTRONICS", SK="PRODUCT#LAPTOP#S#15"` | `Query(PK="CATEGORY#ELECTRONICS", SK_Begin="PRODUCT#", SK_End="PRODUCT#Z#")` |

**✅ Best Practices:**
- **Avoid hot keys** (e.g., `PK="ALL_USERS"`).
- **Use composite PK/SK** for hierarchical data.
- **Time-series:** Sort by `SK` in **descending order** for recent data.

---

## **3. Global Secondary Index (GSI) Pattern**
**Use Case:** Query data by attributes other than PK/SK.

### **Schema Reference**
| **GSI Name**  | **Partition Key**       | **Sort Key**         | **Projection**       | **Use Case**               |
|---------------|-------------------------|----------------------|----------------------|----------------------------|
| `GSI_User_Email` | `USER_EMAIL#<email>`    | `USER#<user_id>`     | `ALL`                | Find users by email        |
| `GSI_Product_Rating` | `PRODUCT#<product_id>` | `RATING#<rating>`    | `INCLUDE (reviewer_id)` | Filter products by rating |

### **Query Examples**
| **Operation**               | **Query**                                      | **Explanation**                          |
|-----------------------------|------------------------------------------------|------------------------------------------|
| **Find Users by Email**     | `Query(GSI=GSI_User_Email, Key="USER_EMAIL#test@example.com")` | Uses GSI for email lookup               |
| **Top-Rated Products**      | `Query(GSI=GSI_Product_Rating, KeyCondition="PRODUCT#123", FilterExpression="RATING#5")` | Combines GSI + filter                   |
| **Count Reviews by Rating** | `Query(GSI=GSI_Product_Rating, KeyCondition="PRODUCT#123", IndexName="GSI_Product_Rating")` + `Scan` on results | Aggregation requires post-processing |

**⚠️ Anti-Patterns:**
- **Too many GSIs** → Increases cost and complexity.
- **Unused GSIs** → Delete inactive ones.
- **High cardinality** in GSI → Can cause throttling.

---

## **4. Time-Series Data Pattern**
**Use Case:** Store and query high-frequency sensor/telemetry data.

### **Schema Reference**
| **PK**               | **SK**               | **Attributes**                     |
|----------------------|----------------------|-------------------------------------|
| `DEVICE#<device_id>` | `TIMESTAMP#<iso_date>` | `temperature`, `humidity`, `status` |

### **Query Examples**
| **Use Case**               | **Query**                                      | **Optimization**                     |
|----------------------------|------------------------------------------------|---------------------------------------|
| **Get Last 24 Hours**      | `Query(PK="DEVICE#123", SK_Begin="TIMESTAMP#2024-01-01", SK_End="TIMESTAMP#2024-01-02")` | Use `Limit` + `LastEvaluatedKey` for pagination |
| **Aggregate by Hour**      | `Query(...)` + `aws CLI --output=json` + `jq` | Process in application layer          |

**✅ Best Practices:**
- **Compress time windows** (e.g., `DAY`, `HOUR`) for efficiency.
- **Use TTL** to auto-expire old data.

---

## **5. Caching Pattern (DynamoDB Accelerator - DAX)**
**Use Case:** Reduce read latency for high-traffic applications.

### **Schema Reference**
| **Caching Strategy**       | **Implementation**                          |
|----------------------------|---------------------------------------------|
| **DAX Cluster**            | Enable DAX for frequently accessed tables.   |
| **Application-Level Cache**| Use Redis/Memcached for microsecond latency. |

### **Query Examples**
| **Operation**               | **Example**                                  |
|-----------------------------|---------------------------------------------|
| **Cached GetItem**          | `GetItem(PK="USER#123", ConsistentRead=false)` → Hits DAX first |
| **Bypass Cache**            | `GetItem(PK="USER#123", ConsistentRead=true)` → Forces hot path |

**✅ Best Practices:**
- **Cache invalidation:** Use **TTL** or **write-through**.
- **Cache size:** Limit to **high-access** items (e.g., top 10% of users).

---

## **6. Related Patterns**
| **Pattern**                  | **Link**                                      | **Description**                          |
|------------------------------|-----------------------------------------------|------------------------------------------|
| **[Single-Table Design]**    | [AWS DynamoDB Best Practices](https://aws.amazon.com/dynamodb/single-table-design/) | Deep dive into single-table modeling.    |
| **[Event-Driven Arch]**      | [DynamoDB Streams](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Streams.html) | Trigger actions on DynamoDB changes.    |
| **[Backup & Restore]**       | [Point-in-Time Recovery](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/BackupAndRestore.html) | Protect against accidental deletions.   |
| **[Cost Optimization]**      | [DynamoDB Pricing Calculator](https://calculator.aws/) | Right-size provisioned capacity.        |

---

## **Common Pitfalls & Mitigations**
| **Pitfall**                  | **Solution**                                  |
|------------------------------|-----------------------------------------------|
| **Hot Partitions**           | Use **composite keys** or **randomized PKs**. |
| **Throttling (ProvisionedThroughputExceeded)** | Use **on-demand capacity** or **exponential backoff**. |
| **Scan Operations**          | Always use **Query** with proper PK/SK.       |
| **Large Items**              | Split into **multiple items** or **compress data**. |
| **No Secondary Indexes**     | Design **GSIs** for common query patterns.    |

---

## **Conclusion**
DynamoDB Database Patterns enable **scalable, flexible, and cost-efficient** data modeling. Key takeaways:
1. **Leverage single-table design** for simplicity.
2. **Optimize PK/SK** for access patterns.
3. **Use GSIs wisely** to avoid over-engineering.
4. **Cache aggressively** for read-heavy workloads.
5. **Monitor and tune** for performance.

For further reading, refer to the **[AWS DynamoDB Developer Guide](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/)** and **[AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)**.

---
**Word Count:** ~1,100
**Format:** Scannable, bullet-point heavy, table-driven for quick reference.