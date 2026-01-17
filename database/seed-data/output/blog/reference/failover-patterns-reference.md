# **[Failover Patterns] Reference Guide**

## **Overview**
Failover patterns define mechanisms to automatically redirect application workloads from a primary component (e.g., service, database, or network endpoint) to a secondary (backup or standby) component when the primary fails, ensuring high availability and resilience. Failover is critical in distributed systems, cloud architectures, and mission-critical applications. This guide covers key failover patterns, their implementation strategies, and supporting schemas for configuration and monitoring.

Common failover use cases include:
- **Service redundancy** (e.g., swapping between web servers).
- **Database replication** (e.g., failover from primary DB to a replica).
- **Network routing** (e.g., DNS-based failover or load balancer redirection).

---

## **Implementation Details**

### **1. Key Concepts**
| **Term**               | **Definition**                                                                 |
|-------------------------|-------------------------------------------------------------------------------|
| **Primary Component**    | The active system handling requests (e.g., primary DB server).                 |
| **Secondary Component**  | A standby system that takes over if the primary fails.                        |
| **Failover Trigger**     | Event causing a switch (e.g., health check timeout, manual intervention).     |
| **Synchronization**      | Approaches to keep the secondary in sync with the primary (e.g., async replication). |
| **Failback**            | Reverting to the primary component after it recovers (manual or automatic). |
| **Observability Metrics**| Key indicators (e.g., lag in replication, latency spikes) to detect failure.   |

---

### **2. Failover Patterns and Strategies**
#### **A. Active-Active Failover**
**Description**: Both primary and secondary components are active and handle traffic simultaneously. No downtime occurs during failover.
**Use Case**: Geo-redundant databases (e.g., PostgreSQL streaming replication).
**Implementation**:
- Configure **synchronous replication** to ensure data consistency.
- Use a **load balancer** (e.g., AWS ALB, HAProxy) to route traffic based on health checks.
- **Failover Trigger**: Automatic if a primary node fails a health check (e.g., `heartbeat` timeout).

**Schema Reference (Active-Active)**
| **Field**               | **Type**    | **Description**                                      |
|--------------------------|-------------|------------------------------------------------------|
| `primary_node`           | `string`    | IP/hostname of primary node.                          |
| `secondary_node`         | `string`    | IP/hostname of secondary node.                        |
| `replication_sync`       | `boolean`   | `true` if synchronous; `false` for async.            |
| `health_check_endpoint`  | `string`    | URL/path to monitor node health (e.g., `/health`).   |
| `failover_timeout`       | `int`       | Seconds before declaring a node "unhealthy."         |

**Example Query (Configuring Active-Active)**
```json
{
  "nodes": [
    {
      "primary_node": "10.0.0.1",
      "secondary_node": "10.0.0.2",
      "replication_sync": true,
      "health_check_endpoint": "/api/health",
      "failover_timeout": 5
    }
  ]
}
```

---

#### **B. Active-Standby Failover**
**Description**: The secondary component is inactive (standby) until the primary fails. Common in databases (e.g., MySQL master-slave).
**Use Case**: Single-writer, multi-reader architectures.
**Implementation**:
- Use **asynchronous replication** to tolerate slight data lag.
- Implement a **monitoring agent** (e.g., Prometheus) to detect primary failures.
- **Failover Trigger**: Manual or automated script (e.g., `pg_ctl promote` for PostgreSQL).

**Schema Reference (Active-Standby)**
| **Field**               | **Type**    | **Description**                                      |
|--------------------------|-------------|------------------------------------------------------|
| `primary_node`           | `string`    | Master node IP/hostname.                              |
| `standby_nodes`          | `array`     | List of replica nodes.                               |
| `replication_lag_threshold` | `int`   | Max allowed lag (seconds) before failover.           |
| `failover_script`        | `string`    | Path to script (e.g., `/usr/local/bin/failover.sh`). |
| `failback_enabled`       | `boolean`   | `true` to auto-revert to primary after recovery.     |

**Example Query (Configuring Active-Standby)**
```json
{
  "primary_node": "10.0.0.1",
  "standby_nodes": ["10.0.0.2", "10.0.0.3"],
  "replication_lag_threshold": 10,
  "failover_script": "/scripts/failover.sh",
  "failback_enabled": true
}
```

---

#### **C. DNS-Based Failover**
**Description**: Use **DNS round-robin** or **failover records** (e.g., CNAME with TTL=1s) to reroute traffic when a primary fails.
**Use Case**: Static IP-based services (e.g., web servers).
**Implementation**:
- Set **short TTL** (e.g., 1 second) for failover records.
- Use a **DNS provider with health checks** (e.g., AWS Route 53, Cloudflare).
- **Failover Trigger**: DNS provider detects unreachable primary and updates records.

