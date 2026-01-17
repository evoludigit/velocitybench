# **[Pattern] Failover Configuration Reference Guide**

---

## **Overview**
Failover Configuration is a resilience pattern used to ensure system continuity by automatically switching to a redundant or backup component when a primary service, node, or dependency fails. This guide provides a structured approach to designing, implementing, and managing failover systems in distributed architectures. It covers key concepts, schema definitions, operational queries, and related patterns to help engineers enforce high availability (HA) and fault tolerance.

---

## **Key Concepts**
| **Term**               | **Definition**                                                                                     | **Use Case**                                                                                     |
|------------------------|---------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| **Primary Node**       | The active service/instance handling requests in a cluster.                                        | Default endpoint for client traffic.                                                            |
| **Backup Node**        | A secondary, standby instance ready to take over if the primary fails.                            | Provides redundancy; minimizes downtime.                                                      |
| **Failover Trigger**   | Event or condition (e.g., health check failure, latency spike) that initiates failover.           | Automates recovery without manual intervention.                                                 |
| **Synchronization**    | Mechanism ensuring backup nodes stay in sync with the primary (e.g., replication, mirroring).    | Prevents inconsistencies during failover.                                                      |
| **Health Checks**      | Probes (e.g., HTTP, TCP, or custom scripts) to monitor node liveness.                           | Detects failures before clients do.                                                             |
| **Failover Scope**     | Level at which failover occurs (e.g., node, service, datacenter).                                | Granularity of recovery (e.g., per-instance vs. regional).                                     |
| **Recovery Time Objective (RTO)** | Target time to restore service after a failover.          | Measures operational efficiency (e.g., 5 minutes).                                             |
| **Recovery Point Objective (RPO)** | Max acceptable data loss during failure.                   | Defines sync frequency (e.g., near-zero loss with synchronous replication).                     |
| **Load Balancer**      | Distributes traffic across primary/backup nodes.                                                | Ensures seamless client switching.                                                             |
| **Monitoring & Alerts**| Tools (e.g., Prometheus, Nagios) to track failover events and node health.                     | Proactive issue resolution.                                                                  |

---

## **Schema Reference**
Below are schema definitions for failover configurations in **JSON** and **YAML** formats.

### **1. Failover Configuration Schema (JSON)**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "FailoverConfiguration",
  "type": "object",
  "properties": {
    "name": {
      "type": "string",
      "description": "Unique identifier for the failover group (e.g., 'db-primary-backup')."
    },
    "primaryNode": {
      "type": "string",
      "description": "Endpoint or identifier of the primary node (e.g., 'db1.example.com:5432')."
    },
    "backupNodes": {
      "type": "array",
      "items": {
        "type": "string",
        "description": "List of backup node endpoints (e.g., ['db2.example.com:5432', 'db3.example.com:5432'])."
      },
      "minItems": 1
    },
    "healthCheck": {
      "type": "object",
      "properties": {
        "interval": {
          "type": "string",
          "format": "duration",
          "description": "Frequency of health checks (e.g., '10s')."
        },
        "timeout": {
          "type": "string",
          "format": "duration",
          "description": "Max time for a health check to complete (e.g., '5s')."
        },
        "path": {
          "type": "string",
          "description": "Endpoint for health checks (e.g., '/health')."
        },
        "expectedStatus": {
          "type": "integer",
          "description": "Expected HTTP status (e.g., 200)."
        }
      },
      "required": ["interval", "timeout"]
    },
    "synchronization": {
      "type": "object",
      "properties": {
        "strategy": {
          "type": "string",
          "enum": ["synchronous", "asynchronous", "eventual"],
          "description": "Replication method (default: 'synchronous')."
        },
        "lagThreshold": {
          "type": "string",
          "format": "duration",
          "description": "Max allowed data lag before failing over (e.g., '1m')."
        }
      },
      "required": ["strategy"]
    },
    "failoverTrigger": {
      "type": "object",
      "properties": {
        "type": {
          "type": "string",
          "enum": ["healthCheckFailure", "latencyThreshold", "manual"],
          "description": "Trigger condition (default: 'healthCheckFailure')."
        },
        "latencyThreshold": {
          "type": "string",
          "format": "duration",
          "description": "Max allowed latency to trigger failover (e.g., '3s')."
        }
      }
    },
    "loadBalancer": {
      "type": "object",
      "properties": {
        "type": {
          "type": "string",
          "enum": ["round-robin", "leastConnections", "ipHash"],
          "description": "Traffic distribution algorithm."
        },
        "healthCheckInterval": {
          "type": "string",
          "format": "duration",
          "description": "Frequency to update node health (e.g., '30s')."
        }
      }
    },
    "metrics": {
      "type": "object",
      "properties": {
        "prometheus": {
          "type": "object",
          "properties": {
            "endpoint": {
              "type": "string",
              "description": "Prometheus server URL (e.g., 'http://metrics.example.com')."
            }
          }
        }
      }
    }
  },
  "required": ["name", "primaryNode", "backupNodes", "healthCheck", "synchronization"]
}
```

### **2. Failover Configuration Schema (YAML)**
```yaml
failover:
  name: "database-cluster"
  primaryNode: "db1.example.com:5432"
  backupNodes:
    - "db2.example.com:5432"
    - "db3.example.com:5432"
  healthCheck:
    interval: "10s"
    timeout: "5s"
    path: "/health"
    expectedStatus: 200
  synchronization:
    strategy: "synchronous"
    lagThreshold: "1m"
  failoverTrigger:
    type: "healthCheckFailure"
    latencyThreshold: "3s"
  loadBalancer:
    type: "round-robin"
    healthCheckInterval: "30s"
  metrics:
    prometheus:
      endpoint: "http://metrics.example.com"
