# **[Pattern] Hybrid Debugging – Reference Guide**

---

## **Overview**
**Hybrid Debugging** combines **local debugging** (direct, high-fidelity tooling) with **distributed tracing/logging** (system-wide observability) to diagnose issues in **multi-service, multi-container, or microservices architectures** where traditional local debugging is impractical. This pattern enables developers to:
- **Isolate problems** by correlating logs, traces, and metrics across services.
- **Reproduce bugs in production-like environments** without disrupting production.
- **Leverage both IDE-based and distributed debugging tools** for efficient troubleshooting.

Hybrid Debugging is ideal for teams using **Kubernetes, serverless (AWS Lambda, Azure Functions), or hybrid cloud deployments** where components are geographically distributed or dynamically scaled. It bridges the gap between **developer productivity** (local debugging) and **system reliability** (observability).

---

## **Implementation Details**

### **Key Concepts**
| **Concept**               | **Description**                                                                                                                                                                                                 | **Tools/Libraries**                                                                                   |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| **Local Debugging**       | Traditional IDE-based debugging (breakpoints, variable inspection) in a controlled environment.                                                                                                            | VS Code, IntelliJ IDEA, PyCharm, Eclipse                                                                 |
| **Distributed Tracing**   | Tracking requests as they traverse multiple services by injecting **trace IDs** and propagating context.                                                                                                    | OpenTelemetry, Jaeger, Zipkin, AWS X-Ray, Datadog Trace                                                  |
| **Structured Logging**    | Logging with **metadata (trace IDs, timestamps, service names)** to correlate logs across services.                                                                                                       | Log4j, ELK Stack, Splunk, Loki                                                                         |
| **Context Propagation**   | Passing debugging context (e.g., session IDs, debug flags) between services via **headers, cookies, or database lookups**.                                                                               | Custom headers, JWT tokens, service mesh (Istio, Linkerd)                                               |
| **Shadow Debugging**      | Running a **mirror instance** of a service with debug tools attached while the real instance continues serving requests.                                                                                  | Kubernetes `sidecar` probes, proxy-based redirection (nginx, Envoy)                                    |
| **Remote Debugging**      | Attaching debuggers to **live containers** (e.g., Kubernetes pods) or remote machines via **SSH/RDP** or **debug adapters**.                                                                             | Chrome DevTools Protocol (CDP), VS Code Remote Attach, Docker Debug                                      |
| **Debugging SDKs**        | Language-specific libraries for **dynamic breakpoint insertion, conditional logging, and telemetry-injected debugging**.                                                                                     | Node.js Debugger, Python `pdb`/`pudb`, Java `JVMTI`, Go `delve`                                           |

---

### **Schema Reference**
The following schema defines the **Hybrid Debugging Pipeline**:

| **Field**               | **Type**       | **Description**                                                                                                                                                                                                 | **Example Value**                     |
|-------------------------|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------|
| `debugSessionId`        | `string`       | Unique identifier for the debugging session (correlates logs/traces).                                                                                                                                             | `dbg-123e4567-e89b-12d3-a456-426614174000` |
| `serviceName`           | `string`       | Name of the service being debugged.                                                                                                                                                                       | `user-service`                        |
| `debugMode`             | `enum`         | Debugging strategy: `local`, `remote`, `shadow`, or `distributed`.                                                                                                                                          | `shadow`                              |
| `traceId`               | `string`       | Unique trace ID for correlating requests across services.                                                                                                                                                  | `trace-id-abc123`                     |
| `logLevel`              | `string`       | Log verbosity: `debug`, `info`, `warn`, `error`.                                                                                                                                                             | `debug`                               |
| `breakpoints`           | `array[object]`| List of breakpoint objects with `file`, `line`, and `condition`.                                                                                                                                          | `[{ "file": "auth.py", "line": 42 }]`  |
| `context`               | `object`       | Key-value pairs for context propagation (e.g., `debug=true`).                                                                                                                                               | `{ "debug": true, "userId": "123" }`  |
| `targetInstance`        | `object`       | Details of the instance to debug (container ID, pod name, IP).                                                                                                                                                | `{ "pod": "auth-pod-1", "namespace": "prod" }` |
| `debugAdapter`          | `string`       | Protocol/adapter for remote debugging (e.g., `chrome-devtools`, `kubernetes-sidecar`).                                                                                                                       | `chrome-devtools`                     |
| `startTime`             | `timestamp`    | When the debugging session began.                                                                                                                                                                       | `2024-05-20T12:00:00Z`                |
| `endTime`               | `timestamp`    | When the debugging session ended (optional).                                                                                                                                                               | `2024-05-20T12:05:30Z`                |

