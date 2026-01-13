# **[Pattern] Encryption Maintenance – Reference Guide**

---

## **Overview**
Encryption Maintenance is a **cryptographic lifecycle management pattern** designed to ensure secure, compliant, and operational integrity of encryption keys, certificates, and cryptographic algorithms across systems. This pattern addresses:
- **Key rotation** (periodic replacement of sensitive material)
- **Key revocation** (disabling compromised or expired keys)
- **Algorithm updates** (migrating to stronger cryptographic standards)
- **Auditability** (logging and tracking cryptographic operations)
- **Fallbacks** (graceful degradation when encryption fails)

The pattern supports **confidentiality, integrity, and availability** of encrypted data by enforcing disciplined cryptographic hygiene while minimizing downtime. It is critical for compliance (e.g., PCI DSS, HIPAA, GDPR) and mitigates risks from key leakage or cryptanalytic advances.

---

## **Implementation Details**
### **1. Core Components**
| **Component**               | **Description**                                                                                                                                                                                                 |
|------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Key Generation Module**   | Produces cryptographically secure keys (e.g., AES-256, RSA-4096) using FIPS 140-2/3 compliant algorithms. Supports hardware security modules (HSMs) for high-assurance scenarios.                                     |
| **Key Rotation Service**    | Automates periodic key replacement (e.g., quarterly for symmetric keys, annually for asymmetric) while maintaining backward compatibility via **key versioning**. Supports in-place or dual-key migration. |
| **Key Storage**             | Encrypted storage (e.g., AWS KMS, HashiCorp Vault) with **least-privilege access**. Avoids plaintext storage of master keys; uses **key wrapping** for derived keys.                                               |
| **Revocation List**         | Centralized database of revoked keys (CRLs or OCSP for PKI) with real-time validation checks. Supports **soft revocation** (temporary disablement) and **hard revocation** (permanent blacklisting).                     |
| **Algorithm Migration**     | Orchestrates updates (e.g., SHA-1 → SHA-3, RC4 → AES) with **transition periods** and **compatibility layers** to avoid service disruptions. Logs deprecated algorithm usage.                                     |
| **Audit Logs**              | Immutable records of all cryptographic operations (key generation, revocation, decryption failures) with timestamps, user identities, and system contexts (e.g., IP addresses). Complies with **SOX/NIST 800-53**. |
| **Fallback Mechanism**      | Graceful degradation (e.g., logging errors, switching to weaker algorithms if primary fails) while triggering alerts for manual intervention. Prioritizes **data integrity** over availability in critical systems. |

---

### **2. Cryptographic Workflow**
1. **Key Generation**
   - Keys are generated using **CSPRNGs** (e.g., `/dev/urandom`, BCRYPT) and stored encrypted (e.g., AES-256-wrapped) in a secure vault.
   - **Example**: `GenerateKey("AES-256", keyId="enc-2024-001")`.

2. **Encryption/Decryption**
   - Data encrypted with current keys; older keys retained for backup (e.g., 12 months).
   - **Example**:
     ```plaintext
     Encrypt(data="PII", key="enc-2024-001") → ciphertext
     Decrypt(ciphertext, key="enc-2024-001") → data
     ```

3. **Rotation**
   - New key (`enc-2024-002`) is generated and used for fresh encryption.
   - **Migration Strategy**:
     - **Dual-Key Mode**: System temporarily accepts both keys (e.g., 7 days).
     - **Key Versioning**: Metadata tracks supported keys per data object.

4. **Revocation**
   - Compromised key (`enc-2024-001`) is revoked via the `RevokeKey()` API.
   - Systems validate keys against the revocation list before use.

5. **Algorithm Update**
   - System migrates from `SHA-1` to `SHA-3` by:
     1. Logging SHA-1 usage.
     2. Generating SHA-3 hashes for new data.
     3. Deprecating SHA-1 after a transition period.

6. **Audit & Alerts**
   - Failed decryptions (e.g., due to revoked keys) trigger alerts:
     ```json
     {
       "event": "DecryptionFailure",
       "timestamp": "2024-05-20T12:34:56Z",
       "key": "enc-2023-005",
       "status": "REVOKED",
       "action": "EscalateToSecurityTeam"
     }
     ```

---

