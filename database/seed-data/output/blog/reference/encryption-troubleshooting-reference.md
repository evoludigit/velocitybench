# **[Pattern] Encryption Troubleshooting Reference Guide**

---

## **Overview**
Encryption troubleshooting involves diagnosing and resolving issues related to cipher mismatches, key errors, policy violations, or failed decryption operations in secure communication, storage, or data processing systems. This guide provides structured steps, diagnostic tools, and validation techniques to identify root causes—such as misconfigured TLS, incorrect key derivation, or hardware-based encryption failures—while ensuring alignment with security best practices (e.g., RFC standards, NIST guidelines, or platform-specific requirements).

---

## **Schema Reference**
Common encryption error schemas and their fields for logging, diagnostics, and remediation.

| **Field**               | **Type**       | **Description**                                                                                     | **Examples**                                                                                     |
|-------------------------|----------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| `ErrorCode`             | String         | Unique identifier for the encryption-related error (platform-specific).                            | `"ERR_CYP_123"`, `"TLS_HANDSHAKE_FAILURE"`                                                       |
| `EventTimestamp`        | ISO 8601       | When the error occurred (precise clock sync critical for forensic analysis).                        | `"2024-05-20T14:30:00.123Z"`                                                                     |
| `Component`             | String         | System/module where the error originated (e.g., `api-gateway`, `database`).                       | `"kms-service"`, `"vault-agent"`                                                                  |
| `Operation`             | String         | Type of encryption/decryption task (e.g., `authenticate`, `decrypt`).                              | `"handshake"`, `"AES_256_CBC"`                                                                     |
| `CipherAlgorithm`       | String         | Name of the algorithm involved (e.g., `AES`, `RSA`).                                               | `"ChaCha20-Poly1305"`, `"ECB"` (deprecated)                                                      |
| `KeySource`             | String         | Where the key was sourced (HSM, cloud KMS, local vault).                                          | `"aws-kms:us-east-1"`, `"pkcs11"`                                                                 |
| `ErrorReason`           | String         | Human-readable description of the failure (e.g., "Invalid key size", "Certificate revoked").         | `"Missing PKCS7 padding"`, `"Unsupported block mode"`                                             |
| `AffectedData`          | Object         | Metadata about the encrypted/decrypted data (e.g., file, payload).                                 | `{"file": "/logs/app.json", "size": "MB", "format": "JSON"}`                                    |
| `PolicyViolation`       | Boolean        | Whether a security policy (e.g., TLS 1.3 only) was violated.                                        | `true`/`false`                                                                                   |
| `LogContext`            | JSON           | Additional context (e.g., session ID, user agent) for correlation.                                | `{"session": "xyz123", "client": "mobapp:v1.2"}`                                                 |
| `RemediationSteps`      | Array          | Suggested fixes (e.g., update key, patch library).                                                 | `["Set TLS 1.3", "Reset HSM pins"]`                                                              |
| `Severity`              | String         | Criticality level (e.g., `CRITICAL`, `WARNING`).                                                   | `"CRITICAL"` (fatal), `"INFO"` (non-blocking)                                                    |

---

## **Diagnostic Flow**
### **1. Identify the Symptom**
- **Symptom**: Failed decryption, handshake timeout, or audit log warnings.
- **Tools**:
  - Check platform logs (e.g., `journalctl` for Linux, Event Viewer for Windows).
  - Use built-in CLI tools:
    ```bash
    # Example: AWS KMS inspection
    aws kms describe-key --key-id alias/my-encryption-key
    ```
  - Monitor metrics (e.g., Prometheus alerts for high latency in cipher operations).

### **2. Validate Key Management**
| **Checklist**               | **Test Command/Tool**                                                                 | **Expected Outcome**                                                                 |
|-----------------------------|-------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| Key expiration              | `openssl x509 -noout -dates -in cert.pem`                                           | Not expired or within validity window.                                               |
| Key revocation status       | `curl https://crl.example.com/crl.pem` (or cloud provider API)                       | Not listed in revocation list.                                                       |
| Permissions (e.g., IAM)     | `aws iam list-policies --policy-arn arn:aws:iam::123456789:policy/EncryptOnly`      | User has `kms:Decrypt` permissions.                                                  |
| Key rotation counter        | `kubectl exec pod/kms-pod -- cat /opt/kms-rotation-counter`                         | Matches expected rotation cycle (e.g., quarterly).                                   |

