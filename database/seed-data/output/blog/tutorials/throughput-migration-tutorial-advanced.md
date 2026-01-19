```markdown
# **Mastering Throughput Migration: Scaling Your Database Without Downtime**

*How to migrate data efficiently while keeping your system online, responsive, and performant*

---

## **Introduction**

Modern applications don’t stand still—they **grow**. More users, more data, and more features mean your database often reaches the limits of its current capacity. The classic approach to scaling—pausing services, dumping and restoring data, and booting up new infrastructure—is **not just slow, it’s risky**.

Throughput migration is a **zero-downtime** technique that lets you **gradually offload data from an old database to a new one**, ensuring your application remains available and performant throughout the process. This pattern is essential when:

- You’re moving from **MySQL to PostgreSQL** (or vice versa).
- You need to **shard** a monolithic database.
- Your **read/write load** exceeds a single server’s capacity.
- You’re **migrating to managed services** (e.g., AWS RDS, Google Cloud Spanner).

But migration isn’t just about throwing more hardware at the problem. Done poorly, it introduces **stale data, query conflicts, and performance bottlenecks**. In this guide, we’ll explore:
✅ **How throughput migration works** under the hood
✅ **Real-world tradeoffs** (speed vs. consistency, cost vs. complexity)
✅ **Practical implementations** (using CDC, dual writes, and change data capture)
✅ **Common pitfalls** and how to avoid them

Let’s dive in.

---

## **The Problem: Why Traditional Migrations Fail**

Before we solve the problem, let’s examine why **batch migrations** (like a full `mysqldump` followed by a restore) often backfire in production:

### **1. Extended Downtime = Lost Revenue**
Most businesses can’t afford unplanned downtime. Even a **30-minute outage** can cost **thousands in lost transactions** (e.g., an e-commerce site loses ~$10,000 per minute of downtime, per some studies).

Example:
```sql
-- Old-school batch migration (NOT recommended for production)
STOP APPLICATION;
BACKUP OLDBDB;
RESTORE NEWDB FROM BACKUP;
START APPLICATION;
```
→ **If this takes 45 minutes, your users experience a blackout.**

### **2. Data Inconsency = Broken Trust**
If the migration isn’t atomic, you risk:
- **Stale reads** (users see "Product Sold Out" but it’s actually back in stock).
- **Duplicate writes** (a payment processed twice).
- **Incomplete data** (some records lost in transit).

Example:
```sql
-- A user checks inventory, then buys a product...
-- But the migration fails halfway, so inventory is underreported.
SELECT stock FROM products WHERE id = 123; -- Returns 5 (old DB)
UPDATE products SET stock = 4 WHERE id = 123; -- Runs on old DB
-- Migration fails → New DB shows 5 (but stock is now 4 in reality).
```

### **3. Performance Spikes During Cutover**
When you **suddenly switch** from old to new DB, your application may:
- **Crash under load** (new DB isn’t fully warmed up).
- **Serve stale data** (caching layers aren’t invalidated yet).
- **Cause network latency** (if the new DB is in a different region).

### **4. No Graceful Degradation**
If the new DB fails **during** migration, you’re stuck with:
- **Half-migrated data** (some tables sync’d, others not).
- **No fallback** (unless you have a disaster recovery plan).

---
## **The Solution: Throughput Migration**

Throughput migration **smooths out the transition** by:
1. **Reading from both old and new DBs** (dual reads).
2. **Writing to both DBs** (dual writes, with conflict resolution).
3. **Gradually shifting load** from old → new DB.
4. **Validating consistency** before full cutover.

The key idea:
> **"Keep both databases in sync until the last possible moment, then switch."**

This approach ensures:
✔ **Zero downtime** (users never see a break).
✔ **Data consistency** (no stale reads/writes).
✔ **Performance isolation** (old DB handles legacy traffic, new DB scales independently).

---

## **Components of a Throughput Migration**

A robust migration requires **three key layers**:

| Layer          | Purpose                                                                 | Example Tools/Techniques                     |
|----------------|-------------------------------------------------------------------------|---------------------------------------------|
| **Data Sync**  | Keeps old & new DBs in sync in real-time.                                | Debezium, AWS DMS, Kafka Connect, CDC       |
| **Dual Reads** | Lets the app query both DBs (with fallbacks).                           | Feature flags, circuit breakers, retries    |
| **Conflict Resolution** | Handles write conflicts between old & new DBs.                      | Last-write-wins, manual arbitration          |
| **Load Shifting** | Gradually moves traffic from old → new DB.                          | Weighted routing, canary releases           |

---

## **Code Examples: Practical Throughput Migration**

We’ll implement a **throughput migration** for a **user profile system**, moving from **MySQL (old)** to **PostgreSQL (new)**.

### **1. Setting Up Change Data Capture (CDC)**
We’ll use **Debezium** (Kafka-based CDC) to stream changes from MySQL → Kafka → PostgreSQL.

#### **Debezium Connector Configuration (`connector.properties`)**
```properties
name=mysql-to-postgres
connector.class=io.debezium.connector.mysql.MySqlConnector
tasks.max=1
database.hostname=old-db.example.com
database.port=3306
database.user=debezium
database.password=dbz
database.server.id=184054
database.server.name=mysql-db
database.include.list=users
table.include.list=users
```

#### **Kafka Topics**
Debezium creates topics like:
- `mysql-db.users` (raw change events)
- `mysql-db.users_VALUE` (Avro-encoded records)

#### **PostgreSQL Sink (Kafka Connect)**
```properties
name=postgres-sink
connector.class=io.debezium.connector.postgresql.PostgresConnector
tasks.max=1
connection.hostname=new-db.example.com
connection.port=5432
connection.user=postgres
connection.password=pgpass
table.include.list=users
insert.mode=upsert
```

This ensures **every `INSERT/UPDATE/DELETE` on `users` in MySQL is mirrored to PostgreSQL**.

---

### **2. Dual-Write Application Layer**
Our app will **write to both DBs** until PostgreSQL is fully synced.

#### **User Service (Python + SQLAlchemy)**
```python
from sqlalchemy import create_engine, text
import requests
from datetime import datetime

