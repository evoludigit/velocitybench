```markdown
---
title: "Streaming Migration: The Zero-Downtime Approach to Database Refactoring"
date: 2023-11-15
tags: ["database", "design-patterns", "backend-engineering", "migration", "etl"]
excerpt: "Learn how to migrate millions of records without halting production with the Streaming Migration pattern—a battle-tested approach for zero-downtime database refactors."
---

# Streaming Migration: The Zero-Downtime Approach to Database Refactoring

The pain of a "big bang" database migration is familiar to us all. A single cutover window. The fear of downtime. The potential for data loss or corruption. In an era where high availability is a non-negotiable, these tradeoffs aren’t acceptable anymore.

In this post, we’ll dive into the **Streaming Migration** pattern—a battle-tested approach to zero-downtime database refactoring. We’ll explore its core components, demonstrate how it works with real-world code examples, and uncover the tradeoffs and pitfalls to avoid. By the end, you’ll have a practical toolkit to safely migrate millions of records without ever stopping your application.

---

## The Problem: Why Streaming Migrations?

### The Cost of Downtime
Consider a high-traffic application like a SaaS platform with millions of active users. A traditional database refactor requires:

```bash
# Example: Traditional migration steps
1. Finetune your data model
2. Build and test the new schema
3. Schedule a 24-hour maintenance window
4. Dump the old database → Load into new schema
5. Resume operations
```

If something goes sideways (network issues, corruption, or schema mismatches), you’re looking at hours of recovery time—during which users are frustrated and revenue is lost.

### The Scalability Trap
Even smaller migrations often hit walls:

- **Large volumes**: Moving millions of records at once can cause timeouts or lock contention.
- **Real-time systems**: Databases like PostgreSQL or MongoDB can’t easily pause writes for hours.
- **Data consistency**: Ensuring both old and new systems stay in sync during the transition is tricky.

### A Utopia We Can’t Afford
Most developers dream of “migrate while the system runs,” but how?

---

## The Solution: Streaming Migration

The **Streaming Migration** pattern answers these challenges with a simple principle:

> *"Migrate data incrementally, in small batches, while both systems remain live."*

This approach involves four core components:

1. **A source database** (the existing system)
2. **A target database** (the new schema)
3. **A streaming layer** (to extract and transform data in chunks)
4. **A reconciliation mechanism** (to handle discrepancies)

The magic happens when these components work together to ensure data consistency between systems.

---

## Components/Solutions: The Streaming Migration Toolkit

### 1. The Streaming Layer
This is where the real work happens. It’s responsible for:

- **Extracting data in small batches** (e.g., 1000 rows at a time)
- **Transforming data** (if needed) to fit the new schema
- **Sending data to the target** without blocking the source

Common tools for this layer:
- **Custom scripts** (Python, Node.js)
- **ETL pipelines** (Airflow, Dagster)
- **Database triggers** (PostgreSQL `PL/pgSQL`, MySQL triggers)

### 2. The Reconciliation Layer
Even with streaming, discrepancies can arise due to:
- Unprocessed records
- Failures
- Race conditions

The reconciliation layer ensures both systems stay in sync by:
- Tracking processed offsets (e.g., last record ID)
- Flagging stale data
- Automating recovery

### 3. The Dual-Write Strategy (Optional)
For critical systems, you may need to **write to both databases** during the transition. This ensures no data loss if the migration fails midway.

---

## Code Examples: Streaming Migration in Action

### Example 1: Python-Based Streaming Migration

Suppose we’re migrating from an old `users` table (PostgreSQL) to a new schema that includes `preferences`:

```sql
-- Old schema (users)
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  created_at TIMESTAMP NOT NULL
);

-- New schema (users_v2)
CREATE TABLE users_v2 (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  created_at TIMESTAMP NOT NULL,
  preferences JSONB
);
```

Here’s a Python script to stream the data:

```python
import psycopg2
import json
from tqdm import tqdm  # For progress tracking

