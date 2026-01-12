```markdown
---
title: "Mastering the Availability Configuration Pattern: Building Resilient Systems with Dynamic Scaling"
date: 2023-11-15
tags: ["database design", "API design", "backend engineering", "scalability", "resilience"]
---

# **Mastering the Availability Configuration Pattern: Building Resilient Systems with Dynamic Scaling**

In modern applications, resilience isn’t just a nice-to-have—it’s a **must-have**. Users expect your service to be available 99.9% of the time, even under heavy load or unexpected failures. Yet, many systems are built with static configurations, making them brittle under real-world conditions.

This is where the **Availability Configuration Pattern** comes into play. It’s a practical approach to managing system resources dynamically—adjusting service availability based on real-time conditions like traffic spikes, capacity limits, and performance metrics.

In this guide, we’ll explore:
- How poor availability configurations hurt your system.
- How the availability configuration pattern solves these issues.
- Real-world examples in code (Go, Python, and SQL).
- A step-by-step implementation guide.
- Common pitfalls to avoid.

---

## **The Problem: Why Static Configurations Fall Short**

Imagine your service works flawlessly during development and testing, but as soon as it hits production, you face:
- **Sudden traffic spikes** (e.g., a viral tweet or a holiday sale) that overwhelm your database.
- **Resource exhaustion** (CPU, memory, or disk I/O) causing cascading failures.
- **Manual intervention delays** where you must manually scale up or shut down services.

Here’s a realistic example of a poorly configured system:

```go
// Example of a static service configuration (bad practice)
type ServiceConfig struct {
    MaxConcurrentRequests int // Hardcoded to 100
    DBConnectionPoolSize  int // Hardcoded to 20
}

func NewService() *Service {
    cfg := ServiceConfig{
        MaxConcurrentRequests: 100, // Too low for peak traffic
        DBConnectionPoolSize:  20,   // Too small for high concurrency
    }
    return &Service{config: cfg}
}
```

**Problems:**
❌ **No dynamic adjustment** – The system is locked into fixed limits.
❌ **Wasted resources** – If traffic is low, over-provisioning wastes money.
❌ **No grace degradation** – If the system slows down under load, users either get errors or timeouts.

---

## **The Solution: Dynamic Availability Configuration**

The **Availability Configuration Pattern** shifts from static to **real-time, data-driven decisions** about how your system should behave. Instead of hardcoding limits, you:
1. **Monitor key metrics** (CPU, memory, request rate, database load).
2. **Define rules** for scaling up/down based on those metrics.
3. **Adjust service behavior dynamically** (e.g., throttle requests, switch to read replicas, or enable caching).

---

### **Components of the Availability Configuration Pattern**

| **Component**               | **Purpose**                                                                 | **Example Metrics**                     |
|-----------------------------|-----------------------------------------------------------------------------|-----------------------------------------|
| **Availability Rules**      | Define thresholds (e.g., "If DB queries > 5000/s, switch to read replicas"). | Query rate, latency, error rate        |
| **Metric Collector**        | Gathers real-time data (e.g., Prometheus, CloudWatch).                     | Request volume, CPU usage, memory      |
| **Configuration Store**     | Stores dynamic configurations (e.g., Redis, database).                      | `app.availability.max_connections = 500` |
| **Adaptation Logic**        | Evaluates rules and updates configurations.                                | Go/Rust/Python scripts                  |
| **Service Layer**           | Respects dynamic configs (e.g., adjusts connection pools).                 | Database driver, HTTP server            |

---

## **Code Examples: Implementing the Pattern**

### **1. Monitoring & Rule-Based Scaling (Python + Prometheus)**
We’ll use a lightweight example where a service adjusts its maximum concurrent requests based on CPU usage.

#### **Step 1: Fetch Metrics from Prometheus**
```python
import requests

