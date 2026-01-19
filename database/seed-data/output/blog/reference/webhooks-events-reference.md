---

# **[Pattern] Webhooks & Event Notifications – Reference Guide**

---

## **1. Overview**
Webhooks enable **server-to-server communication** where a source system (*publisher*) sends HTTP POST requests to a **pre-configured endpoint** (*subscriber*) when an event occurs (e.g., order status change, payment confirmation, inventory update). Unlike polling (where clients periodically check for changes), webhooks **push events in real time**, reducing latency and improving efficiency. However, this introduces challenges:
- **Reliability**: Failed deliveries must be retried or marked as "delivered."
- **Ordering**: Events might arrive out of sequence due to network issues.
- **Deduplication**: Duplicate events may occur due to retries or transient failures.
- **Idempotency**: Subscribers must handle duplicate events without side effects.

This guide covers implementation best practices, schemas, and error-handling strategies.

---

## **2. Key Concepts & Terminology**

| Term               | Definition                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| **Publisher**      | System generating events (e.g., e-commerce platform, IoT device).           |
| **Subscriber**     | System listening for events (e.g., CRM, analytics dashboard).                |
| **Webhook URL**    | HTTPS endpoint provided by the subscriber to receive events.                 |
| **Payload**        | JSON data sent in the POST request body.                                    |
| **Event ID**       | Unique identifier for an event (e.g., `order_12345`).                        |
| **Timestamp**      | When the event occurred (ISO 8601 format).                                  |
| **Retries**        | Publisher’s attempts to resend failed events (configurable limits apply).   |
| **Signature**      | HMAC-based proof of authenticity (to verify the publisher).                 |
| **Idempotency Key**| Unique key to prevent duplicate processing (e.g., `order_id`).              |

---

## **3. Schema Reference**

### **3.1. Webhook Payload Schema**
All webhook events conform to this base structure:

| Field               | Type     | Required | Description                                                                 |
|---------------------|----------|----------|-----------------------------------------------------------------------------|
| `event_id`          | `string` | Yes      | Unique identifier for the event (e.g., `order.created.12345`).               |
| `event_type`        | `string` | Yes      | Type of event (e.g., `"order.created"`, `"payment.processed"`).             |
| `timestamp`         | `string` | Yes      | ISO 8601 timestamp (e.g., `"2023-10-15T14:30:00Z"`).                       |
| `source`            | `string` | Yes      | Publisher’s system name (e.g., `"ecommerce-platform"`).                     |
| `data`              | `object` | Yes      | Event-specific payload (schema varies by `event_type`).                     |
| `signature`         | `string` | Yes      | HMAC-SHA256 signature for authentication (see **3.3** for details).          |
| `idempotency_key`   | `string` | No       | Unique key to deduplicate (e.g., `order_id`).                                |

---

### **3.2. Example Event Payloads**
#### **Order Created Event**
```json
{
  "event_id": "order.created.12345",
  "event_type": "order.created",
  "timestamp": "2023-10-15T14:30:00Z",
  "source": "ecommerce-platform",
  "data": {
    "order_id": "ord_12345",
    "customer_id": "cust_67890",
    "total_amount": 99.99,
    "currency": "USD",
    "items": [
      {"product_id": "prod_abc", "quantity": 2, "price": 49.99}
    ]
  },
  "signature": "abc123...xyz",
  "idempotency_key": "ord_12345"
}
```

#### **Payment Processed Event**
```json
{
  "event_id": "payment.processed.54321",
  "event_type": "payment.processed",
  "timestamp": "2023-10-15T14:35:00Z",
  "source": "payment-gateway",
  "data": {
    "transaction_id": "txn_54321",
    "order_id": "ord_12345",
    "amount": 99.99,
    "status": "completed",
    "payment_method": "credit_card"
  },
  "signature": "def456...ghi",
  "idempotency_key": "txn_54321"
}
```

---

