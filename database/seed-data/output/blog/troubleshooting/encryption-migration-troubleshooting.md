# **Debugging Encryption Migration: A Troubleshooting Guide**

Encryption migration involves transitioning data from one encryption scheme, library, or key management system to another (e.g., moving from AES-128 to AES-256, migrating from symmetric to asymmetric encryption, or switching key management from a custom solution to AWS KMS). Poorly executed migrations can lead to **data corruption, decryption failures, performance bottlenecks, or security vulnerabilities**.

This guide provides **practical, actionable steps** to diagnose and resolve common issues during encryption migration.

---

## **1. Symptom Checklist**
Before diving into fixes, verify these symptoms to narrow down the problem:

### **Decryption Failures**
- ❌ API responses return `500 Internal Server Error` with messages like:
  - `"Decryption failed: Bad padding"`, `"Illegal block size"`, `"Unsupported key size"`
  - `"Key not found"` or `"Key expired"`
- ❌ Databases return `SQLSTATE[HY000]: General error` when querying encrypted fields.
- ❌ Logs show `java.security.InvalidKeyException` (Java) or `PyCryptodome.DECODER_ERROR` (Python).

### **Performance Issues**
- ⚡ Encrypted data queries are **10x slower** than before.
- ⚡ Key rotation or re-encryption introduces **high CPU/memory usage**.
- ⚡ Batch operations (e.g., ETL) fail due to **timeouts** or **OOM errors**.

### **Security & Compliance Failures**
- 🔒 Key material is **leaked** (e.g., in logs or process memory).
- 🔒 Audit logs show **unauthorized decryption attempts**.
- 🔒 Compliance scans flag **weak encryption** (e.g., RC4 still in use).

### **Data Integrity Issues**
- ✅ Data appears **corrupted** after decryption (e.g., garbled text, truncated records).
- ✅ Checksums (e.g., SHA-256) **do not match** expected values.
- ✅ Some records decrypt **succeed**, others **fail randomly**.

### **Key Management Problems**
- 🔑 **Keys are lost** during migration (e.g., HSM disconnect, KMS failover issues).
- 🔑 **Key versioning conflicts** (e.g., v1 key used for v2 data).
- 🔑 **Permissions misconfigured** (e.g., IAM roles lack `kms:Decrypt` access).

---

## **2. Common Issues & Fixes**
Below are **real-world problems** with **direct solutions** (code snippets included).

---

### **Issue 1: Incompatible Encryption Algorithms (e.g., AES-128 → AES-256)**
**Symptom:**
- Decryption fails with `"Illegal block size"` (Java) or `"Block cipher requires unique IV"` (Python).

**Root Cause:**
- Old data was encrypted with **AES-128**, but the new system expects **AES-256**.
- IV (Initialization Vector) handling differs between libraries (e.g., **PKCS5 vs. PKCS7 padding**).

**Fix:**
#### **Option A: Re-encrypt Data During Migration**
```python
# Python (using PyCryptodome)
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

def reencrypt_data(old_key, new_key, ciphertext):
    # Step 1: Decrypt with old key
    cipher_old = AES.new(old_key, AES.MODE_CBC, iv=ciphertext[:16])
    plaintext = unpad(cipher_old.decrypt(ciphertext[16:]), AES.block_size)

    # Step 2: Encrypt with new key
    cipher_new = AES.new(new_key, AES.MODE_CBC)
    new_ciphertext = cipher_new.encrypt(pad(plaintext, AES.block_size))
    return cipher_new.iv + new_ciphertext
```

#### **Option B: Use a Wrapping Key (Key Derivation)**
```java
// Java (using BouncyCastle)
import org.bouncycastle.crypto.engines.AESFastEngine;
import org.bouncycastle.crypto.modes.CBCBlockCipher;
import org.bouncycastle.crypto.params.KeyParameter;

public byte[] migrateKey(byte[] oldKey, byte[] newKey) {
    // Derive a new key from the old one (if compatible)
    byte[] wrappedKey = new AESFastEngine().wrapKey(
        new KeyParameter(newKey),
        new KeyParameter(oldKey)
    );
    return wrappedKey;
}
```

**Prevention:**
- **Test with a small dataset** before full migration.
- **Log IVs and key versions** to track compatibility.

---

### **Issue 2: Key Rotation Gone Wrong**
**Symptom:**
- Some data decrypts, others fail with `"Key not found"`.

**Root Cause:**
- **Keys were not rotated in sync** (e.g., old key still used in some services).
- **HSM or KMS key versioning was not handled** properly.

**Fix:**
#### **Step 1: Freeze Key Rotation Temporarily**
```bash
# AWS KMS: Disable key rotation for the old key
aws kms disable-key-rotation --key-id old-key-arn
```

#### **Step 2: Use Key Hierarchy (If Possible)**
```python
# Python (AWS KMS example)
import boto3
from botocore.exceptions import ClientError

def decrypt_with_fallback(key_arns, ciphertext):
    for key_arn in key_arns:
        try:
            client = boto3.client('kms')
            plaintext = client.decrypt(CiphertextBlob=ciphertext, KeyId=key_arn)['Plaintext']
            return plaintext
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceNotFoundException':
                raise
    raise ValueError("No key matched the ciphertext")
```

