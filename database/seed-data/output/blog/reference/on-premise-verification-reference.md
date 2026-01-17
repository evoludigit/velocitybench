**[Pattern] On-Premise Verification – Reference Guide**

---

### **Overview**
The **On-Premise Verification (OPV)** pattern ensures that sensitive data processing, authentication, and validation occur within a fully controlled, non-cloud environment. This approach mitigates risks associated with third-party infrastructure, compliance violations, or latency-sensitive workloads. OPV is commonly used for:
- **Regulated industries** (finance, healthcare, government) requiring strict data sovereignty.
- **High-security scenarios** (e.g., multifactor authentication, biometric verification).
- **Low-latency needs** (e.g., real-time fraud detection, critical infrastructure monitoring).

OPV integrates with existing on-premise systems (e.g., Active Directory, LDAP, or custom microservices) to validate identities, credentials, or data integrity without external dependencies.

---

### **Key Concepts**
| **Concept**               | **Description**                                                                                                                                                                                                 | **Use Cases**                                                                 |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **Verification Endpoint** | A secure API or service running on-premise that processes authentication/validation requests. May include TLS, rate limiting, and audit logging.                                                           | MFA tokens, API key validation, user role checks.                              |
| **Local Identity Store**   | Database (e.g., SQL, NoSQL) or service (LDAP, Active Directory) storing user credentials/attributes. Supports on-premise single sign-on (SSO).                                                        | On-premise Active Directory, custom user databases.                           |
| **Policy Engine**          | Rule-based logic (e.g., JSON policies, Lua scripts) to enforce custom validation rules (e.g., "Require IP whitelisting for admins").                                                            | IP-based access, device fingerprinting, behavioral analytics.                 |
| **Audit Trail**           | Immutable logs of all verification events for compliance (e.g., GDPR, HIPAA). Includes timestamps, request/response payloads, and user IDs.                                                         | Forensic investigations, audit compliance, fraud detection.                   |
| **Offline Mode**          | Optional fallback for disconnected environments (e.g., caching responses, batch processing).                                                                                                             | Air-gapped systems, rural deployments.                                        |
| **Cross-Service Sync**    | Mechanisms to sync verification results with other on-premise systems (e.g., SIEM tools, microservices).                                                                                               | Incident response, real-time alerts, distributed permission checks.           |

---

### **Schema Reference**
#### **1. Verification Request Payload**
| **Field**               | **Type**       | **Required** | **Description**                                                                                                                                                     | **Example Value**                          |
|-------------------------|----------------|--------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------|
| `request_id`            | `string`       | Yes          | Unique identifier for tracing the request across systems.                                                                                                         | `"req_12345abcde"`                          |
| `user_id`               | `string`       | Yes          | Identifier for the user/device being verified (e.g., UUID, email).                                                                                                | `"user_98765"`                              |
| `credentials`           | `object`       | Conditional* | User-provided data (e.g., password, token, biometric hash).                                                                                                       | `{"password": "secure123", "device_id": "dev_123"}` |
| `context`               | `object`       | No           | Metadata (e.g., IP, timestamp, client app version).                                                                                                               | `{"ip": "192.0.2.1", "timestamp": "2023-10-01T12:00:00Z"}` |
| `policy_id`             | `string`       | No           | Reference to a custom policy (e.g., `"strict_mfa"`).                                                                                                                 | `"strict_mfa"`                              |
| `retry_attempts`        | `integer`      | No           | Number of retries allowed for this request (default: `3`).                                                                                                         | `2`                                         |
| `signatures`            | `array`        | No           | Digital signatures for data integrity (e.g., JWT, PGP).                                                                                        | `[{"alg": "HS256", "signature": "..."}]`   |

\* *Required if `credentials` is not pre-authenticated (e.g., via token).*

---

