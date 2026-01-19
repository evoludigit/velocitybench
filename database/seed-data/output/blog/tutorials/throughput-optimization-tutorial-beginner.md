```markdown
---
title: "Throughput Optimization: Building Scalable APIs That Serve Millions"
date: 2023-11-15
author: "Alex Carter"
description: "Learn how throughput optimization patterns can transform slow, chatty APIs into high-performance systems that handle thousands of requests per second."
tags: ["database", "api design", "performance", "backend engineering"]
---

# Throughput Optimization: Building Scalable APIs That Serve Millions

![High-performance API illustration](https://via.placeholder.com/800x400/2b3a50/FFFFFF?text=Scalable+API+Architecture)

Imagine your API as a busy New York City subway train. If it’s packed to capacity with slow-moving passengers (requests), it leads to bottlenecks, angry riders (users), and delays (latency). Throughput optimization is the secret sauce to increasing the number of requests your system can handle efficiently, keeping your users happy and your costs in check.

As backend developers, we often focus on writing clean, maintainable code—but **performance is the silent requirement that everyone demands**. At some point, your application will need to scale beyond its current limits, whether it’s a sudden surge in users or gradual growth. Throughput optimization helps you design systems that *handle more work with fewer resources*—whether it’s database queries, API calls, or computation.

In this guide, we’ll explore **throughput optimization patterns**, focusing on practical techniques to maximize the number of requests your backend can process efficiently. We’ll cover database optimizations, caching strategies, and architectural patterns—with real-world examples to help you apply these concepts immediately.

---

## The Problem: When Your API Grinds to a Halt

Before diving into solutions, let’s understand the common challenges that plague APIs without proper throughput optimization.

### **1. The "Chatty" Database Problem**
Most applications follow a straightforward pattern:
```
User → API → Database → API → User
```
This round-trip pattern creates unnecessary overhead. If your database is slow or underpowered, every additional request becomes a bottleneck.

**Example:**
A small e-commerce app starts with 1,000 daily users. It works fine. But as it grows to 100,000 users, the database struggles because:
- Each API call fetches the same product data multiple times.
- Transactions block each other, causing delays.
- Lack of indexing means scans instead of lookups.

### **2. The Caching Mismanagement**
Some teams try to solve performance issues by adding a caching layer (e.g., Redis), but misconfigured caching can do more harm than good:
- **Cache misses** (when data isn’t in cache) force expensive database lookups.
- **Over-caching** (storing too much) bloats memory and increases cache evictions.
- **Stale data** (cache not invalidated properly) leads to inconsistent responses.

### **3. Inefficient API Design**
Monolithic endpoints that do too much (e.g., `/api/products?with_reviews=true&with_stock=true&with_discounts=true`) force the database to join tables excessively or fetch unnecessary data. The result? Slow responses and wasted resources.

### **4. Unoptimized Concurrency**
If your API processes requests sequentially (e.g., one thread per request), it can’t handle concurrent users efficiently. Even with async code, improper concurrency management (e.g., thread starvation, deadlocks) can cripple performance.

### **5. External API Bottlenecks**
Many APIs rely on third-party services (payment gateways, map providers, etc.). Waiting for external responses delays your own API’s response time, reducing throughput.

---
## The Solution: Throughput Optimization Patterns

Throughput optimization is about **doing more with less**. The key is to reduce the **cost per request** (CPU, memory, I/O, network) so your system can handle more concurrent users. Here are the core strategies:

### **1. Denormalization & Read Optimization**
**Problem:** Joins and complex queries slow down reads.
**Solution:** Duplicate data where needed to avoid expensive joins.

**When to Use:**
- Analytics dashboards (OLAP workloads).
- Read-heavy applications (e.g., social media feeds).
- Cases where write consistency is less critical than read speed.

**Example: Reducing Joins in a Blog Platform**
Suppose we have a simple blog with `articles` and `comments`:

```sql
-- Original (joins on every read)
SELECT a.title, a.content, c.user, c.comment
FROM articles a
JOIN comments c ON a.id = c.article_id;
```

Instead, we **denormalize** by storing comments directly in the article table:

```sql
-- Denormalized schema (comments stored in articles)
CREATE TABLE articles (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255),
    content TEXT,
    comments JSONB[] DEFAULT '[]'  -- Store comments as JSON
);
```

**Pros:**
- Faster reads (no joins).
- Reduces database load.

**Cons:**
- Requires application logic to keep data in sync.
- Harder to maintain (eventual consistency).

**Practical Example:**
```python
# Simulated denormalization in Python (example using SQLAlchemy)
from sqlalchemy import create_engine, Column, Integer, String, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Article(Base):
    __tablename__ = "articles"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    content = Column(String)
    comments = Column(JSON, default=[])

    def add_comment(self, user: str, text: str):
        self.comments.append({"user": user, "text": text})
