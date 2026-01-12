```markdown
---
title: "Authentication Profiling: When Tokens Aren't Enough"
date: 2023-11-15
author: "Jane Doe"
tags: ["backend", "authentication", "API design", "security", "patterns"]
description: "Learn about authentication profiling—a pattern to balance security with granular access control beyond JWTs alone. Practical examples and tradeoffs included."
---

# Authentication Profiling: When Tokens Aren't Enough

![Authentication Profiling Diagram](https://via.placeholder.com/800x400/28a745/ffffff?text=Authentication+Profiling+Flow)

Authentication is the foundation of every secure system—but modern applications often go beyond simple "login or deny" logic. **Authentication profiling** is a pattern where you categorize users into **behavioral profiles** based on their authentication behavior, access patterns, and contextual signals, rather than just relying on a single token. This approach enables more granular and adaptive access control while maintaining security.

While JWTs and OAuth are great for stateless authentication, they don’t inherently account for:
- When a user logs in from a new device (should this be allowed?).
- How often a user attempts to log in (is this bot traffic?).
- Whether a user’s access patterns suddenly change (e.g., querying unusual endpoints).

This tutorial will explore how to implement authentication profiling, balancing security with usability—without overcomplicating things.

---

## The Problem: Why Tokens Alone Fall Short

Imagine a SaaS application tracking user logins across devices. Today’s system relies solely on JWTs, but it faces these challenges:

1. **False Positives in Bot Traffics**
   - A malicious actor could brute-force an account, generating a valid JWT before detection.
   - *Example*: A phishing attack steals credentials, and the attacker logs in from a new location—but the system only checks if the JWT is valid, not the access pattern.

2. **Contextual Blindspots**
   - A legitimate user might temporarily lose access to their usual device but get locked out if the system *only* checks for device fingerprint matches.
   - *Example*: A user’s laptop is stolen, but the attacker (unaware of the victim) tries logging in from a coffee shop—what should the system do?

3. **Dynamic Access Needs**
   - A user’s role might change (e.g., an intern becomes a manager), but their JWTs don’t reflect this until the next refresh.
   - *Example*: A system assigns a temporary admin role during a critical bug fix, but the user’s token doesn’t update immediately.

4. **Regulatory Compliance Gaps**
   - Some industries (e.g., healthcare) require **multi-tiered authentication** (e.g., MFA + risk scoring) for sensitive actions.
   - *Example*: A doctor must first verify their identity via biometrics before accessing a patient’s EHR.

### Real-World Consequences
- **Data Breaches**: A stolen JWT can grant prolonged access if no additional checks exist.
- **Reputational Damage**: False lockouts hurt user experience, eroding trust.
- **Legal Risks**: Failing to detect anomalous activity may violate compliance requirements.

---

## The Solution: Authentication Profiling

Authentication profiling involves **categorizing users into dynamic groups** based on their behavior, context, and risk factors. The goal is to:
- **Detect anomalies** early (e.g., a sudden login from China).
- **Adapt access dynamically** (e.g., require MFA for high-risk actions).
- **Maintain usability** by only enforcing strict checks when necessary.

The pattern combines **authentication**, **authorization**, and **risk scoring** into a single flow. Here’s how it works:

### Core Components
1. **Profile Attributes**
   - Static: Role, permissions, device fingerprint.
   - Dynamic: Login frequency, response times, failed attempts.
   - Contextual: Geographic location, time of day.

2. **Risk Scoring Engine**
   - Assigns a risk score (e.g., 0–100) based on profile attributes.
   - Example: A user logging in at 3 AM from a new country might trigger a score of 85.

3. **Access Policies**
   - Rules like:
     - *"Require MFA if risk score > 70."*
     - *"Block if > 3 failed attempts in 1 hour."*
   - Policies can be static (e.g., always require MFA for admins) or dynamic (e.g., adjust thresholds based on user history).

4. **Feedback Loop**
   - Logs and updates profile attributes after each interaction to improve future decisions.

---

## Code Examples: Implementing Profiling in Practice

Let’s build a simple profiling system using **Node.js**, **PostgreSQL**, and **Redis** for caching. We’ll focus on:
- Tracking login behavior.
- Scoring risk dynamically.
- Enforcing policies.

---

### 1. Database Schema for Profiling

```sql
-- Users table (existing)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user'
);

