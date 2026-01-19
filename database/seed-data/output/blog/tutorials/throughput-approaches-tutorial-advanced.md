```markdown
---
title: "Scaling Under Pressure: The Throughput Approaches Pattern in Database Design"
author: "Maximilian Black"
date: "2023-10-15"
tags: ["database design", "backend performance", "api design", "scalability"]
---

# Scaling Under Pressure: The Throughput Approaches Pattern in Database Design

![Throughput Approaches Pattern](https://images.unsplash.com/photo-1631615221589-1f1c24d19e9f?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1770&q=80)

In this tutorial, we’ll explore **Throughput Approaches**, a critical pattern for designing databases and APIs that can handle high loads efficiently. Whether you’re building a high-frequency trading system, a social media platform, or a real-time analytics dashboard, throughput—the number of operations your system can process per second—is often the bottleneck.

While you can debate endlessly about which database to use (SQL vs NoSQL, OLTP vs OLAP), the real challenge lies in designing systems to *scale horizontally* while managing data consistency, latency, and cost. Throughput Approaches isn’t just about sharding or partitioning—it’s about structuring your data, queries, and application logic to maximize parallelism while minimizing contention.

By the end of this post, you’ll understand how to:
- Distribute workloads efficiently across database nodes.
- Optimize for high concurrency without sacrificing performance.
- Choose the right tradeoffs between consistency, availability, and partition tolerance (CAP).

Let’s dive in.

---

## The Problem: When Your Database Struggles Under Load

Imagine this scenario: A popular e-commerce platform hosts a flash sale with a 24-hour window. During the sale, 100,000 users hit the "Buy Now" button within 10 seconds. Without proper throughput planning, here’s what happens:

1. **Contention**: The primary database node becomes a bottleneck, as every request competes for the same database connections and locks.
2. **Locking Issues**: If the system uses optimistic or pessimistic locking, many transactions will fail or timeout, leading to degraded user experience.
3. **Increased Latency**: Long-running queries or blocking transactions push response times from 100ms to 10 seconds, frustrating users.
4. **Resource Exhaustion**: High CPU usage and memory pressure can crash the database, requiring costly restarts.
5. **Cost Spikes**: Over-provisioning to handle peak loads becomes unsustainable due to the high cost of scaling vertically.

This is the reality of **throughput starvation**—when a system cannot handle the volume of operations it’s designed for. Traditional approaches like **sharding** or **replication** can help, but they’re only part of the solution. The Throughput Approaches pattern provides a structured way to address these challenges by focusing on how data is accessed, processed, and stored.

---

## The Solution: Throughput Approaches in Action

Throughput approaches are techniques to **distribute load** and **eliminate contention** in database and API designs. The core idea is to **reduce parallelism conflicts** by structuring data and workflows to maximize concurrency. Here are the three primary strategies:

1. **Read-Only Partitioning**: Read-heavy workloads can be scaled by distributing read-only queries across multiple replicas.
2. **Write Scalability**: Write-heavy workloads can be scaled by partitioning writes or batching them to reduce contention.
3. **Hybrid Approaches**: Combining both strategies with techniques like **event sourcing**, **CQRS**, or **micro-batch processing**.

Let’s explore each with code examples.

---

## Components/Solutions: Tools and Techniques

### 1. Read-Only Partitioning (Horizontal Scaling for Reads)
**Concept**: Use database replication to offload read queries to secondary replicas. This is especially useful for analytics, reporting, or any workload where writes are infrequent compared to reads.

**Example**: A social media platform with 1M active users per day but only 10K updates per day. Use **read replicas** to distribute read loads.

#### PostgreSQL Setup with Read Replicas
```sql
-- Create a primary database (write-only)
CREATE DATABASE user_activity PRIMARY;

-- Create read replicas (PostgreSQL 16+ supports logical replication)
CREATE DATABASE user_activity_read PRIMARY WITH REPLICA_IDENTITY FULL;

-- Configure replication (using pg_basebackup for initial sync)
SELECT pg_start_backup('initial_replica', TRUE, TRUE);
-- Sync data (omitted for brevity)
SELECT pg_stop_backup();

-- Set up replication on the primary
SELECT pg_create_logical_replication_slot('slots/user_activity', 'pgoutput');
SELECT pg_start_backup('replica_sync', TRUE, TRUE);

-- On the replica, connect to the primary and sync
SELECT pg_set_replication_slot('slots/user_activity', TRUE);
SELECT pg_create_logical_replication_slot('slots/user_activity', 'pgoutput');
SELECT pg_start_backup('replica_sync', TRUE, TRUE);
```

#### Application Layer: Distribute Reads Across Replicas
```go
// pseudo-code for a Go service distributing reads
package main

