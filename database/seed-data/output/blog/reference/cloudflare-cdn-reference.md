# **[Cloudflare CDN Integration Patterns] Reference Guide**

---

## **Overview**
This reference guide details **Cloudflare CDN integration patterns**, covering common architectures, implementation strategies, and optimization techniques for leveraging Cloudflare’s global edge network. Whether deploying a static website, optimizing dynamic content, or securing APIs, Cloudflare CDN integrates seamlessly with your infrastructure. This guide helps you select the right pattern—such as **Cache-First, Cache-While-Validate, or All-Or-Nothing**—and configures it efficiently. Learn about **TTL strategies, edge caching rules, and failover mechanisms** while avoiding common pitfalls like stale content or excessive backend load.

---

## **Key Concepts & Schema Reference**

### **Core CDN Integration Patterns**
Cloudflare supports three primary caching patterns for content delivery:

| **Pattern Name**       | **Use Case**                          | **Cache Behavior**                                                                 | **Backend Interaction**                          | **Key Configuration**                          |
|------------------------|---------------------------------------|-----------------------------------------------------------------------------------|---------------------------------------------------|-----------------------------------------------|
| **Cache-First**        | Low-latency static assets (CSS, JS)   | Return cached content if available; fetch from origin only on miss.               | Minimal backend calls.                           | `Cache-Level: Edge`                           |
| **Cache-While-Validate** | Balanced performance & freshness (APIs, dynamic pages) | Cache content while verifying with origin on cache expiry. | Periodic validation requests.                    | `Cache-Level: Intermediate`, `Cache-Control: s-maxage` |
| **All-Or-Nothing**     | Critical content (e.g., login pages) | Bypass cache; fetch fresh content from origin.                                  | Full backend dependency.                         | `Cache-Level: ByPass`, `Cache-Control: no-store` |

---

### **Schema: Cloudflare CDN Configuration Parameters**
| **Parameter**               | **Type**       | **Description**                                                                                     | **Default Value**               | **Example Values**                     |
|-----------------------------|----------------|-----------------------------------------------------------------------------------------------------|---------------------------------|---------------------------------------|
| `Cache-Level`               | Enum           | Specifies cache scope: Edge, Intermediate, or Bypass.                                              | `Edge`                           | `Intermediate`, `Bypass`              |
| `Cache-Control`             | String         | Defines HTTP caching directives (e.g., `s-maxage`, `public`).                                       | `public, max-age=1d`            | `s-maxage=3600`, `no-cache`           |
| `Cache-Purge`               | Boolean        | Enables manual cache purging via API/URL.                                                          | `false`                          | `true`                                  |
| `Edge-Caching`              | Boolean        | Activates Cloudflare’s edge cache (reduces origin load).                                           | `true`                           | `false`                                 |
| `TTL (Time-to-Live)**      | Integer (sec)  | Sets how long content stays cached.                                                               | `1d` (1 day)                     | `3600` (1 hour)                        |
| `Cache-Status-Code`        | Integer        | Determines which HTTP status codes trigger caching.                                               | `200`                            | `200, 206, 301`                        |
| `Cache-Method`              | Enum           | Specifies HTTP methods eligible for caching (e.g., `GET`, `HEAD`).                               | `GET, HEAD`                      | `GET, OPTIONS`                         |
| `Cache-Key`                 | String         | Custom key for cache differentiation (e.g., query strings, headers).                              | `URL`                            | `URL, Cookie(user_id)`                 |
| `Origin-Server-Timeouts`   | Integer (ms)   | Timeout for backend requests to avoid stalled requests.                                            | `30000` (30s)                    | `5000` (5s)                             |
| `Rate-Limiting`            | Boolean        | Enables DDoS protection and rate limiting at the edge.                                             | `false`                          | `true` (with thresholds)               |
| `Brokered-Pull**            | Boolean        | Uses Cloudflare’s origin proxy to fetch content (reduces origin IP exposure).                     | `false`                          | `true`                                  |

**\*Advanced settings; typically used with custom origins or security-sensitive apps.**

---

## **Implementation Details**

### **1. Setting Up Cloudflare CDN Integration**
#### **Prerequisites**
- Cloudflare-registered domain with a **pro, business, or enterprise plan**.
- Origin server accessible via **IP or hostname** (A/AAAA record).
- **SSL/TLS** configured for HTTPS (recommended for security).

#### **Steps**
1. **Add Origin Server**
   - Navigate to **Origin Server** in Cloudflare Dashboard.
   - Enter your origin IP/hostname.
   - Set **Origin Shield** (if using Cloudflare’s network to mask your IP).

2. **Configure Cache Rules**
   - Go to **Caching & Optimization** > **Configuration**.
   - Select **Cache Level** (Edge/Intermediate/Bypass) per path (e.g., `/static/*` for Cache-First).
   - Set **Cache-Control** headers (e.g., `s-maxage=86400` for 24-hour caching).

3. **Enable Edge Caching**
   - In **Caching & Optimization**, toggle **Edge Caches** to `On`.
   - Adjust **TTL** (default: 1 day) or set **Cache Method** restrictions.

4. **Test & Validate**
   - Use **Page Rule Testing** in the dashboard to simulate requests.
   - Verify cache hits/misses via **Analytics** > **Performance**.

---

### **2. Optimizing Cache Performance**
#### **TTL Strategies**
| **Scenario**               | **TTL Recommendation**       | **Notes**                                      |
|----------------------------|-----------------------------|------------------------------------------------|
| Static assets (HTML/CSS/JS)| `1 week` to `1 month`       | Long TTL reduces backend load.                 |
| Dynamic content (APIs)     | `5–30 minutes`              | Balance freshness vs. performance.             |
| User-specific content      | `1–5 minutes`               | Use `Cache-Key` with `Cookie` or `QueryString`. |
| High-frequency updates     | `1–5 seconds`               | Short TTL with `Cache-While-Validate`.         |

