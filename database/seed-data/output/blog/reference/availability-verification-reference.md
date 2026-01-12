---
# **[Pattern] Availability Verification – Reference Guide**

---

## **Overview**
The **Availability Verification** pattern ensures that resources (e.g., services, devices, endpoints, or infrastructure components) are operational and accessible before initiating dependent operations. This pattern prevents failures caused by transient downtime, misconfigurations, or network issues, improving system resilience.

Key use cases:
- **Pre-flight checks** before processing user requests (e.g., validating database availability before query execution).
- **Dynamic dependency resolution** in microservices architectures (e.g., checking API gateway health before routing traffic).
- **Infrastructure orchestration** (e.g., verifying container readiness in Kubernetes before deploying workloads).
- **Failure recovery** (e.g., reattempting operations after temporary outages).

The pattern follows a **check-then-act** workflow, where the system verifies availability via lightweight probes (e.g., HTTP `HEAD`/`OPTIONS`, ping, TCP handshake) before proceeding with resource-intensive operations. It complements patterns like **Retry with Exponential Backoff** and **Circuit Breaker**, offering proactive validation.

---

## **Schema Reference**

| **Field**               | **Type**       | **Description**                                                                 | **Example Values**                          | **Required?** |
|-------------------------|----------------|---------------------------------------------------------------------------------|---------------------------------------------|----------------|
| **Resource Identifier** | `string`       | Unique identifier for the resource (e.g., endpoint URL, hostname, service name). | `"https://api.example.com/v1/health"`, `"db-primary"` | ✅ Yes          |
| **Check Type**          | `enum`         | Method to verify availability.                                                   | `HTTP`, `TCP`, `Ping`, `CustomScript`       | ✅ Yes          |
| **Check Parameters**    | `object`       | Configuration for the specific check type.                                      | Varies by type (see subfields below).      | ✅ Yes          |
| **Timeout (ms)**        | `integer`      | Max time to wait for a response before failing the check.                       | `1000` (1 second)                           | ✅ Yes          |
| **Interval (ms)**       | `integer`      | Frequency of checks (e.g., for dynamic environments).                           | `30000` (30 seconds)                        | ❌ No           |
| **Threshold**           | `integer`      | Minimum acceptable response time or success rate (for probabilistic checks).     | `500` (ms), `0.99` (success rate)           | ❌ No           |
| **Authentication**      | `object`       | Credentials or tokens for secure checks.                                        | `{ "bearerToken": "abc123", "apiKey": "xyz" }` | ❌ No           |
| **Expected Status Code**| `array`        | Valid HTTP status codes for success (e.g., `[200, 204]`).                        | `[200, 202]`                               | ❌ No           |
| **Payload**             | `object`       | Data sent in the check request (e.g., for custom scripts).                      | `{ "action": "status" }`                   | ❌ No           |
| **Metadata**            | `object`       | Custom tags or labels for categorization/logging.                               | `{ "environment": "prod", "team": "backend" }` | ❌ No           |
| **Dependency Graph**    | `array`        | Hierarchy of resources (e.g., `db → cache → api`).                              | `[{ "type": "primary", "dependsOn": ["db"] }]` | ❌ No           |

---

### **Check-Type Subfields**

| **Check Type** | **Parameters**                          | **Description**                                                                 |
|----------------|-----------------------------------------|---------------------------------------------------------------------------------|
| **HTTP**       | `method`, `headers`, `path`, `body`     | Configures HTTP requests (e.g., `GET /health`).                                |
| **TCP**        | `port`                                  | Tests if a TCP port is open (no HTTP parsing).                                |
| **Ping**       | `icmp`, `timeout`                       | Uses ICMP echo requests for network-level checks.                               |
| **CustomScript**| `scriptPath`, `args`                   | Executes a local script (e.g., `./custom_check.sh`).                           |

---

## **Implementation Details**

### **1. Check Execution Flow**
1. **Trigger**: Initiate verification (e.g., on system startup, before request processing, or via polling).
2. **Probe**: Send a lightweight check (e.g., `HEAD /health`).
3. **Validate**: Compare response to success criteria (e.g., status code, latency).
4. **Result Handling**:
   - **Success**: Proceed with the dependent operation.
   - **Failure**: Log, notify (e.g., via **Alerting**), and:
     - Retry (if transient).
     - Fail fast (if critical dependency).
     - Use fallback (e.g., secondary endpoint).

---

