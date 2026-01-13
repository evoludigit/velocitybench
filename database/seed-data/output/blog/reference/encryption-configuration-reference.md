# **[Pattern] Encryption Configuration Reference Guide**

---

## **Overview**
The **Encryption Configuration** pattern ensures data confidentiality by applying encryption policies to resources, ensuring sensitive data (e.g., PII, financial records, or secrets) remains protected at rest, in transit, or during processing. This guide provides implementation details for configuring encryption in cloud-native and on-premises environments, covering key management, storage encryption, network security, and compliance considerations.

Key use cases include:
- **Data-at-rest encryption** (e.g., disks, databases, object storage).
- **Data-in-transit encryption** (e.g., TLS for APIs, VPNs).
- **Secret management** (e.g., vaults for credentials).
- **Compliance adherence** (e.g., GDPR, HIPAA, PCI DSS).

This pattern leverages **customer-managed keys (CMKs)** or **service-managed keys (SMKs)** for flexibility and security. Always align encryption settings with organizational policies and regulatory requirements.

---

## **Implementation Details**

### **1. Core Components**
| **Component**               | **Description**                                                                                                                                                                                                 | **Example Technologies**                                                                                     |
|-----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|
| **Key Management System (KMS)** | Centralized service for generating, storing, and rotating cryptographic keys. May be cloud-based (e.g., AWS KMS, Azure Key Vault) or on-premises (e.g., HashiCorp Vault).                          | AWS KMS, Azure Key Vault, Google Cloud KMS, HashiCorp Vault, OpenSSL                                       |
| **Encryption Scope**        | Defines where encryption applies:                                                                                                                                                                         |                                                                                                               |
|                             | - **Data-at-rest**: Encrypts stored data (e.g., EBS volumes, blob storage).                                                                                                                              | AWS EBS Encryption, Azure Disk Encryption, GCP Persistent Disk Encryption                                    |
|                             | - **Data-in-transit**: Secures network traffic (e.g., TLS 1.2+, IPSec).                                                                                                                                       | TLS, VPN (IPsec), mTLS                                                                                      |
|                             | - **Secrets Management**: Protects credentials (e.g., passwords, API keys).                                                                                                                                | AWS Secrets Manager, Azure Key Vault Secrets, HashiCorp Vault Secrets Engine                                |
| **Compliance Policies**     | Rules enforcing encryption standards (e.g., AES-256, key rotation schedules).                                                                                                                              | PCI DSS (AES-256), HIPAA (FIPS 140-2), GDPR (pseudonymization)                                           |
| **Audit Logging**           | Tracks encryption events (e.g., key access, decryption attempts) for forensic purposes.                                                                                                                 | AWS CloudTrail, Azure Monitor, GCP Audit Logs                                                                 |
| **Hardware Security Modules (HSMs)** | Physical devices for high-security key storage (e.g., PCI-compliant environments).                                                                                                                      | AWS CloudHSM, Azure Dedicated HSM, Thales Luna                                                                 |

---

### **2. Key Concepts**
| **Term**                     | **Definition**                                                                                                                                                                                   | **Key Considerations**                                                                                         |
|------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------|
| **Symmetric Encryption**     | Uses the same key for encryption/decryption (fast but requires secure key distribution).                                                                                                         | Ideal for bulk data; use with KMS to manage keys securely.                                                    |
| **Asymmetric Encryption**    | Uses public/private key pairs (slower but enables secure key exchange).                                                                                                                        | Use for TLS handshakes, digital signatures, or encrypting symmetric keys.                                    |
| **Key Rotation**             | Regularly replacing keys to mitigate long-term exposure risks.                                                                                                                                    | Automate rotation (e.g., every 90 days for CMKs) to reduce attack windows.                                   |
| **Customer-Managed Keys (CMKs)** | Keys controlled by the user (e.g., AWS KMS CMKs, Azure Key Vault keys).                                                                                                                         | Greater control but requires proper key lifecycle management.                                                |
| **Service-Managed Keys (SMKs)** | Keys managed by the provider (e.g., Azure Storage Service Encryption).                                                                                                                          | Simpler but less flexibility; may not meet compliance needs.                                                  |
| **Encryption Context**       | Additional data (e.g., headers) appended to ciphertext to ensure uniqueness (e.g., in AWS KMS).                                                                                             | Prevents replay attacks; required for some encryption APIs.                                                   |
| **Transparent Data Encryption (TDE)** | Automatically encrypts data without application changes (e.g., SQL Server TDE, Oracle Transparent Data Encryption).                                                                      | Reduces operational overhead; may impact performance.                                                          |
| **Key Hierarchy**            | Nested key structures (e.g., master key → data key) for granular control.                                                                                                                      | Simplifies key rotation; master keys are less frequently rotated.                                             |
| **Multi-Region Encryption**  | Encrypting data across regions with regional KMS keys (consider cross-region key replication for disaster recovery).                                                                         | Ensure compliance with data residency laws (e.g., GDPR).                                                     |

