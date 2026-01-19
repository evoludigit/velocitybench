**[Pattern] TLS/mTLS Configuration Reference Guide**

---

### **Overview**
FraiseQL enables secure communication using **Transport Layer Security (TLS)** for client connections and **Mutual TLS (mTLS)** for service-to-service authentication. TLS ensures encrypted data in transit, while mTLS enforces bidirectional certificate validation between services, preventing unauthorized access.

Key features include:
- **Automatic certificate rotation** (via **Let’s Encrypt** or custom ACME/CAs).
- **Service mesh integration** (e.g., Istio, Linkerd) for fine-grained traffic control.
- **Certificate validation** with custom policies (e.g., expiry checks, issuer verification).
- **FraiseQL-native configuration** via SQL queries (no external CLI/agent dependency).

This guide covers setup, schema references, and query examples for TLS/mTLS.

---

## **1. Schema Reference**

### **1.1 Core Tables**
| Table | Description | Key Fields |
|-------|-------------|------------|
| `tls_config` | Global TLS settings (e.g., CA bundle, default cipher suite). | `id`, `enabled`, `default_cipher_suite`, `ca_bundle` |
| `tls_peer` | Service identities (for mTLS). | `id`, `service_name`, `certificate_id`, `key_id`, `validation_mode` |
| `tls_certificate` | TLS certificates (auto-rotated or manually uploaded). | `id`, `certificate_data`, `private_key_data`, `issuer`, `expiry_date`, `auto_rotate` |
| `tls_acme_account` | ACME accounts (e.g., Let’s Encrypt) for automated certs. | `id`, `acme_server`, `email`, `registration_token`, `private_key_data` |
| `tls_validation_policy` | Rules for certificate validation (e.g., expiry, issuer). | `id`, `name`, `max_expiry_days`, `required_issuers` |

---

### **1.2 Relationships**
- **`tls_peer` → `tls_certificate`**: A service peer references its certificate.
- **`tls_certificate` → `tls_acme_account`**: Auto-rotation relies on an ACME account.
- **`tls_config` → `tls_validation_policy`**: Global config can enforce validation rules.

---

## **2. Key Query Patterns**

### **2.1 Configure TLS Globally**
Apply TLS settings to all client connections:
```sql
-- Enable TLS, set default cipher suite, and load a CA bundle
UPDATE tls_config
SET
    enabled = true,
    default_cipher_suite = 'TLS_AES_256_GCM_SHA384',
    ca_bundle = (SELECT certificate_data FROM tls_certificate WHERE id = 1)
WHERE id = 1;
```

---

### **2.2 Set Up mTLS for a Service**
Define a service for mTLS with a certificate:
```sql
-- Register a service peer with a certificate
INSERT INTO tls_peer (service_name, certificate_id, key_id, validation_mode)
VALUES ('order-service', 2, 2, 'STRICT');  -- 'STRICT' enforces peer cert validation
```

---

### **2.3 Auto-Rotate Certificates via ACME**
Link an ACME account to a certificate for auto-rotation:
```sql
-- Enable auto-rotation for a certificate
UPDATE tls_certificate
SET auto_rotate = true,
    acme_account_id = 1  -- Must exist in tls_acme_account
WHERE id = 3;
```

---

### **2.4 Enforce Certificate Validation**
Define a validation policy (e.g., require expiry < 14 days):
```sql
-- Create a validation policy
INSERT INTO tls_validation_policy (name, max_expiry_days, required_issuers)
VALUES ('short-expiry-policy', 14, '[{"issuer": "Let\'s Encrypt"}]');
```

Apply it globally:
```sql
UPDATE tls_config
SET default_validation_policy = 1  -- ID from tls_validation_policy
WHERE id = 1;
```

---

### **2.5 Verify TLS Status**
Check active TLS peers:
```sql
SELECT p.service_name, c.issuer, c.expiry_date
FROM tls_peer p
JOIN tls_certificate c ON p.certificate_id = c.id
WHERE p.validation_mode = 'STRICT';
```

Check auto-rotation status:
```sql
SELECT c.id, c.auto_rotate, aa.acme_server
FROM tls_certificate c
LEFT JOIN tls_acme_account aa ON c.acme_account_id = aa.id
WHERE c.auto_rotate = true;
```

---

## **3. Service Mesh Integration**
FraiseQL integrates with **Istio/Linkerd** via sidecar injection:
```sql
-- Enable TLS sidecar for a Kubernetes service (via Istio)
INSERT INTO tls_peer (service_name, mesh_sidecar_enabled)
VALUES ('payment-service', true);
```
Sidecar configuration is auto-generated from `tls_peer` data (e.g., `mtls` in Istio’s `PeerAuthentication`).

---

## **4. Certificate Management**
### **4.1 Manual Upload**
```sql
-- Upload a raw certificate and key
INSERT INTO tls_certificate (certificate_data, private_key_data)
VALUES (
    '-----BEGIN CERTIFICATE-----...',
    '-----BEGIN PRIVATE KEY-----...'
);
```

### **4.2 ACME Provisioning**
```sql
-- Register an ACME account (e.g., Let’s Encrypt)
INSERT INTO tls_acme_account (acme_server, email, registration_token)
VALUES (
    'https://acme-v02.api.letsencrypt.org/directory',
    'admin@example.com',
    'generated_token_here'
);
```

---

## **5. Troubleshooting**
| Issue | Query/Action |
|-------|-------------|
| **Certificate expired** | Run `ANALYZE_TLS_CERTIFICATE(3)` to check expiry. |
| **Peer validation failed** | Verify `validation_mode = 'STRICT'` for the peer. |
| **Auto-rotation disabled** | Ensure `auto_rotate = true` and `acme_account_id` is set. |
| **Sidecar misconfig** | Check `mesh_sidecar_enabled` in `tls_peer`. |

---

## **6. Related Patterns**
1. **[Service Mesh Integration]**: Extend TLS to Istio/Linkerd for traffic control.
2. **[Certificate Auto-Rotation]**: Focus on ACME/Let’s Encrypt workflows.
3. **[JWT Validation]**: Combine with mTLS for token-based auth.
4. **[Kubernetes Ingress TLS]**: Configure TLS for HTTP routes via `tls_peers`.

---
**Note**: All queries require **administrative privileges** (e.g., `admin` role). For production, validate certificates post-upload with:
```sql
SELECT VALIDATE_TLS_CERTIFICATE(1);  -- Returns true/false
```