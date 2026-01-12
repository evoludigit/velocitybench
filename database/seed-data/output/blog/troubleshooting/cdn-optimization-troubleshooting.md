# **Debugging "CDN & Content Delivery Optimization" – A Troubleshooting Guide**

## **Introduction**
A **Content Delivery Network (CDN)** optimizes content delivery by distributing files across geographically dispersed servers (edge locations). When misconfigured or underperforming, CDNs can introduce latency, failures, and reliability issues. This guide helps diagnose and resolve common problems efficiently.

---

## **1. Symptom Checklist**
Before diving into fixes, verify these symptoms:

✅ **Performance Issues**
- Slow page loads (TTFB > 500ms) despite CDN usage.
- High time-to-first-byte (TTFB) or slow resource loading.
- Users in specific regions experience degraded performance.

✅ **Visibility Problems**
- Lack of real-time metrics on CDN cache hit/miss rates.
- Inconsistent performance across regions.
- No clear correlation between CDN usage and backend load.

✅ **Reliability & Failure Issues**
- Frequent 5xx errors (e.g., `502 Bad Gateway`, `504 Gateway Timeout`).
- CDN purging or invalidation failures.
- Missed cache updates (stale content delivered).

✅ **Scaling Problems**
- Backend overwhelmed when CDN misses increase.
- High latency spikes during traffic surges.

---
## **2. Common Issues & Fixes**

### **Issue 1: High Cache Miss Rates**
**Symptoms:**
- Users see freshness headers (`Cache-Control: no-cache`) despite CDN usage.
- Backend logs show excessive `GET` requests for cached resources.

**Root Causes:**
- Incorrect cache keys or TTL settings.
- Dynamic content not marked as cacheable.
- Improper cache invalidation rules.

**Fixes:**
#### **2.1.1 Verify Cache Configuration**
```bash
# Check Cache-Control headers in browser DevTools (Network tab)
# Should show long TTL (e.g., `max-age=3600`) for static assets
```
**Example (Nginx CDN Config):**
```nginx
location /static/ {
    expires 1y;
    add_header Cache-Control "public, max-age=31536000";
}
```

#### **2.1.2 Use Proper Cache Keys**
```bash
# Ensure CDN cache uses correct keys (e.g., ETag/Signature)
# Avoid query strings in cache keys unless necessary
```

#### **2.1.3 Test Cache Invalidation**
```bash
# Manually purge a file via CDN dashboard (e.g., Cloudflare API)
curl -X POST "https://api.cloudflare.com/client/v4/zones/<ZONE_ID>/purge_cache" \
     -H "Authorization: Bearer <TOKEN>" \
     -d '{"files":["/path/to/file"]}'
```

---

### **Issue 2: 5xx Errors (502/504/Gateway Failures)**
**Symptoms:**
- Users see `502 Bad Gateway` or `504 Gateway Timeout`.
- CDN logs show upstream failures.

**Root Causes:**
- Backend origin server timeout.
- CDN edge servers unable to connect to origin.
- Misconfigured failover rules.

**Fixes:**
#### **2.2.1 Check Backend Health**
```bash
# Verify backend responds to health checks
curl -v http://<BACKEND_IP>:<PORT>/health
```
**Fix (Nginx Timeout Adjustment):**
```nginx
proxy_connect_timeout 60s;
proxy_send_timeout 60s;
proxy_read_timeout 60s;
```

#### **2.2.2 Configure CDN Failover**
```bash
# Use CDN failover to secondary origin if primary fails
# Example (Cloudflare Edge Config)
"failover": {
  "primary": "https://origin.example.com",
  "secondary": "https://backup-origin.example.com"
}
```

---

### **Issue 3: Stale Content Delivery**
**Symptoms:**
- Users see outdated content (e.g., updated HTML but stale JS/CSS).
- Cache invalidation not working.

**Root Causes:**
- Incorrect cache purging logic.
- Long TTL preventing quick updates.

**Fixes:**
#### **2.3.1 Use Short TTL for Dynamic Content**
```nginx
# Example: Short TTL for API responses
location ~ ^/api/ {
    expires 5m;
    add_header Cache-Control "private, max-age=300";
}
```

