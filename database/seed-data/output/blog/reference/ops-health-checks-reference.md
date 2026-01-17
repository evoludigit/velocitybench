# **[Pattern] Health Checks Patterns – Reference Guide**

---

## **1. Overview**
The **Health Checks Patterns** define structured ways to monitor the operational status of distributed systems, microservices, or components. These patterns ensure resilience by proactively detecting failures (e.g., unresponsive endpoints, dependencies, or resource exhaustion) and triggering remediation actions. Common use cases include **container orchestration (Kubernetes), service mesh (Istio), and cloud-native applications**.

Key benefits:
- **Early failure detection** (prevents cascading outages).
- **Self-healing capabilities** (scales, restarts, or reroutes traffic).
- **Observability integration** (combines with metrics, logs, and traces).

Health checks can be categorized into:
- **Readiness Probes** (indicate if a component can accept traffic).
- **Liveness Probes** (detect unresponsive services).
- **Startup Probes** (wait for initialization before traffic).
- **Custom/Application Checks** (domain-specific validation).

---

## **2. Schema Reference**

| **Component**       | **Description**                                                                 | **Parameters**                                                                                     | **Example Values**                                                                 |
|---------------------|-------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Readiness Probe** | Checks if the service can handle requests (e.g., DB connection, cache warmup). | `httpGet`, `tcpSocket`, `execCommand`, `initialDelaySeconds`, `periodSeconds`, `successThreshold` | `httpGet /healthz`, `initialDelaySeconds: 10`, `periodSeconds: 5`                  |
| **Liveness Probe**  | Detects if a service is stuck (e.g., hung thread, OOM).                       | Same as Readiness + `failureThreshold`, `timeoutSeconds`, `grpcGet` (for gRPC)                   | `exec ["curl", "-f", "http://localhost:8080/alive"]`, `timeoutSeconds: 3`          |
| **Startup Probe**   | Delays traffic until the app initializes (e.g., DB migrations).               | Same as Readiness + `periodSeconds` (shorter interval during startup).                           | `httpGet /startup-ready`, `periodSeconds: 2` (vs. 30s for normal probes)          |
| **Health Endpoint** | Custom endpoint (e.g., `/actuator/health` in Spring Boot).                   | Path, HTTP method, response expectations (e.g., `200 OK`).                                        | `GET /actuator/health?detail=true`, returns JSON with status: `"OUT_OF_SERVICE"`  |
| **Dependency Check**| Validates external dependencies (e.g., Kafka, Redis).                         | Query parameters (e.g., `?broker=kafka:9092`).                                                  | `POST /kafka/health?broker=kafka:9092`, expects `{ "status": "UP" }`                |

---

## **3. Key Implementation Patterns**

### **3.1 Endpoint-Based Health Checks**
**Use Case:** REST/gRPC services.
**Implementation:**
Define a dedicated `/health` endpoint with:
- **HTTP Status Codes**:
  - `200 OK`: Component is healthy.
  - `503 Service Unavailable`: Ready but dependencies are down.
  - `424 Failed Dependency`: Critical dependency failure (e.g., DB).
- **Response Format (JSON):**
  ```json
  {
    "status": "UP",
    "dependencies": [
      { "name": "database", "status": "UP" },
      { "name": "cache", "status": "DOWN" }
    ]
  }
  ```
**Tools:**
- **Spring Boot Actuator**: Auto-generates `/actuator/health`.
- **Prometheus**: Exposes `/metrics` with health endpoints.
- **gRPC Health Checking**: Uses `HealthCheckService` (gRPC status codes).

---

