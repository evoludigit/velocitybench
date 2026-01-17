# **[Pattern] gRPC Verification Reference Guide**

---

## **1. Overview**
The **gRPC Verification** pattern ensures secure and reliable communication between client and server in **gRPC-based microservices architectures**. This pattern implements **mutual authentication (mTLS), authorization checks, and integrity validation** to prevent unauthorized access, tampering, and data leaks.

Key benefits include:
✔ **End-to-end encryption** via TLS 1.2/1.3
✔ **Role-based access control (RBAC)** validation
✔ **Request validation** (schema enforcement, rate limiting)
✔ **Audit logging** for compliance

This guide covers **implementation best practices, schema validation, and integration with common gRPC frameworks** (Protobuf, gRPC-Gateway, AuthZ tools).

---

## **2. Key Concepts & Implementation Details**

### **2.1 Core Components**
| Component          | Description                                                                 | Tools/Libraries                          |
|--------------------|-----------------------------------------------------------------------------|-------------------------------------------|
| **TLS/mTLS**       | Encrypts communication; mutual auth verifies both client & server identity. | [Envoy](https://www.envoyproxy.io/), [Istio](https://istio.io/) |
| **JWT/OAuth2**     | Token-based auth with short-lived credentials.                            | [Google Auth Library](https://github.com/google/uuid) |
| **Protobuf Schema** | Defines service contracts & validates payloads.                           | [Protocol Buffers](https://developers.google.com/protocol-buffers) |
| **Policy Enforcement** | Checks permissions (e.g., "Can user X invoke Y service?").               | [OPA Gatekeeper](https://www.openpolicyagent.org/) |
| **Rate Limiting**  | Prevents abuse via request throttling.                                   | [Envoy Rate Limiter](https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/filter/network/http/rate_limit/v3/rate_limit.proto) |

---

### **2.2 gRPC Verification Flow**
1. **Client Prep**:
   - Generate a **TLS certificate** (or use a CA-signed cert).
   - Acquire a **JWT token** (via OAuth2/OIDC).
   - Load credentials into gRPC channel:
     ```go
     conn, err := grpc.Dial(
         "service.example.com:50051",
         grpc.WithTransportCredentials(insecure.NewCredentials()),
         grpc.WithPerRPCCredentials(&AuthToken{Token: jwtToken}),
     )
     ```

2. **Server Validation**:
   - **TLS Handshake**: Verify client cert (if mTLS enabled).
   - **JWT Parsing**: Decode and extract `sub` (subject) or `roles`.
   - **Policy Check**: Use OPA to enforce rules (e.g., `allow { input.request.path == "/admin" && input.user.role == "admin" }`).
   - **Protobuf Validation**: Enforce schema constraints (e.g., `required` fields).

3. **Response**:
   - Return `HTTP 200 OK` (or gRPC `OK` status).
   - Log audit trails (e.g., `user: alice@test.com invoked /v1/data`).

---

### **2.3 Protobuf Schema Example**
```protobuf
syntax = "proto3";

service DataService {
  rpc GetUser (UserRequest) returns (UserResponse);
}

message UserRequest {
  string username = 1;  // Required field
  repeated string roles = 2 [ (gogoproto.nullable) = true ];  // Optional
  google.protobuf.Timestamp created_at = 3;
}

message UserResponse {
  string id = 1;
  string email = 2;
}
```
**Schema Validation**:
- Use **[gogoproto](https://github.com/golang/protobuf/tree/master/protobuf/gogoproto)** or **[Protobuf Schema Validator](https://github.com/uber/protovalidate)**.
- Enforce rules via ** Protobuf annotations**:
  ```protobuf
  message UserRequest {
    string username = 1 [(validate.rules).string.min_size = 3];
  }
  ```

---

## **3. Query Examples**

### **3.1 gRPC Client Request (Python)**
```python
from grpc import ssl_channel_credentials, credentials
import grpc
import data_pb2
import data_pb2_grpc

# Load TLS certs
creds = ssl_channel_credentials(
    root_certificates="ca.crt",
    private_key="client.key",
    certificate_chain="client.crt",
)

# Connect with JWT token
metadata = [("authorization", f"Bearer {jwt_token}")]
channel = grpc.secure_channel(
    "service.example.com:50051",
    creds,
    options=(("grpc.ssl_target_name_override", "service.example.com"),),
)

stub = data_pb2_grpc.DataServiceStub(channel)
response = stub.GetUser(data_pb2.UserRequest(username="alice"), metadata=metadata)
```

### **3.2 Server-Side Validation (Go)**
```go
import (
	"context"
	"log"
	"net/http"

	"github.com/grpc-ecosystem/grpc-gateway/v2/runtime"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

func (s *DataServer) GetUser(ctx context.Context, req *pb.UserRequest) (*pb.UserResponse, error) {
	// 1. Extract JWT from metadata
	token, err := s.auth.GetToken(ctx)
	if err != nil {
		return nil, status.Errorf(codes.Unauthenticated, "invalid token")
	}

	// 2. Validate roles
	claims, err := s.auth.ParseJWT(token)
	if !claims.HasRole("admin") {
		return nil, status.Errorf(codes.PermissionDenied, "forbidden")
	}

	// 3. Protobuf validation (enforced by gRPC)
	if req.Username == "" {
		return nil, status.Errorf(codes.InvalidArgument, "username required")
	}

	// 4. Business logic
	return &pb.UserResponse{Id: "123"}, nil
}
```

---

## **4. Schema Reference Table**
| Field               | Type               | Required | Validation Rules                          | Example                          |
|---------------------|--------------------|----------|-------------------------------------------|----------------------------------|
| `username`          | `string`           | ✅ Yes    | Min length: 3, regex: `[a-z]+`           | `"alice"`                        |
| `roles`             | `repeated string`  | ❌ No     | Max 3 roles, must include `"user"`       | `["user", "admin"]`              |
| `created_at`        | `Timestamp`        | ❌ No     | Must be within last 30 days              | `{"seconds": 1234567890}`        |
| `metadata.map`      | `map<string, string>` | ❌ No | Keys must match enum `["org", "team"]`   | `{"org": "acme"}`                |

**Tools for Schema Validation**:
| Tool                          | Purpose                                      | Link                                  |
|-------------------------------|---------------------------------------------|---------------------------------------|
| [Protobuf Validator](https://github.com/uber/protovalidate) | Field-level rules (regex, min/max length). | [Docs](https://github.com/uber/protovalidate/blob/master/docs/quick_start.md) |
| [gRPC-Gateway](https://github.com/grpc-ecosystem/grpc-gateway) | REST ↔ gRPC conversion with validation.   | [Tutorial](https://grpc.io/docs/guides/rest/overview/) |
| [OPA Gatekeeper](https://www.openpolicyagent.org/) | Policy-as-code for authZ.               | [Policy Examples](https://www.openpolicyagent.org/docs/latest/policy-examples.html) |

---

## **5. Related Patterns**
| Pattern               | Description                                                                 | When to Use                          |
|-----------------------|-----------------------------------------------------------------------------|--------------------------------------|
| **[Service Mesh (Istio/Linkerd)](https://istio.io/latest/docs/concepts/what-is-istio/)** | Decouples authZ from app logic via sidecars. | Multi-service gRPC deployments.      |
| **[OAuth2/OIDC Proxy](https://github.com/ory/fosite)**                       | Delegates auth to third-party providers (e.g., Auth0). | External user authentication.       |
| **[Protobuf Enums for API Versioning](https://developers.google.com/protocol-buffers/docs/proto3#enums)** | Uses enums to enforce API contract evolution. | Backward-compatible gRPC changes.    |
| **[gRPC-Gateway (REST Proxy)](https://grpc.io/docs/guides/rest/)**             | Exposes gRPC services as REST for legacy clients. | Hybrid REST/gRPC architectures.    |
| **[Rate Limiting with Envoy](https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/filter/network/http/rate_limit/v3/rate_limit.proto)** | Protects against DDoS via request quotas. | High-traffic gRPC APIs.             |

---

## **6. Troubleshooting**
| Issue                          | Cause                                   | Solution                                  |
|--------------------------------|-----------------------------------------|-------------------------------------------|
| **`Unauthenticated` error**    | Missing/invalid JWT or mTLS cert.       | Verify `grpc-per-rpc-credentials` and CA. |
| **`PermissionDenied`**         | JWT claims lack required role.          | Update OPA policy or issue a new token.  |
| **`InvalidArgument`**          | Protobuf field violation.               | Check `protoc --validate` or use `protovalidate`. |
| **Slow responses**             | Policy evaluation overhead.             | Cache OPA decisions or use local rules.   |
| **TLS handshake failure**      | Wrong cert/SNI mismatch.                | Use `grpc.ssl_target_name_override`.    |

---

## **7. Best Practices**
1. **Certificate Management**:
   - Use **short-lived certs** (e.g., 90-day expiry) with **automated rotation**.
   - Tools: [Vault](https://www.vaultproject.io/) for secret rotation.

2. **Token Expiry**:
   - Set JWT `exp` to **15–30 minutes** and use refresh tokens.

3. **Protobuf Evolution**:
   - Use **`oneof`** for mutually exclusive fields.
   - Avoid breaking changes: **add deprecated fields** before removing them.

4. **Observability**:
   - Log **audit trails** (user, action, timestamp) in **OpenTelemetry**.
   - Monitor **gRPC metrics** (e.g., `grpc_server_handled_total`).

5. **Security**:
   - **Never hardcode credentials** in client code.
   - Use **gRPC’s `grpc.WithPerRPCCredentials`** for token injection.

---
**See also**:
- [gRPC Security Best Practices](https://grpc.io/docs/guides/security/)
- [Open Policy Agent Documentation](https://www.openpolicyagent.org/docs/latest/)