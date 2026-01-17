```markdown
---
title: "Failover Gotchas: How to Avoid the Hidden Pitfalls of High Availability"
author: [Your Name]
date: [YYYY-MM-DD]
tags: ["database", "distributed systems", "high availability", "API design", "backend engineering"]
description: "Learn the secret pitfalls of failover that can turn your high-availability system into a single point of failure. Practical examples, real-world tradeoffs, and actionable fixes."
---

# Failover Gotchas: How to Avoid the Hidden Pitfalls of High Availability

High availability (HA) is often the holy grail of backend engineering: a system that never stops, no matter what. Teams spend months architecting redundancy, load balancing, and automatic failover—only to find themselves staring at a 503 error when the "impossible" happens. The irony? **Failover works perfectly in staging, but fails spectacularly in production**. The problem isn’t the failover mechanism itself—it’s the *gotchas* that lurk in its blind spots.

In this post, we’ll dissect the hidden pitfalls of failover—from stale database states to cascading connection leaks—and show you how to avoid them. We’ll use real-world examples (a payment processing system, a global e-commerce platform, and a microservice-based API) to illustrate tradeoffs and solutions. By the end, you’ll know how to design systems that truly handle failure gracefully.

---

## The Problem: Failover That Doesn’t Fail Forward

Failover is supposed to be seamless. When a primary node fails, a standby takes over with minimal downtime. Yet, in practice, many teams hit these common snags:

1. **Stale Data**: Replication lag causes reads to serve outdated data, leading to inconsistent responses. A payment confirmation system might validate a transaction as paid when the actual bank status is `pending`.
2. **Connection Leaks**: After failover, client applications can’t reconnect properly, leaving thousands of long-lived connections hanging. A database cluster might see memory usage spike dangerously after failover.
3. **Cascading Failures**: Secondary nodes fail under load when promoted to primary. A microservice’s Redis cache becomes overwhelmed because it wasn’t designed for primary duties.
4. **No Graceful Degradation**: The system crashes instead of degrading. A health check API returns `500` instead of `429` (Too Many Requests) when the underlying service is overloaded.
5. **Metadata Overhead**: Failover introduces latency spikes because nodes have to query metadata services (e.g., etcd) to find the new primary, increasing response times.

These issues aren’t rare. They’re the silent killers of high availability. The worst part? Many teams don’t even realize a problem exists until they’re already in production—when users are temporarily locked out of their accounts or transactions are duplicated.

---

## The Solution: Failover with Eyes Open

The key to resilient failover is **defensive design**. You must anticipate failure modes and build redundancy at every layer—database, application, and network. Here’s how we’ll tackle it:

1. **Detect and Handle Stale Data**: Use techniques like read-after-write consistency checks and optimistic concurrency.
2. **Manage Connections Properly**: Implement connection pooling, timeouts, and retry logic with exponential backoff.
3. **Design for Secondary Promotion**: Ensure standby nodes can handle sudden load spikes.
4. **Graceful Degradation**: Prioritize requests, throttle aggressively, and provide meaningful error responses.
5. **Minimize Metadata Latency**: Cache metadata locally where possible and use efficient communication protocols.

We’ll explore these tactics with code examples using PostgreSQL (for databases), Go (for APIs), and Kubernetes (for orchestration).

---

## Components/Solutions

### 1. Database Failover: Avoiding Stale Reads
**Challenge**: Replication lag can cause reads to return outdated data. For example, a user might see their account balance as $1,000 when their last transaction changed it to $950.

**Solution**: Use **read-after-write consistency checks** and **temporal queries** to ensure reads are up-to-date.

**Example**: A PostgreSQL transaction validation system with row versioning:
```sql
-- Table with a row_version column to track writes
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    amount DECIMAL(10,2),
    user_id INTEGER REFERENCES users(id),
    row_version INTEGER DEFAULT 0
);

-- Function to check consistency
CREATE OR REPLACE FUNCTION validate_transaction(user_id INTEGER, expected_version INTEGER)
RETURNS BOOLEAN AS $$
DECLARE
    current_version INTEGER;
BEGIN
    SELECT row_version INTO current_version FROM transactions WHERE user_id = user_id AND id = (SELECT id FROM transactions WHERE user_id = user_id ORDER BY id DESC LIMIT 1);

    -- If current version is ahead of expected version, transaction is stale
    RETURN current_version = expected_version;
END;
$$ LANGUAGE plpgsql;
```

**Tradeoff**: This adds complexity to queries and requires application logic to implement retry logic. For simpler cases, consider **eventual consistency** with a fallback (e.g., retry after a delay).

---

### 2. Connection Management: Preventing Leaks
**Challenge**: After failover, clients can’t reconnect quickly enough, causing timeouts or connection pool exhaustion. A classic example is a payment gateway that loses connections to the database after failover.

**Solution**: Use **connection pooling with retry logic** and **short-timeout strategies**.

**Example**: A Go API with `pgx` (PostgreSQL driver) and retry logic:
```go
package main

import (
	"context"
	"time"
	"github.com/jackc/pgx/v5"
	"github.com/jmoiron/sqlx"
)

