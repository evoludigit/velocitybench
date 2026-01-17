```markdown
# **Signing Guidelines: A Practical Guide to Secure API Requests**

## **Introduction**

In today’s web and API-driven world, security is non-negotiable. When building APIs—whether for internal services or public-facing applications—you need a way to **authenticate requests** and **ensure data integrity**. While OAuth 2.0, JWT (JSON Web Tokens), and API keys are common authentication mechanisms, they don’t always cover **data verification**—the need to confirm that a request hasn’t been tampered with in transit.

This is where **signing guidelines** come in. By signing API requests with a shared secret, you can prevent malicious payload manipulation, replay attacks, and unauthorized data modification. Unlike encryption (which secures privacy), signing (using **HMAC, SHA, or similar algorithms**) proves the **authenticity and integrity** of a request.

In this guide, we’ll explore:
- Why signing is crucial when authentication alone isn’t enough
- How to implement signing in real-world scenarios
- Best practices and common pitfalls

Let’s dive in.

---

## **The Problem: When Authentication Isn’t Enough**

Authentication (e.g., API keys, JWTs) tells you *who* made the request—but it doesn’t guarantee that the request *wasn’t changed* in transit. Attackers can:

1. **Tamper with request payloads** (e.g., modifying POST data to change prices in an e-commerce API).
2. **Replay old requests** (e.g., sending a stale payment confirmation to process another charge).
3. **Manipulate headers** (e.g., spoofing a `Content-Length` field to bypass size limits).

### **Example: An Unsigned API Vending Machine**
Imagine a simple API for a vending machine that accepts coins and dispenses snacks. Without signing:

```http
POST /dispense?snack=chocolate-bar&coin=50¢
```
An attacker could modify the request to:
```http
POST /dispense?snack=gold-bars&coin=50¢
```
The API would happily dispense **far more valuable** items without noticing.

### **Why Signing Helps**
A signed request includes a **cryptographic hash** of the payload, signed with a shared secret. If the payload changes, the hash won’t match—alerting your server.

---

## **The Solution: Signing Requests with HMAC**

### **Key Components**
1. **Shared Secret** – A long, random key known only to the client and server.
2. **Signature Algorithm** – Typically **HMAC-SHA256** (or SHA-512 for extra security).
3. **Base64 Encoding** – Signatures are binary; encoding them makes them safe for URLs/JSON.
4. **Request Structure** – The signature is appended to the request (e.g., as a header or query param).

### **How It Works**
1. The client computes a hash of the request (with a secret) and appends it.
2. The server verifies the hash on receipt.

---

## **Implementation Guide**

### **Step 1: Choose a Signing Algorithm**
For most cases, **HMAC-SHA256** is a good balance of security and performance. Use **HMAC-SHA512** if your data is highly sensitive.

### **Step 2: Define Your Request Structure**
We’ll sign the **HTTP method, path, query parameters (sorted), and request body** (if present). Here’s an example request:

```http
POST /api/transactions HTTP/1.1
Host: api.example.com
Authorization: Bearer abc123
X-Signature: <HMAC-SHA256-signature>
X-Signature-Timestamp: 1625097600
Content-Type: application/json

{
  "amount": 100,
  "currency": "USD"
}
```

### **Step 3: Client-Side Signing (JavaScript Example)**
The client generates the signature before sending the request.

```javascript
const crypto = require('crypto');
const apiKey = 'your_shared_secret';
const requestData = {
  method: 'POST',
  path: '/api/transactions',
  params: new URLSearchParams({ currency: 'USD' }).toString(),
  body: JSON.stringify({ amount: 100 }),
  timestamp: Date.now()
};

function generateSignature() {
  const dataToSign = [
    requestData.method,
    requestData.path,
    requestData.params,
    requestData.body,
    requestData.timestamp
  ].join('&');

  const hmac = crypto.createHmac('sha256', apiKey);
  hmac.update(dataToSign);
  return hmac.digest('base64');
}

const signature = generateSignature();
const timestamp = Math.floor(Date.now() / 1000); // Unix timestamp