### **3. Inspect Cipher Configuration**
- **Mismatched Protocols**:
  - Verify TLS version in server/client configs:
    ```bash
    # Check server TLS settings
    ss -tulnp | grep :443
    ```
  - Validate cipher suites:
    ```bash
    # Use OpenSSL to test cipher strength
    openssl ciphers -v 'ECDHE-ECDSA-AES256-GCM-SHA384'
    ```
- **Deprecated Algorithms**:
  - Blacklist weak ciphers (e.g., RC4, DES) in policies (e.g., `nginx` `ssl_protocols`):
    ```nginx
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ```

### **4. Verify Hardware/SW Enclaves**
- **HSM/TPM Issues**:
  - Check hardware health:
    ```bash
    # IBM Crypto Card status
    tpm2_getrandom --output-file /tmp/rnd.data
    ```
  - Test TPM 2.0:
    ```bash
    tpm2_activatecredmigration --in /dev/tpmrm0 --infile migratingKey.bin  --out migratingKey2.bin
    ```
- **Virtualized Encryption**:
  - Validate acceleration support (`vCPU` flags):
    ```bash
    # Check AMD SEV/Intel SGX support
    cat /sys/devices/system/cpu/cpu0/cpuidLE/leaf7_ebx
    ```

### **5. Audit Logs for Policy Violations**
- **Common Violations**:
  - **TLS**: `alert fatals` in `openssl s_client`.
  - **KMS**: Audit log entries with `Deny` status:
    ```json
    {
      "eventName": "kms:Deny",
      "errorCode": "AccessDenied",
      "requestId": "abc123"
    }
    ```
- **Tools**:
  - AWS CloudTrail for KMS:
    ```bash
    aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=kms:*
    ```

---

## **Query Examples**
### **1. Find All Encryption Failures in Cloud Logs**
```sql
-- AWS Athena query for KMS failures
SELECT
  eventTime,
  eventSource,
  errorCode,
  requestParameters.keyId,
  userIdentity.arn AS user_arn
FROM kms_logs
WHERE errorCode LIKE '%"Failure"'
ORDER BY eventTime DESC
LIMIT 100;
```

### **2. Detect Weak Ciphers in TLS Traffic**
```bash
# Use Wireshark to filter weak ciphers
tshark -f "tcp.port == 443" -Y "tls.handshake.type == 1 && tls.handshake.extensions contains 'cipher_suites'"
```

### **3. Check Key Rotation Compliance**
```bash
# Grep for rotation logs (adjust path)
grep -r "KEY_ROTATED" /var/log/encryption/
```

---

## **Root Cause Analysis (RCA) Patterns**
| **Scenario**                     | **Likely Cause**                          | **Fix**                                                                                     |
|----------------------------------|-----------------------------------------|---------------------------------------------------------------------------------------------|
| Decryption fails with "Invalid Pad" | PKCS#7 padding mismatch                  | Use authenticated encryption (e.g., `AES-GCM`).                                             |
| TLS handshake fails on startup   | Server certificate not trusted          | Update CA bundle (`update-ca-certificates` on Linux).                                       |
| KMS API throttling 5xx errors    | Quota exceeded                          | Request quota increase or distribute requests using exponential backoff.                     |
| HSM "Resource Busy" errors       | Rate-limited operations                  | Adjust session/operation limits or scale HSMs.                                              |

---

## **Preventive Measures**
1. **Automated Validation**:
   - Integrate tools like **OpenSSL** or **qualysSSL** for regular cipher checks.
   - Example: Schedule `nmap` SSL scan:
     ```bash
     nmap --script ssl-enum-ciphers -p 443 example.com
     ```
2. **Key Health Monitoring**:
   - Set up alerts for key usage metrics (e.g., 95% of decryption attempts failing).
3. **Rollback Plan**:
   - Maintain immutable backups of keys (e.g., AWS KMS aliases with versioning enabled).

---

## **Related Patterns**
1. **[Security] Key Rotation Automation** – Replace keys without downtime using tokens.
2. **[Resilience] Circuit Breaker for Encryption Calls** – Isolate KMS/TLS failures to avoid cascading errors.
3. **[Compliance] TLS Hardening Checklist** – Enforce cipher suites per **RFC 7525**.
4. **[Observability] Distributed Tracing for Encryption Latency** – Use **OpenTelemetry** to track decryption bottlenecks.

---
**Last Updated**: `YYYY-MM-DD`
**Version**: `1.0`
**Owner**: `Security Engineering Team`