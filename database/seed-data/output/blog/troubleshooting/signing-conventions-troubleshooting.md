# **Debugging Signing Conventions: A Troubleshooting Guide**

## **Overview**
Signing conventions (e.g., JWT, OAuth, API key rotation, certificate signing, or cryptographic sign-offs) ensure data integrity, authentication, and authorization in distributed systems. Misconfigurations, expiration issues, or improper key handling can lead to security breaches, API failures, or authentication errors.

This guide provides a structured approach to diagnosing and fixing common issues related to signing conventions.

---

## **1. Symptom Checklist**
Before diving into debugging, verify the following symptoms:

### **Authentication & Authorization Failures**
- **[ ]** `401 Unauthorized` errors when accessing protected endpoints.
- **[ ]** `403 Forbidden` despite valid credentials.
- **[ ]** JWT/OAuth tokens failing validation.
- **[ ]** Session expiration without proper warning.

### **System & Performance Issues**
- **[ ]** High latency in token validation or signing processes.
- **[ ]** Unexpected timeouts during authentication flows.
- **[ ]** Logs showing `HMAC mismatch`, `RSA verification failed`, or `invalid signature`.

### **Key & Certificate-Related Errors**
- **[ ]** `InvalidKeySpecException` or `IOError` when loading keys.
- **[ ]** Keys expiring silently (e.g., RSA private keys, X.509 certificates).
- **[ ]** Certificate revocation checks failing.
- **[ ]** Multiple keys in rotation not handled gracefully.

### **Logging & Observability**
- **[ ]** Lack of signing-related audit logs.
- **[ ]** No visibility into failed signature validations.
- **[ ]** Inconsistent error messages across microservices.

---

## **2. Common Issues and Fixes**

### **Issue 1: Invalid or Expired Tokens (JWT/OAuth)**
**Symptoms:**
- `jwt_expired`, `invalid_token`, or `signature_mismatch` errors.
- Users report intermittent login failures.

**Root Causes:**
- Token expiration handling not implemented.
- Clock skew between client and server.
- Incorrect algorithm selection (e.g., using `HS256` instead of `RS256`).

**Debugging Steps:**
1. **Check Token Payload:**
   ```bash
   jwt_decode --validate http://example.com/auth/callback?token=...
   ```
   - Verify:
     - `exp` (expiration time) is not in the past.
     - `iat` (issued at) is within a reasonable window (account for clock skew).
     - `alg` (algorithm) matches the expected one (e.g., `RS256`).

2. **Log Token Signing Details:**
   ```java
   // Example in Java (Spring Security)
   @Override
   protected void doFilterInternal(
       HttpServletRequest request,
       HttpServletResponse response,
       FilterChain filterChain
   ) throws ServletException, IOException {
       try {
           JwtValidator.validate(token); // Log failure reason
       } catch (JwtException e) {
           log.error("Token validation failed: " + e.getMessage());
           response.sendError(HttpStatus.UNAUTHORIZED.value());
           return;
       }
       filterChain.doFilter(request, response);
   }
   ```

3. **Fix Clock Skew:**
   - Ensure NTP is synchronized across all servers.
   - Implement a **token leeway** (e.g., ±5 minutes for JWT `exp`).

4. **Algorithm Consistency:**
   - Replace `HS256` with `RS256` if using asymmetric keys.
   - Update all clients to support the new algorithm.

---

### **Issue 2: Key Rotation Not Handled**
**Symptoms:**
- Some requests succeed, others fail after key rotation.
- Logs show `InvalidKey` or `RSA_VERIFICATION_ERROR`.

**Root Causes:**
- Rotated keys not added to a **trusted key store**.
- Caching mechanisms (e.g., Redis, databases) not invalidated.
- Clients not updated to use the new key.

**Debugging Steps:**
1. **Check Active Keys:**
   - Verify the **trusted key store** (e.g., Vault, AWS KMS, or local `.pem` files).
   - Example (Python with `cryptography`):
     ```python
     from cryptography.hazmat.primitives import serialization
     from cryptography.hazmat.primitives.asymmetric import padding, rsa

     # Load old key (should still work for a grace period)
     with open("old-private.pem") as f:
         old_key = serialization.load_pem_private_key(
             f.read(),
             password=None,
         )

     # Load new key
     with open("new-private.pem") as f:
         new_key = serialization.load_pem_private_key(
             f.read(),
             password=None,
         )
     ```

