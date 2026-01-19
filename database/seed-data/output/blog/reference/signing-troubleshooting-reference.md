# **[Pattern] Signing Troubleshooting Reference Guide**

---

## **Overview**
This guide provides a **structured troubleshooting approach** for common **signing-related issues** in software development, infrastructure, and deployment workflows. Signing ensures data integrity, authenticity, and non-repudiation, but failures can occur due to misconfigurations, key management errors, or tooling issues. This guide categorizes problems by **type (e.g., signing errors, verification failures, certificate issues)** and provides **step-by-step debugging techniques**, **validation steps**, and **best practices** to resolve them efficiently.

---

## **Implementation Details**

### **1. Common Signing Failure Scenarios**
Signing issues typically fall under one of the following categories:

| **Failure Type**          | **Cause**                                                                 | **Example Symptoms**                                                                 |
|---------------------------|---------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| **Key Generation Errors**  | Incorrect key pair creation, improper algorithm selection, or expired keys. | `Error: Failed to generate RSA key: Key size too small`                             |
| **Signing Failures**      | Incorrect private key usage, corrupted signatures, or wrong digest algorithm. | `Failed to sign request: Invalid signature`                                          |
| **Verification Errors**   | Mismatched public keys, tampered data, or incorrect HMAC/SHA checks.       | `Verification failed: Public key does not match`                                    |
| **Certificate Issues**    | Expired certificates, revoked certificates, or misconfigured trust stores.  | `SSL handshake failed: Certificate expired`                                          |
| **Tooling Errors**        | Misconfigured CLI tools (e.g., `gpg`, `openssl`, `signtool`), version mismatches. | `signtool: Unrecognized option`                                                     |
| **Permission Errors**     | Missing access to key files, restricted IAM roles, or filesystem permissions. | `Permission denied: /path/to/private-key.p8`                                        |

---

### **2. Troubleshooting Workflow**
Follow this **step-by-step debug process** for signing issues:

### **Step 1: Identify the Error**
- **Log Analysis**: Check error logs for specific messages (e.g., `java.security.KeyStoreException`, `GPG: No secret key`).
- **Tool Output**: Capture full CLI output (e.g., `openssl verify -verbose`).

### **Step 2: Validate Dependencies**
| **Component**       | **Check**                                                                 | **Tools/Commands**                                                                 |
|---------------------|---------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Cryptographic Libraries** | Verify installed versions (e.g., OpenSSL 3.0 vs. 1.1).                  | `openssl version`, `brew list openssl`                                              |
| **Key Storage**     | Ensure keys are in valid formats (PEM, PFX, P12).                     | `openssl pkcs12 -info -in key.p12`                                                  |
| **Certificate Authority (CA)** | Check if root/intermediate CAs are trusted.              | `openssl x509 -in cert.pem -text -noout | grep Authority`                           |
| **Tool Configuration** | Review config files (e.g., `~/.gnupg/gpg.conf`).                     | `cat ~/.gnupg/gpg.conf`                                                            |

### **Step 3: Key-Specific Debugging**
#### **A. Private Key Issues**
- **Symptoms**: Signing failures, `RSASSA-PKCS1-v1_5` decryption errors.
- **Debug Steps**:
  1. **Export Key for Verification**:
     ```bash
     openssl rsa -in private_key.pem -check
     ```
  2. **Test Key Pair Integrity**:
     ```bash
     echo "test" | openssl rsautl -sign -inkey private_key.pem -keyform PEM -out sig.bin
     echo "test" | openssl rsautl -verify -inkey public_key.pem -in sig.bin -keyform PEM
     ```
  3. **Check Key Strength**:
     ```bash
     openssl rsa -in private_key.pem -text | grep "RSA key" | awk '{print $NF}'
     ```
     *(Minimum: 2048-bit for RSA; 256-bit for ECDSA.)*

#### **B. Certificate Verification Failures**
- **Symptoms**: `Certificate has expired` or `Untrusted issuer`.
- **Debug Steps**:
  1. **Inspect Certificate Chain**:
     ```bash
     openssl x509 -in cert.pem -text -noout
     ```
  2. **Verify Trust**:
     ```bash
     openssl verify -CAfile trusts.pem cert.pem
     ```
  3. **Check Expiry Date**:
     ```bash
     openssl x509 -enddate -noout -in cert.pem
     ```

