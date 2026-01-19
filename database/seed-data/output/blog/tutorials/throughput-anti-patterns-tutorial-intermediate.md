```markdown
---
title: "Throughput Anti-Patterns: How Poor Design Slows Down Your Database (And How to Fix It)"
date: "2023-11-15"
author: "Alex Carter"
tags: ["database-design", "api-design", "back-end", "performance"]
description: "Learn how common throughput anti-patterns are secretly sabotaging your database performance. Practical examples, fixes, and tradeoffs included."
---

# Throughput Anti-Patterns: How Poor Design Slows Down Your Database (And How to Fix It)

As a backend engineer, you've probably faced the dreaded "system slows down under load" problem—especially during those critical moments when traffic spikes (e.g., Black Friday, product launches, or that one viral tweet from your CEO). You've probably rolled your eyes at colleagues who just "added more servers" or "tuned the DB" when the real issue was in the architecture.

In this guide, we'll explore **throughput anti-patterns**—design mistakes that silently drain database performance under load. You'll learn how to recognize them, fix them, and avoid common pitfalls. We'll cover **real-world examples**, tradeoffs, and code-level fixes with a focus on SQL and API design.

---

## Introduction: Why Throughput Matters

Throughput is the rate at which your system can process requests—measured in **transactions per second (TPS)** or **requests per second (RPS)**. Poor throughput isn't just about slow responses; it's about **system collapse** under realistic load. For example:

- A e-commerce platform that works fine at 1,000 RPS but crashes at 5,000 RPS loses **hundreds of thousands of dollars** per minute.
- A SaaS app with slow APIs frustrates users, leading to churn (and angry support tickets).

Many developers optimize for **latency** (response time) but neglect **throughput**. They might tweak indexes or cache aggressively, but their architecture is fundamentally flawed for high-volume scenarios. This is where throughput anti-patterns hide.

---

## The Problem: Common Throughput Anti-Patterns

Throughput anti-patterns are design choices that **scale poorly** under load. They often stem from:
1. **Ignoring database constraints** (e.g., "The DB is fast enough!").
2. **Overusing centralized components** (e.g., a single cache or event bus).
3. **Coupling everything together** (e.g., no clear separation of reads/writes).

Here are the most insidious ones:

### 1. **The "Big Table" Anti-Pattern**
   - **What it is**: Storing all data in a single table (or a few insanely wide tables) to "simplify joins."
   - **Why it hurts throughput**:
     - Joins and scans become **O(n)** operations.
     - Reads/writes are **contended** on a single table.
     - Backups and migrations are **brutal** (e.g., a 1TB table with 10M rows per day).

   **Example**:
   ```sql
   -- A "denormalized" table with everything in one place.
   CREATE TABLE users (
     user_id SERIAL PRIMARY KEY,
     -- 50+ columns: name, address, orders, transactions, etc.
     orders JSONB[],  -- Because "denormalization is bad" and we don't want to join.
     last_login TIMESTAMP
   );
   ```
   - **Problem**: A query like `SELECT * FROM users WHERE user_id = 123` now requires **decoding JSON**, while a `SELECT * FROM users JOIN orders ON ...` is **slow as molasses**.

### 2. **The "Cache All the Things" Anti-Pattern**
   - **What it is**: Over-reliance on a single cache layer (e.g., Redis) without considering **cache invalidation** or **hit rates**.
   - **Why it hurts throughput**:
     - Cache **stampedes** (thousands of requests hit the cache at once, causing spikes in DB load).
     - **Cache wars**: Teams fight over who owns the cache keys, leading to **fragmented logic**.
     - Cache **eviction storms**: When the cache is full, evictions can **thrash the database**.

   **Example**:
   ```python
   # A naive cache implementation with no invalidation logic.
   from functools import lru_cache

   @lru_cache(maxsize=10000)
   def get_expensive_data(user_id):
       # Expensive DB query here.
       return db.query(f"SELECT * FROM data WHERE user_id = {user_id}")
   ```
   - **Problem**: If `get_expensive_data(42)` is called **10,000 times simultaneously**, the cache hits zero immediately, and the DB **crashes**.

### 3. **The "Write-Preallocation" Anti-Pattern**
   - **What it is**: Pre-allocating or batching writes inefficiently (e.g., bulk inserts without considering **locking** or **concurrency**).
   - **Why it hurts throughput**:
     - **Lock contention**: If 100 threads acquire the same table lock for a bulk insert, throughput **drops to 100x slower**.
     - **Network bottlenecks**: Sending large batches over the network **wastes bandwidth**.
     - **Transaction bloat**: Long-running transactions block other operations.

   **Example**:
   ```sql
   -- A "smart" batch insert that locks the table for too long.
   BEGIN;
   INSERT INTO logs (user_id, event, timestamp)
   VALUES
     ('123', 'login', NOW()),
     ('123', 'purchase', NOW()),
     ('456', 'view', NOW());
   -- Oops, this took 500ms and blocked other writes!
   COMMIT;
   ```

### 4. **The "Chatty API" Anti-Pattern**
   - **What it is**: An API that makes **dozens of DB calls per request** instead of batching or using **pre-fetching**.
   - **Why it hurts throughput**:
     - **Database round-trips**: Each call to the DB adds **latency** and **connection overhead**.
     - **Connection pool exhaustion**: If every request opens a new connection, the pool **runs out fast**.
     - **N+1 query problem**: Simple queries turn into **hundreds of requests**.

   **Example**:
   ```python
   # A bad API that fetches orders one by one.
   def get_user_orders(user_id):
       orders = []
       for order_id in get_user_order_ids(user_id):  # DB call 1
           order = get_order_details(order_id)         # DB call 2, 3, 4, ...
           orders.append(order)
       return orders
   ```
   - **Problem**: If `get_user_order_ids` returns 100 IDs, this makes **101 DB calls** (1 for the IDs + 100 for each order).

### 5. **The "Global Transaction" Anti-Pattern**
   - **What it is**: Using **long-running transactions** (e.g., for "atomicity") without considering **locking** or **timeouts**.
   - **Why it hurts throughput**:
     - **Deadlocks**: If two transactions hold locks on the same rows, they **wait forever**.
     - **Blocking**: Other transactions **stall** while waiting for the global transaction to finish.
     - **Timeouts**: Eventually, the transaction **times out**, leaving the system in an inconsistent state.

   **Example**:
   ```sql
   -- A "long transaction" that locks rows for minutes.
   BEGIN;
   UPDATE accounts SET balance = balance - 100 WHERE user_id = 'alice'; -- Locks row!
   UPDATE accounts SET balance = balance + 100 WHERE user_id = 'bob';   -- Locks row!
   -- If this takes >5 seconds, other writes block!
   COMMIT;
   ```

---

## The Solution: Throughput-Friendly Patterns

Now that we’ve identified the anti-patterns, let’s fix them with **practical solutions**. Each fix includes **tradeoffs**—there’s no free lunch.

---

### 1. **Fix: Shard Your Tables**
   **Problem**: The "Big Table" anti-pattern causes **contention** and **slow queries**.
   **Solution**: **Vertical or horizontal sharding** to distribute load.

   #### Vertical Sharding (Split by columns)
   Break wide tables into **smaller, focused tables**.
   ```sql
   -- Before (bad):
   CREATE TABLE users (
     user_id SERIAL PRIMARY KEY,
     name VARCHAR(100),
     address JSONB,           -- Expensive to scan!
     orders JSONB,            -- Expensive to scan!
     preferences JSONB
   );

   -- After (good):
   CREATE TABLE users (
     user_id SERIAL PRIMARY KEY,
     name VARCHAR(100),
     created_at TIMESTAMP
   );

   CREATE TABLE user_addresses (
     user_id INT REFERENCES users(user_id),
     street VARCHAR(100),
     city VARCHAR(100),
     PRIMARY KEY (user_id)
   );

   CREATE TABLE user_orders (
     order_id SERIAL,
     user_id INT REFERENCES users(user_id),
     product_id INT,
     amount DECIMAL(10, 2),
     PRIMARY KEY (order_id)
   );
   ```
   - **Benefits**:
     - Queries target **smaller tables**.
     - Indexes are **smaller and faster**.
   - **Tradeoffs**:
     - Requires **joins** (but modern DBs optimize these well).
     - **Schema migrations** are harder.

   #### Horizontal Sharding (Split by rows)
   Distribute rows across **multiple tables** (e.g., by `user_id` range).
   ```sql
   -- Shard users by ID range.
   CREATE TABLE users_shard_1 (
     user_id INT PRIMARY KEY,
     -- columns...
   );

   CREATE TABLE users_shard_2 (
     user_id INT PRIMARY KEY,
     -- columns...
   );
   ```
   - **Benefits**:
     - **Parallel reads/writes** on shards.
     - **Easier scaling** (add more shards).
   - **Tradeoffs**:
     - **Join complexity** (you may need a "lookup table").
     - **Eventual consistency** (if you’re using async writes).

---

### 2. **Fix: Cache with Intelligence (Not Just "Cache Everything")**
   **Problem**: The "Cache All the Things" anti-pattern leads to **cache storms** and **logic sprawl**.
   **Solution**: **Strategic caching** with **invalidation policies** and **local caching**.

   #### A. **Cache Invalidation Strategies**
   - **Time-to-Live (TTL)**: Let the cache expire after a timeout.
     ```python
     # Using Redis with TTL.
     def get_user_data(user_id):
         cache_key = f"user:{user_id}"
         data = redis.get(cache_key)
         if data:
             return data
         data = db.query(f"SELECT * FROM users WHERE id = {user_id}")
         redis.setex(cache_key, 3600, data)  # Cache for 1 hour.
         return data
     ```
   - **Write-through**: Update cache **whenever data changes**.
     ```python
     def update_user_balance(user_id, amount):
         db.execute(f"UPDATE users SET balance = balance + {amount} WHERE id = {user_id}")
         redis.delete(f"user:{user_id}:balance")  # Invalidate balance cache.
     ```
   - **Publish-Subscribe**: Use Redis Pub/Sub to **invalidate cache** when data changes.
     ```python
     # When data changes, publish an event.
     redis.publish("user:updated", user_id)

     # Cache listener (in another process).
     def cache_listener():
         while True:
             message = redis.blpop("user:updated")
             if message:
                 redis.delete(f"user:{message[1]}")  # Delete cache.
     ```

   #### B. **Local Caching (Avoid Cache Storms)**
   Use **client-side caching** (e.g., `functools.lru_cache` in Python) to **reduce DB load**.
   ```python
   from functools import lru_cache

   @lru_cache(maxsize=1000)
   def get_product_details(product_id):
       return db.query(f"SELECT * FROM products WHERE id = {product_id}")
   ```
   - **Tradeoffs**:
     - **Memory usage** (local caches consume RAM).
     - **Stale data** (if the DB changes, local cache may not reflect it).

---

### 3. **Fix: Batch Writes (But Smartly)**
   **Problem**: The "Write-Preallocation" anti-pattern causes **lock contention**.
   **Solution**: **Batch writes** but **minimize lock duration**.

   #### A. **Bulk Inserts (When Appropriate)**
   ```sql
   -- Use COPY for bulk inserts (faster than INSERT).
   COPY users(id, name) FROM '/tmp/users.csv' DELIMITER ',';
   ```
   - **When to use**: Initial data loads, ETL jobs.

   #### B. **Small Batches (For High-Concurrency Apps)**
   ```python
   # Process writes in small batches (e.g., 100 rows at a time).
   def batch_update(users):
       batch = []
       for user in users:
           batch.append(user)
           if len(batch) >= 100:
               db.execute_batch(batch)
               batch = []
       if batch:
           db.execute_batch(batch)
   ```
   - **Tradeoffs**:
     - **Network overhead** (smaller batches mean more round-trips).
     - **Transaction size** (too small = high overhead; too big = locks).

   #### C. **Asynchronous Writes (For Non-Critical Data)**
   Use a **message queue** (e.g., Kafka, RabbitMQ) to **decouple writes**.
   ```python
   # Write to DB async via a queue.
   def process_order(order):
       queue.publish("orders", order)
       # Return immediately (user doesn't wait for DB).
   ```
   - **Tradeoffs**:
     - **Eventual consistency** (data may not be immediately available).
     - **Queue management** (you need a worker process).

---

### 4. **Fix: Optimize Your API (Reduce DB Calls)**
   **Problem**: The "Chatty API" anti-pattern causes **connection exhaustion**.
   **Solution**: **Batch requests** and **pre-fetch data**.

   #### A. **Single-Table Lookups**
   ```python
   # Bad: Multiple DB calls.
   def get_user_profile(user_id):
       user = db.query(f"SELECT * FROM users WHERE id = {user_id}")  # Call 1
       orders = db.query(f"SELECT * FROM orders WHERE user_id = {user_id}")  # Call 2
       return {"user": user, "orders": orders}

   # Good: Single query with JOIN.
   def get_user_profile(user_id):
       return db.query("""
           SELECT u.*, o.order_id, o.amount
           FROM users u
           LEFT JOIN orders o ON u.id = o.user_id
           WHERE u.id = %s
       """, user_id)
   ```

   #### B. **Pre-Fetch in Background**
   Use **caching** or **materialized views** to pre-compute data.
   ```sql
   -- Materialized view for "user + orders" (PostgreSQL).
   CREATE MATERIALIZED VIEW user_profiles AS
   SELECT u.id, u.name, o.order_id, o.amount
   FROM users u
   LEFT JOIN orders o ON u.id = o.user_id;
   ```
   - **Tradeoffs**:
     - **Refresh overhead** (materialized views need updates).
     - **Storage bloat** (stores pre-computed data).

   #### C. **GraphQL (For Flexible Queries)**
   GraphQL lets clients **request only what they need**, reducing over-fetching.
   ```graphql
   # Instead of:
   # GET /users/123?include=orders,address

   # Clients can ask for:
   query {
     user(id: 123) {
       id
       name
       orders {
         id
         amount
       }
     }
   }
   ```
   - **Tradeoffs**:
     - **N+1 problem** is still possible (but solvable with DataLoader).
     - **Complexity** (requires GraphQL server).

---

### 5. **Fix: Short Transactions (No Long Runs)**
   **Problem**: The "Global Transaction" anti-pattern causes **deadlocks**.
   **Solution**: **Keep transactions short** and **use optimistic locking**.

   #### A. **Short Transactions**
   ```sql
   -- Bad: Long-running transaction.
   BEGIN;
   -- Do 100 things...
   COMMIT; -- Takes 2 seconds!

   -- Good: Short transactions.
   BEGIN;
   UPDATE accounts SET balance = balance - 100 WHERE user_id = 'alice';
   COMMIT; -- Takes 10ms!
   ```

   #### B. **Optimistic Locking (For Concurrency)**
   Use `SELECT ... FOR UPDATE SKIP LOCKED` or **version columns**.
   ```sql
   -- PostgreSQL: Only lock rows you need.
   UPDATE accounts
   SET balance = balance - 100
   WHERE user_id = 'alice' AND balance > 0
   FOR UPDATE SKIP LOCKED;  -- Skip already locked rows.
   ```

   #### C. **Sagacity Pattern (For Distributed Locks)**
   For **high-contention operations**, use a **distributed lock** (e.g., Redis `SETNX`).
   ```python
   def transfer_funds(from_user, to_user, amount):
       lock_key = f"transfer:{from_user}:{to_user}"
       if not redis.setnx(lock_key, "1", nx=True, ex=5):  # 5-second lock
           return "Rate limited."
       try:
           db.execute("UPDATE accounts SET balance = balance - ? WHERE id = ?", amount, from_user)
           db.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", amount, to_user)
       finally:
           redis.delete(lock_key)
   ```

---

## Implementation Guide: How to Audit Your System

Now that you know the anti-patterns, how do you **find them in your own code**? Here’s a step-by-step guide:

### 1. **Check Database Queries**
   - Use **slow query logs** (PostgreSQL: `log_min_duration_statement`).
   - Look for:
     - `SELECT * FROM huge_table WHERE ...` (wide scans).
     - Long-running `UPDATE`/`DELETE` statements.
    