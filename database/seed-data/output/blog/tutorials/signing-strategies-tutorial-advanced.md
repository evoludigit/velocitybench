```markdown
---
title: "Signing Strategies Pattern: Secure Your APIs Like a Pro"
date: 2023-11-15
author: "Alexandra 'Lex' Carter"
description: "A practical guide to implementing signing strategies for API security, covering JWT, HMAC, RSA, and hybrid approaches with real-world code examples."
tags: ["API Design", "Security", "Backend Patterns", "Authentication", "JWT", "HMAC", "RSA", "Authentication Tokens"]
---

# Signing Strategies Pattern: Secure Your APIs Like a Pro

Security is a moving target, but one constant in modern API design is the need for robust signing strategies. Whether you're validating JSON Web Tokens (JWT) from mobile clients, signing API responses for downstream services, or protecting against tampering, **signing strategies** directly impact trust, compliance, and system integrity.

In this post, we’ll dive deep into signing strategies—not as a standalone pattern, but as a critical layer of authentication and authorization in backend systems. We’ll compare HMAC, RSA, and JWT signing approaches, explore hybrid strategies, and share practical code examples in Go and Python. By the end, you’ll understand how to choose the right strategy for your use case and implement it correctly.

---

## **The Problem: Why Signing Matters**

APIs are a prime target for attacks. Without proper signing, adversaries can:
- **Tamper with payloads** (e.g., modifying a JWT `exp` claim to extend its validity).
- **Replay requests** (e.g., malicious clients resubmitting old requests with identical signatures).
- **Impersonate services** (e.g., faking an API response to a downstream system by crafting a valid signature).

Even if you encrypt data (e.g., with AES), signing ensures the integrity of *metadata* (e.g., token claims, request IDs). Here’s a concrete example of a vulnerable scenario:

```go
// Hypothetical insecure API handler (Node.js)
app.post('/payments', (req, res) => {
  if (req.body.amount > 10000) { // No signature validation!
    throw new Error("Fraud detected!");
  }
  // Process payment...
});
```
An attacker could modify `req.body.amount` to `100000` and claim it was never changed by appending a valid HMAC signature. Without verification, the server would blindly honor the request.

---

## **The Solution: Signing Strategies**

Signing strategies ensure:
1. **Authenticity** – Confirm the request originated from a trusted source.
2. **Integrity** – Guarantee the request wasn’t altered in transit.
3. **Non-repudiation** – Prevent clients from later denying they sent a request.

The key components of a signing strategy include:
- A **cryptographic key** (shared or asymmetric).
- A **signature algorithm** (e.g., HMAC-SHA256, RSASSA-PKCS1-v1_5).
- A **claims structure** (e.g., JWT fields or custom headers).
- A **validation mechanism** (e.g., middleware, libraries).

Let’s break down the most common strategies:

### **1. Shared-Secret Signing (HMAC)**
**Use Case**: Internal services, microservices, or when both parties can securely share a key (e.g., via secrets manager).

**Pros**:
- Lightweight and fast (symmetric crypto).
- Suitable for high-throughput systems (e.g., internal APIs).

**Cons**:
- **Key rotation is painful** (must update all clients).
- **Less scalable** for distributed systems (e.g., public APIs).

**Example (Python)**:
```python
import hmac
import hashlib
import json

# Shared secret (stored securely in env vars)
SECRET = b'my-ultra-secret-key-123'

def sign_payload(payload: str, secret: bytes) -> str:
    """Sign a JSON payload using HMAC-SHA256."""
    return hmac.new(secret, payload.encode('utf-8'), hashlib.sha256).hexdigest()

def verify_signature(payload: str, signature: str, secret: bytes) -> bool:
    """Verify HMAC signature."""
    return hmac.compare_digest(
        hmac.new(secret, payload.encode('utf-8'), hashlib.sha256).hexdigest(),
        signature
    )

# Example usage
data = {"user_id": 42, "action": "transfer"}
payload = json.dumps(data, sort_keys=True)  # Sort to avoid timing attacks
signature = sign_payload(payload, SECRET)
print(f"Signature: {signature}")  # Output: "3a1b2c..."
```

**Go Equivalent**:
```go
package main

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/json"
	"fmt"
)

