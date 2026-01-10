```markdown
# **Batch Processing vs Individual Requests: Optimizing APIs for Performance and Scale**

Ever watched a slow API crawl like a slug across a busy highway? That's likely your individual requests hitting the brakes at every database checkpoint. **Batch processing** is the superhighway—grouping multiple operations into single requests to slash latency, reduce overhead, and avoid connection pool meltdowns.

In this post, we’ll explore why batching is non-negotiable for high-performance APIs, how it compares to processing items one-by-one, and practical implementations in both database operations and API design. You’ll leave with actionable patterns, tradeoffs to consider, and anti-patterns to avoid.

---

## **The Problem: Why Individual Requests Are a Performance Nightmare**

Imagine a scenario where users submit an array of 1,000 products to your API, one by one. Each product triggers:
- A network request (round-trip time: **10–100ms**).
- A database transaction (locking, autocommit, connection overhead).
- A new connection (if not pooled).

**Result?** A 30-minute wait for 1,000 inserts, even on a fast machine.

### **The Hidden Costs of Individual Requests**
1. **Network Latency Accumulation**
   - Each HTTP request adds overhead. Even trivial operations become expensive at scale.
   - Example: 1,000 small API calls → **30–100 seconds** of waiting for responses.

2. **Database Transaction Overhead**
   - Databases are optimized for bulk operations (e.g., `INSERT`, `UPDATE` in a single statement).
   - Individual transactions generate:
     - Auto-commit delays.
     - Lock contention (e.g., serializable isolation).
     - Log writes (slowing down on high-throughput systems).

3. **Connection Pool Exhaustion**
   - Databases limit concurrent connections (e.g., PostgreSQL’s `max_connections`).
   - A flood of small requests can **starve** your pool, causing timeouts or crashes.

4. **The N+1 Anti-Pattern**
   - APIs and databases alike suffer from "fetal N+1" queries.
   - Example: Fetching a list of users and their orders one-by-one instead of in a single JOIN.

---
## **The Solution: Batch Processing**
The fix? **Batch processing**—grouping operations into larger chunks to amortize fixed costs (connection handling, network latency, transaction overhead).

| Metric               | Individual Requests | Batch Processing |
|----------------------|---------------------|------------------|
| Time for 1,000 inserts | ~30 seconds         | ~100ms           |
| Network round-trips   | 1,000               | 1                |
| Database connections  | 1,000               | ~10 (with chunking) |
| Lock contention       | High                | Low              |

### **How Batching Works**
1. **Bulk Database Operations**
   - Use database-native batching (e.g., `INSERT INTO (...) VALUES (...)`).
   - Example: A single `INSERT` that adds 1,000 rows **100x faster** than 1,000 individual `INSERT`s.

2. **API-Level Batching**
   - Accept arrays of data in a single request (e.g., `POST /api/orders` with a `orders[]` payload).
   - Example: A client submits 100 orders in one batch instead of 100 separate requests.

3. **Chunked Processing**
   - Break large batches into manageable chunks (e.g., 100–1,000 rows per batch) to avoid memory issues and maintain responsiveness.

---
## **Implementation Guide: Batch Processing in Action**

### **1. Bulk Database Inserts**
Most databases support batch inserts. Here’s how to do it in **PostgreSQL, MySQL, and SQLite**.

#### **PostgreSQL: COPY Command**
Fastest way to load large datasets:
```sql
-- Assuming a table 'products' with columns 'id', 'name', 'price'
COPY products(id, name, price) FROM '/tmp/products.csv' WITH (FORMAT csv);
```
Or dynamically:
```sql
INSERT INTO products(id, name, price)
VALUES
    (1, 'Laptop', 999.99),
    (2, 'Phone', 699.99),
    ...;
-- Repeat for 1,000 rows
```

#### **MySQL: Multi-Row INSERT**
```sql
INSERT INTO orders(customer_id, product_id, quantity)
VALUES
    (1, 101, 2),
    (1, 102, 1),
    (2, 101, 3);
```

#### **SQLite: Transactions + Batch INSERT**
```sql
BEGIN TRANSACTION;
INSERT INTO logs(user_id, event, timestamp)
VALUES (1, 'login', '2023-10-01'), (2, 'logout', '2023-10-01');
COMMIT;
```

**Pro Tip:** Use `BulkCopy` in .NET or `pg_bulkload` for even faster PostgreSQL inserts.

---

### **2. API-Level Batching**
Design your API to accept arrays of items in a single payload.

#### **Example: REST API (JSON)**
```http
POST /api/invoices HTTP/1.1
Content-Type: application/json

