```markdown
---
title: "GRPC Conventions: Designing Robust, Scalable Microservices with REST-like Patterns in gRPC"
date: 2024-06-15
author: Alex Carter
tags: ["grpc", "api-design", "microservices", "backend-engineering", "patterns"]
description: "Learn how to apply REST-like conventions to gRPC to build maintainable, scalable services. This guide covers naming conventions, error handling, pagination, and more, with practical code examples and anti-patterns to avoid."
---

# GRPC Conventions: Designing REST-like APIs with gRPC

gRPC is often celebrated for its performance advantages over REST—binary protocol, low latency, and support for streaming. But raw speed isn’t enough: **Without conventions, even the fastest APIs become unmaintainable.** I’ve seen teams abandon gRPC because their initial enthusiasm for its speed was overshadowed by fragmented designs that required ad-hoc tools for discovery, error handling, and client libraries.

The solution? **Adopt REST-like conventions in gRPC.** By borrowing and adapting proven API design patterns, you can retain gRPC’s performance while gaining maintainability, tooling support, and developer friendliness. This guide covers conventions for naming, authentication, error handling, and more—backed by real-world examples and anti-patterns to avoid.

---

## The Problem: What Happens When You Lose Conventions?

Imagine a microservice architecture where `OrderService` communicates with `InventoryService` using gRPC, but without shared conventions:

```protobuf
// order.proto
service OrderService {
  rpc CreateOrder (CreateOrderRequest) returns (Order) {}
  rpc UpdateOrder (UpdateOrderRequest) returns (Order) {}
  rpc GetOrder (GetOrderRequest) returns (Order) {}
}

message CreateOrderRequest {
  string user_id = 1;
  map<string, OrderItem> items = 2;

  message OrderItem {
    string product_id = 1;
    int32 quantity = 2;
  }
}
```

```protobuf
// inventory.proto
service InventoryService {
  rpc GetProduct (GetProductRequest) returns (Product) {}
  rpc UpdateStock (UpdateStockRequest) returns (bool) {}
}

message GetProductRequest {
  string id = 1;
  bool include_extras = 2;
}
```

**Problems:**
1. **Lack of Consistency:** `CreateOrderRequest` uses `user_id` while `UpdateOrderRequest` might use `user_uuid`. What about `AnnotateOrderRequest`?
2. **No Versioning:** If you later add a `priority` field to `Order`, how do clients handle it? Will you break 100% of them?
3. **Error Handling Chaos:** Is a `500` from `UpdateStock` a transient error? Will clients retry it? No way to know from the API alone.
4. **Discovery Nightmare:** How do devs know what parameters are required for `GetProductRequest`? No OpenAPI/Swagger-like documentation.
5. **Performance vs. Usability:** Binary format is great, but tools like `grpcurl` or Postman can’t inspect the schema easily.

---

## The Solution: REST-like Conventions for gRPC

gRPC isn’t REST, but it can borrow from REST’s conventions to make it **practical at scale**. Here’s the approach:

| Convention Type      | REST Equivalent          | gRPC Adaptation                                                                 |
|----------------------|--------------------------|--------------------------------------------------------------------------------|
| **Naming**           | RESTful resource naming  | Use resources and verbs (e.g., `GetOrder`, `UpdateOrder` instead of `CallOrder`).|
| **Versioning**       | `/v1/orders`             | Package/Protobuf file (`order/v1/order.proto`).                                |
| **Error Handling**   | HTTP status codes        | gRPC status codes + custom error messages with metadata.                       |
| **Pagination**       | `page`/`limit` query     | Pageable request/response messages with `pagination: Page{}` submessage.        |
| **Authentication**   | JWT in headers           | JWT in HTTP headers or custom metadata (e.g., `x-user-id`).                     |
| **Metadata**         | Headers/Query Params     | gRPC metadata keys + fields in request/response messages.                       |

---

## Components/Solutions: A Convention-Layered Approach

### 1. **Package and Protobuf Naming**
Use semantic versioning in your `.proto` files and package names. This helps with dependency management and rollbacks.

```protobuf
// order/v1/order.proto
package order.v1;
syntax = "proto3";

message Order {
  string id = 1;
  string user_id = 2; // REST-like field naming
  repeated OrderItem items = 3;
  string status = 4;
}

