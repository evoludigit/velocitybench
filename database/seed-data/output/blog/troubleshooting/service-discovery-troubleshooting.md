# **Debugging Service Discovery & Load Balancing: A Troubleshooting Guide**

## **Introduction**
Service Discovery & Load Balancing is a critical pattern in distributed systems, ensuring clients dynamically locate healthy service instances while distributing traffic evenly. When misconfigured or failing, it can lead to **stale connections, uneven workloads, cascading failures, and degraded performance**.

This guide provides a **practical, step-by-step approach** to diagnosing and resolving issues efficiently.

---

---

## **1. Symptom Checklist**
Before diving into fixes, verify which symptoms align with your issue:

| **Symptom**                     | **Question to Ask**                                                                 |
|----------------------------------|-----------------------------------------------------------------------------------|
| Clients connect to crashed instances | Are errors like `Connection Refused` or `Timeout` appearing in logs?             |
| Uneven load distribution        | Do some backend instances have significantly higher CPU/memory usage?               |
| Manual config updates required   | Must ops manually edit configs when services move (e.g., Kubernetes pods restart)? |
| Unhealthy instances in rotation  | API checks (e.g., `/health`) return `500` or `503`, but traffic still routes there? |
| Slow response times              | Are requests stuck in DNS resolution or connection pool exhaustion?               |
| Client timeouts                  | Are clients unable to establish connections within timeout thresholds?            |

**Next Steps:**
- Check **logs** (client, load balancer, service discovery).
- Monitor **metrics** (latency, error rates, active connections).
- Validate **endpoints** with `curl`, `telnet`, or health probes.

---

---

## **2. Common Issues & Fixes**

### **Issue 1: Stale Endpoints (Clients Connect to Dead Instances)**
**Cause:**
- Service discovery cache is too slow to update.
- Clients are not refreshing endpoints.
- DNS TTL is too high (e.g., 300s), causing stale records.

**Debugging Steps:**
1. **Check Discovery Cache:**
   - If using **Consul/etcd/Redis**, verify cache TTL and sync frequency.
   - Example (Consul):
     ```sh
     consul kv get -keys "" | grep -i "service-name"
     ```
   - If stale, reduce TTL or increase sync frequency.

2. **Client-Side Fixes:**
   - **Service Mesh (Istio/Linkerd):** Ensure sidecar proxies are updated.
   - **Direct Clients:** Implement **TTL-based cache invalidation** or **polling with jitter**:
     ```python
     # Python (using requests-cache)
     import requests_cache
     requests_cache.install_cache('service_discovery_cache', expire_after=300)
     ```
   - **Kubernetes:** Use `readinessProbes` and `livenessProbes` to avoid routing to unhealthy pods.

3. **DNS Fixes:**
   - Reduce **DNS TTL** (e.g., to 30s) or use **DNS SRV records** with short TTLs.
   - Example (Cloudflare DNS):
     ```
     service-name._tcp.example.com. IN SRV 10 5 8080 instance1.example.com.
     ```

---

### **Issue 2: Manual Configuration Updates Needed**
**Cause:**
- Static host files or config files are not auto-updated.
- No integration with **Kubernetes Service DNS** or **cloud provider metadata**.

**Debugging Steps:**
1. **Check Current Discovery Mechanism:**
   - **Kubernetes:** Use `kube-dns` or `CoreDNS`—ensures auto-discovery via `svc-name.namespace.svc.cluster.local`.
   - **Cloud (AWS/GCP):** Use **Instance Metadata Service (IMDS)** or **Service Networks**.
   - **Custom Service Mesh:** Verify mesh is updated via **sidecar injection**.

2. **Automate Configuration:**
   - **Kubernetes Example:**
     ```yaml
     # Deploy with auto-discovery
     apiVersion: apps/v1
     kind: Deployment
     metadata:
       name: my-service
     spec:
       template:
         spec:
           serviceAccountName: my-service-account
     ```
   - **AWS (ECS):** Use **Service Discovery** to auto-register tasks.

