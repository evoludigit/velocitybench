# **[Pattern] Request Correlation Tracing – Reference Guide**

---

## **Overview**
Request Correlation Tracing (RCT) is a **distributed tracing** technique that assigns a unique identifier (e.g., `X-Correlation-ID`) to an end-user request as it traverses a microservices architecture or multi-component system. This enables log aggregation, debugging, and performance analysis by linking related interactions (e.g., API calls, DB queries, or background jobs) under a single trace.

RCT improves observability by:
- **Tracking request flows** across services.
- **Correlating logs** from different components (e.g., `backend-service`, `payment-gateway`).
- **Simplifying debugging** by tracing root-cause issues (latency spikes, errors).
- **Compliance** with audit trails for regulatory requirements.

Key use cases include:
✔ **Microservices** – Linking cross-service transactions.
✔ **Event-Driven Systems** – Correlating pub/sub messages with their triggers.
✔ **API Gateway** – Propagating IDs to downstream services.
✔ **Error Tracking** – Identifying cascading failures.

---

## **Schema Reference**
The following **standardized schema** defines RCT attributes (adaptable to JSON/XML/headers).

| **Field**               | **Type**       | **Description**                                                                                     | **Example**                          |
|-------------------------|----------------|-----------------------------------------------------------------------------------------------------|--------------------------------------|
| `correlationId`         | String (UUID)  | Unique identifier generated per request (preferably random or timestamp-based).                     | `550e8400-e29b-41d4-a716-446655440000` |
| `traceId`               | String (UUID)  | Optional parent trace ID for hierarchical tracing (e.g., child requests under a parent).           | `123e4567-e89b-12d3-a456-426614174000` |
| `parentSpanId`          | String         | ID of the parent span (e.g., API call) for hierarchical tracing.                                   | `child-span-123`                     |
| `timestamp`             | ISO-8601       | Request start/end time for latency analysis.                                                       | `2023-10-01T12:00:00Z`               |
| `serviceName`           | String         | Name of the service processing the request (e.g., `auth-service`).                               | `order-service`                      |
| `operation`             | String         | API endpoint or operation name (e.g., `/create-order`).                                           | `POST /purchase`                     |
| `status`                | String/Int     | HTTP status code or custom state (e.g., `200`, `500`).                                            | `200`                                |
| `durationMs`            | Integer        | Time taken by the component (milliseconds).                                                        | `45`                                 |
| `tags`                  | Key-Value Pairs| Metadata like `userId`, `sessionToken`, or error details.                                          | `{"userId": "abc123", "error": "DBTimeout"}` |
| `parentRequestId`       | String         | ID of the originating HTTP request (for web contexts).                                           | `req_id_789`                         |

---
**Headers for Propagation** (HTTP/HTTPS):
```http
X-Correlation-ID: 550e8400-e29b-41d4-a716-446655440000
X-Trace-ID:       123e4567-e89b-12d3-a456-426614174000
```

---
**Log Format Example** (JSON):
```json
{
  "correlationId": "550e8400-e29b-41d4-a716-446655440000",
  "traceId": "123e4567-e89b-12d3-a456-426614174000",
  "timestamp": "2023-10-01T12:00:00Z",
  "serviceName": "payment-gateway",
  "operation": "processPayment",
  "status": 200,
  "durationMs": 120,
  "tags": {
    "userId": "abc123",
    "amount": 99.99,
    "currency": "USD"
  }
}
```

---

## **Implementation Details**

### **1. Generating Correlation IDs**
- **Client-Side**: Generate a `correlationId` on the first request (e.g., in the API gateway).
  - *Example (Node.js):*
    ```javascript
    const correlationId = crypto.randomUUID(); // or Date.now().toString()
    headers['X-Correlation-ID'] = correlationId;
    ```
- **Server-Side**: Preserve the ID across service calls (e.g., using middleware).

### **2. Propagating IDs**
- **HTTP Headers**: Append `X-Correlation-ID` to all downstream requests.
  - *Example (Python Flask):*
    ```python
    @app.before_request
    def propagate_correlation():
        if 'X-Correlation-ID' not in request.headers:
            request.headers['X-Correlation-ID'] = str(uuid.uuid4())
    ```
- **Message Brokers**: Include the ID in Kafka/RabbitMQ headers/attributes:
  ```json
  {
    "headers": {
      "correlationId": "550e8400-e29b-41d4-a716-446655440000"
    }
  }
  ```
- **Databases**: Log the ID in SQL queries (e.g., `INSERT INTO audit_logs (correlation_id, ...) VALUES (...)`).

### **3. Hierarchical Tracing (Optional)**
For nested requests (e.g., async tasks), use a `traceId` + `spanId` pattern:
```http
X-Trace-ID:       parent-trace-id
X-Span-ID:        child-span-id
```

### **4. Logging**
- **Structured Logging**: Use a logging library (e.g., Structured Logging in Python, Winston in Node.js) to attach the `correlationId` to all logs:
  ```javascript
  logger.info('Processing payment', { correlationId, amount: 99.99 });
  ```
- **Centralized Logs**: Aggregate logs with the same `correlationId` in tools like:
  - **ELK Stack** (Elasticsearch, Logstash, Kibana)
  - **Splunk**
  - **Datadog/Lightstep**

