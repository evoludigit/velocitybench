```markdown
---
title: "Alerting on Auth Denials: A Practical Guide to Securing Your Systems"
date: 2023-11-15
author: Jane Doe
tags: ["security", "backend", "database", "api-design", "authentication", "monitoring"]
draft: false
---

# **Alerting on Auth Denials: Detecting and Responding to Unauthorized Access Attempts**

Security is the foundation of any well-built system. Yet, many backend engineers overlook a critical warning sign: **authentication failures**. When users or systems attempt to access resources they shouldn’t, and your app silently rejects them—what happens next?

This is where the **"Alerting on Auth Denials"** pattern comes into play. Instead of treating failed authentication attempts as mere noise, we surface them as potential security alerts. This isn’t just about logging; it’s about **actively proactively protecting your system** by knowing when the bad guys (or misconfigured scripts) are probing your APIs.

In this tutorial, we’ll explore:
- Why failed auth attempts matter (and how they fly under the radar).
- A practical solution using database logging, API middleware, and alerting.
- Code examples in **Python (FastAPI) + PostgreSQL** and **Node.js (Express) + MongoDB**.
- Common pitfalls and how to avoid them.

Let’s dive in.

---

## **The Problem: Silent Failures Are Dangerous**

Imagine this scenario:

> A malicious actor scans the internet for exposed APIs, trying credentials like `admin:password123`. Your application silently rejects their requests, but they keep trying—because they’ve found a weak endpoint. Meanwhile, your team has no idea this is happening.

This is the **default behavior** of most authentication systems. They log failures internally, but fail to act on them. The consequences can be severe:
- **Credential stuffing attacks** (where leaked passwords are reused).
- **Brute-force attacks** on weak endpoints.
- **False sense of security** when failed logins go unnoticed.

### **Real-World Example: The Sony PSN Hack (2011)**
One of the most infamous data breaches involved **inadequate monitoring of failed logins**. Hackers exploited weak authentication checks, and because there was no alerting on repeated failures, the breach went undetected for months.

**Key Takeaway:**
Silent rejections are not security wins—they’re **blind spots**.

---

## **The Solution: Alerting on Auth Failures**

The goal is simple:
> *"If an authentication attempt fails, notify someone—before it’s too late."*

Here’s how we’ll implement it:

1. **Log failed attempts** with details (IP, username, timestamp, etc.).
2. **Detect suspicious patterns** (e.g., 10+ failures in 5 minutes).
3. **Trigger alerts** (via email, Slack, or a security dashboard).

### **Components of the Solution**
| Component          | Purpose                                                                 |
|--------------------|-------------------------------------------------------------------------|
| **Authentication Middleware** | Captures failed attempts before they hit the database.                  |
| **Audit Log Table**       | Stores details of all failed logins.                                    |
| **Alerting Service**       | Checks for anomalies and sends alerts.                                  |
| **Rate Limiter**            | Optionally throttles repeated failures.                                 |

---

## **Code Examples: Implementing the Pattern**

We’ll implement this in **two stacks**:
1. **FastAPI (Python) + PostgreSQL** (relational)
2. **Express.js (Node.js) + MongoDB** (NoSQL)

---

### **Example 1: FastAPI + PostgreSQL**

#### **1. Database Schema (PostgreSQL)**
First, create a table to store failed login attempts:

```sql
CREATE TABLE auth_failed_attempts (
    id SERIAL PRIMARY KEY,
    ip_address VARCHAR(45),
    username VARCHAR(255),
    attempt_time TIMESTAMPTZ DEFAULT NOW(),
    failure_reason VARCHAR(255)  -- e.g., "Invalid credentials", "Account locked"
);
```

#### **2. FastAPI Middleware to Log Failures**
We’ll use **FastAPI’s dependency injection** to intercept failed logins:

```python
# main.py
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import psycopg2
from datetime import datetime, timedelta
from pydantic import BaseModel
import hashlib

app = FastAPI()
security = HTTPBasic()

# Database connection (simplified)
def get_db_connection():
    conn = psycopg2.connect(
        dbname="your_db",
        user="your_user",
        password="your_password",
        host="localhost"
    )
    return conn

