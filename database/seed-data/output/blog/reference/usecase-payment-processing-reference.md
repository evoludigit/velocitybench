---
**[Pattern] Payment Processing Patterns – Reference Guide**

---

## **1. Overview**
Payment Processing Patterns define standardized approaches for securely routing, validating, and executing transactions across digital payment systems. This guide covers key patterns for high-volume, low-latency, and high-security payment workflows, including **direct integrations, payment gateways, and asynchronous processing**. These patterns ensure compliance with PCI-DSS, fraud detection, and transaction retry mechanisms for resilience.

---

## **2. Schema Reference**

| **Pattern**               | **Description**                                                                                     | **Key Components**                                                                                     | **Security Considerations**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|
| **Direct API Integration** | Client-to-bank/API connection for real-time processing.                                             | `Merchant → Payment Processor (API)`                                                            | Encrypted tokenization, OAuth 2.0, rate limiting                                                               |
| **Payment Gateway**       | Third-party intermediary for routing, validation, and fraud checks before bank processing.         | `Merchant → Gateway (e.g., Stripe) → Issuer/Bank`                                                 | PCI DSS Level 1 compliance, 3D Secure, CVV hashing                                                          |
| **Asynchronous Queue**    | Offloads transaction processing to a distributed queue (e.g., SQS, Kafka) for delayed validation.  | `Merchant → Queue → Processor → Bank`                                                               | Dead-letter queues, message encryption, idempotency checks                                                   |
| **Pre-Authorization**     | Holds funds temporarily for later settlement (e.g., hotels, subscriptions).                        | `Authorize → Capture (later)`                                                                       | Timeout handling, chargeback thresholds, transaction snapshotting                                            |
| **Dynamic Currency Conversion (DCC)** | Converts currency on-the-fly during checkout for multi-currency merchants.                          | `Merchant → Gateway → FX Provider → Bank`                                                          | Latency-sensitive APIs, exchange rate APIs (e.g., Revolut, Wise)                                             |
| **Subscription Management** | Handles recurring payments with pause/resume/cancel logic.                                        | `Merchant → Processor → Retry Logic → Bank`                                                        | Billing retry policies, failed payment thresholds, trial period handling                                     |
| **Fraud Prevention**       | Integrates ML/rules-based fraud detection (e.g., velocity checks, device fingerprinting).          | `Processor → Fraud API → Decision (Allow/Reject)`                                                  | Real-time API calls, anonymized data sharing, whitelisting/blacklisting                                     |
| **Split Payments**        | Divides a transaction across multiple accounts (e.g., payouts to affiliates).                     | `Merchant → Processor → Payout Routing → Recipients`                                                 | Anti-money laundering (AML) checks, threshold limits                                                          |
| **Challenge Request**     | Requires additional verification (e.g., SMS/email) for high-risk transactions.                    | `Processor → Challenge → User → Reauthenticate → Process`                                          | Timeouts, CAPTCHA integration, fallbacks                                                                     |
| **Micropayments**         | Small-value transactions (e.g., tipping, in-app purchases) with low latency.                       | `Merchant → Processor → Lightweight Protocol (e.g., Lightning Network)`                             | Microtransaction fees, replay attack prevention                                                             |
| **International Payments** | Supports global cards (e.g., SEPA, BACS, UPI) with localized compliance.                          | `Merchant → Gateway → Local Processor → Bank (Country-Specific)`                                  | Localized KYC, currency conversion, tax reporting                                                             |

---

## **3. Query Examples**

### **3.1 Direct API Integration (HTTP POST)**
```http
POST /api/transactions
Headers:
  Authorization: Bearer <token>
  Content-Type: application/json

Body:
{
  "amount": 100.00,
  "currency": "USD",
  "card": {
    "token": "tok_123abc",  // Encrypted via PCI-compliant tokenization
    "type": "visa"
  },
  "metadata": {
    "order_id": "prod-456"
  }
}

Response (Success):
HTTP/2 200 OK
{
  "id": "txn_789def",
  "status": "pending",
  "authorization_code": "A1B2C3D"
}

Response (Error):
HTTP/2 402 PaymentRequired
{
  "error": "fraud_flagged",
  "recommendation": "request_userVerification"
}
```

