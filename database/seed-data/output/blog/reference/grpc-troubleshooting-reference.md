# **[Pattern] GRPC Troubleshooting Reference Guide**

---

## **Overview**
This guide provides a structured approach to diagnosing and resolving issues in **gRPC (gRPC Remote Procedure Call)** deployments and communications. gRPC is a high-performance RPC framework built on HTTP/2, and while it offers efficiency and scalability, it requires careful monitoring due to its complexity. This guide covers common error scenarios, debugging techniques, logging strategies, and best practices for both client and server-side issues.

---

## **1. Key Concepts in gRPC Troubleshooting**

| **Concept**               | **Description**                                                                                                                                                                                                                                                                 |
|---------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Transport Layers**      | gRPC relies on **HTTP/2** (layered on TLS or plaintext). Issues in transport (e.g., TLS handshake failures, proxy misconfigurations) often cause connectivity errors.                                                                                       |
| **Error Codes**           | gRPC uses specific **status codes** (defined in [`grpc/status/code.proto`](https://github.com/grpc/grpc/blob/master/doc/statusCodes.md)) to indicate errors (e.g., `UNAVAILABLE`, `PERMISSION_DENIED`, `INVALID_ARGUMENT`). Error messages are structured. |
| **Deadlines & Timeouts**  | Clients set **deadlines** (e.g., `context.WithTimeout()`) to avoid indefinite hangs. Server-side timeouts (e.g., `GrpcServerShutdownTimeout`) must also be configured.                                                                                   |
| **Load Balancing**        | gRPC clients use **LoadReportingBalancer** or **pick_first** policies. Misconfigurations can lead to uneven traffic distribution or failures.                                                                                                       |
| **Interceptors**          | Client/server **interceptors** (e.g., logging, auth) can intercept RPC calls. Misbehaving interceptors may corrupt requests/responses or introduce latency.                                                                                                |
| **Metrics & Logging**     | gRPC provides **prometheus/grpc-stub** integration and structured logging. Metrics (e.g., `grpc_server_handled_total`) and logs (e.g., `grpc: received message`) are critical for debugging.                                                           |
| **Serialization**         | gRPC uses **Protocol Buffers (protobuf)**. Schema mismatches (e.g., missing fields, version mismatches) cause `INVALID_ARGUMENT` errors.                                                                                                                 |
| **Network Partitioning**  | gRPC handles retries for transient failures (e.g., `UNAVAILABLE`). Retry policies (e.g., exponential backoff) must be tuned to avoid cascading failures.                                                                                                      |
| **Security Issues**       | Misconfigured **TLS** (e.g., expired certificates, weak ciphers) or **authentication** (e.g., missing `metadata`) leads to connection drops or `PERMISSION_DENIED`.                                                                                   |
| **gRPC-Gateway**          | REST-gRPC proxies (e.g., Envoy, gRPC-Gateway) may introduce latency or errors if misconfigured (e.g., incorrect request/response mapping).                                                                                                          |

---

## **2. Schema Reference**

### **gRPC Status Codes (Key Errors)**
| **Code**               | **Description**                                                                                                                                                                                                                     | **Example Scenario**                                                                                     |
|------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| `OK`                   | Success.                                                                                                                                                                                                         | Normal RPC completion.                                                                                    |
| `CANCELLED`            | Client cancelled the RPC (e.g., `context.Done()`).                                                                                                                                                             | User cancels in-progress request.                                                                           |
| `UNAVAILABLE`          | Server unavailable (e.g., no active connection, overload).                                                                                                                                                       | Server restart or network partition.                                                                       |
| `DEADLINE_EXCEEDED`    | Request timeout.                                                                                                                                                                                               | Client deadline too short for server processing.                                                         |
| `INTERNAL`             | Server-side error (non-recoverable).                                                                                                                                                                       | Bug in server implementation.                                                                             |
| `INVALID_ARGUMENT`     | Invalid protobuf schema or metadata.                                                                                                                                                                         | Missing required field in request.                                                                        |
| `PERMISSION_DENIED`    | Auth failure (e.g., missing token, invalid role).                                                                                                                                                                 | Invalid JWT in Authorization header.                                                                       |
| `UNAUTHENTICATED`      | No credentials provided.                                                                                                                                                                                       | Missing `grpc.gateway.auth` header.                                                                      |
| `DATA_LOSS`            | Partial data loss (e.g., stream corruption).                                                                                                                                                               | Network interruption during streaming RPC.                                                               |

---

### **Common gRPC Fields in Error Messages**
| **Field**              | **Type**       | **Description**                                                                                                                                                                                                           |
|------------------------|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `code`                 | `StatusCode`   | Numeric error code (e.g., `3` for `UNAVAILABLE`).                                                                                                                                                                   |
| `message`              | `string`       | Human-readable error description.                                                                                                                                                                                   |
| `details`              | `bytes`        | Structured error data (e.g., protobuf-encoded metadata).                                                                                                                                                           |
| `metadata`             | `map<string, string>` | Additional key-value pairs (e.g., `grpc-status-details-bin`).                                                                                                                                                     |

---
## **3. Query Examples**

### **3.1. Checking gRPC Server Logs**
**Command:**
```bash
# Tail server logs (adjust path to your server binary)
journalctl -u grpc-server --no-pager -f
# OR
docker logs <container_name>
```
**Expected Output (Error Example):**
```
W0601 14:30:00.123 grpc_server.cc:204] RPC failed: status = {code = UNAVAILABLE, details = "Connection closed by peer", metadata = {grpc-status-details-bin=...}}
```

---

### **3.2. Testing Connection with `grpcurl`**
**Command:**
```bash
# Test server health (requires grpcurl)
grpcurl -plaintext localhost:50051 list
# OR
grpcurl -plaintext -d '{"key": "value"}' localhost:50051 com.example.Service/Method
```
**Error Examples:**
- `connect: connection refused` → Server not running or port misconfigured.
- `rpc error: code = InvalidArgument desc = protobuf: invalid wire format` → Malformed request.

---

### **3.3. Inspecting Network Traffic with Wireshark**
**Command:**
```bash
# Capture HTTP/2 traffic (filter on port 50051)
tcp.port == 50051 && http2
```
**Key Patterns:**
- **TLS Handshake Failures:** Check for `SSL handshake failed` errors.
- **Stream Errors:** Look for `SETTINGS_FRAME` errors (e.g., `goaway`).
- **Latency:** Measure time between **CLIENT_STREAM** and **SERVER_STREAM** frames.

---

### **3.4. Debugging Retry Policies**
**Command (Go Client Example):**
```go
import (
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

// Custom retry logic
conn, err := grpc.Dial(
	"localhost:50051",
	grpc.WithUnaryInterceptor(retryInterceptor),
	grpc.WithDefaultServiceConfig(`{
		"loadBalancingPolicy": "round_robin",
		"retryPolicy": {
			"MaxAttempts": 3,
			"InitialBackoff": ".1s",
			"MaxBackoff": "1s",
			"BackoffMultiplier": 2.0
		}
	}`),
)
```
**Debugging Retries:**
- If retries fail, check server logs for `INTERNAL` errors.
- Use `grpc_health_check` to verify server readiness.

---

### **3.5. Validating Protobuf Schemas**
**Command:**
```bash
# Compile proto files (check for errors)
protoc --go_out=. --go_opt=paths=source_relative --go-grpc_out=. --go-grpc_opt=paths=source_relative api/proto/service.proto
```
**Common Errors:**
- `expected field "id" but got "user_id"` → Field name mismatch.
- `service "Service" already defined` → Duplicate service definition.

---

### **3.6. Monitoring gRPC Metrics (Prometheus)**
**Metrics to Check:**
| **Metric**                          | **Description**                                                                                                                                                                                                           | **Alert Condition**                                      |
|-------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------|
| `grpc_server_started_total`         | Count of server starts.                                                                                                                                                                                        | High restart rate (`>1/min`).                             |
| `grpc_server_handled_total`         | Total RPCs handled (split by status code).                                                                                                                                                                      | `UNAVAILABLE` errors spike.                              |
| `grpc_client_call_duration`         | Latency of client calls (histogram).                                                                                                                                                                            | P99 latency > 1s.                                        |
| `grpc_client_handled_total`         | RPCs attempted vs. successful.                                                                                                                                                                                | Retry rate (`UNAVAILABLE` + `DEADLINE_EXCEEDED`) > 20%. |
| `grpc_stream_message`               | Messages sent/received in streaming RPCs.                                                                                                                                                                      | Dropped packets (`sent > received`).                       |
| `grpc_server_handling_seconds`      | Time spent processing RPCs.                                                                                                                                                                                      | Server-side bottlenecks.                                |

**Query Example (PromQL):**
```promql
# RPCs failing with UNAVAILABLE
sum(rate(grpc_client_handled_total{status="UNAVAILABLE"}[5m])) by (service)
```

---

### **3.7. Testing with `grpc_health_probe`**
**Command:**
```bash
# Check server health
grpc_health_probe -addr=localhost:50051 com.example.Health
```
**Expected Output:**
- `SERVING` → Server is healthy.
- `NOT_SERVING` → Service unavailable (e.g., underlying DB down).

---

## **4. Related Patterns**

| **Pattern**                  | **Description**                                                                                                                                                                                                                     | **When to Use**                                                                                         |
|------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| **[gRPC Load Balancing]**     | Distribute traffic across multiple servers using policies like `round_robin`, `least_conn`, or `pick_first`.                                                                                                             | Scaling horizontally; handling server failures gracefully.                                              |
| **[gRPC Interceptors]**       | Add logging, auth, or metrics to RPC calls without modifying core logic.                                                                                                                                             | Centralizing cross-cutting concerns (e.g., tracing, rate limiting).                                   |
| **[gRPC Streams]**            | Handle bidirectional or server-side streams for real-time data (e.g., chat, live updates).                                                                                                                               | Event-driven architectures; WebSocket-like functionality.                                            |
| **[Protobuf Schema Evolution]** | Manage breaking changes in protobuf schemas with backward/forward compatibility.                                                                                                                             | Refactoring services with existing clients.                                                            |
| **[gRPC Gateway]**            | Expose gRPC services via REST/HTTP using Envoy, gRPC-Gateway, or OpenAPI.                                                                                                                                         | Integrating with non-gRPC clients (e.g., mobile apps, legacy systems).                              |
| **[gRPC in Serverless]**     | Deploy gRPC services in AWS Lambda, Cloud Run, or Knative.                                                                                                                                                            | Serverless microservices; event-driven workflows.                                                    |
| **[gRPC Security]**           | Secure gRPC with TLS, mTLS, or JWT authentication.                                                                                                                                                                    | Protecting sensitive APIs; compliance requirements.                                                  |
| **[gRPC Performance Tuning]** | Optimize gRPC for low latency (e.g., connection pooling, compression).                                                                                                                                              | High-throughput systems; reducing overhead.                                                          |
| **[gRPC Observability]**      | Instrument gRPC with OpenTelemetry for distributed tracing.                                                                                                                                                            | Debugging latency in microservices; SLO-based monitoring.                                            |

---

## **5. Common Pitfalls & Fixes**

| **Issue**                          | **Root Cause**                                                                                                                                                                                                 | **Solution**                                                                                                                                                                                                 |
|-------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Connection Timeouts**             | Client deadline too short or server overload.                                                                                                                                                               | Increase deadline (e.g., `context.WithTimeout(10s)`) or scale servers.                                                                                                                                     |
| **`INVALID_ARGUMENT` Errors**       | Protobuf schema mismatch (e.g., missing required field).                                                                                                                                                       | Update client/server schemas; use `protoc` to validate.                                                                                                                                                         |
| **`UNAVAILABLE` Errors**            | Server not reachable or network partition.                                                                                                                                                                     | Check server logs; verify load balancer config. Implement retry logic with backoff.                                                                                                                           |
| **Stream Corruption**               | Network interruption during streaming RPC.                                                                                                                                                                     | Use `grpc.Keepalive` to detect dead connections. Enable client-side retries.                                                                                                                                     |
| **High Latency**                    | Large payloads or insufficient connections.                                                                                                                                                                     | Enable gzip compression (`grpc.WithCompressor("gzip")`). Increase connection pool size.                                                                                                                                |
| **Auth Failures**                   | Missing or invalid `metadata` (e.g., `authorization`).                                                                                                                                                         | Validate tokens; use interceptors to attach metadata.                                                                                                                                                              |
| **Race Conditions in Streams**      | Concurrent stream operations (e.g., send/cancel).                                                                                                                                                              | Use mutexes or channel buffering in server handlers.                                                                                                                                                             |
| **Memory Leaks**                    | Unclosed streams or lingering connections.                                                                                                                                                                     | Implement `grpc.UnaryInterceptor` to clean up resources. Use `grpc.WithPerRPCCredentials()`.                                                                                                                   |

---

## **6. References**
- **[gRPC Docs](https://grpc.io/docs/)** – Official documentation.
- **[gRPC Status Codes](https://github.com/grpc/grpc/blob/master/doc/statusCodes.md)** – Error code reference.
- **[Protobuf Schema Design](https://developers.google.com/protocol-buffers/docs/proto)** – Best practices.
- **[gRPC Health Checks](https://grpc.io/docs/guides/health-checks/)** – Health probing implementation.
- **[gRPC Retry Guide](https://grpc.io/docs/guides/retry/)** – Retry policy tuning.
- **[gRPC Load Balancing](https://grpc.io/docs/guides/client-architectures/)** – Client-side LB strategies.
- **[gRPC Gateway](https://github.com/grpc-ecosystem/grpc-gateway)** – REST-gRPC translation.