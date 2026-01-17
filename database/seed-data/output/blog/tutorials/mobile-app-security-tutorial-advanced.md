```markdown
# **App Security Patterns: A Practical Guide for Backend Engineers**

*How to build secure APIs and applications with battle-tested patterns—without sacrificing performance or developer experience.*

---

## **Introduction**

Security isn’t an afterthought—it’s the foundation of any production-grade application. Yet, many developers treat it as a checkbox: *"We’ve got HTTPS, so we’re good."* But real-world threats—OAuth misconfigurations, SQL injection, JWT forgery, and API abuse—demonstrate that security is a *systemic* concern, not a single layer.

In this guide, we’ll explore **app security patterns**—proven tactics to secure APIs, databases, and infrastructure while maintaining scalability. We’ll cover **authentication, authorization, input validation, rate limiting, and secure coding practices**, using real-world examples in Go, Python, and JavaScript.

By the end, you’ll have a toolkit to defend against common vulnerabilities *without* over-engineering or sacrificing usability.

---

## **The Problem: Where Security Breaks Down**

Security patterns fail in three key areas:

1. **Over-Privileged Identities**
   - Services and users often run with excessive permissions (e.g., DB admin roles for micro-services). This turns a breach into a disaster.
   - *Example:* A 2021 attack on **Kaseya VSA** exploited a single over-privileged VPN account to cripple 1,500 businesses.

2. **Lack of Least Privilege Enforcement**
   - APIs return overly broad access tokens (e.g., `admin` claims in JWTs) or ignore role-based constraints.
   - *Example:* A leaked Discord API token (with `admin` scope) granted attackers access to user data.

3. **Defensive Coding Gaps**
   - Input validation is weak ("*trust the client*" fallacy), leading to injection attacks.
   - *Example:* The **Equifax breach** (2017) stemmed from unpatched Apache Struts, which allowed malicious payloads through unvalidated parameters.

4. **Visibility Blind Spots**
   - Logs, audits, and monitoring are inconsistent, hiding attacks until they’re too late.
   - *Example:* **SolarWinds** attackers spent months undetected due to weak SIEM rules.

---

## **The Solution: Security Patterns That Work**

Security patterns are **reusable, testable approaches** to mitigate risks. They fall into four categories:

1. **Authentication & Identity**
   - Secure user and service login with multi-factor authentication (MFA) and short-lived tokens.
2. **Authorization & Access Control**
   - Enforce "least privilege" with role-based access control (RBAC) and attribute-based policies.
3. **Input & Output Validation**
   - Sanitize inputs and control outputs to prevent injection and XSS.
4. **Defensive Infrastructure**
   - Harden APIs, databases, and logs to detect and block attacks.

---

## **1. Authentication Patterns: Secure Logins**

### **Problem**
- Weak passwords + no MFA = easy accounts to compromise.
- Long-lived JWTs can be leaked and reused.

### **Solution: Time-Bound Tokens + MFA**
Use **OAuth 2.0 with PKCE** (Proof Key for Code Exchange) for web/mobile apps, and **short-lived JWTs** with refresh tokens.

#### **Example: Go (Gin + OAuth2)**
```go
package main

import (
	"github.com/golang-jwt/jwt/v5"
	"github.com/labstack/echo/v4"
	"github.com/labstack/echo-contrib/jwt"
)

const (
	secretKey = "your-256bit-secret"
	expHours  = 15 // Short-lived access tokens
)

func main() {
	e := echo.New()

	// JWT middleware with 15-minute expiry
	jwtMiddleware := jwt.WithConfig(jwt.Config{
		SigningKey: []byte(secretKey),
		SigningMethod: jwt.SigningMethodHS256,
		Expiration: jwt.Expiration{Time: time.Duration(expHours*60)*time.Minute},
	})

	e.POST("/login", loginHandler)
	e.GET("/protected", jwtMiddleware, protectedHandler)

	e.Logger.Fatal(e.Start(":8080"))
}

func loginHandler(c echo.Context) error {
	user := getUserFromDB(c) // Assume valid user
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
		"sub": user.ID,
		"role": user.Role,
		"exp": time.Now().Add(time.Duration(expHours*60)*time.Minute).Unix(),
	})
	return c.JSON(200, map[string]string{"token": token.SignedString([]byte(secretKey))})
}
```

#### **Key Tradeoffs**
- ✅ **Pro:** Harder for attackers to abuse leaked tokens.
- ❌ **Con:** Requires backend logic to refresh tokens (avoid client-side refresh).

---

## **2. Authorization Patterns: Least Privilege**

### **Problem**
- APIs return `admin` roles even when users have limited access.
- No runtime checks prevent unauthorized actions.

### **Solution: Runtime Role Enforcement**
Use **attribute-based access control (ABAC)** with JWT scopes.

#### **Example: Python (FastAPI)**
```python
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/user/{user_id}/delete")
async def delete_user(
    token: str = Depends(verify_token),
    user_id: str,
    current_user_id: str = Depends(lambda: jwt.get("sub", token))
):
    if not token.get("role") == "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Cannot delete others")
    # Delete logic...