2. **Test Key Validation:**
   ```bash
   # Verify a signed token with the new key
   openssl rsautl -verify -in token.signed -inkey new-public.pem -pubin
   ```

3. **Implement Key Cache Invalidation:**
   - Use a **tiered key store** (e.g., short-lived in-memory + long-term in KMS).
   - Example (Redis-based key rotation):
     ```python
     import redis

     r = redis.Redis(host='redis-server')
     r.zadd("trusted_keys", {new_key_fingerprint: "1"})
     r.zrem("trusted_keys", old_key_fingerprint)  # After safe period
     ```

4. **Grace Period Handling:**
   - Allow both keys to sign/verify for **1 hour** after rotation.
   - Log warnings when using the **old key** (e.g., for auditing).

---

### **Issue 3: Missing or Incorrect Signing Header**
**Symptoms:**
- `401 Unauthorized` with no clear error message.
- API requests failing silently.

**Root Causes:**
- Missing `Authorization: Bearer <token>` header.
- Incorrect **signing algorithm** in JWT header (e.g., `alg: "HS256"` but key is RSA).
- Headers tampered with (e.g., by proxies like Nginx).

**Debugging Steps:**
1. **Inspect Request Headers:**
   ```bash
   curl -v -H "Authorization: Bearer <token>" http://example.com/api
   ```
   - Verify the `Authorization` header is present.
   - Check if proxies modify headers (e.g., Alb, Nginx).

2. **Validate JWT Header:**
   ```bash
   echo "<token>" | jq -r '.header.algo'
   ```
   - Should match the expected algorithm (e.g., `"RS256"`).

3. **Fix Header Handling:**
   - Ensure **all clients** send the `Authorization` header.
   - Configure proxies to **preserve headers**:
     ```nginx
     location / {
         proxy_pass http://backend;
         proxy_hide_header Authorization; # Only hide if needed
     }
     ```

---

### **Issue 4: Certificate Revocation Failures**
**Symptoms:**
- `ServerCertRevokedException` in logs.
- SSL handshake failures (`SSL_ERROR_SSL`).

**Root Causes:**
- Certificate not added to **OCSP/CRL** revocation list.
- OCSP stapling not configured.
- Local cache of revoked certificates stuck.

**Debugging Steps:**
1. **Check Certificate Status:**
   ```bash
   openssl ocsp -issuer <CA.crt> -cert <client.crt> -url http://ocsp.example.com
   ```
   - Should return `good` (not `revoked`).

2. **Verify OCSP Stapling:**
   ```bash
   openssl s_client -connect example.com:443 -status -verify 3
   ```
   - Look for `OCSP Response: good`.

3. **Update Certificates:**
   - Revoke the bad certificate via CA.
   - Force cache update:
     ```bash
     sudo rm -rf /etc/ssl/certs/cache/
     sudo service apache2 restart
     ```

---

### **Issue 5: Performance Bottlenecks in Signing**
**Symptoms:**
- Slow token generation/validation (e.g., >500ms).
- High CPU usage in signing-related processes.

**Root Causes:**
- Asymmetric crypto (RSA/ECC) is slower than symmetric (HMAC).
- Key caching not implemented.
- Heavy logging during signing.

**Debugging Steps:**
1. **Profile Signing Operations:**
   ```python
   import time
   start = time.time()
   token = jwt.encode(payload, key, 'RS256')
   print(f"Signing took: {time.time() - start:.2f}s")
   ```
   - If >100ms, consider:
     - Switching to `HS256` (faster, but less secure).
     - Using **libsodium** for faster crypto.

2. **Cache Signing Keys:**
   ```java
   // Spring Security example
   @Bean
   public JwtDecoder jwtDecoder() {
       return NimbusJwtDecoder.withPublicKey(
           loadPublicKeyFromKMS() // Load only once
       ).build();
   }
   ```

3. **Optimize Logging:**
   - Avoid logging sensitive data (e.g., full tokens).
   - Use structured logging (e.g., JSON):
     ```json
     {"event": "jwt_sign", "duration_ms": 42, "algorithm": "RS256"}
     ```

---

## **3. Debugging Tools and Techniques**

