# **[Pattern] Authentication Monitoring Reference Guide**

---
## **Overview**
Authentication Monitoring is a security pattern designed to detect, analyze, and respond to suspicious or anomalous login activities in real time. It supplements traditional authentication mechanisms by enforcing additional layers of validation (e.g., behavioral biometrics, device fingerprinting, or geolocation checks) and triggering alerts for anomalies like brute-force attacks, credential stuffing, or unauthorized access attempts. This guide provides technical details for implementing Authentication Monitoring, including key components, flow diagrams, API schemas, and integration examples.

---

## **Key Concepts**
Authentication Monitoring operates across three primary phases:
1. **Pre-Authentication** – Profile device/user behavior before login.
2. **Auth-Time Validation** – Compare real-time attributes against stored baselines.
3. **Post-Authentication** – Continuously monitor for deviations (e.g., session hijacking).

### **Core Components**
| **Component**               | **Description**                                                                                     |
|-----------------------------|-----------------------------------------------------------------------------------------------------|
| **Baseline Engine**         | Captures normal user behavior (e.g., typing speed, device traits, IP history) via passive monitoring. |
| **Anomaly Detector**        | Uses ML/rule-based engines to flag deviations (e.g., login from a new country).                     |
| **Threat Intelligence Feed**| Cross-references IPs, user agents, or emails against known malicious sources.                      |
| **Risk Scoring Engine**     | Assigns a risk score (e.g., 1–10) to authentication attempts based on multiple factors.              |
| **Remediation Module**      | Enforces actions like MFA prompts, IP blocks, or CAPTCHAs based on risk scores.                 |

---

