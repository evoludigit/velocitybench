# **Debugging "Error Handling and Partial Results" Pattern: A Troubleshooting Guide**
*A Practical Guide for Nested Queries with Graceful Failure*

## **1. Introduction**
When implementing **"Error Handling and Partial Results"**, the goal is to allow partial success in nested operations—meaning if one part fails, others should still execute and return usable data. This pattern is common in:
- Microservices orchestration
- Database transactions with fallback logic
- API aggregates (e.g., fetching user data + posts + likes)
- Asynchronous batch processing

This guide provides a structured approach to diagnosing and fixing issues when errors cause cascading failures or disrupt partial results.

---

## **2. Symptom Checklist**
Before diving into fixes, verify these symptoms:

### **Primary Symptoms**
✅ **Complete Query Failure on Partial Error**
- Operation stops entirely if one sub-query fails (e.g., fetching user + posts, but posts fail → user data is lost).

✅ **No Partial Results Returned**
- System returns `null`/`error` instead of partial results when some sub-operations succeed.

✅ **Debugging Is Difficult**
- Errors are masked by high-level exceptions.
- Logs show only the last failure, not intermediate successes.

### **Secondary Symptoms**
🔹 **Timeouts or Deadlocks**
- Long-running queries hang due to error recovery loops.

🔹 **Inconsistent Data**
- Some clients receive partial data, others don’t (e.g., due to race conditions).

🔹 **Error Propagation Issues**
- Lower-level errors (e.g., DB timeouts) are caught but not properly logged/handled.

🔹 **High Latency in Error Cases**
- Retrying failed operations adds overhead, degrading performance.

---

## **3. Common Issues & Fixes**

### **Issue 1: No Parallel Execution of Sub-Operations**
**Problem:** If sub-operations run sequentially, a failure immediately halts the entire process.

**Example (Bad):**
```javascript
async function fetchUserData(userId) {
  const user = await db.getUser(userId); // Fails → whole function fails
  const posts = await db.getPosts(userId); // Never reaches here
  return { user, posts };
}
```

**Solution:** Use **concurrent execution** with `Promise.all` (or `Promise.allSettled` for partial results).

```javascript
async function fetchUserData(userId) {
  const [user, posts] = await Promise.allSettled([
    db.getUser(userId),
    db.getPosts(userId)
  ]);

  const result = {
    user: user.status === 'fulfilled' ? user.value : null,
    posts: posts.status === 'fulfilled' ? posts.value : []
  };

  return result;
}
```

**Key Takeaway:**
- `Promise.allSettled` ensures all promises complete (success/failure).
- Collect partial results instead of aborting on error.

---

### **Issue 2: Unhandled Rejections in Async Flows**
**Problem:** If a Promise rejects but isn’t caught, the entire flow crashes.

**Example (Bad):**
```javascript
async function processBatch(items) {
  for (const item of items) {
    await db.process(item); // No error handling
  }
}
```

**Solution:** Use `.catch()` on individual promises or wrap in a try-catch block.

```javascript
async function processBatch(items) {
  await Promise.all(
    items.map(item =>
      db.process(item).catch(error => {
        console.error(`Failed to process ${item.id}:`, error);
        return { item, error: "Processed with partial data" };
      })
    )
  );
}
```

**Key Takeaway:**
- Always handle rejections explicitly.
- Log errors for debugging without crashing the main flow.

---

### **Issue 3: Database Transactions Blocking Partial Results**
**Problem:** In database transactions, a rollback on error can discard partial work.

**Example (Bad – SQL):**
```sql
BEGIN TRANSACTION;
INSERT INTO users VALUES (...); -- Fails
INSERT INTO posts VALUES (...); -- Never happens
COMMIT; -- Rolled back
```

**Solution:** Use **sagas** or **eventual consistency** patterns.

