# **Debugging API Troubleshooting: A Practical Guide**

## **Introduction**
APIs are the backbone of modern software systems, enabling communication between microservices, mobile apps, web clients, and external third-party services. When APIs fail, they can disrupt entire applications, degrade user experience, and expose security vulnerabilities.

This guide provides a **structured, actionable approach** to debugging API-related issues efficiently, covering **symptoms, root causes, fixes, tools, and prevention strategies**. Whether dealing with **latency, failed requests, authentication errors, or connectivity issues**, this guide ensures you can resolve problems quickly without extensive downtime.

---

## **1. Symptom Checklist: Identifying API Issues**
Before diving into fixes, systematically verify the nature of the problem. Use this checklist to categorize the issue:

| **Symptom Category**       | **Possible Causes**                                                                 | **Key Questions**                                                                 |
|----------------------------|------------------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| **Request Failures**       | - Server errors (5xx) <br> - Client errors (4xx) <br> - Timeout errors            | - Is the API returning an error response? <br> - Is the client receiving a response? <br> - What’s the exact HTTP status? |
| **Slow Responses**         | - High server load <br> - Database bottlenecks <br> - Network latency             | - Are response times consistently high? <br> - Is the API under heavy load?       |
| **Authentication Errors**  | - Invalid tokens <br> - Expired sessions <br> - Misconfigured CORS/headers        | - Is the client sending valid auth headers? <br> - Are tokens being refreshed properly? |
| **Data Corruption**        | - Malformed JSON/XML <br> - Database inconsistencies <br> - Serialization issues   | - Is the response malformed? <br> - Does the data match expected schema?        |
| **Dependency Failures**    | - External service downtime <br> - Rate limiting <br> - Circuit breaker misconfig  | - Are external APIs returning errors? <br> - Is rate limiting being enforced?   |
| **Client-Side Issues**     | - Incorrect API endpoints <br> - Missing headers <br> - Network restrictions       | - Is the client making the correct request? <br> - Are firewalls/proxies blocking requests? |

**Actionable First Steps:**
1. **Check API Logs** – Look for errors in **server logs** (e.g., `/var/log/nginx/error.log`, application logs).
2. **Replicate the Issue** – Use `curl`, Postman, or a script to test the failing endpoint manually.
3. **Monitor System Metrics** – Use tools like **Prometheus, Datadog, or New Relic** to check CPU, memory, and request rates.
4. **Isolate the Problem** – Determine if the issue is **client-side** (e.g., misconfigured requests) or **server-side** (e.g., backend bugs).

---

## **2. Common API Issues & Fixes (With Code Examples)**

### **A. HTTP 5xx Errors (Server-Side Failures)**
**Symptoms:**
- `500 Internal Server Error`
- `502 Bad Gateway`
- `503 Service Unavailable`
- `504 Gateway Timeout`

**Root Causes & Fixes:**

| **Issue**               | **Possible Cause**                          | **Debugging Steps**                                                                 | **Code Fix (Example in Node.js/Express)** |
|-------------------------|--------------------------------------------|-------------------------------------------------------------------------------------|-------------------------------------------|
| **Database Connection Failures** | DB server down, misconfiguration            | - Check DB logs (`mysql error.log`, `pg_log`) <br> - Verify connection strings | ```javascript // Fix: Retry logic with exponential backoff const retryDB = async (fn) => { for (let i = 0; i < 3; i++) { try { return await fn(); } catch (err) { if (i === 2) throw err; await new Promise(r => setTimeout(r, 1000 * Math.pow(2, i))); } } }; ``` |
| **Uncaught Exceptions in Code** | Bug in business logic                     | - Review stack traces from logs <br> - Add error boundaries | ```javascript // Fix: Error handling middleware app.use((err, req, res, next) => { console.error(err.stack); res.status(500).send('Something broke!'); }); ``` |
| **Memory Leaks / High CPU** | Infinite loops, unclosed DB connections  | - Monitor memory usage (`top`, `htop`) <br> - Check for leaks in profilers | ```javascript // Fix: Use connection pooling const pool = createPool({ connectionLimit: 10, }); ``` |
| **Gateway Timeout (504)** | Slow downstream API calls                 | - Optimize API calls <br> - Implement timeouts | ```javascript // Fix: Set timeout in Axios const axios = require('axios'); const response = await axios.get('https://slow-api.com', { timeout: 3000 }); ``` |

