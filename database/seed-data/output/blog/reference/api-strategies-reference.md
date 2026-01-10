# **[Pattern] API Strategies Reference Guide**

## **Overview**
API Strategies define how your system exposes and manages data over HTTP/HTTPS, balancing trade-offs between **performance**, **simplicity**, **scalability**, and **developer experience**. This pattern categorizes common API designs—**RESTful**, **GraphQL**, **gRPC**, and **Event-Driven APIs**—alongside hybrid approaches like **Microservice Choreography** and **API Gateways**. Each strategy suits specific use cases, influencing latency, client load, and real-time needs. This guide covers core concepts, schema structures, query patterns, and trade-offs for selecting and implementing an API strategy.

---

## **1. Key Concepts & Implementation Details**

### **1.1 Core API Strategies**
| **Strategy**       | **Key Characteristics**                                                                 | **Best Use Cases**                                                                 |
|--------------------|----------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **RESTful**        | Resource-based (CRUD), stateless, cacheable endpoints.                                | Traditional web apps, monoliths, browsers, mobile clients.                      |
| **GraphQL**        | Single endpoint, flexible queries, schema-first design.                                | Complex frontend queries, mobile apps, real-time dashboards.                     |
| **gRPC**           | Binary protocol, strongly typed, low-latency RPC.                                      | Microservices, internal tooling, high-throughput systems.                       |
| **Event-Driven**   | Async pub/sub (e.g., Kafka, WebSockets), decoupled producers/consumers.               | Streaming, notifications, background processing.                                 |
| **Hybrid**         | Combines strategies (e.g., REST + GraphQL at `/graphql` and `/api/v1`).               | Enterprise systems needing backward/forward compatibility.                       |

### **1.2 Non-Functional Requirements**
- **Latency**: gRPC < REST < GraphQL < Event-Driven (for initial response).
- **Query Flexibility**: GraphQL > REST > gRPC.
- **Client Complexity**: REST (simple) < GraphQL (schema learning) < gRPC (codegen).
- **Scalability**: Event-Driven (async) > REST (stateless) > GraphQL (server-side execution).

---
## **2. Schema Reference**
Compare schemas for **REST**, **GraphQL**, and **gRPC** for a hypothetical `User` resource.

| **Strategy** | **Endpoint/Query**          | **Request Payload**                     | **Response Payload**                                      | **Key Attributes**                          |
|--------------|----------------------------|----------------------------------------|----------------------------------------------------------|---------------------------------------------|
| **REST**     | `GET /users/{id}`          | `id: "123"` (URL parameter)            | `{ "id": "123", "name": "Alice", "email": "alice@example.com" }` | Standardized, versioned paths (`/v1/users`). |
| **GraphQL**  | `POST /graphql`            | `{ query: "query { user(id: \"123\") { name email } }" }` | `{ "data": { "user": { "name": "Alice", "email": "alice@example.com" } } }` | Self-documenting, nested queries.          |
| **gRPC**     | `UserService.GetUser()`    | `{ id: "123" }` (binary protobuf)     | `{ id: "123", name: "Alice", email: "alice@example.com" }` | Strong typing, binary serialization.       |

---
## **3. Query Examples**

### **3.1 RESTful Queries**
**Get a User:**
```http
GET /api/v1/users/123
Headers: Accept: application/json
Response:
{
  "id": "123",
  "name": "Alice",
  "email": "alice@example.com"
}
```

**Create a User:**
```http
POST /api/v1/users
Headers: Content-Type: application/json
Body:
{
  "name": "Bob",
  "email": "bob@example.com"
}
Response: 201 Created
```

**Pagination:**
```http
GET /api/v1/users?page=2&limit=10
```

---
### **3.2 GraphQL Queries**
**Fetch User with Posts:**
```graphql
query {
  user(id: "123") {
    name
    email
    posts(first: 3) {
      title
    }
  }
}
Response:
{
  "data": {
    "user": {
      "name": "Alice",
      "email": "alice@example.com",
      "posts": [
        { "title": "Post 1" },
        { "title": "Post 2" }
      ]
    }
  }
}
```

**Mutations (Updates):**
```graphql
mutation {
  updateUser(id: "123", email: "new@example.com") {
    email
  }
}
```

---
### **3.3 gRPC Queries**
**Protocol Buffer Definition (`user.proto`):**
```protobuf
service UserService {
  rpc GetUser (GetUserRequest) returns (User);
}
message GetUserRequest {
  string id = 1;
}
message User {
  string id = 1;
  string name = 2;
  string email = 3;
}
```

