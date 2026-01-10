```markdown
---
title: "Health Checks and Liveness Probes: Building Resilient APIs"
date: 2024-02-15
author: "Alex Carter"
description: "Learn how to implement health checks and liveness probes for self-healing services, with practical examples in Go, Python, and Kubernetes."
tags: ["backend", "devops", "architecture", "kubernetes", "resilience"]
---

# Health Checks and Liveness Probes: Building Resilient APIs

![Health checks illustration](https://res.cloudinary.com/databricks/cloud_images/image/upload/q_auto:good,f_auto/v1629318364/healthchecks/health-check-architecture.png)

In modern distributed systems, we expect applications to self-heal, gracefully handle failures, and recover from transient issues. Yet, many production systems still suffer from cascading failures because containers, pods, or microservices continue accepting traffic even when they're degraded or stuck.

The missing piece? **Proper health checks and liveness/readiness probes**. These patterns allow orchestration systems (like Kubernetes) and load balancers to distinguish between:

- A service that's **slow but functioning** (healthy)
- A service **stuck in a degraded state** (needs restart)
- A service that's **down or misconfigured** (needs replacement)

Without them, you risk:
- Wasting resources on containers that aren't actually running
- Overloading healthy nodes with traffic meant for broken ones
- Exposed users to degraded API responses
- Prolonged downtime during rolling updates

In this article, we'll cover how to implement **health checks** (general service health verification) and **liveness/readiness probes** (Kubernetes-specific patterns) with practical examples in Go, Python, and Kubernetes.

---

## The Problem: When Containers Lie to Load Balancers

Imagine this scenario—a user requests data from your API, which internally calls three services:

1. **User Profile Service** (up, but slow)
2. **Payment Processing** (stuck waiting on a database)
3. **Inventory Service** (down due to misconfiguration)

Your application might return a degraded response, but worse: your load balancer keeps sending traffic to the **Payment Processing** service, which never recovers. Meanwhile, Kubernetes doesn’t know to restart the stuck container.

This happens because:

- **Health checks often check only the application layer**, not dependencies
- **Probes default to "random" HTTP endpoints** (e.g., `/health`), which might report success even when the container is stuck
- **No distinction between "ready" and "functional"**—a slow service might be marked as ready for traffic

Real-world examples of broken patterns:
```python
# Bad health check (checks only app layer)
@app.route('/health')
def health():
    return "OK"  # Always returns success, even if the database is down
```

```go
// Bad liveness probe (waits too long to detect stuck containers)
func healthHandler(w http.ResponseWriter, r *http.Request) {
    time.Sleep(30 * time.Second) // This gives Kubernetes 30 seconds to see it's "alive"
    w.WriteHeader(http.StatusOK)
}
```

---

## The Solution: Three Types of Verification

To fix this, we need a layered approach:

| Type               | Purpose                                                                 |
|--------------------|-------------------------------------------------------------------------|
| **Endpoints**      | Simple HTTP endpoints for manual verification                           |
| **Liveness Probes**| Kubernetes detects if a container is stuck and needs restarting          |
| **Readiness Probes** | Kubernetes waits for a container to be fully initialized before traffic |
| **Dependencies**   | Check external systems (databases, caches, third-party APIs)             |

Each layer builds on the previous one:

1. **Basic Endpoint**: A simple HTTP check for manual use
2. **Liveness Probe**: Kubernetes-specific check for container recovery
3. **Readiness Probe**: Kubernetes-specific check for traffic routing
4. **Dependency Checks**: Ensure your app can actually fulfill requests

---

## Implementation Guide: Building the Checks

### 1. Basic Health Endpoint (HTTP)

Every service should have a dedicated `/health` endpoint (not `/status` or `/ping`). It should:

- Report **fast** (milliseconds)
- **Not depend** on user-specific data
- **Fail fast** if critical dependencies are down

#### Example in Go

```go
package main

import (
	"net/http"
	"time"
)

var (
	// Simulate dependencies (e.g., database, cache)
	dbHealthy bool
	cacheHealthy bool
)

func initDependencies() {
	// In reality, this would check real dependencies
	dbHealthy = true
	cacheHealthy = true
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	// Fast check (no DB queries)
	select {
	case <-time.After(100 * time.Millisecond):
		// Check dependency health
		if !dbHealthy || !cacheHealthy {
			http.Error(w, "Service dependencies down", http.StatusServiceUnavailable)
			return
		}
		w.WriteHeader(http.StatusOK)
		return
	}
}

func main() {
	http.HandleFunc("/health", healthHandler)
	go initDependencies() // Startup checks
	http.ListenAndServe(":8080", nil)
}
```

#### Example in Python (FastAPI)

```python
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import time

app = FastAPI()

# Simulate dependencies
db_healthy = True
cache_healthy = True

def check_dependencies():
    global db_healthy, cache_healthy
    # Replace with actual checks (e.g., DB ping, cache ping)
    db_healthy = True  # Simulate
    cache_healthy = True  # Simulate

@app.get("/health")
async def health_check():
    if not db_healthy or not cache_healthy:
        return JSONResponse(
            status_code=503,
            content={"error": "Service dependencies down"}
        )
    return {"status": "healthy"}

if __name__ == "__main__":
    check_dependencies()  # Startup checks
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

---

### 2. Liveness Probe (Kubernetes-Specific)

Liveness probes determine if a container **needs to be restarted**. Use them when:

- A container is stuck in a **degraded state** (e.g., waiting for a lock).
- A long-running task **blocks the main thread**.
- A **race condition** causes the app to hang.

