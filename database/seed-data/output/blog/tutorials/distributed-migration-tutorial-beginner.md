```markdown
---
title: "Distributed Migration: How to Update Millions of Records Across Services Without Breaking Your System"
date: "2023-10-15"
author: "Alex Carter"
description: "Learn the Distributed Migration pattern to safely update data across services, with practical examples and real-world tradeoffs."
tags: ["database", "microservices", "API design", "migration", "data consistency", "pattern"]
---

# **Distributed Migration: How to Update Millions of Records Across Services Without Breaking Your System**

For most backend engineers, updates to data are part of the daily grind—fixing typos in user profiles, adjusting product prices, or recalculating shipping zones. But what happens when you need to update **millions of records across multiple services**? A poorly executed migration can bring your entire system to a crawl, leaving users frustrated and admins scrambling.

In this guide, you’ll learn the **Distributed Migration pattern**—a systematic approach for updating data safely across distributed systems. We’ll walk through the challenges, break down the solution with code examples, and cover pitfalls to avoid. By the end, you’ll know how to migrate data at scale with confidence.

---

## **The Problem: Why Distributed Migrations Are Hard**

When you need to update data that spans multiple services or databases, you face several challenges:

1. **No Single Point of Control**
   If your system is microservices-based, you can’t run a single `UPDATE` statement across all services—each has its own database. Updates must be coordinated manually, which introduces the risk of inconsistency.

2. **Downtime and Locking**
   A naive approach (e.g., updating all records at once) can lock tables for minutes or hours, freezing queries and causing cascading failures.

3. **Network Latency and Failures**
   Distributed systems are inherently unreliable. If one service fails during migration, you might end up with partial updates or orphaned records.

4. **Data Duplication and Inconsistency**
   If two services read the same record at different times, the "old" value might still be used, leading to contradictory data.

---

## **The Solution: The Distributed Migration Pattern**

The Distributed Migration pattern solves these challenges by:

- **Batch processing** records in small, manageable chunks.
- **Using compensating transactions** to handle failures.
- **Applying updates asynchronously** to minimize downtime.
- **Leveraging change data capture (CDC)** to detect and replay missed updates.

This approach balances **consistency**, **availability**, and **scalability**—the holy trinity of distributed systems.

---

## **Components of the Distributed Migration Pattern**

The pattern typically involves these components:

| Component       | Purpose                                                                 |
|-----------------|-------------------------------------------------------------------------|
| **Batch Processor** | Reads records in small groups (e.g., 1000 at a time) and applies updates. |
| **Dead-Letter Queue** | Handles failed updates so they can be retried later.                  |
| **Idempotency Keys** | Ensures the same update isn’t applied multiple times.                   |
| **Change Data Capture (CDC)** | Tracks which records were updated to avoid re-processing.              |
| **Compensating Actions** | Undoes updates if a batch fails.                                        |

---

## **Step-by-Step Implementation**

Let’s build a distributed migration for updating a `user_preferences` table across three services: **User Service**, **Notification Service**, and **Analytics Service**.

### **Step 1: Define the Migration Plan**

First, create a migration script that:
- Identifies which records need updating.
- Processes them in batches.
- Handles failures gracefully.

#### **Example Migration Script (Python + SQL)**
```python
import sqlite3
from typing import List, Dict
import time

# Simulate a database connection (could be Postgres, MySQL, etc.)
def get_db_connection():
    return sqlite3.connect("migration.db")  # In real life, use your actual DB

def migrate_user_preferences(batch_size: int = 1000):
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Fetch records to update in batches
    offset = 0
    while True:
        # Read a batch of records to update
        cursor.execute("SELECT user_id FROM user_preferences WHERE needs_update = 1 LIMIT ? OFFSET ?", (batch_size, offset))
        batch = cursor.fetchall()

        if not batch:
            break  # No more records

        # 2. Simulate distributed updates (User, Notification, Analytics services)
        for user_id in batch:
            update_user_service(user_id)
            update_notification_service(user_id)
            update_analytics_service(user_id)

            # Mark as processed
            cursor.execute("UPDATE user_preferences SET needs_update = 0 WHERE user_id = ?", (user_id,))

        conn.commit()
        offset += batch_size
        print(f"Processed batch {offset // batch_size}")

def update_user_service(user_id: int):
    """Simulate updating the User Service API."""
    response = requests.post(
        "https://user-service/api/preferences/update",
        json={"user_id": user_id, "value": "new_setting"},
        timeout=10
    )
    if response.status_code != 200:
        print(f"Failed to update User Service for {user_id}, retrying later...")

def update_notification_service(user_id: int):
    """Simulate updating the Notification Service."""
    # Similar API call logic...

def update_analytics_service(user_id: int):
    """Simulate updating the Analytics Service."""
    # Similar API call logic...

# Start the migration
if __name__ == "__main__":
    migrate_user_preferences(batch_size=500)  # Start with a small batch
