**[Pattern] Security Optimization Reference Guide**
*Version 1.0*
*Last Updated: [Date]*
*Tags: #Security #Optimization #DefenseInDepth #Performance*

---

### **1. Overview**
The **Security Optimization** pattern improves security posture while minimizing performance overhead or complexity. It focuses on applying lightweight, high-impact measures—such as selective encryption, granular access controls, or just-in-time privileges—to reduce attack surfaces without sacrificing efficiency.

Key goals:
- **Reduced risk exposure** without over-engineering.
- **Scalable security** that adapts to system load.
- **Compliance alignment** with minimal manual intervention.

This pattern is typically applied to systems handling sensitive data (e.g., APIs, microservices, databases) or high-traffic environments.

---

### **2. Key Concepts**
| **Term**               | **Definition**                                                                                                                                 | **Example Use Case**                                                                                     |
|------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------|
| **Selective Encryption**  | Encrypts only critical data fields (e.g., PII) rather than entire databases or files.                                                          | Masking credit card numbers in logs while leaving timestamps unencrypted.                                |
| **Granular RBAC**      | Role-Based Access Control (RBAC) with least-privilege roles scoped to specific resources/jobs.                                                   | A CI/CD pipeline role with read-only permissions for `secrets` but execute permissions for `build`.       |
| **Just-in-Time (JIT) Privileges** | Dynamic elevation of access rights only during specific operations (e.g., patch deployment) and automatic revocation afterward.        | Temporary `sudo` access for a deploy key during a zero-downtime update.                                   |
| **Rate Limiting**      | Limits request frequency per IP/user to prevent brute-force attacks or DDoS.                                                                | Capping API calls to 100/minute for non-authenticated users.                                               |
| **Zero-Trust Segmentation** | Isolates workloads in micro-segments (e.g., VLANs, pod networks) with strict inter-segment policies.                                       | Kubernetes `NetworkPolicies` restricting pod-to-pod traffic unless authenticated.                         |
| **Data Minimization**  | Stores only necessary data and discards temporary/duplicate records.                                                                         | purging debug logs after 7 days or compressing session cookies.                                           |
| **Hardened Defaults**  | Configures systems with secure defaults (e.g., disabled legacy protocols, locked-down services).                                           | Disabling RDP/SSH root login by default in cloud VMs.                                                     |

---

### **3. Schema Reference**
Below are common schemas for implementing security optimization patterns. Adjust based on your architecture (e.g., cloud, on-prem, serverless).

#### **3.1 Selective Encryption Schema**
| **Field**            | **Type**       | **Description**                                                                                                                                 | **Example Value**                     |
|----------------------|----------------|-------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------|
| `field_name`         | `string`       | Target data field to encrypt (e.g., `user.credit_card`).                                                                                        | `"user.payment_info"`                   |
| `algorithm`          | `enum`         | Encryption standard (AES, RSA, etc.).                                                                                                         | `"AES-256-GCM"`                       |
| `key_rotation_days`  | `integer`      | Days before keys rotate (0 = manual).                                                                                                       | `30`                                   |
| `exclusion_list`     | `array<string>`| Fields to *not* encrypt (e.g., logs, audit trails).                                                                                          | `["user.id", "session.token"]`         |
| `key_vault`          | `string`       | Reference to KMS/API (e.g., AWS KMS, HashiCorp Vault).                                                                                     | `"vault://aws/kms/arn:..."`            |

#### **3.2 Granular RBAC Schema**
| **Field**            | **Type**       | **Description**                                                                                                                                 | **Example Value**                     |
|----------------------|----------------|-------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------|
| `role_name`          | `string`       | Unique role identifier (e.g., `auditor:finance:read`).                                                                                     | `"deploy:staging:write"`               |
| `permissions`        | `array<object>`| List of resource:action pairs.                                                                                                              | `[{"resource":"secrets/abc123", "action":"get"}]` |
| `conditions`         | `object`       | Dynamic filters (e.g., time-of-day, IP range).                                                                                            | `{"time":"09:00-17:00", "ip": "192.168.1.0/24"}` |
| `expiration`         | `datetime`     | Role validity period (empty = permanent).                                                                                                   | `"2024-12-31T23:59:59Z"`              |

