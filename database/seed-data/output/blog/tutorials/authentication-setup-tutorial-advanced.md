```markdown
# **Authentication Setup: A Complete Guide for Modern Backend APIs**
*From JWT to OAuth, Building Secure Auth Systems That Scale*

---

## **Introduction**

Authentication is the backbone of any secure application. Without it, your users’ data, sensitive operations, and business logic are vulnerable to unauthorized access. Yet, despite its critical importance, many backend engineers treat authentication as an afterthought—bolting it on without proper planning, leading to bloated systems, security gaps, and scalability issues.

In this guide, we’ll break down **authentication setup** like a seasoned backend engineer would. We’ll explore modern patterns (JWT, OAuth 2.0, session-based), tradeoffs between them, and real-world code examples. By the end, you’ll know how to design a **scalable, secure, and maintainable** authentication system for your APIs.

---

## **The Problem: Why Authentication Gets It Wrong**

Authentication isn’t just about logging in. Poorly designed systems create:

1. **Security Vulnerabilities**
   - Storing passwords in plaintext (yes, this still happens).
   - Weak token handling (short-lived tokens, no refresh flows).
   - Insecure token storage in client apps (e.g., sending tokens in URLs).

2. **Poor User Experience**
   - Multi-step logins clog workflows.
   - Token expiration forcing users to re-authenticate unnecessarily.

3. **Scalability Nightmares**
   - Session-based auth requires database checks for every request—slowing down APIs under load.
   - Stateless auth (like JWT) can explode in size if not managed properly.

4. **Unmaintainable Code**
   - Mixing auth logic with business logic (e.g., `UserService.doSomething()` vs. `AuthService.validateToken()`).
   - Hardcoded secrets and configurations.

---

## **The Solution: Authentication Components & Tradeoffs**

No single auth system works for all use cases. Here’s a breakdown of common approaches and their tradeoffs:

| Component          | Approach          | Pros                          | Cons                          | Best For                     |
|--------------------|-------------------|-------------------------------|-------------------------------|------------------------------|
| **JWT (Stateless)** | Bearer tokens     | Scalable, stateless, no DB calls | Token size bloat, no revocation | APIs, microservices           |
| **OAuth 2.0**      | Delegated auth    | Strong security, social logins | Complex, multi-party flow     | Web/mobile apps, SaaS        |
| **Session-Based**  | Server-side cookies | Simple, revocable             | DB-dependent, single server   | Traditional monolithic apps  |
| **Passwordless**   | Magic links/OAuth  | No password storage           | Limits to email/phone         | Internal tools, quick logins |

**Key Idea:** Choose based on:
- **Scale needs** (stateless vs. dependent).
- **Security requirements** (revocation vs. stateless).
- **Ecosystem** (OAuth for third-party logins).

---

## **Implementation Guide: Step-by-Step**

Let’s build a **JWT-based auth system** (the most common for APIs) with practical examples in **Node.js (Express) + PostgreSQL**.

---

### **1. Core Components**
Our system will include:
- **User model** (store hashed passwords).
- **Token service** (generate/validate tokens).
- **Middleware** (validate tokens on every request).
- **Refresh tokens** (long-lived but revocable).

---

### **2. Setup Dependencies**
```bash
npm install express jsonwebtoken bcrypt postgres bcryptjs @types/bcrypt @types/jsonwebtoken
```

---

### **3. Database Schema (`users` table)**
```sql
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  last_login TIMESTAMP
);
```

---

### **4. User Model (Handles Password Hashing)**
```typescript
// src/models/User.ts
import bcrypt from 'bcrypt';

export class User {
  static async hashPassword(password: string): Promise<string> {
    const salt = await bcrypt.genSalt(10);
    return bcrypt.hash(password, salt);
  }

  static async comparePasswords(
    inputPassword: string,
    storedHash: string
  ): Promise<boolean> {
    return bcrypt.compare(inputPassword, storedHash);
  }
}
```

**Why?** Never store plaintext passwords—always hash with a salt.

---

### **5. JWT Token Service**
```typescript
// src/services/TokenService.ts
import jwt from 'jsonwebtoken';
import { config } from '../config';

const TOKEN_SECRET = config.jwtSecret;
const TOKEN_EXPIRY = '15m'; // 15 minutes
const REFRESH_EXPIRY = '7d'; // 7 days

export class TokenService {
  static generateTokens(userId: string): { accessToken: string; refreshToken: string } {
    const accessToken = jwt.sign(
      { userId },
      TOKEN_SECRET,
      { expiresIn: TOKEN_EXPIRY }
    );
    const refreshToken = jwt.sign(
      { userId },
      TOKEN_SECRET,
      { expiresIn: REFRESH_EXPIRY }
    );
    return { accessToken, refreshToken };
  }

