# **[Pattern] Webhooks & Real-time Notifications – Reference Guide**

---

## **1. Overview**
Webhooks & Real-time Notifications enable your application to **asynchronously push event data** to external systems (e.g., payment processors, CRM tools, or mobile apps) without polling. This pattern optimizes performance, reduces latency, and ensures critical updates are delivered instantly. Unlike REST APIs (which rely on client requests), webhooks are **event-driven**, triggering payloads when predefined actions occur (e.g., order created, user logged in).

Key benefits:
- **Low-latency updates** (no polling delays).
- **Decoupled architecture** (services communicate independently).
- **Scalability** (handled via HTTP/HTTPS with retries and idempotency).
- **Cost-efficient** (unlike WebSockets, which require persistent connections).

This guide covers **implementation best practices**, schema standards, error handling, and integration with popular services (e.g., Stripe, Slack, Kafka).

---

## **2. Key Concepts**

| **Concept**               | **Description**                                                                 | **Example Use Case**                          |
|---------------------------|-------------------------------------------------------------------------------|-----------------------------------------------|
| **Webhook Endpoint**      | A secure HTTP(S) URL where your system listens for inbound requests.          | `/api/webhooks/payments` (Stripe webhook URL) |
| **Payload**               | Structured JSON data sent with the event (e.g., order status, user actions).   | `{ "event": "order_created", "id": "123" }`     |
| **Signature Verification**| Ensures payloads are from a trusted source (HMAC/SHA-256).                     | Verify `X-Signature` header.                 |
| **Retry Mechanism**       | Automatic re-delivery of failed webhooks (with exponential backoff).          | Retry after 5s, 10s, 30s.                    |
| **Idempotency**           | Prevents duplicate processing of the same event (via `id` or unique tokens).  | `idempotency_key: "order_123"`                |
| **Event Types**           | Predefined actions triggering webhooks (e.g., `user.created`, `payment.failed`).| Slack `message.edited` event.                 |
| **Rate Limiting**         | Throttles incoming requests to prevent abuse (e.g., 100 requests/minute).     | Nginx `limit_req_zone`.                     |
| **Dead Letter Queue (DLQ)**| Stores failed webhooks for manual inspection (e.g., via Kafka/SQS).          | Log failed `payment.chargeback` events.       |

---

## **3. Schema Reference**

### **3.1. Core Webhook Payload Structure**
All webhooks must conform to this JSON schema (Mandatory fields in **bold**):

| **Field**               | **Type**   | **Description**                                                                 | **Example Value**                     |
|-------------------------|------------|-------------------------------------------------------------------------------|---------------------------------------|
| **`id`**                | `string`   | **Unique event identifier** (for deduplication).                              | `"evt_abc123"`                        |
| **`type`**              | `string`   | **Event type** (e.g., `order.created`, `user.deleted`).                      | `"payment.chargeback"`                |
| **`created_at`**        | `datetime` | **Timestamp of event occurrence** (ISO 8601 format).                          | `"2024-05-20T14:30:00Z"`              |
| **`data`**              | `object`   | **Event-specific payload** (schema varies by event type).                     | `{ "amount": 99.99, "currency": "USD" }` |
| **`metadata`**          | `object`   | **Optional key-value pairs** for custom attributes.                            | `{ "source": "web", "user_id": "456" }` |
| **`signature`**         | `string`   | **HMAC signature** (for verification; omitted if not used).                 | `"d41d8cd9..."`                       |

---

### **3.2. Example Event Schemas**
#### **Payment Success (Stripe-like)**
```json
{
  "id": "evt_pay_789",
  "type": "payment.succeeded",
  "created_at": "2024-05-20T14:30:00Z",
  "data": {
    "transaction_id": "txn_456",
    "amount": 99.99,
    "currency": "USD",
    "customer_id": "cust_123"
  }
}
```

#### **User Login (Custom App)**
```json
{
  "id": "evt_user_login_101",
  "type": "user.login",
  "created_at": "2024-05-20T15:15:00Z",
  "data": {
    "user_id": "usr_42",
    "ip_address": "192.168.1.1",
    "device": "mobile"
  }
}
```

---

## **4. Implementation Steps**

### **4.1. Setting Up a Webhook Endpoint**
1. **Choose a Framework**:
   - **Node.js**: Express.js (`express.json()` middleware).
   - **Python**: Flask (`@app.route('/webhook', methods=['POST'])`).
   - **Java**: Spring Boot (`@PostMapping("/webhook")`).

2. **Secure the Endpoint**:
   - Use HTTPS (TLS 1.2+).
   - Restrict access via **IP whitelisting** or OAuth.
   - Validate `Content-Type: application/json`.

3. **Verify Payload**:
   ```javascript
   // Node.js Example (Stripe-style signature check)
   const crypto = require('crypto');
   const rawBody = req.rawBody; // Requires `express-raw`
   const signature = req.headers['stripe-signature'];

   const hmac = crypto.createHmac('sha256', process.env.STRIPE_SECRET_KEY);
   const digest = `sha256=${hmac.update(rawBody).digest('hex')}`;

   if (signature !== digest) throw new Error('Invalid signature');
   ```