fetch('https://api.example.com/api/transactions', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer abc123',
    'X-Signature': signature,
    'X-Signature-Timestamp': timestamp,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ amount: 100, currency: 'USD' })
});
```

### **Step 4: Server-Side Verification (Node.js Example)**
The server checks the signature upon receiving the request.

```javascript
const crypto = require('crypto');
const express = require('express');
const app = express();

app.use(express.json());

app.post('/api/transactions', (req, res) => {
  const sharedSecret = 'your_shared_secret';
  const receivedSignature = req.headers['x-signature'];
  const receivedTimestamp = req.headers['x-signature-timestamp'];

  if (!receivedSignature || !receivedTimestamp) {
    return res.status(403).send('Missing signature or timestamp');
  }

  // Verify timestamp (e.g., within 5 minutes)
  const currentTimestamp = Math.floor(Date.now() / 1000);
  if (Math.abs(currentTimestamp - receivedTimestamp) > 300) {
    return res.status(403).send('Request too old');
  }

  const dataToVerify = [
    req.method,
    req.path,
    req.query ? Object.entries(req.query)
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map(([k, v]) => `${k}=${v}`)
      .join('&') : '',
    req.body ? JSON.stringify(req.body) : '',
    receivedTimestamp
  ].join('&');

  const hmac = crypto.createHmac('sha256', sharedSecret);
  hmac.update(dataToVerify);
  const computedSignature = hmac.digest('base64');

  if (computedSignature !== receivedSignature) {
    return res.status(403).send('Invalid signature');
  }

  // Proceed with the request
  res.send('Transaction processed successfully');
});

app.listen(3000, () => console.log('Server running on port 3000'));
```

---

## **Common Mistakes to Avoid**

### **1. Not Sorting Query Parameters**
If you don’t sort query parameters, the same request could produce different hashes:
```http
GET /user?id=1&name=Alice  // Different from
GET /user?name=Alice&id=1
```

**Fix:** Always sort parameters before hashing.

### **2. Using Weak Secrets**
If your `api_key` is predictable (e.g., `app123`), an attacker could brute-force it.
**Fix:** Use a **cryptographically secure random key** (e.g., 32+ chars).

### **3. Not Validating the Timestamp**
Without a timestamp check, an attacker could replay old requests.
**Fix:** Add a `X-Signature-Timestamp` and reject requests outside a **5-minute window**.

### **4. Signing Only the Body (Not Headers or Paths)**
An attacker could modify the request method or path without altering the body.
**Fix:** Always include the **full request context** in the signature.

### **5. Ignoring Content-Length**
A malicious request could spoof `Content-Length`, causing the server to read extra data.
**Fix:** Include `Content-Length` in the signature or validate it separately.

---

## **Key Takeaways**

✅ **Signing ≠ Encryption** – It proves authenticity but doesn’t hide data.
✅ **Always sign the full request context** (method, path, params, body, timestamp).
✅ **Use HMAC-SHA256/SHA512** for security; avoid MD5.
✅ **Sort query parameters** to prevent hash collisions.
✅ **Add timestamp checks** to prevent replay attacks.
✅ **Keep secrets secure** – Never log or expose them.
✅ **Test with real attack scenarios** (e.g., modified payloads).

---

## **Conclusion**

Signing your API requests is a **simple yet powerful** way to add an extra layer of security beyond authentication. While it won’t replace encryption for sensitive data, it effectively prevents tampering and replay attacks—keeping your APIs safe from common exploits.

### **When to Use Signing**
- When you need **data integrity** (e.g., financial APIs, payment systems).
- When authentication (e.g., API keys) isn’t enough.
- When you can’t rely on TLS alone (some internal services may not use HTTPS).

### **When to Avoid Signing**
- If you’re only handling **read-only** data (use HTTPS instead).
- If your payload is **too large** (signing big blobs is inefficient).
- In **high-latency** systems where timestamps are unreliable.

For most real-world applications, **combining signing with HTTPS and proper authentication** gives you a robust security model.

Now go implement it—in production, signing is the difference between a secure API and an open invitation for abuse.

---
**Further Reading:**
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [HMAC-SHA256 RFC](https://datatracker.ietf.org/doc/html/rfc2104)
```

This blog post is **practical, code-heavy, and honest** about tradeoffs—perfect for beginner backend engineers.