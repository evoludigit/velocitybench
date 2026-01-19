# **Debugging Zero-Downtime Deployments: A Troubleshooting Guide**

Zero-downtime deployments (ZDD) ensure services remain available during updates, minimizing user impact. However, misconfigurations, race conditions, or poor rollout strategies can lead to downtime or degraded performance. This guide helps diagnose, resolve, and prevent common issues in ZDD implementations.

---

## **1. Symptom Checklist**
Before diving into fixes, verify if your deployment *actually* has downtime. Check for these signs:

| **Symptom**                          | **Description**                                                                 | **How to Verify**                                                                 |
|--------------------------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **Service Unavailability**           | Requests fail with `5xx` errors or timeouts.                                 | Check logs, metrics (Prometheus/Grafana), and client error rates.                  |
| **Split-Brain Behavior**             | Clients interact with old/new versions simultaneously, causing inconsistencies. | Monitor request IDs and session mismatches across versions.                       |
| **Database Locking**                 | Long-running transactions block rollback or redirection.                     | Review database lock durations (e.g., `SHOW PROCESSLIST` in MySQL).               |
| **Increased Latency**                | Response times spike during traffic shift.                                   | Compare pre- and post-deployment latency (e.g., New Relic, Datadog).              |
| **Traffic Mismatch**                 | Uneven load distribution between old/new instances.                           | Use tools like `kubectl top pods` (K8s) or AWS CloudWatch metrics.                |
| **Health Checks Fail**               | `/health` endpoints return `5xx` despite traffic redirects.                   | Test endpoints manually and check pod liveness probes.                           |
| **Rollback Required**                | Manual intervention needed to revert changes.                                | Check deployment logs for rollback commands (`kubectl rollout undo`, `kubectl set image --record`). |

---

## **2. Common Issues & Fixes**
Below are root causes, diagnostics, and fixes for ZDD failures.

---

### **Issue 1: Traffic Routing Mismatch**
**Symptom**: Users see old/new versions mixed or no traffic redirected.
**Root Cause**: Incorrect DNS, load balancer, or service mesh configuration.

#### **Diagnosis**
1. **Check traffic distribution**:
   ```bash
   # For AWS ALB
   aws elbv2 describe-load-balancer-attributes --load-balancer-arn <ARN>

   # For Istio
   kubectl get svc -n istio-system istio-ingressgateway -o yaml
   ```
   Verify the `service.beta.kubernetes.io/aws-load-balancer-cross-zone-load-balancing-enabled: "true"` or Istio `VirtualService` rules.

2. **Test client-side routing**:
   ```bash
   curl -H "X-Version: v2" http://your-service  # Force v2 if using canary
   ```

#### **Fix**
- **AWS ALB**: Ensure `Target Group` health checks match the new version.
  ```yaml
  # Example ALB ingress controller annotation (K8s)
  annotations:
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/healthcheck-port: traffic-port
  ```
- **Istio**: Correct `VirtualService` weight:
  ```yaml
  http:
    - match:
        - headers:
            version:
              exact: v1
      route:
        - destination:
            host: your-service
            subset: v1
      weight: 90
    - match:
        - headers:
            version:
              exact: v2
      route:
        - destination:
            host: your-service
            subset: v2
      weight: 10
  ```

---

### **Issue 2: Database Schema Migrations Fail**
**Symptom**: App crashes or returns `DatabaseSchemaError` during rollout.
**Root Cause**: Schema changes without proper rollback or backward compatibility.

#### **Diagnosis**
1. **Check migration logs**:
   ```bash
   # PostgreSQL example
   psql -c "SELECT query, state FROM pg_stat_statements ORDER BY query_time DESC;"
   ```
   Look for long-running migrations or deadlocks.

2. **Test connectivity**:
   ```bash
   curl -X POST http://db:5432/v1/migrate -d '{"version": "2.1"}'
   ```

#### **Fix**
- **Use double-write pattern** (for critical writes):
  ```python
  # Example (Python + SQLAlchemy)
  def double_write(entity):
      with db_session.begin():
          # Write to old schema
          entity.save()
          # Write to new schema
          new_entity = entity.to_new_version()
          new_entity.save()
  ```
- **Enable transactions** and timeouts:
  ```yaml
  # Django settings.py
  DATABASES = {
      'default': {
          'ATOMIC_REQUESTS': True,
          'CONN_MAX_AGE': 30,  # Seconds
      }
  }
  ```

---

### **Issue 3: Health Checks Misconfigured**
**Symptom**: New instances fail liveness probes, causing traffic redirection to old versions.
**Root Cause**: Probe endpoints return `5xx` due to cold starts or slow dependencies.

#### **Diagnosis**
1. **Inspect pod status**:
   ```bash
   kubectl get pods -n <namespace> --watch
   ```
   Watch for `CrashLoopBackOff` or pending restart counts.

2. **Test probe endpoints**:
   ```bash
   curl http://<pod-ip>:<probe-port>/healthz
   ```

#### **Fix**
- **Adjust readiness/liveness probes**:
  ```yaml
  livenessProbe:
    httpGet:
      path: /healthz
      port: 8080
    initialDelaySeconds: 30  # Wait for DB connection
    periodSeconds: 10
    failureThreshold: 3
  readinessProbe:
    httpGet:
      path: /ready
      port: 8080
    initialDelaySeconds: 5
  ```
- **Use circuit breakers** (e.g., Hystrix/Resilience4j):
  ```java
  @HystrixCommand(fallbackMethod = "fallback")
  public String callDB() {
      return dbClient.fetchData();
  }
  ```

---

### **Issue 4: Session Affinity Broken**
**Symptom**: Users see inconsistent session data (e.g., carts reset).
**Root Cause**: Affinity misconfigured or session storage not version-aware.