```javascript
// Example with retries and compensation
async function createUserWithPosts(userData) {
  try {
    await db.saveUser(userData);
    await db.savePosts(userData.posts);
  } catch (error) {
    // Retry or compensate
    if (error.code === "CONFLICT") {
      await db.compensateUserDeletion(userData.id);
      throw error;
    }
  }
}
```

**Key Takeaway:**
- Avoid strict ACID transactions for partial success.
- Use **outbox patterns** or **event sourcing** for compensation.

---

### **Issue 4: API Aggregate Failures (e.g., GraphQL, REST)**
**Problem:** A single field failure (e.g., `posts`) breaks the entire response.

**Example (Bad – GraphQL):**
```graphql
query {
  user(id: "1") { name, posts { title } } # Posts fail → whole `user` is missing
}
```

**Solution:** **Error boundaries in resolvers**, returning `null` or fallback data.

```javascript
// GraphQL resolver
const userResolver = async (_, { id }) => {
  const [user, posts] = await Promise.allSettled([
    db.getUser(id),
    db.getPosts(id)
  ]);

  return {
    ...(user.status === "fulfilled" && user.value),
    posts: posts.status === "fulfilled" ? posts.value : [],
    error: posts.status === "rejected" ? posts.reason : null
  };
};
```

**Key Takeaway:**
- Design APIs to **degrade gracefully**.
- Use **polymorphic responses** (e.g., `{ data, error }`).

---

### **Issue 5: Retry Logic Causing Cascading Failures**
**Problem:** Exponential backoff retries on a single failure can overwhelm the system.

**Example (Bad - Naive Retry):**
```javascript
async function fetchWithRetry(url, maxRetries = 3) {
  try {
    return await fetch(url);
  } catch (error) {
    if (maxRetries-- > 0) {
      await retryWithDelay(1000 * Math.pow(2, maxRetries)); // 1s → 2s → 4s
      return fetchWithRetry(url, maxRetries);
    }
    throw error;
  }
}
```

**Solution:** **Limit retries per sub-operation** and **fail fast** if critical failures occur.

```javascript
async function fetchWithRetry(url, maxRetries = 2) {
  try {
    return await fetch(url);
  } catch (error) {
    if (maxRetries-- > 0 && isRetryableError(error)) {
      await retryWithDelay(1000 * Math.pow(2, maxRetries));
      return fetchWithRetry(url, maxRetries);
    }
    console.error("Non-retriable error:", error);
    return null; // Return partial data
  }
}
```

**Key Takeaway:**
- **Don’t retry on known failures** (e.g., 404 vs. 500).
- **Circuits breakers** help prevent cascading outages.

---

## **4. Debugging Tools & Techniques**

### **A. Logging & Monitoring**
- **Structured Logging:** Use `pino`, `winston`, or OpenTelemetry to track partial results vs. failures.
  ```javascript
  const logger = pino();
  logger.info("Fetched user:", { user, posts: posts?.length || 0 });
  ```
- **Distributed Tracing:** Tools like **Jaeger** or **Zipkin** help track request flows across services.

### **B. Error Boundaries in UI**
- If using React/Vue, implement **error boundaries** to catch JS errors and fallback UI.
  ```javascript
  class ErrorBoundary extends React.Component {
    state = { hasError: false };
    static getDerivedStateFromError(error) {
      return { hasError: true };
    }
    render() {
      return this.state.hasError ? <FallbackUI /> : this.props.children;
    }
  }
  ```

### **C. Query Playgrounds**
- Use **Postman**, **GraphQL Playground**, or **Prisma Studio** to test partial queries manually.
- Example GraphQL query to simulate partial failure:
  ```graphql
  query {
    user(id: "1") {
      name
      posts @skipIf(error: "DB_DOWN") { ... }
    }
  }
  ```

### **D. Database-Specific Debugging**
| Database | Tool/ Technique |
|----------|----------------|
| PostgreSQL | `pgAdmin` + `EXPLAIN ANALYZE` |
| MongoDB | `mongosh --eval "db.stats()"` |
| Redis | `redis-cli --latency` |
| DynamoDB | AWS CloudWatch + `Scan` queries |