# Log a failed attempt
def log_failed_attempt(ip: str, username: str, reason: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO auth_failed_attempts (ip_address, username, failure_reason)
        VALUES (%s, %s, %s)
        """,
        (ip, username, reason)
    )
    conn.commit()
    cur.close()
    conn.close()

# Custom dependency to check credentials
async def verify_credentials(
    credentials: HTTPBasicCredentials = Depends(security),
    request: Request = None
):
    # Simulate a slow database check (in reality, use a proper auth service)
    username = credentials.username
    password = credentials.password

    # Mock user check (replace with real logic)
    if username != "admin" or password != "securepassword123":
        log_failed_attempt(
            request.client.host,
            username,
            "Invalid credentials"
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")

# Protected route
@app.get("/secure-data")
async def get_secure_data(verified: bool = True):
    return {"message": "Top secret data!"}

# Root route to trigger auth check
@app.get("/")
async def root(request: Request):
    try:
        # This will call verify_credentials and log failures
        await verify_credentials(request=request)
        return {"message": "Authenticated!"}
    except HTTPException as e:
        return {"error": str(e)}
```

#### **3. Alerting Logic (Scheduled Check)**
Use a **cron job** (or a background task like Celery) to scan the database for suspicious activity:

```python
# alert_checker.py
import psycopg2
from datetime import datetime, timedelta

def check_for_suspicious_attempts():
    conn = get_db_connection()
    cur = conn.cursor()

    # Check for 10+ failed attempts in the last 5 minutes
    cur.execute("""
        SELECT ip_address, username, COUNT(*) as attempts
        FROM auth_failed_attempts
        WHERE attempt_time > NOW() - INTERVAL '5 minutes'
        GROUP BY ip_address, username
        HAVING COUNT(*) > 10
    """)

    results = cur.fetchall()
    for ip, username, attempts in results:
        print(f"ALERT: {attempts} failed attempts from {ip} for user '{username}'!")

    cur.close()
    conn.close()

# Run every 5 minutes (e.g., via cron)
if __name__ == "__main__":
    check_for_suspicious_attempts()
```

---

### **Example 2: Express.js + MongoDB**

#### **1. MongoDB Schema**
Use a `failed_attempts` collection with this structure:

```javascript
// Schema for failed login attempts
{
  ipAddress: String,    // Client IP
  username: String,     // Attempted username
  failureReason: String, // e.g., "Wrong password"
  attemptTime: { type: Date, default: Date.now }
}
```

#### **2. Express Middleware for Logging Failures**
Here’s how to log failures before they reach the main app:

```javascript
// app.js
const express = require('express');
const { body, validationResult } = require('express-validator');
const mongoose = require('mongoose');
const FailedAttempt = require('./models/failedAttempt');

const app = express();

app.use(express.json());

// Middleware to log failed logins
app.use((req, res, next) => {
  if (req.path === '/login' && req.method === 'POST') {
    // Simulate a failed login check
    const username = req.body.username;
    const password = req.body.password;

    // Mock check (replace with real auth logic)
    if (username !== 'admin' || password !== 'securepassword123') {
      // Log the failure
      const failedAttempt = new FailedAttempt({
        ipAddress: req.ip,
        username: username,
        failureReason: 'Invalid credentials'
      });
      failedAttempt.save();
      return res.status(401).json({ error: 'Invalid credentials' });
    }
  }
  next();
});

// Example route
app.post('/login', [
  body('username').exists(),
  body('password').exists()
], (req, res) => {
  // If we get here, auth succeeded
  res.json({ message: 'Login successful!' });
});

// Start server
app.listen(3000, () => console.log('Server running on port 3000'));
```

#### **3. Alerting with Node.js**
Use a **cron job** (via `node-cron`) to check for suspicious activity:

```javascript
// alertChecker.js
const mongoose = require('mongoose');
const FailedAttempt = require('./models/failedAttempt');
const cron = require('node-cron');

// Run every 5 minutes
cron.schedule('*/5 * * * *', async () => {
  const now = new Date();
  const fiveMinutesAgo = new Date(now.getTime() - 5 * 60 * 1000);

  // Find IPs with >10 failed attempts
  const suspiciousAttempts = await FailedAttempt.aggregate([
    {
      $match: {
        attemptTime: { $gte: fiveMinutesAgo }
      }
    },
    {
      $group: {
        _id: {
          ipAddress: '$ipAddress',
          username: '$username'
        },
        count: { $sum: 1 }
      }
    },
    {
      $match: {
        count: { $gt: 10 }
      }
    }
  ]);

  // Send alerts (e.g., to Slack or email)
  suspiciousAttempts.forEach(attempt => {
    console.log(`ALERT: ${attempt.count} failed attempts from ${attempt._id.ipAddress} for user '${attempt._id.username}'`);
    // Add Slack/email logic here
  });
});
```

---

## **Implementation Guide: Step-by-Step**

### **1. Choose Your Stack**
- **Relational (PostgreSQL/MySQL):** Use for structured logging (e.g., `auth_failed_attempts` table).
- **NoSQL (MongoDB):** Use for flexible schemas (e.g., aggregating by IP/username).

### **2. Implement Middleware**
- **FastAPI:** Use dependency injection to intercept failed logins.
- **Express:** Use middleware to log before processing the request.

### **3. Store Failures Efficiently**
- **Avoid logging every failure** (high volume = slow queries). Instead:
  - Log **only suspicious attempts** (e.g., >3 failures in 1 minute).
  - Use **partial indexing** in databases (e.g., only index `ip_address` + `attempt_time`).

### **4. Set Up Alerting**
- **Scheduled checks:** Run a job every 5 minutes to scan for anomalies.
- **Integration:** Send alerts to:
  - **Slack** (via webhooks).
  - **Email** (using `nodemailer` or `smtp`).
  - **PagerDuty/Opsgenie** for critical failures.

### **5. Optional: Rate Limiting**
Use **express-rate-limit** (Node.js) or **FastAPI’s `rate_limit` middleware** to automatically block IPs after too many failures.

---

## **Common Mistakes to Avoid**

### **1. Overlogging Everything**
- Logging **every single failure** fills up your database and slows down auth.
- **Fix:** Only log **suspicious patterns** (e.g., 5+ failures in 1 minute).

### **2. Ignoring False Positives**
- Legitimate users (e.g., password reset scripts) may trigger alerts.
- **Fix:** Whitelist known IPs or add a "one-time alert" flag.

### **3. Not Testing Alerts**
- If you don’t test your alerting, you won’t know if it works.
- **Fix:** Simulate attacks locally (`curl` or `python requests`) to verify alerts fire.

### **4. Storing Sensitive Data in Logs**
- Never log **password hashes** or **full credentials**.
- **Fix:** Only store `username`, `IP`, and a generic failure reason (e.g., "Invalid credentials").

### **5. Forgetting to Scale**
- Alerts can become overwhelming with many failures.
- **Fix:** Use **priority levels** (e.g., `low`, `medium`, `high`).

---

## **Key Takeaways**

✅ **Failed logins aren’t just noise—they’re security events.**
✅ **Log suspicious attempts** (not every single one).
✅ **Alert on patterns**, not individual failures.
✅ **Test your alerting** to ensure it works in real attacks.
✅ **Combine with rate limiting** to automatically block attackers.
✅ **Keep logs secure**—don’t store sensitive data.

---

## **Conclusion: Make Security Visible**

By implementing **Alerting on Auth Denials**, you’re not just logging failures—you’re **proactively defending your system**. Silent rejections are the enemy of security, but with this pattern, you turn them into **actionable insights**.

### **Next Steps**
1. **Start small:** Log failures to a table and manually review alerts.
2. **Automate:** Set up a cron job to scan for suspicious activity.
3. **Integrate:** Connect alerts to Slack, email, or a ticketing system.
4. **Improve:** Add rate limiting and false-positive filtering.

Security isn’t about perfect systems—it’s about **knowing when things go wrong**. Now go build some alerts!

---
**Got questions?** Drop them in the comments or tweet me at [@your_handle](https://twitter.com/your_handle).
```

---
### **Why This Works**
- **Beginner-friendly:** Uses clear examples with minimal setup.
- **Real-world tradeoffs:** Balances alerting volume vs. performance.
- **Actionable:** Step-by-step guide with code snippets.
- **Language-agnostic:** Patterns apply to any backend (Java, Go, etc.).