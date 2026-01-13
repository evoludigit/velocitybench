# **Debugging Edge Load Balancing & Routing: A Troubleshooting Guide**
*Focused on quick resolution of latency, routing failures, and edge traffic misdirection issues.*

---

## **1. Title & Overview**
**Title:** *Debugging Edge Troubleshooting: A Troubleshooting Guide for Load Balancers, CDNs, and Global Routing Issues*

**Purpose:** This guide helps backend engineers quickly diagnose and resolve issues related to:
- **Edge CDN failures** (missed cache, slow responses)
- **Load balancer misrouting** (traffic sent to wrong regions/servers)
- **DNS or routing loopbacks** (traffic not reaching intended destinations)
- **Latency spikes** (edge nodes degrading performance)

Edge issues often manifest as **system-wide latency, 5xx errors, or inconsistent user experiences**. Unlike monolithic backends, edge problems require **distributed debugging** (checking multiple regions, CDN headers, and routing paths).

---

## **2. Symptom Checklist**
Before diving into fixes, confirm the issue’s **scope** and **edge-related nature**:

| **Symptom**                          | **Edge-Related?** | **Backend-Related?** |
|---------------------------------------|------------------|----------------------|
| Sudden 10x latency in a specific region | ✅ Yes           | ❌ No                |
| Cache-HIT rate drops below 90%        | ✅ Yes           | ❌ No                |
| Users in **Asia** get redirected to **US** servers | ✅ Yes       | ❌ No                |
| `HTTP 429 (Too Many Requests)` at edge | ✅ Yes           | Maybe (rate limiting) |
| `5xx` errors from **edge nodes only** | ✅ Yes           | ❌ No                |
| **DNS resolution fails** for edge-hosted domains | ✅ Yes      | ❌ No                |
| **HTTP 307/308 redirects loop**      | ✅ Yes           | ❌ No                |

**Rule of Thumb:**
- If the issue **affects only specific regions**, it’s likely an edge problem.
- If the issue **happens globally**, check backend health first.

---

## **3. Common Issues & Fixes (Code + Commands)**

### **Issue 1: CDN Cache Misses (High Latency)**
**Symptom:** `Cache-Control: private` headers forcing back-to-origin fetches.
**Root Cause:**
- Cache headers misconfigured (e.g., `no-cache` or `no-store`).
- Dynamic content (e.g., `/api/v1/users/{id}`) being cached.

#### **Fix: Correct Cache Headers**
**Cloudflare (Edge Worker):**
```javascript
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
});

async function handleRequest(request) {
  const url = new URL(request.url);
  const isCacheable = url.pathname.startsWith('/static/');

  if (isCacheable) {
    return new Response('Cached content', {
      headers: { 'Cache-Control': 'public, max-age=3600' }
    });
  }
  // Fallback to origin
  return fetch(request);
}
```

**Nginx (CDN Invalidation):**
```nginx
location /static/ {
  proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=static:10m inactive=60m;
  proxy_cache static;
  proxy_cache_valid 200 301 302 3600m;
}
```

**Debugging:**
```bash
curl -I https://yourdomain.com/static/file.jpg  # Check `Cache-Control`
grep -i "cache" /var/log/nginx/error.log        # Look for cache misconfigs
```

---

### **Issue 2: Load Balancer Misrouting (Wrong Region)**
**Symptom:** Users in **Tokyo** get routed to **Silicon Valley** (high latency).
**Root Cause:**
- **Geographic-based LB** misconfigured (e.g., AWS Global Accelerator regions not updated).
- **CDN origin failover** sending traffic to a degraded region.

#### **Fix: Verify Routing Rules**
**AWS Global Accelerator:**
```bash
aws globalaccelerator update-listener \
  --listener-arn <ARN> \
  --attributes '[
    {Key="ForwardingActionType", Value="BYPASS"},
    {Key="DnsName", Value="your-edge-domain.com"}
  ]'
```

