# **[Pattern] JWT Security Best Practices – Reference Guide**

---

## **Overview**
JWT (JSON Web Token) is a widely adopted standard for stateless authentication and authorization, enabling secure communication between clients and servers. While JWT provides flexibility and scalability, improper implementation can lead to vulnerabilities such as token theft, replay attacks, or unauthorized access. This reference outlines **key security best practices**, implementation guidelines, and threat mitigations to ensure robust JWT-based authentication systems.

This guide covers:
✔ Token generation and signing (algoritms, keys, signing methods)
✔ Secure storage and transmission (HTTPS, HttpOnly cookies, CORS)
✔ Token validation and claims validation (audience, issuer, expiration)
✔ Threat prevention (reflective attacks, token leakage, replay attacks)
✔ Monitoring and logging (token usage, anomalies)

---

## **Schema Reference**

### **JWT Structure**
| Field          | Description                                                                 | Security Considerations                                                                 |
|----------------|-----------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| **Header**     | Contains token type (`typ: "JWT"`) and algorithm (`alg`).                     | Always use `HS256`, `RS256`, or `ES256`. Avoid weak algorithms like `HS256` without proper key rotation. |
| **Payload**    | Contains claims (standard, registered, or custom).                          | Use minimal required claims to reduce attack surface.                                   |
| **Signature**  | HMAC-SHA256, RSA, or ECDSA hash of header + payload + secret/key.           | Prefer asymmetric encryption (`RS256`, `ES256`) for higher security.                     |

### **Standard Claims**
| Claim          | Description                                                                 | Security Best Practice                                                                 |
|----------------|-----------------------------------------------------------------------------|----------------------------------------------------------------------------------------|
| `iss` (Issuer) | Identifies the token issuer (e.g., domain or service name).                | Validate against known issuers to prevent forgery.                                     |
| `sub` (Subject) | Represents the user/principal identity.                                     | Use unique identifiers (e.g., UUID) instead of email/username for sensitive data.     |
| `aud` (Audience)| Specifies the intended recipient(s).                                        | Validate against expected audiences to prevent token misuse.                            |
| `exp` (Expiry)  | Token expiration time (Unix timestamp in seconds).                           | Set short expiry times (e.g., 15-30 minutes) and refresh tokens for longer sessions.   |
| `nbf` (Not Before) | Token validity start time.                                                   | Prevent replay attacks by ensuring tokens are not used before issuance.                  |
| `iat` (Issued At)| Token issuance time.                                                         | Log and monitor for anomalies (e.g., future-dated tokens).                              |

### **Sensitive Claims (Avoid or Protect)**
| Claim          | Risk                                                                       | Mitigation                                                                              |
|----------------|-----------------------------------------------------------------------------|----------------------------------------------------------------------------------------|
| User Roles      | Over-privileged access if modified.                                         | Scope tokens to least privilege; use hierarchical permissions.                        |
| Refresh Tokens  | Persistent access if leaked.                                               | Store refresh tokens securely (HttpOnly cookies, encrypted storage).                     |
| Custom Metadata | Potential exposure of sensitive data.                                       | Avoid storing PII (personally identifiable info) in JWT payload; use external DB.      |

---

## **Implementation Best Practices**

### **1. Token Signing & Algorithms**
| Algorithm      | Security Level | Recommendation                                                                 |
|----------------|----------------|---------------------------------------------------------------------------------|
| **HS256**      | Moderate       | Avoid for sensitive use cases; use only with short-lived tokens and rotated keys. |
| **RS256**      | High           | Prefer for production; use asymmetric keys (public/private pairs).               |
| **ES256**      | High           | Alternative to RSA for modern systems (ECDSA with Curve P-256).                  |
| **HS384/HS512**| High           | Use for increased security (longer key size).                                   |
| **Avoid**      | Weak           | `(none)`, `HMAC-SHA1`, `SHA1`, `SHA256` without asymmetric signing.                |

**Key Management:**
- Use **HSMs (Hardware Security Modules)** or **cloud KMS (Key Management Service)** for private keys.
- **Rotate keys periodically** (e.g., quarterly) and revoke expired tokens.
- **Never hardcode secrets**; retrieve keys from secure vaults (e.g., AWS Secrets Manager, HashiCorp Vault).

### **2. Token Storage & Transmission**
| Scenario               | Secure Method                          | Insecure Method (Avoid)                     |
|-------------------------|----------------------------------------|---------------------------------------------|
| **Browser Storage**     | `HttpOnly`, `Secure` cookies           | `localStorage`, `sessionStorage`            |
| **Mobile Apps**         | Encrypted storage (Keychain/Keystore)  | Plaintext or insecure shared preferences.     |
| **API Requests**        | `Authorization: Bearer <token>` (HTTPS)| Plaintext tokens in URLs or headers (unless HTTPS). |
| **Refresh Tokens**      | Server-side storage (DB) + HttpOnly    | Client-side storage (risk of XSS).           |

