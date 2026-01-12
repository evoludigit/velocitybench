```markdown
---
title: "CDC Cursor-Based Replay: Rebuilding Your Event Stream Without the Headaches"
date: 2024-02-20
tags: ["database", "event-sourcing", "CDC", "replay", "patterns", "practical"]
description: "Learn how to design robust event replay systems using Change Data Capture (CDC) with cursor-based replay. Avoid data loss, maintain consistency, and recover gracefully from failures."
---

# CDC Cursor-Based Replay: Rebuilding Your Event Stream Without the Headaches

When designing distributed systems with event-driven architectures, one of the most critical-but-often-overlooked patterns is **Change Data Capture (CDC) with cursor-based replay**. This pattern allows you to replay events from a specific point in time, ensuring data consistency, fault tolerance, and the ability to recover from failures—without sacrificing performance.

In this post, we’ll explore how CDC cursor-based replay solves real-world challenges, dive into its core components, and walk through practical implementations using PostgreSQL, Kafka, and Go. By the end, you’ll have a battle-tested approach to building resilient event-driven pipelines.

---

## The Problem: Why Replay Matters

Modern systems often rely on event streams for:
- **Audit trails** (e.g., financial transactions)
- **Event sourcing** (reconstructing system state from events)
- **Reprocessing failed tasks** (e.g., Kafka consumer retries)
- **Migration or backup** (e.g., moving data to another system)

But without a robust replay mechanism, you risk:
1. **Inconsistent state**: If an event processor fails mid-stream, how do you know which events to reprocess?
2. **Data loss**: Without a checkpoint, a crash could mean losing hours (or days) of changes.
3. **Slow recovery**: Linear scans for lost events are inefficient and impractical at scale.
4. **Temporal gaps**: If your system needs to answer "show me all changes since 2023-10-01," how do you do it efficiently?

### A Concrete Example: The Failed Order Processing System
Imagine a SaaS platform where orders are processed via an event stream. At 3 AM, a bug in the order validation pipeline causes 10,000 orders to be marked as "shipped" prematurely. You need to:
- Roll back the incorrect "shipped" statuses.
- Reprocess valid orders.
- Ensure no double-processing.

Without cursor-based replay, you’d have to:
- Query the database for all orders since the last checkpoint.
- Risk reprocessing the same orders multiple times.
- Waste time and resources on inefficient scans.

Cursor-based replay solves this elegantly.

---

## The Solution: Cursor-Based Replay with CDC

### How It Works
Cursor-based replay uses a **logical cursor** (or "checkpoint") to track progress through an event stream. The cursor holds:
1. A **binary position** (e.g., PostgreSQL’s `pg_lsn`, Kafka’s offset, or a custom sequence ID).
2. A **timestamp** (optional but useful for analytics).

When reprocessing:
1. The system starts at the last cursor position.
2. It replays all events from that position onward.
3. Upon success, it updates the cursor to the latest position.

This approach ensures:
- **At-least-once delivery** (events are replayed until acknowledged).
- **Idempotency** (replaying the same event twice has no side effects).
- **Efficient recovery** (no full rescan of historical data).

---

## Core Components of Cursor-Based Replay

### 1. Change Data Capture (CDC)
CDC captures database changes in real time. Popular tools:
- **PostgreSQL**: `pg_output`/`logical decoding` (WAL streaming).
- **MySQL**: Binlog consumption (Debezium, MaxScale).
- **Kafka**: Built-in offsets track consumer progress.

### 2. Event Stream
A reliable event store (e.g., Kafka, a database table with timestamps) to hold events in append-only order.

### 3. Cursor Store
A persistent store to track the latest replay position. Options:
- Database table (e.g., `replay_cursors`).
- Distributed key-value store (e.g., Redis).
- Part of the event payload (e.g., Kafka offsets).

### 4. Replay Processor
A component that:
- Fetches events from the cursor position.
- Processes them (e.g., applies to a database or triggers side effects).
- Updates the cursor on success.

---

## Code Examples

### Example 1: PostgreSQL + Kafka + Go
Let’s build a cursor-based replay system for a PostgreSQL database using Kafka as the event stream.

#### 1. Set Up PostgreSQL CDC with Debezium
Debezium captures PostgreSQL changes and streams them to Kafka. Configure `debezium-connector-postgresql.conf`:
```json
name=postgres-connector
connector.class=io.debezium.connector.postgresql.PostgresConnector
database.hostname=postgres
database.port=5432
database.user=debezium
database.password=dbz
database.dbname=orders
database.server.name=postgres
plugin.name=pgoutput
slot.name=debezium
```

#### 2. Create the Event Stream
Kafka topics for orders:
```bash
# Create topics
kafka-topics --bootstrap-server localhost:9092 --create --topic orders.changes --partitions 3 --replication-factor 1
```

#### 3. Go Replay Processor
Here’s a Go implementation for replaying orders:
```go
package main

