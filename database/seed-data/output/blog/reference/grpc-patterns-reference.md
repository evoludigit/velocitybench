---
**[Pattern] - gRPC Patterns Reference Guide**
*Best practices, schemas, and examples for designing scalable, resilient gRPC services*

---

### **1. Overview**
gRPC (Remote Procedure Calls) is a modern, high-performance RPC framework for building microservices. This guide documents **recommended patterns** for designing efficient, maintainable, and production-ready gRPC APIs. Covered topics include **API design principles**, **error handling**, **streaming**, **load balancing**, and **interoperability** with common frameworks (e.g., Protobuf, OpenTelemetry).

Key benefits of adopting these patterns:
- **Performance**: Leverage HTTP/2, binary encoding, and bidirectional streaming.
- **Scalability**: Modular service decomposition with clear contracts.
- **Resilience**: Built-in retries, timeouts, and circuit breakers.
- **Observability**: Standardized logging and tracing (OpenTelemetry-compatible).

---

### **2. Implementation Details**

#### **Core Principles**
| Principle               | Description                                                                 |
|-------------------------|-----------------------------------------------------------------------------|
| **Service Decomposition** | Split monolithic services into domain-specific gRPC services (e.g., `auth`, `order`). |
| **Binary Contracts**     | Use **Protocol Buffers** (`.proto` files) for type-safe, language-agnostic definitions. |
| **Statelessness**       | Avoid request-scoped state; use external stores (Redis, DB) for persistence. |
| **Streaming Over HTTP/2** | Support **unary**, **server-side**, **client-side**, and **bidirectional** streaming. |
| **Idempotency**         | Ensure retry-safe operations (e.g., `PUT` with idempotency keys).          |

---

### **3. Schema Reference**

#### **Basic gRPC Service Definition**
```protobuf
// File: examples/services/order_service.proto
syntax = "proto3";

package order;

service OrderService {
    // Unary RPC
    rpc CreateOrder (CreateOrderRequest) returns (OrderResponse);

    // Server-side streaming
    rpc GetOrderHistory (GetHistoryRequest) returns (stream OrderHistory);

    // Client-side streaming
    rpc BatchUpdate (stream UpdateOrderRequest) returns (BatchResponse);

    // Bidirectional streaming
    rpc LiveUpdates (stream OrderUpdateRequest) returns (stream OrderUpdateResponse);
}

// Structs
message OrderResponse {
    string order_id = 1;
    bool success = 2;
}

message OrderHistory {
    string order_id = 1;
    enum Status { UNPROCESSED = 0; COMPLETED = 1; FAILED = 2 }
    Status status = 2;
}
```

