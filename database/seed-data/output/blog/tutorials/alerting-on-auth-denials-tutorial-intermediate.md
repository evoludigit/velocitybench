```markdown
---
title: "Security First: Alerting on Auth Denials Like a Pro"
date: "2023-10-15"
author: "Alex Carter"
description: "Learn how to implement the Alerting on Auth Denials pattern to proactively detect and respond to suspicious access attempts that should have been blocked but weren't"
tags: ["backend", "database", "security", "patterns", "alerting", "authentication", "api", "monitoring"]
---

# Security First: Alerting on Auth Denials Like a Pro

![Security Shield Alert](https://via.placeholder.com/1200x400/000000/FFFFFF?text=Security+Shields+Ignoring+Auth+Denials+Are+Like+Leaving+Your+Door+Open+At+Night)

Every backend engineer knows that security is paramount. We write secure code, use encrypted connections, and enforce least-privilege principles. But despite our best efforts, security breaches still happen. One underrated but critical aspect of security is **proactively monitoring for authentication failures**—particularly those that *should* have been denied but weren’t. In this post, we’ll explore the **Alerting on Auth Denials** design pattern, a simple yet powerful way to catch security issues before they escalate.

---

## The Problem: Why Auth Denials Matter

Imagine this scenario:
- A user, `alice@example.com`, tries to access a sensitive endpoint (`/api/admin/transfer`) using an API key tied to a read-only role.
- Your application correctly rejects the request with a `403 Forbidden` response.
- Alice never tries again, and life goes on.

Now, imagine **Alice’s compromised account**:
- A malicious actor steals Alice’s credentials (or API key).
- The attacker attempts the same `/api/admin/transfer` request.
- Your app still correctly denies the request… **but you never know it happened.**

While this might seem like a victory (the request was blocked), consider the implications:
1. **Race Condition**: If the attacker tries different endpoints, they might stumble upon one that’s *not* properly secured.
2. **Credential Harvesting**: Repeated 403 responses suggest Alice’s credentials are active and worth further probing.
3. **Compliance Risks**: Many regulations (e.g., GDPR, PCI-DSS) require monitoring for unauthorized access attempts.

This is where **Alerting on Auth Denials** becomes critical. The pattern isn’t about catching every single failed attempt (which would be noisy), but rather **flagging suspicious patterns**—like an attacker systematically probing for weaknesses after a successful breach.

---

## The Solution: Alerting on Auth Denials

The core idea is simple:
1. **Log all 403 responses** (or other auth failures) where the requester was *supposed* to be denied.
2. **Monitor for anomalous behavior** (e.g., bursty attempts, repeated probes, or patterns of access that violate least privilege).
3. **Alert operators** when such behavior is detected, enabling rapid investigation.

This pattern works best with:
- **Role-based access control (RBAC)**: Clear definitions of what a user/role *should* or *shouldn’t* access.
- **Audit trails**: Every 403 response should include metadata like:
  - Requester identity (user, client, device, etc.).
  - Resource being accessed (endpoint, table, etc.).
  - Time of attempt.
  - Requester’s expected permissions (e.g., "read-only").
- **Alerting infrastructure**: Tools like Prometheus + Alertmanager, Datadog, or a custom solution.

---

## Components/Solutions

### 1. Logging Auth Denials
First, ensure your application logs all auth denials. Here’s how to implement this in **Python (FastAPI)** and **Node.js (Express)**:

#### FastAPI (Python) Example
```python
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.security import APIKeyHeader
import logging

app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simulate API key validation (replace with your auth logic)
API_KEY_HEADER = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_HEADER, auto_error=False)

def verify_api_key(api_key: str = Depends(api_key_header)):
    # In a real app, verify against a database or service
    valid_keys = {"admin:read-only", "user:default"}

    if api_key not in valid_keys:
        logger.warning(f"Denied access for API key: {api_key}")
        raise HTTPException(status_code=403, detail="Forbidden")

@app.get("/api/admin/transfer")
async def transfer_funds(request: Request, api_key: str = Depends(verify_api_key)):
    # Your endpoint logic here
    return {"status": "success"}
```

#### Node.js (Express) Example
```javascript
const express = require('express');
const winston = require('winston');
const app = express();

// Configure logging
const logger = winston.createLogger({
  level: 'info',
  transports: [new winston.transports.Console()],
});

// Simulate API key validation
const validApiKeys = new Set(["admin:read-only", "user:default"]);

function verifyApiKey(req, res, next) {
  const apiKey = req.headers['x-api-key'];
  if (!apiKey || !validApiKeys.has(apiKey)) {
    logger.warn(`Denied access for API key: ${apiKey}`);
    return res.status(403).json({ error: "Forbidden" });
  }
  next();
}

app.get('/api/admin/transfer', verifyApiKey, (req, res) => {
  // Your endpoint logic here
  res.json({ status: "success" });
});

app.listen(3000, () => console.log('Server running'));
```

### 2. Database Schema for Auth Denials
Store denied requests in a dedicated table with metadata. Here’s a **PostgreSQL** schema:

```sql
CREATE TABLE auth_denials (
    id BIGSERIAL PRIMARY KEY,
    requester_type VARCHAR(20) NOT NULL,  -- "user", "api_key", "service_account", etc.
    requester_id TEXT NOT NULL,
    resource_type VARCHAR(50) NOT NULL,    -- "endpoint", "table", "row"
    resource_id TEXT,
    denied_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status_code INTEGER NOT NULL,          -- 403, 401, etc.
    user_agent TEXT,
    ip_address INET,
    metadata JSONB                     -- Extra context (e.g., role, expected permissions)
);

