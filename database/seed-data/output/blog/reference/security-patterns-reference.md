# **[Security Patterns] Reference Guide**

---

## **Overview**
Security Patterns provide proven, reusable solutions to common security challenges across software systems. This guide categorizes and documents core security patterns—such as *Authentication*, *Authorization*, *Data Encryption*, *Defense in Depth*, and *Secure Communication*—to help developers and architects embed robust security by design. Each pattern includes a structured schema, implementation best practices, and real-world use cases. Whether securing APIs, databases, or user sessions, these patterns offer modular, adaptable strategies to mitigate risks like data breaches, injection attacks, or unauthorized access.

---

## **Schema Reference**

Security patterns follow a standardized schema to ensure consistency. Below are key attributes with definitions:

| **Attribute**          | **Description**                                                                                     | **Example Values**                                                                 |
|-------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **Pattern Name**        | Unique identifier for the pattern (e.g., `Defense in Depth`, `JWT Authentication`).                   | `Least Privilege Access`, `Rate Limiting`                                         |
| **Category**            | Broader security domain (e.g., *Authentication*, *Data Protection*, *Network Security*).           | `Authentication`, `Data Protection`                                              |
| **Problem Description** | Concise summary of the security challenge addressed (e.g., "Ensure users are verified").           | *"How to protect user accounts from credential stuffing."*                         |
| **Solution**            | High-level approach to resolve the problem (e.g., "Use multi-factor authentication").                | *"Implement OAuth 2.0 with TOTP for login."*                                       |
| **Components**          | Key elements involved (e.g., *API Gateway*, *Database*, *Client App*).                               | `Auth Service, Token Store, Frontend`                                             |
| **Use Cases**           | Scenarios where the pattern applies (e.g., "Securing Web APIs", "Protecting Sensitive APIs").        | *"Mobile banking app", "Cloud-based SaaS platforms"*                              |
| **Non-Functional Reqs** | Performance/constraints (e.g., *"Latency < 100ms"*, *"Supports 10K+ concurrent users"*).           | `High availability`, `Low computational overhead`                                  |
| **Implementation Steps**| Step-by-step actions to deploy the pattern.                                                       | 1. Configure `OAuth2` provider.<br>2. Store tokens in Redis.<br>3. Enforce CORS. |
| **Mitigated Risks**     | Security threats addressed (e.g., *"Brute-force attacks"*, *"Man-in-the-middle"*).                  | `Session hijacking`, `Unauthorized API access`                                    |
| **Anti-Patterns**       | Common mistakes to avoid.                                                                      | *"Storing tokens in frontend-only cookies."*                                      |
| **Tools/Libraries**     | Recommended tools/frameworks (e.g., *Spring Security*, *AWS KMS*).                                 | `Passport.js`, `OpenSSL`, `Vault by HashiCorp`                                    |
| **Example Code Snippets** | Minimal code samples for integration.                                                           | ```python
# JWT Authentication Example
import jwt
token = jwt.encode({"user_id": 123}, "secret_key", algorithm="HS256")
``` |
| **Validation Rules**    | Checks to verify correct implementation (e.g., *"Token expires in < 1h"*).                          | *"HMAC algorithm >= SHA-256."*                                                     |
| **Monitoring Metrics**  | Key performance/security metrics to track (e.g., *"Failed login attempts"*, *"Token rotation rate"*). | `Failed login rate > 5% → Alert.`                                                 |

---

## **Query Examples**

### **1. Querying Patterns by Category**
**Goal:** Retrieve all authentication-related patterns.
```sql
SELECT * FROM security_patterns
WHERE category = 'Authentication'
ORDER BY pattern_name;
```
**Output:**
| Pattern Name           | Problem Description                          | Components                     |
|------------------------|-----------------------------------------------|--------------------------------|
| JWT Authentication     | Stateless user verification                   | API Gateway, Frontend          |
| OAuth 2.0              | Secure third-party authentication              | Auth Server, Client App        |

---

### **2. Filtering by Use Case**
**Goal:** Find patterns for cloud APIs.
```sql
SELECT pattern_name, solution
FROM security_patterns
WHERE use_cases LIKE '%cloud-based%' OR use_cases LIKE '%API%';
```
**Output:**
| Pattern Name       | Solution                              |
|--------------------|---------------------------------------|
| API Rate Limiting  | Implement Redis-based token buckets.   |
| TLS for APIs       | Enforce HTTPS with SNI validation.    |

---

### **3. Checking Mitigated Risks**
**Goal:** Identify patterns that counter SQL injection.
```sql
SELECT pattern_name, solution
FROM security_patterns
WHERE mitigated_risks LIKE '%injection%';
```
**Output:**
| Pattern Name         | Solution                          |
|----------------------|-----------------------------------|
| Prepared Statements  | Use parameterized queries.        |
| WAF Integration      | Deploy Cloudflare/WAF rules.      |

---

