# **[Pattern] Chaos Engineering: Learning from Controlled Failures Reference Guide**

---

## **Overview**
Chaos engineering is a systematic approach to improving system reliability by intentionally introducing **controlled failures** to uncover hidden weaknesses. Instead of reacting to unexpected outages, teams proactively test failure scenarios (e.g., node crashes, network latency, or database corruption) to assess resilience and refine failure recovery mechanisms. By analyzing system behavior under stress, organizations can preemptively address vulnerabilities, reducing downtime and improving user confidence.

This pattern applies to distributed systems (microservices, cloud-native architectures) but can be adapted for monolithic applications. It requires collaboration between engineering, operations, and security teams to define safe failure thresholds and mitigation strategies.

---

## **Key Concepts & Schema Reference**

### **Core Principles**
| **Concept**               | **Description**                                                                                     | **Example**                                                                 |
|---------------------------|-----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **Hypothesis Testing**    | Define assumptions about system behavior under failure (e.g., "The system will fail if 50% of API calls are lost"). | *"If a database replica fails, the primary can handle 10% increased load."* |
| **Blameless Postmortems** | Analyze failures without assigning guilt; focus on root causes and process improvements.          | Reviewing a node crash to identify configuration missteps, not individual errors. |
| **Graceful Degradation**  | Systems should fail predictably (e.g., degrade performance) rather than catastrophically.           | A video streaming service reducing resolution during network congestion.     |
| **Controlled Chaos**      | Failures must be **temporary**, **reversible**, and **non-production** unless explicitly modeled.  | Simulating a regional outage in staging before applying to production.       |
| **Feedback Loop**         | Automate monitoring and alerting to detect anomalies during chaos experiments.                    | Slack alerts for latency spikes during a simulated disk failure.             |

---

### **Schema Reference**
Below is a structured breakdown of chaos engineering components:

| **Component**            | **Attributes**                                                                                     | **Data Type**       | **Example Values**                                  |
|--------------------------|---------------------------------------------------------------------------------------------------|---------------------|-----------------------------------------------------|
| **Experiment**           |                                                                                                   |                     |                                                     |
| - `name`                 | Human-readable identifier for the experiment.                                                   | String              | `db-replica-failure-test`                           |
| - `description`          | Purpose and expected outcomes of the experiment.                                                 | String              | *"Test if the system recovers from losing a Redis replica."* |
| - `duration`             | How long the failure will persist (e.g., 5 minutes, 1 hour).                                     | String (ISO 8601)   | `PT30M` (30 minutes)                                |
| - `target`               | System/service/subsystem to fail (e.g., `redis-slave-01`).                                       | String              | `/services/user-api`                                |
| - `failure-mode`         | Type of failure to induce (e.g., `kill-process`, `network-latency`, `disk-corruption`).           | Enum                | `kill-process`, `network-latency`                    |
| - `severity`             | Impact level (low/medium/high) based on risk assessment.                                          | Enum                | `medium`                                            |
| - `recovery-script`      | Commands/script to revert the failure (e.g., `docker restart`).                                   | String              | `kubectl rollout restart deployment/web-server`       |
| - `metrics-to-monitor`   | Key performance indicators (KPIs) to observe during the experiment (e.g., latency, error rates). | Array               | `[p99-latency, error-rate, throughput]`             |
| - `thresholds`           | Alerting thresholds (e.g., latency > 500ms triggers a warning).                                  | Object              | `{ "latency": { "warning": 300, "critical": 500 } }`|
| - `environment`          | Deployment stage (dev/staging/production) where the experiment runs.                             | Enum                | `staging`                                           |
| - `tags`                 | Labels for categorization (e.g., `database`, `network`).                                          | Array               | `["database", "recovery"]`                          |

---

## **Implementation Steps**

