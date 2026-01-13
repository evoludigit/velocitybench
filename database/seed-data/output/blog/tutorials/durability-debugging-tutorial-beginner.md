```markdown
---
title: "Durability Debugging: Ensuring Your Data Stays Safe (Even When Things Go Wrong)"
date: 2024-01-15
author: ["Alex Carter"]
tags: ["databases", "api-design", "backend-engineering", "durability", "postgres", "sql"]
draft: false
---

# Durability Debugging: Ensuring Your Data Stays Safe (Even When Things Go Wrong)

As a backend developer, you’ve probably spent countless hours writing APIs and databases that handle business logic, user requests, and transactions. But here’s a question that might haunt you in the middle of the night: *What if the data we just wrote gets lost?* Whether due to a crash, network hiccup, or a misconfigured database, data loss is one of the most frustrating problems in software development.

Durability debugging is the practice of systematically checking and ensuring that your data persists even in the face of failures. It’s not just about writing transactions correctly—it’s about understanding how databases handle commits, how your application interacts with them, and how to proactively test for durability issues before they become disasters. In this post, we’ll explore the challenges of durability, why debugging it matters, and how to implement robust checks in your applications. By the end, you’ll have a toolkit to ensure your data stays safe—no matter what.

---

## The Problem: Why Durability Debugging Matters

Data durability is the guarantee that once data is committed to a database, it won’t be lost due to failures like:
- **System crashes** (hardware failures, OS panics).
- **Network outages** (unexpected disconnections between the app and database).
- **Database restarts** (planned or unplanned).
- **Corrupt transactions** (race conditions, improper isolation levels).

Imagine this scenario:
> A user pays $99.99 for a premium subscription. Your app writes to the database, and everything looks good—until the database crashes before the commit is fully logged to disk. When the database restarts, the transaction is gone. The user’s money is gone. Your reputation is tarnished.

This isn’t hypothetical. I’ve seen it happen. Without durability debugging, you’re flying blind.

### Common Signs of Durability Issues
1. **Inconsistent writes**: Some records appear in the database, others don’t.
2. **Partial transactions**: A payment is processed, but the inventory is never updated.
3. **Ghost data**: Data that appears to exist but can’t be queried reliably.
4. **Timeouts or "stuck" transactions**: Your app hangs waiting for a response that never comes.

These issues often slip under the radar in development environments because:
- Local databases (like SQLite in-memory mode) don’t enforce the same durability guarantees as production databases.
- Unit tests rarely simulate hardware failures or network interruptions.

---
## The Solution: Durability Debugging Patterns

Durability debugging combines *proactive checks* and *reactive recovery* to ensure data persistence. Here’s how you can approach it:

### 1. **Understand Your Database’s Durability Guarantees**
Different databases offer different levels of durability:
- **ACID (Atomicity, Consistency, Isolation, Durability)**: SQL databases like PostgreSQL, MySQL, and SQL Server guarantee durability *once a transaction is committed*, but the underlying mechanisms vary.
  - PostgreSQL uses **Write-Ahead Logging (WAL)** to log changes before applying them to disk.
  - MySQL’s InnoDB also uses WAL but offers configurable sync settings (`innodb_flush_log_at_trx_commit`).
- **Eventual consistency**: NoSQL databases (like DynamoDB or MongoDB) may sacrifice strong durability for performance. Some operations may not be immediately visible to other nodes.
- **Local databases**: SQLite (without journal mode) or in-memory databases offer *no* durability guarantees.

**Key takeaway**: If you need strong durability, stick to traditional SQL databases with configurable WAL settings.

---

### 2. **Enable Durability Features in Your Database**
Most SQL databases have settings to enforce durability. For example:
- **PostgreSQL**:
  ```sql
  -- Ensure WAL is always synced to disk before commit (default is 'on')
  ALTER SYSTEM SET synchronous_commit = 'on';
  ```
- **MySQL**:
  ```sql
  -- Ensure logs are flushed to disk after every commit
  SET GLOBAL innodb_flush_log_at_trx_commit = 2;
  ```
- **SQL Server**:
  ```sql
  -- Enforce durability guarantees
  ALTER DATABASE YourDB SET RECOVERY FULL;
  ```

Without these, your database might "optimize" by delaying disk writes until it can batch them, risking data loss on crashes.

---

### 3. **Implement Transaction Retries with Exponential Backoff**
Network flakiness or database timeouts can cause transactions to fail. Instead of giving up, implement retries with delays:
```go
package main

