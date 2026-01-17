---
# **[Pattern] Health Check Endpoints Reference Guide**

---

## **Overview**
The **Health Check Endpoints** pattern ensures reliable Kubernetes deployments by providing dedicated HTTP endpoints for **liveness** (`/health/live`) and **readiness** (`/health/ready`) probes. These endpoints allow Kubernetes to dynamically manage application instances based on their operational status—**liveness** checks if the service is functioning, while **readiness** determines if it is ready to accept traffic.

FraiseQL implements this pattern with **comprehensive dependency checks**, including database connectivity, Redis availability, and external service health. This enables graceful degradation, where non-critical dependencies can be marked as degraded without crashing the entire service, improving resilience in distributed systems.

---

## **Schema Reference**

| **Endpoint**       | **Purpose**                          | **Response Codes**       | **Response Body**                     | **Request Method** | **Dependencies Checked**                     |
|--------------------|--------------------------------------|--------------------------|---------------------------------------|--------------------|---------------------------------------------|
| `/health/live`     | Determines if the service is running | `200 (OK)` / `500 (Error)` | `{"status": "live"}` or error details | `GET`              | In-process health (e.g., process crashes)   |
| `/health/ready`    | Determines if the service is ready to handle traffic | `200 (OK)` / `503 (Service Unavailable)` | `{"status": "ready", "dependencies": {...}}` | `GET`              | Database, Redis, external services           |
| `/health/debug`*   | Detailed health metrics (internal)   | `200 (OK)` / `500 (Error)` | Extensive dependency status details   | `GET`              | All monitored dependencies (advanced)      |

**\*** Only available in **debug mode** (e.g., `FR AISEQL_DEBUG=true`).

---

## **Response Formats**

### **1. `/health/live`**
If the service is running:
```json
{
  "status": "live",
  "timestamp": "2024-05-20T12:00:00Z"
}
```
If the service is unhealthy (e.g., deadlock or crash):
```json
{
  "status": "unhealthy",
  "error": "Process stuck in blocking operation",
  "timestamp": "2024-05-20T12:00:01Z"
}
```

### **2. `/health/ready`**
If all dependencies are healthy:
```json
{
  "status": "ready",
  "dependencies": {
    "database": { "status": "healthy", "last_checked": "2024-05-20T12:00:00Z" },
    "redis": { "status": "healthy", "last_ping": "2024-05-20T11:59:58Z" },
    "external_api": { "status": "healthy", "last_response": "2024-05-20T12:00:00Z" }
  },
  "timestamp": "2024-05-20T12:00:00Z"
}
```
If a dependency is degraded (graceful failure):
```json
{
  "status": "ready",
  "dependencies": {
    "database": { "status": "degraded", "error": "High latency", "last_checked": "2024-05-20T12:00:00Z" },
    "redis": { "status": "healthy", "last_ping": "2024-05-20T11:59:58Z" }
  },
  "timestamp": "2024-05-20T12:00:00Z"
}
```
If the service is **not ready** (e.g., missing critical dependencies):
```json
{
  "status": "unready",
  "error": "Database connection failed",
  "timestamp": "2024-05-20T12:00:01Z"
}
```

### **3. `/health/debug` (Advanced)**
Provides **low-level metrics** (disabled by default):
```json
{
  "status": "debug",
  "dependencies": {
    "database": {
      "status": "healthy",
      "latency": { "avg": 120, "p99": 250 } // in ms
    },
    "redis": {
      "status": "healthy",
      "memory_usage": 85,
      "connected_clients": 42
    }
  },
  "internal_health": {
    "memory_usage": 67,
    "gc_pauses": [25, 18, 32] // in ms
  }
}
```

---

## **Query Examples**

### **1. Basic Health Check (Liveness)**
```bash
curl -X GET http://<service-host>/health/live
```
**Expected Output:**
```json
{"status": "live", "timestamp": "2024-05-20T12:00:00Z"}
```

### **2. Readiness Check with Dependency Insights**
```bash
curl -X GET http://<service-host>/health/ready
```
**Expected Output (healthy):**
```json
{
  "status": "ready",
  "dependencies": {
    "database": { "status": "healthy", "last_checked": "2024-05-20T12:00:00Z" }
  }
}
```

### **3. Debug Mode (Advanced Troubleshooting)**
```bash
FR AISEQL_DEBUG=true curl -X GET http://<service-host>/health/debug
```
**Expected Output:**
```json
{
  "status": "debug",
  "dependencies": {
    "redis": { "memory_usage": 85, "connected_clients": 42 }
  }
}
```

