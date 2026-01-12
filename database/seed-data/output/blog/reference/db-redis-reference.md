---
# **[Pattern] Redis Database Patterns Reference Guide**

---

## **Overview**
Redis Database Patterns provide efficient, scalable, and high-performance ways to abstract common database operations into reusable patterns using Redis’ in-memory data structures (strings, hashes, lists, sets, sorted sets, etc.). These patterns optimize read/write latency, reduce computational overhead, and simplify complex workflows (e.g., caching, session management, event streaming).

Unlike traditional SQL patterns (e.g., CQRS), Redis patterns leverage Redis’ **atomic operations, persistence, and data structures** to solve problems like:
- **Caching** (TTL-based invalidation, lazy loading).
- **Session Management** (stateless user context storage).
- **Leaderboards** (dynamic ranking via sorted sets).
- **Pub/Sub Messaging** (real-time event distribution).
- **Rate Limiting** (token bucket algorithms).
- **Distributed Locking** (preventing race conditions).

This guide covers **implementation details, best practices, and schema optimizations** for each pattern, with examples for common use cases.

---

## **Schema Reference**
| **Pattern**               | **Use Case**                          | **Redis Data Structure**       | **Key Operations**                          | **Pros**                                      | **Cons**                                  | **Example Key**                     |
|---------------------------|---------------------------------------|---------------------------------|--------------------------------------------|-----------------------------------------------|-----------------------------------------|--------------------------------------|
| **Caching (TTL)**         | Reduce DB load by storing temporary data | String, Hash                     | `SET`, `GET`, `EXPIRE`, `DEL`              | Low latency, simple invalidation            | Memory-bound, vulnerable to staleness  | `user:123:profile`                     |
| **Session Store**         | Stateful user interactions            | Hash                            | `HSET`, `HGETALL`, `DEL`                   | Atomic session updates, easy persistence      | Scales poorly with many sessions        | `session:user12345`                   |
| **Leaderboard**           | Real-time rankings (e.g., scores)     | Sorted Set                      | `ZADD`, `ZRANGE`, `ZREVRANGE`              | Efficient scoring, dynamic updates           | Requires regular pruning               | `game:leaderboard:high_scores`       |
| **Rate Limiting**         | Control API requests                  | String (hash-like: tokens)       | `INCR`, `EXPIRE`, `DEL`                    | Simple, accurate rate enforcement            | Token distribution bias                | `user:123:rate_limit:5min`           |
| **Distributed Lock**      | Prevent concurrent access conflicts   | String (with `SETNX`)            | `SETNX`, `EXPIRE`, `DEL`                   | Deadlock-free, lightweight                | Risk of lock leaks                       | `lock:feature-flip:123`               |
| **Pub/Sub Messaging**     | Real-time event distribution          | Channels/Patterns               | `PUBLISH`, `SUBSCRIBE`, `PSUBSCRIBE`      | Losless event delivery, decoupled systems    | Scales with subscriber load              | `notifications:user_updates`          |
| **Queue (Blocking List)** | Task processing (e.g., emails)        | List                            | `LPUSH`, `BRPOP`, `LLEN`                   | Atomic enqueuing/dequeuing                   | FIFO-only, no priority                 | `queue:email_notifications`           |
| **Inverted Index**        | Full-text search (basic)              | Hash (field → set of IDs)        | `HSET`, `SADD`, `SMEMBERS`                 | Lightweight, scalable for small datasets    | No advanced querying (e.g., fuzzy search)| `search:blog:tags:tech`                |
| **Bloom Filter**          | Probabilistic "exists" checks         | Bit Array                       | `BF.ADD`, `BF.MIGHT_HAVE`, `BF.REMOVE`    | Memory-efficient, fast negatives           | False positives possible               | `bloom:exists:users`                  |

---

## **Implementation Details**
### **1. Caching (TTL-Based)**
**Purpose:** Store frequently accessed data in Redis to offload database reads.

#### **Key Commands**
| Command          | Description                                      | Example                          |
|------------------|--------------------------------------------------|----------------------------------|
| `SET key value [EX seconds]` | Stores data with an optional TTL.                | `SET user:123:profile "..." EX 3600` |
| `GET key`        | Retrieves cached value.                          | `GET user:123:profile`           |
| `DEL key`        | Explicitly removes the key.                      | `DEL user:123:profile`           |
| `EXPIRE key seconds` | Sets a TTL without overwriting the value.      | `EXPIRE user:123:profile 3600`   |