import (
	"context"
	"fmt"
	"log"
	"time"

	"github.com/confluentinc/confluent-kafka-go/kafka"
	"golang.org/x/sync/errgroup"
)

type Order struct {
	ID        string    `json:"id"`
	Status    string    `json:"status"`
	CreatedAt time.Time `json:"created_at"`
}

type CursorStore interface {
	Save(ctx context.Context, topic string, offset int64) error
	Get(ctx context.Context, topic string) (int64, error)
}

type DBCursorStore struct{}

func (s *DBCursorStore) Save(ctx context.Context, topic string, offset int64) error {
	// Save offset to PostgreSQL
	return nil // Simplified
}

func (s *DBCursorStore) Get(ctx context.Context, topic string) (int64, error) {
	// Fetch offset from PostgreSQL
	return 100, nil // Simplified
}

func main() {
	// Configure Kafka consumer
	c, err := kafka.NewConsumer(&kafka.ConfigMap{
		"bootstrap.servers": "localhost:9092",
		"group.id":          "order-replayer",
		"auto.offset.reset": "earliest",
	})
	if err != nil {
		log.Fatalf("Failed to create consumer: %s", err)
	}
	defer c.Close()

	// Subscribe to the topic
	err = c.SubscribeTopics([]string{"orders.changes"}, nil)
	if err != nil {
		log.Fatalf("Failed to subscribe: %s", err)
	}

	// Initialize cursor store
	cursorStore := &DBCursorStore{}
	topic := "orders.changes"

	g, ctx := errgroup.WithContext(context.Background())

	// Start replay loop
	g.Go(func() error {
		for {
			offset, err := cursorStore.Get(ctx, topic)
			if err != nil {
				return fmt.Errorf("failed to get cursor: %v", err)
			}

			err = c.AssignTopics([]kafka.TopicPartition{
				{Topic: &topic, Partition: 0, Offset: offset},
				{Topic: &topic, Partition: 1, Offset: offset},
			}, nil)
			if err != nil {
				return fmt.Errorf("failed to assign partitions: %v", err)
			}

			for {
				msg, err := c.ReadMessage(-1)
				if err != nil {
					if err == kafka.ErrNoError {
						continue // No more messages
					}
					return fmt.Errorf("consumer error: %v", err)
				}

				// Parse and process the event (simplified)
				var order Order
				err = json.Unmarshal(msg.Value, &order)
				if err != nil {
					log.Printf("Failed to unmarshal: %v", err)
					continue
				}

				// Apply business logic (e.g., update order status)
				fmt.Printf("Replaying order %s: %+v\n", order.ID, order)

				// Save the new offset (Kafka's offset)
				err = cursorStore.Save(ctx, topic, msg.Offset)
				if err != nil {
					return fmt.Errorf("failed to save cursor: %v", err)
				}
			}
		}
	})

	if err := g.Wait(); err != nil {
		log.Fatalf("Replay failed: %v", err)
	}
}
```

#### Key Notes:
- **Idempotency**: Ensure your `ProcessOrder` function is idempotent (e.g., use upserts in PostgreSQL).
- **Error Handling**: Retry transient failures (e.g., database timeouts) but fail on critical errors (e.g., schema mismatch).
- **Parallelism**: Process partitions in parallel (Kafka’s built-in parallelism works well here).

---

### Example 2: PostgreSQL Logical Decoding + Cursor in SQL
If you prefer a database-native approach, PostgreSQL’s logical decoding can stream changes to a table, which you can then replay.

#### 1. Configure Logical Decoding
Enable WAL streaming in `postgresql.conf`:
```ini
wal_level = logical
max_replication_slots = 5
max_wal_senders = 10
```

#### 2. Create a Replay Table
```sql
CREATE TABLE event_replay_cursors (
    topic_name text NOT NULL,
    position bigint NOT NULL,
    last_restarted_at timestamp WITH TIME ZONE,
    PRIMARY KEY (topic_name)
);
```

#### 3. Insert a Cursor
```sql
INSERT INTO event_replay_cursors (topic_name, position, last_restarted_at)
VALUES ('orders', 100, NOW())
ON CONFLICT (topic_name) DO UPDATE
SET position = EXCLUDED.position, last_restarted_at = EXCLUDED.last_restarted_at;
```

#### 4. Replay Logic (Pseudo-SQL)
```sql
WITH changes AS (
    SELECT
        c.data::json AS event,
        c.lsn AS position,
        c.xmin AS transaction_id
    FROM pg_logical_slot_get_changes(
        'orders_slot', NULL, NULL,
        'create_table_if_not_exists orders (id text, status text)',
        NULL, '{}'
    )
    WHERE c.change IS NOT NULL
    AND c.xid IS NOT NULL
)
UPDATE orders
SET status = (SELECT (changes.event->>'status')::text)
FROM changes
WHERE orders.id = (changes.event->>'id')::text
AND changes.position > (
    SELECT position FROM event_replay_cursors WHERE topic_name = 'orders'
)
RETURNING orders.id, changes.position;
```

---

## Implementation Guide

### Step 1: Choose Your CDC Tool
| Tool               | Pros                          | Cons                          | Best For                     |
|--------------------|-------------------------------|-------------------------------|------------------------------|
| Debezium           | Mature, supports many DBs      | Complex setup                 | Enterprise systems           |
| PostgreSQL logical decoding | Native, low latency | Limited to PostgreSQL         | PostgreSQL-specific workflows |
| Debezium Postgres  | Simpler than raw WAL           | Still requires Debezium        | Simplicity over control      |
| Custom WAL parsing | Full control                  | Hard to maintain              | Specialized use cases        |

### Step 2: Design Your Event Schema
- Include a **timestamp** (e.g., `event_time`) and **source position** (e.g., `pg_lsn`).
- Example Kafka schema:
  ```json
  {
    "id": "order_123",
    "status": "SHIPPED",
    "event_time": "2024-02-01T12:00:00Z",
    "source_lsn": "0/123456789"
  }
  ```

### Step 3: Implement the Cursor Store
- Use a **database table** for simplicity (e.g., `event_replay_cursors`).
- For distributed systems, use a **distributed lock** (e.g., Redis) to avoid race conditions:
  ```go
  // Pseudocode for Redis-based cursor store
  func SaveCursor(ctx context.Context, topic string, offset int64) error {
      key := fmt.Sprintf("replay_cursor:%s", topic)
      if _, err := redis.Client.Set(ctx, key, offset, 0).Result(); err != nil {
          return err
      }
      return nil
  }
  ```

### Step 4: Build the Replay Processor
1. **Fetch the last cursor position** from the store.
2. **Stream events from that position** (Kafka offset, PostgreSQL LSN, etc.).
3. **Process each event** (apply to DB, trigger side effects).
4. **Update the cursor** on success.

### Step 5: Handle Failures
- **Transient errors**: Retry with exponential backoff (e.g., Kafka consumer retries).
- **Critical errors**: Log the cursor position before failing (e.g., to Sentry + Slack).
- **Manual recovery**: Allow admins to reset the cursor to a specific LSN (e.g., `ALTER SYSTEM SET pg_logical_slot_drop('orders_slot') = TRUE`).

---

## Common Mistakes to Avoid

1. **Not Making Events Idempotent**
   - *Problem*: Replaying the same event twice causes duplicate side effects (e.g., double-shipping an order).
   - *Fix*: Use database upserts (e.g., `ON CONFLICT DO NOTHING`) or dedupe keys.

2. **Ignoring Temporal Order**
   - *Problem*: Processing events out of order can lead to race conditions (e.g., updating a user’s balance before their payment is confirmed).
   - *Fix*: Use event timestamps (`event_time`) and delay processing until all prior events are confirmed.

3. **Overcomplicating the Cursor Store**
   - *Problem*: Distributed locks or multi-DB cursors add complexity without value.
   - *Fix*: Start with a simple database table. Only scale later if needed.

4. **Not Testing Failures**
   - *Problem*: Your replay system might work in dev but crash in production during outages.
   - *Fix*: Simulate network drops, DB timeouts, and Kafka brokers going down.

5. **Assuming CDC is Real-Time**
   - *Problem*: WAL latency or network delays can cause replay stalls.
   - *Fix*: Set realistic expectations (e.g., "replay begins within 10 minutes of the event").

---

## Key Takeaways

- **Cursor-based replay enables reliable event reprocessing** by tracking progress via binary positions (LSNs, offsets).
- **CDC is the backbone**: Without capturing changes efficiently, replay is impossible.
- **Idempotency is non-negotiable**: Ensure your system can handle duplicate events.
- **Start simple**: Use a single-table cursor store and scale later if needed.
- **Test failures**: Simulate crashes, timeouts, and network issues to validate recovery.

---

## Conclusion

Cursor-based replay with CDC is a powerful pattern for building resilient event-driven systems. Whether you're recovering from a bug, migrating data, or reprocessing failed tasks, this approach ensures you can:
- Start replaying from a known good state.
- Avoid data loss even after failures.
- Scale processing horizontally (e.g., Kafka consumers).

The key is to **balance simplicity with reliability**. Start with a proven tool like Debezium or PostgreSQL logical decoding, design idempotent events, and test your recovery paths. Once you’ve mastered the basics, you can optimize for latency, parallelism, or distributed consistency.

Ready to try it? Start small—replay a single table’s changes from the last checkpoint. Then expand to more complex workflows. Your future self (and your users) will thank you.

---
**Further Reading**:
- [PostgreSQL Logical Decoding](https://www.postgresql.org/docs/current/logicaldecoding.html)
- [Debezium PostgreSQL Connector](https://debezium.io/documentation/reference/stable/connectors/postgresql.html)
- [Kafka Consumer API](https://kafka.apache.org/documentation/#consumerapi)
```