### **1. Define Goals & Hypotheses**
- **Objective**: Identify what you want to learn (e.g., "Does the system handle a regional outage?").
- **Hypothesis**: Formulate a testable statement (e.g., *"If we kill 30% of the API nodes, the remaining nodes will handle the load without errors."*).
- **Tools**: Use case management tools like **Confluence** or **Jira** to document hypotheses.

### **2. Choose a Chaos Tool**
Select a tool based on your infrastructure:
| **Tool**               | **Best For**                          | **Key Features**                                      |
|------------------------|---------------------------------------|-------------------------------------------------------|
| **Gremlin**            | Cloud-native, microservices           | GUI/automation, real-time telemetry, team collaboration. |
| **Chaos Mesh**         | Kubernetes environments              | Built-in Kubernetes operators, YAML-based experiments.  |
| **Chaos Monkey**       | AWS-based systems                     | Randomly terminates instances; simple CLI.            |
| **Netflix Simian Army**| Legacy/on-prem systems                | Collection of tools (e.g., Chaos Gorilla, Latency Monkey). |
| **Custom Scripts**     | Lightweight, ad-hoc testing           | Bash/Python scripts to kill processes or inject latency. |

---

### **3. Design the Experiment**
#### **Example: Simulating a Database Replica Failure**
```yaml
# Chaos Mesh Experiment (YAML)
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: kill-db-replica
spec:
  action: pod-kill
  mode: one
  selector:
    namespaces:
      - "database"
    labelSelectors:
      app: "redis-slave"
  duration: "1h"
  recovery:
    command: "kubectl rollout restart deployment/redis-slave"
  metrics:
    - name: "redis-latency"
      severity: "warning"
      threshold: "500ms"
```

#### **Key Parameters to Configure**:
- **`action`**: Type of chaos (e.g., `pod-kill`, `network-delay`, `disk-pressure`).
- **`selector`**: Target pods/services (use labels or namespaces).
- **`duration`**: How long the failure persists (avoid exceeding SLOs).
- **`recovery`**: Automated rollback (e.g., restarting a service).
- **`metrics`**: Define monitoring thresholds (integrate with Prometheus/Grafana).

---

### **4. Run the Experiment**
1. **Deploy the Chaos Tool**: Initialize the tool in your target environment (e.g., `helm install chaos-mesh --repo https://charts.chaos-mesh.org`).
2. **Execute the Experiment**: Apply the YAML/config to trigger the failure.
   ```bash
   kubectl apply -f db-replica-failure.yaml
   ```
3. **Observe & Monitor**:
   - Use **Prometheus alerts** or **Grafana dashboards** to track metrics.
   - Log anomalies in tools like **Loki** or **ELK Stack**.
   - Example alert rule:
     ```yaml
     - alert: HighRedisLatency
       expr: redis_latency_seconds > 0.5
       for: 5m
       labels:
         severity: warning
       annotations:
         summary: "Redis latency spike during chaos experiment"
     ```

---

### **5. Analyze Results**
- **Metrics**: Compare pre- and post-experiment data (e.g., error rates, recovery time).
- **Log Analysis**: Review logs for unexpected errors or cascading failures.
- **Postmortem**: Document findings and update runbooks. Example template:
  > **Findings**: The system degraded gracefully but took 8 minutes to recover. **Action**: Optimize retry logic in `serviceA` to reduce recovery time.

---

### **6. Iterate & Improve**
- Revisit **hypotheses** based on outcomes.
- Adjust **failover mechanisms** or **circuit breakers**.
- Schedule **recurring experiments** to test new deployments or configurations.

---

## **Query Examples**

### **1. Listing Active Chaos Experiments**
```bash
# List all running chaos experiments in Kubernetes
kubectl get experiments -A
```
**Output**:
```
NAMESPACE   NAME                 TYPE            AGE
default     db-replica-failure   pod-kill         2h
staging     api-network-latency  network-delay   1h
```

---

