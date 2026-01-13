---
# **[Pattern] Envelope Encryption for Fields Reference Guide**
*Secure Field-Level Encryption in FraiseQL*

---

## **1. Overview**
Envelope encryption is a **scalable, zero-downtime** approach to encrypt sensitive fields in FraiseQL using **AES-256-GCM** for data encryption and a **Key Management System (KMS)** for managing encryption keys. This pattern ensures:
- **Field-level granularity**: Encrypt only specified columns, not entire tables.
- **Multi-provider KMS support**: Integrates with **HashiCorp Vault**, **AWS KMS**, or **GCP KMS**.
- **Zero-downtime key rotation**: Keys are rotated without service interruption.
- **Performance-optimized**: Uses a cache for key retrieval, minimizing latency.

This guide covers schema design, query syntax, and implementation details for enabling/enforcing encryption.

---
## **2. Key Concepts**
| Term               | Description                                                                                     |
|--------------------|-------------------------------------------------------------------------------------------------|
| **Envelope Encryption** | Double-layer encryption: AES-256-GCM for data + KMS-wrapped key.                               |
| **KMS Provider**      | Backend service managing encryption keys (Vault, AWS KMS, GCP KMS).                            |
| **Key Versioning**   | Automatic handling of KMS key versions; no manual intervention required.                     |
| **Cache Layer**      | In-memory key store to reduce KMS API calls during runtime.                                     |
| **Zero-Downtime Rotation** | New KMS keys are tested before replacing old ones; encrypted data remains decryptable.     |

---

## **3. Schema Reference**
### **3.1. Encryption-Ready Table Schema**
To enable field-level encryption, define a table with `ENCRYPTED` fields:
```sql
CREATE TABLE users (
    user_id    INTEGER PRIMARY KEY,
    -- Non-sensitive column
    username  VARCHAR(50) NOT NULL,
    -- SENSITIVE: Encrypted field (AES-256-GCM)
    ssn       ENCRYPTED VARCHAR(20),
    -- SENSITIVE: Encrypted field (AES-256-GCM)
    credit_card ENCRYPTED VARCHAR(30),
    -- Encrypted with KMS-wrapped key (optional)
    api_key    ENCRYPTED(KMS) VARCHAR(50)
);
```

### **3.2. Supported Field Types**
| Data Type          | Notes                                                                          |
|--------------------|---------------------------------------------------------------------------------|
| `ENCRYPTED VARCHAR` | Default (AES-256-GCM).                                                        |
| `ENCRYPTED(KMS)`   | Uses KMS-wrapped keys (e.g., for secrets like API tokens).                     |
| Binary Types       | Unsupported (use `ENCRYPTED` on `TEXT` or `JSONB` casts).                      |

### **3.3. KMS Provider Configuration**
Configure KMS settings in the FraiseQL configuration file (`fraise.yaml`):
```yaml
kms:
  provider: vault  # Options: vault, aws, gcp
  vault:
    address: "https://vault.example.com"
    auth_method: "aws"  # Or "token", "jwt"
    namespace: "sec/db"
  aws:
    region: "us-east-1"
    role_arn: "arn:aws:iam::123456789012:role/kms-role"
  gcp:
    project_id: "my-project"
    key_ring: "fraise-ring"
```

---
## **4. Query Examples**
### **4.1. Inserting Encrypted Data**
```sql
-- Inserts SSN encrypted with AES-256-GCM
INSERT INTO users (username, ssn, credit_card)
VALUES ('alice', '123-45-6789', '4111111111111111');
```
**Output**: Only the encrypted ciphertext (`b'...'`) is stored.

### **4.2. Querying Encrypted Fields**
```sql
-- Automatically decrypts fields on SELECT
SELECT username, ssn, credit_card
FROM users
WHERE username = 'alice';
```
**Result**:
| username | ssn          | credit_card         |
|----------|--------------|----------------------|
| alice    | 123-45-6789  | 4111111111111111    |

### **4.3. Updating Encrypted Data**
```sql
-- Updates encrypted field (auto-reencrypts)
UPDATE users
SET credit_card = '5555555555554444'
WHERE username = 'alice';
```

### **4.4. Key Rotation (Zero-Downtime)**
FraiseQL handles rotation automatically. To trigger a **test rotation**:
```sql
-- Simulates KMS key rotation (no data loss)
CALL fraise.rotations.test_key_rotation('users', 'ssn');
```

### **4.5. Viewing Encryption Metadata**
```sql
-- Shows encryption details for a table
SELECT fraise.encryption.check_table('users');
```
**Output**:
```json
{
  "table": "users",
  "encrypted_fields": ["ssn", "credit_card", "api_key"],
  "kms_provider": "vault",
  "last_rotation": "2024-01-15T12:00:00Z"
}
```

---
## **5. Implementation Details**
### **5.1. How Encryption Works**
1. **Data Encryption**: FraiseQL uses **AES-256-GCM** (authenticated encryption) for field values.
2. **Key Management**:
   - A **data key** (randomly generated) encrypts the field.
   - The **data key** is encrypted with a **KMS key** (wrapped).
3. **Decryption Flow**:
   - Query → KMS retrieves/wraps the correct **data key** → Decrypts field.

### **5.2. Performance Considerations**
| Operation          | Impact                                                                 |
|--------------------|-------------------------------------------------------------------------|
| **INSERT/UPDATE**  | ~5–10% overhead due to encryption; cached keys reduce latency.          |
| **SELECT**         | Decryption overhead (~300 µs per field); parallelizable.               |
| **Key Rotation**   | Near-zero impact; tested keys are verified before promotion.           |

### **5.3. Security Guarantees**
- **Confidentiality**: Only users with KMS permissions can decrypt data.
- **Integrity**: AES-GCM ensures data isn’t altered during storage/transit.
- **Compliance**: Meets **NIST SP 800-57**, **GDPR**, and **HIPAA** requirements.

---
## **6. Related Patterns**
| Pattern                     | Description                                                                 |
|-----------------------------|-----------------------------------------------------------------------------|
| **[Tokenization for Sensitive Fields](...)** | Replace sensitive data with tokens (e.g., credit cards) for auditability. |
| **[Dynamic Data Masking](...)**               | Mask sensitive fields in queries (e.g., `ssn` → `***-***-1234`).         |
| **[Field-Level Access Control](...)**         | Restrict access to encrypted fields via row-level permissions.             |
| **[Key Versioning Strategy](...)**            | Best practices for managing KMS key lifecycles during rotations.           |

---
## **7. Troubleshooting**
| Issue                          | Solution                                                                   |
|--------------------------------|-----------------------------------------------------------------------------|
| **"KMS access denied"**        | Verify IAM/Vault policies; check `kms.provider` in config.                 |
| **Decryption fails**           | Check key cache; retry with `fraise.cache.clear()`.                      |
| **Slow queries on encrypted fields** | Increase KMS API limits or use a more performant provider (e.g., Vault). |

---
## **8. Limitations**
- **No partial decryption**: Entire fields must be decrypted (no columnar access).
- **KMS dependencies**: Downtime in KMS may halt decrypt operations.
- **Binary data**: Not supported (use `TEXT` or `JSONB` casts).

---
**See Also**:
- [FraiseQL Security Model](link)
- [KMS Integration Guide](link)