service OrderService {
  rpc GetOrder (GetOrderRequest) returns (Order) {}
  rpc CreateOrder (CreateOrderRequest) returns (Order) {}
  rpc ListOrders (ListOrdersRequest) returns (ListOrdersResponse) {}
}
```

---

### 2. **Consistent Naming for Request/Response**
Inspired by REST, use **resource + verb** for RPC names:

| REST-like RPC Name       | Protobuf RPC Name          | Purpose                                      |
|--------------------------|---------------------------|----------------------------------------------|
| `GET /orders/{id}`       | `GetOrder`                | Fetch a single order.                        |
| `POST /orders`           | `CreateOrder`             | Create a new order.                          |
| `PATCH /orders/{id}`     | `UpdateOrder`             | Update fields of an order.                   |
| `DELETE /orders/{id}`    | `DeleteOrder`             | Disable an order (soft delete).              |
| `GET /orders`            | `ListOrders`              | Paginated list of orders.                    |

**Avoid:**
- `CallOrder` → Doesn’t suggest intent.
- `ProcessOrderRequest` → Too verbose.

---

### 3. **Error Handling: gRPC Status Codes + Custom Errors**
gRPC status codes aren’t enough alone—**combine them with semantic error messages**.

```protobuf
// Write your own error types. Reuse these across microservices where possible.
message InvalidOrderError {
  string error_type = 1; // e.g., "insufficient_stock"
  string message = 2;    // Human-readable
  repeated string details = 3; // Technical notes
}

message OrderAlreadyExistsError {
  string duplicate_order_id = 1;
}

message OrderServiceError {
  oneof error {
    InvalidOrderError invalid_order = 1;
    OrderAlreadyExistsError already_exists = 2;
  }
}

service OrderService {
  rpc CreateOrder (CreateOrderRequest) returns (Order) {
    option (google.api.http) = {
      post: "/v1/orders"
    };
    returns (google.rpc.Status) {} // gRPC status + custom error
  }
}
```

**Code Example (Server-Side):**
```go
package main

import (
	"context"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	pb "path/to/order/v1"
)

func (s *orderServer) CreateOrder(ctx context.Context, req *pb.CreateOrderRequest) (*pb.Order, error) {
    // Check if order already exists
    if exists := s.existsOrder(req.Id); exists {
        err := status.Error(codes.AlreadyExists, "order already exists")
        err.Details = []grpc.StatusDetail{
            &pb.OrderAlreadyExistsError{
                DuplicateOrderId: req.Id,
            },
        }
        return nil, err
    }

    // Process order
    order := s.createOrder(req)
    return order, nil
}
```

**Code Example (Client-Side):**
```go
func (c *OrderClient) placeOrder(ctx context.Context, req *pb.CreateOrderRequest) (*pb.Order, error) {
    resp, err := c.CreateOrder(ctx, req)
    if err != nil {
        status, ok := status.FromError(err)
        if !ok {
            return nil, err
        }

        switch status.Code() {
        case codes.AlreadyExists:
            var existsError pb.OrderAlreadyExistsError
            if status.GetDetails(&existsError) {
                log.Printf("Duplicate order attempt for ID: %s", existsError.DuplicateOrderId)
                return nil, fmt.Errorf("duplicate order: %w", err)
            }
        case codes.InvalidArgument:
            // Log or retry logic here
        default:
            return nil, fmt.Errorf("unexpected error: %w", err)
        }
    }
    return resp, nil
}
```

---

### 4. **Pagination with `Page` Extension**
Use a **pageable response pattern** similar to REST’s `?limit=10&offset=50`.

```protobuf
message Pagination {
  int32 page_size = 1;    // Default to 20 if not set
  int32 page_token = 2;   // Cursor for pagination (e.g., last_id)
  int32 total_count = 3;  // Total number of items
}

message ListOrdersRequest {
  Pagination pagination = 1;
  string filter = 2; // e.g., "status=pending"
}

message ListOrdersResponse {
  repeated Order orders = 1;
  Pagination pagination = 2;
}
```

---

### 5. **Authentication: JWT or Metadata**
gRPC doesn’t have a built-in auth system, so adapt REST’s patterns:

- **Option 1:** Pass JWT in HTTP headers (recommended for gRPC-Gateway).
- **Option 2:** Use custom metadata (e.g., `grpcgateway` supports this).

```protobuf
// Metadata is an optional gRPC feature. Use it for non-sensitive fields.
message AuthRequest {
  string auth_token = 1; // JWT in metadata
  string client_version = 2;
}

