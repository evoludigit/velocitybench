```markdown
---
title: "Latency Anti-Patterns: How to Stop Your APIs from Crawling at a Snail’s Pace"
date: 2023-11-15
author: "Alex Merritt"
tags: ["database", "api design", "performance", "backend engineering"]
description: "Learn how latency anti-patterns silently kill your API response times, and how to fix them with concrete examples and tradeoff discussions."
---

# Latency Anti-Patterns: How to Stop Your APIs from Crawling at a Snail’s Pace

High-latency APIs are the silent killers of user experience. A 1-second delay can reduce customer satisfaction by **16%** and cost you **10%** in revenue, according to Google’s research. Yet, many engineering teams unwittingly introduce latency anti-patterns that inflate response times—often without even realizing it. These patterns manifest in inefficient queries, poor caching strategies, and overzealous data transfers. The good news? Most are fixable with targeted optimizations.

In this guide, we’ll dissect **common latency anti-patterns**, explain their root causes, and provide **practical fixes** with real-world examples. We’ll also discuss tradeoffs—because no solution is perfect, and understanding the ramifications is key to making informed decisions.

---

## The Problem: Why Latency Matters (And How It Slips In Unnoticed)

Latency isn’t just about slow APIs. It’s a **multi-faceted beast** that affects:

1. **User Experience**: A 2-second delay between a user’s click and the API response can feel like an eternity on mobile.
2. **Business Metrics**: High latency correlates with higher bounce rates, lower conversion rates, and higher support costs.
3. **Cost**: Cloud costs scale with compute time, so inefficient APIs waste money.
4. **Tech Debt**: Poorly optimized APIs accumulate over time, making future refactoring harder.

The problem? Many latency-related issues are **hard to debug** because they’re often hidden behind:
- **Cold starts** (e.g., Lambda, serverless functions).
- **Network overhead** (e.g., excessive redirects, slow DNS).
- **Database bottlenecks** (e.g., N+1 queries, missing indexes).
- **Over-fetching or under-fetching** (e.g., sending 10MB of JSON when 1KB suffices).

Worse, these issues don’t show up in unit tests or static code reviews. They’re **performance anti-patterns**, and they thrive in codebases without observability.

---

## The Solution: Identifying and Fixing Latency Anti-Patterns

To tackle latency, we need a **structured approach**:
1. **Measure**: Understand where latency is coming from (use APM tools like New Relic, Datadog, or OpenTelemetry).
2. **Profile**: Identify hotpaths (e.g., slow queries, blocking operations).
3. **Optimize**: Apply targeted fixes (e.g., caching, database tuning, async I/O).
4. **Monitor**: Ensure fixes don’t introduce regressions.

Let’s dive into **five common latency anti-patterns** and how to dismantle them.

---

## 1. **N+1 Query Problem: The Silent API Killer**

### The Problem
Imagine this scenario:
- Your API fetches a list of products.
- For each product, it makes an additional query to fetch details (e.g., reviews, inventory).
- If you have 100 products, you end up with **101 queries** (1 for the list + 100 for details).

This is the **N+1 query problem**, and it’s **everywhere**:
```go
// Example: Fetching users and their posts (N+1 anti-pattern)
func GetUserWithPosts(userID int) (*User, error) {
    // Query 1: Fetch user
    user, err := db.QueryUser(userID)
    if err != nil { ... }

    // Query 2-100: Fetch each post for the user (N queries)
    var posts []Post
    for _, postID := range user.PostIDs {
        post, err := db.QueryPost(postID)
        if err != nil { ... }
        posts = append(posts, post)
    }

    return &User{Posts: posts}, nil
}
```
This approach is **terrible for latency**:
- Each query introduces **network overhead** and **I/O wait time**.
- Databases struggle under high concurrency (locking, contention).
- Response times **scale linearly with data size**.

### The Solution: **Join or Cache**
Fixes include:
1. **Database Joins**: Fetch everything in a single query.
2. **Data Loading (ORM Patterns)**: Use eager loading or bulk fetching.
3. **Caching**: Cache the full payload (e.g., Redis, CDN).

#### Fix 1: SQL JOIN (Best for Read-Heavy APIs)
```sql
-- Single query instead of N+1
SELECT u.*, p.*
FROM users u
JOIN posts p ON u.id = p.user_id
WHERE u.id = ?
```
**Pros**: Fast, no application-level logic.
**Cons**: Can bloat response size if not filtered carefully.

#### Fix 2: ORM Eager Loading (Go Example with GORM)
```go
// Eager loading posts with GORM
var user User
db.Preload("Posts").First(&user, userID)
```
**Pros**: Cleaner code, reduces N+1.
**Cons**: Still hits the database (better than N+1, but not as fast as JOIN).

#### Fix 3: Caching (Redis Example)
```go
// Cache the full user + posts payload
userKey := fmt.Sprintf("user:%d", userID)
cachedData, err := redis.Get(userKey)
if cachedData != nil {
    return json.Unmarshal(cachedData, &user)
}
```
**Pros**: Eliminates database calls after the first request.
**Cons**: Cache invalidation complexity.

### Tradeoffs
| Approach       | Latency Impact | Complexity | Scalability |
|----------------|----------------|------------|-------------|
| JOIN           | ✅ Very Low    | ⚠️ Moderate | ✅ High     |
| ORM Eager Load | ⚠️ Low        | ⚠️ Low     | ⚠️ Medium   |
| Caching        | ⚠️ Low (after hit) | ❌ High | ❌ Medium   |

---

## 2. **Over-Fetching: Sending More Than Needed**

### The Problem
APIs often return **entire database rows** when clients only need a few fields. This wastes:
- **Bandwidth** (larger payloads).
- **CPU** (serialization/deserialization).
- **Memory** (unnecessary data processing).

Example:
```json
// API returns 10KB but client only needs 1KB
{
  "id": 1,
  "name": "Widget",
  "description": "...",
  "created_at": "2023-01-01",
  "updated_at": "2023-11-15",
  "tags": ["tag1", "tag2", ...],  // Unused by client
  "metadata": {...}               // Rarely accessed
}
```

### The Solution: **Selective Field Projection**
#### Fix 1: SQL `SELECT` Only Needed Columns
```sql
-- Only fetch id, name, and created_at
SELECT id, name, created_at FROM products WHERE id = ?
```
**Pros**: Minimal data transfer.
**Cons**: Requires client to specify fields (API versioning may be needed).

#### Fix 2: API Response Shaping (JSON Field Selection)
```go
// Go: Only include fields the client requested
type ProductResponse struct {
    ID        int    `json:"id"`
    Name      string `json:"name"`
    CreatedAt time.Time `json:"created_at,omitempty"` // Optional
}

