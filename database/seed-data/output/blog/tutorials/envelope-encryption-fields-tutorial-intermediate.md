```markdown
# **Envelope Encryption for Fields: Secure Data with Zero Downtime Key Rotation**

*How FraiseQL implements field-level encryption with AES-256-GCM and multi-cloud KMS support*

---

## **Introduction**

Sensitive data—like SSNs, credit card numbers, or medical records—must be protected *at rest* in databases. But storing plaintext data in production violates compliance standards (e.g., PCI DSS, HIPAA, GDPR) and risks exposure in breaches.

Traditional approaches like full-database encryption (FDE) are too coarse-grained—they lock down *all* data, making queries slower and complicating operations like backups. What’s needed is **fine-grained security**: encrypting only the fields that matter, without sacrificing performance or flexibility.

This is where the **Envelope Encryption for Fields** pattern comes in. It securely encrypts individual columns while keeping metadata (e.g., table schemas) unencrypted, enabling efficient querying and zero-downtime key rotation.

In this post, we’ll explore:
- The problem with plaintext sensitive data
- How FraiseQL implements envelope encryption with **AES-256-GCM** for data and **KMS-backed key management** (Vault, AWS KMS, GCP KMS)
- Practical code examples for encryption, decryption, and zero-downtime key rotation
- Common pitfalls and how to avoid them

---

## **The Problem: Why Plaintext Data is a Security Risk**

### **Compliance Violations**
Regulations like **PCI DSS (Payment Card Industry Data Security Standard)** and **GDPR (General Data Protection Regulation)** mandate strict protections for sensitive data. Storing credit card numbers or PII in plaintext is a **Level 1 breach risk** under PCI DSS—even if the database is "securely hosted."

### **Performance Overheads**
Full-database encryption (FDE) encrypts *everything*, slowing down reads, backups, and migrations. For example, encrypting a petabyte-scale analytics database could add **10x latency** to queries.

### **Key Management Challenges**
Traditional solutions require:
- **Manual key rotation** (risky, often skipped)
- **Single points of failure** (e.g., a lost encryption key = lost data)
- **Vendor lock-in** (e.g., AWS KMS may not support hybrid clouds)

### **Zero-Downtime Rotation is Hard**
If you rotate a database encryption key, *everything* must re-encrypt. This can take hours—or even days—and requires offline backups. **This is unacceptable for production systems.**

---

## **The Solution: Envelope Encryption for Fields**

### **Core Idea**
Instead of encrypting the entire database, we encrypt **only the sensitive fields** using **envelope encryption**:
1. **Data Key (DEK)**: A random AES-256-GCM key encrypts the actual data.
2. **Key Encryption Key (KEK)**: A long-lived key (stored in a **KMS**) encrypts the DEK.

When a query needs decrypted data:
1. The app fetches the KEK (from KMS).
2. The KEK decrypts the DEK.
3. The DEK decrypts the field.

### **Why AES-256-GCM?**
- **Authenticated Encryption**: Detects tampering.
- **Performance**: Faster than CBC mode (no padding overhead).
- **Modern Standard**: Widely supported in databases and libraries.

### **Why KMS for KEKs?**
- **Hardware-backed security**: KMS keys are never exposed.
- **Multi-cloud support**: Works with **HashiCorp Vault**, **AWS KMS**, and **GCP KMS**.
- **Audit logs**: Track who accessed which keys.

### **Zero-Downtime Rotation**
When a KEK is rotated:
1. A new KEK encrypts the **old DEK**.
2. The old KEK continues decrypting data until all DEKs are updated.

This happens **transparently**—no downtime.

---

## **Implementation Guide**

### **1. Setup the Encryption Schema**

We’ll store:
- `encrypted_data`: The field encrypted with AES-256-GCM.
- `dek_iv`: Initialization vector for AES-GCM.
- `dek_key_version`: Links to the KEK version.

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name TEXT,
    ssn_encrypted BYTEA,    -- Encrypted SSN
    ssn_dek_iv BYTEA,       -- IV for AES-GCM
    ssn_dek_key_version VARCHAR(36) -- Reference to KEK version
);
```

