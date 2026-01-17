```markdown
---
title: "Signing Approaches: Secure Your APIs Like a Pro (With Practical Examples)"
date: 2024-02-15
author: John Doe
tags: ["backend", "security", "api-design", "authentication", "jwt"]
description: "A deep dive into signing approaches for secure API design. Learn practical patterns, tradeoffs, and real-world examples for JWT, HMAC, and RSA signing."
---

# **Signing Approaches: Building Secure APIs Without the Headaches**

Insecure APIs are like open doors to your financial system—until they’re breached. Signing is the invisible guard dog that proves your API requests are legitimate, but not all approaches are created equal. As a backend engineer, you’ve probably heard terms like **HMAC**, **RSA**, **JWT**, and **ECDSA** thrown around, but do you *really* understand how they work—or when to use them?

This guide cuts through the noise. We’ll explore **practical signing approaches** for APIs, covering:
- When to use **HMAC vs. asymmetric keys** (and why HMAC isn’t always evil)
- How **JWT signing works** under the hood (and when it’s *not* the right tool)
- Real-world examples in **Go, Python, and Node.js**
- Tradeoffs like performance vs. security
- Common pitfalls (and how to avoid them)

By the end, you’ll know which signing approach fits your use case—and how to implement it *correctly*.

---

## **The Problem: Why Signing Matters (And When It Fails)**

Imagine this scenario: Your API serves as a payment processor, and a malicious actor intercepts an unsigned `POST /transfer` request. With no signature, they could **replay** or **forge** requests, draining accounts or altering inventory data. Signing prevents this by:

1. **Authenticating requests** – Verifying the sender is who they claim to be.
2. **Preventing tampering** – Detecting if data is altered in transit.
3. **Non-repudiation** – Ensuring the sender can’t deny sending the request.

But signing isn’t just about *doing it*—it’s about doing it **right**. Common mistakes lead to vulnerabilities:
- **Using weak keys** (e.g., `secret=password123` in HMAC).
- **Storing private keys insecurely** (e.g., in client-side code).
- **Ignoring key rotation** (leading to long-term exposure).
- **Assuming JWT is always secure** (it’s not, and misconfigurations abound).

Without proper signing, even well-designed APIs can become backdoors.

---

## **The Solution: Signing Approaches Explained**

Signing falls into two broad categories:
1. **Symmetric Signing (HMAC)** – Uses a shared secret (e.g., `HMAC-SHA256`).
2. **Asymmetric Signing (RSA/ECDSA)** – Uses a public/private key pair.

Each has tradeoffs. Let’s explore them with practical examples.

---

## **1. Symmetric Signing: HMAC in Action**

HMAC (Hash-based Message Authentication Code) is **fast** and **efficient**, but requires secure key management. It’s ideal for:
- Internal services where all parties trust a shared secret.
- Low-latency APIs (e.g., IoT, gaming).

### **How It Works**
1. A shared secret (`key`) and a message (`data`) are combined.
2. A cryptographic hash (e.g., SHA-256) produces a signature.
3. The client sends the signature alongside the request.
4. The server verifies the signature using the same `key`.

### **Example: HMAC in Go**
```go
package main

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
)

// Shared secret (stored securely, e.g., in environment variables)
const sharedSecret = "your-256-bit-secret-key-here"

func generateHMAC(data string) string {
	hash := hmac.New(sha256.New, []byte(sharedSecret))
	hash.Write([]byte(data))
	return hex.EncodeToString(hash.Sum(nil))
}

func verifyHMAC(data, signature string) bool {
	expectedSignature := generateHMAC(data)
	return hmac.Equal([]byte(expectedSignature), []byte(signature))
}

func main() {
	data := "transfer=100&to=alice"
	signature := generateHMAC(data)
	fmt.Printf("Signature: %s\n", signature)

	// Later, when verifying:
	fmt.Printf("Is valid? %t\n", verifyHMAC(data, signature))
}
```

### **Tradeoffs**
| **Pros**                          | **Cons**                          |
|-----------------------------------|-----------------------------------|
| Fast (~O(1) computation)          | Key distribution is tricky        |
| No need to manage public keys     | Single key compromise = full breach |
| Works well for internal services  | Not suitable for public APIs      |

**When to use HMAC?**
✅ Internal microservices
✅ Low-latency requirements
❌ Never for client-side apps (keys exposed to attackers)

---

## **2. Asymmetric Signing: RSA and ECDSA**

Asymmetric signing uses **public/private key pairs** where:
- The **private key** signs requests (kept secret).
- The **public key** verifies signatures (shared publicly).

RSA is **widely supported** but **slower**, while ECDSA offers **better performance** with smaller keys.

### **How It Works**
1. The client signs a message (`data`) with their **private key**.
2. The server verifies the signature using the **public key**.
3. If verification fails, the request is rejected.

### **Example: RSA in Python**
```python
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.backends import default_backend
import json

# Generate RSA key pair (do this once)
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
    backend=default_backend()
)
public_key = private_key.public_key()

