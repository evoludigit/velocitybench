---
# **[Pattern] Failover Troubleshooting – Reference Guide**

---

## **Overview**
The **Failover Troubleshooting** pattern ensures system reliability by diagnosing and resolving issues when a primary component (e.g., server, service, or network) fails and falls back to a secondary (backup) resource. This guide outlines methodologies for logging, diagnosing, and mitigating failover failures, covering manual and automated approaches.

Effective failover troubleshooting requires structured logging (e.g., error codes, timestamps), dependency mapping (e.g., DB connections, API endpoints), and systematic rollback procedures. The pattern integrates with **Observability** (logging/metrics) and **Resilience** (retry/logic) patterns to reduce downtime and improve Mean Time to Recovery (MTTR).

---

## **Implementation Details**

### **1. Key Concepts**
| Concept               | Description                                                                                     |
|-----------------------|-------------------------------------------------------------------------------------------------|
| **Primary/Secondary** | Active (primary) and standby (secondary) components that take over in case of failure.         |
| **Failover Trigger**  | Event (e.g., health check failure, latency spike) that initiates failover.                     |
| **Failover Detection**| Mechanism (e.g., heartbeat monitoring, circuit breakers) to identify component degradation.    |
| **Recovery Logic**    | Steps to revert to the primary once the issue is resolved (e.g., manual intervention, auto-heal).|
| **Dependency Mapping**| Tracking interdependencies (e.g., microservices, databases) to ensure synchronized failover.     |

---

### **2. Failure Scenarios & Root Causes**
| Scenario                     | Root Cause Examples                                                                 |
|------------------------------|-------------------------------------------------------------------------------------|
| **Service Unavailability**   | Network partition, container crash, misconfigured service mesh.                      |
| **Database Failover**        | Replication lag, connection timeout, or primary node corruption.                    |
| **API Gateway Failure**      | Rate limiting, misrouted requests, or backend service unavailability.               |
| **Load Balancer Misconfiguration** | Incorrect health checks, stale session data, or regional outages.               |

---

## **Schema Reference**
Below is a **failover troubleshooting schema** for structured logging and root cause analysis.

### **Table 1: Failover Event Log**
| Field               | Type    | Description                                                                                     | Example Value                     |
|---------------------|---------|-------------------------------------------------------------------------------------------------|-----------------------------------|
| `event_id`          | String  | Unique identifier for the failover event.                                                      | `FAIL-20240515-10:45:32`          |
| `timestamp`         | ISO8601 | When the failover was triggered or completed.                                                  | `2024-05-15T10:45:32.123Z`        |
| `component`         | String  | Affected service/component (e.g., `order-service`, `postgres-cluster`).                       | `order-service-primary`            |
| `status`            | Enum    | `FAILED`, `SUCCESS`, `PARTIAL`, `PENDING`.                                                    | `FAILED`                           |
| `primary_node`      | String  | ID of the primary component before failover.                                                  | `node-1`                           |
| `secondary_node`    | String  | ID of the backup component that took over.                                                    | `node-2`                           |
| `cause`             | String  | High-level cause (e.g., `HEALTH_CHECK_FAILED`, `NETWORK_PARTITION`).                         | `HEALTH_CHECK_FAILED`              |
| `root_cause`        | String  | Detailed technical reason (e.g., `DB_CONNECTION_TIMEOUT`, `LISTENER_PORT_CRASH`).              | `DB_CONNECTION_TIMEOUT (5s)`       |
| `dependencies`      | Array   | List of affected dependencies (e.g., databases, APIs).                                       | `["redis-cache", "payment-gateway"]`|
| `duration`          | Duration| Time taken for failover (e.g., `PT0M15S` for 15 seconds).                                     | `PT0M45S`                          |
| `recovery_action`   | String  | Steps taken to recover (e.g., `MANUAL_RESTART`, `AUTO_ROLLBACK`).                            | `AUTO_ROLLBACK`                    |
| `resolved_by`       | String  | User/team responsible for resolution.                                                         | `ops-team@company.com`             |

---

### **Table 2: Failover Health Check Metrics**
| Metric               | Description                                                                                     | Example Value                     |
|----------------------|-------------------------------------------------------------------------------------------------|-----------------------------------|
| `failover_latency`   | Time taken to detect and initiate failover.                                                   | `120ms`                            |
| `secondary_health`   | Health status of the secondary node post-failover (`HEALTHY`, `DEGRADED`, `UNHEALTHY`).         | `HEALTHY`                          |
| `traffic_shift`      | Percentage of traffic redirected to the secondary during failover.                            | `100%` (immediate) or `50%` (gradual)|
| `rollback_time`      | Time taken to revert to primary (if applicable).                                               | `PT0M30S`                          |
| `retries_attempted`  | Number of retry attempts before failing over.                                                  | `3`                                |

