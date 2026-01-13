**[Pattern] Fintech Domain Patterns – Reference Guide**

---

### **Overview**
The **Fintech Domain Patterns** reference guide provides a structured framework for modeling and implementing domain-specific abstractions in financial technology applications. These patterns address common challenges—such as payment processing, account management, regulatory compliance, and data privacy—while ensuring scalability, modularity, and compliance with financial standards (e.g., SWIFT, ISO 20022, PSD2). This guide covers implementation strategies, schema design, query patterns, and anti-patterns to help developers build robust fintech solutions.

---

### **Core Concepts**
Fintech domain patterns group reusable abstractions into logical domains (e.g., **Payments**, **Accounts**, **Compliance**) to reduce duplication and improve maintainability. Key principles include:
- **Domain Separation**: Clear boundaries between financial entities (e.g., a `Payment` domain distinct from a `Transaction` domain).
- **Event-Driven Workflows**: Use of domain events (e.g., `PaymentInititated`, `AccountCreated`) for asynchronous processing.
- **Idempotency & Retry Logic**: Handling duplicate requests in payment/transfer systems.
- **Regulatory Compliance**: Embedding checks (e.g., KYC/AML) in domain logic.

---

### **Schema Reference**
Below are schema tables for core fintech domains. Use these as blueprints for your database/API schemas.

#### **1. Payments Domain**
| Field               | Type          | Description                                                                 | Example Values                     |
|---------------------|---------------|-----------------------------------------------------------------------------|------------------------------------|
| `paymentId`         | UUID          | Unique identifier for a payment request.                                     | `a1b2c3d4-5678-90ef-...`           |
| `status`            | ENUM          | Current state (`PENDING`, `APPROVED`, `FAILED`, `REVERSED`).              | `APPROVED`                         |
| `amount`            | DECIMAL(18,2) | Transaction amount in the smallest currency unit (e.g., cents/pence).     | `1250` (€12.50)                    |
| `currency`          | ISO-4217      | ISO currency code (e.g., `EUR`, `USD`).                                     | `USD`                              |
| `initiator`         | JSON          | Merchant/client details (name, ID, consumer key).                          | `{"type":"MERCHANT", "id":"M123"}` |
| `beneficiary`       | JSON          | Recipient details (account number, IBAN, SWIFT code).                        | `{"iban":"DE89370400440532013000"}`|
| `paymentMethod`     | ENUM          | Supported methods (`SEPA`, `CARD`, `BANK_TRANSFER`, `CRYPTO`).              | `SEPA`                             |
| `processingDate`    | DATETIME      | Scheduled execution time (or `NULL` for immediate).                        | `2024-12-01T14:30:00`              |
| `reference`         | VARCHAR       | External reference (e.g., invoice ID) for reconciliation.                  | `INV-2024-001`                     |
| `idempotencyKey`    | UUID          | Ensures deduplication for retry scenarios.                                 | `d1e2f3g4-...`                     |
| `metadata`          | JSON          | Extended attributes (e.g., `taxId`, ` settlementBank`).                   | `{"taxId":"123456789"}`            |

**Example Query (Find Approved Payments):**
```sql
SELECT *
FROM payments
WHERE status = 'APPROVED'
  AND processingDate >= CURRENT_DATE
  AND amount > 1000;
```

---

#### **2. Accounts Domain**
| Field               | Type          | Description                                                                 | Example Values                     |
|---------------------|---------------|-----------------------------------------------------------------------------|------------------------------------|
| `accountId`         | UUID          | Unique identifier.                                                         | `1b2c3d4-5678-90ef-...`            |
| `ownerId`           | UUID          | Reference to user/account holder.                                           | `user:987654321`                   |
| `iban`              | VARCHAR       | International Bank Account Number (optional for virtual accounts).         | `GB29NWBK60161331926819`           |
| `accountType`       | ENUM          | Classification (`SAVINGS`, `CHECKING`, `LOAN`, `CRYPTO_WALLET`).            | `CHECKING`                         |
| `balance`           | DECIMAL(18,2) | Current available balance.                                                 | `5234.56`                          |
| `currency`          | ISO-4217      | Base currency.                                                              | `EUR`                              |
| `status`            | ENUM          | State (`ACTIVE`, `FROZEN`, `CLOSED`, `PENDING_VERIFICATION`).            | `ACTIVE`                           |
| `openingDate`       | DATE          | Date the account was opened.                                               | `2023-05-15`                       |
| `lastActivity`      | DATETIME      | Timestamp of the most recent transaction.                                  | `2024-06-20T09:45:00`              |
| `complianceFlags`   | JSON          | Regulatory flags (e.g., `{"kyc_verified":true}`).                          | `{"aml_check_passed":false}`       |