3. **Fallback: Dynamic Config Loading**
   - If using **config files**, implement a **watchdog** (e.g., Python’s `watchdog`):
     ```python
     from watchdog.observers import Observer
     def on_changed(event):
         reload_configs()  # Trigger reloading
     observer = Observer()
     observer.schedule(on_changed, path='./configs')
     observer.start()
     ```

---

### **Issue 3: Uneven Load Distribution**
**Cause:**
- **Load balancer misconfiguration** (e.g., round-robin without health checks).
- **Session affinity** (sticky sessions) causing backends to overload.
- **Backend performance differences** (some instances slower than others).

**Debugging Steps:**
1. **Check Load Balancer Health**
   - **NGINX Example:**
     ```nginx
     upstream backend {
         zone backend 64k;
         server instance1:8080 max_fails=3 fail_timeout=30s;
         server instance2:8080 max_fails=3 fail_timeout=30s;
     }
     ```
   - **AWS ALB:** Verify **health check paths** and **success thresholds**.

2. **Disable Stickiness (If Unnecessary)**
   - AWS ALB:
     ```sh
     aws elbv2 update-load-balancer-attributes --load-balancer-arn alb-id \
         --attributes Key=routing.http.sticky_session.enabled,Value=false
     ```
   - **NGINX:** Remove `proxy_set_header X-Forwarded-For;` if not needed.

3. **Use Weighted Round-Robin**
   - **NGINX:**
     ```nginx
     upstream backend {
         server instance1:8080 weight=3;
         server instance2:8080 weight=1;
     }
     ```
   - **Kubernetes Service:** Use `service.spec.loadBalancerIP` (if needed) but prefer **pod-based scaling**.

4. **Monitor Backend Performance**
   - Check **latency metrics** (e.g., Prometheus `http_request_duration_seconds`).
   - Example (PromQL):
     ```promql
     histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, instance))
     ```

---

### **Issue 4: No Health Awareness (Routing to Unhealthy Instances)**
**Cause:**
- **No health checks** in load balancer.
- **Client-side health checks** are bypassed.
- **Service mesh sidecars** are misconfigured.

**Debugging Steps:**
1. **Verify Load Balancer Health Checks**
   - **NGINX:**
     ```nginx
     upstream backend {
         server instance1:8080 check interval=5s fail_timeout=10s;
     }
     ```
   - **AWS ALB:** Configure `/health` endpoint with **success thresholds (2/5)**.

2. **Check Kubernetes Liveness/Readiness Probes**
   - Example:
     ```yaml
     livenessProbe:
       httpGet:
         path: /health
         port: 8080
       initialDelaySeconds: 5
       periodSeconds: 10
     readinessProbe:
       httpGet:
         path: /ready
         port: 8080
       initialDelaySeconds: 2
     ```

3. **Service Mesh Fixes (Istio/Linkerd)**
   - **Istio:** Ensure `DestinationRule` includes **subset-based traffic control**:
     ```yaml
     trafficPolicy:
       loadBalancer:
         simple: LEAST_CONN
     ```
   - **Linkerd:** Verify `checks` in `checks.yaml`:
     ```yaml
     checks:
       - type: http
         path: /health
         interval: 5s
         timeout: 2s
     ```

4. **Client-Side Health Checks**
   - **Retries with Backoff:**
     ```python
     from tenacity import retry, stop_after_attempt, wait_exponential

     @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
     def call_service():
         response = requests.get("http://service:8080/health")
         response.raise_for_status()
     ```

---

---