## **Schema Reference**
### **1. Key Metadata Table**
| **Field**          | **Type**       | **Description**                                                                                     | **Example**                     |
|--------------------|----------------|-----------------------------------------------------------------------------------------------------|---------------------------------|
| `keyId`            | String (UUID)  | Unique identifier for the key.                                                                       | `enc-2024-001`                  |
| `algorithm`        | Enum           | Cryptographic algorithm (AES, RSA, ECDSA).                                                          | `AES-256-CBC`                   |
| `generatedAt`      | Datetime       | Timestamp of key creation.                                                                        | `2024-01-15T00:00:00Z`          |
| `expiryDate`       | Datetime       | Scheduled revocation date (if applicable).                                                          | `2024-07-15T00:00:00Z`          |
| `revokedAt`        | Datetime*      | Timestamp of revocation (null if active).                                                           | `2024-03-01T10:00:00Z`          |
| `activeVersion`    | Boolean        | Indicates if the key is currently usable.                                                            | `true`                          |
| `storageLocation`  | String         | Vault/HSM path where the key is stored (e.g., `vault://secrets/enc`).                             | `hsm://keyStore/enc-2024-001`   |
| `creationMethod`   | Enum           | How the key was generated (e.g., `FIPS_HSM`, `Software_RNG`).                                       | `FIPS_HSM`                      |
| `relatedData`      | JSON           | Links to encrypted data objects using this key (e.g., `{"dbTable": "users", "column": "ssn"}`).    | `{"db": "orders", "id": "123"}`  |
| `keyDerivation`    | Boolean        | Whether the key was derived from a master key (e.g., via PBKDF2).                                   | `false`                         |

\* `revokedAt` is immutable after setting.

---

### **2. Revocation List**
| **Field**          | **Type**       | **Description**                                                                                     | **Example**                     |
|--------------------|----------------|-----------------------------------------------------------------------------------------------------|---------------------------------|
| `keyId`            | String         | ID of the revoked key.                                                                             | `enc-2023-005`                  |
| `revocationType`   | Enum           | `SOFT` (temporary) or `HARD` (permanent).                                                          | `HARD`                          |
| `revokedBy`        | String         | User/role that revoked the key (e.g., `admin:security`).                                          | `admin:security@company.com`    |
| `reason`           | String         | Justification for revocation (e.g., `compromise`, `expiry`).                                       | `compromise`                    |
| `effectiveDate`    | Datetime       | When revocation took effect.                                                                        | `2024-03-01T09:00:00Z`          |
| `validUntil`       | Datetime*      | For soft revocations: when the key is reinstated (null for hard revocations).                     | `2024-09-01T00:00:00Z`          |

\* `validUntil` is required for `SOFT` revocations.

---

### **3. Algorithm Compatibility**
| **Field**          | **Type**       | **Description**                                                                                     | **Example**                     |
|--------------------|----------------|-----------------------------------------------------------------------------------------------------|---------------------------------|
| `algorithm`        | String         | Legacy algorithm (e.g., `SHA-1`, `DES`).                                                             | `DES`                           |
| `replacement`      | String         | Stronger algorithm (e.g., `SHA-3`, `AES-256`).                                                      | `AES-256-GCM`                   |
| `deprecatedSince`  | Datetime       | Date when the algorithm was marked obsolete.                                                         | `2023-12-01T00:00:00Z`          |
| `transitionPeriod` | Integer (days) | Duration during which both algorithms are supported.                                                | `90`                            |
| `complianceRisk`   | Enum           | Impact on compliance (e.g., `LOW`, `MEDIUM`, `CRITICAL`).                                           | `CRITICAL`                      |

---

## **Query Examples**
### **1. List Active Keys**
```sql
SELECT keyId, algorithm, generatedAt, expiryDate
FROM encryption_keys
WHERE activeVersion = true
ORDER BY generatedAt DESC;
```

**Output**:
```
| keyId          | algorithm    | generatedAt          | expiryDate          |
|----------------|--------------|----------------------|---------------------|
| enc-2024-002   | AES-256-CBC  | 2024-04-01T00:00:00Z | NULL                |
| enc-2023-006   | RSA-4096     | 2023-07-15T00:00:00Z | 2024-07-15T00:00:00Z |
```

---

### **2. Check Revocation Status**
```sql
SELECT k.keyId, r.revocationType, r.reason
FROM encryption_keys k
LEFT JOIN revocation_list r ON k.keyId = r.keyId
WHERE k.keyId = 'enc-2023-005';
```

**Output**:
```
| keyId          | revocationType | reason       |
|----------------|----------------|--------------|
| enc-2023-005   | HARD           | compromise   |
```

---

### **3. Find Data Encrypted with a Key**
```sql
SELECT tableName, columnName
FROM encrypted_data
WHERE keyId = 'enc-2024-001';
```

**Output**:
```
| tableName | columnName |
|-----------|------------|
| users     | ssn        |
| payments  | credit_card|
```

---

### **4. Audit Failed Decryptions**
```sql
SELECT *
FROM audit_logs
WHERE event = 'DecryptionFailure'
  AND timestamp > NOW() - INTERVAL '7 days'
ORDER BY timestamp DESC;
```