### **3.2 Payment Gateway (Stripe-like)**
```http
POST /v1/charges
Headers:
  idempotency-key: "txn_123"

Body:
{
  "amount": 1500,
  "currency": "eur",
  "source": "tok_mastercard_123",
  "description": "Order #12345",
  "metadata": {
    "fraud_score": 0.95
  }
}

Response:
HTTP/2 200 OK
{
  "id": "ch_12345abc",
  "status": "succeeded",
  "amount_refunded": 0,
  "created": "2023-10-01T12:00:00Z"
}
```

### **3.3 Asynchronous Queue (SQS Trigger)**
```python
# Pseudocode for SQS Consumer
def process_payment(event):
    for record in event['Records']:
        txn = json.loads(record['body'])
        if txn['status'] == 'pending':
            gateway = PaymentGateway(txn['gateway_token'])
            result = gateway.process(txn)
            if result['status'] == 'approved':
                update_db(txn['id'], 'approved')
            else:
                sqs.send(
                    queue='failures',
                    body=json.dumps(txn)
                )
```

### **3.4 Fraud Detection (Post-Processing)**
```http
POST /api/fraud-check
Headers:
  X-Fraud-Key: <api-key>

Body:
{
  "txn_id": "txn_789def",
  "amount": 5000,
  "ip": "192.0.2.1",
  "device_fingerprint": "abc123..."
}

Response:
HTTP/2 200 OK
{
  "score": 0.87,
  "actions": ["require_3ds", "block"],
  "rules": ["high_value_threshold"]
}
```

---

## **4. Implementation Considerations**

### **4.1 Security**
- **PCI-DSS Compliance**: Never store full PANs; use tokenization.
- **Encryption**: TLS 1.2+ for all APIs; encrypt queues with KMS (AWS, GCP).
- **Rate Limiting**: Enforce `X-Rate-Limit` headers to prevent brute-force attacks.
- **3D Secure**: Enforce for high-risk cards (e.g., SCA compliance in EU).

### **4.2 Idempotency**
- Use `idempotency-key` headers to prevent duplicate processing.
- Example: Stripe’s `idempotency-key` retry mechanism.

### **4.3 Retry Logic**
| **Scenario**               | **Retry Strategy**                                                                 |
|----------------------------|-----------------------------------------------------------------------------------|
| Bank Timeout               | Exponential backoff (max 5 retries, 60s delay).                                    |
| Temporary Network Error     | Circular retry with jitter (avoid thundering herd).                               |
| Permanent Bank Failure      | Route to backup processor (e.g., fallback merchant account).                       |
| Fraud Block                | Manual review + challenge request.                                                 |

### **4.4 Monitoring**
- **Metrics**: Track `txn_latency`, `failure_rate`, `fraud_hits`.
- **Alerts**: Trigger on `failure_rate > 2%` or `latency > 500ms`.
- **Logging**: Store raw txn data (anonymized) for 180 days (GDPR compliance).

---

## **5. Related Patterns**
| **Related Pattern**          | **Purpose**                                                                                     | **When to Use**                                                                                     |
|------------------------------|-------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| **Saga Pattern**             | Distributed transaction coordination (e.g., refunds spanning multiple services).              | Multi-party payments (e.g., escrow, marketplaces).                                               |
| **Circuit Breaker**          | Prevent cascading failures in payment processors.                                              | High-load systems (e.g., Black Friday sales).                                                     |
| **Event Sourcing**           | Audit trail for payment disputes (e.g., chargebacks).                                         | Regulated industries (fintech, crypto).                                                           |
| **API Gateway**              | Centralized routing for payment flows (e.g., routing to Stripe/PayPal).                       | Multi-vendor payment integrations.                                                               |
| **Rate Limiting**            | Throttle transaction volume to prevent abuse.                                                  | Public APIs (e.g., payment links).                                                              |

---

## **6. Example Workflow (Subscription + Fraud Check)**
```
1. Merchant → POST /subscribe (Asynchronous Queue)
   - Body: { "plan": "premium", "card": "tok_123" }
2. SQS → Fraud API (Score: 0.92 → Challenge Required)
   - User verifies via SMS.
3. User Approves → SQS → Payment Processor
   - Processor authorizes $9.99/month (temporary hold).
4. Retry Logic → Calls bank again (success on 2nd attempt).
5. Finalize → POST /subscriptions/{id}/activate
```

---
**See Also**:
- [PCI DSS Payment Tokenization Guide](https://www.pcisecuritystandards.org/)
- [Stripe API Reference](https://stripe.com/docs/api)
- [OWASP Payment Security Controls](https://owasp.org/www-project-payment-card-industry-data-security-standard-controls/)