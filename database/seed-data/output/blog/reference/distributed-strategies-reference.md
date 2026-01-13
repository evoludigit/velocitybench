# **[Pattern] Distributed Strategies Reference Guide**

---
## **Overview**
The **Distributed Strategies** pattern enables organizations to execute application logic in multiple, isolated environments while maintaining consistency, scalability, and fault tolerance. This pattern is ideal for large-scale distributed systems where a single centralized strategy cannot meet performance or availability demands. By decomposing business logic into modular, versioned strategies—each running independently in separate instances (microservices, containers, or serverless functions)—the system achieves **loose coupling**, **parallel processing**, and **easy maintenance**.

Distributed Strategies are particularly useful in:
- **Multi-region deployments** (low-latency global services)
- **A/B testing & canary releases** (side-by-side strategy execution)
- **Legacy migration** (gradual replacement of monolithic logic)
- **Workload isolation** (security, compliance, or team boundaries)
- **Dynamic routing** (user-specific strategy selection at runtime)

The pattern assumes statelessness for each strategy instance and relies on **event-driven communication** or **synchronous routing** to coordinate results.

---

### **Key Concepts**
| Concept               | Description                                                                                                                                                                                                 |
|-----------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Strategy Instance** | A self-contained unit of logic (e.g., a container, serverless function, or microservice) that implements a specific algorithm or process.                                                                 |
| **Strategy Version**  | A semantic version (e.g., `v1.2.0`) tied to a deployed instance. Allows backward compatibility and rollback support.                                                                                          |
| **Strategy Registry** | A centralized catalog (database, service mesh, or config store) listing available strategies, versions, and metadata (e.g., performance metrics, dependencies).                                          |
| **Routing Layer**     | Decides which strategy instance to invoke (e.g., based on user ID, region, or feature flag). Can be static (config-driven) or dynamic (runtime decision).                                                   |
| **Result Aggregator** | Collects outputs from multiple strategies and applies post-processing (e.g., weighted averaging, fallback logic, or error handling).                                                                |
| **Event Bus**         | (Optional) Asynchronous communication channel for strategies to emit events (e.g., `StrategyCompleted`, `StrategyFailed`) and react to external triggers (e.g., `UserProfileUpdated`).               |
| **Circuit Breaker**   | Protects routing layers from cascading failures by shutting down flaky strategies temporarily.                                                                                                             |
| **Canary Routing**    | Gradually shifts traffic from a primary strategy to a new version (e.g., 5% → 50% → 100%) to test stability.                                                                                        |

---

## **Schema Reference**
Below are the core schemas for implementing Distributed Strategies. Fields marked with `*` are required.

### **1. Strategy Registry Entry**
| Field               | Type            | Description                                                                                                                                                                                                 | Example                          |
|---------------------|-----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------|
| `strategyId*`       | `string`        | Unique identifier for the strategy (e.g., `payment_processor`).                                                                                                                                                  | `auth_service`                   |
| `version*`          | `string`        | Semantic version (e.g., `v1.0.0`).                                                                                                                                                                               | `v2.3.1`                         |
| `description`       | `string`        | Human-readable purpose of the strategy.                                                                                                                                                                 | "Token-based authentication"      |
| `endpoint*`         | `string`        | URL or service address (e.g., `http://strategy-service-v2:8080`, `aws-lambda:arn:...`).                                                                                                                      | `http://auth-v2.default.svc`     |
| `healthEndpoint`    | `string`        | Optional endpoint for health checks (e.g., `/health`).                                                                                                                                                   | `/ping`                          |
| `metricsEndpoint`   | `string`        | Endpoint for exposure of strategy-specific metrics (e.g., latency, error rates).                                                                                                                              | `/metrics`                       |
| `dependencies`      | `array<string>` | List of other strategies this one relies on (e.g., `["cache_service:v1.2.0"]`).                                                                                                                               | `["logging:v1.0.0"]`             |
| `routingPolicy`     | `string`        | Rule for selecting this strategy (e.g., `user_geo`, `feature_flag`).                                                                                                                                            | `user_segment`                   |
| `isActive`          | `boolean`       | `true` if strategy is currently enabled for routing.                                                                                                                                                     | `true`                           |
| `createdAt`         | `timestamp`     | Deployment timestamp.                                                                                                                                                                                       | `2024-01-15T08:00:00Z`           |
| `updatedAt`         | `timestamp`     | Last modification timestamp.                                                                                                                                                                               | `2024-02-20T14:30:00Z`           |
| `owner`             | `string`        | Team/organization responsible for the strategy.                                                                                                                                                           | `auth-team@company.com`          |
| `fallbackStrategy`  | `string`        | ID + version of a backup strategy if this one fails (e.g., `auth_service:v1.0.0`).                                                                                                                          | `auth_service:v1.0.0`            |