## **3. Debugging Tools & Techniques**
| **Tool**               | **Use Case**                                                                 | **Example Command/Config**                          |
|------------------------|----------------------------------------------------------------------------|----------------------------------------------------|
| **`curl` / `telnet`**  | Test connectivity to endpoints.                                             | `curl -v http://instance1:8080/health`            |
| **Prometheus + Grafana** | Monitor latency, error rates, and traffic distribution.                 | `rate(http_requests_total[5m]) by (instance)`    |
| **Kubernetes `kubectl`** | Check pod health, service endpoints, and events.                          | `kubectl describe pod my-pod -n my-namespace`     |
| **NGINX `ngx_http_upstreamCheckModule`** | Validate backend health in real-time.                                     | `check interval=5s fail_timeout=10s`              |
| **Consul/etcd CLI**    | Inspect service registrations and cache.                                   | `consul services`                                 |
| **AWS CloudWatch**     | Track ALB health metrics and 5xx errors.                                   | `/aws/alb/HealthyHostCount`                       |
| **Packet Capture (`tcpdump`)** | Debug connection issues (e.g., TLS handshake fails).                      | `tcpdump -i any port 8080 -w capture.pcap`        |
| **OpenTelemetry + Jaeger** | Trace requests across services to find bottlenecks.                     | `otel-collector-config.yml` + `jaeger-query`     |

**Pro Tip:**
- Use **distributed tracing** (Jaeger, Zipkin) to identify where requests get stuck.
- **Log aggregation** (ELK, Loki) helps correlate client logs with service failures.

---

---

## **4. Prevention Strategies**
| **Strategy**                          | **Implementation**                                                                 |
|----------------------------------------|-----------------------------------------------------------------------------------|
| **Short Cache TTLs**                  | Set `maxAge=30s` in service discovery (e.g., Consul, eureka).                    |
| **Automated Health Checks**           | Enforce `/health` endpoints with **liveness/readiness probes** in Kubernetes.   |
| **Dynamic DNS (SRV Records)**         | Use **Cloudflare DNS** or **AWS Route 53** with short TTLs.                      |
| **Service Mesh Adoption**             | Deploy **Istio/Linkerd** for automatic traffic management and mTLS.              |
| **Kubernetes Services**               | Use `ClusterIP` or `NodePort` for internal communication; avoid `LoadBalancer` unless necessary. |
| **Client-Side Retries**               | Implement **exponential backoff** (e.g., `tenacity` in Python).                  |
| **Weighted Traffic Splitting**        | Gradually roll out updates with ** Istio VirtualServices** or **NGINX annotations**. |
| **Monitoring & Alerts**                | Set up **Prometheus Alerts** for:
  - `rate(http_requests_total{status=~"5.."}[5m]) > 0.1`
  - `kube_pod_container_status_waiting > 0` in Kubernetes. |

**Example Prevention Config (Istio):**
```yaml
# Gradual rollout with 90% to old, 10% to new
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: my-service
spec:
  hosts:
  - my-service.namespace.svc.cluster.local
  http:
  - route:
    - destination:
        host: my-service.namespace.svc.cluster.local
        subset: v1
      weight: 90
    - destination:
        host: my-service.namespace.svc.cluster.local
        subset: v2
      weight: 10
```

---

---

## **5. Quick Resolution Checklist**
| **Step** | **Action**                                                                 |
|----------|---------------------------------------------------------------------------|
| 1        | **Verify logs** (client, load balancer, service discovery).               |
| 2        | **Check metrics** (latency, errors, active connections).                  |
| 3        | **Test endpoints** (`curl`, `telnet`).                                  |
| 4        | **Update cache TTLs** (DNS, service discovery).                          |
| 5        | **Enable health checks** (load balancer, probes).                        |
| 6        | **Disable stickiness** if uneven load is suspected.                       |
| 7        | **Scale backends** if some instances are overwhelmed.                     |
| 8        | **Use tracing** (Jaeger) to find bottlenecks.                             |
| 9        | **Automate config updates** (Kubernetes, IMDS, or dynamic config files).  |
| 10       | **Set up alerts** for future incidents.                                   |

---

## **Final Notes**
- **Start small:** Isolate the issue (client, lb, or backend) before diving deep.
- **Leverage observability:** Without logs/metrics, troubleshooting is guesswork.
- **Automate recovery:** Use **retries, circuit breakers (Hystrix), and graceful degradation**.

By following this guide, you should be able to **diagnose and fix** service discovery and load balancing issues **within hours**, not days. For persistent problems, consider **rewriting health checks** or **migrating to a service mesh** for automated resilience.