**Schema Reference (DNS Failover)**
| **Field**               | **Type**    | **Description**                                      |
|--------------------------|-------------|------------------------------------------------------|
| `primary_dns_record`     | `string`    | A/CNAME record for primary (e.g., `app.example.com`). |
| `secondary_dns_record`   | `string`    | Backup record.                                       |
| `ttl_failover`           | `int`       | TTL for failover record (seconds).                  |
| `health_check_url`       | `string`    | Endpoint to test primary health.                     |

**Example Query (DNS Failover Config)**
```json
{
  "records": [
    {
      "primary_dns_record": "app.example.com",
      "secondary_dns_record": "app-fallback.example.com",
      "ttl_failover": 1,
      "health_check_url": "https://app.example.com/health"
    }
  ]
}
```

---

#### **D. Circuit Breaker Pattern (Resilience)**
**Description**: A failover-like mechanism where a client aborts requests to a failing service after X failures/consecutive errors.
**Use Case**: Microservices with unstable dependencies.
**Implementation**:
- Use libraries like **Resilience4j (Java)**, **Polly (.NET)**, or **Hystrix (legacy)**.
- Define **failure thresholds** (e.g., fail after 3 errors in 5 seconds).
- **Fallback**: Serve cached data or degrade gracefully.

**Schema Reference (Circuit Breaker)**
| **Field**               | **Type**    | **Description**                                      |
|--------------------------|-------------|------------------------------------------------------|
| `service_name`           | `string`    | Name of dependent service (e.g., `payment-service`). |
| `failure_threshold`      | `int`       | Max failures before tripping.                        |
| `time_window_seconds`    | `int`       | Time window for threshold (e.g., 5s).                |
| `fallback_response`      | `string`    | JSON template for fallback (e.g., `{"error": "Service Unavailable"}`). |
| `reset_timeout_seconds`  | `int`       | Time to reset circuit after recovery.                |

**Example Query (Configuring Circuit Breaker)**
```json
{
  "circuits": [
    {
      "service_name": "payment-service",
      "failure_threshold": 3,
      "time_window_seconds": 5,
      "fallback_response": {"error": "Payment service unavailable. Try again later."},
      "reset_timeout_seconds": 30
    }
  ]
}
```

---

## **Query Examples**
### **1. Check Failover Status**
**Assume**: A monitoring tool queries the state of all failover configurations.
```json
GET /api/v1/failover/status
```
**Response**:
```json
{
  "nodes": [
    {
      "primary_node": "10.0.0.1",
      "status": "active",
      "replication_lag": 0
    },
    {
      "primary_node": "10.0.0.2",
      "status": "standby",
      "last_failed_over": "2023-10-01T12:00:00Z"
    }
  ]
}
```

### **2. Trigger Manual Failover**
**Example**: Promote a standby database node to primary.
```json
POST /api/v1/failover/trigger?node=10.0.0.2
Headers: {"Authorization": "Bearer xxxx"}
```
**Response**:
```json
{
  "success": true,
  "message": "Node 10.0.0.2 promoted to primary.",
  "timestamp": "2023-10-01T12:05:00Z"
}
```

### **3. Update DNS Failover Record**
**Example**: Change the secondary DNS record due to a new server deployment.
```json
PUT /api/v1/dns/failover
Body:
{
  "primary_dns_record": "app.example.com",
  "secondary_dns_record": "app-new.example.com",
  "ttl_failover": 1
}
```
**Response**:
```json
{
  "status": "updated",
  "new_ttl": 1,
  "propagation_estimate": "30-120 seconds"
}
```

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                                      |
|---------------------------|-------------------------------------------------------------------------------|------------------------------------------------------|
| **Retry Pattern**         | Exponential backoff for transient failures.                                  | When failures are temporary (e.g., network blips).   |
| **Bulkhead Pattern**      | Isolate failure in one component from others.                                | To prevent cascading failures in microservices.      |
| **Rate Limiting**         | Throttle requests to prevent overload during failover.                      | For public APIs or bursty traffic.                   |
| **Idempotency**           | Ensure repeated operations (e.g., retries) don’t cause duplicate side effects. | For payment processing or database writes.           |
| **Chaos Engineering**     | Proactively test failover by injecting failures (e.g., `chaos-monkey`).     | To validate resilience before production.           |

---
**Notes**:
- Combine failover patterns (e.g., use **DNS failover + circuit breakers** for web apps).
- Monitor **replication lag** and **component health** to avoid data loss.
- Test failover procedures regularly (e.g., simulate primary node failures).