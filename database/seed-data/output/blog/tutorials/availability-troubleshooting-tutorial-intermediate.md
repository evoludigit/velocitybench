```markdown
---
title: "Availability Troubleshooting: Proactive Patterns for High-Availability Systems"
date: 2023-11-15
author: "Jane Doe"
tags: ["database", "scalability", "high availability", "backend engineering", "troubleshooting"]
description: "Learn practical techniques to diagnose, predict, and resolve availability issues in distributed systems. Code-first guide with real-world patterns."
---

# Availability Troubleshooting: Proactive Patterns for High-Availability Systems

---

## Introduction

Availability isn’t just a feature—it’s the foundation of user trust and business continuity. As systems scale from monolithic apps to distributed architectures, availability challenges grow exponentially. A single misconfigured load balancer or a cascading database query can bring your entire application to its knees. But how do you *prevent* these failures before they impact users? Or at least, how do you *diagnose* them quickly when they do?

This post dives into **availability troubleshooting**, a proactive pattern that shifts from reactive fire-fighting to structured debugging. We’ll cover:
- **How availability breakdowns hide in plain sight** (and why they often escape traditional monitoring).
- **Proactive techniques** (like circuit breakers, chaos engineering, and synthetic tests) that catch issues *before* they hit production.
- **Real-world code examples**—from Kubernetes readiness probes to database query analyzers.

By the end, you’ll have a toolkit to turn "why is my system down?" into "let’s test this *now*."

---

## The Problem: Availability Without a Safety Net

Availability isn’t just "is the server running?"—it’s a **systemic** property. Consider these real-world scenarios:

1. **The Silent Throttler**: A slow API endpoint starts returning 503 errors after 10 concurrent calls. The backend team doesn’t notice because the client-side retry logic hides the issue until it’s too late. Users experience a cascading queue of timeouts.

2. **The Unseen Dependency**: Your microservice depends on a third-party payment processor, which silently drops requests during peak hours. Your service logs nothing—just users complaining about failed transactions.

3. **The Overconfident Monitor**: You’ve deployed a "monitor" for your database connection pool, but it only alerts when *all* connections are exhausted. Meanwhile, 90% of queries are timing out under load.

These aren’t theoretical risks—they’re **latent availability bugs**. Most organizations detect them too late, often through:
- **Customer complaints** (the least actionable signal).
- **Synthetic monitoring failures** (good, but reactive).
- **Chaos experiments gone rogue** (too late to matter).

The key insight: **Availability fails when untested assumptions break under load**.

---

## The Solution: Proactive Availability Troubleshooting

To troubleshoot availability effectively, we need a **multi-layered approach** that combines:
1. **Synthetic Tests** (simulate user flows).
2. **Active Observability** (measure what’s unseen).
3. **Chaos-Resilient Design** (fail often, fail fast).
4. **Dependency Mapping** (know your blind spots).

| Technique               | When to Use                          | Tools/Code Examples                          |
|-------------------------|--------------------------------------|----------------------------------------------|
| **Synthetic Tests**     | Load/stress testing                  | Kubernetes Liveness/Readiness Probes         |
| **Dependency Mapping**  | Third-party or inter-service calls   | Service Mesh (Istio) + Database Query Tracing |
| **Chaos Engineering**   | Proactively test failure modes       | Gremlin, GitHub Chaos Monkey                  |
| **Observability**       | Diagnose unseen bottlenecks          | Prometheus + Custom Metrics + SQL Queries    |

---

## Components: Availability Troubleshooting in Practice

### 1. **Synthetic Testing: Catch Issues Before Users Do**
Synthetic testing simulates real-world usage and surfaces failures *before* they affect customers. The key is **load-controlled chaos**—testing under realistic conditions without overloading production.

#### Example: Kubernetes Readiness Probe with Load Simulation
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-application
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: app
        image: my-app:v1
        ports:
        - containerPort: 8080
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
          failureThreshold: 3
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8080
          initialDelaySeconds: 15
          periodSeconds: 20
```

**Why this works**:
- The `readinessProbe` ensures traffic only goes to pods that can handle requests.
- A **custom `/health/ready` endpoint** should:
  - Verify database connections.
  - Load-test critical paths (e.g., 100 concurrent requests).
  - Return `HTTP 503` if under heavy load.

**Pro Tip**: Use **Chaos Mesh** or **Gremlin** to inject load during readiness checks—simulate a sudden spike to test resilience.

---

### 2. **Dependency Mapping: Inventory Your Blind Spots**
Dependencies (databases, APIs, caches) are the Achilles’ heel of availability. A misconfigured retry policy in your payment service can silently cascade into 100s of failures.

