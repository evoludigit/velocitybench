---
### **[Pattern] Reference Guide: Encryption Guidelines**

---

### **1. Overview**
This reference guide outlines **Encryption Guidelines** as a foundational security pattern to protect sensitive data through cryptographic techniques. It standardizes how data is encrypted at rest, in transit, and in use, ensuring compliance with security best practices and regulatory frameworks (e.g., GDPR, HIPAA, PCI-DSS). The pattern defines:
- **Key management policies** (generation, storage, rotation, revocation).
- **Encryption standards** (symmetric/asymmetric algorithms, key lengths).
- **Implementation best practices** (hardware security modules, secure protocols, and access controls).
- **Auditability and logging** for compliance tracking.

Use this guide for developers, security teams, and architects to design systems with encryption as a core security pillar.

---

### **2. Schema Reference**

| **Component**          | **Description**                                                                 | **Mandatory?** | **Example Standards/Tools**                                                                 |
|------------------------|---------------------------------------------------------------------------------|----------------|-------------------------------------------------------------------------------------------|
| **Data Classification** | Defines sensitive data types (e.g., PII, PHI, financial data) and their risk levels. | ✅ Yes          | NIST SP 800-60, ISO 27001 classifications                                                   |
| **Encryption-at-Rest**  | Protects data stored in databases, files, or backups.                            | ✅ Yes          | AES-256 (Symmetric), TLS (for databases like PostgreSQL, MongoDB)                         |
| **Encryption-in-Transit**| Secures data in transit (e.g., HTTP → HTTPS, API calls).                          | ✅ Yes          | TLS 1.2/1.3, Mutually Authenticated TLS (mTLS), VPNs                                       |
| **Encryption-in-Use**   | Protects data while active (e.g., in RAM, cloud services).                      | ⚠️ Conditional | Hardware Security Modules (HSMs), Trusted Platform Modules (TPMs), Transparent Data Encryption (TDE) |
| **Key Management**      | Policies for generating, storing, rotating, and revoking encryption keys.        | ✅ Yes          | AWS KMS, HashiCorp Vault, Azure Key Vault, OpenSSL, FIPS 140-2 compliant HSMs              |
| **Key Rotation**        | Frequency and process for rotating keys (e.g., annually for long-term keys).     | ✅ Yes          | Automated rotation (e.g., AWS KMS default: 365 days)                                       |
| **Key Revocation**      | Process to deactivate compromised or unused keys.                                | ✅ Yes          | Certificate Revocation Lists (CRLs), OCSP, Key Blacklisting                                |
| **Tokenization**        | Replaces sensitive data with non-sensitive tokens (e.g., for payment systems).  | ⚠️ Conditional | PCI-DSS tokenization standards, AWS Tokens, custom tokenization libraries                   |
| **Secure Protocols**    | Standards for secure communication (e.g., APIs, databases).                     | ✅ Yes          | OAuth 2.0, OpenID Connect, gRPC with TLS, SSH for remote access                           |
| **Audit Logging**       | Tracks encryption-related events (e.g., key access, decryption attempts).        | ✅ Yes          | SIEM tools (Splunk, ELK Stack), AWS CloudTrail, Azure Monitor                               |
| **Key Backup**          | Secure storage of backup keys for disaster recovery.                            | ⚠️ Conditional | Offline HSMs, encrypted backups with multi-party access                                      |
| **Hardware Security**   | Uses HSMs/TPMs for key generation and storage in high-risk environments.         | ⚠️ Conditional | Thales HSM, AWS CloudHSM, Nitro Enclaves (AWS)                                              |
| **Compliance Mapping**  | Aligns encryption practices with regulations (e.g., GDPR Article 32, HIPAA).     | ✅ Yes          | PCI DSS Requirement 3, NIST SP 800-53, ISO/IEC 27701                                       |

---

### **3. Implementation Details**

#### **3.1 Key Concepts**
- **Symmetric Encryption**:
  - Uses the same key for encryption/decryption (fast but requires secure key exchange).
  - **Algorithms**: AES-256 (preferred), RSA-3072/4096 (for key exchange).
  - **Use Case**: Encrypting large datasets (e.g., databases, files).

- **Asymmetric Encryption**:
  - Uses public/private key pairs (slower but secures key exchange).
  - **Algorithms**: RSA, ECC (Elliptic Curve Cryptography).
  - **Use Case**: Secure authentication, TLS handshakes, digital signatures.

- **Hybrid Encryption**:
  - Combines symmetric (for data) + asymmetric (for key exchange) for efficiency (e.g., TLS).

- **Key Management**:
  - **Key Generation**: Use cryptographically secure RNGs (e.g., `/dev/urandom`, `secrets` module in Python).
  - **Key Storage**:
    - **Short-term keys**: Memory-encrypted (e.g., RAM disk).
    - **Long-term keys**: HSMs or cloud KMS (never hardcoded).
  - **Key Rotation**: Automate via tools (e.g., AWS KMS, Vault auto-rotate).

- **Tokenization**:
  - Replace sensitive data (e.g., credit card numbers) with tokens. Tokens are encrypted but can be reversed securely (e.g., via a tokenization service).

#### **3.2 Best Practices**
1. **Default Encryption**:
   - Enable encryption-by-default for all sensitive data (e.g., databases, storage buckets).
   - Use **TDE (Transparent Data Encryption)** for databases (e.g., SQL Server, Oracle).

