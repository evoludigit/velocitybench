```markdown
---
title: "Availability Migration: The Pattern for Seamless Data Mobility"
date: 2023-10-15
tags: ["database design", "data migration", "API patterns", "backend engineering"]
author: "Alex Carter"
---

# **Availability Migration: The Pattern for Seamless Data Mobility**

## **Introduction**

Data is the lifeblood of modern applications. Whether you're scaling a monolith to microservices, moving from on-premises to the cloud, or simply optimizing your database infrastructure, **moving data efficiently—and without downtime—is a critical challenge**.

This is where the **Availability Migration (AvailMig)** pattern comes in. Unlike traditional data migration—which often involves full cutovers, downtime, or brittle ETL pipelines—Availability Migration focuses on **incremental, low-risk transfers of data while maintaining operational availability**. It’s the approach used by companies like Uber, Airbnb, and Netflix to handle massive data shifts without disrupting users.

In this guide, we’ll break down:
- The core problem of traditional migrations—and why they fail.
- How the Availability Migration pattern solves it with **phased, concurrent data syncs**.
- Practical code examples in Python (for API endpoints) and SQL (for database operations).
- Key tradeoffs, anti-patterns, and best practices.

By the end, you’ll have a battle-tested pattern you can apply to your next database or cloud migration.

---

## **The Problem: Why Traditional Migrations Break**

Most developers approach data migration with one of two strategies:

1. **Big Bang Cutover** – Freeze the system, transfer all data at once, then restart.
2. **ETL Pipelines** – Use batch jobs (e.g., Airflow, Spark) to move data in large chunks over time.

Both approaches have **critical flaws**:

### **1. Big Bang Cutovers Cause Downtime**
- **Example**: A payment processing system migrates from PostgreSQL to CockroachDB.
  If the new cluster isn’t ready or data is corrupted during transfer, users lose access to transactions—**costing millions in lost revenue**.

```sql
-- A failed big-bang migration might look like this:
BEGIN TRANSACTION;
-- Try to copy 10M rows in one shot → locks table, crashes → system down.
COMMIT;
```

### **2. ETL Pipelines Are Brittle & Slow**
- **Example**: A social media app moves user data from MySQL to DynamoDB.
  - **Problem**: The ETL job fails midway, leaving some users’ data in MySQL and others in DynamoDB.
  - **Outcome**: Inconsistent views, API responses, and even compliance violations.

```python
# A naive ETL script (pseudo-code)
def migrate_users():
    for user in old_db.query("SELECT * FROM users"):
        new_db.put_item(user)
    # If the script crashes here, half the users are missing!
```

### **3. API Layer Doesn’t Match Data Layer**
- **Example**: A frontend fetches `GET /users/123` from a legacy API, but the new database has stale data.
  - **Result**: Users see incorrect info (e.g., "Your account is inactive" when it’s *actually* active).

---
## **The Solution: Availability Migration**

The **Availability Migration** pattern solves these issues by **moving data in parallel with the old system**, ensuring:
✅ **Zero downtime** – Read/write continues during migration.
✅ **Eventual consistency** – APIs serve from both systems until fully synced.
✅ **Fail-safe** – If the new system fails, the old one remains operational.

### **How It Works (High-Level)**
1. **Dual-Write Phase**: Write to **both old and new systems** until the new one is ready.
2. **Shadow Read Phase**: Serve reads from the **new system** while maintaining the old one for fallbacks.
3. **Cutover**: Once the new system is verified, switch **all traffic** to it.

---

## **Components of Availability Migration**

### **1. Dual-Write Proxy (Layer 1)**
A service that **forwards writes to both databases** until migration is complete.

**Example**: A Flask endpoint that writes to PostgreSQL *and* MongoDB.

```python
from flask import Flask, request
import psycopg2
from pymongo import MongoClient

app = Flask(__name__)

# Connect to both databases
postgres_conn = psycopg2.connect("dbname=legacy dbuser=postgres")
mongodb_conn = MongoClient("mongodb://legacy-host")

@app.route('/users', methods=['POST'])
def create_user():
    data = request.json
    user_id = data['id']

    # Write to both systems
    with postgres_conn.cursor() as cur:
        cur.execute("INSERT INTO users VALUES (%s, %s)", (user_id, data['name']))

    mongodb_conn['users'].insert_one(data)

    return {"status": "Dual-written"}, 201
