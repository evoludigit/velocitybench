# **[Pattern] Encryption Strategies: At-Rest and In-Transit – Reference Guide**

---

## **Overview**
This pattern defines best practices for securing data **at-rest** (stored in databases, file systems, or storage services) and **in-transit** (transmitted via APIs, networks, or messaging systems). Encryption ensures confidentiality by:
- **Preventing unauthorized access** to stored data.
- **Securing data in transit** from interception or tampering.
- **Complying with regulatory requirements** (e.g., GDPR, HIPAA, PCI-DSS).

At-rest encryption uses **symmetric (AES, ChaCha20) or asymmetric (RSA, ECC) algorithms** with secure key management. In-transit encryption relies on **TLS (Transport Layer Security)** for network communications, **HTTPS for APIs**, and **VPNs or mutual TLS (mTLS) for service-to-service authentication**.

---
## **Key Concepts & Implementation Details**

### **1. At-Rest Encryption**
| **Component**               | **Description**                                                                 | **Implementation**                                                                 |
|-----------------------------|-------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Storage Encryption**      | Encrypts data stored in databases, filesystems, or cloud storage.            | Use built-in features (e.g., AWS KMS, Azure Disk Encryption, TDE in SQL Server). |
| **Transparency**            | Encryption/decryption happens automatically without application changes.    | Supported by OS (e.g., BitLocker, LUKS), databases (column-level encryption), or storage services (S3 SSE, GCP Persistent Disk). |
| **Key Management**          | Secure storage and rotation of encryption keys.                          | Use **HSMs (Hardware Security Modules)** or **cloud KMS** (AWS KMS, Azure Key Vault). |
| **Performance Impact**      | Encryption adds minimal overhead (~1-5% CPU).                              | Use hardware-accelerated encryption (e.g., Intel SGX, AWS Nitro Enclaves).         |
| **Backup & Recovery**       | Encrypted backups must be securely stored and decryptable.                  | Rotate keys periodically; use key versioning for auditability.                     |

### **2. In-Transit Encryption**
| **Component**               | **Description**                                                                 | **Implementation**                                                                 |
|-----------------------------|-------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **TLS/SSL**                 | Encrypts data in transit (HTTP → HTTPS, gRPC → gRPCs).                        | Enforce TLS 1.2+; use **Let’s Encrypt** for certificates.                          |
| **Mutual TLS (mTLS)**       | Server and client authenticate each other.                                   | Deploy internal CA (e.g., HashiCorp Vault PKI) or use cloud services (AWS ACM).     |
| **API Security**            | Protects REST/gRPC APIs with encryption and authentication.                  | Use **JWT/OAuth 2.0** for API keys; enforce TLS for all endpoints.                  |
| **Network Segmentation**    | Isolates sensitive traffic (e.g., VPCs, firewalls).                         | Restrict traffic to private endpoints; use **AWS PrivateLink** or **VPC Peering**.  |
| **Logging & Monitoring**    | Detects anomalies (e.g., unencrypted traffic, MITM attempts).                | Use tools like **Wireshark, CloudTrail, or Prometheus/Grafana**.                     |

---
## **Schema Reference (Key Components)**

### **At-Rest Encryption Schema**
| Field               | Type      | Description                                                                 | Example Values                          |
|---------------------|-----------|-----------------------------------------------------------------------------|------------------------------------------|
| **EncryptionMethod** | String    | Algorithm used (e.g., AES-256, ECC).                                       | `"AES-256-GCM"`                         |
| **KeyVault**        | String    | Key management service (HSM, cloud KMS).                                  | `"aws_kms:arn:aws:kms:..."`              |
| **KeyRotationPolicy** | String   | How often keys are rotated (e.g., 90-day).                               | `"365"`                                 |
| **StorageBackend**  | String    | Where data is stored (DB, filesystem, cloud).                           | `"sqlite3", "s3"`                       |
| **Transparent**     | Boolean   | Whether encryption is automatic (true) or manual.                       | `true`                                  |