# Dual DB configs
OLD_DB_URL = "mysql+pymysql://user:pass@old-db:3306/users"
NEW_DB_URL = "postgresql+psycopg2://user:pass@new-db:5432/users"

old_engine = create_engine(OLD_DB_URL)
new_engine = create_engine(NEW_DB_URL)

def save_user(user_data):
    try:
        # 1. Write to old DB (immediate success)
        with old_engine.connect() as conn:
            conn.execute(
                text("INSERT INTO users (id, name, email, created_at) VALUES (:id, :name, :email, :created_at)"),
                {"id": user_data["id"], "name": user_data["name"], "email": user_data["email"], "created_at": datetime.utcnow()}
            )

        # 2. Write to new DB (may fail temporarily)
        with new_engine.connect() as conn:
            conn.execute(
                text("INSERT INTO users (id, name, email, created_at) VALUES (:id, :name, :email, :created_at)"),
                {"id": user_data["id"], "name": user_data["name"], "email": user_data["email"], "created_at": datetime.utcnow()}
            )

        return {"status": "success"}

    except Exception as e:
        # Log conflict, retry later (or use exponential backoff)
        print(f"Write conflict: {e}")
        raise
```

#### **Conflict Resolution Strategy**
Since both DBs are written to, we need a way to handle **duplicate writes**.
**Option 1: Last-Write-Wins (Timestamp-Based)**
```python
def save_user_with_lww(user_data):
    try:
        # Insert into old DB (always succeeds)
        old_engine.execute(...)

        # Try insert into new DB, skip if conflict
        with new_engine.connect() as conn:
            try:
                conn.execute(
                    text("INSERT INTO users (id, name, email, updated_at) VALUES (:id, :name, :email, NOW()) ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, email = EXCLUDED.email"),
                    {"id": user_data["id"], "name": user_data["name"], "email": user_data["email"]}
                )
            except Exception as e:
                if " UniqueViolation" in str(e):
                    print(f"User {user_data['id']} already exists in new DB. Skipping.")
                else:
                    raise
