# **[Pattern] Authentication Profiling Reference Guide**

---

## **Overview**
**Authentication Profiling** is a security pattern that enhances traditional authentication mechanisms by dynamically assessing user behavior, risk profiles, and contextual factors to adapt access control in real time. It combines **static credentials** (e.g., usernames/passwords, MFA) with **dynamic risk signals** (e.g., device health, location, login velocity, or anomaly detection) to determine trust levels. This pattern mitigates credential stuffing, phishing, and insider threats by continuously evaluating the legitimacy of authentication requests.

Use cases include:
- Zero Trust architectures requiring adaptive access.
- High-risk applications (e.g., financial services, healthcare).
- Enterprise environments with diverse user bases (employees, contractors, IoT devices).
- Compliance needs (e.g., GDPR, PCI DSS) enforcing dynamic access controls.

---

## **Key Concepts**
| **Term**               | **Definition**                                                                                     | **Example**                                                                                     |
|------------------------|---------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| **Static Credentials** | Fixed identifiers (e.g., passwords, SSO tokens) used for initial authentication.                | `Employee ID: "jdoe123" + Password: "SecurePass!"`                                             |
| **Dynamic Signals**    | Real-time metrics collected during/after login to assess risk.                                    | - Device fingerprint (OS, browser, IP geolocation).                                           |
|                        |                                                                                                   | - Login frequency (e.g., 10 failed attempts in 5 minutes).                                       |
|                        |                                                                                                   | - Behavioral biometrics (typing speed, mouse movements).                                       |
| **Trust Score**        | Numerical risk assessment (0–100) derived from dynamic signals; triggers access policies.          | Score < 50 → MFA enforced; Score < 30 → Temporarily block access.                                |
| **Adaptive Policies**  | Rules that map trust scores to access actions (e.g., grant/deny, request MFA, or isolate).       | `IF (trust_score < 40) THEN require step-up authentication; ELSE grant access.`              |
| **Anomaly Detection**  | Algorithms (e.g., ML) identifying unusual patterns (e.g., login from a new country).             | Flags `jdoe123` logging in from Dubai (usual: NYC) as suspicious.                             |
| **Session Context**    | Contextual data tied to an authenticated session (e.g., device, IP, application access).          | Session `S-12345` linked to `Device: Laptop-001 (Trusted)` with access to `HR Portal`.          |
| **Risk Mitigation**    | Actions taken based on profiling (e.g., CAPTCHA, device wipe, or temporary account lock).         | `Risk: High` → Redirect to `Security Challenge` (e.g., "Verify via email").                  |

---

## **Implementation Schema Reference**
Use the following tables to define your profiling system.

### **1. Dynamic Signal Schema**
Collect metrics during authentication to compute a trust score.

| **Field**            | **Type**   | **Description**                                                                                     | **Example Values**                                                                               |
|----------------------|------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| `signal_id`          | String     | Unique identifier for the signal (e.g., `device_os`, `login_velocity`).                              | `device_os`, `geolocation`, `behavioral_biometrics`                                             |
| `value`              | String/Int | Raw metric value (e.g., OS version, login attempts).                                                | `10.5.1`, `5`, `0.75` (typing speed deviation from norm).                                        |
| `score_weight`       | Float      | Relative importance of the signal (0.0–1.0); sums to 1.0 for all signals.                             | `device_os: 0.3`, `geolocation: 0.2`, `behavioral: 0.5`                                        |
| `threshold`          | Float      | Value that triggers a risk level (e.g., `login_attempts_threshold: 3`).                              | `login_attempts_threshold: 3` (3+ attempts → High Risk)                                         |
| `risk_level`         | Enum       | Categorization (Low/Medium/High) based on signal deviation.                                       | `High` (if `value > threshold`).                                                                |

---

### **2. Trust Score Calculation**
Aggregate signals into a composite score (0–100).

