```markdown
---
title: "Throughput Migration: A Pragmatic Guide for Scaling Database Systems"
date: "2024-06-15"
tags: ["database", "scaling", "migration", "api design", "backend engineering"]
categories: ["database patterns", "scaling strategies"]
---

# Throughput Migration: A Pragmatic Pattern for Zero-Downtime Database Scaling

![Throughput Migration Pattern](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*X4W46yT5IA2Q6OcfZW5Qqg.png)

Scaling database throughput is one of the most critical challenges in backend engineering. Whether you're handling an unexpected traffic spike or proactively planning for growth, migrating from a smaller to a larger database isn't just about schema changes—it's about maintaining availability while incrementally handling more requests.

In this guide, we'll explore the **Throughput Migration** pattern, a battle-tested approach for scaling read/write operations across database tiers without downtime. We'll cover:
- Why traditional migration approaches fail
- How the throughput migration pattern works in real-world systems
- Practical code examples for PostgreSQL, Redis, and application-level sharding
- Common pitfalls and how to avoid them

This pattern isn't about instant scalability—it's about **incremental growth with zero availability impact**.

---

## The Problem: Why Traditional Migrations Fail

Most developers approach database scaling with one of two strategies:

1. **Big Bang Replacement**: Draining everything, replacing the database, and reloading data.
   ```bash
   # Example of a dangerous migration (doesn't work for throughput)
   pg_dump -d old_db > dump.sql
   dropdb new_db
   createdb new_db
   psql new_db < dump.sql
   ```

2. **Schema-Only Changes**: Adding new tables while keeping old ones, but failing to distribute load.
   ```sql
   -- Creating a new table without proper read distribution
   CREATE TABLE users_v2 (
     id SERIAL PRIMARY KEY,
     username TEXT NOT NULL,
     Migrations: [20240601] TEXT
   );
   ```

Both approaches share common problems:

- **Downtime**: Even "zero-downtime" replacements can experience latency spikes.
- **Data Inconsistency**: Temporary unavailability during migration leads to stale reads.
- **Underutilized Resources**: You either over-provision for peak loads or struggle during traffic spikes.

A production system at [AcmeCorp](https://acmecorp.example) (fictional) faced this when their PostgreSQL cluster reached 90% CPU utilization during a marketing campaign. Their "solution" was to buy a bigger server, which worked until the next campaign—then the cycle repeated.

**Key insight**: We need a way to **distribute load incrementally** while maintaining consistency.

---

## The Solution: Throughput Migration Pattern

The throughput migration pattern solves this by:

1. **Adding capacity in parallel** to the existing database
2. **Gradually shifting load** from old to new systems
3. **Validating correctness** at each step before deleting old infrastructure

This is similar to how Kubernetes handles pod scaling, but adapted for databases:

```
┌─────────────┐       ┌─────────────┐       ┌─────────────────────┐
│             │       │             │       │                     │
│  Old DB     ├───────▶ New DB     ├───────▶ Application         │
│  (Primary)  │       │  (Read Replica)│       │  Load Balancer     │
└─────────────┘       └─────────────┘       └─────────────────────┘
       ▲                                      ▲
       │                                      │
       └─────────────────────────┬─────────────┘
                                 │
                                 ▼
                        Monitored Metrics
```

### Core Components

| Component               | Purpose                                                                 |
|-------------------------|-------------------------------------------------------------------------|
| **Write Forwarder**     | Routes writes to new database(s) while maintaining old database access |
| **Read Balancer**       | Distributes reads across old and new databases                        |
| **Data Synchronizer**   | Keeps old and new databases in sync (eventually consistent)              |
| **Health Check**        | Validates new system can handle production load before cutoff           |
| **Cutover Script**      | Final step to commit to the new database                               |

---

## Implementation Guide: Three Phases of Throughput Migration

Let's walk through a complete example using PostgreSQL.

### Phase 1: Prepare for Migration

1. **Add replica databases** (read replicas or new shard tier)
2. **Modify application** to route queries to both old and new systems
3. **Set up synchronization** between databases

```sql
-- Create new read replica in PostgreSQL
SELECT pg_start_backup('pre_migration', true);

-- On replica node:
recovery.conf contents:
primary_conninfo = 'host=old_db user=repluser password=secret'
primary_slot_name = 'migration_slot'

restore_command = 'cp /backups/%f %p'

