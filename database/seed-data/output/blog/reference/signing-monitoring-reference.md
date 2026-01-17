# **[Pattern] Signing Monitoring Reference Guide**

---

## **Overview**
The **Signing Monitoring** pattern enables centralized tracking, validation, and alerting for cryptographic signing operations across distributed systems, APIs, and services. This pattern ensures:
- **Authenticity verification** of signed payloads/data.
- **Integrity detection** of tampered messages.
- **Operational visibility** into signing activity (e.g., delays, failures).
- **Compliance adherence** for audit trails and security policies.

Signing Monitoring applies to:
- OAuth tokens (JWT, OIDC)
- API payloads (REST/GraphQL)
- TLS certificates
- IoT device authentication
- Blockchain transactions
- Custom application signatures

It distinguishes between *signing* (authenticating via cryptographic keys) and *monitoring* (observing signing events). Key components include:
1. **Signing Infrastructure**: Key management (HSMs, KMS), signing libraries (e.g., OpenSSL, SignTool).
2. **Monitoring Agents**: Lightweight probes collecting signing metadata (timestamps, duration, errors).
3. **Centralized Dashboard**: Aggregates events for analysis (e.g., Prometheus + Grafana).
4. **Alert Thresholds**: Triggers on anomalies (e.g., failed signatures, latency spikes).

---

## **Implementation Details**

### **Key Concepts**
| Concept               | Description                                                                                                                                                                                                 |
|-----------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Signing Event**     | A logged instance of a signing operation, including metadata (e.g., key ID, payload hash, status).                                                                                                         |
| **Certification Path**| Chain of trust proving a public key’s validity (e.g., from CA to leaf certificate). Used for validating signatures.                                                                                     |
| **Signature Validation** | Process of verifying a signed payload using the public key of the signing entity. Fails if key revoked or expired.                                                                                     |
| **Key Rotation Policy**   | Schedule for replacing cryptographic keys (e.g., quarterly) to mitigate long-term compromise risks.                                                                                                           |
| **Anomaly Detection**      | Identifies irregularities (e.g., duplicate signatures, unexpected signing frequency) via statistical thresholds or ML models.                                                                             |
| **Audit Log**           | Immutable record of signing events for compliance (e.g., PCI DSS, GDPR). Typically stored in SIEM tools like Splunk or AWS CloudTrail.                                                                    |
| **Key Hierarchy**          | Hierarchy of keys (e.g., root CA → intermediate → end-entity) to manage trust boundaries.                                                                                                               |

---

### **Schema Reference**
Below are JSON schemas for core entities in Signing Monitoring.

#### **1. SigningEvent**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SigningEvent",
  "type": "object",
  "properties": {
    "event_id": { "type": "string", "format": "uuid" },
    "timestamp": { "type": "string", "format": "date-time" },
    "signer": {
      "type": "object",
      "properties": {
        "entity_id": { "type": "string" },
        "key_id": { "type": "string" },
        "public_key": { "type": "string" },
        "key_type": { "enum": ["RSA", "ECDSA", "EdDSA", "HMAC"] }
      },
      "required": ["entity_id", "key_id"]
    },
    "payload_hash": { "type": "string", "format": "uuid" },
    "signature": { "type": "string", "format": "base64url" },
    "status": { "enum": ["SUCCESS", "FAILURE", "PENDING"] },
    "duration_ms": { "type": "integer" },
    "error": { "type": "string" },
    "certificate": { "type": "string", "format": "base64url" }, // PEM or DER
    "cert_chain": { "type": "array", "items": { "type": "string", "format": "base64url" } }
  },
  "required": ["event_id", "timestamp", "signer", "payload_hash", "status"]
}
```

#### **2. KeyRotationPolicy**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "KeyRotationPolicy",
  "type": "object",
  "properties": {
    "key_type": { "enum": ["RSA", "ECDSA", "EdDSA"] },
    "rotation_interval": { "type": "string", "format": "duration" }, // e.g., "P90D"
    "window_start": { "type": "string", "format": "date-time" },
    "max_validity_days": { "type": "integer" },
    "revocation_notice": { "type": "integer" }, // Days before revocation
    "algorithms": { "type": ["string", "array"], "items": { "type": "string" } } // e.g., ["RSASSA-PKCS1-v1_5"]
  },
  "required": ["key_type", "rotation_interval"]
}
```

