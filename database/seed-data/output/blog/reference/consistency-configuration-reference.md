**[Pattern] Consistency Configuration Reference Guide**

---

### **Overview**
The **Consistency Configuration** pattern enables developers to define and enforce consistency boundaries across distributed systems by explicitly declaring constraints on data synchronization and state alignment. It ensures predictable behavior in systems where eventual consistency is the norm (e.g., databases, caches, microservices) by allowing **fine-grained control** over consistency guarantees for specific operations or data regions.

This pattern answers the following questions:
- *How do we balance performance and correctness in distributed systems?*
- *When should operations be strongly consistent vs. eventually consistent?*
- *How can we enforce consistency rules without blocking operations?*

Consistency Configuration is typically implemented via:
- **Configuration files** (e.g., JSON/YAML)
- **API annotations** (e.g., `@ConsistencyLevel`)
- **Runtime policies** (e.g., dynamic overrides)
- **Infrastructure policies** (e.g., Kubernetes annotations)

---

## **Implementation Details**

### **Key Concepts**
| Term                  | Definition                                                                                     | Example Use Case                                  |
|-----------------------|-------------------------------------------------------------------------------------------------|----------------------------------------------------|
| **Consistency Scope** | The logical boundary (e.g., table, document, cache region) where consistency rules apply.     | Enforcing strong consistency for a user’s shopping cart. |
| **Consistency Level** | Defines the desired state synchronization (strong, causal, eventual).                         | `@ConsistencyLevel(STRONG)` for inventory updates. |
| **Conflict Resolution** | Rules for handling concurrent modifications (e.g., last-write-wins, merge strategies).          | `ConflictResolution.MERGE` for collaborative editing. |
| **Time-to-Live (TTL)** | Maximum allowed lag before enforcing consistency (e.g., "wait 500ms").                        | `TTL=100ms` for real-time analytics.               |
| **Quorum**            | Minimum number of replicas required to acknowledge a write for strong consistency.             | Quorum=3 for a 5-node database cluster.           |

---

### **When to Use This Pattern**
- **Multi-tier architectures** (e.g., frontend + database + cache).
- **Eventual consistency models** (e.g., DynamoDB, Cassandra) where explicit trade-offs are needed.
- **Hybrid consistency** scenarios (e.g., strongly consistent reads for critical data, eventual consistency for logs).
- **Legacy system modernization** (gradually rolling out stronger guarantees).

**Avoid** when:
- Strong consistency is mandatory for all operations (use **Strong Consistency** pattern).
- The system cannot tolerate latency spikes (use **Optimistic Concurrency Control**).

---

## **Schema Reference**
Below is a standardized schema for defining consistency rules. Implementations may vary slightly by language/framework.

| Field                   | Type       | Required | Description                                                                                     | Example Values                          |
|-------------------------|------------|----------|-------------------------------------------------------------------------------------------------|------------------------------------------|
| `scope`                 | String     | Yes      | Logical identifier for the consistency region (e.g., `users:profile`, `orders:#123`).          | `"orders:#123"`                          |
| `consistency_level`     | Enum       | Yes      | Desired consistency for reads/writes (`STRONG`, `CAUSAL`, `EVENTUAL`).                          | `STRONG`                                 |
| `conflict_resolution`   | Enum       | No       | Strategy for handling conflicts (`LAST_WRITE`, `MERGE`, `CUSTOM`).                              | `MERGE`                                  |
| `read_ttl_ms`           | Integer    | No       | Max allowed read latency before enforcing consistency (milliseconds).                           | `500`                                    |
| `write_quorum`          | Integer    | No       | Minimum replicas to acknowledge a write (for strong consistency).                              | `3`                                      |
| `fallback_policy`       | String     | No       | Action if consistency cannot be guaranteed (e.g., `RETRY`, `SKIP`, `PROMOTE_TO_EVENTUAL`).      | `RETRY`                                  |
| `dependencies`          | Array      | No       | Other scopes this scope depends on (for cascading consistency).                                | `[`orders:#123`, `users:cart`]`         |
| `priority`              | Integer    | No       | Relative importance (higher = more aggressive enforcement).                                    | `10`                                     |

