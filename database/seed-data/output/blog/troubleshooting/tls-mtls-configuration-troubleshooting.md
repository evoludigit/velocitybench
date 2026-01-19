---
# **Debugging TLS/mTLS Configuration: A Troubleshooting Guide**
*For: Backend Engineers*
*Focus: Securing Service-to-Service Communication with TLS/mTLS & Cert Rotation*

---
## **1. Symptom Checklist**
Before diving into debugging, confirm the issue by checking:

| **Symptom**                     | **Question**                                                                 |
|----------------------------------|------------------------------------------------------------------------------|
| GraphQL/API calls in plaintext   | Does `curl -v` or browser DevTools show `HTTP/1.1`?                           |
| Unencrypted service traffic      | Check network traffic (Wireshark, `strace`) for unencrypted payloads.         |
| Manual cert rotation failures    | Are new certs deployed to all services? Check logs for expired cert errors. |
| Cert expiry outages             | Does the system fail with `SSL_ERROR_BAD_CERT_DOMAIN`?                      |
| Service-to-service failures      | Are mTLS handshakes timed out? Check with `openssl s_client -connect`.       |

---

## **2. Common Issues & Fixes**

### **2.1 Plaintext Traffic (No TLS)**
#### **Symptom:**
GraphQL/API endpoints expose data in plaintext.
**Diagnosis:**
```sh
curl -v https://your-api.example.com
```
*Look for:*
- `HTTP/1.1 200` (no cipher suite negotiation)
- Missing `X-Forwarded-Proto: https` headers in logs.

#### **Fix:**
**A. Ensure HTTPS Listeners**
Update your server config (e.g., **Express, Fastify, Nginx**).
**Example (Express):**
```javascript
const express = require('express');
const fs = require('fs');
const https = require('https');

const app = express();
const options = {
  key: fs.readFileSync('/path/to/key.pem'),
  cert: fs.readFileSync('/path/to/cert.pem')
};

https.createServer(options, app).listen(443);
```

**B. Redirect HTTP to HTTPS**
**Nginx Config:**
```nginx
server {
    listen 80;
    server_name your-api.example.com;
    return 301 https://$host$request_uri;
}
```

---

### **2.2 Missing mTLS Between Services**
#### **Symptom:**
Service A calls Service B, but traffic is unencrypted.
**Diagnosis:**
- Check `netstat -tulnp` for ports used internally (should use **443** or custom TLS ports).
- Logs may show `SSL_ERROR_NO_CYBERSUITE_MATCH`.

#### **Fix:**
**A. Mutual TLS Setup**
Ensure both services:
1. Have **client certs** (for mTLS).
2. Verify **CA-signed certs** (use a private PKI or service like **Let’s Encrypt**).

**Example (Node.js mTLS Client):**
```javascript
const https = require('https');

const options = {
  hostname: 'service-b.example.com',
  port: 443,
  rejectUnauthorized: true, // Enforce mTLS
  ca: fs.readFileSync('/path/to/ca.crt'),
  cert: fs.readFileSync('/path/to/client.crt'),
  key: fs.readFileSync('/path/to/client.key')
};

https.get(options, (res) => { ... });
```

**B. Validate Cert Trust**
Ensure:
- Client certs are **signed by a trusted CA**.
- Server certs **match hostnames** (no wildcard mismatches).

---

### **2.3 Manual Certificate Rotation Breaks Services**
#### **Symptom:**
After cert renewal, services fail with `SSL_ERROR_EXPIRED`.
**Diagnosis:**
- Check `/etc/ssl/certs` or Docker volume mounts for stale certs.
- Logs: `error:10000054:SSL routines:OPENSSL_internal:CERTIFICATE_EXPIRED`.

#### **Fix:**
**A. Automate Rotation**
Use tools like **Certbot** (Let’s Encrypt) or **Vault by HashiCorp** for dynamic certs.
**Certbot Example:**
```sh
certbot renew --dry-run  # Test rotation
certbot renew --force-renewal  # Force update
```