## **Schema Reference**
### **1. Baseline Profile Schema**
```json
{
  "user_id": "string (UUID)",
  "baseline_properties": {
    "typing_speed": { "avg": "float", "std_dev": "float" },
    "device_fingerprint": { "sha256": "string", "version": "string" },
    "ip_history": [ { "ip": "string", "geolocation": { "country": "string" }, "last_seen": "timestamp" } ],
    "user_agent_history": [ { "agent": "string", "first_seen": "timestamp" } ],
    "login_frequency": { "avg_days_between": "float" }
  },
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

### **2. Auth-Time Validation Schema**
```json
{
  "user_id": "string (UUID)",
  "session_id": "string (UUID)",
  "request_time": "timestamp",
  "attributes": {
    "ip": "string",
    "ip_geolocation": { "country": "string" },
    "user_agent": "string",
    "device_fingerprint": "string",
    "keyboard_dynamics": { "digits_per_second": "float" }
  },
  "risk_score": { "value": "integer (1-100)", "threshold": "integer (e.g., 80)" },
  "anomalies": [
    {
      "type": "string (e.g., 'unusual_ip', 'slow_typing')",
      "severity": "string (e.g., 'low', 'critical')",
      "details": "string"
    }
  ],
  "recommendation": "string (e.g., 'prompt_mfa', 'block')"
}
```

### **3. Alert Schema**
```json
{
  "alert_id": "string (UUID)",
  "type": "string (e.g., 'brute_force', 'credential_stuffing')",
  "user_id": "string (UUID)",
  "session_id": "string (UUID)",
  "timestamp": "timestamp",
  "risk_score": "integer",
  "context": {
    "ip": "string",
    "user_agent": "string",
    "behavioral_deviations": [ "string" ]
  },
  "severity": "string (e.g., 'medium', 'high')",
  "status": "string (e.g., 'active', 'resolved')"
}
```

---

## **Query Examples**
### **1. Fetch User Baseline Profile**
**GraphQL Query:**
```graphql
query GetUserBaseline($userId: ID!) {
  userBaselineProfile(id: $userId) {
    user_id
    baseline_properties {
      ip_history {
        ip
        geolocation { country }
      }
      typing_speed { avg }
    }
  }
}
```

**REST Endpoint:**
```
GET /api/v1/baselines/{user_id}
Headers: Authorization: Bearer {API_KEY}
Response:
{
  "data": {
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "baseline_properties": {
      "typing_speed": { "avg": 12.5 }
    }
  }
}
```

### **2. Validate Auth-Time Request**
**REST Endpoint (POST):**
```
POST /api/v1/auth/validate
Body:
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "attributes": {
    "ip": "192.168.1.1",
    "user_agent": "Mozilla/5.0 (Linux; Android...",
    "keyboard_dynamics": { "digits_per_second": 5.0 }
  }
}
Headers: Authorization: Bearer {API_KEY}
Response:
{
  "risk_score": 85,
  "anomalies": [ { "type": "slow_typing", "severity": "high" } ],
  "recommendation": "prompt_mfa"
}
```

### **3. Trigger Alert for Suspicious Activity**
**Webhook Payload (Sent to SIEM):**
```json
{
  "alert": {
    "alert_id": "a1b2c3d4-5678-90ef-ghij-klmnopqrstuv",
    "type": "credential_stuffing",
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "context": {
      "ip": "203.0.113.45",
      "user_agent": "Python-Requests"
    },
    "severity": "critical"
  }
}
```

### **4. Retrieve Open Alerts**
**GraphQL Query:**
```graphql
query ActiveAlerts($userId: ID) {
  alerts(filter: { status: "active", user_id: $userId }) {
    alert_id
    type
    severity
    context { ip }
    resolved_at
  }
}
```

---

## **Implementation Steps**
### **1. Baseline Creation**
- **Passive Monitoring**: Collect user behavior data during normal logins (e.g., typing patterns, device traits).
- **Storage**: Store baselines in a time-series database (e.g., InfluxDB) or document store (e.g., MongoDB).
- **Update Policy**: Recalculate baselines weekly or after significant behavior changes.

### **2. Auth-Time Validation**
- **Request Interception**: Inject validation logic into the authentication flow (e.g., middleware in your backend).
- **Risk Scoring**: Use a combination of:
  - **Rule-Based**: Check for blacklisted IPs/devices.
  - **ML-Based**: Compare real-time attributes against baseline (e.g., cosine similarity for typing speed).
- **Thresholds**: Define risk thresholds (e.g., score ≥ 85 → require MFA).

### **3. Alerting & Remediation**
- **Webhooks**: Forward alerts to SIEM (e.g., Splunk, Datadog) or ticketing systems (e.g., Jira).
- **Dynamic Responses**:
  - Low Risk: Log event + notify user via email/SMS.
  - High Risk: Block session or require MFA challenge.
- **Feedback Loop**: Allow users to dispute false positives (update baselines accordingly).

### **4. Integration Examples**
| **Technology**       | **Integration Guide**                                                                 |
|----------------------|---------------------------------------------------------------------------------------|
| **Auth Servers**     | Add middleware (e.g., Express.js, FastAPI) to validate requests before token issuance. |
| **Identity Providers** | Use OAuth2/OIDC extensions (e.g., OpenID Connect Risk Score Extension).              |
| **SIEM Tools**      | Export alerts via HTTP webhooks or syslog (e.g., ELK Stack).                          |
| **CDNs**            | Deploy edge-based validation (e.g., Cloudflare Workers) for low-latency checks.      |

---

## **Query Optimization**
- **Caching**: Cache baseline profiles in Redis with 1-hour TTL.
- **Batch Processing**: Use bulk queries to fetch historical data (e.g., `POST /api/v1/baselines/batch`).
- **Indexing**: Ensure indexes on `user_id`, `ip`, and `timestamp` fields in the database.

---
## **Error Handling**
| **Scenario**               | **Error Code** | **Response Example**                                                                 |
|----------------------------|----------------|-------------------------------------------------------------------------------------|
| Invalid Baseline ID        | 404            | `{ "error": "Baseline not found" }`                                                   |
| Risk Score Calculation Fail| 500            | `{ "error": "Model failure; retry in 5 minutes" }`                                    |
| Webhook Delivery Failed    | 503            | Log to dead-letter queue (e.g., Kafka DLQ) for reprocessing.                        |

---

## **Related Patterns**
1. **Multi-Factor Authentication (MFA)**
   - *Why?* Authentication Monitoring can trigger MFA challenges dynamically based on risk scores.
   - *Integration*: Use MFA as the remediation action for high-risk alerts.

2. **Behavioral Biometrics**
   - *Why?* Typing dynamics and mouse movements can supplement device fingerprinting for baselines.
   - *Integration*: Feed behavioral signals into the Baseline Engine.

3. **Zero Trust Architecture (ZTA)**
   - *Why?* Authentication Monitoring aligns with ZTA’s principle of "never trust, always verify."
   - *Integration*: Use risk scores to dynamically adjust access policies (e.g., conditional VPN access).

4. **Credential Stuffing Protection**
   - *Why?* Authentication Monitoring detects reused credentials by cross-referencing leaked datasets.
   - *Integration*: Block logins using Have I Been Pwned’s API for exposed emails.

5. **Session Hijacking Detection**
   - *Why?* Monitor for sudden IP changes or unusual device switches during active sessions.
   - *Integration*: Terminate sessions with `POST /api/v1/sessions/{id}/terminate`.

---
## **Tools & Libraries**
| **Purpose**               | **Tools/Libraries**                                                                 |
|---------------------------|------------------------------------------------------------------------------------|
| Baseline Collection       | [FingerprintJS](https://github.com/fingerprintjs/fingerprintjs), [Keyboard Dynamics SDK](https://github.com/keyboard-dynamics) |
| Anomaly Detection         | [Elasticsearch Anomaly Detection](https://www.elastic.co/guide/en/stack/_index.html), [TensorFlow.js](https://www.tensorflow.org/js) |
| Risk Scoring              | [Alto’s Risk API](https://www.alto.io/), Custom ML models (PyTorch, scikit-learn)   |
| Alerting                  | [Pushover](https://pushover.net/), [Slack API](https://api.slack.com/messaging/composing) |
| SIEM Integration          | [Splunk Add-on for Firebase](https://splunkbase.splunk.com/app/2105/), [Datadog HTTP Endpoint](https://docs.datadoghq.com/api/v1/) |

---
## **Best Practices**
1. **Gradient Risk Responses**:
   - Low Risk: Send a non-intrusive notification (e.g., "Your login looks unusual. Approve this session?").
   - High Risk: Block the session and notify the user with a remediation step (e.g., "Security alert: Suspicious activity detected. Verify your identity to continue.").

2. **User Privacy**:
   - Anonymize baseline data (e.g., store only statistical summaries like `avg_typing_speed`, not raw keystrokes).
   - Comply with GDPR/CCPA by allowing users to request baseline deletions.

3. **False Positive Mitigation**:
   - Implement a dispute mechanism (e.g., "This was me—update my baseline").
   - Use ensemble models (e.g., combine rule-based + ML-based detectors).

4. **Performance**:
   - Cache baseline comparisons to avoid recalculating risk scores for identical requests.
   - Use asynchronous processing for heavy ML inference (e.g., AWS Lambda).

5. **Testing**:
   - Simulate attacks (e.g., brute-force, credential stuffing) in staging to validate alerting.
   - Measure false positive/negative rates quarterly.

---
## **Troubleshooting**
| **Issue**                          | **Diagnostic Steps**                                                                 | **Solution**                                                                 |
|-------------------------------------|--------------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| High false positive rate           | Check baseline recalculation frequency.                                             | Increase baseline update frequency or adjust ML thresholds.                   |
| Slow auth-time validation          | Profiling shows bottleneck in ML inference.                                         | Use pre-built risk models (e.g., Alto) or cache results.                     |
| Alerts not triggering              | Verify webhook endpoint is reachable.                                               | Test webhook with `curl`; check SIEM logs for delivery failures.              |
| Baseline drift post-device change   | User upgraded to a new phone/tablet.                                                 | Implement adaptive baselines (e.g., allow partial overlap with old device).    |

---
## **Example Workflow**
1. **User Attempts Login**:
   - Client sends `POST /login` with credentials + device attributes.
   - Backend validates credentials → proceeds to **Auth-Time Validation**.

2. **Validation Phase**:
   - Fetch baseline for `user_id = 123e4567...`.
   - Compare `typing_speed` (real-time: 4.0 vs. baseline avg: 12.5) → **risk_score = 92**.
   - Detect `unusual_ip` (new country) → add to anomalies.

3. **Remediation**:
   - Risk score ≥ 85 → trigger MFA challenge.
   - User approves via TOTP → session created with elevated monitoring.

4. **Post-Login**:
   - Continuously monitor session for anomalies (e.g., IP switch).
   - If detected (e.g., `new_device_fingerprint`), terminate session and notify user.

---
## **Further Reading**
- [OWASP Authentication Monitoring Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Monitoring_Cheat_Sheet.html)
- [NIST SP 800-63B: Digital Identity Guidelines](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-63B.pdf)
- [Cloudflare Bot Management](https://developers.cloudflare.com/bot-management/) (for edge-based validation)