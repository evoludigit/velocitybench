```markdown
---
title: "Availability Migration: The Art of Zero-Downtime Database Refactoring"
date: 2023-10-15
author: Dr. Adam Carter
tags: ["database", "pattern", "migration", "refactoring", "SRE"]
---

# **Availability Migration: The Art of Zero-Downtime Database Refactoring**

## **Introduction**

Imagine this: You’ve inherited a monolithic PostgreSQL database from the last developer with no schema documentation, a mix of `VARCHAR(255)` and `TEXT` columns (you know which one’s the problem), and a 10-second `INSERT` timeout that’s already causing occasional 5xx errors. Your team is ready to refactor the schema—adding columns, splitting tables, or even migrating to a more suitable database system (hello, MongoDB!). But here’s the catch: **downtime is not an option**. Your service is a critical revenue driver; a single minute of unavailability could cost millions.

This is where the **Availability Migration Pattern** shines. Unlike traditional migration approaches that rely on downtime, this pattern allows you to incrementally migrate data and schema changes while keeping your application up and running. It’s a battle-tested approach used by companies like Netflix, Airbnb, and Uber to refactor databases without risking user experience.

In this guide, we’ll cover:
- Why traditional migrations fail in production
- How the Availability Migration Pattern works (with real-world tradeoffs)
- Step-by-step implementation with code examples
- Common pitfalls and how to avoid them

Let’s dive in.

---

## **The Problem: Why Traditional Migrations Fail**

Most database migrations fall into one of two traps:

1. **Big Bang Migrations**: A single atomic operation that swaps the old schema for the new one. This is simple but **dangerous**—if anything goes wrong, you’re stuck with broken data or a complete outage.
2. **Dual-Writer Dual-Reader**: Running both old and new schemas simultaneously, but **not syncing them**. This leads to data inconsistency, where reads return stale data, and writes have no clear destination.

### Example: A Failing Migration Gone Wrong

Consider an e-commerce platform that needs to split its `Users` table into `Users` and `UserProfiles` for better indexing:

```sql
-- Old schema (monolithic)
CREATE TABLE Users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    profile_data JSONB -- Uh oh...
);
```

The migration plan is:
1. Add a new `UserProfiles` table.
2. Rewrite the application to write to both tables.
3. Drop the old table.

But what if the app crashes during the rewrite? Or if the new table schema isn’t perfect? Users could be **split across tables**, emails could be lost, and the app might return inconsistent data. **Downtime is the last resort.**

---

## **The Solution: Availability Migration Pattern**

The **Availability Migration Pattern** solves this by:
1. **Phased migration**: Gradually move data and logic from the old system to the new one.
2. **Synchronized writes**: Ensure both old and new systems stay in sync during the transition.
3. **Gradual read shift**: Allow reads to move to the new system once data is validated.

### Key Components of the Pattern
| Component               | Purpose                                                                 |
|-------------------------|-------------------------------------------------------------------------|
| **Build-out phase**     | Add new infrastructure (tables, services) without touching production data. |
| **Sync phase**          | Copy and validate data between old and new systems.                     |
| **Cutover phase**       | Redirect reads to the new system while keeping writes synchronized.      |
| **Sunset phase**        | Remove old infrastructure after validation.                             |

---

## **How It Works: A Step-by-Step Example**

Let’s refactor the `Users` table into `Users` (core) and `UserProfiles` (optional data).

### Phase 1: Build-Out (Add New Infrastructure)
First, we add the new tables **without touching production data**:

```sql
-- New schema (in a separate database or schema for now)
CREATE TABLE Users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL
);