```

### **2. Batch Processing & Bulk Operations**
**Problem:** Single-row operations (e.g., `INSERT`, `UPDATE`) are slow for large datasets.
**Solution:** Process data in batches.

**When to Use:**
- Importing large datasets.
- Sending bulk notifications (e.g., emails).
- Aggregating metrics.

**Example: Batch Insert in PostgreSQL**
```sql
-- Bad: One insert per row
INSERT INTO users (name) VALUES ('Alice');
INSERT INTO users (name) VALUES ('Bob');
INSERT INTO users (name) VALUES ('Charlie');

-- Good: Batch insert
INSERT INTO users (name)
VALUES
    ('Alice'), ('Bob'), ('Charlie');
```

**Pros:**
- Reduces network overhead (fewer round-trips).
- Leverages database batching optimizations.

**Cons:**
- Risk of transaction timeouts on very large batches.
- Requires application-level logic to split batches.

**Practical Example:**
```python
# Batch insert in Python using psycopg2
import psycopg2

def batch_insert_users(users):
    conn = psycopg2.connect("dbname=test user=postgres")
    cursor = conn.cursor()

    # Prepare data in chunks
    batch_size = 1000
    for i in range(0, len(users), batch_size):
        batch = users[i:i + batch_size]
        placeholders = ",".join(["%s"] * len(batch))
        query = f"INSERT INTO users (name) VALUES ({placeholders})"

        cursor.executemany(query, batch)
        conn.commit()

    cursor.close()
    conn.close()
```

### **3. Caching Strategies (Beyond Basic Redis)**
Caching is one of the most effective ways to optimize throughput, but it’s often misapplied. Let’s explore advanced caching patterns.

#### **A. Multi-Level Caching**
Store data in multiple layers:
1. **In-memory cache (Redis/Memcached)** – Fast, but limited in size.
2. **Database (PostgreSQL)** – Persistent, but slower.
3. **Local cache (e.g., Python’s `functools.lru_cache`)** – Ultra-fast for hot data.

**Example:**
```python
from functools import lru_cache
import requests

@lru_cache(maxsize=1000)
def fetch_product_from_external_api(product_id):
    # Simulate slow external API call
    return requests.get(f"https://external-api.com/products/{product_id}").json()

# Now repeated calls return cached results
print(fetch_product_from_external_api(123))  # First call (slow)
print(fetch_product_from_external_api(123))  # Second call (fast, cached)
```

#### **B. Cache Invalidation Strategies**
- **Time-based (TTL):** Set a fixed expiration (e.g., 5 minutes).
- **Event-based:** Invalidate cache when the underlying data changes.
- **Write-through:** Update cache *and* database on every write.

**Example: Event-Based Invalidation with Redis**
```python
import redis
import json

r = redis.Redis(host='localhost', port=6379, db=0)

def get_user_profile(user_id):
    cache_key = f"user:{user_id}"
    cached_data = r.get(cache_key)
    if cached_data:
        return json.loads(cached_data)

    # Fetch from DB and cache
    user = fetch_from_database(user_id)
    r.setex(cache_key, 300, json.dumps(user))  # Cache for 5 minutes
    return user

def update_user_profile(user_id, data):
    fetched_user = fetch_from_database(user_id)
    fetched_user.update(data)

    # Update DB
    update_in_database(user_id, data)

    # Invalidate cache
    r.delete(f"user:{user_id}")
