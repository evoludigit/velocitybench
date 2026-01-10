# **[Pattern] Health Checks and Liveness Probes Reference Guide**

---

## **Overview**
Health checks and liveness/readiness probes provide automated visibility into the operational state of services, enabling resilient and self-healing infrastructure. This pattern ensures that orchestrators (e.g., Kubernetes) and load balancers (e.g., NGINX, AWS ALB) can dynamically adjust traffic routing, initiate failover, or trigger restarts without manual intervention.

Key components:
- **Liveness Probe**: Detects if a service is stuck in a failed state (e.g., hung, crashed) and triggers a restart.
- **Readiness Probe**: Determines if a service is ready to serve traffic, preventing load balancers from routing to incomplete or misconfigured instances.
- **Startup Probe**: Ensures a service initializes properly before accepting traffic (Common in Kubernetes v1.16+).

This pattern complements **Circuit Breakers** (fail-fast strategies) and **Graceful Degradation** (prioritized traffic handling) for robust system reliability.

---

## **Schema Reference**

| **Component**       | **Description**                                                                                     | **Configuration Fields**                                                                                                                                                                                                 | **Example Use Case**                                                                                                                         |
|---------------------|-----------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------|
| **Liveness Probe**  | Monitors if a container/app is running but unresponsive. Restarts the container if the probe fails. | - `httpGet`, `tcpSocket`, or `exec` (command) endpoint.<br>- `initialDelaySeconds` (default: 0).<br>- `periodSeconds` (default: 10).<br>- `timeoutSeconds` (default: 1).<br>- `successThreshold` (default: 1).<br>- `failureThreshold` (default: 3). | A stuck HTTP server hanging on database connection recovery.                                                                           |
| **Readiness Probe** | Validates if a container is ready to serve traffic (e.g., database connection, API health check). | Same as **Liveness Probe** +:<br>- `initialDelaySeconds` (default: 0).<br>- `successThreshold` (default: 1).<br>- **Excluded from traffic routing** if failed.                                           | Delaying traffic to a pod until a background job (e.g., migrations) completes.                                                         |
| **Startup Probe**   | Monitors long-running application startup (e.g., JVM warmup, database sync). Overrides liveness probes. | - `httpGet`/`tcpSocket`/`exec` endpoint.<br>- `periodSeconds`, `timeoutSeconds`.<br>- **Fails the probe** if `startupProbe` takes longer than specified.                                                     | Preventing traffic to a Java app before the JVM fully initializes.                                                                      |
| **HTTP Endpoint**   | Specifies an HTTP endpoint for probing (e.g., `/health`).                                          | - `path` (e.g., `/health`).<br>- `port` (container port or `name:port` if defined in pod spec).<br>- `scheme` (HTTP/HTTPS).<br>- `httpHeaders` (optional, e.g., `Authorization`).                                       | A REST API exposing a `/health` endpoint with a 200 status for readiness.                                                               |
| **TCP Socket**      | Tests if a TCP port is open (useful for non-HTTP services).                                        | - `port` (number or named port from pod spec).<br>- **No HTTP header/path validation**.                                                                                                                               | Checking if a gRPC service is listening on port `50051`.                                                                                   |
| **Exec Command**    | Runs a shell command to check health (e.g., system logs, process status).                           | - `command` (array of strings, e.g., `["sh", "-c", "curl -f http://localhost/health"]`).<br>- **No network dependencies**.                                                                                          | Verifying a local process (e.g., Redis) is running via `ps aux | grep redis`.                                                                      |

---

## **Implementation Guidelines**

### **1. Probe Endpoint Design**
- **Standard Paths**: Use `/health`, `/ready`, or `/live` for consistency (e.g., Kubernetes defaults).
- **Response Codes**:
  - **200 OK**: Liveness/Readiness successful.
  - **5xx**:Critical failure (trigger restart/route away).
  - **4xx (e.g., 404)**: Ignored by probes (unless explicitly configured).
- **Response Headers**:
  - Add custom headers (e.g., `X-App-Health: ok`) for debug visibility.
  - Example:
    ```http
    HTTP/1.1 200 OK
    X-App-Health: ok
    ```

### **2. Probe Configuration Examples**
#### **Kubernetes Deployment (YAML)**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: my-app
        image: my-app:latest
        ports:
        - containerPort: 8080
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
            scheme: HTTP
          initialDelaySeconds: 30  # Wait 30s before first probe
          periodSeconds: 10        # Probe every 10s
          timeoutSeconds: 5        # Fail if no response in 5s
          failureThreshold: 3      # Restart after 3 failures
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          successThreshold: 1
        startupProbe:  # Optional for long-startup apps
          httpGet:
            path: /ready
            port: 8080
          failureThreshold: 30  # Max 5 minutes to start
          periodSeconds: 10