**Example Query (List Frozen Accounts):**
```sql
SELECT accountId, ownerId, iban, balance, status
FROM accounts
WHERE status = 'FROZEN'
  AND created_at > '2024-01-01';
```

---

#### **3. Compliance Domain**
| Field               | Type          | Description                                                                 | Example Values                     |
|---------------------|---------------|-----------------------------------------------------------------------------|------------------------------------|
| `complianceId`      | UUID          | Unique identifier.                                                         | `5e6f7g8h-...`                     |
| `ruleId`            | VARCHAR       | Reference to a compliance rule (e.g., `AML_Rule_001`).                    | `KYC_Verification_2024`            |
| `entityType`        | ENUM          | Scope (`PAYMENT`, `ACCOUNT`, `USER`).                                      | `USER`                             |
| `entityId`          | VARCHAR       | Linked entity ID (e.g., `payment:a1b2`, `user:987`).                       | `user:654321`                      |
| `status`            | ENUM          | State (`PENDING`, `PASSED`, `FAILED`, `EXEMPT`).                          | `PASSED`                           |
| `result`            | JSON          | Detailed outcome (e.g., `{"reason":"incomplete_docs"}`).                   | `{"score":0.98}`                   |
| `auditTrail`        | JSON[]        | Log of actions (e.g., `{"action":"submit", "timestamp":"..."}`).           | `[{...}]`                          |
| `expiryDate`        | DATE          | When the check expires (e.g., for one-time KYC).                           | `2024-12-31`                       |

**Example Query (Find Failed AML Checks):**
```sql
SELECT *
FROM compliance
WHERE entityType = 'PAYMENT'
  AND status = 'FAILED'
  AND ruleId LIKE '%AML%';
```

---

#### **4. Transactions Domain**
| Field               | Type          | Description                                                                 | Example Values                     |
|---------------------|---------------|-----------------------------------------------------------------------------|------------------------------------|
| `txId`              | UUID          | Unique transaction ID.                                                     | `9f0e1d2c-...`                     |
| `paymentId`         | UUID          | Reference to the parent payment (if applicable).                           | `a1b2c3d4-...`                     |
| `accountId`         | UUID          | Source account ID.                                                          | `1b2c3d4-...`                      |
| `amount`            | DECIMAL(18,2) | Debit/credit amount (negative for debits).                                | `-1250` (€12.50 debit)             |
| `type`              | ENUM          | Classification (`DEBIT`, `CREDIT`, `FEE`, `REFUND`).                      | `DEBIT`                            |
| `description`       | VARCHAR       | Freeform note (e.g., "Market purchase").                                   | `Store purchase`                   |
| `status`            | ENUM          | State (`PENDING`, `COMPLETED`, `REVERSED`).                                | `COMPLETED`                        |
| `createdAt`         | DATETIME      | Timestamp of initiation.                                                   | `2024-06-21T10:15:00`              |
| `settledAt`         | DATETIME      | When funds were credited/debited.                                          | `2024-06-21T12:30:00`              |
| `fees`              | DECIMAL(18,2) | Associated fees (e.g., `0.50` for SEPA transfers).                          | `0.50`                             |

**Example Query (List Recent Transactions):**
```sql
SELECT txId, accountId, type, amount, description, status
FROM transactions
WHERE createdAt > NOW() - INTERVAL '7 days'
ORDER BY createdAt DESC
LIMIT 50;
```

---

### **Query Examples**
#### **1. Payment Workflow (Init → Approval → Settlement)**
```sql
-- Step 1: Initiate Payment (returns paymentId + idempotencyKey)
POST /payments
{
  "amount": 1250,
  "currency": "EUR",
  "initiator": {"type": "MERCHANT", "id": "M123"},
  "beneficiary": {"iban": "DE89370400440532013000"},
  "paymentMethod": "SEPA",
  "idempotencyKey": "unique-request-key-123"
}

-- Step 2: Poll for Status (Event-Driven Alternative: Webhook)
GET /payments/a1b2c3d4-5678
→ { "status": "APPROVED", "processingDate": "2024-12-01T14:30" }

-- Step 3: Settlement Confirmation (via Event)
{
  "event": "PaymentSettled",
  "paymentId": "a1b2c3d4-5678",
  "settledAt": "2024-12-01T15:45"
}
```

#### **2. Idempotent Payment Retry**
```sql
-- First Request (200 OK, stored with idempotencyKey)
POST /payments?idempotencyKey=abc123
→ { "paymentId": "p123" }

-- Duplicate Request (Same Key)
POST /payments?idempotencyKey=abc123
→ { "paymentId": "p123" }  # Same response (idempotent)
```

