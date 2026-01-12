# **Debugging Integration: A Troubleshooting Guide**
*For Backend Engineers*

This guide provides a structured approach to debugging integration issues in distributed systems, microservices, or third-party API integrations. The focus is on quick resolution with minimal downtime.

---

## **1. Symptom Checklist**
Before diving into debugging, confirm the issue by systematically checking:

| **Category**               | **Possible Symptoms**                                                                 | **Quick Checks**                                                                 |
|----------------------------|--------------------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| **API/Service Failures**   | Timeout errors, 5xx responses, missing responses                                      | Check API docs for rate limits, latency thresholds, and retries.                 |
| **Data Corruption**        | Incorrect payloads, missing fields, malformed JSON/XML                               | Validate input/output schema (use tools like JSON Schema or XML Validator).      |
| **Authentication Issues**  | 401/403 errors, expired tokens, incorrect credentials                               | Verify OAuth/JWT tokens, API keys, or service account permissions.                 |
| **Network/Connectivity**   | DNS resolution failures, TLS handshake errors, firewall blocks                        | Test connectivity (`telnet`, `curl`, `ping`), check logs for SSL/TLS errors.      |
| **Dependency Failures**    | External service outages (DB, payment gateways, etc.)                                | Monitor downstream service health (e.g., Prometheus, Datadog).                   |
| **Logging & Visibility**   | Missing logs, insufficient context in traces                                         | Enable distributed tracing (OpenTelemetry, Jaeger), increase log verbosity.      |
| **Rate Limiting**          | Throttling errors (429), sudden spikes in errors                                     | Check API rate limit headers, implement exponential backoff in retries.            |
| **Configuration Drift**    | Unexpected behavior due to misconfigured endpoints, timeouts, or retries             | Diff configs across environments (staging vs. prod).                            |
| **Idempotency Issues**     | Duplicate transactions, race conditions                                              | Implement idempotency keys (e.g., UUIDs in request IDs).                         |
| **Circuit Breaker Failures** | Overloaded services, cascading failures                                              | Review circuit breaker thresholds (e.g., Resilience4j, Hystrix).                |

---

## **2. Common Issues and Fixes**
### **A. API/Service Timeout Errors**
**Symptom:**
`Request timed out`, `Connection reset by peer`, or slow responses.

**Root Causes:**
- External service latency (e.g., payment processor, third-party API).
- High network latency (CDN, proxy, or firewall delays).
- Insufficient timeout settings in client code.

**Fixes:**
1. **Increase Timeout (Client-Side):**
   ```java
   // Java (Apache HttpClient)
   RequestConfig config = RequestConfig.custom()
       .setConnectTimeout(10_000)  // 10 sec
       .setSocketTimeout(30_000)   // 30 sec
       .build();
   HttpClient client = HttpClientBuilder.create().setDefaultRequestConfig(config).build();
   ```
   ```javascript
   // Node.js (axios)
   axios.get('https://api.example.com/data', {
       timeout: 10000,  // 10 sec
       timeoutErrorMessage: 'External API timeout'
   });
   ```

2. **Implement Retry with Backoff:**
   ```python
   # Python (with tenacity decorator)
   from tenacity import retry, wait_exponential

   @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
   def call_external_api():
       response = requests.get("https://api.example.com/data", timeout=5)
       response.raise_for_status()
       return response.json()
   ```

3. **Monitor External Service Health:**
   - Use **Prometheus + Alertmanager** to monitor API response times.
   - Example alert rule:
     ```yaml
     - alert: HighApiLatency
       expr: api_request_duration_seconds > 2
       for: 5m
       labels:
         severity: warning
       annotations:
         summary: "API {{ $labels.service }} is slow ({{ $value }}s)"
     ```

---

### **B. Authentication Failures (401/403)**
**Symptom:**
Unauthorized access due to invalid tokens, expired credentials, or missing headers.

**Root Causes:**
- Stale API keys/OAuth tokens.
- Incorrect token scopes.
- Caching issues (e.g., proxy or client-side token reuse).

**Fixes:**
1. **Refresh Tokens Automatically:**
   ```java
   // Java (OAuth2 Client Example)
   OAuth2Token token = oauth2Manager.token();
   if (token.isExpired()) {
       token = oauth2Manager.refresh();
   }
   ```