**Prevention:**
- **Document key rotation windows** and enforce them.
- **Use a key management system (KMS/HSM)** that supports **automatic fallback**.

---

### **Issue 3: IV (Initialization Vector) Mismatch**
**Symptom:**
- `"Invalid block size: expected 16 bytes, got X"` (Python).
- `"Ciphertext length must be a multiple of 16"` (Java).

**Root Cause:**
- Old system used **no IV** (ECB mode), but new system requires **CBC/CTR mode**.
- IV was **not stored with ciphertext** (leading to reuse).

**Fix:**
#### **Option A: Re-generate IVs (If Possible)**
```python
# Python: Ensure IV is always 16 bytes and prepended
def encrypt_with_iv(data, key):
    cipher = AES.new(key, AES.MODE_CBC)
    iv = cipher.iv  # Store IV with ciphertext
    return iv + cipher.encrypt(pad(data, AES.block_size))
```

#### **Option B: Fallback to ECB (Not Recommended for Production)**
```java
// Java (last resort - ECB is insecure!)
import javax.crypto.Cipher;
import javax.crypto.spec.SecretKeySpec;

public byte[] encryptECB(byte[] data, byte[] key) throws Exception {
    Cipher cipher = Cipher.getInstance("AES/ECB/PKCS5Padding");
    SecretKeySpec keySpec = new SecretKeySpec(key, "AES");
    cipher.init(Cipher.ENCRYPT_MODE, keySpec);
    return cipher.doFinal(data);
}
```
⚠️ **Warning:** ECB is **predictable** and **avoid in production**. Only use if **absolutely necessary** for backward compatibility.

**Prevention:**
- **Always store IVs** with ciphertext.
- **Use CTR or GCM mode** instead of CBC for better security.

---

### **Issue 4: Database Encryption Corruption**
**Symptom:**
- SQL queries fail with `SQLSTATE[HY000]: General error`.
- Some encrypted columns work, others don’t.

**Root Cause:**
- **Database schema change** (e.g., column length increased).
- **Transient faults** (e.g., network blips during bulk update).
- **Incorrect padding scheme** (e.g., PKCS7 vs. ISO7816).

**Fix:**
#### **Step 1: Verify Column Data Types**
```sql
-- PostgreSQL example: Check if encrypted blob fits
SELECT length(column_name), pg_encrypt(length(column_name)::text, 'secret_key') FROM table_name;
```
#### **Step 2: Use Transaction Rollback on Failure**
```python
# Python (with retry logic)
import psycopg2
from psycopg2 import sql

def update_encrypted_data(conn, data):
    for record in data:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE records SET encrypted_data = %s WHERE id = %s",
                    (encrypt(record), record['id'])
                )
                conn.commit()
        except psycopg2.Error as e:
            conn.rollback()
            print(f"Failed on record {record['id']}: {e}")
            continue
```

**Prevention:**
- **Test migrations in a staging database first**.
- **Use database transactions** to ensure atomicity.

---

### **Issue 5: Performance Degradation**
**Symptom:**
- Encrypted queries take **10x longer** than before.

**Root Cause:**
- **Overhead of new algorithm** (e.g., AES-GCM vs. AES-CBC).
- **Key lookup delays** (e.g., HSM latency, KMS throttling).
- **Unoptimized batch processing**.

**Fix:**
#### **Option A: Benchmark & Optimize**
```bash
# Time decryption in Python
%timeit decrypt(ciphertext, key)
```
#### **Option B: Use Hardware Acceleration**
```java
// Java: Enable AES-NI
System.setProperty("crypto.policy", "unlimited");
Security.addProvider(new org.bouncycastle.jce.provider.BouncyCastleProvider());
```
#### **Option C: Caching (For Repeated Decrypts)**
```python
from functools import lru_cache

@lru_cache(maxsize=1024)
def decrypt_cached(ciphertext, key):
    return decrypt(ciphertext, key)
```

**Prevention:**
- **Profile before/after migration** (e.g., using `perf` on Linux).
- **Avoid in-memory key caching** if security is a concern.

---

### **Issue 6: Key Leakage in Logs/Process Memory**
**Symptom:**
- Keys appear in **stack traces**, **log files**, or **memory dumps**.

**Root Cause:**
- **Debug logs enabled** during migration.
- **Process memory not zeroized** after key usage.

**Fix:**
#### **Option A: Sanitize Logs**
```python
import logging
import re

def sanitize_key(key):
    return re.sub(b'[0-9a-f]{32}', b'<KEY_REDACTED>', key)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

def log_secure(message, key):
    logging.info(f"{message} (key: {sanitize_key(key)})")
```

#### **Option B: Zeroize Keys After Use**
```java
// Java: Securely wipe memory
import javax.crypto.SecretKey;
import java.security.Key;

public void wipeKey(Key key) {
    byte[] keyBytes = key.getEncoded();
    for (int i = 0; i < keyBytes.length; i++) {
        keyBytes[i] = 0;
    }
    key.getEncoded(); // Force GC
}
```

