# **[Pattern] Encryption Troubleshooting – Reference Guide**

---

## **Overview**
Encryption Troubleshooting is a structured approach to diagnosing and resolving issues related to encrypted data, keys, and infrastructure components (e.g., TLS, VPNs, databases, or cloud storage). This guide covers common failure scenarios, validation techniques, and actionable steps to restore security and functionality. Whether troubleshooting key rotation failures, cipher mismatch errors, or connectivity issues with encrypted services, this pattern provides a systematic methodology for root-cause analysis and remediation.

Key objectives:
- Validate encryption integrity (e.g., hashes, signatures).
- Diagnose key management issues (e.g., revocation, rotation).
- Resolve infrastructure misconfigurations (e.g., TLS handshake failures).
- Ensure compliance with security policies post-fix.

---

## **Key Concepts & Implementation Details**

| **Category**               | **Term**               | **Definition**                                                                                                                                                                                                 |
|----------------------------|------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Encryption Layers**      | TLS Handshake          | Process where client/server authenticate via certificates and negotiate encryption (e.g., TLS 1.2/1.3).                                                                                                        |
|                            | Key Rotation            | Process of replacing cryptographic keys (e.g., RSA, ECDH) to maintain security.                                                                                                                                    |
|                            | Certificate Revocation | Invalidating keys/certificates via CRL (Certificate Revocation List) or OCSP (Online Certificate Status Protocol).                                                                                                |
| **Validation Techniques**  | Hash Comparison         | Verifying file integrity using algorithms like SHA-256.                                                                                                                                                          |
|                            | Decryption Test         | Attempting to decrypt data with suspect keys to confirm compromised access.                                                                                                                                   |
| **Failure Scenarios**      | Cipher Mismatch        | Client/server use incompatible encryption algorithms (e.g., TLS_FALLBACK_SCSV).                                                                                                                                |
|                            | Key Expiry              | Expired keys causing authentication failures (e.g., SSH, VPN).                                                                                                                                                 |
|                            | Policy Violation        | Non-compliance with NIST/FIPS standards (e.g., weak encryption algorithms).                                                                                                                                      |
| **Tools & Protocols**      | OpenSSL                 | Command-line tool for SSL/TLS testing (e.g., `openssl s_client`).                                                                                                                                              |
|                            | Wireshark               | Network protocol analyzer for inspecting encrypted traffic (e.g., TLS packets).                                                                                                                                |
|                            | Hashcat                 | Password/cracking tool for testing decryption vulnerabilities.                                                                                                                                                 |

---

## **Schema Reference**
Below are structured schemas for common encryption troubleshooting scenarios.

| **Scenario**               | **Fields**                                                                 | **Description**                                                                                                                                                                                                 |
|----------------------------|-----------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **TLS Handshake Failure**  | `ClientVersion`, `ServerVersion`, `CipherSuite`, `Protocol`, `ErrorCode`   | Logs from `openssl s_client -connect example.com:443 -showcerts`.                                                                                                                                       |
| **Key Rotation Log**       | `KeyID`, `OldKey`, `NewKey`, `RotationTime`, `Status`                     | Audit trail for key replacements (e.g., AWS KMS, HashiCorp Vault).                                                                                                                                        |
| **Certificate Revocation** | `Subject`, `Issuer`, `RevocationReason`, `RevokedAt`, `CRL/OCSP URL`      | Output from `openssl crl -text -in crl.pem` or OCSP response validation.                                                                                                                                   |
| **Decryption Test Result** | `InputData`, `KeyUsed`, `Success/Failure`, `ErrorMessage`                 | Result from `openssl enc -d -aes-256-cbc -in data.enc -out decrypted.txt`.                                                                                                                               |

---

## **Query Examples**
Use these commands and queries to diagnose encryption issues.

### **1. TLS Handshake Testing**
```bash
# Check supported ciphers and TLS versions
openssl s_client -connect example.com:443 -showcerts -tls1_2 -no_ign_eof

# Debug handshake failures (verbose output)
openssl s_client -connect example.com:443 -debug -msg
```
**Expected Output:**
```plaintext
Protocol: TLSv1.2
Cipher: ECDHE-RSA-AES256-GCM-SHA384
Verification: OK (success)
---
```
**Common Errors:**
- `SSL_handshake_failure` → Cipher mismatch (e.g., server only supports TLS 1.3, client defaulted to 1.2).
- `unable_to_get_local_issuer_certificate` → Missing intermediate CA in certificate chain.

---

