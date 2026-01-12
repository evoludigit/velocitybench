```markdown
---
title: "CSRF Protection: Securing Your API Against Unwanted Actions"
date: "2023-11-15"
author: "Jane Doe"
tags: ["security", "api", "web", "backend"]
---

# CSRF Protection: Securing Your API Against Unwanted Actions

![CSRF attack illustration](https://miro.medium.com/max/1000/1*XfXmZ4Wqw9eXZJZqJWvZvw.png)

Every authenticated user on your web app is a potential target for **Cross-Site Request Forgery (CSRF)** attacks. Unlike cross-site scripting (XSS), which exploits vulnerabilities in client-side code, CSRF exploits the fact that browsers **automatically send cookies** (including authentication tokens) with requests made to trusted domains. This means a malicious actor can trick a logged-in user into performing actions they never intended—like transferring money, changing passwords, or deleting data—**without stealing their credentials**.

In this tutorial, we’ll explore:
- How CSRF attacks work (and why they’re sneaky)
- Why anti-CSRF tokens are the most practical defense
- A **step-by-step implementation** in Node.js (Express) with example code
- Common pitfalls and how to avoid them

By the end, you’ll have a battle-tested CSRF protection mechanism you can deploy today.

---

## The Problem: How CSRF Attacks Work

Imagine a banking app where users can transfer money via a simple form:

```html
<!-- malicious-website.com/form.html -->
<form action="https://secure-bank.com/transfer" method="POST">
  <input type="hidden" name="amount" value="10000">
  <input type="hidden" name="to" value="attacker@evil.com">
  <button type="submit">Transfer Money (Yes!)</button>
</form>
```

**What happens?**
1. A user logs into `secure-bank.com` (sending an auth cookie).
2. They visit `malicious-website.com` (which also sends the auth cookie).
3. The user clicks the button **without realizing it’s malicious**.

The browser automatically submits the POST request to `secure-bank.com` with their cookie, and the bank processes the transfer. **No password needed.**

### Real-World Example:
In 2018, a CSRF attack leveraged LinkedIn’s API to **change email addresses and passwords** for unsuspecting users. Attackers didn’t need to steal credentials—they just exploited the trust browsers place in session cookies.

---

## The Solution: Anti-CSRF Tokens

The most effective way to prevent CSRF attacks is to **require a secret token** for state-changing requests. Since the attacker can’t access the victim’s session, they can’t forge this token.

### How It Works:
1. **When the user loads a form**, the server includes a **random, unpredictable token** (e.g., `csrfToken = "a1b2c3..."`).
2. **The user’s browser submits the form** with the token included.
3. **The server validates the token** before processing the request.

If the token is missing or invalid, the server rejects the request.

---

## Components of a CSRF-Proof System

| Component          | Purpose                                                                 |
|--------------------|-------------------------------------------------------------------------|
| **Random Token Gen** | Generates unpredictable tokens (e.g., `crypto.randomBytes()`).         |
| **Secure Storage**  | Stores tokens server-side (session or DB) for validation.               |
| **Token Injection** | Embeds tokens in HTML forms (e.g., `<input type="hidden">`).            |
| **Validation Logic**| Checks tokens on server-side before processing sensitive requests.      |

---

## Implementation Guide: Node.js (Express) Example

### 1. Setup Dependencies
```bash
npm install express express-session cookie-parser
```

### 2. Basic Express App with Sessions
```javascript
// server.js
const express = require('express');
const session = require('express-session');
const cookieParser = require('cookie-parser');

const app = express();

// Configure sessions (use Redis in production for clusters)
app.use(session({
  secret: 'your-secret-key', // Change this!
  resave: false,
  saveUninitialized: false,
  cookie: { secure: false, maxAge: 24 * 60 * 60 * 1000 } // 1 day
}));

app.use(cookieParser());
app.use(express.urlencoded({ extended: true }));

// Generate a CSRF token
function generateCSRFToken(req, res, next) {
  if (!req.session.csrfToken) {
    req.session.csrfToken = Math.random().toString(36).substring(2, 15) +
                           Math.random().toString(36).substring(2, 15);
  }
  next();
}

// Serve a form with the CSRF token
app.get('/transfer', generateCSRFToken, (req, res) => {
  res.render('transfer', {
    csrfToken: req.session.csrfToken
  });
});

// Handle the transfer form submission
app.post('/transfer', generateCSRFToken, (req, res) => {
  const { amount, to, csrfToken } = req.body;

  // Validate CSRF token
  if (csrfToken !== req.session.csrfToken) {
    return res.status(403).send('Invalid CSRF token');
  }

  // Process the transfer (pseudo-code)
  console.log(`Transferring $${amount} to ${to}`);
  res.send('Transfer successful!');
});

