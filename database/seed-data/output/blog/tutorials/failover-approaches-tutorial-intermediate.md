```markdown
---
title: "Failover Approaches: Building Resilient Systems"
author: "Maxime Moreau"
date: "June 15, 2024"
category: ["Backend", "Database", "API Design"]
tags: ["failover", "high availability", "database design", "API resilience", "resilience patterns"]
description: "Learn about failover approaches in backend systems, including manual, automatic, and hybrid strategies. Practical code examples and implementation guidance for building resilient APIs and databases."
---

# Failover Approaches: Building Resilient Systems

![Failover Pattern Diagram](https://via.placeholder.com/500x300?text=Failover+Approach+Flowchart)

A few years ago, I was working on a SaaS platform that experienced a major outage when our primary database server failed. The recovery took hours, and during that time, we lost thousands of user transactions. That experience taught me the hard way that **failover isn't optional—it's a necessity**.

In this post, we'll explore **failover approaches**—the strategies you can use to ensure your backend systems remain available even when components fail. We'll cover **manual, automatic, and hybrid failover**, discuss tradeoffs, and provide practical code examples for implementing these patterns in real-world scenarios.

---

## The Problem: Why Failover Matters

Imagine you're running an e-commerce platform. During Black Friday, your primary database server crashes. If you don’t have a failover strategy, every transaction will fail, and customers will see errors like:

```
502 Bad Gateway
Database server unavailable
```

This isn’t just bad for the user experience—it can cost your business **tens of thousands per minute** in lost revenue. Even for non-e-commerce apps, downtime means lost trust, reduced API uptime, and potential compliance violations (e.g., GDPR requires high availability).

### Common Failures That Require Failover
- **Database crashes** (e.g., MySQL server dies, PostgreSQL crashes).
- **Server hardware failures** (e.g., a node in your Kubernetes cluster goes down).
- **Network partitions** (e.g., AWS AZ outage).
- **External API failures** (e.g., Stripe payment gateway unresponsive).

Without failover, your system becomes a **single point of failure**, and resilience collapses under pressure.

---

## The Solution: Failover Approaches

Failover is the process of automatically (or manually) switching from a primary component to a backup when the primary fails. There are **three main failover approaches**, each with tradeoffs:

1. **Manual Failover** – Human intervention is required to switch systems.
2. **Automatic Failover** – The system detects failure and switches automatically.
3. **Hybrid Failover** – A mix of manual and automatic, with human oversight for critical decisions.

We’ll explore each in detail, with code examples for databases and APIs.

---

## Components of Failover Systems

Before diving into approaches, let’s define the key components:

1. **Primary Node** – The currently active instance (e.g., primary database, primary API endpoint).
2. **Replica/Standby** – A synchronized backup that can take over if the primary fails.
3. **Monitoring System** – Detects failures (e.g., Prometheus, custom health checks).
4. **Failover Trigger** – Decides when to switch (e.g., health checks, replication lag).
5. **Orchestrator** – Handles the switch (e.g., Kubernetes, manual intervention).

---

## 1. Manual Failover: When Humans Take Control

Manual failover is the simplest approach but also the most error-prone. It involves a human operator detecting a failure and manually promoting a standby instance.

### When to Use
- Small teams where automation isn’t worth the effort.
- Critical systems where over-automation might lead to unintended failures.

### Example: MySQL Manual Failover

Here’s how you might manually failover a MySQL master-slave setup:

```sql
-- On the current master, promote a slave to master
mysql> STOP SLAVE;
mysql> SET GLOBAL read_only=OFF;
mysql> SET GLOBAL super_read_only=OFF;
mysql> SET GLOBAL innodb_fast_shutdown=0;
mysql> FLUSH TABLES WITH READ LOCK;
mysql> RENAME TABLE some_table TO some_table_old;
mysql> UNLOCK TABLES;

-- On the new master, reconfigure slave to replicate from the old master (now slave)
mysql> CHANGE MASTER TO MASTER_HOST='old-master', MASTER_USER='repl_user', MASTER_PASSWORD='password';
mysql> START SLAVE;
```

### Pros & Cons
| **Pros** | **Cons** |
|----------|----------|
| Simple to implement | Human error risk |
| Full control over failure handling | Downtime during manual intervention |
| No need for complex orchestration | Not suitable for high-traffic systems |

### Code Example: API Manual Failover with Load Balancer
If your API has multiple instances, you can manually switch traffic using a load balancer (e.g., Nginx):

```nginx
# Current setup: backend1 is primary
upstream api_nodes {
    server backend1:8080;
    server backend2:8080 backup;
}

# After failure, update to promote backend2
upstream api_nodes {
    server backend2:8080;
    server backend1:8080 backup;
}
```

---

## 2. Automatic Failover: Let the System Handle It

Automatic failover reduces downtime by switching to a standby instance without human intervention. This is ideal for **high-availability systems** (e.g., production APIs, databases).

### When to Use
- Critical systems where downtime is unacceptable.
- Systems with preconfigured replicas.
- When automation can detect failures faster than humans.

### Example: PostgreSQL Automatic Failover with Patroni

[Patroni](https://patroni.readthedocs.io/) is a tool for automatic failover in PostgreSQL. Here’s a sample config:

```yaml
# patroni.yml
scope: myapp_db
namespace: /service/app
restapi:
  listen: 0.0.0.0:8008
  connect_address: 0.0.0.0:8008
etcd:
  hosts: etcd1:2379,etcd2:2379,etcd3:2379
bootstrap:
  dcs:
    ttl: 30
    loop_wait: 10
    retry_timeout: 10
    maximum_lag_on_failover: 1048576
    postgresql:
      use_pg_rewind: true
      parameters:
        wal_level: replica
        max_wal_senders: 10
        hot_standby: "on"
        max_connections: 100