---

## **Query Examples**

### **1. Filter Failover Events by Component**
```sql
SELECT *
FROM failover_logs
WHERE component = 'order-service-primary'
  AND status = 'FAILED'
  ORDER BY timestamp DESC
LIMIT 20;
```
**Output:**
| `event_id`          | `timestamp`               | `cause`               | `root_cause`                     |
|---------------------|---------------------------|-----------------------|----------------------------------|
| FAIL-20240515-10:45 | 2024-05-15T10:45:32.123Z | HEALTH_CHECK_FAILED   | LISTENER_PORT_CRASH (port 8080)  |

---

### **2. Identify Long-Duration Failovers**
```sql
SELECT event_id,
       timestamp,
       duration,
       component
FROM failover_logs
WHERE duration > 'PT5M'  -- Failovers lasting >5 minutes
ORDER BY duration DESC;
```
**Output:**
| `event_id`          | `timestamp`               | `duration` | `component`         |
|---------------------|---------------------------|------------|---------------------|
| FAIL-20240514-09:15 | 2024-05-14T09:15:00.000Z | PT15M       | payment-gateway      |

---

### **3. Dependency Impact Analysis**
```sql
SELECT DISTINCT d.dependency
FROM failover_logs fl
JOIN failover_dependencies fd ON fl.event_id = fd.event_id
WHERE fl.cause = 'SERVICE_UNVAILABLE'
  AND fl.timestamp > '2024-05-01';
```
**Output:**
| `dependency`        |
|---------------------|
| redis-cache         |
| payment-gateway     |

---

### **4. Failover Success Rate by Component**
```sql
SELECT component,
       SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) AS success_count,
       SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) AS failure_count,
       SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) /
         (SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) +
          SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END)) AS success_rate
FROM failover_logs
GROUP BY component;
```
**Output:**
| `component`         | `success_count` | `failure_count` | `success_rate` |
|---------------------|-----------------|-----------------|----------------|
| order-service       | 42              | 3               | 0.93           |
| postgres-cluster    | 12              | 2               | 0.86           |

---

## **Troubleshooting Workflow**

### **Step 1: Validate Failover Trigger**
- **Check logs**:
  ```bash
  grep "FAILURE" /var/log/healthchecks/* | tail -n 10
  ```
- **Verify metrics**:
  ```bash
  # Prometheus query for failed health checks
  up{job="order-service-primary"} == 0
  ```

### **Step 2: Diagnose Root Cause**
- **For service failures**:
  ```bash
  docker ps --filter "status=exited"  # Check crashed containers
  journalctl -u order-service         # Container logs
  ```
- **For database issues**:
  ```bash
  pg_isready -h primary-db -p 5432   # Test connection
  show replication lag;              # PostgreSQL lag check
  ```

### **Step 3: Review Dependencies**
- **Check inter-service calls**:
  ```bash
  # Track API call failures via OpenTelemetry traces
  curl http://api-tracer:4318/v1/traces?start_time=now-5m
  ```
- **Database replication status**:
  ```sql
  SELECT pg_is_in_recovery(), pg_last_xact_replay_timestamp();
  ```

### **Step 4: Resolve & Rollback (If Needed)**
- **Manual rollback**:
  ```bash
  # Restart primary if secondary is stable
  kubectl rollout restart deployment/order-service-primary
  ```
- **Automated recovery**:
  ```yaml
  # Kubernetes Liveness Probe adjustment
  livenessProbe:
    httpGet:
      path: /healthz
      port: 8080
    initialDelaySeconds: 30
    timeoutSeconds: 2
  ```

---

## **Related Patterns**
1. **[Resilience: Circuit Breaker]**
   - Use cases: Prevent cascading failures by limiting retries to secondary nodes.
   - Tools: Hystrix, Resilience4j.

2. **[Observability: Distributed Tracing]**
   - Use cases: Trace failover events across microservices.
   - Tools: Jaeger, OpenTelemetry.

3. **[Configuration: Feature Flags]**
   - Use cases: Temporarily disable failover for critical services during outages.

4. **[Synchronization: Event Sourcing]**
   - Use cases: Ensure secondary nodes have consistent state post-failover.

5. **[Scalability: Auto-Scaling]**
   - Use cases: Dynamically adjust secondary node capacity during failover spikes.

---

## **Best Practices**
- **Log everything**: Include `event_id`, `component`, `cause`, and `dependencies`.
- **Automate alerts**: Notify teams via Slack/PagerDuty for prolonged failovers.
- **Test failovers**: Simulate failures (e.g., `kubectl delete pod <primary>`) to validate recovery.
- **Document rollback procedures**: Keep a playbook for manual interventions.
- **Monitor secondary health**: Use tools like Prometheus to track `failover_latency` and `secondary_health`.

---
**End of Reference Guide** (Word count: ~1,100)