### **2. Key Rotation Validation**
```bash
# List active keys in AWS KMS (via CLI)
aws kms list-aliases --query 'Aliases[?starts_with(KeyId, `alias/aws/`)].KeyId'

# Check key status (e.g., enabled/disabled)
aws kms describe-key --key-id alias/my-key --query 'Enabled'
```
**Expected Output:**
```json
{
  "Enabled": true,
  "KeyCreationDate": "2023-01-01T00:00:00Z"
}
```
**Troubleshooting Steps:**
1. Verify new key is imported to HSM/software module.
2. Update applications/services to reference the new key (e.g., via IAM policies).

---

### **3. Certificate Revocation Check**
```bash
# Validate OCSP response
openssl ocsp -issuer ca.crt -cert client.crt -url http://ocsp.example.com

# Check CRL for revoked certificates
openssl crl -text -in crl.pem | grep -i "revoked"
```
**Expected Output:**
```plaintext
Certificate Revocation List (CRL):
    Last Update: Nov 15 12:00:00 2023 UTC
    Next Update: Dec 15 12:00:00 2023 UTC
    Revoked Certificates:
        Serial Number: 0123456789 (Revoked)
            Revocation Date: Oct 15 09:00:00 2023 UTC
```
**Resolution:**
- Reissue certificates or update internal CRL caches.

---

### **4. Decryption Test**
```bash
# Decrypt a file with a suspect key
openssl enc -d -aes-256-cbc -in encrypted.bin -out decrypted.bin -pass pass:testkey

# Verify hash integrity (e.g., SHA-256)
sha256sum decrypted.bin
```
**Expected Output (`openssl`):**
```plaintext
Decrypted output written to decrypted.bin
```
**Common Errors:**
- `decryption failed` → Incorrect key or corrupted data.
- `bad decrypt` → Key may be revoked or expired.

---

## **Step-by-Step Troubleshooting Flowchart**
1. **Symptom Identification**
   - *Symptom*: Connection refused over VPN.
     → Check: Key expiry, firewall rules, or TLS misconfiguration.
   - *Symptom*: "Permission denied" during decryption.
     → Check: Key permissions (e.g., `chmod 400 private_key.pem`).

2. **Validation**
   - **TLS**: Use `openssl` to verify cipher negotiation.
   - **Keys**: Run `aws kms describe-key` or `vault kv get secrets/key`.
   - **Data Integrity**: Compare hashes (`sha256sum`).

3. **Remediation**
   | **Issue**               | **Action**                                                                 |
   |-------------------------|----------------------------------------------------------------------------|
   | Expired Key              | Rotate key via KMS/Vault; update consumers.                                |
   | Cipher Mismatch          | Update client/server to support overlapping ciphers (e.g., TLS 1.2+).      |
   | Revoked Certificate      | Reissue via CA; push updated certificates to services.                     |
   | Policy Violation         | Audit with `nmap -sV --script ssl-enum-ciphers`; enforce FIPS-compliant algs.|

4. **Testing**
   - Reproduce fix in staging (e.g., `kubectl exec` for containerized apps).
   - Monitor for rollback risks (e.g., `journalctl -u nginx` for TLS errors).

---

## **Related Patterns**
| **Pattern**                     | **Description**                                                                                     | **When to Use**                                                                                     |
|----------------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| **Key Management Automation**    | Automates key rotation and revocation using tools like HashiCorp Vault or AWS KMS.                   | When manual key management is error-prone or scaling beyond 100 keys.                                |
| **Zero-Trust Networking**        | Implements mutual TLS (mTLS) for service-to-service authentication.                                   | For microservices architectures requiring granular access control.                                   |
| **Compliance Auditing**          | Uses tools like OpenSCAP to validate encryption policies against NIST/FIPS standards.                 | During regulatory audits or infrastructure migrations.                                               |
| **Data Residency Controls**      | Encrypts data at rest using customer-managed keys (CMKs) in cloud providers.                          | For industries with strict data sovereignty requirements (e.g., GDPR).                               |
| **Quantum-Resistant Encryption**| Evaluates post-quantum algorithms (e.g., Kyber, Dilithium) for long-term security.                  | Future-proofing cryptographic systems against quantum computing threats.                              |

---

## **Best Practices**
1. **Logging**: Enable TLS handshake logs in web servers (e.g., Apache `LogLevel debug`).
2. **Testing**: Use `sniptest` (TLS vulnerability scanner) to validate configurations pre-deployment.
3. **Documentation**: Maintain a runbook for key recovery procedures (e.g., AWS KMS backup keys).
4. **Alerting**: Set up alerts for key expiry (e.g., AWS CloudTrail + SNS for KMS events).