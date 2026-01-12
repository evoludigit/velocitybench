# **[Pattern] Authentication Troubleshooting Reference Guide**

---

## **Overview**
This guide provides a structured approach to diagnosing and resolving common authentication failures across cloud, distributed, and microservices-based systems. Authentication failures disrupt user access, service integration, and security posture. This pattern consolidates troubleshooting steps into logical categories—*client-side*, *server-side*, and *network/security*—with clear diagnostic flows, logging best practices, and remediation actions.

Key objectives:
- **Isolate** the source of authentication failure (client, server, or intermediary).
- **Validate** credentials, tokens, and session states.
- **Check** infrastructure (IDPs, databases, firewalls) and runtime dependencies.
- **Mitigate** failures without disrupting availability.

---

## **Key Concepts & Terminology**
| Term                     | Definition                                                                 |
|--------------------------|-----------------------------------------------------------------------------|
| **IDP (Identity Provider)** | Centralized service (e.g., Okta, Active Directory, Auth0) managing credentials. |
| **OAuth Token**          | Short-lived/long-lived credentials issued by IDP for API access.            |
| **JWT (JSON Web Token)** | Stateless token format containing claims (user identity, roles).            |
| **4xx Errors**           | Client-side failures (e.g., `401 Unauthorized`, `403 Forbidden`).         |
| **5xx Errors**           | Server-side failures (e.g., `500 Internal Server Error`, `503 Service Unavailable`). |
| **Session Cookie**       | HTTP-only cookie storing session identifier for stateless servers.          |

---

## **Schema Reference**
Below are key authentication components and their validation schemas. Use these to parse logs or API responses for troubleshooting.

### **1. Authentication Request Schema**
| Field               | Type      | Description                                                                 |
|---------------------|-----------|-----------------------------------------------------------------------------|
| `auth_method`       | String    | `basic`, `oauth`, `jwt`, `saml`, `cookie`, `api_key`                       |
| `client_id`         | String    | Unique identifier for the authenticated client/application.                 |
| `timestamp`         | ISO8601   | Request timestamp (used for replay attack checks).                          |
| `nonce`             | String    | Unique token for replay attack prevention (OAuth JWT).                     |
| `ip_address`        | IP        | Source IP for rate-limiting/logging.                                         |
| `user_agent`        | String    | Client device/OS info for debugging.                                         |

### **2. Error Response Schema**
| Field          | Type      | Example Value       | Description                                                                 |
|----------------|-----------|---------------------|-----------------------------------------------------------------------------|
| `error_code`   | String    | `INVALID_CREDENTIALS` | Standardized error identifier (align with IDP/API docs).                   |
| `error_msg`    | String    | "Email not verified" | Human-readable description (may be sanitized for logs).                      |
| `timestamp`    | ISO8601   | `2023-10-15T12:00:00Z` | When the error occurred.                                                     |
| `retry_after`  | Integer   | `30`                | Seconds to wait before retrying (rate-limiting).                           |
| `suggested_remediation` | String | "Reset password"   | Actionable guidance for the user.                                           |

---
## **Troubleshooting Flowchart**
Use this decision tree to diagnose failures systematically:

1. **Is the failure client-side or server-side?**
   - *Client-side*: Error occurs in the browser/app (e.g., `401` after login).
   - *Server-side*: API returns `5xx` or logs indicate backend failure.

2. **Client-Side Failures**
   | Symptom                          | Likely Cause                          | Check                                                                     |
   |----------------------------------|---------------------------------------|---------------------------------------------------------------------------|
   | `401 Unauthorized`               | Invalid token/credentials              | Verify:
     - Token expiry (`exp` claim in JWT).
     - Credentials stored securely (not hardcoded).
     - CORS policies blocking requests.                                      |
   | Login page fails to submit       | Form validation errors                | Test with Postman/cURL.                                                   |
   | Silent failures (no error)       | Token handling bug                    | Enable browser DevTools → Network tab to inspect failed requests.          |

3. **Server-Side Failures**
   | Symptom                          | Likely Cause                          | Check                                                                     |
   |----------------------------------|---------------------------------------|---------------------------------------------------------------------------|
   | `500` after token validation     | IDP service unavailable               | Check IDP health endpoint (e.g., `/health`).                              |
   | Token revocation failures        | Database lockouts                      | Audit session table for stale entries.                                   |
   | Rate-limiting `429`              | Throttling misconfiguration           | Review `X-RateLimit-*` headers in responses.                              |

4. **Network/Security Failures**
   | Symptom                          | Likely Cause                          | Check                                                                     |
   |----------------------------------|---------------------------------------|---------------------------------------------------------------------------|
   | Delays in token issuance         | Firewall blocking IDP ports           | Test connectivity to IDP with `telnet <idp-port>`.                         |
   | MFA bypass attempts              | Brute-force attacks                   | Enable IDP logging for failed MFA attempts.                              |

