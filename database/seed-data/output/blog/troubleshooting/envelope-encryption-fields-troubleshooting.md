# **Debugging Field-Level Envelope Encryption: A Troubleshooting Guide**
*(AES-256-GCM + KMS Integration for PII/PHI Protection)*

---

## **1. Introduction**
Field-level envelope encryption ensures sensitive data (PII/PHI) is encrypted **per field** rather than at the record or database level. This pattern uses **AES-256-GCM** for strong encryption and **AWS KMS** (or similar) for key management.

If sensitive data leaks, compliance fails, or keys are mismanaged, this guide provides a **practical troubleshooting** approach.

---

## **2. Symptom Checklist**
Check these **first** before diving deep:

| **Symptom**                          | **Likely Cause**                          | **Quick Check** |
|--------------------------------------|------------------------------------------|------------------|
| Sensitive data visible in DB logs    | Encryption failed or key not applied      | Query raw logs: `SELECT * FROM table WHERE sensitive_field = ...` |
| Compliance violations (GDPR/HIPAA)  | Missing encryption or key rotation       | Audit system: `kms:ListAliases` (AWS) |
| Manual key management errors         | Hardcoded keys or no KMS integration     | Check config files for `AES_KEY` strings |
| Data corruption after decryption     | Wrong IV, key, or GCM tag mismatch        | Compare `ciphertext` vs. `encrypted_data` |
| Slow queries on encrypted fields     | Poor indexing or inefficient GCM usage   | Check `EXPLAIN ANALYZE` on encrypted queries |

---

## **3. Common Issues & Fixes**
### **A. Encryption Failing (PII Visible in DB)**
#### **Issue:** Sensitive data is stored in plaintext.
**Root Cause:**
- Encryption not applied during write.
- Database connection skips encryption layer.

**Fix:**
1. **Verify Encryption Middleware**
   Ensure your app calls encryption **before** DB write.
   ```python
   # Correct (PyCryptodome + AWS KMS)
   from Crypto.Cipher import AES
   import boto3

   def encrypt_field(data: str, field_name: str) -> str:
       kms = boto3.client('kms')
       response = kms.generate_data_key(
           KeyId='alias/my-encryption-key',
           KeySpec='AES_256'
       )
       cipher = AES.new(response['Plaintext'], AES.MODE_GCM)
       ciphertext, tag = cipher.encrypt_and_digest(data.encode())
       return ciphertext.hex()  # Store ciphertext + key_id
   ```

2. **Check Database Middleware (e.g., SQLAlchemy Hooks)**
   ```python
   # SQLAlchemy event listener (pseudo-code)
   @event.listens_for(Base, 'before_insert')
   def encrypt_sensitive_fields(mapper, connection, target):
       if hasattr(target, 'ssn'):
           target.ssn = encrypt_field(target.ssn, 'ssn')
   ```

3. **Audit Logs**
   - Query DB logs for `INSERT`/`UPDATE` without encryption.
   - Example (PostgreSQL):
     ```sql
     SELECT * FROM pg_stat_statements
     WHERE query LIKE '%UPDATE%ssn%'
     LIMIT 10;
     ```

---

### **B. Key Management Failures**
#### **Issue:** `InvalidKeyException` or `Decryption failed`.
**Root Cause:**
- Stale KMS key.
- Incorrect key version in envelope.
- No automatic rotation.

**Fix:**
1. **Check KMS Key Status**
   ```bash
   aws kms describe-key --key-id alias/my-encryption-key
   # Ensure Status = "Enabled"
   ```

2. **Verify Key Rotation**
   - Enable **auto-rotation** in KMS:
     ```bash
     aws kms create-grant --key-id alias/my-encryption-key \
       --grantee-principal arn:aws:iam::123456789012:role/encryption-role \
       --operations encrypt:decrypt \
       --constraints '{"nonceReuseDuration":"3600"}'
     ```
   - Rotate manually if needed:
     ```bash
     aws kms delete-key --key-id alias/my-encryption-key
     aws kms create-key --description "New Key"
     ```

3. **Decryption Workflow**
   - Fetch KMS key **before** decrypting:
     ```python
     def decrypt_field(ciphertext_hex: str, key_id: str) -> str:
         kms = boto3.client('kms')
         response = kms.decrypt(
             CiphertextBlob=bytes.fromhex(ciphertext_hex),
             KeyId=key_id
         )
         return response['Plaintext'].decode()
     ```

---

### **C. Data Corruption (GCM Tag Mismatch)**
#### **Issue:** Decrypted output is garbled.
**Root Cause:**
- Incorrect **IV** or **tag** handling.
- Key reuse without GCM’s built-in replay protection.