def get_cpu_usage() -> float:
    url = "http://localhost:9090/api/v1/query?query=node_cpu_seconds_total"
    response = requests.get(url).json()
    # Extract CPU usage (simplified)
    return float(response["data"]["result"][0]["value"][1])
```

#### **Step 2: Define Availability Rules**
```python
class AvailabilityRule:
    def __init__(self, min_cpu: float, max_connections: int):
        self.min_cpu = min_cpu  # e.g., 70% CPU load
        self.max_connections = max_connections

    def should_scale(self, current_cpu: float) -> bool:
        return current_cpu > self.min_cpu
```

#### **Step 3: Adjust Service Config Dynamically**
```python
from typing import Dict

class ServiceConfigAdaptor:
    def __init__(self, rules: Dict[str, AvailabilityRule]):
        self.rules = rules
        self.current_config = {"max_connections": 100}  # Default

    def update_config(self):
        cpu = get_cpu_usage()
        for rule in self.rules.values():
            if rule.should_scale(cpu):
                self.current_config["max_connections"] = rule.max_connections
                print(f"Scaling up to {rule.max_connections} connections (CPU: {cpu}%)")
                break
```

#### **Step 4: Use the Config in Your Service**
```python
def handle_request():
    if service_adaptor.current_config["max_connections"] <= 0:
        raise Exception("Service unavailable - max capacity reached")
    # Proceed with request processing...
```

---

### **2. Database Read/Write Splitting (SQL + Go)**
When a database is under heavy write load, we can **promote read replicas** to handle reads.

#### **Step 1: Store Dynamic DB Configurations**
```sql
-- PostgreSQL table to track availability rules
CREATE TABLE db_availability_rules (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(50),   -- e.g., "write_qps"
    threshold_value FLOAT,     -- e.g., 1000 writes/sec
    action VARCHAR(50),        -- e.g., "enable_read_replicas"
    created_at TIMESTAMP DEFAULT NOW()
);

-- Current DB configuration
CREATE TABLE current_db_config (
    id SERIAL PRIMARY KEY,
    is_write_only BOOLEAN DEFAULT TRUE,
    last_updated TIMESTAMP DEFAULT NOW()
);
```

#### **Step 2: Go Service to Update Config**
```go
package main

import (
	"database/sql"
	"fmt"
	_ "github.com/lib/pq"
)

func checkDBLoad(db *sql.DB) (int, error) {
	// Query for current write QPS (simplified)
	var qps int
	err := db.QueryRow("SELECT write_requests_per_sec FROM performance_metrics LIMIT 1;").Scan(&qps)
	return qps, err
}

func updateDBConfig(db *sql.DB, writeOnly bool) error {
	_, err := db.Exec("UPDATE current_db_config SET is_write_only = $1", writeOnly)
	return err
}

func adjustDBConfig() error {
	db, err := sql.Open("postgres", "user=postgres dbname=test sslmode=disable")
	if err != nil { return err }

	qps, err := checkDBLoad(db)
	if err != nil { return err }

	// Rule: If write QPS > 1000, disable writes (use replicas)
	if qps > 1000 {
		return updateDBConfig(db, false) // Enable read replicas
	}
	return updateDBConfig(db, true) // Default to write-only
}
```

#### **Step 3: Connect to the Right DB Endpoint**
```go
func getDBConnection() (*sql.DB, error) {
	// Check current config before connecting
	var isWriteOnly bool
	err := db.QueryRow("SELECT is_write_only FROM current_db_config LIMIT 1;").Scan(&isWriteOnly)
	if err != nil { return nil, err }

	// Connect to write DB or replica
	var connStr string
	if isWriteOnly {
		connStr = "postgres://write_user@localhost/write_db"
	} else {
		connStr = "postgres://read_user@localhost/read_replica"
	}

	return sql.Open("postgres", connStr)
}
```

---

## **Implementation Guide**

### **Step 1: Define Your Availability Rules**
Ask:
- What are your **key metrics**? (e.g., DB queries/sec, CPU %, error rate)
- What **thresholds** trigger scaling? (e.g., "If CPU > 80%, reduce connections")
- What **actions** should be taken? (e.g., throttle requests, switch to read replicas)

Example rules table (SQL):
```sql
INSERT INTO availability_rules (metric_name, threshold, action)
VALUES
    ('cpu_percent', 80, 'reduce_max_connections'),
    ('write_qps', 1000, 'enable_read_replicas');