#### **3.3 Rate Limiting Schema**
| **Field**            | **Type**       | **Description**                                                                                                                                 | **Example Value**                     |
|----------------------|----------------|-------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------|
| `endpoint`           | `string`       | API route or resource (e.g., `/api/payments`).                                                                                                 | `"/auth/login"`                        |
| `limit`              | `integer`      | Max requests per window.                                                                                                                   | `150`                                  |
| `window_seconds`     | `integer`      | Time window for counting (e.g., 60s).                                                                                                        | `300`                                  |
| `identifier`         | `string`       | Field to track (e.g., `user_id`, `ip`).                                                                                                      | `"user_id"`                            |
| `block_duration`     | `integer`      | Seconds to block after limit (0 = no block).                                                                                             | `60`                                   |

#### **3.4 Zero-Trust Segmentation Schema**
| **Field**            | **Type**       | **Description**                                                                                                                                 | **Example Value**                     |
|----------------------|----------------|-------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------|
| `segment_name`       | `string`       | Logical network segment (e.g., `app:dev`, `db:prod`).                                                                                     | `"payments:q2-2024"`                   |
| `allowed_ingress`    | `array<string>`| Source segments/ports allowed to access this one.                                                                                          | `["app:dev:8080", "monitoring:6000"]`  |
| `egress_policy`      | `string`       | Default egress rule (`allow`, `deny`, or `strict`).                                                                                     | `"strict"`                             |
| `mfa_requirement`    | `boolean`      | Enforce MFA for cross-segment access.                                                                                                     | `true`                                 |

---

### **4. Query Examples**
#### **4.1 Selective Encryption**
**Use Case:** Encrypt `user.payment_info` in a PostgreSQL database.
```sql
-- Apply encryption to a specific column
ALTER TABLE users ALTER COLUMN payment_info TYPE jsonb
ENCRYPTED USING 'AES-256-GCM' WITH KEY_ROTATION_DAYS = 30;
```

**API Example (Python, using `cryptography`):**
```python
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import os

# Encrypt sensitive field
key = os.getenv("ENCRYPTION_KEY")
iv = os.urandom(16)
cipher = Cipher(algorithms.AES(key), modes.GCM(iv))
encryptor = cipher.encryptor()
encrypted_data = encryptor.update(b"credit_card=4111...") + encryptor.finalize()
```

#### **4.2 Granular RBAC**
**Use Case:** Configure a Kubernetes `Role` for limited pod access.
```yaml
# roles.yaml
kind: Role
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: limited-buildrole
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list"]
  resourceNames: ["build-pod-*"]
---
# Bind to a ServiceAccount
kind: RoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: buildrole-binding
subjects:
- kind: ServiceAccount
  name: ci-cd-agent
  namespace: staging
roleRef:
  kind: Role
  name: limited-buildrole
  apiGroup: rbac.authorization.k8s.io
```

**API Example (AWS IAM Policy):**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["secrets:GetSecretValue"],
      "Resource": "arn:aws:secretsmanager:us-east-1:123456789012:secret:db-credentials-*",
      "Condition": {
        "IpAddress": {"aws:SourceIp": ["192.168.1.0/24"]},
        "StringEquals": {"aws:RequestTag/Requester": "deploy-team"}
      }
    }
  ]
}
```

#### **4.3 Rate Limiting**
**Use Case:** NGINX rate limiting for `/api/login`.
```nginx
limit_req_zone $binary_remote_addr zone=login_limit:10m rate=150r/m;

server {
  location /api/login {
    limit_req zone=login_limit burst=50;
    allow 192.168.1.0/24;
    deny all;
  }
}
```

**API Example (Express.js with `rate-limiter-flexible`):**
```javascript
const { RateLimiterMemory } = require("rate-limiter-flexible");

const limiter = new RateLimiterMemory({
  points: 150,
  duration: 300, // 5 minutes
  blockDuration: 60, // 1 minute
});

app.post("/api/payments", async (req, res, next) => {
  try {
    await limiter.consume(req.user.id);
    // Proceed if rate limit not exceeded
  } catch {
    res.status(429).send("Too many requests");
  }
});
```

#### **4.4 Zero-Trust Segmentation**
**Use Case:** Kubernetes `NetworkPolicy` for pod isolation.
```yaml
# network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: payments-segment-policy
spec:
  podSelector:
    matchLabels:
      app: payments-service
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: api-gateway
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: database
    ports:
    - protocol: TCP
      port: 5432
