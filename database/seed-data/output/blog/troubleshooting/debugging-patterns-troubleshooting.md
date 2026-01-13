# **Debugging Patterns: A Troubleshooting Guide**
*Common Patterns in Troubleshooting Backend Issues with Practical Fixes*

---

## **1. Introduction**
Debugging is a systematic process of identifying and resolving issues in software systems. Whether dealing with performance bottlenecks, crash loops, or inconsistent behavior, recognizing common **debugging patterns** helps engineers break down problems efficiently.

This guide covers:
- **Symptom Checklists** to identify root causes quickly.
- **Common Issues and Fixes** with code examples.
- **Debugging Tools & Techniques** for quick resolution.
- **Prevention Strategies** to reduce future occurrences.

---

## **2. Symptom Checklist: Recognizing Debugging Patterns**
Before diving into fixes, systematically check for these symptoms by pattern:

| **Pattern**               | **Symptoms**                                                                 | **Likely Cause**                          |
|---------------------------|------------------------------------------------------------------------------|-------------------------------------------|
| **Crash/Crash Loop**      | Application dies; logs show uncaught exceptions, segmentation faults.        | Buggy logic, memory leaks, race conditions. |
| **Performance Degradation** | Slow response times, high CPU/memory usage, timeouts.                   | Inefficient queries, N+1 problems, locks. |
| **Inconsistent State**   | Database corruption, race conditions, lost updates.                       | Poor synchronization, missing transactions. |
| **Timeout Errors**        | HTTP requests fail with `ETIMEDOUT`, `ECONNRESET`.                        | Network issues, slow dependencies, deadlocks. |
| **Data Loss/Corruption**  | Missing records, duplicate entries, incorrect aggregations.              | Transaction errors, incorrect joins.      |
| **Logging/Observability Gaps** | Unable to reproduce issues due to missing logs/metrics.          | Poor logging, insufficient monitoring.    |

**Action:** Classify the symptom into one of these patterns and proceed to the corresponding section.

---

## **3. Common Issues & Fixes**

### **3.1 Crash/Crash Loop**
**Symptoms:** App crashes repeatedly, logs show `NullPointerException`, `Segmentation Fault`, or `UnhandledPromiseRejection`.

#### **Common Causes & Fixes**

| **Issue**                     | **Debugging Steps**                                                                 | **Fix** (Code Example)                                                                 |
|-------------------------------|-------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| **Uncaught Exception in Async Code** | Check error boundaries (e.g., `try/catch` in Promises/Async-Await).          | ```javascript<br>async function fetchData() {<br>  try {<br>    const res = await fetch(url);<br>    return await res.json();<br>  } catch (err) {<br>    console.error("Fetch failed:", err);<br>    throw new Error("Retry or fallback"); // Handle gracefully<br>  }<br>}``` |
| **Memory Leak (e.g., Node.js)** | Use `--leaks` flag (`node --leaks app.js`) or inspect heap dumps (`--inspect`). | ```javascript<br>// Fix: Clean up event listeners<br>server.on('close', () => {<br>  db.close();<br>  clearInterval(pollingTimer);<br>});``` |
| **Race Condition**            | Use locks (`Mutex`), `async/await`, or `Promise.allSettled`.                     | ```javascript<br>const { Mutex } = require('async-mutex');<br>const mutex = new Mutex();<br><br>async function updateUser(userId) {<br>  const release = await mutex.acquire();<br>  try {<br>    await UserModel.update({ id: userId, balance: 100 });<br>  } finally {<br>    release();<br>  }<br>}``` |

---

### **3.2 Performance Degradation**
**Symptoms:** Slow API responses, high `p99` latency, or spikes in memory/CPU.

#### **Common Causes & Fixes**

| **Issue**                     | **Debugging Steps**                                                                 | **Fix**                                                                               |
|-------------------------------|-------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| **N+1 Query Problem**          | Check SQL logs for repeated `SELECT` calls (e.g., fetching users + their orders). | **Fix:** Eager-load relations.                                                                 |
| **Example (Laravel/Eloquent):**                                                                                     |
|                               | ```php<br>// BAD: N+1 queries<br>$users = User::all();<br>$users = $users->with('orders')->get(); // Still N+1<br><br>// GOOD: Eager load upfront<br>$users = User::with('orders')->get();``` |                                                                                           |
| **Inefficient DB Index**      | Run `EXPLAIN ANALYZE` on slow queries; check missing indexes.                     | ```sql<br>CREATE INDEX idx_user_email ON users(email); -- Add if no index exists<br>``` |
| **Blocking I/O (e.g., Disk/DB)** | Use `top`/`htop` to check CPU; `strace` to trace system calls.                     | **Fix:** Asynchronous I/O, caching (Redis), or connection pooling (e.g., PgBouncer). |
| **Lock Contention**           | Check database locks (`SHOW PROCESSLIST` in MySQL).                                | ```sql<br>-- Reduce lock duration<br>BEGIN; -- Use shorter transactions<br>UPDATE accounts SET balance = balance - 10 WHERE id = 1;<br>COMMIT;``` |

