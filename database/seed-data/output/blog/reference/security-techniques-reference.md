# **[Pattern] Security Techniques - Reference Guide**

---

## **Overview**
The **Security Techniques** pattern defines a structured approach to implementing security controls across applications, environments, and infrastructure. It consolidates best practices for authentication, authorization, data protection, and threat mitigation into reusable techniques. This guide outlines key security techniques, their implementation details, and requirements to ensure compliance with security standards while maintaining application usability and scalability.

Security Techniques are categorized into **five core domains**:
1. **Authentication & Identity Management** (Proving users/entities are who they claim to be)
2. **Authorization & Access Control** (Ensuring users/entities have only necessary permissions)
3. **Data Protection & Encryption** (Securing data at rest and in transit)
4. **Network & Infrastructure Security** (Defending against external and internal threats)
5. **Monitoring & Incident Response** (Detecting, responding to, and recovering from security breaches)

Each technique is designed to be modular, allowing selection based on threat models, regulatory requirements (e.g., GDPR, HIPAA), and organizational policies.

---

## **Schema Reference**

Below is the standardized schema for defining **Security Techniques**. Each entry includes **mandatory** and **optional** attributes. Techniques may extend this schema based on domain-specific needs.

| **Field**                     | **Type**       | **Description**                                                                                     | **Mandatory** | **Default/Notes**                          |
|-------------------------------|----------------|-----------------------------------------------------------------------------------------------------|----------------|--------------------------------------------|
| `technique_id`                | String         | Unique identifier (e.g., `auth-2fa`, `enc-aes256`, `net-firewall`).                               | ✅ Yes          | Follows `[domain]-[name]` convention.      |
| `name`                        | String         | Human-readable name (e.g., "Multi-Factor Authentication", "TLS 1.3").                           | ✅ Yes          | —                                          |
| `domain`                      | String         | Security domain (e.g., `auth`, `enc`, `net`).                                                   | ✅ Yes          | See **Overview** for valid domains.        |
| `description`                 | String         | Technical summary of the technique and its purpose.                                               | ✅ Yes          | —                                          |
| `threat_model`                | String[]       | Threats this technique mitigates (e.g., "credential theft", "man-in-the-middle", "data leakage"). | ❌ No           | See [Common Threats](#common-threats).     |
| `compliance`                  | String[]       | Regulatory standards supported (e.g., "GDPR", "PCI-DSS", "NIST SP 800-53").                       | ❌ No           | —                                          |
| `implementation`              | Object         | Technical details (methods, tools, configurations).                                              | ✅ Yes          | —                                          |
| `implementation.categories`    | String[]       | Deployment contexts (e.g., "server-side", "client-side", "database").                          | ❌ No           | —                                          |
| `implementation.steps`        | Array[Step]    | Step-by-step instructions for deployment.                                                        | ✅ Yes          | —                                          |
| `implementation.dependencies` | String[]       | Required services, libraries, or hardware (e.g., "TLS 1.3", "HMAC-SHA256").                     | ❌ No           | —                                          |
| `performance_impact`          | Object         | Metrics on latency, resource usage, or scalability.                                               | ❌ No           | —                                          |
| `cost`                        | Object         | Licensing, operational, or infrastructure costs.                                                 | ❌ No           | —                                          |
| `alternatives`                | String[]       | Similar techniques with trade-offs (e.g., "OAuth 2.0 vs. SAML").                                 | ❌ No           | —                                          |
| `examples`                    | Object         | Real-world or code examples.                                                                     | ❌ No           | —                                          |
| `deprecated`                  | Boolean        | Whether this technique is outdated.                                                              | ❌ No           | Default: `false`.                        |
| `version`                     | String         | Schema version (e.g., "1.2").                                                                      | ❌ No           | Default: "1.0".                          |

---

### **Step Schema (Nested in `implementation.steps`)**
| **Field**     | **Type**   | **Description**                                                                                     |
|----------------|------------|-----------------------------------------------------------------------------------------------------|
| `step_id`      | String     | Unique identifier for the step (e.g., `step-1`).                                                  |
| `description`  | String     | What the step accomplishes.                                                                       |
| `actions`      | Array      | Detailed instructions (code snippets, CLI commands, or config YAML/JSON/XML).                    |
| `validation`   | Object     | How to verify the step was completed correctly.                                                    |
| `validation.method` | String     | (e.g., "audit log", "unit test", "vulnerability scan").                                          |
| `validation.tool`  | String     | (e.g., "OpenSSL", "OWASP ZAP", "Custom script").                                                  |

---

## **Key Techniques**

### **1. Authentication & Identity Management**
| **Technique ID** | `auth-2fa`                        |
|-------------------|-----------------------------------|
| **Name**          | Multi-Factor Authentication (MFA) |
| **Description**   | Requires two or more verification factors (e.g., password + SMS code + biometric). Mitigates brute-force attacks and credential theft. |
| **Threat Model**  | Credential theft, credential stuffing, session hijacking. |
| **Compliance**    | GDPR, NIST SP 800-63B, PCI-DSS. |
| **Implementation** |                                                                                       |
| `categories`      | Server-side, client-side.                                                               |
| `steps`           |                                                                                       |
| - `step-1`        | **Enable MFA provider** (e.g., Google Authenticator, Duo, or FIDO2).                     |
|   `actions`       |                                                                                       |
|   - Install provider SDK (e.g., `pip install pyotp`).                                     |
|   - Configure backend to validate time-based OTPs (TOTP) or hardware keys.                |
| - `step-2`        | **Enforce MFA for all user sessions**.                                                  |
|   `actions`       |                                                                                       |
|   - Update auth middleware (e.g., Flask `flask-login`, Spring Security).                    |
|   - Redirect users to MFA prompt after password login.                                      |
|   `validation`    |                                                                                       |
|   - `method`: "Unit test"                                                                |
|     `tool`: Custom test suite verifying MFA flow.                                          |
| **Performance Impact** | Minimal latency (~2-5s for TOTP generation).                                             |
| **Cost**          | Free (open-source) or paid (enterprise-grade providers like Okta).                       |
| **Alternatives**  | Single-sign-on (SSO) via OAuth 2.0, hardware security keys (FIDO2).                       |

---

### **2. Data Protection & Encryption**
| **Technique ID** | `enc-aes256-gcm`                     |
|-------------------|--------------------------------------|
| **Name**          | AES-256-GCM Symmetric Encryption     |
| **Description**   | Encrypts data at rest using AES-256 in Galois/Counter Mode (GCM), providing authenticated encryption. |
| **Threat Model**  | Data leakage, tampering, side-channel attacks. |
| **Compliance**    | GDPR, FIPS 140-2, HIPAA.             |
| **Implementation** |                                                                                      |
| `categories`      | Database, storage (e.g., S3, filesystems), client-side encryption.                     |
| `steps`           |                                                                                      |
| - `step-1`        | **Generate secure key material**.                                                 |
|   `actions`       |                                                                                      |
|   - Use `openssl rand -hex 32` to generate a 256-bit key.                                |
|   - Store keys in a **Hardware Security Module (HSM)** or **Key Management Service (KMS)** like AWS KMS. |
| - `step-2`        | **Encrypt data before storage**.                                                 |
|   `actions`       |                                                                                      |
|   - **Python (PyCryptodome):**                                                            |
|     ```python
> from Crypto.Cipher import AES
> from Crypto.Random import get_random_bytes
>
> key = b'32_byte_key_here'  # Replace with secure key
> iv = get_random_bytes(12)   # GCM requires 12-byte IV
> cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
> ciphertext, tag = cipher.encrypt_and_digest(b"Sensitive data")
> ```                                                                                     |
|   `validation`    |                                                                                      |
|   - `method`: "Vulnerability scan"                                                      |
|     `tool`: `OWASP ZAP` or `Bandit` (for Python).                                        |
| **Performance Impact** | Slight overhead (~10-20% CPU for large datasets).                                      |
| **Cost**          | Free (self-managed) or paid (AWS KMS: ~$1/GB/month).                                  |
| **Alternatives**  | AES-256-CBC (with HMAC for integrity), Post-Quantum Cryptography (e.g., Kyber).      |

---

### **3. Network & Infrastructure Security**
| **Technique ID** | `net-tls13`                     |
|-------------------|---------------------------------|
| **Name**          | TLS 1.3 Protocol                |
| **Description**   | Encrypts data in transit using the latest TLS standard, reducing latency and mitigating attacks like POODLE and BEAST. |
| **Threat Model**  | Man-in-the-middle, downgrade attacks, session hijacking. |
| **Compliance**    | PCI-DSS, NIST SP 800-52 Rev 2.  |
| **Implementation** |                                                                                     |
| `categories`      | Web servers (Nginx, Apache), application proxies (Cloudflare, Envoy).               |
| `steps`           |                                                                                     |
| - `step-1`        | **Enable TLS 1.3 on endpoints**.                                                  |
|   `actions`       |                                                                                     |
|   - **Nginx:** Add to `nginx.conf`:                                                    |
|     ```nginx
> ssl_protocols TLSv1.3;
> ssl_ciphers 'TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256';
> ```                                                                                     |
|   - **Python (FastAPI):**                                                               |
|     ```python
> from fastapi import FastAPI
> from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
>
> app = FastAPI()
> app.add_middleware(HTTPSRedirectMiddleware)
> ```                                                                                     |
|   `validation`    |                                                                                     |
|   - `method`: "Audit log"                                                              |
|     `tool`: `SSL Labs Test` ([https://www.ssllabs.com/ssltest/](https://www.ssllabs.com/ssltest/)). |
| **Performance Impact** | Improved performance over TLS 1.2 (reduced handshake time).                          |
| **Cost**          | Included with most hosting providers (e.g., Let’s Encrypt).                          |
| **Alternatives**  | TLS 1.2 (deprecated for new deployments), QUIC (HTTP/3).                             |

---

## **Query Examples**
Use the following queries to retrieve or filter Security Techniques based on requirements.

### **1. Find All Techniques for Database Encryption**
```sql
SELECT *
FROM security_techniques
WHERE domain = 'enc'
  AND categories LIKE '%database%';
```
**Result:**
- `enc-aes256-gcm` (if configured for database)
- `enc-transit-sql` (TLS for SQL connections)

---

### **2. List MFA Techniques Compliant with PCI-DSS**
```sql
SELECT technique_id, name, description
FROM security_techniques
WHERE compliance LIKE '%PCI-DSS%'
  AND threat_model LIKE '%credential%';
```
**Result:**
- `auth-2fa` (Multi-Factor Authentication)

---

### **3. Find Low-Cost Techniques for Client-Side Security**
```sql
SELECT technique_id, name, cost
FROM security_techniques
WHERE categories LIKE '%client%'
  AND cost.currency = 'free';
```
**Result:**
- `auth-2fa` (with open-source providers)
- `enc-webcrypto` (Browser-based encryption)

---

## **Common Threats**
| **Threat**                  | **Defined in Techniques With**                                                                 |
|-----------------------------|-----------------------------------------------------------------------------------------------|
| Credential theft            | `auth-2fa`, `auth-password-policy`                                                         |
| Data leakage                | `enc-aes256-gcm`, `enc-field-level`                                                         |
| Man-in-the-middle           | `net-tls13`, `net-dns-over-tls`                                                              |
| Injection attacks           | `auth-http-header-validation`, `api-jwt-validation`                                          |
| Insider threats             | `auth-least-privilege`, `audit-logging`                                                      |

---

## **Related Patterns**
1. **[Zero Trust Architecture]**
   - Integrates Security Techniques like `auth-2fa` and `audit-logging` into a continuous verification model.
   - *See:* [Zero Trust Reference Guide](#).

2. **[Principle of Least Privilege]**
   - Works with techniques like `auth-least-privilege` and `enc-field-level` to minimize attack surface.

3. **[Defense in Depth]**
   - Combines multiple techniques (e.g., `net-tls13` + `enc-aes256-gcm` + `audit-logging`) for layered security.

4. **[Secret Management]**
   - Complements `enc-aes256-gcm` by securing encryption keys via `secret-hsm` or `secret-vault`.

5. **[Rate Limiting & Throttling]**
   - Mitigates brute-force attacks alongside `auth-2fa` or `auth-password-policy`.

---

## **Extensions & Customization**
- **Domain-Specific Techniques**: Extend the schema for edge cases (e.g., `iot-device-auth` for IoT devices).
- **Automated Enforcement**: Integrate techniques into CI/CD pipelines (e.g., SonarQube for static analysis).
- **Threat Adaptation**: Add techniques for emerging threats (e.g., `quantum-resistant-encryption`).

---
## **Versioning**
| **Version** | **Date**       | **Changes**                                                                                     |
|-------------|----------------|-------------------------------------------------------------------------------------------------|
| 1.0         | 2023-10-01     | Initial release with core techniques.                                                         |
| 1.1         | 2023-12-15     | Added `enc-webcrypto` and `net-quic` techniques.                                              |

---
**Note:** For updates, refer to the latest schema at [Security Patterns Registry](#).