### **5. Error Handling**
- **Circuit Breakers**: Use `correlationId` to correlate failures (e.g., Hystrix for Java, Resilience4j for Java/Kotlin).
- **Retries**: Avoid ID conflicts by generating new IDs for retries.

### **6. Performance Considerations**
- **Overhead**: Minimal (~1KB header size).
- **Sampling**: For high-throughput systems, sample traces (e.g., 1% of requests) to avoid log overload.

---

## **Query Examples**

### **1. Find All Logs for a Request**
**Tool**: ELK Stack (Kibana)
**Query**:
```json
{
  "query": {
    "bool": {
      "must": [
        { "term": { "correlationId.keyword": "550e8400-e29b-41d4-a716-446655440000" } }
      ]
    }
  }
}
```
**Output**:
```
| serviceName    | operation      | status | durationMs | timestamp          |
|----------------|----------------|--------|------------|--------------------|
| payment-gw     | processPayment | 200    | 120        | 2023-10-01T12:00:00 |
| auth-service   | validateUser   | 200    | 50         | 2023-10-01T12:00:01 |
```

---

### **2. Trace a Failed Transaction (Grafana + Prometheus)**
**Steps**:
1. Filter logs where `status != 200` **AND** `correlationId` matches a known ID.
2. Visualize latency spikes using `durationMs` metrics:
   ```promql
   histogram_quantile(0.95, sum(rate(request_duration_ms_bucket[5m])) by (correlationId))
   ```

---

### **3. Correlate API and DB Logs**
**SQL Query** (PostgreSQL):
```sql
SELECT *
FROM api_logs
JOIN db_audit_logs ON api_logs.correlation_id = db_audit_logs.correlation_id
WHERE api_logs.correlation_id = '550e8400-e29b-41d4-a716-446655440000';
```

---

### **4. Detect Cascading Failures**
**Tool**: Datadog
**Alert Rule**:
- **Condition**: `status == 500` **AND** `count_by_correlationId > 5` (in 1 minute).
- **Action**: Notify SRE team with the `correlationId`.

---

## **Related Patterns**

| **Pattern**               | **Relation to RCT**                                                                 | **When to Use Together**                          |
|---------------------------|------------------------------------------------------------------------------------|---------------------------------------------------|
| **Circuit Breaker**       | RCT helps identify which downstream service failed (e.g., `payment-gateway`).         | High-availability systems.                       |
| **Distributed Locks**     | Correlate lock acquisitions/releases with user requests.                           | Concurrent request handling.                     |
| **Saga Pattern**          | Use `correlationId` to link compensating transactions.                              | Long-running distributed flows.                 |
| **API Gateway**           | Gateway injects `correlationId` into all downstream calls.                         | Microservices architectures.                     |
| ** observability (OpenTelemetry)** | RCT is a foundational concept; OTel adds metrics/tracing infrastructure.       | Advanced tracing with auto-instrumentation.      |
| **Retry with Exponential Backoff** | Correlate retries to original requests for debugging.                            | Resilient systems.                               |

---

## **Best Practices**
1. **Consistency**: Use the same `correlationId` across all logs/metrics.
2. **Immutability**: Never modify the ID after generation.
3. **Sampling**: For high-volume systems, sample traces (e.g., 0.1%–1%).
4. **Security**: Ensure IDs don’t leak sensitive data (e.g., don’t use `userId` as `correlationId`).
5. **Tooling**: Integrate with APM tools (e.g., Jaeger, Zipkin, New Relic).
6. **Audit Logs**: Persist `correlationId` in databases for compliance.

---
## **Anti-Patterns**
- ❌ **Overhead**: Avoid generating IDs for every internal DB query (use sampling).
- ❌ **Poor Propagation**: Ignoring headers in async tasks (e.g., background jobs).
- ❌ **Inconsistent Naming**: Mixing `X-Correlation-ID`, `X-Trace-ID`, and custom headers.
- ❌ **No Centralization**: Scattering logs without aggregation tools.

---
## **Tools/Libraries**
| **Type**               | **Tools**                                                                 |
|------------------------|---------------------------------------------------------------------------|
| **HTTP Middleware**    | Express Middleware (Node.js), Flask Extensions (Python), Spring Cloud Sleuth (Java). |
| **Logging**            | Winston (Node.js), StructLog (Python), Logback (Java).                     |
| **Tracing**            | OpenTelemetry, Jaeger, Zipkin, Datadog, Lightstep.                          |
| **Message Brokers**    | Kafka Headers, RabbitMQ `message_id`/`correlation_id`.                    |
| **Databases**          | SQL `WITH` clauses, Elasticsearch `parent` field.                         |

---
## **Example Workflow**
1. **User Request**:
   ```http
   GET /orders?user=abc123
   X-Correlation-ID: 550e8400-e29b-41d4-a716-446655440000
   ```
2. **Order Service**:
   - Logs the ID and forwards to `payment-service`.
   ```json
   { "correlationId": "550e8400...", "operation": "fetchOrders" }
   ```
3. **Payment Service**:
   - Processes payment and logs:
   ```json
   { "correlationId": "550e8400...", "status": 200, "amount": 99.99 }
   ```
4. **Debugging**:
   - Query logs with `correlationId` to see the full flow.

---
**Key Takeaway**: RCT is a **low-cost, high-impact** pattern for observability. Start with HTTP headers + structured logs, then extend to async systems and APM tools.