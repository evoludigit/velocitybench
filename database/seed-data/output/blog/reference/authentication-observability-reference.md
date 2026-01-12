# **[Pattern] Authentication Observability Reference Guide**

---

## **Overview**
Authentication Observability (Auth Observability) provides visibility into authentication events, flows, and outcomes to identify anomalies, enforce security policies, and troubleshoot access issues. This pattern ensures real-time monitoring of authentication attempts—successes, failures, delays, and exceptions—across systems, applications, and user identities. By capturing contextual metadata (e.g., user, device, IP, timestamp, factors used), organizations can detect brute-force attacks, misconfigurations, or failed logins before they escalate. Auth Observability complements **Authentication Patterns** (e.g., Multifactor Authentication) and **Authorization Patterns** (e.g., Attribute-Based Access Control) by enabling proactive risk mitigation and compliance auditing.

---

## **Key Concepts**
| **Aspect**               | **Definition**                                                                                                                                                                                                 | **Example**                                                                                     |
|--------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Authentication Event** | A record of an attempt to prove identity (e.g., username/password, biometric, or token). Includes metadata like status (success/fail), used factors, and timestamp.                                      | `{ event: "login", user: "jdoe", status: "failed", method: "otp", timestamp: "2024-05-15T12:00:00Z" }` |
| **Authz Flow**           | A sequence of steps (e.g., MFA challenge → approval → session creation) tied to a user/entity. Helps trace complex flows involving third-party services or conditional logic.                         | `flow: "sso-oauth2", steps: ["validate_token", "claim_mfa_success", "issue_session"]`          |
| **Contextual Metadata**  | Additional data (e.g., user agent, location, device fingerprint) to correlate events across systems (e.g., Cloud SIEM, IAM logs).                                                                                 | `{ ip: "192.0.2.1", user_agent: "MobileApp/1.2.3", geo: "US" }`                                  |
| **Anomaly Detection**    | Alerting on patterns like repeated failures, unusual locations, or timing anomalies (e.g., "User A logs in from Japan at 3 AM").                                                                               | Rule: **"Failures > 5 in 10 mins → Lock account"**                                                  |
| **Telemetry Pipeline**   | Infrastructure (e.g., event buses, databases) to ingest, process, and analyze auth data in real-time or batch.                                                                                               | Kafka → Flink → Elasticsearch → Grafana dashboards                                                  |
| **Session Observability**| Monitoring active sessions (e.g., token expiration, concurrent logins, or unexpected terminations) to catch unauthorized access.                                                                                      | `session: "sess_abc123", status: "active", last_activity: "2024-05-15T14:30:00Z"`             |
| **Third-Party Integration** | Syncing auth logs with external systems (e.g., identity providers like Okta, or SIEM tools like Splunk) for cross-platform visibility.                                                                         | Webhook: `POST /siem/events → {"event": "auth_failed", "user": "jdoe", "source": "azure_ad"}`    |

---

## **Schema Reference**
Below are core schemas for Auth Observability events. Use these to standardize data across tools.

### **1. Basic Authentication Event**
| **Field**          | **Type**       | **Description**                                                                                                                                                                                                 | **Example Values**                          |
|--------------------|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------|
| `event_id`         | String (UUID)  | Unique identifier for the event.                                                                                                                                                                             | `"a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6m7n8"`     |
| `timestamp`        | ISO 8601       | When the event occurred (UTC).                                                                                                                                                                               | `"2024-05-15T12:00:00Z"`                    |
| `user_id`          | String         | Identifier for the authenticated user (PII-encoded if required).                                                                                                                                                     | `"user_12345"`                              |
| `status`           | Enum           | `success`, `failed`, `pending`, `timeout`, or `unknown`.                                                                                                                                                       | `"failed"`                                  |
| `auth_method`      | Enum/Array     | Primary method used (e.g., `"password"`, `"mfa"`, `"fido2"`) or array for multi-factor flows.                                                                                                                 | `["password", "sms_otp"]`                   |
| `source_system`    | String         | System originating the event (e.g., `app-frontend`, `azure_ad`).                                                                                                                                                  | `"sso-oauth2"`                              |
| `ip_address`       | IPv4/IPv6      | Client IP (may be masked for privacy).                                                                                                                                                                         | `"192.0.2.1"`                               |
| `user_agent`       | String         | Browser/device info (sanitized).                                                                                                                                                                                 | `"Mozilla/5.0 (Linux; Android 12)"`          |
| `geo_location`     | Object         | Country, city, or ISP data (if available).                                                                                                                                                                        | `{"country": "US", "city": "Seattle"}`       |
| `custom_attributes`| Object         | Key-value pairs for domain-specific data (e.g., `{"device_fingerprint": "xyz789"}`).                                                                                                                       | `{"risk_score": 0.9, "login_attempts": 3}`   |

---

