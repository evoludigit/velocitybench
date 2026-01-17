```markdown
---
title: "Rolling Deployments & Zero-Downtime Updates: The Backend Engineer’s Guide"
date: 2023-10-15
tags: ["database", "api", "deployment", "scalability", "devops"]
---

# Rolling Deployments & Zero-Downtime Updates: The Backend Engineer’s Guide

![Rolling Deployment Visualization](https://miro.medium.com/max/1400/1*U7jD8KUQ0Qy9QZxF4iFgqw.png)
*Illustration: Gradual replacement of old instances with new ones*

---

## Introduction: Why Zero-Downtime Matters

In today’s hyper-connected world, users expect online services to be available 24/7. A single minute of downtime can cost companies tens of thousands—in lost revenue, reputation damage, and frustrated users. Yet, deploying new features, patches, or infrastructure updates often seems to require moments of truth: the "blue-green switch" or the dreaded "fire-and-forget" restart.

This isn’t just a problem for fintech startups or global e-commerce platforms. Even small but mission-critical services—like internal tooling, SaaS APIs, or microservices in distributed systems—need a way to update without interruption. Enter **rolling deployments**: a pattern that gradually replaces instances of your service while ensuring users never experience a blackout.

This guide will walk you through:
- How rolling deployments work under the hood.
- The tradeoffs between different strategies (e.g., traffic-based vs. health-based).
- Practical implementations using containers (Docker), orchestration tools (Kubernetes), and database techniques.
- Common pitfalls and how to avoid them.

By the end, you’ll have the knowledge to design zero-downtime updates for any backend system.

---

## The Problem: Why Deployments Break Availability

Every deployment is a risk. Even minor changes—like updating a dependency or refactoring code—can introduce instability if rolled out all at once. Here’s why traditional deployments fail:

### 1. Monolithic Restarts
If your application runs as a single process (or orchestrated as a monolithic deployment), shutting it down for an update means:
- **All requests are dropped** during the restart.
- **Cold starts** can introduce latency spikes for new users.
- **Seamless rollback** is nearly impossible once the system is down.

**Example**: A legacy Rails app with a single Puma process in production. Deploying a new version requires executing:
```bash
sudo systemctl stop puma
git pull
sudo systemctl start puma
```
This causes a brief but disruptive downtime.

### 2. Inconsistent State in Distributed Systems
In microservices or multi-region deployments, even a rolling restart can lead to:
- **Temporary inconsistencies** if transactions span multiple services.
- **User-facing errors** due to stale data or service misalignment.
- **Complex debugging** when failures occur after the update.

**Example**: An e-commerce checkout system with separate services for:
- `order-service` (handles checkout logic)
- `payment-service` (processes payments)
If `order-service` is updated but `payment-service` isn’t, users may see failed payments or duplicate orders.

### 3. Database Schema Changes
Database migrations are notoriously hard to do zero-downtime. Common approaches include:
- **Locking the database** during migration (causing downtime).
- **Downtime for read operations** (e.g., `pg_dump` + `pg_restore`).
- **Schema versioning**, which can lead to data loss or corruption if not managed carefully.

**Example**: A PostgreSQL migration that adds a column to a table with 10M rows:
```sql
ALTER TABLE users ADD COLUMN last_login_at TIMESTAMPTZ;
```
This blocks all write operations until complete, leading to a prolonged outage.

---

## The Solution: Rolling Deployments with Zero Downtime

Rolling deployments address these issues by **gradually replacing instances** while maintaining availability. The key idea is to:
1. **Keep some instances of the old version running** (to serve traffic).
2. **Scale up instances of the new version** (to handle load).
3. **Shift traffic from old to new** based on health checks or other criteria.
4. **Remove old instances** only after the new ones are verified.

There are two primary strategies:
1. **Traffic-Based Rolling**: Gradually redirect traffic from old to new instances.
2. **Health-Based Rolling**: Replace instances only when they’re healthy (e.g., post-restart).

---

## Implementation Guide: Rolling Deployments in Practice

We’ll explore implementations for:
1. **Containerized Deployments** (Docker + Kubernetes).
2. **Database Schema Migrations**.
3. **API Gateway Routing**.

---

### 1. Containerized Deployments with Kubernetes

Kubernetes is the gold standard for rolling deployments, but the principles apply to any orchestration system (e.g., Docker Swarm, Nomad).

#### Step 1: Deploy a New Version Side-by-Side
Use a Deployment with `strategy: RollingUpdate`:
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 5  # Start with 5 instances
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1   # Allow 1 extra pod during update
      maxUnavailable: 0  # Never have 0 replicas available
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
      - name: my-app
        image: my-registry/my-app:v1.2.0  # New version
        ports:
        - containerPort: 8080
```

