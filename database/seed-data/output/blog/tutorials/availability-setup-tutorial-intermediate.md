```markdown
# **"Making Your APIs Available When It Matters: The Availability Setup Pattern"**

*How we design systems that stay online when users expect them to—without sacrificing development speed or cost efficiency.*

---

## **Introduction: Why "Just Work" Isn’t Enough Anymore**

Imagine this: You’ve spent months building a scalable payment processing API. Your team has optimized the database, sharded the Redis cluster, and even wrote a custom circuit breaker. On launch day, everything seems perfect—users love it. Then, during Black Friday, your system gracefully degrades under the load, but instead of crashing, it **gracefully fails over** to a backup instance in a different region, routing customers to a slightly slower but fully operational version. Users don’t notice. Your business keeps making money.

This isn’t just bulletproof engineering—this is **availability setup done right**.

But here’s the catch: Most systems *fail* at this. They either:
- Over-engineer availability (costing millions in unused infrastructure), or
- Under-engineer it (crashing under load and losing revenue).

The **"Availability Setup Pattern"** is a practical framework to balance these extremes. It’s not about building a "firewall" around your systems—it’s about designing redundancy, failover, and graceful degradation *into* your architecture, not as an afterthought.

In this guide, we’ll cover:
- The **real-world pain points** that make availability a nightmare if ignored.
- How to **design for availability** (not just "handle failure").
- A **practical breakdown** of the core components: redundancy, monitoring, and failover.
- **Code-first examples** in Python (FastAPI) and Kubernetes, so you can apply this today.
- Common **anti-patterns** that trip up even experienced teams.

Let’s dive in.

---

## **The Problem: When Design Choices Crumble Under Pressure**

Availability isn’t just one thing—it’s the sum of **a thousand small decisions**. Let’s look at how poorly designed systems fail in real-world scenarios.

### **Problem 1: Single Points of Failure Everywhere**
*"Our database was down for 10 minutes during a peak event—our entire service was offline."*
This isn’t hypothetical. A single point of failure (SPOF) can be:
- **Database:** A misconfigured backup job or a corrupted master node.
- **API Gateway:** A single instance handling all traffic (like an unsharded Nginx proxy).
- **Third-Party Dependencies:** A payment provider’s outage halting all transactions.

**Example:** A social media app with a single Redis cache for user sessions. During a DDoS attack, Redis crashes, and the app goes dark for thousands of users.

### **Problem 2: Graceful Degradation Is an Afterthought**
*"We tried to add a fallback, but it broke our whole pipeline."*
Common issues:
- **Uncoordinated failover:** A primary database fails, but the app keeps retrying instead of switching to a replica.
- **No circuit breakers:** A slow third-party API freezes the entire application.
- **Stateful failures:** A crash during a long-running transaction leaves the system in an inconsistent state.

**Example:** An e-commerce site during a sale. The inventory API starts timing out, but the checkout process keeps retrying indefinitely, leading to duplicate orders and angry customers.

### **Problem 3: Monitoring That Doesn’t Help (or Worse, Lies to You)**
*"Our uptime dashboard showed 99.99%, but users were hit with 503s for hours."*
- **Alert fatigue:** Too many false positives (e.g., alerting on disk space *before* it’s critical).
- **No SLOs/SLIs:** Teams optimize for "downtime," not for *user impact*.
- **Black-box monitoring:** Your logs say "success," but users see errors.

**Example:** A SaaS platform where the backend "works" (HTTP 200), but third-party integrations fail silently, causing data inconsistencies.

### **Problem 4: The "It’ll Never Happen to Us" Trap**
*"We tested load once, so we’re good."*
- **Testing ≠ Real-world failure.** A 10-minute spike in traffic behaves differently from a 24-hour outage.
- **Assumptions about dependencies.** "The cloud provider will always auto-scale" is a gamble.
- **No documentation for failure modes.** When things go wrong, devs spend hours debugging instead of fixing.

**Example:** A startup’s API fails during an unexpected regional outage because the team never documented how to manually trigger a failover.

---
## **The Solution: The Availability Setup Pattern**

The **Availability Setup Pattern** is a structured approach to designing systems that:
1. **Detect failure fast** (before users notice).
2. **Failover automatically** (or with minimal human intervention).
3. **Degrade gracefully** (keeping the user experience intact).
4. **Recover cleanly** (without leaving the system in a bad state).

This pattern isn’t about adding "more things"—it’s about **aligning your architecture with failure modes**. Here’s how it works:

| **Component**          | **Purpose**                                                                 | **Example Tools/Techniques**                          |
|------------------------|-----------------------------------------------------------------------------|------------------------------------------------------|
| **Redundancy**         | Ensure no single component is a bottleneck.                                | Multi-AZ databases, clustered message queues         |
| **Monitoring & Alerts**| Catch failures before users do.                                             | Prometheus + Alertmanager, custom health checks      |
| **Failover Logic**     | Switch traffic to healthy instances automatically.                         | Kubernetes `PodDisruptionBudget`, DNS failover       |
| **Graceful Degradation** | Keep the system running (even if slower or with limited features).        | Retry with backoff, fallback endpoints              |
| **State Management**   | Avoid inconsistent states during failures.                                 | Distributed transactions (Saga pattern), idempotency |
| **Disaster Recovery**  | Recover from catastrophic failures.                                         | Backups, geo-replication                           |

---
## **Implementation Guide: Building Availability into Your System**

Let’s walk through a **practical example** using a Python API (FastAPI) and Kubernetes, with availability built in.

### **1. Redundancy: The "No Single Point" Rule**
**Goal:** Ensure no one component can bring the whole system down.

#### **Example: Database Replication**
```sql
-- PostgreSQL primary-replica setup (using `pg_basebackup`)
CREATE EXTENSION IF NOT EXISTS pg_partman;
SELECT pg_create_physical_replication_slot('replica_slot');

