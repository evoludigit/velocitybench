# **Debugging Edge Strategies Pattern: A Troubleshooting Guide**
*(For Backend Engineers Focused on Performance & Resilience)*

---

## **1. Introduction**
The **Edge Strategies** pattern involves processing requests at the edge of a network (e.g., CDN, API Gateway, or global load balancer) to reduce latency, offload computation, or enforce policies (e.g., rate limiting, A/B testing). Common implementations include:
- **CDN Caching** (e.g., Cloudflare, Fastly, Akamai)
- **Edge Computing** (e.g., AWS Lambda@Edge, Cloudflare Workers, Azure Edge Functions)
- **Global Load Balancing** (e.g., Nginx Ingress, AWS ALB/Gateway)
- **Request Transformation** (e.g., header rewriting, query parameter modification)

This guide assumes you’re debugging issues where edge strategies fail to behave as expected.

---

## **2. Symptom Checklist**
Before diving into fixes, verify these symptoms:

| **Symptom**                          | **Possible Cause**                          | **Quick Check** |
|--------------------------------------|--------------------------------------------|-----------------|
| Requests failing with `5xx` (upstream errors) | Edge node misconfiguration | Check CloudTrail (AWS), CDN logs, or edge function traces |
| High latency or timeouts             | Edge node overloaded or misrouted          | Monitor edge metrics (e.g., Cloudflare Workers API) |
| Incorrect responses (e.g., cached stale data) | Cache TTL misconfiguration | Verify cache headers (`Cache-Control`) in responses |
| Unauthorized access at edge         | Missing or incorrect auth headers          | Test with `curl` or Postman; check edge config for auth |
| Region-specific failures             | Awareness rules or failover misconfigured   | Test from multiple regions (e.g., Cloudflare’s "Where From" tool) |
| Missing/transformed request data     | Edge middleware altering payloads         | Compare raw request/response between edge and backend |

---

## **3. Common Issues & Fixes (Code & Config)**
### **Issue 1: Cache Invalidation Not Working**
**Symptoms:**
- Users see stale data after cache invalidation.
- `Cache-Control: max-age=0` headers ignored.

**Root Causes:**
- Incorrect cache key generation (e.g., missing dynamic segments).
- No cache invalidation endpoint (e.g., Purge API not called).
- TTL too long for dynamic content.

**Fixes:**

#### **Cloudflare Workers (JavaScript)**
```javascript
// Ensure cache key includes dynamic parts (e.g., query params)
const cacheKey = `${request.url}?${request.query}`;

// Set short TTL for dynamic content
return new Response(html, {
  headers: {
    "Cache-Control": "public, max-age=60", // 60s for dynamic content
  },
});
```

#### **Fastly VCL (Lua-like)**
```vcl
# Invalidate cache on specific path
if (req.url ~ "^/api/invalidate") {
    purge("https://example.com$uri");
    return (synth(410, "Purged"));
}

# Short TTL for dynamic content
if (req.url ~ "^/api/dynamic") {
    set req.http.cache_control = "public, max-age=30";
}
```

**Prevention:**
- Use **cache keys with versioning** (e.g., `v2_${path}`).
- Implement **TTL-based invalidation** (e.g., `max-age=0, must-revalidate` for private content).

---

### **Issue 2: Edge Function Timeouts or Crashes**
**Symptoms:**
- `504 Gateway Timeout` or `500 Internal Error` in edge logs.
- Function logs show uncaught exceptions.

**Root Causes:**
- Infinite loops or heavy computations.
- Missing error handling.
- Cold starts (for serverless edge functions).

**Fixes:**

#### **AWS Lambda@Edge (Node.js)**
```javascript
// Add timeout handling and logging
exports.handler = async (event, context, callback) => {
  try {
    const result = await transformRequest(event.Records[0].cf.request);
    return { status: "200", body: result };
  } catch (err) {
    // Log to CloudWatch for debugging
    console.error("Edge Function Error:", err);
    return { status: "500", body: "Error processing request" };
  }
};

// Use async/await to avoid timeouts
const transformRequest = async (request) => {
  // Heavy work should be async (e.g., DB calls with retries)
  const data = await fetchAsyncData();
  return data;
};
```

**Prevention:**
- **Split logic** into smaller functions with timeouts.
- Use **Cold Start Mitigation**:
  - Provisioned Concurrency (AWS).
  - Keep functions lightweight (<100ms exec time).
  - Test with **CloudWatch Logs Insights**:
    ```sql
    filter @type = "REPORT"
    | stats count(*) by @message
    | sort @timestamp desc
    ```

---

### **Issue 3: Incorrect Request Forwarding (Headers/Missing Data)**
**Symptoms:**
- Backend receives malformed requests (e.g., missing `Authorization` header).
- Edge modifies query parameters unexpectedly.

**Root Causes:**
- Missing **header forwarding rules**.
- **Query parameter transformation** (e.g., URL encoding issues).

**Fixes:**