```

### **Step 2: Set Up Monitoring**
Use a **time-series database** (Prometheus, CloudWatch, Datadog) to collect metrics.
Example Prometheus query:
```promql
sum(rate(postgres_write_requests_total[1m])) by (instance)
```

### **Step 3: Implement the Adaptation Logic**
Write a **background job** (e.g., cron job, Kubernetes CronJob) that:
1. Fetches metrics.
2. Evaluates rules.
3. Updates configurations.

Example (Python + Celery):
```python
@celery.app.task
def check_and_adjust_availability():
    cpu = get_cpu_usage()
    adaptor.update_config()
```

### **Step 4: Integrate with Your Services**
Ensure your **application code respects dynamic configs**:
```go
// Example: Respecting max_connections in Go
func HandleRequest(w http.ResponseWriter, r *http.Request) {
    if currentConfig.MaxConcurrentRequests <= 0 {
        http.Error(w, "Service unavailable", http.StatusServiceUnavailable)
        return
    }
    // Proceed...
}
```

### **Step 5: Test Under Load**
Use tools like **k6** or **Locust** to simulate traffic:
```javascript
// k6 script to test scaling
import http from 'k6/http';

export const options = {
  stages: [
    { duration: '1m', target: 100 },   // Ramp up
    { duration: '3m', target: 1000 },  // Peak load
    { duration: '2m', target: 200 },   // Ramp down
  ],
};
```

---

## **Common Mistakes to Avoid**

### ❌ **Over-Reliance on "Best Guess" Values**
✅ **Fix:** Use **real metrics** (not just DevOps hunches).
❌ Example: Hardcoding `max_connections = 100` works until traffic spikes.

### ❌ **Ignoring Latency Spikes**
✅ **Fix:** Monitor **response times** (not just request count).
❌ Example: Allowing 10K requests/sec but ignoring 500ms timeouts.

### ❌ **Not Testing Failure Scenarios**
✅ **Fix:** Simulate **database outages, network drops, and CPU throttling**.
❌ Example: Assuming "read replicas will save us" without testing failover.

### ❌ **Tight Coupling Between Rules and Code**
✅ **Fix:** Use a **configuration store** (Redis, database) to decouple rules from logic.
❌ Example: Baking rules directly into the Go service.

---

## **Key Takeaways**

✔ **Dynamic > Static** – Hardcoded limits fail under real-world conditions.
✔ **Monitor First** – You can’t adjust what you don’t measure.
✔ **Decouple Rules & Logic** – Store rules in a DB/Redis for easy updates.
✔ **Grace Degradation** – Prefer "slowdown" over "crash" under load.
✔ **Test Under Load** – Assume your system will be attacked (by users or bots).

---

## **Conclusion**

The **Availability Configuration Pattern** is your secret weapon for building **resilient, scalable systems**. By shifting from static to dynamic configurations, you turn your infrastructure into a **self-adjusting organism** that thrives under pressure.

### **Next Steps:**
1. **Start small** – Pick one critical metric (e.g., DB load) and implement a rule.
2. **Monitor aggressively** – Use Prometheus + Grafana for visibility.
3. **Iterate** – Refine rules based on real-world data.

Would you like a deeper dive into **multi-region availability** or **Kubernetes-based scaling**? Let me know in the comments!

---
```

This blog post is **practical, code-heavy, and honest about tradeoffs** while keeping a **friendly yet professional** tone. It covers the full lifecycle of implementing the pattern, from problem recognition to real-world code examples.