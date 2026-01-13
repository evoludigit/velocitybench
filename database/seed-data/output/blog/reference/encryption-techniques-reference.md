# **[Pattern] Encryption Techniques Reference Guide**

---

## **Overview**
The **Encryption Techniques** pattern provides a structured approach to securing data by applying cryptographic algorithms, key management, and best practices for confidentiality, integrity, and non-repudiation. This guide covers essential encryption techniques—**symmetric, asymmetric, and hybrid encryption**, along with key derivation, secure storage, and algorithm selection. It serves as a reference for developers, security architects, and compliance teams implementing robust encryption workflows in applications, databases, and API communications.

Key use cases include:
- **Data-at-rest protection** (databases, backups)
- **Data-in-transit security** (TLS, API encryption)
- **Secure credential storage** (passwords, API keys)
- **Compliance adherence** (GDPR, HIPAA, PCI-DSS)

---

## **Core Schema Reference**
The following table summarizes the key components of encryption techniques.

| **Component**               | **Description**                                                                                     | **Parameters**                     | **Example Algorithms/Methods**                     |
|-----------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------|----------------------------------------------------|
| **Symmetric Encryption**    | Single-key encryption for speed (e.g., bulk data). Requires secure key exchange.                     | Block size, IV length, key size     | AES-256, ChaCha20, Blowfish                         |
| **Asymmetric Encryption**   | Public/private key pair for secure key exchange and digital signatures. Slower than symmetric.       | Key size, padding scheme            | RSA (2048/4096), ECC (NIST P-256), EdDSA            |
| **Key Derivation Function** | Strengthens keys via iterative hashing (prevents brute-force attacks).                                | Iteration count, salt, hash function | PBKDF2, Argon2, bcrypt, scrypt                     |
| **Hybrid Encryption**       | Combines symmetric + asymmetric for optimal performance and security (e.g., RSA + AES).             | Symmetric cipher + asymmetric key   | RSA-OAEP + AES-GCM                                  |
| **Hashing**                 | One-way function for integrity checks, passwords, and digital signatures.                          | Hash algorithm, salt                | SHA-3, BLAKE3, HMAC-SHA256                         |
| **Key Management**          | Secure storage, rotation, and distribution of cryptographic keys.                                    | Key storage (HSM, KMS, vault)      | AWS KMS, HashiCorp Vault, Thales HSM                |
| **Certificate Authority (CA)** | Trust framework for asymmetric encryption (e.g., TLS client-server authentication).              | Certificate validity, revocation    | Let’s Encrypt, DigiCert, custom PKI                 |
| **Secure Key Exchange**     | Protocols to establish shared secrets (e.g., Diffie-Hellman).                                       | Group parameters, key derivation    | TLS 1.3 (ECDHE), Signal Protocol                   |

---

## **Implementation Details**

### **1. Symmetric Encryption**
**Use Cases:** Bulk data encryption (files, databases, API payloads).
**How It Works:** A shared secret key encrypts/decrypts data efficiently.

#### **Best Practices**
- Use **AES-256-GCM** (authenticated encryption) for modern systems.
- Generate keys using **CSPRNG** (e.g., `secrets` in Python, `/dev/urandom` in Unix).
- Store keys securely (encrypted or in a **Hardware Security Module (HSM)**).

#### **Example (Python - `cryptography` library)**
```python
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os

# Generate a random key (AES-256)
key = os.urandom(32)  # 256-bit key

# Encrypt data
iv = os.urandom(16)   # Initialization Vector (IV)
cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
encryptor = cipher.encryptor()
ciphertext = encryptor.update(b"Sensitive Data") + encryptor.finalize()
tag = encryptor.tag  # Authentication tag (critical for integrity)

# Decrypt data
decryptor = cipher.decryptor()
plaintext = decryptor.update(ciphertext) + decryptor.finalize()
decryptor.authenticate(tag)  # Verify integrity
```

---

### **2. Asymmetric Encryption**
**Use Cases:** Secure key exchange, digital signatures, TLS.
**How It Works:** Public keys encrypt; private keys decrypt (or vice versa for signatures).

#### **Best Practices**
- Use **ECC (P-256 or P-384)** over RSA for equivalent security with smaller keys.
- Avoid **DES, 3DES, or RSA < 2048-bit** (vulnerable to brute-force).
- Never embed private keys in code; use **key vaults** (e.g., AWS KMS).

#### **Example (Python - `cryptography` library)**
```python
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

# Generate RSA key pair
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
public_key = private_key.public_key()

# Encrypt with public key
encrypted = public_key.encrypt(
    b"Secret Message",
    padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
)

# Decrypt with private key
decrypted = private_key.decrypt(
    encrypted,
    padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
)
```

---

