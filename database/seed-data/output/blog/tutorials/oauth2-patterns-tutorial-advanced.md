```markdown
---
title: "Delegated Authorization: 10+ OAuth 2.0 Implementation Patterns for Secure APIs"
date: 2023-11-15
tags: ["authentication", "authorization", "oauth2", "backend", "api-design"]
description: "Master OAuth 2.0 patterns with 10+ actionable patterns for secure API authentication and delegation. Real-world examples, tradeoffs, and anti-patterns."
---

# Delegated Authorization: 10+ OAuth 2.0 Implementation Patterns for Secure APIs

![OAuth 2.0 Flow Diagram](https://miro.medium.com/max/1400/1*Gv9KK_Ij4pe7V7FLjPE8Lg.png)
*Visualizing OAuth 2.0's delegation flow*

---

## Introduction

OAuth 2.0 isn’t just a protocol—it’s a **design pattern** for secure delegation. In an era where APIs power everything from mobile apps to embedded systems, OAuth 2.0 provides a granular way to let users grant access to their data *without sharing credentials*. Yet, misimplementation abounds: poorly scoped tokens, insecure redirection URIs, and unintended token leakage are common pitfalls.

For backend engineers, this means choosing between **10+ concrete OAuth 2.0 patterns**—each with tradeoffs about security, usability, and complexity. This guide dives into the most battle-tested patterns, illustrated with code and real-world examples. We’ll cover:
- When to use **public vs. confidential clients**
- How **PKCE** (Proof Key for Code Exchange) prevents code interception
- When **refresh tokens** are a crutch (and what to use instead)
- The **token revocation** patterns that actually work
- And much more.

---

## The Problem: Why OAuth 2.0 Without Patterns Becomes a Security Minefield

OAuth 2.0’s flexibility is also its Achilles’ heel. Without explicit patterns, implementations suffer from:

1. **Overly Permissive Scopes**
   ```http
   /auth/authorize?response_type=code&client_id=...&scope=all:read:write
   ```
   *What does `all:read:write` even mean?*
   Most libraries default to broad scopes. Applications accidentally grant excessive access.

2. **No Expiry or Short-Lived Tokens**
   A token fetched in 2020 might still work in 2023, even after the user’s password was reset.

3. **PKCE Ignored**
   Mobile apps often follow the insecure flow:
   ```python
   # ❌ Vulnerable code exchange without PKCE
   request.post("/oauth/token", data={"code": code, "client_id": "app1"})
   ```

4. **Token Rotation Without Safeguards**
   Storing long-lived refresh tokens on the client bypasses security best practices.

5. **Revocable Tokens Are Non-Revocable**
   Many implementations claim revocation but lack a viable way to invalidate tokens.

6. **Lack of Monitoring for Token Abuse**
   No alerts when a token is used from unexpected locations.

---

## The Solution: OAuth 2.0 Patterns That Scale

The real power of OAuth 2.0 comes from **patterns**, not just API usage. Here are 10+ battle-tested patterns to implement securely.

---

### **1. Public vs. Confidential Clients: When to Use Each**
**Pattern:** Always classify your client as either `public` or `confidential` and enforce stricter requirements for confidential clients.

#### **What’s the Difference?**
- **Public clients** (e.g., SPAs, mobile apps) cannot securely store secrets. They rely on **PKCE** and short-lived tokens.
- **Confidential clients** (e.g., backend services, servers) can securely store secrets (PKCE not required).

#### **Anti-Pattern:**
```python
# ❌ Misclassifying a mobile app as confidential
auth_client.register_client(
    client_name="My Mobile App",
    client_type="confidential",  # WRONG: Can't store secrets
)
```

#### **Pattern:**
```python
# ✅ Correctly classifying a mobile app as public
auth_client.register_client(
    client_name="My Mobile App",
    client_type="public",  # Enforces PKCE
    redirect_uris=["https://myapp.com/callback"],
    grant_types=["authorization_code", "refresh_token"],
)
```

---

### **2. PKCE: Stopping Intermediary Attacks**
**Pattern:** Use **PKCE (Proof Key for Code Exchange)** for all authorization code flows with public clients.

#### **Why It Matters:**
PKCE prevents attackers from swapping authorization codes for tokens after intercepting them.

#### **Anti-Pattern:**
```http
# ❌ Vulnerable OAuth flow (no PKCE)
GET /oauth/authorize?client_id=app1&response_type=code&redirect_uri=https://myapp.com/callback
```
Attacker intercepts `code` and exchanges it for a token:
```http
POST /oauth/token
  Body: grant_type=authorization_code&code=intercepted_code&client_id=app1&redirect_uri=https://myapp.com/callback
