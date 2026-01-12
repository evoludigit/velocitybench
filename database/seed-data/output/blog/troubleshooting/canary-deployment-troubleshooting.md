# **Debugging Canary Deployments: A Troubleshooting Guide**

Canary deployments are a critical pattern for reducing risk when rolling out changes to production. However, misconfiguration, traffic misrouting, or hidden dependencies can cause issues that degrade performance, introduce failures, or make debugging difficult.

This guide provides a structured approach to identifying and resolving common problems in canary deployments.

---

## **1. Symptom Checklist**
Before diving into debugging, verify if the issue aligns with canary deployment problems. Check for:

✅ **Unexpected traffic shifts** – Are traffic percentages correct? Are canary users being served as intended?
✅ **Performance degradation** – Is the canary version slower than the stable version?
✅ **Failed requests** – Are errors spiking in the canary environment?
✅ **Inconsistent behavior** – Some users report issues while others don’t?
✅ **Resource exhaustion** – Are canary instances under heavy load while stable ones are idle?
✅ **Cascading failures** – Does failure in the canary version impact downstream services?

If multiple symptoms appear, prioritize them based on impact (e.g., failures > performance degradation).

---

## **2. Common Issues and Fixes**

### **Issue 1: Incorrect Traffic Routing**
**Symptoms:**
- Not all users are receiving the canary version.
- Traffic percentages don’t match expectations (e.g., 5% canary but traffic shows 20%).
- Stability version users experience canary-like behavior.

**Root Causes:**
- Misconfigured load balancer or service mesh rules.
- Improper canary header/cookie-based routing.
- Weighted traffic split not enforced.

**Debugging Steps:**
1. **Verify routing rules** (e.g., Istio, Nginx, ALB, Traefik).
   ```sh
   # Check Istio VirtualService weights
   kubectl get virtualservice -n <namespace>
   ```
   ```yaml
   # Should look like:
   trafficPolicy:
     loadBalancer:
       simple: 95  # 95% stable
       canary:
         destinations:
         - subset: v1
           weight: 5  # 5% canary
   ```
2. **Inspect logs for misrouted requests.**
   ```sh
   # Check Nginx load balancer logs
   journalctl -u nginx -f
   ```
3. **Use tracing tools** (e.g., OpenTelemetry, Jaeger) to track request flows.
   ```sh
   kubectl logs -l app=my-service --tail=50
   ```

**Fixes:**
- Correct service mesh or LB rules.
- Ensure **sticky sessions** are disabled if not needed.
- Use **A/B testing tools** (e.g., LaunchDarkly, Feature Flags) for explicit routing.

---

### **Issue 2: Performance Degradation in Canary**
**Symptoms:**
- Canary requests are slower than stable ones.
- Latency spikes during canary rollout.
- Database queries or external API calls are inefficient.

**Root Causes:**
- New code has hidden bottlenecks (e.g., inefficient DB queries).
- Canary traffic overloads a shared resource (e.g., cache, API rate limits).
- Unoptimized microservices in the canary.

**Debugging Steps:**
1. **Compare stable vs. canary performance** using APM tools (e.g., New Relic, Datadog).
   ```sh
   # Check Prometheus metrics for latency
   curl http://prometheus-server:9090/graph?g0.expr=histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))
   ```
2. **Profile slow requests** with pprof or OpenTelemetry.
   ```sh
   # Run Go profiling
   go tool pprof http.postprofile
   ```
3. **Check database load** (e.g., slow queries, locks).
   ```sh
   # Check PostgreSQL slow queries
   psql -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
   ```

**Fixes:**
- Optimize slow queries or caching logic.
- Adjust **request limits** (e.g., increase DB connection pool).
- Gradually increase canary traffic if instability is suspected.

---

### **Issue 3: Cascading Failures from Canary**
**Symptoms:**
- Failures in canary versions cause downstream service outages.
- External APIs or databases are overwhelmed by canary traffic.

**Root Causes:**
- Canary version has **breaking API changes**.
- Shared dependencies (e.g., Redis, Kafka) are overloaded.
- Circuit breakers are misconfigured.

**Debugging Steps:**
1. **Check service dependencies** (e.g., Redis, databases).
   ```sh
   # Check Redis memory usage
   redis-cli INFO memory
   ```
2. **Review circuit breaker logs** (e.g., Hystrix, Resilience4j).
   ```sh
   # Check Hystrix metrics
   curl http://monitoring-service/hystrix.stream
   ```
3. **Compare stable vs. canary logs** for failed calls.
   ```sh
   # Filter logs for canary pods
   kubectl logs -l app=my-service,version=canary --since=5m
   ```

