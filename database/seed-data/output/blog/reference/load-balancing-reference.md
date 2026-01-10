# **[Pattern] Load Balancing Strategies & Algorithms – Reference Guide**

---

## **1. Overview**
Load balancing dynamically distributes client requests across multiple servers (backend services, microservices, or data partitions) to:
- **Optimize performance** by reducing response latency.
- **Maximize throughput** by preventing overloading any single server.
- **Ensure high availability** with failover capabilities.
- **Improve fault tolerance** through redundancy.

This pattern is critical in distributed systems, microservices architectures, and cloud-based applications. Algorithms differ in how they select servers, balancing trade-offs between fairness, simplicity, and fault tolerance. Common strategies include **round-robin, least-connections, weighted random, IP hash, and sticky sessions**, each suited to specific use cases (e.g., latency-sensitive vs. request-volume-optimized workloads).

---

## **2. Schema Reference**

| **Component**               | **Description**                                                                                     | **Parameters**                                                                                     | **Example Values/Notes**                                                                 |
|-----------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| **Load Balancer**           | Centralized or decentralized entity directing requests to servers.                                 | `backend_servers`, `health_checks`, `algorithm`, `session_persistence`                          | `"backend_servers": ["server1:8080", "server2:8080"]`                                      |
| **Request**                 | Incoming client query with metadata (e.g., timestamps, session ID).                                | `timestamp`, `session_id`, `method`, `path`, `headers`, `payload`                               | `{"timestamp": "2024-01-01T12:00:00", "session_id": "abc123"}`                          |
| **Server**                  | Backend service with metadata (e.g., current connections, response time, weight).                  | `id`, `status` (active/inactive), `connections`, `response_time`, `weight`                     | `{"id": "server1", "status": "active", "weight": 2}`                                       |
| **Algorithm**               | Logic for selecting servers.                                                                       | `type` (e.g., `ROUND_ROBIN`, `LEAST_CONNECTIONS`, `WEIGHTED_RANDOM`), `params`                  | `{"type": "WEIGHTED_RANDOM", "params": {"weights": [2, 1]}}`                              |
| **Health Check**            | Mechanism to validate server availability (e.g., HTTP ping, latency threshold).                     | `interval`, `timeout`, `success_threshold`, `failure_threshold`                                  | `{"interval": "5s", "timeout": "2s", "success_threshold": 2}`                            |
| **Session Persistence**     | Ensures requests from the same session go to the same server (e.g., via `JSESSIONID` or IP hash). | `strategy` (`NONE`, `COOKIE_BASED`, `IP_HASH`), `cookie_name`                                  | `{"strategy": "IP_HASH"}`                                                                |
| **Monitoring Metrics**      | Tracked metrics for performance tuning (e.g., queue length, error rates).                          | `requests_processed`, `error_rate`, `avg_latency`, `server_utilization`                         | `{"avg_latency": "150ms", "server_utilization": [0.7, 0.3]}`                              |

---

## **3. Algorithm Reference**

### **3.1 Supported Algorithms**
| **Algorithm**         | **Description**                                                                                     | **Use Case**                                                                                     | **Pros**                                                                                   | **Cons**                                                                                   |
|-----------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| **Round-Robin**       | Rotates servers sequentially (no prioritization).                                                  | Simple, low-latency requests (e.g., static content).                                            | Simple to implement.                                                                       | No consideration for server load or performance.                                        |
| **Least Connections** | Directs requests to the server with the fewest active connections.                                  | CPU/memory-bound workloads (e.g., database queries).                                             | Fair distribution of load.                                                                | Overhead from tracking connections.                                                     |
| **Weighted Random**   | Servers are selected probabilistically based on assigned weights.                                   | Heterogeneous servers (e.g., different capacities).                                            | Flexible; prioritizes high-capacity servers.                                              | Requires manual weight tuning.                                                            |
| **IP Hash**           | Uses client IP to assign requests to a fixed server (sticky sessions).                              | Session-affinity needed (e.g., shopping carts).                                                 | Consistent session handling.                                                              | Poor load balancing if client IPs are skewed.                                          |
| **Least Response Time**| Selects the server with the lowest average response time.                                         | Latency-sensitive applications (e.g., real-time APIs).                                          | Optimizes for speed.                                                                        | Requires frequent monitoring of response times.                                         |
| **Weighted Least Conn**| Combines `Least Connections` with server weights.                                                  | Mixed workloads with variable server capacities.                                                | Balances fairness and performance.                                                       | Complex to implement.                                                                  |
| **Consistent Hashing** | Maps keys (e.g., request IDs) to servers to minimize rebalancing.                                  | Large-scale distributed systems (e.g., Cassandra).                                            | Efficient rebalancing; minimizes data migration.                                        | Requires consistent key distribution.                                                   |