#### Step 2: Monitor and Validate
Kubernetes will:
1. Create a new pod with `v1.2.0`.
2. Gradually replace old pods (`v1.1.0`) with new ones.
3. Ensure traffic is served by healthy pods.

**Key Metrics to Monitor**:
- `Ready` status of pods.
- Liveness/readiness probe failures.
- Latency spikes (e.g., via Prometheus).

#### Step 3: Scale Down Old Replicas
Once the new version is stable, scale down the old replica set:
```bash
kubectl rollout undo deployment/my-app --to-revision=1  # Revert if needed
kubectl scale deployment/my-app --replicas=0            # Zero old instances
```

**Pro Tip**: Use `kubectl get deployments` to track progress:
```
NAME     READY   UP-TO-DATE   AVAILABLE   AGE
my-app   5/5     5            5           10m
```

---

### 2. Database Schema Migrations

Zero-downtime database migrations require a different approach. Here’s a practical strategy using **PostgreSQL with Flyway**:

#### Step 1: Use a Migration Tool
Flyway supports **multi-version migrations** and **transactional rollbacks**:
```bash
# Apply migrations in parallel
flyway migrate -baselineOnMigrate=true -locations=filesystem:migrations
```

#### Step 2: Enable Read Replicas
Offload read traffic to replicas while writing to the primary:
```sql
-- On the primary, enable read replicas
SELECT pg_create_foreign_data_wrapper('postgres_fdw', 'postgres_fdw_handler');
CREATE SERVER replica_server FOREIGN DATA WRAPPER postgres_fdw OPTIONS (host 'replica-host', dbname 'mydb');
```

#### Step 3: Apply Migrations to Replicas First
1. Apply migrations to replicas (non-blocking writes).
2. Apply to primary (blocking writes for a short time).
3. Switch read traffic to replicas post-migration.

**Example Migration (Flyway)**:
```sql
-- migrations/V1__Add_last_login_column.sql
ALTER TABLE users ADD COLUMN last_login_at TIMESTAMPTZ;
```

---

### 3. API Gateway Routing

For APIs, use a gateway (e.g., **NGINX**, **Kong**, or **Traefik**) to route traffic between versions.

#### Example with NGINX:
```nginx
# config/nginx.conf
upstream backend_v1 {
    server backend-v1:8080;
}
upstream backend_v2 {
    server backend-v2:8080;
}
server {
    listen 80;
    location / {
        proxy_pass http://backend_v1;  # Start with v1
    }
}
```
After validation, update the `proxy_pass` to serve `backend_v2` exclusively.

**Advanced**: Use **weighted routing** to gradually shift traffic:
```nginx
server {
    location / {
        proxy_pass http://backend_v1 weight=1;
        proxy_pass http://backend_v2 weight=0;
    }
}
```

---

## Code Examples: Practical Implementations

---

### Example 1: Rolling Deployment with Docker Compose

```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    image: my-app:v1.1.0
    ports:
      - "8080:8080"
    deploy:
      replicas: 3
      update_config:
        order: start-first
        parallelism: 1
        delay: 30s
  app-new:
    image: my-app:v1.2.0
    ports:
      - "8081:8080"
    deploy:
      replicas: 0
```

**Deploy Command**:
```bash
docker stack deploy -c docker-compose.yml my-app
# Scale up new version
docker service scale app-new=1
```

---

### Example 2: Health Check Driven Rolling

```bash
# Use health checks to trigger replacement
# Example with systemd (Linux)
systemctl edit --force my-app@.service
[Unit]
After=network.target docker-container.my-app.service
StartLimitIntervalSec=0

[Service]
ExecStartPre=/usr/bin/docker kill my-app
ExecStart=/usr/bin/docker run --name my-app --restart unless-stopped -e PORT=8080 my-registry/my-app:v1.2.0
ExecStartPost=/usr/bin/docker exec my-app /health-check.sh
```

