# **[Pattern] Audit Verification – Reference Guide**

---

## **Overview**
The **Audit Verification** pattern ensures data integrity and compliance by systematically validating records against authoritative sources, logs, or external systems. This pattern is critical for:
- **Regulatory compliance** (e.g., GDPR, HIPAA, PCI-DSS)
- **Fraud detection** in financial transactions or user activities
- **Data reconciliation** between systems (e.g., CRM ↔ ERP)
- **Operational audits** (e.g., system logs, access logs)

A typical workflow involves:
1. **Trigger**: A change event (e.g., user update, transaction, log entry).
2. **Verification**: Cross-check the record against auditable sources (e.g., blockchain, third-party API, or internal ledger).
3. **Action**: Flag discrepancies, log results, or auto-correct if allowed.
4. **Reporting**: Generate audit trails or alerts for review.

This pattern is often implemented as a **micro-service** or **rule engine** and integrates with **event-driven architectures** (e.g., Kafka, AWS EventBridge) or **workflow tools** (e.g., Camunda).

---

## **Schema Reference**
Below is the **core data model** for implementing Audit Verification. Adjust fields based on your use case (e.g., financial vs. HR audits).

| **Field**               | **Type**       | **Description**                                                                                                                                                     | **Example Values**                                                                                     |
|-------------------------|----------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| **`audit_id`**          | UUID           | Unique identifier for the verification instance.                                                                                                                 | `550e8400-e29b-41d4-a716-446655440000`                                                                 |
| **`entity_type`**       | Enum           | The system/table/record type being audited (e.g., `USER`, `TRANSACTION`, `LOG_ENTRY`).                                                                         | `TRANSACTION`, `USER_ACCOUNT`                                                                        |
| **`entity_id`**         | String/ID      | The unique key of the record/entity under audit.                                                                                                               | `txn_abc123`, `user_1001`                                                                              |
| **`verification_type`**| Enum           | Method of verification (e.g., `SYSTEM_LOG`, `THIRD_PARTY_API`, `BLOCKCHAIN`, `MANUAL_REVIEW`).                                                                  | `BLOCKCHAIN_HASH`, `CREDIT_CARD_API`                                                                  |
| **`source_system`**     | String         | The authoritative system providing the data for verification (e.g., `PAYMENT_GATEWAY`, `ERP`, `EXTERNAL_DATABASE`).                                             | `STRIPE`, `SAP`, `AWS_S3`                                                                               |
| **`source_record_id`**  | String         | The key/reference in the source system.                                                                                                                      | `gateway_txn_456`, `inventory_SKU_789`                                                                 |
| **`status`**            | Enum           | Current state of verification (e.g., `PENDING`, `VERIFIED`, `DISCREPANCY`, `FAILED`).                                                                         | `VERIFIED`, `DISCREPANCY`                                                                              |
| **`result`**            | Boolean/String | Outcome of verification (`true`/`false` for binary checks; `{"status":"matched","notes":"..."}` for detailed results).                                         | `true`, `{"status":"partial_match","timestamp":"2023-10-01"}`                                          |
| **`timestamp`**         | Timestamp      | When the verification was executed.                                                                                                                          | `2023-10-01T14:30:00Z`                                                                                 |
| **`discrepancy_details`**| JSON           | Human-readable explanation if `status=DISCREPANCY` (e.g., field mismatches, timestamps).                                                                    | `{"field":"amount","expected":100,"actual":150,"units":"USD"}`                                         |
| **`verifier`**          | String         | System/user who performed the verification (e.g., `audit_service`, `admin_user_42`).                                                                         | `audit_bot_v1.2`                                                                                      |
| **`metadata`**          | JSON           | Additional context (e.g., `audit_level`="high", `priority`="critical").                                                                                     | `{"audit_level":"high","sla_minutes":360}`                                                             |

---

## **Implementation Details**
### **Key Concepts**
1. **Verification Strategies**
   - **Hash-based**: Compare checksums (e.g., SHA-256) of records.
   - **API Polling**: Query external systems (e.g., credit bureaus) for real-time validation.
   - **Event Correlation**: Match events across systems (e.g., log-in + payment confirmation).
   - **Threshold Checks**: Validate values (e.g., "balance <= limit").

2. **Automation Levels**
   - **Fully Automatic**: Auto-correct or reject invalid records (e.g., fraudulent transactions).
   - **Human-in-the-Loop**: Flag discrepancies for manual review (e.g., HR records).
   - **Scheduled**: Run periodic audits (e.g., weekly database reconciliation).

3. **Failure Modes**
   - **Temporary Failures**: Retry logic (e.g., exponential backoff for API timeouts).
   - **Permanent Failures**: Escalate to admins or mark as `status=FAILED` with `error_code`.

4. **Storage**
   - **Audit Logs**: Immutable record of all verifications (e.g., in a database or blockchain).
   - **Metadata**: Store lightweight results (e.g., `result=true`) vs. raw data (e.g., `discrepancy_details`).

---

### **Technical Considerations**
- **Performance**:
  - Batch verifications to reduce load (e.g., process 100 records/sec).
  - Cache frequent checks (e.g., Redis for API responses).
