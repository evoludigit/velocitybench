```markdown
---
title: "Envelope Encryption for Fields: A Practical Guide to Protecting Sensitive Data"
date: 2023-11-15
tags: ["database", "security", "encryption", "patterns", "backend", "api"]
author: "Alex Martin"
description: "Learn how to implement field-level encryption with envelope encryption (AES-256-GCM + KMS) to secure sensitive data in databases while ensuring compliance and zero-downtime key rotation."
---

# **Envelope Encryption for Fields: A Practical Guide to Protecting Sensitive Data**

Imagine you're building a healthcare application that stores patient data. The system must comply with **HIPAA**, but you're worried about storing sensitive information like SSNs or medical records in plaintext. Storing encrypted data everywhere—even in your database—can seem daunting. But what if we told you there’s a way to encrypt **only the fields that matter** while keeping the rest of your data accessible?

That’s where **envelope encryption** comes in. Instead of locking down an entire table or database, you encrypt **individual fields** on a row-by-row basis. This approach balances security and usability—you can still query and process data efficiently while keeping secrets safe.

In this guide, we’ll explore how **FraiseQL** implements **envelope encryption for fields** using **AES-256-GCM** for data encryption and **Key Management Services (KMS)** like **AWS KMS, HashiCorp Vault, or GCP KMS** for key storage. We’ll also cover **zero-downtime key rotation**, ensuring your system stays secure and compliant even when keys change.

Let’s dive in.

---

## **The Problem: Sensitive Data in Plaintext Violates Compliance**

Many applications store sensitive data in databases without proper encryption, exposing them to risks like:
- **Compliance violations** (HIPAA, GDPR, PCI-DSS)
- **Data breaches** (if credentials are compromised)
- **Regulatory fines** (heavy penalties for non-compliance)

While **column-level encryption** (like AWS KMS’s native encryption) works, it often encrypts **entire columns**, making queries slower and harder to manage. What if you only need to encrypt **specific fields** (e.g., `SSN` in a user table) but keep the rest accessible?

Enter **envelope encryption for fields**—a flexible way to encrypt only what matters while keeping other data usable.

---

## **The Solution: Envelope Encryption for Fields**

Envelope encryption is a **two-layer security approach**:
1. **Data Encryption Key (DEK)** – A random symmetric key (AES-256-GCM) that encrypts the actual data.
2. **Key Encryption Key (KEK)** – A long-term key stored securely in a **KMS** (like AWS KMS or HashiCorp Vault) that encrypts the DEK.

### **How It Works**
1. **When storing data**:
   - Generate a random **AES-256-GCM** key (DEK).
   - Encrypt the sensitive field (e.g., `SSN`) with the DEK.
   - Encrypt the DEK itself with the KEK from KMS.
   - Store both encrypted values in the database.

2. **When retrieving data**:
   - Fetch the encrypted DEK from the database.
   - Decrypt it using the KEK from KMS.
   - Use the DEK to decrypt the sensitive field.

This ensures:
✅ **No plaintext data in the database**
✅ **Flexible encryption per field**
✅ **Key rotation without downtime**

---

## **Components & Solutions**

| Component               | Purpose                                                                 | Example Providers                     |
|-------------------------|-------------------------------------------------------------------------|---------------------------------------|
| **AES-256-GCM**         | Encrypts the actual data (fast, authenticated)                           | `crypto` (Node.js), `AES` (Java/Python) |
| **Key Management (KMS)**| Stores long-term keys securely (supports rotation)                     | AWS KMS, HashiCorp Vault, GCP KMS     |
| **Database Layer**      | Stores encrypted data without plaintext                                  | PostgreSQL, MySQL, FraiseDB          |
| **Application Logic**   | Handles encryption/decryption workflow                                   | Custom services or FraiseQL           |

---

## **Implementation Guide**

Let’s implement this in **Python with FraiseQL** (a hypothetical but realistic setup).

### **1. Setting Up FraiseQL with KMS Integration**

First, configure your **KMS provider** (e.g., AWS KMS):

```python
# Example: Using AWS KMS (aws-sdk-python)
import boto3

kms_client = boto3.client('kms')
arn = "arn:aws:kms:us-east-1:123456789012:key/abcd1234-5678-90ef-ghij-klmnopqrstuv"

def encrypt_kms_data(plaintext):
    response = kms_client.encrypt(
        KeyId=arn,
        Plaintext=plaintext
    )
    return response['CiphertextBlob']

def decrypt_kms_data(ciphertext):
    response = kms_client.decrypt(
        CiphertextBlob=ciphertext
    )
    return response['Plaintext'].decode()
```

### **2. Encrypting a Sensitive Field Before Storage**

When storing data (e.g., inserting a new user):

```python
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import os

def generate_aes_key():
    return os.urandom(32)  # 256-bit AES key

