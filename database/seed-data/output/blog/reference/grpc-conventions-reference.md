# **[Pattern] gRPC Conventions Reference Guide**

---

## **Overview**
The **gRPC Conventions** pattern defines standardized protocols, message schemas, and metadata structures for building scalable, interoperable APIs using **gRPC**. This guide covers key conventions for service definitions, error handling, authentication, and metadata, ensuring consistency across microservices, APIs, and event-driven architectures.

gRPC’s structured binary format and HTTP/2 support make it ideal for high-performance systems, but adopting clear conventions prevents ambiguity in payloads, service contracts, and error responses. This document provides implementation details, schema templates, and best practices for designing gRPC services that align with industry standards while maintaining extensibility.

---

## **Key Concepts & Implementation Details**

### **1. Service Definition Best Practices**
- **Service Naming**: Use lowercase, kebab-case (`order_service` instead of `OrderService`).
- **Method Naming**: Use `get`, `list`, `create`, `update`, `delete` + entity name (`GetOrder`, `CreateUser`).
- **Unary vs. Streaming**: Prefer unary for single requests/response, streaming for real-time data (e.g., logs, chat).
- **Empty Messages**: Use `google.protobuf.Empty` for requests without fields.

**Example Service Definition**:
```protobuf
service OrderService {
  rpc GetOrder (GetOrderRequest) returns (OrderResponse);
  rpc ListOrders (ListOrdersRequest) returns (stream OrderResponse);
  rpc CreateOrder (CreateOrderRequest) returns (OrderResponse);
}
```

### **2. Request/Response Schema Conventions**
- **Request Schema**: Include `timestamp`, `correlation_id`, and `page_token` (for pagination).
- **Response Schema**: Include `result` (primary data), `pagination_token`, and `metadata`.
- **Error Handling**: Return `Status` (gRPC standard) with `code` and `message`.

**Response Template**:
```protobuf
message OrderResponse {
  Order result = 1;
  string pagination_token = 2;
  map<string, string> metadata = 3; // Optional fields
}
```

### **3. Error Handling**
- Use gRPC’s `Status` message (included in `google/rpc/status.proto`).
- Standard HTTP-like codes: `OK`, `INVALID_ARGUMENT`, `NOT_FOUND`, `PERMISSION_DENIED`.

**Example Error Response**:
```protobuf
message ErrorResponse {
  google.rpc.Status status = 1;
  string error_details = 2; // Optional custom details
}
```

### **4. Authentication & Metadata**
- **Metadata**: Use HTTP headers (e.g., `Authorization`, `X-Correlation-ID`) as metadata.
- **Token Propagation**: Pass tokens via `grpc-metadata` (e.g., `authorization: Bearer <token>`).

**Example Metadata**:
```protobuf
metadata {
  key: "authorization"
  value: "Bearer abc123..."
}
```

### **5. Pagination & Filtering**
- **Page Size**: Limit to ≤1,000 items per page (configurable via `max_results`).
- **Cursor-Based Pagination**: Use `next_page_token` instead of `offset/limit`.

**Pagination Fields**:
```protobuf
message ListOrdersRequest {
  int32 max_results = 1;
  string page_token = 2; // Optional
}
```

### **6. Versioning**
- **Schema Versioning**: Append `-vX` to service names (`order_service-v2`).
- **Deprecation**: Mark deprecated methods with `deprecated = true`.

---

## **Schema Reference**

| **Component**               | **Structure**                          | **Fields**                                                                 |
|-----------------------------|----------------------------------------|-----------------------------------------------------------------------------|
| **Base Request**            | `BaseRequest`                          | `timestamp`, `correlation_id`, `client_id`                                  |
| **Base Response**           | `BaseResponse`                         | `result`, `pagination_token`, `metadata`                                   |
| **Error Response**          | `ErrorResponse`                        | `status`, `error_details`                                                   |
| **Pagination**              | `PageRequest`/`PageResponse`           | `max_results`, `page_token`, `total_count`                                |
| **Authentication Metadata** | `AuthMetadata`                         | `token`, `expires_at`                                                       |

**Example Base Request**:
```protobuf
message BaseRequest {
  string correlation_id = 1; // For tracing
  string client_id = 2;      // Optional
}
```

---

## **Query Examples**

### **1. Unary Request**
**Request**:
```json
{
  "correlation_id": " traces-123",
  "order_id": "order-456"
}
```
**Response**:
```json
{
  "result": {
    "id": "order-456",
    "status": "SHIPPED"
  },
  "metadata": {
    "last_updated": "2024-02-20T12:00:00Z"
  }
}
```

### **2. Streaming Response (Logs)**
**Client Call**:
```bash
grpcurl -plaintext localhost:50051 LogService.ListLogs stream
```
**Server Response**:
```json
{
  "message": "Log entry 1",
  "timestamp": "2024-02-20T11:00:00Z"
}
{
  "message": "Log entry 2",
  "timestamp": "2024-02-20T11:05:00Z"
}
```

### **3. Error Response**
**Request**:
```json
{
  "invalid_field": "malformed_data"
}
```
**Response**:
```json
{
  "status": {
    "code": 3, // INVALID_ARGUMENT
    "message": "Invalid request format"
  }
}
```

---

## **Related Patterns**
1. **[Protocol Buffers Schema Design](<link>)** – Extend gRPC conventions with Protobuf best practices.
2. **[gRPC-Gateway](<link>)** – Bridge gRPC services to REST APIs.
3. **[Service Mesh Integration](<link>)** – Use Istio/Linkerd with gRPC for observability.
4. **[Event-Driven gRPC](<link>)** – Design pub/sub patterns with gRPC streaming.

---
**Note**: Append `-vX` to service names for versioning (e.g., `payment_service-v3`). For deprecated methods, set `deprecated = true` in `.proto` files.

---
**Last Updated**: [Insert Date]
**Version**: 1.0