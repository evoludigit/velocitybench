# **Debugging: On-Premise Verification – A Troubleshooting Guide**
*For Backend Engineers Handling Trusted Offline Validation*

The **On-Premise Verification (OPV)** pattern ensures that sensitive operations—such as authentication, payment processing, or regulatory compliance checks—can be validated in an isolated, trusted on-premise environment before being committed to a cloud system. Misconfigurations, network issues, or misaligned trust boundaries can cause failures, delays, or security risks.

This guide helps you diagnose common **OPV-related failures** efficiently, with a focus on practical fixes and prevention.

---

## **1. Symptom Checklist**
Before diving into debugging, systematically verify these **symptoms** to narrow down the root cause:

| **Symptom**                     | **Possible Causes**                          | **Action to Confirm** |
|---------------------------------|---------------------------------------------|-----------------------|
| **OPV Requests Hang/Timeout**   | Network latency, firewall blocking, or TLS issues | Check logs, `ping`, `traceroute` |
| **Unsigned/Invalid Responses**  | Local signing key mismatch, certificate expiry, or clock skew | Verify keys, NTP sync |
| **Rejected by Cloud System**    | Incorrect trust token format, JWT validation failure | Inspect payload, cloud logs |
| **High Latency in Local Validity Checks** | Slow local database queries, disk I/O bottlenecks | Profile DB queries, monitor disk usage |
| **Intermittent OPV Failures**   | Race conditions, partial network outages | Enable distributed tracing |
| **Audit Logs Omitting OPV Events** | Missing middleware logging, permission issues | Check local & cloud audit trails |

**Quick Checklist Workflow:**
1. **Is the issue intermittent or consistent?**
   - Consistent → Likely misconfiguration (keys, certs, policies).
   - Intermittent → Network, load, or race condition.
2. **Are local and cloud systems communicating?**
   - Test with `curl`/`Postman` to bypass app-layer issues.
3. **Verify end-to-end trust**:
   - Can the cloud system validate the OPV signature locally?

---

## **2. Common Issues and Fixes (With Code Examples)**

### **2.1 Network & Connectivity Issues**
**Symptom:** OPV requests never reach the cloud or time out.

#### **Common Causes & Fixes:**
| **Issue**                          | **Debugging Steps**                                                                 | **Fix** |
|------------------------------------|-------------------------------------------------------------------------------------|---------|
| **Outbound Firewall Blocking**     | Use `tcpdump` or `Wireshark` to capture blocked packets.                             | Whitelist OPV endpoints in firewall rules. |
| **MTU Fragmentation**              | Check for "IP fragment" errors in logs.                                             | Increase MTU or enable path MTU discovery (PMTUD). |
| **SSL/TLS Handshake Failures**     | Cloud system rejects client certs or ciphers.                                        | Test with `openssl s_client -connect <host>:<port> -showcerts`. |
| **Load Balancer/Proxy Issues**     | OPV traffic bypasses the LB or misrouted.                                           | Verify LB health checks, retry policies. |

**Example: Testing TLS with `curl`**
```bash
curl -v --cert client.crt --key client.key https://cloud-system.com/opv-endpoint
```
If this fails, the issue is **network/TLS-related**, not application logic.

---

### **2.2 Trust & Cryptographic Failures**
**Symptom:** Cloud system rejects OPV responses as invalid or unsigned.

#### **Common Causes & Fixes:**
| **Issue**                          | **Debugging Steps**                                                                 | **Fix** |
|------------------------------------|-------------------------------------------------------------------------------------|---------|
| **Expired/Invalid Signing Key**    | Local key used to sign OPV tokens is stale or compromised.                          | Regenerate keys, rotate in PKI. |
| **JWT Payload Mismatch**           | OPV token claims (e.g., `iss`, `aud`) don’t match cloud expectations.               | Compare signed payload with expected schema. |
| **Clock Skew**                     | Local NTP server out of sync with cloud’s time source.                               | Check `ntpq -p`, adjust NTP config. |
| **Missing/Incorrect headers**      | `Authorization` header format is wrong (e.g., wrong algorithm).                     | Test with:
   ```bash
   echo '{"alg":"HS256"," typ":"JWT"}' | jq -c > header.json
   echo '{"sub":"user123", "exp":1234567890}' | jq -c > payload.json
   echo '{"alg":"HS256"}' | jq -c > signature.json
   base64 -e header.json | base64 -e payload.json | base64 -e signature.json | jq -s .
   ```

**Example: Validating a JWT Manually**
```python
import jwt
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

# Load public key from cloud system
with open("cloud_public_key.pem", "rb") as f:
    public_key = load_pem_private_key(f.read(), None)

# Decode and verify JWT
token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
header, payload, signature = token.split('.')
decoded_header = jwt.utils.decode_jwt_header(header.encode())
decoded_payload = jwt.decode(token, public_key, algorithms=["RS256"])
```

---

### **2.3 Performance & Latency Bottlenecks**
**Symptom:** OPV checks take >5s, causing timeouts.

#### **Common Causes & Fixes:**
| **Issue**                          | **Debugging Steps**                                                                 | **Fix** |
|------------------------------------|-------------------------------------------------------------------------------------|---------|
| **Slow Local Database Queries**    | OPV validation requires a blocking DB call.                                          | Optimize queries, add caching (Redis). |
| **Disk I/O for Large Logs**        | Local validation writes excessive logs.                                             | Increase disk IOPS, compress logs. |
| **Unoptimized Crypto Operations**  | ECDSA/RSA signing is too slow for high throughput.                                 | Use hardware acceleration (AWS Nitro, Azure Confidential VMs). |