### **2. Checking Metrics During an Experiment**
```bash
# Query Prometheus for latency during a chaos experiment
kubectl exec -it prometheus-server -- prometheus query \
  'up{job="redis", namespace="database"}' --start-time 5m
```

---

### **3. Automated Alerting with Thanos**
```bash
# Query Thanos for alerting rules triggered during chaos
thanos query \
  --query='sum(rate(alertmanager_alerts_sent_total[5m])) by (alertname)' \
  --time.filter.relative=5m
```

---

### **4. Rolling Back a Failed Experiment**
```bash
# Revert a pod-kill experiment
kubectl rollout restart deployment/redis-slave
```

---

## **Best Practices**

1. **Start Small**: Begin with low-impact experiments (e.g., killing a single pod) before scaling to multi-service failures.
2. **Scope Control**: Limit experiments to specific teams/environments (e.g., `team-x-staging`).
3. **Communicate**: Notify teams in advance to avoid confusion during experiments.
4. **Automate Recovery**: Ensure experiments self-heal to avoid prolonged outages.
5. **Document Everything**: Track experiments in a database (e.g., **Chaos Toolkit’s results** or **GitLab CI artifacts**).
6. **Compliance**: Ensure experiments comply with security policies (e.g., no production accidents).

---

## **Common Pitfalls & Mitigations**

| **Pitfall**                          | **Mitigation**                                                                                     |
|---------------------------------------|---------------------------------------------------------------------------------------------------|
| **Uncontrolled Cascading Failures**   | Use circuit breakers (e.g., Hystrix, Resilience4j) and limit experiment scope.                  |
| **False Positives in Metrics**        | Validate metrics with manual verification (e.g., `curl` checks).                                   |
| **Production Accidents**              | Run experiments in **staging** or **canary environments** first.                                    |
| **Underestimating Recovery Time**     | Set conservative `duration` values and test recovery scripts in isolation.                        |
| **Lack of Blameless Culture**         | Encourage postmortems without blame; focus on process improvements.                              |

---

## **Related Patterns**

| **Pattern**                          | **Description**                                                                                     | **When to Use**                                                                                     |
|---------------------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| **[Circuit Breaker](https://refactoring.guru/patterns)** | Temporarily stops calling a failing service to prevent cascading failures.                          | When a downstream service is unreliable (e.g., third-party APIs).                                      |
| **[Retry with Exponential Backoff](https://www.awsarchitectureblog.com/2015/03/retry-cache-stale-data-at-the-edges-with-amazon-cloudfront.html)** | Retries failed requests with increasing delays to avoid overwhelming systems.                  | Handling transient errors (e.g., network timeouts).                                                   |
| **[Rate Limiting](https://blog.cloudflare.com/rate-limiting/)** | Limits the number of requests to prevent abuse or overload.                                         | Protecting APIs from DDoS or sudden traffic spikes.                                                    |
| **[Blue-Green Deployment](https://martinfowler.com/bliki/BlueGreenDeployment.html)** | Deploys updates to a separate environment and switches traffic only after validation.              | Reducing downtime during deployments (complements chaos engineering for testing resilience).          |
| **[Chaos Mesh Observability](https://chaos-mesh.org/docs/)** | Integrates chaos engineering with observability tools (e.g., Prometheus, OpenTelemetry).           | Debugging complex distributed systems during experiments.                                              |

---

## **Further Reading**
- **Book**: *Chaos Engineering: System Resilience via Cybernetic Attacks* by Greg Ferro.
- **Tool Docs**:
  - [Chaos Mesh](https://chaos-mesh.org/docs/)
  - [Gremlin](https://www.gremlin.com/docs/)
- **Case Studies**:
  - [Netflix’s Chaos Engineering](https://netflixtechblog.com/chaos-engineering-at-netflix-1627ab9f969e)
  - [Spotify’s Triage](https://medium.com/spotify-engineering/triage-our-chaos-engineering-platform-for-production-environments-101690774722)