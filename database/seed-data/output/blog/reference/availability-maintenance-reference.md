# **[Pattern] Availability Maintenance Reference Guide**

---

## **1. Overview**
The **Availability Maintenance** pattern ensures systems remain operational during planned or unplanned disruptions by dynamically maintaining availability across redundant nodes or services. This pattern is critical for high-availability (HA) architectures, where minimal downtime is required, often measured in **nine-nines** (e.g., 99.999% uptime). It is commonly used in cloud-native, microservices, and distributed systems to handle failures, load balancing, and failover scenarios.

Key use cases include:
- **Automated failover** – Seamless transition between nodes when a primary service fails.
- **Load-based scaling** – Adjusting resource allocation based on demand to avoid bottlenecks.
- **Predictive maintenance** – Proactively shifting traffic away from degrading nodes before failure.
- **Multi-region redundancy** – Distributing workloads across geographically dispersed locations.

This pattern typically combines **health checks**, **traffic routing**, and **stateful session management** to minimize downtime and data loss.

---

## **2. Schema Reference**
The following table defines the core components and their interactions in the **Availability Maintenance** pattern:

| **Component**          | **Description**                                                                 | **Attributes**                                                                 | **Dependencies**                     |
|------------------------|---------------------------------------------------------------------------------|-------------------------------------------------------------------------------|---------------------------------------|
| **Health Monitor**     | Continuously checks the operational status of nodes/services.                   | - Check interval (e.g., `5s`, `1m`)<br>- Timeout threshold (e.g., `30s`)<br>- Grace period (e.g., `10s`) | API endpoints, metrics (Prometheus), external probes |
| **Traffic Director**   | Routes client requests to healthy nodes based on availability metrics.         | - Routing algorithm (round-robin, weighted, least connections)<br>- Health thresholds (e.g., `>50%` healthy) | Health Monitor, Service Mesh (Istio, Linkerd) |
| **Failover Orchestrator** | Coordinates failover logic, including session persistence and data sync.      | - Failover trigger (e.g., `HealthMonitor.UNHEALTHY`)<br>- Replica count (e.g., `3`)<br>- Sync interval (e.g., `5m`) | Database replicas, distributed locks (ZooKeeper, Etcd) |
| **Session Manager**    | Ensures client sessions are preserved during failover using sticky sessions or tokens. | - Session persistence (cookie-based, token-based)<br>- Timeout (e.g., `30m`)<br>- Redundancy (e.g., `2` backups) | Redis, Consul, or in-memory caches |
| **Resource Scaler**    | Dynamically adjusts resource allocation (e.g., pods, VMs) based on load.       | - Scaling policy (e.g., `CPU>80%` → scale up)<br>- Min/max replicas (e.g., `2-10`)<br>- Pre-warming (e.g., `5m` lead time) | Kubernetes HPA, Cloud Auto-Scaling |
| **Backup Replica**     | Mirror of the primary node to enable immediate failover.                       | - Sync strategy (async, semi-sync)<br>- Data consistency (strong/eventual)<br>- Location (same region/geo-replicated) | Database replication, CDNs, object storage |

---

## **3. Implementation Details**
### **3.1 Core Principles**
1. **Redundancy**: Deploy at least `N+1` (e.g., 3 nodes for `N=2`) to handle `N` failures.
2. **Decoupling**: Isolate components (e.g., API vs. DB) to limit blast radius.
3. **Observability**: Monitor health, latency, and errors with centralized logging (e.g., ELK, Grafana).
4. **Graceful Degradation**: Prioritize critical services during outages (e.g., read replicas for writes).

### **3.2 Failure Modes & Mitigations**
| **Failure Mode**               | **Symptom**                          | **Mitigation**                                                                 |
|--------------------------------|--------------------------------------|-------------------------------------------------------------------------------|
| Node crash                     | High latency or `503 Service Unavailable` | Use **Health Monitor** + **Traffic Director** to reroute.                     |
| Network partition              | Split-brain scenario                 | Implement **quorum-based consensus** (e.g., Raft, Paxos) for critical services. |
| Data corruption                | Inconsistent reads                  | Enable **strong consistency** (e.g., PostgreSQL streaming replication).       |
| DDoS attack                    | Resource exhaustion                  | Use **rate limiting** (e.g., Nginx, Envoy) and **auto-scaling**.              |
| Config drift                   | Mismatched node settings            | Enforce **immutable deployments** (e.g., Kubernetes manifests).              |

