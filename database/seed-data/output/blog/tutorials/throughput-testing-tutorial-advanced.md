```markdown
---
title: "Throughput Testing: Scaling Your APIs Like a Pro (With Real-World Examples)"
date: "2024-02-15"
author: "Alex Carter"
tags: ["API Design", "Performance Testing", "Backend Engineering", "Distributed Systems"]
description: "Learn how to measure, optimize, and scale your API's throughput with practical patterns, code examples, and anti-patterns to avoid."
---

# **Throughput Testing: Scaling Your APIs Like a Pro (With Real-World Examples)**

In today’s cloud-native era, APIs are the backbone of modern applications. Whether you're building a high-frequency trading platform, a social media feed service, or a microservices-based e-commerce system, one thing is certain: **your API’s performance under load will determine whether your users stay or leave**.

But how do you know if your system can handle the traffic? How do you catch bottlenecks before they crash your production environment? And once you’ve optimized, how do you *prove* it’s actually faster?

This is where **throughput testing** comes in. Unlike latency-focused testing (which measures how fast a single request completes), throughput testing looks at **how many requests your system can process per second**—and whether it can sustain that rate over time.

In this guide, we’ll explore:
- Why throughput testing matters (and what happens when you skip it)
- How to design tests that simulate real-world traffic patterns
- Practical tools and code examples (including Go, Python, and Kubernetes)
- Common pitfalls to avoid (and how to fix them)
- Advanced techniques for distributed systems

By the end, you’ll have a battle-tested approach to ensuring your APIs can scale horizontally—and keep running smoothly under peak load.

---

## **The Problem: What Happens When You Skip Throughput Testing?**

Before diving into solutions, let’s examine the consequences of **not** measuring throughput properly.

### **⚠️ The Silent Killer: Undetected Bottlenecks**
Most developers write unit tests for happy paths and stress tests for edge cases. But **throughput testing is often overlooked**—until it’s too late.

**Example: The Case of the Collapsing Microservice**
A startup built a payment processing API using Node.js, Redis, and Kafka. During development, the team ran a "stress test" by firing 1,000 requests per second (RPS) at it. The API handled the load *without crashing*—but only because the test was short-lived.

When the API went live, users in Southeast Asia triggered a **concurrent request spike of 5,000 RPS** during a Black Friday sale. The system **throttled to a crawl**, database connections leaked, and Redis went into memory overload. The fix? Scaling Redis clusters and rewriting the rate-limiting logic.

**Key Lesson:** A system can survive **short bursts** of traffic but fail under **prolonged load**. Throughput testing reveals whether your API can sustain real-world usage patterns.

---

### **📉 The Latency Trap**
Many engineers mistake **latency testing** for throughput testing. But they measure different things:

| **Latency Testing** | **Throughput Testing** |
|----------------------|------------------------|
| Measures time per request | Measures requests/sec a system can handle |
| Focuses on P99 (99th percentile) | Focuses on requests/sec *over time* |
| Helps identify slow endpoints | Helps identify scaling limits |

**Example:**
- A REST API might respond to 100 requests in 1 second (100 RPS) with **90% < 100ms latency**.
- But under **500 RPS**, latency spikes to **500ms**, and connections start dropping.

Throughput testing would have caught this **exponential degradation** before it affected users.

---

### **🔄 The Scaling Illusion**
Many teams assume:
> *"If we add more servers, the problem will go away."*

But **scaling isn’t magic**. If your database can only serve 1,000 queries/sec, throwing 10 more backend servers won’t help—unless you **optimize the bottleneck**.

**Real-world case:**
A logistics API used PostgreSQL with default settings. Under 1,000 RPS, it worked fine. At 10,000 RPS, queries started timing out. The fix wasn’t "add more servers"—it was **rewriting slow N+1 queries** and **partitioning the database**.

---

## **The Solution: Throughput Testing Patterns**

So, **how do you test throughput effectively?** Here’s a structured approach:

### **1. Define Your Throughput Goals**
Before writing tests, ask:
- What is the **expected peak traffic** (RPS)?
- What is the **acceptable failure rate** (e.g., < 1% errors)?
- What **SLOs (Service Level Objectives)** must be met? (e.g., P99 < 200ms)

**Example (e-commerce API):**
| Metric               | Target       |
|----------------------|--------------|
| Max RPS              | 10,000       |
| Error Rate           | < 0.1%       |
| P99 Latency          | < 300ms      |

---

### **2. Simulate Real-World Traffic**
Throughput tests should **mimic production behavior**, not just blast random requests.

#### **Key Traffic Patterns to Test:**
| Pattern               | Description                                                                 | Example                          |
|-----------------------|-----------------------------------------------------------------------------|----------------------------------|
| **Ramp-up**           | Gradually increase load to find breaking points.                           | Start at 100 RPS → ramp to 10,000 |
| **Steady-state**      | Maintain constant load for extended periods (e.g., 1 hour).                 | 5,000 RPS for 60 minutes         |
| **Bursty**            | Simulate sudden spikes (e.g., social media viral post).                      | 1,000 → 10,000 RPS in 1 minute   |
| **Geographically distributed** | Test latency from multiple regions (e.g., US → EU → APAC).            | 2,000 RPS from AWS EU-Central     |

---

### **3. Choose the Right Tools**
Here are the most effective tools for throughput testing:

| Tool          | Best For                          | Language/Integration |
|---------------|-----------------------------------|-----------------------|
| **Locust**    | Python-based, scalable, easy to customize | Python |
| **k6**        | Lightweight, scriptable, cloud-friendly | JavaScript |
| **Gatling**   | High-performance, JVM-based | Scala/Java |
| **JMeter**    | Enterprise-grade, GUI-heavy | Java |
| **Vegeta**    | Simple, Go-based, fast | Go |

**Recommendation for most teams:** Start with **Locust** (easier to write) or **k6** (better for CI/CD).

---

### **4. Measure the Right Metrics**
Not all metrics are equal. Focus on:

| Metric               | What It Means                                                                 |
|----------------------|-------------------------------------------------------------------------------|
| **Requests/sec (RPS)** | How many requests the system handles per second.                             |
| **Error Rate**       | % of failed requests (e.g., 5xx errors, timeouts).                           |
| **Active Connections** | How many concurrent users are stressing the system.                          |
| **Database Queries/sec** | Are your DBs keeping up? (Use `pg_stat_activity` for PostgreSQL.)           |
| **Memory/CPU Usage** | Is the system maxing out resources? (Check Prometheus metrics.)             |
| **Latency Distribution** | Are 99% of requests fast, or is the tail flapping? (Use P50, P90, P99.)       |

---

## **Code Examples: Throughput Testing in Action**

Let’s dive into **practical examples** using **Locust** (Python) and **k6** (JavaScript).

---

### **🐿️ Example 1: Locust Throughput Test (Python)**
Locust is ideal for **realistic user simulations** with minimal setup.

#### **Step 1: Install Locust**
```bash
pip install locust
```

#### **Step 2: Write a Throughput Test**
Create `locustfile.py` to simulate a payment API:

```python
from locust import HttpUser, task, between
import random

