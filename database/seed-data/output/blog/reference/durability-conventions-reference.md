**[Pattern] Durability Conventions Reference Guide**

---

### **Overview**
The **Durability Conventions** pattern ensures that data operations persist reliably across failures, system restarts, or network disruptions. By defining standardized conventions for data storage, validation, and recovery, this pattern minimizes data loss, reduces recovery complexity, and guarantees consistency—critical for systems requiring high availability (e.g., financial transactions, command queues, or configuration management).

This guide covers:
- Core concepts and terminology.
- Schema requirements for durable data formats.
- Query and validation patterns for ensuring durability.
- Integration with complementary patterns (e.g., Idempotency, Retry Mechanisms).

---

### **Key Concepts**
| Term               | Definition                                                                                     | Example                                                                 |
|--------------------|-----------------------------------------------------------------------------------------------|---------------------------------------------------------------------------|
| **Durability**     | Guarantee that data survives failures/outages.                                                | Database writes with commit acknowledgment before response.               |
| **Convention**     | Agreed-upon rules for encoding, validation, or recovery of durable data.                       | JSON schema validation for request payloads with checksum fields.       |
| **Atomicity**      | All-or-nothing commitment of multiple operations as a single logical unit.                      | ACID transactions in databases.                                           |
| **Idempotency Key**| Unique identifier ensuring retries/replays do not cause duplicate side effects.                | UUID in HTTP `ETag` or `Idempotency-Key` headers.                        |
| **Checksum**       | Cryptographic or algorithmic hash validating data integrity post-restoration.                   | SHA-256 checksums for backup files.                                        |
| **Replay Buffer**  | Temporary storage of operations to replay in case of partial failure.                          | Kafka transaction logs or SQL `UNCOMMITTED` tables.                       |

---

### **Schema Reference**
Durability conventions rely on structured metadata encoding. Below are required fields for **durable data schemas** (e.g., JSON, Protobuf, or Avro).

#### **Core Schema Fields**
| Field             | Type       | Required | Description                                                                                                   | Example Value                     |
|-------------------|------------|----------|---------------------------------------------------------------------------------------------------------------|-----------------------------------|
| **`@durability`** | Object     | Yes      | Root metadata for durability guarantees.                                                                       | `{ "version": "1.0", "checksum": "..." }` |
| **`id`**          | String     | Yes      | Unique identifier (UUID or composite key).                                                                     | `"txn-123e4567-e89b-12d3-a456-426614174000"` |
| **`operation`**   | String     | Yes      | Type of operation (`create`, `update`, `delete`).                                                             | `"update"`                         |
| **`timestamp`**   | ISO8601    | Yes      | Operation timestamp (UTC).                                                                                  | `"2024-05-20T12:34:56.789Z"`      |
| **`checksum`**    | String     | Yes      | CRC32/MD5/SHA-256 of the payload (excluding metadata).                                                          | `"d41d8cd98f00b204e9800998ecf8427e"` |
| **`idempotencyKey`** | String   | Conditional | Ensures replay safety (e.g., `ETag`, transaction ID).                                                           | `"user-order-789"`                 |
| **`retryLimit`**  | Integer    | No       | Max retries before failure (default: 3).                                                                     | `5`                                |
| **`state`**       | Enum       | No       | Operation status (`pending`, `completed`, `failed`).                                                           | `"completed"`                      |

#### **Payload Example**
```json
{
  "@durability": {
    "version": "1.0",
    "checksum": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
  },
  "id": "order-abc123",
  "operation": "create",
  "timestamp": "2024-05-20T12:34:56.789Z",
  "payload": {
    "userId": "user-xyz",
    "items": [{"name": "laptop", "price": 999}]
  },
  "idempotencyKey": "user-order-abc123"
}
```

---

### **Validation Rules**
Durability conventions enforce these checks **before** committing data:

| Rule                          | Implementation                                                                                     | Tooling Example                     |
|-------------------------------|---------------------------------------------------------------------------------------------------|-------------------------------------|
| **Checksum Integrity**       | Verify payload checksum against `@durability.checksum` before storage.                            | Custom validator or OpenAPI Schema  |
| **Idempotency Key Uniqueness** | Reject duplicates using `idempotencyKey`.                                                          | Database `UNIQUE` constraint on `idempotencyKey`. |
| **Timestamp Ordering**       | Ensure `timestamp` reflects chronological order (e.g., for replay).                                 | Compare `timestamp` on operation replay. |
| **Retry Limit Enforcement**   | Log failed operations with `retryLimit` and enforce max retries.                                    | Exponential backoff algorithm.      |
| **Schema Compliance**        | Validate `@durability` fields and payload using a schema (e.g., JSON Schema, Protobuf).           | `jsonschema` or `protbuf` validators. |

