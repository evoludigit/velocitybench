```markdown
# **Security Patterns: Building Defensible Backend Systems**

*How to design APIs and databases that resist attacks—without sacrificing usability*

---

## **Introduction: Why Security Isn’t an Afterthought**

Building secure systems isn’t just about locking doors after a break-in—it’s about embedding security into every layer of your architecture from day one. As backend engineers, we often focus on performance, scalability, or clean abstractions, but security patterns are just as critical. A single misconfigured endpoint, unvalidated input, or weak authentication can expose your system to credential leaks, data breaches, or even financial loss.

This guide covers **practical security patterns** for APIs and databases, grounded in real-world tradeoffs. You’ll learn how to:
- Protect against common threats like SQL injection and JWT tampering
- Implement defensive strategies without over-engineering
- Balance security with usability
- Avoid pitfalls that even experienced engineers fall into

We’ll start with the **problem space**, then dive into **proven patterns** with code examples, and finish with actionable advice. Let’s get started.

---

## **The Problem: Security Gaps in Unprotected Systems**

Security flaws often stem from:
1. **Over-reliance on high-level libraries** – Using ORMs or auth frameworks without understanding their limitations.
2. **Input validation as an afterthought** – Only sanitizing data when an OWASP alert fires.
3. **Assumptions about HTTPS** – Relying solely on TLS without considering other attack vectors.
4. **Exposed admin interfaces** – Publicly available endpoints for `POST /admin/reset-password`.
5. **Hardcoding secrets** – Embedding API keys in client-side code or version control.

### **Real-World Consequences**
- **SQL Injection**: Exposed databases via unparameterized queries (e.g., `UPDATE users SET password='admin' WHERE id=1;`).
- **JWT Tampering**: Missing signature checks in token payloads leads to unauthorized access.
- **CSRF Vulnerabilities**: Lack of CSRF tokens in state-changing API calls.

Let’s examine a **vulnerable example** to illustrate the risks.

### **Example: Insecure User Login Endpoint**
```javascript
// ❌ Vulnerable to SQL Injection
app.post('/api/login', (req, res) => {
  const { username, password } = req.body;
  const query = `SELECT * FROM users WHERE username='${username}' AND password='${password}'`;
  db.query(query, (err, results) => {
    if (err) throw err;
    if (results.length) res.send("Logged in!");
    else res.status(403).send("Failed");
  });
});
```
If `username=admin'; DROP TABLE users;--`, this deletes your database.

---

## **The Solution: Security Patterns for APIs and Databases**

Security patterns are **repeatable, battle-tested strategies** to mitigate risks. We’ll categorize them into:

1. **Authentication & Authorization**
2. **Input Validation & Sanitization**
3. **Secure Data Storage**
4. **Defensive Programming**
5. **API-Specific Protections**

Each pattern addresses specific threats while maintaining usability.

---

## **Pattern 1: Use Prepared Statements (SQL Injection Prevention)**

**Problem**: Unparameterized queries allow injection attacks.
**Solution**: Use **prepared statements** (or ORM queries) to separate data from logic.

### **Code Example: Secure Login with Prepared Statements**
```javascript
// ✅ Protected against SQL Injection
const { username, password } = req.body;
db.query('SELECT * FROM users WHERE username=? AND password=?', [username, password], (err, results) => {
  if (err) throw err;
  // ...
});
```
**Tradeoffs**:
- Slightly more verbose (but worth it).
- ORMs like Sequelize/TypeORM abstract this away, but understand their underlying behavior.

---

## **Pattern 2: Implement JWT with Signatures (Token Tampering Prevention)**

**Problem**: Malicious users can modify JWT payloads if not validated.
**Solution**: Sign tokens with HMAC/SHA and verify signatures.

### **Example: Secure JWT Implementation**
```javascript
const jwt = require('jsonwebtoken');
const SECRET = process.env.JWT_SECRET;

app.post('/api/login', (req, res) => {
  const token = jwt.sign({ userId: 123 }, SECRET, { expiresIn: '1h' });
  res.json({ token });
});

// Middleware to verify tokens
function authMiddleware(req, res, next) {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) return res.status(401).send("Unauthorized");

  jwt.verify(token, SECRET, (err, user) => {
    if (err) return res.status(403).send("Invalid token");
    req.user = user;
    next();
  });
}
```
**Tradeoffs**:
- Secret management is critical (use env vars, not code).
- Short expiration times reduce risk but require refresh tokens.

---

## **Pattern 3: Rate Limiting (Abuse Prevention)**

**Problem**: Brute-force attacks or API key scraping.
**Solution**: Limit request rates per IP/key.

### **Example: Rate Limiting with Redis**
```javascript
const rateLimit = require('express-rate-limit');
const redisStore = require('rate-limit-redis');

app.use(
  rateLimit({
    store: new redisStore({
      sendCommand: (redis, command, args) => redis.command(command, args),
    }),
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 100, // Limit each IP to 100 requests
    message: "Too many requests, try again later",
  })
);
```
**Tradeoffs**:
- Adds latency (mitigate with caching).
- False positives may lock out legitimate users.

---

## **Pattern 4: Input Validation (Sanitization & Schema Enforcement)**