### **Step 4: Signing/Verification Operations**
| **Operation**       | **Command Template**                                                                 | **Example**                                                                         |
|---------------------|-------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------|
| **Sign a File**     | `openssl dgst -sha256 -sign private_key.pem -out sig.bin input_file`                 | `openssl dgst -sha256 -sign key.pem -out sig.bin `/etc/passwd`                     |
| **Verify Signature**| `openssl dgst -sha256 -verify public_key.pem -signature sig.bin input_file`       | `openssl dgst -sha256 -verify pub.pem -signature sig.bin `/etc/passwd``           |
| **Sign with GPG**   | `gpg --detach-sign --armor -u <key-id> file.txt`                                    | `gpg --detach-sign --armor -u Alice file.txt`                                     |
| **Verify GPG Sig**  | `gpg --verify file.txt.asc file.txt`                                                 | `gpg --verify report.asc report.txt`                                               |

### **Step 5: Environment-Specific Fixes**
| **Environment**      | **Troubleshooting Focus**                                                                 | **Actions**                                                                          |
|----------------------|-----------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------|
| **CI/CD Pipelines**  | Secret management, cached tools, permission issues.                                    | Ensure `~/.gnupg` or `~/.m2` is cached; use `gpg --batch --no-tty` mode.          |
| **Containerized Apps** | Key mounting, volume permissions.                                                    | Use `docker run --mount type=bind,source=/path/to/keys,target=/keys`                |
| **Cloud Platforms**  | IAM roles, KMS permissions, metadata service access.                                   | Attach policies to keys (e.g., AWS KMS: `kms:Sign`).                              |

---

## **Schema Reference**
Below are **data structures** commonly used in signing workflows.

| **Schema Name**       | **Fields**                                                                                     | **Description**                                                                       |
|-----------------------|------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| **KeyPair**           | `type` (RSA/ECDSA), `size` (bits), `publicKey` (PEM), `privateKey` (PEM), `createdAt` (ISO8601) | Represents a cryptographic key pair for signing.                                     |
| **Signature**         | `algorithm` (RSA-SHA256), `digest` (Base64), `signedData` (Base64), `timestamp` (ISO8601)       | Stores metadata for a generated signature.                                           |
| **Certificate**       | `subject` (DN), `issuer` (DN), `serial` (hex), `notBefore`/`notAfter` (ISO8601), `publicKey` | Defines a X.509 certificate with validity and trust information.                     |
| **GPG Keyring**       | `userId` (string), `keyId` (hex), `trusted` (bool), `expires` (ISO8601)                     | Represents a GPG key with trust flags and expiry.                                   |
| **SigningConfig**     | `algorithm` (string), `keyId` (string), `hash` (SHA-256), `outputFormat` (PEM/DER)         | Configuration for signing operations.                                                |

---

## **Query Examples**
### **1. Check Key Validity with OpenSSL**
```bash
# Validate RSA private key
openssl rsa -in private_key.pem -check -noout

# Verify public/private key pair
echo "test" | openssl rsautl -sign -inkey private_key.pem -out sig.bin
echo "test" | openssl rsautl -verify -inkey public_key.pem -in sig.bin
```

### **2. Debug GPG Signing**
```bash
# List imported GPG keys
gpg --list-keys

# Sign a file and verify
echo "Hello" > test.txt
gpg --detach-sign --armor -u Alice test.txt  # Generates test.txt.asc
gpg --verify test.txt.asc test.txt          # Verifies signature
```

### **3. Troubleshoot Certificate Chains**
```bash
# Check certificate validity
openssl x509 -enddate -noout -in cert.pem

# Verify chain trust
openssl verify -CAfile root_ca.pem cert.pem
```

### **4. AWS KMS Signing Troubleshooting**
```bash
# List KMS keys
aws kms list-keys

# Sign data with KMS
aws kms sign --key-id alias/my-key --signing-algorithm RSASSA-PSS-SHA256 --input "Hello" --output sig.bin
aws kms verify --key-id alias/my-key --signing-algorithm RSASSA-PSS-SHA256 --input "Hello" --signature sig.bin
```

### **5. Docker Container Signing**
```bash
# Mount keys into container
docker run -v /path/to/keys:/keys my-image

# Sign in container
cat /keys/private_key.pem | docker sign --key-pem -
```

---

## **Related Patterns**
| **Pattern Name**               | **Description**                                                                                     | **When to Use**                                                                         |
|---------------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| **[Key Management Best Practices]** | Guidelines for generating, rotating, and storing keys securely.                                   | Before implementing signing to avoid future key-related issues.                        |
| **[Digital Envelope Pattern]**    | Encrypting data with keys to ensure confidentiality before signing.                                | When signing sensitive data requires additional security layers.                       |
| **[Certificate Authority (CA) Setup]** | Setting up a private CA for internal signing.                                                      | For enterprise environments needing self-signed certificates.                           |
| **[CI/CD Signing Automation]**    | Integrating signing into build pipelines (e.g., GitHub Actions, GitLab CI).                     | For automated software deployment with signing verification.                           |
| **[JWT Validation]**             | Validating JSON Web Tokens (JWTs) using public keys.                                              | When working with API authentication/authorization.                                     |

---

## **Best Practices**
1. **Key Rotation**: Rotate keys every **6–12 months** (or per security policy).
2. **Least Privilege**: Restrict key access (e.g., IAM policies, filesystem permissions).
3. **Tooling Updates**: Keep signing tools (e.g., OpenSSL, GPG) updated to avoid deprecated algorithms.
4. **Logging**: Log signing operations for auditing (e.g., `gpg --logger-file /var/log/gpg.log`).
5. **Backup Keys**: Store backups offline in **air-gapped systems**.
6. **Algorithm Selection**: Prefer **ECDSA-256** or **RSA-3072** over weaker options (e.g., SHA-1).
7. **Validation**: Always verify signatures in **production environments** before deployment.