---

### **B. HTTP 4xx Errors (Client-Side Issues)**
**Symptoms:**
- `400 Bad Request` (malformed data)
- `401 Unauthorized` (invalid auth)
- `403 Forbidden` (permission denied)
- `404 Not Found` (endpoint missing)
- `429 Too Many Requests` (rate limiting)

**Root Causes & Fixes:**

| **Issue**               | **Possible Cause**                          | **Debugging Steps**                                                                 | **Code Fix (Example in Python/Flask)** |
|-------------------------|--------------------------------------------|-------------------------------------------------------------------------------------|-------------------------------------------|
| **Invalid Request Body** | Missing/incorrect JSON                     | - Validate input with `Joi`/`Pydantic` <br> - Check client-side logs | ```python # Fix: Input validation from pydantic class UserCreate(BaseModel): username: str email: str @app.post("/register") def register(user: UserCreate): # Process valid data ``` |
| **Expired JWT Tokens**   | Short-lived tokens, no refresh logic       | - Check token expiry time <br> - Implement refresh flow | ```javascript // Fix: JWT refresh middleware const verifyToken = (req, res, next) => { const token = req.headers.authorization?.split(' ')[1]; if (!token) return res.status(401).send('Access denied'); try { const decoded = jwt.verify(token, process.env.JWT_SECRET); req.user = decoded; next(); } catch (err) { if (err.name === 'TokenExpiredError') { // Handle refresh logic } else { res.status(403).send('Invalid token'); } } }; ``` |
| **CORS Misconfiguration** | Incorrect `Access-Control-Allow-Origin`    | - Verify CORS headers <br> - Test with `curl -I` | ```javascript // Fix: Proper CORS middleware app.use(cors({ origin: 'https://yourclient.com', credentials: true })); ``` |
| **Rate Limiting (429)** | Too many requests in a short time          | - Check rate limit headers <br> - Implement client-side retries | ```javascript // Fix: Exponential backoff on 429 const retryOnRateLimit = async (fn) => { let retries = 3; while (retries--) { try { return await fn(); } catch (err) { if (err.response?.status !== 429) throw err; await new Promise(r => setTimeout(r, 1000 * Math.pow(2, retries))); } } }; ``` |

---

### **C. Performance & Latency Issues**
**Symptoms:**
- Slow responses (>500ms)
- Timeouts before response completes
- High p99 latency spikes

**Root Causes & Fixes:**

| **Issue**               | **Possible Cause**                          | **Debugging Steps**                                                                 | **Code Fix (Example in Go)** |
|-------------------------|--------------------------------------------|-------------------------------------------------------------------------------------|-------------------------------|
| **Unoptimized Database Queries** | Full table scans, missing indexes       | - Use `EXPLAIN ANALYZE` (PostgreSQL) <br> - Check slow query logs | ```go // Fix: Add indexes db, err := sql.Open("postgres", "...") if err != nil { log.Fatal(err) } _, err = db.Exec("CREATE INDEX idx_user_email ON users(email)") ``` |
| **Blocking I/O Operations** | Synchronous DB calls, no async            | - Use database drivers with async support (e.g., `go-pg`) <br> - Offload to workers | ```go // Fix: Async DB query ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second) defer cancel() var users []User err = db.SelectContext(ctx, &users, "SELECT * FROM users") ``` |
| **Large Response Payloads** | Over-fetching data                         | - Implement pagination (`limit`, `offset`) <br> - Use GraphQL for granular queries | ```python # Fix: Pagination @app.get("/users") def get_users(offset: int = 0, limit: int = 10): users = User.query.offset(offset).limit(limit).all() return users ``` |

---

### **D. Network & Connectivity Issues**
**Symptoms:**
- Intermittent failures
- `ECONNREFUSED`, `ENOTFOUND`
- Slow DNS resolution