#### **2. Verification Response Payload**
| **Field**               | **Type**       | **Description**                                                                                                                                                     | **Example Value**                          |
|-------------------------|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------|
| `status`                | `string`       | `"success"`, `"failed"`, or `"pending"` (for offline mode).                                                                                                       | `"success"`                                 |
| `user_data`             | `object`       | Validated user attributes (e.g., roles, expiration).                                                                                                               | `{ "roles": ["admin"], "expires_at": "2023-12-31" }` |
| `errors`                | `array`        | List of validation failures (e.g., `{"code": "invalid_credentials", "message": "Wrong password"}`).                                                               | `[{ "code": "ip_blocked", "message": "IP address restricted" }]` |
| `policy_result`         | `object`       | Details of policy evaluation (e.g., rules passed/failed).                                                                                                         | `{ "rules": {"ip_whitelist": "pass", "mfa": "fail" } }` |
| `audit_id`              | `string`       | Reference to the audit log entry.                                                                                                                                  | `"audit_54321"`                             |
| `timestamp`             | `string`       | ISO 8601 timestamp of the response.                                                                                                                              | `"2023-10-01T12:00:05Z"`                   |

---

#### **3. Audit Log Entry**
| **Field**               | **Type**       | **Description**                                                                                                                                                     | **Example Value**                          |
|-------------------------|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------|
| `event_id`              | `string`       | Unique identifier for the audit entry.                                                                                                                             | `"log_67890"`                               |
| `request_id`            | `string`       | Links to the original verification request.                                                                                                                       | `"req_12345abcde"`                          |
| `user_id`               | `string`       | User/device involved.                                                                                                                                             | `"user_98765"`                              |
| `action`                | `string`       | `"verify"`, `"authenticate"`, or `"policy_evaluate"`.                                                                                                          | `"authenticate"`                            |
| `status`                | `string`       | `"success"`, `"failed"`, or `"pending"`.                                                                                                                       | `"success"`                                 |
| `payload`               | `object`       | Original request/response (sanitized for PII).                                                                                                                 | `{ "ip": "192.0.2.1", "status": "success" }` |
| `rules_evaluated`       | `array`        | List of policies applied (e.g., `{"ip_whitelist": "pass", "mfa": "fail"}`).                                                                                 | `[{"name": "mfa", "result": "fail"}]`        |
| `duration_ms`           | `integer`      | Latency of the verification process.                                                                                                                             | `42`                                        |

---

### **Implementation Steps**
#### **1. Set Up the Verification Endpoint**
- **Deployment**:
  - Deploy as a **gRPC service**, **REST API**, or **WebSocket** endpoint on a secure on-premise server (e.g., Kubernetes pod, VM).
  - Secure with:
    - TLS (certificates from internal CA or Let’s Encrypt).
    - Firewall rules (allow only trusted IPs/subnets).
    - Rate limiting (e.g., 100 requests/sec/IP).
- **Dependencies**:
  ```yaml
  # Docker example (simplified)
  services:
    verification-endpoint:
      image: organization/opv-service:v1.0
      ports:
        - "8080:8080"
      environment:
        - IDENTITY_DB_URL=postgres://localhost:5432/identity
        - POLICY_ENGINE_PATH=/etc/policies/strict_mfa.json
      volumes:
        - ./policies:/etc/policies
  ```

#### **2. Configure the Local Identity Store**
- **Database Example (SQL)**:
  ```sql
  CREATE TABLE users (
    user_id UUID PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    roles JSONB NOT NULL,  -- e.g., ["admin", "analyst"]
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
  );
  ```