import (
	"database/sql"
	"math/rand"
	"time"
)

var replicas = []string{
	"postgres://user:pass@read-replica-1:5432/user_activity",
	"postgres://user:pass@read-replica-2:5432/user_activity",
}

func getUserActivity(userID int) (*sql.DB, error) {
	// Randomly select a replica
	dbURL := replicas[rand.Intn(len(replicas))]
	db, err := sql.Open("postgres", dbURL)
	if err != nil {
		return nil, err
	}
	return db, nil
}
```

---

### 2. Write Scalability (Partitioning Writes)
**Concept**: Distribute writes across multiple database nodes to avoid hotspots. Techniques include:
- **Key-based sharding**: Partition by a specific column (e.g., `user_id % 10`).
- **Time-based sharding**: Partition by date ranges (e.g., `orders_2023`, `orders_2024`).
- **Directory-based sharding**: Use a service (e.g., **Vitess**, **CockroachDB**) to route writes dynamically.

**Example**: An e-commerce platform with high write volume to order tables. Use **time-based sharding** to distribute writes by month.

```sql
-- Create sharded tables for each month
CREATE TABLE orders_2023 (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE orders_2024 (
    -- Same schema, but for 2024
);

-- Application logic to route writes to the correct shard
func saveOrder(order Order) error {
    year := time.Now().Year()
    dbName := fmt.Sprintf("orders_%d", year)
    db, err := getDB(dbName)
    if err != nil {
        return err
    }
    _, err = db.Exec(`
        INSERT INTO orders_$year (user_id, amount, created_at)
        VALUES ($1, $2, NOW())
    `, order.UserID, order.Amount)
    return err
}
```

**Tradeoff**: Cross-shard queries become complex (e.g., aggregating all orders across years). Tools like **Vitess** or **CockroachDB** automate this.

---

### 3. Hybrid Approaches: Event Sourcing + CQRS
**Concept**: Decouple reads and writes using:
- **Event Sourcing**: Store state changes as a sequence of events.
- **CQRS**: Maintain separate read and write models.

**Example**: A real-time analytics dashboard that logs user events but rarely queries them.

#### Event Sourcing with Kafka and Postgres
```sql
-- Write model: Store events in a journal
CREATE TABLE user_events (
    id BIGSERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    event_type VARCHAR(20) NOT NULL,
    data JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Read model: Materialized view for dashboards
CREATE MATERIALIZED VIEW user_activity_dashboard AS
SELECT
    user_id,
    COUNT(*) AS total_events,
    COUNT(*) FILTER (WHERE event_type = 'purchase') AS purchases
FROM user_events
GROUP BY user_id;
```

#### Application Layer: Publish Events to Kafka
```go
// Publish user events to Kafka
func publishEvent(userID int, eventType string, data map[string]interface{}) error {
    event := struct {
        UserID    int            `json:"user_id"`
        EventType string         `json:"event_type"`
        Data      json.RawMessage `json:"data"`
    }{
        UserID:    userID,
        EventType: eventType,
        Data:      json.RawMessage(mustMarshal(data)),
    }

    msg := &sarama.ProducerMessage{
        Topic: "user_events",
        Value: sarama.StringEncoder(json.MustEncode(event)),
    }

    return producer.SendMessage(msg)
}
```

#### Kafka Consumer: Update Materialized View
```python
# Python consumer to update the materialized view
from confluent_kafka import Consumer, KafkaException

conf = {'bootstrap.servers': 'kafka:9092', 'group.id': 'view_updater'}
consumer = Consumer(conf)
consumer.subscribe(['user_events'])

while True:
    msg = consumer.poll(1.0)
    if msg is None:
        continue
    if msg.error():
        raise KafkaException(msg.error())

    # Parse event and update the materialized view
    event = json.loads(msg.value().decode('utf-8'))
    if event['event_type'] == 'purchase':
        # Use a database connection to update the view
        cursor.execute("""
            UPDATE user_activity_dashboard
            SET purchases = purchases + 1
            WHERE user_id = %s
        """, (event['user_id'],))
        conn.commit()
```

**Tradeoffs**:
- **Event Sourcing**: Higher storage overhead due to append-only logs.
- **CQRS**: Complexity in maintaining consistency between read/write models.

---

## Implementation Guide: Best Practices

### 1. Choose the Right Partitioning Strategy
| Strategy               | Use Case                          | Tools/Examples                          |
|------------------------|-----------------------------------|-----------------------------------------|
| **Key-based sharding** | Uniform distribution (e.g., users)| Vitess, CockroachDB                     |
| **Time-based**         | Time-series data (e.g., logs)     | PostgreSQL (tables/partitions)          |
| **Directory-based**    | Dynamic routing                   | Vitess, ScyllaDB                        |

**Rule of Thumb**:
- If writes are **hot** (e.g., one table gets 90% of writes), use **key-based** or **directory-based** sharding.
- If writes are **distributed** (e.g., user actions), consider **time-based** sharding or **event sourcing**.

---

### 2. Optimize for Contention
- **Use connection pooling**: Tools like PgBouncer (PostgreSQL) or Pylon (MySQL) reduce connection overhead.
- **Avoid long transactions**: Break large writes into smaller batches (e.g., 100 records at a time).
- **Use asynchronous processing**: Offload non-critical writes to background workers (e.g., Celery, Kafka Streams).

**Example with PgBouncer**:
```ini
# pgbouncer.ini: Configure connection pooling
[databases]
user_activity = host=db.example.com port=5432 dbname=user_activity

[pgbouncer]
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 50
```

---

### 3. Monitor and Scale Dynamically
- **Use metrics**: Track query latency, lock contention, and throughput per shard.
- **Auto-scaling**: Use **Kubernetes Horizontal Pod Autoscaler (HPA)** or **AWS Auto Scaling** to adjust replicas based on load.
- **Chaos engineering**: Test failure scenarios (e.g., replica outages) to validate resiliency.

**Example with Prometheus and Alertmanager**:
```yaml
# Alert for high write latency (e.g., >500ms)
- alert: HighWriteLatency
  expr: postgres_write_latency > 0.5
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High write latency on {{ $labels.instance }}"
```

---

## Common Mistakes to Avoid

1. **Over-Sharding Too Early**: Start with a single node if your load is low. Sharding introduces complexity (e.g., distributed transactions, cross-shard joins).
2. **Ignoring Cross-Shard Queries**: If you shard by `user_id`, aggregating data across shards (e.g., `SUM(amount) FROM orders`) becomes expensive. Pre-compute aggregations or use **global secondary indexes** (e.g., DynamoDB).
3. **Hot Keys**: Distribute writes evenly. For example, if all users have `user_id = 1`, sharding by `user_id % N` won’t help. Use **consistent hashing** or **salting** (e.g., `user_id * 1000 + random(1000)`).
4. **Underestimating Replication Lag**: Read replicas can fall behind during high write loads. Use **logical replication** (PostgreSQL) or **change data capture (CDC)** (Debezium) to minimize lag.
5. **Tight Coupling**: Avoid ORMs that generate inefficient queries (e.g., N+1 problems). Use raw SQL or a query builder (e.g., SQLx, GORM) for fine-grained control.

---

## Key Takeaways

- **Throughput is about distribution**: The goal is to spread load across resources to avoid bottlenecks.
- **Read-heavy workloads**: Use **replication** (read replicas) to scale reads independently.
- **Write-heavy workloads**: Use **sharding** or **event sourcing** to distribute writes.
- **Hybrid approaches work best**: Combine strategies (e.g., CQRS + event sourcing) for complex workloads.
- **Monitor and iterate**: Use metrics to identify hotspots and adjust dynamically.

---

## Conclusion

Throughput isn’t just a database problem—it’s a system-wide challenge that requires careful planning. Whether you’re dealing with a monolithic application or a microservices architecture, the Throughput Approaches pattern provides a framework to design scalable, high-performance systems.

### Next Steps:
1. **Experiment**: Test sharding or replication in a staging environment with realistic load.
2. **Benchmark**: Use tools like **HammerDB**, **k6**, or **Locust** to simulate high throughput.
3. **Refine**: Iterate based on metrics—scale replicas, adjust sharding keys, or optimize queries.

By applying these techniques, you’ll build systems that handle peak loads gracefully, avoiding the "flash sale disaster" scenario. Happy scaling!

---

### Further Reading:
- [Vitess: Database for Horizontally Scaled Services](https://vitess.io/)
- [CockroachDB: The Distributed SQL Database](https://www.cockroachlabs.com/docs/)
- [Event Sourcing Patterns](https://martinfowler.com/eaaDev/EventSourcing.html)
- [CAP Theorem Explained](https://github.com/butlerx/awesome-cs/blob/main/README.md#distributed-systems)
```