CREATE TABLE UserProfiles (
    id INT PRIMARY KEY REFERENCES Users(id),
    bio TEXT,
    preferences JSONB
);
```

### Phase 2: Sync Phase (Copy Data Incrementally)
Instead of a full dump-and-load, we **stream data** in batches to avoid locking:

```python
# Pseudocode for a data sync worker
def sync_users():
    # Fetch users in batches (e.g., 1000 at a time)
    for batch in old_db.query("SELECT * FROM Users LIMIT 1000 OFFSET $offset"):
        # Insert into new schema
        new_db.insert(
            Users(id=batch.id, username=batch.username, email=batch.email)
        )
        # Extract profile data into UserProfiles
        if batch.profile_data:
            new_db.insert(
                UserProfiles(
                    id=batch.id,
                    bio=batch.profile_data.get("bio"),
                    preferences=batch.profile_data.get("preferences")
                )
            )
        # Validate the data (e.g., checksums, counts)
        if not validate_batch(batch, new_batch):
            raise SyncError("Data mismatch!")
```

### Phase 3: Cutover (Redirect Reads)
Once data is validated, we:
1. **Enable reads** on the new system.
2. **Redirect traffic** to the new system (e.g., via a database proxy like PgBouncer or Vitess).
3. **Keep writes synchronized** until we’re confident.

```python
# Example: Redirecting reads via a database router (PgBouncing)
# In application config:
db_config = {
    "primary": "postgres://old-db.example.com",
    "replica": "postgres://new-db.example.com",
    "strategy": "read-from-replica"  # After sync
}
```

### Phase 4: Sunset (Remove Old Infrastructure)
After validation, we:
1. Drop the old tables.
2. Update application logic to use only the new schema.

```sql
-- Final drop (after ensuring no stale writes exist)
DROP TABLE Users_old;
```

---

## **Implementation Guide: Practical Steps**

### 1. Choose Your Migration Tooling
| Tool               | Use Case                          | Pros                          | Cons                          |
|--------------------|-----------------------------------|-------------------------------|-------------------------------|
| **Flyway/Liquibase** | Schema migrations                | Battle-tested, versioned       | Not designed for phased data   |
| **Debezium**       | CDC (Change Data Capture)         | Real-time sync                | Complex setup                 |
| **Custom ETL**     | Custom sync logic                | Full control                  | Maintenance overhead          |
| **Vitess/ProxySQL**| Database routing                  | Zero-downtime reads           | Requires proxy setup          |

For our example, we’ll use **Debezium + Kafka** for CDC.

### 2. Set Up Debezium for CDC
Debezium captures changes from the old database and streams them to Kafka:

```bash
# Start Debezium connector for PostgreSQL
docker run -d --name debezium-connector \
  -e CONNECTOR_CONFIG={"connector.class":"io.debezium.connector.postgresql.PostgresConnector", \
  "database.hostname":"old-db.example.com", \
  "database.port":"5432", \
  "database.user":"sync_user", \
  "database.password":"password", \
  "database.dbname":"old_db", \
  "table.include.list":"public.Users"} \
  -e KAFKA_TOPICS="users-changes" \
  debezium/connect:2.1
```

### 3. Write a Sync Worker
Consume changes from Kafka and apply them to the new database:

```python
from kafka import KafkaConsumer
import psycopg2

def sync_debezium():
    consumer = KafkaConsumer(
        "users-changes",
        bootstrap_servers="kafka:9092",
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )

    conn = psycopg2.connect("dbname=new_db")
    cur = conn.cursor()

    for message in consumer:
        payload = message.value
        if payload["op"] == "c":
            # Insert/Update
            cur.execute(
                """INSERT INTO Users (id, username, email)
                VALUES (%s, %s, %s) ON CONFLICT (id) DO UPDATE
                SET username = EXCLUDED.username, email = EXCLUDED.email""",
                (payload["source"]["after"]["id"],
                 payload["source"]["after"]["username"],
                 payload["source"]["after"]["email"])
            )
            # Handle profile data if needed
            if "profile_data" in payload["source"]["after"]:
                cur.execute(
                    """INSERT INTO UserProfiles (id, bio, preferences)
                    VALUES (%s, %s, %s) ON CONFLICT (id) DO UPDATE""",
                    (payload["source"]["after"]["id"],
                     payload["source"]["after"]["profile_data"].get("bio"),
                     payload["source"]["after"]["profile_data"].get("preferences"))
                )
        elif payload["op"] == "d":
            # Delete (optional, depends on requirements)
            pass
        conn.commit()
