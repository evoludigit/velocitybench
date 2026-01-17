**[Pattern] Signing Observability Reference Guide**
*Version: 1.0*
*Last Updated: [Date]*

---

### **Overview**
The **Signing Observability** pattern enables monitoring, tracing, and debugging of cryptographic signing operations (e.g., JWT, digital signatures, TLS handshakes). By instrumenting signing workflows with observability signals (metrics, traces, logs), teams can:
- Detect anomalous signing behavior (e.g., rate limits, signature failures).
- Verify compliance with security policies (e.g., key rotation thresholds).
- Troubleshoot failures in distributed systems where signing occurs across microservices.

This guide covers schema standards (OpenTelemetry, OpenTraces), implementation details for common signing libraries, and query examples for observability platforms.

---

## **1. Key Concepts**
### **1.1 Observability Signals in Signing**
| **Signal Type** | **Purpose**                                                                 | **Example Metrics/Tags**                          |
|------------------|-----------------------------------------------------------------------------|--------------------------------------------------|
| **Metrics**      | Track success/failure rates, latency, and resource usage.                   | `signing.success_rate`, `signature_verify_latency` |
| **Traces**       | Correlate signing steps (key lookup, signing, verification) across services. | `operation.name="sign_jwt"`, `signing_key_id`    |
| **Logs**         | Debug low-level errors (e.g., invalid key format, HMAC failures).          | `error=invalid_signature`, `algorithm=ES256`     |

### **1.2 Core Components**
- **Signer Service**: Component generating signatures (e.g., JWT producer).
- **Verifier Service**: Component validating signatures (e.g., API gateway).
- **Key Management System (KMS)**: Stores/rotates cryptographic keys (e.g., AWS KMS, HashiCorp Vault).
- **Observability Backend**: Collects signals (e.g., Prometheus, OpenTelemetry Collector).

---

## **2. Schema Reference**
Use the following structures to instrument observability data. Adapt schemas based on your tech stack.

### **2.1 Metrics Schema**
| **Metric Name**               | **Type** | **Description**                                      | **Labels**                          |
|-------------------------------|----------|------------------------------------------------------|-------------------------------------|
| `signing.operations.total`    | Counter  | Total signing/verification attempts.                 | `operation=sign/verify`, `status=success/failure` |
| `signing.latency`             | Histogram| End-to-end latency (p99, p50).                       | `operation`, `algorithm`            |
| `kms.key_lookups`             | Counter  | Key fetch operations (Cache hits/misses).            | `cache_result=hit/miss`            |

**Example (Prometheus):**
```prometheus
signing_operations_total{operation="sign", status="success"} 1245
```

### **2.2 Traces Schema (OpenTelemetry)**
| **Span Attribute**            | **Description**                                      | **Example Value**                  |
|-------------------------------|------------------------------------------------------|------------------------------------|
| `sign.operation`              | Type of signing (JWT, TLS, S/MIME).                  | `"jwt_signature"`                  |
| `sign.algorithm`              | Crypto algorithm used (RS256, ES256, HMAC-SHA256).    | `"ES256"`                          |
| `sign.key_id`                 | Key identifier (e.g., KMS alias, JWK thumbprint).    | `"arn:aws:kms:us-east-1:..."`      |
| `sign.context.not_before`     | JWT/Signature validity timestamp.                    | `2023-12-01T00:00:00Z`             |

**Example Trace (OpenTelemetry JSON):**
```json
{
  "spans": [
    {
      "name": "sign_jwt",
      "attributes": {
        "sign.operation": "jwt_signature",
        "sign.algorithm": "ES256",
        "sign.key_id": "key-12345",
        "sign.context.not_before": "2023-12-01T00:00:00Z"
      }
    }
  ]
}
```

### **2.3 Logs Schema**
| **Log Field**       | **Description**                                      | **Example**                     |
|---------------------|------------------------------------------------------|---------------------------------|
| `sign.status`       | Outcome of signing/verification (`success`, `failure`). | `"failure"`                     |
| `sign.error`        | Human-readable error (if any).                       | `"invalid_key_format"`          |
| `sign.input_size`   | Size of data being signed (bytes).                   | `"1024"`                        |

**Example (JSON Lines):**
```json
{"sign": {"status": "failure", "error": "invalid_signature", "algorithm": "RS256"}, "timestamp": "2023-11-15T14:30:00Z"}
```

---

## **3. Implementation Details**
### **3.1 Instrumenting Signing Libraries**
#### **Python (PyJWT)**
```python
import jwt
from opentelemetry import trace

# Start a span for signing
with trace.get_tracer("signing").start_as_current_span("sign_jwt") as span:
    span.set_attribute("sign.operation", "jwt_signature")
    span.set_attribute("sign.algorithm", "HS256")
    try:
        token = jwt.encode(payload, "secret", algorithm="HS256")
        span.set_attribute("sign.status", "success")
    except Exception as e:
        span.set_attribute("sign.status", "failure")
        span.set_attribute("sign.error", str(e))
        raise
```

