---
# **[Pattern] Fastly CDN Integration Reference Guide**

---

## **Overview**
This reference guide provides detailed implementation instructions for integrating **Fastly’s Content Delivery Network (CDN)** with applications, APIs, or infrastructure. The guide covers **key pattern schema, query examples, best practices, and common pitfalls** to optimize performance, reduce latency, and minimize costs.

Fastly CDN accelerates the delivery of static and dynamic content by caching responses across a global edge network. This guide assumes prior knowledge of:
- Basic HTTP/HTTPS operations
- CDN terminology (e.g., edge servers, cache rules, VCL)
- Familiarity with backend architectures (origin servers, APIs)

---

## **Schema Reference**

| **Component**               | **Description**                                                                                                                                                                                                 | **Example Values**                                                                 |
|-----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Delivery Method**         | How content is fetched from Fastly.                                                                                                                                                                          | Static File, Dynamic API, Stream-Innovation, Cache Key Customization              |
| **Cache Behavior**          | Rules defining how Fastly caches responses.                                                                                                                                                              | `stale_if_error`, `stale_while_revalidate`, `purge_on`                            |
| **Cache Key Customization** | Custom headers/methods used to generate unique cache keys.                                                                                                                                                   | `HTTP://example.com/path?custom_id={QueryArg}`                                   |
| **Origin Server**           | The source of uncached content (e.g., origin host, backend API).                                                                                                                                            | `example.com` or `https://api.example.com`                                         |
| **TTL (Time-to-Live)**      | Duration cached content remains valid.                                                                                                                                                                     | `300s` (5 minutes), `1h`, `24h`                                                    |
| **Dynamic Content Rules**   | Logic applied to dynamic content (e.g., API responses).                                                                                                                                                     | `if (req.http.x-api-version == "v2") { cache 0s }`                              |
| **Purging Mechanism**       | Methods to invalidate cache entries.                                                                                                                                                                       | API `/purge`, Direct Cache Purge, Signed Cache Purge URLs                        |
| **Monitoring & Logging**    | Tools to track performance, errors, and cache hits/misses.                                                                                                                                                | Fastly Logs, AWS CloudWatch, GCP Stackdriver                                       |
| **Geographic Optimization** | Rules to serve content based on user location.                                                                                                                                                            | `geo { if (req.http.Country == "US") { set var.region = "us-west-2" } }`        |
| **Rate Limiting**           | Controls traffic to prevent abuse.                                                                                                                                                                         | `rate_limit 1000r/s` (1000 requests per second)                                  |
| **Compression**             | Enables gzipped responses for faster transfers.                                                                                                                                                             | `compress` in VCL (e.g., `if (req.http.accept-encoding ~ gzip) { ... }`)        |
| **Edge Compute**            | Processing logic executed at edge locations (e.g., URL rewrites, auth).                                                                                                                                       | JavaScript via `@edge`, `fetch` operations                                        |

---

## **Query Examples**

### **1. Static Content Optimization**
**Scenario:** Cache HTML/JS/CSS files with a 1-hour TTL.
**Implementation:**
```vcl
sub vcl_recv {
    if (req.url ~ "(.html|.js|.css)$") {
        set req.cache_level = "fast";
        set req.ttl = 3600s;
    }
}
```

### **2. Dynamic API Response Caching**
**Scenario:** Cache API responses for 5 minutes unless invalidated.
**Implementation:**
```vcl
sub vcl_backend_response {
    if (req.url ~ "/api/v1/") {
        set beresp.ttl = 300s;
        set beresp.http.cache-control = "max-age=300";
    }
}
```

### **3. Custom Cache Key for Dynamic Content**
**Scenario:** Cache API responses by user ID (e.g., `/user/123`).
**Implementation:**
```vcl
sub vcl_hash {
    if (req.url ~ "/user/") {
        set req.url = regsub(req.url, "/user/(\d+)", "/user/{QueryArg}");
    }
}
```

### **4. Geographically Targeted Delivery**
**Scenario:** Serve content from a region-specific origin.
**Implementation:**
```vcl
sub vcl_recv {
    if (req.http.accept-encoding ~ "br") {
        geo us {
            set req.backend = "us-origin.example.com";
        }
        default {
            set req.backend = "eu-origin.example.com";
        }
    }
}
```