- **LDAP/Active Directory Integration**:
  Use libraries like [`ldapjs`](https://www.npmjs.com/package/ldapjs) (Node.js) or [`python-ldap`](https://pypi.org/project/python-ldap/) to sync user data.

#### **3. Define Verification Policies**
- **Policy File Example (`strict_mfa.json`)**:
  ```json
  {
    "rules": [
      {
        "name": "ip_whitelist",
        "condition": "user_ip IN ['10.0.0.0/8', '192.168.1.0/24']",
        "message": "IP not authorized"
      },
      {
        "name": "mfa_required",
        "condition": "request.credentials.mfa_token IS NOT NULL",
        "message": "MFA token required"
      },
      {
        "name": "account_active",
        "condition": "user.is_active",
        "message": "Account suspended"
      }
    ],
    "strategy": "all"  // "all" or "any" for rule enforcement
  }
  ```
- **Dynamic Policies**:
  Use a configuration server (e.g., Consul, etcd) to update policies without redeploying the endpoint.

#### **4. Implement Audit Logging**
- **Database Schema**:
  ```sql
  CREATE TABLE audit_logs (
    log_id UUID PRIMARY KEY,
    event_id VARCHAR(255) NOT NULL,
    user_id UUID,
    action VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    payload JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX (status),
    INDEX (user_id)
  );
  ```
- **Tools**:
  - **ELK Stack** (Elasticsearch, Logstash, Kibana) for centralized logging.
  - **OpenTelemetry** for distributed tracing.

#### **5. Handle Offline Mode (Optional)**
- **Caching Layer**:
  Use Redis or SQLite to store recent verification results with TTL (e.g., 5 minutes).
  ```python
  # Pseudocode (Python)
  def verify_offline(user_id, request):
      cached = cache.get(f"verif:{user_id}")
      if cached and cached["expires_at"] > now():
          return cached["response"]
      # Fallback to full verification if cache miss
      return full_verification(user_id, request)
  ```
- **Batch Processing**:
  Queue pending requests (e.g., RabbitMQ) to reprocess once connectivity is restored.

#### **6. Sync with Other Systems**
- **Webhooks**:
  Trigger alerts to SIEM tools (e.g., Splunk, Wazuh) on failed verifications:
  ```http
  POST https://siem.example.com/webhook/log
  Content-Type: application/json

  {
    "type": "verification_failed",
    "user_id": "user_98765",
    "ip": "192.0.2.2",
    "timestamp": "2023-10-01T12:00:05Z"
  }
  ```
- **Event Bus**:
  Use Kafka or NATS for real-time sync between microservices.

---

### **Query Examples**
#### **1. Basic Authentication (gRPC)**
**Request (`authenticate.rpc`)**:
```protobuf
syntax = "proto3";

service Verification {
  rpc Authenticate (AuthRequest) returns (AuthResponse) {
    option (google.api.method_signature) = "user_id,credentials";
  }
}

message AuthRequest {
  string user_id = 1;
  map<string, string> credentials = 2;  // e.g., {"password": "...", "mfa_token": "..."}
  string context_ip = 3;
}

message AuthResponse {
  bool success = 1;
  string error_message = 2;
  map<string, string> user_attributes = 3;  // e.g., {"role": "admin"}
}
```
**Example Call**:
```bash
grpcurl -plaintext localhost:8080 Verification.Authenticate \
  '{"user_id": "user_98765", "credentials": {"password": "secure123"}}'
```
**Response**:
```json
{
  "success": true,
  "user_attributes": {"role": "admin", "expires_at": "2023-12-31"}
}
```

#### **2. Policy Evaluation (REST)**
**Request**:
```http
POST /v1/verify/policy
Content-Type: application/json

{
  "user_id": "user_98765",
  "policy_id": "strict_mfa",
  "context": {
    "ip": "192.0.2.1",
    "client_app": "mobile_v1.0"
  }
}
```
**Response**:
```json
{
  "status": "success",
  "policy_result": {
    "rules": {
      "ip_whitelist": "pass",
      "mfa": "fail",
      "client_version": "pass"
    }
  },
  "audit_id": "audit_54321"
}
```

#### **3. Audit Query (SQL)**
```sql
-- Find all failed verifications for a user
SELECT *
FROM audit_logs
WHERE user_id = 'user_98765'
  AND status = 'failed'
  AND created_at > NOW() - INTERVAL '7 days';
```

#### **4. Offline Cache Check (Redis)**
```bash
# Check if a user's verification is cached
redis-cli GET "verif:user_98765"
# Response (JSON):
# {"success":true,"response":{"status":"approved"},"expires_at":"2023-10-01T12:05:00Z"}
```

---

### **Error Handling**
| **Error Code**          | **Description**                                                                 | **HTTP/gRPC Status** | **Resolution**                                                                 |
|-------------------------|---------------------------------------------------------------------------------|----------------------|--------------------------------------------------------------------------------|
| `invalid_request`       | Missing or malformed payload (e.g., missing `user_id`).                   | `400 Bad Request`    | Validate input schema; log for debugging.                                     |
| `credentials_rejected`  | Invalid password, MFA token, or signature.                                    | `401 Unauthorized`   | Enforce password policies; audit failed attempts.                              |
| `policy_violation`      | Rule failed (e.g., IP not whitelisted).                                        | `403 Forbidden`      | Review policy settings; allowlist IPs/protocols.                             |
| `service_unavailable`   | Dependency failure (e.g., DB connection lost).                                 | `503 Service Unavailable` | Implement retry logic; monitor DB health.                                    |
| `rate_limited`          | Exceeded request quota for the IP/user.                                         | `429 Too Many Requests` | Use token buckets or sliding windows for rate limiting.                        |
| `offline_fallback`      | No connectivity to identity store.                                            | `504 Gateway Timeout` | Enable caching or batch processing for offline scenarios.                      |

---

### **Performance Considerations**
| **Optimization**          | **Technique**                                                                 | **Impact**                                                                 |
|---------------------------|------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Caching**               | Cache frequent queries (e.g., user roles) in Redis (TTL: 1 hour).             | Reduces DB load by 80%.                                                    |
| **Connection Pooling**    | Reuse DB connections (e.g., PgBouncer for PostgreSQL).                        | Cuts connection overhead from 50ms to 2ms.                                  |
| **Async Processing**      | Offload policy evaluation to a worker queue (e.g., Celery).                  | Prevents endpoint blocking; improves latency for concurrent requests.       |
| **Batch Verification**    | Process multiple users in a single DB call (e.g., `WHERE user_id IN (...)`). | Reduces round trips for bulk operations.                                    |
| **Compression**           | Gzip payloads for REST/gRPC endpoints.                                        | Saves bandwidth (30–50% reduction).                                         |
| **Hardware**              | Use NVMe SSDs for DB storage; scale horizontally with load balancers.         | Handles 10K+ RPS with low latency.                                         |

---

### **Security Best Practices**
1. **Encryption**:
   - Encrypt credentials at rest (AES-256 with HSM).
   - Use TLS 1.3 for all communications.
2. **Least Privilege**:
   - Restrict database users to read-only for verification endpoints.
   - Rotate API keys/passwords every 90 days.
3. **Input Validation**:
   - Sanitize all inputs to prevent SQLi/NoSQLi (e.g., use parameterized queries).
   - Validate JSON payloads with a schema (e.g., JSON Schema).
4. **Audit Controls**:
   - Log all admin actions (e.g., policy changes).
   - Block brute-force attacks with temporary IP bans.
5. **Zero Trust**:
   - Assume breach: require re-authentication for privileged actions.
   - Enforce device fingerprinting for admins.

---

### **Related Patterns**
| **Pattern**                     | **Description**                                                                                                                                                     | **When to Combine**                                                                 |
|----------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **[Micro-Frontends]**           | Decouple verification UI from backend services for modularity.                                                                                                   | Use if OPV requires custom client-side workflows (e.g., biometric scanners).       |
| **[Policy as Code]**             | Store and version policies in Git (e.g., Open Policy Agent).                                                                                                   | Ideal for auditing policy changes in regulated environments.                          |
| **[Event Sourcing]**