---
### **Example JSON Configuration**
```json
{
  "scopes": [
    {
      "scope": "users:profile",
      "consistency_level": "STRONG",
      "conflict_resolution": "MERGE",
      "write_quorum": 3,
      "fallback_policy": "RETRY"
    },
    {
      "scope": "logs:app",
      "consistency_level": "EVENTUAL",
      "read_ttl_ms": 1000,
      "fallback_policy": "PROMOTE_TO_EVENTUAL"
    }
  ]
}
```

---

## **Query Examples**
Consistency Configuration is typically applied at runtime via annotations, environment variables, or runtime APIs. Below are examples in various contexts.

---

### **1. Database Configuration (ORM/Query Builder)**
```python
# Python (SQLAlchemy Example)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Apply consistency rules to a query
query = session.query(User).filter(User.id == 123)
query.apply_consistency(
    scope="users:profile",
    consistency_level="STRONG",
    write_quorum=2
)
```

```java
// Java (Spring Data JPA Example)
@QueryConsistency(
    scope = "users:profile",
    consistencyLevel = ConsistencyLevel.STRONG,
    writeQuorum = 3
)
public User getUserWithConsistency(@Param("id") Long id) {
    // ...
}
```

---

### **2. Cache Configuration**
```javascript
// Node.js (Redis Example)
const { createClient } = require('redis');
const client = createClient();

/**
 * Set a cache key with consistency rules.
 * @param {string} key - Cache key (e.g., "user:123:profile")
 * @param {string} value - Data to store
 * @param {Object} consistency - Rules (scope, level, etc.)
 */
async function setWithConsistency(key, value, consistency) {
  await client.set(key, value);
  await client.configSet(
    `consistency:${key}`,
    JSON.stringify(consistency)
  );
}

// Usage:
setWithConsistency(
  "user:123:profile",
  JSON.stringify(userData),
  { scope: "users:profile", consistency_level: "STRONG" }
);
```

---

### **3. API Gateway/Service Mesh**
```yaml
# Istio VirtualService (Kubernetes)
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: product-service
spec:
  hosts:
  - "products.example.com"
  http:
  - route:
    - destination:
        host: product-service
    consistency:
      scope: "inventory:#123"
      consistency_level: STRONG
      write_quorum: 2
```

---

### **4. Runtime Overrides (Dynamic)**
```go
// Go (gRPC Example)
package main

import (
	"context"
	"google.golang.org/grpc/metadata"
)

func callWithConsistency(ctx context.Context, scope, level string, quorum int) error {
	md := metadata.New(map[string]string{
		"consistency-scope":  scope,
		"consistency-level": level,
		"quorum":             strconv.Itoa(quorum),
	})
	ctx = metadata.NewOutgoingContext(ctx, md)
	// Proceed with RPC call
}
```

---

## **Conflict Resolution Strategies**
| Strategy       | Behavior                                                                                     | Use Case                                  |
|-----------------|---------------------------------------------------------------------------------------------|-------------------------------------------|
| **Last-Write-Wins** | Discards older versions when conflicts occur.                                          | Non-critical metadata (e.g., user tags). |
| **Merge**        | Combines changes (e.g., JSON patches, CRDTs).                                              | Collaborative editing (e.g., docs).       |
| **Custom**       | User-defined logic via a callback.                                                          | Business-specific rules (e.g., audits).   |
| **Skip**         | Silently discards the conflicting operation.                                               | Idempotent writes (e.g., analytics).      |
| **Retry**        | Retries the operation with exponential backoff.                                           | Critical transactions (e.g., payments).  |

---
### **Example Merge Conflict Resolution (Pseudocode)**
```python
def merge_conflict(left, right, scope):
    if scope == "user:profile":
        # Prefer non-empty fields from the right (right wins for missing fields)
        return {**left, **right}
    elif scope == "orders:#123":
        # For orders, ensure price is not changed unless both agree
        if left.get("price") != right.get("price"):
            raise ConflictError("Price modification conflict")
        return right  # Right wins otherwise
```

---

## **Related Patterns**
| Pattern                          | Relationship to Consistency Configuration                           | When to Combine                          |
|----------------------------------|------------------------------------------------------------------|-------------------------------------------|
| **Saga Pattern**                 | Use Consistency Configuration to define **local transactions** within a saga.        | Distributed workflows with partial failures. |
| **Eventual Consistency**         | Consistency Configuration **enforces** eventual consistency rules.          | Gradual rollouts of new features.          |
| **Strong Consistency**           | Mutually exclusive; use one or the other based on requirements.         | Critical transactions (e.g., banking).    |
| **Optimistic Concurrency Control** | Conflict resolution strategies can be aligned.                     | Read-heavy systems with rare conflicts.  |
| **Circuit Breaker**              | Apply consistency rules **before** tripping circuit breakers.        | Fault-tolerant microservices.             |
| **Idempotency Keys**             | Consistency scopes can act as idempotency keys.                  | Retry-safe APIs.                         |

