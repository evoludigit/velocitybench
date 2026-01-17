---
# **[Anti-Pattern] Logging Anti-Patterns – Reference Guide**
*Identify and avoid common logging pitfalls that degrade observability, performance, and system reliability.*

---

## **1. Overview**
Logging is a critical component of observability, but poorly designed logging practices—*"anti-patterns"*—can introduce noise, security risks, or performance bottlenecks. These anti-patterns may stem from misguided conventions, tooling misconfigurations, or developer assumptions. This guide categorizes and explains **10 key logging anti-patterns**, their consequences, and recommended fixes to ensure effective, secure, and performant logging.

**Key Risks of Anti-Patterns:**
- **Reduced Observability:** Logs become overwhelming or irrelevant.
- **Security Vulnerabilities:** Sensitive data leaks (e.g., tokens, PII).
- **Performance Degrades:** High-cardinality or excessive verbosity slows systems.
- **Storage Bloat:** Uncontrolled log volume inflates storage costs.

---

## **2. Schema Reference**
| **Anti-Pattern**               | **Description**                                                                 | **Impact**                                                                 | **Mitigation Strategy**                                                                 |
|---------------------------------|---------------------------------------------------------------------------------|-----------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| **1. Logging Sensitive Data**   | Including passwords, API keys, tokens, or PII in logs.                          | Compliance violations, data breaches.                                        | Use dynamic redaction or exclude sensitive fields entirely (e.g., `environment="production"` checks). |
| **2. Over-Logging**             | Logging every method call, internal state transitions, or low-level events.      | Log overload, slower processing, wasted storage.                              | Log only critical events (e.g., errors, thresholds) or use structured logging with levels (DEBUG/WARN/ERROR). |
| **3. Unstructured Logs**        | Writing plaintext logs without metadata (timestamps, context IDs, levels).      | Harder to parse, correlate, or query.                                        | Use structured logging formats (JSON, Protobuf) with key-value pairs for consistency. |
| **4. Logging Exceptions Blindly** | Capturing raw stack traces without context or filtering.                    | Logs drowned by noise; hard to debug root causes.                             | Log exception summaries + context (e.g., `ERROR: UserLoginFailed: [user_id=123]`).      |
| **5. Log Rotation Mismanagement** | No rotation policies or excessive retention periods.                             | Disk space exhaustion, compliance risks.                                      | Configure log rotation (e.g., `max_size=100MB`, `max_age=30d`) and retention policies.    |
| **6. Inconsistent Formatting**  | Mixing timestamps, log levels, or delimiters across microservices.              | Difficulty in correlating logs across services.                               | Enforce a standardized format (e.g., RFC 3339 timestamps, `JSON` keys).                   |
| **7. Logging to Stdout/Stderr** | Writing logs directly to console or file without a central pipeline.            | Lost logs, no centralized querying.                                           | Route all logs to a structured logging system (ELK, Splunk, Loki).                       |
| **8. Ignoring Log Levels**      | Using only `DEBUG` or `ERROR` without granularity (e.g., `WARN`, `INFO`).       | Missed warnings; excessive noise at higher levels.                            | Use hierarchical levels (e.g., `DEBUG < INFO < WARN < ERROR`) and filter logs accordingly. |
| **9. Correlating Logs Poorly**  | Lack of trace IDs, request IDs, or session IDs across distributed systems.      | Hard to trace user flows or failures.                                        | Inject trace IDs (e.g., `X-Request-ID`) into logs and metadata.                         |
| **10. Logging Without Context** | Missing context (e.g., user ID, endpoint, correlation ID).                      | Hard to debug user-specific issues.                                           | Include context in every log (e.g., `user_id`, `endpoint`, `trace_id`).                   |

---

## **3. Query Examples**
Use these queries to identify anti-patterns in logs (adapt to your logging system, e.g., ELK, Loki, or Splunk):

### **3.1 Detect Sensitive Data Leaks**
```sql
// Query for passwords/tokens in logs (ELK/KQL)
logs
| where message contains ("password" OR "token" OR "API_KEY")
| project timestamp, message, source
```
**Mitigation:** Add a redaction rule for these terms (e.g., `***-**-****`).

---

### **3.2 Identify Over-Logging**
```sql
// Count log lines per minute (Loki/Grafana)
sum by (time série) (
  log_lines
)
| rate(1m)
```
**Mitigation:** Reduce log volume by filtering low-priority events.

---

### **3.3 Find Unstructured Logs**
```sql
// Check for missing JSON structure (Grok patterns or regex)
logs
| where not (message matches "^\\{.*\\}$" OR message matches "^\\<.*\\>$")
```
**Mitigation:** Enforce structured logging (e.g., `json="true"` in your logger config).

---