// Middleware to filter response
func ShapeResponse(w http.ResponseWriter, r *http.Request) {
    desiredFields := r.URL.Query().Get("fields") // "id,name"
    // Only marshal fields in desiredFields
}
```
**Pros**: Fine-grained control.
**Cons**: Adds complexity to the API layer.

#### Fix 3: GraphQL (If You’re Using It)
GraphQL **natively** avoids over-fetching:
```graphql
query {
  product(id: 1) {
    id
    name
    createdAt
  }
}
```
**Pros**: Client specifies exactly what they need.
**Cons**: Overhead of GraphQL resolver system.

### Tradeoffs
| Approach       | Latency Impact | Flexibility | Complexity |
|----------------|----------------|-------------|------------|
| SQL `SELECT`   | ✅ Very Low    | ❌ Low      | ⚠️ Low     |
| Response Shaping | ⚠️ Low        | ✅ High     | ❌ High    |
| GraphQL        | ⚠️ Moderate   | ✅ Very High| ❌ High    |

---

## 3. **Blocking I/O: When Your API Stalls**

### The Problem
Blocking I/O (e.g., synchronous database calls, file I/O, HTTP requests) **freezes the entire request**. Example:
```go
// Blocking database call in a web handler
func GetProduct(w http.ResponseWriter, r *http.Request) {
    product, err := db.QueryProduct(r.URL.Query().Get("id")) // BLOCKS
    if err != nil { ... }
    json.NewEncoder(w).Encode(product) // Won't happen until DB returns
}
```
- If the DB is slow, the **entire request hangs**.
- Worse, if multiple requests hit the same DB, you get **thundering herd problems**.

### The Solution: **Async I/O or Worker Pools**
#### Fix 1: Asynchronous Database Access (Context + Goroutines)
```go
func GetProduct(w http.ResponseWriter, r *http.Request) {
    ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
    defer cancel()

    // Spawn async DB call
    go func() {
        product, err := db.QueryProduct(ctx, r.URL.Query().Get("id"))
        if err != nil { ... }
        json.NewEncoder(w).Encode(product)
    }()

    // Return early (or handle asynchronously)
    w.WriteHeader(http.StatusOK)
}
```
**Pros**: Non-blocking.
**Cons**: Harder to debug (goroutines + context).

#### Fix 2: Worker Pool (For Batch Operations)
```go
// Pool of goroutines to handle DB work
var workerPool = sync.Pool{
    New: func() interface{} {
        return workers.New()
    },
}