**Fix:**
1. **Reproduce with `AES.GCM`**
   ```python
   from Crypto.Cipher import AES
   from Crypto.Random import get_random_bytes

   # Encrypt
   cipher = AES.new(key=key, mode=AES.MODE_GCM, nonce=get_random_bytes(12))
   ciphertext, tag = cipher.encrypt_and_digest(b"ssn=123-45-6789")

   # Decrypt (must use SAME IV + tag)
   cipher = AES.new(key=key, mode=AES.MODE_GCM, nonce=cipher.nonce)
   plaintext = cipher.decrypt_and_verify(ciphertext, tag)
   print(plaintext.decode())  # "ssn=123-45-6789"
   ```

2. **Debugging Steps**
   - Compare `cipher.nonce` (IV) between encrypt/decrypt calls.
   - Ensure `tag` is stored/transmitted alongside ciphertext.

---

### **D. Performance Bottlenecks**
#### **Issue:** Slow queries on encrypted fields.
**Root Cause:**
- Full-table scans due to missing indexes.
- GCM overhead on high-volume fields.

**Fix:**
1. **Index Encrypted Fields (If Needed)**
   - Use **salted hashes** for lookup:
     ```python
     def encrypt_field_salted(data: str, salt: str) -> str:
         cipher = AES.new(get_key(), AES.MODE_GCM)
         full_data = f"{data}_{salt}".encode()
         ciphertext, tag = cipher.encrypt_and_digest(full_data)
         return f"{cipher.nonce.hex()}:{tag.hex()}:{ciphertext.hex()}"
     ```
   - Store `nonce` separately for indexing.

2. **Benchmark GCM**
   - Test with `timeit`:
     ```python
     import timeit
     timeit.timeit(lambda: AES.new(key, AES.MODE_GCM).encrypt(b"data"), number=1000)
     ```

---

## **4. Debugging Tools & Techniques**
| **Tool/Technique**               | **Use Case**                                  | **Example Command** |
|-----------------------------------|-----------------------------------------------|---------------------|
| **AWS KMS Audit Logs**            | Verify key access/denials                     | `aws cloudtrail lookup-events` |
| **PostgreSQL `pgbadger`**        | Analyze slow queries on encrypted columns     | `pgbadger db_dump.log` |
| **Prometheus + Grafana**         | Monitor encryption/decryption latency         | `request_duration_seconds` |
| **AWS X-Ray**                     | Trace encrypted data flow                     | `aws xray get-trace-summary` |
| **Manual `curl` API Tests**       | Verify encryption middleware                   | `curl -X POST -H "Content-Type: application/json" -d '{"ssn":"123"}' http://api/encrypt` |

---

## **5. Prevention Strategies**
### **A. Automate Key Rotation**
- **Enable AWS KMS Key Rotation** (automatically replaces keys every 365 days).
- **Use Lambda to Rotate** (if custom logic is needed).

### **B. Validate Encryption at All Layers**
1. **Database Layer**
   - Use **行级加密（TDE）** (e.g., AWS KMS CMK for RDS) as a fallback.
   - Example (AWS RDS):
     ```bash
     aws rds modify-db-instance --db-instance-identifier my-db \
       --storage-encrypted --kms-key-id alias/my-cmk
     ```

2. **Application Layer**
   - **Unit Tests for Encryption**
     ```python
     def test_roundtrip_encryption():
         plain = "test@sensitive.com"
         encrypted = encrypt_field(plain, "email")
         decrypted = decrypt_field(encrypted['ciphertext'], encrypted['key_id'])
         assert decrypted == plain
     ```

3. **Compliance Checks**
   - **Automated Scans** (e.g., AWS Config Rules for KMS-enabled DBs).
   - **GDPR/HIPAA Audit Logs** (track key access).

### **C. Monitoring & Alerts**
- **Set Up CloudWatch Alarms**
  - Alert on `KMS:FailedDecrypt` or `Database:SlowQuery`.
- **Example Rule (AWS CloudWatch):**
  ```json
  {
    "MetricFilter": {
      "MetricName": "KMS.Errors",
      "Statistic": "Sum",
      "Namespace": "AWS/KMS",
      "Dimensions": [{
        "Name": "KeyId",
        "Value": "alias/my-encryption-key"
      }]
    },
    "ComparisonOperator": "GreaterThanThreshold",
    "Threshold": 0,
    "EvaluationPeriods": 1,
    "Period": 60
  }
  ```

---

## **6. Final Checklist Before Going Live**
1. ✅ **Keys are in KMS**, not hardcoded.
2. ✅ **Auto-rotation** is enabled (or manually tested).
3. ✅ **GCM tags** are stored/verified during decryption.
4. ✅ **Performance** is benchmarked (acceptable latency < 100ms).
5. ✅ **Audit logs** capture encryption/decryption attempts.
6. ✅ **Backup keys** are stored securely (AWS KMS Backup Plans).

---
### **Next Steps**
- If issues persist, **check AWS KMS CloudTrail** for denials.
- For **data corruption**, compare `ciphertext` + `tag` between layers.

---
**Troubleshooting Guide End.** 🚀
*(Focused on speed and practical fixes—no fluff!)*