# **[Pattern] gRPC Troubleshooting Reference Guide**

---

## **Overview**
gRPC (gRPC Remote Procedure Call) is a modern, high-performance RPC framework for building distributed systems. While gRPC offers efficiency and language neutrality, it introduces unique challenges like connection management, serialization, and error handling. This guide provides a structured troubleshooting methodology for diagnosing and resolving common issues in gRPC-based applications. It covers network diagnostics, service logs, performance bottlenecks, and protocol-level problems, ensuring a systematic approach to resolving failures.

---

## **Key Concepts & Implementation Details**

### **1. Core gRPC Components**
| **Component**       | **Description**                                                                 |
|---------------------|-------------------------------------------------------------------------------|
| **Unary RPCs**      | Single request-response exchange (simplest, synchronous-like).                  |
| **Server Stream**   | Client sends one request; server streams multiple responses.                     |
| **Client Stream**   | Client streams multiple requests; server returns one response.                  |
| **Bidirectional**   | Both client and server stream requests/responses simultaneously.                |
| **Load Balancing**  | Distributes client traffic across multiple servers (e.g., `pick_first`, `least_conn`). |
| **Retry & Timeouts**| Configurable retry logic and deadline policies for fault tolerance.             |
| **Compression**     | Optional protocol buffers compression (e.g., `gzip`, `deflate`).               |

### **2. Common Failure Scenarios**
| **Scenario**               | **Root Cause**                                                                 | **Impact**                                                                 |
|----------------------------|-------------------------------------------------------------------------------|----------------------------------------------------------------------------|
| **Connection Rejected**    | TLS misconfiguration, DNS resolution failure, firewall blocking.             | Service unavailable; timeouts or errors.                                  |
| **500 Server Errors**       | Server-side crashes or logic errors.                                         | Partial or complete service degradation.                                  |
| **Slow RPCs**              | Network latency, serialization overhead, or inefficient code.               | Poor user experience; increased costs.                                   |
| **Unary vs. Streaming Mixup** | Incorrect stream type usage (e.g., calling a unary RPC as bidirectional).    | Protocol violations or crashes.                                           |
| **Metadata Corruption**    | Malformed headers (e.g., `authorization`, `trace-id`).                        | Security breaches or tracing failures.                                     |

---

## **Schema Reference**
gRPC errors follow a structured format. Below are key schemas for diagnosing issues.

### **1. gRPC Status Codes**
| **Code** | **Name**               | **Description**                                                                 |
|----------|------------------------|-------------------------------------------------------------------------------|
| `OK`     | `OK`                   | Request completed successfully.                                               |
| `CANCELLED` | `CANCELLED`        | Request was cancelled (e.g., client closed connection).                       |
| `UNKNOWN` | `UNKNOWN`            | Server encountered an unknown error.                                         |
| `INVALID_ARGUMENT` | `INVALID_ARGUMENT` | Invalid client-side input (e.g., malformed protobuf).                        |
| `DEADLINE_EXCEEDED` | `DEADLINE_EXCEEDED` | Request took longer than the specified deadline.                              |
| `NOT_FOUND` | `NOT_FOUND`           | Resource not found (e.g., service unavailable or endpoint not registered).    |
| `ALREADY_EXISTS` | `ALREADY_EXISTS` | Operation attempted on an existing resource (e.g., duplicate ID).          |
| `PERMISSION_DENIED` | `PERMISSION_DENIED` | Client lacks permissions.                                                     |
| `RESOURCE_EXHAUSTED` | `RESOURCE_EXHAUSTED` | Server out of resources (e.g., quotas exceeded).                             |
| `FAILED_PRECONDITION` | `FAILED_PRECONDITION` | Precondition failed (e.g., `if-match` header mismatch).                     |
| `ABORTED`           | `ABORTED`             | Request aborted (e.g., conflicting operation).                               |
| `OUT_OF_RANGE`      | `OUT_OF_RANGE`        | Request out of valid range (e.g., pagination index).                        |
| `UNAUTHENTICATED`   | `UNAUTHENTICATED`     | Client not authenticated.                                                    |
| `UNAVAILABLE`       | `UNAVAILABLE`         | Service unavailable (e.g., server down).                                     |
| `DATA_LOSS`         | `DATA_LOSS`           | Data loss (e.g., during streaming).                                          |

---

### **2. gRPC Error Metadata**
Errors often include additional metadata in the `grpc-status-details` header:
| **Key**                     | **Value Type**       | **Description**                                                                 |
|-----------------------------|----------------------|-------------------------------------------------------------------------------|
| `grpc-status-details-bin`   | Bytes                | Protocol buffers-encoded error details (e.g., `InvalidArgument`, `QuotaExceeded`). |
| `grpc-message`              | String               | Human-readable error message.                                                 |
| `trace-id`                  | String               | Tracing ID for debugging.                                                      |
| `request-id`                | String               | Unique request identifier.                                                    |

---

## **Troubleshooting Workflow**

### **Step 1: Verify Network Connectivity**
- **Check DNS Resolution**:
  ```bash
  nslookup <service-domain>  # Replace with your gRPC service domain
  ```
- **Test TCP Connectivity**:
  ```bash
  telnet <host> <port>  # Default gRPC port: 50051
  ```
- **Use `grpcurl` for Basic Testing**:
  ```bash
  grpcurl -plaintext <host>:<port> list <service>  # List available services
  grpcurl -plaintext <host>:<port> describe <service>/<method>  # Inspect RPC
  ```

---