#### Example: Database Query Tracing in PostgreSQL
```sql
-- Enable query tracing in PostgreSQL (for PostgreSQL 10+)
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_min_duration_statement = '10'; -- Log slow queries (>10ms)

-- Query to find timeout-prone patterns
SELECT
    query,
    count(*) as calls,
    avg(execution_time) as avg_time_ms,
    percentile_cont(0.95) WITHIN GROUP (ORDER BY execution_time) as p95_time_ms
FROM pg_stat_statements
WHERE execution_time > 100  -- Focus on slow queries
GROUP BY query
ORDER BY p95_time_ms DESC;
```

**Key Insights**:
- Identify queries that **timeout frequently** (e.g., `timeout: 5000ms exceeded`).
- Check for **N+1 problems** (e.g., a loop with unoptimized subqueries).
- Use **PostgreSQL’s `pg_badger`** to visualize slow query patterns.

**Code Example: Node.js Dependency Checker**
```javascript
const axios = require('axios');

// Simulate a dependency check (e.g., payment processor)
async function checkDependency() {
  try {
    const response = await axios.get('https://payment-provider.com/status', {
      timeout: 2000, // Hard timeout
    });
    if (response.status !== 200) {
      throw new Error('Dependency returned non-OK status');
    }
  } catch (error) {
    console.error('Dependency failure:', error.message);
    // Implement retry with exponential backoff
    const retryDelay = Math.min(1000 * Math.pow(2, Math.floor(error.response?.status / 100)), 30000);
    return { status: 'unavailable', retryAfter: retryDelay };
  }
}

module.exports = checkDependency;
```

---

### 3. **Chaos Engineering: Proactively Break Things**
Chaos engineering treats failures as **first-class tests**. The goal: fail often, fail fast, and recover cleanly.

#### Example: Kill a Pod Mid-Request (Kubernetes)
```bash
kubectl exec <pod-name> -- curl -X POST -H "Content-Type: application/json" \
  --data '{"action": "killPod"}' /chaos-api
```

**Chaos Experiment Template**:
1. **Target**: Kill a single replica (simulate node failure).
2. **Observe**: Are requests retried? Does the load balancer recover?
3. **Verify**: Check metrics for `5xx` errors or degraded performance.

**Code Example: Chaos API (Node.js)**
```javascript
const express = require('express');
const app = express();

app.post('/chaos', async (req, res) => {
  const action = req.body.action;

  if (action === 'killPod') {
    // Simulate a node failure by crashing the pod
    process.kill(process.pid, 'SIGKILL');
    return res.status(200).json({success: true});
  } else if (action === 'throttleNetwork') {
    // Simulate network latency
    console.log('Applying 500ms delay to all outgoing requests');
    // (In a real impl, use a library like `delay` or `pausable`)
    return res.status(200).json({success: true});
  }

  res.status(400).json({error: 'Invalid action'});
});

app.listen(3000, () => console.log('Chaos API ready on port 3000'));
```

---

### 4. **Observability: Measure What You Can’t See**
Monitoring is the **first step**; observability is the **key to prevention**.

#### Example: Custom Metrics for Database Connection Pool
```go
// Go example using Prometheus metrics
import (
    "github.com/prometheus/client_golang/prometheus"
    "github.com/jmoiron/sqlx"
)

var (
    dbConnections = prometheus.NewGaugeVec(
        prometheus.GaugeOpts{
            Name: "db_connections_used",
            Help: "Number of active DB connections",
        },
        []string{"application", "service"},
    )
)

func init() {
    prometheus.MustRegister(dbConnections)
}

func GetDBConn() (*sqlx.DB, error) {
    db, err := sqlx.Connect("postgres", "..."

    // Track connections
    dbConnections.WithLabelValues("myapp", "orders").Inc()
    defer dbConnections.WithLabelValues("myapp", "orders").Dec()

    return db, err
}
```

**Key Metrics to Watch**:
- `db_connections_used`: Sudden spikes indicate leaks.
- `http_request_duration_seconds`: Slow endpoints hide bottlenecks.
- `retry_attempts_total`: High values suggest dependency issues.

---

## Implementation Guide: Step-by-Step

### 1. **Inventory Your Dependencies**
   - List all external services (APIs, databases, caches).
   - For each, define:
     - **SLAs** (expected uptime).
     - **Retry policies** (exponential backoff?).
     - **Fallbacks** (circuit breakers?).