```

---

### **5. Implementation Considerations**
| **Aspect**          | **Best Practice**                                                                                                                                 | **Tools/Libraries**                                                                                     |
|---------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| **Key Management**  | Use HSMs or cloud KMS for keys; avoid hardcoding.                                                                                          | AWS KMS, HashiCorp Vault, Azure Key Vault                                                          |
| **Performance**     | Benchmark encryption overhead (e.g., <5ms latency for AEAD).                                                                               | Benchmark with `ab` (ApacheBench) or `k6`                                                          |
| **Audit Logging**   | Log encryption/decryption events (who, when, which field).                                                                               | ELK Stack, Datadog, OpenTelemetry                                                                       |
| **Testing**         | Validate with chaos engineering (e.g., failover key rotation).                                                                          | Chaos Mesh, Gremlin                                                                                   |
| **Compliance**      | Align with GDPR, HIPAA, or SOC2 requirements.                                                                                              | Compliance-as-Code (e.g., Policies-as-Code with Open Policy Agent)                                   |

---

### **6. Query Examples (Continued)**
#### **4.5 Just-in-Time Privileges**
**Use Case:** AWS IAM temporary credentials for EC2 deployments.
```bash
# Generate temporary credentials via CLI
aws sts assume-role \
  --role-arn arn:aws:iam::123456789012:role/DeployRole \
  --role-session-name "one-time-deploy" \
  --duration-seconds 3600 \
  --query "Credentials" --output json > /tmp/credentials.json
```

**API Example (Python):**
```python
import boto3

sts_client = boto3.client("sts")
response = sts_client.assume_role(
    RoleArn="arn:aws:iam::123456789012:role/DeployRole",
    RoleSessionName="script-execution",
    DurationSeconds=3600
)
credentials = response["Credentials"]
```

#### **4.6 Data Minimization**
**Use Case:** PostgreSQL partial indexing to reduce scanned rows.
```sql
-- Create index only on necessary columns
CREATE INDEX idx_user_email ON users(email) WHERE is_active = true;
```

**API Example (Node.js):**
```javascript
// Query only required fields
db.collection("users")
  .find({}, { projection: { _id: 0, name: 1, email: 1 } })
  .toArray();
```

---

### **7. Common Pitfalls & Mitigations**
| **Pitfall**                          | **Mitigation**                                                                                                                                 |
|--------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|
| Over-encryption (performance cost)   | Profile latency with tools like `perf` or `vtune`; prioritize high-value data.                                                          |
| RBAC bloat                            | Regularly audit roles with `kubectl auth can-i` (K8s) or AWS IAM Access Analyzer.                                                       |
| Rate-limiting false positives         | Use whitelists for trusted IPs instead of blanket blocking.                                                                            |
| Segmentation overkill               | Start with 1–2 critical segments; expand gradually.                                                                                      |
| Key rotation failures                | Test key rotation in staging with `failover` tests.                                                                                       |
| Compliance gaps                       | Use tools like OpenSCAP or Prisma Cloud for automated compliance checks.                                                                   |

---

### **8. Related Patterns**
| **Pattern**                     | **Description**                                                                                                                                 | **When to Pair With Security Optimization**                                      |
|----------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **Defense in Depth**             | Layered security controls (e.g., firewalls + encryption + monitoring).                                                                | Use selective encryption *in addition* to network segmentation.                     |
| **Secrets Management**           | Secure storage and rotation of credentials.                                                                                              | Combine with JIT privileges for dynamic credential access.                         |
| **Zero-Trust Architecture**      | No implicit trust; verify every access request.                                                                                         | Zero-trust segmentation reinforces this pattern.                                   |
| **Observability**                | Centralized logging/metrics for security events.                                                                                         | Audit logs from selective encryption or RBAC policies.                              |
| **Chaos Engineering**            | Test system resilience under failure scenarios.                                                                                          | Validate key rotation or rate-limiting under high load.                             |
| **Infrastructure as Code (IaC)** | Templatize security configurations (e.g., Terraform modules).                                                                        | Enforce hardened defaults via IaC (e.g., deny-unauthorized-cloudwatch-logs).        |

---

### **9. References**
- **NIST SP 800-53**: Security controls for systems and organizations.
  [Link](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final)
- **OWASP Security Cheat Sheet**: Best practices for app security.
  [Link](https://cheatsheetseries.owasp.org/)
- **CIS Benchmarks**: Hardened configurations for cloud/on-prem.
  [Link](https://www.cisecurity.org/benchmark/)
- **IETF RFC 7252**: Datagram Transport Layer Security (DTLS) for selective encryption.
  [Link](https://datatracker.ietf.org/doc/html/rfc7252)