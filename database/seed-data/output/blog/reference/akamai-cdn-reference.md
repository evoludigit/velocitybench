# **[Pattern] Akamai CDN Integration Patterns Reference Guide**

---
## **Overview**
This guide provides implementation details, best practices, and troubleshooting insights for integrating **Akamai’s Content Delivery Network (CDN)** with your infrastructure. Akamai CDN delivers scalable, low-latency content via a global edge network, but successful integration requires careful configuration of caching policies, DNS redirection, and edge logic. This reference covers:
- **Core integration patterns** (edge-side includes, dynamic content routing, and cache optimization).
- **Technical requirements** (APIs, SDKs, and Akamai’s edge configuration language).
- **Common pitfalls** (TTL misconfigurations, origin failures, or unsupported content types).
- **Query and troubleshooting** techniques via Akamai’s Control Center and API tools.

For developers and operations teams, this guide ensures consistent performance, cost efficiency, and reliability in Akamai deployments.

---

## **Schema Reference**

### **Core Integration Components**
| **Component**               | **Description**                                                                                                                                                                                                 | **Key Properties**                                                                                     | **Supported Configurations**                                                                 |
|------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Akamai EdgeConfig**        | JavaScript-based logic executed at Akamai’s edge servers for dynamic routing, authentication, and response transformations.                                                                               | - `handlerName` <br> - `publicKey` <br> - `scriptVersion` <br> - `coverage`                          | Pre-warm scripts, conditional caching, client IP validation                                         |
| **Origin Servers**           | Backend servers providing content to Akamai’s CDN (e.g., S3, custom apps).                                                                                                                                         | - `originHost` <br> - `protocol` (HTTP/HTTPS) <br> - `port` <br> - `failoverOrigin`                  | Multi-origin failover, health checks, caching headers                                                 |
| **Cache Policies**           | Rules governing how content is stored, expired, and served from Akamai’s edge nodes.                                                                                                                        | - `cacheKey` (algorithm) <br> - `TTL` (default/max) <br> - `cacheOn`/`cacheOff` conditions       | Query-string caching, cookie-based exclusion, purge lists                                            |
| **DNS Configuration**        | Akamai’s authoritative DNS records (CNAMEs, A records) pointing to edge nodes.                                                                                                                             | - `host` <br> - `recordType` (CNAME/A) <br> - `TTL` (default/edge)                                      | Multi-value CNAMEs, IP geographic routing (GeoDNS)                                                  |
| **APIs & SDKs**              | REST/Webhook APIs for dynamic configuration, including `Property API`, `EdgeConfig API`, and `Properties API`.                                                                                                 | - `endpoint` <br> - `authMethod` (API key/Bearer token) <br> - `rateLimit`                           | Real-time edge config updates, cache invalidation, analytics                                         |
| **Security Rules**           | Edge-side filters for rate limiting, bot mitigation, and access control.                                                                                                                                        | - `ruleName` <br> - `action` (allow/deny) <br> - `IP/Geo/HTTP headers` conditions           | WAF integration, request throttling, MFA enforcement                                                  |
| **Monitoring Tools**         | Usage metrics via Akamai’s Control Center, dashboards, or third-party integrations (e.g., Datadog, Splunk).                                                                                               | - `metrics` (hits, misses, latency) <br> - `alerts` (SNS, email) <br> - `samplingRate`               | Real-time monitoring, custom dashboards, automated scaling                                              |

---
## **Query Examples**

### **1. Updating a Cache Policy via API**
Use Akamai’s **Properties API** to modify cache settings dynamically:
```bash
curl -X PUT \
  "https://api.akamaiapis.com/v1/property/{propertyId}/cache" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "cacheKey": {
      "algorithm": "SHA_384",
      "parameters": ["query", "cookie"]
    },
    "ttl": {
      "default": 3600,
      "max": 86400
    }
  }'
```
**Response:**
```json
{
  "status": "success",
  "policyId": "1234567890"
}
```

### **2. Applying an EdgeConfig Script**
Deploy a custom script to Akamai’s edge:
```bash
curl -X POST \
  "https://api.akamaiapis.com/v1/edgeconfig/{propertyId}/scripts/{scriptId}/deploy" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "version": "1.0",
    "coverage": "US,EU",
    "deploy": true
  }'
```

