# **[Pattern] Failover Testing – Reference Guide**

## **Overview**
Failover Testing is a resilience engineering pattern used to validate how an application or infrastructure system gracefully recovers from failures in critical components. This pattern ensures high availability by simulating failures (e.g., node crashes, network partitions, or service outages) and verifying automated recovery mechanisms like redundant nodes, backup systems, or circuit breakers. Tested scenarios include primary server failure, database downtime, and dependency service disruptions. Effectiveness is measured by **recovery time (RTO)**, **data integrity**, and **minimal user impact (Uptime SLA adherence)**. Key use cases include cloud architectures, microservices, and distributed systems where reliability is critical.

---

## **Implementation Details**

### **1. Core Concepts**
| **Concept**               | **Description**                                                                                     | **Example**                        |
|---------------------------|-----------------------------------------------------------------------------------------------------|------------------------------------|
| **Failure Modes**         | Types of failures to test (e.g., hardware, software, network, logical).                            | Disk failure, API service outage   |
| **Recovery Mechanisms**   | Automated processes to restore service (e.g., load balancers, failover clusters, cold standby).   | Kubernetes Pod autoscaling         |
| **RTO (Recovery Time Objective)** | Max acceptable downtime post-failure (e.g., < 5 minutes).                                         | 99.99% uptime SLA                   |
| **Chaos Engineering**     | Deliberate introduction of failures to test resilience (e.g., using tools like Gremlin or Chaos Monkey). | Randomly terminating containers    |
| **Monitoring & Logging**  | Tracking metrics (latency, error rates) and audit trails during/after failures.                     | Prometheus alerts for 5xx errors   |
| **Rollback Strategy**     | Plan to revert to a stable state if recovery fails (e.g., blue-green deployments).                | Swapping traffic to a previous version |

---

### **2. Failure Simulation Techniques**
| **Technique**             | **Purpose**                                                                                     | **Tools**                          |
|---------------------------|-------------------------------------------------------------------------------------------------|------------------------------------|
| **Hardware Failures**     | Simulate disk crashes, CPU throttling, or memory leaks.                                         | `stress-ng`, `kill -9 <process>`   |
| **Network Partitioning**  | Test connectivity failures between components (e.g., NATS streaming, gRPC calls).                | `tc qdisc`, `netem`                |
| **Service Overload**      | Flood a service with requests to test throttling/circuit breakers.                              | `k6`, `locust`                     |
| **Dependency Injection**  | Replace a healthy dependency with a simulate failure (e.g., mocking a database).                | `Mock Service Worker`, `Postman`   |
| **Time Synchronization**   | Test systems where clocks are out of sync (e.g., JWT expiration).                               | `ntpdate -q`                       |

---

### **3. Testing Phases**
Failover testing typically follows these phases:

1. **Pre-Test Setup**
   - Define **failure scenarios** (e.g., "Kill primary database node").
   - Configure **monitoring** (e.g., Prometheus, Datadog) for metrics.
   - Isolate test environments (avoid production leaks).

2. **Failure Injection**
   - Use tools to simulate failures (e.g., `kubectl delete pod` for Kubernetes).
   - Example command:
     ```bash
     # Simulate a network partition between pods
     kubectl exec -it podA -- ip link set dev eth0 down
     ```

3. **Observation & Validation**
   - Verify **automatic recovery** (e.g., new pod spun up in Kubernetes).
   - Check **user experience** (e.g., latency spikes, failed transactions).
   - Review logs for errors (e.g., `journalctl -u my-service`).

4. **Post-Test Analysis**
   - Measure **RTO** (time to restore service).
   - Document **failures** and **lessons learned**.
   - Adjust **recovery mechanisms** if needed.

---

## **Schema Reference**
Below is a reference schema for defining failover test configurations in YAML/JSON:

```yaml
failoverTest:
  name: "PrimaryDBNodeCrash"
  environment: "staging"
  steps:
    - action: "kill"
      target: "database-primary"
      duration: "30s"
    - action: "assert"
      condition: "replica-available-after: 5m"
      metric: "db-connections > 0"
  expectedResults:
    RTO: "< 2m"
    DataLoss: "false"
  dependencies:
    - "load-balancer:db-router"
    - "cache:redis-cluster"
```

| **Field**            | **Type**   | **Description**                                                                 | **Example**                     |
|----------------------|------------|---------------------------------------------------------------------------------|---------------------------------|
| `name`               | String     | Unique identifier for the test scenario.                                         | `user-auth-failover`            |
| `environment`        | String     | Target deployment environment (e.g., `prod`, `staging`).                         | `staging`                       |
| `steps.action`       | Enum       | Type of failure: `kill`, `throttle`, `partition`, `override`.                   | `kill`                          |
| `steps.target`       | String     | Resource to fail (e.g., service name, host IP).                                  | `api-gateway:8080`              |
| `steps.duration`     | Duration   | How long to simulate the failure.                                               | `PT10S` (10 seconds)            |
| `expectedResults.RTO`| Duration   | Max acceptable recovery time.                                                    | `PT2M`                          |
| `dependencies`       | List       | Services/resources required for the test.                                        | `[cache-redis, event-bus]`      |

---

## **Query Examples**
### **1. Simulate a Node Failure in Kubernetes**
```bash
# Terminate a pod to test PodDisruptionBudget (PDB)
kubectl delete pod my-app-pod-1 --grace-period=0 --force
```

### **2. Throttle Network Traffic (Using `tc`)**
```bash
# Simulate 50% packet loss between containers
tc qdisc add dev eth0 root netem loss 50%
```

### **3. Kill a Process (Using `kill`)**
```bash
# Forcefully terminate a Java process
pkill -f "MyService.Application"
```

### **4. Validate Recovery with `kubectl`**
```bash
# Check if a replacement pod is running
kubectl get pods -w | grep my-app
```

### **5. Query Monitoring for Failover Metrics**
```bash
# Check Prometheus for 5xx errors during failover
curl "http://prometheus:9090/api/v1/query?query=rate(http_requests_total{status=~\"5..\"}[5m])"
```

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                                     | **When to Use**                          |
|---------------------------|-----------------------------------------------------------------------------------------------------|------------------------------------------|
| **[Circuit Breaker](https://docs.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker)** | Prevents cascading failures by stopping requests to a failing service.                         | High-latency dependencies               |
| **[Bulkhead](https://microservices.io/patterns/reliability/bulkhead.html)**                 | Isolates components to limit failure impact (e.g., thread pools).                                | CPU/memory-intensive services           |
| **[Retry with Exponential Backoff](https://martinfowler.com/eaa Catalog/retry.html)**        | Retries failed operations with increasing delays.                                                 | Transient network issues                |
| **[Rate Limiting](https://docs.microsoft.com/en-us/azure/architecture/patterns/rate-limiting)** | Controls request volume to prevent overload.                                                     | Public APIs                               |
| **[Chaos Engineering](https://chaosengineering.io/)**                                      | Systematically tests resilience by injecting failures.                                            | Greenfield projects, cloud-native apps   |

---

## **Best Practices**
1. **Automate Testing**: Use tools like **Chaos Mesh** (Kubernetes), **Gremlin**, or **Chaos Monkey** to repeat tests.
2. **Isolate Tests**: Run in staging/non-production environments to avoid production leaks.
3. **Gradual Escalation**: Start with low-impact failures (e.g., single pod) before testing cluster-wide outages.
4. **Document Failures**: Maintain a **failure library** to track recurring issues.
5. **Measure RTO/SLA**: Compare recovery times against business requirements.
6. **Collaborate Across Teams**: Include DevOps, SREs, and developers in testing.

---
**See Also**:
- [Resilience Patterns (Microsoft)](https://docs.microsoft.com/en-us/azure/architecture/patterns/)
- [Chaos Engineering Handbook](https://www.oreilly.com/library/view/chaos-engineering-handbook/9781492047082/)