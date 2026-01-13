# **Debugging Deployment Strategies: A Troubleshooting Guide**

## **1. Introduction**
Deployment Strategies are critical for managing rollouts in modern applications, ensuring zero downtime, gradual rollouts, and rollback capabilities. Common patterns include **Blue-Green, Canary, Rolling, A/B Testing, and Feature Flags**. If implemented incorrectly, they can lead to downtime, traffic misrouting, or inconsistent application behavior.

This guide provides a **practical, structured approach** to diagnosing and resolving issues in Deployment Strategies.

---

## **2. Symptom Checklist**
Before diving into fixes, verify which symptoms align with your issue:

| **Symptom**                     | **Possible Cause**                                                                 |
|----------------------------------|------------------------------------------------------------------------------------|
| Traffic not reaching new release | Misconfigured routing (e.g., missing DNS, load balancer misrouting)               |
| Sudden traffic spikes after rollout | Canary/A/B test misconfiguration, incorrect traffic splitting                    |
| Application crashes post-deploy  | Incompatible version mismatch, resource constraints, or untested rollout logic    |
| Rollback fails to revert changes | Incomplete rollback script, stale configurations, or stuck services              |
| High latency after deployment    | Overloaded services due to gradual rollout, caching issues, or regional delays     |
| Users report inconsistent UI/UX   | Feature flag misalignment, caching conflicts, or stale deployments               |
| Health checks failing            | Deployment strategy not handling service health properly (e.g., canary too aggressive) |

**Quick Check:**
✅ **Verify routing** (DNS, LB, service mesh)
✅ **Check traffic distribution** (is it as expected?)
✅ **Monitor logs** (errors, timeouts, unexpected rejections)
✅ **Compare states** (old vs. new deployment configs)

---

## **3. Common Issues & Fixes (with Code Snippets)**

### **3.1 Traffic Misrouting (Blue-Green, Canary, A/B)**
**Symptom:** Traffic is not splitting correctly, or old version is still serving requests after new deploy.

#### **Possible Causes & Fixes**

| **Issue**                     | **Debugging Steps**                                                                 | **Fix**                                                                                     |
|-------------------------------|------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|
| **DNS not updated**           | Check DNS TTL, verify records in cloud provider (e.g., Route 53, Cloudflare)         | Reduce TTL in DNS records or flush cache                                       |
| **Load Balancer misconfigured** | Verify LB rules (e.g., ALB, NGINX) point to correct targets                          | Update LB rules to route traffic to new target group                                  |
| **Service Mesh (Istio/Linkerd) misrouting** | Check `DestinationRule`, `VirtualService` configs                                  | Adjust `traffic-split` or `subset` rules                                           |
| **Canary traffic not splitting** | Misconfigured traffic percentages (e.g., 90% old, 10% new)                       | Update Canary policy (e.g., Kubernetes `Weighted` service):<br>```yaml<br>`weighted:<br>  canary:<br>    weight: 20<br>    labels:<br>      version: v2<br>  stable:<br>    weight: 80<br>    labels:<br>      version: v1<br>``` |

**Example Fix (Istio Canary):**
```yaml
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: my-service
spec:
  hosts:
  - my-service.example.com
  http:
  - route:
    - destination:
        host: my-service.example.com
        subset: v1
      weight: 80
    - destination:
        host: my-service.example.com
        subset: v2
      weight: 20
```

---

### **3.2 Rollback Fails or is Slower Than Expected**
**Symptom:** Rollback doesn’t revert traffic as expected, or services remain stuck in the old state.

#### **Possible Causes & Fixes**

| **Issue**                     | **Debugging Steps**                                                                 | **Fix**                                                                                     |
|-------------------------------|------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|
| **No rollback policy defined** | Check if `rollback` is implemented in CI/CD (e.g., Argo Rollouts, Flagger)       | Add rollback logic:<br>```yaml<br>- command: ["sh", "-c", "kubectl rollout undo deployment/my-dep"]``` |
| **Incomplete resource cleanup** | Orphaned pods, stuck services, or lingering configs in DB                      | Force cleanup:<br>```bash<br>kubectl delete pod --all -n <namespace> --force``` |
| **DNS/Load Balancer stuck**   | Cache hasn’t refreshed after rollback                                               | Update DNS TTL or manually update LB rules                                              |
| **Database inconsistency**    | Schema changes not reverted                                                           | Run a migration revert script (e.g., Flyway, Liquibase)                                    |

**Example (Kubernetes Rollback):**
```bash
# Check rollout status
kubectl rollout status deployment/my-app

