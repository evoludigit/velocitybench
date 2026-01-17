# **[Pattern] gRPC Approaches Reference Guide**

---

## **Overview**
This guide provides a structured reference for implementing **gRPC Approaches**, a communication pattern leveraging **Google’s gRPC** (Remote Procedure Call) framework. gRPC enables high-performance, language-neutral RPC over HTTP/2, ideal for microservices, serverless architectures, and real-time applications. This pattern covers **key concepts**, **implementation strategies**, and **best practices** for designing efficient gRPC-based systems, including service definition, authentication, streaming, and error handling.

---

## **Key Concepts**
### **1. Core Principles**
- **Binary Protocol**: Uses Protocol Buffers (protobuf) for serialization (smaller payloads, faster parsing).
- **HTTP/2 Multiplexing**: Supports concurrent bidirectional streaming, reducing latency.
- **Strong Typing**: Compile-time checks via `.proto` definitions.
- **Interceptors**: Middleware for logging, auth, or performance metrics.

### **2. Common Approaches**
| Approach               | Use Case                                  | Trade-offs                          |
|------------------------|-------------------------------------------|-------------------------------------|
| **Unary RPC**          | Synchronous single request-response.      | Simplest but not scalable for high throughput. |
| **Client Streaming**   | Client sends multiple requests sequentially. | Server processes one request at a time. |
| **Server Streaming**   | Server sends multiple responses sequentially. | Client buffers output (e.g., logs, live updates). |
| **Bidirectional**      | Full-duplex (client + server stream).    | Higher complexity; requires backpressure handling. |

---

## **Schema Reference**
### **1. Protobuf Syntax Basics**
Define services and messages in `.proto` files:

```protobuf
// Example: UserService.proto
syntax = "proto3";

service UserService {
  rpc GetUser (GetUserRequest) returns (UserResponse);
}

message GetUserRequest {
  string id = 1;
}

message UserResponse {
  string name = 1;
  int32 age = 2;
}
```

#### **Key Fields**
| Field           | Description                                      |
|-----------------|--------------------------------------------------|
| `service`       | Defines RPC endpoints.                           |
| `rpc`           | Declares a remote procedure call (e.g., `GetUser`). |
| `message`       | Request/response payload schema.                 |
| `repeated`      | Array fields in protobuf.                        |

---

## **Query Examples**
### **1. Unary RPC (Request-Response)**
```go
// Client call
resp, err := client.GetUser(ctx, &pb.GetUserRequest{Id: "123"})

// Server implementation
func (s *UserService) GetUser(ctx context.Context, req *pb.GetUserRequest) (*pb.UserResponse, error) {
  user := fetchUser(req.Id)
  return &pb.UserResponse{Name: user.Name, Age: user.Age}, nil
}
```

### **2. Server Streaming (Client Receives Multiple Responses)**
```protobuf
service ChatService {
  rpc StreamMessages (ChatRequest) returns (stream ChatResponse);
}
```
**Client**:
```go
stream, err := client.StreamMessages(ctx, &pb.ChatRequest{Channel: "general"})
for {
  resp, err := stream.Recv()
  if err == io.EOF { break }
  fmt.Println(resp.Message)
}
```

### **3. Bidirectional Streaming (Full-Duplex)**
```protobuf
service LiveChat {
  rpc Chat (stream Message) returns (stream Message);
}
```
**Client**:
```go
stream, err := client.Chat(ctx)
go func() {
  for msg := range messages {
    stream.Send(&pb.Message{Text: msg})
  }
}()
for {
  resp, err := stream.Recv()
  if err == io.EOF { break }
  fmt.Println(resp.Text)
}
```

---

## **Implementation Details**
### **1. Setting Up gRPC**
- **Install Tools**:
  ```sh
  # Protobuf compiler
  brew install protoc
  # gRPC plugins
  brew install protoc-gen-go-grpc protoc-gen-go
  ```
- **Generate Code**:
  ```sh
  protoc --go_out=. --go-grpc_out=. UserService.proto
  ```

### **2. Authentication**
- **JWT Validation**:
  ```go
  // Interceptor example
  func jwtInterceptor(ctx context.Context, req interface{}, info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (interface{}, error) {
    token := extractToken(ctx)
    if !validateToken(token) {
      return nil, status.Errorf(codes.Unauthenticated, "invalid token")
    }
    return handler(ctx, req)
  }
  ```
- **Configure Interceptors**:
  ```go
  grpcServer := grpc.NewServer(grpc.UnaryInterceptor(jwtInterceptor))
  ```

### **3. Error Handling**
- **gRPC Status Codes**:
  ```go
  return nil, status.Errorf(codes.NotFound, "user not found")
  ```
- **Custom Errors**:
  ```protobuf
  enum ErrorType {
    NOT_FOUND = 0;
    INVALID_INPUT = 1;
  }

  message ErrorResponse {
    ErrorType type = 1;
    string details = 2;
  }
  ```

### **4. Performance Optimizations**
- **Connection Pooling**: Reuse gRPC connections for clients.
- **Compression**: Enable `grpc.TransportParams{Compression: codec.Name("gzip")}`.
- **Backpressure**: Handle streaming with `context.WithTimeout` and `Select`.

---

## **Query Examples (Advanced)**
### **1. Retry with Exponential Backoff**
```go
import "github.com/grpc-ecosystem/go-grpc-middleware/retry"

retryPolicy := retry.DefaultCallPolicy()
retryPolicy.MaxAttempts = 3
retryPolicy.Backoff.Multiplier = 1.2

client := grpc.NewClient(
  conn, grpc.WithUnaryInterceptor(middleware.RetryInterceptor(retryPolicy)),
)
```

### **2. Load Balancing**
- **Client-Side LB**: Use `grpc.Connect()` with `grpc.WithBalancerName("round_robin")`.
- **gRPC-Gateway**: For REST ↔ gRPC translation.

---

## **Related Patterns**
1. **[REST ↔ gRPC Gateway Conversion](https://grpc.io/blog/protocol-buffers-rest-rest-gateway/)**
   - Translate REST endpoints to gRPC using Envoy or gRPC-Gateway.
2. **[Service Mesh Integration](https://istio.io/latest/docs/tasks/traffic-management/grpc-tls/)**
   - Secure and observe gRPC traffic with Istio.
3. **[Event-Driven Architectures](https://cloud.google.com/blog/products/devops-sre/designing-serverless-applications-with-grpc)**
   - Combine gRPC with Pub/Sub for async workflows.
4. **[Canary Deployments](https://kubernetes.io/docs/tutorials/scaling-pod-autoscaling/)**
   - Gradually roll out gRPC changes using Kubernetes.

---

## **Best Practices**
| Practice               | Implementation                                                                 |
|------------------------|---------------------------------------------------------------------------------|
| **Keep Definitions Stable** | Avoid breaking changes in `.proto` files.                                     |
| **Use Protoc Buffers**  | Prefer protobuf over JSON for performance and validation.                        |
| **Leverage Interceptors** | Centralize auth/logging/retries without clogging business logic.                |
| **Monitor gRPC Metrics** | Track latency, error rates, and throughput with Prometheus/OpenTelemetry.     |
| **Document Breaking Changes** | Use semantic versioning for `.proto` files.                                  |

---
**See also**: [gRPC Best Practices Guide](https://grpc.io/docs/guides/) | [Protocol Buffers Docs](https://developers.google.com/protocol-buffers)