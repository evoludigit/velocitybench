# **[Pattern] Encryption Debugging – Reference Guide**

---

## **Overview**
Encryption debugging ensures secure, transparent, and traceable cryptographic operations by validating key processes, detecting anomalies, and verifying integrity checks. This guide covers best practices for debugging encryption-related issues, validation mechanisms, and troubleshooting common failure points. Use this pattern when:
- Encrypted data fails decryption.
- Unauthorized access or tampering is suspected.
- Performance bottlenecks arise in cryptographic operations.
- Compliance requirements (e.g., AES, RSA validation) are not met.

---

## **Key Concepts & Schema Reference**

### **Schema: Encryption Debugging Workflow**
| Component               | Description                                                                                     | Example Values                                                                 |
|-------------------------|-------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Cryptographic Primitive** | The encryption algorithm (symmetric or asymmetric) used.                                       | AES-256, RSA-2048, ECDSA-P256                                         |
| **Key Material**        | Secrets, keys, or certificates involved (e.g., master key, session key, public key).             | `0x1a2b...`, `-----BEGIN PUBLIC KEY-----`                                |
| **Data Input**          | Plaintext or ciphertext undergoing processing.                                                  | `user_data`, `encrypted_payload`                                           |
| **Validation Check**    | Mechanism to verify correctness (e.g., HMAC, integrity tags, key rotation).                     | HMAC-SHA256, RSASSA-PSS                                                  |
| **Error State**         | Identified issues (e.g., corrupted keys, wrong IV, unsupported algorithm).                     | `KeyLengthError`, `IntegrityCheckFailed`, `UnsupportedAlgorithm`            |
| **Debug Metadata**      | Logs/traceback data for reproducibility (e.g., timestamps, operation IDs).                     | `{"op_id": "42", "timestamp": "2024-01-15T12:34:56Z", "status": "failed"}` |

---

### **Implementation Details**

#### **1. Pre-Debug Requirements**
- **Logging**: Enable trace-level logs for cryptographic operations.
- **Environment**: Isolate test data (e.g., sandbox keys) to avoid production leaks.
- **Tools**: Validate against libraries like:
  - OpenSSL (`openssl enc -d -aes-256-cbc -in file.enc`)
  - PyCryptodome (`from Crypto.Cipher import AES`)
  - AWS KMS (`aws kms decrypt --key-id alias/my-key`)

#### **2. Debugging Steps**
- **Step 1: Verify Key Integrity**
  ```python
  # Example: Check RSA public key validity
  from cryptography.hazmat.primitives import serialization
  public_key = serialization.load_pem_public_key(key_bytes)
  public_key.verify(signature, data, padding=RSASSA_PKCS1v15)
  ```
  **Error Handling**:
  - `ValueError`: Invalid public key.
  - `KeyError`: Missing key material.

- **Step 2: Decrypt Payload with Fallbacks**
  ```bash
  # Try multiple encryption modes (e.g., CBC, GCM)
  openssl enc -d -aes-256-cbc -in data.enc -out plaintext.txt -pass file:key.txt
  openssl enc -d -aes-256-gcm -in data.enc -out plaintext.txt -nopad
  ```
  **Debug Output**: Look for `bad decrypt` or `decryption failed`.

- **Step 3: Check Input/Output Consistency**
  - Compare plaintext/ciphertext length (e.g., AES may add padding).
  - Use integrity checks:
    ```python
    import hmac
    key = b'secret_key'
    sig = hmac.new(key, ciphertext, hashlib.sha256).digest()
    if not hmac.compare_digest(sig, stored_sig):
        raise IntegrityError("Tampered data!")
    ```

- **Step 4: Validate IV/Nonce**
  - Ensure IVs are unique and never reused (e.g., for AES in CBC mode).
  ```python
  from Crypto.Random import get_random_bytes
  iv = get_random_bytes(16)  # For AES-256-CBC
  ```