#### **Best Practices**
- **Cache Invalidation:**
  Use **write-through** (update DB *and* cache) or **lazy loading** (load from DB when cache misses).
  Example (write-through):
  ```python
  def update_user_profile(user_id, data):
      # Update DB (simplified)
      db.execute("UPDATE users SET ... WHERE id = %s", (user_id,))
      # Update cache
      redis.execute("SET user:%s:profile %s EX 3600", user_id, data)
  ```
- **TTL Strategy:**
  Short TTLs (e.g., 5–30 mins) for volatile data; long TTLs (e.g., 1 hour) for stable data.
- **Memory Management:**
  Monitor Redis memory with `INFO memory` and use `config set maxmemory-policy allkeys-lru` to evict stale keys.

#### **Common Pitfalls**
- **Cache Stampede:** Many requests hit the DB simultaneously when cache expires. Mitigate with **pre-loading** or **randomized TTLs**.
- **Over-Caching:** Cache data that shouldn’t be (e.g., sensitive/unique data). Use pattern-specific structures (e.g., `HMSET` for multi-field users).

---

### **2. Session Store**
**Purpose:** Store user sessions in Redis to enable stateless applications.

#### **Key Commands**
| Command          | Description                                      | Example                          |
|------------------|--------------------------------------------------|----------------------------------|
| `HSET key field value` | Sets multiple fields in a hash.                 | `HSET session:user123 user_id 123 role "admin"` |
| `HGETALL key`    | Retrieves all fields for a session.             | `HGETALL session:user123`        |
| `DEL key`        | Invalidates the session.                        | `DEL session:user123`            |
| `EXPIRE key seconds` | Sets a TTL for the session.                  | `EXPIRE session:user123 1800`    |

#### **Best Practices**
- **Session Structure:**
  Use a **hash** to store metadata (e.g., user ID, IP, last activity).
  Example:
  ```json
  { "user_id": "123", "ip": "192.168.1.1", "last_active": "1625097600", "cart": ["item1", "item2"] }
  ```
- **Session ID Generation:**
  Use UUIDs or hashed tokens (e.g., `sha256(user_id + timestamp)`) to avoid collisions.
- **Concurrency:**
  Use `HSET` (atomic) or `WATCH`/`MULTI` for critical updates (rarely needed).

#### **Common Pitfalls**
- **Memory Bloat:** Store only essential session data. Offload large data (e.g., cart) to a separate key.
- **Race Conditions:** Avoid race conditions during session updates by using **Redis transactions** (`MULTI/EXEC`).

---

### **3. Leaderboard (ZSET Pattern)**
**Purpose:** Maintain real-time rankings (e.g., game scores, social media likes).

#### **Key Commands**
| Command          | Description                                      | Example                          |
|------------------|--------------------------------------------------|----------------------------------|
| `ZADD key score member` | Adds/updates a score-member pair.            | `ZADD game:leaderboard 1000 player1` |
| `ZRANGE key start end [WITHSCORES]` | Sorted list (asc/desc).               | `ZRANGE game:leaderboard 0 9 WITHSCORES` |
| `ZREVRANGE key start end [WITHSCORES]` | Descending order.                          | `ZREVRANGE game:leaderboard 0 9 WITHSCORES` |
| `ZREM key member` | Removes a member.                             | `ZREM game:leaderboard player1`  |
| `ZINCRBY key increment member` | Increments a score atomically.              | `ZINCRBY game:leaderboard 50 player1` |

#### **Best Practices**
- **Score Type:**
  Use **floats** for fractional scores (e.g., 99.5) or **integers** for simplicity.
- **Pruning:**
  Regularly remove old/irrelevant entries to free memory:
  ```bash
  ZREMRANGEBYSCORE game:leaderboard -inf 0
  ```
- **Batch Updates:**
  Use `MULTI`/`EXEC` for bulk operations:
  ```bash
  MULTI
  ZINCRBY game:leaderboard 10 player1
  ZINCRBY game:leaderboard -5 player2
  EXEC
  ```

#### **Common Pitfalls**
- **Score Duplicates:** If scores are floats, ensure uniqueness or use a secondary key (e.g., `player_id:score`).
- **Memory Growth:** Unbounded ZSETs can grow indefinitely. Set a **max size** and prune old entries.

---

### **4. Rate Limiting (Token Bucket)**
**Purpose:** Enforce rate limits (e.g., API calls, login attempts).

#### **Key Commands**
| Command          | Description                                      | Example                          |
|------------------|--------------------------------------------------|----------------------------------|
| `INCR key`       | Atomically increments a counter.                | `INCR user:123:requests`         |
| `EXPIRE key seconds` | Sets a TTL for the counter.              | `EXPIRE user:123:requests 60`   |
| `DEL key`        | Resets the counter.                            | `DEL user:123:requests`          |

