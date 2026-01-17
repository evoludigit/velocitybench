# **Debugging Progressive Delivery Patterns: A Troubleshooting Guide**

---

## **1. Overview**
Progressive Delivery (also called Canary, Blue-Green, or Feature Flags) ensures that new features and updates are rolled out incrementally, minimizing risk. Issues in Progressive Delivery typically stem from misconfigured rollout strategies, monitoring gaps, or integration problems with CI/CD pipelines.

This guide provides a structured approach to diagnosing and resolving common issues.

---

## **2. Symptom Checklist**
Before diving into debugging, verify these symptoms:

✅ **Deployment Failures** – Features roll out incorrectly (e.g., 100% traffic instead of 5%).
✅ **Traffic Mismatch** – Users receive unexpected versions of an application.
✅ **Feature Flags Not Working** – Enabled flags don’t affect behavior.
✅ **Performance Degradation** – Unexpected spikes in latency/error rates.
✅ **CI/CD Pipeline Issues** – Builds fail due to Progressive Delivery constraints.
✅ **Monitoring Alerts** – Unusual traffic patterns or failed health checks.

If you observe any of these, proceed to troubleshooting.

---

## **3. Common Issues & Fixes**

### **A. Canary Rollout Not Deploying Correctly**
**Symptom:** Users get the new version when only 5% should be live.

#### **Root Cause:**
- Incorrect percentage allocation in the Progressive Delivery tool (e.g., Argo Rollouts, Flagger, Istio).
- Misconfigured `weights` or `trafficSplit` in Kubernetes manifests.

#### **Fix:**
1. **Check Canary Configuration (Argo Rollouts example):**
   ```yaml
   apiVersion: argoproj.io/v1alpha1
   kind: Rollout
   metadata:
     name: my-app
   spec:
     strategy:
       canary:
         steps:
         - setWeight: 10  # Deploy to 10% of traffic
   ```
   - Verify `setWeight` matches the intended rollout percentage.

2. **Validate Traffic Splitting (Istio example):**
   ```yaml
   trafficPolicy:
     loadBalancer:
       simple: "5"  # 5% of traffic to new version
   ```

3. **Check Service Mesh Monitoring:**
   ```sh
   kubectl get virtualservices -n <namespace>
   ```
   - Ensure the correct split is applied.

---

### **B. Feature Flags Not Triggering**
**Symptom:** A feature enabled via a flag (`ENABLE_NEW_FEATURE=true`) is not active.

#### **Root Cause:**
- **Flag not evaluated correctly** (e.g., missing environment variable).
- **Flag service (e.g., LaunchDarkly, Unleash) misconfigured.**
- **Client-side logic bug** (e.g., wrong flag key in code).

#### **Fix:**
1. **Verify Flag Evaluation (Example with LaunchDarkly SDK):**
   ```javascript
   const client = ldInitializationSettings =>
     FlagsSDK.initialize(ldInitializationSettings, (err, sdk) => {
       if (err) throw err;
       const flagValue = sdk.variation('NEW_FEATURE', false); // Default: false
       console.log('Flag value:', flagValue); // Should be true if enabled
     });
   ```
   - Check if `flagValue` matches expectations.

2. **Debug Flag Service Response:**
   - Use a **flag evaluation API** (e.g., `GET /api/flags/NEW_FEATURE`).
   - Verify the response contains `value: true`.

3. **Check Environment Variables:**
   ```sh
   kubectl exec -it <pod> -- env | grep FEATURE_
   ```
   - Ensure the flag variable is set (`ENABLE_NEW_FEATURE=true`).

---

### **C. Blue-Green Deployment Failing Over**
**Symptom:** Traffic shifts back to the old version unexpectedly.

#### **Root Cause:**
- **Health checks failing** (e.g., startup probes too strict).
- **Load balancer misconfiguration** (e.g., no fallback to old version).
- **DNS latency issues** (slow propagation).

#### **Fix:**
1. **Inspect Health Checks (Kubernetes Liveness/Readiness Probes):**
   ```yaml
   livenessProbe:
     httpGet:
       path: /health
       port: 8080
     initialDelaySeconds: 10
   ```
   - Adjust `initialDelaySeconds` if the app takes longer to start.