**Root Causes & Fixes:**

| **Issue**               | **Possible Cause**                          | **Debugging Steps**                                                                 | **Fix** |
|-------------------------|--------------------------------------------|-------------------------------------------------------------------------------------|----------|
| **DNS Resolution Failures** | Misconfigured DNS, firewall blocking      | - Test DNS with `dig` or `nslookup` <br> - Check firewall rules (`ufw`, `iptables`) | Update `/etc/resolv.conf` or cloud DNS settings |
| **Proxy/Firewall Blocking** | Corporate proxies, cloud security rules   | - Check `curl -v` output <br> - Test with `telnet` | Modify proxy settings or whitelist IPs |
| **Load Balancer Issues** | Sticky sessions, health check failures    | - Check load balancer logs (AWS ALB, Nginx) <br> - Verify health endpoints | ```nginx # Fix: Proper health check server { location /health { return 200 'OK'; } } ``` |

---

## **3. Debugging Tools & Techniques**

### **A. Logging & Monitoring**
| **Tool**               | **Use Case**                                                                 | **Example Command** |
|-------------------------|-----------------------------------------------------------------------------|---------------------|
| **Structured Logging** | Correlate logs with traces (`JSON` format)                                   | `winston` (Node), `structlog` (Python) |
| **APM Tools**          | Track requests end-to-end (`New Relic`, `Datadog`, `OpenTelemetry`)          | Install agent: `opentelemetry-collector` |
| **Distributed Tracing** | Identify latency bottlenecks (`Jaeger`, `Zipkin`)                            | ```bash curl -H "x-request-id: 123" http://your-api ``` |
| **Log Aggregation**    | Centralized logs (`ELK Stack`, `Loki`, `Splunk`)                              | `filebeat` for log shipping |

### **B. API Testing & Validation**
| **Tool**               | **Use Case**                                                                 | **Example Command** |
|-------------------------|-----------------------------------------------------------------------------|---------------------|
| **Postman/Newman**     | Test API endpoints, simulate load                                           | `newman run collection.json --reporters cli,junit` |
| **cURL**               | Quick manual testing                                                          | `curl -X POST -H "Content-Type: application/json" -d '{"key": "value"}' http://api` |
| **K6**                 | Load testing & performance benchmarking                                     | ```javascript import http from 'k6/http'; export default function () { http.get('https://api.example.com'); } ``` |
| **Swagger/OpenAPI**    | Document and validate API contracts                                           | Generate spec with `swagger-cli` |

### **C. Network Debugging**
| **Tool**               | **Use Case**                                                                 | **Example Command** |
|-------------------------|-----------------------------------------------------------------------------|---------------------|
| **tcpdump/Wireshark**  | Inspect network traffic (HTTP, gRPC)                                        | `tcpdump -i eth0 -w capture.pcap` |
| **mtr/traceroute**     | Diagnose network latency & hops                                               | `mtr api.example.com` |
| **curl -v**            | Debug HTTP headers & connections                                             | `curl -v -X GET http://api` |
| **ngrep**              | Filter HTTP traffic by keywords                                              | `ngrep -d any port 80 "error"` |

### **D. Database Debugging**
| **Tool**               | **Use Case**                                                                 | **Example Command** |
|-------------------------|-----------------------------------------------------------------------------|---------------------|
| **pgBadger** (PostgreSQL) | Analyze slow queries & lock issues                                         | `pgbadger --summary logfile.log` |
| **EXPLAIN ANALYZE**    | Optimize query plans                                                         | ```sql EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'test@example.com'; ``` |
| **Database Replay**    | Reproduce issues in a controlled env (`mysqlpump`, `pg_dump`)              | `mysqldump --where="time > '2023-01-01'" -u user db > issue.sql` |

---

## **4. Prevention Strategies**

### **A. Proactive Monitoring**
1. **Set Up Alerts for:**
   - High error rates (`>1%` 5xx responses)
   - Latency spikes (`p99 > 1s`)
   - External service failures
   - Database connection drops