**Prevention:**
- **Use `logger.debug()` sparingly** (avoid in production).
- **Enable memory sanitization** (e.g., `gdb` to check for leaks).

---

## **3. Debugging Tools & Techniques**
| **Tool/Technique**       | **Purpose**                                                                 | **Example Command/Code**                          |
|--------------------------|-----------------------------------------------------------------------------|----------------------------------------------------|
| **`strace` (Linux)**     | Trace system calls (e.g., `open`, `read`) to find slow I/O.                | `strace -f -e trace=file ./your_encryptor`         |
| **`perf` (Linux)**       | Profile CPU/memory usage during decryption.                                 | `perf record -g ./your_app` → `perf report`       |
| **AWS CloudTrail**       | Audit KMS API calls (e.g., `Decrypt` failures).                            | Check `EventName=Decrypt` in CloudTrail logs        |
| **Wireshark**            | Capture network traffic (e.g., KMS calls, database queries).               | Filter for `kms` or your app’s port                |
| **`openssl`**            | Verify ciphertext integrity (e.g., `openssl enc -aes-256-cbc -d`).          | `openssl enc -d -aes-256-cbc -iv $(head -c 16 /dev/urandom | xxd -p) -in file.enc` |
| **`valgrind`**           | Detect memory leaks (e.g., uninitialized keys).                             | `valgrind --leak-check=full ./your_app`            |
| **Log4j/Kafka Spies**    | Monitor key usage in distributed systems.                                   | `kafka-spy --broker-list host:port --topic debug-topics` |
| **`gdb` (Debugger)**     | Inspect memory after crashes.                                                | `gdb -c core dumpfile` → `bt`                      |

**Quick Debugging Workflow:**
1. **Reproduce the issue** (e.g., decrypt a failing record).
2. **Check logs** for `CipherException`, `KeyException`, or timeouts.
3. **Use `strace`/`perf`** to find slow operations.
4. **Compare old vs. new encryption** (e.g., dump ciphertexts).

---

## **4. Prevention Strategies**
| **Strategy**              | **Action Items**                                                                 | **Tools/Techniques**                          |
|---------------------------|----------------------------------------------------------------------------------|-----------------------------------------------|
| **Backward Compatibility** | Support **both old and new keys** during migration.                               | Key hierarchies, fallback decryption         |
| **Key Rotation Testing**  | Test **key rotation in staging** before production.                                | AWS KMS `enable-key-rotation`                |
| **Secure Logging**        | **Never log keys** (use `logger.debug` only in dev).                                | `logger.info("User accessed data")`            |
| **Data Validation**       | Verify **checksums** after decryption.                                           | SHA-256 hashing of plaintext                 |
| **Performance Monitoring** | Set **alerts for decryption latency spikes**.                                    | Prometheus + Grafana                         |
| **Immutable Backups**     | **Do not modify old encrypted data** until migration is complete.                | Database snapshots, S3 versioning             |
| **Automated Testing**     | Write **unit tests** for old/new encryption schemes.                              | pytest + `hypothesis` for fuzzing             |
| **Disaster Recovery Plan**| Document **rollback steps** (e.g., switch back to old keys if needed).          | Runbooks, chaos engineering tests             |

**Example Migration Checklist:**
```markdown
# Encryption Migration Checklist
- [ ] Test decryption with old keys (last 24h data)
- [ ] Verify checksums on sample records
- [ ] Profile performance (old vs. new)
- [ ] Audit logs for key access (no unauthorized decrypts)
- [ ] Rollback plan tested (can we switch back to old keys?)
- [ ] Key rotation scheduled (no overlap, no gaps)
```

---

## **5. Final Checklist Before Going Live**
✅ **Data Validation:**
- [ ] Decrypted data matches **expected values** (sample records).
- [ ] **Checksums** match (SHA-256, MD5 for old data if needed).

✅ **Performance:**
- [ ] **No slowdowns** in production-like environments.
- [ ] **Key lookup times** are acceptable (e.g., <50ms for KMS).

✅ **Security:**
- [ ] **No keys in logs** (sanitized or redacted).
- [ ] **Audit trails** exist for key usage.
- [ ] **No ECB mode** in production.

✅ **Rollback Plan:**
- [ ] **Old keys still available** (if needed).
- [ ] **Backup restored** if migration fails.

✅ **Monitoring:**
- [ ] **Alerts for decryption failures**.
- [ ] **Key rotation has no gaps**.

---
### **Next Steps**
1. **Start with a non-critical system** (e.g., test environment).
2. **Gradually migrate** (e.g., 10% of data first).
3. **Monitor closely** for 48h after full migration.
4. **Document everything** (keys, IVs, algorithms, rollback steps).

If issues persist, **regress to a known good state** (old encryption) and **debug step-by-step**.

---
**Final Note:**
Encryption migration is **risky but manageable** if approached systematically. **Test early, monitor closely, and have a rollback plan.**