### **5. Cache Purge via API**
**Scenario:** Invalidate cached content programmatically.
**Endpoint:** `POST /service/<ID>/purge/<URL>`
**Body:**
```json
{
  "uri": "/path/to/content",
  "version": "v1"
}
```

### **6. Real-Time Cache Invalidation**
**Scenario:** Use **Fastly’s Signed Cache Purge** to invalidate dynamically.
**Implementation:**
```bash
curl -X POST \
  "https://api.fastly.com/service/<ID>/purge/<URL>" \
  -H "Fastly-Key: <API_KEY>" \
  -H "Fastly-Signature: <SIGNED_REQUEST>"
```

### **7. Rate Limiting for APIs**
**Scenario:** Limit API calls to 1000 requests/second.
**Implementation:**
```vcl
sub vcl_recv {
    if (req.url ~ "/api/") {
        rate_limit 1000r/s;
    }
}
```

---

## **Best Practices**

1. **Leverage Cache Levels**
   - Use `fast` for static assets, `mid` for semi-dynamic content, `pass` for real-time data.

2. **Optimize TTLs**
   - **Short TTLs (e.g., 1-5 min):** For frequently changing content (e.g., news feeds).
   - **Long TTLs (e.g., 1h-24h):** For static assets (e.g., images, CSS).

3. **Custom Cache Keys for Dynamic Content**
   - Avoid cache collisions by including query parameters or cookies in the key.

4. **Use Edge Compute for Logic**
   - Offload processing (e.g., URL rewrites, A/B testing) to Fastly’s edge.

5. **Monitor Cache Efficiency**
   - Track `Cache-Hit-Ratio` in Fastly dashboards to refine rules.

6. **Leverage Brotli/Gzip Compression**
   - Reduce payload size for faster transfers.

7. **Implement Proper Purge Strategies**
   - Use **signed purges** for security (validate requests via API keys).

8. **Test Edge Cases**
   - Verify behavior under high traffic, DDoS, or backend failures.

---

## **Common Pitfalls & Solutions**

| **Pitfall**                          | **Cause**                                  | **Solution**                                                                 |
|---------------------------------------|--------------------------------------------|------------------------------------------------------------------------------|
| High cache miss ratio                | Static content not marked for caching.     | Explicitly set `cache_level` and `ttl` for all static assets.                |
| Stale data delivery                  | TTL too long for dynamic content.         | Use `stale_if_error` or `stale_while_revalidate` for critical paths.        |
| API cache collision                  | Dynamic cache keys not unique enough.      | Include user-specific or time-based tokens in cache keys.                    |
| Purge failures                       | Invalid purge URLs or API key issues.      | Validate purge endpoints and use signed requests for security.              |
| Slow edge response times             | Overloaded backend during traffic spikes.   | Implement **rate limiting** or **origin shielding** to reduce load.          |
| Compression not enabled              | Missing `compress` directive.             | Add `compress` to VCL for supported content types (e.g., `text/html`, `js`). |
| Ignored headers during forwarding    | Missing `forward` rules in VCL.           | Use `forward` to pass headers like `Authorization` or `X-User-ID`.         |

---

## **Related Patterns**

1. **[Origin Shielding](https://developer.fastly.com/reference/edge-compute/)**
   - Protects backend servers from direct exposure to internet traffic.

2. **[Real-Time Analytics with Edge Compute](https://developer.fastly.com/reference/edge-compute/)**
   - Enables real-time data processing at the edge (e.g., A/B testing, personalization).

3. **[Multi-Region CDN Deployment](https://developer.fastly.com/guides/deploying-a-multiregion-cdn/)**
   - Strategies for deploying globally optimized CDN setups.

4. **[Cache Warmup Techniques](https://developer.fastly.com/community/tutorials/cache-warmup/)**
   - Pre-populates cache before traffic spikes.

5. **[Fastly + Serverless Integration](https://developer.fastly.com/guides/integrating-fastly-with-serverless/)**
   - Combines Fastly with AWS Lambda, Cloudflare Workers, or Vercel Edge Functions.

---

## **Further Reading**
- [Fastly VCL Documentation](https://developer.fastly.com/reference/vcl/)
- [Fastly API Reference](https://developer.fastly.com/api/)
- [Fastly Best Practices](https://developer.fastly.com/resources/best-practices/)

---
**Last Updated:** [Insert Date]
**Feedback:** [Contact Support](https://support.fastly.com)