{
  "invoices": [
    { "id": "inv-1", "amount": 100.00, "due_date": "2023-12-01" },
    { "id": "inv-2", "amount": 200.00, "due_date": "2023-12-01" },
    { "id": "inv-3", "amount": 150.00, "due_date": "2023-12-01" }
  ]
}
```

#### **Example: GraphQL (Batching Queries)**
```graphql
query GetUsersAndOrders {
  users {
    id
    name
    orders {
      id
      amount
    }
  }
}
```
*(GraphQL can batch queries with directives like `@batch`.)*

---

### **3. Chunking for Large Batches**
Never send 100,000 rows in one batch—it’ll kill your server. Instead, chunk them:

#### **Python Example**
```python
import psycopg2
from math import ceil

def batch_insert(chunk_size=1000):
    conn = psycopg2.connect("dbname=test user=postgres")
    cursor = conn.cursor()

    # Simulate 1,000,000 rows
    data = [(i, f"Item {i}") for i in range(1_000_000)]

    # Split into chunks
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i + chunk_size]
        query = "INSERT INTO items(id, name) VALUES %s"
        cursor.executemany(query, chunk)
        print(f"Processed chunk {i//chunk_size + 1}")

    conn.commit()
    conn.close()

batch_insert()
```

**Key:** Chunk size should balance:
- **Too small** → Too many batches (repeated overhead).
- **Too large** → Memory pressure or transaction timeouts.

---

### **4. Transaction Management**
Batching doesn’t mean sacrificing data safety. Use **batching + transactions**:

```python
# Fast bulk insert + atomic transaction
def batch_with_transaction(chunk_size=1000):
    conn = psycopg2.connect("dbname=test")
    cursor = conn.cursor()

    conn.autocommit = False  # Disable auto-commit
    try:
        for i in range(0, 1_000_000, chunk_size):
            chunk = [(i, f"Item {i}") for i in range(i, i + chunk_size)]
            cursor.executemany(
                "INSERT INTO items(id, name) VALUES %s",
                chunk
            )
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
    finally:
        conn.close()
```

---

## **Common Mistakes to Avoid**

1. **Ignoring Chunk Sizes**
   - **Bad:** `INSERT`ing 100,000 rows at once → crashes or deadlocks.
   - **Good:** Split into 1,000 batches of 100 rows.

2. **Not Handling Errors Gracefully**
   - A single failed batch should **not** rollback the entire process.
   - Use **partial success** with retries or dead-letter queues.

3. **Forgetting Connection Reuse**
   - Reuse database connections (e.g., via connection pools).
   - Example: `psycopg2.pool.SimpleConnectionPool`.

4. **Batching Without Consideration for Client Limits**
   - Some clients (e.g., mobile apps) can’t handle 10,000-row responses.
   - Offer **pagination** (e.g., `/api/batch?offset=0&limit=1000`).

5. **Over-Optimizing Without Testing**
   - Batching may slow down small workloads (due to higher overhead per batch).
   - Test with real-world data sizes.

---

## **Key Takeaways**
✅ **Batch processing reduces latency** by cutting network and transaction overhead.
✅ **Use database-native batching** (e.g., `COPY`, `executemany`).
✅ **Design APIs to accept arrays** (e.g., `POST /api/orders` with `orders[]`).
✅ **Chunk large datasets** to avoid memory and timeout issues.
✅ **Always handle errors**—never let a single failure rollback an entire batch.
⚠️ **Tradeoffs:** Batching adds complexity for small workloads; test thoroughly.

---

## **Conclusion**
Batching is a **must-know pattern** for building performant, scalable APIs. Whether you’re loading bulk data, processing user actions, or optimizing database queries, grouping operations reduces overhead and improves responsiveness.

### **When to Use Batch Processing**
| Scenario                     | Batch Approach                          |
|------------------------------|-----------------------------------------|
| Bulk data import             | Database `COPY` or `executemany`        |
| User uploads (e.g., Excel)   | API accepts array of rows               |
| High-frequency updates       | Chunked processing with retries         |
| Analytics pipelines          | Offline bulk processing (e.g., Spark)   |

### **When to Avoid It**
- **Small, frequent updates** (e.g., real-time notifications).
- **Unpredictable data sizes** (if batching risks hitting limits).

**Final Tip:** Start small—test batching with a 10% subset of your data. Optimize iteratively.

Now go ahead and **batch like a pro**—your users (and database) will thank you.
```