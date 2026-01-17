# **[Pattern] gRPC Guidelines Reference Guide**

---

## **Overview**
This reference guide outlines best practices for designing, implementing, and deploying **gRPC** services following **Google’s gRPC Guidelines** and industry standards. gRPC (Remote Procedure Call) is a high-performance, language-neutral RPC framework for modern applications, leveraging **HTTP/2** for efficient communication. This document covers **service definition (protobuf)**, error handling, performance tuning, security, and interoperability best practices while ensuring maintainability and scalability.

Key principles include:
✔ **Protobuf-based Service Definition** – Structured, extensible, and versioned contracts.
✔ **Performance Optimization** – Minimal latency, efficient serialization, and unbiased load distribution.
✔ **Security & Authentication** – TLS, Service-to-Service Auth, and Mutual TLS (mTLS).
✔ **Observability** – Logging, metrics, and tracing for debugging and monitoring.
✔ **Error Handling** – Clear, versioned error schemas and retries with backoff.

---
## **Implementation Details**

### **1. Service Definition (Protobuf)**
Define services using **Protocol Buffers (protobuf)**, a binary format for structured data.
Structure follows **gRPC Best Practices**:

| **Category**               | **Guideline**                                                                 | **Example**                                                                 |
|----------------------------|-------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **Naming Conventions**      | Use **snake_case** for methods, **PascalCase** for services.                  | `GetUser` (not `get_user`), `UserService` (not `user_service`)             |
| **Service Scope**          | Group related RPCs under a logical service (e.g., `authservice.proto`).      | `Service AuthService { ... }`                                                 |
| **Method Types**           | Prefer **Unary RPCs** for simple requests/responses; use **Streaming** only when necessary. | `rpc GetUser (UserRequest) returns (UserResponse);` |
| **Request/Response**       | Keep payloads **small** (<1MB) and **serializable**. Use nested messages for related fields. | ```protobuf message UserRequest { string user_id = 1; bool include_extra = 2; } ``` |
| **Error Handling**         | Define custom errors with `syntax = "proto3"` and reserve `1` for gRPC status. | ```protobuf enum Status { ERROR_NOT_FOUND = 2; } message ErrorResponse { Status status = 1; string message = 2; } ``` |
| **Versioning**             | Use **package versions** (e.g., `v1`) or **field tags** (e.g., `bool is_v1 = 1000`). | ```protobuf message User { string id = 1; string name = 2 [(gprc.google.com/protobuf.version) = "v1"]; } ``` |
| **Optional Fields**        | Avoid `optional`—use `bool has_xxx` + `string xxx` instead.                    | ```protobuf message User { bool has_avatar = 1; string avatar_url = 2; } ``` |

---

### **2. Error Handling**
gRPC uses **HTTP/2 error codes** (status codes) for responses.

| **Error Code**          | **Use Case**                          | **Protobuf Example**                          |
|-------------------------|---------------------------------------|-----------------------------------------------|
| `INTERNAL` (1)          | Server-side failures.                 | `status: INTERNAL`, `message: "DB timeout"`   |
| `UNAVAILABLE` (5)       | Service unavailable (retryable).      | `status: UNAVAILABLE`, `message: "Load balanced"` |
| `DEADLINE_EXCEEDED` (8) | Client timeout.                        | `status: DEADLINE_EXCEEDED`                   |
| `INVALID_ARGUMENT` (3)  | Invalid client input.                 | `status: INVALID_ARGUMENT`                    |
| **Custom Errors**       | Define in `.proto` (see above).       | ```protobuf enum CustomError { USER_NOT_FOUND = 100; } ``` |

**Retry Strategy:**
- Use exponential backoff for **transient errors** (e.g., `UNAVAILABLE`).
- Libraries: **gRPC Retry Policy** (`max_attempts`, `initial_backoff`).

---

### **3. Performance Optimization**
| **Technique**            | **Best Practice**                                                                 | **Implementation**                                                                 |
|--------------------------|-----------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Compression**          | Enable **gzip/deflate** for large payloads.                                       | `grpc_go_options { compression_algorithm = COMPRESS_GZIP; }` (in proto)            |
| **Load Balancing**       | Use **gRPC’s built-in load balancers** (round-robin, least connections).          | Configure in client (`Channel`).                                                   |
| **Connection Reuse**     | Reuse connections (default: **keepalive** enabled).                               | ```go   ctx, cancel := context.WithTimeout(context.Background(), 30s)   conn, err := grpc.Dial("localhost:50051", grpc.WithKeepalive...) ``` |
| **Batching**             | Use **Server Streaming** for async processing (e.g., logs, notifications).       | ```protobuf service EventService { rpc StreamEvents (EventRequest) returns (stream EventResponse); } ``` |
| **Protobuf Optimization**| Avoid deep nesting; use arrays instead of repeated fields.                         | ```protobuf message LogEntry { repeated string tags = 1; } ``` (instead of nested) |

---