```

#### **Docker Compose**
```yaml
services:
  app:
    image: my-app
    ports:
      - "8080:8080"
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8080/health || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 30s
```

#### **AWS ECS Task Definition**
```json
"healthCheck": {
  "command": ["CMD-SHELL", "curl -f http://localhost:8080/health || exit 1"],
  "interval": 10,
  "retries": 3,
  "timeout": 5
}
```

---

### **3. Best Practices**
- **Minimize Probe Overhead**:
  - Avoid complex logic in probe endpoints (e.g., database queries).
  - Cache results if probes are called frequently (e.g., memoization).
- **Avoid False Positives/Negatives**:
  - **False Positive**: Probe succeeds but the app is unhealthy (e.g., `/health` returns 200 even if the DB is down). *Solution*: Use application-layer checks (e.g., verify critical dependencies).
  - **False Negative**: Probe fails but the app is healthy (e.g., `/ready` times out due to a slow endpoint). *Solution*: Adjust `timeoutSeconds` or use a non-blocking check (e.g., TCP socket).
- **Resource Limits**:
  - Restrict probe endpoints to low-priority traffic (e.g., route via a dedicated `/health` subdomain).
- **Logging**:
  - Log probe results for debugging:
    ```log
    [INFO] Liveness probe: /health -> 200 OK (successThreshold=1/1)
    [WARN] Readiness probe: /ready -> 503 (failureThreshold=3/3)
    ```

---

## **Query Examples**
### **1. Testing Probe Endpoints Locally**
```bash
# Liveness check (from another container/pod)
curl -v http://<pod-ip>:8080/health

# Readiness check
curl -v http://<pod-ip>:8080/ready

# Exec probe (if configured)
kubectl exec <pod-name> -- test -f /tmp/healthy.file
```

### **2. Kubernetes Debugging**
```bash
# Check probe status
kubectl describe pod <pod-name> | grep -A 10 -B 10 "liveness"

# Force a probe failure (for testing)
kubectl port-forward <pod-name> 8080:8080 &
# Kill the probe endpoint process (e.g., simulate a crash)
kill $(pgrep -f "gunicorn")

# View probe logs
kubectl logs <pod-name> -c my-app
```

### **3. Alerting on Probe Failures**
```yaml
# Prometheus Alert (example for Kubernetes readiness probe)
- alert: PodReadinessDegraded
  expr: kube_pod_status_ready{condition="false"} == 1
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Pod {{ $labels.pod }} not ready"
    description: "Pod {{ $labels.namespace }}/{{ $labels.pod }} has been in a 'NotReady' state for >5m."
```

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                                     | **When to Use**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| **Circuit Breakers**      | Temporarily stops sending traffic to a failing service to prevent cascading failures.              | When a service is intermittently unavailable (e.g., third-party APIs).                               |
| **Graceful Degradation**  | Prioritizes critical traffic while degrading non-critical features during high load.               | During load spikes or resource constraints (e.g., disable analytics during a DDoS).                  |
| **Chaos Engineering**     | Intentionally disrupts services to test resilience (e.g., kill pods, simulate network latency).     | During pre-production testing to validate health checks and failover mechanisms.                     |
| **Configurable Timeouts** | Dynamically adjusts probe/endpoint timeouts based on environment (e.g., slower in staging).       | For apps with variable startup times (e.g., large dependencies).                                   |
| **Canary Deployments**    | Gradually rolls out changes to a subset of users/traffic.                                          | For testing new features while monitoring health checks for regressions.                             |

---
## **Troubleshooting**
| **Issue**                          | **Cause**                              | **Solution**                                                                                     |
|-------------------------------------|----------------------------------------|--------------------------------------------------------------------------------------------------|
| Probe fails immediately             | `initialDelaySeconds` too low.         | Increase delay (e.g., `initialDelaySeconds: 30`).                                                   |
| Pod restarts too frequently         | Liveness probe too aggressive.         | Adjust `failureThreshold` or `periodSeconds`.                                                     |
| Readiness probe never succeeds      | `/ready` endpoint returns 5xx.        | Check application logs for errors in the readiness handler.                                       |
| Probe works locally but not in K8s  | Port/mismatch or network policies.     | Verify `containerPort` vs. `hostPort`, and check network rules.                                   |
| Startup probe times out             | App initializes slower than expected.  | Increase `failureThreshold` or optimize startup (e.g., async initialization).                      |

---
## **Further Reading**
- [Kubernetes Probes Documentation](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#container-probes)
- [AWS Health Checks for ECS](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-definition-healthcheck.html)
- [Prometheus Probing Best Practices](https://prometheus.io/docs/practices/instrumenting/jvm/#liveness-and-readiness-probes)