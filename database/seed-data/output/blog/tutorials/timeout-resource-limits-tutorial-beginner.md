```markdown
# **Database Query Timeouts and Resource Limits: Protecting Your APIs from Slow Queries**

*How to prevent runaway queries from crashing your system*

---
*By [Your Name], Senior Backend Engineer*

---

## **Introduction**

Have you ever hit a page load button in your web app and watched the spinner spin for **minutes**—only to see a frustrating error like `Query execution timed out`? Or worse, had your entire application slow to a crawl because some hidden database query was chewing through CPU and memory?

This isn’t just a rare edge case—it’s a **real and growing problem** in backend development. Databases like PostgreSQL, MySQL, and MongoDB can’t run indefinitely without limits. Without proper safeguards, a single poorly written query can:

- **Crash your application** by consuming all available memory.
- **Block new requests** as the database struggles to recover.
- **Waste server resources**, leading to higher costs (especially in cloud environments).
- **Cause cascading failures** if your app depends on slow database responses.

In this post, we’ll explore the **Query Timeout and Resource Limits** pattern—a critical practice for writing resilient APIs. You’ll learn:

✅ How to set timeouts for database queries
✅ How to limit resource consumption (CPU, memory)
✅ Practical examples in JavaScript (Node.js), Python (FastAPI), and SQL
✅ Common pitfalls and how to avoid them

By the end, you’ll understand why every query should have boundaries—and how to enforce them effectively.

---

## **The Problem: When Queries Go Rogue**

Imagine this scenario:

1. A user searches for products in an e-commerce app, triggering a complex `JOIN`-heavy query.
2. The query includes an unnecessary `WHERE` clause like `WHERE status = 'active' OR status = 'pending'` (redundant, but let’s say it’s user input).
3. The database scans **millions of rows**, then sorts the results by a slow-computing column.
4. The query runs for **20 seconds**—longer than your app’s default timeout (10 seconds).
5. The connection hangs, and the app either:
   - Returns a timeout error to the user (poor UX).
   - Crashes due to too many stalled connections.
   - Blocks other queries from running.

This isn’t hypothetical. It happens in production. The fix isn’t just "optimize the query"—it’s **enforcing limits** so the system can’t break.

### **Why Do Queries Get Stuck?**
Common culprits include:

| Cause                          | Example Scenario                                                                 |
|--------------------------------|---------------------------------------------------------------------------------|
| **Inefficient `JOIN`s**        | Cartesians joins (`SELECT * FROM users, orders` without a proper `ON` clause).   |
| **Missing indexes**            | Querying a `WHERE` clause on an unindexed column forces a full table scan.       |
| **Recursive queries**          | Queries like `WITH RECURSIVE` that run until a limit is hit (but never is).        |
| **Slow computations**          | Functions like `UPPER()`, `CONCAT()`, or complex aggregations in `SELECT`.       |
| **No limits on batch operations** | `BULK INSERT` or `UPDATE` statements that run for hours.                      |

Even well-intentioned devs can write queries that "just work in dev" but **explode in production** when data volumes grow.

---

## **The Solution: Enforce Timeouts and Resource Limits**

The solution isn’t to ban slow queries—it’s to **control them**. You need three layers of defense:

1. **Database-level timeouts** – The database itself kills queries after a threshold.
2. **Application-level timeouts** – Your code cuts off the query before it exhausts resources.
3. **Resource limits** – Restrict CPU, memory, or disk usage per query.

---

### **1. Database Timeout Settings**
Most databases let you set a **maximum execution time** for queries. This is your first line of defense.

#### **PostgreSQL: `server_side_timeout`**
PostgreSQL allows you to set a timeout for long-running transactions:

```sql
-- Set at the database level (requires superuser)
ALTER SYSTEM SET server_side_timeout = '10s';
SELECT pg_reload_conf();  -- Apply changes
```

This **terminates the entire transaction** if it exceeds 10 seconds. It’s stricter than application-level timeouts (which only kill the connection).

#### **MySQL: `wait_timeout` and `interactive_timeout`**
MySQL has separate settings for client connections:

```sql
-- Set in my.cnf or via mysql> command
SET GLOBAL wait_timeout = 30;
SET GLOBAL interactive_timeout = 30;
```
- `wait_timeout`: Time before the connection is closed (in seconds).
- `interactive_timeout`: Time before long-running queries are killed (useful for CLI tools).

#### **MongoDB: `maxTimeMS`**
MongoDB lets you enforce timeouts per query:

```javascript
// In Node.js with MongoDB driver
db.collection('users')
  .find({ status: 'active' })
  .maxTimeMS(5000);  // Abort if query takes >5sec