```

**Tradeoff**:
- **Slower writes** (double database latency).
- **Eventual consistency** (new system may lag slightly).

---

### **2. Two-Phase Read Proxy (Layer 2)**
A service that **prioritizes the new system** but falls back to the old one if needed.

**Example**: A Python API gateway using `redis` for caching.

```python
from flask import Flask, jsonify
import redis
import requests

app = Flask(__name__)
cache = redis.Redis(host='cache-server')

def get_user_from_new_db(user_id):
    try:
        response = requests.get(f"http://new-api/users/{user_id}")
        return response.json()
    except requests.RequestException:
        return None  # Fallback to old DB

def get_user_from_old_db(user_id):
    response = requests.get(f"http://old-api/users/{user_id}")
    return response.json()

@app.route('/users/<int:user_id>')
def get_user(user_id):
    # Check cache first
    cache_key = f"user:{user_id}"
    user = cache.get(cache_key)

    if user:
        return jsonify(user)

    # Try new DB first, then old DB
    new_user = get_user_from_new_db(user_id)
    if new_user:
        cache.set(cache_key, new_user)
        return jsonify(new_user)

    # Fallback to old DB
    old_user = get_user_from_old_db(user_id)
    cache.set(cache_key, old_user)
    return jsonify(old_user)
```

**Tradeoff**:
- **Inconsistent reads** (temporary mismatches between systems).
- **Cache invalidation complexity** (must handle stale reads).

---

### **3. Migration Status Tracker (Layer 3)**
A dashboard or API to monitor sync progress.

**Example**: A simple SQL table tracking migration health.

```sql
-- Track migration sync status
CREATE TABLE migration_status (
    system_name VARCHAR(50) PRIMARY KEY,
    last_sync_timestamp TIMESTAMP,
    record_count_big_bang INT,
    record_count_dual_write INT,
    is_healthy BOOLEAN DEFAULT FALSE
);

-- Insert initial state
INSERT INTO migration_status VALUES
('new_postgres', NOW(), 0, 0, FALSE);
```

**Example Python script to update sync status**:
```python
import psycopg2
from datetime import datetime

def update_sync_status():
    conn = psycopg2.connect("dbname=new_db")
    cur = conn.cursor()

    # Count records in new DB
    cur.execute("SELECT COUNT(*) FROM users")
    new_count = cur.fetchone()[0]

    # Update status
    cur.execute(
        "UPDATE migration_status SET "
        "last_sync_timestamp = %s, "
        "record_count_dual_write = %s, "
        "is_healthy = TRUE WHERE system_name = 'new_postgres'",
        (datetime.now(), new_count)
    )
    conn.commit()
```

**Tradeoff**:
- **Requires extra monitoring overhead**.
- **False positives/negatives** if health checks are simplistic.

---

### **4. Cutover Script (Layer 4)**
A **one-time** switch to the new system.

**Example**: A PostgreSQL `ALTER TABLE` + API rewrite.

```sql
-- Step 1: Verify sync is complete
SELECT COUNT(*) FROM migration_status WHERE is_healthy = TRUE;

-- Step 2: Drop foreign keys (if any)
ALTER TABLE users DROP FOREIGN KEY IF EXISTS fk_old_system;

-- Step 3: Rewrite API to point only to new DB
-- (Update config files or use feature flags)
```

**Tradeoff**:
- **Still requires coordination** (e.g., stopping writes to old DB).
- **Rollback risk** if something fails.

---

## **Implementation Guide: Step-by-Step**

### **Phase 1: Dual-Write Setup**
1. **Deploy the dual-write proxy** (e.g., a Lambda function, Flask app, or Kubernetes service).
2. **Log dual-writes** for reconciliation (e.g., track IDs written to both systems).
3. **Monitor for conflicts** (e.g., timestamps mismatches).

**Example conflict detection**:
```python
def check_for_conflicts():
    # Compare timestamps of the same record in both DBs
    postgres_times = postgres_conn.execute("SELECT created_at FROM users WHERE id = 123")
    mongo_times = mongodb_conn['users'].find_one({"id": 123})['created_at']
    if postgres_times != mongo_times:
        raise ConflictError("Timestamps don’t match!")