### **3.2 Infrastructure-Level Probes**
**Use Case:** Container orchestration (Kubernetes, Docker).
**Implementation:**
Configure probes in **PodSpec** (YAML):
```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 10
  failureThreshold: 3
readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 3
  periodSeconds: 2
```
**Key Parameters:**
| **Parameter**          | **Purpose**                                                                 |
|------------------------|-----------------------------------------------------------------------------|
| `initialDelaySeconds`  | Wait before first probe (e.g., 5s for startup).                             |
| `periodSeconds`        | Interval between probes (e.g., 10s).                                       |
| `failureThreshold`     | Number of consecutive failures to trigger action (e.g., restart/kill pod). |
| `timeoutSeconds`       | Max time to wait for a probe response (default: 1s).                       |

**Actions on Failure:**
- **Liveness**: Restart pod (default).
- **Readiness**: Remove pod from service load balancer.
- **Startup**: Skip traffic until probe passes.

---

### **3.3 Custom/Application-Specific Checks**
**Use Case:** Business logic validation (e.g., payment service validates auth token).
**Implementation:**
- **Example (Node.js/Express):**
  ```javascript
  app.get('/health', (req, res) => {
    const checks = {
      database: checkDBConnection(),
      authService: checkAuthService()
    };
    res.json({ status: 'UP', checks });
  });
  ```
- **Integration with Observability:**
  - Log failures to **ELK Stack** or **Splunk**.
  - Alert via **Prometheus + Alertmanager** or **Grafana Alerts**.

**Pattern Variations:**
1. **Circuit Breaker**: Combine with **Retry** or **Fallback** patterns (e.g., stop sending requests after 3 failures).
2. **Chaos Engineering**: Inject failures during health checks (e.g., **Gremlin**, **Chaos Monkey**).

---

### **3.4 Observability Integration**
**Metrics:**
- **Prometheus Counters**:
  - `health_checks_total` (total probes).
  - `health_checks_failed` (rollup for SLOs).
- **Distributed Tracing** (Jaeger/Zipkin):
  - Trace health check latency and dependencies.

**Logging:**
- Include probe metadata in logs:
  ```
  {"level":"INFO", "event":"health_check", "endpoint":"/startup-ready", "status":"UP", "latency":"42ms"}
  ```

---

## **4. Query Examples**

### **4.1 Endpoint-Based Checks**
**Readiness Check:**
```bash
curl -I http://service:8080/ready
# Expected: HTTP/200 OK
```

**Dependency Check (Query Param):**
```bash
curl "http://service:8080/health?broker=kafka:9092"
# Expected: {"status":"UP", "kafka":{"status":"UP"}}
```

**gRPC Health Check:**
```bash
grpc_health_probe -addr=localhost:50051 -service=payment.service.Health
# Expected: {"status":"SERVING"}
```

---

### **4.2 Kubernetes Probes**
**View Pod Probes:**
```bash
kubectl describe pod my-pod | grep -A 10 "Liveness"
# Output:
#   Liveness:     http-get http://:8080/healthz delay=5s timeout=1s period=10s #success=3 #failure=3
```

**Force Probe Execution (Debugging):**
```bash
kubectl exec my-pod -- curl -v http://localhost:8080/liveness
```

---

### **4.3 Custom Script Checks**
**Bash Example (Exec Probe):**
```bash
#!/bin/bash
# Check if a process is running
pgrep -x "my-service" >/dev/null || exit 1
exit 0
```
**Integrate with Kubernetes:**
```yaml
livenessProbe:
  exec:
    command: ["/bin/bash", "/health_check.sh"]
```

---

## **5. Error Handling & Remediation**

| **Error Scenario**               | **Detection Method**               | **Remediation Action**                          |
|-----------------------------------|-------------------------------------|-------------------------------------------------|
| Service unresponsive             | Liveness probe fails                | Restart pod (Kubernetes)                        |
| Dependency down (e.g., DB)       | Custom `/health?db=down` endpoint   | Route traffic to backup DB or fail fast         |
| High latency                      | gRPC/Prometheus `processing_time`   | Scale out or optimize queries                  |
| Startup timeout                  | Startup probe fails                 | Increase `initialDelaySeconds` or fix init code |
| Configuration drift               | Compare `/health` response vs. config| Rollback or reapply configs                     |