service OrderService {
  rpc CreateOrder (CreateOrderRequest) returns (Order) {
    option (grpc.metadata) = {
      key: "auth_token";
    };
  }
}
```

---

### 6. **Field Naming Conventions**
- **Boolean fields:** `is_active`, `has_expired` (not `isActive`—go language prefers snake_case).
- **Nested resources:** Use descriptive names (e.g., `user: User{}` instead of `profile: User`).
- **Arrays:** `items: repeated Item{}` (not `product_list`).

```protobuf
message OrderItem {
  string product_id = 1;
  string product_name = 2;
  int32 quantity = 3;
  string currency = 4;
  string price = 5;
}
```

---

## Implementation Guide

### Step 1: Choose a Base Package
Start with `service/v1/proto.proto`:

```protobuf
syntax = "proto3";
package service.v1;
option go_package = "github.com/yourorg/service/v1;service";

import "google/api/annotations.proto";
import "google/rpc/error_details.proto";
```

### Step 2: Define Common Types
Create shared types (e.g., `pagination.proto`):

```protobuf
package common.v1;

message PageRequest {
  int32 page_size = 1 [default = 20];
  string page_token = 2;
}

message PageResponse {
  int32 page_size = 1;
  string page_token = 2;
  int32 total = 3;
}
```

### Step 3: Wire Up gRPC-Gateway (Optional)
If exposing REST-compatible endpoints:

```yaml
# config.yaml
type: google.api.Service
config_version: 3
name: order.v1.order_service
title: Order Service
apis:
  - name: order.v1.OrderService
```

```yaml
# api.yaml
type: google.api.HttpRule
select: *.OrderService.CreateOrder
get: /v1/orders
```

Generate code with:
```bash
protoc \
  --go_out=. \
  --go-grpc_out=. \
  --http_out=./http \
  --plugin=protoc-gen-grpc_gateway \
  --grpc-gateway_out=. \
  *.proto
```

---

## Common Mistakes to Avoid

1. **Overloading Methods**
   Don’t use `UpdateOrder` for both partial and full updates. Create `UpdateOrder` + `PatchOrder`.

2. **Lack of Versioning**
   Avoid modifying existing fields in `.proto` files. Use backward-compatible defaults instead:
   ```protobuf
   message Order {
     string id = 1;
     string user_id = 2;          // Required
     string notes = 3 [default = ""];
   }
   ```

3. **Ignoring gRPC Deadlines**
   Never assume calls will succeed. Set deadlines and retry transient errors:
   ```go
   ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
   defer cancel()
   resp, err := s.CreateOrder(ctx, &pb.CreateOrderRequest{})
   ```

4. **Hiding Error Details in Production**
   Always include error details (even if obfuscated). Clients need metadata to retry or handle failures.

5. **Not Testing Unary vs. Streaming**
   Ensure your service works as both a server and client for unary and streaming calls.

---

## Key Takeaways

✅ **Adapt REST conventions** for consistency: resource names, HTTP-like verbs, pagination.
✅ **Use gRPC status codes + custom errors** to replace HTTP statuses.
✅ **Version your `.proto` files** with semantic versioning (`service/v1/proto.proto`).
✅ **Standardize field naming** (snake_case, descriptive names) for tooling and docs.
✅ **Combine gRPC metadata + headers** for auth and cross-cutting concerns.
✅ **Avoid ad-hoc patterns**—choose one approach (e.g., always use `PageRequest` for pagination).
✅ **Test against real clients** (not just unit tests). Use `grpcurl` to inspect traffic.
✅ **Document your conventions** in a team README or Pulumi/Terraform docs.

---

## Conclusion

gRPC’s raw speed is a gift—but like any tool, its power fades without discipline. By adopting REST-like conventions, you unlock **maintainability, scalability, and developer productivity** without sacrificing gRPC’s performance. Key steps:
1. Use **consistent naming** for RPCs and fields.
2. **Version your `.proto` files** to avoid breaking changes.
3. **Standardize error handling** with gRPC status codes + custom details.
4. **Embrace pagination and metadata** like REST.

Go forth and design APIs that last. And when in doubt, remember: **if it doesn’t work like REST, is it really gRPC?**

---
```

This blog post is ready to publish. It balances theory with practical examples, highlights tradeoffs (e.g., binary protocol vs. tooling support), and avoids hype by focusing on real-world scenarios. The code snippets demonstrate implementation details in Go, but the principles apply to any language (Java, Python, C++).