```

---

### **2. Application-Level Timeouts**
Even if the database allows slow queries, your app should **enforce stricter limits**. Here’s how to do it in popular languages:

#### **Node.js (with `pg` and `mysql2`)**
```javascript
const { Pool } = require('pg');

const pool = new Pool({
  connectionTimeoutMillis: 5000,  // Socket timeout
  idleTimeoutMillis: 30000,
  max: 20,
});

// Set a query timeout (Node.js `Client` method)
const client = await pool.connect();
await client.query('SELECT * FROM slow_table', (err, res) => {
  if (err && err.code === '40P01') {  // Query was killed
    console.warn('Query timed out at the database level');
  }
});
```

For **async/await** (PostgreSQL):
```javascript
async function safeQuery() {
  const client = await pool.connect();
  try {
    const res = await client.query('SELECT * FROM big_table', {
      timeout: 5000,  // Node.js timeout in ms
    });
    return res;
  } finally {
    client.release();
  }
}
```

#### **Python (with `psycopg2` and `pymysql`)**
```python
import psycopg2
from psycopg2 import OperationalError

def query_with_timeout():
    conn = None
    try:
        conn = psycopg2.connect("dbname=test user=postgres")
        with conn.cursor() as cur:
            cur.set_single_interpolation(True)
            cur.execute("SELECT * FROM huge_table", timeout=5)  # 5-second timeout
            return cur.fetchall()
    except OperationalError as e:
        if "timeout" in str(e):
            print("Query timed out!")
        raise
    finally:
        if conn:
            conn.close()
```

#### **Go (with `database/sql`)**
```go
import (
	"database/sql"
	"time"
)

func safeQuery(db *sql.DB) error {
	rows, err := db.QueryContext(
		context.WithTimeout(context.Background(), 3*time.Second),
		"SELECT * FROM very_slow_query",
	)
	// Handle rows...
	return err
}
```

---

### **3. Resource Limits**
Timeouts alone aren’t enough. You should also **limit CPU and memory** to prevent runaway queries from starving other processes.

#### **PostgreSQL: `statement_timeout`**
```sql
ALTER ROLE app_user SET statement_timeout = '5000ms';
```
This kills **any statement** (not just transactions) exceeding 5 seconds.

#### **MySQL: Resource Group Limits**
MySQL’s **Resource Groups** let you restrict CPU/memory per connection:

```sql
CREATE RESOURCE GROUP my_group
    MEMORY_LIMIT 100M
    CPU_LIMIT 50;

GRANT my_group TO 'app_user'@'%';
```

#### **MongoDB: `maxTimeMS` + `allowDiskUse`**
If a query uses too much memory, MongoDB can spill to disk (slowing it down). Disable this for critical queries:

```javascript
db.users.find(
  { name: { $regex: ".*very.*long.*regex.*" } },
  { maxTimeMS: 2000, allowDiskUse: false }  // Reject if it tries disk usage
);
```

---

## **Implementation Guide: How to Apply This in Your App**

### **Step 1: Set Database Default Timeouts**
Configure your database to kill queries automatically:

| Database  | Setting                     | Recommended Value |
|-----------|----------------------------|-------------------|
| PostgreSQL| `statement_timeout`        | 5s – 10s          |
| MySQL     | `interactive_timeout`      | 5s                |
| MongoDB   | `maxTimeMS` (per query)    | 5s – 10s          |

### **Step 2: Enforce Timeouts in Your Code**
Wrap database calls with timeouts:

```javascript
// Node.js example with retry logic
async function executeWithTimeout(query, timeout = 5000) {
  const client = await pool.connect();
  try {
    const res = await client.query(query, {
      timeout: timeout,
    });
    return res;
  } catch (err) {
    if (err.code === '40P01') {
      throw new Error(`Query timed out after ${timeout}ms`);
    }
    throw err;
  } finally {
    client.release();
  }
}
```

### **Step 3: Log and Monitor Slow Queries**
Use a **logging middleware** to track queries near the timeout:

```javascript
const logger = require('pino')();