2. **Validate Token Claims:**
   ```javascript
   // Node.js (using jwt-decode)
   const decoded = jwtDecode(token);
   if (decoded.exp * 1000 < Date.now()) {
       throw new Error("Token expired");
   }
   ```

3. **Check Service Account Permissions:**
   - Verify IAM policies (AWS), RBAC (Kubernetes), or API-specific roles.

---

### **C. Data Format Mismatches (JSON/XML Parsing Errors)**
**Symptom:**
`JSON.parse error`, `Invalid XML`, or missing required fields.

**Root Causes:**
- Schema drift (API changed its response structure).
- Malformed payloads (e.g., UTF-8 encoding issues).
- Case sensitivity in keys (e.g., `userName` vs `username`).

**Fixes:**
1. **Validate Input/Output Schemas:**
   ```json
   // Example JSON Schema for validation (using Ajv in Node.js)
   const schema = {
     "type": "object",
     "properties": {
       "user": { "type": "object", "required": ["id", "email"] }
     }
   };
   const validate = new Ajv();
   const valid = validate.validate(schema, payload);
   if (!valid) throw new Error("Invalid payload");
   ```

2. **Handle Edge Cases in Parsing:**
   ```python
   # Python (safe JSON parsing)
   try:
       data = json.loads(request.body)
   except json.JSONDecodeError:
       log.error("Invalid JSON payload")
       return BadRequest("Malformed JSON")
   ```

3. **Log Raw Payloads for Debugging:**
   ```java
   // Log incoming/outgoing requests (Spring Boot)
   @RestControllerAdvice
   class GlobalExceptionHandler {
       @ExceptionHandler(JsonParseException.class)
       public ResponseEntity<String> handleJsonError(Exception ex) {
           log.error("Failed to parse JSON: {}", ex.getMessage());
           log.info("Raw request body: {}", request.getReader().lines().collect(Collectors.toList()));
           return ResponseEntity.badRequest().body("Invalid JSON");
       }
   }
   ```

---

### **D. Network/Connectivity Issues**
**Symptom:**
`Could not connect to host`, `SSL handshake failure`, `DNS resolution failed`.

**Root Causes:**
- Firewall blocking ports (e.g., 443 for HTTPS).
- Misconfigured SSL certificates (expired or self-signed).
- DNS propagation delays.

**Fixes:**
1. **Test Connectivity Manually:**
   ```bash
   # Check TCP connectivity
   telnet api.example.com 443

   # Check HTTPS handshake
   openssl s_client -connect api.example.com:443 -servername api.example.com
   ```

2. **Configure SSL Properly:**
   ```java
   // Java (Trusting all certs for testing - NOT for prod!)
   SSLContext sslContext = SSLContext.getInstance("TLS");
   sslContext.init(null, new TrustManager[] { new X509TrustManager() {
       public void checkClientTrusted(...) { }
       public void checkServerTrusted(...) { }
       public java.security.cert.X509Certificate[] getAcceptedIssuers() { return new X509Certificate[0]; }
   } }, new SecureRandom());
   HttpsURLConnection.setDefaultSSLSocketFactory(sslContext.getSocketFactory());
   ```

   **For Production:**
   - Use a proper truststore (`-Djavax.net.ssl.trustStore=/path/to/truststore.jks`).

3. **Resolve DNS Issues:**
   - Use `dig` or `nslookup` to verify DNS records.
   - Configure a local DNS cache (`/etc/hosts` for testing).

---

### **E. Rate Limiting Throttling (429 Errors)**
**Symptom:**
`Too Many Requests`, `Quota Exceeded`.

**Root Causes:**
- Uncontrolled burst traffic.
- Missing headers (`X-RateLimit-Limit`, `X-RateLimit-Remaining`).
- No retry logic with backoff.

**Fixes:**
1. **Implement Exponential Backoff:**
   ```python
   # Python (with exponential backoff)
   import time
   from random import uniform

   def call_with_retry(url, max_retries=3):
       retries = 0
       while retries < max_retries:
           try:
               response = requests.get(url, timeout=5)
               if response.status_code == 429:
                   wait = 2 ** retries + uniform(0, 1)
                   time.sleep(wait)
                   retries += 1
                   continue
               return response
           except requests.exceptions.RequestException as e:
               log.error(f"Request failed: {e}")
               return None
   ```