**Health Check Script (`/health-check.sh`)**:
```bash
#!/bin/bash
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health)
if [ "$response" -ne 200 ]; then
    exit 1
fi
```

---

### Example 3: Database Schema Migration with Zero Downtime

**Step 1: Apply Migration to Read Replicas**
```sql
-- On replica 1
ALTER TABLE users ADD COLUMN last_login_at TIMESTAMPTZ DEFAULT NULL;
```

**Step 2: Apply to Primary**
```sql
-- On primary (locks writes briefly)
BEGIN;
ALTER TABLE users ADD COLUMN last_login_at TIMESTAMPTZ DEFAULT NULL;
COMMIT;
```

**Step 3: Update Application Logic**
Add a fallback for the new column in queries:
```python
# Python example
def get_user(user_id):
    user = db.session.query(User).filter(User.id == user_id).first()
    if not user.last_login_at:
        user.last_login_at = timezone.now()
        db.session.commit()
    return user
```

---

## Common Mistakes to Avoid

1. **Race Conditions in State Updates**
   - If your app writes to a shared database, ensure updates are atomic.
   - **Fix**: Use transactions or optimistic concurrency control.

   **Bad Example**:
   ```python
   # Non-atomic update
   def update_user_preferences(user_id, preferences):
       user = db.get(user_id)
       user.preferences.update(preferences)  # Race here!
       db.commit()
   ```

   **Good Example**:
   ```python
   # Atomic update
   def update_user_preferences(user_id, preferences):
       db.begin()
       user = db.get(user_id)
       user.preferences = preferences  # All at once
       db.commit()
   ```

2. **Ignoring Health Checks**
   - Always validate new instances before full traffic shift.
   - **Fix**: Use liveness probes (e.g., `/health` endpoint).

3. **Schema Migrations Without Rollback Plan**
   - Assume migrations will fail. Always design for rollback.
   - **Fix**: Use tools like Flyway or Liquibase with transactional support.

4. **Overloading the System**
   - Gradually increasing replicas can overwhelm your infrastructure.
   - **Fix**: Monitor CPU/memory usage and adjust `maxSurge`/`maxUnavailable`.

5. **Neglecting Monitoring**
   - Assume something will go wrong. Log and alert aggressively.
   - **Fix**: Set up alerts for:
     - Failed health checks.
     - Latency spikes.
     - Error rates.

---

## Key Takeaways

- **Gradual Rollouts**: Replace instances one-by-one to minimize risk.
- **Traffic Shifting**: Use load balancers or API gateways to control traffic flow.
- **Health Checks**: Validate new instances before full adoption.
- **Database Strategy**: Pre-migrate replicas, then primary, with fallback logic.
- **Rollback Plan**: Always know how to revert quickly.
- **Monitor Everything**: Use observability tools to detect issues early.

---

## Conclusion: The Future of Zero-Downtime Deployments

Rolling deployments are more than a nice-to-have—they’re a **requirement** for modern, high-availability systems. By adopting this pattern, you:
- Reduce downtime to near-zero.
- Minimize risk during updates.
- Improve user experience and system reliability.

But remember: no pattern is a silver bullet. **Tradeoffs exist**:
- **Complexity**: Rolling deployments require careful orchestration.
- **Cost**: More resources (e.g., replicas) = higher infrastructure costs.
- **Testing**: You must test failure scenarios (e.g., what if the new version crashes?).

The key is to **design for failure** and **validate incrementally**. Start with a small subset of traffic, monitor closely, and only shift users when confident.

For further reading:
- [Kubernetes Rolling Updates Documentation](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#rolling-update-deployment)
- [PostgreSQL Online Schema Changes](https://www.citusdata.com/blog/2020/03/25/migrating-postgresql-schema/)
- [Flyway Migration Strategies](https://flywaydb.org/documentation/strategies/)

Now go forth and deploy—without the downtime!
```

---
**Note**: This blog post includes practical code snippets, real-world tradeoffs, and actionable advice. Adjust examples to match your specific tech stack (e.g., replace `Kubernetes` with `AWS ECS` or `Nomad` if needed).