### **2. Key Design Principles**
- **Idempotency**: Checks should not alter the resource state (e.g., avoid `POST` requests).
- **Statelessness**: Probes should not rely on session data.
- **Low Overhead**: Prioritize fast checks (e.g., `OPTIONS` over `GET` for CORS compatibility).
- **Decoupling**: Use event-driven models (e.g., publish/subscribe) for distributed checks.

---

### **3. Example Architectures**
- **Monolithic Apps**:
  ```mermaid
  graph TD
      A[User Request] --> B{Availability Check}
      B -->|Pass| C[Process Request]
      B -->|Fail| D[Notify & Retry/Fail]
  ```
- **Microservices**:
  ```mermaid
  graph TD
      A[Service A] --> B[Check Service B's Health]
      B -->|OK| C[Proceed with Workload]
      B -->|Timeout| D[Circuit Breaker: Skip Service B]
  ```

---

## **Query Examples**

### **1. HTTP Check (REST API)**
**Schema Snippet**:
```json
{
  "resource": "https://api.example.com/v1/health",
  "checkType": "HTTP",
  "checkParameters": {
    "method": "HEAD",
    "timeout": 500,
    "expectedStatusCodes": [200, 204],
    "authentication": {
      "bearerToken": "secure-token-123"
    }
  }
}
```
**Tool Output**:
```bash
$ curl -I -H "Authorization: Bearer secure-token-123" https://api.example.com/v1/health --max-time 0.5
HTTP/1.1 200 OK
```

---

### **2. TCP Check (Database)**
**Schema Snippet**:
```json
{
  "resource": "db-primary",
  "checkType": "TCP",
  "checkParameters": {
    "port": 5432,
    "timeout": 2000
  }
}
```
**Tool Output**:
```bash
$ nc -zv db-primary 5432
Connection to db-primary port 5432 succeeded!
```

---

### **3. Custom Script Check (Infrastructure)**
**Script (`/checks/vm_ready.sh`)**:
```bash
#!/bin/bash
if systemctl is-active --quiet docker; then
  exit 0
else
  exit 1
fi
```
**Schema Snippet**:
```json
{
  "resource": "vm-001",
  "checkType": "CustomScript",
  "checkParameters": {
    "scriptPath": "/checks/vm_ready.sh",
    "args": ["--verbose"]
  }
}
```
**Tool Output**:
```bash
$ /checks/vm_ready.sh --verbose
Docker service is running (OK)
exit_code: 0
```

---

## **Related Patterns**

| **Pattern**                  | **Description**                                                                 | **Interaction with Availability Verification**                          |
|------------------------------|---------------------------------------------------------------------------------|--------------------------------------------------------------------------|
| **Retry with Exponential Backoff** | Automatically retry failed operations with increasing delays.                    | Use verification results to determine if retries are needed.               |
| **Circuit Breaker**          | Prevents cascading failures by temporarily blocking calls to faulty services.    | Verification can trigger circuit opens/closes (e.g., after N failures).  |
| **Bulkheading**              | Isolates dependent operations to limit failure impact.                            | Verify critical dependencies before executing bulk tasks.                 |
| **Saga Pattern**             | Manages distributed transactions via compensating actions.                        | Verify each participant’s availability before initiating a saga.          |
| **Health Checks (Liveness/Readiness)** | Kubernetes-specific probes for pod health.                                    | Can reuse availability verification logic for Kubernetes endpoints.       |
| **Chaos Engineering**        | Deliberately introduces failures to test resilience.                              | Use verification to validate recovery mechanisms post-failure.           |

---

## **Best Practices**

1. **Minimize Latency**: Optimize check duration (e.g., prefer `HEAD` over `GET`).
2. **Prioritize Critical Paths**: Focus checks on high-impact dependencies first.
3. **Monitor and Alert**: Log verification results and set thresholds for alerts (e.g., "TCP fails >3 times in 5 mins").
4. **Avoid Overhead in High-Traffic Systems**: Cache results where possible (e.g., 30-second interval for stable environments).
5. **Document Failure Modes**: Define SLOs/SLIs for each check (e.g., "API must respond in <500ms 99.9% of the time").
6. **Test in Staging**: Validate checks in a pre-production environment mirroring production constraints.

---
**See also**:
- [Kubernetes Liveness/Readiness Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [OpenTelemetry Health Checks](https://opentelemetry.io/docs/specs/otel/protocol/collector/health/)