### **In-Transit Encryption Schema**
| Field               | Type      | Description                                                                 | Example Values                          |
|---------------------|-----------|-----------------------------------------------------------------------------|------------------------------------------|
| **Protocol**        | String    | Encryption protocol (TLS, mTLS, IPSec).                                    | `"TLSv1.3"`                             |
| **CertificateSource** | String   | Where certs are issued (CA, Vault).                                       | `"letsencrypt"`                         |
| **ValidationMode**  | String    | How client/server auth is enforced (none, certificate, mutual).            | `"mutual"`                              |
| **NetworkPolicy**   | Array     | Rules for allowed traffic (ports, IPs).                                   | `[{ "port": 443, "protocol": "TCP" }]` |
| **AuditLogEnabled** | Boolean   | Whether connection logs are enabled.                                      | `true`                                  |

---

## **Query Examples**

### **1. Check Database Encryption Status (SQL)**
```sql
-- Verify if a database column is encrypted (PostgreSQL)
SELECT column_name,
       pgp_is_symmetric_key_encrypted(column_name) AS is_encrypted
FROM information_schema.columns
WHERE table_name = 'sensitive_data';
```
**Output:**
```
| column_name   | is_encrypted |
|---------------|--------------|
| user_credentials | true         |
| payment_data    | false        |
```

### **2. Validate TLS Configuration (OpenSSL)**
```bash
# Check if a server supports TLS 1.3
openssl s_client -connect example.com:443 -tls1_3
```
**Output:**
```
...
Protocol  TLSv1.3
Cipher   TLS_AES_256_GCM_SHA384
...
```

### **3. Audit Encrypted Traffic (Wireshark Filter)**
```bash
# Capture HTTPS traffic (TLS decrypted if certs are provided)
wireshark -k -i eth0 -f "tls && http"
```
**Key Filter Flags:**
- `tls.handshake.type == 1` (Client Hello)
- `tls.record.layer == 1` (Application Data)

### **4. Rotate Encryption Keys (AWS CLI)**
```bash
# Rotate a KMS key and re-encrypt existing data
aws kms disable-key-rotation --key-id alias/my-app-key
aws kms enable-key-rotation --key-id alias/my-app-key

# Re-encrypt data (example for DynamoDB)
aws dynamodb update-continuous-backups \
  --table-name Users \
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true
```

---

## **Related Patterns**
1. **[Secure Key Management]** – Centralized key storage (HSMs, Vault).
2. **[Zero Trust Architecture]** – Assume breach; enforce least-privilege access.
3. **[Data Masking]** – Redact sensitive fields in logs/dashboards.
4. **[Secure APIs]** – API gateways with mTLS and rate-limiting.
5. **[Network Hardening]** – Firewall rules, VPC isolation, and DDoS protection.

---
## **Best Practices**
- **At-Rest:**
  - Use **AES-256** for symmetric encryption; **ECC-384** for asymmetric.
  - Rotate keys annually or per compliance requirements.
  - Encrypt backups separately from primary storage.
- **In-Transit:**
  - Enforce **TLS 1.2/1.3** everywhere; disable older protocols (SSLv3, TLS 1.0/1.1).
  - Use **short-lived certificates** (≤90 days) for APIs.
  - Monitor for **TLS downgrade attacks** (e.g., via `SSLv3_RECORD`.
- **Hybrid Approach:**
  - Combine at-rest (DB encryption) + in-transit (TLS) for end-to-end security.

---
## **Troubleshooting**
| **Issue**                          | **Diagnostic Command**                          | **Solution**                                      |
|------------------------------------|------------------------------------------------|--------------------------------------------------|
| Database queries slow due to encryption | `EXPLAIN ANALYZE SELECT ...;`                | Use columnar storage (e.g., ClickHouse) for faster decryption. |
| TLS handshake fails                 | `openssl s_client -connect host:port -debug` | Update certificates or adjust cipher suites (`SSL_CTX_set_cipher_list`). |
| Key rotation errors                | `aws kms describe-key --key-id alias/key-name` | Check key state (`Enabled`, `PendingDeletion`).   |
| Unencrypted traffic in logs        | `tcpdump -i eth0 port 80`                       | Redirect HTTP to HTTPS; block non-TLS ports.     |