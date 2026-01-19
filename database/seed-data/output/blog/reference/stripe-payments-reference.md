---

# **[Pattern] Stripe Payments Integration Patterns Reference Guide**

## **Overview**
This guide outlines **Stripe Payments Integration Patterns**, providing structured approaches for securely and efficiently implementing Stripe’s payment processing into applications. The patterns cover **transaction flows, error handling, testing, and compliance**, ensuring scalability and reliability. Whether handling one-time payments, subscriptions, or fraud mitigation, this reference helps developers implement best practices while avoiding common pitfalls.

---

## **1. Key Integration Patterns**

### **1.1 Core Payment Flow Patterns**
Stripe supports multiple payment flows based on business needs:

| **Pattern**               | **Use Case**                                                                 | **Key API/Endpoint**                     |
|---------------------------|------------------------------------------------------------------------------|------------------------------------------|
| **Checkout Session**      | Hosted payment pages (e.g., custom UI, third-party integrations).          | `checkout.sessions.create`              |
| ** PaymentIntents**       | Server-side payment handling (e.g., mobile apps, custom frontend).          | `payment_intents.create`                |
| **PaymentLinks**          | Pre-built shareable payment links (e.g., invoices, donation buttons).       | `payment_links.create`                  |
| **Subscription Management** | Recurring billing (e.g., SaaS, memberships).                          | `subscriptions.create`, `canceled` calls |
| **Radar (Fraud Detection)** | Fraud risk assessment for high-value transactions.                     | `radar.values.create`                   |
| **Invoicing**             | Automated billing for customers (e.g., monthly subscriptions).              | `invoices.create`                       |

---

### **1.2 Offline & Sync Patterns**
For systems requiring periodic syncs or offline processing:

| **Pattern**               | **Description**                                                                 | **Implementation Note**                          |
|---------------------------|------------------------------------------------------------------------------|--------------------------------------------------|
| **Webhooks + Buffering**  | Process webhooks asynchronously (e.g., retry failed calls).                | Use `events.list` to fetch historical events.   |
| **Batch Processing**      | Group transactions (e.g., reconcile daily transactions).                   | Call `payment_intents.list` with `created:gt` filter. |
| **Local Cache + Sync**    | Store payment status locally (e.g., mobile apps) and sync later.           | Use `payment_intents.retrieve` for updates.     |

---

### **1.3 Fraud & Risk Management**
Stripe’s **Radar** and **3D Secure** patterns help mitigate fraud:

| **Pattern**               | **Description**                                                                 | **Key API**                                  |
|---------------------------|------------------------------------------------------------------------------|---------------------------------------------|
| **Radar Rules**          | Apply custom risk rules (e.g., block high-value transactions from high-risk countries). | `radar.rules.create` |
| **3D Secure (SCA)**       | Enforce Strong Customer Authentication (EUR/SEPA compliance).             | Auto-triggered via `PaymentIntent` flow.   |
| **Device Fingerprinting** | Detect bot traffic using device/behavioral data.                          | Radar’s `device_presence` flag.            |

---

## **2. Schema Reference**
### **2.1 PaymentIntent Schema**
| Field                  | Type      | Required | Description                                                                 |
|------------------------|-----------|----------|-----------------------------------------------------------------------------|
| `id`                   | string    | Yes      | Unique Stripe-generated identifier.                                          |
| `amount`               | integer   | Yes      | Amount in smallest currency unit (e.g., `$10 = 1000` for USD).               |
| `currency`             | string    | Yes      | 3-letter ISO code (e.g., `usd`, `eur`).                                     |
| `payment_method_types` | array     | Yes      | Supported methods (e.g., `['card']`, `['sepa_debit']`).                     |
| `confirm`              | boolean   | No       | Immediately confirm if `true` (risk of declined cards).                     |
| `transfer_data`        | object    | No       | Configure payouts to connected accounts (e.g., `destination: 'acct_123'`).  |
| `metadata`             | object    | No       | Custom key-value pairs (e.g., `{"order_id": "123"}`).                       |

**Example Request (Create PaymentIntent):**
```json
{
  "amount": 1000,
  "currency": "usd",
  "payment_method_types": ["card"],
  "confirm": true,
  "metadata": {"order_id": "456"}
}
```

---