4. **Process the Event**:
   - Route to a handler based on `event.type`.
   - Apply **idempotency checks** (e.g., database lookup by `event.id`).

---

### **4.2. Handling Retries and Failures**
- **Exponential Backoff**: Retry with delays (e.g., 1s, 2s, 4s).
- **Dead Letter Queue (DLQ)**: Store failed events for later inspection.
  ```python
  # Python (using SQS)
  import boto3
  dlq = boto3.client('sqs')
  dlq.send_message(
      QueueUrl='arn:aws:sqs:us-east-1:123456789:failed-webhooks',
      MessageBody=json.dumps(event)
  )
  ```

---

### **4.3. Broadcasting to Multiple Services**
Use a **message broker** (e.g., Kafka, RabbitMQ) to fan-out events:
1. Your app publishes events to a topic (e.g., `user_events`).
2. Consumers (Slack, Email Service) subscribe to topics of interest.

**Kafka Example (Node.js)**:
```javascript
const { Kafka } = require('kafkajs');
const kafka = new Kafka({ brokers: ['localhost:9092'] });
const producer = kafka.producer();

await producer.connect();
await producer.send({
  topic: 'user_events',
  messages: [{ value: JSON.stringify(event) }],
});
```

---

## **5. Query Examples**

### **5.1. Testing a Webhook Locally**
Use tools like:
- **ngrok**: Expose local dev endpoint (`ngrok http 3000`).
- **Postman/Newman**: Send mock payloads to your endpoint.

**Postman Request**:
```
POST https://your-app.ngrok.io/webhook
Content-Type: application/json

{
  "id": "test_evt",
  "type": "test.event",
  "data": { "message": "Hello!" }
}
```

---

### **5.2. Filtering Webhook Events**
**SQL Query (PostgreSQL)**:
```sql
-- Find failed webhook attempts
SELECT * FROM webhook_attempts
WHERE status = 'failed'
  AND retries < 3
  AND created_at > NOW() - INTERVAL '1 hour';
```

**Kafka Consumer (Python)**:
```python
from kafka import KafkaConsumer

consumer = KafkaConsumer(
    'failed_webhooks',
    bootstrap_servers=['localhost:9092'],
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

for msg in consumer:
    print(f"Failed event: {msg.value}")
```

---

## **6. Error Handling**
| **Error**               | **Cause**                          | **Solution**                                |
|-------------------------|------------------------------------|---------------------------------------------|
| **Signature Mismatch**  | Invalid HMAC or missing key.       | Verify `X-Signature` header.                |
| **Duplicate Events**    | Retry without idempotency.          | Store `event.id` in a DB with `UNIQUE` key. |
| **Rate Limit Exceeded** | Too many requests.                 | Implement backoff or upgrade tier.          |
| **Payload Validation**  | Invalid JSON schema.               | Use `Ajv` (JavaScript) or `Marshmallow` (Python). |
| **Network Timeout**     | External service unavailable.      | Retry with exponential backoff.             |

---

## **7. Related Patterns**
| **Pattern**                     | **Description**                                                                 | **When to Use**                                  |
|----------------------------------|-------------------------------------------------------------------------------|--------------------------------------------------|
| **[Event Sourcing](https://en.wikipedia.org/wiki/Event_sourcing)** | Store state changes as immutable events.                                        | Audit logs, financial transactions.              |
| **[CQRS](https://martinfowler.com/bliki/CQRS.html)** | Separate read/write models for scalability.                                   | High-traffic apps needing real-time updates.    |
| **[Saga Pattern](https://microservices.io/patterns/data/saga.html)** | Manage distributed transactions via choreography.                           | Microservices with ACID compliance.             |
| **[Long Polling](https://en.wikipedia.org/wiki/Polling_(computer_science))** | Alternative to webhooks for synchronous updates.                              | Legacy systems unable to use async.             |
| **[Server-Sent Events (SSE)](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)** | Real-time updates via HTTP streaming.                                         | Browser-based dashboards.                       |

---

## **8. Tools & Libraries**
| **Tool/Library**       | **Purpose**                                      | **Languages**               |
|------------------------|--------------------------------------------------|-----------------------------|
| **Stripe Webhooks**    | Pre-built webhook infrastructure.                | All                         |
| **Kafka**             | Distributed event streaming.                    | Java, Python, Node.js       |
| **Webhook.io**        | Managed webhook testing/forwarding.              | API-based                   |
| **Express-raw**       | Parse raw HTTP request bodies (Node.js).         | JavaScript                  |
| **Postman Collections**| Test webhook payloads.                          | All                         |

---

## **9. Troubleshooting Checklist**
1. **Endpoint Accessible?**
   - Test with `curl -v https://your-endpoint`.
2. **Signature Valid?**
   - Recompute HMAC locally and compare.
3. **Rate Limits Hit?**
   - Check logs for `429 Too Many Requests`.
4. **Schema Mismatch?**
   - Validate payloads with `json-schema-validator`.
5. **DLQ Empty?**
   - Query your message broker for failed events.

---
**See Also**:
- [Stripe Webhook Docs](https://stripe.com/docs/webhooks)
- [Slack Incoming Webhooks](https://api.slack.com/messaging/webhooks)
- [Kafka Webhooks Guide](https://kafka.apache.org/documentation/#webhooks)