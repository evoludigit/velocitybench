# **[Pattern] SendGrid Email Integration Patterns – Reference Guide**

---

## **Overview**
SendGrid Email Integration Patterns standardizes how to send, track, and manage emails programmatically via SendGrid’s REST API. This guide covers implementation best practices, common patterns (e.g., batch sending, event-driven workflows, retry logic), and key concepts like API limits, event webhooks, and email metrics.

Key use cases include:
- **Mandatory**: Transactional emails (e.g., password resets, notifications).
- **Optional**: Marketing campaigns, newsletters, or analytics-driven emails.
- **Advanced**: Dynamic content, segmentation, and A/B testing.

This pattern assumes integration with a backend service (Node.js, Python, Java, etc.) and leverages SendGrid’s **v3 API** for reliability. Always comply with [email laws](https://sendgrid.com/legal/email-marketing-compliance/) (e.g., CAN-SPAM, GDPR).

---

## **Core Concepts & Schema Reference**

### **1. Core Object Types**
| **Component**               | **Description**                                                                 | **Required Fields**                                                                 |
|-----------------------------|---------------------------------------------------------------------------------|-------------------------------------------------------------------------------------|
| **Email Send Request**      | Define content and recipients for a single email or batch.                    | `personalizations[].to`, `from.email`, `subject`, `html`, `text`, `reply_to`      |
| **Batch Sending**           | Send emails to multiple recipients efficiently.                               | `batch_id`, `personalizations[].to`, `email` (with `from`, `subject`, etc.)        |
| **Event Webhook**           | Asynchronously receive events (e.g., delivery, bounce, click).                | `endpoints`, `secret` (for verification), `events[].name` (`accepted`, `delivered`, `bounced`) |
| **Webhook Event Data**      | Payload structure for event notifications.                                   | `event`, `event_id`, `email`, `timestamp`, `metadata`                              |
| **API Key**                 | Authentication for API requests.                                             | `api_key` (X-Auth-Token header)                                                     |
| **Email Metrics**           | Track performance via the **SendGrid Metrics API**.                          | `metrics_type` (`clicks`, `opens`, `bounces`, `spam_reports`), `date_range`       |

---

### **2. Key API Endpoints**
| **Endpoint**                     | **Method** | **Purpose**                                                                                     |
|-----------------------------------|------------|-------------------------------------------------------------------------------------------------|
| `/v3/mail/send`                  | POST       | Send a single or batch email.                                                                |
| `/v3/mail/batch`                 | POST       | Queue emails for deferred sending (asynchronous).                                            |
| `/v3/webhooks`                   | POST       | Register/unregister event webhooks.                                                          |
| `/v3/suppression/addresses`      | GET/POST   | Manage blocked/ignored email addresses.                                                      |
| `/metrics/waiting`               | GET        | Check deferred emails in the queue.                                                          |
| `/metrics/delivery`              | GET        | Retrieve delivery status for sent emails.                                                    |

---

## **Implementation Patterns**

### **1. Single Email Send**
**Use Case:** One-time emails (e.g., welcome messages).

#### **Request Example (Node.js)**
```javascript
const sgMail = require('@sendgrid/mail');
sgMail.setApiKey(process.env.SENDGRID_API_KEY);

const msg = {
  to: 'user@example.com',
  from: { email: 'sender@example.com', name: 'Support Team' },
  subject: 'Welcome to Our Platform!',
  text: 'Hello, please verify your email...',
  html: '<strong>Check your inbox!</strong>',
  reply_to: 'support@example.com'
};

sgMail.send(msg)
  .then(() => console.log('Email sent'))
  .catch(error => console.error(error));
```

**Error Handling:**
- **HTTP 429:** Rate limit exceeded. Use exponential backoff (see [Rate Limits](https://docs.sendgrid.com/api-reference/rate-limits)).
- **HTTP 400:** Malformed email. Validate `to`/`from` fields.

---

### **2. Batch Sending**
**Use Case:** Sending identical emails to many recipients (e.g., newsletters).

#### **Request Example**
```javascript
const recipients = [
  { email: 'user1@example.com' },
  { email: 'user2@example.com' }
];

const email = {
  from: { email: 'newsletter@example.com', name: 'Company News' },
  subject: 'Monthly Update',
  html: '<p>Content for all users...</p>',
  personalizations: recipients.map(r => ({ to: [r] }))
};

sgMail.sendMultiple(email)
  .then(response => console.log(`Batch ID: ${response[0].batch_id}`));
```

**Best Practices:**
- Limit batches to **500 recipients per request** (SendGrid’s soft limit).
- Use `waiting` metrics to monitor deferred emails:
  ```javascript
  fetch(`https://api.sendgrid.com/v3/metrics/waiting?batch_id=${BATCH_ID}`)
    .then(res => res.json())
    .then(data => console.log(data.total));
  ```

---

### **3. Event-Driven Workflows (Webhooks)**
**Use Case:** Trigger actions on email events (e.g., retries for failed deliveries).

#### **Webhook Setup**
1. **Register a Webhook:**
   ```javascript
   const webhook = {
     endpoint: 'https://yourapi.com/webhook',
     events: ['accepted', 'delivered', 'bounced'],
     secret: 'YOUR_VERIFICATION_SECRET' // Required for verification
   };

   await fetch('https://api.sendgrid.com/v3/webhooks', {
     method: 'POST',
     headers: { 'Authorization': `Bearer ${sgMail.getApiKey()}` },
     body: JSON.stringify(webhook)
   });
   ```

2. **Verify Webhook Signatures** (Server-side):
   ```python
   from flask import request
   from sendgrid import webhook

   @app.route('/webhook', methods=['POST'])
   def handle_webhook():
       signature = request.headers.get('X-Webhook-Signature')
       if not webhook.verify_signature(request.data, signature, 'YOUR_SECRET'):
           raise Exception("Invalid signature")
       event = request.json
       handle_event(event['event'], event['email'])
   ```

**Event Handling Logic:**
- **`delivery.status == 'delivered`:** Log analytics.
- **`event.type == 'bounced'`:** Add address to suppression list:
  ```javascript
  await fetch(`https://api.sendgrid.com/v3/suppression/addresses`, {
    method: 'POST',
    body: JSON.stringify({ email: 'bounced@example.com' })
  });
  ```

---

### **4. Retry Logic for Failed Emails**
**Use Case:** Resend emails after delays (e.g., for bounces or throttling).

#### **Implementation Steps:**
1. **Poll `waiting` Metrics:**
   ```javascript
   async function checkBatch(batchId) {
     const response = await fetch(`https://api.sendgrid.com/v3/metrics/waiting?batch_id=${batchId}`);
     const data = await response.json();
     if (data.total > 0) {
       await new Promise(resolve => setTimeout(resolve, 60000)); // Delay 1 minute
       return checkBatch(batchId); // Retry
     }
   }
   ```
2. **Resend Failed Emails:**
   ```javascript
   const failedEmails = await getFailedEmailsFromDatabase(); // Custom logic
   await sgMail.sendMultiple({
     to: failedEmails,
     from: { email: 'resend@example.com' },
     subject: 'Resent: Previous Message'
   });
   ```

**Key Parameters:**
| **Action**       | **Delay** | **Max Retries** |
|------------------|-----------|-----------------|
| Initial Send     | 0s        | 1               |
| Delivery Failure | 1min      | 3               |
| Hard Bounce      | 1h        | 1 (suppress)    |

---

### **5. Dynamic Content & Segmentation**
**Use Case:** Personalize emails based on user data (e.g., product recommendations).

#### **Example: Templated Emails**
```javascript
const userData = { name: 'Alice', product: 'Premium Plan' };
const template = `<p>Hello ${userData.name},</p>` +
                 `<p>Here’s your ${userData.product} upgrade!</p>`;

const email = {
  to: 'alice@example.com',
  from: { email: 'promotions@example.com' },
  subject: `Upgrade to ${userData.product}`,
  html: template
};

await sgMail.send(email);
```

**Advanced:** Use **SendGrid’s Webhook Events** to update templates dynamically on user actions (e.g., clicks).

---

## **Query Examples**

### **1. Check Email Delivery Status**
```bash
curl -X GET \
  https://api.sendgrid.com/v3/mail/sent \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "status:delivered", "limit": 100}'
```

**Response:**
```json
{
  "results": [
    {
      "email_id": "d70c83e6-2880-4974-932d-5b44973f064d",
      "status": "delivered",
      "recipients": [{ "email": "user@example.com" }]
    }
  ]
}
```

---

### **2. List Suppressed Addresses**
```bash
curl -X GET \
  https://api.sendgrid.com/v3/suppression/addresses \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Response:**
```json
{
  "results": [
    { "email": "bounced@example.com", "reason": "hard_bounce" }
  ]
}
```

---

### **3. Trigger a Webhook Event (Testing)**
```bash
curl -X POST \
  https://api.sendgrid.com/v3/webhooks/test \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"event": "delivered", "email": { "id": "d70c83e6-2880-4974-932d-5b44973f064d" }}'
```

---

## **Common Pitfalls & Mitigations**

| **Pitfall**                          | **Mitigation**                                                                 |
|--------------------------------------|---------------------------------------------------------------------------------|
| **Rate Limits (429 Errors)**         | Use exponential backoff; monitor with [`metrics/rate_limit`](https://docs.sendgrid.com/api-reference/rate-limits). |
| **Hard Bounces**                     | Automatically suppress addresses; use `suppression/addresses`.                 |
| **Unverified Webhooks**              | Always verify signatures on the server.                                       |
| **Large Batches (>500 Recipients)**   | Split batches or use [`batch` endpoint](https://docs.sendgrid.com/api-reference/mail-send-batch). |
| **Missing Reply-To**                 | Required for compliance; default to `support@example.com`.                     |

---

## **Related Patterns**
1. **[Authentication] OAuth 2.0 for SendGrid**
   - Use OAuth instead of API keys for multi-tenant applications.
   - [SendGrid OAuth Docs](https://docs.sendgrid.com/api-reference/authentication/oauth-2-0).

2. **[Event-Driven Architecture] Kafka/SNS Integration**
   - Stream email events to Kafka or AWS SNS for complex processing.
   - Example: Trigger Slack alerts on bounces.

3. **[Data Storage] Database Schema for Email Tracking**
   - Schema for logging sent emails, metrics, and user preferences.
   - Example:
     ```sql
     CREATE TABLE email_events (
       event_id VARCHAR(36) PRIMARY KEY,
       email_id VARCHAR(36),
       event_type VARCHAR(50), -- 'delivered', 'bounced', etc.
       timestamp TIMESTAMP,
       metadata JSONB
     );
     ```

4. **[Security] Email Content Sanitization**
   - Avoid XSS by sanitizing HTML content (use [DOMPurify](https://github.com/cure53/DOMPurify)).

5. **[Analytics] SendGrid Metrics + Custom Dashboards**
   - Integrate SendGrid’s metrics with tools like Grafana or Power BI.
   - Key metrics: `opens`, `clicks`, `unsubscribes`, `spam_reports`.

---

## **Further Reading**
- [SendGrid API Reference](https://docs.sendgrid.com/api-reference)
- [Webhook Events Documentation](https://docs.sendgrid.com/api-reference/webhooks)
- [Compliance Guide](https://sendgrid.com/legal/email-marketing-compliance)
- [Rate Limit Management](https://docs.sendgrid.com/api-reference/rate-limits)