### **E. Load Testing**
- Use **k6**, **Locust**, or **Gatling** to simulate partial failure scenarios.
  ```javascript
  // k6 script to test partial success
  import http from 'k6/http';

  export default function () {
    const res = http.get('https://api.example.com/user/1');
    if (res.status === 500) {
      console.error("Simulated failure");
    }
    console.log("Partial result:", JSON.parse(res.body));
  }
  ```

---

## **5. Prevention Strategies**

### **A. Design for Failure Early**
- **Fail Fast:** Validate inputs before expensive operations.
  ```javascript
  if (!userId) throw new Error("Missing user ID");
  ```
- **Defensive Programming:** Assume services will fail.
  ```javascript
  function withRetry(fn, retries = 3) {
    return async (...args) => {
      for (let i = 0; i < retries; i++) {
        try { return await fn(...args); } catch (error) { if (i === retries - 1) throw error; }
      }
    };
  }
  ```

### **B. Circuit Breakers**
- Implement **Hystrix-like** resilience (e.g., `opossum` in Node.js).
  ```javascript
  const circuitBreaker = require('opossum');

  const safeFetch = circuitBreaker(async (url) => {
    return await fetch(url);
  }, {
    timeout: 5000,
    errorThresholdPercentage: 50,
    resetTimeout: 30000
  });
  ```

### **C. Idempotency Keys**
- For retries, use **idempotency keys** to avoid duplicate processing.
  ```javascript
  const idempotencyKey = `${userId}-${Date.now()}`;
  await db.processWithIdempotency(idempotencyKey, userData);
  ```

### **D. Feature Flags & Canary Releases**
- Roll out partial result handling gradually.
  ```javascript
  // Enable in config
  const enablePartialResults = process.env.ENABLE_PARTIAL_RESULTS === "true";

  if (enablePartialResults) {
    return { user, posts: posts || [] };
  } else {
    return { user, posts }; // Throw if undefined
  }
  ```

### **E. Post-Mortem Analysis**
- After a failure, ask:
  1. **Which sub-operation failed?** (Logs)
  2. **Was it recoverable?** (Retry patterns)
  3. **Did clients accept partial results?** (Monitoring)
  4. **Can we auto-compensate?** (Saga patterns)

---

## **6. Quick Reference Table**
| **Issue**               | **Symptom**                          | **Fix**                                  | **Tool/Example**                     |
|-------------------------|--------------------------------------|------------------------------------------|---------------------------------------|
| No parallel execution   | Full failure on any error            | `Promise.allSettled`                     | [Code](#example-1)                    |
| Unhandled async errors  | Crashes on rejection                 | `.catch()` or try-catch                 | [Code](#example-2)                    |
| DB transaction leaks    | Partial data lost on rollback        | Sagas / eventual consistency            | [Code](#example-3)                    |
| API aggregate failures  | Missing fields in response           | Error boundaries + fallback data        | [Code](#example-4)                    |
| Retry storms            | System overload                     | Circuit breakers + retries per op       | [Code](#example-5)                    |

---

## **7. Final Checklist for Implementation**
Before deploying:
1. **Test partial failures** in staging.
2. **Log all rejected promises** (`Promise.allSettled`).
3. **Set up alerts** for repeated failures.
4. **Document fallback behavior** (e.g., "Posts missing → return empty array").
5. **Monitor partial success rates** (e.g., "90% of API calls return partial data").

---

## **8. Further Reading**
- [Error Boundaries in React](https://reactjs.org/docs/error-boundaries.html)
- [Saga Pattern for Distributed Transactions](https://microservices.io/patterns/data/saga.html)
- [Resilience Patterns by Microsoft](https://resilience.github.io/)
- [k6 for Load Testing](https://k6.io/docs/)

---
**Happy debugging!** This pattern is tough but pays off when you need robustness over strict consistency. 🚀