---

### **3.3 Inconsistent State**
**Symptoms:** Duplicate transactions, stale data, or race conditions.

#### **Common Causes & Fixes**

| **Issue**                     | **Debugging Steps**                                                                 | **Fix**                                                                               |
|-------------------------------|-------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| **Missing Database Transactions** | Enable `pgAudit` (Postgres) or `binlog` (MySQL) to track changes.                  | ```javascript<br>// Fix: Wrap DB ops in transactions<br>await db.transaction(async (trx) => {<br>  await trx.run('UPDATE accounts SET balance = balance - 10');<br>  await trx.run('UPDATE accounts SET balance = balance + 10');<br>});``` |
| **Eventual Consistency Issues (CQRS)** | Replay events to verify consistency.                                               | **Fix:** Use sagas or compensating transactions.                                        |
| **Race in Shared State**      | Add `if (condition) lock` logic or use atomic operations.                            | ```python<br># Fix: Atomic decrement<br>from threading import Lock<br>lock = Lock()<br><br>def decrement_counter():<br>  with lock:<br>    if counter > 0:<br>      counter -= 1``` |

---

### **3.4 Timeout Errors**
**Symptoms:** `ETIMEDOUT`, `ECONNRESET`, or slow external API calls.

#### **Common Causes & Fixes**

| **Issue**                     | **Debugging Steps**                                                                 | **Fix**                                                                               |
|-------------------------------|-------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| **Slow External API**         | Use `curl -v` or `tcpdump` to inspect network latency.                               | **Fix:** Implement retry logic with exponential backoff.                              |
| **Example (Exponential Backoff):**                                                                       |
|                               | ```javascript<br>const retry = async (fn, maxRetries = 3) => {<br>  let retries = 0;<br>  while (retries < maxRetries) {<br>    try {<br>      return await fn();<br>    } catch (err) {<br>      retries++;<br>      if (retries === maxRetries) throw err;<br>      await new Promise(res => setTimeout(res, 100 * retries)); // Exponential delay<br>    }<br>  }<br>};``` |                                                                                           |
| **Deadlock in DB**            | Check `SHOW ENGINE INNODB STATUS` (MySQL) or `pg_locks` (Postgres).                | **Fix:** Add `FOR UPDATE` hints or optimize schema.                                      |
| **Connection Pool Exhaustion** | Monitor pool size (`--max-connections` in Redis/MySQL).                             | **Fix:** Increase pool size or use connection recycling.                              |

---

### **3.5 Data Loss/Corruption**
**Symptoms:** Missing records, duplicate transactions, or incorrect aggregations.

#### **Common Causes & Fixes**

| **Issue**                     | **Debugging Steps**                                                                 | **Fix**                                                                               |
|-------------------------------|-------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| **Uncommitted Transaction**   | Check DB logs for interrupted transactions.                                           | **Fix:** Enable `autocommit` or use `BEGIN/COMMIT` explicitly.                       |
| **Incorrect JOIN Logic**      | Run `EXPLAIN` on problematic queries.                                                 | ```sql<br>-- Fix: Add proper JOIN conditions<br>SELECT u.*, o.amount<br>FROM users u<br>JOIN orders o ON u.id = o.user_id AND o.status = 'completed';<br>``` |
| **Race in Distributed Systems** | Use `CRDTs` or conflict-free replicated data types.                                  | **Fix:** Implement operational transformation (OT) for collaborative apps.            |

---

## **4. Debugging Tools & Techniques**
### **4.1 Observability Tools**
| **Tool**          | **Purpose**                                                                 | **Example Command/Setup**                                                                 |
|-------------------|-----------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| **Logging**       | Capture runtime data (structured logs with `winston`/`logfmt`).               | ```bash<br># JSON logs<br>logger.info({ event: 'user_login', userId: 123 });``` |
| **APM (New Relic, Datadog)** | Track latency, errors, and traces.                                           | ```javascript<br>// New Relic<br>require('newrelic');``` |
| **Distributed Tracing** | Trace requests across microservices (Jaeger, OpenTelemetry).                | ```bash<br># Start Jaeger<br>docker run -d -p 16686:16686 jaegertracing/all-in-one``` |
| **Database Profiling** | Identify slow queries (`pgBadger`, `Percona PMM`).                            | ```bash<br># MySQL slow query log<br>mysql -u root -p -e "SET GLOBAL slow_query_log = 'ON';"` |