#### **3. AlertRule**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "AlertRule",
  "type": "object",
  "properties": {
    "rule_id": { "type": "string" },
    "condition": {
      "type": "object",
      "properties": {
        "metric": { "type": "string" }, // e.g., "signature_success_rate", "key_revocation"
        "operator": { "enum": [">=", "<=", "!=", "IN"] },
        "threshold": { "type": ["number", "string"] },
        "window_ms": { "type": "integer" }
      },
      "required": ["metric", "operator"]
    },
    "channels": { "type": ["string", "array"], "items": { "type": "string" } }, // e.g., ["email", "Slack", "PagerDuty"]
    "severity": { "enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW"] }
  },
  "required": ["rule_id", "condition", "channels"]
}
```

---

## **Query Examples**
Use the following queries to analyze signing data in tools like **Prometheus**, **Elasticsearch**, or **SQL databases**.

### **1. PromQL (Prometheus)**
- **Failed Signatures Rate**:
  `rate(signing_events{status="FAILURE"}[5m]) / rate(signing_events[5m])`
- **Key Rotation Compliance**:
  `sum by(key_id) (signing_events{status="SUCCESS"}) > key_rotation_policy{key_type="RSA"}.rotation_interval`
- **Certificate Expiry Alert**:
  `max by(certificate)(signing_events{status="SUCCESS"}.certificate_valid_until) - now() < 7d`

### **2. Elasticsearch (Kibana)**
- **Signatures by Entity**:
  ```json
  GET signing_events/_search
  {
    "aggs": {
      "entities": { "terms": { "field": "signer.entity_id" } }
    }
  }
  ```
- **Slow Signing Operations**:
  ```json
  GET signing_events/_search
  {
    "query": { "range": { "duration_ms": { "gt": 1000 } } },
    "aggs": {
      "top_key_ids": { "terms": { "field": "signer.key_id" } }
    }
  }
  ```

### **3. SQL (PostgreSQL)**
```sql
-- Signatures with invalid certificates
WITH valid_certs AS (
  SELECT certificate_id
  FROM certificates
  WHERE NOT EXPIRED AND status = 'ACTIVE'
)
SELECT se.*
FROM signing_events se
JOIN keys k ON se.key_id = k.key_id
JOIN valid_certs vc ON k.certificate_id = vc.certificate_id
WHERE se.status = 'FAILURE';
```

---

## **Related Patterns**
| Pattern                     | Description                                                                                                                                                                                                                       | When to Use                                                                                                                                                                 |
|-----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Key Management System (KMS)** | Centralized storage/retrieval of cryptographic keys (e.g., AWS KMS, HashiCorp Vault).                                                                                                                               | When keys are stored in a secure, accessible repository with lifecycle management.                                                                                     |
| **Distributed Tracing**     | Correlates signing events with application requests (e.g., OpenTelemetry).                                                                                                                                             | When diagnosing latency spikes across microservices.                                                                                                                |
| **Rate Limiting**           | Throttles signing requests to prevent abuse (e.g., Redis + Token Bucket).                                                                                                                                               | When mitigating brute-force attacks on signing operations.                                                                                                           |
| **Certificate Transparency**| Logs certificate issuance to detect fraud (e.g., Google CT).                                                                                                                                                           | When validating external public keys (e.g., TLS certificates).                                                                                                      |
| **Policy as Code (PaC)**    | Defines signing rules in code (e.g., Open Policy Agent).                                                                                                                                                               | When enforcing dynamic signing policies (e.g., least-privilege key access).                                                                                           |
| **Observability Pipeline**  | Combines metrics, logs, and traces (e.g., Fluentd → Loki → Grafana).                                                                                                                                                      | When aggregating signing data with other system telemetry.                                                                                                           |
| **Cryptographic Agility**   | Supports multiple algorithms/key types (e.g., RSA + ECDSA).                                                                                                                                                               | When future-proofing against algorithm deprecation (e.g., SHA-1 → SHA-256).                                                                                               |

---

## **Best Practices**
1. **Minimize Key Exposure**:
   - Use **hardware security modules (HSMs)** for private keys.
   - Restrict key access via **attribute-based access control (ABAC)**.

2. **Key Rotation**:
   - Rotate keys **automatically** using tools like **AWS Certificate Manager (ACM)** or **Let’s Encrypt**.
   - Pre-warm new keys to avoid **downtime** during rotation.

3. **Validation**:
   - Validate signatures **client-side** (e.g., JWT libraries) and **server-side** for defense-in-depth.
   - Reject signatures from **revoked or expired** keys.

4. **Auditability**:
   - Retain signing logs for **compliance** (e.g., GDPR’s "right to erasure" may require log purging).
   - Use **immutable storage** (e.g., S3 Object Lock) for audit trails.

5. **Performance**:
   - Cache **public keys** to reduce latency (validate cache freshness).
   - Batch validation for **high-throughput** systems (e.g., IoT devices).

6. **Alerting**:
   - Set alerts for:
     - **Key revocation** (e.g., CRL/DV updates).
     - **Anomalous frequency** (e.g., 10x baseline signing rate).
     - **Certificate expiry** (e.g., 30 days before expiration).

7. **Security**:
   - Use **TLS 1.2+** for key transport (avoid SSLv3/DTLS).
   - Rotate **shared secrets** (e.g., HMAC keys) every **90 days**.

---

## **Example Implementation (Python)**
```python
import time
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
import json
from prometheus_client import start_http_server, Counter

# Metrics
SIGNING_SUCCESS = Counter(
    'signing_events_total',
    'Total signing events',
    ['status', 'key_type', 'entity_id']
)

def sign_payload(payload_bytes, private_key, key_type="RSA"):
    start_time = time.time()
    try:
        if key_type == "RSA":
            signature = private_key.sign(
                payload_bytes,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
        else:  # ECDSA
            signature = private_key.sign(payload_bytes, hashes.ECDSA(hashes.SHA256()))
        SIGNING_SUCCESS.labels(
            status="SUCCESS",
            key_type=key_type,
            entity_id=private_key._key._curve.name
        ).inc()
        return signature
    except Exception as e:
        SIGNING_SUCCESS.labels(
            status="FAILURE",
            key_type=key_type,
            entity_id=private_key._key._curve.name
        ).inc()
        raise RuntimeError(f"Signing failed: {str(e)}") from e

# Start Prometheus metrics server
start_http_server(8000)

# Example usage
private_key = load_private_key_from_pem(b"-----BEGIN RSA PRIVATE KEY-----\n...")
payload = b"Hello, world!"
signature = sign_payload(payload, private_key)
print(f"Signature: {signature.hex()}")
```

---
**References**:
- [RFC 7515 (JWT)](https://tools.ietf.org/html/rfc7515)
- [NIST SP 800-57 (Key Management)](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-57.1r5.pdf)
- [Prometheus Documentation](https://prometheus.io/docs/introduction/overview/)