# **[Pattern] Authentication Debugging – Reference Guide**

---
### **Overview**
Authentication Debugging is a systematic approach to diagnosing and resolving authentication failures in distributed systems. This pattern provides structured methods—such as logging, traffic inspection, and component validation—to isolate where authentication mechanisms (e.g., OAuth, JWT, Kerberos) break down. Common use cases include troubleshooting failed API calls, expired tokens, or misconfigured role-based access control (RBAC). Implementations typically span multiple layers (client, server, service mesh) and require cross-team collaboration between security, DevOps, and product teams. This guide covers key components, schema references, query examples, and related patterns for debugging authentication issues efficiently.

---

## **Key Concepts & Implementation Details**

| **Concept**               | **Description**                                                                                                                                                                                                 |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Debugging Layers**      | Authentication issues may occur at: **Client** (e.g., malformed requests), **Middleware** (e.g., reverse proxies), **Service** (e.g., token validation logic), or **Broker** (e.g., OAuth servers). |
| **Common Failure Modes**  | 1. Missing/invalid tokens, 2. Token expiration, 3. Incorrect scopes/roles, 4. Mismatched public keys (JWT asymm. crypto), 5. Rate-limiting or IP restrictions.                                                                 |
| **Tools & Techniques**    | - Logging: Structured logs (JSON) for tokens, headers, and timestamps. <br> - Tracing: Distributed tracing (Jaeger, OpenTelemetry) to track request flows. <br> - Inspection: Packet capture (Wireshark) or proxy tools (Fiddler). <br> - Mocking: Stubs for downstream dependencies (e.g., mock auth servers). |
| **Debugging Workflow**    | 1. **Reproduce**: Confirm the issue (e.g., via Postman or scripted request). <br> 2. **Isolate**: Pinpoint the layer (client/server). <br> 3. **Validate**: Check logs, tokens, and configurations. <br> 4. **Fix**: Update code/config or escalate. |

---

## **Schema Reference**

### **1. Authentication Request Flow**
| **Field**               | **Type**   | **Description**                                                                                                                                                                                                 | **Example Value**                     |
|-------------------------|------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------|
| `request_id`            | String     | Unique identifier for debugging tracing.                                                                                                                                                                     | `"req-7f3a8b9c-4d5e-6f7g-8h9i-0j1k"` |
| `timestamp`             | ISO-8601   | When the request was made.                                                                                                                                                                                     | `"2023-10-15T14:30:45Z"`              |
| `client_ip`             | IPv4/IPv6  | Source IP of the request (may be masked in logs).                                                                                                                                                             | `"192.168.1.100"`                     |
| `auth_method`           | Enum       | Type of authentication (e.g., `Bearer`, `Basic`, `OAuth2`).                                                                                                                                                   | `"Bearer"`                            |
| `token`                 | String     | Encoded or raw token (obfuscate in logs).                                                                                                                                                                       | `"eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."` |
| `token_expiry`          | ISO-8601   | Expiration time of the token.                                                                                                                                                                                 | `"2023-10-15T15:00:00Z"`              |
| `scope`                 | Array      | Granted permissions (e.g., `["read:profile", "write:settings"]`).                                                                                                                                                   | `["read:api"]`                        |
| `user_identity`         | Object     | Decoded claims from the token (e.g., `sub`, `name`).                                                                                                                                                             | `{"sub": "user123", "name": "Alice"}`  |
| `response_status`       | Integer    | HTTP status code (e.g., `401`, `403`).                                                                                                                                                                                   | `403`                                  |
| `error_code`            | String     | Machine-readable error (e.g., `invalid_token`, `expired_token`).                                                                                                                                                 | `"expired_token"`                     |
| `debug_metadata`        | Object     | Additional context (e.g., proxy headers, service versions).                                                                                                                                                       | `{"x-forwarded-for": "10.0.0.1"}`     |

---