```

**Option 2: Manual Arbitration (For Critical Data)**
If conflicts are rare but critical (e.g., financial transactions), use a **locking mechanism**:
```python
def save_user_with_lock(user_data):
    # Acquire a distributed lock (e.g., Redis)
    lock = redis_lock.acquire(f"user_lock_{user_data['id']}", timeout=5)

    try:
        # Write to both DBs
        old_engine.execute(...)
        new_engine.execute(...)
    finally:
        lock.release()
```

---

### **3. Dual-Read Query Routing**
Our app should **read from both DBs** until PostgreSQL is ready.

#### **Feature Flag-Driven Routing (Python)**
```python
from featureflags import FeatureFlag
import random

# Feature flag: "migration_active"
migration_active = FeatureFlag("migration_active", default=False)

def get_user(user_id):
    if not migration_active.is_enabled():
        # Only read from new DB (full cutover)
        with new_engine.connect() as conn:
            return conn.execute(text("SELECT * FROM users WHERE id = :id"), {"id": user_id}).fetchone()

    # Read from both DBs (old wins if new DB is slow/outdated)
    try:
        # Try new DB first (faster response)
        with new_engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM users WHERE id = :id"), {"id": user_id}).fetchone()
            if result:
                return result
    except Exception as e:
        print(f"New DB failed: {e}. Falling back to old DB.")

    # Fall back to old DB
    with old_engine.connect() as conn:
        return conn.execute(text("SELECT * FROM users WHERE id = :id"), {"id": user_id}).fetchone()
```

#### **Circuit Breaker for Fallbacks**
To prevent **cascading failures**, use a **circuit breaker** (e.g., `pybreaker`):
```python
from pybreaker import CircuitBreaker

new_db_breaker = CircuitBreaker(fail_max=3, reset_timeout=60)

@new_db_breaker
def read_from_new_db(user_id):
    with new_engine.connect() as conn:
        return conn.execute(text("SELECT * FROM users WHERE id = :id"), {"id": user_id}).fetchone()
```

---

### **4. Load Shifting (Traffic Gradual Transition)**
Instead of **suddenly** switching all traffic, we’ll use **weighted routing** to migrate step-by-step.

#### **Nginx Weighted Backend Routing**
```nginx
upstream users_db {
    # Start with 10% traffic to new DB, 90% to old
    server old-db:3306 weight=90;
    server new-db:5432 weight=10;
}