2. **Monitor Rate Limits:**
   - Use **Grafana + Prometheus** to track API calls.
   - Set alerts for `rate_api_requests_total > 1000`.

3. **Cache Responses (CDN or Proxy):**
   - Use **Varnish**, **Nginx**, or **Cloudflare** to cache frequent requests.

---

## **3. Debugging Tools and Techniques**
| **Tool/Technique**       | **Use Case**                                                                 | **Example Command/Config**                          |
|--------------------------|-----------------------------------------------------------------------------|----------------------------------------------------|
| **cURL**                 | Test API endpoints manually.                                                 | `curl -v -H "Authorization: Bearer $TOKEN" https://api.example.com/data` |
| **Postman/Insomnia**     | Debug HTTP requests with pre-request scripts.                                | Add headers, body, and response validation.        |
| **Wireshark/tcpdump**    | Inspect raw network traffic (TCP, HTTP headers).                              | `tcpdump -i eth0 -w capture.pcap host api.example.com` |
| **OpenTelemetry**        | Distributed tracing for latency analysis.                                     | Instrument code with `@OpenTelemetry` SDK.          |
| **Prometheus + Grafana** | Monitor metrics (latency, error rates, throughput).                           | `prometheus.yml` scrape targets.                  |
| **Chaos Engineering**    | Simulate failures (e.g., kill pods, throttle network).                       | Use **Gremlin** or **Chaos Mesh**.                |
| **Log Analysis (ELK)**   | Correlate logs across services (e.g., ECS + Fluentd + Elasticsearch).         | `kibana` query: `service:api AND status:error`.    |
| **API Mocking (Postman Mock Server)** | Test integrations without hitting real APIs.                                  | Replace `https://api.example.com` with a mock.     |

---

## **4. Prevention Strategies**
### **A. Design for Resilience**
1. **Circuit Breakers:**
   - Use **Resilience4j** (Java), **Hystrix**, or **circuitbreaker.py** (Python).
   - Example (Java):
     ```java
     CircuitBreakerConfig config = CircuitBreakerConfig.custom()
         .failureRateThreshold(50)
         .waitDurationInOpenState(Duration.ofMillis(1000))
         .build();
     CircuitBreaker circuitBreaker = CircuitBreaker.of("external-api", config);
     circuitBreaker.executeRunnable(() -> callExternalApi());
     ```

2. **Bulkheads:**
   - Isolate API calls in separate threads/processes to prevent cascading failures.
   - Example (Node.js):
     ```javascript
     const pool = new ThreadPool({ size: 10 });
     const worker = pool.queue(() => callExternalApi());
     ```

3. **Idempotency Keys:**
   - Ensure retries don’t cause duplicate operations.
   - Example (Request IDs):
     ```go
     // Go (using UUID)
     id := uuid.New().String()
     if !db.DuplicateRequestExists(id) {
         db.InsertRequest(id, payload)
     }
     ```

### **B. Observability**
1. **Centralized Logging:**
   - Use **ELK Stack**, **Loki**, or **Fluent Bit**.
   - Example (Spring Boot + ELK):
     ```properties
     logging:
       pattern:
         level: "%5p [${spring.application.name},%X{traceId}]"
     ```

2. **Metrics Collection:**
   - Track **latency percentiles (P99)**, **error rates**, and **throughput**.
   - Example (Prometheus annotations):
     ```yaml
     - alert: HighErrorRate
       expr: rate(http_requests_total{status=~"5.."}[1m]) > 0.1
       labels:
         severity: critical
     ```

3. **Distributed Tracing:**
   - Use **OpenTelemetry** to trace requests across microservices.
   - Example (Python):
     ```python
     from opentelemetry import trace
     tracer = trace.get_tracer(__name__)
     with tracer.start_as_current_span("external_api_call"):
         response = requests.get("https://api.example.com/data")
     ```

