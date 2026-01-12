```markdown
---
title: "Authentication Patterns: A Practical Guide for Backend Developers"
author: "Alex Carter"
date: "2023-11-15"
description: "A deep dive into authentication patterns, tradeoffs, and best practices for designing robust access control in your APIs. Learn from code examples and real-world considerations."
tags: ["backend", "authentication", "security", "API design", "patterns"]
---

# Authentication Patterns: A Practical Guide for Backend Developers

Authentication is the foundation of secure systems. Without it, APIs are like unlocked doors— anyone can walk in, and sensitive data is exposed. Yet, designing authentication patterns isn’t just about "making things secure." It’s about balancing **security**, **usability**, **scalability**, and **maintainability** in a way that fits your application’s needs.

In this guide, we’ll explore **real-world authentication patterns**—what they are, when to use them, and how to implement them. We’ll dive into code examples, tradeoffs, and common pitfalls so you can make informed decisions for your projects. By the end, you’ll have a toolkit of patterns you can adapt to your needs, whether you're building a simple CRUD API or a complex microservice ecosystem.

---

## The Problem: Why Authentication Patterns Matter

Imagine this: You build an API for a SaaS product, and it’s widely adopted. Initially, you might use a simple username/password combo for authentication. But as users grow, you realize:
- **Passwords alone are fragile**: Users reuse passwords, and breaches happen. A single leaked credential compromises everything.
- **Scalability becomes a nightmare**: Storing and managing session tokens server-side (e.g., in Redis) requires careful tuning as traffic grows.
- **Multi-device access is messy**: How do you revoke tokens from one device without breaking others? What if a user loses their phone and hacks the old token?
- **Third-party integrations are manual**: Adding social logins (Google, GitHub) requires custom code for each provider, complicating the system.
- **Auditability is lacking**: How do you track who accessed what data and when? Without proper authentication, you’re flying blind.

These are the **problems authentication patterns solve**. A well-designed pattern ensures:
1. **Security**: Protects against common attacks (e.g., replay attacks, credential stuffing).
2. **Usability**: Lets users authenticate with minimal friction (e.g., MFA, social logins).
3. **Scalability**: Handles millions of users without performance bottlenecks.
4. **Extensibility**: Supports features like SSO, federation, or token-based access without rewriting the auth system.

---

## The Solution: Authentication Patterns in Action

Let’s explore **three core authentication patterns**, each with tradeoffs, use cases, and code examples. We’ll focus on **stateless** patterns (preferred for modern APIs) and touch on **stateful** ones where relevant.

---

### 1. **JWT (JSON Web Token) with Stateless Authentication**
**Use Case**: RESTful APIs, microservices, or any system where scalability and horizontal scaling are priorities.

#### How It Works
JWTs are stateless tokens that encode:
- **Header**: Algorithm (e.g., `HS256`) and token type (`JWT`).
- **Payload**: Claims like `sub` (subject), `exp` (expiry), `iat` (issued at), and custom claims.
- **Signature**: Created using a secret (for HMAC) or a private key (for RSA).

The server issues a JWT upon successful authentication (e.g., after username/password validation) and sends it to the client in the `Authorization` header:
```
Authorization: Bearer <token>
```

The client includes this token in every subsequent request. The server validates the token’s signature and checks its claims (e.g., expiry, audience) without querying a database.

#### Tradeoffs
| **Pros**                          | **Cons**                          |
|-----------------------------------|-----------------------------------|
| Stateless (scalable horizontally) | No built-in refresh mechanism     |
| Compact and secure (if properly configured) | Token revocation is tricky (requires a blacklist) |
| Works well with microservices     | Short-lived tokens risk frequent re-authentication |

#### Code Example: JWT Authentication in Node.js (Express)
Here’s a minimal implementation using `jsonwebtoken` and `bcrypt` for password hashing. We’ll also handle token refresh (a common extension).

```javascript
// Server setup (app.js)
const express = require('express');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcrypt');
const app = express();