2. **Key Hierarchy**:
   - **Master Keys**: Long-lived, stored in HSMs (e.g., AWS KMS CMKs).
   - **Data Encryption Keys (DEKs)**: Short-lived, derived from master keys (e.g., using AES-KW).

3. **Secure Protocols**:
   - Enforce TLS 1.2/1.3 for all external communications.
   - Use **mTLS** for service-to-service communication.

4. **Access Controls**:
   - Implement **least-privilege access** for keys (e.g., IAM policies in AWS).
   - Audit key usage with **SIEM tools**.

5. **Disaster Recovery**:
   - Backup encryption keys offline (e.g., encrypted USB drives with multi-factor access).
   - Test recovery procedures quarterly.

6. **Algorithm Agility**:
   - Avoid deprecated algorithms (e.g., DES, SHA-1, RC4).
   - Plan for **post-quantum cryptography** (e.g., NIST’s PQC standards).

---

### **4. Query Examples**

#### **4.1 Key Management Queries**
**Example 1: Generate a 256-bit AES Key (Python)**
```python
from Crypto.Cipher import AES
import os

def generate_aes_key():
    return os.urandom(32)  # 256-bit key

key = generate_aes_key()
print(f"AES Key (hex): {key.hex()}")
```

**Example 2: Rotate a Key Using AWS KMS**
```bash
# Rotate a customer master key (CMK) automatically
aws kms enable-key-rotation --key-id alias/my-cmk
```

**Example 3: Query Key Usage in Azure Key Vault**
```bash
# List keys with their properties (PowerShell)
Get-AzKeyVaultKey -VaultName MyVault | Select-Object Name, KeyType, Enabled, Attributes
```

---

#### **4.2 Encryption-at-Rest Queries**
**Example 4: Encrypt a File with AES-256 (CLI)**
```bash
# Encrypt a file with AES-256 (OpenSSL)
openssl enc -aes-256-cbc -salt -in secret.txt -out secret.enc -pass pass:my-password
```

**Example 5: Configure PostgreSQL TDE**
```sql
-- Enable Transparent Data Encryption (PostgreSQL)
ALTER SYSTEM SET encryption = 'on';
SELECT pg_reload_conf();
```

---

#### **4.3 Encryption-in-Transit Queries**
**Example 6: Enforce TLS 1.2 in Nginx**
```nginx
# Nginx configuration to disable weak TLS versions
ssl_protocols TLSv1.2 TLSv1.3;
ssl_prefer_server_ciphers on;
ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
```

**Example 7: Validate TLS in cURL**
```bash
# Check server TLS configuration
curl -v --tlsv1.3 https://example.com
```

---

#### **4.4 Audit Logging Queries**
**Example 8: Query KMS Audit Logs (AWS CloudTrail)**
```json
// Sample CloudTrail event for key access
{
  "eventName": "GenerateDataKey",
  "requestParameters": {
    "keyId": "alias/my-cmk",
    "grantTokens": ["..."]
  },
  "userIdentity": {
    "type": "IAMUser",
    "arn": "arn:aws:iam::123456789012:user/admin"
  }
}
```

**Example 9: ELK Stack Query for Encryption Events**
```json
// Elasticsearch query for decryption attempts
{
  "query": {
    "bool": {
      "must": [
        { "match": { "event.category": "encryption" } },
        { "term": { "event.action": "decrypt" } }
      ]
    }
  }
}
```

---

### **5. Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                                                                 |
|---------------------------|---------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **[Data Masking]**        | Replace sensitive data with non-sensitive placeholders (e.g., `****-****-1234`). | Development/test environments, logging.                                         |
| **[Secure Authentication]** | Multi-factor authentication (MFA) and OAuth 2.0 for access control.            | User authentication, API gateways.                                               |
| **[Zero Trust Networking]** | Micro-segmentation and least-privilege access for network security.           | Cloud-native environments, hybrid infrastructures.                             |
| **[Secure Coding Guidelines]** | Hardening code against cryptographic vulnerabilities (e.g., CSRF, XSS).      | Application development.                                                          |
| **[Key Rotation Automation]** | Automated tools for key rotation (e.g., HashiCorp Vault, AWS KMS).          | High-security environments, compliance-heavy systems.                           |
| **[Post-Quantum Cryptography]** | Preparing for quantum-resistant algorithms (e.g., Kyber, Dilithium).      | Long-term encryption needs (beyond 2030).                                        |

---

### **6. References**
- **NIST Guidelines**:
  - [SP 800-57 (Key Management)](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-57Part1r5.pdf)
  - [SP 800-131a (Transitional Guidance for TLS)](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-131a.pdf)
- **Standards**:
  - [ISO/IEC 27001:2022](https://www.iso.org/standard/73586.html) (Information Security Management)
  - [PCI DSS Requirement 3](https://www.pcisecuritystandards.org/documents/pci_dss_v4_0.pdf) (Encryption)
- **Tools**:
  - [AWS KMS](https://aws.amazon.com/kms/)
  - [HashiCorp Vault](https://www.vaultproject.io/)
  - [OpenSSL](https://www.openssl.org/)

---
**Last Updated**: [Insert Date]
**Version**: 1.3