### **2.2 Subscription Schema**
| Field                  | Type      | Required | Description                                                                 |
|------------------------|-----------|----------|-----------------------------------------------------------------------------|
| `id`                   | string    | Yes      | Stripe subscription ID.                                                     |
| `status`               | string    | No       | `active`, `past_due`, `cancelled`, etc.                                     |
| `current_period_end`   | timestamp | No       | Next billing cycle end date (ISO format).                                  |
| `customer`             | string    | Yes      | Linked customer ID (e.g., `cus_123`).                                     |
| `items`                | array     | Yes      | List of subscription items (price IDs).                                    |
| `default_payment_method`| string    | No       | Default card/payment method (e.g., `pm_123`).                              |

**Example Request (Create Subscription):**
```json
{
  "customer": "cus_abc123",
  "items": [
    {"price": "price_123"}
  ],
  "expand": ["latest_invoice.payment_intent"]
}
```

---

## **3. Query Examples**

### **3.1 List PaymentIntents (Paginated)**
```bash
curl https://api.stripe.com/v1/payment_intents \
  -H "Authorization: Bearer sk_test_..." \
  -H "Stripe-Version: 2023-10-16" \
  -G \
  --data-urlencode "status=requires_payment_method" \
  --data-urlencode "limit=5"
```

**Response Snippet:**
```json
{
  "data": [
    {
      "id": "pi_3Jy958...",
      "status": "requires_payment_method",
      "amount": 1000,
      "currency": "usd"
    }
  ],
  "has_more": true,
  "url": "/v1/payment_intents?limit=5&starting_after=pi_3Jy958..."
}
```

---

### **3.2 Cancel a Subscription**
```bash
curl https://api.stripe.com/v1/subscriptions/sub_abc123 \
  -X POST \
  -H "Authorization: Bearer sk_test_..." \
  -H "Stripe-Version: 2023-10-16" \
  -d '{"cancel_at_period_end": false}'
```

---

### **3.3 Fetch Events (Webhook Retries)**
```bash
curl https://api.stripe.com/v1/events \
  -H "Authorization: Bearer sk_test_..." \
  -H "Stripe-Version: 2023-10-16" \
  --data-urlencode "type=payment_intent.succeeded" \
  --data-urlencode "auto_paging=true"
```

---

## **4. Best Practices**
### **4.1 Error Handling**
- **Retry failed `PaymentIntents`**:
  Use exponential backoff for transient errors (e.g., `422` for validation).
  Example:
  ```python
  from time import sleep
  import stripe

  stripe.api_key = "sk_test_..."
  intent = stripe.PaymentIntent.retrieve("pi_3Jy958...")
  if intent.status == "requires_payment_method":
      sleep(2)  # Retry logic
  ```
- **Validate webhook signatures**:
  Always verify `Stripe-Signature` header to prevent spoofing.

### **4.2 Testing**
- **Test Modes**:
  Use `test_*` keys (e.g., `pk_test_`) and test cards (e.g., `4242 4242 4242 4242`).
- **Mock Webhooks**:
  Test event handling locally with tools like [Stripe CLI](https://github.com/stripe/stripe-cli).

### **4.3 Compliance**
- **PCI DSS**:
  Never store raw card data. Use Stripe Elements or PaymentIntents for tokenization.
- **GDPR**:
  Mask PII in logs (e.g., `customer.email` → `customer.email: ****@example.com`).

---

## **5. Common Pitfalls & Solutions**
| **Pitfall**                                  | **Solution**                                                                 |
|----------------------------------------------|------------------------------------------------------------------------------|
| **Declined cards due to `confirm: true`**    | Set `confirm: false` and handle `requires_action` manually.                  |
| **Race conditions during subscriptions**    | Use `payment_intent` + `subscription` flow with `expand: ["latest_invoice.payment_intent"]`. |
| **Unreliable webhook delivery**             | Implement a dead-letter queue for failed webhooks.                          |
| **High Latency in high-volume regions**     | Use Stripe’s regional endpoints (e.g., `api.stripe.com/v1` vs. `api.eu-stripe.com/v1`). |

---

## **6. Related Patterns**
1. **[Stripe Connect for Marketplaces]** – Enable payouts to sellers via Stripe Connect.
2. **[Idempotency Keys]** – Prevent duplicate payments by using idempotency keys in requests.
3. **[Stripe Billing for Subscriptions]** – Advanced pricing tiers and promo codes.
4. **[Stripe Radar for Fraud]** – Customize fraud rules and blacklists.
5. **[Offline Payments]** – Process payments when no internet is available (e.g., mobile apps).

---
**References:**
- [Stripe API Docs](https://stripe.com/docs/api)
- [PaymentIntent Documentation](https://stripe.com/docs/payments/payment-intents)
- [Webhook Best Practices](https://stripe.com/docs/webhooks/best-practices)