  static verifyAccessToken(token: string): { userId: string } | null {
    try {
      return jwt.verify(token, TOKEN_SECRET) as { userId: string };
    } catch (err) {
      return null;
    }
  }
}
```

**Key Tradeoffs:**
- **Short-lived access tokens** → Secure but require refresh flows.
- **Long-lived refresh tokens** → Convenient but risky (revocation needed).

---

### **6. Auth Controller (Login & Registration)**
```typescript
// src/controllers/AuthController.ts
import express from 'express';
import { User } from '../models/User';
import { TokenService } from '../services/TokenService';

const router = express.Router();

router.post('/login', async (req, res) => {
  const { email, password } = req.body;
  const user = await User.findByEmail(email);

  if (!user || !(await User.comparePasswords(password, user.password_hash))) {
    return res.status(401).json({ error: 'Invalid credentials' });
  }

  const { accessToken, refreshToken } = TokenService.generateTokens(user.id);
  res.json({ accessToken, refreshToken });
});

router.post('/register', async (req, res) => {
  const { email, password } = req.body;
  const hashedPassword = await User.hashPassword(password);
  await User.create({ email, password_hash: hashedPassword });
  res.status(201).json({ message: 'User created' });
});

export default router;
```

**Security Note:** Always validate input (e.g., `email` must be a valid string).

---

### **7. Protected Routes (Middleware)**
```typescript
// src/middleware/auth.ts
import { TokenService } from '../services/TokenService';

export const protectRoute = async (req: express.Request, res: express.Response, next: express.NextFunction) => {
  const authHeader = req.headers.authorization;
  if (!authHeader?.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'No token provided' });
  }

  const token = authHeader.split(' ')[1];
  const user = TokenService.verifyAccessToken(token);

  if (!user) {
    return res.status(403).json({ error: 'Invalid token' });
  }

  req.userId = user.userId;
  next();
};
```

**Usage in a route:**
```typescript
import { protectRoute } from '../middleware/auth';

router.get('/protected', protectRoute, (req, res) => {
  res.json({ message: 'This is protected data', userId: req.userId });
});
```

---

### **8. Refresh Token Flow**
Users should refresh tokens without re-authenticating:
```typescript
// Add to AuthController
router.post('/refresh', async (req, res) => {
  const { refreshToken } = req.body;
  try {
    const { userId } = jwt.verify(refreshToken, TOKEN_SECRET) as { userId: string };

    const newAccessToken = TokenService.generateTokens(userId).accessToken;
    res.json({ accessToken: newAccessToken });
  } catch (err) {
    res.status(403).json({ error: 'Invalid refresh token' });
  }
});
```

**Why?** Avoids password re-entry while maintaining security.

---

### **9. Logging Out (Token Revocation)**
```typescript
// Add a 'blacklist' table for refresh tokens
CREATE TABLE refresh_tokens (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  token_hash TEXT NOT NULL,
  revoked_at TIMESTAMP
);

router.post('/logout', async (req, res) => {
  const { refreshToken } = req.body;
  const hashedToken = await User.hashPassword(refreshToken); // Overkill—use a dedicated hash.
  await RefreshTokenService.revoke(refreshToken);
  res.json({ message: 'Logged out' });
});
```

**Alternative:** Use a Redis cache for fast revocation (scalable).

---

## **Common Mistakes to Avoid**

1. **Hardcoding Secrets**
   - ❌ `const JWT_SECRET = 'mysecret';`
   - ✅ Use environment variables (`dotenv`).

2. **No Token Expiry**
   - JWTs should expire (even refresh tokens).

3. **Overusing Sessions**
   - Sessions work, but they scale poorly under load.

4. **Storing Tokens Client-Side Only**
   - Always use **HTTP-only cookies** for JWTs to prevent XSS attacks.

5. **Ignoring Rate Limiting**
   - Prevent brute-force attacks with `express-rate-limit`.

6. **Mixing Auth with Business Logic**
   - Keep auth separate (e.g., `AuthService`, `UserService`).

---

## **Key Takeaways**

✅ **Stateless auth (JWT) scales better** but requires refresh flows.
✅ **Always hash passwords** (BCrypt + salt).
✅ **Use middleware for auth validation** (clean separation).
✅ **Short-lived tokens + refresh tokens** balance security & UX.
✅ **Avoid sessions** unless you’re certain of low scale.
✅ **Never log tokens or passwords** (even for debugging).

---

## **Conclusion**

Authentication isn’t a one-size-fits-all problem. The right approach depends on your app’s scale, security needs, and user flow. For modern APIs, **JWT + refresh tokens** is a robust default, but don’t hesitate to combine patterns (e.g., OAuth for social logins).

**Next Steps:**
- Experiment with **OAuth 2.0** for third-party logins.
- Explore **session rotation** for high-security apps.
- Benchmark **Redis vs. database** for session storage.

Start small, test thoroughly, and iterate. Security is never "done"—it’s an ongoing process.

---
**Further Reading:**
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [JWT Best Practices](https://auth0.com/blog/critical-jwt-security-considerations/)
```