---

### **2. Strategy Request Message**
| Field               | Type            | Description                                                                                                                                                                                                 | Example                          |
|---------------------|-----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------|
| `contextId*`        | `string`        | Correlates requests across distributed calls (e.g., `user_123_session_456`).                                                                                                                                       | `ecommerce_order_789`            |
| `payload*`          | `object`        | Strategy-specific input data (schema varies by strategy).                                                                                                                                                 | `{"token": "abc123", "ttl": 3600}`|
| `metadata`          | `object`        | Optional metadata (e.g., `user_id`, `requested_by`).                                                                                                                                                      | `{"user_id": "42"}`             |
| `strategyId*`       | `string`        | Target strategy ID (e.g., `auth_service`).                                                                                                                                                              | `auth_service`                   |
| `version`           | `string`        | Target version (defaults to latest if omitted).                                                                                                                                                          | `v2.3.1`                         |
| `timeoutMs`         | `integer`       | Max time to wait for a response (defaults to service-wide timeout).                                                                                                                                       | `2000`                           |
| `retryPolicy`       | `object`        | Retry configuration (e.g., `max_retries: 2`, `backoff_ms: 500`).                                                                                                                                           | `{ "max_retries": 3 }`           |

**Example Payload (Authentication Strategy):**
```json
{
  "contextId": "ecommerce_order_789",
  "payload": {
    "token": "abc123",
    "ttl": 3600
  },
  "metadata": {
    "user_id": "42",
    "requested_by": "frontend_app"
  },
  "strategyId": "auth_service",
  "version": "v2.3.1",
  "timeoutMs": 2000
}
```

---

### **3. Strategy Response Message**
| Field               | Type            | Description                                                                                                                                                                                                 | Example                          |
|---------------------|-----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------|
| `contextId*`        | `string`        | Matches request context ID for correlation.                                                                                                                                                               | `ecommerce_order_789`            |
| `status`            | `string`        | `"success"`, `"failed"`, or `"timeout"`.                                                                                                                                                                | `"success"`                      |
| `data`              | `object`        | Strategy-specific output.                                                                                                                                                                                 | `{"valid": true, "user_id": "42"}`|
| `errors`            | `array<object>` | Detailed error(s) if `status` is `"failed"`.                                                                                                                                                           | `[{ "code": "invalid_token", "message": "Expired token" }]` |
| `strategyId`        | `string`        | ID of the executed strategy.                                                                                                                                                                              | `auth_service`                   |
| `version`           | `string`        | Version executed.                                                                                                                                                                                      | `v2.3.1`                         |
| `executionTimeMs`   | `integer`       | Time taken to process the request.                                                                                                                                                                       | `120`                            |
| `traceId`           | `string`        | Distributed tracing identifier.                                                                                                                                                                          | `abc123-xyz456`                  |

**Example Response:**
```json
{
  "contextId": "ecommerce_order_789",
  "status": "success",
  "data": {
    "valid": true,
    "user_id": "42",
    "expires_at": "2024-03-01T12:00:00Z"
  },
  "strategyId": "auth_service",
  "version": "v2.3.1",
  "executionTimeMs": 120,
  "traceId": "abc123-xyz456"
}
```