# Sign a request
def sign_request(data: str, private_key) -> str:
    signature = private_key.sign(
        data.encode(),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return base64.b64encode(signature).decode()

# Verify a signature
def verify_signature(data: str, signature: str, public_key) -> bool:
    signature_bytes = base64.b64decode(signature)
    try:
        public_key.verify(
            signature_bytes,
            data.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except:
        return False

# Usage
data = json.dumps({"amount": 100, "to": "alice"})
signature = sign_request(data, private_key)
print(f"Signature: {signature}")

# Later, verify with the public key
print(f"Valid? {verify_signature(data, signature, public_key)}")
```

### **Tradeoffs**
| **Pros**                          | **Cons**                          |
|-----------------------------------|-----------------------------------|
| No shared secret needed           | Slower than HMAC (~100x)          |
| Scales to many clients           | Key rotation is complex           |
| Works for public APIs             | Larger key sizes (e.g., 2048-bit) |
| Secure even if private key leaks  | (ECDSA is faster and more compact) |

**When to use RSA/ECDSA?**
✅ Public APIs (e.g., payment processors)
✅ Long-term security requirements
✅ Client-side signing (e.g., mobile apps)
❌ Avoid for high-frequency internal calls

---

## **3. JWT Signing: The Good, Bad, and Ugly**

JWT (JSON Web Tokens) often uses **HMAC or RSA** for signing. It’s popular, but **misuse is rampant**.

### **Example: JWT with RSA in Node.js**
```javascript
const jwt = require('jsonwebtoken');

// Private key (keep this secure!)
const PRIVATE_KEY = '-----BEGIN RSA PRIVATE KEY-----\n...[your private key]...\n-----END RSA PRIVATE KEY-----';

// Sign a token
const payload = { sub: "user123", role: "admin" };
const token = jwt.sign(payload, PRIVATE_KEY, { algorithm: 'RS256' });
console.log("Token:", token);

// Verify a token
try {
  const decoded = jwt.verify(token, PUBLIC_KEY, { algorithms: ['RS256'] });
  console.log("Decoded:", decoded);
} catch (err) {
  console.error("Invalid token:", err.message);
}
```

### **Common JWT Pitfalls**
1. **Using weak algorithms** (`HS256` with predictable secrets).
2. **No expiration** (`exp` claim ignored).
3. **Storing private keys client-side** (e.g., in React/JS).
4. **Assuming HTTPS is enough** (tokens can be leaked).

**Fixes:**
- Always use **RSA/ECDSA** (`RS256`, `ES256`).
- Set `exp` to enforce token lifetime.
- Keep private keys **server-side only**.
- Use **short-lived tokens** (e.g., 15-30 min).

---

## **Implementation Guide: Choosing the Right Approach**

| **Use Case**               | **Recommended Approach** | **Key Considerations**                          |
|----------------------------|--------------------------|------------------------------------------------|
| Internal microservices     | HMAC                     | Shared secret via secure config (e.g., Vault). |
| Public APIs (e.g., payments)| RSA/ECDSA                 | Use **short-lived keys**, rotate often.          |
| Mobile/Web clients         | RSA/ECDSA                 | Never expose private keys to clients.          |
| High-throughput services   | HMAC + async verification| Tradeoff: Speed vs. security.                  |
| Long-term security         | ECDSA (e.g., P-256)       | Smaller keys = faster, but still secure.       |

### **Step-by-Step: Secure JWT with RSA (Python)**
1. **Generate keys** (do this once):
   ```bash
   openssl genpkey -algorithm RSA -out private.pem -pkeyopt rsa_keygen_bits:2048
   openssl rsa -pubout -in private.pem -out public.pem
   ```
2. **Sign tokens** (server-side):
   ```python
   from cryptography.hazmat.primitives import serialization
   from cryptography.hazmat.primitives.asymmetric import padding
   from cryptography.hazmat.primitives import hashes

   with open("private.pem", "rb") as key:
       private_key = serialization.load_pem_private_key(
           key.read(),
           password=None,
           backend=default_backend()
       )

   # Sign as shown in previous example
   ```
3. **Verify tokens**:
   ```python
   with open("public.pem", "rb") as key:
       public_key = serialization.load_pem_public_key(
           key.read(),
           backend=default_backend()
       )

   # Verify as shown in previous example
   ```

---

## **Common Mistakes to Avoid**

1. **Hardcoding secrets in code**
   ❌ `const SECRET = "password123";`
   ✅ Use **environment variables** (`os.getenv("API_SECRET")`).

2. **Ignoring key rotation**
   - If a key is compromised, **all past signatures are invalid**.
   - Rotate keys **quarterly** at minimum.

3. **Not verifying signatures on every request**
   - Always validate signatures **before processing**.
   - Tools like **JWT.io** can help debug, but **never trust them for production**.

4. **Using `HS256` (HMAC) for public APIs**
   - If the secret leaks, the entire system is compromised.

5. **Assuming HTTPS is enough**
   - **Signing + HTTPS** is critical, but HTTPS alone doesn’t prevent replay attacks.

6. **Overloading signatures**
   - Signing **all** requests can slow down APIs. Optimize:
     - Sign only **critical** operations (e.g., `transfer`, `delete`).
     - Use **short-lived tokens** for read-only actions.

---

## **Key Takeaways**

- **HMAC is fast but risky** – Only use for **internal, trusted services**.
- **RSA/ECDSA is safer** – Best for **public APIs and client-side signing**.
- **JWT is not magic** – Misconfigured JWTs are a top attack vector.
- **Key management is critical** – Rotate keys, never hardcode secrets.
- **Tradeoffs exist** –
  - Speed (HMAC) vs. security (RSA).
  - Key size (ECDSA is better than RSA for performance).
- **Always verify signatures** – Never skip validation.

---

## **Conclusion: Signing Is Non-Negotiable**

API security starts with signing. Whether you’re **transferring money**, **authenticating users**, or **syncing devices**, proper signing prevents breaches before they happen.

**TL;DR:**
- **Internal APIs?** → HMAC (if keys are secure).
- **Public APIs?** → RSA/ECDSA (always).
- **JWT?** → Use RSA, set `exp`, and rotate keys.
- **Never skip verification** – Even if the app "works."

Now go implement this **right**. Your future self (and your users) will thank you.

---
### **Further Reading**
- [OWASP JWT Security Best Practices](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)
- [Cryptography Best Practices (NIST)](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-131A.pdf)
- [Go Cryptography Guide](https://golang.org/pkg/crypto/)
```