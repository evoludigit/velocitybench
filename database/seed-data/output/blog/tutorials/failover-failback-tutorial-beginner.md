```markdown
---
title: "Failover & Failback Patterns: Building Resilient Systems"
date: 2023-11-15
author: "Jane Doe"
tags: ["database", "api", "resilience", "patterns"]
description: "Learn how failover and failback patterns prevent downtime and ensure business continuity in your application. Practical examples and real-world tradeoffs included."
---

# Failover & Failback Patterns: Building Resilient Systems

Ever seen a service go down when its primary database crashes? Or watched helplessly as a critical API becomes unreachable because its backend server failed? **Failover and failback patterns** are the secret sauce behind systems that keep functioning even when things go wrong. This tutorial explains how these patterns work, how to implement them, and why they’re essential for resilience—not just in theory, but with real-world examples and code.

We’ll start by exploring the problem of system failures and lost availability. Then, you’ll learn how failover automatically swaps traffic to backup systems, while failback carefully returns traffic to the primary after recovery. Along the way, you’ll see code examples in Python (using `requests` for HTTP failover) and SQL for database failover. By the end, you’ll know how to design for resilience, avoid common mistakes, and balance automation with safety.

---

## The Problem: A Single Point of Failure

Imagine a shopping website with a single database server. On Black Friday, the server overloads and crashes. If there’s no backup, the entire site goes down, losing thousands in potential revenue and frustrating customers. Or worse, the database is corrupted during the crash—now you’ve lost transaction records. This is the **single point of failure (SPoF)** problem.

Even worse, if there’s no automation, your operations team scrambles to manually redirect traffic to a backup. During this time, orders can’t be processed, users see errors, and trust in your service plummets. Downtime isn’t just costly—it’s embarrassing.

Let’s break down the consequences:
- **Unplanned downtime**: Customers can’t access your services.
- **Data loss**: Corruption or incomplete transactions.
- **Inefficient recovery**: Manual interventions slow down fixes.
- **Scalability limits**: Only works for a limited number of users.

This is why high-availability systems (HA) need **failover**—to switch to a backup system automatically—and **failback**—to return to the primary system safely once it’s recovered.

---

## The Solution: Failover & Failback Patterns

### How It Works
**Failover** is the process of automatically redirecting traffic from a failed primary system to a backup (secondary) system. **Failback** is the process of returning traffic to the primary system once it’s back online and verified as healthy.

Think of it like a power grid with backup generators:
- **Failover**: When the main power fails, the generator kicks in instantly (automatic).
- **Failback**: When power is restored, the grid manager checks if the main power is stable before switching back (manual and careful).

### Core Components
A failover/failback system typically includes:

1. **Primary System**: The main system handling traffic under normal conditions.
2. **Secondary System**: The backup system that takes over during failures.
3. **Monitoring**: Tools to detect failures (e.g., health checks, latency monitoring).
4. **Routing Layer**: A load balancer, API gateway, or application logic to switch traffic.
5. **Synchronization**: Mechanisms to keep the secondary system in sync with the primary (e.g., replication).
6. **Failback Logic**: Rules to decide when it’s safe to switch back (e.g., "after 5 minutes of stability").

---

## Implementation Guide: Code Examples

### 1. API Failover with Python (HTTP Client)
Let’s build a simple HTTP client that fails over to a secondary API endpoint if the primary fails. We’ll use `requests` with retry logic.

#### Example: Primary API with Fallback
```python
import requests

def call_primary_api(url):
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()  # Raises HTTPError for bad responses
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Primary API failed: {e}")
        return call_secondary_api(url)