**B. Docker/Kubernetes Certs**
Use **secrets** and **.ConfigMaps** for certs (auto-reloaded on rotation).
**K8s YAML:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: tls-certs
type: kubernetes.io/tls
data:
  tls.crt: <base64-encoded-cert>
  tls.key: <base64-encoded-key>
```

**C. Reload Services Gracefully**
- Use **liveness probes** in K8s:
  ```yaml
  livenessProbe:
    httpGet:
      path: /health
      scheme: HTTPS
  ```
- For non-K8s: Use **signal handlers** for rolling restarts.

---

### **2.4 Cert Expiry Causes Outages**
#### **Symptom:**
System-wide failure when certs expire (e.g., 503 errors).
**Fix:**
**A. Alert on Expiry**
Set up a **Prometheus alert**:
```yaml
- alert: CertificateExpiringSoon
  expr: cert_expiry_seconds < 3600
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Cert expiry in {{ $labels.host }} ({{ $value }}s left)"
```

**B. Fail Closed (Not Open)**
Configure clients to **reject expired certs** (default `rejectUnauthorized: true`).
**Example (Docker):**
```yaml
env:
  - name: NODE_EXTRA_CA_CERTS
    value: "/etc/ssl/certs/ca-certificates.crt"
```

---

## **3. Debugging Tools & Techniques**

| **Tool**               | **Use Case**                                  | **Example Command**                     |
|------------------------|---------------------------------------------|------------------------------------------|
| `openssl s_client`     | Test TLS handshake                          | `openssl s_client -connect api:443 -showcerts` |
| `strace`              | Trace syscalls for TLS errors               | `strace -e trace=network node app.js`   |
| **Wireshark**         | Inspect encrypted traffic (if SSL keys)     | Filter `tls.handshake.type == 1`         |
| **Postman/curl -v**   | Verify TLS/HTTPS manually                   | `curl -v --cacert ca.crt https://api`    |
| **Prometheus + Grafana** | Monitor cert expiry metrics                | Query `cert_expiry_seconds`             |
| **Vault HCL**         | Dynamic certs via secrets engine            | `vault write -field=certificate pki_int/issue/internal-api` |

---

## **4. Prevention Strategies** *(Checklist for Ops)**
| **Action**                          | **Implementation**                                                                 |
|-------------------------------------|------------------------------------------------------------------------------------|
| **Enforce TLS everywhere**          | Use **TLS 1.2+** (disable SSLv3, TLS 1.0/1.1).                                      |
| **Automate cert rotation**          | Integrate **Certbot + Ansible/Terraform** for renewals.                             |
| **Use mTLS for service mesh**       | Deploy **Istio, Linkerd, or Nginx sidecars** for internal mTLS.                    |
| **Fail closed by default**          | Set `rejectUnauthorized: true` in clients.                                        |
| **Monitor cert expiry**             | Alert 30+ days before expiry (Slack/PagerDuty).                                   |
| **Audit TLS configs**               | Run `ssllabs.com` scans weekly.                                                    |
| **Docker/K8s cert secrets**         | Store certs in secrets, not volumes.                                               |
| **Zero-trust for internal services**| Use **short-lived tokens + mTLS** (e.g., **OAuth2 with JWT**).                     |

---
## **Final Checklist for Production**
1. **All endpoints** use HTTPS/mTLS (no HTTP).
2. **Certs** are auto-renewed (test with `--dry-run`).
3. **Clients** reject expired/untrusted certs (`rejectUnauthorized: true`).
4. **Alerts** fire 30 days before expiry.
5. **Traffic** is inspected for unencrypted payloads (Wireshark, logs).

---
**Time to Resolve:** 15–60 mins (symptom → fix) if tools are pre-configured.
**Pro Tip:** Start with `openssl s_client`—it solves 80% of TLS issues.