# Force rollback (if stuck)
kubectl rollout undo deployment/my-app --to-revision=2
```

---

### **3.3 Feature Flags Misbehaving**
**Symptom:** Some users see old features while others see new ones inconsistently.

#### **Possible Causes & Fixes**

| **Issue**                     | **Debugging Steps**                                                                 | **Fix**                                                                                     |
|-------------------------------|------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|
| **Flag not evaluated correctly** | Check flag service (LaunchDarkly, Flagsmith) for misconfigurations                 | Verify flag rules in dashboard:<br>`user.id in ["admin"] → true`                         |
| **Client-side caching stale**  | Browser/SDK cache not invalidating                                                 | Add cache-busting query param:<br>`/feature?v=${Date.now()}`                                |
| **Server-side filter mismatch** | Incorrect feature filter logic (e.g., ` percentageRollout(10%)`)                   | Adjust rollout percentage:<br>```java<br>launchDarkly.client().flag("newFeature", user);``` |
| **Race condition in rollout**  | Flags evaluated after traffic switch                                               | Use **feature flag-first routing** (evaluate flag before LB)                                 |

**Example (LaunchDarkly Client-Side Fix):**
```javascript
// Ensure fresh evaluation
const flagValue = launchDarkly.client().variation(
  "newFeature",
  user,
  false, // default
  { force: true } // bypass cache
);
```

---

### **3.4 Gradual Rollout (Rolling/Canary) Causes Overload**
**Symptom:** New version degrades performance due to sudden traffic increase.

#### **Possible Causes & Fixes**

| **Issue**                     | **Debugging Steps**                                                                 | **Fix**                                                                                     |
|-------------------------------|------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|
| **No auto-scaling configured** | Pods/VMs can’t handle sudden traffic                                               | Enable HPA (Horizontal Pod Autoscaler):<br>```yaml<br>autoscaling:<br>  scaleTargetRef:<br>    apiVersion: apps/v1<br>    kind: Deployment<br>    name: my-app<br>  minReplicas: 2<br>  maxReplicas: 10<br>  metrics:<br>  - type: Resource<br>    resource:<br>      name: cpu<br>      target:<br>        type: Utilization<br>        averageUtilization: 80``` |
| **Database connections exhausted** | New version uses more DB connections than old                                      | Increase DB pool size or implement connection pooling tuning                             |
| **Cold starts in serverless**  | Lambda/Cloud Run cold starts slow down rollout                                     | Use provisioned concurrency (AWS Lambda) or reduce canary rate                          |

**Example (Kubernetes HPA):**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: my-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

### **3.5 Health Checks Failing**
**Symptom:** ` readinessProbe` or `livenessProbe` fails after deployment.

#### **Possible Causes & Fixes**

| **Issue**                     | **Debugging Steps**                                                                 | **Fix**                                                                                     |
|-------------------------------|------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|
| **Probe misconfigured**       | Incorrect path (e.g., `/health` vs. `/api/health`)                               | Update probe in deployment:<br>```yaml<br>livenessProbe:<br>  httpGet:<br>    path: /api/health<br>    port: 8080<br>  initialDelaySeconds: 10<br>  periodSeconds: 5``` |
| **Application startup slow** | Probe runs before app is ready                                                      | Increase `initialDelaySeconds`                                                             |
| **Network partition**         | Service mesh or LB is throttling unhealthy pods                                     | Check `kubectl describe pod` for `CrashLoopBackOff`                                         |

**Example (Correct Probe Config):**
```yaml
livenessProbe:
  httpGet:
    path: /api/health
    port: 8080
  initialDelaySeconds: 15
  periodSeconds: 10
  failureThreshold: 3