#### **Cloudflare Workers (Pass Through Headers)**
```javascript
// Forward original headers (except Cloudflare-added ones)
const headers = Object.fromEntries(
  request.headers.entries().filter(([name]) =>
    !name.startsWith("cf-")
  )
);

return fetch(request, {
  headers,
});
```

#### **Nginx Ingress (Kubernetes)**
```yaml
# Ensure headers are preserved in annotations
metadata:
  annotations:
    nginx.ingress.kubernetes.io/configuration-snippet: |
      proxy_hide_header "X-Forwarded-For";
      proxy_set_header X-Real-IP $remote_addr;
```

**Prevention:**
- **Whitelist/Blacklist Headers**:
  - Cloudflare: Use `Request Headers` settings.
  - Nginx: Use `proxy_hide_header`/`proxy_pass_header`.
- **Test with `curl`**:
  ```bash
  curl -v -H "X-My-Header: test" https://your-edge-domain.com
  ```

---

### **Issue 4: Geographic Routing Failures**
**Symptoms:**
- Users in `Region X` get an error, while others don’t.
- `X-Cloudflare-Region` (or equivalent) shows unexpected values.

**Root Causes:**
- Misconfigured **geographic routing** (e.g., wrong `geoip` rules).
- **Failover rules** not updating (e.g., DNS propagation lag).

**Fixes:**

#### **Cloudflare Workers (Geo-Based Logic)**
```javascript
// Route based on visitor location
const visitorCountry = request.cf.country;

if (visitorCountry === "US") {
  return fetch("https://us-backend.example.com" + request.url);
} else {
  return fetch("https://eu-backend.example.com" + request.url);
}
```

#### **AWS Route 53 (Failover)**
- Verify **health checks** are working:
  ```bash
  aws route53 get-health-check --health-check-id YOUR_CHECK_ID
  ```
- Ensure **DNS TTL** is low (e.g., `300` seconds) for quick propagation.

**Prevention:**
- **Test with `dig`/`nslookup`**:
  ```bash
  dig your-domain.com @ns1.cloudflare.com
  ```
- Use **Cloudflare’s "Where From" Tool** to debug regional behavior.

---

### **Issue 5: Rate Limiting Misconfiguration**
**Symptoms:**
- Legitimate users hit `429 Too Many Requests`.
- Rate limits differ by region.

**Root Causes:**
- Global rate limit too strict.
- Missing **IP-based vs. token bucket** distinction.

**Fixes:**

#### **Cloudflare Workers (Rate Limiting)**
```javascript
// Token bucket algorithm (simplified)
const maxRequests = 100;
const windowMs = 60 * 1000; // 1 minute
const key = `rate_limit:${request.headers.get("CF-Connecting-IP")}`;

const now = Date.now();
const stored = await KV.get(key) || { count: 0, lastReset: now };

if (stored.count >= maxRequests && now - stored.lastReset < windowMs) {
  return new Response("Rate limit exceeded", { status: 429 });
}

// Update counter
await KV.put(key, {
  count: stored.count + 1,
  lastReset: stored.count === maxRequests ? now : stored.lastReset,
});
```

**Prevention:**
- **Use CDN rate limiting** (e.g., Cloudflare’s built-in limits).
- **Monitor limits** with:
  ```bash
  # Cloudflare API
  curl "https://api.cloudflare.com/client/v4/accounts/YOUR_ACCOUNT/rulesets/RULESET_ID/evaluations" \
    -H "Authorization: Bearer YOUR_TOKEN"
  ```

---

## **4. Debugging Tools & Techniques**
### **A. Logs & Metrics**
| **Tool**               | **Use Case**                                  | **Example Query**                          |
|------------------------|---------------------------------------------|--------------------------------------------|
| **Cloudflare Workers** | Edge function logs                          | `curl "https://api.cloudflare.com/client/v4/accounts/YOUR_ACCOUNT/workers/scripts/WORKER_ID/logs"` |
| **AWS CloudWatch**     | Lambda@Edge errors                          | `filter @type = "REPORT" | stats count(*) by @message` |
| **Fastly Debug Tool**  | VCL execution flow                          | `fastly-request-debugger` (CLI)           |
| **Nginx Access Logs**  | Ingress traffic analysis                    | `grep "500" /var/log/nginx/access.log`     |
| **Datadog/New Relic**  | Edge performance metrics                    | `avg:aws.lambda.duration{Region:us-east-1}` |

### **B. Real-Time Testing**
- **Cloudflare Warp** (test from different locations):
  ```bash
  curl -H "CF-Connecting-IP: 123.45.67.89" https://your-site.com
  ```
- **Postman/Insomnia** (test edge-specific headers):
  ```json
  // Postman headers for testing
  {
    "X-Edge-Location": "NYC",
    "Authorization": "Bearer test"
  }
  ```
- **Browser DevTools** (check `Network` tab for edge responses):
  - Look for `x-edge-location` or `cf-cache-status` headers.