### **2. Encrypting Data (Application Layer)**

Here’s how FraiseQL handles encryption in Go:

```go
package fraise

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"encoding/hex"
	"github.com/go-aes/gcm"
	"log"
)

// EncryptField encrypts a sensitive field using AES-256-GCM.
func EncryptField(data []byte, dekKey []byte) ([]byte, []byte, error) {
	// Generate a random IV (96-bit for GCM)
	iv := make([]byte, gcm.NonceSize)
	if _, err := rand.Read(iv); err != nil {
		return nil, nil, err
	}

	// Encrypt data
	aesGCM, err := gcm.NewECDSAE256(dekKey)
	if err != nil {
		return nil, nil, err
	}

	ciphertext := aesGCM.Seal(nil, iv, data, nil)
	return ciphertext, iv, nil
}
```

### **3. Storing the DEK in KMS**

The DEK is encrypted with a KEK from KMS (e.g., AWS KMS):

```go
// EncryptDEKWithKEK encrypts the DEK using a KMS key.
func EncryptDEKWithKEK(dekKey []byte, kmsKeyID string) ([]byte, error) {
	// In a real system, use the KMS SDK (e.g., AWS KMS Go SDK)
	// For example:
	// client := kms.New(client.Config{Region: "us-west-2"})
	// resp, err := client.Encrypt(&kms.EncryptInput{
	//     KeyId:      aws.String(kmsKeyID),
	//     Plaintext:  dekKey,
	// })
	// return resp.CiphertextBlob, err
	return []byte{}, nil // Simplified for example
}
```

### **4. Inserting Encrypted Data**

```go
func InsertUser(name, ssn string) error {
	// 1. Generate a random DEK
	dekKey := make([]byte, 32)
	if _, err := rand.Read(dekKey); err != nil {
		return err
	}

	// 2. Encrypt the SSN
	ssnBytes := []byte(ssn)
	encryptedSSN, iv, err := EncryptField(ssnBytes, dekKey)
	if err != nil {
		return err
	}

	// 3. Encrypt the DEK with KMS
	dekEncrypted, err := EncryptDEKWithKEK(dekKey, "alias/fraise_kek")
	if err != nil {
		return err
	}

	// 4. Store in DB
	_, err = db.Exec(`
		INSERT INTO users (name, ssn_encrypted, ssn_dek_iv, ssn_dek_key_version)
		VALUES ($1, $2, $3, $4)
	`, name, encryptedSSN, iv, "v1")
	return err
}
```

### **5. Decrypting Data (Query Time)**

When querying the `users` table, FraiseQL:
1. Fetches the DEK from KMS using `ssn_dek_key_version`.
2. Decrypts the DEK with the KEK.
3. Decrypts the `ssn_encrypted` field.

```go
func DecryptUserSSN(userID int) (string, error) {
	var ssnEncrypted, iv, dekKeyVersion []byte
	err := db.QueryRow(`
		SELECT ssn_encrypted, ssn_dek_iv, ssn_dek_key_version
		FROM users WHERE id = $1
	`, userID).Scan(&ssnEncrypted, &iv, &dekKeyVersion)
	if err != nil {
		return "", err
	}

	// 1. Fetch the KEK from KMS (e.g., "v1")
	kek, err := KMSDecryptDEK(dekKeyVersion)
	if err != nil {
		return "", err
	}

	// 2. Decrypt the DEK
	aesGCM, err := gcm.New(kek, iv)
	if err != nil {
		return "", err
	}

	// 3. Decrypt the SSN
	ssnBytes, err := aesGCM.Open(nil, iv, ssnEncrypted, nil)
	if err != nil {
		return "", err
	}

	return string(ssnBytes), nil
}
```

---

## **Zero-Downtime Key Rotation**

### **Step 1: Generate a New KEK**
```go
// In KMS (AWS example):
// aws kms create-key --description "Fraise DEK KEK v2" --key-usage ENCRYPT_DECRYPT
```

