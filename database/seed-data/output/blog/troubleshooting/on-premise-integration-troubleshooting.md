# **Debugging On-Premise Integration: A Troubleshooting Guide**
*For Senior Backend Engineers*

On-premise integration involves connecting cloud-based or hybrid systems with legacy or locally hosted applications. Common issues arise from network latency, authentication failures, schema mismatches, and unhandled exceptions. This guide provides a systematic approach to diagnosing and resolving integration problems efficiently.

---

## **1. Symptom Checklist**
Before diving into debugging, classify symptoms into **Network, Authentication, Data, Performance, or Application Issues**. Check:

### **Network-Related Symptoms**
✅ **Connection refused / Timeout errors** (e.g., `Connection refused: connect()` in HTTP clients)
✅ **SSL/TLS handshake failures** (e.g., `SSL_ERROR_SSL` in Java)
✅ **Firewall/Proxy filtering packets** (e.g., `No route to host` errors)
✅ **DNS resolution failures** (e.g., `DNS_PROBE_FINISHED_NXDOMAIN`)
✅ **Slow response times** (latency > 1s for synchronous calls)

### **Authentication/Authorization Symptoms**
✅ **401/403 Unauthorized/Forbidden errors** (JWT/OAuth validation failures)
✅ **Session expiration** (expired tokens in API gateway logs)
✅ **Invalid credentials** (misconfigured API keys, service accounts)

### **Data-Related Symptoms**
✅ **Schema mismatches** (e.g., field name changes, type mismatches)
✅ **Corrupted payloads** (malformed JSON/XML in logs)
✅ **Data inconsistency** (duplicate entries, stale records)
✅ **Transaction failures** (e.g., `Database Deadlock` in SQL)

### **Performance Symptoms**
✅ **High latency in bulk operations** (e.g., 1000-record batch failing)
✅ **Memory leaks** (unbounded queues in message brokers)
✅ **Deadlocks/wait chains** (`BLOCKED` status in database queries)

### **Application-Level Symptoms**
✅ **Crashes on deserialization** (e.g., `JsonParseException`)
✅ **Uncaught exceptions** (stack traces in logs)
✅ **Race conditions** (e.g., `ConcurrentModificationException`)

---

## **2. Common Issues & Fixes (With Code Examples)**

### **Issue 1: Connection Timeouts**
**Symptom:**
`java.net.SocketTimeoutException` (Java) or `Request Timeout` (HTTP clients).

**Root Cause:**
- Firewall blocking ports (default: 443 for HTTPS).
- Network congestion or misconfigured proxies.
- Idle connections not closing.

**Fix:**
```java
// Java - Increase timeout (HTTP client)
HttpRequest request = HttpRequest.newBuilder()
    .timeout(Duration.ofSeconds(30))  // Default: 30s
    .uri(URI.create("https://onpremise-api.com/data"))
    .build();

// Test with telnet/curl
curl --connect-timeout 10 https://onpremise-api.com
```

**Prevention:**
- Use **keep-alive** for HTTP/2.
- Monitor network latency with `ping`/`traceroute`.

---

### **Issue 2: Authentication Failures (JWT/OAuth)**
**Symptom:**
`401 Unauthorized` with no error payload.

**Root Cause:**
- Expired token (missing `refresh_token` logic).
- Incorrect audience (`aud` claim mismatch).
- Missing `Authorization: Bearer` header.

**Fix:**
```java
// Verify JWT in Spring Security
@Configuration
public class SecurityConfig {
    @Bean
    public JwtDecoder jwtDecoder() {
        return NimbusJwtDecoder.withJwkSetUri("https://auth-server/.well-known/jwks.json")
            .build();
    }

    @Bean
    public JwtAuthenticationConverter jwtConverter() {
        return new JwtAuthenticationConverter();
    }
}
```

**Prevention:**
- Cache tokens with short TTL (e.g., 5m).
- Use **OAuth2 Introspection** for token validation.

---

### **Issue 3: Schema Mismatches**
**Symptom:**
`SchemaValidationError` (JSON Schema) or `NullPointerException`.

**Root Cause:**
- API contract drift (e.g., `user.id` → `user.userId`).
- Missing optional fields in payload.

**Fix (Python Example):**
```python
from pydantic import BaseModel, ValidationError

class OldUserModel(BaseModel):
    user_id: str

class NewUserModel(BaseModel):
    userId: str  # Updated field name

# Handle migration gracefully
def migrate_payload(payload):
    try:
        return NewUserModel(**payload)
    except ValidationError as e:
        old_model = OldUserModel(**payload)
        return {"userId": old_model.user_id}
```

**Prevention:**
- Use **API versioning** (`/v1/users`, `/v2/users`).
- Enforce backward compatibility with **schema registry** (e.g., Avro).

---

### **Issue 4: Data Corruption (Malformed Payloads)**
**Symptom:**
`JsonParseException` or `XmlPullParserException`.

**Root Cause:**
- Incomplete payloads (network split).
- Incorrect encoding (UTF-8 vs. ISO-8859-1).

**Fix (Java Example):**
```java
// Handle malformed JSON safely
try {
    ObjectMapper mapper = new ObjectMapper();
    mapper.configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
    User user = mapper.readValue(inputStream, User.class);
} catch (JsonProcessingException e) {
    log.error("Invalid JSON payload: {}", e.getMessage());
    throw new BadRequestException("Malformed data");
}
```