def stream_users(source_conn, target_conn, batch_size=1000):
    # Source cursor
    with source_conn.cursor() as src_cur:
        src_cur.execute("SELECT id, name, email, created_at FROM users")

        # Target cursor
        with target_conn.cursor() as tgt_cur:
            last_offset = 0
            while True:
                # Fetch batch
                src_cur.execute(
                    "SELECT * FROM users LIMIT %s OFFSET %s",
                    (batch_size, last_offset)
                )
                records = src_cur.fetchall()

                if not records:
                    break

                # Transform and insert into new schema
                for record in records:
                    tgt_cur.execute(
                        """
                        INSERT INTO users_v2 (id, name, email, created_at, preferences)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            record[0],
                            record[1],
                            record[2],
                            record[3],
                            json.dumps({"dark_mode": True})  # Example transformation
                        )
                    )

                # Commit after each batch
                target_conn.commit()

                # Update offset
                last_offset += len(records)
                print(f"Processed {last_offset} records...")

# Example usage
source_conn = psycopg2.connect("source_db_uri")
target_conn = psycopg2.connect("target_db_uri")

stream_users(source_conn, target_conn)
```

### Example 2: PostgreSQL TRIGGER-Based Migration
For databases that support it, you can use triggers to stream writes:

```sql
-- Add a new column to the old table (for tracking migration status)
ALTER TABLE users ADD COLUMN is_migrated BOOLEAN DEFAULT FALSE;

-- Create a function to migrate data on write
CREATE OR REPLACE FUNCTION migrate_user()
RETURNS TRIGGER AS $$
BEGIN
    IF NOT NEW.is_migrated THEN
        -- Insert into new table (simplified for demo)
        INSERT INTO users_v2 (id, name, email, created_at)
        VALUES (NEW.id, NEW.name, NEW.email, NEW.created_at);

        -- Mark as migrated
        UPDATE users SET is_migrated = TRUE WHERE id = NEW.id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add trigger
CREATE TRIGGER tr_migrate_user
AFTER INSERT OR UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION migrate_user();
```

### Example 3: Kafka-Based Streaming (Advanced)
For distributed systems, a message queue like Kafka can orchestrate the migration:

```python
# Producer (consumes from source DB, emits to Kafka)
from confluent_kafka import Producer

def produce_user_records(source_conn):
    producer = Producer({"bootstrap.servers": "kafka:9092"})
    with source_conn.cursor() as src_cur:
        src_cur.execute("SELECT * FROM users")
        for record in src_cur:
            producer.produce(
                "users-migration",
                json.dumps(record).encode('utf-8')
            )
    producer.flush()

# Consumer (consumes from Kafka, inserts into target DB)
from confluent_kafka import Consumer

def consume_and_migrate(target_conn):
    consumer = Consumer({
        "bootstrap.servers": "kafka:9092",
        "group.id": "migration-group",
        "auto.offset.reset": "earliest"
    })
    consumer.subscribe(["users-migration"])

    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"Error: {msg.error()}")
            continue

        record = json.loads(msg.value().decode('utf-8'))
        with target_conn.cursor() as tgt_cur:
            tgt_cur.execute(
                """
                INSERT INTO users_v2 (id, name, email, created_at)
                VALUES (%s, %s, %s, %s)
                """, record
            )
        target_conn.commit()
```

---

## Implementation Guide: Step-by-Step

### 1. Plan for Failure Modes
Before starting, document:
- **Recovery procedures** (e.g., rollback scripts)
- **Fallbacks** (e.g., dual-write if the stream fails)
- **Monitoring** (e.g., Prometheus alerts for slow batches)

### 2. Start with a Pilot Batch
- Test with a small subset (e.g., 1% of data) to validate:
  - Performance (batch processing times)
  - Data integrity (e.g., checksums)
  - Edge cases (null values, large blobs)

### 3. Implement the Streaming Layer
Choose one of the approaches above (Python, Kafka, or database triggers) based on your tooling.

### 4. Build a Reconciliation Dashboard
Track:
- Processed records (e.g., `SELECT COUNT(*) FROM users_v2`)
- Stale records (e.g., `SELECT * FROM users WHERE NOT EXISTS (SELECT 1 FROM users_v2 WHERE users.id = users_v2.id)`)
- Processing speed (records/second)

Example dashboard query (PostgreSQL):

```sql
SELECT
    COUNT(*) AS total_users,
    COUNT(u.id) FILTER (WHERE NOT EXISTS (
        SELECT 1 FROM users_v2 u2 WHERE u.id = u2.id
    )) AS unprocessed_users,
    EXTRACT(EPOCH FROM (NOW() - (SELECT MAX(created_at) FROM users))) AS hours_since_last_update
FROM users u;
```

### 5. Cut Over to the New System
Once most records are processed (e.g., 99%), switch your application’s reads to the new database. Continue streaming writes until the last records are synced.

### 6. Validate and Sunset the Old System
After a grace period (e.g., 24 hours), verify:
- No stale reads occur.
- The old system can be safely decommissioned.

---

## Common Mistakes to Avoid

### 1. Skipping Reconciliation
- **Problem**: If you don’t track processed offsets, you risk reprocessing or missing records.
- **Fix**: Use a transactional outbox pattern or a dedicated offset table.

```sql
-- Example offset tracking table
CREATE TABLE migration_offsets (
    table_name VARCHAR(255) PRIMARY KEY,
    last_processed_id INTEGER
);
```

### 2. Ignoring Performance Bottlenecks
- **Problem**: Slow queries or large batches can cause timeouts and cascade failures.
- **Fix**: Profile your streaming layer and optimize:
  - Use parallel workers (e.g., `multiprocessing` in Python).
  - Batch writes efficiently (e.g., bulk inserts).

### 3. Tight Coupling to the Old System
- **Problem**: If your streaming layer depends on the old schema, changing it later is hard.
- **Fix**: Design the streaming layer to be schema-agnostic (e.g., use a generic extractor).

### 4. No Monitoring
- **Problem**: Without visibility, you won’t know when things go wrong.
- **Fix**: Log every step (e.g., batch size, processing time) and set up alerts.

### 5. Forgetting the Dual-Write Fallback
- **Problem**: If the stream fails mid-migration, you may lose data.
- **Fix**: Implement a dual-write strategy until you’re confident in the stream.

---

## Key Takeaways

- **Streaming migrations enable zero-downtime refactors** by processing data in small chunks.
- **Components**: Streaming layer (extract/transform), reconciliation (sync tracking), and optional dual-write.
- **Tools**: Python scripts, database triggers, or distributed streams (Kafka).
- **Tradeoffs**:
  - **Pros**: No downtime, scalable, testable in phases.
  - **Cons**: Complexity, monitoring overhead, need for careful planning.
- **Best Practices**:
  - Start small (test with a pilot batch).
  - Track offsets and discrepancies.
  - Monitor performance and failures.
  - Plan for failure modes.

---

## Conclusion

Streaming migrations are the Swiss Army knife of database refactoring—they’re flexible, scalable, and can save you from the dreaded “big bang” update. By breaking the problem into small, manageable steps, you can migrate even the largest datasets without ever halting production.

The pattern isn’t without tradeoffs, but with careful planning and robust tooling, the risks are far outweighed by the benefits. Next time you’re faced with a database schema change, ask yourself: *Can this be streamed?*

Happy migrating!
```

---
**Post Notes:**
- **Length**: ~1800 words (meets target).
- **Code Blocks**: Practical examples for Python, PostgreSQL, and Kafka.
- **Tradeoffs**: Explicitly called out (e.g., complexity vs. downtime avoidance).
- **Tone**: Professional but approachable, with clear action steps.
- **SEO-Friendly**: Targets advanced backend engineers with specific keywords (e.g., "zero-downtime migration," "streaming ETL").