**Output**:
```json
[
  {
    "event": "DecryptionFailure",
    "timestamp": "2024-05-20T14:23:45Z",
    "key": "enc-2023-005",
    "status": "REVOKED",
    "dataObject": "user_12345",
    "action": "EscalateToSecurityTeam"
  }
]
```

---

### **5. Transition Algorithm Usage**
```sql
-- Check for pending SHA-1 hashes before migration
SELECT COUNT(*)
FROM data_hashes
WHERE algorithm = 'SHA-1';
```
**Action**: If count > 0, schedule migration with a 90-day grace period.

---

## **Related Patterns**
| **Pattern**                  | **Description**                                                                                                                                                                                                 | **Connection to Encryption Maintenance**                                                                                     |
|------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------|
| **[Secure Key Storage](https://docs.example.com/patterns/secure-key-storage)** | Best practices for storing cryptographic keys in memory, disk, or hardware modules.                                                                                                                          | Encryption Maintenance relies on Secure Key Storage for vaulting keys during rotation/revocation.                          |
| **[Cryptographic Agility](https://docs.example.com/patterns/cryptographic-agility)** | Designing systems to adapt to algorithm changes (e.g., AES-NI, post-quantum cryptography).                                                                                                                 | Algorithm Migration in Encryption Maintenance implements Cryptographic Agility by supporting dual algorithms during transitions. |
| **[Data Encryption Key Management](https://docs.example.com/patterns/dek-management)** | Managing Data Encryption Keys (DEKs) derived from master keys (e.g., KMS).                                                                                                                                   | DEKs are rotated via the Key Rotation Service in Encryption Maintenance.                                                      |
| **[Confidential Computing](https://docs.example.com/patterns/confidential-computing)** | Protecting data in use via hardware-enforced isolation (e.g., Intel SGX).                                                                                                                                     | Encryption Maintenance ensures keys used in Confidential Computing are rotated/revoked securely within the enclave.          |
| **[Zero-Trust Architecture](https://docs.example.com/patterns/zero-trust)** | Granting least-privilege access to cryptographic operations.                                                                                                                                                   | Audit Logs in Encryption Maintenance align with Zero-Trust by logging all key access attempts.                              |

---

## **Best Practices**
1. **Key Rotation Frequency**:
   - **Symmetric keys**: Rotate every 90–365 days (shorter for high-risk data).
   - **Asymmetric keys**: Rotate annually (or sooner if compromised).
   - **Certificates**: Follow PKI standards (e.g., 1–5 years).

2. **Migration Strategy**:
   - Use **dual-key mode** to avoid downtime during rotation.
   - Test decryption failures for revoked keys in staging before production.

3. **Revocation**:
   - Revoke keys **proactively** (e.g., before expiry) if there are signs of compromise.
   - Log revocations with clear justification.

4. **Auditability**:
   - Retain audit logs for **at least 5 years** (NIST 800-53 recommendation).
   - Include **system context** (e.g., IP, user agent) to trace key usage.

5. **Compliance**:
   - Align rotation schedules with regulatory deadlines (e.g., PCI DSS QSA 3.5).
   - Document algorithm transitions in risk assessments.

6. **Failures**:
   - Design fallbacks to **log errors** (not silently discard data).
   - Alert on repeated decryption failures (potential key compromise).

---

## **Anti-Patterns**
| **Anti-Pattern**               | **Problem**                                                                                                                                                                                                 | **Mitigation**                                                                                                                                                     |
|---------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Static Keys**                 | Keys never rotated, increasing risk of leakage.                                                                                                                                                           | Enforce **automated rotation** with the Key Rotation Service.                                                                                        |
| **No Revocation List**          | Compromised keys remain usable indefinitely.                                                                                                                                                             | Implement a **centralized revocation database** with real-time validation.                                                                                   |
| **Algorithm Hardcuts**          | Abruptly dropping weak algorithms (e.g., SHA-1) without migration.                                                                                                                                    | Use **transition periods** (e.g., 90 days) and **compatibility layers**.                                                                                     |
| **Plaintext Key Backups**       | Keys stored unencrypted in backups.                                                                                                                                                                    | **Encrypt backups** with a separate master key (e.g., AWS KMS).                                                                                              |
| **Ignoring Decryption Failures** | Silent failures hide compromised keys or corrupted data.                                                                                                                                                 | Log failures and trigger **alerts** (e.g., Slack/PagerDuty).                                                                                              |
| **Over-Rotation**               | Excessive key changes break dependencies (e.g., stored procedures).                                                                                                                                      | Coordinate rotations with **application teams** and use **key versioning**.                                                                                        |

---
**Last Updated**: 2024-05-20
**Version**: 1.3