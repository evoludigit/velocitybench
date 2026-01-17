# **Debugging Security Migration: A Troubleshooting Guide**

## **Introduction**
Security Migration refers to the process of updating, replacing, or modernizing security controls, cryptographic algorithms, authentication mechanisms, or compliance standards (e.g., migrating from TLS 1.0 to TLS 1.2+, updating PBKDF2 to Argon2, or shifting from legacy auth to OAuth 2.0/OpenID Connect). Misconfigurations, backward compatibility issues, or incomplete migrations can introduce vulnerabilities, performance bottlenecks, or downtime.

This guide provides a structured approach to diagnosing and resolving common Security Migration issues.

---

## **1. Symptom Checklist**
Before diving into fixes, confirm which issues are present:

| **Symptom** | **Description** | **Possible Cause** |
|-------------|----------------|-------------------|
| **Authentication Failures** | Users/logins fail with "Invalid Credentials" or "Access Denied" (even for valid users). | - Crypto hash mismatch (e.g., old vs. new password hashing).
- Session tokens expired or misconfigured.
- OAuth/OpenID Connect provider misalignment. |
| **Performance Degradation** | Slow response times, timeouts, or high latency during authentication/authorization. | - Slow cryptographic algorithms (e.g., legacy DES instead of AES).
- Excessive logging or validation overhead. |
| **Cryptographic Failures** | Decryption errors, HMAC mismatches, or SSL handshake failures. | - Key version mismatch (old keys still in use).
- Unsupported cipher suites (e.g., TLS 1.1 forced on TLS 1.2+ system). |
| **Compliance Alerts** | Security scanners flag deprecated protocols (e.g., SSLv3, SHA-1) or weak algorithms. | - Unpatched libraries or outdated dependencies.
- Missing crypto policy updates (e.g., Java’s `jce policy files`). |
| **Downtime or Crashes** | System crashes on restart or during migration windows. | - Broken session storage (e.g., Redis/MongoDB schema changes).
- race conditions in token refresh logic. |
| **Inconsistent User Roles/Permissions** | Users lose/gain unexpected access post-migration. | - RBAC/RBAC+ migration errors.
- Cache invalidation issues (e.g., Redis keys not updated). |

---

## **2. Common Issues and Fixes**

### **2.1 Authentication Failures**
#### **Issue: Password Hash Mismatch**
**Scenario:** After migrating from `PBKDF2` to `Argon2`, existing users cannot log in.
**Root Cause:** The old password storage doesn’t match the new hashing algorithm.
**Fix:**
```java
// Before: PBKDF2 (legacy)
String oldHash = PBKDF2.hash(password, salt, iterations);

// After: Argon2 (new)
String newHash = Argon2.hash(password, salt, params);
```
**Solution:**
- **Option 1:** Re-hash all existing passwords during migration (do this during low-traffic periods).
  ```python
  # Python example using bcrypt (Argon2 alternative)
  for user in db.users:
      user.password = bcrypt.hashpw(user.password, bcrypt.gensalt())
  db.users.save()
  ```
- **Option 2:** Dual-mode authentication (temporarily support both hashes).
  ```java
  if (PBKDF2.verify(userInput, storedHash)) {
      // Legacy flow
  } else if (Argon2.verify(userInput, storedHash)) {
      // New flow
  }
  ```

#### **Issue: Session Token Expiration or Format Change**
**Scenario:** Users lose sessions after migrating from JWT to a short-lived token system.
**Root Cause:** Token lifetimes or signing algorithms changed.
**Fix:**
- Extend the migration window to allow both old and new token types.
  ```javascript
  // Express.js middleware: Support old JWT + new tokens
  app.use((req, res, next) => {
      try {
          const token = req.headers.authorization?.split(' ')[1];
          if (token) {
              // Try old JWT first
              jwt.verify(token, OLD_JWT_SECRET);
          } else if (newToken.verify(token)) { // Custom new token class
              // Proceed with new logic
          } else {
              res.status(401).send('Invalid token');
          }
      }
  });
  ```

---

### **2.2 Cryptographic Failures**
#### **Issue: TLS/SSL Handshake Failures**
**Scenario:** Clients (browsers, APIs) cannot connect to the server.
**Root Cause:** Server enforces TLS 1.2+, but clients (e.g., legacy systems) only support TLS 1.1.
**Fix:**
- **Short-term:** Allow TLS 1.2+ and TLS 1.1 (if critical legacy clients exist).
  ```nginx
  ssl_protocols TLSv1.1 TLSv1.2 TLSv1.3;
  ```