```

#### **Pattern: PKCE in Action**
```http
# ✅ PKCE flow: Step 1 (auth request)
GET /oauth/authorize?response_type=code&client_id=app1&redirect_uri=https://myapp.com/callback&code_challenge=SOMETHING_HASHED
```
```http
# ✅ Step 2 (token exchange includes challenge)
POST /oauth/token
  Body: grant_type=authorization_code&code=intercepted_code&client_id=app1&redirect_uri=https://myapp.com/callback&code_verifier=HASHED_SECRET
```
*[PKCE ensures `intercepted_code` cannot be used without knowing `code_verifier`.]*

#### **Code Example (Go):**
```go
import (
	"crypto/sha256"
	"encoding/base64"
)

// Generate PKCE code_challenge and code_verifier
func generatePKCE() (string, string) {
	// Step 1: Create random verifier
	verifier := randBytes(64)
	// Step 2: Hash for code_challenge
	hashed := sha256.Sum256(verifier)
	base64URLEncoded := base64.URLEncoding.EncodeToString(hashed[:])
	// Step 3: Encode as URL-safe string
	return base64URLEncoded, string(verifier)
}
```

---

### **3. Short-Lived Access Tokens + Refresh Tokens (With Limits)**
**Pattern:** Use short-lived access tokens (e.g., 1 hour) and refresh tokens only when necessary.

#### **Anti-Pattern: Long-Lived Refresh Tokens**
```python
# ❌ Storing refresh tokens indefinitely
def save_refresh_token(user_id, refresh_token):
    db.execute("INSERT INTO tokens (user_id, token) VALUES (?, ?)", user_id, refresh_token)
```
*Problem:* If a refresh token is leaked, the attacker can get new access tokens forever.

#### **Pattern: Short-Lived Tokens + Rotation**
```python
# ✅ Generate short-lived access tokens
access_token = jwt.encode(
    {"sub": user_id, "exp": datetime.utcnow() + timedelta(hours=1)},
    SECRET_KEY,
    algorithm="HS256"
)