import (
	"database/sql"
	"log"
	"time"

	_ "github.com/lib/pq" // PostgreSQL driver
)

func retryTransaction(db *sql.DB, retries int, delay time.Duration, fn func(*sql.DB) error) error {
	for i := 0; i < retries; i++ {
		err := fn(db)
		if err == nil {
			return nil // Success!
		}

		// Exponential backoff
		time.Sleep(delay * time.Duration(1<<i))
	}

	return fmt.Errorf("transaction failed after %d retries", retries)
}

func processPayment(db *sql.DB, userID, amount int) error {
	return retryTransaction(db, 3, 100*time.Millisecond, func(conn *sql.DB) error {
		tx, err := conn.Begin()
		if err != nil {
			return err
		}
		defer tx.Rollback() // Rollback if we fail

		// Example: Deduct from user balance
		_, err = tx.Exec("UPDATE accounts SET balance = balance - $1 WHERE id = $2", amount, userID)
		if err != nil {
			return err
		}

		// Example: Record payment
		_, err = tx.Exec("INSERT INTO payments (user_id, amount) VALUES ($1, $2)", userID, amount)
		if err != nil {
			return err
		}

		return tx.Commit() // Commit if everything succeeded
	})
}
```

---

### 4. **Use Database-Side Triggers for Critical Operations**
If your application crashes before committing, triggers can act as a last line of defense. For example, a trigger on `DELETE` could log the deletion to a separate table:
```sql
-- PostgreSQL example: Log deletions to an audit table
CREATE TABLE deletions_log (
    id SERIAL PRIMARY KEY,
    table_name TEXT NOT NULL,
    record_id INT NOT NULL,
    deleted_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE OR REPLACE FUNCTION log_deletion()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO deletions_log (table_name, record_id) VALUES (TG_TABLE_NAME, NEW.id);
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_deletions
AFTER DELETE ON products
FOR EACH ROW EXECUTE FUNCTION log_deletion();
```

**Tradeoff**: Triggers add complexity and require careful maintenance.

---

### 5. **Validate Durability with Write-Ahead Logging Checks**
After a commit, verify that the database has actually synced to disk. This is tricky because databases don’t expose low-level WAL status directly, but you can:
- **Check transaction logs**: Query the `pg_stat_activity` view in PostgreSQL to see if a transaction is still marked as "in progress."
- **Use database-specific tools**:
  ```sql
  -- PostgreSQL: Check if WAL has been flushed to disk
  SELECT pg_is_in_recovery();
  -- Returns true if the database is in standby mode (after a restart)
  ```

---

### 6. **Implement Application-Level Durability Checks**
Your app should validate that writes succeeded before proceeding. For example:
```python
# Python example using SQLAlchemy
from sqlalchemy import create_engine, exc

def process_order(order_data):
    engine = create_engine("postgresql://user:pass@localhost/db")
    conn = engine.connect()

    try:
        conn.execute("BEGIN")
        conn.execute(
            "INSERT INTO orders (user_id, product_id, status) VALUES (:user_id, :product_id, 'pending')",
            {"user_id": order_data["user_id"], "product_id": order_data["product_id"]}
        )
        conn.execute(
            "UPDATE inventory SET quantity = quantity - 1 WHERE product_id = :product_id",
            {"product_id": order_data["product_id"]}
        )
        conn.commit()  # Only if both succeed

        # Double-check by querying
        result = conn.execute(
            "SELECT 1 FROM orders WHERE id = (SELECT MAX(id) FROM orders)"
        ).fetchone()
        if result is None:
            raise Exception("Write failed despite commit!")
    except exc.IntegrityError as e:
        conn.rollback()
        raise Exception(f"Order processing failed: {e}")
    finally:
        conn.close()
```

---

## Implementation Guide: Step-by-Step

### Step 1: Profile Your Database for Durability
- **PostgreSQL**: Run `SHOW synchronous_commit;` and `SHOW wal_level;` in `psql`.
- **MySQL**: Run `SHOW VARIABLES LIKE 'innodb_flush_log_at_trx_commit';`.
- **SQL Server**: Check `ALTER DATABASE YourDB SET RECOVERY FULL;`.

### Step 2: Configure Durability Settings
Update your database configuration (e.g., `postgresql.conf` or `my.cnf`) to enforce durability:
```ini
# PostgreSQL example
synchronous_commit = on
fsync = on
full_page_writes = on
```

### Step 3: Instrument Your Application
Add logging or metrics to track:
- Commit success/failure rates.
- Transaction retry counts.
- Database connection timeouts.

Example using OpenTelemetry (Python):
```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter

provider = TracerProvider()
provider.add_span_processor(ConsoleSpanExporter())
trace.set_tracer_provider(provider)

tracer = trace.get_tracer(__name__)

def trace_transaction(func):
    def wrapper(*args, **kwargs):
        with tracer.start_as_current_span(func.__name__):
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                tracer.current_span().set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                raise
    return wrapper

@trace_transaction
def save_user(user_data):
    # Your database logic here
    pass
```

### Step 4: Test for Durability Issues
Simulate failures:
1. **Crash the database mid-transaction**: Use `kill -9` (Linux) or Task Manager (Windows) to kill the PostgreSQL process.
2. **Network interrupts**: Use `tcpdump` or `netcut` to simulate packet loss between your app and database.
3. **Disk failure**: Use `dd` to fill up disk space and watch for errors.
4. **Automate tests**: Use tools like [PgBadger](https://github.com/dimitri/pgbadger) to analyze logs for durability anomalies.

### Step 5: Monitor for Data Corruption
Set up alerts for:
- Unexpected rollbacks.
- Long-running transactions (`pg_stat_activity` in PostgreSQL).
- Failed WAL recovery (`pg_is_in_recovery` returns `true` after a restart).

Example alerting rule (Prometheus + Alertmanager):
```yaml
# alerts.yml
groups:
- name: durability-alerts
  rules:
  - alert: LongRunningTransaction
    expr: pg_stat_activity_current_transaction_age > 60
    for: 1m
    labels:
      severity: warning
    annotations:
      summary: "Long-running transaction in PostgreSQL ({{ $value }}s old)"
```

---

## Common Mistakes to Avoid

1. **Assuming "commit = durable"**:
   - Not all databases sync to disk immediately after `COMMIT`. Check your `fsync` or `innodb_flush_log_at_trx_commit` settings.

2. **Ignoring connection pooling**:
   - Reused connections may hang or be in an inconsistent state. Use tools like PgBouncer to manage connections safely.

3. **Over-relying on application retries**:
   - Retries help with transient failures, but they won’t fix logical errors (e.g., race conditions).

4. **Skipping database backups**:
   - Even with durability settings, backups are your last line of defense. Use tools like `pg_dump` (PostgreSQL) or `mysqldump` (MySQL).

5. **Not testing failure scenarios**:
   - If your tests don’t simulate crashes or timeouts, you’re testing blind. Use chaos engineering tools like [Chaos Mesh](https://chaos-mesh.org/) or [PostgresChaos](https://github.com/chaos-mesh/postgres-chaos).

6. **Mixing durable and non-durable operations**:
   - Example: Using `BEGIN/COMMIT` for a critical payment but relying on `INSERT` for a non-critical log entry. Ensure all operations are atomic.

---

## Key Takeaways

- **Durability is a database feature, not just a transaction feature**. Configure your DB to enforce WAL and fsync.
- **Commit ≠ Durable**. Always verify writes by querying the database after commits.
- **Retry with caution**. Use exponential backoff, but don’t assume retries will fix logical errors.
- **Monitor for anomalies**. Long-running transactions, rollbacks, and WAL recovery issues are red flags.
- **Test failures**. Simulate crashes, network drops, and disk failures in staging.
- **Back up your data**. Durability settings protect against crashes; backups protect against disasters.
- **Document your approach**. Note which durability settings you’ve configured and why.

---

## Conclusion

Durability debugging is often overlooked until it’s too late—until your user’s data vanishes into thin air. By understanding your database’s durability mechanisms, configuring them correctly, and implementing application-level checks, you can build systems that *actually* persist data.

Start small:
1. Configure your database for maximum durability today.
2. Add retries to your critical transactions.
3. Simulate a failure in staging this week.

The goal isn’t perfection—it’s reducing the chance of data loss from *near-zero* to *unlikely*. And when you do that, your users (and your sleep schedule) will thank you.

---

### Further Reading
- [PostgreSQL Durability Guide](https://www.postgresql.org/docs/current/runtime-config-wal.html)
- [MySQL InnoDB Durability Options](https://dev.mysql.com/doc/refman/8.0/en/innodb-parameters.html#sysvar_innodb_flush_log_at_trx_commit)
- [Chaos Engineering for Databases](https://www.chaosengineering.com/database/)
- [Testing Durability with PgChaos](https://github.com/saikrishna/pgchaos)

---
```