```

When the primary PostgreSQL fails, Patroni will:
1. Detect the failure via etcd.
2. Promote a standby to master.
3. Update DNS/PXC (if configured).
4. Notify operators (e.g., via Slack).

### Code Example: Automatic Failover in Kubernetes
Kubernetes handles pod restarts automatically, but for stateful apps (e.g., databases), you need **StatefulSets** and **headless services**:

```yaml
# statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
spec:
  serviceName: postgres
  replicas: 3
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_PASSWORD
          value: "password"
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 1Gi
```

When a pod fails, Kubernetes recreates it automatically. For databases, you also need **replication** (e.g., PostgreSQL streaming replication).

---

## 3. Hybrid Failover: The Best of Both Worlds?

Hybrid failover combines automation with human oversight. For example:
- Automatically switch to a standby if the primary fails.
- But notify humans for critical decisions (e.g., "Is this a real failure or just a temporary issue?").

### Example: AWS RDS with Manual Failover

AWS RDS supports **manual failover** but also has **automatic failover** for Multi-AZ deployments. You can also use **RDS Proxy** for connection pooling and failover.

```bash
# Manually failover in AWS CLI
aws rds describe-db-instances --db-instance-identifier my-db --query 'DBInstances[0].PreferredBackupWindow'
aws rds failover-db-cluster --db-cluster-identifier my-cluster --target-region us-east-2
```

### Code Example: Custom Failover Orchestrator (Python)

Here’s a simple Python script that checks database health and triggers failover if needed:

```python
import psycopg2
import time
from prometheus_client import start_http_server

# Health check endpoint (for Prometheus)
def check_db_health():
    try:
        conn = psycopg2.connect("host=primary-db user=admin password=password")
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        return True
    except Exception as e:
        print(f"DB health check failed: {e}")
        trigger_failover()
        return False

def trigger_failover():
    print("Initiating failover...")
    # Logic to promote a replica (e.g., via Patroni API or Kubernetes)
    # Example: Call Patroni REST API
    import requests
    requests.post("http://patroni:8008/v1/preferred/", json={"host": "new-primary"})

if __name__ == "__main__":
    start_http_server(8000)  # Prometheus metrics
    while True:
        check_db_health()
        time.sleep(10)
```

---

## Implementation Guide: Choosing the Right Approach

| **Factor**               | **Manual Failover** | **Automatic Failover** | **Hybrid Failover** |
|--------------------------|---------------------|------------------------|---------------------|
| **Complexity**           | Low                 | High                   | Medium              |
| **Downtime**             | High                | Low                    | Low-Medium          |
| **Best For**             | Small teams         | High-availability apps | Critical systems    |
| **Tools**                | Load balancers      | Patroni, Kubernetes    | Custom scripts + Patroni |

### Steps to Implement Failover
1. **Choose your approach** (manual, automatic, or hybrid).
2. **Set up replication** (for databases) or high-availability (for APIs).
3. **Configure monitoring** (Prometheus, New Relic, AWS CloudWatch).
4. **Test failover** (simulate failures in staging).
5. **Document the process** (what happens during failover?).

---

## Common Mistakes to Avoid

1. **Overlooking Replication Lag**
   - If your standby is too far behind, promoting it could lead to data loss.
   - *Fix:* Use tools like Patroni or Kubernetes Operators to enforce replication lag thresholds.

2. **Ignoring Network Partitions**
   - In distributed systems, network splits can prevent failover.
   - *Fix:* Use **quorum-based consensus** (e.g., etcd, ZooKeeper).

3. **Not Testing Failover**
   - Many teams assume failover works until it fails in production.
   - *Fix:* Run **chaos engineering** (e.g., kill primary nodes in staging).

4. **Tight Coupling to Primary**
   - Clients should not assume a single primary exists.
   - *Fix:* Use **DNS-based failover** (e.g., Route53, Cloudflare).

5. **Forgetting to Update DNS**
   - After failover, DNS may still point to the old primary.
   - *Fix:* Use **dynamic DNS updates** (e.g., AWS Route53 API).

---

## Key Takeaways

- **Manual failover** is simple but risky for high-traffic systems.
- **Automatic failover** reduces downtime but requires more setup.
- **Hybrid failover** balances automation with human oversight.
- **Replication lag is critical**—always monitor it.
- **Test failover in staging** before relying on it in production.
- **Use monitoring** (Prometheus, Grafana) to detect failures early.

---

## Conclusion: Failover is a Continuum

There’s no **one-size-fits-all** failover solution. Your choice depends on:
- **System criticality** (SaaS vs. internal tool).
- **Team size** (small team vs. DevOps-heavy).
- **Budget** (manual is cheaper, but automation costs more).

For most production systems, **automatic failover with monitoring** is the way to go. Start with a simple approach (e.g., Patroni for PostgreSQL or Kubernetes for APIs), then refine based on lessons learned.

### Next Steps
1. **For databases:** Try [Patroni](https://patroni.readthedocs.io/) or [Kubernetes StatefulSets](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/).
2. **For APIs:** Use [Kubernetes PodDisruptionBudgets](https://kubernetes.io/docs/tasks/run-application/configure-pdb/) or [AWS Auto Scaling](https://aws.amazon.com/autoscaling/).
3. **For monitoring:** Set up [Prometheus + Grafana](https://prometheus.io/docs/introduction/overview/).

Failover isn’t just about recovery—it’s about **proactive resilience**. Start small, test often, and keep improving.

---
```

This blog post provides a **complete, practical guide** to failover approaches, balancing theory with real-world examples. It avoids hype, explains tradeoffs clearly, and gives actionable code snippets.