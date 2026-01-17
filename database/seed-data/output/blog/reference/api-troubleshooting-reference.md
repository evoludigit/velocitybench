**[Pattern] API Troubleshooting Reference Guide**

---

### **Overview**
This guide provides a structured approach to diagnosing, resolving, and preventing common API issues. Whether dealing with **latency spikes, authentication failures, rate limits, or data inconsistencies**, this pattern ensures systematic troubleshooting while leveraging logging, monitoring, and collaboration tools. Targeted at **API developers, DevOps engineers, and support teams**, it outlines best practices for **proactive debugging**, **postmortems**, and **long-term reliability improvements**.

---

### **Key Concepts & Implementation Details**

#### **1. Root Cause Analysis (RCA) Framework**
| **Step**               | **Description**                                                                                                                                                                                                 | **Tools/Resources**                                                                                     |
|-------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| **Symptom Identification** | Log API errors (e.g., `5xx`, `4xx`), time-series data, or client feedback. Use metrics like **latency percentiles (P99)**, **error rates**, or **throttled requests**.                                             | - **Logging:** ELK Stack (Elasticsearch, Logstash, Kibana), Datadog, Splunk <br>- **Metrics:** Prometheus, Grafana, New Relic |
| **Hypothesis Generation** | Isolate potential causes (e.g., code, infrastructure, third-party dependencies, misconfiguration). Common culprits include:                                                                                            | - **Code:** Git blame, code reviews <br>- **Infrastructure:** Cloud Console (AWS/GCP), Terraform State <br>- **Network:** `curl`, Wireshark, `tcpdump` |
| **Validation**           | Test hypotheses with targeted queries, load tests, or traffic isolation (e.g., canary deployments).                                                                                                                     | - **Load Testing:** JMeter, Locust <br>- **Isolation:** Kubernetes Namespaces, VPC Segmentation <br>- **Repro:** Postman, `curl`, API Gateway Tracing |
| **Resolution**           | Apply fixes (e.g., retries, circuit breakers, rate-limiting adjustments). Document changes in a **change log**.                                                                                               | - **Circuit Breakers:** Hystrix, Resilience4j <br>- **Retries:** Exponential backoff (e.g., AWS Retry API) |
| **Feedback Loop**        | Close the loop with stakeholders (e.g., clients notified of outages, internal postmortems). Use **SLOs/SLIs** to measure reliability improvements.                                                          | - **Postmortems:** Blameless retrospective (Google SRE) <br>- **SLOs:** Error budgets, Service Level Indicators (SLIs) |

---

#### **2. Common API Issues & Debugging Workflows**
| **Issue Type**          | **Symptoms**                          | **Debugging Steps**                                                                                                                                                     | **Mitigation Strategies**                                                                                     |
|--------------------------|----------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|
| **Latency Spikes**       | High `P99` latency, slow responses    | - Check **distributed tracing** (e.g., Jaeger, OpenTelemetry) for bottlenecks. <br>- Analyze **database queries** (slow SQL, N+1 problems). <br>- Review **cold starts** (serverless). | - Optimize queries (indexes, caching). <br>- Scale horizontally. <br>- Use **client-side caching** (Redis). |
| **Authentication Errors**| `401 Unauthorized`, `403 Forbidden`    | - Verify **JWT/OAuth tokens** (expiry, claims). <br>- Check **API Key** rotations. <br>- Audit **IAM policies** (AWS, GCP).                                                           | - Implement **token refresh logic**. <br>- Use **short-lived tokens**. <br>- Rotate keys automatically.       |
| **Rate Limiting**        | `429 Too Many Requests`               | - Validate **rate limits** (e.g., per-minute, per-second). <br>- Check **client caching** (proxies, CDNs). <br>- Review **burst capacity**.                                                             | - Adjust limits dynamically. <br>- Use **token bucket algorithms**. <br>- Educate clients on caching.         |
| **Data Inconsistencies** | Duplicate records, stale data          | - Audit **transaction logs** (PostgreSQL WAL, Kafka). <br>- Check **eventual consistency** trade-offs. <br>- Validate **schema migrations**.                                                                | - Use **idempotency keys**. <br>- Implement **CQRS** (separate reads/writes). <br>- Retry failed transactions. |
| **Network Issues**       | Timeouts, `502 Bad Gateway`           | - Test **connectivity** (`ping`, `traceroute`). <br>- Check **firewall rules**, **MTU sizes**. <br>- Review **load balancer** health.                                                                        | - Enable **connection pooling**. <br>- Use **HTTP/2** for multiplexing. <br>- Monitor **TCP handshake failures**. |
| **Versioning Conflicts** | `406 Not Acceptable`                   | - Verify **header compatibility** (`Accept: application/vnd.api.v1+json`). <br>- Check **deprecated endpoints**. <br>- Review **backward compatibility**.                                                                 | - Document **deprecation policies**. <br>- Use **feature flags**. <br>- Warn clients via `Deprecated-Api` header. |

---

### **Schema Reference**
Below is a **standardized logging schema** for API troubleshooting (JSON format):