app.use(express.json());

// Mock database (replace with a real DB in production)
const users = [
  { id: 1, username: 'alice', passwordHash: bcrypt.hashSync('securepass', 10) }
];

// JWT secret and settings
const JWT_SECRET = 'your-256-bit-secret'; // In production, use env vars!
const JWT_EXPIRY = '15m';
const REFRESH_EXPIRY = '7d';

// Helper to generate tokens
const generateTokens = (user) => {
  const accessToken = jwt.sign(
    { sub: user.id, username: user.username },
    JWT_SECRET,
    { expiresIn: JWT_EXPIRY }
  );
  const refreshToken = jwt.sign(
    { sub: user.id },
    process.env.REFRESH_SECRET || JWT_SECRET,
    { expiresIn: REFRESH_EXPIRY }
  );
  return { accessToken, refreshToken };
};

// Login endpoint
app.post('/login', async (req, res) => {
  const { username, password } = req.body;
  const user = users.find(u => u.username === username);

  if (!user || !(await bcrypt.compare(password, user.passwordHash))) {
    return res.status(401).send({ error: 'Invalid credentials' });
  }

  const { accessToken, refreshToken } = generateTokens(user);
  res.json({ accessToken, refreshToken });
});

// Protected route
app.get('/protected', authenticateJWT, (req, res) => {
  res.json({ message: `Hello, ${req.user.username}!` });
});

// Refresh token endpoint
app.post('/refresh', (req, res) => {
  const { refreshToken } = req.body;
  try {
    const decoded = jwt.verify(refreshToken, process.env.REFRESH_SECRET || JWT_SECRET);
    const user = users.find(u => u.id === decoded.sub);
    if (!user) throw new Error('User not found');
    const { accessToken } = generateTokens(user);
    res.json({ accessToken });
  } catch (err) {
    res.status(401).send({ error: 'Invalid refresh token' });
  }
});

// Middleware to authenticate JWT
function authenticateJWT(req, res, next) {
  const authHeader = req.headers.authorization;
  if (!authHeader?.startsWith('Bearer ')) {
    return res.status(401).send({ error: 'Unauthorized' });
  }
  const token = authHeader.split(' ')[1];
  jwt.verify(token, JWT_SECRET, (err, user) => {
    if (err) return res.status(403).send({ error: 'Forbidden' });
    req.user = user;
    next();
  });
}

app.listen(3000, () => console.log('Server running on port 3000'));
```

#### Key Extensions
- **Refresh Tokens**: Long-lived tokens (e.g., 7 days) to avoid frequent re-login. Store them securely (e.g., HTTP-only cookies) and revoke them on logout.
- **Token Revocation**: Use a Redis set to track invalidated tokens (not scalable for millions of users).
- **Short-Lived Tokens**: Issue new tokens for each request (e.g., OAuth 2.0 "short-lived access token").

---

### 2. **OAuth 2.0 / OpenID Connect**
**Use Case**: When you need **delegated authentication** (e.g., "Login with Google") or **fine-grained access control** (e.g., APIs for third parties).

#### How It Works
OAuth 2.0 is a framework for **authorization**, while OpenID Connect (OIDC) adds an **identity layer** (e.g., claiming who the user is). Here’s the flow for a typical OAuth 2.0 authorization code grant (used by apps like GitHub, Google):

1. **User requests access**: The app redirects the user to the OAuth provider (e.g., Google) with a `client_id` and `redirect_uri`.
   ```http
   GET https://accounts.google.com/o/oauth2/auth?
     response_type=code&
     client_id=YOUR_CLIENT_ID&
     redirect_uri=http://yourapp.com/callback&
     scope=openid%20profile%20email&
     state=random_state_string
   ```
2. **User grants access**: The provider redirects back to your app with an **authorization code**.
   ```http
   GET http://yourapp.com/callback?code=AUTH_CODE&state=random_state_string
   ```
3. **App exchanges code for tokens**: The app sends the `code` to the provider’s token endpoint to get an **access token** (and optionally a **refresh token**).
4. **App calls APIs**: The access token is included in requests to protected APIs (e.g., Google’s APIs).

OIDC adds a **ID token** (a JWT) that proves the user’s identity (e.g., `sub`, `email`, `name`).

#### Tradeoffs
| **Pros**                          | **Cons**                          |
|-----------------------------------|-----------------------------------|
| Built for scalability (used by Google, GitHub) | Complex to implement from scratch |
| Supports third-party logins      | Requires compliance with provider policies |
| Fine-grained scopes               | Tokens may expose more than needed (e.g., `openid` + `profile` + `email`) |

#### Code Example: OAuth 2.0 with Passport.js (Node.js)
Passport.js simplifies OAuth integration. Below is a minimal setup with Google OAuth.

```javascript
// Install dependencies: npm install express passport passport-google-oauth20
const express = require('express');
const passport = require('passport');
const GoogleStrategy = require('passport-google-oauth20').Strategy;
const session = require('express-session');