#### **Go (JWT Library)**
```go
package main

import (
    "github.com/golang-jwt/jwt/v5"
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/attribute"
    "go.opentemetry.io/otel/trace"
)

func SignJWT(token *jwt.Token) (*jwt.Token, error) {
    ctx, span := otel.Tracer("signing").Start(ctx, "sign_jwt")
    defer span.End()

    span.SetAttributes(
        attribute.String("sign.operation", "jwt_signature"),
        attribute.String("sign.algorithm", token.Method.KeyID()),
    )

    if _, err := token.SigningMethod.(*jwt.SigningMethodHMAC).Sign(token); err != nil {
        span.RecordError(err)
        span.SetAttributes(attribute.String("sign.status", "failure"))
        return nil, err
    }
    span.SetAttributes(attribute.String("sign.status", "success"))
    return token, nil
}
```

#### **Node.js (jsonwebtoken)**
```javascript
const jwt = require('jsonwebtoken');
const { trace } = require('@opentelemetry/api');

function signToken(payload, secret) {
  const span = trace.getSpan(trace.context.active());
  span.setAttribute('sign.operation', 'jwt_signature');
  span.setAttribute('sign.algorithm', 'HS256');

  try {
    const token = jwt.sign(payload, secret, { algorithm: 'HS256' });
    span.setAttribute('sign.status', 'success');
    return token;
  } catch (err) {
    span.setAttribute('sign.status', 'failure');
    span.recordException(err);
    throw err;
  }
}
```

### **3.2 Key Rotation Monitoring**
Track key rotation events to detect stale keys:
- **Metric**: `kms.key_rotation_attempts`
  - Labels: `operation=rotate`, `status=success/failure`.
- **Alert Rule**:
  ```promql
  rate(kms_key_rotation_attempts{status="failure"}[5m]) > 0
  ```

### **3.3 TLS Handshake Observability**
For TLS, instrument server/client handshakes:
```bash
# Example OpenTelemetry Collector config (tls_span_processor)
spans:
  - processor: tls_span_processor
    tls_span_processor:
      attributes:
        - key: "tls.handshake.start"
          value: "spans.attributes['tls.handshake.start']"
        - key: "tls.certificate.subject"
          value: "spans.attributes['tls.certificate.subject']"
```

---

## **4. Query Examples**
### **4.1 Detecting Signature Failures**
**PromQL (Alerting):**
```promql
# Failures > 1% of total operations
sum(rate(signing_operations_total{status="failure"}[5m]))
  /
sum(rate(signing_operations_total[5m])) > 0.01
```

**Grafana Explore (Traces):**
- Query: `trace("sign_jwt") | filter(sign.error="invalid_key_format")`
- Visualize: **Trace Overview** with `sign.algorithm` as color.

### **4.2 Key Usage Analytics**
**Loki Logs Query:**
```logql
# Keys not rotated in 30 days
 logs
   | json
   | where sign.operation = "jwt_signature"
   | where timestamp <= now() - 30d
   | count by sign.key_id
```

**Metric (Key Exposure Risk):**
```promql
# Keys with >1000 verifications but <10 rotations in 30d
sum(by(key) (kms_verifications_total[30d])) > 1000
and on(key) sum(rate(kms_rotations_total[30d])) < 10
```

### **4.3 Latency Percentiles**
**PromQL (SLO Monitoring):**
```promql
# P99 signing latency > 500ms
histogram_quantile(0.99, rate(signing_latency_bucket[5m]))
  > 0.5
```

---

## **5. Related Patterns**
| **Pattern**               | **Purpose**                                                                 | **Integration Notes**                          |
|---------------------------|-----------------------------------------------------------------------------|------------------------------------------------|
| **[Rate Limiting](https://example.com/rate-limiting)** | Prevent abuse of signing services (e.g., JWT flood attacks).              | Combine with `signing.operations.total` metrics. |
| **[Distributed Tracing](https://example.com/dtrace)** | Correlate signing across microservices.                                   | Use `trace.parent_id` for cross-service linkage. |
| **[Secret Management](https://example.com/secrets)** | Secure key storage and rotation.                                           | Audit `kms.key_rotation_attempts` for failures. |
| **[Chaos Engineering](https://example.com/chaos)**  | Test resilience to key revocation or signing outages.                       | Simulate `sign.status=failure` in traces.       |

---

## **6. Best Practices**
1. **Anonymize Sensitive Data**:
   - Redact raw tokens/logs in observability tools (e.g., using [FluentBit](https://fluentbit.io/)).
   - Example: `sign.payload = "anonymous"` in logs.

2. **Sample High-Volume Signing**:
   - Use [OpenTelemetry sampling](https://opentelemetry.io/docs/specs/semconv/tracing/semantic_conventions/sampling/) for JWTs with `sample_rate=0.1`.

3. **Retain Traces for Compliance**:
   - Configure retention policies (e.g., 7 days for debug traces, 30 days for audit logs).

4. **Standardize Key IDs**:
   - Use consistent formats (e.g., UUIDs for Vault keys, KMS ARNs).

5. **Alert on Anomalies**:
   - Example rule:
     ```yaml
     # Terraform Prometheus Alert
     resource "prometheus_alert_rule" "signing_failure_spike" {
       name             = "signing_failure_spike"
       prometheus_rule {
         alert = "SigningFailuresSpiked"
         expr  = "increase(signing_operations_total{status=\"failure\"}[5m]) > 100"
         for   = "1m"
       }
     }
     ```

---
**Appendices**:
- [OpenTelemetry Signing Semantic Conventions](https://github.com/open-telemetry/semantic-conventions/blob/main/docs/signing.md)
- [AWS KMS Observability Integration](https://aws.amazon.com/blogs/security/observability-with-amazon-cloudwatch/)