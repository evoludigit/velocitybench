```markdown
# Batch Processing vs. Individual Requests: How to Avoid API Performance Landmines

*"Every request is a trip to the store. If you’re making one per item, you’re paying for gas for your eggs."*

---

## Introduction: The API Performance Paradox

You’ve built a sleek API that handles individual requests with elegance—each insert, update, or delete feels fast and responsive. But when load increases, your system stutters. The problem? **You’re paying for every operation individually.**

Imagine a user uploads 10,000 records. If you process each one separately:
- **10,000 network round-trips** (latency adds up).
- **10,000 transactions** (database locks, connection overhead).
- **10,000 context switches** (your server juggles 10,000 tasks).

This isn’t just inefficient—it’s **technically naive**.

**Batch processing** changes the game. By combining operations into a single request, you slash overhead by 90%. A batch of 10,000 inserts might take **1 second** instead of 30. The key? Understanding where to batch—and where not to.

In this guide, we’ll explore:
- Why individual requests are a performance anti-pattern.
- How batching works at the database and API levels.
- Practical code examples (Python, JavaScript, SQL) for bulk operations.
- Common pitfalls and tradeoffs.

Let’s start by highlighting the problem.

---

## The Problem: The Hidden Cost of Individual Requests

*"Performance is not just about speed; it’s about efficiency. And efficiency is about avoiding waste."*

Your API might handle 100 requests per second *seemingly* fine. But dig deeper, and you’ll find:

### 1. **Network Latency Addition**
Every HTTP request carries overhead:
- **TCP handshake** (~100ms per connection).
- **Serialization/deserialization** (JSON parsing, etc.).
- **DNS resolution** (for external services).

For 10,000 records, that’s **1,000 seconds of network time**—regardless of how fast your backend is.

**Example:**
```plaintext
# 10,000 individual requests (100ms each) = 1,000 seconds (~16 minutes)
# 1 batch of 10,000 requests = 1 second (if optimized)
```

### 2. **Database Transaction Overhead**
Databases aren’t designed for fine-grained operations. Each `INSERT` or `UPDATE` incurs:
- **Transaction logging** (WAL in PostgreSQL, redo logs in MySQL).
- **Lock contention** (if rows overlap).
- **Connection pool exhaustion** (each request may need a new connection).

**SQL Example: Slow Individual Inserts**
```sql
-- Bad: 10,000 individual inserts
INSERT INTO users (name, email) VALUES ('Alice', 'alice@example.com');
INSERT INTO users (name, email) VALUES ('Bob', 'bob@example.com');
-- ... 9,998 more times
```
This is **terrible** for performance.

### 3. **N+1 Queries (The Silent Killer)**
Even if you *think* you’re batching, **N+1 query patterns** sneak in:
- **API Side:** Fetching 10 items, then querying a database 10 times (e.g., for relations).
- **Database Side:** Joining tables inelegantly (e.g., fetching users, then fetching their orders in a loop).

**Example (Bad API Design):**
```javascript
// Bad: 10 individual DB calls for 10 users
const users = await User.findMany();
const userOrders = await Promise.all(
  users.map(user => Order.findByUser(user.id))
);
```

### 4. **Connection Pool Exhaustion**
Databases like PostgreSQL have connection pools (e.g., `max_connections=100`). If your app opens 100 concurrent connections for `INSERT` statements, you’ll hit:
```plaintext
ERROR:  connection to server at "localhost" (::1), port 5432 failed
```
**Solution?** Batch, so you reuse a single connection.

---

## The Solution: Batch Processing (Like Grocery Shopping)

*"Batching is the difference between paying for every item individually and shopping with a list."*

Imagine you need to buy groceries:
- **Individual Requests:** Drive to the store 20 times (1 trip per item).
- **Batched:** Make a list, drive once, and buy everything.

**The same applies to APIs and databases.**
Batching combines multiple operations into a single request, amortizing fixed costs (network, transactions, locks) across many rows.

---

### Three Levels of Batching

| Level          | What It Does                          | Example                          |
|----------------|---------------------------------------|----------------------------------|
| **Database**   | Execute multiple SQL statements at once | `INSERT ... VALUES (a,b), (c,d)`   |
| **API**        | Accept an array in a single endpoint  | `POST /users?batch=[{...}, {...}]` |
| **Application**| Process chunks (e.g., 1,000 items at a time) | Loop in 1,000-item batches |

---

## Practical Examples: Batching in Code

Let’s explore code examples in **Python (FastAPI)** and **JavaScript (Express)**.

---

### 1. **Bulk Database Inserts (SQL)**
Most databases support bulk operations natively.

#### PostgreSQL (Bulk Insert)
```sql
-- Single INSERT (slow)
INSERT INTO users (name, email) VALUES ('Alice', 'alice@example.com');