```

---

## **Implementation Details**
### **1. Failover Workflow**
1. **Monitoring**: Health checks (e.g., `/health`) are polled on primary nodes.
2. **Detection**: If a primary fails (e.g., health check returns non-200), the failover orchestrator is triggered.
3. **Synchronization Check**: Backup nodes are verified for consistency (within `lagThreshold`).
4. **Failover**: Traffic is routed to the first healthy backup node via the load balancer.
5. **Recovery**: Failed primary is replaced if repaired (or promoted if no backups remain).

### **2. Synchronization Strategies**
| **Strategy**       | **Description**                                                                                     | **Pros**                                  | **Cons**                                  |
|--------------------|---------------------------------------------------------------------------------------------------|-------------------------------------------|-------------------------------------------|
| **Synchronous**    | Primary waits for acknowledgment from backups before committing writes.                           | Strong consistency.                       | Higher latency.                           |
| **Asynchronous**   | Primary commits immediately; backups replicate later.                                             | Lower latency.                            | Risk of data loss if primary fails.      |
| **Eventual**       | Backups sync over time; no strict timeline.                                                      | Decoupled writes.                         | Extended recovery window.                 |

### **3. Health Check Types**
| **Type**       | **Example**                          | **Use Case**                                                                                     |
|----------------|--------------------------------------|--------------------------------------------------------------------------------------------------|
| **HTTP**       | `GET /health` → 200 OK               | Web services, APIs.                                                                              |
| **TCP**        | Port probe (e.g., 5432 for PostgreSQL)| Databases, low-level services.                                                                  |
| **Custom**     | Executable script (e.g., `pg_isready`) | Complex checks (e.g., database connection tests).                                              |
| **Latency**    | RTT > 3s → Failover                  | Detect slow performance before outright failures.                                               |

---

## **Query Examples**
### **1. Query Failover Status (CLI/REST)**
**Endpoint**: `GET /v1/failover/{groupName}/status`
**Request**:
```bash
curl -X GET "http://config-server:8080/v1/failover/database-cluster/status" -H "Authorization: Bearer <=TOKEN>"
```
**Response**:
```json
{
  "groupName": "database-cluster",
  "primaryNode": "db1.example.com:5432",
  "currentStatus": "healthy",
  "backupNodes": [
    {"node": "db2.example.com:5432", "status": "healthy", "syncLag": "0s"},
    {"node": "db3.example.com:5432", "status": "unhealthy", "lastCheck": "2024-01-01T12:00:00Z"}
  ],
  "lastFailoverTime": "2024-01-01T11:30:00Z",
  "recoveryInProgress": false
}
```

### **2. Trigger Manual Failover**
**Endpoint**: `POST /v1/failover/{groupName}/failover`
**Request**:
```bash
curl -X POST "http://config-server:8080/v1/failover/database-cluster/failover" \
  -H "Authorization: Bearer <=TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"force": false}'
