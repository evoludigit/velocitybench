# **[Pattern] Bulk Operations & Batch APIs Reference Guide**

---

## **1. Overview**
Bulk Operations & Batch APIs optimize high-volume data manipulation by processing multiple records in a single request rather than individual transactions. This pattern mitigates performance bottlenecks, reduces server load, and prevents resource exhaustion when handling 1,000+ records at once.

### **Key Use Cases**
- **Mass inserts/updates**: Adding or modifying hundreds/thousands of records (e.g., bulk user imports, inventory updates).
- **Scheduled batch processing**: Offloading time-consuming operations (e.g., nightly data migrations).
- **API efficiency**: Reducing latency by minimizing round-trips to the server.

### **Core Principles**
- **Rate limiting**: Enforce thresholds to avoid overwhelming systems.
- **Idempotency**: Ensure retries on failures don’t duplicate unintended side effects.
- **Error handling**: Provide granular failure responses (e.g., per-record status codes).

---

## **2. Schema Reference**

### **Batch Request Payload**
| Field               | Type       | Description                                                                 | Required |
|---------------------|------------|-----------------------------------------------------------------------------|----------|
| `items`             | Array      | List of records to process (max `N` per batch, see limits below).         | Yes       |
| `operation`         | String     | `"insert"`, `"update"`, or `"delete"` (default: `"insert"`).               | No        |
| `idempotency_key`   | String     | Unique key to ensure retry safety (UUID recommended).                     | No        |
| `merge_conflicts`   | Boolean    | If `true`, overwrite conflicting fields during updates.                    | No        |
| `skip_validation`   | Boolean    | Bypasses schema validation (use cautiously).                                | No        |

### **Batch Response Payload**
| Field               | Type       | Description                                                                 | Example Value          |
|---------------------|------------|-----------------------------------------------------------------------------|------------------------|
| `successful`        | Integer    | Count of successfully processed items.                                     | 987                    |
| `failed`            | Integer    | Count of failed items.                                                      | 12                     |
| `errors`            | Array      | Detailed error object for failed items:                                      |                        |
| &nbsp;&nbsp;`item`  | Object     | Failed record (partial or full, based on `skip_validation`).               | `{"id": "123", ...}`   |
| &nbsp;&nbsp;`code`  | String     | Error classification (e.g., `validation_error`, `resource_limit`).          | `validation_error`     |
| &nbsp;&nbsp;`message` | String | Human-readable error description.                                          | `"Duplicate 'email' detected."` |

---

## **3. Implementation Details**

### **A. Rate Limits & Throttling**
- **Default limits**:
  - Max `items`: 5,000 per batch (adjustable via config).
  - Max batch size: 10 MB (gzip-compressed).
  - Rate limit: 10 batches/minute per API key.
- **Mitigation**:
  - Use exponential backoff for retries (e.g., `3s → 10s → 30s`).
  - Implement server-side throttling with `429 Too Many Requests`.

### **B. Idempotency**
- **Mechanism**: Client generates a `idempotency_key` (e.g., UUID) and includes it in the request.
- **Server behavior**:
  - On retry, the server checks for existing processing of the key.
  - Returns `200 OK` if already processed; `409 Conflict` if processing but not yet complete.
- **Example**:
  ```http
  POST /api/v1/batch
  Headers: idempotency-key: abc123-xyz456
  Body: { "items": [...], "operation": "insert" }
  ```

### **C. Error Handling**
- **Partial success**: The API returns a `207 Multi-Status` for mixed success/failure batches.
- **Retry strategies**:
  - Transient errors (e.g., `500 Internal Server Error`): Exponential backoff.
  - Idempotent errors (e.g., `409 Conflict`): Retry immediately or skip.
  - Non-retryable (e.g., `400 Bad Request`): Notify admin.

### **D. Performance Considerations**
- **Batch size tuning**:
  - Start with 1,000 items per batch; adjust based on `p99` latency.
  - Monitor server CPU/memory usage (e.g., via Prometheus).
- **Parallel processing**:
  - Use async APIs (e.g., Webhooks) for non-critical updates.
  - Example:
    ```http
    POST /api/v1/batch/async
    Headers: accept: application/json; profile=async
    ```

---

## **4. Query Examples**

### **A. Basic Batch Insert**
```http
POST /api/v1/batch
Content-Type: application/json

{
  "items": [
    {"name": "Alice", "email": "alice@example.com"},
    {"name": "Bob", "email": "bob@example.com"}
  ],
  "operation": "insert"
}
```

**Response**:
```json
{
  "successful": 2,
  "failed": 0,
  "errors": []
}
```

---

### **B. Conditional Update with Merge Conflicts**
```http
POST /api/v1/batch
Content-Type: application/json

{
  "items": [
    {"id": "1", "last_name": "Smith", "merge_conflicts": true},
    {"id": "2", "last_name": "Doe"}  // Conflicts with existing "last_name": "Johnson"
  ],
  "operation": "update"
}
```

**Response** (if conflicts exist):
```json
{
  "successful": 1,
  "failed": 1,
  "errors": [
    {
      "item": {"id": "2", "last_name": "Johnson"},
      "code": "merge_conflict",
      "message": "Field 'last_name' cannot be merged. Use 'merge_conflicts: true' or update field first."
    }
  ]
}
```

---

### **C. Deferred Async Processing**
```http
POST /api/v1/batch/async
Content-Type: application/json
Headers: accept: application/json; profile=async

{
  "items": [
    {"user_id": "456", "status": "active"},
    {"user_id": "789", "status": "pending"}
  ],
  "operation": "update"
}
```

**Response**:
```json
{
  "status": "processing",
  "batch_id": "batch_abc123",
  "webhook_url": "https://callback.example.com/webhook"
}
```

**Webhook Payload** (after processing):
```json
{
  "batch_id": "batch_abc123",
  "results": [
    {"user_id": "456", "status": "success"},
    {"user_id": "789", "status": "failed", "error": "Invalid status value"}
  ]
}
```

---

## **5. Error Codes**

| Code               | Description                                                                 | HTTP Status |
|--------------------|-----------------------------------------------------------------------------|--------------|
| `200 OK`           | Batch fully processed successfully.                                         | 200          |
| `207 Multi-Status` | Partial success/failure (check `errors` array).                             | 207          |
| `400 Bad Request`  | Invalid payload (e.g., malformed `items`, missing required fields).        | 400          |
| `409 Conflict`     | Idempotency key conflict (already processing or complete).                   | 409          |
| `429 Too Many`     | Rate limit exceeded (check `Retry-After` header).                           | 429          |
| `500 Internal`     | Server error (transient; retry with backoff).                              | 500          |

---

## **6. Related Patterns**
| Pattern                          | Description                                                                 | When to Use                                      |
|----------------------------------|-----------------------------------------------------------------------------|--------------------------------------------------|
| **Retry & Backoff**              | Exponential delays between retries for transient failures.                 | Handling `5xx` errors or throttling.             |
| **Idempotency Keys**             | Ensures duplicate requests don’t cause side effects.                         | Critical operations (e.g., payments, inventory).  |
| **Async Processing**             | Offloads work to background jobs (e.g., SQS, RabbitMQ).                    | Non-critical or time-consuming updates.         |
| **Paginated Queries**            | Splits large datasets into smaller chunks for retrieval.                     | Fetching historical data or logs.               |
| **Optimistic Locking**           | Uses `version` fields to handle concurrent updates gracefully.              | Multi-user systems (e.g., collaborative editing). |

---

## **7. Best Practices**
1. **Validation**:
   - Validate client-side before sending batches (reduce server load).
   - Use `skip_validation` sparingly (e.g., for trusted sources).
2. **Monitoring**:
   - Track `failed` counts and error codes (e.g., via Datadog).
   - Alert on spikes in batch failures.
3. **Testing**:
   - Simulate network latency (e.g., `netem` tool) to test retry logic.
   - Test edge cases: empty batches, malformed `idempotency_key`.
4. **Documentation**:
   - Specify exact limits (e.g., `"items": [max 5000]`).
   - Provide examples for success/failure scenarios.

---
**See Also**:
- [API Design: Bulk Operations](https://example.com/api-guides/bulk-ops)
- [Rate Limiting Guide](https://example.com/api-guides/rate-limits)