# ✅ Issue refresh tokens with limited scope and expiry
refresh_token = jwt.encode(
    {"sub": user_id, "exp": datetime.utcnow() + timedelta(days=7)},
    REVOCATION_SECRET_KEY,
    algorithm="HS256"
)
```
**Key Rules:**
- Access tokens: Max 1 hour (or shorter).
- Refresh tokens: Max 7 days (not months/years).
- Always rotate tokens on refresh.

#### **Revocable Refresh Tokens (Postgres Example):**
```sql
CREATE TABLE refresh_tokens (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    token_hash TEXT NOT NULL,  -- Store hashed tokens only
    revoked_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Store hash, not raw token
INSERT INTO refresh_tokens (user_id, token_hash)
VALUES ('user-123', '5f4dcc3b5aa765d61d8327deb882cf99');
```

---

### **4. Scope Granularity: Avoid `*` and `all`**
**Pattern:** Use **one-word, descriptive scopes** and avoid wildcards.

#### **Anti-Pattern:**
```http
# ❌ Vague scopes
GET /auth/authorize?scope=all:read:write
```
*Problem:* What does `all:read:write` really mean? Is it a single permission or multiple?

#### **Pattern: Atomic Scope Design**
```http
# ✅ Granular scopes
GET /auth/authorize?scope=profile.read+calendar.read+contacts.write
```
*Rule:* Each scope should match a single resource/permission (e.g., `votes.create`).

#### **Backend Validation (Python):**
```python
ALLOWED_SCOPES = {
    "profile.read",
    "calendar.read",
    "contacts.write",
}

def validate_scopes(scopes):
    for scope in scopes:
        if scope not in ALLOWED_SCOPES:
            raise PermissionError(f"Invalid scope: {scope}")
```

---

### **5. Token Expiry: Beyond "Just Set an Expire Time"**
**Pattern:** Use **short TTLs + MAC refresh** to prevent token misuse.

#### **Anti-Pattern: No Expiry or Long Expiry**
```python
# ❌ No expiry or 30-day expiry
access_token = jwt.encode(
    {"sub": user_id},
    KEY,
    algorithm="HS256",
    expires=30 * 24 * 60 * 60  # 30 days
)
```
*Problem:* Tokens linger for months, increasing risk of leaks.

#### **Pattern: Short TTL + MAC (Mutual Authentication + Refresh)**
1. Issue short-lived access tokens (e.g., 1 hour).
2. Require **MAC (e.g., HMAC) for refreshes** to prevent replay attacks.

```python
# ✅ Short TTL + MAC refresh
def generate_access_token(user_id):
    return jwt.encode(
        {"sub": user_id},
        KEY,
        algorithm="HS256",
        expires=3600  # 1 hour
    )

def generate_refresh_token(user_id, refresh_count):
    # Include usage count to track abuse
    return jwt.encode(
        {
            "sub": user_id,
            "refresh_count": refresh_count,
            "exp": datetime.utcnow() + timedelta(days=7)
        },
        REFRESH_KEY,
        algorithm="HS256"
    )
```

---

### **6. Token Revocation: Blacklisting vs. "Forgotten" Tokens**
**Pattern:** Use **blacklisting** for critical tokens and **short-lived tokens** for others.

#### **Anti-Pattern: "Forgotten Tokens"**
```python
# ❌ Not revoking tokens (just ignoring them)
if token_not_revoked(user_id):
    return access_token
```
*Problem:* Tokens stay valid even after user security changes.

#### **Pattern: Token Revocation with Blacklist**
```python
# ✅ Revoke tokens when user changes password
def on_password_change(user_id):
    db.execute("UPDATE refresh_tokens SET revoked_at=NOW() WHERE user_id=?", user_id)

# ✅ Check during token validation
def is_token_revoked(token):
    token_hash = hash_token(token)
    return db.execute("SELECT 1 FROM revoked_tokens WHERE token_hash=?", token_hash)
```

#### **Alternative: Short-Lived Tokens + MAC**
Instead of revoking, use **short-lived tokens** and **MAC refreshes** to prevent misuse.

---

### **7. PKCE + Refresh Tokens: The "Just-In-Time" Flow**
**Pattern:** Combine PKCE with refresh tokens for mobile apps (when needed).

#### **Use Case:**
- Mobile apps need **short-lived tokens** but also **refresh capability**.
- Avoid storing refresh tokens on the device.

#### **Flow:**
1. User authenticates via PKCE.
2. Server issues **short-lived access token + refresh token**.
3. Client stores refresh token **securely** (e.g., OS keychain).
4. When access token expires, client refreshes using the refresh token.

#### **Code Example (Python):**
```python
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2AuthorizationCodeBearer

app = FastAPI()
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="https://auth.example.com/auth",
    tokenUrl="https://auth.example.com/token",
    scopes={"profile": "Access user profile"}
)

@app.get("/protected")
async def protected_route(token: str = Depends(oauth2_scheme)):
    # Verify PKCE challenge was sent
    if not verify_pkce_challenge(token):
        raise HTTPException(status_code=403, detail="Invalid token")
    return {"message": "Access granted"}
```

---

### **8. Delegated Authorization: API-to-API Flow**
**Pattern:** Use **client credentials grant** for API-to-API communication.

#### **Use Case:**
- Service A needs to access Service B’s data.
- No user involved (machine-to-machine).

#### **Flow:**
1. Service A requests a **short-lived token** via client credentials.
2. Service B validates the token and grants access.

#### **Example (Postman Collection):**
```http
POST https://auth.example.com/token
  Headers:
    Authorization: Basic BASE64(client_id:client_secret)
  Body:
    grant_type=client_credentials
    scope=api:read