---

### **3.2 Algorithm Selection Guide**
| **Scenario**                          | **Recommended Algorithm**       | **Why?**                                                                                     |
|---------------------------------------|----------------------------------|-----------------------------------------------------------------------------------------------|
| Low-latency, stateless requests        | Round-Robin                      | Simplest; no overhead.                                                                         |
| Stateless, high-throughput workloads  | Least Connections                | Prevents overloading any single server.                                                       |
| Heterogeneous servers                 | Weighted Random                  | Allocates traffic proportional to server capacity.                                            |
| Session persistence required          | IP Hash or Cookie-Based          | Ensures consistency for stateful sessions.                                                   |
| Mixed workloads (e.g., DB + API)      | Weighted Least Conn              | Balances connections and server importance.                                                   |
| Distributed key-value stores          | Consistent Hashing               | Minimizes data redistribution during server changes.                                          |

---

## **4. Implementation Details**

### **4.1 Core Components**
1. **Load Balancer**:
   - **Centralized**: Single process (e.g., Nginx, HAProxy) directs all traffic.
   - **Decentralized**: Client-side (e.g., DNS round-robin) or service mesh (e.g., Istio).
   - **Edge vs. Cloud**: Cloud providers (AWS ALB, GCP LB) often include built-in load balancing.

2. **Health Checks**:
   - **Active**: Load balancer probes servers (e.g., HTTP `HEAD /health`).
   - **Passive**: Monitors server responses to failures (e.g., 5xx errors).
   - **Thresholds**: Adjust `success_threshold` (e.g., 2 successful probes) and `failure_threshold` (e.g., 3 failures to mark as down).

3. **Session Persistence**:
   - **Cookie-Based**: Sets a cookie (e.g., `JSESSIONID`) to redirect to the same server.
   - **IP Hash**: Hashes client IP to a server ID (e.g., `hash(client_ip) % num_servers`).
   - **URL Rewrite**: Appends session ID to URL (less common; security risk).

4. **Dynamic Reconfiguration**:
   - **Hot Reloading**: Update server weights or algorithms without downtime (e.g., Kubernetes `Service` with `endpoints`).
   - **Traffic Shifting**: Gradually migrate traffic (e.g., using `weight` in Kubernetes `Service`).

---

### **4.2 Example Code Snippets**
#### **Python (Flask + Round-Robin)**
```python
from flask import Flask
import requests

app = Flask(__name__)
servers = ["http://server1:8080", "http://server2:8080"]
server_index = 0

@app.route("/")
def proxy():
    global server_index
    server = servers[server_index]
    server_index = (server_index + 1) % len(servers)  # Round-robin
    return requests.get(server + "/").text
```

#### **Bash (DNS Round-Robin)**
```bash
# /etc/hosts file (simulated)
192.168.1.10 server1.example.com
192.168.1.11 server2.example.com
# Client resolves to servers in rotation via DNS.
```

#### **Kubernetes (Weighted Load Balancer)**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-app
spec:
  ports:
  - port: 80
    targetPort: 8080
  selector:
    app: my-app
  sessionAffinity: ClientIP  # IP Hash persistence
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app-server1
spec:
  replicas: 2
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
        server: server1
    spec:
      containers:
      - name: app
        image: my-app:v1
        resources:
          limits:
            cpu: "500m"
            memory: "512Mi"
```

---

## **5. Query Examples**
### **5.1 Selecting a Server**
**Input**:
- Request: `GET /api/users`
- Servers: `[{"id": "s1", "status": "active", "weight": 2}, {"id": "s2", "status": "active", "weight": 1}]`
- Algorithm: `WEIGHTED_RANDOM`

**Output**:
- Probability: `s1` (66.6%), `s2` (33.3%).
- Sample selection: `s1` (66% chance).

**Command Line (CLI Tool)**:
```bash
loadbalancer select --algorithm weighted_random --weights 2,1 --servers s1,s2
# Output: s1
```

---

### **5.2 Health Check Failure**
**Input**:
- Server `s1` fails 3 active probes in a row (`failure_threshold=3`).
- Current servers: `[{"id": "s1", "status": "active"}, {"id": "s2", "status": "active"}]`.

**Output**:
- `s1` marked as `inactive`.
- Traffic rerouted to `s2`.

**API Call**:
```bash
curl -X POST http://localhost:3000/health/check \
  -H "Content-Type: application/json" \
  -d '{"server_id": "s1", "status": "failed"}'