-- After replica is synced:
SELECT pg_create_logical_replication_slot('migration_slot', 'pgoutput');
```

### Phase 2: Gradual Load Shift

1. **Start with read-only operations** (most tolerant to lag)
2. **Incrementally increase write load**
3. **Monitor performance metrics**:

```python
# Example Python monitoring script
def monitor_db_health(old_db, new_db):
    """Compare performance between old and new databases"""
    queries = [
        "SELECT * FROM users WHERE status = 'active'",
        "INSERT INTO audit_log SELECT * FROM generated_events()"
    ]

    results = []
    for query in queries:
        old_result = timeit(old_db.execute, query)
        new_result = timeit(new_db.execute, query)
        results.append({
            'query': query,
            'old_latency': old_result,
            'new_latency': new_result,
            'latency_ratio': old_result/new_result
        })

    return results
```

3. **Adjust distribution** based on metrics:

```python
# Example load balancer configuration (using Python anydbm)
def balance_reads(old_db, new_db, distribution=0.7):
    """Route reads with specified distribution"""
    def select_db(query):
        if query.startswith('INSERT') or query.startswith('UPDATE'):
            return old_db  # Always use primary for writes
        if random.random() < distribution:
            return old_db
        return new_db
```

### Phase 3: Final Cutover

1. **Validate new system** can handle 100% load
2. **Switch application** to new database
3. **Monitor for errors** for 24 hours
4. **Clean up old infrastructure** after verification

```sql
-- Final cutover script
BEGIN;
-- Verify data consistency
SELECT COUNT(*) FROM users WHERE status = 'active'
INTERSECT
SELECT COUNT(*) FROM new_users WHERE status = 'active';

-- Update application config
UPDATE config SET value = 'new_db_connection' WHERE key = 'database_uri';

-- Delete old infrastructure
DROP DATABASE old_db;
COMMIT;
```

---

## Code Examples: Practical Implementations

### Example 1: Read Replica Migration with PostgreSQL

```python
# database_migrator.py - Python implementation
from contextlib import contextmanager
import time
import random

class ThroughputMigrator:
    def __init__(self, old_db, new_db):
        self.old_db = old_db
        self.new_db = new_db
        self.read_ratio = 0.8  # Start with 80% reads on old DB

    @contextmanager
    def balanced_connection(self):
        """Context manager for database operations"""
        try:
            yield self._select_db()
        except Exception as e:
            # Fallback to old DB if new one fails
            print(f"Falling back to old DB: {e}")
            yield self.old_db

    def _select_db(self):
        """Route based on current distribution"""
        if random.random() < self.read_ratio:
            return self.old_db
        return self.new_db

    def migrate(self):
        """Incrementally migrate load"""
        while True:
            # Simulate load test
            results = self._test_queries()

            # Adjust distribution based on performance
            if results['new_db_latency'] < results['old_db_latency'] * 0.9:
                self.read_ratio *= 0.95  # Shift more load to new DB

            # Final cutover when old is no longer primary
            if self.read_ratio < 0.05:
                self._cutover()

    def _test_queries(self):
        """Compare performance between databases"""
        queries = [
            "SELECT * FROM users WHERE status = 'active' LIMIT 1000",
            "INSERT INTO audit_log (event) VALUES (generate_event())"
        ]

        old_results = {}
        new_results = {}

        for query in queries:
            old_start = time.time()
            self.old_db.execute(query)
            old_results[query] = time.time() - old_start

            new_start = time.time()
            self.new_db.execute(query)
            new_results[query] = time.time() - new_start

        return {
            'old_db_latency': sum(old_results.values()),
            'new_db_latency': sum(new_results.values()),
            'query_results': {**old_results, **new_results}
        }

    def _cutover(self):
        """Final database switch"""
        print("Performing final cutover...")
        # Update application config, DNS, etc.
        self.old_db.close()
        self.new_db = self.old_db  # Now new DB is primary
```

### Example 2: Redis Cluster Migration

```bash
# redis_migration.sh - Shell script for Redis cluster migration
#!/bin/bash

# Phase 1: Add new cluster node
redis-cli --cluster create node1:6379 node2:6379 node3:6379 --cluster-replicas 1

# Phase 2: Enable incremental transport
redis-cli CONFIG SET cluster-allow-reads-on-slaves yes

# Phase 3: Route reads to slaves first
# In your application:
# redis = StrictRedis(host='old_node', port=6379, db=0, socket_timeout=5)
# redis.slave_for_reading = True  # Route reads to replica

# Phase 4: Monitor with redis-migrate
redis-migrate --verbose --source old_db:6379 --target new_db:6379 --read-only-mode

# Phase 5: Cutover when replication lag < 1s
while true; do
    lag=$(redis-cli INFO replication | grep "lag:" | cut -d: -f2)
    echo "Current lag: $lag"
    if [[ "$lag" -lt 1 ]]; then
        echo "Replication lag acceptable. Performing cutover..."
        # Update config files to new node
        break
    fi
    sleep 10
done
```

### Example 3: Application-Level Sharding

```java
// ShardRouter.java - Java implementation for database sharding
public class ShardRouter {
    private final List<DatabaseConnection> connections;
    private final int shardCount;