2. **Use SLOs (Service Level Objectives):**
   - Example: **"API must respond in <500ms 99.9% of the time."**
   - Tools: **Prometheus Alertmanager**, **Grafana Alerts**

### **B. Rate Limiting & Throttling**
- Implement **token bucket** or **leaky bucket** algorithms.
- Example (Node.js with `rate-limiter-flexible`):
  ```javascript
  const RateLimiter = require('rate-limiter-flexible');
  const limiter = new RateLimiter.MemoryRateLimiter({
    points: 100, // 100 requests
    duration: 60, // per 60 seconds
  });

  app.use(async (req, res, next) => {
    try {
      await limiter.consume(req.ip);
      next();
    } catch (err) {
      res.status(429).send('Too many requests');
    }
  });
  ```

### **C. Retry & Circuit Breaker Patterns**
- **Exponential Backoff:** Retry failed requests with increasing delays.
- **Circuit Breaker:** Stop retrying if failures persist (e.g., **Hystrix**, **Bull**).
- Example (Python with `tenacity`):
  ```python
  from tenacity import retry, stop_after_attempt, wait_exponential

  @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
  def call_external_api():
      response = requests.get("https://external-api.com")
      response.raise_for_status()
      return response.json()
  ```

### **D. Failover & Redundancy**
1. **Database Replication:**
   - Use **read replicas** for scaling reads.
   - Example (PostgreSQL):
     ```sql
     SELECT * FROM pg_create_physical_replication_slot('slot1');
     ```
2. **Service Mesh (Istio, Linkerd):**
   - Handle **gRPC timeouts** and **retries** automatically.
3. **Multi-Region Deployment:**
   - Deploy APIs in **AWS us-east-1 & eu-west-1** with **Route53 failover**.

### **E. Input Validation & Security**
1. **Validate All Requests:**
   - Use **Zod** (JavaScript), **Pydantic** (Python), or **Schema Validator**.
   - Example (Python):
     ```python
     from pydantic import BaseModel, ValidationError

     class UserCreate(BaseModel):
         username: str
         email: str
         password: str  # Never store plaintext!

     try:
         user = UserCreate(**request.json())
     except ValidationError as e:
         return {"error": str(e)}, 400
     ```
2. **SQL Injection Protection:**
   - Always use **prepared statements** (ORMs like SQLAlchemy, TypeORM help).
   - Example (Node.js with `pg`):
     ```javascript
     const result = await db.query('SELECT * FROM users WHERE email = $1', [userEmail]);
     ```
3. **Rate Limiting by User/Endpoint:**
   - Track limits per **user IP**, **API key**, or **endpoint**.

### **F. Chaos Engineering**
- **Test Resilience with Chaos Monkey:**
  - Randomly kill pods (`kubectl delete pod <pod-name>`).
  - Use **Gremlin** or **Chaos Mesh** for auto-failing services.
- **Examples:**
  - **Kill a database pod** → Check if API recovers with read replicas.
  - **Throttle network** → Test gRPC timeouts.

---

## **5. Step-by-Step Debugging Workflow**

### **Step 1: Reproduce the Issue**
- **Manual Test:** Use `curl`, Postman, or a script.
- **Automated Test:** Run existing test suites.
- **Check Logs:** Look for errors in:
  - Application logs (`/var/log/app.log`)
  - Web server logs (`/var/log/nginx/error.log`)
  - Database logs

### **Step 2: Isolate the Problem**
| **Question**               | **How to Check**                                                                 |
|----------------------------|---------------------------------------------------------------------------------|
| Is it a **client-side** issue? | Test with `curl` (no client-side processing).                                   |
| Is it a **network** issue?  | Check `tcpdump`, `mtr`, proxy logs.                                             |
| Is it a **server-side** issue? | Review application logs, metrics (Prometheus).                                  |
| Is it a **dependency** issue? | Test downstream APIs manually.                                                  |

### **Step 3: Apply Fixes Based on Symptoms**
| **Symptom**               | **Likely Fix**                                                                 |
|---------------------------|-------------------------------------------------------------------------------|
| **500 Errors**            | Check backend logs,