app.use((req, res, next) => {
  const start = Date.now();
  req.on('end', () => {
    const duration = Date.now() - start;
    if (duration > 500) {  // Log slow requests
      logger.warn(`Slow request: ${duration}ms`);
    }
  });
  next();
});
```

### **Step 4: Use Query Analyzers**
Tools like:
- **PostgreSQL’s `EXPLAIN ANALYZE`** – Helps identify slow queries.
- **MySQL’s `slow_query_log`** – Logs queries taking longer than a threshold.
- **MongoDB’s `profile` level** – Logs slow operations.

Example (PostgreSQL):
```sql
EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = 123;
```

---

## **Common Mistakes to Avoid**

### **❌ Mistake 1: Trusting the Database Timeout Alone**
- **Problem**: If your app isn’t monitoring timeouts, users see slow responses instead of errors.
- **Fix**: Enforce timeouts in **both** the database **and** your application.

### **❌ Mistake 2: Using `SELECT *` and Processing Massive Data**
- **Problem**: Fetching 100K rows into memory is a recipe for crashes.
- **Fix**:
  ```sql
  -- Bad: Fetches everything
  SELECT * FROM products WHERE category = 'books';

  -- Good: Limits rows + fetches only needed columns
  SELECT id, name, price FROM products WHERE category = 'books' LIMIT 100;
  ```

### **❌ Mistake 3: Ignoring `EXPLAIN` Plans**
- **Problem**: Writing queries without checking their execution plan leads to hidden inefficiencies.
- **Fix**: Always run:
  ```sql
  EXPLAIN ANALYZE SELECT ...;
  ```

### **❌ Mistake 4: Disabling Timeouts in Production**
- **Problem**: "It works in dev, so we’ll disable timeouts for reliability."
- **Fix**: **Never disable timeouts**. Instead, optimize queries or rewrite them.

### **❌ Mistake 5: Not Testing with Real Data**
- **Problem**: A query that runs in 1s on a small table may take **minutes** on production data.
- **Fix**: Test with **production-like datasets** before deploying.

---

## **Key Takeaways**

Here’s what you should remember:

✔ **Timeouts save the day** – Timeouts prevent runaway queries from crashing your app.
✔ **Database + application timeouts** – Both layers work together for defense in depth.
✔ **Resource limits matter** – Don’t just set timeouts; restrict CPU/memory too.
✔ **Use `EXPLAIN`** – Always analyze slow queries before optimizing.
✔ **Log and monitor** – Know which queries are slow before users complain.
✔ **Test with real data** – Dev environments often don’t expose production issues.
✔ **Avoid `SELECT *`** – Fetch only what you need, and limit rows.

---

## **Conclusion: Build Resilient APIs**

Long-running queries are **not a bug**—they’re a **design flaw**. The Query Timeout and Resource Limits pattern ensures your API stays performant, even when queries go wrong.

### **Next Steps**
1. **Audit your queries**: Use `EXPLAIN` to find slow ones.
2. **Set timeouts**: Configure database and app-level limits.
3. **Monitor**: Log slow queries and fix them proactively.
4. **Educate your team**: Slow queries often come from well-intentioned but unoptimized code.

By enforcing these limits, you’ll make your system **faster, more reliable, and easier to debug**. And when a query *does* go rogue? Your users (and your server) will thank you.

---
**Further Reading**
- [PostgreSQL Timeouts & Limits](https://www.postgresql.org/docs/current/runtime-config-statement.html)
- [MySQL Query Timeouts](https://dev.mysql.com/doc/refman/8.0/en/server-system-variables.html#sysvar_interactive_timeout)
- [MongoDB Query Timeout Docs](https://www.mongodb.com/docs/manual/reference/method/db.collection.find/#mongodb-method--db.collection.find)

**Got questions?** Drop them in the comments—let’s discuss how you handle timeouts in your stack!
```

This post is **practical, code-heavy, and honest** about tradeoffs while keeping it beginner-friendly.