-- Bulk INSERT (fast)
INSERT INTO users (name, email)
VALUES
  ('Alice', 'alice@example.com'),
  ('Bob', 'bob@example.com'),
  ('Charlie', 'charlie@example.com');
```

#### PostgreSQL (COPY Command - Fastest)
```sql
-- Even faster: Use COPY (for large datasets)
\copy users FROM '/path/to/data.csv' DELIMITER ','
```

#### Python (Bulk Insert with SQLAlchemy)
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Connect to DB
engine = create_engine("postgresql://user:pass@localhost/db")
Session = sessionmaker(bind=engine)
session = Session()

# Bulk insert (batch of 1000 users)
users_to_insert = [
    {"name": "Alice", "email": "alice@example.com"},
    {"name": "Bob", "email": "bob@example.com"},
    # ... 998 more
]

# Fast path: Execute a single INSERT with VALUES
session.execute(
    "INSERT INTO users (name, email) VALUES (:name, :email)",
    users_to_insert
)
session.commit()
```

#### JavaScript (Bulk Insert with Prisma)
```javascript
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

const users = [
  { name: 'Alice', email: 'alice@example.com' },
  { name: 'Bob', email: 'bob@example.com' },
  // ... 998 more
];

// Bulk insert with Prisma (single transaction)
await prisma.$transaction([
  prisma.user.createMany({ data: users }),
]);
```

---

### 2. **Batch API Endpoints**
Expose endpoints that accept arrays.

#### FastAPI (Python) Example
```python
from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.post("/users/batch-create")
async def batch_create_users(users: list[dict]):
    # Validate input
    if len(users) > 1000:
        raise HTTPException(status_code=400, detail="Too many users")

    # Process in bulk (e.g., using SQLAlchemy bulk_insert)
    # ...
    return {"status": "success"}
```

#### Express (JavaScript) Example
```javascript
const express = require('express');
const app = express();

app.use(express.json());

app.post('/users/batch', async (req, res) => {
  const { users } = req.body; // Array of user data

  if (users.length > 1000) {
    return res.status(400).json({ error: "Too many users" });
  }

  // Process in bulk (e.g., with Prisma)
  await prisma.user.createMany({ data: users });
  res.json({ status: "success" });
});
```

---

### 3. **Chunking Large Batches**
Never process **all** data in one go. Chunk batches for:
- **Database limits** (e.g., `createMany` in Prisma has max 100k records).
- **Memory limits** (don’t load 1M records into RAM).
- **Recovery** (if a chunk fails, only roll back that chunk).

#### Python (Chunked Processing)
```python
def process_in_chunks(data, chunk_size=1000):
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i + chunk_size]
        # Process chunk (e.g., insert into DB)
        session.execute(
            "INSERT INTO users (...) VALUES (...)",
            chunk
        )
        session.commit()
```

#### JavaScript (Chunked Processing)
```javascript
async function processInChunks(data, chunkSize = 1000) {
  for (let i = 0; i < data.length; i += chunkSize) {
    const chunk = data.slice(i, i + chunkSize);
    await prisma.user.createMany({ data: chunk });
  }
}
```

---

## Implementation Guide: When and How to Batch