**Retry Policies:**
- Exponential backoff for transient failures (e.g., **Hystrix**).
- Circuit breaker (e.g., **Resilience4j** in Java):
  ```java
  CircuitBreaker circuitBreaker = CircuitBreaker.ofDefaults("db-check");
  if (circuitBreaker.executeChecked(() -> checkDB(), Throwables::printStackTrace)) {
    // Proceed if DB is up
  }
  ```

---

## **6. Best Practices**
1. **Idempotency**: Ensure `/health` and `/ready` endpoints are stateless.
2. **Performance**: Keep probes lightweight (avoid blocking calls).
3. **Security**:
   - Restrict access to health endpoints (e.g., internal network only).
   - Use **mTLS** for service-to-service checks.
4. **SLOs**: Define **Service Level Objectives** (e.g., "99.9% of probes must pass").
5. **Avoid Overloading**: Limit probe frequency (e.g., `periodSeconds: 10`).

---

## **7. Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                                  |
|---------------------------|-------------------------------------------------------------------------------|--------------------------------------------------|
| **[Circuit Breaker]**     | Prevents cascading failures by stopping calls to a failing dependency.        | High-latency or flaky services.                  |
| **[Retry]**               | Automatically retries failed requests with backoff.                          | Transient network issues.                       |
| **[Fallback]**            | Provides degraded functionality when primary service fails.                   | Critical paths with backup systems.              |
| **[Bulkhead]**            | Isolates resources (e.g., threads/DB connections) to limit impact.            | Resource exhaustion (e.g., OOM, DB pool depletion). |
| **[Distributed Tracing]** | Tracks requests across services for latency analysis.                        | Debugging health check delays.                  |
| **[Config Management]**   | Dynamically updates health check endpoints (e.g., feature flags).            | A/B testing or canary deployments.              |

---

## **8. Tools & Frameworks**
| **Tool/Framework**       | **Use Case**                                  | **Example**                                  |
|--------------------------|-----------------------------------------------|----------------------------------------------|
| **Prometheus**           | Metrics collection + alerts for health checks | `up{service="payment"}` metric.             |
| **Istio**                | Service mesh health checks + traffic control  | `IstioSidecar` annotations.                 |
| **Spring Boot Actuator** | Auto-generated `/actuator/health`.           | Add dependency: `implementation 'io.spring.boot:spring-boot-starter-actuator'`. |
| **Kubernetes**           | Built-in probes (liveness/readiness).        | `kubectl describe pod <pod>`.               |
| **Resilience4j**         | Circuit breakers, retries, rate limiting.     | Java: `@CircuitBreaker(name = "dbCheck")`    |
| **Chaos Mesh**           | Inject failures to test health checks.       | Simulate node/endpoint failures.             |

---

## **9. Example: Full Implementation (Kubernetes + Spring Boot)**
### **9.1 Spring Boot `application.yml`**
```yaml
management:
  endpoint:
    health:
      show-details: always
  health:
    db:
      enabled: true
    diskSpace:
      enabled: true
```

### **9.2 Kubernetes Deployment**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payment-service
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: payment
        image: payment-service:latest
        livenessProbe:
          httpGet:
            path: /actuator/health/liveness
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /actuator/health/readiness
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
```

### **9.3 Prometheus Alert Rule**
```yaml
groups:
- name: health-alerts
  rules:
  - alert: ServiceDown
    expr: up{job="payment-service"} == 0
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Payment service is down"
      description: "Service has been down for 5 minutes"
```

---
**References:**
- [Kubernetes Docs: Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [Spring Boot Actuator](https://docs.spring.io/spring-boot/docs/current/reference/htmlsingle/#actuator.endpoints)
- [Prometheus Health Checks](https://prometheus.io/docs/practices/instrumentation/#health-checks)