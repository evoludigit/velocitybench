```markdown
---
title: 'Authentication Observability: Building Security That You Can Trust'
date: 2023-11-15
tags: ['backend design', 'security', 'observability', 'authentication', 'postgres', 'api design', 'go', 'javascript']
authors: ['ben@backend-patterns.com']
---

# Authentication Observability: Building Security That You Can Trust

*How to make your authentication system more than just a "wall"—make it a strategic layer you can inspect, debug, and trust.*

---

## Intro: The Authentication Black Box

Authentication is the first line of defense in almost every application. You’ve spent weeks designing a secure setup—JWTs with short-lived tokens, OAuth flows, role-based access control (RBAC), and maybe even WebAuthn for the modern user experience. But if you’re like most developers, your audit logs look like this:

```
2023-11-15T09:23:45Z - INFO  Authentication request from IP 192.168.1.100
2023-11-15T09:23:47Z - SUCCESS Authenticated user@example.com
```

Not much to go on, right? This is the "authentication black box"—a critical layer that often lacks the observability to debug, audit, or even understand how it’s being used.

Authentication observability isn’t just a fancy term for "logging everything." It’s about intentionally instrumenting your authentication system so that you can:
- Trace failed login attempts (and why they failed).
- Detect brute-force attacks in real time.
- Correlate authentication events with application errors or business anomalies.
- Debug authentication issues for end users without asking them to repeat steps.
- Regulate access patterns to comply with security policies or audit requirements.

In this guide, we’ll cover how to build an observable authentication system, from database design to API patterns. We’ll use Postgres, Go, and JavaScript (Node.js) as examples because they’re widely used and demonstrate different approaches effectively.

---

## The Problem: When Authentication Lacks Visibility

Authentication failures aren’t just annoying—they can be expensive. Let’s explore some common pain points:

### 1. Debugging Without a Trail
Imagine a user reports that they can’t access their dashboard, but their token appears valid. Without observability, your stack trace might show a 500 error, but you have no clue if the issue is:
- A failed JWT validation (e.g., expired or malformed).
- A misconfigured role (e.g., `user` doesn’t have `dashboard_access`).
- A corrupted database row for that user.

### 2. Brute-Force Attacks Go Unnoticed
Imagine a malicious actor tries to brute-force login credentials. Without observability:
- You might not notice until users complain about account lockouts.
- You can’t detect if the same IP/device is trying multiple credentials.
- You lack evidence to block or alert on suspicious activity.

### 3. Compliance Gaps
Regulations like GDPR or SOC 2 require you to know:
- Who accessed what resources and when.
- Why authentication requests failed.
- Whether security controls (e.g., MFA) were enforced.

Without observability, you’re flying blind when it comes to compliance.

### 4. Performance Issues in Auth
If your authentication API is slow, you might notice:
- Users complaining about delays.
- But you can’t pinpoint whether the slowdown is:
  - JWT validation overhead.
  - A slow database query for user lookup.
  - A third-party identity provider (IdP) timeout.

---

## The Solution: Authentication Observability Pattern

The goal of observability is to make authentication **traceable, actionable, and auditable**. To achieve this, we’ll focus on three core components:

1. **Audit Logs**: Every authentication event is recorded with context.
2. **Metadata Tracking**: Extra details like IP, user agent, and event time.
3. **Correlation IDs**: Linking authentication events to broader system flows.
4. **Real-Time Alerts**: Detecting suspicious activity.

Let’s break it down with code examples.

---

## Step 1: Designing an Observable Authentication System

### Database Schema: Audit Logs

First, we need a table to log every authentication event. Here’s a practical Postgres schema:

```sql
CREATE TABLE auth_audit_logs (
  id BIGSERIAL PRIMARY KEY,
  event_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  event_type VARCHAR(20) NOT NULL CHECK (event_type IN ('login_attempt', 'token_issue', 'token_revoke', 'role_update')),
  user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  ip_address INET NOT NULL,
  user_agent TEXT,
  correlation_id VARCHAR(64), -- For tracing
  result BOOLEAN NOT NULL, -- true = success, false = failure
  status_code INTEGER, -- e.g., 401, 403, 429
  error_message TEXT,
  location VARCHAR(50) CHECK (location IN ('web', 'mobile', 'api', 'admin_panel')),
  metadata JSONB, -- Extra flexible data (e.g., device_id, country)
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Key details:
- **`correlation_id`**: A unique ID to link related requests (e.g., same user, same session).
- **`status_code`**: Why the request failed (e.g., 401 Unauthorized, 429 Too Many Requests).
- **`metadata`**: Flexible field for extra information (e.g., `{"country": "US", "device_type": "android"}`).

---

### Example: Logging a Login Attempt in Go

Let’s simulate a login endpoint in Go that logs every attempt. We’ll use the [chi router](https://github.com/go-chi/chi) for routing.

```go
package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"log"
	"net/http"
	"time"

	"github.com/go-chi/chi/v5"
	_ "github.com/lib/pq"
)

type AuthLog struct {
	EventType   string
	UserID      *string // NULL if anonymous user
	IPAddress   string
	UserAgent   string
	Correlation string
	Result      bool
	StatusCode  int
	ErrorMsg    string
	Location    string
	Metadata    map[string]interface{}
}

func (a *AuthLog) Log(db *sql.DB) error {
	_, err := db.Exec(`
		INSERT INTO auth_audit_logs (
			event_type, user_id, ip_address, user_agent,
			correlation_id, result, status_code, error_message,
			location, metadata
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
	`, a.EventType, a.UserID, a.IPAddress, a.UserAgent, a.Correlation,
	a.Result, a.StatusCode, a.ErrorMsg, a.Location, a.Metadata)
	return err
}

func loginHandler(db *sql.DB, w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	ip := r.RemoteAddr

	// Generate a correlation ID for tracing
	correlationID := ctx.Value("correlation_id").(string)
	if correlationID == "" {
		correlationID = generateCorrelationID()
	}

	// Parse body (simplified for example)
	var input struct {
		Username string `json:"username"`
		Password string `json:"password"`
	}
	if err := json.NewDecoder(r.Body).Decode(&input); err != nil {
		logFail(db, correlationID, ip, r.UserAgent(), "malformed_request", 400, err.Error(), "api")
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	user, err := authenticateUser(db, input.Username, input.Password)
	if err != nil {
		logFail(db, correlationID, ip, r.UserAgent(), "auth_failed", 401, err.Error(), "api")
		http.Error(w, "Invalid credentials", http.StatusUnauthorized)
		return
	}

	logSuccess(db, correlationID, ip, r.UserAgent(), user.ID, "api")
	w.WriteHeader(http.StatusOK)
	w.Write([]byte("Login successful"))
}

func logFail(db *sql.DB, correlationID, ip, userAgent, reason string, statusCode int, errMsg string, location string) {
	a := AuthLog{
		EventType:   "login_attempt",
		UserID:      nil,
		IPAddress:   ip,
		UserAgent:   userAgent,
		Correlation: correlationID,
		Result:      false,
		StatusCode:  statusCode,
		ErrorMsg:    errMsg,
		Location:    location,
		Metadata:    map[string]interface{}{"reason": reason},
	}
	a.Log(db)
}

func logSuccess(db *sql.DB, correlationID, ip, userAgent string, userID string, location string) {
	a := AuthLog{
		EventType:   "login_attempt",
		UserID:      &userID,
		IPAddress:   ip,
		UserAgent:   userAgent,
		Correlation: correlationID,
		Result:      true,
		StatusCode:  http.StatusOK,
		Location:    location,
		Metadata:    map[string]interface{}{},
	}
	a.Log(db)
}

func generateCorrelationID() string {
	return generateUUID() // Simplified; use a proper UUID library
}

func generateUUID() string {
	// Simplified for brevity
	return fmt.Sprintf("%04X%04X-0000-1000-8000-00805F9B34FB", rand.Intn(1<<48))
}
```

---

### Key Observations from This Example:
1. **Correlation ID**: Every request gets a unique ID to trace it across services.
2. **Explicit Logging**: Both successes and failures are logged.
3. **Metadata**: Extra details like `reason` are stored for debugging.

---

### Example: Logging Token Issuance in Node.js/Express

For a REST API, we can use Express middleware to log every JWT creation. Here’s a snippet:

```javascript
const express = require('express');
const jwt = require('jsonwebtoken');
const { v4: uuidv4 } = require('uuid');

const app = express();
app.use(express.json());

// Mock database client
const db = { query: async (sql, params) => console.log(sql, params) };

// Login endpoint
app.post('/login', async (req, res) => {
  const { username, password } = req.body;
  const correlationId = req.headers['x-correlation-id'] || uuidv4();

  // Simulate authentication
  const user = await db.query('SELECT * FROM users WHERE username = $1 AND password = $2', [username, password]);
  if (!user) {
    logAuthEvent({
      eventType: 'login_attempt',
      userId: null,
      ip: req.ip,
      userAgent: req.get('User-Agent'),
      correlationId,
      result: false,
      statusCode: 401,
      errorMessage: 'Invalid credentials',
      location: 'web',
      metadata: { reason: 'auth_failed' }
    });
    return res.status(401).json({ error: 'Invalid credentials' });
  }

  // Issue JWT
  const token = jwt.sign({ userId: user.id }, process.env.JWT_SECRET, { expiresIn: '1h' });

  // Log token issuance
  logAuthEvent({
    eventType: 'token_issue',
    userId: user.id,
    ip: req.ip,
    userAgent: req.get('User-Agent'),
    correlationId,
    result: true,
    statusCode: 200,
    location: 'web',
    metadata: { tokenType: 'JWT', expiration: '1h' }
  });

  res.json({ token });
});

// Helper function
async function logAuthEvent(params) {
  const sql = `
    INSERT INTO auth_audit_logs (
      event_type, user_id, ip_address, user_agent,
      correlation_id, result, status_code, error_message,
      location, metadata
    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
  `;
  await db.query(sql, [
    params.eventType,
    params.userId,
    params.ip,
    params.userAgent,
    params.correlationId,
    params.result,
    params.statusCode,
    params.errorMessage,
    params.location,
    JSON.stringify(params.metadata)
  ]);
}
```

---

## Step 2: Real-Time Monitoring

Logging alone isn’t enough—you need to act on suspicious events. Here’s how:

### 1. Rate Limiting Failed Logins
Use a sliding window to detect brute-force attempts:

```sql
-- Example: Rate limiting table
CREATE TABLE auth_rate_limits (
  user_id UUID,
  ip_address INET,
  window_start TIMESTAMPTZ,
  attempts INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (user_id, ip_address, window_start)
);

-- Helper function to check/update limits (Postgres PL/pgSQL)
CREATE OR REPLACE FUNCTION check_login_rate_limit(user_id UUID, ip_address INET) RETURNS BOOLEAN AS $$
DECLARE
  current_time TIMESTAMPTZ := NOW();
  window_minutes INTEGER := 15; -- 15-minute window
  window_start TIMESTAMPTZ;
BEGIN
  -- Calculate window start (e.g., 15 minutes ago)
  window_start := current_time - (window_minutes * 60 * INTERVAL '1 minute');

  -- Update rate limit record
  UPDATE auth_rate_limits
  SET attempts = CASE
                   WHEN attempts IS NULL THEN 1
                   ELSE attempts + 1
                 END,
      window_start = window_start
  WHERE user_id = user_id AND ip_address = ip_address AND window_start = window_start;

  -- Insert if not found
  IF NOT FOUND THEN
    INSERT INTO auth_rate_limits (user_id, ip_address, window_start, attempts)
    VALUES (user_id, ip_address, current_time - (window_minutes * 60 * INTERVAL '1 minute'), 1);
  END IF;

  -- Check if limit exceeded (e.g., 5 attempts)
  RETURN (SELECT attempts FROM auth_rate_limits
          WHERE user_id = user_id AND ip_address = ip_address AND window_start = window_start) >= 5;
END;
$$ LANGUAGE plpgsql;
```

### 2. Alerting on Brute-Force Attempts
Set up a job to check for failed logins and alert admins, e.g., with a cron job or Postgres `pg_cron`:

```sql
-- Example: Find suspicious failed logins
SELECT
  u.email,
  ip_address,
  COUNT(*) AS failed_attempts,
  MAX(event_time) AS last_attempt
FROM auth_audit_logs a
JOIN users u ON a.user_id = u.id
WHERE
  event_type = 'login_attempt'
  AND result = false
  AND error_message = 'Invalid credentials'
  AND event_time > NOW() - INTERVAL '1 hour'
GROUP BY u.email, ip_address
HAVING COUNT(*) > 3
ORDER BY failed_attempts DESC
LIMIT 10;
```

---

## Implementation Guide

### Step 1: Instrument Your Code
- Add logging for every authentication event (login, token issue/revoke, role updates).
- Include `correlation_id` in every request to trace across services.
- Use middleware to extract context (IP, user agent, etc.).

### Step 2: Design Your Database Schema
- Store audit logs with enough detail to investigate failures.
- Use JSONB for flexible metadata (e.g., `{"country": "US", "device_type": "android"}`).
- Consider partitioning large tables by time for scalability.

### Step 3: Add Rate Limiting
- Implement sliding window rate limiting for logins.
- Block IPs or ban users after X failed attempts.

### Step 4: Set Up Alerts
- Use tools like Prometheus + Alertmanager or Postgres `pg_cron` to monitor for suspicious activity.
- Example: Alert if > 10 failed logins from a single IP in 1 hour.

### Step 5: Correlate Auth with Errors
- Link authentication logs to application errors using `correlation_id`.
- Example: "User X tried to access dashboard but got a 500 error—was their token valid?"

### Step 6: Regular Audits
- Query logs for compliance (e.g., "Did all admin logins use MFA last month?").
- Example query:
  ```sql
  SELECT
    u.email,
    COUNT(*) AS failed_logins,
    MAX(a.event_time) AS last_failed_attempt
  FROM auth_audit_logs a
  JOIN users u ON a.user_id = u.id
  WHERE
    event_type = 'login_attempt'
    AND result = false
    AND a.event_time > NOW() - INTERVAL '30 days'
  GROUP BY u.email
  ORDER BY failed_logins DESC;
  ```

---

## Common Mistakes to Avoid

1. **Overlogging Sensitive Data**
   - Avoid logging plaintext passwords or sensitive user data (e.g., credit card details).
   - Redact metadata like `metadata: { "cc_number": "4111-..." }`.

2. **Ignoring Correlation IDs**
   - Without correlation IDs, you can’t trace requests across microservices.
   - Always pass the `correlation_id` in headers like `x-correlation-id`.

3. **Not Handling Rate Limiting Gracefully**
   - Don’t just reject requests—return clear error messages (e.g., "Too many attempts. Try again in 5 minutes").
   - Example:
     ```go
     if rateLimitExceeded {
       logFail(db, correlationID, ip, userAgent, "rate_limited", 429, "Too many attempts", "api")
       http.Error(w, "Too many login attempts. Please try again later.", http.StatusTooManyRequests)
       return
     }
     ```

4. **Logging Without Action**
   - If you log brute-force attempts but don’t block IPs, your logs are useless.
   - Use tools like Redis to block IPs temporarily (e.g., for 10 minutes).

5. **Compliance Gaps**
   - Don’t assume "logging everything" meets compliance. Review requirements (e.g., GDPR’s "right to be forgotten