**Client Call (Python):**
```python
from user_pb2 import GetUserRequest
from user_pb2_grpc import UserServiceStub
import grpc

stub = UserServiceStub(grpc.insecure_channel("localhost:50051"))
request = GetUserRequest(id="123")
response = stub.GetUser(request)
print(response.name)  # Alice
```

---
### **3.4 Event-Driven (Kafka Example)**
**Publish a User Event:**
```python
producer = KafkaProducer(bootstrap_servers=['localhost:9092'])
producer.send(
  topic='user_created',
  value='{"id": "123", "name": "Alice"}'.encode('utf-8')
)
```

**Consume Events:**
```python
consumer = KafkaConsumer('user_created', bootstrap_servers=['localhost:9092'])
for message in consumer:
  print(message.value.decode('utf-8'))  # {"id": "123", ...}
```

---
## **4. Trade-Off Analysis**
| **Criteria**       | **REST**               | **GraphQL**            | **gRPC**               | **Event-Driven**        |
|--------------------|------------------------|------------------------|------------------------|-------------------------|
| **Latency**        | Medium (HTTP overhead) | High (query parsing)   | Low (binary)           | Very Low (async)        |
| **Query Flexibility** | Limited (fixed endpoints) | High (client-defined) | Low (predefined RPCs) | None (event schema fixed) |
| **Client Complexity** | Low (standard HTTP)   | Medium (schema learning) | High (codegen)       | Low (listeners only)    |
| **Scalability**    | Good (stateless)       | Moderate (server-side) | Excellent (binary)     | Excellent (decoupled)   |
| **Use Case Fit**   | CRUD apps, browsers    | Complex frontend apps  | Microservices         | Real-time systems       |

---
## **5. Related Patterns**
1. **Resource Naming Conventions**
   - REST: `/resources/{id}` (e.g., `/products/123`).
   - GraphQL: Schema-first (e.g., `type Product { id: ID! }`).
2. **API Versioning**
   - REST: URL (`/v1/users`), headers (`Accept: application/vnd.company.v1+json`).
   - GraphQL: Schema extensions (`__schema`) or separate endpoints (`/graphql/v2`).
3. **Authentication**
   - REST: JWT in `Authorization` header.
   - GraphQL: Same, or custom directives (`@auth`).
   - gRPC: Token in metadata (`("authorization", "Bearer token")`).
4. **Rate Limiting**
   - REST: `X-RateLimit-Limit` header.
   - GraphQL: Middleware (e.g., Apollo’s `rateLimit` plugin).
5. **API Gateways**
   - Unify strategies (e.g., Kong, AWS API Gateway) for routing, auth, and monitoring.
6. **Caching Strategies**
   - REST: CDN (Cloudflare), client-side (ETag).
   - GraphQL: Persisted queries, Apollo Cache.
   - gRPC: gRPC-Web with caching proxies.

---
## **6. Implementation Checklist**
| **Step**               | **REST**               | **GraphQL**            | **gRPC**               | **Event-Driven**        |
|------------------------|------------------------|------------------------|------------------------|-------------------------|
| **Schema Definition**  | OpenAPI/Swagger        | GraphQL SDL            | Protocol Buffers       | Kafka Schema Registry   |
| **Server Setup**       | Flask/FastAPI          | Hasura/Apollo Server   | gRPC Server (Python/Go)| Kafka Producer/Consumer |
| **Client Libraries**   | `fetch`, `axios`       | `Apollo Client`        | gRPC Client (protobuf) | Kafka-Python/SDKs       |
| **Tooling**            | Postman, Insomnia       | GraphQL Playground     | gRPCurl                | Kafka UI (Kafdrop)      |
| **Monitoring**         | Prometheus, Datadog    | Apollo Studio          | gRPC Metrics           | Kafka Lag Monitoring    |

---
## **7. When to Choose Which Strategy**
- **Use REST** if:
  - You need simplicity (browsers, mobile), or a mature ecosystem (Postman, OpenAPI).
  - Your clients are limited in complexity (e.g., vanilla JS).
  - Versioning is critical (`/v1`, `/v2`).

- **Use GraphQL** if:
  - Frontends need flexible queries (e.g., React/Next.js).
  - You want to reduce over-fetching/under-fetching.
  - Your team prefers a single endpoint for all data.

- **Use gRPC** if:
  - You’re building microservices with high throughput.
  - Latency is critical (e.g., trading systems).
  - Strong typing and code generation are priorities.

- **Use Event-Driven** if:
  - You need real-time updates (e.g., chat, notifications).
  - Producers/consumers are decoupled (e.g., payment processing).
  - Async processing is required (e.g., file uploads).