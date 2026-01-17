# **[Encryption Troubleshooting] Reference Guide**

---

## **Overview**
Encryption troubleshooting ensures secure data integrity and availability when encryption issues arise. This guide covers common encryption failures, diagnostic approaches, and remediation steps for symmetric, asymmetric, and key management problems. Use this pattern to validate encryption configurations, debug compromised keys, or resolve interoperability gaps in hybrid environments.

The guide is structured to help technical teams:
- **Identify** root causes (e.g., misconfigured algorithms, expired keys, protocol mismatches).
- **Validate** encrypted data integrity (hashing, digital signatures, or integrity checks).
- **Recover** from failures (key rotation, fallback mechanisms, or cryptographic updates).
- **Audit** encryption logs for anomalies (e.g., failed decryption attempts, unexpected rejections).

For advanced users, this guide includes schema references for common encryption standards (AES, RSA, TLS), query examples for logging systems, and integrations with related patterns like *Key Rotation* and *Secure Key Management*.

---

## **Key Concepts & Implementation Details**

### **1. Common Encryption Failure Scenarios**
| **Scenario**               | **Root Cause**                          | **Symptoms**                          | **Impact**                          |
|----------------------------|----------------------------------------|---------------------------------------|-------------------------------------|
| Failed decryption          | Expired key, wrong IV, corrupted data  | `DecryptError`, partial data         | Data unavailability                 |
| Authenticaiton failure     | Invalid signature, HMAC mismatch      | `VerificationFailed` error           | Security breach risk                |
| Protocol downgrade        | TLS_FALLBACK_SCSV rejection           | Connection reset, degraded security  | Vulnerability to known attacks      |
| Key revocation             | Key in excluded list (e.g., CRL/OcSP)  | Access denied, `KeyRejected`         | Temporarily locked access           |
| Performance degradation    | CPU-intensive cipher (e.g., RSA-ECB)   | High latency, resource exhaustion    | Poor user experience, DoS risk      |

---

### **2. Diagnostic Checklist**
Before troubleshooting, verify:
- **Correct algorithm selection**: Ensure the cipher (e.g., AES-256-GCM) matches requirements (e.g., FIPS 140-2 Level 3).
- **Key material validity**: Check for expiration, corruption, or improper handling (e.g., zero-padding).
- **Environment consistency**: Verify OS/crypto library versions (e.g., OpenSSL, Bouncy Castle) and platform support.
- **Network transparency**: For TLS, rule out MITM attacks or proxy misconfigurations.

---

### **3. Troubleshooting Steps by Layer**

#### **A. Key Management**
| **Step**                     | **Action**                                      | **Tools/Commands**                     |
|------------------------------|--------------------------------------------------|----------------------------------------|
| **Verify key storage**       | Confirm keys are encrypted-at-rest (e.g., HSM, KMS). | `aws kms list-aliases`, `kubectl get secrets` |
| **Check key rotation**       | Ensure keys are rotated per policy (e.g., every 90 days). | `openssl rsa -check -in private.pem`   |
| **Audit key access logs**    | Review IAM policies or audit trails for unauthorized access. | `grep "kms:Decrypt" /var/log/auth.log` |
| **Test key revocation**      | Simulate revocation and verify access denial.    | `curl --cacert revoked.crt https://target` |

#### **B. Symmetric Encryption (AES, ChaCha20)**
| **Issue**                    | **Debugging Command**                          | **Fix**                                |
|------------------------------|------------------------------------------------|----------------------------------------|
| Wrong IV length              | `echo "test" | openssl enc -aes-256-cbc -iv <IV> -nosalt` fails | Use `--iv-length 16` for AES-256-CBC. |
| Corrupted payload            | `openssl dgst -sha256 -verify public.pem -signature signature.txt data.txt` fails | Re-encrypt data with correct padding. |
| Performance bottleneck       | `perf stat -e cycles ./myapp` shows high CPU usage | Switch to ChaCha20-Poly1305 for lower overhead. |

#### **C. Asymmetric Encryption (RSA, ECC)**
| **Issue**                    | **Debugging Command**                          | **Fix**                                |
|------------------------------|------------------------------------------------|----------------------------------------|
| Weak modulus                 | `openssl rsa -pubin -in public.pem -text` shows <2048-bit key | Generate new key: `openssl genpkey -algorithm RSA -outform PEM -out key.pem -pkeyopt rsa_keygen_bits:4096`. |
| Signature verification fail | `openssl dgst -sha256 -verify public.pem -signature sig.bin data.bin` fails | Ensure signature algorithm matches (e.g., RSASSA-PSS). |
| Slow operations              | `openssl speed -evp rsa` shows poor performance | Use NIST P-256 (ECC) instead of RSA-2048. |

#### **D. TLS/Transport Encryption**
| **Issue**                    | **Debugging Command**                          | **Fix**                                |
|------------------------------|------------------------------------------------|----------------------------------------|
| TLS handshake failure        | `openssl s_client -connect example.com:443` shows `SSL handshake failed` | Check for cipher mismatch (`-cipher AES256-SHA`). |
| Heartbleed vulnerability     | `openssl s_client -connect example.com:443 -bugs heartbleed` | Upgrade OpenSSL to 1.0.1g+.             |
| Certificate chain invalid    | `openssl verify -CAfile root.ca.pem cert.pem` fails | Reissue certificate with full chain.   |
| Session resumption failure   | `TLS session_id` not matching                  | Enable session tickets: `-session-tickets`. |

