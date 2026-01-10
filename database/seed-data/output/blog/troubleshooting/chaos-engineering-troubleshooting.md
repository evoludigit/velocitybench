# **Debugging Chaos Engineering: Learning from Controlled Failures – A Troubleshooting Guide**

---

## **Introduction**
Chaos Engineering is a structured approach to testing system resilience by intentionally injecting failures (e.g., killing pods, network latency, or disk errors) to uncover weaknesses before they disrupt production. While this pattern strengthens system robustness, improper execution can lead to cascading failures or unintended outages.

This guide provides a structured approach to troubleshooting issues when Chaos Engineering experiments go wrong, ensuring quick recovery and learning.

---

## **1. Symptom Checklist: When Something Went Wrong**
Chaos Engineering experiments may fail or cause issues. Check for these symptoms:

| **Symptom** | **Description** | **Potential Root Cause** |
|-------------|----------------|--------------------------|
| **Unplanned outages** | Services crash or become unresponsive during/after experiment. | Over-aggressive failure injection, race conditions, or resource starvation. |
| **Performance degradation** | High latency, timeouts, or throttling in dependent services. | Network partitions, missing retries, or inefficient fallback mechanisms. |
| **False positives/negatives** | System incorrectly reports success/failure in experiments. | Flaky tests, improper assertions, or incomplete failure detection. |
| **Unintended cascading effects** | Secondary systems fail due to experiment side effects. | Poor isolation, missing circuit breakers, or unbounded retries. |
| **Security breaches** | Chaos tools improperly access sensitive components. | Over-permissive RBAC, unencrypted secrets, or misconfigured probes. |
| **Data corruption** | Inconsistent state or lost transactions during experiments. | Missing transactional rollbacks, improper event sourcing, or race conditions. |

---

## **2. Common Issues and Fixes**
### **Issue 1: Unplanned Outages During an Experiment**
**Symptoms:**
- Pods crash loop back-off.
- Services fail with `Connection refused` or `Timeout`.
- Monitoring alerts trigger for high error rates.

**Root Causes:**
- **Too many resources consumed** (e.g., killing too many pods at once).
- **Missing circuit breakers** in dependent services.
- **No retry logic** in client applications.

**Fixes:**
#### **A. Mitigate Resource Overload**
Ensure experiments gradually ramping up injections:
```yaml
# Example: Gradually kill pods in a Kubernetes Chaos Mesh experiment
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: network-latency
spec:
  action: delay
  mode: one
  selector:
    namespaces:
      - default
    labelSelectors:
      app: my-service
  delay:
    latency: "100ms"
    jitter: "50ms"
  duration: 30s
  # Gradually increase from 10% to 100% of pods
  scale: 10  # Starts with 10% of pods, scales up over time
```

#### **B. Implement Retry Logic in Clients**
Use exponential backoff in client calls (e.g., in Python with `tenacity`):
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def call_failure_tolerant_api():
    response = requests.get("http://my-service")
    response.raise_for_status()
    return response.json()
```

#### **C. Add Circuit Breakers**
Use Istio’s `DestinationRule` or Hystrix to limit retries:
```yaml
# Istio Circuit Breaker Example
apiVersion: networking.istio.io/v1alpha3
kind: DestinationRule
metadata:
  name: my-service-circuit-breaker
spec:
  host: my-service
  trafficPolicy:
    connectionPool:
      tcp: { maxConnections: 100 }
      http: { http2MaxRequests: 1000 }
    outlierDetection:
      consecutiveErrors: 5
      interval: 10s
      baseEjectionTime: 30s
```

---

### **Issue 2: Performance Degradation Under Chaos**
**Symptoms:**
- High latency spikes.
- Timeouts in dependent services.
- Increased error rates in logging.

**Root Causes:**
- **Network latency introduced without fallback paths.**
- **Missing load balancing** during failures.
- **Database connection leaks** under stress.

**Fixes:**
#### **A. Use Chaos Mesh’s Network Chaos with Fallbacks**
Ensure services retry with a fallback:
```python
# Python client with fallback (e.g., cache or backup service)
@retry(stop=stop_after_attempt(3), retry_error_callback=logger.warning)
def call_with_fallback():
    try:
        return call_primary_service()
    except Exception as e:
        logger.error(f"Primary failed: {e}")
        return call_fallback_service()
