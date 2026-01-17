# **[Pattern] Rate Limiting & DDoS Protection Reference Guide**

---

## **1. Overview**
Rate Limiting & DDoS Protection is a defensive pattern that restricts the rate of requests to an application, API, or service to prevent abuse, brute-force attacks, and distributed denial-of-service (DDoS) events. This guide provides implementation best practices, design considerations, and technical schema for enforcing rate limits and mitigating DDoS threats.

Key goals include:
- Preventing resource exhaustion (e.g., CPU, memory, bandwidth).
- Protecting against automated attacks (e.g., scrapers, bots).
- Enabling graceful degradation under load spikes.

This pattern applies to APIs, web applications, and infrastructure services, using a combination of client-side and server-side mechanisms.

---

## **2. Schema Reference**

| **Category**               | **Field**               | **Description**                                                                                                                                                                                                                                                                 | **Required** | **Default** | **Example Values**                     |
|----------------------------|-------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------|-------------|------------------------------------------|
| **Rate Limiting Policy**   | Policy Name             | Unique identifier for the rate-limiting rule (e.g., `general_api_limit`, `login_attempts`).                                                                                                                                                                           | Yes          | -           | `login_attempts_10m`                    |
|                            | Rate Unit               | Time window for rate calculation (e.g., `seconds`, `minutes`, `hours`).                                                                                                                                                                                             | Yes          | -           | `minutes`                              |
|                            | Rate Limit              | Maximum allowed requests within `Rate Unit`.                                                                                                                                                                                                                       | Yes          | -           | `100`                                   |
|                            | Burst Limit             | Short-term spike tolerance (e.g., 2x the rate limit).                                                                                                                                                                                                                  | No           | `0`         | `200`                                   |
|                            | Chargeable Actions      | List of triggering actions (e.g., `GET /api/data`, `POST /login`).                                                                                                                                                                                                       | Yes          | -           | `[ "/api/data", "POST /login" ]`         |
|                            | Exempt IPs              | List of IP ranges to bypass rate limiting (e.g., internal services).                                                                                                                                                                                           | No           | `[]`        | `[ "192.168.0.0/16", "10.0.0.0/8" ]`    |
|                            | Throttling Strategy     | How to handle exceeding limits: `reject`, `queue`, or `delay`.                                                                                                                                                                                                             | No           | `reject`   | `delay`                                |
|                            | Delay Duration          | Waiting time (milliseconds) for `delay` strategy.                                                                                                                                                                                                                     | No           | `5000`      | `10000`                                |
|                            | Header Key              | Header name to attach rate-limit metadata (e.g., `X-RateLimit-Limit`).                                                                                                                                                                                               | No           | `X-RateLimit-*` | `custom-header`                         |
| **DDoS Mitigation**        | Mitigation Level        | Severity tier: `low` (noise), `medium` (block), `high` (firewall).                                                                                                                                                                                                   | Yes          | -           | `high`                                  |
|                            | Block Duration          | Time to block malicious IPs (seconds).                                                                                                                                                                                                                             | No           | `300`       | `86400`                                |
|                            | Anomaly Detection      | Method: `threshold` (fixed), `adaptive` (ML-based), or `signature` (known attacks).                                                                                                                                                                           | No           | `threshold`| `adaptive`                             |
|                            | Threshold Value         | Number of anomalies to trigger mitigation (for `threshold`).                                                                                                                                                                                                           | No           | `10`        | `5`                                     |
|                            | Blacklist Source        | Storage backend (e.g., `redis`, `database`, `cloud_waf`).                                                                                                                                                                                                               | Yes          | -           | `redis`                                 |
| **Monitoring**             | Alert Threshold         | Request rate triggering alerts (e.g., `10k RPS`).                                                                                                                                                                                                                              | No           | `5000`      | `15000`                                |
|                            | Metrics Exporter        | System collecting metrics (e.g., `prometheus`, `cloud_logs`).                                                                                                                                                                                                             | Yes          | -           | `prometheus`                           |
|                            | Sampling Rate           | Percentage of requests to sample for analysis.                                                                                                                                                                                                                             | No           | `100`       | `10`                                    |

---

## **3. Query Examples**

### **3.1 Enforcing Rate Limits (API Gateway)**
**Scenario**: Limit `GET /api/data` to 100 requests/minute with a 200-burst limit.

```http
# Request to configure rate limit in API Gateway (e.g., Kong, Nginx)
POST /apis/{api-id}/rate-limiting
Headers: {
  "Content-Type": "application/json"
}
Body:
{
  "policy_name": "api_data_limit",
  "rate_unit": "minutes",
  "rate_limit": 100,
  "burst_limit": 200,
  "chargeable_actions": ["GET /api/data"]
}
```