---
**JSON Example:**
```json
{
  "debugSessionId": "dbg-123e4567-e89b-12d3-a456-426614174000",
  "serviceName": "user-service",
  "debugMode": "shadow",
  "traceId": "trace-id-abc123",
  "logLevel": "debug",
  "breakpoints": [{"file": "auth.py", "line": 42}],
  "context": {"debug": true, "userId": "123"},
  "targetInstance": {"pod": "auth-pod-1", "namespace": "prod"},
  "debugAdapter": "kubernetes-sidecar"
}
```

---

## **Query Examples**
### **1. Correlating Logs with a Trace ID**
**Goal:** Find all logs for a trace ID where `debug=true`.
**Query (Elasticsearch/Kibana):**
```json
{
  "query": {
    "bool": {
      "must": [
        { "term": { "trace_id.keyword": "trace-id-abc123" } },
        { "term": { "context.debug": true } }
      ]
    }
  }
}
```
**Output:**
Returns logs from all services with `traceId: trace-id-abc123` and `debug: true`, enabling cross-service correlation.

---

### **2. Finding Active Debug Sessions**
**Goal:** List all active hybrid debugging sessions (where `endTime` is `null`).
**Query (SQL-like):**
```sql
SELECT *
FROM debug_sessions
WHERE endTime IS NULL
ORDER BY startTime DESC;
```
**Output:**
| `debugSessionId`          | `serviceName` | `debugMode` | `traceId`       | `startTime`          |
|---------------------------|----------------|--------------|-----------------|----------------------|
| `dbg-123e4567...`         | `user-service` | `shadow`     | `trace-id-abc123`| `2024-05-20T12:00:00Z` |

---

### **3. Identifying Broken Breakpoints**
**Goal:** Find breakpoints that were never hit in the last 24 hours.
**Query (PromQL for metrics):**
```promql
# Metrics to track: `debug_breakpoint_hits{service="user-service"}`
sum by (breakpoint) (
  rate(debug_breakpoint_hits[1d])
) < 1
```
**Output:**
Returns breakpoints (e.g., `auth.py:42`) that were never triggered, indicating they may be misconfigured.

---

### **4. Shadow Debugging Workflow**
**Steps to debug a production `payment-service`:**
1. **Deploy a shadow pod** (mirroring `payment-service`) with debug flags:
   ```yaml
   # deployment.yaml (shadow instance)
   containers:
     - name: payment-service
       image: payment-service:latest
       command: ["python", "-m", "debug", "--shadow"]
   ```
2. **Initiate a debug session** via OpenTelemetry trace ID:
   ```bash
   kubectl logs payment-service-shadow -l app=payment-service --tail=100 --since=1h
   ```
3. **Attach IDE debugger** to the shadow pod via VS Code Remote Attach:
   - Configure `launch.json`:
     ```json
     {
       "type": "cppdbg",
       "request": "attach",
       "name": "Attach to Shadow Pod",
       "miDebuggerPath": "/usr/bin/gdb",
       "processId": "${command:pickProcess}",
       "remoteHost": "pod-ip-from-kubectl"
     }
     ```

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                                                                                                                                                 | **Use Case for Hybrid Debugging**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------|
| **Circuit Breaker**       | Isolates failures in one service from affecting others.                                                                                                                                                       | Use shadow debugging to validate circuit breaker logic without impacting production.                              |
| **Service Mesh**          | Manages inter-service communication (Istio, Linkerd).                                                                                                                                                     | Propagate debug context (e.g., `X-Debug-ID`) via service mesh sidecars.                                          |
| **Feature Flags**         | Dynamically enable/disable features.                                                                                                                                                                       | Temporarily enable debug logging for a subset of users via feature flags.                                           |
| **Chaos Engineering**     | Intentionally inject failures to test resilience.                                                                                                                                                         | Hybrid debugging helps diagnose why a chaos experiment (e.g., pod kill) caused cascading failures.              |
| **Distributed Cache**     | Stores data in-memory (Redis, Memcached) for low-latency access.                                                                                                                                         | Debug cache misses by correlating logs with cache hits/misses in distributed traces.                              |
| **Observability Pipeline**| Centralized logging, metrics, and tracing (OpenTelemetry, Grafana).                                                                                                                                       | Hybrid Debugging relies on this pipeline to correlate data across services.                                       |

