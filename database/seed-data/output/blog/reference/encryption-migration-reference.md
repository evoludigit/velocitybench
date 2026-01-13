# **[Pattern] Encryption Migration Reference Guide**

---
## **Overview**
The **Encryption Migration** pattern ensures secure transition of data from legacy encryption schemes to modern, compliant, and scalable encryption solutions. This guide covers key concepts, implementation best practices, schema considerations, and example workflows for migrating encrypted data while maintaining integrity, confidentiality, and minimal downtime.

Use cases include:
- **Compliance updates** (e.g., PCI DSS, GDPR, HIPAA).
- **Performance optimization** (reducing overhead of outdated algorithms).
- **Security hardening** (phasing out deprecated ciphers).
- **Hybrid cloud migrations** (aligning encryption with new infrastructure).

This pattern minimizes risk by:
✔ Validating data integrity post-migration.
✔ Supporting backward compatibility during transition.
✔ Auditing the migration process for compliance.

---

## **Key Concepts**
| **Concept**               | **Description**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------|
| **Legacy Encryption**     | Existing encryption keys/ciphers (e.g., AES-128, DES, RSA-1024) that may be deprecated.              |
| **Target Encryption**     | New encryption standards (e.g., AES-256-GCM, ECDHE, post-quantum algorithms).                       |
| **Hybrid Encryption**     | Combining legacy and modern encryption during migration (e.g., AES-256 + legacy key wrapping).      |
| **Key Rotation**          | Securely generating and transitioning keys without exposing plaintext data.                         |
| **Data Validation**       | Verifying encrypted data post-migration (checksums, integrity hashes).                             |
| **Ciphertext Migration**  | Process of converting encrypted data from one format to another without decrypting/re-encrypting.   |

---

## **Schema Reference**
### **1. Key Management Schema**
| **Field**               | **Type**       | **Description**                                                                                     | **Example**                     |
|-------------------------|----------------|-----------------------------------------------------------------------------------------------------|---------------------------------|
| `legacy_key_id`         | `UUID`         | Unique identifier for the legacy encryption key.                                                    | `uuid("550e8400-e29b-41d4-a716-446655440000")` |
| `target_key_id`         | `UUID`         | Unique identifier for the new encryption key.                                                        | `uuid("a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6m7n8")` |
| `algorithm`             | `String`       | Legacy encryption algorithm (e.g., `"AES-128-CBC"`, `"RSA-OAEP"`)                                  | `"AES-128-CBC"`                 |
| `target_algorithm`      | `String`       | Target encryption algorithm (e.g., `"AES-256-GCM"`, `"ECDHE"`).                                      | `"AES-256-GCM"`                 |
| `key_version`           | `Integer`      | Version of the key (used for rotation).                                                           | `2`                              |
| `is_active`             | `Boolean`      | Flags whether the key is currently in use.                                                          | `true`                           |
| `created_at`            | `Timestamp`    | When the key was generated.                                                                         | `"2023-10-01T12:00:00Z"`        |
| `expires_at`            | `Timestamp`    | Key expiration (if applicable).                                                                     | `"2024-01-01T00:00:00Z"`        |
| `encryption_mode`       | `Enum`         | Mode (e.g., `SYMMETRIC`, `ASYMMETRIC`, `HYBRID`).                                                    | `"SYMMETRIC"`                    |

---

### **2. Encrypted Data Schema**
| **Field**               | **Type**       | **Description**                                                                                     | **Example**                     |
|-------------------------|----------------|-----------------------------------------------------------------------------------------------------|
| `data_id`               | `UUID`         | Unique identifier for the encrypted data record.                                                   | `uuid("1a2b3c4d-5e6f-7890-1234-56789abcdef0")` |
| `ciphertext`            | `Binary`       | Encrypted payload (varies by algorithm).                                                          | `base64("...")`                  |
| `iv` (Initialization Vector) | `Binary`     | Used in block ciphers (e.g., CBC, GCM).                                                            | `base64("...")`                  |
| `salt`                  | `Binary`       | Random value for key derivation (e.g., PBKDF2).                                                    | `base64("...")`                  |
| `legacy_key_ref`        | `UUID` (FK)    | References the `legacy_key_id` used for encryption.                                                 | `uuid("550e8400-e29b-41d4-a716-...")` |
| `target_key_ref`        | `UUID` (FK)    | References the `target_key_id` (if re-encrypted).                                                  | `uuid("a1b2c3d4-e5f6-7890-g1h2-...")` |
| `encryption_algorithm`  | `String`       | Algorithm used to encrypt this record.                                                              | `"AES-128-CBC"`                 |
| `iv_algorithm`          | `String`       | How the IV was generated (e.g., `"CTR_MODE"`, `"GCM_IMPLICIT_IV"`).                              | `"GCM_IMPLICIT_IV"`             |
| `is_reencrypted`        | `Boolean`      | Whether the data has been migrated to the new key.                                                | `false`                          |
| `migration_status`      | `Enum`         | Status (e.g., `PENDING`, `COMPLETED`, `FAILED`).                                                  | `"COMPLETED"`                    |