const app = express();
app.use(express.json());
app.use(session({ secret: 'your-secret', resave: false, saveUninitialized: false }));
app.use(passport.initialize());
app.use(passport.session());

// Configure Google Strategy
passport.use(new GoogleStrategy({
    clientID: process.env.GOOGLE_CLIENT_ID,
    clientSecret: process.env.GOOGLE_CLIENT_SECRET,
    callbackURL: 'http://yourapp.com/auth/google/callback'
  },
  (accessToken, refreshToken, profile, done) => {
    // Save user to database (e.g., users table) and return user object
    return done(null, { id: profile.id, username: profile.displayName, email: profile.emails?.[0].value });
  }
));

passport.serializeUser((user, done) => done(null, user.id)); // Store user ID in session
passport.deserializeUser((id, done) => {
  // Load user from database
  const user = users.find(u => u.id === id);
  done(null, user);
});

// OAuth login route
app.get('/auth/google',
  passport.authenticate('google', { scope: ['profile', 'email'] })
);

app.get('/auth/google/callback',
  passport.authenticate('google', { failureRedirect: '/login' }),
  (req, res) => {
    // Successful authentication, redirect home.
    res.redirect('/dashboard');
  }
);

// Protected route
app.get('/dashboard',
  requireAuth, // Custom middleware to check session
  (req, res) => {
    res.json({ message: `Welcome, ${req.user.username}!` });
  }
);

// Custom middleware to check session
function requireAuth(req, res, next) {
  if (req.isAuthenticated()) return next();
  res.status(401).send({ error: 'Unauthorized' });
}

app.listen(3000, () => console.log('Server running on port 3000'));
```

#### Key Extensions
- **PKCE (Proof Key for Code Exchange)**: Adds security for public clients (e.g., mobile apps) by preventing code interception attacks.
- **Token Scopes**: Request only the permissions you need (e.g., `https://api.example.com/scopes/read`).
- **Introspection**: Some providers offer `/introspect` endpoints to check if a token is valid without calling a protected API.

---

### 3. **Session-Based Authentication (Stateful)**
**Use Case**: Internal tools, low-scalability apps, or legacy systems where statelessness isn’t critical.

#### How It Works
The server stores session data (e.g., user ID, auth state) in memory or a database. Upon login, the server issues a **session ID** (e.g., a cookie) and associates it with the user. Subsequent requests include this cookie, and the server looks up the session.

Example flow:
1. User logs in with username/password.
2. Server validates credentials and creates a session in memory/database.
3. Server sets a cookie with `sessionId=abc123`.
4. Client sends the cookie in every request.
5. Server validates the cookie and retrieves the session.

#### Tradeoffs
| **Pros**                          | **Cons**                          |
|-----------------------------------|-----------------------------------|
| Simple to implement               | Stateful (scales poorly horizontally) |
| Built-in session management      | Cookie-based tokens are vulnerable to CSRF |
| Works well with web apps          | Harder to debug (server-side state) |