#### **3. Compliance Check for Account Opening**
```sql
-- Trigger Compliance Check (KYC)
POST /compliance/rules/KYC_Verification_2024
{
  "entityType": "USER",
  "entityId": "user:987654321",
  "docs": { "passport": "base64_encoded" }
}

-- Poll for Result
GET /compliance/rules/KYC_Verification_2024/user:987654321
→ { "status": "PASSED", "auditTrail": [...] }
```

---

### **Best Practices**
1. **Domain Boundaries**:
   - Use **Bounded Contexts** (Domain-Driven Design) to separate domains (e.g., `Payments` vs. `Lending`). Avoid "God" tables (e.g., a single `financial_events` table).
   - Example: Store `Payments` and `Loans` in distinct microservices with shared schemas where needed.

2. **Idempotency**:
   - Enforce unique `idempotencyKey` per request to avoid duplicate processing.
   - Store keys in a database with TTL for cleanup.

3. **Regulatory Compliance**:
   - Embed checks in domain logic (e.g., validate KYC before account activation).
   - Log compliance events with immutable timestamps.

4. **Data Privacy**:
   - Mask sensitive fields (e.g., `iban` → `IBAN_*123`) in APIs for non-admin users.
   - Use **tokenization** for payment cards (e.g., store `cardToken` instead of raw PAN).

5. **Event Sourcing**:
   - For audit trails, append-only event logs (e.g., Kafka topics) instead of updating status fields directly.
   - Example event: `{"type": "AccountFrozen", "accountId": "abc", "reason": "suspiciousActivity"}`

6. **Error Handling**:
   - Return **machine-readable errors** with codes (e.g., `402 PaymentRequired` for blocked accounts).
   - Example response:
     ```json
     {
       "error": {
         "code": "ACCOUNT_FROZEN",
         "message": "This account is under review."
       }
     }
     ```

---

### **Anti-Patterns & Pitfalls**
| **Anti-Pattern**               | **Risk**                                                                 | **Mitigation**                                  |
|---------------------------------|---------------------------------------------------------------------------|------------------------------------------------|
| **Tight Coupling**              | Changing one domain (e.g., `Payments`) breaks another (e.g., `Reports`). | Use clear interfaces (e.g., `PaymentService`). |
| **Overly Complex Schemas**      | Schema bloat slows queries and increases maintenance.                    | Start simple; normalize later.                 |
| **Ignoring Idempotency**        | Duplicate payments/transfers cause double charges.                        | Enforce `idempotencyKey` validation.            |
| **Hardcoded Compliance Rules**  | Rules become outdated without updates.                                   | Externalize rules (e.g., Redis cache).         |
| **No Event Logging**            | Debugging is difficult post-failure.                                     | Append-only event logs (e.g., Kafka).           |
| **Sensitive Data in Logs**      | Exposes customer info (e.g., `iban` in logs).                            | Filter logs with `REDACT` middleware.          |

---

### **Related Patterns**
1. **[Event Sourcing for Audits]**
   - Append-only logs for immutable transaction history (e.g., blockchain-like ledger for fintech domains).
   - *Use Case*: Reconstruct account activity post-dispute.

2. **[Idempotency as a Service]**
   - Centralized idempotency handling with retry logic (e.g., AWS Step Functions, custom Redis store).
   - *Use Case*: Handling payment retries without duplicate processing.

3. **[Domain-Driven Design (DDD) for Fintech]**
   - Model domains (e.g., `Payments`, `Lending`) as separate services with shared kernels for cross-cutting concerns.
   - *Reference*: [Eric Evans’ *DDD Blueprints*](https://vladmihalcea.com/ddd-blueprint-finance-domain/).

4. **[API Gateway for Fintech]**
   - Centralize authentication (e.g., OAuth 2.0), rate limiting, and compliance checks before routing to domain services.
   - *Tools*: Kong, Apigee, or custom Node.js/Go gateway.

5. **[Regulatory Reporting Patterns]**
   - Pre-aggregate compliance data (e.g., AML transactions) for quick reporting (e.g., FATCA, CRD IV).
   - *Example*: Materialized views for "high-risk" transactions.

6. **[CQRS for Query-Heavy Domains]**
   - Separate read models (e.g., `UserDashboard`, `AuditLog`) from write models to optimize performance.
   - *Use Case*: Real-time dashboards for fraud detection.

---
### **Further Reading**
- **Standards**:
  - [ISO 20022](https://www.iso20022.org/) (Message formats for payments).
  - [PSD2](https://www.ebpf.eu/regulatory-framework/psd2/) (EU open banking regulations).
- **Architecture**:
  - *Domain-Driven Design* by Eric Evans (2003).
  - *Building Evolutionary Architectures* by Neal Ford et al.
- **Tools**:
  - **Event Sourcing**: EventStoreDB, Kafka.
  - **Schema Management**: GraphQL (for flexible queries), Prisma (ORM).
  - **Compliance**: OpenCompliance (AML/KYC SDK).