```

#### **C. Cache Sharding**
Distribute cache keys across multiple Redis nodes to avoid hotspots.

**Example:**
```python
def get_sharded_key(user_id, shard_count=3):
    return f"user:{user_id % shard_count}"
```

### **4. Connection Pooling**
**Problem:** Opening/closing database connections for every request is expensive.
**Solution:** Reuse connections via pooling.

**When to Use:**
- Any application that interacts with a database.
- Especially useful for high-throughput APIs.

**Example: Connection Pooling in PostgreSQL (using `psycopg2.pool`)**
```python
from psycopg2 import pool

# Initialize pool
connection_pool = pool.ThreadedConnectionPool(
    minconn=1,
    maxconn=20,
    host="localhost",
    database="test",
    user="postgres",
    password="password"
)

def get_user(user_id):
    conn = connection_pool.getconn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    connection_pool.putconn(conn)
    return user
```

**Pros:**
- Reduces connection overhead.
- Reuses established connections.

**Cons:**
- Requires proper cleanup to avoid leaks.

### **5. Asynchronous Processing & Offloading Work**
**Problem:** Blocking operations (e.g., file uploads, external API calls) slow down your API.
**Solution:** Offload work to background tasks.

**When to Use:**
- Long-running operations (e.g., PDF generation, image resizing).
- Notifications (emails, SMS).
- External API calls.

**Example: Using Celery for Background Tasks**
```python
# tasks.py
from celery import Celery

celery = Celery('tasks', broker='redis://localhost:6379/0')

@celery.task
def send_welcome_email(user_id):
    user = get_user_from_db(user_id)
    # Simulate slow email sending
    time.sleep(2)
    print(f"Sending welcome email to {user['email']}")

# API endpoint
@app.post("/register")
def register(user_data):
    user = create_user(user_data)
    send_welcome_email.delay(user.id)  # Offload to Celery
    return {"status": "success"}
```

**Pros:**
- Keeps API requests fast.
- Handles work asynchronously.

**Cons:**
- Adds complexity (message queues, workers).
- Requires monitoring for failed tasks.

### **6. Database Sharding & Read Replicas**
**Problem:** A single database can’t handle all the read/write load.
**Solution:** Split data across multiple instances.

**When to Use:**
- High read/write throughput (e.g., 10K+ RPS).
- Global applications (geographic distribution).

**Example: Read Replicas in PostgreSQL**
```bash
# Configure primary (write) and replica (read) in postgresql.conf
wal_level = replica
max_wal_senders = 5
```

**Pros:**
- Offloads read queries to replicas.
- Scales horizontally.

**Cons:**
- Complex setup (syncing data).
- Requires application-level routing.

### **7. Query Optimization**
**Problem:** Slow queries waste resources.
**Solution:** Optimize SQL queries with indexing, query tuning, and pagination.

**Example: Adding an Index**
```sql
-- Add an index on a frequently queried column
CREATE INDEX idx_user_email ON users(email);

-- Now queries like this run faster
SELECT * FROM users WHERE email = 'user@example.com';
```

**Example: Pagination Instead of Offsets**
```sql
-- Bad: Offsets (inefficient for large datasets)
SELECT * FROM products OFFSET 1000 LIMIT 10;

-- Good: Cursor-based pagination
SELECT * FROM products WHERE id > 1000 LIMIT 10;
```

**Pros:**
- Speeds up queries.
- Reduces database load.

**Cons:**
- Requires understanding of your query patterns.

---

## Implementation Guide: Step-by-Step Throughput Optimization

Let’s walk through a **practical example** of optimizing a simple product API using these patterns.

### **Scenario:**
A small online store with:
- A `/products` endpoint that returns product listings.
- A `/products/{id}` endpoint for details.
- A `/cart` endpoint to fetch cart items.

**Current Issues:**
- Slow page loads (1-2 seconds).
- Database is a bottleneck.
- No caching.

### **Step 1: Denormalize for Faster Reads**
We’ll optimize the `/products` endpoint by denormalizing `reviews` into the `products` table.

```sql
-- Original schema
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    price DECIMAL(10, 2)
);

CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    rating INTEGER,
    comment TEXT
);

-- After denormalization
ALTER TABLE products ADD COLUMN reviews JSONB DEFAULT '[]';
```

### **Step 2: Add Caching**
We’ll cache product listings and details in Redis.

```python
# Using Flask-Redis
from flask import Flask, jsonify
import redis

app = Flask(__name__)
r = redis.Redis(host='localhost', port=6379, db=0)

@app.route('/products')
def get_products():
    cache_key = "products:list"
    cached_data = r.get(cache_key)
    if cached_data:
        return jsonify(json.loads(cached_data))

    products = fetch_products_from_db()  # Fetch from DB
    r.setex(cache_key, 300, json.dumps(products))  # Cache for 5 mins
    return jsonify(products)
```

### **Step 3: Use Connection Pooling**
We’ll reuse database connections.

```python
# Using SQLAlchemy connection pooling
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine("postgresql://user:pass@localhost/db",
                       pool_size=10,
                       max_overflow=10)
Session = sessionmaker(bind=engine)
```

### **Step 4: Offload Heavy Work**
We’ll use Celery to send order confirmations asynchronously.

```python
# tasks.py
from celery import Celery

celery = Celery('orders', broker='redis://localhost:6379/0')

@celery.task
def send_order_confirmation(order_id):
    order = get_order_from_db(order_id)
    # Send email (simulated)
    print(f"Sending confirmation for order {order_id}")
```

```python
# In the API
@app.post('/checkout')
def checkout():
    order = process_payment()
    create_order(order)  # Save to DB
    send_order_confirmation.delay(order.id)  # Offload
    return {"status": "success"}
```

### **Step 5: Optimize Queries**
We’ll add indexes and use pagination.

```sql
-- Add indexes
CREATE INDEX idx_products_name ON products(name);
CREATE INDEX idx_products_price ON products(price);
```

```python
# Paginated endpoint
@app.get('/products')
def get_products(page=1, per_page=10):
    offset = (page - 1) * per_page
    products = db.session.query(products).offset(offset).limit(per_page).all()
    return jsonify([p.serialize() for p in products])
```

### **Step 6: Monitor and Iterate**
Use tools like:
- **PostgreSQL `EXPLAIN ANALYZE`** to profile queries.
- **Redis `INFO stats`** to check cache hit ratios.
- **APM tools (New Relic, Datadog)** to track latency.

---

## Common Mistakes to Avoid

1. **Over-Caching**
   - Caching too much data can lead to cache evictions and higher memory usage.
   - **Fix:** Cache only what’s frequently accessed and set appropriate TTLs.

2. **Ignoring Write Consistency**
   - Denormalization and caching can lead to stale data.
   - **Fix:** Use eventual consistency patterns (e.g., write-ahead logs) or event sourcing.

3. **Not Monitoring Cache Efficiency**
   - If your cache has a 1% hit ratio, it’s doing more harm than good.
   - **Fix:** Track cache metrics (hits/misses) and adjust.

4. **Blocking Background Tasks**
   - If your API waits for Celery tasks to complete, it’s still blocking users.
   - **Fix:** Always return a `202 Accepted` status and let the client poll for completion.

5. **Underestimating Database Limits**
   - PostgreSQL, for example, has a limit (~1,000 concurrent connections by default).
   - **Fix:** Use connection pooling and read replicas.

6. **Not Testing Under Load**
   - Optimizations only work if tested with real traffic.
   - **Fix:** Use tools like `locust` or `k6` to simulate load.

---

## Key Takeaways

Here’s a quick checklist for throughput optimization:

✅ **Optimize Queries:**
   - Add indexes (`EXPLAIN ANALYZE` your slow queries).
   - Use pagination (`LIMIT/OFFSET` is simple but inefficient; prefer cursors).
   - Avoid `SELECT *`; fetch only what you need.

✅ **Leverage Caching:**
   - Cache frequently accessed data (Redis/Memcached).
  