**Response (Success)**:
```json
{
  "status": "success",
  "policy_id": "pl_123456789"
}
```

---

### **3.2 Blocking DDoS Traffic (Cloud WAF)**
**Scenario**: Block IP ranges exceeding 10k RPS with a 5-minute blacklist.

```bash
# AWS WAFv2 Rule (via CloudFormation)
Resources:
  DDoSProtectionRule:
    Type: AWS::WAFv2::Rule
    Properties:
      Name: "DDoS-Mitigation-High"
      Priority: 1
      Statement:
        RateBasedStatement:
          Limit: 10000
          AggregateKeyType: "IP"
      VisibilityConfig:
        SampledRequestsEnabled: true
        CloudWatchMetricsEnabled: true
        MetricName: "DDoS-Mitigation-Metrics"
```

**Response (AWS Console/CLI)**:
```json
{
  "Rule": {
    "ARN": "arn:aws:wafv2:us-east-1:123456789012:regional/webacl/abc123/rules/d6b5c4a3",
    "Name": "DDoS-Mitigation-High",
    "Limit": 10000,
    "BlacklistDuration": "300s"
  }
}
```

---

### **3.3 Detecting Anomalies (Custom Backend)**
**Scenario**: Use a threshold-based detector to flag suspicious IPs.

```python
# Pseudo-code (Python)
def detect_anomaly(request_ip, threshold=10):
    # Retrieve request count from Redis (e.g., using `rate-limit` library)
    count = redis.get(f"requests:{request_ip}:1m")
    if count and int(count) > threshold:
        log_anomaly(request_ip)
        block_ip(request_ip, duration=300)  # 5-minute blacklist
```

**Output**:
```plaintext
[2023-10-01 14:30:00] ANOMALY: IP 192.0.2.1 exceeded threshold (15 requests).
```

---

## **4. Implementation Considerations**

### **4.1 Client-Side vs. Server-Side**
- **Client-side**: Token bucket/btoken algorithms (e.g., [RFC 6585](https://datatracker.ietf.org/doc/html/rfc6585)). Use HTTP headers like `X-RateLimit-Remaining`.
- **Server-side**: Database/Redis stores for distributed enforcement (e.g., `INCR` + `EXPIRE` operations).

### **4.2 DDoS Mitigation Strategies**
| **Strategy**       | **Use Case**                          | **Tools**                                  |
|--------------------|---------------------------------------|--------------------------------------------|
| **Rate Limiting**  | General abuse prevention              | Nginx, Kong, AWS WAF                       |
| **IP Blacklisting**| Known bad actors                      | Redis, AWS Security Groups                 |
| **Challenge Pages**| Human vs. bot detection               | Cloudflare, Akamai                        |
| **ML-Based**       | Adaptive thresholding (e.g., AWS GuardDuty) | TensorFlow, Custom ML models |

### **4.3 Performance Trade-offs**
- **Redis vs. Database**: Redis is faster but less persistent; databases offer durability.
- **Sampling**: Reduce overhead by sampling requests (e.g., 10%) for analysis.

---

## **5. Error Handling & Responses**
| **Error Code** | **Meaning**                          | **HTTP Status** | **Example Response**                                                                 |
|----------------|--------------------------------------|-----------------|------------------------------------------------------------------------------------|
| `429`          | Rate limit exceeded                  | `429`           | `{"error": "Rate limit exceeded", "retry-after": 30}`                               |
| `403`          | DDoS blocked (IP)                    | `403`           | `{"error": "Access denied: DDoS protection"}`                                      |
| `503`          | Service unavailable (backend overload)| `503`           | `{"error": "Service temporarily unavailable"}`                                      |
| `400`          | Invalid rate limit config             | `400`           | `{"error": "Invalid burst_limit: must be <= rate_limit"}`                           |

---

## **6. Related Patterns**
1. **[Authentication & Authorization](link)**: Integrate rate limiting with auth systems (e.g., JWT validation).
2. **[Circuit Breaker](link)**: Combine with rate limiting to gracefully handle cascading failures.
3. **[Distributed Tracing](link)**: Trace requests through rate-limited paths for debugging.
4. **[Auto-Scaling](link)**: Dynamically adjust limits based on load (e.g., Kubernetes HPA).
5. **[API Gateway Patterns](link)**: Deploy rate limiting at the edge (e.g., AWS API Gateway, Azure API Management).