- **Scalability**:
  - Use **event-driven** designs (e.g., Kafka topics for audit events).
  - Partition workloads by `entity_type` or `source_system`.
- **Security**:
  - Encrypt `metadata` or `discrepancy_details` if sensitive.
  - Role-based access (e.g., only admins can `status=VERIFIED`).
- **Idempotency**:
  - Design to handle duplicate triggers (e.g., via `audit_id` deduplication).

---

## **Query Examples**
### **1. Find Unverified Transactions**
```sql
-- SQL (PostgreSQL)
SELECT *
FROM audit_verification
WHERE entity_type = 'TRANSACTION'
  AND status = 'PENDING'
  AND timestamp > NOW() - INTERVAL '7 days';
```

**Output**:
| audit_id               | entity_type | entity_id | status   | timestamp               |
|------------------------|-------------|-----------|----------|-------------------------|
| 550e8400-e29b-41d4-a716-446655440001 | TRANSACTION | txn_abc123 | PENDING  | 2023-10-01T10:00:00Z |

---

### **2. Filter by Discrepancy Type**
```sql
-- MongoDB
db.audit_verification.find({
  "status": "DISCREPANCY",
  "discrepancy_details.field": "amount",
  "result": { $exists: true }
})
```

**Output**:
```json
{
  "_id": ObjectId("550e8400e29b41d4a716446655440002"),
  "entity_type": "TRANSACTION",
  "discrepancy_details": {
    "field": "amount",
    "expected": 100,
    "actual": 150,
    "units": "USD"
  },
  "status": "DISCREPANCY"
}
```

---

### **3. Aggregate Verification Stats (Python)**
```python
from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017/")
db = client.audit_db

# Count verified/failed records by source_system
pipeline = [
    {"$group": {
        "_id": "$source_system",
        "verified": {"$sum": {"$cond": [{"$eq": ["$status", "VERIFIED"]}, 1, 0]}},
        "failed": {"$sum": {"$cond": [{"$eq": ["$status", "FAILED"]}, 1, 0]}}
    }}
]
results = list(db.audit_verification.aggregate(pipeline))

for result in results:
    print(f"{result['_id']}: Verified={result['verified']}, Failed={result['failed']}")
```

**Output**:
```
STRIPE: Verified=1500, Failed=2
PAYMENT_GATEWAY: Verified=890, Failed=12
```

---

### **4. Check Blockchain Hash Match**
```bash
# CLI (using jq for JSON parsing)
aws dynamodb query \
  --table-name AuditLogs \
  --key '{"entity_id": {"S": "txn_abc123"}}' \
  --projection-expression "blockchain_hash"

jq '.Items[0].blockchain_hash' output.json
# Output: "0x7f83b1657ff1..." (should match the transaction's hash)
```

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                                     | **When to Use**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| **Event Sourcing**        | Store state changes as immutable events for replayability.                                         | When you need to audit a **sequence of events** (e.g., user actions, transactions).               |
| **CQRS**                  | Separate read/write models to optimize queries.                                                     | If your verifications require **complex aggregations** (e.g., fraud analytics).                  |
| **Canary Releases**       | Gradually roll out changes to detect issues early.                                                 | Audit **new system integrations** before full deployment.                                          |
| **Saga Pattern**          | Coordinate distributed transactions with compensating actions.                                     | When verifications span **multiple microservices** (e.g., order fulfillment).                     |
| **Immutable Audit Logs**  | Store logs in a write-once, append-only format (e.g., blockchain, S3 object versioning).          | For **regulatory compliance** (e.g., financial records, healthcare data).                          |
| **Rate Limiting**         | Control the volume of verification requests.                                                       | Prevent **overloading** external APIs (e.g., credit checks).                                      |
| **Idempotency Keys**      | Ensure duplicate requests don’t cause side effects.                                                | Safeguard against **duplicate audit triggers** (e.g., retry logic).                               |

---

## **Best Practices**
1. **Design for Compliance**:
   - Store raw verification data (not just results) to prove due diligence.
   - Use **timestamps** to link audits to events (e.g., GDPR’s "right to erasure").

2. **Optimize Performance**:
   - **Pre-filter**: Only audit high-value records (e.g., transactions > $1,000).
   - **Async Processing**: Offload verifications to a queue (e.g., SQS, RabbitMQ).

3. **Monitor & Alert**:
   - Set up alerts for `status=FAILED` or `status=DISCREPANCY` (e.g., via Slack/PagerDuty).
   - Track **verification latency** (e.g., "95% of checks completed < 2s").

4. **Document Discrepancies**:
   - Include **human-readable notes** in `discrepancy_details` for investigations.
   - Example: `{"type": "timezone_mismatch", "source_tz": "UTC", "record_tz": "EST"}`.

5. **Test Edge Cases**:
   - **Offline systems**: Simulate API failures.
   - **Malicious data**: Test with intentionally corrupt records.

---
**Example Workflow**:
1. A user updates their credit card in a web app → **trigger** an `entity_type=USER` audit.
2. The system queries the **payment gateway API** (`source_system=STRIPE`) for the card.
3. If mismatched, log a `DISCREPANCY` with `discrepancy_details` and send an email to the user.
4. Admins review the log in the dashboard and `status=VERIFIED` after confirmation.