---

## **Schema Reference**

### **1. AWS Encryption Configuration Schema**
| **Field**                     | **Type**      | **Description**                                                                                                                                                                                                   | **Example Value**                          |
|-------------------------------|---------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------|
| `ResourceType`                | String        | Target resource (e.g., `EBS`, `S3`, `RDS`).                                                                                                                                                                   | `"EBS"`                                    |
| `KeyId`                       | String        | ARN of the KMS key (CMK or SMK).                                                                                                                                                                           | `arn:aws:kms:us-east-1:123456789012:key/abcd1234-5678-90ef-ghij-klmnopqrstuv` |
| `Enabled`                     | Boolean       | Whether encryption is enforced.                                                                                                                                                                         | `true`                                     |
| `SSEAlgorithm`                | String        | Encryption algorithm (e.g., `AES-256`, `aws:kms`).                                                                                                                                                             | `"AES-256"`                                |
| `Tags`                        | Object        | Metadata (e.g., `Environment: Production`).                                                                                                                                                             | `{ "CostCenter": "12345" }`                |
| `KeyRotationInterval`         | Integer       | Key rotation period in days (0 = disabled).                                                                                                                                                                 | `90`                                       |
| `HSMEnabled`                  | Boolean       | Uses HSM-backed keys for higher security.                                                                                                                                                                     | `false`                                    |
| `ReplicationRegion`           | String[]      | Regions where encrypted data is replicated.                                                                                                                                                                   | `["us-west-2", "eu-west-1"]`                |

---

### **2. Azure Encryption Configuration Schema**
| **Field**                     | **Type**      | **Description**                                                                                                                                                                                                   | **Example Value**                          |
|-------------------------------|---------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------|
| `StorageAccountName`          | String        | Name of the Azure Storage account.                                                                                                                                                                         | `"myStorageAccount"`                        |
| `KeyVaultName`                | String        | Azure Key Vault storing the CMK.                                                                                                                                                                           | `"myKeyVault"`                              |
| `KeyName`                     | String        | Name of the key in Key Vault.                                                                                                                                                                               | `"MyStorageKey"`                            |
| `EnableHttpsTrafficOnly`      | Boolean       | Enforces HTTPS for data-in-transit.                                                                                                                                                                        | `true`                                     |
| `DefaultAction`               | String        | `Allow`/`Deny` for unencrypted traffic.                                                                                                                                                                       | `"Deny"`                                   |
| `KeyRotationPolicy`           | Object        | Rotation schedule (e.g., `validityInMonths: 12`).                                                                                                                                                               | `{ "validityInMonths": 12 }`               |
| `EncryptionType`              | String        | `CustomerManaged`/`ServiceManaged`.                                                                                                                                                                       | `"CustomerManaged"`                         |
| `ServiceEndpoint`             | String        | Key Vault endpoint URL.                                                                                                                                                                                     | `"https://myKeyVault.vault.azure.net/"`      |

---

### **3. GCP Encryption Configuration Schema**
| **Field**                     | **Type**      | **Description**                                                                                                                                                                                                   | **Example Value**                          |
|-------------------------------|---------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------|
| `ResourceType`                | String        | Target resource (e.g., `CMEK` for Cloud Storage).                                                                                                                                                                   | `"CMEK"`                                   |
| `KeyRingName`                 | String        | Name of the Key Ring in Cloud KMS.                                                                                                                                                                         | `"production-keyring"`                      |
| `KeyName`                     | String        | Name of the cryptographic key.                                                                                                                                                                             | `"my-storage-key"`                          |
| `Location`                    | String        | GCP region for the Key Ring.                                                                                                                                                                               | `"us-central1"`                             |
| `EnableInTransitEncryption`   | Boolean       | Enforces TLS for data-in-transit.                                                                                                                                                                        | `true`                                     |
| `CustomerManagedKeyVersion`   | String        | Version of the CMK (e.g., `projects/12345/locations/us-central1/keyRings/production-keyring/cryptoKeys/my-key/cryptoKeyVersions/1`).                                                                 | `projects/12345/locations/us-central1/keyRings/production-keyring/cryptoKeys/my-key/cryptoKeyVersions/1` |
| `AuditLogSink`                | String        | BigQuery table for encryption logs.                                                                                                                                                                        | `"projects/my-project/logs/audit-logs"`     |

---

## **Query Examples**

