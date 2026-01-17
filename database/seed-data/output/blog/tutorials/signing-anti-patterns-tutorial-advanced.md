```markdown
---
title: "Signing Anti-Patterns: How to Avoid Common Cryptographic Pitfalls in API Design"
date: 2024-03-20
author: "Eliot Burrows"
description: "Secure your APIs by understanding and avoiding common signing anti-patterns. Learn best practices with code examples and real-world tradeoffs."
featuredImage: "/images/api-security.jpg"
tags: ["api design", "security", "cryptography", "backend engineering", "authentication", "api signing"]
---

# **Signing Anti-Patterns: How to Avoid Common Cryptographic Pitfalls in API Design**

As backend engineers, we often take signing for granted—until we don’t. A properly signed API request or response can protect against tampering, authentication, and integrity checks. But cryptographic signing is deceptively complex. Missteps here aren’t just inefficient; they can lead to vulnerabilities, poor performance, or brittle systems that fail under real-world load.

In this post, we’ll dissect **signing anti-patterns**—common mistakes in API signing that engineers make when blindly applying cryptographic best practices. We’ll walk through:
- Why signing is harder than it looks
- Real-world consequences of common anti-patterns
- Practical solutions with code examples
- How to design robust signing systems

---

## **Why Signing Matters**
API signing is a critical pillar of security, but it’s often an afterthought. Developers may reach for cryptographic libraries without understanding the full lifecycle of signing—from key rotation to performance implications. A well-designed signing system ensures:

- **Integrity**: Requests/responses haven’t been altered.
- **Authentication**: The sender is who they claim to be.
- **Non-repudiation**: The sender can’t deny sending a request.

But poor signing design can lead to:
- **Attacks**: Fake signatures or replay attacks if keys aren’t managed properly.
- **High overhead**: Excessive signing/verification slowing down your API.
- ** fragility**: Systems breaking under load or during key rotation.

---

## **The Problem: Common Signing Anti-Patterns**

### **1. The "One-Size-Fits-All" Signing Approach**
Many systems blindly apply signing to every request or response, without considering the **actual risk level**. For example, signing every GET request to a public API is often unnecessary and adds latency.

#### **Example: Over-Signing a Public API**
```python
# ❌ Over-signing: Every request is signed (even public ones)
@app.route("/public-data/<id>")
def get_public_data(id):
    data = fetch_data(id)
    signature = sign(data, secret_key)  # Unnecessary for GET requests
    return {"data": data, "signature": signature}, 200
```

**Tradeoff**: While this adds security, it’s **overkill** for stateless, public data. The performance cost of signing every response can add milliseconds that compound under scale.

---

### **2. Hardcoding Secret Keys**
Storing secret keys in code or configuration files is a classic anti-pattern. Hardcoded secrets are exposed in:
- Git history
- Server logs
- Deployment artifacts

#### **Example: Hardcoded Key**
```python
# ❌ Hardcoded key (never do this!)
SECRET_KEY = "my-secret-key-123"  # Exposed in source control!
def sign(data):
    return hmac.sign(data, SECRET_KEY)
```

**Tradeoff**: Convenient for dev, but **catastrophic for production**. Use secrets management (e.g., HashiCorp Vault, AWS Secrets Manager).

---

### **3. Not Using Short-Lived Tokens**
Long-lived signing keys increase risk. If a key is leaked, attackers can impersonate requests for days or months.

#### **Example: Stale Key Usage**
```python
# ❌ Using keys longer than necessary
signing_key = Key.from_pem(open("long-live-key.pem").read())  # Risky!
def process_request():
    # ... (key never rotated)
```

**Tradeoff**: Simplicity vs. **extended exposure window**. Rotate keys frequently (e.g., weekly).

---

### **4. Ignoring Key Rotation**
When keys expire, most systems **fail silently** instead of gracefully degrading. This can lead to outages during deployments.

#### **Example: No Rotation Handling**
```python
# ❌ No handling for key rotation
def verify_signature(signature):
    if current_key != new_key:  # Should log and fall back!
        raise KeyError("Key mismatch!")
    return hmac.verify(signature, current_key)