### **3. Token Validation**
**Mandatory Checks:**
1. **Signature Verification**: Ensure the token hasn’t been tampered with.
2. **Expiration (`exp`)**: Reject tokens past their expiry time.
3. **Issuer (`iss`)**: Validate against allowed issuers.
4. **Audience (`aud`)**: Ensure token is for the correct service/application.
5. **Not Before (`nbf`)**: Reject tokens issued before current time (mitigates replay attacks).

**Optional but Recommended:**
- **Custom Claims**: Validate presence/format of required claims (e.g., `roles`, `scopes`).
- **Token Usage Limits**: Track and block tokens with excessive requests (rate-limiting).
- **Revocation List**: Maintain a blacklist of compromised/invalidated tokens (e.g., after logout).

### **4. Threat Mitigations**
| Threat                | Cause                          | Mitigation                                                                       |
|-----------------------|--------------------------------|----------------------------------------------------------------------------------|
| **Replay Attacks**    | Stolen tokens reused.           | Short expiry times + `nbf` validation.                                           |
| **Token Leakage**     | Logs, browser history, XSS.     | Use `HttpOnly`, `Secure` cookies; avoid logging full tokens.                     |
| **Brute Force**       | Weak algorithms/keys.          | Use asymmetric encryption (`RS256`, `ES256`); enforce key rotation.              |
| **IDOR (Insecure Direct Object Reference)** | Missing `aud` validation. | Validate `aud` claim against expected API endpoints.                              |
| **Token Forgery**     | Weak signing algorithms.        | Prefer `RS256`/`ES256`; validate `iss` claim.                                     |

### **5. Refresh Tokens**
- **Scope**: Use refresh tokens **only** for obtaining new access tokens.
- **Storage**: Server-side (database) + client-side in `HttpOnly` cookies.
- **Rotation**: Issue a new refresh token upon successful login/token refresh.
- **Revocation**: Invalidate refresh tokens on logout or suspicious activity.

**Example Flow:**
```
1. User logs in → Server issues access token (short-lived) + refresh token.
2. Client stores refresh token securely (HttpOnly cookie).
3. Access token expires → Client sends refresh token to `/refresh` endpoint.
4. Server validates refresh token, issues new access token, rotates refresh token.
5. Client updates stored tokens.
```

---

## **Query Examples**
### **1. Validating a JWT (Node.js with `jsonwebtoken`)**
```javascript
const jwt = require('jsonwebtoken');

function verifyToken(token) {
  try {
    const decoded = jwt.verify(token, 'your-private-key-or-public-key', {
      algorithms: ['RS256'], // Enforce algorithm
      issuer: 'your-issuer',
      audience: 'your-audience',
    });
    return decoded;
  } catch (err) {
    throw new Error('Token validation failed');
  }
}
```

### **2. Generating a JWT (Python with `PyJWT`)**
```python
import jwt
from datetime import datetime, timedelta

def generate_token(payload, secret_key):
    token = jwt.encode(
        payload={
            'sub': 'user123',
            'name': 'John Doe',
            'roles': ['admin'],
            'exp': datetime.utcnow() + timedelta(minutes=30),
            'iat': datetime.utcnow()
        },
        key=secret_key,
        algorithm='HS256'  # Use RS256 in production
    )
    return token
```

### **3. Securing API Endpoints (Express.js Middleware)**
```javascript
const jwtMiddleware = (req, res, next) => {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) return res.status(401).send('Unauthorized');

  jwt.verify(token, process.env.JWT_SECRET, { algorithms: ['HS256'] }, (err, decoded) => {
    if (err) return res.status(403).send('Forbidden');
    req.user = decoded;
    next();
  });
};

app.get('/protected', jwtMiddleware, (req, res) => {
  res.send(`Hello, ${req.user.name}!`);
});
```

---

## **Related Patterns**
1. **[Stateless Authentication]** – Principles of stateless auth (JWT, OAuth 2.0).
2. **[Secure API Design]** – Guidelines for protecting API endpoints (rate-limiting, CORS, input validation).
3. **[Key Management]** – Best practices for storing and rotating cryptographic keys.
4. **[Session Management]** – Alternatives to JWT (e.g., server-side sessions, cookies).
5. **[OAuth 2.0/OpenID Connect]** – Extensions for JWT-based authorization flows (e.g., `id_token`).
6. **[Token Revocation]** – Implementing token blacklists or short-lived tokens.
7. **[Logging & Monitoring]** – Tracking token usage for anomalies (e.g., brute-force attempts).

---
**References**
- [RFC 7519 (JWT Specification)](https://tools.ietf.org/html/rfc7519)
- [OWASP JWT Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_cheatsheet.html)
- [NIST Special Publication 800-63B](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-63B.pdf)