```
**Response**:
```json
{
  "success": true,
  "newPrimary": "db2.example.com:5432",
  "message": "Failover initiated. Traffic redirected."
}
```

### **3. View Synchronization Lag**
**Endpoint**: `GET /v1/failover/{groupName}/sync-status`
**Request**:
```bash
curl -X GET "http://config-server:8080/v1/failover/database-cluster/sync-status"
```
**Response**:
```json
{
  "lagStats": {
    "db1->db2": {"current": "15s", "threshold": "60s"},
    "db1->db3": {"current": "0s",  "threshold": "60s"}
  },
  "alertThresholdReached": false
}
```

---

## **Operational Queries**
### **1. Detecting Failover Events**
**SQL (Log Analysis)**:
```sql
SELECT
  event_time,
  node,
  event_type,
  duration_ms
FROM failover_events
WHERE event_type = 'failover'
  AND event_time > now() - interval '24 hours'
ORDER BY event_time DESC;
```

### **2. Calculating RTO/RPO Metrics**
**Grafana Dashboard Query**:
- **RTO**: `histogram_quantile(0.95, sum(rate(failover_duration_seconds_bucket[5m])) by (node))`
- **RPO**: `max_by(time, lag_seconds) where node = 'db1' group by node`

### **3. Backups Health Check (Shell Script)**
```bash
#!/bin/bash
for node in ${BACKUP_NODES}; do
  response=$(curl -s -o /dev/null -w "%{http_code}" "http://${node}/health")
  if [ "$response" -ne 200 ]; then
    echo "ERROR: Node ${node} unhealthy (status: ${response})" >&2
    exit 1
  fi
done
```

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                                     | **When to Use**                                                                                     |
|---------------------------|---------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| **Circuit Breaker**       | Prevents cascading failures by temporarily stopping requests to a failing service.                | Mitigate knock-on effects during failover.                                                       |
| **Retry with Backoff**    | Automatically retries failed requests with exponential delays.                                     | Handle transient failures (e.g., network blips).                                                |
| **Bulkheading**           | Isolates failure domains (e.g., per-service queues) to contain failures.                          | Prevent a single failure from affecting unrelated systems.                                       |
| **Bulkhead Pattern**      | Limits concurrent executions in a component to avoid resource exhaustion.                          | Protect against cascading failures during failover.                                             |
| **Saga Pattern**          | Manages distributed transactions across services using compensating actions.                     | Complex workflows with multiple dependencies.                                                    |
| **Rate Limiting**         | Controls request volume to prevent overload during failover.                                      | Protect APIs from abuse during traffic spikes.                                                   |
| **Chaos Engineering**     | Deliberately injects failures to test failover resilience.                                       | Validate failover mechanisms before production.                                                   |

---

## **Best Practices**
1. **Test Failovers Regularly**: Simulate node failures in staging to validate recovery.
2. **Monitor Sync Lag**: Use tools like `pg_stat_replication` (PostgreSQL) or `SHOW REPLICA STATUS` (MySQL).
3. **Minimize Downtime**: Prioritize low-latency replication (e.g., synchronous for critical data).
4. **Automate Recovery**: Use tools like **Kubernetes Liveness Probes** or **AWS Auto Scaling** to handle failovers.
5. **Document Failover Procedures**: Include steps for manual intervention if automation fails.
6. **Chaos Testing**: Use **Gremlin** or **Chaos Mesh** to inject failures and observe failover behavior.
7. **Alert on Failures**: Set up alerts for prolonged failover events (e.g., via **Slack/PagerDuty**).

---
**Example Failover Procedure (PostgreSQL)**
```sql
-- Check replication status
SELECT * FROM pg_stat_replication;

-- If primary fails, promote a backup:
sudo systemctl restart postgresql@db2
sudo pg_ctl promote -D /var/lib/postgresql/data
```

---
**Key Takeaways**
- Failover Configuration ensures **high availability** by automating recovery.
- **Synchronization** and **health checks** are critical for consistency.
- **Monitoring** and **testing** are non-negotiable for reliability.
- Combine with **Circuit Breakers** and **Retries** for robust fault tolerance.

For further reading, see:
- [AWS Multi-AZ Failover Guide](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_PG_ReadRepl.html)
- [Kubernetes Failover Documentation](https://kubernetes.io/docs/tasks/run-application/configure-pdb/)