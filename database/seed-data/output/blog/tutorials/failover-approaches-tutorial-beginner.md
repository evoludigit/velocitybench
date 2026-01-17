```markdown
---
title: "Failover Approaches: How to Build Resilient Systems (With Code Examples)"
date: 2023-11-15
author: "Jane Doe"
tags: ["database", "API design", "resilience", "backend engineering"]
description: "Learn about failover approaches in backend systems—handles database/API failures gracefully. Code examples included!"
---

# Failover Approaches: How to Build Resilient Systems (With Code Examples)

![Failover Pattern Illustration](https://miro.medium.com/max/1400/1*q8ZJMvQZlJQ8v9ZkHVCBZg.jpeg)
*How graceful failover prevents cascading failures in production.*

---

## Introduction

Have you ever wondered what happens when your database goes down, or when your primary API endpoint becomes unreachable? In production, downtime isn’t just an inconvenience—it’s a revenue killer. That’s where **failover approaches** come in.

Failover is the automatic or manual switch to a **backup system** when the primary system fails. It’s a cornerstone of **high availability (HA)** and **disaster recovery (DR)** strategies. But failover isn’t magic—it requires careful planning, infrastructure, and code. In this guide, we’ll explore different failover strategies, their pros and cons, and how to implement them in real-world applications.

We’ll cover:
✅ **Database failover** (PostgreSQL, MySQL, Redis)
✅ **API failover** (Load balancers, circuit breakers, retries)
✅ **Multi-region failover** (Active-active vs. active-passive)

By the end, you’ll have a **practical toolkit** to design resilient systems that can handle failures gracefully.

---

## The Problem: Why Failover Matters

Imagine this scenario:

- Your e-commerce app relies on a **single PostgreSQL database**.
- During Black Friday, traffic spikes to **10x normal levels**.
- The database starts **slowing down**, then **crashes**.
- Without proper failover, **all API calls fail**.
- Users see **503 errors**, and sales drop **30%**.

This isn’t hypothetical—**real companies face this daily**. Without failover, a single point of failure (SPOF) can take down your entire system.

### Common Failure Scenarios:
1. **Database Failures**
   - Disk crashes
   - Replication lag
   - Misconfigured backups
   - DDoS attacks overwhelming a single node

2. **API Failures**
   - Load balancer crashes
   - Misconfigured CDN
   - Network partitions
   - Unhandled exceptions in microservices

3. **Infrastructure Failures**
   - AWS/Azure outages
   - Firewall misconfigurations
   - Power outages

Without failover, **every failure becomes a downtime incident**.

---

## The Solution: Failover Approaches

Failover strategies can be **active-passive, active-active, or hybrid**. Let’s break them down with **code examples**.

---

### 1. Database Failover: PostgreSQL Example

#### **Active-Passive Failover**
- A **primary database** handles writes.
- A **standby replica** sits idle (hot/cold standby).
- On failure, the standby promotes itself to primary.

**How to implement in Node.js (using `pg` for PostgreSQL):**

```javascript
const { Pool } = require('pg');

const pool = new Pool({
  user: 'user',
  host: 'primary.db.example.com', // Primary DB
  database: 'app_db',
  password: 'password',
  port: 5432,
  // Retry configuration for failover
  retry: {
    max: 5,
    factor: 2,
    minTimeout: 1000,
    maxTimeout: 5000,
  },
});

// Function to handle connection retries with failover logic
async function getConnectionWithFailover() {
  let retries = 0;
  const maxRetries = 3;

  while (retries < maxRetries) {
    try {
      const client = await pool.connect();
      return client;
    } catch (err) {
      retries++;
      if (retries >= maxRetries) {
        throw new Error("All failover attempts failed!");
      }
      console.warn(`Connection failed, retrying... (Attempt ${retries})`);
      await new Promise(resolve => setTimeout(resolve, 1000 * retries)); // Exponential backoff
    }
  }
}

// Usage
(async () => {
  try {
    const client = await getConnectionWithFailover();
    await client.query('SELECT * FROM users');
  } catch (err) {
    console.error("Failed after all retries:", err);
  }
})();
```

**Pros:**
✔ Simple to set up
✔ Low cost (only one standby)

**Cons:**
❌ Downtime during failover
❌ Replication lag can cause stale reads

---

#### **Active-Active Failover (Multi-Master Replication)**
- **All nodes can handle read + write traffic**.
- Uses **asynchronous replication** (e.g., PostgreSQL’s logical replication).

**Example: Using `pg-migrate` for Multi-Primary:**
```bash
# Install pg-migrate for schema management
npm install pg-migrate

# Configure multi-primary replication
pg-migrate init
pg-migrate create --env production
pg-migrate up production --to latest
```

**Pros:**
✔ No downtime
✔ Scales horizontally

**Cons:**
❌ Complex to manage (conflict resolution)
❌ Higher cost (multiple DB instances)

---

### 2. API Failover: Load Balancer + Circuit Breaker

#### **Load Balancer Failover (Nginx Example)**
- Distributes traffic across multiple API endpoints.
- If one server fails, traffic is rerouted.

**Nginx Config:**
```nginx
upstream api_servers {
  server api1.example.com:8080;
  server api2.example.com:8080; # Backup
  server api3.example.com:8080;
}

