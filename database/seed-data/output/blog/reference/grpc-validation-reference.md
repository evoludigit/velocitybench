# **[Pattern] gRPC Validation Reference Guide**

---

## **Overview**
The **gRPC Validation** pattern ensures that gRPC requests and responses adhere to predefined rules before processing, preventing malformed data, invalid payloads, or security vulnerabilities. This pattern integrates validation logic into `.proto` schemas, server interceptors, or client-side checks, leveraging gRPC’s built-in features (e.g., Protocol Buffers validation) and third-party tools (e.g., Beam, gRPC-Getaway). Key use cases include:
- **Data integrity**: Reject requests with missing/invalid fields.
- **Security**: Block malicious payloads (e.g., JSON injection).
- **API consistency**: Enforce strict field types/constraints across clients and services.

This guide covers schema design, implementation strategies, and validation tools.

---

## **Key Concepts**
| **Term**               | **Definition**                                                                                                                                                                                                 |
|-------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Schema Validation**   | Uses Protocol Buffers syntax (`required`, `optional`, `repeated`) and custom validation rules (e.g., regex, min/max values) in `.proto` files.                                                        |
| **Interceptors**        | Server-side middleware (e.g., Go’s `UnaryInterceptor`) to validate data before processing. Can include business rules (e.g., "price > 0").                                                          |
| **Client-Side Checks**  | Preemptive validation in gRPC clients (e.g., Python’s `grpcio` or Java’s `grpc-okhttp`) to fail fast before sending requests.                                                                |
| **Tooling**             | Third-party libraries to extend validation (e.g., [Beam](https://github.com/google/beam) for schema evolution, [gRPC-Getaway](https://github.com/grpc-ecosystem/grpc-gateway) for OpenAPI integration). |
| **Validation Modes**    | - **Strict**: Reject on any error.<br>- **Permissive**: Log warnings but process data (use cautiously).                                                                                                   |

---

## **Implementation Details**

### **1. Schema Validation in `.proto` Files**
Define constraints directly in Protocol Buffers:

```protobuf
service UserService {
  rpc CreateUser (CreateUserRequest) returns (UserResponse);
}

message CreateUserRequest {
  string username = 1 [ (gogoproto.nullable) = true ];  // Optional field
  string email = 2 [(validate.rules).string = {
    regex: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"  // Regex validation
  }];
  int32 age = 3 [(validate.rules).int = { min: 18, max: 120 }];  // Range check
}
```
**Supported Rules** (via [`google/protobuf/any.proto`](https://github.com/protocolbuffers/protobuf/blob/main/src/google/protobuf/any.proto)):
- **String**: `regex`, `in`, `len` (min/max length).
- **Int/Float**: `min`, `max`, `in`.
- **Message**: Nested object validation (e.g., `address.city = "strict"`).

**Note**: Enable validation with compiler flags:
```sh
protoc --plugin=protoc-gen-validate=./validate --validate_out=lang=go:. user.proto
```

---

### **2. Server-Side Interceptors**
Add runtime validation before processing. Example in **Go**:
```go
func UnaryValidationInterceptor(ctx context.Context, req interface{}, info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (interface{}, error) {
    // Example: Check user ID format
    if userID := info.FullMethod; !regexp.MustCompile(`/^users\/[0-9]+$`).MatchString(userID) {
        return nil, status.Error(codes.InvalidArgument, "invalid user ID format")
    }
    return handler(ctx, req)
}

// Register interceptor
grpcServer.UnaryInterceptor(UnaryValidationInterceptor)
```

**Languages**:
- **Java**: Use [`io.grpc.ServerInterceptors`](https://grpc.github.io/grpc-java/javadoc/io/grpc/ServerInterceptors.html).
- **Python**: [`grpcio`'s `UnaryStreamInterceptor`](https://grpc.io/grpc/python/docs/interceptors.html).

---

### **3. Client-Side Validation**
Validate requests before sending. Example in **Python**:
```python
from grpc import StatusCode
from grpc_validation import validate_request

def validate_order(request: OrderRequest) -> None:
    try:
        validate_request(
            request,
            rules={
                "items": {"type": "array", "minItems": 1},
                "total": {"type": "number", "min": 0}
            }
        )
    except ValidationError as e:
        raise StatusCode.INVALID_ARGUMENT("Invalid order: " + str(e))

# Call RPC
with grpc.insecure_channel("localhost:50051") as channel:
    stub = OrderServiceStub(channel)
    stub.CreateOrder(validate_order(OrderRequest(...)))
```

---

### **4. Tooling & Extensions**
| **Tool**               | **Purpose**                                                                 | **Setup**                                                                 |
|-------------------------|-----------------------------------------------------------------------------|---------------------------------------------------------------------------|
| **[Beam](https://github.com/google/beam)** | Schema evolution and validation for gRPC services.                       | Add to `protoc` command: `--plugin=protoc-gen-beam=./beam --beam_out=...` |
| **[gRPC-Gateway](https://github.com/grpc-ecosystem/grpc-gateway)** | HTTP ↔ gRPC validation (e.g., Swagger/OpenAPI rules).                | Configure in `gateway.proto` with `google.api.http`.                    |
| **[Validator](https://github.com/grpc-ecosystem/grpc-validator)** | Runtime field validation in JSON payloads (for REST-gRPC hybrids). | Install via `go get github.com/grpc-ecosystem/grpc-validator`.           |

---

## **Schema Reference**
| **Field Type**       | **Constraint**               | **Example Rule**                          | **Protobuf Syntax**                          |
|----------------------|-------------------------------|--------------------------------------------|----------------------------------------------|
| `string`             | Regex                        | Email format                              | `regex: "^.+@.+\\..+$"`                     |
| `int32/int64`        | Range                        | Age between 18–120                         | `min: 18, max: 120`                         |
| `float`              | Precision                    | 2 decimal places                          | `precision: 2`                              |
| `message`            | Nested validation            | Sub-message `address.city` must be non-empty | `strict: true`                              |
| `enum`               | Allowed values               | Status in `["ACTIVE", "INACTIVE"]`         | `in: ["ACTIVE", "INACTIVE"]`                |
| `repeated`           | Min/max items                | At least 1 item in `items` array          | `minItems: 1, maxItems: 10`                 |

**Full Rules Reference**:
- [Protobuf Validation Rules](https://github.com/google/protobuf/blob/main/src/google/protobuf/descriptor.proto#L2000).

---

## **Query Examples**

### **1. Valid Request**
**Request**:
```protobuf
CreateUserRequest {
  username: "alice123",
  email: "alice@example.com",
  age: 25
}
```
**Response**: `UserResponse{ user_id: "123" }` (success).

---

### **2. Invalid Request (Regex Fail)**
**Request**:
```protobuf
CreateUserRequest {
  email: "invalid-email"  # Missing "@" symbol
}
```
**Response**:
```json
{ "error": "InvalidArgument: email does not match regex" }
```

---

### **3. Server Interceptor Example (Go)**
**Scenario**: Block invalid user IDs (e.g., `/users/abc`).
```go
// Interceptor logic
if !validID := regexp.MustCompile(`^[0-9]+$`).MatchString(req.UserID); !validID {
    return nil, status.Error(codes.InvalidArgument, "UserID must be numeric")
}
```

---

### **4. Client-Side Validation (Python)**
**Scenario**: Enforce `total > 0` in `OrderRequest`.
```python
try:
    validate_request(
        order,
        rules={
            "total": {"type": "number", "min": 0.01}
        }
    )
except ValidationError:
    print("Order total must be > 0")
```

---

## **Error Handling Patterns**
| **Error Type**         | **Status Code** | **Example**                                  | **Handling**                                  |
|------------------------|------------------|----------------------------------------------|-----------------------------------------------|
| **Invalid Argument**   | `INVALID_ARGUMENT` | Missing required field.                     | Return detailed error (e.g., `json: {"field": "username is required"}`). |
| **Range Exceeded**     | `OUT_OF_RANGE`   | Age < 18.                                    | Use `grpc.Status` with `codes.OutOfRange`.    |
| **Permission Denied**  | `PERMISSION_DENIED` | Unauthorized API key.                       | Log attempt + re-authenticate.                |
| **Schema Evolution**   | `UNAVAILABLE`    | Field removed in new service version.        | Graceful degradation (e.g., ignore optional fields). |

---

## **Performance Considerations**
1. **Client Validation**: Run checks *before* invoking RPC to avoid network round-trips.
2. **Server Validation**: Use interceptors for lightweight checks (e.g., regex). For complex rules (e.g., cross-field logic), delegate to business logic.
3. **Caching**: Cache validation results for repeated requests (e.g., rate-limiting).
4. **Tooling Overhead**: Beam/gRPC-Gateway add compile-time complexity; benchmark if critical.

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                                  |
|---------------------------|---------------------------------------------------------------------------------|--------------------------------------------------|
| **[gRPC Health Checks](https://github.com/grpc-ecosystem/grpc-health-proto)** | Check if a service is ready/serving.                                            | Pre-deployment or load balancer health probes.   |
| **[gRPC Transcoding](https://grpc.io/blog/gprc-transcoding/)**                    | Convert between gRPC and REST/JSON.                                               | Exposing legacy APIs via gRPC-Gateway.            |
| **[gRPC Retries](https://grpc.io/docs/guides/error-retries/)**                     | Exponential backoff for transient failures.                                      | Handling network partitions.                     |
| **[Schema Evolution](https://developers.google.com/protocol-buffers/docs/proto3#evolution)** | Updating `.proto` files without breaking clients.                          | Gradual API changes (e.g., adding optional fields). |
| **[gRPC Web](https://github.com/grpc/grpc-web)**                                 | gRPC over HTTP for web clients.                                                    | Frontend integrations.                           |

---

## **Troubleshooting**
| **Issue**                          | **Root Cause**                                  | **Solution**                                      |
|-------------------------------------|-------------------------------------------------|---------------------------------------------------|
| `INVALID_ARGUMENT` on valid data    | Schema mismatch (e.g., client sends `int32` but server expects `int64`). | Align `.proto` file with all implementations.     |
| Validation fails in production      | Rule too strict (e.g., regex too complex).       | Test with real-world edge cases.                  |
| Performance degradation              | Heavy client-side validation.                   | Offload to server with lightweight interceptors.  |
| Beam errors during schema evolution | Client/server version mismatch.                 | Use `oneof` or `map` for dynamic fields.         |

---

## **Best Practices**
1. **Fail Fast**: Validate on the client *and* server (defense in depth).
2. **Idempotency**: Ensure repeated validations return the same result.
3. **Document Rules**: Clearly specify validation constraints in API docs (e.g., Swagger tags).
4. **Minimal Fields**: Prefer `optional` over `repeated` for required fields.
5. **Avoid Over-Validation**: Balance security with usability (e.g., allow flexible date formats).

---
**See Also**:
- [Protobuf Validation Rules](https://github.com/google/protobuf/blob/main/src/google/protobuf/descriptor.proto)
- [gRPC Interceptors](https://grpc.io/docs/languages/go/advanced/interceptors/)
- [Beam Schema Evolution](https://github.com/google/beam)