```

#### **B. Configure Database Connection Pools**
Avoid connection leaks in PostgreSQL (example with `pgBouncer`):
```ini
# pgBouncer config (max_prepared=0 to avoid leaks)
max_client_conn = 100
default_pool_size = 20
```

---

### **Issue 3: False Positives/Negatives in Experiments**
**Symptoms:**
- System reports "resilient" even after failures.
- Flaky assertions in tests.

**Root Causes:**
- **Incomplete failure detection** (e.g., missing health checks).
- **Race conditions** in assertions.

**Fixes:**
#### **A. Use Reliable Health Checks**
Ensure endpoints return proper status codes:
```go
// Example: Go HTTP handler with proper health status
func (h *Handler) HealthCheck(w http.ResponseWriter, r *http.Request) {
    if !h.IsHealthy() {
        http.Error(w, "ServiceUnavailable", http.StatusServiceUnavailable)
        return
    }
    w.WriteHeader(http.StatusOK)
}
```

#### **B. Add Timeouts to Assertions**
Use `pytest-timeout` or similar to avoid hanging tests:
```python
# pytest with timeout
import pytest
from pytest_timeout import timeout

@timeout(30)  # 30-second timeout
def test_resilience():
    assert call_service_under_chaos() == "expected"
```

---

### **Issue 4: Unintended Cascading Failures**
**Symptoms:**
- Secondary services fail after experiment starts.
- Alerts fire for unrelated components.

**Root Causes:**
- **No isolation** between services.
- **Unbounded retries** causing overload.
- **Shared dependencies** (e.g., database, cache).

**Fixes:**
#### **A. Use Chaos Mesh’s Pod Chaos with Taints**
Avoid affecting unrelated pods:
```yaml
# Chaos Mesh Pod Chaos with taints
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: pod-kill
spec:
  action: pod-kill
  mode: one
  selector:
    namespaces:
      - default
    labelSelectors:
      app: my-service
  duration: 30s
  # Only target pods with specific taint
  taints:
    - key: "resilience-test"
      value: "true"
```

#### **B. Limit Retries with Circuit Breakers**
Use Spring Retry or similar:
```java
// Spring Retry Configuration (Java)
@Configuration
public class RetryConfig {
    @Bean
    public RetryTemplate retryTemplate() {
        RetryTemplate retryTemplate = new RetryTemplate();
        retryTemplate.setMaxAttempts(3);
        retryTemplate.setBackOffMultiplier(2.0);
        return retryTemplate;
    }
}
```

---

### **Issue 5: Security Breaches During Chaos**
**Symptoms:**
- Unauthorized access to services.
- Secrets leaked in logs.

**Root Causes:**
- **Over-permissive RBAC** in chaos tools.
- **Plaintext secrets** in experiments.

**Fixes:**
#### **A. Restrict Chaos Tool Permissions**
Limit Chaos Mesh’s Kubernetes RBAC:
```yaml
# Chaos Mesh RBAC (minimal permissions)
kind: ClusterRole
metadata:
  name: chaos-mesh-role
rules:
- apiGroups: [""]
  resources: ["pods", "services"]
  verbs: ["get", "list", "delete"]
- apiGroups: ["chaos-mesh.org"]
  resources: ["networkchaos", "podchaos"]
  verbs: ["create", "delete"]
```

#### **B. Mask Secrets in Logs**
Use `chaos-mesh` with anarchist for secret masking:
```yaml
# Example: Anarchist config for masking
apiVersion: anarchist.chaos-mesh.org/v1alpha1
kind: Anarchist
metadata:
  name: secret-masking
spec:
  selector:
    labelSelectors:
      app: my-service
  secrets:
  - name: "db-password"
    masking: "******"