| **Signal Category**   | **Formula**                                                                                     | **Notes**                                                                                          |
|-----------------------|-------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| **Device Trust**      | `(device_health_score * 0.3) + (device_fingerprint_entropy * 0.2)`                               | Higher entropy = More unique hardware/software → Higher score.                                     |
| **Behavioral Norms**  | `100 - (abs(measured_behavior - baseline_behavior) * 0.5)`                                      | Baseline from user’s historical data (e.g., typing speed).                                        |
| **Geolocation**       | `IF (ip_geolocation == known_locations) THEN 10 ELSE (distance_from_last_login / max_distance)*50` | Rewards logins from usual locations; penalizes large deviations.                                   |
| **Network Risk**      | `IF (vpn_used) THEN 5 ELSE (dns_reputation_score * 0.1)`                                         | Lower DNS reputation (e.g., Tor exit nodes) → Lower score.                                        |
| **Time-Based**        | `IF (login_time == usual_window) THEN 10 ELSE (abs(hour_diff) * 2)`                             | Penalizes logins outside typical hours (e.g., 3 AM).                                              |

**Composite Score**:
```
trust_score = Σ(signal_value * score_weight)
```

---

### **3. Adaptive Policy Rules**
Map trust scores to access actions.

| **Rule ID**   | **Condition**                          | **Action**                                                                                     | **Example**                                                                                     |
|---------------|----------------------------------------|------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| `policy_001`  | `trust_score >= 70`                    | Grant full access.                                                                                | Allow `jdoe123` to access `Customer Portal`.                                                  |
| `policy_002`  | `trust_score < 70 AND > 40`           | Require step-up authentication (e.g., TOTP or push notification).                                  | Redirect to "Verify with Authenticator App."                                                 |
| `policy_003`  | `trust_score <= 40`                    | Isolate session (restrict to "Basic Portal" only).                                               | Limit access to `Public Dashboard` (no sensitive data).                                         |
| `policy_004`  | `login_attempts > 3`                   | Temporarily lock account (5-minute cooldown).                                                   | Return: `"Account locked. Try again in 5 minutes or request reset."`                            |
| `policy_005`  | `device_not_trusted`                   | Require device verification (e.g., scan for malware, enforce updates).                           | Force `Windows Update` or `Security Scan` before granting access.                                |

---

## **Query Examples**
Use these queries to interact with profiling data in a database or analytics engine.

---

### **1. Retrieve User Login History for Profiling**
```sql
SELECT
    user_id,
    login_time,
    ip_address,
    device_fingerprint,
    login_attempts,
    trust_score,
    final_outcome  -- e.g., "granted", "blocked", "mfa_required"
FROM login_events
WHERE user_id = 'jdoe123'
  AND login_time > DATE_SUB(NOW(), INTERVAL 1 MONTH)
ORDER BY login_time DESC;
```

**Expected Output**:
| `user_id` | `login_time`       | `ip_address`   | `device_fingerprint` | `login_attempts` | `trust_score` | `final_outcome`     |
|-----------|--------------------|----------------|----------------------|------------------|---------------|----------------------|
| jdoe123   | 2023-10-01 09:00:00 | 192.168.1.1    | `Macintosh-2023`     | 1                | 85            | granted              |
| jdoe123   | 2023-10-02 03:00:00 | 103.12.34.56   | `Android-2023`       | 4                | 30            | mfa_required        |

---

### **2. Calculate Real-Time Trust Score for a New Login**
```python
# Pseudocode for scoring (e.g., in Flask/Django)
def calculate_trust_score(user_id, login_data):
    signals = {
        "device_health": login_data["device_health_score"] * 0.3,
        "behavioral": (100 - abs(login_data["typing_speed_deviation"] * 0.5)),
        "geolocation": (
            10 if login_data["ip_geolocation"] in user_history[user_id]["known_locations"]
            else (login_data["distance_from_last_login"] / 5000) * 50
        ),
    }
    trust_score = sum(signals.values())
    return round(min(trust_score, 100), 2)
```

