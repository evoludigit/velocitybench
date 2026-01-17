```markdown
# "If You're Not Documenting Your Scaling Conventions, You're Writing in Code" — The Scaling Conventions Pattern

## Introduction

Imagine you’re debugging a production outage where requests are timing out and errors are piling up. The logs are a mess of undefined behavior: some queries are fetching 10x more data than expected, others are stuck in long-running transactions, and some API endpoints are serving stale data. Your team is frantic—_"Why is this happening now?"_ you ask. The culprit? **No scaling conventions**.

Scaling isn’t just about throwing more servers at a problem. It’s a set of intentional design patterns that ensure your system can handle load gracefully—without breaking under pressure. But without clear scaling *conventions*—rules, standards, and guardrails—your team will fight sprawling, inconsistent code that behaves unpredictably under load.

In this post, I’ll walk you through the **Scaling Conventions Pattern**, a framework to standardize how your system handles scalability. I’ll show you how to avoid the chaos of inconsistent scaling decisions, provide code-first examples, and walk you through anti-patterns that sink even well-architected systems. Let’s get started.

---

## The Problem: Why Scaling Conventions Fail

Scaling without conventions is like building a skyscraper without blueprints—every floor might look different, but they’re all bound to collapse eventually.

### **Symptoms of Scaling Without Conventions**
1. **Inconsistent Query Patterns**
   You might have a `SELECT *` in one query fetching 500 columns, while another query uses `SELECT id FROM table` for the same purpose. Under load, this leads to unpredictable performance and memory spikes.

2. **Lock Contention Nightmares**
   Teams write ad-hoc transactions and locks without considering future contention. A "simple" `UPDATE` operation might block a critical payment flow, causing cascading failures.

3. **API Endpoint Anti-Patterns**
   Some endpoints return paginated results while others dump gigabytes of JSON, confusing clients and wasting bandwidth. No clear rules mean no way to enforce consistency.

4. **Data Consistency Dilemmas**
   Without conventions around eventual vs. strong consistency, teams disagree on whether a "read-after-write" should succeed immediately or wait for replication. This leads to bugs that surface under load.

5. **Microservices Misalignment**
   When services are loosely coupled without scaling guardrails, a "small" change in one service can break another unexpectedly. Example: A service suddenly reads from a DB instead of caching, causing a 10x latency spike.

### **Real-World Example: The Amazon AWS Outage (2017)**
In February 2017, Amazon’s US-East region experienced a cascading failure caused by **unbounded retries** in one service. Developers had no scaling conventions around:
- **Retry logic** (exponential backoff? No)
- **Circuit breakers** (none)
- **Request batching** (no limits)

The result? A ripple effect of cascading failures as retries clogged the system further. **No conventions → No control → Outage.**

---

## The Solution: Scaling Conventions as Your Safety Net

Scaling conventions ensure that every team member—whether at their first or tenth project—knows how to handle load correctly. They’re not prescriptive (because you can’t predict all future scaling needs), but they provide **guardrails** that prevent common pitfalls.

The **Scaling Conventions Pattern** focuses on three pillars:
1. **Query & DB Layer Standards** (How you fetch and modify data)
2. **API & Service Boundaries** (How you expose and consume functionality)
3. **Error Handling & Resilience** (How you recover from failure)

Let’s dive into how to implement this.

---

## Components/Solutions: Building Your Scaling Conventions

### **1. Query & DB Layer Standards**
**Goal:** Ensure queries are scalable, predictable, and maintainable.

#### **Code Example: Consistent Query Patterns**
Create a **query convention** to standardize how data is fetched. Here’s an example using PostgreSQL and Go:

```go
// ❌ Bad: SELECT * with no pagination
func GetAllUsersBad() ([]User, error) {
    var users []User
    _, err := db.Query("SELECT * FROM users")
    if err != nil { ... }
    return users, nil
}

// ✅ Good: Force pagination + limit columns
func GetAllUsersGood(limit int, offset int) ([]User, error) {
    query := `
        SELECT id, name, email, created_at
        FROM users
        LIMIT $1 OFFSET $2
    `
    var users []User
    rows, err := db.Query(query, limit, offset)
    if err != nil { ... }
    defer rows.Close()
    return users, nil
}
```

**Why this works:**
- Limits memory usage (`SELECT *` can return hundreds of columns).
- Enforces pagination (critical for large datasets).
- Encourages explicit column selection (reduces joins and overhead).

#### **SQL Convention: Always Use `LIMIT` and `OFFSET` (or Keyset Pagination)**
```sql
-- ❌ Bad: Unbounded fetch
SELECT * FROM orders WHERE customer_id = 123;

-- ✅ Good: Paginated fetch
SELECT * FROM orders
WHERE customer_id = 123
ORDER BY created_at DESC
LIMIT 10 OFFSET 0;

-- Even better: Keyset pagination (avoids OFFSET issues)
SELECT * FROM orders
WHERE customer_id = 123
AND id < 12345  -- Last seen ID
ORDER BY id DESC
LIMIT 10;
```

---

### **2. API & Service Boundaries**
**Goal:** Define how services interact to avoid bottlenecks and chaos.

#### **Code Example: Standardized API Responses**
Enforce **response size limits** and **consistent error formats**:

```go
// ❌ Bad: No size limits, inconsistent errors
type UserResponse struct {
    Data    []User
    Message string
}

// ✅ Good: Structured, paginated, and consistent
type UserResponse struct {
    Data      []User
    Page      int
    Total     int
    HasMore   bool
    Error     *ErrorWrapper
}