-- In `docker-compose.yml`:
services:
  postgres-primary:
    image: postgres
    environment:
      POSTGRES_PASSWORD: secret
    volumes:
      - pg_data:/var/lib/postgresql/data
  postgres-replica:
    image: postgres
    command: >
      postgres -c wal_level=replica
      -c primary_conninfo='host=postgres-primary port=5432 user=postgres password=secret'
      -c replication_slot_name=replica_slot
    depends_on:
      - postgres-primary
```

**Key takeaways:**
- Use **read replicas** for scaling reads.
- Enable **WAL archiving** for disaster recovery.
- Test failover manually (`pg_ctl promote`).

#### **Example: API Gateway Redundancy**
Instead of a single Nginx instance:
```yaml
# Kubernetes Deployment (nginx-gateway)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-gateway
spec:
  replicas: 3  # Multiple instances
  selector:
    matchLabels:
      app: nginx-gateway
  template:
    spec:
      containers:
      - name: nginx
        image: nginx:latest
        ports:
        - containerPort: 80
---
# Service with load balancing
apiVersion: v1
kind: Service
metadata:
  name: nginx-gateway
spec:
  selector:
    app: nginx-gateway
  ports:
    - protocol: TCP
      port: 80
      targetPort: 80
  type: LoadBalancer  # Distributes traffic across pods
```

**Why this works:**
- Traffic is split across 3 pods (no single failure point).
- Kubernetes’ `Selector` ensures only healthy pods receive traffic.

---

### **2. Monitoring: Know Failure Before Users Do**
**Goal:** Detect and alert on failures **before** they impact users.

#### **Example: Health Checks in FastAPI**
```python
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import psycopg2
from prometheus_client import make_wsgi_app, Counter
import prometheus_client

# Metrics
REQUEST_COUNT = Counter('api_request_count', 'Total API requests')
DB_CONNECTIONS = Counter('db_connections_active', 'Active DB connections')

app = FastAPI()

@app.on_event("startup")
async def startup():
    try:
        await test_database_connection()
    except Exception as e:
        raise RuntimeError(f"Database startup failed: {e}")

async def test_database_connection():
    conn = psycopg2.connect("dburl=your_db_url")
    conn.close()

@app.get("/health")
async def health_check():
    return JSONResponse({"status": "healthy"})

@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    REQUEST_COUNT.inc()
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        DB_CONNECTIONS.inc()
        raise HTTPException(status_code=500, detail=str(e))
```

#### **Example: Alerting with Prometheus + Alertmanager**
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'fastapi'
    scrape_interval: 5s
    static_configs:
      - targets: ['localhost:8000']  # Where FastAPI runs

# Alert rules (alert.rules)
groups:
- name: api-alerts
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[1m]) > 0.1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High error rate on API: {{ $labels.instance }}"
      description: "Errors are spiking ({{ $value }}%)."

# Alertmanager config (alertmanager.yml)
route:
  group_by: ['alertname']
  receiver: 'team-slack'
receivers:
- name: 'team-slack'
  slack_api_url: 'https://hooks.slack.com/services/...'
```

**Key takeaways:**
- **Health checks** should be fast (< 1s) and idempotent.
- **Metrics** should track both success and failure rates.
- **Alerts** should be actionable (not just "something is wrong").

---

### **3. Failover Logic: Switch Traffic When Things Break**
**Goal:** Automatically route traffic to healthy instances.

#### **Example: Kubernetes Pod Disruption Budget**
```yaml
# Ensures at least 2 pods are always up during voluntary disruptions (e.g., scaling)
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: api-pdb
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: fastapi-app
```

#### **Example: Database Failover with PgBouncer**
```ini
# pgbouncer.ini
[databases]
your_db = host=postgres-primary port=5432 dbname=your_db

[pgbouncer]
listen_addr = *
listen_port = 6432
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction

# userlist.txt
"replica_user" "secret" "host=postgres-replica port=5432 dbname=your_db"
```

**How this works:**
- PgBouncer routes queries to the primary by default.
- If the primary fails, it automatically switches to the replica (if configured).

**FastAPI + PgBouncer Connection Pooling:**
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Connects to PgBouncer instead of direct DB
DATABASE_URL = "postgresql://replica_user:secret@pgbouncer:6432/your_db"
engine = create_engine(DATABASE_URL, pool_pre_ping=True)  # Checks liveness
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