### **A. Logging & Monitoring**
- **Centralized Logging:** Use ELK, Datadog, or CloudWatch to correlate signing failures.
- **Audit Logs:** Log every JWT signing/validation (without sensitive data).
  ```log
  {"timestamp": "2024-05-20T12:00:00Z", "event": "jwt_generated", "user_id": "123", "algorithm": "RS256", "duration_ms": 32}
  ```
- **Error Tracking:** Tools like Sentry or Datadog Alerts for `signature_mismatch`.

### **B. Network & Proxy Debugging**
- **Mitmproxy:** Inspect raw HTTP requests/responses.
  ```bash
  mitmproxy --mode transparent
  ```
- **Wireshark/tcpdump:**
  ```bash
  tcpdump -i any port 443 -w jwt_traffic.pcap
  ```
  - Look for truncated or modified JWT payloads.

### **C. Automated Validation**
- **Unit Tests for Signing:**
  ```python
  def test_jwt_signing():
      payload = {"sub": "user123"}
      token = jwt.encode(payload, "SECRET_KEY", "HS256")
      assert jwt.decode(token, "SECRET_KEY", "HS256") == payload
  ```
- **Integration Tests for Key Rotation:**
  - Simulate key rotation and verify old/new tokens work.

### **D. Infrastructure Checks**
- **Key Storage Security:**
  - Ensure private keys are stored in **HSM** or **Vault**, not in code.
  - Rotate keys **before** they are compromised.
- **Clock Sync:**
  - Use **NTP** (e.g., `ntpd` or `chronyd`) across all servers.
  - Set maximum allowed clock skew in JWT libraries.

---

## **4. Prevention Strategies**

### **A. Design Principles**
1. **Least Privilege for Keys:**
   - Use **short-lived tokens** (e.g., 15-min JWTs).
   - Restrict key access (e.g., IAM policies for AWS KMS).

2. **Key Rotation Policy:**
   - Rotate RSA keys every **90 days**.
   - Use **OCSP stapling** to avoid revocation delays.

3. **Algorithm Future-Proofing:**
   - Avoid `SHA-1` or weak algorithms (e.g., `HS256` without HMAC-SHA256).
   - Plan for **ES256** (ECDSA) if RSA becomes slow.

### **B. Operational Practices**
1. **Automated Testing:**
   - Run **CI checks** for:
     - Token expiration handling.
     - Key rotation compatibility.
   - Example (GitHub Actions):
     ```yaml
     - name: Test JWT Signing
       run: python -m pytest tests/jwt_test.py
     ```

2. **Incident Response Plan:**
   - **Key compromise?** Revoke immediately and issue new tokens.
   - **Clock drift?** Pause services until fixed.

3. **Documentation:**
   - Maintain a **signing convention cheat sheet** (e.g., GitHub wiki).
   - Example:
     ```
     | Algorithm | Key Type | Max Lifetime | Rotation |
     |-----------|----------|--------------|----------|
     | RS256     | RSA 2048 | 15 min       | 90 days  |
     ```

### **C. Tooling & Automation**
- **Automated Key Rotation:**
  - Use **Terraform + AWS KMS** for scheduled key rotation.
  ```hcl
  resource "aws_kms_key" "api_key" {
    description = "API signing key"
    key_usage    = "SIGN_VERIFY"
    policy       = file("kms_policy.json")
    is_enabled   = true
    rotation_enabled = true
  }
  ```
- **Token Generation Libraries:**
  - Prefer **OAuth 2.1** or **OpenID Connect** libraries (e.g., `python-jose`, `spring-security-oauth2`).

---

## **5. Summary Checklist for Quick Resolution**
| **Issue**               | **Quick Fix**                          | **Long-Term Fix**                  |
|-------------------------|----------------------------------------|------------------------------------|
| Expired JWT             | Extend lease time (if possible)        | Implement short-lived tokens       |
| Key rotation failure    | Use both old/new keys (grace period)   | Automate key rotation              |
| Missing Authorization   | Check client headers                   | Enforce header validation          |
| OCSP revocation         | Manually update certs                  | OCSP stapling + auto-updates      |
| Slow signing            | Cache keys / use faster algo (HS256)   | Optimize crypto libraries         |

---
## **Final Notes**
- **Security First:** Always audit signing processes for leaks.
- **Test Rotations:** Simulate key rotation in staging before production.
- **Monitor:** Set up alerts for `signature_mismatch` errors.

By following this guide, you can quickly diagnose and resolve signing convention issues while preventing future incidents.