```

#### **Key Tradeoffs**
- ✅ **Pro:** Flexible policies (e.g., `can_delete: true/false`).
- ❌ **Con:** JWT size grows with claims; use **sparse scopes** (avoid `{"admin": true}`).

---

## **3. Input Validation Patterns: Defend Against Injection**

### **Problem**
- SQL injection, NoSQL injection, XSS, and command injection are still common.
- Regex or type-checking is insufficient.

### **Solution: Use Framework-Safe Methods**
- **SQL:** Parameterized queries (never `query = "SELECT * FROM users WHERE id = " + userId`).
- **NoSQL:** Store data in BSON/JSON without eval().
- **HTTP:** Use structured parsers (e.g., `json.loads()` instead of `eval()`).

#### **Example: SQL Injection Prevention (PostgreSQL + Python)**
```python
import psycopg2
from psycopg2 import sql

def get_user_by_id(user_id: str):
    conn = psycopg2.connect("dbname=users")
    query = sql.SQL("SELECT * FROM users WHERE id = {}").format(sql.Literal(user_id))
    cursor = conn.cursor()
    cursor.execute(query)
    return cursor.fetchone()  # Safe: No user input in SQL structure
```

#### **Anti-Pattern: Bad (SQL Injection Risk)**
```python
# ❌ UNSAFE: String interpolation
user_id = request.args.get("id")
query = f"SELECT * FROM users WHERE id = {user_id}"
cursor.execute(query)
```

#### **Key Tradeoffs**
- ✅ **Pro:** Zero runtime risk if queries are parameterized.
- ❌ **Con:** Debugging can be harder (e.g., logging raw queries).

---

## **4. Rate Limiting & Abuse Prevention**

### **Problem**
- Brute-force attacks (e.g., password guessing).
- DDoS via excessive API calls.

### **Solution: Token Bucket + Fail2Ban**
- **Token Bucket:** Limit requests per user/IP.
- **Fail2Ban:** Automatically block IPs after X failed attempts.

#### **Example: Token Bucket (Redis + Node.js)**
```javascript
const redis = require("redis");
const client = redis.createClient();

const rateLimit = (req, res, next) => {
  const ip = req.ip;
  const maxRequests = 100;
  const windowMs = 60 * 1000; // 1 minute

  client.incr(`rate:${ip}`, (err, count) => {
    if (err) return next(err);
    if (count > maxRequests) {
      return res.status(429).json({ error: "Too many requests" });
    }
    client.expire(`rate:${ip}`, windowMs / 1000);
    next();
  });
};

app.use(rateLimit);
```

#### **Key Tradeoffs**
- ✅ **Pro:** Simple to implement; works for most abuse cases.
- ❌ **Con:** False positives possible (e.g., shared VPNs).

---

## **Implementation Guide: Secure Your API**

1. **Layer 1: Authentication**
   - Use **OAuth2 + PKCE** for web/mobile.
   - Short-lived JWTs (≤15 mins) + refresh tokens.

2. **Layer 2: Authorization**
   - Enforce scopes at runtime (e.g., `user.can:delete`).
   - Audit access denied events.

3. **Layer 3: Input Sanitization**
   - **SQL:** Always use parameterized queries.
   - **NoSQL:** Never use `eval()` on user input.
   - **HTTP:** Validate JSON schemas.

4. **Layer 4: Protection**
   - Rate limit all endpoints.
   - Log and monitor suspicious activity.

---

## **Common Mistakes to Avoid**

| **Mistake**               | **Why It’s Bad**                          | **Fix**                                  |
|---------------------------|-------------------------------------------|------------------------------------------|
| Hardcoding secrets        | Keys leaked in Git                             | Use secrets managers (AWS SSM, HashiCorp) |
| Ignoring CORS              | XSS via misconfigured headers             | Strict `Origin` checks                     |
| No logging for failures   | Hard to debug attacks                      | Log 4xx/5xx with user context             |
| Global admin role         | Single point of breach                     | Fine-grained RBAC                         |
| Client-side JWT validation | Tokens can be forged                       | Always validate on server                  |

---

## **Key Takeaways**

✅ **Authenticate securely** → Use OAuth2 + PKCE, short-lived tokens.
✅ **Enforce least privilege** → Scope JWTs, audit access.
✅ **Validate inputs rigorously** → Parameterized queries, JSON schemas.
✅ **Protect your APIs** → Rate limiting, fail2ban.
✅ **Monitor everything** → Log failures, alert on anomalies.

---

## **Conclusion**

Security isn’t about perfect systems—it’s about **defenses in depth**. By applying these patterns, you’ll reduce attack surfaces while keeping your code maintainable.

- **Start small:** Add rate limiting and JWT validation first.
- **Test often:** Use tools like [OWASP ZAP](https://www.zaproxy.org/) to scan for vulnerabilities.
- **Iterate:** Update dependencies (e.g., fix SQLi via library updates).

Security is a marathon, not a sprint. But with these patterns, you’ll be running the right race.

**Further Reading:**
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- ["Security Patterns" by Venkat Subramaniam](https://www.amazon.com/Security-Patterns-Effective-Reusable-Software-Design/dp/0321883365)

---
**Comments?** Share your secure API tips below!
```