| **Field**               | **Type**   | **Description**                                                                                                                                                     | **Example**                          |
|--------------------------|------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------|
| `timestamp`              | ISO 8601   | UTC timestamp of the event.                                                                                                                                         | `"2023-10-15T12:34:56.789Z"`       |
| `api_version`            | String     | Version of the API (e.g., `v1`, `v2`).                                                                                                                                   | `"v1"`                               |
| `endpoint`               | String     | Fully qualified path (e.g., `/users/{id}`).                                                                                                                           | `"/users/123"`                       |
| `method`                 | String     | HTTP method (`GET`, `POST`, etc.).                                                                                                                                     | `"GET"`                              |
| `status_code`            | Integer    | HTTP response code (e.g., `200`, `500`).                                                                                                                               | `404`                                |
| `latency_ms`             | Float      | End-to-end processing time in milliseconds.                                                                                                                             | `150.2`                              |
| `error`                  | Object     | Structured error details.                                                                                                                                         | `{ "type": "RateLimitExceeded", "code": "429" }` |
| `request_id`             | String     | Unique identifier for tracing.                                                                                                                                       | `"req_abc123"`                       |
| `user_agent`             | String     | Client software (e.g., `Postman/7.30.0`).                                                                                                                             | `"aws-sdk/2.13.7"`                    |
| `correlation_id`         | String     | Cross-service trace ID (e.g., distributed tracing).                                                                                                                   | `"corr_xyx789"`                      |
| `metadata`               | Object     | Custom key-value pairs (e.g., `retries=3`).                                                                                                                           | `{ "retries": 3, "region": "us-west-2" }` |

---
### **Query Examples**
#### **1. Filtering High-Latency Requests (Grafana/PromQL)**
```promql
# Latency > 1s (P99)
histogram_quantile(0.99, sum(rate(api_latency_bucket[5m])) by (le))
```
**Expected Output:**
```
le="1s" 12345  # 12,345 requests took > 1s
```

#### **2. Auth Errors by Endpoint (ELK Stack)**
```json
// Kibana Query DSL
{
  "query": {
    "bool": {
      "must": [
        { "term": { "status_code": "401" } },
        { "term": { "endpoint": { "value": "/login", "wildcard": "*" } } }
      ]
    }
  }
}
```

#### **3. Rate Limit Violations (CloudWatch Metrics)**
```bash
# AWS CLI to find throttled API calls
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name ThrottledRequests \
  --dimensions Name=ApiName,Value=MyApi \
  --start-time 2023-10-15T00:00:00 \
  --end-time 2023-10-15T23:59:59 \
  --period 60 \
  --statistics Sum
```

#### **4. Distributed Tracing ( Jaeger Query)**
```
service=api-service operation=GET /users endpoint=prod user_agent=aws-sdk
```

---

### **Related Patterns**
| **Pattern**                          | **Description**                                                                                                                                                                                                 | **When to Use**                                                                                     |
|---------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| **[Circuit Breaker](https://...)**   | Temporarily stops failing requests to prevent cascading failures.                                                                                                                                         | High-availability systems (e.g., payment processing).                                                 |
| **[Retry with Backoff](https://...)** | Exponentially delays retries to avoid thundering herds.                                                                                                                                                 | Idempotent operations (e.g., bulk inserts).                                                           |
| **[Rate Limiting](https://...)**     | Controls request volume to prevent abuse.                                                                                                                                                         | Public APIs or microservices with variable loads.                                                     |
| **[Distributed Tracing](https://...)** | Tracks requests across services using unique IDs.                                                                                                                                                     | Microservices architectures (e.g., e-commerce checkout).                                             |
| **[Idempotency Keys](https://...)**  | Ensures duplicate requests produce the same result.                                                                                                                                                   | Financial APIs, order processing.                                                                     |
| **[Postmortem Template](https://...)** | Structured retrospective for outages.                                                                                                                                                               | After incidents (e.g., database corruption).                                                          |
| **[SLO/SLI Tracking](https://...)**   | Measures reliability via error budgets.                                                                                                                                                                   | Long-term reliability planning (e.g., "99.9% uptime").                                                |

---
### **Best Practices Checklist**
1. **Proactive Monitoring**: Set up **alerts** for `P99` latency > 500ms or error rates > 1%.
2. **Centralized Logging**: Use **structured logs** (JSON) with `request_id` for correlation.
3. **Tracing**: Enable **distributed tracing** (OpenTelemetry) for multi-service flows.
4. **Client Documentation**: Publish **API status pages** (e.g., Statuspage.io) and **deprecation timelines**.
5. **Chaos Engineering**: Periodically test **failure scenarios** (e.g., regional outages).
6. **Automated Remediation**: Use **runbooks** or **Ansible** to auto-scale or restart services.
7. **Client Tools**: Provide **SDKs with retries** and **idempotency support** (e.g., AWS SDK v3).

---
### **Further Reading**
- **[Google SRE Book](https://sre.google/sre-book/table-of-contents/)** – Reliability engineering principles.
- **[AWS Well-Architected API Best Practices](https://aws.amazon.com/architecture/well-architected/lens/api/)** – Cloud-native API design.
- **[OpenTelemetry Docs](https://opentelemetry.io/docs/)** – Distributed tracing implementation.