```

---

### **Phase 2: Shadow Read Deployment**
1. **Deploy the read proxy** (Layer 2).
2. **Set up a cache** (Redis, Memcached) to reduce DB load.
3. **Gradually shift traffic** to the new system (e.g., 10% → 50% → 100%).

**Example traffic shift script**:
```bash
# Use AWS ALB or Nginx to shift weights
# Start with 10% new DB, 90% old DB
aws elbv2 modify-load-balancer-attributes --load-balancer-arn <arn> --attributes Key=routing.http2.target_group.health_check.path,Value=/health
```

---

### **Phase 3: Cutover**
1. **Verify sync completion** (e.g., `record_count_big_bang == record_count_dual_write`).
2. **Disable writes to the old DB** (e.g., update API to reject writes).
3. **Update DNS/CDN** to point to the new DB.
4. **Monitor for errors** (e.g., 5xx responses, timeouts).

**Example cutover script**:
```python
# Disable writes to old DB (e.g., via API gateway)
import boto3

def disable_old_db_writes():
    client = boto3.client('apigateway')
    response = client.put_integration(
        restApiId='old-api-id',
        resourceId='users-resource',
        type='AWS_PROXY',
        integrationHttpMethod='POST',
        credentialsArn='arn:aws:iam::123456789012:role/MigrationRole',
        requestTemplates={'application/json': '{"statusCode": 503}'}
    )
```

---

## **Common Mistakes to Avoid**

| **Mistake**               | **Why It’s Bad**                          | **How to Fix It**                          |
|---------------------------|------------------------------------------|-------------------------------------------|
| **No reconciliation layer** | How do you know the new DB is accurate? | Log dual-writes and compare checkpoints. |
| **No fallback mechanism**  | Users see errors when the new DB fails.  | Use read proxy with old-DB fallback.      |
| **Big-bang cutover**      | Downtime = lost revenue.                 | Use phased migration (shadow reads first). |
| **Ignoring cache**        | Stale reads break user trust.            | Invalidate cache aggressively.            |
| **No monitoring**         | You don’t know when to cut over.         | Track `is_healthy` and sync progress.     |

---

## **Key Takeaways**

✅ **Availability Migration = Zero Downtime**
- Dual-write + shadow reads → **no forced outages**.

✅ **Eventual Consistency Is Okay (Temporarily)**
- Users tolerate minor delays if the system stays up.

✅ **Monitor Everything**
- Track `record_count`, `latency`, and `error_rates` in both systems.

✅ **Fail Fast, Recover Gracefully**
- If the new DB crashes, **revert to the old one immediately**.

✅ **Cutover Is the Riskiest Step**
- Have a **rollback plan** (e.g., revert DNS, restart old DB).

---

## **Conclusion**

Availability Migration is **not a silver bullet**—it’s a **tradeoff**:
✔ **Pros**: Zero downtime, gradual risk reduction.
❌ **Cons**: Higher operational complexity, eventual consistency.

But for **large-scale systems** where uptime matters, it’s the **only viable approach**.

### **Next Steps**
1. **Start small**: Migrate a non-critical table first (e.g., `user_preferences`).
2. **Automate**: Use Terraform + CI/CD to deploy proxies.
3. **Test failures**: Simulate DB crashes to ensure fallbacks work.

By following this pattern, you’ll **avoid the pitfalls of big-bang migrations** and build systems that **scale without screaming**.

---
**What’s your biggest migration challenge?** Hit me up on [Twitter](https://twitter.com/alexcarterdev) or [GitHub](https://github.com/alexcarterdev) with your war stories—I’d love to hear them!
```

---
### **Why This Works**
- **Code-first**: Real Python/Flask/SQL examples show *how* to implement.
- **Honest tradeoffs**: Calls out the downsides (e.g., dual-write latency).
- **Actionable**: Step-by-step guide + anti-patterns help developers avoid mistakes.
- **Scalable**: Applies to monoliths → microservices, on-prem → cloud, etc.

Would you like me to expand on any section (e.g., database-specific optimizations for PostgreSQL vs. MongoDB)?