---
### **3. Migration Audit Log Schema**
| **Field**               | **Type**       | **Description**                                                                                     | **Example**                     |
|-------------------------|----------------|-----------------------------------------------------------------------------------------------------|
| `log_id`                | `UUID`         | Unique identifier for the audit entry.                                                              | `uuid("4d3e2c1b-0a9f-8765-4321-...")` |
| `data_id`               | `UUID` (FK)    | References the encrypted data record.                                                               | `uuid("...")`                    |
| `action`                | `Enum`         | Migration action (e.g., `ENCRYPT`, `DECRYPT`, `REENCRYPT`, `VALIDATE`).                              | `"REENCRYPT"`                    |
| `old_key_id`            | `UUID`         | Legacy key used in the action.                                                                    | `uuid("...")`                    |
| `new_key_id`            | `UUID`         | Target key used in the action (if applicable).                                                     | `uuid("...")`                    |
| `started_at`            | `Timestamp`    | When the action began.                                                                             | `"2023-10-01T14:30:00Z"`        |
| `completed_at`          | `Timestamp`    | When the action finished.                                                                          | `"2023-10-01T14:30:22Z"`        |
| `status`                | `Enum`         | `SUCCESS` or `FAILURE`.                                                                           | `"SUCCESS"`                      |
| `error_message`         | `String`       | Error details (if applicable).                                                                    | `null`                           |

---

## **Implementation Steps**
### **1. Pre-Migration Checks**
- **Audit Legacy Keys**: Identify all active legacy keys and their usage (e.g., via `SELECT * FROM keys WHERE is_active = true`).
- **Assess Compliance**: Ensure the target algorithm meets regulatory requirements (e.g., NIST SP 800-175B for post-quantum).
- **Back Up Data**: Create a snapshot of encrypted data before migration.

### **2. Key Rotation Workflow**
```sql
-- Step 1: Generate a new target key (example for AES-256-GCM)
INSERT INTO keys (
    key_id,
    algorithm,
    target_algorithm,
    key_version,
    is_active,
    created_at
) VALUES (
    uuid_generate_v4(),
    'AES-128-CBC',
    'AES-256-GCM',
    2,
    false,
    NOW()
);
```

### **3. Hybrid Encryption Phase**
- **Encrypt New Data**: Use the new key for all fresh writes.
- **Re-encrypt Legacy Data**: Batch-process existing records to re-encrypt with the new key (use **ciphertext migration** to avoid decrypting plaintext).

```sql
-- Example: Re-encrypt data (pseudo-code)
UPDATE encrypted_data
SET
    ciphertext = reencrypt_with_new_key(ciphertext, old_key_id, new_key_id),
    target_key_ref = new_key_id,
    encryption_algorithm = 'AES-256-GCM',
    is_reencrypted = true,
    migration_status = 'COMPLETED'
WHERE legacy_key_ref = old_key_id AND is_reencrypted = false;
```

### **4. Validation**
- **Integrity Checks**: Verify checksums or HMACs of re-encrypted data match pre-migration values.
- **Decrypt-Encrypt Test**: Randomly decrypt/re-encrypt a sample to ensure correctness.

```sql
-- Validate migration (example query)
SELECT
    data_id,
    CASE
        WHEN
            (SELECT checksum FROM encrypted_data_checksums WHERE data_id = encrypted_data.data_id)
            != (SELECT checksum(ciphertext) FROM encrypted_data WHERE data_id = encrypted_data.data_id)
        THEN 'FAILED'
        ELSE 'PASSED'
    END AS validation_status
FROM encrypted_data
WHERE is_reencrypted = true LIMIT 100;
```

### **5. Cutover**
- **Decommission Legacy Key**: Update application configs to use only the new key.
- **Update Audit Logs**: Mark legacy keys as inactive (`UPDATE keys SET is_active = false WHERE key_id = old_key_id`).

---

## **Query Examples**
### **1. List All Legacy Keys**
```sql
-- Find keys using deprecated algorithms
SELECT
    key_id,
    algorithm,
    target_algorithm,
    created_at,
    expires_at
FROM keys
WHERE algorithm IN ('DES', 'AES-128-CBC', 'RSA-1024')
ORDER BY created_at;
```