### **3.4 Trace Correlated Logs**
```sql
// Find logs with missing trace IDs (Splunk)
index=main
| search NOT "trace_id="*
| table _time, source, message
```
**Mitigation:** Auto-generate trace IDs and include them in logs.

---

### **3.5 Audit Log Rotation**
```sql
// Check for logs older than retention policy (Loki)
log_lines
| where time > now() - 90d
| count by (time_series)
```
**Mitigation:** Set retention policies (e.g., `logs.retention=30d`).

---

## **4. Implementation Details**
### **4.1 Logging Frameworks and Configurations**
| **Framework**       | **Anti-Pattern Fix**                                                                 | **Example Config**                                                                 |
|---------------------|-------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Python (logging)** | Avoid `logging.debug()` for every step; use `structlog` for structured logs.       | `logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s')`          |
| **Java (Log4j)**    | Exclude sensitive fields via `PatternLayout` or `LookbackCeilatorFilter`.          | `<Log4j2Config> <PatternLayout pattern="%d{HH:mm:ss} [%t] %-5level %msg%n" />`    |
| **Go (zap)**        | Use `zap.LevelEnabler` to filter logs by severity.                                    | `zap.NewNop().Sugar().Debug("debug message")` (disable in production).             |
| **Node.js (winston)** | Redact sensitive fields with `transform: (info) => { ... }`.                       | `winston.format.json({ redact: ["password"] })`                                      |

---

### **4.2 Best Practices**
1. **Principles of Least Privilege:**
   - Log only what’s necessary for debugging. Remove `DEBUG` logs in production.
   - Example: Replace `logging.info(f"User data: {user_data}")` with `logging.info(f"User ID: {user_id}")`.

2. **Structured Logging:**
   - Use JSON or key-value pairs for machine readability.
   - Example (Python `structlog`):
     ```python
     import structlog
     structlog.configure(
         processors=[
             structlog.processors.JSONRenderer()
         ]
     )
     logger = structlog.get_logger()
     logger.info("user_login", user_id=123, success=True)
     ```

3. **Centralized Logging:**
   - Ship logs to a system like **ELK Stack**, **Loki**, or **Datadog**.
   - Example (AWS CloudWatch):
     ```yaml
     # cloudwatch-config.log
     [cloudwatch-logs]
     logGroupName = /my-app/logs
     region = us-west-2
     ```

4. **Log Retention Policies:**
   - Configure retention based on compliance (e.g., HIPAA: 6 years).
   - Example (Loki retention):
     ```yaml
     retention: "30d"
     ```

5. **Correlation IDs:**
   - Inject a unique ID for each request/flow.
   - Example (Express.js middleware):
     ```javascript
     app.use((req, res, next) => {
       req.traceId = crypto.randomUUID();
       next();
     });
     logger.info("request_start", { traceId: req.traceId });
     ```

---

## **5. Related Patterns**
To complement logging anti-patterns, adopt these **best practices and patterns**:

| **Pattern**               | **Description**                                                                 | **Reference**                                                                 |
|---------------------------|-------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **Structured Logging**    | Format logs as key-value pairs for queryability.                             | [Structured Logging Guide](https://www.structured-logging.org/)               |
| **Observability Stack**   | Combine logging, metrics, and tracing (e.g., OpenTelemetry).                | [OpenTelemetry Docs](https://opentelemetry.io/docs/)                         |
| **Log Sampling**          | Reduce log volume by sampling (e.g., 1% of requests).                        | [Sampling in OpenTelemetry](https://opentelemetry.io/docs/specs/otel/sdk/#sampling) |
| **Secure Log Shipping**   | Encrypt logs in transit and at rest (e.g., TLS, KMS).                         | [AWS KMS for Logs](https://docs.aws.amazon.com/kms/latest/developerguide/)    |
| **SLO-Based Alerts**      | Alert on logging anomalies (e.g., spike in errors).                           | [SLOs in Site Reliability Engineering](https://sre.google/sre-book/table-of-contents/) |

---

## **6. References**
- **OWASP Logging Cheat Sheet:** [https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)
- **Grafana Loki Docs:** [https://grafana.com/docs/loki/latest/](https://grafana.com/docs/loki/latest/)
- **OpenTelemetry Logging:** [https://opentelemetry.io/docs/specs/otel/spec-logging/](https://opentelemetry.io/docs/specs/otel/spec-logging/)
- **ELK Stack Guides:** [https://www.elastic.co/guide/en/elastic-stack-guide/current/index.html](https://www.elastic.co/guide/en/elastic-stack-guide/current/index.html)

---
**Key Takeaway:** Avoid logging anti-patterns by **filtering, structuring, and centralizing** logs while prioritizing security and performance. Use the schema and queries provided to audit your logging setup proactively.