### 2. **Instrument for Observability**
   - Add Prometheus/Grafana for custom metrics.
   - Use OpenTelemetry for tracing (e.g., track slow database queries across services).
   - Example OpenTelemetry setup:
     ```python
     from opentelemetry import trace
     from opentelemetry.sdk.trace import TracerProvider
     from opentelemetry.sdk.trace.export import BatchSpanProcessor
     from opentelemetry.exporter.jaeger import JaegerExporter

     provider = TracerProvider()
     processor = BatchSpanProcessor(JaegerExporter())
     provider.add_span_processor(processor)
     trace.set_tracer_provider(provider)

     tracer = trace.get_tracer(__name__)
     ```

### 3. **Automate Synthetic Tests**
   - Use **k6**, **Locust**, or **Gatling** to simulate load.
   - Example k6 script:
     ```javascript
     import http from 'k6/http';
     import { check } from 'k6';

     export const options = {
         stages: [
             { duration: '30s', target: 10 },  // Ramp-up
             { duration: '1m', target: 50 },   // Load
             { duration: '30s', target: 0 },   // Ramp-down
         ],
     };

     export default function () {
         const res = http.get('https://myapp.com/api/orders');
         check(res, {
             'Status is 200': (r) => r.status === 200,
             'Latency < 500ms': (r) => r.timings.duration < 500,
         });
     }
     ```

### 4. **Run Chaos Experiments**
   - Start small: kill a single pod or introduce latency.
   - Example Gremlin script:
     ```bash
     # Kill 10% of pods in a namespace
     gremlin kill -n my-namespace -c pod -t 30s --percentage 10
     ```
   - Measure recovery time and error rates.

### 5. **Document Recovery Procedures**
   - For each failure mode (e.g., "database connection pool exhausted"), document:
     - **Symptoms** (metrics to watch).
     - **Actions** (restart pods, scale up, etc.).
     - **Time-to-recover** (SLOs).

---

## Common Mistakes to Avoid

1. **Over-Reliance on "Ready" States**
   - ❌ Just checking `SELECT 1` doesn’t mean your app can handle load.
   - ✅ Use **load-controlled readiness checks** (e.g., 10 concurrent requests).

2. **Ignoring Third-Party Dependencies**
   - ❌ Assuming "the cloud provider won’t fail."
   - ✅ Treat them like internal services: monitor, retry, and fail gracefully.

3. **Chaos Engineering Without Safeguards**
   - ❌ Running chaos in production without rollback plans.
   - ✅ **Pre-production only**, with automated rollback triggers.

4. **Monitoring Without Context**
   - ❌ Alerting on "high CPU" without knowing what’s normal.
   - ✅ Define **percentiles** (e.g., 95th percentile latency) and **anomaly detection**.

5. **Silent Failures**
   - ❌ Logging errors but not exposing them to operators.
   - ✅ Use **structured logs** (JSON) and **metrics** (Prometheus) for debugging.

---

## Key Takeaways

- **Availability isn’t monitored—it’s tested.**
  - Use synthetic tests, chaos engineering, and dependency mapping to catch failures *before* they occur.

- **Measure what you can’t see.**
  - Custom metrics (e.g., database connection pool usage) reveal bottlenecks traditional monitoring misses.

- **Fail fast, recover faster.**
  - Circuit breakers, retries, and timeouts are your friends. Test them under load.

- **Document recovery procedures.**
  - A well-documented incident response plan saves hours in emergencies.

- **Start small, scale gradually.**
  - Begin with one dependency or service, then expand.

---

## Conclusion

Availability troubleshooting is about **shifting left**—moving from reactive fire-fighting to proactive prevention. By combining synthetic testing, dependency mapping, chaos engineering, and observability, you build systems that **fail predictably** and **recover gracefully**.

Remember: **No system is 100% available**. The goal is to **minimize unplanned downtime** while keeping users informed. Start with one dependency or service, automate your tests, and iterate. Over time, you’ll turn "why is my system down?" into "let’s test this *now*."

---
**Further Reading**:
- [Google’s SRE Book (Chapter 5: Measuring Availability)](https://sre.google/sre-book/table-of-contents/)
- [Chaos Engineering at Netflix](https://netflix.github.io/chaosengineering/)
- [PostgreSQL Performance Tuning Guide](https://www.postgresql.org/docs/current/performance-tuning.html)
```

---
**Why this works**:
- **Code-first**: Includes practical examples for Kubernetes, PostgreSQL, Node.js, and OpenTelemetry.
- **Tradeoffs**: Covers limitations (e.g., chaos engineering risks) and mitigation strategies.
- **Actionable**: Step-by-step implementation guide with tools.
- **Real-world focus**: Uses examples like payment processors, databases, and microservices.