def call_secondary_api(url):
    try:
        response = requests.get(url.replace("primary", "secondary"), timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Both APIs failed: {e}")

# Example usage
primary_url = "https://api.example.com/data"
data = call_primary_api(primary_url)
print(data)
```

#### How It Works:
- `call_primary_api` tries the primary endpoint first.
- If it fails, it automatically falls back to `call_secondary_api`.
- The secondary endpoint’s URL is constructed by replacing `"primary"` with `"secondary"` (e.g., `https://api-secondary.example.com/data`).

#### Tradeoffs:
- **Pros**: Simple, works for any HTTP API.
- **Cons**: No active monitoring of health; just retries on failure. For production, you’d want to add health checks.

---

### 2. Database Failover (PostgreSQL)
For databases, failover involves replicating data to a secondary node and promoting it to primary when the original fails. Let’s use PostgreSQL’s built-in replication.

#### Step 1: Set Up Replication
On the **primary** node (`postgres-primary`):
```sql
-- Enable replication in postgresql.conf
listen_addresses = '*'
wal_level = replica
max_wal_senders = 3
```

On the **secondary** node (`postgres-secondary`):
```sql
-- Connect to the primary to create a replication user
CREATE ROLE replica WITH REPLICATION LOGIN PASSWORD 'secure_password';
```

#### Step 2: Configure Replication in `postgresql.conf` (Secondary)
```ini
primary_conninfo = 'host=postgres-primary port=5432 user=replica password=secure_password'
primary_slot_name = 'my_replica_slots'
```

#### Step 3: Start Streaming Replication
On the secondary, run:
```bash
pg_basebackup -h postgres-primary -U replica -D /path/to/replica -P -C -R
```

#### Step 4: Failover Logic (Manual or Automatic)
PostgreSQL provides tools like `pg_ctl` and `pgpromote` for failover. For automation, use tools like:
- **Patroni**: Manages PostgreSQL failover with etcd or Kubernetes.
- **Repmgr**: Replication manager for PostgreSQL.

#### Example: Failover with Patroni (Python)
```python
from patroni import etcd, api

def trigger_failover():
    # Connect to etcd (used by Patroni for coordination)
    etcd_client = etcd.Client(host='etcd.example.com')
    patroni_client = api.PatroniClient(etcd_client)

    # Promote the secondary to primary
    result = patroni_client.promote()
    if result.success:
        print("Failover completed successfully!")
    else:
        print("Failover failed:", result.error)
```

#### Tradeoffs:
- **Pros**: Near real-time replication (depends on `wal_level`).
- **Cons**: Synchronization lag can cause stale reads. Write operations to the secondary may not be immediate.

---

### 3. Load Balancer Failover (Nginx)
For web servers, a load balancer can monitor health and route traffic based on status.

#### Example Nginx Configuration with Failover
```nginx
upstream backend {
    server primary-server:8080 max_fails=3 fail_timeout=30s;
    server secondary-server:8080 backup;
}

server {
    listen 80;
    location / {
        proxy_pass http://backend;
    }
}
```
- `max_fails=3`: Nginx will mark the server as down after 3 failed checks.
- `backup`: If the primary fails, traffic is sent to the secondary.
- `fail_timeout=30s`: Nginx waits 30 seconds before retrying the primary.

#### Tradeoffs:
- **Pros**: Simple to set up, handles HTTP health checks.
- **Cons**: No application-level logic; just routing based on server health.

---

## Common Mistakes to Avoid

1. **Blind Failback**: Switching back to the primary without verifying its health. This can cause another outage if the primary is still unstable.
   - **Fix**: Add failback delays and health checks before switching.

2. **No Synchronization**: Keeping the secondary out of sync with the primary. This leads to stale data or conflicts.
   - **Fix**: Use strong consistency models (e.g., synchronous replication) or accept eventual consistency.

3. **Overloading the Secondary**: During failover, the secondary takes all traffic, which might overload it.
   - **Fix**: Test failover under load and scale the secondary accordingly.

4. **Split-Brain**: Both primary and secondary are running simultaneously after failover, causing data conflicts.
   - **Fix**: Use quorum-based consensus (e.g., etcd, ZooKeeper) to coordinate failover.

5. **Ignoring Monitoring**: Not monitoring the health of both primary and secondary systems.
   - **Fix**: Implement comprehensive monitoring (e.g., Prometheus, Datadog) and alerts.

---

## Key Takeaways
- **Failover** automatically switches traffic to a backup system during failures.
- **Failback** returns traffic to the primary only after verifying its health.
- **Replication** is critical for keeping the secondary in sync with the primary.
- **Monitoring and health checks** are essential for detecting failures early.
- **Tradeoffs**:
  - Strong consistency (e.g., synchronous replication) improves accuracy but adds latency.
  - Eventual consistency (e.g., asynchronous replication) reduces latency but may cause stale reads.
- **Automation** reduces manual intervention but requires careful failback logic.
- **Testing** is non-negotiable—simulate failures to ensure your failover works.

---

## Conclusion

Failover and failback patterns are the backbone of resilient, high-availability systems. By automating failover and carefully managing failback, you can minimize downtime, protect your data, and keep your users happy—even when things go wrong.

Start small: Implement failover for a single API endpoint or database read replica. Gradually expand to full system failover. And always test your failover scenarios—because the only way to guarantee resilience is to **break things intentionally** and see how your system recovers.

Now go build something that never goes down!
```

---
**Further Reading:**
- [PostgreSQL Replication Docs](https://www.postgresql.org/docs/current/replication.html)
- [Patroni for PostgreSQL High Availability](https://patroni.readthedocs.io/)
- [Nginx Upstream Documentation](http://nginx.org/en/docs/http/ngx_http_upstream_module.html)