### **2. Authentication Flow Event**
| **Field**          | **Type**       | **Description**                                                                                                                                                                                                 | **Example Values**                          |
|--------------------|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------|
| `flow_id`          | String (UUID)  | Unique flow identifier to trace multi-step authentications.                                                                                                                                                      | `"flow_xyz789"`                             |
| `steps`            | Array[Object]  | List of steps in the flow with status and metadata.                                                                                                                                                           | `[{"step": "validate_token", "status": "pass"}, {"step": "mfa", "status": "fail"}]` |
| `start_time`       | ISO 8601       | When the flow began.                                                                                                                                                                                             | `"2024-05-15T12:00:00Z"`                    |
| `end_time`         | ISO 8601       | When the flow completed (or failed).                                                                                                                                                                             | `"2024-05-15T12:05:00Z"`                    |
| `duration_ms`      | Integer        | Flow duration in milliseconds (useful for bot detection).                                                                                                                                                       | `30000`                                     |
| `decision`         | String         | Final outcome (e.g., `"allow"`, `"deny"`, `"challenge_mfa"`).                                                                                                                                                      | `"deny"`                                    |
| `policy_id`        | String         | Reference to the policy that evaluated the flow (e.g., `policy_id: "p_risk_based_access"`).                                                                                                                         | `"p_risk_based_access"`                     |

---

### **3. Session Event**
| **Field**          | **Type**       | **Description**                                                                                                                                                                                                 | **Example Values**                          |
|--------------------|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------|
| `session_id`       | String (UUID)  | Unique session token or identifier.                                                                                                                                                                              | `"sess_abc123"`                             |
| `user_id`          | String         | Associated user.                                                                                                                                                                                                     | `"user_12345"`                              |
| `start_time`       | ISO 8601       | When the session began.                                                                                                                                                                                             | `"2024-05-15T12:15:00Z"`                    |
| `end_time`         | ISO 8601       | When the session ended (explicit logout or timeout).                                                                                                                                                            | `"2024-05-15T14:30:00Z"`                    |
| `active`           | Boolean        | Whether the session is currently active.                                                                                                                                                                           | `false`                                     |
| `tokens_used`      | Array[Object]  | Tokens issued during the session (e.g., JWTs, refresh tokens).                                                                                                                                                       | `[{"type": "access", "issued_at": "2024-05-15T12:15:00Z"}]` |
| `locations`        | Array[Object]  | Geolocation history of the session.                                                                                                                                                                               | `[{"ip": "192.0.2.1", "timestamp": "2024-05-15T12:15:00Z"}]`  |

---

## **Implementation Patterns**

### **1. Event Collection**
- **Logs**: Ship auth events to a centralized log aggregator (e.g., ELK Stack, Datadog, Sumo Logic).
  ```bash
  # Example: Forward auth logs to Kafka
  journalctl -u auth-service | kafka-console-producer --broker-list kafka:9092 --topic auth_events
  ```
- **APIs**: Use telemetry SDKs (e.g., OpenTelemetry, AWS CloudWatch Embedded Metric Format) to instrument authentication services.
  ```python
  from opentelemetry import trace
  tracer = trace.get_tracer(__name__)
  with tracer.start_as_current_span("auth_login"):
      # ... authentication logic ...
  ```

### **2. Real-Time Processing**
- **Streaming**: Use Kafka Streams or Flink to detect anomalies (e.g., ">3 failures in 5 mins").
  ```java
  // Pseudo-code: Kafka Streams anomaly detection
  KStream<String, AuthEvent> events = builder.stream("auth_events");
  events.filter((key, event) -> event.status == "failed")
        .groupByKey()
        .aggregate(
            () -> new CountKey(),
            (key, value, agg) -> { agg.count++; return agg; },
            Materialized.<String, CountKey, KeyValueStore<Bytes, byte[]>>as("failures")
        )
        .toStream()
        .filter((key, agg) -> agg.count > 3)
        .to("anomalies");
  ```
- **Alerting**: Integrate with PagerDuty/Opsgenie via webhooks or SIEM tools (e.g., Splunk ES).

### **3. Storage**
- **Time-Series Databases**: Use Prometheus or InfluxDB for metrics (e.g., login rates per user).
  ```sql
  -- PromQL: Query failed logins by user
  rate(auth_fails_total{user="jdoe"}[5m]) > 0
  ```
- **Search**: Elasticsearch for ad-hoc queries (e.g., "Show all failed logins from China in the last 7 days").
  ```json
  GET /auth_events/_search
  {
    "query": {
      "bool": {
        "must": [
          {"term": {"status": "failed"}},
          {"range": {"timestamp": {"gte": "now-7d"}}},
          {"geo_distance": {"geo_ip": {"distance": "10000", "geo_point": {"latitude": 40.7, "longitude": -74.0}}}}}
        ]
      }
    }
  }
  ```

### **4. Post-Processing**
- **Enrichment**: Augment events with threat intelligence (e.g., "Is this IP in a botnet?").
  ```python
  # Pseudo-code: Enrich with AbuseIPDB
  def enrich_event(event):
      ip = event["ip_address"]
      response = requests.get(f"https://api.abuseipdb.com/api/v2/check?ipAddress={ip}&maxAgeInDays=90")
      event["threat_intel"] = response.json()
      return event
  ```