#### **Common Message Fields**
| Field                | Type               | Purpose                                                                 |
|----------------------|--------------------|-------------------------------------------------------------------------|
| `id`                 | `string`           | Unique identifier for entities (UUID, UUIDv4 recommended).              |
| `timestamp`          | `google.protobuf.Timestamp` | ISO 8601-compatible timestamps for auditing.                          |
| `metadata`           | `map<string, string>` | Key-value pairs for tracing/logging (e.g., `trace_id: "xyz"`).          |
| `error_details`      | `ErrorDetails`     | Structured error responses (see [Error Handling](#error-handling)).    |

---

### **4. Query Examples**

#### **A. Unary RPC (Create Order)**
**Request (`CreateOrderRequest`):**
```json
{
  "metadata": { "trace_id": "123-abc" },
  "items": [
    { "product_id": "prod-1", "quantity": 2 }
  ]
}
```
**Response (Success):**
```json
{
  "order_id": "ord-456",
  "success": true,
  "timestamp": "2023-10-15T14:30:00Z"
}
```

#### **B. Server-Side Streaming (Order History)**
**Request (`GetHistoryRequest`):**
```json
{
  "order_id": "ord-456",
  "limit": 10
}
```
**Response (Streamed):**
```json
// First streamed item:
{
  "order_id": "ord-456",
  "status": "UNPROCESSED",
  "timestamp": "2023-10-15T14:30:01Z"
}
// Subsequent items (if any):
{
  "order_id": "ord-456",
  "status": "COMPLETED",
  "timestamp": "2023-10-15T14:35:00Z"
}
```

#### **C. Client-Side Streaming (Batch Update)**
**Client sends multiple updates:**
```json
// Update 1:
{ "order_id": "ord-456", "action": "SHIP" }

// Update 2:
{ "order_id": "ord-456", "action": "PAYMENT_CONFIRMED" }
```
**Server Response:**
```json
{
  "success": true,
  "processed_count": 2
}
```

#### **D. Bidirectional Streaming (Live Updates)**
**Client sends `OrderUpdateRequest`:**
```json
{ "track_order": "ord-456" }
```
**Server streams updates:**
```json
// Update 1:
{ "status": "SHIPPED", "eta": "2023-10-16T10:00:00Z" }

// Update 2:
{ "status": "DELIVERED" }
```

---

### **5. Error Handling**
Use **gRPC status codes** and **structured errors** for clarity.

| Status Code | Description                          | Example Usage                     |
|-------------|--------------------------------------|------------------------------------|
| `INVALID_ARGUMENT` | Invalid client input.                | `error_details.message`: "Invalid quantity." |
| `UNAUTHENTICATED`  | Missing/auth tokens.                 | Redirect to auth flow.             |
| `RESOURCE_EXHAUSTED`| Rate limiting.                       | `quota_exceeded: true`.           |
| `DEADLINE_EXCEEDED`| Timeout (server/client).              | Retry with longer timeout.        |

**Example Error Response:**
```json
{
  "success": false,
  "error_details": {
    "code": "INVALID_ARGUMENT",
    "message": "Product not found: prod-123",
    "details": ["Check product ID."]
  }
}
```

---

### **6. Advanced Patterns**

#### **A. Retry & Timeout**
- **Client-side retries**: Configure with exponential backoff (e.g., using `grpc-retries`).
  ```yaml
  # grpc-retries.config
  retry_policy:
    max_attempts: 3
    initial_backoff: 100ms
    max_backoff: 5s
  ```
- **Server-side timeouts**: Enforce per-RPC limits in service implementations.
  ```protobuf
  rpc GetOrder (GetOrderRequest) returns (OrderResponse)
      option (google.api.http) = {
        get: "/v1/orders/{order_id}"
        timeout: "10s"  // Enforced by Envoy/NGINX
      };
  ```

#### **B. Load Balancing**
| Strategy          | When to Use                          | Configuration                          |
|-------------------|--------------------------------------|----------------------------------------|
| **Round Robin**   | Default for stateless services.      | `grpc.loadBalancingPolicy.name: "round_robin"` |
| **Least Connections** | Dynamic workloads.               | `grpc.loadBalancingPolicy.name: "least_conn"` |
| **Health-Checked PickFirst** | Failover to healthy nodes. | Enable gRPC health checks.            |

#### **C. Observability**
- **Metrics**: Export gRPC metrics to Prometheus via `grpc-stats`.
  ```protobuf
  // metrics.proto
  message GrpcMetrics {
    string rpc_name = 1;
    int64 total_calls = 2;
    double avg_latency_ms = 3;
  }
  ```
- **Tracing**: Inject OpenTelemetry spans into RPC calls.
  ```python
  # Python (grpc-opentelemetry)
  from opentelemetry import trace
  tracer = trace.get_tracer(__name__)
  with tracer.start_as_current_span("GetOrder"):
      order = stub.GetOrder(request)
  ```

---

### **7. Related Patterns**
| Pattern               | Description                                                                 | Reference Link                          |
|-----------------------|-----------------------------------------------------------------------------|------------------------------------------|
| **Protocol Buffers**  | Schema definition language for gRPC contracts.                             | [Protobuf Docs](https://developers.google.com/protocol-buffers) |
| **Service Mesh**      | Manage gRPC traffic with Envoy/Linkerd.                                    | [gRPC Service Mesh Guide](https://grpc.io/docs/service_mesh/) |
| **Idempotency Keys**  | Ensure retry safety with unique request IDs.                               | [Idempotency Pattern](https://microservices.io/patterns/data/idempotency.html) |
| **GraphQL + gRPC**    | Hybrid APIs (e.g., Apollo Federation + gRPC subscriptions).               | [gRPC + GraphQL](https://www.apollographql.com/docs/apollo-server/data/remote-service/) |

---
**Next Steps**:
- [ ] Define your `.proto` schema with `option (google.api.http) = {...}` for REST compatibility.
- [ ] Integrate with `grpc-gateway` for REST proxying.
- [ ] Benchmark with `wrk` or `locust` to validate performance.