**Example: Profiling DB Latency in Node.js**
```javascript
const { performance } = require('perf_hooks');

async function validateOpvRequest() {
  const start = performance.now();
  const result = await db.query("SELECT * FROM validations WHERE id = ?", [req.id]);
  const latency = performance.now() - start;
  console.log(`DB Latency: ${latency}ms`);
  // ...
}
```

---

### **2.4 Race Conditions & State Mismatches**
**Symptom:** OPV responses are valid locally but rejected by the cloud.

#### **Common Causes & Fixes:**
| **Issue**                          | **Debugging Steps**                                                                 | **Fix** |
|------------------------------------|-------------------------------------------------------------------------------------|---------|
| **Out-of-Sync State**              | Cloud system expects a transaction ID that isn’t in the OPV response.               | Add correlation IDs, enable idempotency. |
| **Partial Failures**               | Network split-brain causes inconsistent state.                                       | Implement sagas or compensating transactions. |

**Example: Correlation IDs in OPV**
```json
// Request from client
{
  "opvRequest": {
    "transactionId": "txn-12345",
    "validationPayload": {...}
  },
  "correlationId": "corr-abc123"
}

// Response from OPV
{
  "status": "VALID",
  "transactionId": "txn-12345",
  "correlationId": "corr-abc123",
  "signature": "..."
}
```

---

## **3. Debugging Tools and Techniques**
### **3.1 Network Diagnostics**
- **`tcpdump`/`Wireshark`**: Capture OPV traffic to verify packet loss, retransmissions.
  ```bash
  tcpdump -i eth0 -w opv_traffic.pcap port 443
  ```
- **`curl`/`Postman`**: Test OPV endpoints manually.
- **`traceroute`**: Check for hops introducing latency.
  ```bash
  traceroute cloud-system.com
  ```

### **3.2 Logging & Observability**
- **Structured Logging**: Use `JSON` logs with `correlationId` for tracing.
  ```python
  import logging
  logging.info(json.dumps({
      "event": "opv_validation",
      "correlationId": "corr-123",
      "status": "success",
      "latencyMs": 120
  }))
  ```
- **Distributed Tracing**: Integrate OpenTelemetry to trace OPV flows.
  ```python
  from opentelemetry import trace
  tracer = trace.get_tracer(__name__)
  with tracer.start_as_current_span("opv_validation"):
      # ... validation logic ...
  ```

### **3.3 Key & Certificate Management**
- **`openssl`**: Verify keys and certs.
  ```bash
  openssl x509 -in client.crt -text -noout  # Check expiry
  openssl pkey -in private.key -text       # Check key type
  ```
- **Hashicorp Vault**: Automate key rotation and secret management.

### **3.4 Performance Profiling**
- **`pprof` (Go)**: Profile CPU/disk usage.
  ```bash
  go tool pprof http://localhost:6060/debug/pprof/profile
  ```
- **`sysdig`/`datadog`**: Monitor OPV latency in production.

---

## **4. Prevention Strategies**
### **4.1 Architectural Best Practices**
- **Immutable Keys**: Rotate keys automatically (e.g., quarterly).
- **Circuit Breakers**: Fail fast if OPV validation times out.
  ```python
  # Python example with `pybreaker`
  from pybreaker import CircuitBreaker
  breaker = CircuitBreaker(fail_max=3, reset_timeout=60)
  @breaker
  def validate_opv():
      return cloud_system.validate_opv_token(token)
  ```
- **Chaos Engineering**: Test OPV resilience with `Chaos Mesh`.

### **4.2 Monitoring & Alerting**
- **SLOs**: Set alerts for OPV validation >500ms.
- **Dashboards**: Track:
  - `opv_validation_latency_p99`
  - `opv_rejection_rate`
  - `network_failure_count`

### **4.3 Disaster Recovery**
- **Backup OPV State**: Store validations in a durable store (e.g., DynamoDB).
- **Chaos Testing**: Simulate:
  - Network partitions (`netem`).
  - Key revocation.

**Example: Chaos Testing with `netem`**
```bash
# Simulate 50% packet loss
sudo tc qdisc add dev eth0 root netem loss 50%
# Run OPV tests, then remove
sudo tc qdisc del dev eth0 root
```

---

## **5. Conclusion**
| **Issue Type**       | **Quick Fix**                          | **Long-Term Solution**                  |
|----------------------|----------------------------------------|-----------------------------------------|
| Network Blocking     | Whitelist IPs/firewall rules           | Implement VPN or site-to-site VPN       |
| Invalid Signatures   | Regenerate keys, check NTP             | Automate key rotation with Vault        |
| High Latency         | Optimize DB queries, cache results     | Use serverless OPV or edge caching     |
| Race Conditions      | Add correlation IDs                    | Implement idempotency keys              |

**Final Checklist Before Going Live:**
1. ✅ Test OPV end-to-end with `curl`/`Postman`.
2. ✅ Verify keys/certs are valid and synchronized.
3. ✅ Monitor OPV latency in staging.
4. ✅ Set up alerts for rejection rates.
5. ✅ Document OPV failure recovery procedure.

By following this guide, you should be able to **resolve 90% of OPV issues in <1 hour**. For persistent problems, isolate the issue using tracing, logging, and manual testing. Prevention (key rotation, monitoring, chaos testing) will reduce future outages.

---
**Next Steps:**
- Run a dry run with `Chaos Mesh` on staging.
- Automate OPV validation logs with Loki/Grafana.
- Schedule a key rotation test.