```

---

## **4. Debugging Tools & Techniques**

### **4.1 Observability Stack**
| **Tool**          | **Purpose**                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| **Prometheus + Grafana** | Monitor metrics (latency, error rates, traffic split)                        |
| **OpenTelemetry**   | Trace requests across microservices to find misrouted calls                  |
| **Datadog/New Relic** | APM for deep performance insights                                          |
| **Kubernetes Events** | Check `kubectl get events` for pod/rollout issues                           |

**Example (Check Canary Traffic in Prometheus):**
```promql
# Traffic split for canary vs stable
sum(rate(http_requests_total{service="my-service", version="v2"}[1m])) by (version)
```

### **4.2 Network Debugging**
| **Tool**          | **Use Case**                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| **`curl -v`**      | Check HTTP responses from different versions                                 |
| **`kubectl port-forward`** | Debug locally: `kubectl port-forward svc/my-service 8080:80`          |
| **Wireshark/tcpdump** | Inspect network traffic between LB and pods                                |
| **Istio Telemetry** | Check `istio-telemetry` for misrouted requests                             |

**Example (Check Service Version in Response):**
```bash
curl -H "X-User-ID: test" http://my-service:8080/api/health
# Should return version header: X-Version: v2
```

### **4.3 Log Correlation**
- **Centralized Logging (ELK, Loki, Datadog):** Filter logs by `X-Version` header.
- **Structured Logging:** Ensure logs include `version`, `user_id`, and `timestamp`.
- **Error Tracking (Sentry, Honeycomb):** Correlate errors with traffic splits.

**Example (Grep Logs for Canary Errors):**
```bash
# Filter logs for version v2 errors
kubectl logs -l app=my-app,version=v2 --since=5m | grep "ERROR"
```

---

## **5. Prevention Strategies**
### **5.1 Pre-Deployment Checks**
✅ **Automated Smoke Tests** – Verify new version handles traffic before full rollout.
✅ **Canary Analysis** – Use tools like **Flux, Argo Rollouts, or Flagger** to auto-scale based on error rates.
✅ **Multi-Stage Rollouts** – Start with **0.1% traffic**, then gradually increase.

**Example (Flux Canary Analysis):**
```yaml
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: my-app
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  service:
    port: 8080
  analysis:
    interval: 1m
    threshold: 5
    maxWeight: 50
    stepWeight: 10
    metrics:
    - name: request-success-rate
      thresholdRange:
        min: 99
      interval: 1m
    - name: request-duration
      thresholdRange:
        max: 500
      interval: 1m
```

### **5.2 Post-Deployment Monitoring**
🔹 **Real User Monitoring (RUM)** – Track user-reported issues.
🔹 **Automated Rollback Triggers** – If error rate > 2%, auto-revert.
🔹 **Chaos Engineering** – Test failure scenarios (e.g., `Chaos Mesh` to kill pods).

### **5.3 Configuration Best Practices**
📌 **Infrastructure as Code (IaC)** – Use Terraform/Helm to avoid manual misconfigs.
📌 **Environment Parity** – Test in staging with **same traffic patterns** as prod.
📌 **Feature Flag Management** – Centralize flags (LaunchDarkly, Unleash) to avoid drift.

---

## **6. Summary Checklist for Quick Resolution**
| **Step** | **Action** |
|----------|------------|
| **1. Verify Routing** | Check DNS, LB, service mesh configs. |
| **2. Check Traffic Split** | Use Prometheus/Grafana to confirm percentages. |
| **3. Review Logs** | Filter by `version`, `user_id`, and error patterns. |
| **4. Test Rollback** | Manually trigger a rollback to validate recovery. |
| **5. Adjust Autoscaling** | Scale up canary pods if overload occurs. |
| **6. Update Probes** | Fix `readinessProbe`/`livenessProbe` misconfigs. |
| **7. Enable Automated Alerts** | Set up SLOs (e.g., error budget) for future rollouts. |

---

## **7. Final Thoughts**
Deployment Strategies are powerful but require **careful validation**. The key is:
1. **Start small** (canary with 5% traffic).
2. **Monitor aggressively** (metrics + logs + traces).
3. **Automate rollback** if things go wrong.
4. **Test in staging** with similar conditions as production.

By following this guide, you can **minimize downtime, reduce risk, and deploy with confidence**.

---
**Need Help?**
- **Kubernetes?** → `kubectl describe deployment <name>`
- **Istio?** → `istioctl analyze`
- **Database issues?** → Check slow queries with `pg_stat_statements` (PostgreSQL)

Happy debugging! 🚀