2. **Check Load Balancer Rules (Nginx Example):**
   ```nginx
   upstream backend {
     server old-version:8080;
     server new-version:8080 backup;  # Only falls back if new fails
   }
   ```
   - Ensure the backup server is configured.

3. **Validate DNS Propagation:**
   ```sh
   dig <your-domain>  # Check if new version is resolving correctly
   ```

---

### **D. Monitoring Gaps in Progressive Delivery**
**Symptom:** No visibility into rollout percentages or errors.

#### **Root Cause:**
- **No promotion metrics** (e.g., no Prometheus/Grafana dashboards).
- **Custom metrics not exposed** (e.g., feature flag usage).
- **Alerting missing** (e.g., no failsafe for canary failures).

#### **Fix:**
1. **Set Up Metrics (Prometheus + Grafana):**
   ```yaml
   metrics:
     port: 8080
     path: /metrics
   ```
   - Scrape metrics from the app and Progressive Delivery tool.

2. **Example Grafana Dashboard (Canary Health):**
   - Track `argoproj_rollout_status` (for Argo Rollouts).
   - Add alerts for `error_rate > 5%` in canary traffic.

3. **Expose Feature Flag Usage (Custom Metrics):**
   ```javascript
   if (flagValue) {
     metrics.increment('new_feature_usage'); // Track via Prometheus
   }
   ```

---

## **4. Debugging Tools & Techniques**
| **Tool/Technique**       | **Purpose**                                                                 | **Example Command/Query**                     |
|--------------------------|----------------------------------------------------------------------------|---------------------------------------------|
| **Kubernetes `kubectl`** | Inspect rollouts, pods, and traffic rules.                                  | `kubectl get rollouts -n my-ns`             |
| **Prometheus + Grafana** | Track canary metrics, error rates, and traffic splits.                     | `rate(http_requests_total{status=5xx}[1m])` |
| **Flag Evaluation API**  | Debug flag logic if flags are misbehaving.                                  | `curl http://flag-service/flags/NEW_FEATURE` |
| **Istio Telemetry**      | Check traffic routing in service mesh.                                     | `kubectl get virtualservices`               |
| **Logging (EFK Stack)**  | Correlate errors with rollout events.                                      | `grep "NEW_FEATURE" /var/log/app.log`       |
| **Chaos Engineering**    | Test failover scenarios (e.g., kill 20% of pods).                          | `kubectl delete pod <pod-name> --grace-period=0` |

---

## **5. Prevention Strategies**
| **Strategy**                          | **Action Items**                                                                 |
|----------------------------------------|--------------------------------------------------------------------------------|
| **Automated Rollback Testing**         | Use tools like **Flagger** to auto-rollback if error rate exceeds threshold.    |
| **Gradual Rollout Validation**         | Enforce **canary health checks** before full rollout.                          |
| **Feature Flag Best Practices**        | - Avoid hardcoding flag keys. <br> - Use **fallback values** for safety. |
| **Monitoring & Alerting**              | - Track **traffic splits** in real-time. <br> - Alert on **unexpected errors**. |
| **Infrastructure Resilience**         | - Ensure **DNS failover** between versions. <br> - Use **readiness probes**. |
| **Documentation & Runbooks**          | - Document **rollout steps** for quick recovery. <br> - Define **SLOs** for progressive delivery. |

---

## **6. Quick Recovery Checklist**
If a rollout goes wrong:
1. **Pause new deployments** (`kubectl rollout pause <deployment>`).
2. **Revert to stable version** (if using Blue-Green).
3. **Check logs** (`kubectl logs <pod>`).
4. **Adjust canary weights** (if partial rollback needed).
5. **Restart monitoring** (check dashboards for anomalies).

---

## **Final Notes**
Progressive Delivery reduces risk but requires **strict monitoring, automated safeguards, and clear rollback procedures**. Always:
- **Test rollouts in staging** before production.
- **Use feature flags for safe experimentation**.
- **Automate recovery** where possible.

By following this guide, you can quickly diagnose and resolve issues while maintaining smooth deployments. 🚀