// Usage in handler
func ProcessBatch(w http.ResponseWriter, r *http.Request) {
    var wg sync.WaitGroup
    for _, item := range items {
        wg.Add(1)
        worker := workerPool.Get().(*workers.Worker)
        go func(i int) {
            defer wg.Done()
            defer workerPool.Put(worker)
            worker.Process(i)
        }(i)
    }
    wg.Wait()
    w.WriteHeader(http.StatusOK)
}
```
**Pros**: Scales horizontally.
**Cons**: More complex error handling.

#### Fix 3: Use a Task Queue (Celery, SQS)
For **offline processing**, use a queue:
```go
// Push work to a queue (e.g., AWS SQS)
func GenerateReport(w http.ResponseWriter, r *http.Request) {
    sqs.Publish("report-generation", map[string]string{
        "user_id": r.URL.Query().Get("user_id"),
    })
    w.WriteHeader(http.StatusAccepted)
}
```
**Pros**: Decouples API from slow work.
**Cons**: Higher latency for immediate responses.

### Tradeoffs
| Approach          | Latency Impact | Complexity | Best For               |
|-------------------|----------------|------------|------------------------|
| Async Goroutines  | ⚠️ Low         | ❌ High    | Simple async needs     |
| Worker Pool       | ⚠️ Low         | ❌ High    | Batch processing       |
| Task Queue        | ❌ High        | ❌ High    | Offline/long-running   |

---

## 4. **Missing Indexes: The Database’s Silent Pain**

### The Problem
Without proper indexes, databases **scan entire tables** (full table scans). Example:
```sql
-- No index on "status" column
SELECT * FROM orders WHERE status = 'shipped';
```
- If the `orders` table has **1M rows**, this is **slow**.
- Worse, it **locks rows**, blocking other queries.

### The Solution: **Index Strategically**
#### Fix 1: Add Indexes for Filtered Columns
```sql
-- Add index for frequent filter
CREATE INDEX idx_orders_status ON orders(status);
```
**Pros**: Speeds up queries.
**Cons**: Indexes slow down `INSERT`/`UPDATE`.

#### Fix 2: Composite Indexes for Multiple Filters
```sql
-- Optimize for "status AND created_at" queries
CREATE INDEX idx_orders_status_date ON orders(status, created_at);
```
**Pros**: Covers multiple query patterns.
**Cons**: Index size grows.

#### Fix 3: Partial Indexes (PostgreSQL)
```sql
-- Only index active orders
CREATE INDEX idx_orders_active ON orders(status) WHERE status = 'active';
```
**Pros**: Reduces index size.
**Cons**: Not all databases support it.

### Tradeoffs
| Approach               | Query Speed | Write Speed | Storage Overhead |
|------------------------|-------------|-------------|------------------|
| Single Index           | ✅ Fast      | ⚠️ Slower   | ⚠️ Medium        |
| Composite Index        | ✅ Very Fast | ❌ Slow     | ❌ High           |
| Partial Index          | ✅ Fast      | ⚠️ Similar  | ✅ Low            |

---

## 5. **No Caching Layer: Reinventing the Wheel Every Time**

### The Problem
Without caching:
- **Database is hit for every request**.
- **Compute resources waste time on redundant work**.
- **Memcached/Redis/CDN** could solve 80% of latency issues.

Example:
```go
// No caching: Every request hits the DB
func GetUserConfig(userID int) (*Config, error) {
    return db.QueryUserConfig(userID) // Slow every time
}
```

### The Solution: **Layered Caching Strategy**
#### Fix 1: Redis for Hot Data
```go
// Cache the result for 5 minutes
func GetUserConfig(userID int) (*Config, error) {
    cacheKey := fmt.Sprintf("user_config:%d", userID)
    cached, err := redis.Get(cacheKey)
    if cached != nil {
        var config Config
        json.Unmarshal(cached, &config)
        return &config, nil
    }

    config, err := db.QueryUserConfig(userID)
    if err != nil { ... }

    // Set cache with TTL
    redis.SetEX(cacheKey, 5*time.Minute, config.ToJSON())
    return config, nil
}
```

#### Fix 2: CDN for Static Assets
```http
// Serve JSON APIs via CDN (e.g., Cloudflare Workers)
GET /api/products?v=1
Cache-Control: public, max-age=300
```

#### Fix 3: Database-Level Caching (PostgreSQL `BRIN` Indexes)
```sql
-- For time-series data, use BRIN for fast range scans
CREATE INDEX idx_orders_time ON orders USING BRIN(created_at);
```

### Tradeoffs
| Approach       | Latency Impact | Consistency | Complexity |
|----------------|----------------|-------------|------------|
| Redis Cache    | ⚠️ Very Low    | ⚠️ Eventual | ⚠️ Medium  |
| CDN            | ✅ Very Low     | ❌ Strict    | ❌ High     |
| DB Caching     | ⚠️ Low         | ✅ Strong    | ⚠️ Low     |

---

## Implementation Guide: How to Fix Latency in Your Codebase

1. **Profile First**
   - Use tools like **`pprof` (Go), `EXPLAIN ANALYZE` (SQL), or APM (Datadog)** to find bottlenecks.
   - Example:
     ```bash
     # Capture latency profile in Go
     go tool pprof http://localhost:8080/debug/pprof/profile
     ```

2. **Fix the Worst Offenders**
   - Start with **N+1 queries** (easiest win).
   - Then tackle **over-fetching** and **blocking I/O**.

3. **Add Instrumentation**
   - Track response times per endpoint:
     ```go
     start := time.Now()
     deferred func() {
         log.Printf("Endpoint %s took %v", r.URL.Path, time.Since(start))
     }()
     ```

4. **Test Locally**
   - Use **mock databases** (e.g., Testcontainers) to simulate slow queries:
     ```go
     func TestSlowDBQuery(t *testing.T) {
         db := sqlmock.New()
         db.ExpectQuery("SELECT ...").WillReturnError(square.ErrSlowDB)
         // ...
     }
     ```

5. **Monitor Post-Deployment**
   - Set up **SLOs (Service Level Objectives)** for latency (e.g., "99% of API calls < 500ms").
   - Use **alerting** (e.g., Prometheus + Alertmanager).

---

## Common Mistakes to Avoid

1. **Blindly Optimizing**
   - Don’t prematurely optimize. Profile first!
   - Example: Adding indexes to every column **hurts writes**.

2. **Ignoring Cold Starts**
   - Serverless functions (Lambda, Cloud Functions) have **cold start latency**.
   - Mitigation: Use **provisioned concurrency** or **warm-up calls**.

3. **Over-Caching**
   - Stale data can hurt users. Use **cache invalidation** (e.g., event-driven).
   - Example:
     ```go
     // Invalidate cache when a config changes
     pubsub.Subscribe("config-updated").Handle(func(msg string) {
         redis.Del("all_user_configs")
     })
     ```

4. **Forgetting Edge Cases**
   - What if the cache fails? What if the DB is down?
   - Implement **fallbacks** (e.g., return stale data with `Cache-Control`).

5. **Not Measuring**
   - Without metrics