**Prevention:**
- Validate payloads with **JSON Schema** (e.g., [jsonschema](https://github.com/Julian/jsonschema)).
- Use **idempotent APIs** for retries.

---

### **Issue 5: Database Deadlocks**
**Symptom:**
`SQLSTATE[40P01]` (PostgreSQL) or `DeadlockFound` (SQL Server).

**Root Cause:**
- Two transactions locking the same row.
- Long-running queries holding locks.

**Fix (SQL Query Optimization):**
```sql
-- Avoid long queries (use LIMIT)
SELECT * FROM orders WHERE status = 'processed';  -- Ugly
SELECT * FROM orders WHERE status = 'processed' LIMIT 1000;  -- Better

-- Use proper indexing
CREATE INDEX idx_order_status ON orders(status);
```

**Prevention:**
- Implement **pessimistic locking** (e.g., `SELECT ... FOR UPDATE` in PostgreSQL).
- Use **connection pooling** (HikariCP) to limit active connections.

---

## **3. Debugging Tools & Techniques**

### **Network Debugging**
| Tool | Purpose | Example Command |
|------|---------|----------------|
| **Wireshark** | Packet inspection | `tshark -i eth0 -f "tcp port 443"` |
| **tcpdump** | Low-level traffic capture | `tcpdump -i eth0 host 192.168.1.100` |
| **curl -v** | HTTP request inspection | `curl -v -X POST -H "Content-Type: application/json" https://api.example.com` |
| **Postman/Insomnia** | API request replay | Save failing request, modify headers, retry |

### **Logging & Tracing**
- **Structured Logging:**
  ```json
  // Log payloads (redact PII)
  LOG.info("Request: {} | Response: {}", requestBody, responseBody);
  ```
- **Distributed Tracing:**
  Use **OpenTelemetry** or **Jaeger** to trace requests across services.
  ```java
  // Add tracing to JAX-RS
  @Context
  private Tracer tracer;
  public Response onPreMatch(ContainerRequestContext ctx) {
      tracer.activeSpan().setTag("http.method", ctx.getMethod());
      tracer.activeSpan().setTag("http.path", ctx.getUriInfo().getPath());
  }
  ```

### **Profiling & Memory Analysis**
- **JVM Profiling:**
  `jstack <pid>` (thread dumps)
  `jcmd <pid> GC.heap_history` (memory analysis)
- **Database Profiling:**
  ```sql
  -- PostgreSQL slow query log
  ALTER SYSTEM SET log_min_duration_statement = 100;
  ```

---

## **4. Prevention Strategies**

### **1. API Contract Management**
- Use **OpenAPI/Swagger** for versioned contracts.
- Implement **postman collections** for regression testing.

### **2. Retry Policies**
- **Exponential backoff** for transient failures:
  ```java
  // Java - Resilience4j
  RetryConfig config = RetryConfig.custom()
      .maxAttempts(3)
      .intervalFunction(RetryIntervalFixed.of(1, TimeUnit.SECONDS))
      .build();

 Retryable(on = { IOException.class })
  @RetryConfig(name = "defaultRetryConfig", fallbackMethod = "fallback")
  public String callOnPremiseApi(String url) { ... }
  ```

### **3. Monitoring & Alerts**
- **Key Metrics to Track:**
  - `connection_errors` (Prometheus)
  - `auth_failures` (Grafana dashboards)
  - `data_validation_errors` (ELK stack)
- **Alert Thresholds:**
  - `latency > 500ms` → Alert (PagerDuty)
  - `error_rate > 5%` → Escalate

### **4. Chaos Engineering**
- **Simulate failures** with **Chaos Mesh** or **Gremlin**:
  ```yaml
  # Chaos Mesh - Network Latency Injection
  apiVersion: chaos-mesh.org/v1alpha1
  kind: NetworkChaos
  metadata:
    name: onpremise-network-latency
  spec:
    action: delay
    mode: one
    selector:
      namespaces:
        - default
      pod:
        name: onpremise-api
    delay:
      latency: "100ms"
  ```

### **5. Documentation & Runbooks**
- **Standardize integration docs** (e.g., `/docs/onpremise-integration.md`).
- **Create runbooks** for:
  - "API Gateway Misconfiguration"
  - "Database Connection Issues"

---

## **Final Checklist for Quick Resolution**
| Step | Action | Tool |
|------|--------|------|
| 1 | Check network connectivity | `curl -v`, `telnet` |
| 2 | Validate authentication | JWT/OAuth tools (Postman) |
| 3 | Verify payload schema | JSON Schema Validator |
| 4 | Test database connectivity | `pg_isready`, `mssql-cli` |
| 5 | Inspect logs | ELK, Datadog, or local logs |
| 6 | Reproduce in staging | Docker/Kubernetes |

---
**Key Takeaway:**
On-premise integrations fail due to **disconnected teams, misconfigurations, or evolving requirements**. Focus on **observability (logs, metrics, traces)**, **automated validation**, and **fail-safe retry policies** to minimize downtime.

**Next Steps:**
1. Audit existing integrations for **deprecated APIs**.
2. Implement **automated schema validation** (e.g., [JSON Schema Validator](https://www.jsonschemavalidator.net/)).
3. Set up **SLOs** for integration reliability (e.g., 99.9% uptime).

---
Would you like a deeper dive into any specific area (e.g., Kafka integration, ADFS/OAuth2 deep dives)?