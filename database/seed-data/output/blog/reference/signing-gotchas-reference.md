# **[Pattern] Signing Gotchas: Reference Guide**

---

## **Overview**
The **Signing Gotchas** pattern documents common pitfalls, edge cases, and anti-patterns when implementing cryptographic signing in authentication, authorization, and data integrity workflows. Signing is a critical security mechanism—if misapplied, it can lead to vulnerabilities like replay attacks, incorrect validation, or unauthorized access. This guide covers misconfigurations, protocol-specific issues, and best practices to mitigate risks.

---

## **1. Key Concepts & Implementation Gotchas**

### **1.1 Core Signing Principles**
| Concept               | Description                                                                 |
|-----------------------|-----------------------------------------------------------------------------|
| **Digital Signatures** | Proves message authenticity and integrity using a private key.              |
| **Asymmetric Signing** | Private key signs → public key verifies (e.g., RSA, ECDSA).                  |
| **Symmetric Signing**  | Shared secret (HMAC) signs/verifies data (less common for auth).             |
| **Token Signing**     | Used in JWTs, OAuth tokens, and API signatures (e.g., AWS Signature v4).    |
| **Timing Attacks**    | Adversaries exploit variable execution time in signature verification.      |
| **Replay Attacks**    | Attackers resubmit valid signed requests to exploit missing nonce checks. |

---

## **2. Common Signing Gotchas**

### **2.1 Configuration & Key Management**
| **Gotcha**                     | **Risk**                                                                   | **Mitigation**                                                                 |
|---------------------------------|-------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **Hardcoded Private Keys**      | Keys exposed in code, logs, or version control.                              | Use **environment variables** or **HSM/key vaults** (AWS KMS, HashiCorp Vault). |
| **Key Rotation Not Enforced**   | Long-lived keys risk compromise.                                             | Rotate keys periodically (e.g., AWS: 30–90 days).                             |
| **Insecure Key Strength**       | Weak (RSA-1024, SHA-1) keys are vulnerable to brute-force attacks.            | Use **RSA-2048+, ECDSA (P-256/P-384), or Ed25519**.                       |
| **Shared Private Keys**         | Multi-user private keys enable credential sharing (e.g., AWS root account). | **Avoid sharing private keys**; grant least privilege via IAM policies.       |

---

### **2.2 Protocol-Specific Issues**
#### **JWT (JSON Web Tokens)**
| **Gotcha**                     | **Risk**                                                                   | **Mitigation**                                                                 |
|---------------------------------|-------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **No `alg` Header Validation**  | Forces use of weak algorithms (e.g., `HS256` without key rotation).         | Enforce **strong algorithms** (`RS256`, `ES256`) and **HMAC key rotation**.  |
| **Missing `exp` Claim**         | Tokens never expire → extended exposure.                                      | **Add `exp` claim** with short TTL (e.g., 15–30 mins).                      |
| **No `nonce` or `jti`**        | Replay attacks possible.                                                    | Include **unique identifiers** (`jti`) or validate `nonce` for stateless auth.|
| **Overly Permissive Claims**    | `scope` or `roles` claims grant excessive access.                           | **Scopes should be granular** (e.g., `read:profile` vs. `*`).              |

#### **OAuth 2.0 / OpenID Connect**
| **Gotcha**                     | **Risk**                                                                   | **Mitigation**                                                                 |
|---------------------------------|-------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **PKCE Not Enforced**           | Authorization codes stolen via MITM.                                         | **Require PKCE** for public clients.                                          |
| **Unsigned `id_token`**        | Man-in-the-middle can forge tokens.                                          | **Always sign `id_token`** with `RS256` or `ES256`.                         |
| **No `state` Parameter**        | CSRF attacks via redirect holographing.                                       | **Use `state` parameter** and validate server-side.                           |
| **Long-Lived Access Tokens**    | Tokens leaked → prolonged breach window.                                      | **Short-lived tokens** + refresh tokens with 1-hour TTL.                     |

#### **AWS Signature v4**
| **Gotcha**                     | **Risk**                                                                   | **Mitigation**                                                                 |
|---------------------------------|-------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **Regional Endpoint Misconfiguration** | Signing fails if region in request header doesn’t match account region.   | **Match region in `X-Amz-Region`** to account region.                        |
| **Missing `X-Amz-Date` Header** | Signature calculation fails.                                                | **Include `X-Amz-Date`** with ISO 8601 timestamp.                           |
| **Canonical Request Errors**    | Whitespace, line breaks, or missing headers break signing.                   | **Strictly follow AWS canonicalization rules**.                               |
| **No Query Parameter Sorting**  | Parameters must be sorted alphabetically.                                   | **Sort query strings** before signing (e.g., `?A=1&B=2` → `A=1&B=2`).        |

---

### **2.3 Validation & Edge Cases**
| **Gotcha**                     | **Risk**                                                                   | **Mitigation**                                                                 |
|---------------------------------|-------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **Lazy Validation**             | Signatures verified only at end of pipeline (too late for error handling). | **Validate ASAP** (e.g., middleware in frameworks like Express.js).          |
| **No Signature Padding**        | ECDSA signatures may lack padding (e.g., secp256k1 in Bitcoin).              | **Use ASN.1/DER encoding** for consistency.                                   |
| **UTC vs. Local Time Mismatch** | Tokens expire due to timezone differences.                                   | **Use UTC timestamps** everywhere.                                            |
| **Malformed Input Data**        | Signing data with unexpected characters (e.g., null bytes).                 | **Base64url-encode data** before signing (RFC 7515).                         |
| **Sign-Then-Encrypt vs. Encrypt-Then-Sign** | Confuses integrity checks.                       | **Use `Encrypt-Then-Sign`** for JWTs/OAuth to ensure data isn’t tampered with before encryption. |