#### Code Example: Session-Based Auth in Python (Flask)
Here’s a Flask app using `flask-session` with Redis for session storage.

```python
# Install dependencies: pip install flask flask-session redis
from flask import Flask, request, jsonify, session, redirect, url_for
from flask_session import Session
import bcrypt
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.from_url('redis://localhost:6379')  # Use Redis for sessions

# Initialize session
Session(app)

# Mock database
users = [
    {'id': 1, 'username': 'bob', 'password_hash': bcrypt.hashpw(b'password123', bcrypt.gensalt()).decode()}
]

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password').encode()

    user = next((u for u in users if u['username'] == username), None)
    if not user or not bcrypt.checkpw(password, user['password_hash'].encode()):
        return jsonify({'error': 'Invalid credentials'}), 401

    # Start a new session
    session['user_id'] = user['id']
    session.permanent = True  # Use cookie for longer sessions
    return jsonify({'message': 'Logged in successfully'})

@app.route('/protected')
def protected():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    user = next(u for u in users if u['id'] == session['user_id'])
    return jsonify({'message': f'Hello, {user["username"]}!'})

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
```

#### Key Extensions
- **CSRF Protection**: Use `flask-talisman` or similar to add `SameSite` cookies.
- **Session Timeout**: Configure `SESSION_COOKIE_AGE` and `SESSION_COOKIE_SECURE` (HTTPS only).
- **Secure Cookies**: Set `Secure`, `HttpOnly`, and `SameSite=Strict` flags.

---

## Implementation Guide: Choosing Your Pattern

Now that we’ve covered the patterns, how do you choose? Here’s a decision tree:

1. **Is your app RESTful or microservices-based?**
   - **Yes**: Prefer **JWT** or **OAuth 2.0** (stateless).
   - **No (e.g., traditional web apps)**: Session-based auth may suffice.

2. **Do you need third-party logins (e.g., Google, GitHub)?**
   - **Yes**: Use **OAuth 2.0/OIDC**.
   - **No**: JWT or sessions work.

3. **Are you scaling horizontally?**
   - **Yes**: Avoid sessions (use JWT or OAuth).
   - **No**: Sessions are fine.

4. **Do you need fine-grained permissions?**
   - **Yes**: Combine JWT with **Role-Based Access Control (RBAC)** or **Attribute-Based Access Control (ABAC)**.
   - **No**: Basic JWT claims are sufficient.

5. **Do users need to access APIs from mobile/SPAs?**
   - **Yes**: Use **JWT** (SPAs can store tokens securely in `localStorage` or HTTP-only cookies for backend apps).
   - **No**: Sessions may work.

---

## Common Mistakes to Avoid

1. **Using JWT Without a Refresh Mechanism**
   - Problem: Short-lived JWTs force users to log in frequently.
   - Fix: Implement refresh tokens (stored in HTTP-only cookies).

2. **Storing Secrets in Code**
   - Problem: Hardcoding `JWT_SECRET` or database passwords in your repo.
   - Fix: Use environment variables (e.g., `dotenv` in Node.js, `python-dotenv` in Python).

3. **Not Validating Tokens on the Server**
   - Problem: Blindly trusting client-side token validation.
   - Fix: Always re-validate tokens on the server (even if the client does it too).

4. **Overusing Superadmin Tokens**
   - Problem: Generating long-lived admin tokens with minimal scopes.
   - Fix: Use short-lived tokens even for admins and rotate them frequently.

5. **Ignoring Token Revocation**
   - Problem: Users can’t log out other devices (e.g., lost phone still has a valid token).
   - Fix: Implement blacklists (for small-scale) or token binding (e.g., requiring a device ID).

6. **Not Using HTTPS**
   - Problem: Tokens (especially JWTs) can be intercepted in transit.
   - Fix: Enforce HTTPS in production.

7. **Assuming All JWTs Are Equal**
   - Problem: Using `HS256` (HMAC) instead of `RS256` (RSA) for security-critical apps.
   - Fix: