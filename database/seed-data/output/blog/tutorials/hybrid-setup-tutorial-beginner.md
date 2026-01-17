```markdown
# **Hybrid Setup Pattern: Balancing Traditional Databases with Modern APIs**

*How to combine relational databases with NoSQL or microservices for scalable, flexible backends*

---

## **Introduction**

Building a modern backend system often feels like a balancing act: you need the **strong consistency** of relational databases (RDBMS) for core transactions, but also the **scalability** and **flexibility** of NoSQL for user data, logs, or analytics. Meanwhile, APIs must serve both structured queries and real-time demands—often from multiple services.

This is where the **Hybrid Setup Pattern** shines. Instead of locking yourself into a single database type (SQL-only or NoSQL-only), you **combine multiple database systems**—each optimized for its role—while keeping a clean API layer to abstract their differences. This approach is widely used in:
- **E-commerce platforms** (PostgreSQL for inventory, MongoDB for product metadata)
- **Social media apps** (MySQL for core user relationships, Firebase for push notifications)
- **Fintech applications** (Cassandra for high-velocity transactions, Elasticsearch for search)

But like any pattern, it has tradeoffs. In this guide, we’ll explore:
✅ Why monolithic database setups often fail at scale
✅ How to design a hybrid architecture with real-world examples
✅ Practical techniques for querying across databases
✅ Common pitfalls and how to avoid them

Let’s dive in.

---

## **The Problem: When a Single Database Isn’t Enough**

Imagine you’re building a **ride-sharing app** called `SwiftRide`.

### **Challenge 1: Schema Rigidity in RDBMS**
Ride requests, driver availability, and user profiles all need to be stored. With a traditional RDBMS (e.g., PostgreSQL), you might model it like this:

```sql
-- PostgreSQL schema for SwiftRide
CREATE TABLE users (
  user_id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  wallet_balance DECIMAL(10, 2) DEFAULT 0.00
);

CREATE TABLE rides (
  ride_id SERIAL PRIMARY KEY,
  user_id INT REFERENCES users(user_id),
  driver_id INT REFERENCES users(user_id),
  start_location TEXT NOT NULL,
  end_location TEXT NOT NULL,
  status VARCHAR(20) DEFAULT 'pending' -- 'accepted', 'completed', 'cancelled'
);

CREATE TABLE ride_history (
  ride_id INT REFERENCES rides(ride_id),
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (ride_id, timestamp)
);
```

👉 **Problem:**
- **Joins get expensive** when querying driver availability alongside user profiles.
- **Scaling reads** requires sharding, which complicates transactions.
- **Flexibility suffers**—updating the schema (e.g., adding driver ratings) requires migrations.

### **Challenge 2: NoSQL’s Weak Consistency for Critical Data**
Switching to a NoSQL database like MongoDB might look like this:

```json
// MongoDB schema for SwiftRide (simplified)
{
  "_id": "user_123",
  "name": "Alex Johnson",
  "email": "alex@example.com",
  "wallet_balance": 50.00,
  "rides": [
    {
      "ride_id": "ride_456",
      "status": "completed",
      "driver": "driver_789"
    }
  ]
}
```

👉 **Problem:**
- **Eventual consistency** means race conditions when updating `wallet_balance` during ride payments.
- **No native joins** make complex queries (e.g., "Show me drivers near me with 5-star ratings") harder.
- **Data duplication** happens (e.g., storing ride history in both the `user` and `driver` documents).

### **Challenge 3: API Bottlenecks**
Your API layer must now:
- Handle **mixed read patterns** (some queries need joins, others don’t).
- Manage **distributed transactions** (e.g., deducting money from a user’s wallet and adding it to a driver’s earnings).
- Support **real-time updates** (e.g., live driver tracking) without blocking the primary DB.

👉 **Result:** **Monolithic databases and APIs become the weakest link** in scalable systems.

---

## **The Solution: Hybrid Setup Pattern**

The **Hybrid Setup Pattern** resolves these issues by:
1. **Using multiple databases**, each optimized for their role.
2. **Designing an API layer** that abstracts database differences.
3. **Implementing compensating transactions** for consistency across databases.

### **Key Components of a Hybrid Setup**
| Component          | Purpose                                                                 | Example Tools                                  |
|--------------------|-------------------------------------------------------------------------|-----------------------------------------------|
| **Primary DB**     | Core transactions (ACID compliance)                                     | PostgreSQL, MySQL                             |
| **Secondary DB**   | Flexible, high-write data (e.g., logs, user activity)                   | MongoDB, Cassandra                           |
| **Search DB**      | Fast, full-text search (e.g., product discovery, driver location)       | Elasticsearch, Redis (with Geo queries)       |
| **Cache Layer**    | Reduce DB load for read-heavy operations                                | Redis, Memcached                              |
| **Event Bus**      | Decouple changes across databases (e.g., ride status update triggers a DB write) | Kafka, RabbitMQ                              |
| **API Gateway**    | Route requests to the correct backend service                            | Kong, AWS API Gateway                         |

---

## **Implementation Guide**

Let’s rebuild `SwiftRide` with a **hybrid setup**.

### **1. Database Schema Design**
| Database   | Purpose                          | Example Tables/Collections                     |
|------------|----------------------------------|-----------------------------------------------|
| **PostgreSQL** | ACID transactions (wallet, ride status) | `users`, `rides`, `wallet_transactions`      |
| **MongoDB**    | Flexible ride history, user activity | `user_activity`, `ride_history`              |
| **Elasticsearch** | Fast driver/ride search          | `drivers_index`, `rides_index`                |

#### **Example: PostgreSQL for Core Transactions**
```sql
-- PostgreSQL: Core user and wallet data
CREATE TABLE users (
  user_id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  wallet_balance DECIMAL(10, 2) NOT NULL DEFAULT 0.00
);

CREATE TABLE rides (
  ride_id SERIAL PRIMARY KEY,
  user_id INT REFERENCES users(user_id),
  driver_id INT REFERENCES users(user_id),
  start_location TEXT NOT NULL,
  end_location TEXT NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'pending',
  fare DECIMAL(10, 2) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add a trigger to update timestamps
CREATE OR REPLACE FUNCTION update_ride_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = CURRENT_TIMESTAMP;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_ride_time
BEFORE UPDATE ON rides
FOR EACH ROW EXECUTE FUNCTION update_ride_timestamp();
```

#### **Example: MongoDB for Ride History**
```json
// MongoDB: Flexible ride history (time-series data)
{
  "_id": ObjectId("507f1f77bcf86cd799439011"),
  "ride_id": "ride_456",
  "user_id": "user_123",
  "driver_id": "driver_789",
  "status": "completed",
  "timestamp": ISODate("2023-10-15T10:00:00Z"),
  "location_history": [
    { "lat": 37.7749, "lng": -122.4194, "timestamp": ISODate("2023-10-15T10:00:00Z") },
    { "lat": 37.7849, "lng": -122.4094, "timestamp": ISODate("2023-10-15T10:05:00Z") }
  ]
}
```

#### **Example: Elasticsearch for Driver Search**
```json
// Elasticsearch: Driver index for location-based queries
{
  "_index": "drivers",
  "_id": "driver_789",
  "name": "Jane Doe",
  "rating": 4.8,
  "last_active": "2023-10-15T14:30:00Z",
  "location": {
    "lat": 37.7800,
    "lng": -122.4000
  },
  "vehicle": "Toyota Camry"
}
```

---

### **2. API Layer: Abstracting Database Differences**
Your API should **not** expose the hybrid nature of the backend. Instead, it should:
- Use a **service layer** to handle database-specific logic.
- Implement **adapters** to convert between API responses and database formats.

#### **Example: FastAPI Service Layer (Python)**
```python
# services/ride_service.py
from fastapi import HTTPException
from databases import Database
from pymongo import MongoClient
from elasticsearch import Elasticsearch

# Database connections
db_postgres = Database("postgresql://user:pass@localhost/swiftride")
db_mongo = MongoClient("mongodb://localhost:27017/")
es = Elasticsearch("http://localhost:9200")

class RideService:
    async def create_ride(self, user_id: int, driver_id: int, start: str, end: str, fare: float):
        # 1. Start a transaction in PostgreSQL
        async with db_postgres.acquire() as conn:
            await conn.execute("""
                INSERT INTO rides (user_id, driver_id, start_location, end_location, fare, status)
                VALUES (:user_id, :driver_id, :start, :end, :fare, 'accepted')
            """, {
                "user_id": user_id,
                "driver_id": driver_id,
                "start": start,
                "end": end,
                "fare": fare
            })

            # 2. Update wallet balances (compensating transaction)
            await conn.execute("""
                UPDATE users SET wallet_balance = wallet_balance - :fare WHERE user_id = :user_id
                RETURNING wallet_balance
            """, {"fare": fare, "user_id": user_id})

            user_balance = await conn.fetch_one("SELECT wallet_balance FROM users WHERE user_id = :user_id", {"user_id": user_id})
            if user_balance["wallet_balance"] < 0:
                await conn.rollback()  # Compensating transaction: Reject if insufficient funds
                raise HTTPException(status_code=400, detail="Insufficient funds")

            # 3. Log ride in MongoDB
            await db_mongo["ride_history"].insert_one({
                "ride_id": user_balance["user_id"],  # TODO: Fix this (placeholder)
                "user_id": user_id,
                "driver_id": driver_id,
                "status": "accepted",
                "timestamp": datetime.now()
            })

            # 4. Index ride in Elasticsearch for search
            await es.index(
                index="rides",
                id=f"ride_{user_balance['user_id']}",
                document={
                    "user_id": user_id,
                    "driver_id": driver_id,
                    "status": "accepted",
                    "start": start,
                    "end": end
                }
            )

            return {"message": "Ride created successfully"}
```

---

### **3. Handling Distributed Transactions**
Since PostgreSQL and MongoDB are separate, you **cannot** use native transactions across them. Instead:
1. **Use compensating transactions** (roll back changes if a step fails).
2. **Implement eventual consistency** for non-critical data (e.g., ride history).
3. **Use an event bus** (e.g., Kafka) to sync changes asynchronously.

#### **Example: Kafka Event for Ride Status Update**
```python
# After updating PostgreSQL, publish an event
from confluent_kafka import Producer

conf = {'bootstrap.servers': 'localhost:9092'}
producer = Producer(conf)

def publish_ride_event(topic: str, event_data: dict):
    producer.produce(topic, json.dumps(event_data).encode('utf-8'))
    producer.flush()

# Inside RideService.create_ride():
publish_ride_event(
    "ride-updates",
    {
        "event_type": "ride_created",
        "ride_id": "ride_123",
        "user_id": user_id,
        "driver_id": driver_id,
        "status": "accepted"
    }
)
```

Then, a **consumer service** listens to this topic and updates MongoDB/Elasticsearch:
```python
# consumer.py
from confluent_kafka import Consumer
import json
from pymongo import MongoClient

conf = {'bootstrap.servers': 'localhost:9092', 'group.id': 'ride-consumer'}
consumer = Consumer(conf)
consumer.subscribe(['ride-updates'])

db = MongoClient("mongodb://localhost:27017/")

while True:
    msg = consumer.poll(1.0)
    if msg is None:
        continue
    if msg.error():
        print(f"Error: {msg.error()}")
        continue

    event = json.loads(msg.value().decode('utf-8'))
    if event["event_type"] == "ride_created":
        db["ride_history"].insert_one({
            "ride_id": event["ride_id"],
            "user_id": event["user_id"],
            "driver_id": event["driver_id"],
            "status": event["status"],
            "timestamp": datetime.now()
        })
```

---

## **Common Mistakes to Avoid**

### **1. Overloading a Single Database**
❌ **Mistake:** Storing **all** user data in MongoDB while keeping only transactions in PostgreSQL.
✅ **Fix:** Use PostgreSQL for **critical data** (wallet, ride status) and MongoDB for **supplementary data** (ride history, activity logs).

### **2. Ignoring Eventual Consistency**
❌ **Mistake:** Treating the hybrid setup like a single database (e.g., expecting ride history to match PostgreSQL immediately).
✅ **Fix:** Design APIs to accept minor inconsistencies (e.g., "Show me my last 10 rides" may return slightly stale data).

### **3. Not Implementing Compensating Transactions**
❌ **Mistake:** Assuming PostgreSQL and MongoDB will always stay in sync.
✅ **Fix:** Use **retries**, **dead-letter queues**, or **saga patterns** to handle failures.

### **4. Tight Coupling Between Services**
❌ **Mistake:** Having the API directly query multiple databases without a service layer.
✅ **Fix:** Abstract database logic into **services** (like `RideService` above).

### **5. Forgetting to Cache Frequently Accessed Data**
❌ **Mistake:** Querying PostgreSQL **every time** a user’s profile is loaded.
✅ **Fix:** Use **Redis** to cache user data with a **short TTL** (e.g., 5 minutes).

---

## **Key Takeaways**
✔ **Hybrid setups work best when:**
   - Your data has **mixed access patterns** (some need joins, others don’t).
   - You need **scalability** for certain workloads (e.g., search, logs).
   - You can tolerate **eventual consistency** for non-critical data.

✔ **Best practices:**
   - Use **PostgreSQL/MySQL** for **ACID transactions**.
   - Use **MongoDB/Cassandra** for **flexible, high-write data**.
   - Use **Elasticsearch** for **search-heavy queries**.
   - **Abstract databases** behind services to hide complexity.
   - **Sync changes asynchronously** using event buses.

✔ **Tradeoffs to accept:**
   - **Complexity** increases (more moving parts).
   - **Eventual consistency** means some reads may return stale data.
   - **Debugging** is harder (distributed transactions).

---

## **Conclusion**

The **Hybrid Setup Pattern** is a powerful way to balance the strengths of relational and NoSQL databases while building scalable APIs. By carefully choosing which database to use for which role and designing a robust service layer, you can avoid the pitfalls of monolithic setups.

### **When to Use This Pattern?**
✅ Your app has **mixed data models** (structured + unstructured).
✅ You need **ACID compliance for core data** but **scalability for others**.
✅ You’re okay with **eventual consistency** where it matters least.

### **When to Avoid It?**
❌ Your app is **simple** (a single table in PostgreSQL suffices).
❌ You **cannot tolerate** eventual consistency (e.g., banking).
❌ Your team lacks experience with **distributed systems**.

---
### **Next Steps**
1. **Experiment locally:** Set up PostgreSQL + MongoDB + Elasticsearch and build a small service.
2. **Add caching:** Use Redis to reduce DB load.
3. **Implement event sourcing:** Log all changes to a stream (Kafka) for replayability.

The hybrid approach may seem complex, but it’s the **future of scalable backends**. Start small, iterate, and you’ll build systems that **scale with your users**.

---
**Happy coding!** 🚀
```