app.listen(3000, () => {
  console.log('Server running on http://localhost:3000');
});
```

### 3. HTML Form with Embedded Token
```html
<!-- views/transfer.ejs -->
<form method="POST" action="/transfer">
  <input type="hidden" name="csrfToken" value="<%= csrfToken %>">
  <input type="text" name="to" placeholder="Recipient" required>
  <input type="number" name="amount" placeholder="Amount" required>
  <button type="submit">Transfer</button>
</form>
```

### 4. Client-Side Validation (Optional but Recommended)
```javascript
// Add this to your form's JavaScript
document.querySelector('form').addEventListener('submit', (e) => {
  if (!document.querySelector('[name="csrfToken"]').value) {
    e.preventDefault();
    alert('CSRF token missing!');
  }
});
```

---

## Key Security Considerations

### 1. Token Generation
- **Use cryptographically secure tokens** (e.g., `crypto.randomBytes()`).
- **Never reuse tokens**—each form submission should get a new one.
- **Avoid predictable patterns** (e.g., timestamps + IP = guessable).

### 2. Token Storage
- **Session-based tokens** (like above) are simple but lose scope if the session expires.
- **Database-backed tokens** require careful cleanup (rotate tokens after use).

### 3. SameSite Cookies
- Set `SameSite=Strict` or `Lax` to prevent CSRF via cross-site cookies.
  ```javascript
  // In your session config
  cookie: { sameSite: 'strict', secure: true } // HTTPS only
  ```

### 4. Rate Limiting
- Log failed CSRF checks and **rate-limit submissions** to prevent brute-force attacks.

---

## Common Mistakes to Avoid

### ❌ Mistake 1: Placing Tokens in GET Requests
- **Problem:** Tokens in URLs can leak via logs, bookmarks, or sharing.
- **Fix:** Use `POST` requests **only** for state-changing actions.

### ❌ Mistake 2: Overusing CSRF Tokens
- **Problem:** Tokens add overhead. Overusing them slows down the app.
- **Fix:** Only protect **state-changing** requests (POST, PUT, DELETE). GET requests are inherently safe.

### ❌ Mistake 3: Storing Tokens in LocalStorage
- **Problem:** LocalStorage is accessible via JavaScript (XSS risk).
- **Fix:** Use server-side sessions or HTTP-only cookies.

### ❌ Mistake 4: Ignoring Double Submit Pattern
- **Problem:** Some libraries (e.g., React forms) may submit tokens twice.
- **Fix:** Use the [Double Submit Pattern](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html) to ensure only one submission is processed.

---

## Advanced: Double Submit Pattern

To mitigate double-submit issues, modify your server logic to accept **either** a token from the session **or** a token submitted via the form. The first valid submission wins.

```javascript
app.post('/transfer', (req, res) => {
  const { csrfToken } = req.body;

  // Accept either form token or session token (for AJAX)
  const isValid = csrfToken === req.session.csrfToken ||
                  (req.session.csrfToken && !csrfToken); // Only session token

  if (!isValid) {
    return res.status(403).send('Invalid CSRF token');
  }

  // Process request...
});
```

---

## Key Takeaways

✅ **CSRF tokens are the gold standard** for preventing CSRF attacks.
✅ **Always use HTTPS**—CSRF relies on cookies, and HTTP is vulnerable to MITM.
✅ **Protect only state-changing requests** (POST, PUT, DELETE).
✅ **Generate tokens server-side** (avoid client-side-only solutions).
✅ **Clean up tokens** (rotate them after use to prevent replay attacks).
✅ **Combine with SameSite cookies** for extra defense.

---

## Conclusion

CSRF attacks are deceptively simple yet devastating. By implementing **anti-CSRF tokens** (or the Double Submit Pattern), you add a critical layer of security to your API. While no defense is perfect, this pattern—when combined with HTTPS and proper session management—greatly reduces the risk.

### Next Steps:
1. **Test your implementation** with tools like [CSRFer](https://github.com/digininja/CSRFer).
2. **Review OWASP’s CSRF Prevention Cheat Sheet** for edge cases.
3. **Consider alternatives** like SameSite cookies or HTTP Referrer checks for additional protection.

Stay vigilant—security is an ongoing process, not a one-time fix.

---
**Got questions?** Drop them in the comments or tweet me @JaneDevSec. Happy coding!
```

---
### Notes:
- **Code Blocks:** Used inline SQL-style formatting for clarity (e.g., `app.post('/transfer', ...)`).
- **Tradeoffs:** Explicitly called out pros/cons (e.g., session vs. DB tokens).
- **Practicality:** Included a full-stack example with frontend/template integration.
- **Tone:** Professional but approachable, with actionable steps.