#### Key Rules for Liveness Probes:
- Should **detect crashes or hangs**, not gradual degradation.
- Should **fail within 1-5 seconds** (longer delays slow Kubernetes recovery).
- Should **not depend on user data**.

#### Example Kubernetes Liveness Probe (YAML)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-service
spec:
  template:
    spec:
      containers:
      - name: my-service
        image: my-service:latest
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8080
          initialDelaySeconds: 10  # Wait for app to start
          periodSeconds: 5         # Check every 5 seconds
          timeoutSeconds: 2        # Fail fast if >2s
          failureThreshold: 3      # Restart after 3 failed checks
```

#### Go Implementation for `/health/live`

```go
func liveHandler(w http.ResponseWriter, r *http.Request) {
	// Fast check (no DB/cache)
	select {
	case <-time.After(200 * time.Millisecond):
		w.WriteHeader(http.StatusOK)
		return
	}
}
```

#### Python Implementation for `/health/live`

```python
@app.get("/health/live")
async def live_check():
    return {"status": "live"}  # Super fast (no DB checks)
```

---

### 3. Readiness Probe (Kubernetes-Specific)

Readiness probes determine if a container **can handle traffic**. Use them when:

- Your app has **cold starts** (e.g., bootstrapping).
- Initialization takes time (e.g., loading models, caches).
- You want to **avoid sending traffic to partially initialized services**.

#### Key Rules for Readiness Probes:
- Should **wait for full initialization** (e.g., cache warmup).
- Should **fail if critical dependencies are down**.
- Can be **slower than liveness probes** (e.g., 5-10s timeout).

#### Example Kubernetes Readiness Probe

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-service
spec:
  template:
    spec:
      containers:
      - name: my-service
        image: my-service:latest
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8080
          initialDelaySeconds: 20  # Wait for app to initialize
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
```

#### Go Implementation for `/health/ready`

```go
func readyHandler(w http.ResponseWriter, r *http.Request) {
	// Check dependencies + DB queries
	select {
	case <-time.After(500 * time.Millisecond):
		if !dbHealthy || !cacheHealthy {
			http.Error(w, "Dependencies not ready", http.StatusServiceUnavailable)
			return
		}
		w.WriteHeader(http.StatusOK)
		return
	}
}
```

#### Python Implementation for `/health/ready`

```python
@app.get("/health/ready")
async def ready_check():
    if not db_healthy or not cache_healthy:
        return JSONResponse(
            status_code=503,
            content={"error": "Dependencies not ready"}
        )
    return {"status": "ready"}
```

---

### 4. Dependency Checks (Critical!)

Most health checks fail because they **only check the application layer**, not dependencies. Always verify:

- **Databases**: Can you connect? Are queries fast?
- **Caches**: Is the cache warm?
- **Third-party APIs**: Are they responding?
- **External services**: Are they reachable?

#### Example: Database Health Check (PostgreSQL)

```go
import (
	"database/sql"
	_ "github.com/lib/pq"
)

func checkDB() error {
	db, err := sql.Open("postgres", "postgres://user:pass@db:5432/db?sslmode=disable")
	if err != nil {
		return err
	}
	defer db.Close()
	return db.Ping()
}

// Integrate into readiness/live checks
```

#### Example: Cache Health Check (Redis)

```python
import redis

def check_cache():
    r = redis.Redis(host="redis", port=6379)
    try:
        r.ping()
        return True
    except redis.ConnectionError:
        return False
```

---

## Common Mistakes to Avoid

1. **Using `/health` for both liveness and readiness**
   - Liveness should be **super fast** (e.g., `time.Sleep(0)` in the handler).
   - Readiness should check **dependencies**.

2. **Long timeouts in probes**
   - Kubernetes restarts containers based on probe failures. Long timeouts delay recovery.

3. **Ignoring dependency failures**
   - A health check that returns `OK` even when the database is down is useless.

4. **Not testing probes locally**
   - Always test manually:
     ```bash
     curl http://localhost:8080/health/ready
     curl http://localhost:8080/health/live
     ```

5. **Overcomplicating probes**
   - Probes should be **simple** (e.g., `/health/live` = "Is the app running?").

6. **Not updating probes after config changes**
   - If your database host changes, update the readiness probe.

---

## Key Takeaways

✅ **Always implement `/health` endpoints** (manual + automated checks).
✅ **Use `/health/live` for liveness probes** (fast, no dependencies).
✅ **Use `/health/ready` for readiness probes** (checks dependencies).
✅ **Check external dependencies** (databases, caches, APIs).
✅ **Set short timeouts** (2-5s) for probes to avoid delays.
✅ **Test probes locally** before deploying to Kubernetes.
✅ **Fail fast**—let Kubernetes restart stuck containers.
✅ **Avoid sending traffic to slow-but-functional services** (use readiness probes).

---

## Conclusion: Self-Healing Services Start Here

Health checks and probes might seem like "boilerplate," but they’re the **foundation of resilient systems**. Without them, even well-written code can lead to cascading failures.

**Key Actions to Take Now:**
1. Add `/health`, `/health/live`, and `/health/ready` to your service.
2. Configure Kubernetes probes as shown above.
3. Test them locally before deploying.
4. Monitor probe failures in production.

Start small—implement checks for your next feature or deployment. Over time, your services will become **self-healing**, reducing toil and improving reliability.

For further reading:
- [Kubernetes Probes Documentation](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [Resilience Patterns in Distributed Systems](https://resilience4j.readme.io/docs/overview)
- [Chaos Engineering with Gremlin](https://www.gremlin.com/)

Now go make your services **unbreakable**!
```