### **3.3. Authentication (HMAC-SHA256)**
Publishers sign payloads to prevent tampering.
**Algorithm**:
```
signature = hmac_sha256(
  base64url_encode(utf8_encode(payload_stringified)),
  shared_secret
)
```
- **`shared_secret`**: A secret key shared between publisher and subscriber (stored securely).
- **Payload Stringification**: Convert the payload to a string (e.g., using [RFC 7515](https://tools.ietf.org/html/rfc7515)).

**Subscriber Validation**:
```python
import hmac, hashlib, base64

def verify_signature(payload, received_signature, shared_secret):
    payload_str = json.dumps(payload, separators=(",", ":"))
    expected_signature = hmac.new(
        shared_secret.encode(),
        payload_str.encode(),
        hashlib.sha256
    ).digest()
    return hmac.compare_digest(
        base64.urlsafe_b64encode(expected_signature),
        received_signature.encode()
    )
```

---

## **4. Implementation Best Practices**

### **4.1. Publisher Requirements**
1. **Retry Logic**:
   - Retry failed deliveries **exponentially** (e.g., 1s, 5s, 30s).
   - Limit retries to **5–7 attempts** (avoid loops with subscribers offline).
   - Use HTTP status codes:
     - `429 Too Many Requests`: Rate-limited.
     - `5xx`: Retryable error.
     - `4xx` (except `401`, `403`): Non-retryable.

2. **Idempotency**:
   - Require `idempotency_key` for critical events (e.g., payments).
   - Subscribers should treat identical requests as no-ops.

3. **Delivery Guarantees**:
   - **At-least-once**: Default (may send duplicates).
   - **At-most-once**: Use idempotency keys to avoid duplicates.

4. **Monitoring**:
   - Log failed deliveries with timestamps and retries.
   - Provide a **webhook dashboard** to track delivery status.

---

### **4.2. Subscriber Requirements**
1. **Endpoint Design**:
   - **URL**: `/webhooks/{event_type}` (e.g., `/webhooks/order.created`).
   - **Method**: Only `POST` (reject `GET`/`PUT`).
   - **Headers**:
     ```http
     Content-Type: application/json
     X-Event-ID: order.created.12345
     ```
   - **Status Codes**:
     - `200 OK`: Success.
     - `202 Accepted`: Async processing (e.g., queueing).
     - `400 Bad Request`: Malformed payload/signature.
     - `401 Unauthorized`: Invalid signature.
     - `429 Too Many Requests`: Throttle publisher.

2. **Error Handling**:
   - **Silent Failure**: Subscribers should **not** return `2xx` for retries.
   - **Retry-After Header**:
     ```http
     Retry-After: 30
     ```
   - **Dead Letter Queue (DLQ)**: Log failed events for manual review.

3. **Validation**:
   - Validate `signature` (as shown in **3.3**).
   - Check `timestamp` freshness (e.g., reject events older than 5 minutes).
   - Parse `data` against expected schemas (e.g., using JSON Schema).

4. **Scaling**:
   - Use **load balancers** to distribute traffic.
   - Consider **message queues** (e.g., Kafka, RabbitMQ) for async processing.

---

### **4.3. Testing**
1. **Local Testing**:
   - Use tools like [ngrok](https://ngrok.com/) to expose local endpoints.
   - Test with `curl`:
     ```bash
     curl -X POST https://your-subscriber.com/webhooks/order.created \
       -H "Content-Type: application/json" \
       -d '{"event_id": "...", "data": {...}}' \
       -H "Signature: abc123..."
     ```

2. **Stress Testing**:
   - Simulate high-volume events with tools like [locust](https://locust.io/).
   - Verify retries and rate limits.

3. **Mock Publishers**:
   - Use libraries like [webhooks.io](https://webhooks.io/) for sandbox testing.

---

## **5. Query Examples**
### **5.1. Subscriber: Valid Request**
**Request**:
```http
POST /webhooks/order.created HTTP/1.1
Host: api.yoursubscriber.com
Content-Type: application/json
X-Event-ID: order.created.12345
Signature: abc123...xyz

{
  "event_id": "order.created.12345",
  "event_type": "order.created",
  "data": { ... }
}
```
**Response (Success)**:
```http
HTTP/1.1 200 OK
```

---

### **5.2. Subscriber: Invalid Signature**
**Request** (same as above, but signature is wrong):
```http
Signature: wrong_signature_123...
```
**Response**:
```http
HTTP/1.1 401 Unauthorized
{
  "error": "Invalid signature"
}
```

---

### **5.3. Subscriber: Retry-After Header**
**Request**:
```http
POST /webhooks/payment.processed HTTP/1.1
Host: api.yoursubscriber.com
...
```
**Response (Rate-Limited)**:
```http
HTTP/1.1 429 Too Many Requests
Retry-After: 60
```

---

## **6. Error Handling & Retries**
| Scenario               | Publisher Action                          | Subscriber Action                     |
|-------------------------|------------------------------------------|----------------------------------------|
| `5xx` Error             | Retry exponentially (max 5 attempts).    | Acknowledge with `2xx` status.        |
| `400 Bad Request`       | Stop retries (non-retryable).            | Return details in error payload.       |
| `429 Too Many Requests` | Wait `Retry-After` seconds.               | Throttle or queue requests.             |
| Duplicate Event         | Retry once (if `idempotency_key` differs).| Idempotently process event.           |
| Timeout (`504`)         | Retry with exponential backoff.          | Increase timeout threshold.           |

---

## **7. Related Patterns**
| Pattern                     | Description                                                                 |
|-----------------------------|-----------------------------------------------------------------------------|
| **[Idempotent Operations]**  | Ensures duplicate requests have the same effect (critical for webhooks).   |
| **[Synchronous APIs]**       | Contrasts with webhooks (request-response vs. event-driven).               |
| **[Event Sourcing]**        | Stores state changes as a sequence of events (complements webhooks).       |
| **[CQRS]**                  | Separates read/write models; webhooks feed real-time updates to read models. |
| **[Rate Limiting]**         | Prevents subscriber overload from high-frequency webhooks.                  |
| **[Distributed Locks]**     | Coordinates retries across multiple publisher instances.                    |

---
## **8. Further Reading**
- [RFC 6648](https://tools.ietf.org/html/rfc6648) – Webhook Standard.
- [AWS Webhooks Best Practices](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-webhooks-best-practices.html).
- [Stripe Webhook Signing](https://stripe.com/docs/webhooks/signatures).
- [Kafka vs. Webhooks](https://www.confluent.io/blog/kafka-vs-webhooks/) (when to use each).

---
**Last Updated**: `2023-10-15`
**Feedback**: [Contact Support](#)