### **3. Hybrid Encryption**
**Use Cases:** Combines symmetric speed with asymmetric security (e.g., TLS, PGP).
**How It Works:** Asymmetric encrypts a symmetric key; symmetric encrypts the data.

#### **Example (AES + RSA)**
```python
# Step 1: Generate a symmetric key (AES-256)
symmetric_key = os.urandom(32)

# Step 2: Encrypt the symmetric key with RSA
encrypted_key = public_key.encrypt(
    symmetric_key,
    padding.OAEP(...)
)

# Step 3: Encrypt data with AES
iv = os.urandom(16)
ciphertext = encrypt_with_aes(symmetric_key, b"Data", iv)
```

---

### **4. Key Derivation Functions (KDFs)**
**Use Cases:** Strengthen weak passwords/keys (e.g., hashing passwords).
**How It Works:** Applies iterative hashing with salt to resist brute-force.

#### **Example (PBKDF2 - Python)**
```python
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import hashlib

salt = os.urandom(16)
key = PBKDF2HMAC(
    algorithm=hashlib.sha256(),
    length=32,
    salt=salt,
    iterations=100000,
    backend=default_backend()
).derive(b"Password123!")
```

**Best KDFs:**
- **`bcrypt`/`scrypt`**: Memory-hard for GPU resistance.
- **`Argon2`**: Modern standard (winner of Password Hashing Competition).

---

### **5. Hashing & Digital Signatures**
**Use Cases:** Password storage, file integrity, non-repudiation.

#### **Example (HMAC-SHA256 for Integrity)**
```python
import hmac, hashlib
key = b"SecretKey"
message = b"Data to verify"
hmac_value = hmac.new(key, message, hashlib.sha256).digest()
```

#### **Example (Digital Signature - ECDSA)**
```python
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes

private_key = ec.generate_private_key(ec.SECP256R1())
public_key = private_key.public_key()

# Sign
signature = private_key.sign(
    b"Data",
    ec.ECDSA(hashes.SHA256())
)

# Verify
assert public_key.verify(signature, b"Data", ec.ECDSA(hashes.SHA256()))
```

---

### **6. Key Management**
**Best Practices:**
- **Never hardcode keys** in source code (use secrets management).
- **Rotate keys** regularly (e.g., annual for long-term keys).
- Use **HSMs** for high-security applications (e.g., banking).

#### **Example: AWS KMS**
```python
import boto3

client = boto3.client('kms')
response = client.encrypt(
    KeyId='alias/my-key',
    Plaintext=b"Data"
)
# Encrypts data using AWS-managed key.
```

---

## **Query Examples**
### **1. Encrypting a Database Column (SQL)**
```sql
-- SQL (PostgreSQL) with pgcrypto extension
SELECT pgp_sym_encrypt('Sensitive Data', 'AES_KEY', 'gcm');
-- Output: Encrypted data (tag included in GCM mode)
```

### **2. Generating an RSA Keypair (OpenSSL)**
```sh
# Generate private key
openssl genpkey -algorithm RSA -out private.pem -pkeyopt rsa_keygen_bits:2048

# Extract public key
openssl rsa -pubout -in private.pem -out public.pem
```

### **3. Verifying a Digital Signature (OpenSSL)**
```sh
# Sign data
openssl dgst -sign private.pem -sha256 -out signature.bin "data.txt"

# Verify
openssl dgst -verify public.pem -sha256 -signature signature.bin "data.txt"
```

---

## **Related Patterns**
1. **[Secure Key Storage]** – Guidelines for managing cryptographic keys in distributed systems.
2. **[TLS/SSL Configuration]** – Best practices for encrypting network traffic (e.g., HTTPS).
3. **[Password Hashing]** – Secure storage of user credentials (e.g., bcrypt, Argon2).
4. **[Zero-Knowledge Proofs]** – Authentication without exposing secrets.
5. **[End-to-End Encryption]** – Encrypting messages from sender to recipient (e.g., Signal Protocol).
6. **[Data Masking]** – Redacting sensitive data in logs/databases.

---

## **Compliance Notes**
| **Standard**       | **Encryption Requirements**                                                                 |
|--------------------|-------------------------------------------------------------------------------------------|
| **GDPR**           | Pseudonymization of PII; AES-256 for data-at-rest.                                        |
| **HIPAA**          | Encryption of PHI (e.g., AES-256, RSA 2048-bit).                                          |
| **PCI-DSS**        | Encrypt PAN (credit card data) in transit and at rest (TLS 1.2+, AES 128-bit minimum).    |
| **FIPS 140-2/3**   | Approved algorithms (e.g., AES-NI, SHA-3) for government/military use.                    |

---
**Appendix:** *For algorithm selection, consult [NIST SP 800-175](https://csrc.nist.gov/publications/detail/sp/800-175/final) or [Cryptography Research](https://cryptography.io/).*