### **4. Custom Query Parameters (Filtering)**
FraiseQL supports **query parameters** to filter responses:
```bash
curl -X GET "http://<service-host>/health/ready?filter=database,redis"
```
**Expected Output (filtered):**
```json
{
  "status": "ready",
  "dependencies": {
    "database": { "status": "healthy" },
    "redis": { "status": "healthy" }
  }
}
```

### **5. Retry Logic (Kubernetes Probes)**
Kubernetes **liveness probes** should retry repeatedly (default: `periodSeconds: 10`).
```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10
```
**Readiness probes** should use a shorter timeout for faster traffic redirection:
```yaml
readinessProbe:
  httpGet:
    path: /health/ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
```

---

## **Implementation Details**

### **1. Dependency Monitoring**
FraiseQL checks dependencies **asynchronously** in the background:
- **Database:** Verifies connection pool health.
- **Redis:** Pings the server and checks memory usage.
- **External APIs:** Tests a **non-critical endpoint** (e.g., `/status`).

### **2. Graceful Degradation**
- If a **non-critical dependency** fails, it logs a **warning** and continues running.
- If a **critical dependency** (e.g., database) fails, the service marks itself as **unready**.

### **3. Performance Optimizations**
- **Caching:** Dependency checks are **cached for 10 seconds** (configurable).
- **Parallel Checks:** Multiple dependencies are tested **concurrently** (default: 5 concurrent checks).

### **4. Configuration**
Health checks are configurable via environment variables:
| **Variable**          | **Default** | **Description**                          |
|-----------------------|-------------|------------------------------------------|
| `FR AISEQL_HEALTH_CHECK_INTERVAL` | `10s`       | How often to poll dependencies.          |
| `FR AISEQL_READINESS_TIMEOUT`      | `5s`        | Max time for readiness checks.           |
| `FR AISEQL_DEBUG`                     | `false`     | Enable `/health/debug` endpoint.        |

Example:
```bash
FR AISEQL_HEALTH_CHECK_INTERVAL=5s FR AISEQL_DEBUG=true ./fraiseql
```

### **5. Security**
- **No authentication** for `/health/live` and `/health/ready` (required for Kubernetes probes).
- **Rate limiting** enabled by default (100 requests/minute).

---

## **Error Handling & Retries**

| **Error Type**          | **Response Code** | **Kubernetes Impact**                     |
|-------------------------|-------------------|-------------------------------------------|
| **Database down**       | `503`             | Pod marked **unready** (traffic routed elsewhere). |
| **Redis timeout**       | `503`             | Pod marked **unready** (if critical).     |
| **External API failure**| `429` (Rate limit) | Depends on configuration (may degrade gracefully). |
| **Internal crash**      | `500`             | Pod marked **unhealthy** (restarted).      |

**Retry Logic:**
- Kubernetes **liveness probes** retry every `periodSeconds` (default: 10s).
- **Readiness probes** retry faster (default: 5s) for quicker failover.

---

## **Related Patterns**

1. **[Circuit Breaker Pattern]**
   - Use **resilience4j** to complement health checks by **auto-disabling failed dependencies**.
   - Example: If the database fails 3 times, FraiseQL stops retrying for 30 seconds.

2. **[Distributed Tracing]**
   - Integrate with **Jaeger/Zipkin** to trace dependency failures across microservices.

3. **[Configuration as Code]**
   - Store health check thresholds (e.g., max DB latency) in **environment variables** or a config file.

4. **[Observability Stack]**
   - Export health metrics to **Prometheus** (`/metrics` endpoint) for monitoring.
   - Example Prometheus rule:
     ```promql
     alert HighDatabaseLatency if fraiseql_database_latency > 1000
     ```

5. **[Chaos Engineering]**
   - Use **Chaos Mesh** to **simulate dependency failures** (e.g., kill Redis pod) and test recovery.

---

## **Best Practices**

✅ **Do:**
- Use **separate probes** (`live` vs. `ready`) for different failure scenarios.
- **Test in staging** before deploying to production.
- **Monitor `/health/ready` failures** in observability tools (e.g., Datadog).

❌ **Don’t:**
- Assume `/health/live` = **fully functional** (always check `/health/ready` for dependencies).
- Ignore **graceful degradation**—design services to recover from partial failures.
- Use **hardcoded thresholds** (e.g., "Redis must respond in <100ms") without monitoring.

---
**Need more details?** Check the [FraiseQL Source Code](https://github.com/fraiseql/fraiseql/blob/main/docs/health-checks.md).