CREATE INDEX idx_auth_denials_requester_id ON auth_denials(requester_id);
CREATE INDEX idx_auth_denials_resource_type_id ON auth_denials(resource_type, resource_id);
CREATE INDEX idx_auth_denials_denied_at ON auth_denials(denied_at);
```

### 3. Alerting Logic
Use a time-series database (e.g., InfluxDB, Prometheus) or a monitoring tool (e.g., Datadog) to detect anomalies. Example **PromQL query** to alert on sudden spikes in auth denials:

```promql
# Alert if >100 auth denials occur in a 1-minute window
rate(auth_denials_total[1m]) > 100
```

For a custom solution, use Python’s `pandas` to analyze patterns:

```python
import pandas as pd
from datetime import datetime, timedelta

# Load data (example: CSV exported from your DB)
df = pd.read_csv("auth_denials.csv", parse_dates=["denied_at"])

# Filter for the last 24 hours
df = df[df["denied_at"] >= datetime.now() - timedelta(hours=24)]

# Group by requester_id and count attempts
attempts_by_user = df.groupby("requester_id").size().reset_index(name="count")

# Alert if any user has >100 attempts
alert_users = attempts_by_user[attempts_by_user["count"] > 100]
print(alert_users)
```

### 4. Alerting Channels
Send alerts via:
- **Email** (e.g., using `smtplib` in Python).
- **Slack** (webhook integration).
- **PagerDuty/AlertManager** (for critical issues).

Example **Slack alert** in Python:
```python
import requests

SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/..."
def send_slack_alert(text):
    payload = {"text": text}
    requests.post(SLACK_WEBHOOK_URL, json=payload)

# Example usage
send_slack_alert("⚠️ Suspicious auth denials detected for user: alice@example.com")
```

---

## Implementation Guide

### Step 1: Instrument Your Auth Layer
- Log all 403/401 responses with metadata (see examples above).
- Ensure logs include:
  - Requester identity (user, API key, etc.).
  - Resource being accessed.
  - Time of attempt.
  - User agent/IP (for correlation).

### Step 2: Store Denials in a Dedicated Table
- Use a schema like the one above to preserve queryability.
- Avoid logging sensitive data (e.g., passwords) in plaintext.

### Step 3: Set Up Monitoring
- **Time-series database**: Store denials and query for spikes (e.g., Prometheus).
- **Custom scripts**: Use `pandas` or `sqlalchemy` to analyze patterns (see earlier example).
- **Existing tools**: Integrate with Datadog, New Relic, or Elasticsearch.

### Step 4: Define Alerting Rules
Start with simple rules:
1. **Bursty attempts**: >100 denials in 1 minute for a single requester.
2. **Pattern violations**: A requester repeatedly Denied for resources they shouldn’t access (e.g., an API key with read-only permissions Denied for a write endpoint).
3. **Geolocation anomalies**: Denials from unexpected locations/IP ranges.

### Step 5: Test and Refine
- Simulate attacks to ensure alerts fire.
- Adjust thresholds based on your traffic patterns.

---

## Common Mistakes to Avoid

1. **Logging Too Much or Too Little**
   - *Mistake*: Logging every 403 without context (e.g., missing `requester_id` or `resource_id`).
   - *Fix*: Only log denials where the requester *should* have been denied (e.g., RBAC violations). Include metadata like expected permissions.

2. **Alert Fatigue**
   - *Mistake*: Alerting on every single denial (e.g., >5 denials/minute for a read-only user).
   - *Fix*: Focus on anomalies (e.g., sudden spikes) or repeated patterns (e.g., same user Denied for 10 different resources).

3. **Ignoring False Positives**
   - *Mistake*: Alerting on legitimate but unusual activity (e.g., a bot crawling your API).
   - *Fix*: Use machine learning (e.g., `scikit-learn`) or rule-based filtering to reduce noise.

4. **No Investigation Path**
   - *Mistake*: Alerting without clear next steps for operators.
   - *Fix*: Include context in alerts (e.g., "User `alice@example.com` Denied for `/api/admin/*` 50 times in 5 minutes").

5. **Over-Reliance on Logging**
   - *Mistake*: Assuming logs alone will catch everything (e.g., missing Denials in distributed systems).
   - *Fix*: Use centralized logging (e.g., ELK Stack) and correlation IDs to track requests across services.

---

## Key Takeaways

- **Alerting on Auth Denials** catches attacks that bypass your auth layer.
- **Log all 403/401 responses** with metadata (requester, resource, time).
- **Monitor for anomalies** (spikes, patterns, geolocation shifts).
- **Start simple**: Use PromQL or `pandas` before investing in complex tools.
- **Balance sensitivity and noise**: Focus on high-value resources and suspicious patterns.
- **Investigate alerts**: False positives are expected; refine rules over time.

---

## Conclusion

Security is an ongoing battle, and **Alerting on Auth Denials** is a low-effort, high-impact way to stay ahead of attackers. By logging and monitoring auth failures, you can:
1. Detect credential theft early.
2. Catch misconfigured permissions.
3. Alert on automated scanning (e.g., `nmap`, `dirb`).

Start small—log 403s, set up basic monitoring, and refine as you go. The goal isn’t perfection but **being aware of what’s happening** so you can react before an attacker exploits a gap.

As you implement this pattern, experiment with:
- **Machine learning**: Use clustering to detect unusual access patterns.
- **SIEM integration**: Correlate auth denials with other security events (e.g., failed logins).
- **Automated response**: Block suspicious IPs or revoke keys based on alerts.

Security isn’t just about building firewalls—it’s about **seeing what’s happening** and acting before damage is done. Happy monitoring!

---
### Further Reading
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [Prometheus Alerting Documentation](https://prometheus.io/docs/alerting/latest/)
- ["Designing Secure Systems" (Book)](https://www.oreilly.com/library/view/designing-secure-systems/9781492033697/)
```