#### **2.3.2 Automate Cache Purge on Updates**
```python
# Example: Invalidates CDN cache on file changes (Flask)
@app.route("/update-cache")
def purge_cache():
    import requests
    requests.post("https://api.cloudflare.com/client/v4/zones/<ZONE_ID>/purge_cache",
                 json={"files": ["/static/newfile.js"]})
    return "Purged"
```

---

## **3. Debugging Tools & Techniques**

### **Tool 1: CDN Provider Dashboards**
- **Cloudflare:** [CDN Performance](https://www.cloudflare.com/dashboards/) – Check hit rates, latency, errors.
- **AWS CloudFront:** [CloudFront Metrics](https://console.aws.amazon.com/cloudfront/) – Monitor cache behavior.

**Example (CloudFront Logs Analysis):**
```bash
# Filter CloudFront logs for 5xx errors
grep "HTTP 502" /var/log/cloudfront/*.log | awk '{print $12}'
```

### **Tool 2: Browser DevTools**
- **Network Tab:** Check response headers (`Cache-Control`, `ETag`).
- **Performance Tab:** Identify slow-loading resources.

**Example (Check Cacheability):**
```bash
# Open browser DevTools → Network → Filter "static" → Check headers
```

### **Tool 3: Synthetic Monitoring (Synthetic Checks)**
```bash
# Use tools like Pingdom/K6 to simulate user requests
k6 run script.js
# Example script.js:
import http from 'k6/http';
import { check } from 'k6';

export default function () {
  const res = http.get('https://your-cdn-url/path');
  check(res, {
    'Status is 200': (r) => r.status === 200,
    'Cache-Control valid': (r) => r.headers['cache-control']?.includes('public'),
  });
}
```

### **Tool 4: Logging & Tracing**
- **CDN Logs:** Analyze for errors (`5xx`, `404`).
- **Backend Logs:** Check for timeouts (`ETIMEDOUT`, `ECONNREFUSED`).

**Example (Tail Cloudflare Logs):**
```bash
# If using Cloudflare Stream, check logs via API
curl "https://api.cloudflare.com/client/v4/accounts/<ACCOUNT_ID>/stream/logs" \
     --header "Authorization: Bearer <TOKEN>"
```

---

## **4. Prevention Strategies**

### **Best Practice 1: Monitoring & Alerts**
- **Set up alerts** for:
  - Cache miss rate > 10%.
  - 5xx errors > 0% for 5 minutes.
- **Example (Cloudflare Alerts):**
  ```bash
  # Configure via Cloudflare Dashboard → Performance → Alerts
  ```

### **Best Practice 2: Cache Optimization**
- **Use Smart Cache:**
  ```nginx
  # Cache only GET requests with no cookies
  if ($request_method !~ ^(GET|HEAD)$) {
      proxy_cache_bypass on;
  }
  ```
- **Leverage Browser Caching:**
  ```nginx
  add_header X-Cache "hit" if (upstream_cache_status = HIT);
  add_header X-Cache "miss" if (upstream_cache_status = MISS);
  ```

### **Best Practice 3: Automated Testing**
- **Unit Test CDN Behavior:**
  ```python
  # Example: Assert CDN returns cached content
  def test_cdn_cache():
      response = requests.get("https://cdn.example.com/file.js")
      assert response.headers["Cache-Control"] == "public, max-age=3600"
  ```

### **Best Practice 4: Failover & Redundancy**
- **Use Multiple CDN Providers (Hybrid CDN).**
- **Example (AWS CloudFront + Fastly):**
  ```bash
  # Route traffic based on region (CloudFront + Fastly)
  CF = CloudFront("https://main-origin")
  Fastly = Fastly("https://fastly-cache")
  # Use Lambda@Edge to route dynamically
  ```

---

## **Conclusion**
Proper CDN optimization requires:
✔ **Correct caching policies** (TTL, headers).
✔ **Robust error handling** (failover, timeouts).
✔ **Monitoring & alerts** (cache misses, 5xx errors).
✔ **Automated invalidation** (purge on updates).

By following this guide, you can **diagnose, fix, and prevent** CDN-related performance and reliability issues efficiently.

---
**Next Steps:**
- Review CDN logs for anomalies.
- Adjust cache strategies based on traffic patterns.
- Implement automated testing for cache behavior.