---

## **4. Query Examples**
### **4.1 Health Check Query (API)**
```http
GET /healthz
Headers:
  Accept: application/json
Response:
{
  "status": "healthy",
  "nodes": [
    {"id": "node-1", "status": "healthy", "latency": "5ms"},
    {"id": "node-2", "status": "unhealthy", "error": "disk-full"}
  ]
}
```

### **4.2 Traffic Routing Rule (Istio VirtualService)**
```yaml
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: my-service
spec:
  hosts:
  - "my-service.example.com"
  http:
  - route:
    - destination:
        host: my-service
        subset: v1
      weight: 90  # 90% traffic to v1
    - destination:
        host: my-service
        subset: v2
      weight: 10  # 10% canary traffic
    retries:
      attempts: 3
      perTryTimeout: 2s
    timeout: 10s
```

### **4.3 Failover Trigger (Kubernetes HPA)**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: my-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: External
    external:
      metric:
        name: requests_per_second
        selector:
          matchLabels:
            app: my-app
      target:
        type: AverageValue
        averageValue: 1000
```

### **4.4 Session Persistence (Redis-backed)**
```python
# Python example using Flask-Session + Redis
from flask import Flask, session
from flask_session import Session

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = {
    'host': 'redis-cluster.example.com',
    'port': 6379,
    'db': 0,
    'socket_timeout': 10,
    'retry_on_timeout': True
}
Session(app)

@app.route('/')
def index():
    session['user'] = "admin"  # Sticky across failovers
    return "Session preserved!"
```

---

## **5. Related Patterns**
| **Pattern**                     | **Description**                                                                 | **When to Use**                                                                 |
|----------------------------------|---------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Circuit Breaker**            | Prevents cascading failures by stopping requests to unhealthy services.         | High-latency APIs or third-party dependencies.                                  |
| **Bulkhead Pattern**           | Isolates failures by limiting concurrent requests to a service.                | Critical paths (e.g., payment processing) to avoid overload.                   |
| **Retry with Exponential Backoff** | Retries failed requests with increasing delays to avoid thundering herds.    | Idempotent operations (e.g., API calls, database writes).                      |
| **Multi-Region Deployment**     | Deploys services across geographic locations to reduce latency and improve resilience. | Global applications (e.g., SaaS platforms).                                  |
| **Chaos Engineering**          | Intentionally injects failures to test resilience.                              | Pre-launch testing or disaster recovery drills.                                |
| **Saga Pattern**               | Manages distributed transactions across services using compensating actions.  | Microservices with long-running workflows (e.g., order processing).            |

---

## **6. Best Practices**
1. **Monitor Proactively**:
   - Set up alerts for `HealthMonitor` failures (e.g., via Prometheus Alertmanager).
   - Use synthetic transactions to simulate user traffic.

2. **Optimize Failover Latency**:
   - Keep replica data **synchronously replicated** for critical services.
   - Minimize **RPO (Recovery Point Objective)** and **RTO (Recovery Time Objective)**.

3. **Test Failures**:
   - Run **chaos experiments** (e.g., kill random pods in Kubernetes).
   - Simulate **network partitions** using tools like [Chaos Mesh](https://chaos-mesh.org/).

4. **Document Rollback Procedures**:
   - Define clear steps to revert to a prior stable state (e.g., Kubernetes rollback).

5. **Cost vs. Availability Tradeoffs**:
   - Balance redundancy (e.g., 3 replicas) with cloud costs (e.g., AWS/Azure pricing).

6. **Compliance Considerations**:
   - Ensure failover meets regulatory requirements (e.g., GDPR for data locality).

---
**See also**:
- [Kubernetes HA docs](https://kubernetes.io/docs/tutorials/clustering/ha-small-cluster/)
- [AWS Multi-AZ Deployment Guide](https://aws.amazon.com/solutions/implementing-high-availability-on-aws/)
- [Istio Traffic Management](https://istio.io/latest/docs/tasks/traffic-management/)