---

## **Best Practices**
1. **Context Propagation:**
   - Use **standard headers** (`X-Trace-ID`, `X-Debug-ID`) or **OpenTelemetry context** to avoid inventing new keys.
   - Example:
     ```http
     GET /api/user HTTP/1.1
     X-Trace-ID: trace-id-abc123
     X-Debug-ID: dbg-123e4567...
     ```

2. **Shadow Debugging Limits:**
   - Shadow pods consume resources. **Limit shadow instances to non-production hours** or use **lightweight proxies** (e.g., Envoy).
   - Example proxy rule:
     ```yaml
     # Istio VirtualService for shadow debugging
     match:
       - headers(x-debug-id): ".*"
     route:
       - destination:
           host: payment-service.shadow.svc.cluster.local
     ```

3. **Breakpoint Management:**
   - Use **dynamic breakpoints** (e.g., `if (user.isAdmin) { pause }`) instead of static ones.
   - Tools: Python `pudb`, Java `JVMTI`, Node.js `inspect`.

4. **Security:**
   - Restrict debug sessions to **specific roles** (e.g., `debugger` Kubernetes RBAC).
   - Example policy:
     ```yaml
     apiVersion: rbac.authorization.k8s.io/v1
     kind: RoleBinding
     metadata:
       name: debug-access
     subjects:
       - kind: User
         name: alice
         apiGroup: rbac.authorization.k8s.io
     roleRef:
       kind: Role
       name: debug-pods
       apiGroup: rbac.authorization.k8s.io
     ```

5. **Performance Impact:**
   - **Disable debug logging in production** unless absolutely necessary (use feature flags).
   - Example flag:
     ```python
     # Python example
     if os.getenv("DEBUG_MODE", "false").lower() == "true":
         logging.basicConfig(level=logging.DEBUG)
     ```

---
## **Tools Checklist**
| **Category**          | **Tools**                                                                                     | **Key Features**                                                                                          |
|-----------------------|---------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------|
| **IDE Debuggers**     | VS Code, IntelliJ, PyCharm                                                        | Remote attach, breakpoint management, variable inspection.                                                |
| **Distributed Tracing** | OpenTelemetry, Jaeger, AWS X-Ray                     | Trace correlation, service graphs, latency analysis.                                                     |
| **Logging**           | ELK Stack, Splunk, Loki                                                             | Structured logs, log enrichment, queryable metadata.                                                     |
| **Container Debugging** | Docker Debug, VS Code Remote-SSH, Kubernetes Port-Forward | Attach debuggers to live containers, proxy requests.                                                     |
| **Shadow Debugging**  | Istio, Envoy, Kubernetes Sidecar                         | Mirror traffic to debug pods, context propagation.                                                        |
| **Observability**     | Prometheus, Grafana, Datadog                                | Metrics, alerts, dashboards for debugging context.                                                        |

---
## **Troubleshooting**
| **Issue**                          | **Root Cause**                                | **Solution**                                                                                                 |
|-------------------------------------|-----------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| **Lost trace context**              | Context not propagated between services.     | Use OpenTelemetry’s `propagator` (e.g., `baggage`) or standard headers.                                   |
| **Breakpoints not hitting**         | Shadow pod not receiving traffic.              | Verify Istio/Envoy rules route debug traffic to shadow pods.                                                 |
| **High latency during debugging**   | Debugging overhead.                          | Limit shadow instances, disable logging in non-debug builds.                                                 |
| **Permission denied (Kubernetes)**  | RBAC misconfiguration.                        | Grant `debug-pods` role to the user’s service account.                                                      |
| **Logs/traces misaligned**          | Incorrect `traceId` or `debugSessionId`.      | Use unique, globally random IDs (UUIDv4) and ensure propagation in all services.                           |