### **When to Batch**
| Scenario                          | Solution                          | Example                          |
|-----------------------------------|-----------------------------------|----------------------------------|
| Uploading 10,000+ records          | Batch API endpoint                | `POST /users/batch`               |
| Processing user orders             | Bulk database update              | `UPDATE orders SET status='paid'` |
| Fetching related data (e.g., posts + comments) | **Denormalize or deduplicate** | Fetch posts, then fetch comments in bulk |

### **When NOT to Batch**
| Scenario                          | Why Not Batch                     | Example                          |
|-----------------------------------|-----------------------------------|----------------------------------|
| Real-time data (e.g., live chat) | High latency in batch processing | Use individual inserts           |
| Idempotent operations (e.g., single record updates) | Overkill for single records | Stick to single requests        |
| Low-volume data (e.g., <100 records/day) | No performance gain           | Individual requests are fine     |

---

## Common Mistakes to Avoid

### 1. **Over-Batching**
- **Problem:** Batch sizes too large → memory exhaustion.
- **Fix:** Use chunking (e.g., 1,000–5,000 records per batch).

### 2. **No Error Handling in Batches**
- **Problem:** A single batch failure can lose all data.
- **Fix:** Process chunk-by-chunk with transactions.

```python
# Bad: All-or-nothing
session.execute("INSERT INTO users (...) VALUES (...)", big_batch)

# Good: Chunked with rollback
for chunk in chunks_of_users:
    session.execute("INSERT ...", chunk)
    session.commit()
```

### 3. **Ignoring Database Limits**
- **Problem:** Some databases (e.g., MySQL) have `INSERT` limits.
- **Fix:** Check docs (e.g., MySQL’s `INSERT ... VALUES (a,b), (c,d)` has a 64k limit).

### 4. **Not Validating Input**
- **Problem:** Malformed batch data crashes your server.
- **Fix:** Validate before processing.

```javascript
if (!Array.isArray(users) || users.some(u => !u.name)) {
  return res.status(400).json({ error: "Invalid input" });
}
```

### 5. **Forgetting to Close Connections**
- **Problem:** Leaky connections exhaust pools.
- **Fix:** Use connection pooling (e.g., `pg.Pool` in Node.js).

```javascript
// Node.js with pg
const { Pool } = require('pg');
const pool = new Pool();

pool.connect().then(client => {
  // Process batch
  client.release(); // Always release!
});
```

---

## Key Takeaways

✅ **Batch processing reduces overhead** by combining multiple operations into one request.
✅ **Database bulk inserts are faster** than individual statements (test with `EXPLAIN ANALYZE`).
✅ **API batch endpoints** should accept arrays (e.g., `POST /users/batch`).
✅ **Chunk large batches** (e.g., 1,000–5,000 records at a time) for memory and recovery.
✅ **Avoid over-batching**—balance performance with system constraints.
✅ **Always validate input** before processing batches.
✅ **Use transactions** to roll back failed chunks.

---

## Conclusion: Batch Like a Pro

Batching isn’t a silver bullet—it’s a **tool for high-volume, low-latency systems**. Use it wisely:
- **For bulk data** (uploads, imports, batch updates).
- **For API efficiency** (reduce requests from clients).
- **For database performance** (fewer transactions, less lock contention).

But don’t batch **everything**. Individual requests have their place (real-time systems, low-volume data).

**Final Tip:** Profile your system. Use tools like:
- **PostgreSQL:** `EXPLAIN ANALYZE` to compare bulk vs. individual inserts.
- **API:** Record latency per endpoint (e.g., with New Relic or Prometheus).

Now go batch like a grocery shopper—**smart, efficient, and without wasting gas**.

---
**Further Reading:**
- [PostgreSQL Bulk Insert Guide](https://www.postgresql.org/docs/current/sql-insert.html)
- [Prisma Batch Operations](https://www.prisma.io/docs/guides/performance-and-optimization/batch-operations)
- [SQLAlchemy Bulk Operations](https://docs.sqlalchemy.org/en/14/orm/extensions/bulk.html)
```