- **Dashboards**: Visualize trends in Grafana (e.g., "Failed logins by hour").
  ```json
  // Grafana Panel: Failed logins
  {
    "title": "Failed Logins (Last 24h)",
    "type": "timeseries",
    "queries": [
      { "refId": "A", "datasource": "prometheus", "query": "rate(auth_fails_total[5m])" }
    ]
  }
  ```

---

## **Query Examples**
### **1. Failed Logins by User (SQL-like)**
**Tool**: PostgreSQL (using TimescaleDB)
```sql
SELECT
    user_id,
    COUNT(*) as failure_count,
    MIN(timestamp) as first_failure,
    MAX(timestamp) as last_failure
FROM auth_events
WHERE status = 'failed'
  AND timestamp > NOW() - INTERVAL '7 days'
GROUP BY user_id
HAVING COUNT(*) > 3
ORDER BY failure_count DESC;
```

### **2. Anomalous Login Locations (Grafana/ELK)**
**Tool**: Elasticsearch Query DSL
```json
GET /auth_events/_search
{
  "size": 0,
  "aggs": {
    "by_geo": {
      "terms": {
        "field": "geo_location.country",
        "size": 10
      },
      "aggs": {
        "failure_rate": {
          "avg": { "script": "doc['status'].value == 'failed' ? 1 : 0" }
        }
      }
    }
  }
}
```

### **3. Session Duration Analysis (PromQL)**
**Tool**: Prometheus
```promql
# Average session duration (in seconds) for the last 30 days
avg(
  rate(session_duration_seconds_sum[30d])
    /
  rate(session_duration_seconds_count[30d])
)
by (user_id)
```

### **4. MFA Flow Completion Rate**
**Tool**: Flink SQL
```sql
-- Calculate % of flows that completed MFA successfully
SELECT
    flow_id,
    COUNT(*) as total_flows,
    SUM(CASE WHEN status = 'success' AND auth_method LIKE '%mfa%' THEN 1 ELSE 0 END) as mfa_successes,
    SUM(CASE WHEN status = 'success' AND auth_method NOT LIKE '%mfa%' THEN 1 ELSE 0 END) as single_factor_successes
FROM auth_flows
WHERE start_time > NOW() - INTERVAL '1 month'
GROUP BY flow_id
ORDER BY mfa_successes DESC;
```

---

## **Related Patterns**
| **Pattern**                     | **Description**                                                                                                                                                                                                 | **Use Case Example**                                                                                     |
|----------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| **[Multi-Factor Authentication](https://example.com/mfa)** | Requires users to provide **two or more verification factors** (e.g., password + SMS code).                                                                                                              | Protecting admin dashboards from credential stuffing.                                                  |
| **[Risk-Based Authentication](https://example.com/risk-based)** | Adjusts auth requirements dynamically based on **context** (e.g., user location, device risk score).                                                                                                       | Triggering MFA for logins from a new country.                                                            |
| **[Identity Federation](https://example.com/federation)** | Delegates authentication to **third-party identity providers** (e.g., SAML, OAuth 2.0).                                                                                                               | Enabling SSO for employees using Azure AD or Google Workspace.                                          |
| **[Token-Based Authentication](https://example.com/tokens)** | Uses **JWTs or refresh tokens** for stateless auth, with observability into token issuance/lifetime.                                                                                                     | Monitoring expired access tokens to detect credential leaks.                                           |
| **[Authorization Patterns](https://example.com/authorization)** | Enforces **access control** (e.g., RBAC, ABAC) after successful auth, with observability into denied requests.                                                                                              | Auditing why a user couldn’t access a resource (e.g., missing permission).                            |
| **[Anonymous Auth](https://example.com/anonymous)**       | Allows temporary access for **guest sessions** with limited permissions, observable via session duration and actions.                                                                                       | Enabling read-only access for non-members on a public wiki.                                           |
| **[Passwordless Auth](https://example.com/passwordless)** | Eliminates passwords using **magic links, push notifications, or biometrics**, with observability into delivery failures.                                                                                     | Reducing support tickets from forgotten passwords.                                                      |

---

## **Anti-Patterns to Avoid**
1. **Logging Only Successes**: Focus on **failed attempts** (80% of threats are detected via failures).
2. **Ignoring Context**: Always correlate metadata (e.g., IP, device) to avoid false positives.
3. **Centralizing All Logs**: Use **federated observability** (e.g., per-service logs + global SIEM).
4. **Over-Observing**: Balance granularity with **privacy compliance** (e.g., GDPR, CCPA).
5. **Alert Fatigue**: Prioritize **signal over noise** (e.g., only alert on high-risk events).

---
**Further Reading**:
- [NIST SP 800-63B](https://pages.nist.gov/800-63-3/sp800-63b.html) (Digital Identity Guidelines)
- [OpenTelemetry AuthZ Documentation](https://opentelemetry.io/docs/specs/otel/semconv/auth/)
- [CIS Benchmarks for IAM](https://www.cisecurity.org/benchmark/iam/)