# **[Pattern] Chaos Engineering: Reference Guide**

---

## **Overview**
Chaos Engineering is a systematic approach to improving the **reliability, resilience, and robustness** of distributed systems by intentionally introducing controlled failures. Unlike traditional load testing or chaos monkey-style tools, chaos engineering focuses on probing system limits, validating recovery mechanisms, and identifying hidden dependencies. By simulating real-world disruptions—such as node failures, network partitions, or cascading errors—teams can uncover weaknesses before they impact production. This pattern provides **implementation guidance, best practices, and key considerations** for adopting chaos testing in software systems.

---

## **1. Key Concepts & Schema Reference**

| **Term**               | **Definition**                                                                                     | **Example**                                                                                     |
|------------------------|---------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Chaos Hypothesis**   | A testable assumption about system behavior under failure conditions.                             | *"If the primary database fails, the backup replica will activate within 10 seconds."*       |
| **Chaos Experiment**   | A controlled disruption (e.g., killing a process, throttling network traffic) to validate hypotheses. | Simulating a 99% packet loss between two microservices during a peak load.                |
| **Chaos Toolkit**      | Tools like **Chaos Mesh, Gremlin, or Chaos Monkey** that automate experiment execution.           | Using Chaos Mesh to inject latency spikes in a Kubernetes environment.                         |
| **Chaos Surface**      | The boundary of the system being tested (e.g., specific pods, databases, or AWS regions).         | Limiting experiments to the `user-service` deployment in the `staging` namespace.           |
| **Chaos Blame**        | Identifying the root cause of failures during experiments (e.g., misconfiguration, lack of retries). | A 500-error spike was triggered by a missing circuit breaker in `payment-service`.          |
| **Chaos Safety Net**   | Mechanisms to mitigate accidental production damage (e.g., rollback triggers, circuit breakers). | Auto-scaling down non-critical services if CPU usage exceeds 90%.                            |
| **Synthetic Chaos**    | Automated experiments activated by metrics (e.g., "kill a pod if error rate > 10%").              | Using Prometheus alerts to trigger a disk-fill chaos experiment during high disk usage.    |

---

## **2. Implementation Details**

### **A. Design Principles**
1. **Start Small & Iterate**
   - Begin with **low-risk experiments** (e.g., killing a single container in a non-production environment).
   - Gradually increase scope (e.g., regional outages, multi-tier failures).

2. **Define Clear Hypotheses**
   - Every experiment should answer a **specific question** (e.g., *"Does our auto-scaling handle a 50% pod loss?"*).
   - Use the **Hypothesis-Driven Development (HDD)** framework:
     - **Hypothesis:** *"Our retry logic prevents data loss when a DB fails."*
     - **Experiment:** Kill the primary DB for 30 seconds.
     - **Observation:** Secondary DB failed to sync; data was lost.

3. **Controlled Chaos**
   - **Isolate experiments** to avoid production impact.
   - Use **time-based or condition-based triggers** (e.g., `if (error_rate > 5%) then kill a node`).

4. **Monitor & Observe**
   - Instrument systems with **metrics (Prometheus), logs (Loki), and traces (Jaeger)**.
   - Set up **SLOs (Service Level Objectives)** to measure success (e.g., "99.9% of requests must complete in <500ms").

5. **Safety First**
   - Implement **circuit breakers, rate limiting, and automatic rollback mechanisms**.
   - Test in **staging/production-like environments** before running experiments.

---

### **B. Common Chaos Experiment Types**

| **Experiment Type**       | **Description**                                                                                     | **Tools/Methods**                                                                              |
|---------------------------|---------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Node Failure**          | Kill a server (VM, Kubernetes pod, EC2 instance) to test failover.                                | `kubectl delete pod`, AWS EC2 stop command, Chaos Mesh.                                      |
| **Network Latency**       | Simulate slow networks (e.g., 500ms latency, 30% packet loss).                                       | `tc netem` (Linux), Gremlin network chaos, Chaos Mesh.                                       |
| **Disk Fill**             | Fill disk space to test eviction policies.                                                          | `fallocate -l 90% /dev/sdX`, Chaos Mesh disk-fill.                                            |
| **Crash/Restart**         | Forcefully restart services (e.g., Docker container, Java app server).                             | `docker kill`, `pkill -f <service>`, Chaos Mesh pod chaos.                                    |
| **Data Corruption**       | Inject errors into databases (e.g., corrupt a table row, kill a replication slave).              | `pg_rewind` (PostgreSQL), custom scripts, Gremlin database chaos.                            |
| **Dependency Overload**   | Overwhelm a dependency (e.g., 10x API calls to a slow service).                                    | `locust`, JMeter, or Gremlin API chaos.                                                      |
| **Regional Outage**       | Simulate AWS/Azure region failure (e.g., kill all instances in `us-west-2`).                     | Terraform, Chaos Mesh region chaos.                                                          |
| **Clock Skew**            | Manually set system time to test time-sensitive logic (e.g., session expiry).                     | `date +%Y-%m-%d` (Linux), Gremlin clock skew.                                                |

---

### **C. Best Practices**

1. **Automate Experiments**
   - Use **Chaos Engineering platforms** (e.g., Chaos Mesh, Gremlin, Netflix’s Chaos Monkey).
   - Define experiments as **code** (e.g., YAML templates for Kubernetes Chaos Mesh jobs).