---

## **Best Practices**
1. **Scope Granularity**:
   - Keep scopes **small and focused** (e.g., `orders:#123` vs. `all_orders`).
   - Avoid **global strong consistency** unless absolutely necessary.

2. **Default to Eventual Consistency**:
   - Assume `EVENTUAL` by default; enforce `STRONG` only where critical.

3. **Monitor Consistency Violations**:
   - Log violations and set alerts for scopes with frequent conflicts.

4. **Dynamic Adjustment**:
   - Allow runtime overrides for non-critical operations (e.g., `fallback_policy: SKIP`).

5. **Document Trade-offs**:
   - Clearly label scopes with their consistency guarantees in API docs.

6. **Testing**:
   - Test conflict resolution strategies with **chaos engineering** (e.g., network partitions).
   - Use tools like **Jepsen** to validate consistency properties.

---

## **Anti-Patterns**
- **Global Consistency Rules**: Applying `STRONG` to all operations degrades performance.
- **Overly Complex Merges**: Custom conflict resolution that is hard to maintain.
- **Ignoring TTLs**: Forgetting to set `read_ttl_ms` can lead to unpredictable latency.
- **Tight Coupling**: Binding consistency to business logic (e.g., `if (isPayment) { STRONG }`).

---

## **Example Workflow**
1. **Define Config**:
   ```json
   {
     "scopes": [
       {
         "scope": "user:123:profile",
         "consistency_level": "STRONG",
         "conflict_resolution": "MERGE"
       }
     ]
   }
   ```
2. **Apply to API Call**:
   ```python
   update_user_profile(123, {"name": "Alice"}, consistency_scope="user:123:profile")
   ```
3. **Conflict Handling**:
   - If `user:123:profile` is updated concurrently, the merge strategy combines changes:
     ```json
     { "name": "Bob", "age": 30 } (current)
     + { "name": "Alice" } (new)
     = { "name": "Alice", "age": 30 } (resolved)
     ```

---

## **Tools and Libraries**
| Tool/Library               | Description                                                                 |
|----------------------------|-----------------------------------------------------------------------------|
| **Cassandra DSE**          | Built-in consistency tuning via `CONSISTENCY LEVEL` in CQL.                 |
| **Apache Kafka**           | Use `isolation.level=read_committed` for transactional consistency.         |
| **SQLAlchemy (Python)**    | Extensions like `sqlalchemy-consistency` for dynamic rules.                |
| **Istio**                  | Service mesh consistency policies via Envoy filters.                         |
| **AWS AppSync**            | Fine-grained consistency controls via GraphQL directives.                   |
| **Custom Implementations** | Lightweight libraries like `consistency-go` or `consistency-js`.          |

---

## **Troubleshooting**
| Issue                          | Cause                                   | Solution                                  |
|--------------------------------|-----------------------------------------|-------------------------------------------|
| **Stale Reads**                | `EVENTUAL` consistency with high latency. | Increase `read_ttl_ms` or switch to `CAUSAL`. |
| **High Latency**               | Too many `STRONG` reads/writes.         | Audit scopes; promote to `EVENTUAL`.      |
| **Deadlocks**                  | Circular dependencies between scopes.   | Restructure scopes or use `CAUSAL`.       |
| **Conflicts Not Resolved**     | Missing `conflict_resolution` config.  | Define a strategy (e.g., `MERGE`).        |
| **Fallback Policy Ignored**    | Policy not properly configured.          | Verify `fallback_policy` in runtime logs. |

---

## **Further Reading**
- [CAP Theorem](https://www.infoq.com/articles/cap-twelve-years-later-how-the-rules-have-changed/)
- [Eventual Consistency Done Right](https://martinfowler.com/articles/two-phase-commit.html)
- [Jepsen Framework](https://jepsen.io/) (Testing consistency)
- [Istio Consistency Patterns](https://istio.io/latest/docs/concepts/traffic-management/#consistency)