```
**Response:**
```json
{
  "access_token": "abc123...",
  "expires_in": 3600,
  "token_type": "Bearer"
}
```

---

### **9. Token Leakage Detection: Monitor & Alert**
**Pattern:** Track token usage and alert on suspicious activity.

#### **Example: Log Token Usage (Postgres)**
```sql
CREATE TABLE token_usage (
    id SERIAL PRIMARY KEY,
    token_hash TEXT NOT NULL,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Log every access
INSERT INTO token_usage (token_hash, ip_address, user_agent)
VALUES ('abc123...', inet '192.168.1.1', ' curl/7.81.0 ')
```

#### **Alert on Anomalies (Python):**
```python
def check_for_leaks(token_hash):
    usage = db.execute("""
        SELECT ip_address, COUNT(*) as count
        FROM token_usage
        WHERE token_hash = ? AND timestamp > NOW() - INTERVAL '1 hour'
        GROUP BY ip_address
    """, token_hash)

    if any(count > 1 for _, count in usage):
        alert("Potential token leak for hash: %s", token_hash)
```

---

### **10. Token Rotation: Automate & Notify Users**
**Pattern:** Rotate tokens periodically and notify users.

#### **Example: Token Rotation (Python)**
```python
def rotate_tokens(user_id):
    # Revoke old refresh tokens
    db.execute("UPDATE refresh_tokens SET revoked_at=NOW() WHERE user_id=?", user_id)

    # Generate new tokens
    new_access_token = generate_access_token(user_id)
    new_refresh_token = generate_refresh_token(user_id, 0)

    # Notify user (e.g., via email)
    send_rotation_notification(user_id)

    return new_access_token, new_refresh_token
```

---

## Implementation Guide: OAuth 2.0 Patterns in Practice

### **Step 1: Choose Your Client Type**
- **Mobile/Web Apps?** → Use `public` client + PKCE.
- **Backend Service?** → Use `confidential` client (no PKCE needed).

### **Step 2: Enforce Short-Lived Tokens**
- Access tokens: **1 hour max**.
- Refresh tokens: **7 days max** (not longer).

### **Step 3: Use PKCE for Authorization Code Flows**
- Always include `code_challenge` and `code_verifier` for public clients.

### **Step 4: Granular Scopes**
- Avoid `*` or `all`.
- Use atomic scopes (e.g., `profile.read`, `messages.send`).

### **Step 5: Implement Token Revocation**
- Store hashed tokens + revocation timestamp.
- Rotate tokens periodically.

### **Step 6: Monitor Token Usage**
- Log IP, user agent, and timestamp for every token use.
- Alert on anomalies (e.g., same token used from multiple IPs).

### **Step 7: Automate Token Rotation**
- Rotate refresh tokens every 5-7 days.
- Notify users via email/SMS.

---

## Common Mistakes to Avoid

| **Mistake**                          | **Why It’s Bad**                          | **Fix**                          |
|--------------------------------------|-------------------------------------------|----------------------------------|
| Ignoring PKCE                        | Vulnerable to code interception          | Always use PKCE for public clients |
| Long-lived refresh tokens            | Leaks enable long-term access            | Max 7-day expiry                  |
| No token expiry                      | Tokens linger after credential changes   | Set short TTLs (1 hour)           |
| Vague scopes (`*`, `all`)           | Unclear permissions                      | Use atomic scopes                |
| No revocation mechanism              | Tokens can’t be invalidated              | Blacklist or rotate tokens       |
| Storing plaintext refresh tokens     | Easily stolen                             | Hash tokens + revocation          |
| No monitoring for token misuse       | Hard to detect leaks early               | Log and alert on anomalies       |
| Using JWT for refresh tokens         | JWTs are stateless; need revocation      | Use short-lived JWTs + rotation  |

---

## Key Takeaways
✅ **Public clients = PKCE mandatory** (no exceptions).
✅ **Short-lived access tokens** (1 hour) + **limited refresh tokens** (7 days).
✅ **Avoid `*` scopes**—use atomic permissions.
✅ **Rotate tokens** periodically and notify users.
✅ **Monitor token usage** and alert on abuse.
✅ **Revoke tokens** when credentials change.
✅ **Use client credentials** for API-to-API flows.
✅ **Never trust the client**—always validate on the server.

---

## Conclusion: OAuth 2.0 Patterns = Secure Delegation by Design