    public ShardRouter(List<DatabaseConnection> connections) {
        this.connections = connections;
        this.shardCount = connections.size();
    }

    public DatabaseConnection getConnection(long userId) {
        // Consistent hashing for user distribution
        int shardIndex = (int) (Math.abs(userId) % shardCount);
        return connections.get(shardIndex);
    }

    public void migrateShard(int oldIndex, int newIndex) {
        // Phase 1: Add new connection
        connections.add(oldIndex + 1, new DatabaseConnection("new_shard_url"));

        // Phase 2: Gradually shift users
        int shiftSize = connections.size() / 2;
        for (int i = 0; i < shiftSize; i++) {
            // Move user i to new shard (i + oldIndex)
            // Implementation depends on your data distribution
            System.out.printf("Moving user %d to new shard%n", i);
        }

        // Phase 3: Remove old connection when safe
        connections.remove(oldIndex);
    }

    // For read-after-write consistency
    public void executeWithRetry(Runnable operation, int maxRetries) {
        int retryCount = 0;
        while (retryCount < maxRetries) {
            try {
                operation.run();
                return;
            } catch (DatabaseException e) {
                retryCount++;
                // Exponential backoff
                Thread.sleep((long) Math.pow(2, retryCount) * 100);
            }
        }
        throw new RuntimeException("All retries failed");
    }
}
```

---

## Common Mistakes to Avoid

1. **Under-estimating replication lag**:
   - Always start with read-only operations
   - Use tools like `pg_repack` or `redis-migrate` to monitor lag
   - Example of bad approach:
     ```python
     # DANGEROUS: Immediately shift writes without testing
     def bad_migration():
         global write_db
         write_db = new_db  # All writes now go to new DB before verification
     ```

2. **Not monitoring cross-database consistency**:
   - Always implement application-level checks
   - Example test:
     ```python
     def verify_consistency():
         old_count = old_db.execute("SELECT COUNT(*) FROM orders").value
         new_count = new_db.execute("SELECT COUNT(*) FROM orders").value
         if old_count != new_count:
             raise MigrationError("Data inconsistency detected")
     ```

3. **Skipping the health check phase**:
   - Never proceed to cutover without:
     - Load testing with production-like queries
     - Monitoring for unexpected errors
     - Validating backup/restore procedures

4. **Assuming your ORM handles everything**:
   - Many ORMs don't support multi-database routing
   - Example of required application code:
     ```python
     # SQLAlchemy doesn't handle this automatically
     Base.metadata.create_all(new_engine)  # You must implement this manually
     ```

5. **Not having a rollback plan**:
   - Always document your migration steps
   - Example rollback procedure:
     ```bash
     # If migration fails, restore from backup
     pg_restore -d old_db -F c backup_file.dump
     ```

---

## Key Takeaways

✅ **Incremental is better than immediate**: Shift load gradually to catch issues early

✅ **Monitor everything**: Latency, error rates, and data consistency at every stage

✅ **Write first, read second**: Start with read replicas, then move writes

🔄 **Test failures**: Your migration plan must work when:
   - The new database is overloaded
   - Network partitions occur
   - Application code has bugs

🚀 **Automate validation**: Write scripts to verify data consistency before cutover

📊 **Measure success**: Track:
   - Throughput (ops/sec)
   - Latency percentiles (p99, p95)
   - Error rates
   - Resource utilization

🔄 **Plan for rollback**: Have a documented procedure to revert if something goes wrong

---

## Conclusion: Mastering Throughput Migration

Throughput migration isn't about replacing your database overnight—it's about **growing your capacity safely, one increment at a time**. By following this pattern, you'll avoid the pitfalls of big-bang migrations while ensuring your system remains available during scaling operations.

Key to success:
1. Start with read replicas
2. Gradually shift load
3. Validate at every step
4. Have a rollback plan

Remember: Even with perfect migration planning, **unexpected failures will happen**. That's why you need to:
- Design for failure at every layer
- Monitor continuously
- Be prepared to revert quickly

For production systems, consider building a migration framework that:
- Tracks database state
- Enforces consistency checks
- Provides rollback capabilities

The throughput migration pattern gives you the confidence to scale your database infrastructure without downtime—one carefully measured step at a time.

Now go forth and migrate responsibly!
```

---
**Further Reading:**
- [PostgreSQL Logical Replication Docs](https://www.postgresql.org/docs/current/logical-replication.html)
- [Redis Cluster Documentation](https://redis.io/topics/cluster-spec)
- ["Database Percolator" Paper](https://www.usenix.org/system/files/conference/osdi12/osdi12-paper.pdf) (related concept)
- ["The Art of Scalability" book](https://www.oreilly.com/library/view/the-art-of/9781449340330/) by Geoffrey A. Dean