def encrypt_field(plaintext, aes_key):
    cipher = AES.new(aes_key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode())
    return {
        "ciphertext": ciphertext.hex(),
        "nonce": cipher.nonce.hex(),
        "tag": tag.hex()
    }

def store_user_encrypted(ssn, user_data):
    # 1. Generate a random AES key (DEK)
    aes_key = generate_aes_key()

    # 2. Encrypt the SSN with AES-GCM
    encrypted_ssn = encrypt_field(ssn, aes_key)
    encrypted_key = encrypt_kms_data(aes_key)  # Encrypt DEK with KMS

    # 3. Store encrypted data in the database
    query = """
    INSERT INTO users (name, encrypted_ssn_ciphertext, encrypted_ssn_nonce,
                      encrypted_ssn_tag, encrypted_aes_key)
    VALUES ($1, $2, $3, $4, $5)
    """
    db.execute(query, (
        user_data['name'],
        encrypted_ssn['ciphertext'],
        encrypted_ssn['nonce'],
        encrypted_ssn['tag'],
        encrypted_key
    ))
```

### **3. Decrypting Data When Retrieving**

When fetching and decrypting data:

```python
def decrypt_field(encrypted_data, aes_key):
    ciphertext = bytes.fromhex(encrypted_data['ciphertext'])
    nonce = bytes.fromhex(encrypted_data['nonce'])
    tag = bytes.fromhex(encrypted_data['tag'])

    cipher = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
    plaintext = cipher.decrypt_and_verify(ciphertext, tag)
    return plaintext.decode()

def fetch_and_decrypt_ssn(user_id):
    # 1. Fetch encrypted data from DB
    query = "SELECT encrypted_ssn_ciphertext, encrypted_ssn_nonce, encrypted_ssn_tag, encrypted_aes_key FROM users WHERE id = $1"
    row = db.execute(query, (user_id,)).fetchone()

    if not row:
        return None

    # 2. Decrypt the AES key with KMS
    aes_key = decrypt_kms_data(row['encrypted_aes_key'])

    # 3. Decrypt the SSN
    ssn_data = {
        'ciphertext': row['encrypted_ssn_ciphertext'],
        'nonce': row['encrypted_ssn_nonce'],
        'tag': row['encrypted_ssn_tag']
    }

    ssn = decrypt_field(ssn_data, aes_key)
    return ssn
```

### **4. Zero-Downtime Key Rotation**

To rotate keys without downtime:

```python
def rotate_encryption_keys(user_id):
    # 1. Generate a new AES key
    new_aes_key = generate_aes_key()

    # 2. Encrypt the old DEK with the new KMS key
    old_aes_key = decrypt_kms_data(row['encrypted_aes_key'])
    new_encrypted_old_key = encrypt_kms_data(old_aes_key)

    # 3. Store both old and new encrypted DEKs temporarily
    db.execute("""
    UPDATE users
    SET encrypted_aes_key = $1, encrypted_aes_key_old = $2
    WHERE id = $3
    """, (encrypt_kms_data(new_aes_key), new_encrypted_old_key, user_id))

    # 4. Later, delete the old key (when all apps have migrated)
    db.execute("UPDATE users SET encrypted_aes_key_old = NULL WHERE id = $1", (user_id,))
```

---

## **Common Mistakes to Avoid**

❌ **Hardcoding encryption keys** – Always use a **KMS** for key management.
❌ **Reusing the same DEK for multiple fields** – Each field should have a unique DEK.
❌ **Not handling key rotation gracefully** – Always test **zero-downtime rotation** before production.
❌ **Ignoring authentication tags in AES-GCM** – Always verify integrity to prevent tampering.
❌ **Over-encrypting** – Only encrypt what’s truly sensitive (avoid performance overhead).

---

## **Key Takeaways**

✔ **Envelope encryption** encrypts **fields individually**, not entire tables.
✔ **AES-256-GCM** provides **fast, authenticated encryption**.
✔ **KMS (AWS/GCP/Vault)** secures the **long-term keys**.
✔ **Zero-downtime rotation** ensures security during key changes.
✔ **Never store plaintext data**—even in logs or backups.

---

## **Conclusion**

Envelope encryption for fields is a **practical, efficient way** to secure sensitive data in databases while maintaining flexibility. By combining **AES-256-GCM** with **KMS-backed keys**, you ensure **strong encryption** without sacrificing performance.

**Next Steps:**
- Experiment with **FraiseQL’s built-in field-level encryption** (if available).
- Test **key rotation** in a staging environment before production.
- Audit your app to **identify all sensitive fields** that need protection.

Start small, but **secure everything that matters**. Your users—and regulators—will thank you.

---
```

Would you like me to add more details on any specific part, like deeper dives into the cryptographic functions or a different programming language example?