### **1. AWS: List Encrypted EBS Volumes**
```bash
aws ec2 describe-volumes \
  --filters "Name=tag:EncryptionStatus,Values=true" \
  --query "Volumes[].{VolumeId:VolumeId,Encrypted:Encrypted,KeyId:AdditionalAttrs.KeyId}"
```
**Output:**
```json
[
  {
    "VolumeId": "vol-12345678",
    "Encrypted": true,
    "KeyId": "arn:aws:kms:us-east-1:123456789012:key/abcd1234-5678-90ef-ghij-klmnopqrstuv"
  }
]
```

---

### **2. Azure: Check Storage Account Encryption**
```powershell
Get-AzStorageAccount | Where-Object { $_.Encryption -ne $null } | Select-Object Name, Encryption, KeyVaultName
```
**Output:**
```
Name            Encryption KeyVaultName
----            -------- ------------
myStorageAcc   CustomerManaged myKeyVault
```

---

### **3. GCP: Inspect CMEK Configuration**
```bash
gcloud kms keys list --location=us-central1 --keyring=production-keyring | grep "my-storage-key"
```
**Output:**
```
destructionTime: "2025-01-01T00:00:00Z"
purpose: ENCRYPT_DECRYPT
label: encryption-key
```

---

### **4. HashiCorp Vault: Verify Encryption**
```bash
vault read -field=value secret/data/my-app/database
```
**Output:**
```json
{
  "password": "encrypted:p@ssw0rd",  // Vault handles decryption
  "username": "admin"
}
```

---

## **Related Patterns**
Consume or extend these patterns for comprehensive security:

| **Pattern**                          | **Description**                                                                                                                                                                                                 | **When to Use**                                                                                     |
|--------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| **[Secret Management]**               | Centralized vault for credentials, API keys, and tokens.                                                                                                                                                         | When managing secrets across microservices or CI/CD pipelines.                                       |
| **[Network Encryption]**              | Configures TLS, VPNs, or mTLS for secure communication.                                                                                                                                                         | For securing API traffic, internal services, or remote access.                                       |
| **[Data Masking/Pseudonymization]**  | Anonymizes sensitive data (e.g., PII) while retaining utility.                                                                                                                                                   | For GDPR compliance or analytics on sensitive datasets.                                               |
| **[Hardware Security Module (HSM)]**  | Hardware-based key storage for high-security workloads (e.g., PCI compliance).                                                                                                                               | For PCI DSS, financial, or government-regulated data.                                                  |
| **[Key Rotation Automation]**         | Automates key rotation to reduce risks of long-term exposure.                                                                                                                                                     | For environments requiring frequent key changes (e.g., high-turnover users).                        |
| **[Compliance Scanning]**             | Scans resources for encryption misconfigurations (e.g., unencrypted S3 buckets).                                                                                                                               | During audits or before merging compliance-critical changes.                                        |
| **[Zero-Trust Networking]**           | Implements least-privilege access and continuous authentication.                                                                                                                                               | For cloud-native or multi-cloud environments with dynamic workloads.                                 |

---

## **Best Practices**
1. **Principle of Least Privilege**:
   - Grant KMS permissions only to necessary roles (e.g., `kms:Encrypt` vs. `kms:*`).

2. **Key Hierarchy**:
   - Use **master keys** for key management and **data keys** for bulk encryption (e.g., AWS CMK + data key caching).

3. **Compliance Alignment**:
   - Map encryption settings to standards (e.g., PCI DSS requires AES-256 + HSM for cardholder data).

4. **Automate Rotation**:
   - Schedule key rotation (e.g., Azure Key Vault’s automatic rekeying) to minimize exposure windows.

5. **Audit and Monitor**:
   - Enable logging for key access (e.g., AWS CloudTrail) and set up alerts for anomalous decryption requests.

6. **Backup Keys Securely**:
   - Use **key recovery solutions** (e.g., AWS KMS key backup) but limit recovery access to authorized admins.

7. **Performance Considerations**:
   - **Symmetric encryption** is faster than asymmetric; use asymmetric only for key exchange or signing.
   - Benchmark encryption overhead (e.g., TLS handshake latency) for high-throughput services.

8. **Multi-Cloud Strategy**:
   - Standardize on **vendor-agnostic tools** (e.g., HashiCorp Vault) if managing cross-cloud encryption.

9. **Incident Response**:
   - Document **key revocation procedures** and **decryption failover** for critical systems.

10. **Documentation**:
    - Maintain a **key inventory** (e.g., CSV of keys, owners, and purposes) for compliance and recovery.

---
**Further Reading**:
- [AWS KMS Best Practices](https://docs.aws.amazon.com/kms/latest/developerguide/best-practices.html)
- [Azure Encryption Overview](https://learn.microsoft.com/en-us/azure/architecture/security/design/encryption-overview)
- [GCP Customer-Managed Encryption Keys](https://cloud.google.com/kms/docs/cmek)
- [NIST SP 800-57: Key Management](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-57.1r5.pdf)