# **[Pattern] Failover Gotchas: Reference Guide**

---

## **Overview**
Failover is a critical resilience mechanism that ensures system continuity during hardware/software failures or outages. However, improperly implemented failover can introduce subtle but catastrophic issues—what we call **"Failover Gotchas."** This guide provides a structured breakdown of common failure points, validation criteria, and best practices to avoid pitfalls in multi-region, multi-cluster, or active-passive systems. From state synchronization delays to cascading failures, this reference covers both architectural and operational pitfalls, helping teams design robust failover mechanisms.

---

## **Schema Reference**
Below are key components of a failover system and their potential failure points.

| **Component**               | **Description**                                                                 | **Common Gotcha**                                                                 | **Mitigation Strategy**                                                                 |
|-----------------------------|---------------------------------------------------------------------------------|------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| **Failover Trigger**        | Mechanism that detects failure (health checks, alerts, or manual intervention). | False positives/negatives due to misconfigured thresholds or noisy neighbors.       | Use multi-vantage point monitoring (e.g., client and server-side checks).                |
| **State Synchronization**   | Ensuring data consistency between primary and standby systems.                 | Inconsistent state due to network latency, replication lag, or partial updates.     | Implement **strong eventual consistency** (e.g., CRDTs, conflict-free replicated data types) or **quorum-based syncs**. |
| **Network Topology**        | Underlying infrastructure connecting failover nodes (e.g., VPN, direct links).  | Latency spikes causing timeouts or traffic blackholing.                             | Deploy **low-latency failover links** (e.g., BGP anycast, CDN edge failover).           |
| **Authentication/Authorization** | Credential propagation or token validation during failover.             | Session tokens invalidated after failover, leading to authentication storms.        | Use **short-lived tokens + refresh mechanisms** or **session sticky policies**.          |
| **Draining Traffic**        | Graceful shutdown of connections during failover.                             | Active connections dropped abruptly, causing client retries or timeouts.           | Implement **TCP FIN/TCP_RST handling** or **session persistence** (e.g., stickiness cookies). |
| **Dependency Failures**     | Failover of third-party services (e.g., databases, caches)                    | Cascading failures if dependencies don’t synchronously fail over.                   | Test **inter-service failover dependencies** in isolation.                               |
| **Logging & Observability** | Visibility into failover events and recovery status.                          | Logs siloed to failed nodes or missing failure context.                           | Centralize logs with **correlation IDs** and **failover-specific metrics** (e.g., RTO/RPO). |
| **Rollback Mechanism**      | Process to revert to a previous state if failover fails.                       | No clear rollback path, leading to prolonged outages.                              | Design **atomic failover transactions** or **blue-green deployment** rollback paths.    |
| **Client-Side Handling**    | How clients detect and recover from failover.                                 | Clients retrying wrong nodes or blindly assuming failover success.                 | Enforce **client-side failover policies** (e.g., exponential backoff, retry filters).    |
| **Cost Management**         | Resource costs of maintaining standby systems.                                | Unused standby systems incurring unnecessary costs.                                | Use **auto-scaling standby nodes** or **spot instances** for non-critical workloads.    |

---

## **Implementation Details**
Failover **gotchas** fall into three categories:

### **1. Architectural Pitfalls**
- **Inconsistent State Across Regions**
  - *Problem*: If primary-write replication doesn’t sync in time, standby nodes serve stale data.
  - *Example*: User upgrades profile, but failover to standby serves the old version.
  - *Fix*: Use **strong consistency models** (e.g., Paxos, Raft) or **synchronous replication**.

- **Single Point of Failure (SPOF) in Failover Logic**
  - *Problem*: A centralized failover controller becomes the bottleneck or failure point.
  - *Example*: All nodes rely on a single API endpoint to detect failover—if that endpoint fails, no recovery.
  - *Fix*: Distribute failover logic (e.g., **leader election algorithms** like Raft).

- **Network Partition Awareness**
  - *Problem*: Failover assumes network partitions are recoverable, but they may persist.
  - *Example*: Database splits into two partitions; both declare themselves primary.
  - *Fix*: Implement **partition detection** (e.g., **Gossip protocols**) and **quorum-based decisions**.

### **2. Operational Pitfalls**
- **False Positives in Health Checks**
  - *Problem*: A "healthy" node is incorrectly marked as failed due to flaky metrics.
  - *Example*: CPU load spikes due to a burst of traffic → node fails over, but it was just temporary.
  - *Fix*: Use **statistical health checks** (e.g., moving averages) or **multi-metric validation**.