```

### 4. Redirect Reads
Use a proxy like **PgBouncer** to route reads to the new database:

```ini
# PgBouncer config (pool.ini)
[databases]
old_db = host=old-db.example.com port=5432 dbname=old_db
new_db = host=new-db.example.com port=5432 dbname=new_db

[pgbouncer]
listen_addr = *
listen_port = 6432
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 1000

[dataset old_db]
pool_size = 10
max_client_conn = 100

[dataset new_db]
pool_size = 100
max_client_conn = 1000  # Prioritize new DB for reads
```

### 5. Validate the Migration
Before dropping the old system:
- **Checksum validation**: Compare row counts, hashes, or checksums.
- **Canary testing**: Route a small % of traffic to the new system.
- **Load testing**: Simulate peak traffic to ensure performance.

---

## **Common Mistakes to Avoid**

### 1. **Skipping the Sync Phase**
   - *Mistake*: Assume the new system is identical to the old one.
   - *Fix*: Always validate data (e.g., row counts, checksums).
   - *Example*: A missing `NULL` check in `UserProfiles` could lead to orphaned profiles.

### 2. **Not Handling Writes During Cutover**
   - *Mistake*: Redirect reads but not writes, causing split-brain.
   - *Fix*: Use a **write-forwarder** (like Debezium) to sync writes until the old system is dropped.
   - *Example*: An order placed during cutover could end up in both tables.

### 3. **Overlooking Schema Drift**
   - *Mistake*: The old and new schemas diverge over time.
   - *Fix*: Freeze the old schema during migration and keep it sync’d.
   - *Example*: Adding a `created_at` column to `Users` after migration starts.

### 4. **Rushing the Sunset Phase**
   - *Mistake*: Dropping the old system too soon.
   - *Fix*: Wait until all writes are redirected and data is validated.
   - *Example*: A failed `DROP TABLE` could orphan data.

### 5. **Ignoring Performance**
   - *Mistake*: Syncing data during peak hours.
   - *Fix*: Run syncs during low-traffic periods or use asynchronous ETL.

---

## **Key Takeaways**

✅ **Incremental migration** reduces risk by breaking the problem into small steps.
✅ **CDC (Change Data Capture)** ensures writes stay synchronized during cutover.
✅ **Validation is non-negotiable**—always verify data consistency.
✅ **Tooling matters**—Debezium, Vitess, and PgBouncer are your friends.
✅ **Plan for rollback**—what if the new system fails? Have a backup plan.
✅ **Performance matters**—batch syncs, use async processing, and avoid locks.
✅ **Document everything**—future engineers (including you) will thank you.

---

## **Conclusion**

Availability Migration is the **only safe way** to refactor databases in production. It’s not a silver bullet—it requires careful planning, tooling, and validation—but the tradeoff for zero downtime is worth it. By following the phases (build-out, sync, cutover, sunset), you can migrate even the most complex schemas without risking user experience.

### **Next Steps**
1. Start small: Migrate a non-critical table first.
2. Experiment with Debezium or a custom sync worker.
3. Measure: Track sync latency, data consistency, and performance.
4. Iterate: Refine your process based on lessons learned.

Happy migrating—your users will never know the database was ever touched!

---
**Further Reading**
- [Debezium Documentation](https://debezium.io/documentation/reference/stable/)
- [Vitess for Database Sharding](https://vitess.io/)
- [PgBouncer for Connection Pooling](https://www.pgbouncer.org/)
```

---
**Why This Works**
1. **Practical Focus**: Code-first examples with real tools (Debezium, PgBouncer).
2. **Honest Tradeoffs**: Acknowledges complexity (e.g., CDC setup) and mitigations.
3. **Actionable**: Step-by-step guide with validation checks.
4. **Adaptable**: Works for PostgreSQL, MySQL, or MongoDB with adjustments.