func signHMAC(payload string, secret []byte) string {
	mac := hmac.New(sha256.New, secret)
	mac.Write([]byte(payload))
	return fmt.Sprintf("%x", mac.Sum(nil))
}

func verifyHMAC(payload, signature string, secret []byte) bool {
	mac := hmac.New(sha256.New, secret)
	mac.Write([]byte(payload))
	expected := fmt.Sprintf("%x", mac.Sum(nil))
	return hmac.Equal([]byte(signature), []byte(expected))
}

// Usage
type Payload struct {
	UserID string `json:"user_id"`
	Action string `json:"action"`
}

data := Payload{UserID: "42", Action: "transfer"}
payload, _ := json.Marshal(data)
signature := signHMAC(string(payload), []byte("my-secret"))
fmt.Println("Signature:", signature)
```

---

### **2. Public-Key Signing (RSA)**
**Use Case**: Public APIs, external services, or when you need to verify signatures *without* sharing secrets (e.g., JWTs).

**Pros**:
- **Key rotation is easier** (public keys can be long-lived; private keys are revoked).
- **Suitable for distributed systems** (e.g., mobile apps, third-party services).

**Cons**:
- **Slower than HMAC** (asymmetric crypto overhead).
- **Key management complexity** (private keys must be securely stored).

**Example (JWT with RSA in Go)**:
```go
package main

import (
	"github.com/golang-jwt/jwt/v5"
	"time"
)

var (
	rsaPrivateKey = []byte(`-----BEGIN PRIVATE KEY-----
	MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQ...
	-----END PRIVATE KEY-----`)

	rsaPublicKey = []byte(`-----BEGIN PUBLIC KEY-----
	MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...
	-----END PUBLIC KEY-----`)
)

func generateJWT(userID string) (string, error) {
	token := jwt.NewWithClaims(
		jwt.SigningMethodRS256,
		jwt.MapClaims{
			"user_id": userID,
			"exp":     time.Now().Add(time.Hour * 24).Unix(),
		},
	)

	return token.SignedString(rsaPrivateKey)
}

func validateJWT(tokenString string) (*jwt.Token, error) {
	return jwt.Parse(
		tokenString,
		func(token *jwt.Token) (interface{}, error) {
			// Verify the signing method
			if _, ok := token.Method.(*jwt.SigningMethodRSA); !ok {
				return nil, fmt.Errorf("unexpected signing method")
			}
			return jwt.ParseRSAPublicKeyFromPEM(rsaPublicKey)
		},
	)
}

// Usage
token, _ := generateJWT("123")
fmt.Println("JWT:", token)
```

---

### **3. Hybrid Strategies**
**Use Case**: Combine the strengths of HMAC + RSA (e.g., sign tokens with RSA, then use HMAC for request integrity).

**Example**: Sign a JWT with RSA, then HMAC-sign the entire request payload (headers + body) for downstream services.

```python
# Pseudocode for hybrid signing
def hybrid_sign(token: str, payload: dict, secret: bytes) -> dict:
    # 1. Sign JWT with RSA
    jwt_token = signJWT(payload, privateKey)

    # 2. Sign the full request (headers + body) with HMAC
    combined_payload = f"{token}{json.dumps(payload)}"
    request_signature = signHMAC(combined_payload, secret)

    return {
        "token": jwt_token,
        "signature": request_signature,
        "payload": payload
    }

def verify_hybrid(token: str, signature: str, payload: dict, secret: bytes) -> bool:
    # 1. Verify JWT with public key
    if not verifyJWT(token, publicKey):
        return False

    # 2. Verify HMAC
    combined_payload = f"{token}{json.dumps(payload)}"
    return verifyHMAC(combined_payload, signature, secret)