- **Incomplete Data Migration**
  - *Problem*: Failover cuts over before all data is replicated.
  - *Example*: User data is partially transferred; failover serves inconsistent records.
  - *Fix*: Enforce **data consistency checks** before promoting standby (e.g., **pre-failover sync validation**).

- **Improper Session Handling**
  - *Problem*: Client sessions are invalidated during failover, forcing reauthentication.
  - *Example*: User logs in → fails over → session token expires → login loop.
  - *Fix*: Use **sticky sessions** or **short-lived tokens with refresh endpoints**.

### **3. Client-Side Failover Issues**
- **Retry Storms After Failover**
  - *Problem*: Clients aggressively retry failed requests, overwhelming the new primary.
  - *Example*: 10,000 clients retry simultaneously after a failover → new primary crashes.
  - *Fix*: Implement **client-side backoff** (e.g., exponential delay) and **rate limiting**.

- **Incorrect Failover Target Selection**
  - *Problem*: Clients don’t update their failover endpoint after the primary changes.
  - *Example*: Client keeps calling `old-primary.example.com` instead of `new-primary.example.com`.
  - *Fix*: Use **DNS-based failover** (e.g., Azure Traffic Manager) or **service discovery** (e.g., Consul).

- **Timeout Configurations**
  - *Problem*: Clients timeout too quickly, assuming failure when network latency is normal.
  - *Example*: DNS failover takes 3s → client times out after 2s → spam of retries.
  - *Fix*: Set **adaptive timeouts** based on observed latency.

---

## **Query Examples**
### **1. Detecting Inconsistent State Between Regions**
```sql
-- Check for stale records in region B after failover from region A
SELECT COUNT(*)
FROM user_profiles
WHERE region = 'B' AND last_updated < (SELECT MAX(last_updated) FROM user_profiles WHERE region = 'A');
```

### **2. Monitoring Failover Latency**
```bash
# Measure time taken for failover notifications to propagate (Prometheus example)
duration_seconds{job="failover_metrics"} = failover_start_time - last_heartbeat_time
```

### **3. Identifying False Failover Triggers**
```bash
# Alert if health check failures occur without actual outages
alert(HealthCheckFlakinessHigh)
  when sum(rate(health_check_failures[5m])) by (service) > 3 and
    avg_over_time(health_check_failures[1h]) == 0
```

### **4. Validating Session Persistence During Failover**
```python
# Check if session tokens remain valid after failover (Python + Redis)
def test_session_persistence():
    token = generate_token(user_id="123")
    assert validate_token(token) == True  # Before failover
    perform_failover()
    assert validate_token(token) == True  # After failover (should not expire)
```

---

## **Related Patterns**
| **Pattern**                     | **Description**                                                                 | **Why It Complements Failover Gotchas**                                                                 |
|----------------------------------|---------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| **[Circuit Breaker](https://microservices.io/patterns/reliability/circuit-breaker.html)** | Temporarily stops requests to a failing service to prevent cascading failures. | Mitigates retry storms and dependency failures during failover.                                         |
| **[Bulkheads](https://microservices.io/patterns/reliability/bulkhead.html)**               | Isolates failures in one component from affecting others.                       | Prevents a single failover from collapsing the entire system.                                          |
| **[Retry with Backoff](https://www.awsarchitectureblog.com/2015/03/efficient-retry-strategies-for-retries.html)** | Exponentially increase retry delays to avoid overloading systems.          | Reduces client-side bottlenecks during failover recovery.                                               |
| **[Idempotency](https://martinfowler.com/bliki/IdempotentOperation.html)**               | Ensures repeated operations have the same effect as a single operation.         | Prevents duplicate requests during failover from causing data corruption.                              |
| **[Chaos Engineering](https://chaoss.github.io/)**                                        | Proactively test system resilience by injecting failures.                     | Uncovers hidden failover gotchas in staging environments before production.                            |

---

## **Key Takeaways**
1. **Validate State Consistency**: Ensure standby systems mirror primary data before promoting.
2. **Test Failover End-to-End**: Simulate network partitions, dependency failures, and client behaviors.
3. **Monitor Failover Metrics**: Track RTO (Recovery Time Objective) and RPO (Recovery Point Objective).
4. **Document Rollback Procedures**: Know how to revert if failover fails.
5. **Communicate Failover Events**: Log and alert stakeholders during failover transitions.

By addressing these gotchas proactively, teams can build **resilient failover systems** that minimize downtime and data loss.