### **Step 2: Inspect Client-Server Logs**
#### **Server-Side Logs**
- Enable **debug-level logging** in the gRPC server:
  ```go
  import "google.golang.org/grpc/logverbosity"

  func main() {
      logverbosity.SetLogVerbosity(logverbosity.VerbosityDetailed)
  }
  ```
- Key log entries to search for:
  - `GRPC_*` messages (e.g., `GRPC-begin-unary-call`).
  - Error stacks for `UNKNOWN` or `INVALID_ARGUMENT` codes.

#### **Client-Side Logs**
- Add **interceptors** to log RPC details:
  ```python
  # Python (grpcio) example
  def logging_unary_unary(client_interceptor):
      def intercept(unary_unary, request, context):
          print(f"Request sent: {request}")
          response = unary_unary(request, context)
          print(f"Response received: {response}")
          return response
      return client_interceptor(unary_unary)
  ```

---

### **Step 3: Diagnose Performance Issues**
| **Issue**               | **Tool**               | **Command/Flag**                          | **Action Items**                                                                 |
|-------------------------|------------------------|------------------------------------------|-------------------------------------------------------------------------------|
| **Latency**             | `grpc-health-probe`    | `--connect-timeout=10s`                  | Optimize serialization (e.g., protobuf schema), reduce payload size.          |
| **Backpressure**        | `netdata` / `Prometheus` | Monitor `grpc_server_handled_total`      | Adjust streaming window size or use client-side backpressure.                  |
| **Connection Leaks**    | `lsof` / `ss`          | `ss -tulnp | grep <port>`                            | Close idle connections, enforce timeouts.                                      |
| **Serialization Overhead** | `protobuf` validator | Validate schema with `protoc --validate` | Simplify protobuf messages; avoid nested structures.                          |

---

### **Step 4: Advanced Debugging**
#### **Enable gRPC Tracing**
- Use **OpenTelemetry** or **Jaeger** for distributed tracing:
  ```bash
  # Install Jaeger dependencies
  docker-compose -f jaeger-all-in-one.yaml up
  ```
- Configure the client/server to inject tracing headers:
  ```go
  // Go example
  ctx := otel.GetContext(ctx)
  md := metadata.New(map[string]string{"traceparent": "00-..."})
  _, err := stub.SomeRPC(ctx, &pb.Request{}, grpc.Header(&md))
  ```

#### **Replay Debugging with `grpc_cli`**
- Capture and replay gRPC calls:
  ```bash
  grpc_cli record -p <port> -o trace.bin
  grpc_cli replay < trace.bin
  ```

---

## **Query Examples**

### **1. Basic RPC Testing**
```bash
# List available services
grpcurl -plaintext localhost:50051 list

# Call a unary RPC
grpcurl -plaintext -d '{"key": "value"}' localhost:50051 service.Method

# Stream a request (client stream)
grpcurl -plaintext -d '{"data": "first"}' localhost:50051 service/StreamMethod
echo '{"data": "second"}' | grpcurl -plaintext -d @- localhost:50051 service/StreamMethod
```

---

### **2. Metadata Inspection**
```bash
# Check metadata in error responses
grpcurl -plaintext -v localhost:50051 service.Method 2>&1 | grep "grpc-status-details"
```

---

### **3. Performance Benchmarking**
```bash
# Use `grpc_perf_test` to measure latency
go run $GOPATH/src/google.golang.org/grpc/cmd/grpc_perf_test/main.go \
  -rpc_method=service.Method \
  -rpc_duration=30s \
  -rpc_qps=1000 \
  -grpc_address=localhost:50051
```

---

## **Related Patterns**

1. **[Service Discovery with Consul]**
   - *Use Case*: Dynamically resolve gRPC service endpoints.
   - *Tools*: Consul, etcd.
   - *Reference*: [Consul gRPC Service Discovery](https://www.consul.io/docs/connect/grpc).

2. **[gRPC Load Balancing]**
   - *Use Case*: Distribute client traffic across multiple servers.
   - *Strategies*: Round-robin, least connections, random.
   - *Tools*: Envoy, Nginx.

3. **[Protocol Buffers Optimization]**
   - *Use Case*: Reduce payload size and improve serialization speed.
   - *Techniques*: Use `google.protobuf.Duration`/`.Timestamp` for built-in types, avoid optional fields.
   - *Reference*: [Protobuf Best Practices](https://developers.google.com/protocol-buffers/docs/best-practices).

4. **[gRPC with Auth (OAuth2/JWT)]**
   - *Use Case*: Secure gRPC services with JWT or OAuth2.
   - *Implementation*: Use `credentials.GetClientTLS()` with a custom auth interceptor.
   - *Reference*: [gRPC Auth Guide](https://grpc.io/docs/languages/go/grpc-auth/).

5. **[gRPC Retry Policies]**
   - *Use Case*: Handle transient failures gracefully.
   - *Tools*: `grpc-retry`, custom exponential backoff logic.
   - *Example*:
     ```go
     conn, err := grpc.Dial(
         target,
         grpc.WithUnaryInterceptor(retry.UnaryClientInterceptor()),
         grpc.WithConnectParams(grpc.ConnectParams{Backoff: time.Second}),
     )
     ```

---
## **Final Notes**
- **Start small**: Isolate issues to client, network, or server before diving deep.
- **Leverage tools**: `grpcurl`, `jaeger`, and service mesh observability (e.g., Istio).
- **Document schemas**: Validate protobuf schemas early to catch `INVALID_ARGUMENT` errors.
- **Monitor metrics**: Track `grpc_server_handled_total`, `grpc_client_call_duration`, and `grpc_client_call_error_count`.