-- Login attempts table (for profiling)
CREATE TABLE login_attempts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    device_fingerprint VARCHAR(255), -- e.g., browser/OS/IP
    location_country VARCHAR(100),
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    is_successful BOOLEAN DEFAULT FALSE
);

-- User profiles (dynamic attributes)
CREATE TABLE user_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(id),
    risk_score INTEGER DEFAULT 0, -- 0-100
    last_activity TIMESTAMP,
    failed_attempts INTEGER DEFAULT 0,
    login_frequency INTEGER DEFAULT 0 -- logins/hour
);
```

---

### 2. Risk Scoring Logic (Node.js)

We’ll calculate a risk score based on:
- Failed attempts.
- Geographic distance from usual location.
- Time since last login.

```javascript
// risk-scoring.js
const calculateRiskScore = (userProfile, attempt) => {
    let score = 0;

    // 1. Failed attempts penalty
    score += userProfile.failed_attempts * 5;
    if (userProfile.failed_attempts > 3) {
        return 100; // Max penalty for excessive failures
    }

    // 2. Geographic risk (simplified: assume "usual" location is the first login)
    const usualLocation = getUsualLocation(userProfile.user_id); // Hypothetical helper
    if (!usualLocation || attempt.location_country !== usualLocation) {
        score += 20; // Penalty for new location
    }

    // 3. Time since last activity
    const hoursSinceLast = Math.floor((Date.now() - userProfile.last_activity) / (1000 * 60 * 60));
    if (hoursSinceLast > 12) {
        score += 10 * Math.min(hoursSinceLast, 48); // Max 48 hours penalty
    }

    // 4. Login frequency (unusual bursts = higher risk)
    const avgFrequency = userProfile.login_frequency / 10; // Normalize
    if (attempt.timestamp && userProfile.last_activity) {
        const minutesBetween = (attempt.timestamp - userProfile.last_activity) / (1000 * 60);
        if (minutesBetween < 5) {
            score += 15; // Rapid successive logins
        }
    }

    // Cap at 100
    return Math.min(score, 100);
};

const getUsualLocation = async (userId) => {
    // Query: Find the first login's country for this user
    const [row] = await db.query(
        `SELECT location_country FROM login_attempts WHERE user_id = $1 ORDER BY timestamp ASC LIMIT 1`,
        [userId]
    );
    return row?.location_country;
};
```

---

### 3. Policy Enforcement Middleware

We’ll create a middleware that checks the risk score before granting access.

```javascript
// auth.js
const enforceAccessPolicy = async (req, res, next) => {
    const authHeader = req.headers.authorization;
    if (!authHeader) return res.status(401).send("Unauthorized");

    const token = authHeader.split(" ")[1];
    try {
        const decoded = jwt.verify(token, process.env.JWT_SECRET);

        // Fetch user profile (Redis cache first)
        const profile = await getUserProfile(decoded.userId);
        if (!profile) return res.status(403).send("Profile not found");

        // Check risk score
        const riskScore = calculateRiskScore(profile, req.userAttemptData);

        // Apply policies
        if (riskScore > 70) {
            if (req.method === "POST" && req.path.startsWith("/api/sensitive")) {
                return res.status(403).send("MFA required for high-risk action");
            }
        }

        next();
    } catch (err) {
        res.status(401).send("Invalid token");
    }
};