type ErrorWrapper struct {
    Code    string
    Message string
    Retry   bool
}
```

**API Contract Convention:**
- **Always paginate** endpoints returning >100 items.
- **Use `Accept: application/json`** headers to control response format.
- **Rate-limit all public APIs** (e.g., using Redis).

---

### **3. Error Handling & Resilience**
**Goal:** Prevent cascading failures with clear patterns.

#### **Code Example: Retry with Exponential Backoff**
```go
// ❌ Bad: Unbounded retries
func CallService() error {
    maxAttempts := 5
    for i := 0; i < maxAttempts; i++ {
        err := callRemoteService()
        if err == nil { return nil }
    }
    return err
}

// ✅ Good: Exponential backoff + jitter
func CallService() error {
    maxAttempts := 5
    baseDelay := 100 * time.Millisecond
    for i := 0; i < maxAttempts; i++ {
        delay := time.Duration(rand.Int63n(int64(baseDelay * time.Duration(1<<uint(i)))))
        time.Sleep(delay)
        err := callRemoteService()
        if err == nil { return nil }
    }
    return fmt.Errorf("service failed after %d retries", maxAttempts)
}
```

**Convention: Use Circuit Breakers**
```go
// Using Go’s github.com/sony/gobreaker
breaker := gobreaker.NewCircuitBreaker(gobreaker.Settings{
    MaxRequests:     100,
    Interval:        30 * time.Second,
    Timeout:         10 * time.Second,
    ReadyToTrip:     gobreaker.EWMA(0.5, 5, []float64{1.0, 10.0}),
})
func FallibleCall() error {
    return breaker.Execute(func() error {
        return callUnreliableService()
    })
}
```

---

## Implementation Guide: How to Adopt Scaling Conventions

### **Step 1: Document Your Scaling Rules**
Create a **conventions doc** (live in your codebase’s `docs/` folder) with:
- **DB Queries:** Always paginate. Never `SELECT *`.
- **APIs:** Use `Accept: application/json` for size control.
- **Caching:** Default to 5-minute TTL for API responses.
- **Retries:** Exponential backoff + jitter.

Example snippet from a conventions doc:
```
# Database Queries
- Always use `LIMIT` and `OFFSET` (or keyset pagination).
- Avoid `SELECT *` unless fetching a single record.
- Use connection pooling (e.g., `pgpool` for PostgreSQL).
```

### **Step 2: Enforce via Code Reviews**
- Add a **query linting tool** (e.g., SQLFluff or custom Go tools) to catch violations.
- Use **GitHub/GitLab CI checks** to fail builds on bad queries.

```go
// Example: Query validation middleware
func ValidateQuery(query string) error {
    if strings.Contains(query, "SELECT *") {
        return errors.New("query uses 'SELECT *'—use explicit columns")
    }
    if !strings.Contains(query, "LIMIT") {
        return errors.New("query missing LIMIT—add pagination")
    }
    return nil
}
```

### **Step 3: Benchmark Under Load**
Before merging scaling changes, **stress-test** with:
- **Locust/K6** for API endpoints.
- **pgbench** for database layers.
- **Chaos engineering** (kill nodes randomly to test resilience).

Example Locust test for pagination:
```python
from locust import HttpUser, task

class UserApiUser(HttpUser):
    @task
    def fetch_users(self):
        for page in range(1, 11):  # Simulate pagination
            self.client.get(f"/users?page={page}&limit=100")
```

### **Step 4: Train Your Team**
Hold a **conventions workshop** where you:
- Walk through real-world scaling failures.
- Show **before/after** code examples.
- Assign **convention champions** per team.

---

## Common Mistakes to Avoid

1. **Over-engineering for Zombie Loads**
   - ❌ Adding circuit breakers to a low-traffic API.
   - ✅ Only add them where failure is likely (e.g., external services).

2. **Ignoring Data Freshness**
   - ❌ Caching everything for 1 hour, even for "static" data.
   - ✅ Use **TTL policies** (e.g., 5 min for user profiles, 1 day for product catalogs).

3. **No Recovery Paths**
   - ❌ If DB fails, assume the app must crash.
   - ✅ Implement **fallbacks** (e.g., read-only mode on DB outage).

4. **Scoped Conventions to One Team**
   - ❌ Engineering has one set, ML ops has another.
   - ✅ **Centralize conventions** in a shared doc.

5. **Forgetting About Cold Starts**
   - ❌ Deploying serverless functions with no warm-up.
   - ✅ Use **pre-warming** or **provisioned concurrency**.

---

## Key Takeaways
- **Scaling conventions are not optional**—they’re your system’s immune system.
- **Start with DB queries and API contracts**—these are the most critical.
- **Enforce via code, not just docs** (linting, CI checks).
- **Test under load**—conventions are useless unless proven.
- **Update conventions as you learn** (e.g., after a failover drill).

---

## Conclusion

Scaling without conventions is like driving a car without brakes—eventually, you’ll crash. But with **scaling conventions**, you build a system where:
- Every query is predictable.
- Every API endpoint is consistent.
- Every failure is contained.

Your next step? Start by documenting just **three scaling rules** (e.g., "No `SELECT *`," "Always paginate API responses," "Use exponential backoff for retries"). Then, enforce them with code reviews and tests. Over time, your system will become more resilient, maintainable, and *scalable*—without the chaos.

Now go write your conventions doc. Your future self will thank you.

---
```