```

---

### **5.3 Session Persistence**
**Input**:
- Client IP: `192.168.1.100`
- Servers: `[s1, s2]`
- Algorithm: `IP_HASH`

**Output**:
- Hash: `hash("192.168.1.100") % 2 = 0` → `s1`.
- Subsequent requests from `192.168.1.100` always go to `s1`.

**Pseudocode**:
```python
def get_server(ip, servers):
    hash_val = hash(ip) % len(servers)
    return servers[hash_val]
```

---

## **6. Monitoring & Metrics**
| **Metric**               | **Description**                                                                                     | **Tools**                                                                                     |
|--------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| **Request Rate**         | Throughput per second (e.g., RPS).                                                                   | Prometheus, Datadog.                                                                        |
| **Error Rate**           | % of failed requests (e.g., 5xx errors).                                                            | Custom logging + Grafana dashboards.                                                         |
| **Server Latency**       | Average response time per server.                                                                   | APM tools (New Relic, AppDynamics).                                                          |
| **Connection Pool**      | Active connections per server.                                                                     | `jstack` (Java), `netstat` (Linux).                                                          |
| **Queue Length**         | Requests waiting in the load balancer queue.                                                       | Custom metrics (e.g., `queue_length` in Prometheus).                                      |
| **Health Check Failures**| Rate of failed health probes.                                                                       | Load balancer metrics (e.g., HAProxy `proxy_stat`).                                       |

**Example Query (PromQL)**:
```promql
# Error rate (5xx) per server
sum(rate(http_requests_total{status=~"5.."}[1m])) by (server)
```

---

## **7. Failure Modes & Mitigations**
| **Failure**                          | **Cause**                                                                                     | **Mitigation**                                                                              |
|--------------------------------------|-------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------|
| **Server Overload**                   | Too many requests to a single server.                                                       | Use `Least Connections` or `Weighted Random`.                                              |
| **Sticky Session Imbalance**         | Uneven distribution due to session affinity.                                                 | Monitor session distribution; adjust `IP_HASH` keys.                                       |
| **Health Check False Positives**     | Misconfigured thresholds (e.g., slow but stable server).                                  | Increase `timeout` or relax `failure_threshold`.                                            |
| **Algorithm Drift**                   | Servers added/removed without rebalancing.                                                  | Use consistent hashing or dynamic reconfiguration.                                         |
| **Network Partition**                 | Load balancer isolated from backend servers.                                                 | Enable passive health checks + retry logic.                                                |
| **Cold Start Latency**                | New server added with no warm-up traffic.                                                    | Pre-warm servers or use gradual traffic shift.                                             |

---

## **8. Related Patterns**
| **Pattern**                      | **Description**                                                                                     | **Integration Example**                                                                       |
|-----------------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| **Circuit Breaker**               | Prevents cascading failures by halting traffic to failing services.                              | Load balancer routes to `CircuitBreaker` wrapper before servers.                           |
| **Retry with Backoff**            | Retries failed requests with exponential backoff.                                               | Combined with `Least Response Time` for resilient APIs.                                   |
| **Rate Limiting**                 | Limits requests per server to prevent abuse.                                                    | Applied at load balancer level (e.g., Redis rate limiter).                                 |
| **Service Mesh**                  | Decentralized load balancing with observability (e.g., Istio, Linkerd).                          | Use `VirtualService` in Istio to define traffic splitting rules.                            |
| **Database Sharding**             | Distributes database workloads across partitions.                                               | Pair with `Consistent Hashing` for query routing.                                          |
| **Canary Releases**               | Gradually shifts traffic to new versions.                                                      | Load balancer routes 10% of traffic to `v2` while monitoring.                            |
| **Multi-Region Deployment**       | Deploys services in multiple geographic regions.                                               | Use `Weighted Random` with regional weights (e.g., 70% US, 30% EU).                       |

---

## **9. Best Practices**
1. **Start Simple**: Begin with `Round-Robin` and monitor.
2. **Monitor Everything**: Track latency, error rates, and server utilization.
3. **Avoid Over-Optimization**: Complex algorithms (e.g., `Least Response Time`) add overhead.
4. **Test Failures**: Simulate server outages to validate recovery.
5. **Document Assumptions**: Note why you chose an algorithm (e.g., "IP Hash for session affinity").
6. **Leverage Infrastructure**: Use cloud LB (e.g., AWS ALB) or service mesh for built-in support.
7. **Balance Consistency & Flexibility**: Use `Consistent Hashing` for stateful systems; `Round-Robin` for stateless.
8. **Plan for Scaling**: Ensure algorithms support horizontal scaling (e.g., decentralized LB).

---
**End of Reference Guide** (Word count: ~1,100)