---

### **Query Examples**
#### **1. Query Durable Operations by Status**
**Use Case**: List pending operations for recovery.
```sql
SELECT * FROM durable_operations
WHERE state = 'pending'
  AND timestamp > NOW() - INTERVAL '1 hour'
ORDER BY timestamp ASC;
```
**Equivalent in REST**:
```http
GET /durable/operations?state=pending&maxAge=1h
Headers: Accept: application/json
```

#### **2. Validate Checksum on Replay**
**Use Case**: Verify data integrity post-restore.
```python
def verify_checksum(payload, stored_checksum):
    import hashlib
    data = json.dumps(payload).encode()
    computed_checksum = hashlib.sha256(data).hexdigest()
    return computed_checksum == stored_checksum
```

#### **3. Idempotent Operation Retry**
**Use Case**: Safe retry of a failed transaction (e.g., `idempotencyKey = "txn-123"`).
```http
POST /transactions/{txn-123}
Headers:
  Idempotency-Key: "txn-123"
  Retry-After: 30  # Backoff delay
```

#### **4. Replay Buffer Query**
**Use Case**: Recover failed operations from a buffer.
```sql
-- Replay pending operations in order
INSERT INTO target_table (data)
SELECT payload
FROM durable_buffer
WHERE idempotencyKey NOT IN (SELECT idempotencyKey FROM target_table)
  AND state = 'pending'
ORDER BY timestamp ASC;
```

---

### **Integration Patterns**
| Pattern               | Integration with Durability Conventions                                                                 | Example Use Case                          |
|-----------------------|---------------------------------------------------------------------------------------------------------|-------------------------------------------|
| **Idempotency**       | Use `idempotencyKey` to ensure replay safety.                                                          | REST APIs with `ETag` or `Idempotency-Key`. |
| **Retry Mechanisms**  | Combine with exponential backoff and `retryLimit` fields.                                               | Kafka consumer retries with dead-letter queue. |
| **Event Sourcing**    | Append-only log of durable events (e.g., `create`, `update`) with checksums.                            | CQRS state reconstruction.               |
| **Distributed Locks** | Acquire locks during durable writes to prevent conflicts.                                               | Database transactions with `SELECT FOR UPDATE`. |
| **Backup/Restore**    | Include checksums in backup archives for post-disaster validation.                                     | S3 versioned backups with SHA-256 hashes.  |

---

### **Failure Scenarios & Mitigations**
| Scenario                          | Mitigation                                                                                     |
|-----------------------------------|-----------------------------------------------------------------------------------------------|
| **Checksum Mismatch**            | Reject operation; log error with `payload` and `computed_checksum`.                          |
| **Duplicate Idempotency Key**     | Return `409 Conflict` with retry-after header.                                                 |
| **Corrupted Payload**             | Reject if `checksum` validation fails; use replay buffer for recovery.                         |
| **Timestamp Rollback**            | Reject operations with `timestamp` older than the latest committed state.                      |
| **Buffer Overflow**               | Implement size-based TTL (e.g., 7-day replay buffer) or archival to cold storage.               |

---

### **Tools & Libraries**
| Tool/Library          | Purpose                                                                                         | Language/Framework         |
|-----------------------|-------------------------------------------------------------------------------------------------|-----------------------------|
| **JSON Schema**       | Validate `@durability` and payload schemas.                                                     | JavaScript/Python           |
| **OpenAPI/Swagger**   | Document durable operation conventions in API specs.                                             | REST APIs                   |
| **Kafka**            | Durable event streaming with checksums and idempotent producers.                               | Java/Scala/Python           |
| **PostgreSQL**        | `RETURNING` clauses + `ON CONFLICT DO UPDATE` for idempotency.                                  | SQL                         |
| **Terraform**        | Enforce durability in infrastructure-as-code (e.g., backup policies).                            | IaC                         |

---
**Best Practices**
1. **Default to Durability**: Assume failures will occur; design for recovery by default.
2. **Minimize Payload Size**: Optimize checksums (e.g., CRC32 instead of SHA-256 for large data).
3. **Monitor Checksum Failures**: Alert on checksum mismatches (potential corruption).
4. **Document Conventions**: Publish `@durability` schema in your API docs (e.g., OpenAPI).
5. **Test Replay Scenarios**: Validate recovery workflows in CI (e.g., mock failures and replay).

---
**See Also**
- **[Idempotency Pattern]** for handling duplicate operations.
- **[Retry Mechanisms]** for transient failure handling.
- **[Event Sourcing]** for immutable audit trails.
- **[Backup Strategies]** for long-term durability.