```

---

## **Implementation Guide**

### **Step 1: Choose Your Strategy**
| Strategy       | Best For                          | Tradeoffs                          |
|----------------|-----------------------------------|------------------------------------|
| **HMAC**       | Internal services, high throughput | Key rotation pain                  |
| **RSA**        | Public APIs, external clients     | Slower, harder key management     |
| **Hybrid**     | Combined security (e.g., JWT + HMAC) | Complexity increases with layers  |

### **Step 2: Implement Key Management**
- **For HMAC**: Store secrets in a secrets manager (e.g., AWS Secrets Manager, HashiCorp Vault).
- **For RSA**: Use a HSM (Hardware Security Module) for private keys or rotate keys annually.

**Example (Vault Integration)**:
```go
// Pseudocode for fetching HMAC secret from Vault
secret, err := vaultKVRead("api-secrets/hmac-key")
if err != nil {
    log.Fatal(err)
}
```

### **Step 3: Validate Signatures in Middleware**
**Go (Gin Example)**:
```go
func signingMiddleware() gin.HandlerFunc {
    return func(c *gin.Context) {
        // 1. Extract signature from headers
        sig := c.GetHeader("X-Signature")
        payload := c.Request.URL.RawQuery // or c.Request.Body

        // 2. Verify HMAC
        if !verifyHMAC(payload, sig, []byte(os.Getenv("SECRET"))) {
            c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "invalid signature"})
            return
        }
        c.Next()
    }
}
```

**Python (FastAPI Example)**:
```python
from fastapi import Request, Depends, HTTPException
import hmac

async def verify_signature(
    request: Request,
    secret: str = Depends(get_secret)
) -> None:
    sig = request.headers.get("X-Signature")
    payload = await request.body()
    if not hmac.compare_digest(
        hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest(),
        sig
    ):
        raise HTTPException(status_code=401, detail="Invalid signature")
```

### **Step 4: Handle Key Rotation**
- **HMAC**: Shutdown services, deploy new keys, and update clients.
- **RSA**: Issue new JWTs with the updated public key (e.g., via short-lived tokens).

**Example (JWT Key Rotation)**:
```go
// Invalidate old keys and require new ones
func shouldValidateOldKey(token *jwt.Token) bool {
    // Logic to check expiration of old keys
    return false // New tokens must use the latest public key
}
```

---

## **Common Mistakes to Avoid**

1. **Hardcoding Secrets**
   ❌ Bad:
   ```python
   SECRET = "hardcoded-secret"  # Never do this!
   ```
   ✅ Good:
   Use environment variables or secrets managers.

2. **Not Sorting Payloads**
   Attackers can exploit timing attacks by reordering JSON keys:
   ```json
   { "a": 1, "b": 2 } != { "b": 2, "a": 1 }
   ```
   ✅ Fix: Sort keys before signing.

3. **Ignoring Signature Size Limits**
   Long signatures increase latency. Limit payload size (e.g., `< 1KB`).

4. **Mixing HMAC and RSA**
   Avoid signing the *same* data with both HMAC and RSA unless necessary.

5. **No Error Handling for Signature Validation**
   Always log failed validations (but never leak which strategy failed).

---

## **Key Takeaways**
- **HMAC is fast but inflexible** for large-scale systems.
- **RSA is secure but slower**—ideal for public APIs or critical data.
- **Hybrid strategies** (JWT + HMAC) offer layered security.
- **Always rotate keys** and use secrets managers.
- **Validate signatures in middleware** early to fail fast.
- **Sort payloads** before signing to prevent timing attacks.

---

## **Conclusion**

Signing strategies are the unsung heroes of API security. Whether you’re protecting a microservice or a public API, choosing the right approach—and implementing it correctly—directly impacts your system’s trustworthiness.

**Key actions to take now:**
1. Audit your current signing strategy (if any).
2. Benchmark HMAC vs. RSA for your workload.
3. Implement middleware for signature validation.
4. Set up key rotation policies.

Start small—add signing to one high-risk endpoint first—and iterate. Security is a journey, not a destination.

---
### **Further Reading**
- [JWT Best Practices (OWASP)](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)
- [HMAC Security Considerations](https://tools.ietf.org/html/rfc2104)
- [RFC 7518 (JWA)](https://tools.ietf.org/html/rfc7518) (for signing methods)

---
*What’s your go-to signing strategy? Share your use cases in the comments!*
```