---

## **Query Examples**
### **1. Validate a JWT Token**
Use OpenSSL or online tools to decode and verify a JWT:
```bash
# Decode JWT (no verification)
openssl base64 -d -A -in token.fragments | jq
```
**Flags to check**:
- `alg`: Ensure it’s `HS256`, `RS256`, etc. (match your setup).
- `exp`: Must be > current timestamp.
- `iss`: Should match your IDP’s issuer URL.

### **2. Debug OAuth Token Flow**
Check token issuance with `curl`:
```bash
curl -X POST \
  "https://idp.example.com/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code&code=AUTH_CODE&redirect_uri=CALLBACK_URI&client_id=CLIENT_ID&client_secret=SECRET"
```
**Expected Response**:
```json
{
  "access_token": "JWT_TOKEN",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "REFRESH_TOKEN"
}
```
**Troubleshooting**:
- If `access_token` is missing, validate `CLIENT_ID`/`SECRET` in IDP dashboard.
- Check `redirect_uri` matches the registered callback URL.

### **3. Audit Failed Logins**
Query your IDP or application logs for failed attempts:
```sql
-- Example for PostgreSQL (IDP audit table)
SELECT
    user_id,
    ip_address,
    timestamp,
    auth_method,
    COUNT(*) as failure_count
FROM auth_attempts
WHERE status = 'FAILED'
  AND timestamp > NOW() - INTERVAL '1 hour'
GROUP BY user_id, ip_address, auth_method
ORDER BY failure_count DESC;
```
**Expected Output**:
```
| user_id | ip_address      | timestamp               | auth_method | failure_count |
|---------|-----------------|-------------------------|-------------|---------------|
| user123 | 192.168.1.100   | 2023-10-15 14:30:00 UTC | password    | 5             |
```

### **4. Check Session Cookies**
Inspect cookie headers in HTTP responses:
```bash
# Capture cookies with curl
curl -v -b "session_id=COOKIE_VALUE" https://api.example.com/profile
```
**Flags to check**:
- `HttpOnly`, `Secure`, `SameSite` attributes.
- Cookie domain matches your application’s domain.

---

## **Logging & Monitoring Best Practices**
| Component          | Log Format Example                          | Monitoring Tool          |
|--------------------|--------------------------------------------|--------------------------|
| **IDP**            | `{ "event": "login_attempt", "status": "failed", "user_id": "123", "ip": "1.2.3.4" }` | Prometheus + Grafana     |
| **API Gateway**    | `{ "timestamp": "2023-10-15T12:00:00Z", "error": "invalid_token", "client_id": "app123" }` | Datadog/ELK Stack        |
| **Database**       | `INSERT INTO audit_log (action, user_id, result) VALUES ('token_revoke', '456', 'success')` | AWS CloudWatch           |

**Key Metrics to Track**:
- Failed login rates per IP.
- Token expiration trends.
- Latency in token issuance/validation.

---

## **Common Fixes**
| Issue                          | Immediate Fix                          | Long-Term Solution                   |
|--------------------------------|----------------------------------------|--------------------------------------|
| **Token expired**              | Refresh token via `/token` endpoint.    | Extend token TTL or implement short-lived refresh tokens. |
| **CORS errors**                | Update `Access-Control-Allow-Origin`.   | Configure CORS whitelist in API gateway. |
| **IDP unreachable**            | Check VPN/firewall rules.               | Set up health checks and auto-scaling. |
| **Brute-force attacks**        | Enable failed-login locks.             | Implement rate-limiting (e.g., Redis). |

---

## **Related Patterns**
1. **[Idempotency Pattern]**
   - Ensures retryable operations (e.g., token refresh) don’t duplicate state.
   - *Use Case*: Handle transient IDP failures during high load.

2. **[Circuit Breaker Pattern]**
   - Temporarily stops requests to a failed IDP to prevent cascading failures.
   - *Use Case*: Mitigate IDP outages during peak traffic.

3. **[Distributed Tracing]**
   - Correlate authentication failures across microservices.
   - *Tools*: Jaeger, OpenTelemetry.

4. **[Zero Trust Architecture]**
   - Continuous authentication (e.g., MFA, device posture checks).
   - *Use Case*: Beyond basic username/password validation.

5. **[Token Rotation]**
   - Automatically refresh tokens before expiry.
   - *Implementation*: Use a cron job or event-driven approach (e.g., Kafka).

---
## **Further Reading**
- **[OAuth 2.0 RFC 6749](https://tools.ietf.org/html/rfc6749)**
- **[JWT Best Practices](https://auth0.com/blog/critical-jwt-security-considerations/)**
- **[AWS Sign-In with Amazon Cognito](https://docs.aws.amazon.com/cognito/latest/developerguide/)**