### **C. Testing Strategies**
1. **Contract Testing (Pact):**
   - Verify API consumers and providers using **PactIO**.
   - Example (Java + Pact):
     ```java
     @Test
     public void testConsumer() {
         Pact pact = new PactBuilder()
             .addInteraction("get_user", interaction -> interaction
                 .uponReceiving("GET /user/123")
                 .withRequestBody("{}")
                 .willRespondWith(200, "{\"id\": 123}")
             )
             .build();
         pact.verify();
     }
     ```

2. **Chaos Testing:**
   - Inject failures (e.g., kill pods, delay network) to test resilience.
   - Example (Chaos Mesh):
     ```yaml
     # Kill 10% of pods randomly
     apiVersion: chaos-mesh.org/v1alpha1
     kind: ChaosExperiment
     metadata:
       name: pod-killer
     spec:
       action: pod-kill
       mode: one
       selector:
         namespaces:
           - default
       value:
         percent: 10
     ```

3. **Load Testing (Locust, k6):**
   - Simulate traffic to find bottlenecks.
   - Example (k6):
     ```javascript
     import http from 'k6/http';

     export default function () {
       http.get('https://api.example.com/data', {
         headers: { 'Authorization': 'Bearer $TOKEN' }
       });
     }
     ```

---

## **5. Step-by-Step Debugging Workflow**
When an integration fails, follow this structured approach:

### **Step 1: Reproduce the Issue**
- **Manual Test:** Use `curl`/`Postman` to replicate the error.
  ```bash
  curl -v -X POST https://api.example.com/transaction \
       -H "Content-Type: application/json" \
       -H "Authorization: Bearer $TOKEN" \
       -d '{"amount": 100}'
  ```
- **Check Logs:** Look for recent errors in:
  - Application logs (Spring Boot Actuator, `/actuator/logs`).
  - External service logs (via their web UI or API).

### **Step 2: Isolate the Problem**
- **Is it the client or server?**
  - If the issue persists in Postman, the problem is likely on the **server** side.
  - If it works in Postman but fails in production, check:
    - Headers (missing `Authorization`, `X-API-Key`).
    - Payload differences (encoding, whitespace).
    - Network conditions (VPN, proxy).

- **Check Dependencies:**
  - Verify downstream services are up (`curl` their health endpoints).
  - Example:
    ```bash
    curl https://payment-gateway.example.com/health
    ```

### **Step 3: Analyze Logs and Traces**
- **Enable Distributed Tracing:**
  - Add `traceparent` header to requests:
    ```java
    // Java (OpenTelemetry)
    Span span = tracer.spanBuilder("external_call").startSpan();
    try (Scope scope = span.makeCurrent()) {
        span.setAttribute("http.url", url);
        response = client.execute(request);
    } finally {
        span.end();
    }
    ```
- **Correlate Logs:**
  - Use `X-Request-ID` or `traceId` to join logs across services.
  - Example query (ELK):
    ```
    service:api AND "status=500" AND request_id:abc123
    ```

### **Step 4: Apply Fixes (Based on Symptom Checklist)**
Refer to the **Common Issues and Fixes** section above.

### **Step 5: Validate and Monitor**
- **Test in Staging:** Ensure the fix doesn’t break other integrations.
- **Roll Out Gradually:** Use **canary deployments** for critical APIs.
- **Set Up Alerts:**
  - Example (Prometheus):
    ```yaml
    - alert: IntegrationErrorRateIncrease
      expr: rate(api_errors_total[5m]) > 0.1
      for: 1m
      labels:
        severity: critical
    ```

### **Step 6: Document and Prevent Recurrence**
- **Update API Documentation:** If the issue was due to schema changes.
- **Add Unit/Integration Tests:**
  ```java
  @Test
  public void testExternalApiCall_Failure() {
      when(externalApiClient.call()).thenThrow(new ApiTimeoutException());
      assertThrows(ApiTimeoutException.class, () -> service.processRequest());
  }
  ```
- **Improve Logging:**
  - Log **input/output** for all external calls.
  - Example (Python):
    ```python
    def call_external_api(url, data):
        log.info(f"Calling {url} with payload: {json.dumps(data)}")
        response = requests.post(url, json=data)
        log.info(f"Received response: {response.status_code} - {response.text}")
        return response