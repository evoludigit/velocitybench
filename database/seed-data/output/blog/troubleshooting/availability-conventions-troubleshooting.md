# **Debugging *Availability Conventions*: A Troubleshooting Guide**

## **Introduction**
*Availability Conventions* is a distributed system design pattern that enforces consistent, predictable behavior for querying system availability state. This pattern ensures that clients (e.g., service meshes, load balancers, or monitoring tools) can reliably determine if a service is up, down, or degraded without relying on inconsistent or stale status checks.

Common scenarios where this pattern is used:
- Service discovery in microservices
- Failure detection & recovery in Kubernetes
- Health checks for distributed databases
- API gateway and proxy routing logic

---

## **Symptom Checklist**
Before diving into debugging, check if your system exhibits any of these symptoms:

### **Client-Side Symptoms**
- [ ] Clients report inconsistent availability statuses for the same service (e.g., sometimes "UP" but often "DOWN").
- [ ] Service mesh/proxy misroutes traffic due to incorrect health statuses.
- [ ] Monitoring dashboards show unstable or incorrect availability metrics.
- [ ] API errors (e.g., `503 Service Unavailable`) occur intermittently, even when the backend is functional.
- [ ] Clients retry failed requests excessively due to unreliable availability checks.

### **Server-Side Symptoms**
- [ ] Health check endpoints (`/health`, `/ready`) return inconsistent responses (e.g., `200 OK` when the service is degraded).
- [ ] Logs indicate slow or delayed health check responses from backend services.
- [ ] Resource exhaustion (CPU/memory) during health check storms (e.g., Kubernetes liveness probes firing rapidly).
- [ ] Dependencies (databases, caches) are not properly factored into availability checks.
- [ ] Environment-specific failures (e.g., works in dev but fails in prod due to missing conventions).

### **Infrastructure-Side Symptoms**
- [ ] Load balancers or proxies (NGINX, Envoy, Istio) fail to update routing rules due to stale availability data.
- [ ] Service discovery caches (e.g., etcd, Consul) are out of sync with actual service states.
- [ ] Network partitions cause availability checks to fail intermittently.
- [ ] Time synchronization issues (e.g., NTP drift) affect timestamp-based availability checks.

---

## **Common Issues and Fixes**

### **1. Inconsistent Health Check Endpoints**
**Symptom:**
Health checks return different responses under load or during transient failures, causing clients to behave unpredictably.

**Root Cause:**
- Endpoints check only application-level readiness (e.g., HTTP server is up) but not dependency availability (e.g., database connectivity).
- No proper throttling or circuit-breaking for health checks.

**Fix:**
#### **Solution: Implement Structured Health Checks**
Ensure health endpoints return consistent, structured responses with clear status codes and metadata.

**Example (Node.js/Express):**
```javascript
const healthCheck = (req, res) => {
  const dbStatus = checkDatabaseConnection(); // Your DB check logic
  const appStatus = isApplicationReady();      // Your app readiness check

  res.status(200).json({
    status: 'UP' || 'DOWN' || 'DEGRADED',
    details: {
      database: dbStatus,
      application: appStatus,
      timestamp: new Date().toISOString()
    }
  });
};
```

**Key Improvements:**
- Include **dependency statuses** (e.g., database, cache).
- Use **standard HTTP status codes** (`200`, `503`, `429` for throttling).
- Add **metadata** (e.g., `lastChecked`, `retryAfter` for degraded services).

---

### **2. Health Check Storms (Kubernetes Liveness Probes)**
**Symptom:**
Rapid-fire health checks (e.g., from Kubernetes) cause resource exhaustion or slowdowns.

**Root Cause:**
- Default Kubernetes probes (e.g., `/health` every 10s) may overwhelm lightweight services.
- No backoff or rate-limiting in health endpoints.