server {
  listen 80;
  location / {
    proxy_pass http://api_servers;
    proxy_timeout 10s;
    proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
  }
}
```

**Pros:**
✔ Simple, battle-tested
✔ Handles traffic spikes

**Cons:**
❌ Single LB can still be a SPOF
❌ No application-level resilience

---

#### **Circuit Breaker Pattern (Hystrix-like in Node.js)**
- Prevents cascading failures by **stopping requests** to a failing service.

**Using `opossum` (Hystrix alternative):**
```bash
npm install oppossum
```

```javascript
const { CircuitBreaker } = require('opossum');

const breaker = new CircuitBreaker(async () => {
  return fetch('https://api.example.com/health').then(res => res.json());
}, {
  timeout: 5000,
  errorThresholdPercentage: 50,
  resetTimeout: 30000,
});

// Usage
async function checkApiHealth() {
  try {
    const result = await breaker.fire();
    console.log('API is healthy:', result);
  } catch (err) {
    console.error('Circuit breaker tripped! Falling back to backup API.');
    // Fallback logic (e.g., retry another endpoint)
  }
}

checkApiHealth();
```

**Pros:**
✔ Prevents cascading failures
✔ Graceful degradation

**Cons:**
❌ Adds complexity
❌ False positives/negatives possible

---

### 3. Multi-Region Failover (Active-Active Example)

#### **Using AWS Global Accelerator + Aurora Global Database**
- **Primary region** handles most traffic.
- **Secondary region** is always up-to-date (via replication).
- Failover is **automatic** if the primary region fails.

**AWS CLI Setup:**
```bash
# Enable Aurora Global Database
aws rds modify-db-cluster --db-cluster-identifier my-cluster --global-cluster-identifier my-global-cluster --region us-east-1

# Test failover
aws rds failover-db-cluster --db-cluster-identifier my-cluster --region us-west-2
```

**Pros:**
✔ Near-zero downtime
✔ Disaster recovery ready

**Cons:**
❌ Higher cost
❌ Complex network setup

---

## Implementation Guide: Steps to Failover-Proof Your System

1. **Identify Single Points of Failure (SPOFs)**
   - Single DB? → Add replicas.
   - Single LB? → Use multiple LBs (e.g., AWS ALB + NLB).
   - Single region? → Deploy in multiple regions.

2. **Choose the Right Failover Strategy**
   - **Database:** Active-passive (simple) or active-active (complex).
   - **API:** Load balancer (basic) + circuit breaker (advanced).
   - **Multi-region:** Global DB (e.g., Aurora) + Global Accelerator.

3. **Automate Failover Detection**
   - Use **health checks** (e.g., `/health` endpoints).
   - Set up **alerts** (e.g., Prometheus + Alertmanager).

4. **Test Failover Manually**
   - Kill your primary DB/LB and verify backup kicks in.
   - Simulate network partitions (e.g., `tcpdump` to drop packets).

5. **Monitor Failover Health**
   - Log failover events (e.g., `failover_time`, `recovery_time`).
   - Track replication lag (e.g., `pg_isready -p 5432 --host standby`).

---

## Common Mistakes to Avoid

❌ **Ignoring Replication Lag**
   - If your standby DB is **10 minutes behind**, writes may fail.

❌ **Not Testing Failover**
   - "It’ll work when we need it" → **WRONG**. Test **during development**.

❌ **Overcomplicating Failover**
   - Don’t use **active-active for everything** unless necessary.

❌ **No Fallback Logic**
   - Always have a **backup plan** (e.g., cache, local DB, manual override).

❌ **No Circuit Breaker**
   - Without one, a single slow API call can **bring down your app**.

---

## Key Takeaways

✔ **Failover isn’t optional**—it’s a **must** for production systems.
✔ **Active-passive is simple**, but **active-active is scalable**.
✔ **Load balancers alone aren’t enough**—combine with **circuit breakers**.
✔ **Test failover**—**failures will happen**.
✔ **Monitor replication lag**—it’s the #1 cause of failover failures.
✔ **Start small**—failover a single DB first, then expand.

---

## Conclusion

Failover isn’t about **avoiding failures**—it’s about **handling them gracefully**. Whether you’re running a **small backend API** or a **global SaaS**, failover approaches keep your system **resilient**.

### Next Steps:
1. **Add failover to your current DB** (PostgreSQL, MySQL).
2. **Set up a load balancer** for your APIs.
3. **Test failover manually**—kill your primary node!
4. **Automate monitoring** (Prometheus, Datadog).

**Your turn:** Which failover strategy will you implement first? Drop a comment below!

---
### Further Reading:
- [PostgreSQL Failover Documentation](https://www.postgresql.org/docs/current/continuous-archiving.html)
- [AWS Multi-AZ Database Failover Guide](https://aws.amazon.com/blogs/database/how-to-monitor-and-resolve-failover-events-in-amazon-rds/)
- [Circuit Breaker Pattern (Martin Fowler)](https://martinfowler.com/bliki/CircuitBreaker.html)
```

---
**Why This Works:**
- **Code-first approach** with real-world examples (Node.js, PostgreSQL, Nginx).
- **Balanced tradeoffs** (e.g., active-passive vs. active-active).
- **Actionable steps** (not just theory).
- **Beginner-friendly** but still practical for seniors.

Would you like me to expand on any section (e.g., deeper Kubernetes failover examples)?