**Problem**: Invalid or malformed data breaks your app.
**Solution**: Validate inputs via schemas (e.g., Joi, Zod) or server-side checks.

### **Example: Validating a User Signup**
```javascript
const Joi = require('joi');

app.post('/api/signup', (req, res) => {
  const schema = Joi.object({
    email: Joi.string().email().required(),
    password: Joi.string().min(8).pattern(/^[a-zA-Z0-9]+$/),
  });

  const { error, value } = schema.validate(req.body);
  if (error) return res.status(400).json({ error: error.details[0].message });
  // Process valid data
});
```
**Tradeoffs**:
- Validation adds complexity but catches errors early.
- Client-side validation is **not enough** (always validate server-side).

---

## **Pattern 5: Secure Database Practices**

**Problem**: Direct user input in queries or weak hashing.
**Solution**:
- Use **prepared statements** (already covered).
- **Hash passwords** with bcrypt/argon2.
- **Encrypt sensitive fields** (e.g., PII) with AES.

### **Example: Secure Password Handling**
```javascript
const bcrypt = require('bcrypt');
const saltRounds = 12;

// When storing a password
const hashedPassword = await bcrypt.hash(password, saltRounds);

// When verifying
const match = await bcrypt.compare(inputPassword, storedHashedPassword);
```
**Tradeoffs**:
- Hashing adds CPU overhead (use async/await).
- Encryption requires key management (consider AWS KMS).

---

## **Pattern 6: CORS & CSRF Protections**

**Problem**: Unauthorized cross-origin requests or state mutations.
**Solution**:
- **CORS**: Restrict allowed origins.
- **CSRF**: Use tokens for state-changing actions.

### **Example: CSRF Protection for Forms**
```javascript
app.use((req, res, next) => {
  const csrfToken = req.session.csrfToken || (req.session.csrfToken = Math.random().toString(36).substring(2));
  res.locals.csrfToken = csrfToken;
});

app.post('/api/sensitive', (req, res) => {
  if (req.body._csrf !== req.session.csrfToken) return res.status(403).send("CSRF token invalid");
  // Process request
});
```
**Tradeoffs**:
- CSRF tokens add complexity but are essential for web apps.
- For APIs, use `Content-Type: application/json` (tokens are less relevant).

---

## **Implementation Guide: Adopting Security Patterns**

1. **Start with Authentication**
   - Use **OAuth 2.0/JWT** for APIs.
   - Implement **multi-factor auth** (MFA) for admin routes.

2. **Validate All Inputs**
   - Enforce schemas (Joi/Zod) for all endpoints.
   - Reject malformed data early.

3. **Secure Database Directly**
   - Replace unparameterized queries with ORMs or prepared statements.
   - Use **bcrypt/argon2** for passwords, **AES** for sensitive fields.

4. **Rate-Limit Critical Endpoints**
   - Protect `/login`, `/reset-password`, and admin routes.

5. **Monitor & Audit**
   - Log suspicious activity (e.g., repeated failures).
   - Use tools like **Sentry** or **Datadog** for anomaly detection.

---

## **Common Mistakes to Avoid**

1. **Assuming HTTPS Alone Is Enough**
   - HTTPS protects data in transit but does **not** prevent:
     - SQL injection
     - CSRF attacks
     - Poorly validated inputs.

2. **Over-Reliance on Libraries**
   - Example: Using a JWT library without understanding its token format.

3. **Hardcoding Secrets**
   - Never commit `SECRET_KEY` to GitHub. Use environment variables.

4. **Ignoring API Key Leaks**
   - If an API key is exposed, revoke it immediately.

5. **Skipping Input Validation**
   - "Trusting the client" is a common pitfall. Always validate on the server.

6. **Not Testing for Vulnerabilities**
   - Use **OWASP ZAP**, **Burp Suite**, or **sqlmap** to test your APIs.

---

## **Key Takeaways**

- **Security patterns are not optional**—they’re the foundation of a robust system.
- **Defense in depth**: Layer protections (e.g., input validation + rate limiting + JWT).
- **Tradeoffs exist**: Balance security with usability (e.g., stricter CORS vs. cross-origin needs).
- **Stay updated**: Follow OWASP Top 10 and CVE databases for emerging threats.
- **Test continuously**: Security is a moving target—automate scanning in CI/CD.

---

## **Conclusion: Build Secure by Default**

Security isn’t about locking down all possibilities—it’s about **making attacks harder than they’re worth**. By adopting these patterns, you’ll reduce the attack surface while keeping your systems flexible.

**Next Steps**:
1. Audit your APIs for these patterns (use [OWASP Cheat Sheets](https://cheatsheetseries.owasp.org/)).
2. Start small: Implement JWT validation or rate limiting in one endpoint.
3. Automate security checks in your CI pipeline (e.g., with `node-security` or `sonarqube`).

Security is an investment, not a cost. The best time to build resilient systems was yesterday—today is the second-best time.

---
**Further Reading**:
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [JWT Best Practices](https://auth0.com/blog/jwt-best-practices/)
- [SQL Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)

**Code examples available on GitHub**: [github.com/your-repo/security-patterns-examples](https://github.com/your-repo/security-patterns-examples)
```