### **4. Security**
| **Requirement**          | **Implementation**                                                                 |
|--------------------------|------------------------------------------------------------------------------------|
| **TLS (mTLS)**           | Enforce **mutual TLS** for service-to-service auth.                                | ```yaml   server:   tls:     cert_file: server.crt     key_file: server.key   client:     tls:       ca_certs: ca.crt ``` |
| **Authentication**       | Use **JWT/OAuth2** or **gRPC Metadata** (e.g., `Authorization: Bearer <token>`).   | ```go   ctx := metadata.NewOutgoingContext(ctx, map[string]string{   "authorization": "Bearer " + token, }) ``` |
| **Service Accounts**     | Define **IAM roles** for gRPC services (e.g., `roles/grpc.client`).               | Assign via **Google Cloud IAM** (or other providers).                              |

---

### **5. Observability**
| **Tool**                | **Implementation**                                                                 |
|-------------------------|------------------------------------------------------------------------------------|
| **Logging**             | Log structured JSON (e.g., `grpc_gateway` for HTTP interop).                      | ```go   logger.Info("RPC call", "method", "GetUser", "latency", latency.String()) ``` |
| **Metrics**             | Export **Prometheus metrics** (e.g., `grpc_server_handled_total`).                 | Use `go.uber.org/grpc-prometheus` library.                                          |
| **Tracing**             | Use **OpenTelemetry** for distributed tracing (e.g., Jaeger, Zipkin).              | ```go   otel.SetTracerProvider(tracerprovider.New())   ctx, span := oteltrace.Start(ctx, "GetUser")   defer span.End() ``` |

---

## **Query Examples**

### **1. Unary RPC (Synchronous)**
**Client (Go):**
```go
resp, err := client.GetUser(ctx, &pb.UserRequest{UserId: "123"})
if err != nil {
    log.Fatalf("RPC failed: %v", err)
}
fmt.Println(resp.Name)
```

**Server (Go):**
```go
func (s *server) GetUser(ctx context.Context, req *pb.UserRequest) (*pb.UserResponse, error) {
    user, err := s.store.GetUser(req.UserId)
    if err != nil {
        return nil, status.Errorf(codes.NotFound, "User not found")
    }
    return &pb.UserResponse{Name: user.Name}, nil
}
```

---

### **2. Server Streaming RPC**
**Client (Go):**
```go
stream, err := client.StreamEvents(ctx)
if err != nil {
    log.Fatalf("Failed to stream: %v", err)
}
for {
    event, err := stream.Recv()
    if err == io.EOF {
        break
    }
    if err != nil {
        log.Fatalf("Stream error: %v", err)
    }
    fmt.Println(event.Data)
}
```

**Server (Go):**
```go
func (s *server) StreamEvents(req *pb.EventRequest, stream pb.EventService_StreamEventsServer) error {
    for _, event := range s.generateEvents(req.Filter) {
        if err := stream.Send(&pb.EventResponse{Data: event}); err != nil {
            return err
        }
    }
    return nil
}
```

---

### **3. Client Streaming RPC**
**Client (Go):**
```go
stream, err := client.BatchProcess(ctx)
if err != nil {
    log.Fatalf("Failed to connect: %v", err)
}
for _, data := range inputs {
    if err := stream.Send(&pb.Data{Value: data}); err != nil {
        return err
    }
}
resp, err := stream.CloseAndRecv()
if err != nil {
    log.Fatalf("Processing failed: %v", err)
}
fmt.Println(resp.Result)
```

**Server (Go):**
```go
func (s *server) BatchProcess(stream pb.DataService_BatchProcessServer) error {
    var data []string
    for {
        in, err := stream.Recv()
        if err == io.EOF {
            break
        }
        if err != nil {
            return err
        }
        data = append(data, in.Value)
    }
    result := s.process(data)
    return stream.SendAndClose(&pb.Result{Value: result})
}
```

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                                     | **When to Use**                                                                          |
|---------------------------|-----------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------|
| **gRPC-Gateway**          | Translate gRPC → HTTP REST for legacy clients.                                                     | When integrating with older REST-based systems.                                          |
| **Protobuf Schema Registry** | Versioned schemas for backward compatibility.                                                        | When evolving APIs with breaking changes.                                                |
| **Asynchronous Workflows** | Combine gRPC with **Pub/Sub** or **SQS** for async processing.                                       | For event-driven microservices (e.g., order processing).                                 |
| **gRPC-Web**              | Enable gRPC over HTTP/1.1 for browser-based clients.                                                 | When targeting web/mobile apps.                                                          |
| **Service Mesh (Istio/Linkerd)** | Manage gRPC traffic (retries, circuit breaking) via a proxy layer.                                  | In complex distributed systems with high availability requirements.                     |

---
## **Further Reading**
- [gRPC Guidelines (Official)](https://grpc.io/docs/guides/)
- [Protobuf Language Guide](https://developers.google.com/protocol-buffers/docs/proto)
- [gRPC Best Practices (Google)](https://cloud.google.com/blog/products/application-development/grpc-best-practices)
- [OpenTelemetry for gRPC](https://opentelemetry.io/docs/instrumentation/gprc/)