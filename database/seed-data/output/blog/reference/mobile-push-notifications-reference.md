**[Design Pattern] Push Notifications Patterns – Reference Guide**

---

### **Overview**
Push Notifications Patterns standardize how applications deliver real-time alerts (e.g., updates, alerts, or events) to users' devices via APIs like **FCM (Firebase Cloud Messaging)**, **APNs (Apple Push Notification Service)**, or third-party platforms. This guide covers common patterns for sending, managing, and optimizing push notifications with extensibility for future use cases.

Key considerations:
- **Latency**: Ensure near-instant delivery (millisecond/second-level).
- **Targeting**: Granular audience segmentation (user traits, device state).
- **Payload**: Structured data payloads (JSON) for customization.
- **Compliance**: GDPR/CCPA adherence for consent management.
- **Scalability**: Handled via backend services (e.g., microservices) or managed APIs.

---

### **Core Patterns**

#### **1. Unicast Push**
Sends a notification to a **single user/device**.

| **Field**           | **Description**                                                                 | **Example Value**                     |
|---------------------|-------------------------------------------------------------------------------|----------------------------------------|
| `token`             | Device push token (FCM/APNs identifier)                                       | `"abc123..."`                         |
| `headers`           | Optional metadata (e.g., `priority`, `collapse_key`).                          | `{ "priority": "high" }`              |
| `payload`           | User-defined key-value data (max 4KB).                                         | `{ "title": "New Message", "badge": 1 }`|
| `data` (optional)   | JSON payload for deep linking or custom actions.                               | `{ "action": "open_chat", "uid": 123 }`|

**Use Case**: One-on-one alerts (e.g., direct messages, reminders).

---

#### **2. Multicast Push**
Broadcasts to **multiple devices** (filtered via criteria like tags/attributes).

| **Field**           | **Description**                                                                 |
|---------------------|-------------------------------------------------------------------------------|
| `registration_tokens`| Array of device tokens (FCM/APNs).                                             |
| `conditions`        | Optional filters (e.g., `"tags": ["premium_users", "ios"]`).                   |
| `data`              | Payload with optional dynamic templates.                                       |

**Use Case**: Marketing campaigns, system-wide updates.

---

#### **3. Topic-Based Push**
Subscribes devices to **themes/topics** (e.g., `"news_breaking"`, `"sales"`), enabling granular targeting.

| **Operation**       | **Request**                                                                   | **Response**                          |
|---------------------|-------------------------------------------------------------------------------|----------------------------------------|
| Subscribe Topic     | `POST /v1/subscriptions` with `{ "topic": "news_breaking", "token": "..." }` | `{"status": "subscribed"}`             |
| Unsubscribe Topic   | `DELETE /v1/subscriptions` with same payload.                                 | `{"status": "unsubscribed"}`          |

**Use Case**: Users opt-in to interests (e.g., sports, tech).

---

#### **4. Dynamic Payload Pattern**
Generates **customized content** per user (e.g., personalized offers).

```json
{
  "android": {
    "notification": {
      "title": "{{user_name}}'s Birthday!",
      "body": "Enjoy 10% off your next order."
    }
  },
  "data": {
    "offer_id": "{{offer_id}}",
    "template_id": "birthday_discount"
  }
}
```
**Tools**: Use templating engines (e.g., Handlebars) or backend logic to inject variables.

---

#### **5. Exponential Backoff Retry**
Handles transient failures (e.g., network latency) with retries:

1. **First Attempt**: Immediate send.
2. **Subsequent Attempts**: Delay grows exponentially (e.g., 1s → 2s → 4s).

**Use Case**: Unreliable networks or server overloads.

---

#### **6. A/B Testing Pattern**
Tests **notification variants** (e.g., subject lines, CTAs) for engagement.

| **Metric**          | **Tracking**                                                                 |
|---------------------|-------------------------------------------------------------------------------|
| `click_rate`        | `% of users opening → clicking link`.                                         |
| `opt_out_rate`      | `% unsubscribing after notification`.                                         |
| `revenue_impact`    | Revenue per test variant (if applicable).                                     |

**Tools**: Analytics tools (e.g., Mixpanel, GA4) + push notification SDKs.

---

#### **7. Batch Processing**
Groups notifications to **reduce costs** (e.g., per-hour batches) and improve scalability.

**Example Batch Request**:
```json
{
  "tokens": ["token1", "token2", "token3"],
  "payload": { "title": "Daily Digest", "body": "Your updates are here." },
  "schedule": "2024-05-20T18:00:00Z"
}
```
**Constraint**: Ensure payloads are identical; use dynamic payloads for variation.

---

#### **8. In-App Fallback**
If push fails (e.g., user offline), **fallback to in-app notifications** with:
```json
{
  "fallback": {
    "message": "We tried to notify you via push but sent this instead.",
    "action": "check_notifications"
  }
}
```

---

### **Schema Reference**
Below are standardized schemas for common patterns. Adjust fields as needed for your platform (FCM/APNs/third-party).