- **Step 5: Cross-Reference with Metadata**
  - Log key versions, timestamps, and operation IDs.
  - Example schema:
    ```json
    {
      "key_version": 3,
      "used_at": "2024-01-15T12:00:00Z",
      "success": false,
      "error": "InvalidIV"
    }
    ```

#### **3. Common Pitfalls & Fixes**
| Issue                          | Cause                              | Solution                                                                 |
|--------------------------------|------------------------------------|---------------------------------------------------------------------------|
| Decryption fails               | Wrong cipher mode or IV            | Verify mode (`CBC`, `GCM`) and IV generation.                             |
| Slow operations                | Poorly optimized library           | Use hardware acceleration (e.g., Intel SGX, AWS Nitro Enclaves).           |
| Silent data corruption         | Missing integrity checks           | Always use HMAC/SHA for sensitive data.                                    |
| Key rotation failed            | Old key not invalidated            | Implement key revocation lists (KRLs) or time-based expiration.            |

---

## **Query Examples**

### **1. Debugging a Failed AES Decryption**
**Scenario**: `data.enc` fails to decrypt with `openssl`.
**Command**:
```bash
# Try CBC mode with explicit IV
openssl enc -d -aes-256-cbc -in data.enc -out output.txt -iv 0x0123456789abcdef -pass pass:key

# If IV is embedded, extract it first
openssl enc -d -aes-256-cbc -in data.enc -out output.txt -pass file:key.txt -nopad
```

**Debug Output**:
```
error:0D08309D:asn1 encoding routines:ASN1_check_tlen:wrong tag
```
**Fix**: Ensure IV is correctly formatted (16 bytes for AES-256).

---

### **2. Validating RSA Signature**
**Scenario**: `SignatureVerificationError` in Python.
**Code**:
```python
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

public_key = serialization.load_pem_public_key(open("pub_key.pem").read().encode())
try:
    public_key.verify(
        signature=bytes.fromhex("a1b2..."),
        data=b"message",
        padding=RSASSA_PKCS1v15(),
        algorithm=hashes.SHA256()
    )
except Exception as e:
    print(f"Verification failed: {e}")  # Output: "Invalid signature"
```

---

### **3. Troubleshooting ECDSA Key Pair**
**Scenario**: `InvalidKeyError` when generating/loading keys.
**Fix**:
- Ensure curve is supported (e.g., `secp256k1` for Bitcoin).
```python
from cryptography.hazmat.primitives.asymmetric import ec

# Generate key
private_key = ec.generate_private_key(ec.SECP256R1())
public_key = private_key.public_key()

# Serialize in PEM format
pem_private = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)
```

---

## **Related Patterns**
| Pattern Name                | Description                                                                                     |
|-----------------------------|-------------------------------------------------------------------------------------------------|
| **Secure Key Management**   | Best practices for storing and rotating keys (e.g., AWS KMS, HashiCorp Vault).                |
| **Automatic Failover**      | Ensures encryption continues if a key service is unavailable (e.g., HSM redundancy).            |
| **Performance Tuning**      | Optimizing crypto ops (e.g., using GPU acceleration with CUDA).                               |
| **Audit Logging**           | Logging all cryptographic operations for compliance (e.g., FIPS 140-2).                       |
| **Zero-Trust Validation**   | Verifying keys at runtime (e.g., using attestation via TPM 2.0).                              |

---

## **Key Takeaways**
1. **Validate Early**: Check keys, IVs, and metadata before processing.
2. **Use Standard Tools**: Leverage OpenSSL/PyCryptodome for cross-validation.
3. **Log Everything**: Include timestamps, operation IDs, and error states.
4. **Test Edge Cases**: Corrupt IVs, wrong modes, or expired keys to simulate failures.
5. **Document Secrets**: Never hardcode keys; use secure vaults or environment variables.

---
**References**:
- [NIST SP 800-57 (Key Management)](https://csrc.nist.gov/publications/detail/sp/800-57/final)
- [OpenSSL Manual](https://www.openssl.org/docs/man3.0/man1/enc.html)