---

## **Schema Reference**
### **1. Encryption Configuration Schema**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "EncryptionTroubleshootingConfig",
  "type": "object",
  "properties": {
    "symmetric": {
      "type": "object",
      "properties": {
        "algorithm": {"enum": ["AES-128-CBC", "AES-256-GCM", "ChaCha20-Poly1305"]},
        "keySize": {"minimum": 16, "maximum": 32},
        "ivLength": {"minimum": 12, "maximum": 16},
        "padding": {"enum": ["PKCS7", "None"]}
      }
    },
    "asymmetric": {
      "type": "object",
      "properties": {
        "algorithm": {"enum": ["RSA", "ECDSA"]},
        "keySize": {"minimum": 2048, "maximum": 8192},
        "signatureScheme": {"enum": ["PS384", "RSAPSS"]}
      }
    },
    "tls": {
      "type": "object",
      "properties": {
        "version": {"enum": ["TLSv1.2", "TLSv1.3"]},
        "ciphers": {"type": "array", "items": {"type": "string"}},
        "certificateChain": {"type": "array", "items": {"type": "string"}},
        "sessionTimeout": {"type": "integer", "minimum": 300}
      }
    },
    "keyManagement": {
      "type": "object",
      "properties": {
        "rotationPolicy": {"enum": ["Manual", "Automatic"]},
        "expiryWarning": {"type": "integer", "minimum": 7},
        "recoveryProcedures": {"type": "array", "items": {"type": "string"}}
      }
    }
  },
  "required": ["symmetric", "keyManagement"]
}
```

---

### **2. Common Logging Schema for Encryption Events**
```json
{
  "encryptionEvent": {
    "timestamp": "ISO8601",
    "type": ["DecryptError", "KeyRotation", "TLSHandshake"],
    "source": "string", // e.g., "KMS", "AppService"
    "details": {
      "statusCode": "string", // e.g., "403 Forbidden"
      "error": "string",     // e.g., "InvalidSignature"
      "metadata": {
        "keyId": "string",
        "algorithm": "string",
        "durationMs": "integer"
      }
    },
    "severity": ["INFO", "WARNING", "ERROR", "CRITICAL"]
  }
}
```

---

## **Query Examples**
### **1. Grep for Decryption Failures (Linux)**
```bash
# Search logs for failed decryption in JSON format
grep -E '"type":"DecryptError"' /var/log/app.log | jq '.details.error'
```
**Output:**
```
"InvalidSignature"
"KeyRejected"
```

### **2. Monitor TLS Handshake Failures (Prometheus)**
```promql
# Alert if TLS handshake errors exceed threshold
sum(rate(tls_handshake_errors_total[5m])) by (service) > 10
```

### **3. Audit Key Access (AWS KMS)**
```bash
# List recent KMS decrypt operations
aws kms list-keys | jq -r '.Keys[].KeyId'
aws kms get-key-usage --key-id <ARN> | grep "RotationEnabled"
```

### **4. Verify Certificate Chain (OpenSSL)**
```bash
# Check if intermediate CA is missing
openssl verify -CAfile root.ca.pem client.crt
```
**Output if invalid:**
```
error 20 at 0 depth lookup: unable to get local issuer certificate
```

---

## **Related Patterns**
| **Pattern**                     | **Description**                                                                 | **Integration Points**                          |
|---------------------------------|---------------------------------------------------------------------------------|--------------------------------------------------|
| **[Secure Key Rotation]**       | Automates key replacement and revocation policies.                              | Uses `EncryptionTroubleshooting` to validate rotation impact. |
| **[Zero-Trust Networking]**     | Enforces mutual TLS (mTLS) for service-to-service communication.               | Leverages TLS debugging from this pattern.     |
| **[Data Masking]**              | Anonymizes data for testing while preserving encryption.                       | Integrates with symmetric encryption troubleshooting. |
| **[Cryptographic Agility]**     | Supports algorithm upgrades (e.g., AES-384).                                  | Uses schema validation from this pattern.       |
| **[Audit Logging]**             | Centralizes encryption-related events for compliance.                           | Ingests logs from `encryptionEvent` schema.      |

---

## **Best Practices**
1. **Isolate Encryption Failures**:
   - Test decryption locally before assuming environment issues.
   - Use `stress-testing` tools like `wrk` for TLS performance.

2. **Leverage Observability**:
   - Correlate encryption logs with application metrics (e.g., latency spikes during key rotation).
   - Set up alerts for `KeyRejected` or `DecryptError` events.

3. **Plan for Downgrades**:
   - Maintain backward compatibility (e.g., support TLS 1.2 even during migrations to 1.3).
   - Document fallback mechanisms (e.g., manual key recovery).

4. **Compliance Checklists**:
   - Audit against regulations like **NIST SP 800-57** (cryptographic module validation) or **GDPR** (data integrity).

5. **Documentation**:
   - Include encryption-specific troubleshooting in runbooks (e.g., "Failed decryption: Check IV length").
   - Use **chef cookbooks** or **Ansible roles** for consistent cryptographic configurations.

---
**Note**: For production environments, combine this pattern with *Chaos Engineering* to test encryption resilience under load.