**Example Input/Output**:
```python
login_data = {
    "device_health_score": 9.5,
    "typing_speed_deviation": 0.2,
    "ip_geolocation": "Dubai",  # Not in user's usual locations (NYC)
    "distance_from_last_login": 10000,  # km
}
trust_score = calculate_trust_score("jdoe123", login_data)
# Output: 58.7 (Low Risk → Require MFA)
```

---

### **3. Flag Anomalous Logins for Review**
```sql
WITH user_baselines AS (
    SELECT
        user_id,
        AVG(login_time) AS avg_login_hour,
        STDDEV(ip_geolocation_distance_km) AS location_stddev
    FROM login_history
    GROUP BY user_id
)
SELECT
    l.*,
    ABS(DATEDIFF(CURDATE(), l.login_time)) AS days_since_last_login,
    l.ip_geolocation_distance_km / ub.location_stddev AS location_deviation
FROM login_history l
JOIN user_baselines ub ON l.user_id = ub.user_id
WHERE
    ABS(l.login_time.hour - ub.avg_login_hour) > 5  -- >5 hours from usual
    OR l.ip_geolocation_distance_km / ub.location_stddev > 3  -- 3x normal deviation
ORDER BY location_deviation DESC;
```

**Expected Output**:
| `user_id` | `login_time`       | `location_deviation` | **Action**                     |
|-----------|--------------------|-----------------------|--------------------------------|
| jdoe123   | 2023-10-03 02:00:00 | 5.2                   | **Review** (anomalous location) |

---

### **4. Enforce Adaptive Policies**
```javascript
// Example Node.js logic for policy enforcement
function enforcePolicy(user_id, trust_score) {
    const policies = [
        { score_threshold: 70, action: "grant_access" },
        { score_threshold: 40, action: "require_mfa" },
        { score_threshold: 0, action: "block_access" },
    ];

    for (const policy of policies) {
        if (trust_score >= policy.score_threshold) {
            return { action: policy.action, details: `Score: ${trust_score}` };
        }
    }
    return { action: "block_access", details: "High risk detected" };
}

// Usage:
const result = enforcePolicy("jdoe123", 35);
// Output:
// {
//   action: "require_mfa",
//   details: "Score: 35"
// }
```

---

## **Integration Patterns**
Combine Authentication Profiling with other patterns for robust security:

| **Pattern**               | **Integration Description**                                                                                     | **Benefits**                                                                                     |
|---------------------------|---------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Multi-Factor Authentication (MFA)** | Use profiling to dynamically select MFA methods (e.g., TOTP for medium risk, push notification for high risk). | Reduces friction for trusted users while enforcing security for high-risk scenarios.          |
| **Zero Trust Network Access (ZTNA)** | Continuously profile devices/applications; grant access only to trusted sessions.                          | Eliminates "trust by default" and enforces least-privilege access.                           |
| **Behavioral Analytics**   | Train ML models on historical profiling data to predict anomalies (e.g., credential theft).                | Proactively detects account takeovers before they succeed.                                   |
| **Identity Proofing**      | Combine profiling with knowledge-based authentication (KBA) for high-risk users (e.g., executives).        | Adds an extra layer for privileged accounts.                                                 |
| **Device Posture Assessment** | Profile device health (e.g., OS updates, antivirus) before granting access.                              | Prevents compromised devices from accessing sensitive systems.                                |
| **Continuous Authentication** | Re-evaluate trust scores during a session (e.g., every 30 minutes).                                     | Maintains adaptive access even if risk changes mid-session.                                    |

---

## **Schema Evolution**
Extend the pattern for advanced use cases:

1. **Dynamic Credential Rotation**:
   - Rotate passwords/TOTP seeds based on trust score (e.g., high-risk users get new credentials weekly).

2. **Session Isolation**:
   - Isolate high-risk sessions in a "sandbox" environment (e.g., restricted browser tabs, read-only access).

3. **Context-Aware Policies**:
   - Adjust policies based on external factors (e.g., `trust_score *= 0.8` during a known phishing campaign).