### **2. Token Validation Schema**
| **Field**               | **Type**   | **Description**                                                                                                                                                                                                 | **Example**                          |
|-------------------------|------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `algorithm`             | String     | JWT signing algorithm (e.g., `HS256`, `RS256`).                                                                                                                                                                     | `"RS256"`                             |
| `public_key`            | String     | Base64-encoded public key (for asymmetric crypto).                                                                                                                                                             | `"MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA..."` |
| `kid`                   | String     | Key identifier in JWT header (`kid` claim).                                                                                                                                                                       | `"key-1"`                             |
| `issuer`                | String     | Token issuer (e.g., `https://auth.example.com`).                                                                                                                                                               | `"https://auth.example.com"`          |
| `audience`              | String     | Target service audience.                                                                                                                                                                                         | `"api.example.com"`                   |
| `valid_until`           | ISO-8601   | Token validity period.                                                                                                                                                                                         | `"2023-10-15T15:00:00Z"`              |

---

## **Query Examples**

### **1. Filtering Failed Authentication Logs**
**Use Case**: Find all `401 Unauthorized` requests in the last hour with `invalid_token` errors.

```sql
SELECT *
FROM auth_logs
WHERE status_code = 401
  AND error_code = 'invalid_token'
  AND timestamp >= NOW() - INTERVAL '1 hour';
```

**Grafana Loki Query**:
```loki
{job="auth-service"} | json
  | status_code=~"^40[1-9]"
  | error_code="invalid_token"
  | line_format "{{.timestamp}} {{.request_id}}: {{.user_identity}}"
```

---

### **2. Tracking Token Expiry Issues**
**Use Case**: Identify tokens expiring within 5 minutes of use (potential clock skew or misconfiguration).

```sql
SELECT
  request_id,
  token_expiry,
  timestamp,
  DATEDIFF(token_expiry, timestamp) AS expiry_margin_minutes
FROM auth_logs
WHERE DATEDIFF(token_expiry, timestamp) BETWEEN 0 AND 5
ORDER BY expiry_margin_minutes;
```

---

### **3. Debugging Proxy Headers**
**Use Case**: Correlate client requests with proxy-manipulated headers (e.g., `X-Forwarded-For`).

```bash
# Grep logs for proxy-related errors
grep -E "X-Forwarded-For|proxy" /var/log/auth-service.log | jq
```

---

### **4. Validating JWT Claims**
**Use Case**: Verify if a JWT `kid` matches the expected public key.

```bash
# Extract kid from JWT header
jwt_header=$(echo "$JWT_TOKEN" | jq -R 'split("\.")[0] | @base64d' | jq -r '.kid')

# Fetch corresponding public key from metadata store
curl -s "https://keys.example.com/$jwt_header" | jq
```

---

## **Related Patterns**

| **Pattern**                          | **Description**                                                                                                                                                                                                 |
|--------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **[Circuit Breaker](https://...)**  | Useful for rate-limiting authentication attempts during outages (e.g., OAuth provider downtime).                                                                                                             |
| **[Layered Logging](https://...)**   | Enables cross-layer debugging by standardizing log formats across client, API, and auth services.                                                                                                                |
| **[Canary Releases](https://...)**   | Gradually roll out auth changes to detect issues early (e.g., new token formats).                                                                                                                               |
| **[Service Mesh Debugging](https://...)** | Tools like Istio or Linkerd provide fine-grained authentication metrics (e.g., token validation latency).                                                                                                     |
| **[Idempotency Keys](https://...)** | Prevents duplicate auth requests from retry logic (e.g., transient failures).                                                                                                                                  |

---
**Notes**:
- For asymmetric JWT validation, ensure the public key (`kid`) is cached locally or fetched from a secure endpoint.
- Use **token replay attacks** testing tools (e.g., `jwt_tool` CLI) to verify token security.
- **Security Warning**: Never log raw tokens or sensitive claims in production environments. Use token hashes instead.