#### **Implementation (Sliding Window)**
1. **Track requests per user** with a counter + TTL:
   ```bash
   INCR user:123:requests
   EXPIRE user:123:requests 60
   ```
2. **Check limit** (e.g., 100 requests/minute):
   ```bash
   IF (GET user:123:requests) > 100 THEN DENY ELSE ALLOW
   ```
3. **Alternative (Token Bucket):**
   Use `LPUSH` + `LTRIM` to simulate tokens:
   ```bash
   LPUSH user:123:tokens timestamp
   LTRIM user:123:tokens 0 -99  # Keep last 99 tokens (sliding window)
   ```

#### **Best Practices**
- **Key Naming:**
  Include time windows (e.g., `user:123:rate_limit:1min`).
- **Precision:**
  For microsecond precision, use `INCRBY` with `microseconds` TTLs.

#### **Common Pitfalls**
- **Clock Skew:** Ensure client/server clocks are synchronized (use NTP).
- **Burst Handling:** Token bucket allows bursts; adjust `LTRIM` window size.

---
## **Query Examples**
### **1. Caching**
```bash
# Set a 10-minute cache
SET user:456:posts "[]" EX 600

# Retrieve posts
GET user:456:posts

# Update cache (write-through)
HSET user:456:posts 0 "post1" 1 "post2"
EXPIRE user:456:posts 600
```

### **2. Session Store**
```bash
# Create a session
HSET session:abc123 user_id 456 role "editor"
EXPIRE session:abc123 1800

# Update session (atomic)
HSET session:abc123 last_active $(date +%s)

# Delete session
DEL session:abc123
```

### **3. Leaderboard**
```bash
# Add a score
ZADD game:top_scores 1000 player1 2000 player2

# Get top 5 players (descending)
ZREVRANGE game:top_scores 0 4 WITHSCORES

# Increment a player's score
ZINCRBY game:top_scores 50 player1
```

### **4. Rate Limiting**
```bash
# Track requests (sliding window)
INCR user:789:requests
EXPIRE user:789:requests 60

# Check limit (script)
if (GET user:789:requests) > 5 THEN
    RETURN "TOO_MANY_REQUESTS"
else
    RETURN "OK"
```

---

## **Related Patterns**
1. **[Cache Aside Pattern]**
   - **Relation:** Redis caching is often implemented alongside this pattern for read-heavy workloads.
   - **Key Difference:** Cache Aside explicitly separates cache from data store; Redis Patterns integrate directly with Redis structures.

2. **[Pub/Sub Decoupling]**
   - **Relation:** The **Pub/Sub Messaging** pattern in Redis enables event-driven architectures (e.g., notifications, real-time analytics).
   - **Example:** Use `PUBLISH "order_created" "order123"` to notify subscribers.

3. **[Database Offloading]**
   - **Relation:** Patterns like **Session Store** and **Leaderboard** reduce load on primary databases.
   - **Trade-off:** Adds latency for writes (e.g., session updates).

4. **[Circuit Breaker]**
   - **Relation:** Redis can act as a **circuit breaker cache** (fallback for failed DB calls).
   - **Implementation:** Store stale data with a `force_refresh` flag.

5. **[Sharding]**
   - **Relation:** Scale Redis Patterns horizontally using **Redis Cluster** or **keyspace sharding** (e.g., `user:{shard}:{id}`).

---

## **Performance Considerations**
| **Metric**       | **Optimization**                                  | **Tool/Command**                     |
|------------------|--------------------------------------------------|--------------------------------------|
| **Latency**      | Use **Redis Cluster** for low-latency reads.      | `CLUSTER INFO`                       |
| **Throughput**   | Tune `maxmemory-policy` (e.g., `allkeys-lfu`).    | `config set maxmemory 1gb`           |
| **Memory**       | Compress large strings with `REDISLZFAST`.        | `config set hash-max-ziplist-value 64` |
| **Persistence**  | Use **RDB snapshots** for durability.            | `SAVE` or `BGSAVE`                   |

---
## **When Not to Use Redis Patterns**
- **Complex Queries:** Avoid for multi-table joins or aggregations (use a SQL DB).
- **High Write Throughput:** Redis is optimized for reads; use a distributed DB (e.g., Cassandra) for write-heavy apps.
- **Strong Consistency:** Eventual consistency is inherent in Redis; use **Sentinel** for failover.