| **Pattern**               | **Request Schema**                                                                 | **Response Schema**                                |
|---------------------------|-----------------------------------------------------------------------------------|----------------------------------------------------|
| **Unicast**               | `{ "token": string, "payload": object, "headers": object }`                      | `{ "status": "sent" \| "failed", "id": string }`   |
| **Multicast**             | `{ "tokens": string[], "conditions": object, "payload": object }`                | Array of `{ "token": string, "status": string }`    |
| **Topic-Based**           | `{ "topic": string, "token": string }` (subscribe/unsubscribe)                   | `{ "status": "subscribed" \| "unsubscribed" }`     |
| **Dynamic Payload**       | `{ "template": string, "vars": {key: value}, "user_id": string }`                | `{ "rendered_payload": object }`                   |
| **Exponential Backoff**   | Same as Unicast, with `retry_policy: { max_attempts: number, delay_factor: number }` | Logs retry attempts in monitoring system.          |
| **A/B Testing**           | `{ "test_group": string, "variants": [{ "payload": object, "weight": number }] }` | `{ "test_id": string, "results": array }`         |
| **Batch Processing**      | `{ "tokens": string[], "payload": object, "schedule": string }`                   | `{ "batch_id": string, "sent_count": number }`      |

---

### **Query Examples**
#### **1. Subscribe to a Topic (FCM)**
```bash
curl -X POST "https://fcm.googleapis.com/v1/projects/my-project/messages:send" \
  -H "Authorization: Bearer AA..." \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "topic": "news_breaking",
      "apns": { "payload": { "aps": { "alert": "New breaking news!" } } }
    }
  }'
```

#### **2. Send Multicast with Conditions (APNs)**
```bash
curl -X POST "https://api.push.apple.com/3/device/<token>" \
  -H "apns-topic: com.example.app" \
  -H "apns-devtoken: <authorization-token>" \
  -d '{
    "aps": { "alert": "Hello!", "badge": 1 },
    "tags": ["premium_users", "ios"]
  }'
```

#### **3. Batch Send with Exponential Backoff (Custom API)**
```http
POST /v1/push/batch
Headers:
  X-Retry-Policy: "max_attempts=3,delay_factor=2"

Body:
{
  "tokens": ["abc123", "def456"],
  "payload": { "title": "Batch Alert", "body": "Processed at ${timestamp}" },
  "schedule": "now"
}
```

---

### **Implementation Best Practices**
1. **Token Management**:
   - Regenerate tokens periodically (e.g., when OS updates).
   - Batch token updates via APIs like `POST /v1/tokens/refresh`.

2. **Payload Optimization**:
   - Keep payloads <4KB (FCM limit).
   - Use `data` fields for deep linking; reserve `notification` fields for user-facing content.

3. **Analytics Integration**:
   - Track `open_rate`, `click_rate`, and `conversion_rate` via backend logs.
   - Example:
     ```sql
     INSERT INTO push_events (user_id, event_type, timestamp)
     VALUES (123, 'notification_opened', NOW());
     ```

4. **Privacy Compliance**:
   - Store tokens encrypted (e.g., AES-256).
   - Allow users to revoke tokens via `DELETE /v1/subscriptions/<token>`.

5. **Testing**:
   - Use **mock endpoints** (e.g., Postman) to simulate push delivery.
   - Test on both iOS/Android emulators.

---

### **Error Handling**
| **Error Code** | **Description**                          | **Resolution**                                  |
|----------------|------------------------------------------|------------------------------------------------|
| `400 Bad Request` | Invalid payload/token format.           | Validate schema before sending.                |
| `401 Unauthorized` | Missing/invalid auth token.              | Regenerate API key or check permissions.       |
| `429 Too Many Requests` | Rate limit exceeded.                     | Implement exponential backoff.                 |
| `503 Service Unavailable` | Platform downtime.                      | Retry with jitter (random delay).              |

---

### **Related Patterns**
1. **[Event-Driven Architecture]**
   Use pub/sub systems (e.g., Kafka) to decouple notification triggers (e.g., "order_delivered") from delivery.

2. **[Feature Flags]**
   Enable/disable push notifications dynamically (e.g., for A/B tests) via feature toggles.

3. **[User Segmentation]**
   Combine with segmentation services (e.g., Segment, Amplitude) to target users based on behavior.

4. **[Rate Limiting]**
   Implement at the API gateway to prevent abuse (e.g., 100 requests/minute per user).

5. **[Webhooks for Confirmation]**
   Use webhooks (e.g., `notification_delivered`) to confirm successful push delivery.

6. **[Progressive Delivery]**
   Gradually roll out notifications to a subset of users (e.g., 10%) to monitor impact.

---
### **Tools & Libraries**
| **Tool**          | **Purpose**                                                                 |
|-------------------|-----------------------------------------------------------------------------|
| Firebase Cloud Messaging (FCM) | Managed push service for Android/iOS.                                      |
| OneSignal         | Unified platform for web/mobile/email pushes.                              |
| Braze             | Advanced customer messaging with A/B testing.                               |
| Pushover          | Simple API for alerts (e.g., servers).                                       |
| Custom Backend (Node.js/Python) | For full control over notification logic.                                  |

---
**Note**: Always refer to the [FCM documentation](https://firebase.google.com/docs/cloud-messaging) or platform-specific guides for updates.