**Cloudflare LB Settings:**
```bash
curl -X PUT "https://api.cloudflare.com/client/v4/zones/<ZONE_ID>/load_balancers/<LB_ID>/basic_settings" \
  -H "Authorization: Bearer <API_KEY>" \
  -H "Content-Type: application/json" \
  --data '{
    "geolocation_routing": {
      "enabled": true,
      "pools": [
        {
          "name": "Asia",
          "origins": ["asia1.example.com"]
        }
      ]
    }
  }'
```

**Debugging:**
```bash
dig +short yourdomain.com  # Check CDN DNS records
aws route53 list-health-checks  # Verify failover health checks
```

---

### **Issue 3: HTTP Redirect Loops (307/308)**
**Symptom:** Users stuck in **redirect loops** (e.g., `/login` → `/login?edge=true` → `/login`).
**Root Cause:**
- **Edge function misrouting** (e.g., Cloudflare Workers adding `?edge=true`).
- **Backend URL changes** not propagated to CDN.

#### **Fix: Trace Redirect Chain**
**Cloudflare Workers Debugging:**
```javascript
addEventListener('fetch', event => {
  event.respondWith(handleRedirect(event.request));
});

async function handleRedirect(request) {
  const url = new URL(request.url);
  if (url.searchParams.has('edge=true')) {
    return Response.redirect('https://yourdomain.com/login', 301);
  }
  // ... rest of logic
}
```

**Nginx Redirect Fix:**
```nginx
server {
  listen 80;
  server_name yourdomain.com;
  return 301 https://yourdomain.com/login;  # Permanent redirect
}
```

**Debugging:**
```bash
curl -v -L https://yourdomain.com/login  # -L follows redirects
grep -i "redirect" /var/log/nginx/access.log
```

---

### **Issue 4: DNS Propagation Delays**
**Symptom:** New CDN/edge domain not resolving for hours.
**Root Cause:**
- **DNS TTL too high** (e.g., `86400` seconds).
- **CDN DNS records not updated** (e.g., Cloudflare `DNS only` not enabled).

#### **Fix: Shorten TTL Temporarily**
```bash
# AWS Route 53 (TTL reduction)
aws route53 change-resource-record-sets \
  --hosted-zone-id <ZONE_ID> \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "yourdomain.com",
        "Type": "CNAME",
        "TTL": 300,
        "ResourceRecords": [{"Value": "cname.cloudflare.com"}]
      }
    }]
  }'
```

**Cloudflare DNS Fix:**
```bash
curl -X PUT "https://api.cloudflare.com/client/v4/zones/<ZONE_ID>/dns_records/<RECORD_ID>" \
  -H "Authorization: Bearer <API_KEY>" \
  --data '{"type":"CNAME","name":"yourdomain.com","content":"cname.cloudflare.com","ttl":300}'
```

**Debugging:**
```bash
dig +trace yourdomain.com  # Check propagation path
whois yourdomain.com      # Verify DNS owner
```

---

## **4. Debugging Tools & Techniques**

| **Tool**               | **Use Case**                          | **Example Command**                          |
|------------------------|---------------------------------------|---------------------------------------------|
| **Cloudflare Debugger** | Inspect edge responses                | `curl -v https://yourdomain.com`           |
| **AWS CloudWatch**      | LB metrics (4xx/5xx errors)           | `aws logs get-log-events --log-group-name /aws/lambda` |
| **Nginx `stub_status`** | Real-time cache hit/miss stats       | `nginx -s reload && curl http://localhost/stub_status` |
| **dig/dnsdumpster**     | DNS propagation checks               | `dig @8.8.8.8 yourdomain.com`              |
| **Wireshark**           | Low-level TCP/UDP issues              | `tshark -i eth0 -f "host yourdomain.com"`    |
| **Cloudflare API**      | Check edge cache status               | `curl "https://api.cloudflare.com/client/v4/zones/<ID>/cache_purges"` |