```

**Tradeoff**: Key rotation is a **must** for security, but requires careful planning to avoid downtime.

---

### **5. Signing Without Context Awareness**
Signatures should **only cover critical fields**. For example, signing the entire request body is inefficient if only the payload matters.

#### **Example: Signing Unnecessary Fields**
```python
# ❌ Signing the whole request (including headers)
data = {
    "headers": {"user-agent": "curl/7.68"},
    "body": {"foo": "bar"}
}
signed_data = sign(json.dumps(data))  # Overkill!
```

**Tradeoff**: Smaller payloads = **faster signing** and **smaller attack surface**.

---

## **The Solution: Signing Anti-Patterns Fixed**

### **1. Selective Signing**
Sign **only what matters**. For APIs, this usually means:
- **Signed requests**: Cover the body and critical headers (e.g., `Authorization`).
- **Signed responses**: Only for sensitive data (e.g., PII).

#### **Example: Smart Signing**
```python
# ✅ Sign only the payload, not headers
from cryptography.hazmat.primitives import hmac

def sign_payload(payload, key):
    return hmac.HMAC(key, hasher=SHA256()).update(payload.encode()).finalize()

# Usage:
request_payload = {"user": "alice", "action": "deposit"}
signature = sign_payload(request_payload, SECRET_KEY)
```

---

### **2. Secure Key Management**
Use **environment variables, secrets managers, or hardware security modules (HSMs)**.

#### **Example: Using AWS Secrets Manager**
```python
# ✅ Secure key fetching (Python)
import boto3
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

def get_hsm_key():
    client = boto3.client("secretsmanager")
    secret = client.get_secret_value(SecretId="api-signing-key")
    return secret["SecretString"]

key = get_hsm_key()
```

---

### **3. Short-Lived Tokens and Key Rotation**
Implement **automatic key rotation** with a fallback mechanism.

#### **Example: Graceful Key Rotation**
```python
# ✅ Handling two keys during rotation
current_key = load_key("current-key.pem")
next_key = load_key("next-key.pem")  # Load next key in advance

def verify_signature(signature):
    try:
        return hmac.verify(signature, current_key)
    except:
        return hmac.verify(signature, next_key)  # Fallback
```

**Tradeoff**: Adds complexity but **reduces risk**.

---

### **4. Key-Based Signing Policies**
Use **short-lived tokens** for sensitive operations (e.g., financial transfers).

#### **Example: JWT for Request Signing**
```python
# ✅ Using JWT with short expiry (e.g., 5 minutes)
import jwt

payload = {"sub": "user123", "exp": datetime.utcnow() + timedelta(minutes=5)}
token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
```

---

## **Implementation Guide**

### **Step 1: Define What to Sign**
- **Sign requests**: Only if they modify state (POST/PUT).
- **Sign responses**: Only for sensitive data (e.g., user profiles).
- **Avoid signing headers**: They’re often redundant.

### **Step 2: Choose the Right Algorithm**
- **HMAC** (for legacy systems)
- **RSA/ECDSA** (for better security, slightly slower)
- **JWT** (for stateless auth, but has its own risks)

### **Step 3: Automate Key Rotation**
- Use **CI/CD pipelines** to rotate keys.
- Test rotation **before production**.
- Monitor key usage with **metrics**.

### **Step 4: Validate Signatures Efficiently**
- **Batch verification** (if possible).
- **Caching** (if keys don’t change often).

---

## **Common Mistakes to Avoid**

| **Anti-Pattern** | **Risk** | **Fix** |
|------------------|----------|---------|
| Hardcoding keys | Key leaks | Use secrets managers (Vault, AWS Secrets) |
| Signing everything | Performance overhead | Sign only critical data |
| No key rotation | Extended exposure | Rotate keys daily/weekly |
| No fallback during rotation | Downtime | Implement double-key verification |
| Weak algorithms (SHA-1) | Breachable signatures | Use SHA-256+ |

---

## **Key Takeaways**
- **Sign only what’s necessary** (payloads > headers).
- **Never hardcode keys**—use secure storage.
- **Rotate keys frequently** (automate this).
- **Test rotation** before deploying.
- **Monitor signing performance** (latency can impact user experience).

---

## **Conclusion**
Signing is an **essential security layer**, but it’s easy to misconfigure. The anti-patterns we covered—over-signing, hardcoded keys, and poor rotation practices—are common but avoidable. By applying selective signing, secure key management, and automated rotation, you can build APIs that are **both secure and performant**.

Start small: audit your current signing strategy. Identify where you’re over-signing or using long-lived keys, and refine. Security is a **continuous process**, not a one-time fix.

---
**Further Reading**
- [AWS KMS for Key Management](https://aws.amazon.com/kms/)
- [OAuth 2.1 Draft (Improving JWT Security)](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-v2-1-05)
- [Cryptography Best Practices (NIST)](https://csrc.nist.gov/projects/cryptographic-algorithm-validation-program)
```