### **Step 2: Encrypt Old DEKs with New KEK**
```go
func RotateKEK(oldKeyVersion, newKeyVersion string) error {
	// 1. List all DEKs encrypted with old KEK
	deks, err := ListDEKs(oldKeyVersion)
	if err != nil {
		return err
	}

	// 2. Re-encrypt each DEK with the new KEK
	for _, dek := range deks {
		dekEncrypted, err := EncryptDEKWithKEK(dek, newKeyVersion)
		if err != nil {
			return err
		}
		// Update DB record
	}
	return nil
}
```

### **Step 3: Update Applications to Use New KEK**
FraiseQL’s query planner automatically detects the KEK version and fetches the correct KEK from KMS.

---

## **Common Mistakes to Avoid**

### **1. Not Using Unique DEKs per Field**
❌ **Bad**: Reusing the same DEK for multiple fields.
✅ **Good**: Generate a **new DEK for every sensitive field** (even in the same row).

*Why?* If one DEK is compromised, only that field is exposed.

### **2. Skipping IVs or Using Predictable Ones**
❌ **Bad**: Hardcoding IVs or using zero IVs.
✅ **Good**: Generate a **random IV for each encryption**.

*Why?* GCM requires a unique IV per encryption.

### **3. Ignoring Key Versioning**
❌ **Bad**: Storing the KEK directly in the DB.
✅ **Good**: Use **versioned KEK references** (e.g., `ssn_dek_key_version`).

*Why?* Allows zero-downtime rotation.

### **4. Not Testing Decryption Failures**
❌ **Bad**: Assuming decryption always works.
✅ **Good**: Handle **tampering (GCM auth fails)** and **missing keys (KMS errors)** gracefully.

```go
// Example: Safe decryption with error handling
decrypted, err := aesGCM.Open(nil, iv, ciphertext, nil)
if err != nil {
    log.Printf("Decryption failed: %v", err) // Could be tampering or key rotation issue
    // Retry with fallback KEK if needed
}
```

### **5. Overlooking Performance**
❌ **Bad**: Encrypting **all** fields in high-frequency queries.
✅ **Good**: Only encrypt **what you need** (e.g., PII, not timestamps).

*Why?* Every encryption/decryption adds **microsecond latency**.

---

## **Key Takeaways**

✅ **Fine-grained security**: Encrypt only what you need.
✅ **Multi-cloud KMS support**: Works with **Vault, AWS KMS, GCP KMS**.
✅ **Zero-downtime rotation**: Smooth key updates without downtime.
✅ **Performance**: Avoids the overhead of full-database encryption.
✅ **Compliance-ready**: Meets **PCI DSS, HIPAA, GDPR** requirements.

⚠️ **Tradeoffs**:
- **Complexity**: More moving parts than plaintext storage.
- **Cold starts**: First decryption after key rotation may be slower.
- **Audit overhead**: KMS operations add logging.

---

## **Conclusion**

Envelope encryption for fields is the **sweet spot** between security and performance. By encrypting only sensitive data with **AES-256-GCM** and managing keys via **KMS**, FraiseQL balances compliance, performance, and flexibility.

### **Next Steps**
1. **Try it out**: Implement this pattern in your next project.
2. **Automate key rotation**: Use tools like **HashiCorp Vault** or **AWS KMS Aliases** for easier management.
3. **Monitor KMS usage**: Set up alerts for unusual decryption attempts.

For production-grade implementation, consider **FraiseQL’s built-in support** for envelope encryption with **multi-cloud KMS integration**. Stay secure—and happy coding!

---
**Further Reading**
- [AWS KMS Developer Guide](https://docs.aws.amazon.com/kms/latest/developerguide/)
- [NIST SP 800-38D (AES-GCM)](https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-38d.pdf)
- [PCI DSS Requirement 3.4](https://www.pcisecuritystandards.org/document_library?category=pcidss)

---
*Would you like a deeper dive into any specific part (e.g., KMS integration, performance benchmarks)? Let me know!*
```