**Advanced Debugging:**
- **Edge Function Logging:**
  ```javascript
  addEventListener('fetch', event => {
    event.respondWith(handleRequest(event.request));
  });

  async function handleRequest(request) {
    const now = new Date();
    console.log(`[${now.toISOString()}] Request: ${request.url}`);
    return fetch(request);
  }
  ```
- **Backend Correlation IDs:**
  ```python
  # Flask Example
  import uuid
  def generate_correlation_id():
      return str(uuid.uuid4())

  @app.before_request
  def add_correlation_id():
      request.headers['X-Correlation-ID'] = generate_correlation_id()
  ```

---

## **5. Prevention Strategies**

### **A. Configuration Best Practices**
1. **CDN Cache Rules:**
   - Use **path-based** caching (e.g., `/static/` vs `/api/`).
   - Set **realistic TTLs** (e.g., `3600` for static assets, `10` for dynamic).
   - Exclude sensitive endpoints (`/admin`, `/payments`) from caching.

2. **Load Balancer Health Checks:**
   - **Ping endpoints periodically** (e.g., `/health`).
   - **Failover to backup regions** if primary degrades.

3. **DNS & Routing:**
   - **Disable DNS-only mode** in Cloudflare (use "Proxo" for full edge control).
   - **Monitor DNS propagation** with `dig +trace`.

### **B. Monitoring & Alerts**
- **Cloudflare:**
  - Enable **Edge Worker Logging** (`curl` logs to S3).
  - Alert on **cache hit ratios** < 80%.
- **AWS:**
  - Set **CloudWatch Alarms** for `HTTPCode_Target_5XX_Error`.
  - Use **Global Accelerator Latency Metrics**.

### **C. Automated Fixes**
- **Cache Purge on Deploy:**
  ```bash
  # Cloudflare Purge Cache via API
  curl -X POST "https://api.cloudflare.com/client/v4/zones/<ZONE_ID>/purge_cache" \
    -H "Authorization: Bearer <API_KEY>" \
    --data '{"files": ["/static/**"]}'
  ```
- **Auto-Retry Failed Calls (Edge Functions):**
  ```javascript
  async function fetchWithRetry(url, retries = 3) {
    try {
      return await fetch(url);
    } catch (e) {
      if (retries > 0) {
        await new Promise(resolve => setTimeout(resolve, 1000));
        return fetchWithRetry(url, retries - 1);
      }
      throw e;
    }
  }
  ```

### **D. Disaster Recovery Plan**
| **Scenario**               | **Action**                                  |
|----------------------------|--------------------------------------------|
| **CDN Region Down**        | Failover to backup edge nodes.             |
| **DNS Propagation Fail**   | Lower TTL temporarily.                     |
| **Edge Function Crash**    | Roll back to last stable version.          |
| **Load Balancer Overload** | Scale backend instances (auto-scaling).    |

---

## **6. Quick Resolution Checklist**
1. **Confirm Edge vs. Backend Issue** (Check `curl -v` responses).
2. **Check Cache Headers** (`Cache-Control: public/max-age=...`).
3. **Verify Routing Rules** (DNS, LB policies).
4. **Inspect Edge Logs** (Cloudflare Workers, AWS CloudWatch).
5. **Test with `dig`/`nslookup`** (DNS propagation).
6. **Apply Fixes** (Cache headers, LB rules, DNS TTL).
7. **Monitor & Alert** (Set up CloudWatch/Cloudflare alerts).

---
**Final Note:**
Edge issues are **distributed by nature**. Always:
✅ **Isolate the region** (is it global or regional?).
✅ **Check CDN/edge logs first** (not just backend).
✅ **Automate cache invalidations** on deployments.

For **critical outages**, prioritize:
1. **Restore DNS routing**.
2. **Fix cache/bypass CDN temporarily**.
3. **Scale backend if LB is overwhelmed**.