const getUserProfile = async (userId) => {
    // Check Redis cache first
    const cacheKey = `user_profile:${userId}`;
    const cached = await redis.get(cacheKey);
    if (cached) return JSON.parse(cached);

    // Fall back to DB
    const [rows] = await db.query(
        `SELECT * FROM user_profiles WHERE user_id = $1`,
        [userId]
    );
    const profile = rows[0];
    if (profile) {
        redis.setex(cacheKey, 60, JSON.stringify(profile)); // Cache for 1 minute
    }
    return profile;
};
```

---

### 4. Updating Profiles After Login

We’ll update the profile after each login attempt, successful or not.

```javascript
// login-handler.js
const handleLogin = async (req, res) => {
    try {
        const { email, password } = req.body;
        const user = await authenticateUser(email, password);

        // Generate JWT
        const token = jwt.sign({ userId: user.id }, process.env.JWT_SECRET, { expiresIn: '1h' });

        // Record login attempt
        const attempt = {
            user_id: user.id,
            device_fingerprint: req.headers['x-device-fingerprint'],
            location_country: req.ip, // Simplified for example
            is_successful: true,
            timestamp: new Date()
        };
        await db.query(
            `INSERT INTO login_attempts (user_id, device_fingerprint, location_country, is_successful, timestamp)
             VALUES ($1, $2, $3, $4, $5)`,
            [attempt.user_id, attempt.device_fingerprint, attempt.location_country, true, attempt.timestamp]
        );

        // Update profile
        await updateUserProfile(user.id, { last_activity: new Date() });

        res.json({ token });
    } catch (err) {
        // Failed login
        await updateUserProfile(req.body.userId, (prev) => ({
            ...prev,
            failed_attempts: prev.failed_attempts + 1
        }));
        res.status(401).send("Invalid credentials");
    }
};