### **2. Find Orphaned Data (Unreencrypted)**
```sql
-- Identify data still encrypted with legacy keys
SELECT
    data_id,
    legacy_key_ref,
    encryption_algorithm,
    COUNT(*) AS unreencrypted_count
FROM encrypted_data
WHERE is_reencrypted = false
GROUP BY legacy_key_ref, encryption_algorithm;
```

### **3. Audit Migration Progress**
```sql
-- Track re-encryption status by key
SELECT
    k.key_id AS legacy_key_id,
    k.algorithm AS old_algorithm,
    t.algorithm AS new_algorithm,
    COUNT(ed.data_id) AS total_records,
    SUM(CASE WHEN ed.is_reencrypted THEN 1 ELSE 0 END) AS reencrypted_records,
    SUM(CASE WHEN ed.is_reencrypted = false THEN 1 ELSE 0 END) AS pending_records
FROM keys k
LEFT JOIN encrypted_data ed ON k.key_id = ed.legacy_key_ref
LEFT JOIN keys t ON k.target_key_id = t.key_id
WHERE k.is_active = true
GROUP BY k.key_id, k.algorithm, t.algorithm;
```

### **4. Force Re-encryption (Batch Job)**
```sql
-- Batch re-encrypt data for a specific key (use a transaction!)
BEGIN;
    UPDATE encrypted_data
    SET
        ciphertext = reencrypt_with_new_key(ciphertext, :old_key_id, :new_key_id),
        target_key_ref = :new_key_id,
        migration_status = 'COMPLETED'
    WHERE legacy_key_ref = :old_key_id
      AND is_reencrypted = false
      AND migration_status = 'PENDING'
      LIMIT 1000; -- Process in batches
COMMIT;
```

---

## **Best Practices**
1. **Minimize Decryption Exposure**: Use **ciphertext migration** (e.g., AES-128 → AES-256 via key wrapping) to avoid plaintext handling.
2. **Batch Processing**: Re-encrypt data in manageable chunks to avoid locking tables.
3. **Immutable Logs**: Store migration logs in a write-once medium (e.g., S3 with versioning).
4. **Rollback Plan**: Maintain a hot standby of legacy keys for 30–90 days post-migration.
5. **Automate Validation**: Integrate checksum checks into CI/CD pipelines for encrypted data.

---

## **Related Patterns**
| **Pattern**                          | **Description**                                                                                     | **When to Use**                                  |
|--------------------------------------|-----------------------------------------------------------------------------------------------------|--------------------------------------------------|
| **[Key Rotation](key-rotation.md)**  | Securely update cryptographic keys without downtime.                                                | When keys expire or are compromised.              |
| **[Hybrid Encryption](hybrid-encryption.md)** | Combine symmetric and asymmetric encryption for performance/security.                           | Legacy systems need gradual migration.           |
| **[Zero-Knowledge Proofs](zkps.md)** | Verify data integrity without revealing plaintext.                                                  | Compliance audits or data sharing.               |
| **[Tokenization](tokenization.md)**  | Replace sensitive data with non-sensitive tokens.                                                   | PCI DSS compliance for payment data.             |
| **[Confidential Computing](confidential-computing.md)** | Encrypt data in-use (e.g., via Intel SGX).                                                        | High-security workloads (e.g., healthcare).       |

---
## **Troubleshooting**
| **Issue**                          | **Solution**                                                                                     |
|-------------------------------------|-----------------------------------------------------------------------------------------------------|
| **Re-encryption fails silently**    | Add error logging to `migration_status` and monitor for `FAILURE` logs.                          |
| **Performance bottleneck**          | Parallelize re-encryption using database partitions or sharding.                                   |
| **Key compatibility issues**        | Test re-encryption with a small dataset first (e.g., 1% of records).                            |
| **Audit log corruption**            | Use a distributed log (e.g., Kafka) with exactly-once semantics.                                 |

---
## **Tools & Libraries**
| **Purpose**               | **Tools**                                                                                     |
|---------------------------|-------------------------------------------------------------------------------------------------|
| **Key Management**        | HashiCorp Vault, AWS KMS, Google Cloud KMS.                                                   |
| **Encryption Libraries**  | LibreSSL, OpenSSL, Bouncy Castle, AWS KMS SDK.                                                  |
| **Data Validation**       | HMAC-SHA256, BLAKE3 for checksums.                                                             |
| **Migration Orchestration** | Apache Airflow, Kubernetes Jobs, or custom ETL pipelines.                                      |

---
**Note**: Always test migrations in a **staging environment** before production. Use tools like `gpg --decrypt` or `openssl enc` to validate manual re-encryption workflows.