4. **Federated Profiling**:
   - Share anonymous profiling data across organizations (e.g., healthcare providers) to detect cross-organizational attacks.

5. **Explainable AI (XAI) for Trust Scores**:
   - Provide users with insights into why their trust score was low (e.g., "Your device is running an outdated OS").

---

## **Tools & Libraries**
| **Tool/Library**         | **Purpose**                                                                                     | **Example Use Case**                                                                           |
|--------------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **HashiCorp Vault**      | Dynamic secrets + adaptive MFA policies.                                                         | Rotate API keys based on profiling results.                                                 |
| **Splunk**               | Centralized logging for profiling signals (e.g., device health, geolocation).                  | Correlate logs to flag anomalous login patterns.                                             |
| **Auth0/Okta**           | Commercial identity platforms with built-in risk-based policies.                                | Profile users and enforce adaptive MFA.                                                      |
| **Python `scikit-learn`**| Train ML models for anomaly detection (e.g., clustering user behavior).                       | Detect account takeovers by comparing new behavior to baselines.                             |
| **TensorFlow/PyTorch**   | Deep learning for complex profiling (e.g., predicting typos in passwords).                      | Flag synthetic accounts with unnatural input patterns.                                      |
| **OpenID Connect (OIDC)**| Extend OIDC with custom risk claims in the ID token.                                            | Share `trust_score` in JWTs for downstream services.                                          |
| **Ping Identity**        | Enterprise-grade adaptive authentication.                                                        | Deploy profiling alongside traditional SSO.                                                 |

---

## **Best Practices**
1. **Baseline User Behavior**:
   - Collect 30+ days of historical data per user to establish norms (e.g., usual login times, device usage).

2. **Gradual Rollout**:
   - Start with low-risk users (e.g., contractors) to validate policies before expanding to executives.

3. **Transparency**:
   - Notify users when their trust score triggers an action (e.g., "Your login failed due to an unusual device location").

4. **False Positive Mitigation**:
   - Allow users to appeal decisions (e.g., "This was a legitimate login; adjust my profile").

5. **Regulatory Compliance**:
   - Ensure profiling aligns with GDPR’s "right to explanation" (provide reasons for access denials).

6. **Performance Optimization**:
   - Cache frequent queries (e.g., `user_id → trust_score`) to avoid real-time computations.

7. **Multi-Channel Support**:
   - Profile behavior across channels (e.g., mobile app, web, API) to avoid channel-hopping attacks.

8. **Simulated Attacks**:
   - Test profiling against mock phishing attacks or credential leaks to refine signals.

---

## **Example Walkthrough: High-Risk Login**
**Scenario**:
User `jdoe123` logs in from a new country with a compromised device.

1. **Signals Collected**:
   - `device_health`: 3/10 (malware detected).
   - `geolocation`: 8,000 km from last login (score = 20/100).
   - `login_attempts`: 1 (no brute-force flag).
   - `behavioral`: 85/100 (typing speed matches baseline).

2. **Trust Score Calculation**:
   ```
   (3 * 0.3) + (85 * 0.5) + (20 * 0.2) = 0.9 + 42.5 + 4 = 47.4
   ```
   → **Score: 47** (Medium Risk).

3. **Policy Enforcement**:
   - `policy_002` triggers: **"Require step-up authentication."**
   - User must complete a **CAPTCHA** or **push notification** from their authenticator app.

4. **Outcome**:
   - User passes CAPTCHA → Access granted with **1-hour session timeout**.
   - Device is **quarantined** until updated (via `policy_005`).

---

## **Troubleshooting**
| **Issue**                          | **Root Cause**                          | **Solution**                                                                                     |
|-------------------------------------|----------------------------------------|-------------------------------------------------------------------------------------------------|
| **False Positives (Blocked Legit Users)** | Overly strict thresholds or poor baselines. | Adjust `score_weight` or retrain behavioral models