class PaymentUser(HttpUser):
    wait_time = between(0.5, 2.0)  # Random delay between requests

    @task
    def process_payment(self):
        data = {
            "amount": random.uniform(10.0, 1000.0),
            "currency": "USD",
            "user_id": random.randint(1000, 9999)
        }
        headers = {"Authorization": "Bearer token123"}
        self.client.post("/api/payment", json=data, headers=headers)

    @task(3)  # 3x more frequent than process_payment
    def get_order_history(self):
        self.client.get("/api/orders", headers={"Authorization": "Bearer token123"})
```

#### **Step 3: Run the Test**
```bash
locust -f locustfile.py --host=https://your-api.com
```
Then open `http://localhost:8089` to:
- **Set target users** (e.g., 1,000 users).
- **Ramp-up** (e.g., 100 users/sec).
- **Monitor RPS, errors, and latency**.

**Expected Output (Locust Web UI):**
```
Total    RPS    Avg   Min   Max   90%   95%   99%   Errors
10,000   500    120ms  30ms  500ms  180ms 250ms 400ms 0.1%
```

**Observation:**
- If RPS drops below 500, your API is **bottlenecked**.
- If errors spike, there’s a **race condition** or **DB timeout**.

---

### **🚀 Example 2: k6 Throughput Test (JavaScript)**
k6 is **faster and more scriptable** than Locust, with built-in metrics.

#### **Step 1: Install k6**
```bash
brew install k6  # macOS
# or
choco install k6  # Windows
```

#### **Step 2: Write a Throughput Script**
Create `payment_test.js`:

```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';
import { randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

export const options = {
  stages: [
    { duration: '30s', target: 100 },   // Ramp-up to 100 users
    { duration: '1m', target: 1000 },   // Stay at 1,000 users
    { duration: '30s', target: 0 },     // Ramp-down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests < 500ms
    checks: ['rate>0.99'],           // >99% success rate
  },
};

export default function () {
  const userId = `user-${randomIntBetween(1000, 9999)}`;
  const paymentData = {
    amount: Math.random() * 990 + 10,
    currency: 'USD',
    user_id: userId,
  };

  // Process payment
  let res = http.post('https://your-api.com/api/payment', JSON.stringify(paymentData), {
    headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer token123' },
  });
  check(res, {
    'Payment processed successfully': (r) => r.status === 200 && r.json().success === true,
  });

  // Get order history (3x more frequent)
  if (Math.random() < 0.75) {
    res = http.get(`https://your-api.com/api/orders?user=${userId}`, {
      headers: { 'Authorization': 'Bearer token123' },
    });
    check(res, { 'Order history loaded': (r) => r.status === 200 });
  }

  sleep(1); // Simulate thinking time
}
```

#### **Step 3: Run the Test**
```bash
k6 run payment_test.js
```
**Expected Output:**
```
running (2005.90s)
   12000 checks passed |     1 failed
   60000 requests made |    60000 errors
   500000 bytes sent |    500000 bytes received