**Fix:**
#### **Solution: Throttle Health Checks & Implement Backoff**
- Configure Kubernetes probes with longer intervals (`initialDelaySeconds`, `periodSeconds`).
- Add rate-limiting to health endpoints.

**Example (NGINX with `limit_req`):**
```nginx
limit_req_zone $binary_remote_addr zone=health_checks:10m rate=10r/s;

server {
  location /health {
    limit_req zone=health_checks burst=5;
    proxy_pass http://backend;
  }
}
```

**Kubernetes Probe Tuning Example:**
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 30       # Longer interval
  failureThreshold: 3
```

---

### **3. Stale Service Discovery Data**
**Symptom:**
Clients see outdated service availability (e.g., a service appears "UP" even after crashing).

**Root Cause:**
- Service discovery caches (e.g., Consul, etcd) are not updated fast enough.
- No proper heartbeats or lease mechanisms.

**Fix:**
#### **Solution: Lease-Based Availability Tracking**
- Implement **TTL-based leases** for service registration.
- Use **heartbeats** with exponential backoff on failure.

**Example (Consul Service Registration):**
```go
import "github.com/hashicorp/consul/api"

func registerService(address string) error {
  config := api.DefaultConfig()
  client, err := api.NewClient(config)
  if err != nil {
    return err
  }

  reg := &api.AgentServiceRegistration{
    ID:      "my-service",
    Name:    "my-service",
    Address: address,
    Port:    8080,
    Check: &api.AgentServiceCheck{
      DeregisterCriticalServiceAfter: "30s", // Fail fast if unhealthy
      Interval:                        "10s",
      HTTP:                           "http://localhost:8080/health",
      Timeout:                        "5s",
    },
  }
  return client.Agent().ServiceRegister(reg)
}
```

---

### **4. Network Partition Handling**
**Symptom:**
Availability checks fail intermittently due to network issues (e.g., DNS flapping, split-brain scenarios).

**Root Cause:**
- No **circuit breaker** or **retries with backoff** in availability checks.
- Over-reliance on HTTP health checks without TCP-level validation.

**Fix:**
#### **Solution: Multi-Level Availability Checks**
- **First Level:** Fast TCP connect check (avoids slow HTTP overhead).
- **Second Level:** HTTP health check (if TCP succeeds).
- **Third Level:** Dependency-specific checks (e.g., DB connection).

**Example (Go with retries):**
```go
import (
  "net/http"
  "time"
)

func checkAvailability(addr string) (bool, error) {
  var httpClient = &http.Client{
    Timeout: 5 * time.Second,
    Transport: &http.Transport{
      DialContext: (&net.Dialer{
        Timeout: 2 * time.Second,
      }).DialContext,
    },
  }

  maxRetries := 3
  backoff := time.Second

  for i := 0; i < maxRetries; i++ {
    resp, err := httpClient.Get("http://" + addr + "/health")
    if err == nil && resp.StatusCode == http.StatusOK {
      return true, nil
    }
    time.Sleep(backoff)
    backoff *= 2 // Exponential backoff
  }
  return false, fmt.Errorf("failed after %d retries", maxRetries)
}
```

---

### **5. Environment-Specific Failures**
**Symptom:**
Availability checks work in development but fail in production due to missing configurations.

**Root Cause:**
- Hardcoded endpoints or checks that don’t account for environment variables.
- Missing dependency checks in staging.

**Fix:**
#### **Solution: Environment-Aware Health Checks**
- Use **feature flags** or **config-driven endpoints**.
- Test dependency availability in all environments.

**Example (Docker Compose Override for Testing):**
```yaml
# docker-compose.yml
services:
  app:
    environment:
      - DATABASE_URL=postgres://user:pass@db:5432/mydb
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

**Production Override:**
```yaml
# docker-compose.prod.yml
services:
  app:
    environment:
      - DATABASE_URL=${PROD_DB_URL}
```

---

## **Debugging Tools and Techniques**