2. **Run in Stages**
   - **Stage 1:** Local/dev environment (e.g., `kubectl apply -f chaos-yaml.yaml`).
   - **Stage 2:** Staging/production-like environment.
   - **Stage 3:** Limited production experiments (e.g., "kill 1% of pods in non-critical services").

3. **Document & Share Findings**
   - Maintain a **Chaos Engineering wiki** with hypotheses, results, and action items.
   - Example template:
     ```
     Experiment: DB Replica Failover
     Hypothesis: Secondary DB will take over in <5s.
     Results: Failed after 12s due to missing health checks.
     Fix: Added `READY` probe to DB pods.
     ```

4. **Integrate with CI/CD**
   - Run **post-deployment chaos tests** (e.g., "if deployment succeeds, run a disk-fill experiment").
   - Example GitHub Action:
     ```yaml
     - name: Run Chaos Test
       if: github.ref == 'refs/heads/main'
       run: chaos-mesh apply -f chaos-tests/disk-fill.yaml
     ```

5. **Measure Impact**
   - Use **SLOs** to quantify reliability improvements.
     - **Before:** "DB failures caused 30% downtime."
     - **After:** "Auto-failover reduced downtime to <1 minute."

---

## **3. Query Examples**

### **A. Chaos Mesh (Kubernetes)**
**Inject Pod Chaos (Kill a Pod)**
```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: pod-kill
spec:
  action: pod-kill
  mode: one
  duration: "1m"
  selector:
    namespaces:
      - default
    labelSelectors:
      app: my-app
```
**Apply the experiment:**
```sh
kubectl apply -f pod-kill.yaml
```

**Introduce Network Latency**
```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: latency
spec:
  action: delay
  mode: one
  duration: "3m"
  selector:
    namespaces:
      - default
    labelSelectors:
      app: my-app
  delay:
    latency: "500ms"
```

---

### **B. Gremlin (Multi-Cloud)**
**Kill an EC2 Instance**
```sh
gremlin kill --host=ec2-12-34-56-78.amazonaws.com --region=us-east-1
```
**Simulate 50% Packet Loss**
```sh
gremlin network --host=api.example.com --packet-loss=50%
```

---

### **C. Custom Scripts (Linux)**
**Kill a Process**
```sh
pkill -f "user-service"
```
**Inject Disk Fill (90%)**
```sh
fallocate -l 90% /dev/sdX && sync
```

---

## **4. Related Patterns**

| **Pattern**               | **Description**                                                                                     | **When to Use**                                                                                  |
|---------------------------|---------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **[Circuit Breaker](https://docs.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker)** | Prevents cascading failures by stopping requests to failing services.                             | When a dependent service is unreliable (e.g., payment gateway).                              |
| **[Retry with Exponential Backoff](https://martinfowler.com/articles/retry.html)**               | Retries failed requests with increasing delays to avoid overload.                               | For idempotent APIs (e.g., database writes).                                                 |
| **[Rate Limiting](https://docs.microsoft.com/en-us/azure/architecture/patterns/rate-limiting)**    | Limits request volume to prevent abuse or throttling.                                            | For public APIs or to protect backend services.                                               |
| **[Multi-Region Deployment](https://docs.microsoft.com/en-us/azure/architecture/guide/technology-choices/multi-region-deployment)** | Deploys services across regions for disaster recovery.                                         | For globally distributed applications (e.g., Netflix).                                       |
| **[Feature Flags](https://launchdarkly.com/blog/feature-flags/)**                              | Enables/disables features dynamically without redeploying.                                       | For gradual rollouts or disabling buggy features.                                            |
| **[Observability Stack](https://www.newrelic.com/observability)**                              | Combines metrics, logs, and traces for root cause analysis.                                      | Post-chaos experiments to debug failures.                                                   |

---

## **5. Anti-Patterns & Pitfalls**
| **Anti-Pattern**               | **Risk**                                                                                       | **Mitigation**                                                                                  |
|---------------------------------|------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Running Chaos in Production Without Safety Nets** | Risk of cascading failures or data loss.                                                       | Always use **safety nets** (e.g., auto-rollback, circuit breakers).                            |
| **Testing Only Happy Paths**    | Misses real-world failure modes.                                                                | Test **edge cases** (e.g., concurrent failures, dependency overloads).                          |
| **No Clear Hypotheses**         | Experiments lack purpose; results are hard to interpret.                                        | Define **testable hypotheses** before running experiments.                                      |
| **Ignoring Observability**      | Cannot diagnose failures during or after experiments.                                          | Instrument with **metrics, logs, and traces** before chaos testing.                           |
| **Overloading Chaos Tools**     | Tools may conflict or degrade system performance.                                               | Schedule experiments during **low-traffic windows**.                                           |

---
## **6. Further Reading**
- **[Chaos Engineering at Netflix](https://netflix.github.io/chaosengineering/)** – Original chaos monkey implementation.
- **[Gremlin Chaos Engineering](https://gremlin.com/)** – Enterprise-grade chaos testing.
- **[Chaos Mesh Docs](https://chaos-mesh.org/)** – Kubernetes-native chaos experiments.
- **[Resilient Systems Book](https://www.oreilly.com/library/view/resilient-software-patterns/9781492074472/)** – Patterns for building fault-tolerant systems.