const updateUserProfile = async (userId, updates) => {
    const [rows] = await db.query(
        `SELECT * FROM user_profiles WHERE user_id = $1 FOR UPDATE`,
        [userId]
    );
    const profile = rows[0] || {
        user_id: userId,
        risk_score: 0,
        failed_attempts: 0,
        login_frequency: 0
    };

    // Apply updates
    const updated = { ...profile, ...updates };

    // Recalculate risk score if needed
    if ('risk_score' in updates || 'failed_attempts' in updates) {
        const lastAttempt = await getLastLoginAttempt(userId);
        updated.risk_score = calculateRiskScore(updated, lastAttempt);
    }

    // Save to DB and cache
    await db.query(
        `INSERT INTO user_profiles (user_id, risk_score, failed_attempts, login_frequency, last_activity)
         VALUES ($1, $2, $3, $4, $5)
         ON CONFLICT (user_id) DO UPDATE SET
         risk_score = $2, failed_attempts = $3, login_frequency = $4, last_activity = $5`,
        [
            userId,
            updated.risk_score,
            updated.failed_attempts,
            updated.login_frequency + 1,
            updated.last_activity
        ]
    );

    // Update cache
    redis.setex(`user_profile:${userId}`, 60, JSON.stringify(updated));
};
```

---

## Implementation Guide

### Step 1: Define Your Profiles
Start with **static profiles** (roles, permissions) and gradually add dynamic attributes:
- **Beginner**: Track login frequency.
- **Intermediate**: Add geolocation checks.
- **Advanced**: Integrate with behavioral analytics tools.

### Step 2: Instrument Your System
- **Track all login attempts** (even failed ones).
- **Log user actions** (e.g., API calls, data access) to detect anomalies.
- **Use a lightweight cache** (Redis) for profile lookup.

### Step 3: Build the Risk Engine
Start simple:
1. **Failed attempts**: Penalize 5 points per attempt (cap at 100).
2. **Geolocation**: Penalize if the login is from a new country.
3. **Time since last login**: Penalize if >12 hours inactive.
4. **Behavioral signals**: Penalize if response times are slow (may indicate a bot).

### Step 4: Design Access Policies
Example rules:
| Risk Score | Policy                                                                 |
|------------|------------------------------------------------------------------------|
| > 90       | Require MFA + phone call verification.                                |
| 70–90      | Require MFA for sensitive actions (e.g., `/api/payouts`).              |
| 40–70      | Log but allow access.                                                 |
| < 40       | No additional checks.                                                |

### Step 5: Test and Iterate
- **Simulate attacks**: Test how your system responds to brute-force attempts.
- **Monitor false positives**: Ensure legitimate users aren’t blocked.
- **Adjust thresholds**: Start conservative (e.g., score > 70 = MFA).

### Step 6: Integrate with Existing Auth
- **JWT + Profiling**: Use JWTs for stateless auth but overlay profiling checks.
- **OAuth Flows**: Extend OAuth to include risk assessment (e.g., require MFA for high-risk users).

---

## Common Mistakes to Avoid

1. **Overcomplicating Early**
   - Start with **one or two signals** (e.g., failed attempts + location) before adding complexity.
   - *Example*: Don’t track every API call initially; focus on logins first.

2. **Ignoring False Positives**
   - A strict policy that blocks 5% of legitimate users will hurt adoption.
   - *Solution*: Begin with low thresholds and adjust based on data.

3. **Storing Too Much Data**
   - Profiling requires **minimal data** to avoid privacy concerns.
   - *Example*: Don’t log keystrokes; stick to device/IP/location.

4. **No Feedback Loop**
   - If profiles aren’t updated, the system becomes stale.
   - *Solution*: Use triggers or background jobs to update profiles.

5. **Assuming One Size Fits All**
   - Different roles (e.g., admins vs. users) may need different policies.
   - *Example*: Require less scrutiny for admins but more for regular users.

6. **Neglecting Compliance**
   - Profiling may inadvertently collect PII (e.g., IP addresses).
   - *Solution*: Anonymize data where possible (e.g., store country, not exact IP).

---

## Key Takeaways

- **Authentication profiling** goes beyond tokens by analyzing behavior and context.
- **Start simple**: Track login failures and geolocation before adding complex signals.
- **Balance security and usability**: Erring too far on either side hurts your system.
- **Iterate based on data**: Monitor false positives/negatives and adjust policies.
- **Combine with existing auth**: Use JWTs/OAuth as the baseline but overlay profiling.
- **Prioritize privacy**: Collect only what’s necessary to assess risk.

---

## Conclusion

Authentication profiling is a **practical middle ground** between overly permissive systems (e.g., JWT-only) and heavyweight solutions (e.g., manual review for every action). By dynamically categorizing users and adapting access based on risk, you can:
- **Reduce false positives** from bot traffic.
- **Enhance security** without hurting usability.
- **Comply with regulations** (e.g., requiring MFA for sensitive actions).

### Next Steps
1. **Experiment**: Add profiling to a non-critical endpoint first.
2. **Measure**: Track false positives/negatives and adjust thresholds.
3. **Scale**: Expand to more signals (e.g., behavioral biometrics) as needed.

As your system grows, profiling will evolve from a nice-to-have to a **necessity**—especially if you’re dealing with sensitive data or high-stakes users. Start small, stay iterative, and prioritize data-driven decisions over guesswork.

---
**Further Reading**
- [OWASP Authentication Profiling Guide](https://owasp.org/www-project-authentication-cheat-sheet/)
- [Behavioral Biometrics for Authentication](https://www.nist.gov/topics/information-security/behavioral-biometrics)
- [PostgreSQL for Analytics](https://www.postgresql.org/docs/current/query.html)

**Code Repository**: [GitHub - auth-profiling-example](https://github.com/your-repo/auth-profiling-example)
```

---
**Notes**:
- The blog post includes **SQL schema**, **Node.js code**, and a **step-by-step guide** with tradeoffs.
- It avoids vague advice, focusing on **practical implementation**.
- Tradeoffs (e.g., performance vs. security) are explicitly called out.
- The tone is **professional but approachable**, with clear examples.