### **1. Logging & Monitoring**
- **Log Health Check Responses:**
  ```javascript
  app.use((req, res, next) => {
    console.log(`[HEALTH] ${req.method} ${req.path} - ${res.statusCode}`);
    next();
  });
  ```
- **Prometheus Metrics for Availability:**
  ```go
  func healthHandler(w http.ResponseWriter, r *http.Request) {
    metrics.Gauge("service_availability").Set(1.0) // UP
    // ... other checks
  }
  ```
  Expose `/metrics` for scraping.

### **2. Network Debugging**
- **TCP Connect Tests:**
  ```bash
  telnet <service-address> 8080       # Check if TCP port is open
  curl -v http://<service-address>/health  # Debug HTTP
  ```
- **Packet Capture (Wireshark/tcpdump):**
  ```bash
  tcpdump -i any port 8080 -w health_checks.pcap
  ```

### **3. Infrastructure Validation**
- **Consul/etcd Check Status:**
  ```bash
  consul services                  # List registered services
  consul service check my-service   # Check health
  ```
- **Kubernetes Event Debugging:**
  ```bash
  kubectl get events --sort-by=.metadata.creationTimestamp
  kubectl describe pod <pod-name>
  ```

### **4. Load Testing**
- **Simulate High Traffic:**
  ```bash
  wrk -t12 -c400 -d30s http://<service>/health
  ```
- **Check for Throttling:**
  ```bash
  ab -n 10000 -c 100 http://<service>/health  # Apache Benchmark
  ```

---

## **Prevention Strategies**

### **1. Design-Time Best Practices**
- **Standardize Health Check Endpoints:**
  Use `/health` (liveness) and `/ready` (readiness) as conventions.
- **Implement Circuit Breakers:**
  Use libraries like [Hystrix](https://github.com/Netflix/Hystrix) or [Resilience4j](https://resilience4j.readme.io/docs) to prevent cascading failures.
- **Dependency Awareness:**
  Ensure health checks include critical dependencies (DB, cache, etc.).

### **2. Runtime Safeguards**
- **Rate-Limit Health Checks:**
  Use NGINX, Envoy, or application-level throttling.
- **Heartbeat-Based Registration:**
  Require periodic heartbeats for service discovery.
- **Environment Parity:**
  Test availability checks in **staging** that mirrors production (e.g., same DB, cache, network).

### **3. Observability**
- **Centralized Logging (ELK, Loki):**
  Aggregate health check logs for analysis.
- **Synthetic Monitoring:**
  Use tools like [Grafana Synthetic Monitoring](https://grafana.com/docs/grafana-cloud/synthetic-monitoring/) to simulate client availability checks.
- **Anomaly Detection:**
  Set up alerts for inconsistent health statuses (e.g., "service reported UP 100% but database checks 0%").

### **4. Testing Strategy**
- **Unit Tests for Health Endpoints:**
  ```javascript
  test("health endpoint returns correct status", async () => {
    server.get("/health").reply(200, { status: "UP" });
    const res = await axios.get("http://localhost:3000/health");
    expect(res.data.status).toBe("UP");
  });
  ```
- **Chaos Engineering:**
  Use [Chaos Mesh](https://chaos-mesh.org/) or [Gremlin](https://www.gremlin.com/) to test failure recovery.

---

## **Conclusion**
*Availability Conventions* ensure reliable system behavior by enforcing consistent availability checks. When debugging issues, focus on:
1. **Inconsistent Responses** → Standardize health endpoints and include dependency checks.
2. **Resource Exhaustion** → Throttle health checks and use efficient probes.
3. **Stale Data** → Implement leases and heartbeats in service discovery.
4. **Network Issues** → Use multi-level checks (TCP → HTTP → DB).
5. **Environment Mismatches** → Test in staging with production-like configurations.

By applying these fixes and prevention strategies, you can minimize downtime and ensure predictable availability across distributed systems.