---

## **Query Examples**
Below are practical queries for interacting with Distributed Strategies, assuming a **gRPC-based routing service** (`StrategyRouter`) and a **RESTful registry API**.

---

### **1. Register a New Strategy**
**gRPC (StrategyRouter):**
```proto
rpc RegisterStrategy (RegisterStrategyRequest) returns (RegisterStrategyResponse) {}
```
**Request Payload:**
```json
{
  "strategy": {
    "strategyId": "recommendation_engine",
    "version": "v1.0.0",
    "endpoint": "http://recommendation-service.default.svc:8080",
    "description": "Collaborative filtering for product recommendations",
    "routingPolicy": "user_preference",
    "isActive": true,
    "dependencies": ["user_profiles:v1.2.0"],
    "metricsEndpoint": "/prometheus"
  }
}
```
**Response:**
```json
{
  "status": "success",
  "strategyId": "recommendation_engine",
  "version": "v1.0.0",
  "assignedId": "recsys-12345"  // Internal registry key
}
```

---

### **2. Lookup Available Strategies**
**REST (Registry API):**
```
GET /v1/strategies?policy=user_segment&active=true
```
**Query Parameters:**
| Param      | Description                                                                 |
|------------|-----------------------------------------------------------------------------|
| `policy`   | Filter by routing policy (e.g., `user_segment`, `feature_flag`).           |
| `active`   | Boolean filter (`true`/`false`).                                            |
| `limit`    | Max results (default: 20).                                                  |
| `version`  | Specific version (e.g., `v2.3.1`).                                          |

**Response (JSON):**
```json
{
  "strategies": [
    {
      "strategyId": "auth_service",
      "version": "v2.3.1",
      "endpoint": "http://auth-v2.default.svc:8080",
      "routingPolicy": "user_segment",
      "isActive": true,
      "assignedId": "auth-67890"
    },
    {
      "strategyId": "auth_service",
      "version": "v1.0.0",
      "endpoint": "http://auth-v1.default.svc:8080",
      "routingPolicy": "user_segment",
      "isActive": false,
      "assignedId": "auth-abc123"
    }
  ],
  "count": 2
}
```

---

### **3. Invoke a Strategy**
**gRPC (StrategyRouter):**
```proto
rpc InvokeStrategy (InvokeRequest) returns (InvokeResponse) {}
```
**Request Payload:**
```json
{
  "contextId": "checkout_999",
  "payload": {
    "order_id": "order_123",
    "items": ["prod_456", "prod_789"]
  },
  "metadata": {
    "user_segment": "premium",
    "requested_by": "mobile_app"
  },
  "strategyId": "payment_processor",
  "version": "v1.2.0",
  "timeoutMs": 3000
}
```
**Response:**
```json
{
  "contextId": "checkout_999",
  "status": "success",
  "data": {
    "transaction_id": "txn_789",
    "status": "approved",
    "amount": 99.99
  },
  "strategyId": "payment_processor",
  "version": "v1.2.0",
  "executionTimeMs": 85
}
```

---

### **4. Dynamic Routing (Feature Flag Example)**
**REST (Routing API):**
```
GET /v1/strategies/routing?strategyId=auth_service&user_id=42&flag=canary_auth
```
**Query Parameters:**
| Param       | Description                                                                 |
|-------------|-----------------------------------------------------------------------------|
| `strategyId`| Target strategy (e.g., `auth_service`).                                    |
| `user_id`   | Identifies the user for segment-based routing.                             |
| `flag`      | Feature flag to override default routing (e.g., `canary_auth`).             |

**Response:**
```json
{
  "selectedStrategy": {
    "strategyId": "auth_service",
    "version": "v2.3.1",  // Overrides default v1.0.0 for users in canary
    "endpoint": "http://auth-v2.default.svc:8080",
    "routingPolicy": "feature_flag"
  }
}
```

