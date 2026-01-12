---
# **[Pattern] Cryptographic Audit Trails Reference Guide**

---

## **1. Overview**
Fraise’s **Cryptographic Audit Trails** pattern ensures **immutable, tamper-proof logging** of database changes in a Debezium-compatible format. Each event is cryptographically signed (SHA-256 + HMAC-SHA256) and isolated per tenant, facilitating regulatory compliance (e.g., GDPR, SOC 2) and forensic audits. This pattern integrates with FraiseQL’s change tracking to generate **replayable, time-ordered audit logs** that prevent alteration or deletion while supporting high-throughput ingestion.

---

## **2. Key Concepts & Architecture**

### **2.1 Core Components**
| Concept               | Description                                                                 |
|-----------------------|-----------------------------------------------------------------------------|
| **Cryptographic Chain** | A sequence of hashes (SHA-256) linking each audit entry to its predecessor.  |
| **HMAC Anchoring**    | Each entry is signed with an HMAC-SHA256 key derived from the previous hash. |
| **Tenant Isolation**  | Audit trails are scoped by tenant (e.g., `tenant_id`), preventing cross-tenant leakage. |
| **Immutable Storing** | Logs are written to a **write-once-read-many (WORM)** storage layer (e.g., S3, GCS). |
| **Debezium Format**   | Aligns with Kafka Connect’s [CDC format](https://debezium.io/documentation/reference/connect/format.html) for interoperability. |

---

### **2.2 Data Flow**
1. **Change Capture**: FraiseQL captures database changes (e.g., INSERT/UPDATE/DELETE) via Debezium connectors.
2. **Cryptographic Signing**: Each event is hashed (SHA-256) and signed with the previous hash’s HMAC.
3. **Tenant Scoping**: Events are labeled with `tenant_id` and partitioned by tenant.
4. **WORM Storage**: Signed logs are appended to an immutable object store.
5. **Audit Verification**: Clients can validate chains using the initial root hash.

---

### **2.3 Cryptographic Validation**
To verify an audit trail:
1. Retrieve the **root hash** (e.g., `root_hash: "abc123..."`).
2. For each subsequent entry:
   - Recompute its SHA-256 hash.
   - Verify its HMAC matches the previous hash.
3. If the chain breaks, the log is tampered with.

**Example Validation Pseudocode**:
```python
def verify_chain(logs, root_hash):
    current_hash = root_hash
    for i, log in enumerate(logs):
        computed_hash = sha256(log["payload"])
        if hmac_sha256(current_hash, log["hmac_key"]) != log["hmac_signature"]:
            return False
        current_hash = computed_hash
    return True
```

---

## **3. Schema Reference**
Audit trails follow this **Debezium-compatible JSON schema**:

| Field               | Type       | Description                                                                 | Required | Example Value                     |
|---------------------|------------|-----------------------------------------------------------------------------|----------|------------------------------------|
| `tenant_id`         | `string`   | Unique tenant identifier (e.g., `customer_123`).                           | ✅        | `"tenant_456"`                     |
| `operation`         | `string`   | Event type: `insert`, `update`, `delete`.                                 | ✅        | `"update"`                         |
| `payload`           | `object`   | Original database record (serialized).                                      | ✅        | `{"id":1, "name":"Alice"}`          |
| `timestamp`         | `timestamp`| ISO-8601 event timestamp.                                                   | ✅        | `"2023-10-01T12:00:00Z"`           |
| `previous_hash`     | `string`   | SHA-256 hash of the preceding log entry (or `null` for the root).          | ✅        | `"d3b07384..."` (or `null`)        |
| `current_hash`      | `string`   | SHA-256 hash of **this** entry’s payload + `previous_hash`.                 | ✅        | `"a1b2c3..."`                      |
| `hmac_signature`    | `string`   | HMAC-SHA256 of `previous_hash + current_hash` using a tenant-specific key.| ✅        | `"e9f8g7..."`                      |
| `signature_key`     | `string`   | Derived HMAC key (e.g., `hmacsha256(tenant_key, "audit_v1")`).              | ✅        | `"x9y8z7..."`                      |
| `metadata`          | `object`   | Additional context (e.g., `source_table`, `user_id`).                      | ❌        | `{"table":"users"}`                |

---
**Note**: `previous_hash` and `current_hash` form the cryptographic chain. The `signature_key` should be **rotated periodically** (e.g., monthly) and stored securely.

---

## **4. Query Examples**
### **4.1 Basic Audit Trail Query (FraiseQL)**
List all audit entries for a tenant:
```sql
SELECT
    tenant_id,
    operation,
    timestamp,
    payload,
    current_hash
FROM audit_logs
WHERE tenant_id = 'tenant_456'
ORDER BY timestamp DESC
LIMIT 100;
```

### **4.2 Verify Chain Integrity**
Check if logs are tampered with:
```sql
WITH RECURSIVE chain_verify AS (
    SELECT
        *,
        previous_hash AS current_hash,
        "current_hash" AS next_hash
    FROM audit_logs
    WHERE tenant_id = 'tenant_456'
    ORDER BY timestamp
    LIMIT 1
  UNION ALL
    SELECT
        a.*,
        a.previous_hash AS current_hash,
        a.current_hash AS next_hash
    FROM audit_logs a
    JOIN chain_verify c ON a.previous_hash = c.current_hash
    WHERE a.tenant_id = 'tenant_456'
)
SELECT
    COUNT(*) AS valid_entries,
    MAX(timestamp) AS last_entry_time
FROM chain_verify
WHERE
    current_hash = sha256(concat(payload::text, previous_hash::text))
    AND hmac_sha256(current_hash, signature_key) = hmac_signature;
```

### **4.3 Filter by Operation**
Find all deletions in a specific table:
```sql
SELECT
    tenant_id,
    timestamp,
    payload
FROM audit_logs
WHERE
    tenant_id = 'tenant_456'
    AND operation = 'delete'
    AND metadata->>'source_table' = 'users';
```

---

## **5. Performance Considerations**
| Factor               | Optimization Strategy                                      |
|----------------------|-----------------------------------------------------------|
| **Storage Overhead** | Compress payloads (e.g., gzip) before hashing.            |
| **Chain Validation** | Cache HMAC keys client-side to avoid rederiving.           |
| **High Throughput**  | Partition logs by tenant and parallelize validation.      |
| **Key Rotation**     | Use a **rolling HMAC key** (e.g., AWS KMS) for scalability. |

---

## **6. Related Patterns**
| Pattern                          | Description                                                                 |
|----------------------------------|-----------------------------------------------------------------------------|
| **[Event Sourcing]**              | Store state changes as immutable sequences (complements audit trails).       |
| **[Debezium CDC]**                | Capture database changes in real-time for FraiseQL integration.             |
| **[Tenant Isolation]**             | Scope resources (logs, keys) by tenant to enforce compliance.               |
| **[WORM Storage]**                 | Use S3 Object Lock or GCS Time-Based Retention for immutable logs.         |
| **[Key Rotation]**                 | Automate HMAC key rotation via AWS KMS or HashiCorp Vault.                  |

---
## **7. Compliance Notes**
- **GDPR**: Tenant-isolated trails enable **right to erasure** via selective log purging.
- **SOC 2**: Cryptographic verification meets **audit evidence** requirements.
- **PCI DSS**: Use **AES-256** for storing HMAC keys (not SHA-256 alone).

---
## **8. Troubleshooting**
| Issue                          | Solution                                                                 |
|--------------------------------|-------------------------------------------------------------------------|
| **Invalid Chain**              | Recompute hashes with the original payload; check for corrupted storage.|
| **Key Rotation Failures**      | Verify KMS/Vault permissions for the new key.                           |
| **Slow Validation**            | Precompute hashes in bulk or use a indexed lookup on `current_hash`.    |

---
**Need help?** Open a support ticket with:
- The tenant ID.
- A sample log entry.
- The exact error (if any).