### **3. Checking Cache Hits/Misses**
Query Akamai’s **Usage API** for performance metrics:
```bash
curl -X GET \
  "https://api.akamaiapis.com/v1/metrics/property/{propertyId}/cache/stats" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Accept: application/json" \
  -G \
  --data-urlencode "dimensions=date,tier" \
  --data-urlencode "startTime=2023-01-01T00:00:00Z" \
  --data-urlencode "endTime=2023-01-02T00:00:00Z"
```

---
## **Implementation Details**

### **Key Patterns**
1. **Edge-Side Includes (ESI)**
   - **Use Case:** Dynamically insert content (e.g., ads, user-specific blocks) into cached responses.
   - **Implementation:**
     - Configure an `ESI` cache policy in Akamai’s Control Center.
     - Mark fragments with `<esi:include>` tags.
     - Example:
       ```html
       <esi:include src="//cdn.example.com/user-meta?user=123" />
       ```
   - **Best Practice:** Set strict TTL for non-cacheable fragments.

2. **Dynamic Content Routing**
   - **Use Case:** Route requests to different origins based on geolocation or content type.
   - **Implementation:**
     - Use **EdgeConfig** to check headers/cookies:
       ```javascript
       function handler(transaction) {
         if (transaction.client.ip.country === "US") {
           transaction.uri = "/origin-us/" + transaction.uri;
         }
       }
       ```
     - Configure **multi-origin failover** in Akamai’s **Origin Servers** tab.

3. **Cache Optimization**
   - **Use Case:** Reduce origin load and improve latency.
   - **Implementation:**
     - **Query-String Caching:** Include query strings in `cacheKey` (e.g., `?id=123`).
     - **Cookie Exclusion:** Exclude sensitive cookies from caching:
       ```json
       {
         "cacheKey": {
           "excludeCookies": ["user_session"]
         }
       }
       ```
     - **Purge Lists:** Automatically invalidate stale content via API:
       ```bash
       curl -X POST \
         "https://api.akamaiapis.com/v1/property/{propertyId}/purge" \
         -H "Authorization: Bearer YOUR_API_KEY" \
         -d '["/static/images/logo.png"]'
       ```

### **Common Pitfalls & Fixes**
| **Pitfall**                          | **Root Cause**                          | **Solution**                                                                                     |
|---------------------------------------|-----------------------------------------|-------------------------------------------------------------------------------------------------|
| High origin load                     | Poor TTL settings                       | Increase `default TTL`; use shorter TTLs for dynamic content.                                   |
| Broken responses                      | Cache invalidation lag                  | Enable **pre-warm** for critical assets; use `purge` API for urgent updates.                   |
| Security vulnerabilities              | Weak EdgeConfig rules                   | Restrict `coverage` by region; validate client IPs with `transaction.client.ip`.                |
| GeoDNS misrouting                     | Incorrect `GeoDNS` configuration       | Verify `recordType` (CNAME/A) and `TTL` in DNS settings.                                        |
| API rate limits                      | High-frequency updates                  | Implement exponential backoff; use **async batch updates** via Akamai’s API.                    |

---
## **Related Patterns**
| **Pattern**                          | **Description**                                                                                     | **Reference**                                                                                     |
|---------------------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| **[Origin Shield]**                   | Offloads origin traffic to Akamai’s Anycast network, reducing latency and server load.             | [Akamai Origin Shield Docs](https://docs.akamai.com/)                                            |
| **[Akamai Bot Control]**              | Mitigates bot traffic using edge-side rules and WAF integration.                                     | [Bot Control Patterns](https://developer.akamai.com/)                                            |
| **[Edge-Side Includes (ESI) Deep Dive]** | Advanced ESI techniques for modular content delivery.                                               | [ESI Best Practices](https://docs.akamai.com/cdn-development/edge-software-development/esi)      |
| **[Multi-Origin Failover]**            | Configures backup origins to handle primary server failures.                                        | [Failover Configuration](https://developer.akamai.com/property-configuration/failover)           |
| **[Akamai Security Rules]**            | Custom rules for DDoS protection, authentication, and data validation.                               | [Security Rules Docs](https://docs.akamai.com/cdn-development/security)                          |

---
## **Key Takeaways**
- **Start small:** Test with a single cache policy or EdgeConfig script before scaling.
- **Monitor relentlessly:** Use Akamai’s **Usage API** to track hits/misses and latency.
- **Automate invalidations:** Schedule purges for dynamic content (e.g., via cron jobs).
- **Optimize TTLs:** Balance freshness (low TTL) and performance (high TTL) per content type.
- **Leverage SDKs:** Use Akamai’s Python/Node.js SDKs for programmatic config management.