### **C. Post-Mortem Analysis**
1. **Reproduce the issue** locally (e.g., `curl` with headers).
2. **Compare edge vs. backend responses**:
   ```bash
   curl -v https://edge-domain.com/api | grep "Cache-Control"
   curl -v https://backend-domain.com/api | grep "Cache-Control"
   ```
3. **Check edge provider dashboards**:
   - Cloudflare: [Edge Workers Dashboard](https://dash.cloudflare.com/)
   - AWS: [CloudFront Distribution Metrics](https://console.aws.amazon.com/cloudfront/)

---

## **5. Prevention Strategies**
### **A. Configuration Best Practices**
1. **Edge Function Design**:
   - Keep functions **stateless** and **idempotent**.
   - Avoid **synchronous database calls** (use async queues).
   - Set **memory limits** (e.g., Cloudflare Workers: 256MB).

2. **Caching**:
   - Use **dynamic cache keys** (e.g., include `Accept-Language`).
   - Set **short TTLs** for dynamic content (`max-age=30`).
   - Implement **cache warming** for critical paths.

3. **Geographic Routing**:
   - Use **multi-region backends** with failover.
   - Test **DNS propagation** with `dig`.

4. **Security**:
   - Whitelist/blacklist **headers** to prevent header manipulation.
   - Use **edge auth middleware** (e.g., Cloudflare Access).

### **B. Monitoring & Alerts**
| **Metric**               | **Tool**               | **Alert Condition**                     |
|--------------------------|------------------------|-----------------------------------------|
| Edge function errors     | Cloudflare Logs        | `errors > 5` in 5 minutes               |
| Cache hit ratio          | Fastly Dash            | `hit_ratio < 80%` for 10 minutes        |
| Latency spikes           | Datadog                | `avg:edge_latency > 500ms`              |
| Rate limit hits          | Cloudflare Rules       | `429_responses > 100` in 1 hour         |

**Example Alert (Datadog):**
```json
// Alert when Cloudflare Workers errors exceed threshold
{
  "monitor": {
    "type": "query_alert",
    "query": "sum:cloudflare.workers.errors{environment:prod} > 5",
    "name": "High Edge Function Errors",
    "message": "Edge functions failing in production!",
    "notify": ["@oncall-team"]
  }
}
```

### **C. Testing Strategies**
1. **Load Test Edge Paths**:
   - Use **Locust** or **k6** to simulate traffic:
     ```javascript
     // k6 script for edge testing
     import http from 'k6/http';

     export default function () {
       http.get('https://your-edge-domain.com/api', {
         headers: { 'X-My-Header': 'test' },
       });
     }
     ```
2. **Chaos Engineering**:
   - Kill edge nodes (e.g., AWS ALB) to test failover.
   - Use **Cloudflare’s "Failover" feature** to simulate outages.
3. **Canary Deployments**:
   - Route **1% of traffic** to a new edge config before full rollout.

---

## **6. Quick Reference Cheat Sheet**
| **Problem**               | **First Check**                          | **Quick Fix**                          |
|---------------------------|------------------------------------------|----------------------------------------|
| Cache not updating        | TTL or invalidation endpoint             | Reduce TTL; call `/invalidate` API     |
| Edge function crashes     | Logs for uncaught errors                 | Add `try/catch`; reduce runtime        |
| Missing request headers   | Forwarding rules                         | Whitelist headers in config            |
| Regional failures         | GeoIP/dns propagation                    | Test with `dig`; lower DNS TTL         |
| Rate limiting users       | Global vs. per-IP limits                 | Increase limits or use token bucket    |

---

## **7. When to Escalate**
- **Provider-Side Issues**:
  - Outages (e.g., Cloudflare outage: [status.cloudflare.com](https://www.cloudflare.com/status/)).
  - Configuration limits (e.g., "You’ve hit the edge function concurrency limit").
- **Unresolvable Debugging**:
  - No logs or metrics available.
  - Issue only reproduces in specific regions (may require provider support).

**Escalation Template (Example for Cloudflare Support):**
```
Subject: Edge Worker "Missing Data" Issue in EU Regions

Hi Support,
- **Reproduction Steps**: Accessing `https://api.example.com/data` from Germany fails with `404`.
- **Expected**: Data should return from `eu-backend.example.com`.
- **Actual**: Response is `404`; CF-Connecting-IP shows `DE` but routing seems incorrect.
- **Logs**: Attached edge function logs (no errors, but empty response).
- **Diagnostics**: Ran `dig api.example.com` from DE IP—seems to resolve correctly.

Can you check if there’s a routing misconfiguration or missing `geoip` rule?
Thanks!
```

---

## **8. Further Reading**
- [Cloudflare Workers Debugging Guide](https://developers.cloudflare.com/workers/wrangler/configuration/#debugging)
- [AWS Lambda@Edge Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/lambda-edge.html)
- [Fastly VCL Debugging Tips](https://docs.fastly.com/guides/debugging-vcl-scripts)