---

### **4. Graceful Degradation: Keep the System Running**
**Goal:** Limit impact when failures happen.

#### **Example: Circuit Breaker in FastAPI**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

# Retry a slow external API with exponential backoff
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def call_external_api():
    response = requests.get("https://slow-api.example.com/data")
    return response.json()

@app.get("/slow-data")
async def get_slow_data():
    try:
        return {"data": call_external_api()}
    except Exception:
        return {"fallback": "cache_data"}, 200  # Serve stale data
```

#### **Example: Fallback Endpoint for Third-Party Failures**
```python
# FastAPI with fallback logic
@app.get("/payments/process")
async def process_payment(amount: float):
    try:
        # Try primary payment provider
        result = primary_payment_provider.charge(amount)
        if result["status"] == "success":
            return {"status": "paid"}
    except Exception as e:
        # Fallback to Stripe if primary fails
        try:
            stripe_result = stripe.charge(amount)
            return {"status": "paid (fallback)"}
        except Exception as stripe_e:
            return {"status": "error", "details": str(stripe_e)}, 500
```

**Key takeaways:**
- **Retry with backoff** (never retry forever).
- **Fallback to stale data** (cache > none).
- **Isolate failures** (don’t let one API call crash the whole request).

---

### **5. State Management: Avoid Inconsistent Failures**
**Goal:** Never leave the system in a bad state.

#### **Example: Idempotent API Endpoints**
```python
from fastapi import HTTPException

# Example: Payment processing with idempotency
idempotency_keys = {}

@app.post("/payments")
async def create_payment(
    amount: float,
    idempotency_key: str,
    request: Request
):
    if idempotency_key in idempotency_keys:
        return {"status": "already processed"}, 200

    idempotency_keys[idempotency_key] = True
    try:
        payment = process_payment(amount)
        return {"status": "completed"}
    except Exception as e:
        # Cleanup on failure
        del idempotency_keys[idempotency_key]
        raise
```

#### **Example: Distributed Transactions with Saga Pattern**
```python
# Saga for order processing: Inventory -> Payment -> Notification
async def process_order(order_id: str):
    try:
        # Step 1: Reserves inventory
        await reserve_inventory(order_id)
        # Step 2: Processes payment
        await process_payment(order_id)
        # Step 3: Sends confirmation
        await send_confirmation(order_id)
    except Exception as e:
        # Compensating transactions
        await release_inventory(order_id, "Order failed: %s" % e)
        raise
```

---

## **Common Mistakes to Avoid**

1. **"We’ll Handle Failures Later"**
   - **Mistake:** Adding availability as an afterthought (e.g., "Deploy Kubernetes *after* the API works").
   - **Fix:** Design for failure from the start. Use **postmortem checklists** for every new feature.

2. **Over-Reliance on "Cloud Auto-Healing"**
   - **Mistake:** Assuming Kubernetes or AWS will magically recover from failures.
   - **Fix:** Test failover manually. Use tools like [`kubectl drain`](https://kubernetes.io/docs/concepts/workloads/pods/pod-drain/) to simulate node failures.

3. **No Monitoring for "Happy Path" Failures**
   - **Mistake:** Only alerting on errors, not on performance degradation (e.g., slow DB queries).
   - **Fix:** Monitor **latency percentiles (p99, p95)** and set alerts for anomalies.

4. **Inconsistent State on Failures**
   - **Mistake:** Not handling retries, timeouts, or compensating transactions.
   - **Fix:** Design for **idempotency** and **saga patterns**.

5. **Ignoring Cost of High Availability**
   - **Mistake:** Building a 99.999% SLA system for a startup with low traffic.
   - **Fix:** Start with **SLOs (Service Level Objectives)**. Example:
     ```
     - 99.9% uptime for critical APIs
     - 95% latency < 200ms
     ```

6. **No Documentation for Failure Modes**
   - **Mistake:** Assuming devs will "know" how to recover from a primary DB failure.
   - **Fix:** Write a **runbook** for each failure scenario. Example:
     ```
     [Primary DB Failure]
     1. Check if replica is promoting automatically (if not, run `pg_ctl promote`).
     2. Restart PgBouncer to switch traffic.
     3. Monitor replica lag with `pg_stat_replication`.
     ```

---

## **Key Takeaways: The Availability Setup Checklist**

✅ **Redundancy First:**
   - Multi-AZ databases, clustered services.
   - Test failover manually (**don’t just assume it works**).

✅ **Monitor Everything:**
   - Track errors, latency, and resource usage.
   - Alert on **anomalies**, not just failures.

✅ **Fail Fast, Recover Faster:**
   - Use circuit breakers, retries with backoff.
   - Design for **graceful degradation** (stale data > no data).

✅ **Manage State Carefully:**
   - Idempotency for API calls.
   - Saga pattern for distributed transactions.

✅ **Document Failures:**
   - Write runbooks for **every** failure scenario.
   - Include **postmortem templates** for incident response.

✅ **Balance Cost and Reliability:**
   - Start with **SLOs**, not "perfect availability."
   - Optim