---

## **3. Schema Reference**
Below are key signing-related schemas (simplified for clarity).

### **JWT Claims (RFC 7519)**
| Field          | Type    | Description                                                                 | Example Value                     |
|----------------|---------|-----------------------------------------------------------------------------|-----------------------------------|
| `iss`          | String  | Issuer of the token.                                                       | `https://example.com`             |
| `sub`          | String  | Subject (user/tenant ID).                                                  | `user123`                         |
| `aud`          | String  | Audience (valid recipient).                                                 | `api.example.com`                 |
| `exp`          | Number  | Expiration time (Unix timestamp).                                           | `1712345678`                      |
| `nbf`          | Number  | Not Before (early rejection).                                               | `1712340000`                      |
| `iat`          | Number  | Issued At (timestamp).                                                      | `1712345600`                      |
| `jti`          | String  | JWT ID (anti-replay).                                                       | `a1b2c3d4-e567-8901-2345-6789abc` |
| `scope`        | String  | Space-separated permissions (e.g., `read write`).                          | `profile:read profile:write`      |

### **AWS Signature v4 Headers**
| Header                | Required | Description                                                                 |
|-----------------------|----------|-----------------------------------------------------------------------------|
| `Authorization`       | Yes      | Base64-encoded `AWS4-HMAC-SHA256` signature.                               |
| `X-Amz-Date`          | Yes      | ISO 8601 timestamp (e.g., `20230501T123456Z`).                             |
| `X-Amz-Security-Token`| No*      | Session token for temporary credentials.                                    |
| `X-Amz-Region`        | Yes      | AWS region (e.g., `us-west-2`).                                             |

*Note: Required for temporary credentials (STS).

---

## **4. Query Examples**
### **4.1 Validating a JWT (Python)**
```python
import jwt
from jwt.exceptions import InvalidTokenError

def validate_jwt(token, public_key):
    try:
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience="api.example.com"
        )
        return payload
    except InvalidTokenError as e:
        print(f"JWT Error: {e}")
        return None
```

### **4.2 AWS Signature v4 Request (cURL)**
```bash
curl -X GET "https://dynamodb.us-west-2.amazonaws.com/" \
  -H "Authorization: AWS4-HMAC-SHA256 Credential=AKIAIOSFODNN7EXAMPLE/20230501/us-west-2/dynamodb/aws4_request, SignedHeaders=host;x-amz-date, Signature=..." \
  -H "X-Amz-Date: 20230501T123456Z" \
  -H "X-Amz-Region: us-west-2"
```

### **4.3 Detecting Replay Attacks (Node.js)**
```javascript
const jwt = require('jsonwebtoken');
const { v4: uuidv4 } = require('uuid');

const validateToken = (token, req) => {
  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET, {
      algorithms: ["HS256"],
      issuer: req.query.issuer,
      jti: req.query.jti, // Unique per request
    });
    return decoded;
  } catch (err) {
    throw new Error("Invalid or replayed token");
  }
};
```

---

## **5. Best Practices**
1. **Enforce Strong Algorithms**
   - Prefer **RSA-2048**, **ECDSA (P-384)**, or **Ed25519** over legacy (RSA-1024, SHA-1).
   - Avoid `HS256` for JWTs unless keys are rotated frequently.

2. **Use Hardware Security Modules (HSM)**
   - Store private keys in **AWS CloudHSM**, **Azure Key Vault**, or **Thales HSM**.

3. **Token Lifecycle Management**
   - **Short TTLs** (15–30 mins) + **refresh tokens** for long-lived access.
   - **Rotate keys** every 30–90 days.

4. **Defend Against Timing Attacks**
   - Use **constant-time comparison** (e.g., `timingSafeEqual` in OpenSSL).
   - Avoid `strcmp` or `==` for signature validation.

5. **Audit Logging**
   - Log **failed signature validations** (e.g., expired tokens, wrong algorithm).
   - Example log fields:
     - `timestamp`, `client_ip`, `token_alg`, `result` (success/fail).

6. **Framework-Specific Gotchas**
   - **Express.js**: Use middleware like [`express-jwt`](https://github.com/auth0/express-jwt) with strict validation.
   - **FastAPI**: Validate JWTs with [`python-jose`](https://github.com/mpdavis/python-jose) and Pydantic.
   - **AWS Lambda**: Avoid hardcoding keys; pull from **AWS Secrets Manager**.

---

## **6. Related Patterns**
| Pattern                          | Description                                                                 | When to Use                                  |
|----------------------------------|-----------------------------------------------------------------------------|----------------------------------------------|
| **[Secure Token Generation]**    | Guidelines for creating cryptographically secure tokens.                   | When generating JWTs, OAuth tokens, or API keys. |
| **[Rate Limiting for Signatures]** | Prevent brute-force attacks on signature endpoints.                     | High-risk APIs (e.g., AWS API Gateway).     |
| **[Zero-Trust Authentication]**   | Multi-factor + ephemeral credentials.                                      | High-security environments (e.g., finance). |
| **[CSP: Content Security Policy]** | Mitigates XSS attacks that could steal signed cookies.                     | Web apps using JWTs in `HttpOnly` cookies.   |
| **[Key Rotation Strategies]**     | How to rotate keys without downtime.                                       | When managing long-lived signing keys.       |

---

## **7. Further Reading**
- [RFC 7515 (JWT)](https://datatracker.ietf.org/doc/html/rfc7515)
- [AWS Signature v4 Docs](https://docs.aws.amazon.com/general/latest/gr/sigv4-signing.html)
- [OWASP JWT Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)
- [Timing Attack Prevention](https://crypto.stanford.edu/~dabo/cgi-bin/overflow/xor.pdf)