var (
	// Default connection pool size (adjust based on workload)
	poolSize = 25
	// Retry delay after failover
	retryDelay = 5 * time.Second
)

func connectDB(ctx context.Context) (*sqlx.DB, error) {
	var conn *pgx.Conn
	var err error

	// Configure connection pool
	pgxConfig, err := pgx.ParseConfig("postgres://user:pass@primary-db:5432/db?application_name=api")
	if err != nil {
		return nil, err
	}
	pgxConfig.PoolSize = poolSize

	// Retry logic for failover scenarios
	for i := 0; i < 3; i++ {
		conn, err = pgx.Connect(ctx, pgxConfig.String())
		if err == nil {
			break
		}
		if i < 2 { // Don't retry on fatal errors (e.g., "could not connect to server")
			time.Sleep(time.Duration(i) * retryDelay)
		}
	}
	if err != nil {
		return nil, err
	}

	// Create a sqlx.DB wrapper
	db, err := sqlx.Connect("pgx", conn.Config().ConnConfig().ConnectionString())
	return db, err
}
```

**Tradeoff**: Retry logic can amplify failures if not configured carefully. Use exponential backoff (e.g., `retry.Delay(time.Duration(math.Pow(2, retryCount)) * time.Second)`) and limit the number of retries.

---

### 3. Secondary Promotion: Preparing Standbys
**Challenge**: Secondary nodes fail when promoted to primary because they weren’t designed for high load. A caching service might crash under sudden traffic when promoted.

**Solution**: **Pre-warm standbys** and **test promotion in staging**.

**Example**: A Kubernetes pod disruption budget (PDB) to ensure standbys are ready:
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-service
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: api-service
    spec:
      containers:
      - name: api
        image: your-api:latest
        ports:
        - containerPort: 8080
        resources:
          requests:
            cpu: "100m"  # Pre-warm CPU
            memory: "256Mi"
          limits:
            cpu: "500m"
            memory: "512Mi"
---
# poddisruptionbudget.yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: api-pdb
spec:
  selector:
    matchLabels:
      app: api-service
  maxUnavailable: 1  # Allow 1 pod to be disrupted at a time
```

**Tradeoff**: Pre-warming increases resource usage. Balance this with your SLAs—if downtime is unacceptable, pre-warm more aggressively.

---

### 4. Graceful Degradation: Let the System Breathe
**Challenge**: Failover causes a crash instead of graceful degradation. A health check API returns `500` instead of `429` when the database is down.

**Solution**: **Implement circuit breakers** and **rate limiting**.

**Example**: A Go API with `go-circuits` and `prometheus` for monitoring:
```go
package main

import (
	"net/http"
	"time"
	"github.com/sony/gobreaker"
)

var cb *gobreaker.CircuitBreaker

func init() {
	cb = gobreaker.NewCircuitBreaker(gobreaker.Settings{
		MaxRequests:     100,
		Interval:        time.Second * 10,
		Timeout:         time.Second * 30,
		ReadyToTrip: func(counts gobreaker.Counts) bool {
			// Trip if error rate exceeds 50%
			return counts.RequestCount > 0 &&
				float64(counts.ErrorCount)/float64(counts.RequestCount) > 0.5
		},
	})
}

func handleHealthCheck(w http.ResponseWriter, r *http.Request) {
	err := cb.Execute(func() error {
		// Simulate slow database query
		time.Sleep(2 * time.Second)
		return nil
	})

	if err != nil {
		http.Error(w, "Service unavailable", http.StatusServiceUnavailable)
		return
	}
	w.WriteHeader(http.StatusOK)
	w.Write([]byte("Service healthy"))
}
```

**Tradeoff**: Circuit breakers introduce latency. Monitor them closely—trip points should align with your team’s capacity to handle failure.

---

### 5. Metadata Latency: Cache Everything
**Challenge**: Failover causes latency spikes because nodes query metadata services (e.g., etcd) for the new primary.

**Solution**: **Cache metadata locally** and **minimize communication**.

**Example**: A Go client caching etcd metadata:
```go
package main

import (
	"context"
	"time"
	"sync"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	etcdclient "go.etcd.io/etcd/client/v3"
)

var (
	etcdClient *etcdclient.Client
	metadata   map[string]string
	mu         sync.Mutex
	cacheTTL   = 30 * time.Second
)

func initEtcdClient(addr string) error {
	cli, err := etcdclient.New(etcdclient.Config{
		Endpoints:   []string{addr},
		DialTimeout: 5 * time.Second,
	})
	if err != nil {
		return err
	}
	etcdClient = cli
	return nil
}

func getPrimaryDB() (string, error) {
	mu.Lock()
	defer mu.Unlock()

	now := time.Now()
	if len(metadata) > 0 && now.Sub(metadata["lastUpdated"]) < cacheTTL {
		return metadata["primaryDB"], nil
	}

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	// Query etcd for the latest primary
	resp, err := etcdClient.Get(ctx, "/db/primary")
	if err != nil {
		return "", err
	}

	if len(resp.Kvs) == 0 {
		return "", errors.New("no primary DB found")
	}

	metadata = map[string]string{
		"primaryDB":  string(resp.Kvs[0].Value),
		"lastUpdated": now,
	}
	return metadata["primaryDB"], nil
}
```

**Tradeoff**: Caching introduces stale data risk. Use short TTLs and invalidation strategies (e.g., watch etcd for changes).

---

## Implementation Guide: Step-by-Step Failover Safety

1. **Step 1: Instrument Everything**
   - Add latency and error metrics to your database queries and API endpoints.
   - Use tools like Prometheus, Datadog, or OpenTelemetry to track failover events.

2. **Step 2: Test Failover in Staging**
   - Simulate node failures with tools like `pg_ctl failover` (PostgreSQL) or `kubectl delete pod`.
   - Verify that your application recovers without manual intervention.

3. **Step 3: Implement Retry Logic**
   - Use exponential backoff for database connections and API calls.
   - Example retry strategy:
     ```go
     func retryWithBackoff(ctx context.Context, maxRetries int, fn func() error) error {
         var lastErr error
         for i := 0; i < maxRetries; i++ {
             err := fn()
             if err == nil {
                 return nil
             }
             lastErr = err
             delay := time.Duration(math.Pow(2, float64(i))) * time.Second
             if deadline, ok := ctx.Deadline(); ok {
                 remaining := time.Until(deadline)
                 if delay > remaining {
                     delay = remaining
                 }
             }
             time.Sleep(delay)
         }
         return lastErr
     }
     ```

4. **Step 4: Design for Secondary Promotion**
   - Ensure standbys have the same resource limits as primaries.
   - Test promotion by manually failing the primary and verifying standby takes over.

5. **Step 5: Add Graceful Degradation**
   - Implement circuit breakers for external dependencies (e.g., payment gateways).
   - Return `429` (Too Many Requests) instead of `500` when the system is overwhelmed.

6. **Step 6: Monitor Failover Events**
   - Alert on failover events with tools like Slack or PagerDuty.
   - Example alerting rule for PostgreSQL failovers:
     ```
     ALERTIF (pg_stat_replication.pg_is_in_recovery = true AND pg_stat_replication.pg_replay_lag > 5000)
     ```

---

## Common Mistakes to Avoid

1. **Assuming Failover is Automatic**
   - Don’t assume your database or Kubernetes cluster will handle failover correctly. Test it manually.

2. **Ignoring Replication Lag**
   - Stale reads can cause data inconsistency. Always validate writes before proceeding.

3. **Overloading Standbys**
   - Standbys should be identical to primaries in terms of resources. Under-provisioning them turns failover into a disaster.

4. **Lacking Retry Logic**
   - Temporary failures (e.g., network blips) should retry with backoff. Without it, your system will fail fast.

5. **Not Monitoring Failover Events**
   - If you don’t know when failover happens, you can’t debug issues. Monitor and alert on failover events.

6. **Caching Metadata Poorly**
   - Stale metadata causes clients to query the wrong endpoints. Cache it smartly with short TTLs.

7. **Designing for Perfection**
   - Graceful degradation isn’t about hiding failures—it’s about letting the system operate under pressure. Prioritize requests, throttle aggressively, and provide feedback.

---

## Key Takeaways

- **Failover is only as good as your testing**: Always simulate failures in staging. What works in theory often fails in practice.
- **Stale data is silent killer**: Use consistency checks, eventual consistency, or temporal queries to mitigate stale reads.
- **Connections must be managed**: Implement connection pooling, timeouts, and retry logic to avoid leaks.
- **Standbys must be primaries-in-waiting**: Pre-warm them, test promotion, and ensure they can handle load spikes.
- **Graceful degradation is better than crashes**: Use circuit breakers, rate limiting, and meaningful error responses.
- **Metadata latency hurts**: Cache metadata locally and minimize communication with metadata services.
- **Monitor everything**: Failover events, replication lag, and connection leaks should all be instrumented and alerted on.
- **No silver bullets**: Failover is a balancing act. Tradeoffs exist—make informed choices based on your SLAs and team capacity.

---

## Conclusion

Failover gotchas are the hidden costs of high availability. They turn your "always-on" system into a moving target, where every failure reveals a new vulnerability. The good news? These issues are solvable—with the right mix of testing, instrumentation, and defensive design.

Start small: test failover in staging, implement retry logic, and monitor replication lag. Gradually add circuit breakers, graceful degradation, and metadata caching. The goal isn’t perfection—it’s resilience. A system that fails forward, not fails down.

Remember: **The best failover is the one you never need to use—but the second-best is the one you can debug in 10 minutes.** Build with that in mind.

---
**Further Reading**:
- [PostgreSQL High Availability Guide](https://www.postgresql.org/docs/current/high-availability.html)
- [Circuit Breakers: Designing Resilient Software](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Kubernetes Pod Disruption Budget](https://kubernetes.io/docs/tasks/run-application/configure-pdb/)
- [Go Retry Package](https://github.com/avast/retry-go)
```

This blog post is structured to be practical, code-heavy, and honest about tradeoffs while keeping a friendly yet professional tone. It balances theory with actionable steps and includes real-world examples to illustrate key concepts.