#### **Diagnosis**
1. **Check session storage**:
   ```bash
   # Redis example
   redis-cli KEYS "session:*
   ```
   Verify sessions are stored correctly.

2. **Test session persistence**:
   ```bash
   curl -H "Cookie: sessionid=abc123" http://service
   ```

#### **Fix**
- **Enable stickiness** (e.g., in AWS ALB):
  ```yaml
  annotations:
    alb.ingress.kubernetes.io/sticky-lb-cookie: "true"
    alb.ingress.kubernetes.io/sticky-lb-cookie-name: "AWSALB"
  ```
- **Use distributed sessions** (e.g., Redis):
  ```python
  # Flask example
  session_store = RedisSessionStore(host='redis', port=6379)
  app.config['SESSION_TYPE'] = 'redis'
  ```

---

### **Issue 5: Slow Rollout (Traffic Shift Issues)**
**Symptom**: Latency spikes during traffic transition.
**Root Cause**: Too few new instances or uneven scaling.

#### **Diagnosis**
1. **Monitor scaling events**:
   ```bash
   kubectl describe hpa <hpa-name>
   ```
   Check `scaledUpReplicas` and `scaledDownReplicas`.

2. **Compare QPS**:
   ```bash
   # PromQL query
   rate(http_requests_total[1m]) by (version)
   ```

#### **Fix**
- **Scale preemptively**:
  ```bash
  kubectl scale deployment myapp --replicas=15 --record
  ```
- **Use canary analysis** (e.g., Prometheus alerts):
  ```yaml
  # Alert if >5% error rate in v2
  - alert: CanaryErrorRate
      expr: rate(http_requests_total{version="v2"}[1m]) / rate(http_requests_total[1m]) > 0.05
  ```

---

## **3. Debugging Tools & Techniques**
| **Tool**               | **Use Case**                                                                 | **Example Command**                                  |
|------------------------|-----------------------------------------------------------------------------|------------------------------------------------------|
| **Prometheus/Grafana** | Monitor latency, error rates, and traffic distribution.                   | `http_request_duration_seconds`                     |
| **Kubernetes Events**  | Check pod/rollout issues in real-time.                                   | `kubectl get events --sort-by='.metadata.creationTimestamp'` |
| **Jaeger/Tracing**     | Debug distributed transaction failures.                                    | `jaeger query -service=myapp`                      |
| **AWS CloudWatch**     | ALB/ECS metrics (request counts, latency).                                 | `GetMetricData -MetricName RequestCount`             |
| **Netdata**            | Real-time system metrics (CPU, memory).                                    | `netdata` (web UI at `localhost:19999`)              |
| **Istio Telemetry**    | Service mesh traffic, latency, and errors.                                | `kubectl port-forward -n istio-system svc/istio-telemetry 9090` |

---

## **4. Prevention Strategies**
Implement these practices to avoid ZDD issues:

### **1. Automated Testing**
- **Integration tests** for traffic shifts:
  ```bash
  # Example (Python + Locust)
  @task(3)
  def route_to_v2(self):
      with self.client.get("/api", headers={"X-Version": "v2"}) as response:
          assert response.status_code == 200
  ```
- **Chaos Engineering**: Simulate failures during rollouts.

### **2. Blue/Green Deployment**
- Deploy entirely to a new environment before switching traffic.
  ```bash
  # Terraform example
  module "blue_green" {
    source = "./modules/bg-deploy"
    env    = "production"
    new_version = "v2"
  }
  ```

### **3. Feature Flags**
- Defer critical features until traffic is stable:
  ```javascript
  // Server-side (Node.js)
  const useNewFeature = flags.getFlag('new-feature', false);
  if (!useNewFeature) return legacyEndpoint();
  ```

### **4. Canary Analysis**
- Gradually shift traffic and monitor:
  ```yaml
  # Istio VirtualService (canary)
  http:
    - route:
        - destination:
            host: stable
            subset: v1
      weight: 90
    - route:
        - destination:
            host: canary
            subset: v2
      weight: 10
  ```

### **5. Post-Rollout Checks**
- **Automated rollback** if SLOs are breached:
  ```bash
  # Example (Argo Rollouts)
  kubectl apply -f rollout.yaml -n production
  ```
  ```yaml
  # rollout.yaml
  apiVersion: argoproj.io/v1alpha1
  kind: Rollout
  spec:
    strategy:
      canary:
        steps:
        - setWeight: 10
        - pause: {duration: 1h}
        - setWeight: 50
        analysis:
          templates:
          - templateName: success-rate
          metrics:
          - name: success-rate
            interval: 1m
            threshold: '\d{2}%'
            count: 2
  ```

---

## **5. Summary of Key Actions**
| **Issue**               | **Quick Fix**                                      | **Long-Term Fix**                          |
|-------------------------|---------------------------------------------------|--------------------------------------------|
| Traffic routing mismatch | Adjust ALB/Istio weights                            | Implement blue/green or canary            |
| Database schema errors   | Rollback and retry migrations                      | Use backward-compatible migrations        |
| Health check failures   | Adjust probe timeouts                              | Add circuit breakers                       |
| Session affinity issues  | Enable stickiness or use Redis                    | Standardize session storage                |
| Slow rollout            | Scale preemptively                                | Automate canary analysis                   |

---

## **Final Notes**
- **Start small**: Test ZDD on staging first.
- **Monitor aggressively**: Use alerts for `5xx` errors or latency spikes.
- **Automate rollbacks**: Define clear SLOs and trigger rollbacks if breached.

Zero-downtime deployments are achievable with careful planning and tooling. By following this guide, you can diagnose and resolve issues quickly while minimizing downtime.