- **Long-term:** Phase out TLS 1.1 and upgrade clients.
- **Debugging:**
  ```bash
  # Test with OpenSSL
  openssl s_client -connect yourserver:443 -tls1_2
  ```

#### **Issue: HMAC/Signature Failures**
**Scenario:** API requests fail with "Invalid signature" errors.
**Root Cause:** Secret key or algorithm mismatch (e.g., HMAC-SHA1 → HMAC-SHA256).
**Fix:**
- Ensure all clients are using the new key:
  ```python
  # Old: HMAC-SHA1
  import hmac
  import hashlib
  old_signature = hmac.new(OLD_SECRET, msg, hashlib.sha1).digest()

  # New: HMAC-SHA256
  new_signature = hmac.new(NEW_SECRET, msg, hashlib.sha256).digest()
  ```
- **Migration Strategy:** Require clients to update their keys via a secure channel.

---

### **2.3 Compliance and Scanning Issues**
#### **Issue: Deprecated Algorithms in Use**
**Scenario:** Vulnerability scanners flag SHA-1, RC4, or DES.
**Root Cause:** Libraries default to insecure algorithms.
**Fix:**
- **Java:** Update `local_policy.jar` and `US_export_policy.jar` to restrict weak ciphers.
- **Node.js:** Enable `TLS_MIN_VERSION=1.2` in environment variables.
- **Python:** Use `ssl.TLSVersion.TLSv1_2` in `ssl.SSLContext`.

---

## **3. Debugging Tools and Techniques**
### **3.1 Logging and Monitoring**
- **Enable detailed auth logs:**
  ```bash
  # Example: Enable JWT decoding in logs (Node.js)
  const jwt = require('jsonwebtoken');
  app.use((req, res, next) => {
      try {
          const token = req.headers.authorization?.split(' ')[1];
          const decoded = jwt.verify(token, process.env.JWT_SECRET);
          console.log('Decoded JWT:', decoded);
          next();
      } catch (err) {
          console.error('JWT Error:', err);
          next();
      }
  });
  ```
- **Use APM tools (New Relic, Datadog):** Track latency spikes during migration.

### **3.2 Network Debugging**
- **Wireshark/tcpdump:** Inspect TLS handshakes.
  ```bash
  tcpdump -i any -w capture.pcap port 443
  ```
- **cURL for API debug:**
  ```bash
  curl -v -H "Authorization: Bearer <token>" https://api.example.com/health
  ```

### **3.3 Cryptographic Debugging**
- **OpenSSL for certificate inspection:**
  ```bash
  openssl x509 -text -in server.crt
  ```
- **Check Java crypto policy:**
  ```bash
  java -version
  keytool -list -keystore $JAVA_HOME/lib/security/cacerts
  ```

### **3.4 Database/Session Debugging**
- **Verify session storage:**
  ```sql
  -- Check for orphaned sessions (Redis example)
  KEYS "*:session:*";
  ```
- **Compare user data pre/post-migration:**
  ```python
  # Sample: Verify password hashes match
  assert bcrypt.checkpw(old_password, db_user.password)
  ```

---

## **4. Prevention Strategies**
### **4.1 Pre-Migration Checklist**
1. **Back up all secrets and keys** (use tools like HashiCorp Vault).
2. **Test in staging:** Ensure the new system works with a subset of users.
3. **Monitor for drift:** Use CI/CD pipelines to detect changes in dependencies.

### **4.2 Rollback Plan**
- **Dual-write during migration:** Keep old and new systems running in parallel.
- **Feature flags:** Enable/disable new security controls via flags.
  ```java
  if (featureFlag.isEnabled("new-auth")) {
      // New auth logic
  } else {
      // Fallback to old auth
  }
  ```

### **4.3 Post-Migration**
1. **Audit logs**: Validate no unauthorized access occurred during migration.
2. **Deprecate old systems:** Gradually phase out legacy protocols.
3. **Rotate secrets**: After full migration, revoke old keys/certificates.

---

## **5. Final Checklist for a Smooth Migration**
| **Task** | **Status** |
|----------|-----------|
| ✅ All user passwords re-hashed (if applicable) | |
| ✅ Session storage migrated or dual-writen | |
| ✅ TLS/SSL configured for minimum TLS 1.2+ | |
| ✅ Deprecated algorithms disabled in libs | |
| ✅ Backups verified | |
| ✅ Rollback plan tested | |
| ✅ Monitoring alerts configured | |

---
**Key Takeaway:** Security migrations are risky but manageable with gradual rollouts, dual-support phases, and rigorous testing. Always validate changes in staging before going live.