### **4.2 Debugging Techniques**
1. **Reproduce Locally**
   - Use `docker-compose` to spin up dev environments.
   - Example:
     ```yaml
     # docker-compose.yml
     services:
       db:
         image: postgres
         environment:
           POSTGRES_PASSWORD: example
     ```
2. **Isolate the Issue**
   - Comment out code sections to narrow down the cause.
   - Example (binary search debugging):
     ```javascript
     // Comment out chunks of code until the bug disappears
     // if (featureA) { // <-- Remove this block if suspected
     //   doSomething();
     // }
     ```
3. **Use Assertions**
   - Validate assumptions with `assert`.
     ```javascript
     const { assert } = require('assert');
     assert.deepStrictEqual(user.balance, 100, "Balance should be 100");
     ```
4. **Debug SQL Queries**
   - Run `EXPLAIN ANALYZE` in PostgreSQL:
     ```sql
     EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'test@example.com';
     ```
5. **Memory Profiling**
   - Use `--inspect` in Node.js or `heapdump` in Chrome DevTools.

---

## **5. Prevention Strategies**
### **5.1 Code-Level Practices**
- **Input Validation:** Sanitize all inputs (e.g., `express-validator`).
  ```javascript
  // Sanitize user input
  const { body, validationResult } = require('express-validator');
  app.post('/api/user', [
    body('email').isEmail(),
  ], (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) return res.status(400).send(errors.array());
  });
  ```
- **Defensive Programming:** Assume all external calls may fail.
  ```javascript
  // Handle edge cases
  const result = await db.query('SELECT * FROM users WHERE id = ?', [userId]);
  if (!result.rows.length) throw new Error("User not found");
  ```
- **Idempotency:** Design APIs to be retried safely (e.g., `idempotency-key` header).

### **5.2 Infrastructure-Level Practices**
- **Chaos Engineering:** Test failure scenarios with `chaos-monkey`.
- **Automated Rollbacks:** Use blue-green deployments or feature flags.
- **Backup & Recovery:** Automate DB backups (e.g., `pg_dump` cron jobs).

### **5.3 Monitoring & Alerting**
- **SLOs/SLIs:** Define error budgets (e.g., "Allow 1% of requests to fail").
- **Alerting Rules:**
  - `p99 latency > 500ms` → Alert.
  - `Database connections > 80%` → Alert.
- **Tools:**
  - Prometheus + Grafana for metrics.
  - AlertManager for alerts.

### **5.4 Testing Strategies**
- **Unit Tests:** Mock external dependencies (e.g., `sinon`).
  ```javascript
  // Mock a slow API call
  const sinon = require('sinon');
  sinon.stub(apiClient, 'fetchUser').resolves({ id: 1, name: 'Test' });
  ```
- **Integration Tests:** Test DB interactions (e.g., `testcontainers`).
  ```javascript
  // Test DB transaction
  test('transaction should rollback on error', async () => {
    const trx = await db.transaction();
    try {
      await trx.query('UPDATE accounts SET balance = balance - 100');
      await trx.query('UPDATE accounts SET balance = balance + 100'); // Fails
      await trx.commit(); // Should not reach here
    } catch {
      await trx.rollback();
    }
  });
  ```
- **Chaos Tests:** Simulate network partitions (`netem` tool).

---

## **6. Summary Checklist for Quick Resolution**
1. **Classify the symptom** (Crash? Performance? Inconsistency?).
2. **Reproduce locally** (Isolate the issue with `docker-compose`/`minimal repro`).
3. **Inspect logs/metrics** (APM, database logs, system metrics).
4. **Apply fixes systematically** (Start with the most likely cause).
5. **Prevent recurrence** (Add tests, improve observability, review code reviews).
6. **Monitor the fix** (Ensure the issue doesn’t regress).

---

## **7. Further Reading**
- [Google’s Site Reliability Engineering (SRE) Book](https://sre.google/sre-book/)
- [Debugging Distributed Systems (Martin Kleppmann)](https://www.patterns.dev/posts/debugging-distributed-systems/)
- [12-Factor App](https://12factor.net/) (Best practices for debugging in cloud apps)