```

### **Step 2: Handle Failures with Retries and Dead-Letter Queues**

Not every record will update successfully. Use a **dead-letter queue (DLQ)** to track failed updates.

#### **Adding a Dead-Letter Queue (Python + SQLite)**
```python
def update_record_safely(service_func, user_id: int, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            service_func(user_id)
            return True  # Success!
        except Exception as e:
            print(f"Attempt {attempt + 1} failed for {user_id}: {e}")

            # Log to DLQ
            cursor.execute(
                "INSERT INTO dlq (user_id, service, error, attempt) VALUES (?, ?, ?, ?)",
                (user_id, service_func.__name__, str(e), attempt)
            )
            conn.commit()
            time.sleep(2 ** attempt)  # Exponential backoff

    return False  # All retries failed

# Update the migration loop to use safe updates
for user_id in batch:
    if not update_record_safely(update_user_service, user_id):
        print(f"User {user_id} failed after retries, check DLQ.")

    # Mark as processed (even if some services failed)
    cursor.execute("UPDATE user_preferences SET needs_update = 0 WHERE user_id = ?", (user_id,))
```

### **Step 3: Use Idempotency Keys to Avoid Duplicates**

If the process crashes and restarts, the same record should **not** be updated twice. Use an `idempotency_key` (e.g., `user_id + operation_type`) to track processed updates.

#### **SQL to Track Processed Updates**
```sql
-- Add a column to track processed updates
ALTER TABLE user_preferences ADD COLUMN IF NOT EXISTS last_migration_id INTEGER;

-- Update a record only if it hasn't been processed before
UPDATE user_preferences
SET
    needs_update = 0,
    last_migration_id = (SELECT MAX(id) FROM some_migration_tracker)
WHERE
    id IN (SELECT user_id FROM batch_to_process)
    AND last_migration_id IS NULL;
```

### **Step 4: Use Change Data Capture (CDC) for Real-Time Sync**

If you’re using a database like **Debezium**, **PostgreSQL Logical Decoding**, or **AWS DMS**, you can **listen for changes** and apply them in real time. This ensures no data is missed.

#### **Example with Debezium (Kafka)**
1. Set up a Kafka topic to capture changes to `user_preferences`.
2. Write a consumer that applies updates to downstream services:
   ```python
   from confluent_kafka import Consumer

   def consume_updates():
       config = {'bootstrap.servers': 'kafka:9092', 'group.id': 'migration-consumer'}
       consumer = Consumer(config)
       consumer.subscribe(['user_preferences.changes'])

       while True:
           msg = consumer.poll(1.0)
           if msg is None:
               continue
           if msg.error():
               raise Exception(f"Consumer error: {msg.error()}")

           # Parse change and apply to services
           change = json.loads(msg.value())
           if change['op'] == 'update':
               apply_update(change['before'], change['after'])
   ```

---

## **Implementation Guide**

### **1. Start Small**
- Test with a **single table** and **small dataset** before scaling.
- Use a **staging environment** identical to production.

### **2. Monitor Progress**
- Log each batch’s start/end time.
- Track failures in a dashboard (e.g., Prometheus + Grafana).

### **3. Use Transactions Wisely**
- Keep transactions **short-lived** (e.g., per-record updates).
- Avoid locking tables for too long.

### **4. Plan for Rollback**
- If a batch fails, **undo previous updates** using compensating transactions.
- Example:
  ```python
  def undo_update(user_id: int):
      requests.post(
          "https://user-service/api/preferences/revert",
          json={"user_id": user_id}
      )
  ```

### **5. Document the Process**
- Write a **runbook** for retrying failed batches.
- Document **idempotency keys** and **dead-letter queue** usage.

---

## **Common Mistakes to Avoid**

| Mistake                          | Why It’s Bad                          | Fix                          |
|----------------------------------|---------------------------------------|------------------------------|
| **No batch processing**          | Locks entire database for hours.      | Use `LIMIT` and `OFFSET`.    |
| **No retries on failure**        | Failed updates get lost.              | Implement exponential backoff.|
| **No idempotency**               | Same record updated multiple times.   | Use `last_updated_at` checks.|
| **No monitoring**                | No visibility into progress/failures. | Log everything!              |
| **Not testing in staging**       | Production outages.                   | Mimic production data.       |

---

## **Key Takeaways**

✅ **Batch processing** prevents locks and keeps the system responsive.
✅ **Dead-letter queues** ensure no record is permanently lost.
✅ **Idempotency keys** prevent duplicate updates.
✅ **CDC (Change Data Capture)** keeps downstream services in sync.
✅ **Compensating transactions** let you roll back safely.
✅ **Monitor everything**—migrations can go wrong even with the best plan.

---

## **Conclusion**

Distributed migrations are **not** a one-time task—they’re a **process**. By adopting the Distributed Migration pattern, you can update data safely across services, handle failures gracefully, and keep your system running smoothly.

### **Next Steps**
- Try this pattern with a **small dataset** in staging.
- Explore **CDC tools** like Debezium or AWS DMS for real-time syncs.
- Automate retries and rollbacks with **Kubernetes CronJobs** or **Airflow**.

Now go forth and migrate with confidence!

---
**Want more?**
- [Distributed Transactions: Saga Pattern](link)
- [Event Sourcing for Auditability](link)
- [How We Migrated 10 Million Users Without Downtime](case-study-link)
```