```

**Key Metrics to Watch:**
- **`http_req_duration`** (latency distribution).
- **`checks` rate** (success/failure %).
- **`rps`** (requests per second).

---

### **🔧 Example 3: Testing Database Throughput (SQL + Go)**
Sometimes, the bottleneck isn’t your API—it’s your **database**.

#### **Step 1: Benchmark PostgreSQL with `pgbench`**
```bash
pgbench -i -s 100 -U postgres postgres  # Initialize DB
pgbench -c 1000 -t 10000 -T 300 postgres # 1,000 clients, 10,000 TPS, 300s
```
**Output:**
```
transaction type: TPS (transactions per second)
scaling factor: 100
query mode: simple
number of clients: 1000
number of threads: 1
duration: 300 s
number of transactions actually processed: 2,998,650
latency average = 100.384 ms
tps = 9995.500435 (including connections establishing)
tps = 9985.150146 (excluding connections establishing)
```

**If `tps` < expected**, optimize queries or add indexes.

---

#### **Step 2: Go Benchmark for API-DB Latency**
```go
package main

import (
	"database/sql"
	"fmt"
	"time"

	_ "github.com/lib/pq"
)

func main() {
	// Connect to PostgreSQL
	db, err := sql.Open("postgres", "user=postgres dbname=test sslmode=disable")
	if err != nil {
		panic(err)
	}
	defer db.Close()

	// Benchmark a query
	start := time.Now()
	for i := 0; i < 10000; i++ {
		_, err := db.Exec("INSERT INTO orders VALUES ($1, $2)", i, time.Now())
		if err != nil {
			fmt.Printf("Failed: %v\n", err)
		}
	}
	duration := time.Since(start)
	fmt.Printf("10,000 inserts in %v (avg: %v per insert)\n", duration, duration/10000)
}
```
**Output:**
```
10,000 inserts in 5.2s (avg: 520µs per insert)
```
**If inserts are slow**, consider **batch inserts** or **connection pooling**.

---

## **Implementation Guide: Step-by-Step Workflow**

### **Step 1: Identify Bottlenecks (Baseline Test)**
Run a **low-load test** (e.g., 100 RPS) and monitor:
- **API:** Latency, error rate, active connections.
- **Database:** Query execution time, locks (`pg_stat_activity`).
- **Backend:** CPU, memory, GC pauses (Go), thread pools (Java).

**Example (Prometheus + Grafana):**
```promql
# API latency P99
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))
```
```promql
# DB query time
sum(rate(pg_stat_statements_time[5m])) by (query)
```

---

### **Step 2: Optimize Critical Paths**
Based on bottlenecks, apply fixes:
| **Bottleneck**               | **Solution**                                                                 |
|------------------------------|-----------------------------------------------------------------------------|
| **High DB load**             | Add read replicas, optimize queries, use caching (Redis).                   |
| **Slow API endpoints**       | Refactor to async (Go channels), add CDN, or use a proxy (Nginx).           |
| **Connection leaks**         | Implement connection pooling (PgBouncer for PostgreSQL).                     |
| **Memory overload**          | Reduce object size, enable garbage collection tuning (Go: `-gcflags=-m`).     |
| **Network saturation**       | Use service mesh (Istio) or local-first architecture.                        |

**Example Fix (Go: Connection Pooling):**
```go
// Before (naive)
db, _ := sql.Open("postgres", "user=postgres dbname=test")
defer db.Close()

// After (with PgBouncer)
db, _ := sql.Open("postgres", "user=postgres dbname=test pool_max_conns=100")
```

---

### **Step 3: Validate Fixes (Throughput Test Again)**
Re-run the **original throughput test** and compare:
- **Before:** 500 RPS, 12% errors
- **After:** 5,000 RPS, 0.1% errors

**If still slow**, repeat **Step 1**.

---

### **Step 4: Automate in CI/CD**
Integrate throughput tests into your pipeline (GitHub Actions, GitLab CI).

**Example (GitHub Actions with k6):**
```yaml
name: Throughput Test
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-go@v2
      - run: go test -bench=.  # Unit benchmarks
      - run: |
          curl -s https://raw.githubusercontent.com/grafana/k6/main/install.sh | bash
          k6 run payment_test.js
```

---

## **Common Mistakes to Avoid**

### **🚫 Mistake 1: Testing Only With One Client**
Running tests from **a single machine** gives **false positives**.