**Fixes:**
- **Implement circuit breakers** (e.g., Retry + Fallback).
  ```java
  // Spring resilience4j example
  @Retry(name = "apiRetry")
  @CircuitBreaker(name = "apiCircuitBreaker")
  public String callExternalApi() {
      // ...
  }
  ```
- **Rate-limit canary traffic** to avoid cascading failures.
- **Roll back immediately** if failures affect stability.

---

### **Issue 4: Visibility Gaps**
**Symptoms:**
- No observability into canary traffic.
- Difficult to correlate canary-specific errors.

**Root Causes:**
- Logs are not partitioned by version.
- Metrics do not distinguish stable vs. canary.
- Distributed tracing is missing.

**Debugging Steps:**
1. **Ensure structured logging** with version tags.
   ```log
   {"timestamp": "2024-01-20T12:00:00", "version": "canary", "level": "ERROR", "message": "DB timeout"}
   ```
2. **Check distributed tracing** (e.g., Jaeger, Zipkin).
   ```sh
   kubectl port-forward svc/jaeger-query 16686:16686
   ```
3. **Use canary-specific dashboards** (e.g., Grafana).

**Fixes:**
- **Tag metrics by version** (e.g., `version: stable`, `version: canary`).
- **Implement feature flags** (e.g., LaunchDarkly) for precise control.
  ```sh
  # Check LaunchDarkly canary flag status
  curl https://client-sdk-ingest.launchdarkly.com/api/v1/client-sdk/flags?clientKey=YOUR_KEY
  ```

---

## **3. Debugging Tools & Techniques**

| **Tool**               | **Purpose**                          | **Example Command/Configuration** |
|------------------------|--------------------------------------|-----------------------------------|
| **Prometheus + Grafana** | Metrics for latency, errors, traffic | `histogram_quantile(0.95, http_request_duration_seconds)` |
| **OpenTelemetry**      | Distributed tracing                 | `otel-collector-config.yaml`       |
| **Istio/Linkerd**      | Service mesh observability           | `kubectl get svc -n istio-system`  |
| **Jaeger/Zipkin**      | Request flow analysis                | `kubectl port-forward jaeger-query 16686` |
| **LaunchDarkly**       | Feature flag management              | `curl LD_API_KEY@client-sdk-ingest.launchdarkly.com` |
| **k6/Locust**          | Load testing for canary validation   | `k6 run canary_test.js`            |

**Debugging Workflow:**
1. **Isolate the issue** (stable vs. canary).
2. **Check logs/metrics** for differences.
3. **Reproduce locally** (e.g., Docker + test data).
4. **Apply fixes incrementally** (start with rollback, then optimize).

---

## **4. Prevention Strategies**

### **Pre-Rollout Checks**
✔ **Load test the canary** (e.g., k6, Locust).
✔ **Monitor key metrics** (latency, error rate, throughput).
✔ **Use feature flags** for gradual rollout.
✔ **Define rollback criteria** (e.g., error rate > 1%).

### **Post-Rollout Best Practices**
🔹 **Gradually increase traffic** (e.g., 1% → 5% → 10% → 100%).
🔹 **Automate rollbacks** (e.g., Prometheus + Alertmanager).
🔹 **Maintain canary versions** for a while post-success.
🔹 **Document canary environments** (e.g., DNS, LB rules).

### **Example Canary Rollout Script (Terraform + Istio)**
```hcl
resource "kubernetes_horizontal_pod_autoscaler" "canary" {
  metadata {
    name = "canary-hpa"
  }
  spec {
    scale_target_ref {
      api_version = "apps/v1"
      kind        = "Deployment"
      name        = "my-app-canary"
    }
    min_replicas = 1
    max_replicas = 10
    metrics {
      resource {
        name = "cpu"
        target {
          type = "Utilization"
          average_utilization = 70
        }
      }
    }
  }
}
```

---

## **5. Final Checklist for Canary Debugging**
| **Step**               | **Action**                                  |
|------------------------|--------------------------------------------|
| **Verify traffic split** | Check Istio/Nginx rules.                   |
| **Compare logs**        | Filter by `version: canary`.               |
| **Inspect metrics**     | Look for latency/error spikes.             |
| **Reproduce locally**   | Test in staging with same config.         |
| **Apply fixes**         | Optimize, retry, or roll back.             |
| **Monitor post-fix**    | Ensure stable + canary behave similarly.   |

---

### **Conclusion**
Canary deployments reduce risk, but misconfigurations can lead to outages. By following this structured approach—**check routing, compare performance, trace requests, and monitor metrics**—you can quickly diagnose and resolve issues.

**Key Takeaway:**
*"Test aggressively in staging, roll gradually, and automate rollbacks."*

Would you like a deeper dive into any specific section (e.g., Istio canary setup)?