### **4. Combining Conditions**
**Goal:** List low-latency, high-availability patterns for databases.
```sql
SELECT pattern_name, components
FROM security_patterns
WHERE non_functional_reqs LIKE '%low latency%' AND
      non_functional_reqs LIKE '%high availability%' AND
      category = 'Data Protection';
```
**Output:**
| Pattern Name           | Components               |
|------------------------|--------------------------|
| Database Sharding       | Primary DB, Read Replicas |
| Encrypted Backups       | S3, KMS                  |

---

## **Implementation Details**

### **Core Principles**
1. **Defense in Depth (DiD):**
   - **Problem:** Single-layer security fails under attack.
   - **Solution:** Layer security controls (e.g., firewalls + encryption + monitoring).
   - **Example:**
     ```mermaid
     graph TD
         A[Client] -->|HTTPS| B[API Gateway]
         B -->|Auth Header| C[Auth Service]
         C -->|JWT| D[Backend]
         D -->|DB Query| E[Database]
     ```

2. **Least Privilege Access:**
   - **Problem:** Overprivileged accounts risk data leaks.
   - **Solution:** Assign minimal permissions (e.g., IAM roles).
   - **Tool:** AWS IAM policies or Kubernetes RBAC.

3. **Secure Communication:**
   - **Problem:** Unencrypted traffic risks interception.
   - **Solution:** Enforce TLS 1.2+ and mutual TLS (mTLS) for service-to-service.

### **Best Practices**
- **For Authentication:**
  - Prefer **OAuth 2.0** over basic auth.
  - Rotate secrets every **90 days**.
  - Use **passwordless auth** (e.g., WebAuthn) where possible.

- **For Data Protection:**
  - Encrypt data **at rest** (AES-256) and **in transit** (TLS 1.3).
  - Mask sensitive fields in logs (e.g., `****-****-1234`).

- **For APIs:**
  - Implement **rate limiting** (e.g., 100 requests/minute).
  - Validate all inputs (use libraries like OWASP ZAP).

### **Common Pitfalls**
- **Hardcoded Secrets:** Avoid `config.py` with plaintext keys.
- **Overly Complex Auth:** Simplify flows (e.g., avoid nested OAuth flows).
- **Ignoring Updates:** Fail to patch libraries (e.g., Log4j vulnerabilities).

---

## **Query Examples (Continued)**

### **5. Pattern Adoption Check**
**Goal:** Check if a pattern supports specific tools.
```sql
SELECT pattern_name, tools_libraries
FROM security_patterns
WHERE tools_libraries LIKE '%Spring Security%' AND
      category = 'Authentication';
```
**Output:**
| Pattern Name       | Tools/Libraries               |
|--------------------|-------------------------------|
| Spring Security    | `spring-boot-starter-security`|

---

### **6. Performance Impact Analysis**
**Goal:** Identify patterns with high computational cost.
```sql
SELECT pattern_name, non_functional_reqs
FROM security_patterns
WHERE non_functional_reqs LIKE '%high overhead%';
```
**Output:**
| Pattern Name           | Non-Functional Reqs                          |
|------------------------|---------------------------------------------|
| Full Disk Encryption   | *"Slows I/O by ~30%"*                        |

---

## **Related Patterns**

| **Pattern**               | **Description**                                                                 | **When to Use**                                  |
|---------------------------|---------------------------------------------------------------------------------|-------------------------------------------------|
| **Defense in Depth**      | Combine multiple security layers.                                             | Cloud environments, multi-tenant systems.      |
| **Zero Trust Architecture** | Assume breach; verify every access.                                          | High-security industries (finance, healthcare). |
| **Secure by Default**     | Disable features unless explicitly enabled.                                    | Open-source projects, public APIs.             |
| **Fail-Secure**           | System degrades safely under attack (e.g., reject invalid inputs).             | Critical infrastructure.                       |
| **Data Minimization**     | Collect only necessary user data.                                             | GDPR-compliant apps.                            |

---

## **Example Workflow: Securing a REST API**

1. **Apply *Authentication* (JWT):**
   - Clients authenticate via OAuth 2.0 → receive JWT.
   - **Validation:** Verify JWT signature on each request.

2. **Apply *Rate Limiting*:**
   - Use Redis to track request counts per IP.
   - **Rule:** `max_requests = 100`, `window = 1 minute`.

3. **Apply *Defense in Depth*:**
   - Layer 1: API Gateway enforces TLS.
   - Layer 2: Backend validates JWT.
   - Layer 3: Database uses connection pooling with least privileges.

4. **Monitor:**
   - Log failed JWT validations → trigger alerts if rate exceeds threshold.

---
**Reference Tools:**
- [OWASP Security Patterns](https://cheatsheetseries.owasp.org/)
- AWS Security Patterns: [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)

---
**Key Takeaways:**
- **Modularity:** Combine patterns (e.g., *JWT + Rate Limiting*).
- **Trade-offs:** Balance security with performance (e.g., mTLS adds latency).
- **Compliance:** Align with frameworks like ISO 27001 or SOC 2.