```

---

## **3. Debugging Tools and Techniques**
### **A. Observability Tools**
| **Tool**               | **Purpose**                                                                 | **Example Command/Query**                          |
|------------------------|-----------------------------------------------------------------------------|-----------------------------------------------------|
| **Prometheus + Grafana** | Monitor metrics under chaos (latency, errors, SLA violations).               | `rate(http_requests_total{status=~"5.."}[1m])`      |
| **Chaos Mesh Dashboard** | Visualize experiments running in real-time.                                 | Access via `kubectl port-forward` to `chaos-dashboard` |
| **Kubernetes Events**   | Check pod failures during experiments.                                     | `kubectl get events --sort-by=.metadata.creationTimestamp` |
| **Jaeger/Tracing**     | Debug distributed failures across services.                                 | `jaeger query --service=my-service --end=now`      |

### **B. Logging and Tracing**
- **Structured Logging:** Use JSON logs (e.g., `logrus`, `structlog`) to filter by chaos labels.
- **Distributed Tracing:** Enable OpenTelemetry in services to trace requests during experiments.

### **C. Chaos Mesh Debugging Commands**
```sh
# List running chaos experiments
kubectl get chaos -A

# Check experiment logs
kubectl logs -n chaos-mesh chaos-experiment-name

# Force-stop a runaway experiment
kubectl delete chaos -n chaos-mesh chaos-experiment-name
```

---

## **4. Prevention Strategies**
### **A. Pre-Experiment Checks**
1. **Define SLAs:** Ensure experiments don’t violate critical service-level agreements.
2. **Run in Staging First:** Test chaos in a non-production environment.
3. **Use Canary Releases:** Gradually roll out experiments to a subset of traffic.

### **B. Automated Safety Nets**
- **Chaos Mesh Safety Net:**
  ```yaml
  # Auto-terminate experiments if errors exceed threshold
  apiVersion: chaos-mesh.org/v1alpha1
  kind: SafetyNet
  metadata:
    name: error-threshold
  spec:
    metric:
      namespace: default
      resource: pods
      selector:
        labelSelectors:
          app: my-service
      metricName: "error_rate"
      threshold: 0.1  # 10% error rate triggers termination
  ```
- **Alerting:** Set up alerts in Prometheus/Grafana for unusual metrics during experiments.

### **C. Post-Experiment Review**
1. **Replay Logs:** Use tools like `chaos-mesh replay` to debug failed experiments.
2. **Automated Blameless Postmortems:**
   - Use tools like **Better Uptime** or **PagerDuty** to document lessons learned.
   - Example template:
     ```
     1. What broke?
     2. How did it break?
     3. What was the impact?
     4. What’s the fix?
     5. How do we prevent it?
     ```

---

## **5. Recovery Playbook (Quick Actions)**
| **Scenario**               | **Immediate Action**                                                                 | **Long-Term Fix**                                  |
|----------------------------|--------------------------------------------------------------------------------------|---------------------------------------------------|
| **Pods crashing**          | Scale down chaos experiment (`kubectl scale chaos`).                                | Add resource limits to pods.                     |
| **Network partition**      | Reset network chaos (`kubectl delete networkchaos`).                                | Improve DNS resilience.                           |
| **Database locks**         | Kill stuck transactions (`pg_terminate_backend` in PostgreSQL).                      | Use connection pooling.                          |
| **Security breach**        | Rotate secrets and revoke RBAC access.                                              | Implement secret rotation policies.               |
| **Cascading failures**     | Roll back to last known good state (e.g., `kubectl rollout undo`).                 | Add circuit breakers and retries.                |

---

## **Conclusion**
Chaos Engineering is powerful but risky if misused. By following this guide:
1. **Detect issues early** using the symptom checklist.
2. **Apply targeted fixes** (retries, circuit breakers, isolation).
3. **Leverage observability tools** to debug efficiently.
4. **Prevent future issues** with safety nets and SLAs.

**Key Takeaway:** Chaos should **uncover** problems, not **create** them. Always validate in staging and have a recovery plan.

---
**Further Reading:**
- [Chaos Mesh Documentation](https://docs.chaos-mesh.org/)
- [Gremlin’s Chaos Engineering Handbook](https://docs.gremlin.com/)
- [Netflix’s Chaos Monkey](https://netflix.github.io/chaosmonkey/)