---

### **5. Fallback to Legacy Strategy**
**gRPC (StrategyRouter):**
```proto
rpc InvokeWithFallback (InvokeWithFallbackRequest) returns (InvokeWithFallbackResponse) {}
```
**Request Payload:**
```json
{
  "contextId": "shipping_456",
  "payload": {
    "order_id": "order_123",
    "destination": "us-west"
  },
  "strategyId": "shipping_calculator",
  "version": "v2.0.0",
  "fallbackStrategy": "shipping_calculator:v1.5.0"
}
```
**Behavior:**
1. Tries `shipping_calculator:v2.0.0` (new version).
2. If it fails, automatically retries with `v1.5.0` (legacy).
3. Aggregates results (e.g., prioritizes `v2.0.0` if successful).

**Response:**
```json
{
  "contextId": "shipping_456",
  "primaryResult": {
    "status": "success",
    "data": { "cost": 12.99, "delivery_days": 3 },
    "strategyVersion": "v2.0.0"
  },
  "fallbackResult": null,
  "finalDecision": {
    "cost": 12.99,
    "delivery_days": 3,
    "source": "primary"
  }
}
```

---

### **6. Canary Rollout (Traffic Splitting)**
**REST (Routing API):**
```
POST /v1/strategies/canary
```
**Request Body:**
```json
{
  "strategyId": "recommendation_engine",
  "newVersion": "v1.1.0",
  "initialTrafficPercent": 10,
  "trafficRamp": {
    "days": 7,
    "stepPercent": 5  // Increase by 5% per day
  },
  "monitoring": {
    "errorThreshold": 1.0,  // Stop if error rate > 1%
    "metric": "recommendation_accuracy"
  }
}
```
**Response:**
```json
{
  "status": "started",
  "canaryId": "recsys-canary-123",
  "schedule": {
    "day1": { "recommendation_engine:v1.0.0": 90, "recommendation_engine:v1.1.0": 10 },
    "day2": { "v1.0.0": 85, "v1.1.0": 15 },
    ...
  }
}
```

---

## **Implementation Best Practices**
1. **Idempotency**: Ensure strategies are idempotent (same input → same output) to avoid duplicate processing.
2. **Circuit Breakers**: Implement retry logic with exponential backoff for transient failures.
3. **Observability**:
   - Expose metrics (latency, error rates) via Prometheus/OpenTelemetry.
   - Log strategy invocations with context ID for tracing.
4. **Schema Evolution**:
   - Use backward-compatible payload schemas (e.g., add optional fields).
   - Document breaking changes in version notes.
5. **Security**:
   - Authenticate/authorize all strategy endpoints (e.g., mutual TLS, API keys).
   - Validate payloads against OpenAPI schemas.
6. **Testing**:
   - Test failure modes (e.g., strategy downtime, network partitions).
   - Use chaos engineering to simulate canary rollouts.
7. **Cost Optimization**:
   - Scale strategy instances based on demand (Kubernetes HPA, AWS Auto Scaling).
   - Cache frequent strategy calls (e.g., Redis).

---

## **Error Handling**
| Error Code         | Description                                                                 | Example Response                                                                 |
|--------------------|-----------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| `STRATEGY_NOT_FOUND`| Requested strategy version does not exist.                                   | `{ "code": "STRATEGY_NOT_FOUND", "message": "auth_service:v3.0.0 not found" }` |
| `ROUTING_FAILED`   | No active strategy matched the routing policy.                             | `{ "code": "ROUTING_FAILED", "message": "No active auth strategies for user_segment" }` |
| `INVALID_PAYLOAD`  | Payload schema validation failed.                                           | `{ "code": "INVALID_PAYLOAD", "errors": ["missing required field: token"] }` |
| `STRATEGY_TIMEOUT` | Strategy exceeded its timeout.                                              | `{ "code": "STRATEGY_TIMEOUT", "strategyId": "payment_processor", "timeoutMs": 3000