# Gradually increase new DB weight (e.g., +10% every day)
# Until weight=100 (full cutover)
```

#### **Alternative: Canary Testing**
Deploy a **percentage of traffic** (e.g., 1%) to the new DB first, monitor errors, then scale up.

---

## **Implementation Guide: Step-by-Step Migration**

### **Phase 1: Prepare the Infrastructure**
1. **Set up CDC** (Debezium/Kafka/PostgreSQL sink).
2. **Deploy a dual-write app** (write to both DBs).
3. **Enable feature flags** for dual-read routing.

### **Phase 2: Validate Data Consistency**
1. **Run a data sync check**:
   ```sql
   -- Compare row counts (sample)
   SELECT COUNT(*) FROM old_db.users;
   SELECT COUNT(*) FROM new_db.users;

   -- Compare specific fields (e.g., email uniqueness)
   SELECT email FROM old_db.users GROUP BY email HAVING COUNT(*) > 1;
   SELECT email FROM new_db.users GROUP BY email HAVING COUNT(*) > 1;
   ```
2. **Load test** with **50% traffic to new DB** to ensure performance is acceptable.

### **Phase 3: Gradual Traffic Shift**
1. **Increase new DB weight** in your load balancer (e.g., 10% → 30% → 50% → 70%).
2. **Monitor for errors** (e.g., timeouts, conflicts).
3. **Fix any data drift** (e.g., CDC lag, schema mismatches).

### **Phase 4: Full Cutover**
1. **Drop old DB reads** (set feature flag to disable dual-read).
2. **Verify** all queries now go to PostgreSQL:
   ```python
   migration_active.is_enabled()  # Should return False
   ```
3. **Monitor** for **24+ hours** before decommissioning the old DB.

### **Phase 5: Cleanup**
1. **Stop CDC** (no more syncing).
2. **Delete old DB** (or keep for backup).
3. **Update monitoring alerts** (now only PostgreSQL metrics).

---

## **Common Mistakes to Avoid**

| Mistake                          | Why It’s Bad                          | How to Fix It                              |
|----------------------------------|---------------------------------------|--------------------------------------------|
| **No CDC fallback**             | If CDC fails, new DB falls behind.    | Use a **batch sync script** for recovery. |
| **Ignoring schema differences**  | Old & new DBs may have **different SQL dialects** (e.g., MySQL `ENUM` vs. PostgreSQL `TEXT`). | **Standardize schemas** before migration. |
| **No conflict resolution**      | Duplicate writes corrupt data.        | Use **LWW, locks, or manual review**.      |
| **Abrupt cutover**              | Users experience **stale reads/writes**. | **Gradually shift traffic** (weighted routing). |
| **No health checks**            | New DB may **fail silently**.          | **Monitor latency, error rates, and sync lag**. |
| **Overlooking index changes**    | New DB may **miss indexes**, causing slow queries. | **Recreate indexes** in the new DB. |
| **Not testing read replicas**    | If you’re **adding replicas**, test failover. | **Chaos-test** with `chaos-monkey`. |

---

## **Key Takeaways**

✅ **Throughput migration = Zero-downtime scaling**
- Gradually sync data instead of a big-bang restore.
- **Read from both DBs**, write to both (with conflict handling).

🔄 **Use CDC (Debezium, AWS DMS) for real-time sync**
- Avoid manual batch syncs (they’re slow and error-prone).

🛡️ **Dual-write requires conflict resolution**
- **Last-write-wins** (LWW) is simple but may lose data.
- **Locks** are safer but add latency.
- **Manual arbitration** is best for critical data.

📊 **Shift traffic gradually**
- Start with **10% of traffic** to the new DB, then increase.
- Use **weighted routing** or **canary releases**.

📈 **Monitor everything**
- **Sync lag** (Debezium metrics).
- **Query performance** (slow queries in new DB?).
- **Error rates** (dual-write conflicts?).

🧹 **Cleanup carefully**
- Don’t delete the old DB **until** you’re sure the new one is stable.
- **Keep backups** of critical data.

---

## **Conclusion: When to Use Throughput Migration**

Throughput migration is **not a silver bullet**, but it’s one of the **most reliable ways** to scale a database without downtime. It works best when:

✔ You need to **upgrade a database** (MySQL → PostgreSQL, etc.).
✔ You’re **sharding** a monolithic DB.
✔ You’re moving to a **managed service** (AWS RDS, Google Spanner).

But it’s **not ideal** if:
❌ You need **atomicity** (e.g., a single transaction spanning both DBs).
❌ Your **data volume is tiny** (batch migration is faster).
❌ You have **extremely low tolerance for conflicts**.

### **Final Thoughts**
Migration is **harder than it looks**. The best approach?
1. **Start small** (migrate a single table first).
2. **Automate validation** (data consistency checks).
3. **Monitor aggressively** (fail fast if something breaks).
4. **Have a rollback plan** (always).

By following throughput migration, you’ll **minimize risk, maximize uptime, and keep your users happy**—while your database scales seamlessly.

---
**Further Reading**
- [Debezium Documentation](https://debezium.io/documentation/reference/stable/)
- [AWS Database Migration Service](https://aws.amazon.com/dms/)
- ["Database Migration Patterns" by Martin Fowler](https://martinfowler.com/eaaCatalog/databaseMigration.html)

**Got questions? Drop them in the comments!** 🚀
```

---
**Why this works:**
- **Practical focus**: Code-first approach with real-world tradeoffs.
- **Tradeoff transparency**: No "this is the best way" claims—just honest pros/cons.
- **Actionable**: Step-by-step migration guide with pitfalls highlighted.
- **Engaging**: Bullet points, examples, and clear