#### **Edge Functions for Dynamic Caching**
- Use **Worker Scripts** to generate dynamic cache keys or transform responses.
- Example: Cache user-specific content based on `X-User-ID` header:
  ```javascript
  // Cloudflare Worker
  addEventListener('fetch', (event) => {
    event.respondWith(handleRequest(event.request));
  });

  async function handleRequest(request) {
    const url = new URL(request.url);
    const userId = request.headers.get('X-User-ID');
    const cacheKey = `${url.pathname}?user=${userId}`;
    // Logic to fetch or cache based on cacheKey
  }
  ```

---

### **3. Handling Failures & Fallbacks**
| **Issue**                  | **Mitigation Strategy**                                                                 |
|----------------------------|----------------------------------------------------------------------------------------|
| **Origin Downtime**        | Enable **Origin Failover** to a secondary endpoint.                                     |
| **Stale Content**          | Use `Cache-While-Validate` with short TTLs or purge cache via API (`/cache_purge`).     |
| **Cache Bloat**            | Implement **Cache-Purge** rules (e.g., purge `/api/*` after updates).                  |
| **DDoS Attacks**           | Activate **Rate Limiting** or **WAF Rules** in Cloudflare.                             |
| **Slow Origin Response**   | Increase `Origin-Server-Timeouts` (max 60s) or use **Brokered Pull**.                 |

**Example Purge API Call:**
```bash
curl -X POST "https://api.cloudflare.com/client/v4/zones/<ZONE_ID>/purge_cache" \
  -H "Authorization: Bearer <API_KEY>" \
  -H "Content-Type: application/json" \
  --data '{"purge_everything":true}'
```

---

## **Query Examples**
### **1. Cache-First for Static Content**
**Request:**
`GET /styles/main.css`

**Response Headers (Cached):**
```
Cache-Control: public, s-maxage=2592000, stale-while-revalidate=86400
X-Cache: HIT from cloudflare
```

### **2. Cache-While-Validate for API**
**Request:**
`GET /api/user?user_id=123`

**Response Headers (First Request):**
```
Cache-Control: public, s-maxage=300, stale-while-revalidate=60
Age: 0
X-Cache: MISS
```

**Subsequent Request (Validated):**
```
Cache-Control: public, s-maxage=300, stale-while-revalidate=60
Age: 120
X-Cache: HIT from cloudflare
```

### **3. All-Or-Nothing for Login Page**
**Request:**
`GET /login`

**Response Headers (Bypass Cache):**
```
Cache-Control: no-store
X-Cache: BYPASS
```

---

## **Best Practices**
1. **Leverage Page Rules**
   - Apply granular caching rules (e.g., `Cache-Level: Edge` for `/static/*`, `Bypass` for `/api/*`).

2. **Monitor Cache Efficiency**
   - Use **Analytics** > **Performance** to track:
     - Cache Hit Ratio
     - Origin Requests
     - Latency Percentiles

3. **Secure Your Cache**
   - Restrict cache keys with secrets (e.g., `Cache-Key: "URL+<API_KEY>"`).
   - Use **Cloudflare Access** for authenticated endpoints.

4. **Avoid Cache Stampedes**
   - Implement **lazy loading** or **probabilistic early expiration** for popular content.

5. **Test Incrementally**
   - Start with low-TTL values, then increase based on traffic patterns.

---

## **Common Pitfalls & Fixes**
| **Pitfall**                          | **Cause**                                      | **Solution**                                  |
|---------------------------------------|------------------------------------------------|---------------------------------------------|
| **Stale Content**                     | Long TTL or missed purges.                     | Reduce TTL or use `Cache-While-Validate`.   |
| **High Origin Load**                  | Over-caching or inefficient TTL.              | Optimize TTL; use `s-maxage` judiciously.   |
| **Cache Misses on Dynamic Content**   | Cache keys not accounting for auth/query vars. | Include `Cookie` or `QueryString` in `Cache-Key`. |
| **API Errors in Cached Responses**    | Cache serving stale invalid responses.         | Enable `stale-while-revalidate`.            |
| **Slow Edge Response Times**          | Underpowered origin or slow CDN regions.       | Use **Brokered Pull** or **Origin Shield**. |

---

## **Related Patterns**
1. **[Cloudflare Workers for Edge Computing]**
   - Extend CDN with runtime logic (e.g., A/B testing, auth).
   - *Reference*: [Cloudflare Workers Docs](https://developers.cloudflare.com/workers/)

2. **[Load Balancing with Cloudflare Arbital]**
   - Distribute traffic across multiple origins (e.g., failover, A/B testing).
   - *Reference*: [Arbital Pattern Guide](https://developers.cloudflare.com/load-balancer/)

3. **[Secure CDN with WAF & Bot Mitigation]**
   - Protect CDN from attacks while maintaining performance.
   - *Reference*: [Cloudflare WAF Docs](https://developers.cloudflare.com/waf/)

4. **[Multi-CDN Strategy]**
   - Combine Cloudflare with other providers (e.g., Fastly) for redundancy.
   - *Reference*: [Multi-CDN Best Practices](https://www.cloudflare.com/learning/cdn/what-is-a-cdn/)

5. **[Serverless Functions for Dynamic Content]**
   - Generate content at the edge (e.g., personalization, ads).
   - *Reference*: [Durable Objects](https://developers.cloudflare.com/durable-objects/)

---
**Last Updated:** [Insert Date]
**For support:** [Cloudflare Community](https://community.cloudflare.com/) | [API Status](https://www.cloudflare.com/status)